from pydantic import BaseModel, Field

class ParecerLLM(BaseModel):
    raciocinio_analitico: str = Field(
        ...,
        description="Despacho formal explicando os fatores de risco. Não recalcular o score."
    )
    justificativa_legal: str = Field(
        ...,
        description="Citação completa e formal da norma recuperada no RAG."
    )

class ResultadoDescontoSchema(BaseModel):
    """
    Resultado produzido exclusivamente pelo motor determinístico
    de desconto.
    """

    teto_legal: float = Field(
        ...,
        description="Teto legal aplicável à operação."
    )

    teto_operacional: float = Field(
        ...,
        description="Teto operacional previsto no regulamento interno."
    )

    desconto_por_score: float = Field(
        ...,
        description="Desconto definido exclusivamente pela matriz de score."
    )

    adicional_avista: float = Field(
        ...,
        description="Adicional em pontos percentuais por liquidação à vista."
    )

    desconto_final: float = Field(
        ...,
        description="Percentual final de desconto determinado pelo motor."
    )

    desconto_aplicavel: bool = Field(
        ...,
        description="Indica se a operação é elegível ao desconto."
    )

    fundamento: str = Field(
        ...,
        description="Fundamento normativo utilizado pelo motor."
    )

    motivo: str = Field(
        ...,
        description="Explicação determinística do cálculo."
    )


class RespostaRenegociacao(BaseModel):

    raciocinio_analitico: str = Field(
        ...,
        description=(
            "Despacho detalhado com a ponderação dos fatores de risco. "
            "Não utilizar termos técnicos de programação."
        ),
    )

    status_aprovacao: bool = Field(
        ...,
        description="Status determinado pelo motor de risco."
    )

    desconto_concedido: float = Field(
        ...,
        description=(
            "Percentual final determinado pelo motor de desconto. "
            "Nunca calculado pelo LLM."
        ),
    )

    desconto_por_score: float = Field(
        ...,
        description="Desconto-base determinado pela matriz de score."
    )

    adicional_avista: float = Field(
        ...,
        description="Adicional aplicado pela liquidação à vista."
    )

    teto_legal: float = Field(
        ...,
        description="Teto legal aplicável."
    )

    teto_operacional: float = Field(
        ...,
        description="Teto operacional interno."
    )

    quantidade_parcelas: int = Field(
        ...,
        description="Quantidade de parcelas da proposta."
    )

    pagamento_avista: bool = Field(
        ...,
        description="Indica se a proposta prevê liquidação à vista."
    )

    fundamento_desconto: str = Field(
        ...,
        description="Fundamento normativo do desconto."
    )

    justificativa_legal: str = Field(
        ...,
        description="Citação formal da norma utilizada."
    )

    dias_atraso: int = Field(
        ...,
        description="Dias de atraso identificados."
    )

    cpf_processado: str = Field(
        ...,
        description="CPF extraído do documento."
    )

    # -----------------------------
    # Matriz de Score
    # -----------------------------

    score_base: float
    pontos_atraso: float
    pontos_reincidencia: float
    pontos_garantia: float
    reducao_quitado: float
    score_bruto: float
    score_final: float
    linha_corte: float