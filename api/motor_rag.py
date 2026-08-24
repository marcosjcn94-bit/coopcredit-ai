import os

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Caminhos absolutos baseados na estrutura do seu projeto
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
PASTA_PDFS = os.path.normpath(os.path.join(DIRETORIO_ATUAL, "..", "pdfs_sinteticos"))
DIRETORIO_CHROMA = os.path.join(DIRETORIO_ATUAL, "chroma_db_local")

DESCONTO_POR_SCORE = {
    7.5: 5.0,
    7.0: 10.0,
    6.5: 15.0,
    6.0: 20.0,
}

DESCONTO_MAXIMO_INTERNO = 25.0
DESCONTO_ADICIONAL_AVISTA = 5.0


def calcular_desconto_por_score(score: float) -> float:
    """
    Art. 19-A:
    Define o desconto operacional conforme o score de risco.
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

# ---------------------------------------------------------------------------
# CLASSIFICAÇÃO NORMATIVA
# ---------------------------------------------------------------------------
# Cada PDF é classificado por um trecho do nome do arquivo (case-insensitive).
# hierarquia: 1 = lei complementar (mais forte), 2 = regulamento interno do
# banco, 3 = decreto municipal, 4 = instrução normativa (mais fraca).
# fundamenta_desconto: só normas com isso True podem embasar desconto ao
# devedor. Decreto municipal trata de tributo sobre a operação (não desconto
# ao cliente) e instrução normativa é só procedimental — nenhum dos dois
# fundamenta desconto, mesmo que fale de "base de cálculo" ou "redução".
CLASSIFICACAO_NORMAS = [
    {
        "match": "decreto_municipal",
        "tipo_norma": "decreto_municipal",
        "hierarquia": 3,
        "status": "vigente",
        "fundamenta_desconto": False,
    },
    {
        "match": "instru",  # cobre "Instrução_Normativa..."
        "tipo_norma": "instrucao_normativa",
        "hierarquia": 4,
        "status": "vigente",
        "fundamenta_desconto": False,
    },
    {
        "match": "99",  # Lei_Complementar_Estadual_Fictícia_nº_99 — REVOGADA
        "tipo_norma": "lei_complementar_estadual",
        "hierarquia": 1,
        "status": "revogada",
        "fundamenta_desconto": False,
    },
    {
        "match": "104",  # Lei_Complementar_Estadual_Sintética_nº_104 — VIGENTE
        "tipo_norma": "lei_complementar_estadual",
        "hierarquia": 1,
        "status": "vigente",
        "fundamenta_desconto": True,
    },
    {
        "match": "regulamento_interno",
        "tipo_norma": "regulamento_interno_bancario",
        "hierarquia": 2,
        "status": "vigente",
        "fundamenta_desconto": True,
    },
]

# Metadata "segura" aplicada quando um arquivo não bate com nenhum padrão
# conhecido. Propositalmente NÃO fundamenta desconto — um documento não
# identificado nunca deve virar base legal automática.
METADATA_DESCONHECIDA = {
    "tipo_norma": "desconhecida",
    "hierarquia": 99,
    "status": "indefinido",
    "fundamenta_desconto": False,
}


def classificar_norma(nome_arquivo: str) -> dict:
    """Identifica tipo, hierarquia e vigência da norma a partir do nome do PDF."""
    nome_normalizado = nome_arquivo.lower()
    for regra in CLASSIFICACAO_NORMAS:
        if regra["match"] in nome_normalizado:
            return {
                "tipo_norma": regra["tipo_norma"],
                "hierarquia": regra["hierarquia"],
                "status": regra["status"],
                "fundamenta_desconto": regra["fundamenta_desconto"],
            }
    print(
        f"[AVISO] Arquivo '{nome_arquivo}' não reconhecido pela classificação normativa."
    )
    return dict(METADATA_DESCONHECIDA)


def inicializar_banco_vetorial(forcar_reindexacao: bool = False):
    """Lê os PDFs, fatia, anexa metadata normativa e indexa no ChromaDB local."""

    print("Carregando modelo gratuito de Embeddings (HuggingFace)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    banco_existe = os.path.exists(DIRETORIO_CHROMA) and os.listdir(DIRETORIO_CHROMA)
    if banco_existe and not forcar_reindexacao:
        print("Carregando banco vetorial ChromaDB existente...")
        return Chroma(persist_directory=DIRETORIO_CHROMA, embedding_function=embeddings)

    print("Indexando os PDFs sintéticos com metadata normativa...")
    documentos_fatiados = []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " ", ""],
    )

    if not os.path.exists(PASTA_PDFS):
        raise FileNotFoundError(f"A pasta de PDFs não foi encontrada em: {PASTA_PDFS}")

    for arquivo in os.listdir(PASTA_PDFS):
        if not arquivo.endswith(".pdf"):
            continue

        caminho_completo = os.path.join(PASTA_PDFS, arquivo)
        metadata_norma = classificar_norma(arquivo)
        print(
            f"Processando '{arquivo}' -> tipo={metadata_norma['tipo_norma']} "
            f"status={metadata_norma['status']} hierarquia={metadata_norma['hierarquia']}"
        )

        loader = PyPDFLoader(caminho_completo)
        documentos_brutos = loader.load()
        chunks = text_splitter.split_documents(documentos_brutos)

        # Anexa a classificação normativa a CADA chunk, além do que o loader
        # já traz (source, page).
        for chunk in chunks:
            chunk.metadata.update(metadata_norma)
            chunk.metadata["arquivo_origem"] = arquivo

        documentos_fatiados.extend(chunks)

    banco_vetorial = Chroma.from_documents(
        documents=documentos_fatiados,
        embedding=embeddings,
        persist_directory=DIRETORIO_CHROMA,
    )

    print("[SUCESSO] Base vetorial criada e indexada com metadata normativa!")
    return banco_vetorial


def buscar_regras_fiscais(query: str, k: int = 4) -> str:
    """
    Busca semântica (RAG) restrita a normas que:
    - estão vigentes (exclui automaticamente a LC 99, revogada);
    - efetivamente fundamentam desconto ao devedor (exclui decreto municipal
      e instrução normativa, que tratam de outros assuntos).

    Resultados são ordenados por hierarquia normativa (lei > regulamento
    interno) antes de montar o contexto final.
    """
    banco = inicializar_banco_vetorial()

    filtro_normativo = {
        "$and": [
            {"status": {"$eq": "vigente"}},
            {"fundamenta_desconto": {"$eq": True}},
        ]
    }

    resultados = banco.similarity_search(query, k=k, filter=filtro_normativo)

    # Ordena por hierarquia (1 = lei complementar vem antes do regulamento
    # interno do banco), mesmo que a similaridade semântica tenha retornado
    # em outra ordem.
    resultados_ordenados = sorted(
        resultados, key=lambda doc: doc.metadata.get("hierarquia", 99)
    )

    blocos = []
    for doc in resultados_ordenados:
        cabecalho = f"[{doc.metadata.get('tipo_norma', 'norma')} — {doc.metadata.get('arquivo_origem', '?')}]"
        blocos.append(f"{cabecalho}\n{doc.page_content}")

    return "\n\n---\n\n".join(blocos)


def buscar_contexto_tributario(query: str, k: int = 4) -> str:
    """
    Busca separada para questões tributárias/procedimentais (ex: REMTRC
    municipal, formulários do PAF) — quando o caso exigir esse contexto,
    sem misturar com a decisão de desconto ao devedor.
    """
    banco = inicializar_banco_vetorial()
    resultados = banco.similarity_search(query, k=k)
    blocos = [
        f"[{doc.metadata.get('tipo_norma', 'norma')} — status: {doc.metadata.get('status', '?')}]\n{doc.page_content}"
        for doc in resultados
    ]
    return "\n\n---\n\n".join(blocos)

def calcular_desconto_final(
    score: float,
    pagamento_avista: bool,
) -> dict:

    desconto_score = calcular_desconto_por_score(score)

    if desconto_score == 0:
        return {
            "desconto_score": 0.0,
            "adicional_avista": 0.0,
            "desconto_final": 0.0,
        }

    adicional_avista = (
        DESCONTO_ADICIONAL_AVISTA
        if pagamento_avista
        else 0.0
    )

    desconto_final = min(
        desconto_score + adicional_avista,
        30.0,
    )

    return {
        "desconto_score": desconto_score,
        "adicional_avista": adicional_avista,
        "desconto_final": desconto_final,
    }
    
TETO_LEGAL_ATE_12_PARCELAS = 33.33
TETO_OPERACIONAL_INTERNO = 25.0
ADICIONAL_LIQUIDACAO_AVISTA = 5.0
TETO_AVISTA = 30.0
