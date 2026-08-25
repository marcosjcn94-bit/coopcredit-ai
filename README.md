# 🏦 CoopCredit AI - Motor de Renegociação Inteligente

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?logo=streamlit)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)
![Kubernetes](https://img.shields.io/badge/Kubernetes-K8s-326CE5?logo=kubernetes)
![GitHub Actions](https://img.shields.io/badge/CI%2FCD-Active-2088FF?logo=github-actions)

Arquitetura experimental (Prova de Conceito) desenvolvida para análise, auditoria e simulação de renegociação de crédito cooperativo. O projeto integra Processamento de Linguagem Natural (NLP), Visão Computacional, Motor de Regras Determinístico e Orquestração em Nuvem.

## 🎯 Arquitetura da Solução e Governança

Para atender aos rigorosos padrões do mercado financeiro, a IA Generativa não realiza cálculos financeiros. A arquitetura garante rastreabilidade e compliance da seguinte forma:

1. **Visão Computacional (OCR):** Extração automatizada de CPF via documentos de identidade utilizando `EasyOCR` e `OpenCV`.
2. **Motor de Risco Determinístico:** Algoritmo em Python puro que obedece estritamente às normativas da instituição, penalizando reincidências e bonificando amortizações.
3. **RAG Normativo (ChromaDB):** Recuperação de contexto legal utilizando `sentence-transformers` para embasar a decisão.
4. **LLM (Gemini Pro):** Atua exclusivamente na interpretação semântica e na redação do despacho final, bloqueando alucinações numéricas.
5. **Integração e Prontidão para MCP (Model Context Protocol):** A arquitetura de microsserviços (FastAPI) e o isolamento do motor determinístico foram desenhados com o padrão *Agentic*, servindo como base estrutural para adoção do MCP. Isso permite que a API atue como um "Servidor MCP", expondo o banco de dados e as regras de negócio como *Tools* (Ferramentas) padronizadas para qualquer LLM compatível.
6. **Governança de Dados:** Implementação de mascaramento de PII (Personally Identifiable Information) para proteção de dados sensíveis.

## 🚀 Tecnologias Utilizadas

* **Backend & MLOps:** FastAPI, Pytest, LangChain.
* **Inteligência Artificial:** Google Gemini Pro, HuggingFace, ChromaDB.
* **Frontend & Analytics:** Streamlit, Pandas, Altair.
* **Infraestrutura:** Docker, Kubernetes (Manifestos YAML), CI/CD via GitHub Actions.

## ⭕ Integração Contínua (CI/CD)

Este repositório possui uma esteira automatizada (.github/workflows/ci-pipeline.yml). A cada novo push, o GitHub Actions provisiona um ambiente limpo e executa dezenas de testes unitários de regras de negócio, garantindo que nenhuma atualização quebre os tetos operacionais ou normativas.

## 🛠️ Como Executar o Projeto

## 0️⃣ Preparação (Obrigatório)
Clone o repositório:
```bash
git clone https://github.com/marcosjcn94-bit/coopcredit-ai.git
````

**Atenção:** Crie um arquivo chamado `.env` na raiz do projeto e insira a variável `GOOGLE_API_KEY=sua_chave_real_aqui` para ativar o LLM.


## 1️⃣ Escolha sua Abordagem de Orquestração
Execute apenas uma das opções abaixo de acordo com o seu ambiente:

### 🔆 Opção A: Docker Compose (Mais Rápida)
```bash
docker-compose up --build
````

### 🔆 Opção B: Python Local (Nativo)
Requer dois terminais abertos simultaneamente:
````
pip install -r requirements.txt
# Terminal 1:
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
# Terminal 2:
python -m streamlit run interface.py
````

### 🔆 Opção C: Kubernetes (K8s / Minikube)
````
docker build -t coopcredit-api:latest .
docker build -t coopcredit-frontend:latest .
kubectl create secret generic coopcredit-secrets --from-env-file=.env
kubectl apply -f k8s/
kubectl port-forward service/coopcredit-frontend-service 8501:8501
````

## 2️⃣ Teste de Visão Computacional (OCR)
Com a aplicação rodando (acesse http://localhost:8501), utilize o arquivo `cnh_sintetica.jpg` fornecido neste repositório. Faça o upload na interface para simular a extração do CPF e o acionamento do banco de dados relacional.
