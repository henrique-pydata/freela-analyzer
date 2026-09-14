import json

from backend.src.database.conexao import conectar
from backend.src.database.sincronizacao import obter_status_sincronizacao


def _json_para_lista(valor: str | None) -> list[str]:
    if not valor:
        return []
    try:
        resultado = json.loads(valor)
    except (json.JSONDecodeError, TypeError):
        return [valor]
    return [str(item) for item in resultado] if isinstance(resultado, list) else [str(resultado)]


def _montar_filtros(
    score_minimo: int | None = None,
    vale_a_pena: str | None = None,
    dificuldade: str | None = None,
    projeto_exclusivo: bool | None = None,
    categoria: str | None = None,
) -> tuple[str, list]:
    filtros: list[str] = []
    parametros: list = []
    if score_minimo is not None:
        filtros.append("a.score >= ?"); parametros.append(score_minimo)
    if vale_a_pena is not None:
        filtros.append("a.vale_a_pena = ?"); parametros.append(vale_a_pena)
    if dificuldade is not None:
        filtros.append("a.dificuldade = ?"); parametros.append(dificuldade)
    if projeto_exclusivo is not None:
        filtros.append("p.projeto_exclusivo = ?"); parametros.append(projeto_exclusivo)
    if categoria is not None:
        filtros.append("p.categoria = ?"); parametros.append(categoria)
    return (("WHERE " + " AND ".join(filtros)) if filtros else "", parametros)


def _analise_dict(resultado) -> dict | None:
    if resultado.score is None:
        return None
    return {
        "vale_a_pena": resultado.vale_a_pena,
        "score": resultado.score,
        "dificuldade": resultado.dificuldade,
        "tecnologias": _json_para_lista(resultado.tecnologias),
        "riscos": _json_para_lista(resultado.riscos),
        "prazo_estimado": resultado.prazo_estimado,
        "orcamento_informado": resultado.orcamento_informado,
        "orcamento_justo": resultado.orcamento_justo,
        "faixa_preco": resultado.faixa_preco,
        "justificativa": resultado.justificativa,
        "pontos_esclarecer": _json_para_lista(resultado.pontos_esclarecer),
        "veredito": resultado.veredito,
        "data_analise": resultado.data_analise,
    }


def listar_projetos(
    pagina: int = 1, por_pagina: int = 20, score_minimo: int | None = None,
    vale_a_pena: str | None = None, dificuldade: str | None = None,
    projeto_exclusivo: bool | None = None, categoria: str | None = None,
    ordem: str = "score",
) -> tuple[list[dict], int]:
    offset = (pagina - 1) * por_pagina
    where_sql, parametros = _montar_filtros(score_minimo, vale_a_pena, dificuldade, projeto_exclusivo, categoria)
    if ordem == "recente":
        order_sql = "p.data_coleta DESC, p.id DESC"
    elif ordem == "orcamento":
        order_sql = "TRY_CONVERT(DECIMAL(18,2), REPLACE(REPLACE(REPLACE(REPLACE(p.orcamento,'R$',''),' ',''),'.',''),',','.')) DESC, p.data_coleta DESC"
    else:
        order_sql = "CASE WHEN a.score IS NULL THEN -1 ELSE a.score END DESC, p.data_coleta DESC"

    with conectar() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute(
                f"SELECT COUNT(*) FROM dbo.projetos p LEFT JOIN dbo.analises_ia a ON a.projeto_id = p.id WHERE p.status = 'ATIVO' " + (" AND " + where_sql[6:] if where_sql else ""),
                *parametros,
            )
            total = cursor.fetchone()[0]
            cursor.execute(
                f"""
                SELECT p.id, p.titulo, p.descricao, p.url, p.data_coleta, p.ultima_verificacao,
                       p.status, p.categoria, p.subcategoria, p.orcamento, p.nivel_experiencia,
                       p.visibilidade, p.propostas, p.interessados, p.projeto_exclusivo,
                       a.vale_a_pena, a.score, a.dificuldade, a.tecnologias, a.riscos,
                       a.prazo_estimado, a.orcamento_informado, a.orcamento_justo, a.faixa_preco,
                       a.justificativa, a.pontos_esclarecer, a.veredito, a.data_analise
                FROM dbo.projetos p
                LEFT JOIN dbo.analises_ia a ON a.projeto_id = p.id
                {('WHERE p.status = \'ATIVO\' ' + ('AND ' + where_sql[6:] if where_sql else ''))}
                ORDER BY {order_sql}
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
                """,
                *parametros, offset, por_pagina,
            )
            projetos=[]
            for r in cursor.fetchall():
                projetos.append({
                    "id":r.id,"titulo":r.titulo,"descricao":r.descricao,"url":r.url,
                    "data_coleta":r.data_coleta,"ultima_verificacao":r.ultima_verificacao,"status":r.status,
                    "categoria":r.categoria,"subcategoria":r.subcategoria,"orcamento":r.orcamento,
                    "nivel_experiencia":r.nivel_experiencia,"visibilidade":r.visibilidade,
                    "propostas":r.propostas,"interessados":r.interessados,"projeto_exclusivo":bool(r.projeto_exclusivo),
                    "analise":_analise_dict(r),
                })
            return projetos,total
        finally:
            cursor.close()


