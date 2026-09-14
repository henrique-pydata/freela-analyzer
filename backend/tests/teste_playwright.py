import os

import pytest


@pytest.mark.skipif(
    os.getenv("RUN_BROWSER_TESTS") != "1",
    reason="Teste externo do Playwright desativado por padrão.",
)
def test_playwright_smoke() -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        navegador = playwright.chromium.launch(headless=True)
        pagina = navegador.new_page()
        pagina.goto("https://www.99freelas.com.br", wait_until="domcontentloaded")
        assert pagina.title()
        navegador.close()
