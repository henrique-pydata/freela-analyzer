from backend.src.scraper.scraper import detectar_status_projeto


def test_arquivo_de_integracao_nao_e_executado_na_coleta() -> None:
    # O teste real de navegador é opt-in em teste_playwright.py.
    assert detectar_status_projeto(type("Pagina", (), {"locator": lambda self, _: self, "all_inner_texts": lambda self: []})(), "Projeto ativo") == "ATIVO"
