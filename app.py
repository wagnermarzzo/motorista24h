from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import os
import math
import requests

app = Flask(__name__)
app.secret_key = "motorista24h"

ADMIN_USER = "Troia"
ADMIN_PASS = "88691553"

EMPRESA_TESTE_USER = "Wagner"
EMPRESA_TESTE_PASS = "88691553"

UPLOAD = "static/uploads"

if os.path.exists(UPLOAD) and not os.path.isdir(UPLOAD):
    os.remove(UPLOAD)

os.makedirs(UPLOAD, exist_ok=True)


def db():
    return sqlite3.connect("database.db")


def init_db():

    conn = db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS motoristas(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    cidade TEXT,
    veiculo TEXT,
    telefone TEXT,
    lat REAL,
    lon REAL,
    saldo REAL DEFAULT 0,
    status TEXT DEFAULT 'offline',
    pix TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS empresas(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    cidade TEXT,
    telefone TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS entregas(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coleta TEXT,
    entrega TEXT,
    distancia REAL,
    veiculo TEXT,
    valor REAL,
    status TEXT,
    foto TEXT,
    motorista INTEGER
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS saques(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    motorista INTEGER,
    valor REAL,
    status TEXT
    )
    """)

    conn.commit()


init_db()


@app.route("/")
def index():

    conn = db()

    moto = conn.execute("SELECT count(*) FROM motoristas WHERE veiculo='moto'").fetchone()[0]
    carro = conn.execute("SELECT count(*) FROM motoristas WHERE veiculo='carro'").fetchone()[0]
    van = conn.execute("SELECT count(*) FROM motoristas WHERE veiculo='van'").fetchone()[0]

    return render_template("index.html", moto=moto, carro=carro, van=van)


@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        usuario = request.form["usuario"]
        senha = request.form["senha"]

        if usuario == ADMIN_USER and senha == ADMIN_PASS:
            session["admin"] = True
            return redirect("/admin")

        if usuario == EMPRESA_TESTE_USER and senha == EMPRESA_TESTE_PASS:
            session["empresa"] = 999
            return redirect("/empresa")

        conn = db()

        motorista = conn.execute(
            "SELECT * FROM motoristas WHERE telefone=?",
            (usuario,)
        ).fetchone()

        empresa = conn.execute(
            "SELECT * FROM empresas WHERE telefone=?",
            (usuario,)
        ).fetchone()

        if motorista:
            session["motorista"] = motorista[0]
            return redirect("/motorista")

        if empresa:
            session["empresa"] = empresa[0]
            return redirect("/empresa")

    return render_template("login.html")


@app.route("/empresa", methods=["GET","POST"])
def empresa():

    if request.method == "POST":

        coleta = request.form["coleta"]
        entrega = request.form["entrega"]
        distancia = float(request.form["distancia"])
        veiculo = request.form["veiculo"]

        tabela = {
            "moto": (10,1.5),
            "carro": (15,2),
            "van": (20,2.8)
        }

        base, km = tabela[veiculo]

        valor = base + distancia * km

        conn = db()

        conn.execute("""
        INSERT INTO entregas(coleta,entrega,distancia,veiculo,valor,status)
        VALUES(?,?,?,?,?,?)
        """,(coleta,entrega,distancia,veiculo,valor,"aguardando"))

        conn.commit()

    conn = db()

    entregas = conn.execute("""
    SELECT * FROM entregas ORDER BY id DESC LIMIT 50
    """).fetchall()

    return render_template("dashboard_empresa.html",entregas=entregas)


@app.route("/motorista", methods=["GET","POST"])
def motorista():

    if request.method == "POST":

        entrega_id = request.form["id"]
        foto = request.files["foto"]

        path = os.path.join(UPLOAD,foto.filename)

        foto.save(path)

        conn = db()

        conn.execute("""
        UPDATE entregas
        SET foto=?,status='entregue'
        WHERE id=?
        """,(path,entrega_id))

        conn.commit()

    conn = db()

    entregas = conn.execute("""
    SELECT * FROM entregas ORDER BY id DESC LIMIT 50
    """).fetchall()

    saldo = conn.execute("""
    SELECT saldo FROM motoristas WHERE id=?
    """,(session["motorista"],)).fetchone()[0]

    return render_template("dashboard_motorista.html",entregas=entregas,saldo=saldo)


@app.route("/admin")
def admin():

    if "admin" not in session:
        return redirect("/login")

    conn = db()

    motoristas = conn.execute("SELECT * FROM motoristas").fetchall()
    empresas = conn.execute("SELECT * FROM empresas").fetchall()
    entregas = conn.execute("SELECT * FROM entregas").fetchall()
    saques = conn.execute("SELECT * FROM saques").fetchall()

    total = conn.execute("""
    SELECT SUM(valor) FROM entregas WHERE status='entregue'
    """).fetchone()[0] or 0

    return render_template("admin.html",
        motoristas=motoristas,
        empresas=empresas,
        entregas=entregas,
        saques=saques,
        total=total)

if __name__ == "__main__":
    app.run(debug=True)
