import os

from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env para a memória
load_dotenv()

from api.motor_score import ResultadoScore
from api.schemas import ParecerLLM, RespostaRenegociacao
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from api.motor_desconto import ResultadoDesconto

def analisar_renegociacao_com_ia(
    dados_cliente: dict,
    contexto_lei: str,
    cpf: str,
    numero_parcelas: int,
    percentual_garantia: float,
    custo_judicial: float,
    reincidencia: int,
    valor_ja_pago: float,
    resultado_score: ResultadoScore,
    resultado_desconto: ResultadoDesconto,
    pagamento_avista: bool,
) -> RespostaRenegociacao:
    """Gera apenas a narrativa e a fundamentação; o score/status vêm do Python."""

    print("Acionando Agente LLM para elaboração do despacho...")

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY não configurada no ambiente.")

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.6-flash",
        temperature=0.1,
        google_api_key=api_key,
    )
    llm_estruturado = llm.with_structured_output(ParecerLLM)

    template_auditoria = """
Você é uma Plataforma Inteligente de Análise e Renegociação de Crédito Cooperativo responsável por redigir
um despacho formal de renegociação.

REGRA FUNDAMENTAL:
O SCORE E O STATUS DE APROVAÇÃO JÁ FORAM CALCULADOS PELO MOTOR
DETERMINÍSTICO EM PYTHON. VOCÊ NÃO PODE RECALCULAR, MODIFICAR OU
CONTESTAR ESSES VALORES.

DADOS DA OPERAÇÃO:
- Saldo Devedor Atual: R$ {saldo}
- Valor Original Já Quitado: {valor_pago}%
- Dias de Atraso: {atraso} dias
- Acordos Anteriores Rompidos: {reincidencia}
- Proposta Atual: {parcelas} parcelas mensais
- Garantia Real: {garantia}
- Custo Estimado de Execução: R$ {custo_jud}

MATRIZ DETERMINÍSTICA CALCULADA PELO PYTHON:
- Score-base: {score_base}
- Pontos por atraso: +{pontos_atraso}
- Pontos por acordos rompidos: +{pontos_reincidencia}
- Pontos por ausência de garantia: +{pontos_garantia}
- Redução pelo percentual quitado: -{reducao_quitado}
- Score bruto: {score_bruto}
- Score final: {score_final}
- Linha de corte: {linha_corte}
- Status determinado pelo motor: {status}

MATRIZ DE DESCONTO CALCULADA PELO PYTHON:

- Teto legal: {teto_legal}%
- Teto operacional: {teto_operacional}%
- Desconto pela matriz de score: {desconto_por_score}%
- Adicional por pagamento à vista: {adicional_avista} pontos percentuais
- Desconto final: {desconto_final}%
- Fundamento: {fundamento_desconto}
- Motivo: {motivo_desconto}

LEGISLAÇÃO / POLÍTICA INTERNA RECUPERADA PELO RAG:
{contexto}

INSTRUÇÕES:
1. Redija um despacho humano, formal e objetivo explicando os fatores
   que aumentaram e reduziram o risco.
2. Use EXATAMENTE o score final fornecido pelo Python.
3. Não invente pontos, pesos, fórmulas ou critérios de risco.
4. Não altere o status fornecido pelo motor.
5. Se o status for REPROVADO, o desconto_concedido deve ser 0.
6. Se o status for APROVADO, utilize o percentual de desconto
   fornecido pelo motor determinístico de desconto.

7. Não calcule ou proponha outro percentual.

8. Utilize o contexto recuperado pelo RAG exclusivamente para
   fundamentar a justificativa legal e verificar a compatibilidade
   normativa da operação.

9. Não crie fundamento legal que não esteja presente no contexto.

10. Na justificativa legal, cite a norma e o artigo/dispositivo
    encontrados no contexto.

11. Não utilize termos de programação no despacho.

REGRA ABSOLUTA SOBRE O DESCONTO:

O percentual de desconto já foi calculado pelo motor determinístico
em Python.

NÃO calcule, altere, arredonde, aumente ou reduza esse percentual.

O campo desconto_concedido NÃO deve ser decidido pelo LLM.

Use exatamente o percentual fornecido pelo motor.
"""

    prompt = PromptTemplate(
        input_variables=[
            "saldo",
            "atraso",
            "parcelas",
            "garantia",
            "custo_jud",
            "reincidencia",
            "valor_pago",
            "contexto",
            "score_base",
            "pontos_atraso",
            "pontos_reincidencia",
            "pontos_garantia",
            "reducao_quitado",
            "score_bruto",
            "score_final",
            "linha_corte",
            "status",
        ],
        template=template_auditoria,
    )

    chain = prompt | llm_estruturado

    status_texto = "APROVADO" if resultado_score.aprovado else "REPROVADO"

    parecer = chain.invoke(
        {
            "saldo": dados_cliente["saldo_devedor"],
            "atraso": dados_cliente["dias_atraso"],
            "parcelas": numero_parcelas,
            "garantia": f"{percentual_garantia}%",
            "custo_jud": custo_judicial,
            "reincidencia": reincidencia,
            "valor_pago": valor_ja_pago,
            "contexto": contexto_lei,
            "score_base": resultado_score.score_base,
            "pontos_atraso": resultado_score.pontos_atraso,
            "pontos_reincidencia": resultado_score.pontos_reincidencia,
            "pontos_garantia": resultado_score.pontos_garantia,
            "reducao_quitado": resultado_score.reducao_quitado,
            "score_bruto": resultado_score.score_bruto,
            "score_final": resultado_score.score_final,
            "linha_corte": 8.0,
            "status": status_texto,
            "teto_legal": resultado_desconto.teto_legal,
            "teto_operacional": resultado_desconto.teto_operacional,
            "desconto_por_score": resultado_desconto.desconto_por_score,
            "adicional_avista": resultado_desconto.adicional_avista,
            "desconto_final": resultado_desconto.desconto_final,
            "fundamento_desconto": resultado_desconto.fundamento,
            "motivo_desconto": resultado_desconto.motivo,
        }
    )

    # Garantia adicional: se o motor reprovar, o desconto nunca passa pelo LLM.
    desconto = (
        resultado_desconto.desconto_final
            if resultado_score.aprovado
                else 0.0
)
    return RespostaRenegociacao(
    raciocinio_analitico=parecer.raciocinio_analitico,

    status_aprovacao=resultado_score.aprovado,

    desconto_concedido=desconto,

    desconto_por_score=resultado_desconto.desconto_por_score,

    adicional_avista=resultado_desconto.adicional_avista,

    teto_legal=resultado_desconto.teto_legal,

    teto_operacional=resultado_desconto.teto_operacional,

    quantidade_parcelas=numero_parcelas,

    pagamento_avista=pagamento_avista,

    fundamento_desconto=resultado_desconto.fundamento,

    justificativa_legal=parecer.justificativa_legal,

    dias_atraso=dados_cliente["dias_atraso"],

    cpf_processado=cpf,

    **resultado_score.as_dict(),

    linha_corte=8.0,
)
