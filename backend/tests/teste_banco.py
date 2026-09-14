import os

import pytest


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS") != "1",
    reason="Teste de banco de integração desativado por padrão.",
)
def test_busca_projeto_no_banco() -> None:
    from backend.src.database.conexao import buscar_projeto

    assert buscar_projeto("776222") is not None
