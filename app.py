from flask import Flask, render_template, request, session
import sqlite3
import requests
import random
import os

app = Flask(__name__)
app.secret_key = "motorista24h"

DATABASE = "database.db"

# =================================
# CONFIGURAÇÕES
# =================================

GOOGLE_API_KEY = "AIzaSyBnpIgc5k0bckNxjW4y4mDM4W-C9VRP8EQ"

# modo teste evita usar google maps
MODO_TESTE = True


# =================================
# BANCO DE DADOS
# =================================

def db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def criar_tabelas():

    conn = db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS corridas (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        cnpj TEXT,
        empresa TEXT,
        telefone TEXT,

        origem TEXT,
        destino TEXT,

        veiculo TEXT,

        distancia REAL,

        valor_total REAL,

        codigo_confirmacao TEXT,

        status TEXT

    )
    """)

    conn.commit()
    conn.close()


criar_tabelas()


# =================================
# VALIDAR CNPJ
# =================================

def validar_cnpj(cnpj):

    url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}"

    try:

        r = requests.get(url)

        if r.status_code == 200:

            data = r.json()

            empresa = data.get("razao_social", "Empresa")

            return True, empresa

        return False, None

    except:
        return False, None


# =================================
# CALCULAR DISTANCIA
# =================================

def calcular_distancia(origem, destino):

    if MODO_TESTE:
        return random.randint(3, 25)

    url = "https://maps.googleapis.com/maps/api/distancematrix/json"

    params = {
        "origins": origem,
        "destinations": destino,
        "key": GOOGLE_API_KEY,
        "language": "pt-BR"
    }

    response = requests.get(url, params=params)

    data = response.json()

    distancia_metros = data["rows"][0]["elements"][0]["distance"]["value"]

    distancia_km = distancia_metros / 1000

    return round(distancia_km, 2)


# =================================
# CALCULAR VALOR
# =================================

def calcular_valor(distancia, veiculo):

    taxa_fixa = {
        "moto": 10,
        "carro": 12,
        "van": 15
    }

    valor_km = 1.50

    base = taxa_fixa[veiculo] + (distancia * valor_km)

    taxa_site = base * 0.10

    total = base + taxa_site

    return round(total, 2)


# =================================
# PAGINA INICIAL
# =================================

@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":

        cnpj = request.form["cnpj"]
        telefone = request.form["telefone"]
        origem = request.form["origem"]
        destino = request.form["destino"]
        veiculo = request.form["veiculo"]

        valido, empresa = validar_cnpj(cnpj)

        if not valido:
            return "CNPJ inválido"

        distancia = calcular_distancia(origem, destino)

        valor = calcular_valor(distancia, veiculo)

        codigo = str(random.randint(1000, 9999))

        conn = db()

        conn.execute(
            """
            INSERT INTO corridas
            (cnpj, empresa, telefone, origem, destino, veiculo, distancia, valor_total, codigo_confirmacao, status)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            """,
            (
                cnpj,
                empresa,
                telefone,
                origem,
                destino,
                veiculo,
                distancia,
                valor,
                codigo,
                "aguardando_confirmacao"
            )
        )

        conn.commit()
        conn.close()

        session["codigo"] = codigo

        return render_template(
            "confirmar_codigo.html",
            valor=valor,
            distancia=distancia,
            codigo=codigo
        )

    return render_template("index.html")


# =================================
# CONFIRMAR CODIGO
# =================================

@app.route("/confirmar", methods=["POST"])
def confirmar():

    codigo_digitado = request.form["codigo"]

    if codigo_digitado == session.get("codigo"):

        conn = db()

        conn.execute(
            """
            UPDATE corridas
            SET status = 'aguardando_motorista'
            WHERE codigo_confirmacao = ?
            """,
            (codigo_digitado,)
        )

        conn.commit()
        conn.close()

        return render_template("sucesso.html")

    return "Código incorreto"


# =================================
# VER CORRIDAS (PAINEL TESTE)
# =================================

@app.route("/corridas")
def corridas():

    conn = db()

    corridas = conn.execute(
        "SELECT * FROM corridas ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template("corridas.html", corridas=corridas)


# =================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
