from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "motorista24h"

DATABASE = "database.db"

def db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabelas():

    conn = db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS motoristas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        telefone TEXT,
        cidade TEXT,
        veiculo TEXT,
        status TEXT DEFAULT 'offline'
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS entregas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        coleta TEXT,
        entrega TEXT,
        valor REAL,
        status TEXT DEFAULT 'disponivel'
    )
    """)

    conn.commit()

criar_tabelas()

# LOGIN TESTE
EMPRESA_TESTE_USER = "Wagner"
EMPRESA_TESTE_PASS = "88691553"

# PAGINA INICIAL
@app.route("/")
def index():
    return render_template("login.html")

# LOGIN
@app.route("/login", methods=["POST"])
def login():

    usuario = request.form["usuario"]
    senha = request.form["senha"]

    if usuario == EMPRESA_TESTE_USER and senha == EMPRESA_TESTE_PASS:
        session["empresa"] = True
        return redirect("/empresa")

    conn = db()

    motorista = conn.execute(
        "SELECT * FROM motoristas WHERE telefone=?",
        (usuario,)
    ).fetchone()

    if motorista:
        session["motorista"] = motorista["id"]
        return redirect("/motorista")

    return redirect("/")

# CADASTRO MOTORISTA
@app.route("/cadastro_motorista", methods=["GET","POST"])
def cadastro_motorista():

    if request.method == "POST":

        nome = request.form["nome"]
        telefone = request.form["telefone"]
        cidade = request.form["cidade"]
        veiculo = request.form["veiculo"]

        conn = db()

        conn.execute(
        "INSERT INTO motoristas (nome, telefone, cidade, veiculo) VALUES (?, ?, ?, ?)",
        (nome, telefone, cidade, veiculo)
        )

        conn.commit()

        return redirect("/")

    return render_template("cadastro_motorista.html")

# PAINEL MOTORISTA
@app.route("/motorista")
def motorista():

    if "motorista" not in session:
        return redirect("/")

    conn = db()

    entregas = conn.execute(
        "SELECT * FROM entregas WHERE status='disponivel'"
    ).fetchall()

    return render_template("motorista.html", entregas=entregas)

# ALTERAR STATUS MOTORISTA
@app.route("/status_motorista", methods=["POST"])
def status_motorista():

    if "motorista" not in session:
        return redirect("/")

    status = request.form["status"]

    conn = db()

    conn.execute(
    "UPDATE motoristas SET status=? WHERE id=?",
    (status, session["motorista"])
    )

    conn.commit()

    return redirect("/motorista")

if __name__ == "__main__":
    app.run()
