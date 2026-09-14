from typing import Literal, TypedDict


StatusSincronizacao = Literal["NUNCA_EXECUTADA", "EXECUTANDO", "CONCLUIDA", "FALHOU"]


class StatusSincronizacaoResponse(TypedDict):
    status: StatusSincronizacao
    inicio: str | None
    fim: str | None
    erro: str | None
    ultima_atualizacao: str | None
