import requests
import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
import os

st.set_page_config(
    page_title="CoopCredit AI",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🏦 CoopCredit AI")

st.markdown(
    """
    ### Plataforma de Inteligência Artificial para Crédito Cooperativo

    **Visão Computacional · NLP · LLMs · RAG · Motor de Regras · 
    Governança e Rastreabilidade**

    Arquitetura experimental para análise e renegociação de operações de
    crédito, integrando processamento de documentos, dados financeiros,
    recuperação de conhecimento normativo e inteligência artificial generativa.

    #### Arquitetura da solução

    **Documento**
    → **OCR / Visão Computacional**
    → **Identificação do Associado**
    → **Dados Financeiros**
    → **Motor Determinístico de Risco**
    → **RAG Normativo**
    → **LLM**
    → **Parecer Auditável**

    > O cálculo de risco é executado por regras determinísticas em Python.
    > O LLM atua na interpretação contextual e geração do parecer,
    > preservando rastreabilidade e separação entre cálculo e linguagem.
    """
)

col1, col2 = st.columns([2, 1])

with col1:
    arquivo_imagem = st.file_uploader(
        "Documento (PNG/JPG)", type=["png", "jpg", "jpeg"]
    )

with col2:
    parcelas_propostas = st.number_input(
        "Nº de Parcelas proposto pelo Associado",
        min_value=1,
        max_value=60,
        value=12
    )

st.markdown("---")
st.subheader("Simulador de Cenários")

col3, col4 = st.columns(2)

with col3:
    garantia_real = st.slider(
        "Garantia Real sobre Saldo Devedor (%)",
        0,
        100,
        0
    )

    valor_ja_pago = st.slider(
        "Valor Original Já Quitado da Dívida (%)",
        0,
        100,
        15
    )

with col4:
    reincidencia = st.number_input(
        "Acordos Rompidos pelo Associado (Histórico)",
        min_value=0,
        max_value=10,
        value=0
    )

    custo_judicial = st.number_input(
        "Custo de Execução Fiscal (R$)",
        min_value=1000,
        value=25000,
        step=1000
    )

# Saldo devedor utilizado na simulação
saldo_devedor_banco = 55000.00

if st.button("Iniciar Auditoria"):

    if arquivo_imagem is not None:

        with st.spinner("Analisando legislação, calculando Score de Risco e emitindo despacho..."):

            arquivos = {
                "documento_identidade": (
                    arquivo_imagem.name,
                    arquivo_imagem.getvalue(),
                    arquivo_imagem.type,
                )
            }

            dados_form = {
                "numero_parcelas": parcelas_propostas,
                "percentual_garantia": garantia_real,
                "custo_judicial": custo_judicial,
                "reincidencia": reincidencia,
                "valor_ja_pago": valor_ja_pago,
            }

            API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api/v1/renegociar")
            resposta = requests.post(
                API_URL,
                files=arquivos,
                data=dados_form,
            )

        if resposta.status_code == 200:

            dados = resposta.json()

            # cáclulo financeiro
            desconto = dados["desconto_concedido"] / 100
            novo_total_sem_juros = saldo_devedor_banco * (1 - desconto)

            # Aplicação da Tabela Price (1.5% a.m) para parcelamento
            taxa = 0.015
            if parcelas_propostas == 1:
                valor_parcela = novo_total_sem_juros
                novo_total_com_juros = novo_total_sem_juros
            else:
                valor_parcela = (novo_total_sem_juros * (taxa * (1 + taxa) ** parcelas_propostas) / ((1 + taxa) ** parcelas_propostas - 1))
                novo_total_com_juros = valor_parcela * parcelas_propostas

            if dados["status_aprovacao"]:
                st.success("✅ Acordo Aprovado pelo Comitê de IA!")
            else:
                st.error("❌ Acordo Reprovado por Alto Risco de Crédito!")

            st.markdown("### 📊 Raio-X e Projeção do Novo Contrato")

            # Primeira Linha
            f1, f2 = st.columns(2)
            f1.metric("Saldo Devedor Atual", f"R$ {saldo_devedor_banco:,.2f}")
            f2.metric("Período de Atraso", f"{dados['dias_atraso']} dias")

            # Segunda Linha
            f3, f4 = st.columns(2)
            f3.metric("Score de Risco", f"{dados['score_final']}")
            f4.metric("Desconto Concedido Autorizado", f"{dados['desconto_concedido']} %")

            # Terceira Linha
            f5, f6 = st.columns(2)
            f5.metric("Novo Saldo Devedor", f"R$ {novo_total_com_juros:,.2f}")
            f6.metric(f"Parcela ({parcelas_propostas}x)", f"R$ {valor_parcela:,.2f}")

            st.markdown("### 📈 Simulação de Cenários (Curva de Juros / 1,5% a.m.)")

            taxa = 0.015
            cenarios_keys = []
            cenarios_values = []
            cenarios_ordem = []

            desconto_avista = min(
                dados['desconto_por_score'] + 5.0,
                30.0
            )

            valor_1x = saldo_devedor_banco * (
                1 - (desconto_avista / 100)
            )

            for n in range(1, 19):

                if n == 1:
                    cenarios_keys.append("1x (À Vista)")
                    cenarios_values.append(round(valor_1x, 2))

                else:
                    pmt = (novo_total_sem_juros * (taxa * (1 + taxa) ** n)
                        / ((1 + taxa) ** n - 1)
                    )

                    cenarios_keys.append(f"{n}x")
                    cenarios_values.append(round(pmt * n, 2))

                cenarios_ordem.append(n)  # garante a ordem real de 1 a 18, sem depender de texto

            df_grafico = pd.DataFrame({
                "Opções de Pagamento": cenarios_keys,
                "Novo Encargo Total do Associado": cenarios_values,
                "Ordem": cenarios_ordem,
            })

            # Separador de milhar em vírgula, sem casas decimais (ex: 41,250)
            df_grafico["Valor Formatado"] = df_grafico[
                "Novo Encargo Total do Associado"
            ].apply(
                lambda x: f"R$ {x:,.0f}"
            )
            # Tabela simplificada para exibição
            df_tabela = df_grafico[
               ["Opções de Pagamento", "Novo Encargo Total do Associado"]
            ].copy()

            # Formatação brasileira: R$ 52.250,00
            df_tabela["Novo Encargo Total do Associado"] = df_tabela[
                "Novo Encargo Total do Associado"
            ].apply(
               lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )

            st.dataframe(
               df_tabela,
               use_container_width=True,
               hide_index=True
            )

            rotulos = alt.Chart(df_grafico).mark_text(
                align="left",
                baseline="middle",
                dy=-10,
                color="white"
            ).encode(
                x=alt.X(
                    "Opções de Pagamento:O",
                    sort=alt.EncodingSortField(
                        field="Ordem",
                        order="ascending"
                    )
                ),
                y=alt.Y(
                    "Novo Encargo Total do Associado:Q"
                ),
                text=alt.Text(
                    "Novo Encargo Total:N"
                ),
            )

            # Oportunidade à Vista (Calcula o score base + 5%, respeitando o teto de 30%)
            if parcelas_propostas > 1 and dados["status_aprovacao"]:

                desconto_avista_simulado = min(
                    dados["desconto_por_score"] + 5.0,
                    30.0
                )

                total_avista_simulado = saldo_devedor_banco * (
                    1 - (desconto_avista_simulado / 100)
                )

                st.success(
                    f"💡 **Simulação de Quitação à Vista:** Com o bônus de liquidação antecipada, "
                    f"o desconto saltaria para **{desconto_avista_simulado}%**. "
                    f"O valor para pagamento único seria de **R$ {total_avista_simulado:,.2f}**."
                )

            with st.expander(
                "📄 Ver Despacho Analítico (Raciocínio da IA)",
                expanded=True
            ):

                st.write(
                    dados["raciocinio_analitico"]
                )

            texto_caixa_azul = f"""**Justificativa Legal / Base Normativa:**

{dados["justificativa_legal"]}

---

**🧮 Memória de Cálculo (Motor Determinístico)**
* **Score Base:** {dados["score_base"]}
* **Atraso (+):** {dados["pontos_atraso"]}
* **Reincidência (+):** {dados["pontos_reincidencia"]}
* **Garantia (+):** {dados["pontos_garantia"]}
* **Boa-fé/Quitado (-):** {dados["reducao_quitado"]}
* **SCORE DE RISCO FINAL:** {dados["score_final"]} / 10.0 (Corte: {dados["linha_corte"]})

**🏁Referência Analítica:** Diretrizes de Risco fundamentadas nos Arts. 5º a 12º do Regulamento Interno Bancário Sintético de Renegociação de Crédito.*

**🔐 Governança de Dados:**
PII protegidos em logs de observabilidade ·
CPF mascarado ·
Rastreabilidade sem exposição de dados sensíveis
"""

            st.info(texto_caixa_azul)

        else:

            st.error(
                f"Erro detalhado da API: {resposta.text}"
            )

    else:

        st.warning(
            "Por favor, anexe a imagem do documento."
        )
