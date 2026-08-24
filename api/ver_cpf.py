import os
import sqlite3

caminho = (
    "api/dados_sicredi.db"
    if os.path.exists("api/dados_sicredi.db")
    else "dados_sicredi.db"
)
conn = sqlite3.connect(caminho)
cpf = conn.execute("SELECT cpf FROM operacoes_credito LIMIT 1").fetchone()[0]
print(f"\n✅ USE ESTE CPF NO PAINT: {cpf}\n")