def buscar_analise(projeto_id: str) -> dict | None:
    projeto = buscar_projeto_com_analise(projeto_id)
    return projeto.get("analise") if projeto else None


def buscar_projeto_com_analise(projeto_id: str) -> dict | None:
    with conectar() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute(
                """
                SELECT p.id,p.titulo,p.descricao,p.url,p.data_coleta,p.ultima_verificacao,p.status,
                       p.categoria,p.subcategoria,p.orcamento,p.nivel_experiencia,p.visibilidade,
                       p.propostas,p.interessados,p.projeto_exclusivo,
                       a.vale_a_pena,a.score,a.dificuldade,a.tecnologias,a.riscos,a.prazo_estimado,
                       a.orcamento_informado,a.orcamento_justo,a.faixa_preco,a.justificativa,
                       a.pontos_esclarecer,a.veredito,a.data_analise
                FROM dbo.projetos p LEFT JOIN dbo.analises_ia a ON a.projeto_id=p.id
                WHERE p.id=? AND p.status='ATIVO'
                """, projeto_id)
            r=cursor.fetchone()
            if r is None: return None
            return {
                "id":r.id,"titulo":r.titulo,"descricao":r.descricao,"url":r.url,
                "data_publicacao":None,"data_coleta":r.data_coleta,"ultima_verificacao":r.ultima_verificacao,
                "status":r.status,"categoria":r.categoria,"subcategoria":r.subcategoria,
                "orcamento":r.orcamento,"nivel_experiencia":r.nivel_experiencia,"visibilidade":r.visibilidade,
                "propostas":r.propostas,"interessados":r.interessados,"projeto_exclusivo":bool(r.projeto_exclusivo),
                "analise":_analise_dict(r),
            }
        finally:
            cursor.close()


def obter_estatisticas() -> dict:
    with conectar() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM dbo.projetos WHERE status='ATIVO'")
            total=cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM dbo.analises_ia a INNER JOIN dbo.projetos p ON p.id=a.projeto_id WHERE p.status='ATIVO'")
            analisados=cursor.fetchone()[0]
            cursor.execute("SELECT AVG(CAST(a.score AS FLOAT)) FROM dbo.analises_ia a INNER JOIN dbo.projetos p ON p.id=a.projeto_id WHERE p.status='ATIVO'")
            score=cursor.fetchone()[0]
            cursor.execute("SELECT a.vale_a_pena,COUNT(*) FROM dbo.analises_ia a INNER JOIN dbo.projetos p ON p.id=a.projeto_id WHERE p.status='ATIVO' GROUP BY a.vale_a_pena")
            vale={"SIM":0,"NÃO":0,"TALVEZ":0}
            for r in cursor.fetchall(): vale[r[0]]=r[1]
            cursor.execute("SELECT a.dificuldade,COUNT(*) FROM dbo.analises_ia a INNER JOIN dbo.projetos p ON p.id=a.projeto_id WHERE p.status='ATIVO' GROUP BY a.dificuldade")
            dificuldade={"BAIXA":0,"MÉDIA":0,"ALTA":0}
            for r in cursor.fetchall(): dificuldade[r[0]]=r[1]
            sync=obter_status_sincronizacao()
            return {
                "total_projetos":total,"projetos_analisados":analisados,"projetos_pendentes":max(total-analisados,0),
                "score_medio":round(score,2) if score is not None else 0,"vale_a_pena":vale,"dificuldade":dificuldade,
                "ultima_atualizacao":sync["ultima_atualizacao"],
            }
        finally:
            cursor.close()
