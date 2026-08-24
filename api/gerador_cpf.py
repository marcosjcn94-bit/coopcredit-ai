import random
import sqlite3

from validate_docbr import CPF

# Inicializa gerador de CPF sintético válido
gerador_cpf = CPF()

# Conecta ao banco de dados SQLite (cria o arquivo se não existir)
conn = sqlite3.connect("dados_sicredi.db")
cursor = conn.cursor()

# Cria a tabela expandida
cursor.execute("""
CREATE TABLE IF NOT EXISTS operacoes_credito (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cpf TEXT UNIQUE NOT NULL,
    nome_cliente TEXT NOT NULL,
    saldo_devedor REAL NOT NULL,
    dias_atraso INTEGER NOT NULL,
    codigo_regulamento TEXT,
    reincidencia INTEGER DEFAULT 0,
    possui_garantia BOOLEAN NOT NULL,
    valor_ja_pago REAL DEFAULT 0.0,
    custo_judicial REAL DEFAULT 0.0,
    score INTEGER NOT NULL,
    numero_parcelas INTEGER NOT NULL
);
""")

# Lista de nomes fictícios para enriquecer o dataset
nomes = [
    "Ana Silva",
    "Carlos Souza",
    "Mariana Santos",
    "João Oliveira",
    "Beatriz Costa",
    "Lucas Pereira",
    "Fernanda Lima",
    "Rafael Almeida",
    "Juliana Ribeiro",
    "Gabriel Martins",
]

# Populando com 50 registros sintéticos de exemplo
print("Gerando dados sintéticos coerentes com o regulamento...")
for i in range(50):
    cpf = gerador_cpf.generate()
    nome = f"{random.choice(nomes)} {i + 1}"
    saldo_devedor = round(random.uniform(1000.0, 50000.0), 2)
    dias_atraso = random.randint(0, 360)
    codigo_regulamento = f"REG-{random.randint(100, 999)}"
    reincidencia = random.choice([0, 1, 2])
    possui_garantia = random.choice([True, False])
    valor_ja_pago = round(saldo_devedor * random.uniform(0.0, 0.3), 2)
    custo_judicial = round(random.uniform(0.0, 2500.0), 2) if dias_atraso > 90 else 0.0
    score = random.randint(300, 950)
    numero_parcelas = random.choice([12, 24, 36, 48, 60])

    try:
        cursor.execute(
            """
            INSERT INTO operacoes_credito (
                cpf, nome_cliente, saldo_devedor, dias_atraso, codigo_regulamento, 
                reincidencia, possui_garantia, valor_ja_pago, custo_judicial, score, numero_parcelas
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                cpf,
                nome,
                saldo_devedor,
                dias_atraso,
                codigo_regulamento,
                reincidencia,
                possui_garantia,
                valor_ja_pago,
                custo_judicial,
                score,
                numero_parcelas,
            ),
        )
    except sqlite3.IntegrityError:
        pass  # Ignora caso gere um CPF duplicado por coincidência

conn.commit()
conn.close()
print("Banco de dados atualizado e populado com sucesso!")
