import os
import sqlite3

from validate_docbr import CPF

# Define o caminho do banco de dados dentro da pasta api
CAMINHO_DB = os.path.join(os.path.dirname(__file__), "dados_sicredi.db")


def inicializar_banco_sintetico():
    """Cria a tabela e insere o cliente de teste sintético se não existir."""
    conexao = sqlite3.connect(CAMINHO_DB)
    cursor = conexao.cursor()

    # Criação da tabela de operações de crédito (com a estrutura expandida)
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

    # GERADOR DE CPF FAKE/SINTÉTICO VÁLIDO (Substitui o seu CPF real)
    gerador_cpf = CPF()
    cpf_sintetico = (
        gerador_cpf.generate()
    )  # Gera um CPF com pontuação válido matematicamente

    try:
        cursor.execute(
            """
            INSERT INTO operacoes_credito (
                cpf, nome_cliente, saldo_devedor, dias_atraso, 
                codigo_regulamento, reincidencia, possui_garantia, 
                valor_ja_pago, custo_judicial, score, numero_parcelas
            )
            VALUES (?, 'Cliente Sintético (Teste)', 55000.00, 150, 'REG-001', 1, 1, 5000.00, 200.00, 650, 24)
        """,
            (cpf_sintetico,),
        )
        conexao.commit()
    except sqlite3.IntegrityError:
        # Se já existir, ignoramos
        pass

    conexao.close()


def consultar_dados_cliente(cpf: str) -> dict:
    """Busca os dados financeiros do cliente pelo CPF."""
    conexao = sqlite3.connect(CAMINHO_DB)
    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT nome_cliente, saldo_devedor, dias_atraso, codigo_regulamento, 
               reincidencia, possui_garantia, valor_ja_pago, custo_judicial, score, numero_parcelas 
        FROM operacoes_credito WHERE cpf = ?
    """,
        (cpf,),
    )
    resultado = cursor.fetchone()

    conexao.close()

    if resultado:
        return {
            "nome": resultado[0],
            "saldo_devedor": resultado[1],
            "dias_atraso": resultado[2],
            "codigo_regulamento": resultado[3],
            "reincidencia": resultado[4],
            "possui_garantia": bool(resultado[5]),
            "valor_ja_pago": resultado[6],
            "custo_judicial": resultado[7],
            "score": resultado[8],
            "numero_parcelas": resultado[9],
        }
    return None


# Garante que o banco seja criado assim que este arquivo for importado
inicializar_banco_sintetico()
