import re
from datetime import datetime
from typing import Final

from playwright.sync_api import (
    Error as PlaywrightError,
    Locator,
    Page,
    TimeoutError as PlaywrightTimeoutError,
)

from backend.src.models.projeto import (
    ProjetoCompleto,
    ProjetoResumo,
    StatusProjeto,
)


BASE_URL: Final[str] = "https://www.99freelas.com.br"
BASE_PROJECTS_URL: Final[str] = (
    f"{BASE_URL}/projects"
    "?order=mais-recentes"
    "&categoria=web-mobile-e-software"
)
TIMEOUT_NAVEGACAO_MS: Final[int] = 30000
TENTATIVAS_NAVEGACAO: Final[int] = 3


class ScraperError(Exception):
    """Erro recuperável relacionado à navegação do scraper."""


STATUS_INVALIDOS: Final[dict[StatusProjeto, tuple[str, ...]]] = {
    "CANCELADO": (
        "este projeto foi cancelado",
        "projeto foi cancelado",
        "projeto cancelado pela moderação",
    ),
    "REPROVADO": (
        "este projeto foi reprovado",
        "projeto foi reprovado",
        "projeto reprovado pela moderação",
    ),
    "ENCERRADO": (
        "este projeto foi encerrado",
        "projeto foi encerrado",
        "este projeto foi concluído",
        "projeto foi concluído",
        "projeto concluído",
        "projeto finalizado",
    ),
}

STATUS_BOTAO_INVALIDO: Final[dict[StatusProjeto, tuple[str, ...]]] = {
    "CANCELADO": ("cancelado",),
    "REPROVADO": ("reprovado",),
    "ENCERRADO": ("encerrado", "concluído", "finalizado"),
}


def _normalizar_texto(valor: str) -> str:
    return re.sub(r"\s+", " ", valor).strip().lower()


def detectar_status_projeto(
    pagina: Page,
    texto: str,
) -> StatusProjeto:
    texto_normalizado = _normalizar_texto(texto)

    for status, marcadores in STATUS_INVALIDOS.items():
        if any(marcador in texto_normalizado for marcador in marcadores):
            return status

    try:
        textos_botoes = pagina.locator("button, a").all_inner_texts()
    except PlaywrightError:
        textos_botoes = []

    botoes_normalizados = {
        _normalizar_texto(valor)
        for valor in textos_botoes
        if valor.strip()
    }

    for status, marcadores in STATUS_BOTAO_INVALIDO.items():
        if any(
            marcador_alvo in botao
            for botao in botoes_normalizados
            for marcador_alvo in marcadores
        ):
            return status

    return "ATIVO"


def extrair_id(url: str) -> str | None:
    resultado = re.search(r"-(\d+)(?:\?|$)", url)
    return resultado.group(1) if resultado else None


def extrair_informacao(texto: str, nome: str) -> str | None:
    padrao = rf"{re.escape(nome)}:\s*([^\n]+)"
    resultado = re.search(padrao, texto, re.IGNORECASE)
    return resultado.group(1).strip() if resultado else None


def extrair_descricao(texto: str) -> str | None:
    marcadores_inicio = (
        "Descrição do Projeto:",
        "Descrição do projeto:",
    )

    for marcador in marcadores_inicio:
        if marcador not in texto:
            continue

        descricao = texto.split(marcador, 1)[1]
        marcadores_fim = (
            "Atividades do cliente nesse projeto",
            "Sobre o cliente",
            "Cliente:",
        )

        for marcador_fim in marcadores_fim:
            if marcador_fim in descricao:
                descricao = descricao.split(marcador_fim, 1)[0]
                break

        descricao = descricao.strip()
        return descricao or None

    return None


def verificar_exclusividade_card(card: Locator) -> bool:
    indicador = card.locator(
        'div.flags img[alt="Projeto exclusivo"]'
    )
    return indicador.count() > 0


def _navegar_com_retry(pagina: Page, url: str) -> None:
    ultimo_erro: Exception | None = None

    for tentativa in range(1, TENTATIVAS_NAVEGACAO + 1):
        try:
            pagina.goto(
                url,
                wait_until="domcontentloaded",
                timeout=TIMEOUT_NAVEGACAO_MS,
            )
            pagina.wait_for_load_state(
                "domcontentloaded",
                timeout=TIMEOUT_NAVEGACAO_MS,
            )
            return
        except (PlaywrightTimeoutError, PlaywrightError) as erro:
            ultimo_erro = erro
            print(
                f"Falha ao abrir {url} "
                f"(tentativa {tentativa}/{TENTATIVAS_NAVEGACAO}): {erro}"
            )
            if tentativa < TENTATIVAS_NAVEGACAO:
                pagina.wait_for_timeout(1000 * tentativa)

    raise ScraperError(
        f"Não foi possível abrir a página: {url}"
    ) from ultimo_erro


