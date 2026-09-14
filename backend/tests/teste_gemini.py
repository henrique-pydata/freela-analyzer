import os

import pytest


@pytest.mark.skipif(
    os.getenv("RUN_GEMINI_TESTS") != "1",
    reason="Teste externo do Gemini desativado por padrão.",
)
def test_gemini_smoke() -> None:
    from dotenv import load_dotenv
    from google import genai

    load_dotenv()
    chave = os.getenv("GEMINI_API_KEY")
    if not chave:
        pytest.skip("GEMINI_API_KEY não configurada.")

    client = genai.Client(api_key=chave)
    resposta = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
        contents="Responda apenas: OK",
    )
    assert (resposta.text or "").strip()
