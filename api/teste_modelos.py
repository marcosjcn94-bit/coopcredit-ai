import json
import os
import urllib.request

from dotenv import load_dotenv

load_dotenv()
CHAVE = os.getenv("GOOGLE_API_KEY")

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={CHAVE}"

try:
    print("Consultando os servidores do Google...")
    req = urllib.request.urlopen(url)
    dados = json.loads(req.read())

    print("\n=== MODELOS LIBERADOS NA SUA CHAVE ===")
    for modelo in dados.get("models", []):
        # Filtra apenas os modelos que conseguem gerar texto/decisões
        if "generateContent" in modelo.get("supportedGenerationMethods", []):
            # Remove o prefixo 'models/' para deixar o nome limpo
            nome_limpo = modelo["name"].replace("models/", "")
            print(f"- {nome_limpo}")
    print("======================================\n")

except Exception as e:
    print(f"Erro na requisição: {e}")
