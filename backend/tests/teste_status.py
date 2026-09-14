from backend.src.scraper.scraper import detectar_status_projeto


class PaginaFake:
    def __init__(self, botoes: list[str] | None = None) -> None:
        self.botoes = botoes or []

    def locator(self, _seletor: str):
        return self

    def all_inner_texts(self) -> list[str]:
        return self.botoes


def test_detecta_cancelamento_por_texto() -> None:
    assert detectar_status_projeto(
        PaginaFake(),
        "Este projeto foi cancelado pela moderação.",
    ) == "CANCELADO"


def test_detecta_reprovacao_por_texto() -> None:
    assert detectar_status_projeto(
        PaginaFake(),
        "Este projeto foi reprovado pela moderação.",
    ) == "REPROVADO"


def test_detecta_encerramento_por_texto() -> None:
    assert detectar_status_projeto(
        PaginaFake(),
        "Este projeto foi encerrado.",
    ) == "ENCERRADO"


def test_detecta_cancelamento_por_botao() -> None:
    assert detectar_status_projeto(
        PaginaFake(["Enviar proposta", "Cancelado"]),
        "Informações adicionais do projeto.",
    ) == "CANCELADO"


def test_projeto_sem_marcador_continua_ativo() -> None:
    assert detectar_status_projeto(
        PaginaFake(["Enviar proposta"]),
        "Projeto ativo recebendo propostas.",
    ) == "ATIVO"