def extrair_projeto(
    pagina: Page,
    url: str,
    projeto_exclusivo: bool,
    data_coleta: str | None = None,
) -> ProjetoCompleto:
    print(f"\nAbrindo projeto: {url}")

    try:
        _navegar_com_retry(pagina, url)
        texto = pagina.locator("body").inner_text(
            timeout=TIMEOUT_NAVEGACAO_MS
        )
    except (ScraperError, PlaywrightTimeoutError, PlaywrightError) as erro:
        raise ScraperError(
            f"Falha ao extrair o projeto {url}: {erro}"
        ) from erro

    projeto_id = extrair_id(url)
    if not projeto_id:
        raise ScraperError(
            f"Não foi possível extrair o ID do projeto: {url}"
        )

    status = detectar_status_projeto(pagina, texto)
    agora = datetime.now().isoformat(timespec="seconds")

    titulo = None
    try:
        titulo_elemento = pagina.locator("h1").first
        if titulo_elemento.count() > 0:
            titulo = titulo_elemento.inner_text(timeout=5000).strip()
    except PlaywrightTimeoutError:
        titulo = None

    if not titulo:
        raise ScraperError(
            f"Não foi possível encontrar o título do projeto: {url}"
        )

    return {
        "id": projeto_id,
        "titulo": titulo,
        "descricao": extrair_descricao(texto),
        "url": url,
        "data_publicacao": None,
        "data_coleta": data_coleta or agora,
        "ultima_verificacao": agora,
        "status": status,
        "categoria": extrair_informacao(texto, "Categoria"),
        "subcategoria": extrair_informacao(texto, "Subcategoria"),
        "orcamento": extrair_informacao(texto, "Orçamento"),
        "nivel_experiencia": extrair_informacao(texto, "Nível de experiência"),
        "visibilidade": extrair_informacao(texto, "Visibilidade"),
        "propostas": extrair_informacao(texto, "Propostas"),
        "interessados": extrair_informacao(texto, "Interessados"),
        "projeto_exclusivo": projeto_exclusivo,
    }


def encontrar_projetos(
    pagina: Page,
    numero_pagina: int,
) -> list[ProjetoResumo]:
    url = f"{BASE_PROJECTS_URL}&page={numero_pagina}"
    print(f"\n{'=' * 70}\nABRINDO PÁGINA {numero_pagina}\n{url}\n{'=' * 70}")

    _navegar_com_retry(pagina, url)
    try:
        pagina.locator("body").inner_text(timeout=TIMEOUT_NAVEGACAO_MS)
    except PlaywrightTimeoutError as erro:
        raise ScraperError(
            f"Timeout ao ler a página {numero_pagina}."
        ) from erro

    cards = pagina.locator("li.result-item")
    projetos: list[ProjetoResumo] = []
    ids_encontrados: set[str] = set()

    for indice in range(cards.count()):
        card = cards.nth(indice)
        try:
            projeto_id = card.get_attribute("data-id")
            if not projeto_id or projeto_id in ids_encontrados:
                continue

            titulo_elemento = card.locator("h1.title a")
            if titulo_elemento.count() == 0:
                continue

            titulo = titulo_elemento.inner_text().strip()
            href = titulo_elemento.get_attribute("href")
            if not href:
                continue

            url_projeto = href if href.startswith("http") else BASE_URL + href
            projeto = ProjetoResumo(
                id=projeto_id,
                titulo=titulo,
                url=url_projeto,
                projeto_exclusivo=verificar_exclusividade_card(card),
            )
            projetos.append(projeto)
            ids_encontrados.add(projeto_id)
            print(
                f"{projeto_id} | {titulo} | Exclusivo: "
                f"{projeto['projeto_exclusivo']}"
            )
        except (PlaywrightTimeoutError, PlaywrightError) as erro:
            print(
                f"Erro ao processar card {indice} da página "
                f"{numero_pagina}: {erro}"
            )

    print(f"Projetos encontrados nesta página: {len(projetos)}")
    return projetos


def coletar_todos_os_projetos(pagina: Page) -> list[ProjetoResumo]:
    projetos_encontrados: list[ProjetoResumo] = []
    ids_totais: set[str] = set()
    numero_pagina = 1
    falhas_consecutivas = 0
    max_falhas_consecutivas = 2

    while falhas_consecutivas < max_falhas_consecutivas:
        try:
            projetos_pagina = encontrar_projetos(pagina, numero_pagina)
            falhas_consecutivas = 0
        except ScraperError as erro:
            falhas_consecutivas += 1
            print(
                f"Falha ao coletar a página {numero_pagina}: {erro}. "
                f"Falhas consecutivas: {falhas_consecutivas}/"
                f"{max_falhas_consecutivas}"
            )
            numero_pagina += 1
            continue

        if not projetos_pagina:
            print(f"Fim da paginação na página {numero_pagina}.")
            break

        novos = 0
        for projeto in projetos_pagina:
            if projeto["id"] in ids_totais:
                continue
            ids_totais.add(projeto["id"])
            projetos_encontrados.append(projeto)
            novos += 1

        print(f"Novos projetos adicionados: {novos}")
        numero_pagina += 1

    if falhas_consecutivas >= max_falhas_consecutivas:
        print("A coleta foi encerrada após falhas consecutivas de navegação.")

    return projetos_encontrados
