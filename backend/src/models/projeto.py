from typing import Literal, TypedDict


StatusProjeto = Literal[
    "ATIVO",
    "CANCELADO",
    "ENCERRADO",
    "REPROVADO",
]


class ProjetoResumo(TypedDict):
    id: str
    titulo: str
    url: str
    projeto_exclusivo: bool


class ProjetoCompleto(ProjetoResumo):
    descricao: str | None
    data_publicacao: str | None
    data_coleta: str
    ultima_verificacao: str
    status: StatusProjeto
    categoria: str | None
    subcategoria: str | None
    orcamento: str | None
    nivel_experiencia: str | None
    visibilidade: str | None
    propostas: str | None
    interessados: str | None
