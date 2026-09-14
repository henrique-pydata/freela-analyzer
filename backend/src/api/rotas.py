from fastapi import APIRouter, HTTPException, Query

from backend.src.database.conexao import conectar
from backend.src.database.consultas import (
    buscar_analise,
    buscar_projeto_com_analise,
    listar_projetos,
    obter_estatisticas,
)
from backend.src.database.sincronizacao import obter_status_sincronizacao

router = APIRouter()


@router.get("/health", tags=["Sistema"])
def health() -> dict[str, str]:
    try:
        with conectar() as conexao:
            cursor = conexao.cursor()
            try:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            finally:
                cursor.close()
        return {"status": "online"}
    except Exception as erro:
        raise HTTPException(
            status_code=503,
            detail=f"Banco indisponível: {erro}",
        ) from erro


@router.get("/sincronizacao", tags=["Sincronização"])
def status_sincronizacao() -> dict:
    try:
        return obter_status_sincronizacao()
    except Exception as erro:
        raise HTTPException(
            status_code=503,
            detail=f"Não foi possível consultar a sincronização: {erro}",
        ) from erro


@router.get("/estatisticas", tags=["Sistema"])
def estatisticas() -> dict:
    return obter_estatisticas()


@router.get("/projetos", tags=["Projetos"])
def projetos(
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=20, ge=1, le=100),
    score_minimo: int | None = Query(default=None, ge=0, le=100),
    vale_a_pena: str | None = Query(default=None, pattern="^(SIM|NÃO|TALVEZ)$"),
    dificuldade: str | None = Query(default=None, pattern="^(BAIXA|MÉDIA|ALTA)$"),
    projeto_exclusivo: bool | None = None,
    categoria: str | None = None,
    ordem: str = Query(default="score", pattern="^(score|recente|orcamento)$"),
) -> dict:
    encontrados, total = listar_projetos(
        pagina=pagina,
        por_pagina=por_pagina,
        score_minimo=score_minimo,
        vale_a_pena=vale_a_pena,
        dificuldade=dificuldade,
        projeto_exclusivo=projeto_exclusivo,
        categoria=categoria,
        ordem=ordem,
    )
    return {
        "projetos": encontrados,
        "pagina": pagina,
        "por_pagina": por_pagina,
        "total": total,
    }


@router.get("/projetos/melhores", tags=["Projetos"])
def melhores_projetos(
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=20, ge=1, le=100),
    score_minimo: int = Query(default=70, ge=0, le=100),
) -> dict:
    encontrados, total = listar_projetos(
        pagina=pagina,
        por_pagina=por_pagina,
        score_minimo=score_minimo,
        ordem="score",
    )
    return {
        "projetos": encontrados,
        "pagina": pagina,
        "por_pagina": por_pagina,
        "total": total,
    }


@router.get("/projetos/{projeto_id}/analise", tags=["Análises"])
def analise_projeto(projeto_id: str) -> dict:
    analise = buscar_analise(projeto_id)
    if analise is None:
        raise HTTPException(
            status_code=404,
            detail="Este projeto não possui análise válida ou não está ativo.",
        )
    return analise


@router.get("/projetos/{projeto_id}", tags=["Projetos"])
def detalhe_projeto(projeto_id: str) -> dict:
    projeto = buscar_projeto_com_analise(projeto_id)
    if projeto is None:
        raise HTTPException(
            status_code=404,
            detail="Projeto não encontrado ou não está ativo.",
        )
    return projeto
