import sqlite3

conn = sqlite3.connect("database.db")

c = conn.cursor()

c.execute("""
CREATE TABLE motoristas(
id INTEGER PRIMARY KEY,
nome TEXT,
cidade TEXT,
veiculo TEXT,
telefone TEXT
)
""")

c.execute("""
CREATE TABLE empresas(
id INTEGER PRIMARY KEY,
nome TEXT,
cidade TEXT,
telefone TEXT
)
""")

c.execute("""
CREATE TABLE entregas(
id INTEGER PRIMARY KEY,
coleta TEXT,
entrega TEXT,
distancia REAL,
veiculo TEXT,
valor REAL
)
""")

conn.commit()
