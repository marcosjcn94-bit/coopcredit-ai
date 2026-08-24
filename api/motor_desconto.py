"""
motor_desconto.py

Motor determinístico para cálculo do desconto aplicável
em operações de renegociação de crédito.

Regras implementadas:

- Art. 15 da Lei Complementar Sintética:
    Até 33,33% de redução para renegociação com
    liquidação integral em até 12 parcelas.

- Art. 19 do Regulamento Interno:
    Operações com até 18 parcelas podem receber
    redução de até 25%, desde que exista autorização
    normativa específica.

- Matriz interna de risco:
    Score 7,5  ->  5%
    Score 7,0  -> 10%
    Score 6,5  -> 15%
    Score 6,0  -> 20%
    Score <=5,5 -> 25%

- Liquidação à vista:
    adicional de até 5 pontos percentuais,
    limitado ao teto operacional definido.

IMPORTANTE:
Este módulo não utiliza LLM para calcular valores.
"""


from dataclasses import dataclass
from typing import Optional


# ============================================================
# CONSTANTES NORMATIVAS
# ============================================================

# Art. 15 — Lei Complementar Sintética
TETO_LEGAL_ATE_12_PARCELAS = 33.33
LIMITE_PARCELAS_LEI_COMPLEMENTAR = 12


# Art. 19 — Regulamento Interno
TETO_OPERACIONAL_INTERNO = 25.0
LIMITE_PARCELAS_REGULAMENTO = 18


# Art. 19-A — Matriz de modulação por score
ADICIONAL_LIQUIDACAO_AVISTA = 5.0

# Limite operacional máximo quando aplicado o benefício à vista.
TETO_OPERACIONAL_AVISTA = 30.0


# ============================================================
# RESULTADO
# ============================================================

@dataclass
class ResultadoDesconto:
    """
    Resultado completo do motor determinístico de desconto.
    """

    score: float

    quantidade_parcelas: int

    pagamento_avista: bool

    teto_legal: float

    teto_operacional: float

    desconto_por_score: float

    adicional_avista: float

    desconto_final: float

    desconto_aplicavel: bool

    fundamento: str

    motivo: str


# ============================================================
# MATRIZ DE DESCONTO
# ============================================================

def calcular_desconto_por_score(score: float) -> float:
    """
    Art. 19-A

    Determina o percentual de desconto de acordo
    com a pontuação final de risco.

    Quanto menor o risco, maior o benefício.

    Score >= 8,0:
        0%

    Score >= 7,5:
        5%

    Score >= 7,0:
        10%

    Score >= 6,5:
        15%

    Score >= 6,0:
        20%

    Score < 6,0:
        25%
    """

    score = float(score)

    if score >= 8.0:
        return 0.0

    if score >= 7.5:
        return 5.0

    if score >= 7.0:
        return 10.0

    if score >= 6.5:
        return 15.0

    if score >= 6.0:
        return 20.0

    return 25.0


# ============================================================
# VALIDAÇÃO DO ART. 15
# ============================================================

def verificar_artigo_15(
    quantidade_parcelas: int,
) -> bool:
    """
    Verifica a condição de parcelamento prevista no
    Art. 15 da Lei Complementar Sintética.

    Até 12 parcelas:
        pode existir fundamento legal para redução
        de até 33,33%.

    Atenção:
    este teto legal não substitui automaticamente
    o teto operacional interno de 25%.
    """

    return quantidade_parcelas <= LIMITE_PARCELAS_LEI_COMPLEMENTAR


# ============================================================
# VALIDAÇÃO DO ART. 19
# ============================================================

def verificar_artigo_19(
    quantidade_parcelas: int,
) -> bool:
    """
    Verifica se a operação está dentro do limite
    de parcelamento previsto no Art. 19.

    Até 18 parcelas:
        pode receber redução de até 25%,
        desde que exista autorização normativa.
    """

    return quantidade_parcelas <= LIMITE_PARCELAS_REGULAMENTO


# ============================================================
# CÁLCULO DO DESCONTO
# ============================================================

