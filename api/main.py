from typing import Annotated

from api.agente_llm import analisar_renegociacao_com_ia
from api.banco_sql import consultar_dados_cliente
from api.extrator_visao import processar_documento_e_extrair_cpf
from api.motor_desconto import calcular_desconto
from api.motor_rag import buscar_regras_fiscais
from api.motor_score import calcular_score
from api.schemas import RespostaRenegociacao
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

app = FastAPI(title="CoopCredit AI")


@app.post("/api/v1/renegociar", response_model=RespostaRenegociacao)
async def processar_renegociacao(
    documento_identidade: Annotated[UploadFile, File(...)],
    numero_parcelas: Annotated[int, Form(...)] = 1,
    percentual_garantia: Annotated[float, Form(...)] = 0.0, # <--- Alterado aqui
    custo_judicial: Annotated[float, Form(...)] = 0.0,
    reincidencia: Annotated[int, Form(...)] = 0,
    valor_ja_pago: Annotated[float, Form(...)] = 0.0,
    pagamento_avista: Annotated[bool, Form(...)] = False,
):
    if not documento_identidade.filename.lower().endswith((".png", ".jpg", ".jpeg")):
        raise HTTPException(status_code=400, detail="Documento inválido.")

    if numero_parcelas < 1:
        raise HTTPException(
            status_code=400,
            detail="O número de parcelas deve ser maior ou igual a 1.",
        )

    if reincidencia < 0:
        raise HTTPException(
            status_code=400,
            detail="A reincidência não pode ser negativa.",
        )

    if not 0 <= valor_ja_pago <= 100:
        raise HTTPException(
            status_code=400,
            detail="valor_ja_pago deve estar entre 0 e 100 (%).",
        )

    try:
        # 1. OCR -> CPF
        bytes_imagem = await documento_identidade.read()
        cpf_identificado = processar_documento_e_extrair_cpf(bytes_imagem)

        if cpf_identificado == "CPF NÃO ENCONTRADO":
            raise HTTPException(
                status_code=422,
                detail="Não foi possível identificar um CPF no documento.",
            )

        # 2. SQLite -> dados financeiros oficiais do protótipo
        dados_financeiros = consultar_dados_cliente(cpf_identificado)
        if not dados_financeiros:
            raise HTTPException(status_code=404, detail="CPF não encontrado.")

        # 3. PYTHON -> score determinístico
        resultado_score = calcular_score(
            dias_atraso=dados_financeiros["dias_atraso"],
            acordos_rompidos=reincidencia,
            percentual_garantia=percentual_garantia,
            percentual_quitado=valor_ja_pago,
        )
        # 4. Desconto determinístico
        resultado_desconto = calcular_desconto(
            score=resultado_score.score_final,
            quantidade_parcelas=numero_parcelas,
            pagamento_avista=pagamento_avista,
        )

        # 5. RAG -> legislação/política de desconto
        query_busca = (
            f"redução base de cálculo renegociação {numero_parcelas} parcelas mensais"
        )
        contexto_lei = buscar_regras_fiscais(query_busca, k=4)

        # 6. LLM -> somente despacho/fundamentação; score/status já estão fechados
        decisao_final = analisar_renegociacao_com_ia(
            dados_cliente=dados_financeiros,
            contexto_lei=contexto_lei,
            cpf=cpf_identificado,
            numero_parcelas=numero_parcelas,
            percentual_garantia=percentual_garantia,
            custo_judicial=custo_judicial,
            reincidencia=reincidencia,
            valor_ja_pago=valor_ja_pago,
            resultado_score=resultado_score,
            resultado_desconto=resultado_desconto,
            pagamento_avista=pagamento_avista
        )

        return decisao_final

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {e}") from e
