import os
import random
import re
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError
from pydantic import ValidationError

from backend.src.models.analise import AnaliseProjeto
from backend.src.models.projeto import ProjetoCompleto


BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
MAX_TENTATIVAS = max(1, int(os.getenv("GEMINI_MAX_TENTATIVAS", "4")))
BACKOFF_INICIAL = max(0.5, float(os.getenv("GEMINI_BACKOFF_INICIAL", "2")))
BACKOFF_MAXIMO = max(BACKOFF_INICIAL, float(os.getenv("GEMINI_BACKOFF_MAXIMO", "60")))
INTERVALO_MINIMO = max(0.0, float(os.getenv("GEMINI_INTERVALO_MINIMO", "2")))

_client: genai.Client | None = None
_ultima_chamada = 0.0


def _obter_client() -> genai.Client:
    global _client
    if _client is not None:
        return _client

    if not API_KEY:
        raise RuntimeError(
            "A variável GEMINI_API_KEY não foi encontrada no arquivo backend/.env."
        )

    _client = genai.Client(api_key=API_KEY)
    return _client


def _esperar_intervalo_minimo() -> None:
    global _ultima_chamada
    agora = time.monotonic()
    restante = INTERVALO_MINIMO - (agora - _ultima_chamada)
    if restante > 0:
        time.sleep(restante)
    _ultima_chamada = time.monotonic()


def _extrair_retry_after(erro: APIError) -> float | None:
    mensagem = str(erro)
    padroes = (
        r"retryDelay['\"]?\s*[:=]\s*['\"]?(\d+(?:\.\d+)?)s",
        r"retry in\s+(\d+(?:\.\d+)?)s",
    )
    for padrao in padroes:
        resultado = re.search(padrao, mensagem, re.IGNORECASE)
        if resultado:
            return float(resultado.group(1))
    return None


def _eh_quota_diaria(erro: APIError) -> bool:
    mensagem = str(erro).lower()
    indicadores = (
        "perdayperproject",
        "per day",
        "daily quota",
        "requestsperday",
    )
    return any(indicador in mensagem for indicador in indicadores)


def _deve_repetir(erro: APIError) -> bool:
    return erro.code in {429, 500, 502, 503, 504}


def _calcular_backoff(tentativa: int, erro: APIError) -> float:
    retry_after = _extrair_retry_after(erro)
    if retry_after is not None:
        return min(max(retry_after, 1.0), BACKOFF_MAXIMO)

    base = min(BACKOFF_INICIAL * (2 ** (tentativa - 1)), BACKOFF_MAXIMO)
    jitter = random.uniform(0, base * 0.25)
    return min(base + jitter, BACKOFF_MAXIMO)


def montar_prompt(projeto: ProjetoCompleto) -> str:
    return f"""
Analise o seguinte projeto de freelancer.

Use somente as informações fornecidas abaixo.
Não invente informações que não estejam presentes.
Se alguma informação importante estiver faltando, deixe isso claro.
Se fizer estimativas, deixe claro que são estimativas.

Considere especialmente:
- compatibilidade com um freelancer individual;
- dificuldade técnica;
- conhecimentos necessários;
- riscos de execução;
- orçamento;
- concorrência;
- informações ausentes;
- possibilidade real de concluir o projeto.

Seja objetivo e direto.

Limites recomendados:
- justificativa: no máximo 3 parágrafos curtos;
- riscos: no máximo 5 itens;
- tecnologias: apenas as realmente necessárias;
- pontos para esclarecer: no máximo 5 itens;
- veredito: no máximo 2 parágrafos curtos.

PROJETO:

Título: {projeto["titulo"]}
Descrição: {projeto["descricao"]}
Categoria: {projeto["categoria"]}
Subcategoria: {projeto["subcategoria"]}
Orçamento: {projeto["orcamento"]}
Nível de experiência: {projeto["nivel_experiencia"]}
Visibilidade: {projeto["visibilidade"]}
Propostas: {projeto["propostas"]}
Interessados: {projeto["interessados"]}
""".strip()


def _extrair_analise(resposta: Any) -> AnaliseProjeto:
    analise_parsed = getattr(resposta, "parsed", None)
    if isinstance(analise_parsed, AnaliseProjeto):
        return analise_parsed
    if analise_parsed is not None:
        return AnaliseProjeto.model_validate(analise_parsed)

    texto = getattr(resposta, "text", None)
    if not texto:
        raise ValueError("O Gemini retornou uma resposta vazia.")
    return AnaliseProjeto.model_validate_json(texto)


def gerar_analise_com_retry(
    prompt_texto: str,
    max_tentativas: int = MAX_TENTATIVAS,
) -> AnaliseProjeto | None:
    client = _obter_client()

    for tentativa in range(1, max_tentativas + 1):
        try:
            print(
                f"Enviando para o Gemini "
                f"(tentativa {tentativa}/{max_tentativas})..."
            )
            _esperar_intervalo_minimo()

            resposta = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt_texto,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": AnaliseProjeto,
                    "http_options": {"timeout": 30000},
                },
            )
            return _extrair_analise(resposta)

        except APIError as erro:
            if erro.code == 429 and _eh_quota_diaria(erro):
                print(
                    "A quota diária do Gemini foi excedida. "
                    "O projeto ficará pendente sem novas tentativas."
                )
                return None

            if not _deve_repetir(erro):
                print(f"Erro não recuperável do Gemini ({erro.code}): {erro}")
                return None

            if tentativa == max_tentativas:
                print(
                    f"Gemini continuou indisponível após {max_tentativas} "
                    "tentativas. O projeto ficará pendente."
                )
                return None

            espera = _calcular_backoff(tentativa, erro)
            print(
                f"Gemini retornou {erro.code}. "
                f"Nova tentativa em {espera:.1f}s."
            )
            time.sleep(espera)

        except ValidationError as erro:
            print("A resposta do Gemini não correspondeu ao formato esperado.")
            print(erro)
            return None

        except Exception as erro:
            print(f"Erro inesperado durante a análise do Gemini: {erro}")
            return None

    return None


def analisar_projeto(projeto: ProjetoCompleto) -> AnaliseProjeto | None:
    return gerar_analise_com_retry(montar_prompt(projeto))
