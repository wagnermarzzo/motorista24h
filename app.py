from flask import Flask, render_template, request, redirect, session
import sqlite3
import requests

app = Flask(__name__)
app.secret_key = "motorista24h"

GOOGLE_API_KEY = "AIzaSyBnpIgc5k0bckNxjW4y4mDM4W-C9VRP8EQ"

DATABASE = "database.db"


def db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def criar_tabelas():
    conn = db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS empresas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT,
        senha TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS motoristas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT,
        senha TEXT,
        veiculo TEXT,
        latitude REAL,
        longitude REAL,
        status TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS entregas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        empresa_id INTEGER,
        motorista_id INTEGER,
        coleta TEXT,
        destino TEXT,
        distancia REAL,
        valor REAL,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return render_template("login_empresa.html")


@app.route("/login_empresa", methods=["POST"])
def login_empresa():

    email = request.form["email"]
    senha = request.form["senha"]

    conn = db()

    empresa = conn.execute(
        "SELECT * FROM empresas WHERE email=? AND senha=?",
        (email, senha)
    ).fetchone()

    if empresa:
        session["empresa_id"] = empresa["id"]
        return redirect("/dashboard_empresa")

    return "Login inválido"


@app.route("/dashboard_empresa")
def dashboard_empresa():

    conn = db()

    entregas = conn.execute(
        "SELECT * FROM entregas WHERE empresa_id=?",
        (session["empresa_id"],)
    ).fetchall()

    return render_template("dashboard_empresa.html", entregas=entregas)


@app.route("/criar_entrega")
def criar_entrega():
    return render_template("criar_entrega.html")


def calcular_distancia(origem, destino):

    url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origem}&destinations={destino}&key={GOOGLE_API_KEY}"

    r = requests.get(url).json()

    metros = r["rows"][0]["elements"][0]["distance"]["value"]

    km = metros / 1000

    return km


def calcular_valor(km, veiculo):

    taxa = {
        "moto": 10,
        "carro": 12,
        "van": 15
    }

    return taxa[veiculo] + (km * 1.5)


@app.route("/salvar_entrega", methods=["POST"])
def salvar_entrega():

    coleta = request.form["coleta"]
    destino = request.form["destino"]
    veiculo = request.form["veiculo"]

    km = calcular_distancia(coleta, destino)

    valor = calcular_valor(km, veiculo)

    conn = db()

    conn.execute(
        "INSERT INTO entregas (empresa_id, coleta, destino, distancia, valor, status) VALUES (?,?,?,?,?,?)",
        (session["empresa_id"], coleta, destino, km, valor, "procurando_motorista")
    )

    conn.commit()

    return redirect("/dashboard_empresa")


if __name__ == "__main__":
    criar_tabelas()
    app.run()
