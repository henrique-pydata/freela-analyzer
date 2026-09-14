import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import pyodbc
from dotenv import load_dotenv

from backend.src.models.analise import AnaliseProjeto
from backend.src.models.projeto import ProjetoCompleto, ProjetoResumo

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

DEFAULT_CONNECTION_STRING = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=FreelaAnalyzer;"
    "Trusted_Connection=yes;"
    "Encrypt=no;"
    "TrustServerCertificate=yes;"
    "Connection Timeout=30;"
)

PROJETO_COLUNAS = (
    "id, titulo, descricao, url, data_coleta, ultima_verificacao, status, "
    "categoria, subcategoria, orcamento, nivel_experiencia, visibilidade, "
    "propostas, interessados, projeto_exclusivo"
)


def _connection_string() -> str:
    return os.getenv("FREELA_DB_CONNECTION_STRING", DEFAULT_CONNECTION_STRING)


@contextmanager
def conectar() -> Iterator[pyodbc.Connection]:
    conexao = pyodbc.connect(_connection_string(), timeout=30)
    try:
        yield conexao
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def projeto_existe(projeto_id: str) -> bool:
    with conectar() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute("SELECT 1 FROM dbo.projetos WHERE id = ?", projeto_id)
            return cursor.fetchone() is not None
        finally:
            cursor.close()


def salvar_projeto(projeto: ProjetoCompleto) -> None:
    with conectar() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO dbo.projetos (
                    id, titulo, descricao, url, data_coleta, ultima_verificacao,
                    status, categoria, subcategoria, orcamento, nivel_experiencia,
                    visibilidade, propostas, interessados, projeto_exclusivo
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                projeto["id"], projeto["titulo"], projeto["descricao"],
                projeto["url"], projeto["data_coleta"], projeto["ultima_verificacao"],
                projeto["status"], projeto["categoria"], projeto["subcategoria"],
                projeto["orcamento"], projeto["nivel_experiencia"], projeto["visibilidade"],
                projeto["propostas"], projeto["interessados"], projeto["projeto_exclusivo"],
            )
            conexao.commit()
        finally:
            cursor.close()


def buscar_projeto(projeto_id: str) -> ProjetoCompleto | None:
    with conectar() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute(
                f"SELECT {PROJETO_COLUNAS} FROM dbo.projetos WHERE id = ?",
                projeto_id,
            )
            resultado = cursor.fetchone()
            if resultado is None:
                return None
            return {
                "id": resultado.id,
                "titulo": resultado.titulo,
                "descricao": resultado.descricao,
                "url": resultado.url,
                "data_publicacao": None,
                "data_coleta": resultado.data_coleta,
                "ultima_verificacao": resultado.ultima_verificacao,
                "status": resultado.status,
                "categoria": resultado.categoria,
                "subcategoria": resultado.subcategoria,
                "orcamento": resultado.orcamento,
                "nivel_experiencia": resultado.nivel_experiencia,
                "visibilidade": resultado.visibilidade,
                "propostas": resultado.propostas,
                "interessados": resultado.interessados,
                "projeto_exclusivo": bool(resultado.projeto_exclusivo),
            }
        finally:
            cursor.close()


def listar_projetos_para_verificacao() -> list[ProjetoResumo]:
    with conectar() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute(
                """
                SELECT id, titulo, url, projeto_exclusivo
                FROM dbo.projetos
                WHERE status = 'ATIVO'
                ORDER BY ultima_verificacao ASC, id ASC
                """
            )
            return [
                {
                    "id": r.id,
                    "titulo": r.titulo,
                    "url": r.url,
                    "projeto_exclusivo": bool(r.projeto_exclusivo),
                }
                for r in cursor.fetchall()
            ]
        finally:
            cursor.close()


def atualizar_projeto(projeto: ProjetoCompleto) -> None:
    with conectar() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute(
                """
                UPDATE dbo.projetos
                SET titulo = ?, descricao = ?, ultima_verificacao = ?, status = ?,
                    categoria = ?, subcategoria = ?, orcamento = ?,
                    nivel_experiencia = ?, visibilidade = ?, propostas = ?,
                    interessados = ?, projeto_exclusivo = ?
                WHERE id = ? AND status = 'ATIVO';
                """,
                projeto["titulo"], projeto["descricao"], projeto["ultima_verificacao"],
                projeto["status"], projeto["categoria"], projeto["subcategoria"],
                projeto["orcamento"], projeto["nivel_experiencia"], projeto["visibilidade"],
                projeto["propostas"], projeto["interessados"], projeto["projeto_exclusivo"],
                projeto["id"],
            )
            conexao.commit()
        finally:
            cursor.close()


def remover_projeto(projeto_id: str) -> None:
    with conectar() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute("DELETE FROM dbo.analises_ia WHERE projeto_id = ?", projeto_id)
            cursor.execute("DELETE FROM dbo.projetos WHERE id = ?", projeto_id)
            conexao.commit()
        finally:
            cursor.close()


def analise_existe(projeto_id: str) -> bool:
    with conectar() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute("SELECT 1 FROM dbo.analises_ia WHERE projeto_id = ?", projeto_id)
            return cursor.fetchone() is not None
        finally:
            cursor.close()


def salvar_analise(projeto_id: str, analise: AnaliseProjeto) -> None:
    with conectar() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO dbo.analises_ia (
                    projeto_id, vale_a_pena, score, dificuldade, tecnologias, riscos,
                    prazo_estimado, orcamento_informado, orcamento_justo, faixa_preco,
                    justificativa, pontos_esclarecer, veredito
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                projeto_id,
                analise.vale_a_pena,
                analise.score,
                analise.dificuldade,
                json.dumps(analise.tecnologias, ensure_ascii=False),
                json.dumps(analise.riscos, ensure_ascii=False),
                analise.prazo_estimado,
                analise.orcamento_informado,
                analise.orcamento_justo,
                analise.faixa_preco,
                analise.justificativa,
                json.dumps(analise.pontos_esclarecer, ensure_ascii=False),
                analise.veredito,
            )
            conexao.commit()
        finally:
            cursor.close()
