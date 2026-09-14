import os

import pytest


@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "1",
    reason="Teste Gemini/SQL de integração desativado por padrão.",
)
def test_analise_real_de_projeto() -> None:
    from backend.src.database.conexao import (
        analise_existe,
        buscar_projeto,
        salvar_analise,
    )
    from backend.src.ia.analise import analisar_projeto

    projeto = buscar_projeto("776222")
    if projeto is None:
        pytest.skip("Projeto de integração não existe no banco.")

    if analise_existe(projeto["id"]):
        return

    analise = analisar_projeto(projeto)
    if analise is None:
        pytest.skip("Gemini não retornou uma análise nesta execução.")

    salvar_analise(projeto["id"], analise)
