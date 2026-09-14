"""Executa todas as migrations SQL do projeto em ordem."""

from __future__ import annotations

import re
from pathlib import Path

import pyodbc

from backend.src.database.conexao import DEFAULT_CONNECTION_STRING

ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "backend" / "sql"


def connection_string() -> str:
    import os

    return os.getenv("FREELA_DB_CONNECTION_STRING", DEFAULT_CONNECTION_STRING)


def split_batches(sql: str) -> list[str]:
    return [
        batch.strip()
        for batch in re.split(r"(?im)^[ \t]*GO[ \t]*(?:--.*)?$", sql)
        if batch.strip()
    ]


def main() -> None:
    migrations = sorted(SQL_DIR.glob("*.sql"))
    if not migrations:
        raise SystemExit(f"Nenhuma migration encontrada em {SQL_DIR}")

    print(f"Aplicando {len(migrations)} migration(s) em {SQL_DIR}")
    with pyodbc.connect(connection_string(), timeout=30) as connection:
        lock_cursor = connection.cursor()
        try:
            lock_cursor.execute(
                """
                DECLARE @result INT;
                EXEC @result = sp_getapplock
                    @Resource = 'FreelaAnalyzerSchemaMigration',
                    @LockMode = 'Exclusive',
                    @LockOwner = 'Session',
                    @LockTimeout = 60000;
                SELECT @result;
                """
            )
            lock_result = int(lock_cursor.fetchone()[0])
            if lock_result < 0:
                raise RuntimeError(
                    f"Não foi possível adquirir o lock de migration (código {lock_result})."
                )
        finally:
            lock_cursor.close()

        for migration in migrations:
            print(f"==> {migration.name}")
            sql = migration.read_text(encoding="utf-8")
            cursor = connection.cursor()
            try:
                for batch in split_batches(sql):
                    cursor.execute(batch)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()

        release_cursor = connection.cursor()
        try:
            release_cursor.execute(
                "EXEC sp_releaseapplock @Resource = 'FreelaAnalyzerSchemaMigration', @LockOwner = 'Session';"
            )
            connection.commit()
        finally:
            release_cursor.close()
    print("Migrações concluídas.")


if __name__ == "__main__":
    main()
