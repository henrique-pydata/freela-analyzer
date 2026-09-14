import os
from typing import Any

from backend.src.database.conexao import conectar

STATUS_ATIVOS = {"PENDENTE", "EXECUTANDO"}
JOB_STALE_MINUTES = max(1, int(os.getenv("SYNC_STALE_MINUTES", "10")))


def _row_to_dict(row: Any) -> dict:
    if row is None:
        return {
            "status": "NUNCA_EXECUTADA",
            "inicio": None,
            "fim": None,
            "erro": None,
            "fase": "AGUARDANDO",
            "progresso_atual": 0,
            "progresso_total": 0,
            "percentual": 0,
            "sucessos": 0,
            "falhas": 0,
            "projeto_atual": None,
            "mensagem": None,
            "ultima_atualizacao": None,
        }

    total = int(row.progresso_total or 0)
    atual = min(int(row.progresso_atual or 0), total) if total else 0
    percentual = round((atual / total) * 100, 1) if total else 0

    return {
        "status": row.status,
        "inicio": row.inicio,
        "fim": row.fim,
        "erro": row.erro,
        "fase": row.fase,
        "progresso_atual": atual,
        "progresso_total": total,
        "percentual": percentual,
        "sucessos": int(row.sucessos or 0),
        "falhas": int(row.falhas or 0),
        "projeto_atual": row.projeto_atual,
        "mensagem": row.mensagem,
        "ultima_atualizacao": row.fim if row.status == "CONCLUIDA" else None,
    }


def obter_status_sincronizacao() -> dict:
    with conectar() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute(
                """
                SELECT status, inicio, fim, erro, fase,
                       progresso_atual, progresso_total,
                       sucessos, falhas, projeto_atual, mensagem
                FROM dbo.sincronizacao_status
                WHERE id = 1;
                """
            )
            return _row_to_dict(cursor.fetchone())
        finally:
            cursor.close()


def solicitar_sincronizacao() -> dict | None:
    """Coloca uma nova execução na fila lógica persistente.

    Retorna None quando já existe uma execução pendente/em andamento.
    """
    with conectar() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute(
                """
                UPDATE dbo.sincronizacao_status
                SET status = 'PENDENTE',
                    inicio = NULL,
                    fim = NULL,
                    erro = NULL,
                    fase = 'AGUARDANDO',
                    progresso_atual = 0,
                    progresso_total = 0,
                    sucessos = 0,
                    falhas = 0,
                    projeto_atual = NULL,
                    mensagem = 'Sincronização aguardando o worker.'
                OUTPUT INSERTED.status, INSERTED.inicio, INSERTED.fim,
                       INSERTED.erro, INSERTED.fase, INSERTED.progresso_atual,
                       INSERTED.progresso_total, INSERTED.sucessos,
                       INSERTED.falhas, INSERTED.projeto_atual,
                       INSERTED.mensagem
                WHERE id = 1
                  AND status NOT IN ('PENDENTE', 'EXECUTANDO');
                """
            )
            row = cursor.fetchone()
            conexao.commit()
            return _row_to_dict(row) if row else None
        finally:
            cursor.close()


def assumir_sincronizacao() -> bool:
    """Adquire o job pendente; recupera também um worker que morreu."""
    with conectar() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute(
                """
                UPDATE dbo.sincronizacao_status
                SET status = 'EXECUTANDO',
                    inicio = COALESCE(inicio, SYSUTCDATETIME()),
                    atualizado_em = SYSUTCDATETIME(),
                    erro = NULL,
                    fase = CASE WHEN fase = 'AGUARDANDO' THEN 'INICIALIZANDO' ELSE fase END,
                    mensagem = CASE WHEN fase = 'AGUARDANDO'
                                    THEN 'Worker iniciou a sincronização.'
                                    ELSE mensagem END
                OUTPUT INSERTED.status
                WHERE id = 1
                  AND (
                      status = 'PENDENTE'
                      OR (
                          status = 'EXECUTANDO'
                          AND atualizado_em IS NOT NULL
                          AND atualizado_em < DATEADD(MINUTE, -?, SYSUTCDATETIME())
                      )
                  );
                """,
                JOB_STALE_MINUTES,
            )
            row = cursor.fetchone()
            conexao.commit()
            return row is not None
        finally:
            cursor.close()


def atualizar_progresso(
    *,
    fase: str,
    progresso_atual: int,
    progresso_total: int,
    sucessos: int,
    falhas: int,
    projeto_atual: str | None,
    mensagem: str | None = None,
) -> None:
    with conectar() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute(
                """
                UPDATE dbo.sincronizacao_status
                SET fase = ?,
                    progresso_atual = ?,
                    progresso_total = ?,
                    sucessos = ?,
                    falhas = ?,
                    projeto_atual = ?,
                    mensagem = ?,
                    atualizado_em = SYSUTCDATETIME()
                WHERE id = 1 AND status = 'EXECUTANDO';
                """,
                fase,
                max(0, progresso_atual),
                max(0, progresso_total),
                max(0, sucessos),
                max(0, falhas),
                projeto_atual,
                mensagem,
            )
            conexao.commit()
        finally:
            cursor.close()


def finalizar_sincronizacao(erro: str | None = None) -> None:
    status = "CONCLUIDA" if erro is None else "FALHOU"
    mensagem = (
        "Sincronização concluída com sucesso."
        if erro is None
        else "Sincronização finalizada com erro inesperado."
    )
    with conectar() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute(
                """
                UPDATE dbo.sincronizacao_status
                SET status = ?,
                    fim = SYSUTCDATETIME(),
                    atualizado_em = SYSUTCDATETIME(),
                    erro = ?,
                    projeto_atual = NULL,
                    mensagem = ?
                WHERE id = 1;
                """,
                status,
                erro[:2000] if erro else None,
                mensagem,
            )
            conexao.commit()
        finally:
            cursor.close()
