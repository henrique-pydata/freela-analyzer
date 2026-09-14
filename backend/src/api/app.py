import logging
import os

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from backend.src.api.rotas import router
from backend.src.database.sincronizacao import obter_status_sincronizacao, solicitar_sincronizacao

logger = logging.getLogger(__name__)


def _cors_origins() -> list[str]:
    valor = os.getenv("FREELA_CORS_ORIGINS", "")
    if not valor.strip():
        return []
    return [item.strip() for item in valor.split(",") if item.strip()]


app = FastAPI(
    title="Freela Analyzer API",
    description="API do Freela Analyzer.",
    version="2.0.0",
)

origins = _cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.post("/sincronizar", status_code=status.HTTP_202_ACCEPTED, tags=["Sincronização"])
def sincronizar() -> dict:
    try:
        estado = solicitar_sincronizacao()
    except Exception as erro:
        logger.exception("Não foi possível enfileirar sincronização.")
        raise HTTPException(
            status_code=503,
            detail=f"Não foi possível enfileirar a sincronização: {erro}",
        ) from erro

    if estado is None:
        atual = obter_status_sincronizacao()
        raise HTTPException(
            status_code=409,
            detail={
                "mensagem": "Uma sincronização já está pendente ou em andamento.",
                "status": atual,
            },
        )

    return {
        "status": "enfileirada",
        "mensagem": "Sincronização enfileirada. O worker executará o processamento em segundo plano.",
        "sincronizacao": estado,
    }


app.include_router(router)