def calcular_desconto(
    score: float,
    quantidade_parcelas: int,
    pagamento_avista: bool = False,
) -> ResultadoDesconto:
    """
    Calcula deterministicamente o desconto aplicável.

    Parâmetros
    ----------
    score:
        Score final produzido pelo motor de risco.

    quantidade_parcelas:
        Número de parcelas da renegociação.

    pagamento_avista:
        True quando houver liquidação integral em
        pagamento único.

    Retorno
    -------
    ResultadoDesconto
        Objeto contendo todos os elementos utilizados
        para a decisão.
    """

    score = float(score)
    quantidade_parcelas = int(quantidade_parcelas)

    if quantidade_parcelas <= 0:
        raise ValueError(
            "A quantidade de parcelas deve ser maior que zero."
        )

    # --------------------------------------------------------
    # Score acima ou igual à linha de corte
    # --------------------------------------------------------

    if score >= 8.0:
        return ResultadoDesconto(
            score=score,
            quantidade_parcelas=quantidade_parcelas,
            pagamento_avista=pagamento_avista,
            teto_legal=TETO_LEGAL_ATE_12_PARCELAS,
            teto_operacional=TETO_OPERACIONAL_INTERNO,
            desconto_por_score=0.0,
            adicional_avista=0.0,
            desconto_final=0.0,
            desconto_aplicavel=False,
            fundamento="Matriz de risco — Art. 19-A",
            motivo=(
                "Score igual ou superior a 8,0. "
                "Operação não elegível ao benefício."
            ),
        )

    # --------------------------------------------------------
    # Verificação dos limites normativos
    # --------------------------------------------------------

    art_15_aplicavel = verificar_artigo_15(
        quantidade_parcelas
    )

    art_19_aplicavel = verificar_artigo_19(
        quantidade_parcelas
    )

    # --------------------------------------------------------
    # O Art. 19 permite até 18 parcelas.
    # Fora disso, não há autorização pelo regulamento.
    # --------------------------------------------------------

    if not art_19_aplicavel:

        return ResultadoDesconto(
            score=score,
            quantidade_parcelas=quantidade_parcelas,
            pagamento_avista=pagamento_avista,
            teto_legal=(
                TETO_LEGAL_ATE_12_PARCELAS
                if art_15_aplicavel
                else 0.0
            ),
            teto_operacional=0.0,
            desconto_por_score=0.0,
            adicional_avista=0.0,
            desconto_final=0.0,
            desconto_aplicavel=False,
            fundamento="Art. 19 — Regulamento Interno",
            motivo=(
                "Quantidade de parcelas superior ao limite "
                "de 18 parcelas previsto no regulamento."
            ),
        )

    # --------------------------------------------------------
    # Desconto definido pela matriz de score
    # --------------------------------------------------------

    desconto_score = calcular_desconto_por_score(score)

    # O Art. 19 estabelece teto operacional de 25%.
    desconto_score = min(
        desconto_score,
        TETO_OPERACIONAL_INTERNO,
    )

    # --------------------------------------------------------
    # Benefício para pagamento à vista
    # --------------------------------------------------------

    adicional_avista = 0.0

    if pagamento_avista:

        adicional_avista = ADICIONAL_LIQUIDACAO_AVISTA

    desconto_final = desconto_score + adicional_avista

    # --------------------------------------------------------
    # Limite máximo à vista
    # --------------------------------------------------------

    desconto_final = min(
        desconto_final,
        TETO_OPERACIONAL_AVISTA,
    )

    # --------------------------------------------------------
    # Garantia adicional de respeito ao teto interno
    # para operações parceladas.
    # --------------------------------------------------------

    if not pagamento_avista:

        desconto_final = min(
            desconto_final,
            TETO_OPERACIONAL_INTERNO,
        )

    # --------------------------------------------------------
    # Fundamento normativo
    # --------------------------------------------------------

    if pagamento_avista:

        fundamento = (
            "Art. 19-A e Art. 19-B — "
            "Matriz de risco e liquidação à vista"
        )

    elif art_15_aplicavel:

        fundamento = (
            "Art. 15 da Lei Complementar Sintética + "
            "Art. 19 do Regulamento Interno"
        )

    else:

        fundamento = (
            "Art. 19 do Regulamento Interno + "
            "Art. 19-A"
        )

    # --------------------------------------------------------
    # Motivo
    # --------------------------------------------------------

    motivo = (
        f"Score {score:.2f} determinou desconto-base de "
        f"{desconto_score:.2f}%. "
    )

    if pagamento_avista:

        motivo += (
            f"Aplicado adicional de "
            f"{adicional_avista:.2f} pontos percentuais "
            f"por liquidação à vista."
        )

    else:

        motivo += (
            "Operação mantida na modalidade parcelada."
        )

    return ResultadoDesconto(
        score=score,
        quantidade_parcelas=quantidade_parcelas,
        pagamento_avista=pagamento_avista,
        teto_legal=(
            TETO_LEGAL_ATE_12_PARCELAS
            if art_15_aplicavel
            else 0.0
        ),
        teto_operacional=TETO_OPERACIONAL_INTERNO,
        desconto_por_score=desconto_score,
        adicional_avista=adicional_avista,
        desconto_final=desconto_final,
        desconto_aplicavel=True,
        fundamento=fundamento,
        motivo=motivo,
    )


# ============================================================
# FUNÇÃO AUXILIAR PARA A INTERFACE / API
# ============================================================

def resultado_para_dict(
    resultado: ResultadoDesconto,
) -> dict:
    """
    Converte o resultado para um dicionário simples,
    facilitando integração com Streamlit, FastAPI,
    schemas Pydantic ou agente LLM.
    """

    return {
        "score": resultado.score,
        "quantidade_parcelas": resultado.quantidade_parcelas,
        "pagamento_avista": resultado.pagamento_avista,
        "teto_legal": resultado.teto_legal,
        "teto_operacional": resultado.teto_operacional,
        "desconto_por_score": resultado.desconto_por_score,
        "adicional_avista": resultado.adicional_avista,
        "desconto_final": resultado.desconto_final,
        "desconto_aplicavel": resultado.desconto_aplicavel,
        "fundamento": resultado.fundamento,
        "motivo": resultado.motivo,
    }