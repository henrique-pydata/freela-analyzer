from typing import Literal

from pydantic import BaseModel, Field


class AnaliseProjeto(BaseModel):
    vale_a_pena: Literal[
        "SIM",
        "NÃO",
        "TALVEZ",
    ]

    score: int = Field(
        ge=0,
        le=100,
    )

    dificuldade: Literal[
        "BAIXA",
        "MÉDIA",
        "ALTA",
    ]

    tecnologias: list[str]
    riscos: list[str]

    prazo_estimado: str

    orcamento_informado: str
    orcamento_justo: str
    faixa_preco: str

    justificativa: str

    pontos_esclarecer: list[str]

    veredito: str