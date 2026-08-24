import re

import cv2
import easyocr
import numpy as np

# Instanciamos o leitor na memória global apenas uma vez (MLOps Best Practice)
# O parâmetro ['pt'] carrega o modelo otimizado para o idioma português.
print("Carregando o modelo de Visão Computacional (EasyOCR)...")
leitor_ocr = easyocr.Reader(["pt"])


def processar_documento_e_extrair_cpf(conteudo_imagem: bytes) -> str:
    """
    Recebe os bytes de uma imagem, converte para matriz matemática (OpenCV)
    e utiliza OCR para extrair o texto. Aplica Regex para encontrar um CPF válido.
    """
    # 1. Conversão dos bytes da API para o formato de imagem do OpenCV
    matriz_numpy = np.frombuffer(conteudo_imagem, np.uint8)
    imagem_cv2 = cv2.imdecode(matriz_numpy, cv2.IMREAD_COLOR)

    if imagem_cv2 is None:
        raise ValueError("A imagem está corrompida ou num formato não suportado.")

    # 2. Extração de Texto via Redes Neurais (EasyOCR)
    resultados = leitor_ocr.readtext(imagem_cv2, detail=0)
    texto_completo = " ".join(resultados)

    # 3. Auditoria do Texto: Busca do Fato Gerador (CPF) via Expressão Regular
    # Mapeia formatos como 123.456.789-00 ou 12345678900
    padrao_cpf = r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"
    match = re.search(padrao_cpf, texto_completo)

    if match:
        # Limpa pontos e traços, mantendo apenas os números para o SQL
        cpf_limpo = re.sub(r"[^\d]", "", match.group(0))
        return cpf_limpo
    else:
        return "CPF NÃO ENCONTRADO"
