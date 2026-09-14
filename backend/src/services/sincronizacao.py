import logging
import os
from typing import Callable

from playwright.sync_api import Browser, Page, sync_playwright

from backend.src.database.conexao import (
    analise_existe,
    atualizar_projeto,
    buscar_projeto,
    listar_projetos_para_verificacao,
    remover_projeto,
    salvar_analise,
    salvar_projeto,
)
from backend.src.database.sincronizacao import atualizar_progresso
from backend.src.ia.analise import analisar_projeto
from backend.src.models.projeto import ProjetoCompleto, ProjetoResumo
from backend.src.scraper.scraper import (
    ScraperError,
    coletar_todos_os_projetos,
    extrair_projeto,
)

logger = logging.getLogger(__name__)


def _env_bool(name: str, default: bool) -> bool:
    valor = os.getenv(name)
    if valor is None:
        return default
    return valor.strip().lower() in {"1", "true", "yes", "sim", "on"}


def _criar_pagina(navegador: Browser) -> Page:
    pagina = navegador.new_page()
    pagina.set_default_timeout(15000)
    pagina.set_default_navigation_timeout(30000)
    return pagina


def _obter_projeto_completo(pagina: Page, projeto: ProjetoResumo) -> ProjetoCompleto | None:
    existente = buscar_projeto(projeto["id"])
    if existente is not None:
        if existente["status"] != "ATIVO":
            remover_projeto(projeto["id"])
            return None
        return existente

    try:
        projeto_completo = extrair_projeto(
            pagina,
            projeto["url"],
            projeto["projeto_exclusivo"],
        )
        if projeto_completo["status"] != "ATIVO":
            return None
        salvar_projeto(projeto_completo)
        logger.info("Projeto %s salvo no banco.", projeto["id"])
        return projeto_completo
    except ScraperError:
        raise
    except Exception as erro:
        raise ScraperError(
            f"Erro inesperado ao persistir projeto {projeto['id']}: {erro}"
        ) from erro


def _verificar_projetos_existentes(
    pagina: Page,
    on_progress: Callable[..., None],
) -> tuple[int, int, int]:
    projetos = listar_projetos_para_verificacao()
    total = len(projetos)
    sucessos = 0
    falhas = 0

    if total == 0:
        logger.info("Nenhum projeto ativo para verificar.")
        return 0, 0, 0

    for indice, projeto in enumerate(projetos, start=1):
        on_progress(
            "VERIFICANDO",
            indice - 1,
            total,
            sucessos,
            falhas,
            projeto["titulo"],
            f"Verificando status de {projeto['id']} ({indice}/{total}).",
        )
        try:
            existente = buscar_projeto(projeto["id"])
            if existente is None:
                sucessos += 1
                continue

            projeto_atualizado = extrair_projeto(
                pagina,
                projeto["url"],
                projeto["projeto_exclusivo"],
                data_coleta=existente["data_coleta"],
            )
            if projeto_atualizado["status"] != "ATIVO":
                remover_projeto(projeto["id"])
                logger.info(
                    "Projeto %s removido após confirmação de status %s.",
                    projeto["id"],
                    projeto_atualizado["status"],
                )
            else:
                atualizar_projeto(projeto_atualizado)
            sucessos += 1
        except ScraperError as erro:
            falhas += 1
            logger.warning(
                "Projeto %s não pôde ser verificado; mantendo registro atual. Erro: %s",
                projeto["id"],
                erro,
            )
        except Exception:
            falhas += 1
            logger.exception(
                "Erro inesperado ao verificar projeto %s; mantendo registro atual.",
                projeto["id"],
            )
        finally:
            on_progress(
                "VERIFICANDO",
                indice,
                total,
                sucessos,
                falhas,
                projeto["titulo"],
                f"Verificação {indice}/{total} concluída.",
            )

    return total, sucessos, falhas


def _processar_projeto(
    pagina: Page,
    projeto: ProjetoResumo,
) -> tuple[str, bool]:
    projeto_id = projeto["id"]
    try:
        projeto_completo = _obter_projeto_completo(pagina, projeto)
        if projeto_completo is None:
            return "ignorado", True

        if analise_existe(projeto_id):
            return "ja_analisado", True

        logger.info("Analisando projeto %s com Gemini.", projeto_id)
        analise = analisar_projeto(projeto_completo)
        if analise is None:
            logger.warning("Gemini não retornou análise para o projeto %s.", projeto_id)
            return "pendente", False

        salvar_analise(projeto_id, analise)
        logger.info("Análise do projeto %s salva no banco.", projeto_id)
        return "analisado", True
    except ScraperError as erro:
        logger.warning("Projeto %s não pôde ser processado: %s", projeto_id, erro)
        return "erro", False
    except Exception:
        logger.exception("Erro inesperado ao processar projeto %s.", projeto_id)
        return "erro", False


def executar_sincronizacao() -> None:
    """Executa uma sincronização completa. Deve ser chamada somente pelo worker."""
    navegador: Browser | None = None
    pagina: Page | None = None
    totais = {"sucessos": 0, "falhas": 0}

    def on_progress(
        fase: str,
        atual: int,
        total: int,
        sucessos: int,
        falhas: int,
        projeto_atual: str | None,
        mensagem: str | None = None,
    ) -> None:
        totais["sucessos"] = sucessos
        totais["falhas"] = falhas
        atualizar_progresso(
            fase=fase,
            progresso_atual=atual,
            progresso_total=total,
            sucessos=sucessos,
            falhas=falhas,
            projeto_atual=projeto_atual,
            mensagem=mensagem,
        )

    try:
        headless = _env_bool("PLAYWRIGHT_HEADLESS", True)
        logger.info("Iniciando sincronização no worker.")

        with sync_playwright() as playwright:
            navegador = playwright.chromium.launch(headless=headless)
            pagina = _criar_pagina(navegador)

            existentes_total, existentes_ok, existentes_falhas = _verificar_projetos_existentes(
                pagina, on_progress
            )
            totais["sucessos"] = existentes_ok
            totais["falhas"] = existentes_falhas

            on_progress(
                "COLETANDO",
                0,
                0,
                totais["sucessos"],
                totais["falhas"],
                None,
                "Coletando projetos novos do 99Freelas...",
            )
            projetos = coletar_todos_os_projetos(pagina)
            logger.info("Coleta concluída: %d projetos encontrados.", len(projetos))

            total_analise = len(projetos)
            analise_sucessos = 0
            analise_falhas = 0

            if total_analise == 0:
                on_progress(
                    "ANALISANDO",
                    0,
                    0,
                    totais["sucessos"],
                    totais["falhas"],
                    None,
                    "Nenhum projeto encontrado para analisar.",
                )
            else:
                for indice, projeto in enumerate(projetos, start=1):
                    on_progress(
                        "ANALISANDO",
                        indice - 1,
                        total_analise,
                        totais["sucessos"] + analise_sucessos,
                        totais["falhas"] + analise_falhas,
                        projeto["titulo"],
                        f"Analisando projeto {indice}/{total_analise}.",
                    )
                    resultado, ok = _processar_projeto(pagina, projeto)
                    if ok:
                        analise_sucessos += 1
                    else:
                        analise_falhas += 1
                    on_progress(
                        "ANALISANDO",
                        indice,
                        total_analise,
                        totais["sucessos"] + analise_sucessos,
                        totais["falhas"] + analise_falhas,
                        projeto["titulo"],
                        f"{resultado.replace('_', ' ').capitalize()}: {indice}/{total_analise}.",
                    )

            totais["sucessos"] += analise_sucessos
            totais["falhas"] += analise_falhas

            atualizar_progresso(
                fase="CONCLUIDA",
                progresso_atual=total_analise,
                progresso_total=total_analise,
                sucessos=totais["sucessos"],
                falhas=totais["falhas"],
                projeto_atual=None,
                mensagem=(
                    f"Sincronização concluída: {totais['sucessos']} sucessos e "
                    f"{totais['falhas']} falhas/pendências."
                ),
            )
            logger.info(
                "Sincronização concluída. Verificados=%d, encontrados=%d, sucessos=%d, falhas=%d.",
                existentes_total,
                len(projetos),
                totais["sucessos"],
                totais["falhas"],
            )
    except Exception as erro:
        logger.exception("Falha fatal na sincronização.")
        raise
    finally:
        if pagina is not None:
            try:
                pagina.close()
            except Exception:
                logger.exception("Falha ao fechar a página do Playwright.")
        if navegador is not None:
            try:
                navegador.close()
            except Exception:
                logger.exception("Falha ao fechar o navegador do Playwright.")
