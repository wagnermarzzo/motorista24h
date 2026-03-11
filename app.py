from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import os
import math
import requests

app = Flask(__name__)
app.secret_key = "motorista24h"

ADMIN_USER = "Troia"
ADMIN_PASS = "88691553"

UPLOAD = "static/uploads"

# garante que uploads seja pasta
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


def distancia(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1-lat2)**2 + (lon1-lon2)**2)


def motorista_proximo(lat, lon):

    conn = db()

    motoristas = conn.execute(
        "SELECT * FROM motoristas WHERE status='online'"
    ).fetchall()

    melhor = None
    menor = 999999

    for m in motoristas:

        if m[5] and m[6]:

            d = distancia(lat, lon, m[5], m[6])

            if d < menor:
                menor = d
                melhor = m

    return melhor


@app.route("/")
def index():

    conn = db()

    moto = conn.execute("SELECT count(*) FROM motoristas WHERE veiculo='moto'").fetchone()[0]
    carro = conn.execute("SELECT count(*) FROM motoristas WHERE veiculo='carro'").fetchone()[0]
    van = conn.execute("SELECT count(*) FROM motoristas WHERE veiculo='van'").fetchone()[0]

    return render_template("index.html", moto=moto, carro=carro, van=van)


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        usuario = request.form["usuario"]
        senha = request.form["senha"]

        if usuario == ADMIN_USER and senha == ADMIN_PASS:
            session["admin"] = True
            return redirect("/admin")

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


@app.route("/cadastro_motorista", methods=["GET", "POST"])
def cadastro_motorista():

    if request.method == "POST":

        nome = request.form["nome"]
        cidade = request.form["cidade"]
        veiculo = request.form["veiculo"]
        telefone = request.form["telefone"]

        conn = db()

        conn.execute("""
        INSERT INTO motoristas(nome,cidade,veiculo,telefone)
        VALUES(?,?,?,?)
        """, (nome, cidade, veiculo, telefone))

        conn.commit()

        return redirect("/login")

    return render_template("cadastro_motorista.html")


@app.route("/cadastro_empresa", methods=["GET", "POST"])
def cadastro_empresa():

    if request.method == "POST":

        nome = request.form["nome"]
        cidade = request.form["cidade"]
        telefone = request.form["telefone"]

        conn = db()

        conn.execute("""
        INSERT INTO empresas(nome,cidade,telefone)
        VALUES(?,?,?)
        """, (nome, cidade, telefone))

        conn.commit()

        return redirect("/login")

    return render_template("cadastro_empresa.html")


@app.route("/calcular_distancia", methods=["POST"])
def calcular_distancia():

    try:

        coleta = request.form["coleta"]
        entrega = request.form["entrega"]

        headers = {"User-Agent": "Motorista24H"}

        r1 = requests.get(
            f"https://nominatim.openstreetmap.org/search?q={coleta}&format=json",
            headers=headers,
            timeout=5
        ).json()

        r2 = requests.get(
            f"https://nominatim.openstreetmap.org/search?q={entrega}&format=json",
            headers=headers,
            timeout=5
        ).json()

        lat1 = float(r1[0]["lat"])
        lon1 = float(r1[0]["lon"])
        lat2 = float(r2[0]["lat"])
        lon2 = float(r2[0]["lon"])

        km = ((lat1-lat2)**2 + (lon1-lon2)**2)**0.5 * 111

        return jsonify({
            "km": round(km, 2),
            "lat1": lat1,
            "lon1": lon1,
            "lat2": lat2,
            "lon2": lon2
        })

    except:
        return jsonify({"erro": "Falha ao calcular distância"})


@app.route("/empresa", methods=["GET", "POST"])
def empresa():

    if request.method == "POST":

        coleta = request.form["coleta"]
        entrega = request.form["entrega"]
        distancia = float(request.form["distancia"])
        veiculo = request.form["veiculo"]

        tabela = {
            "moto": (10, 1.5),
            "carro": (15, 2),
            "van": (20, 2.8)
        }

        base, km = tabela[veiculo]
        valor = base + distancia * km

        conn = db()

        conn.execute("""
        INSERT INTO entregas(coleta,entrega,distancia,veiculo,valor,status)
        VALUES(?,?,?,?,?,?)
        """, (coleta, entrega, distancia, veiculo, valor, "aguardando"))

        conn.commit()

    conn = db()

    entregas = conn.execute("""
    SELECT * FROM entregas ORDER BY id DESC LIMIT 50
    """).fetchall()

    return render_template("dashboard_empresa.html", entregas=entregas)


@app.route("/motorista", methods=["GET", "POST"])
def motorista():

    if request.method == "POST":

        entrega_id = request.form["id"]
        foto = request.files["foto"]

        path = os.path.join(UPLOAD, foto.filename)
        foto.save(path)

        conn = db()

        conn.execute("""
        UPDATE entregas
        SET foto=?,status='entregue'
        WHERE id=?
        """, (path, entrega_id))

        conn.commit()

    conn = db()

    entregas = conn.execute("""
    SELECT * FROM entregas ORDER BY id DESC LIMIT 50
    """).fetchall()

    saldo = conn.execute("""
    SELECT saldo FROM motoristas WHERE id=?
    """, (session["motorista"],)).fetchone()[0]

    return render_template(
        "dashboard_motorista.html",
        entregas=entregas,
        saldo=saldo
    )


@app.route("/status_motorista", methods=["POST"])
def status_motorista():

    status = request.form["status"]

    conn = db()

    conn.execute("""
    UPDATE motoristas SET status=? WHERE id=?
    """, (status, session["motorista"]))

    conn.commit()

    return redirect("/motorista")


@app.route("/solicitar_saque", methods=["POST"])
def solicitar_saque():

    valor = request.form["valor"]

    conn = db()

    conn.execute("""
    INSERT INTO saques(motorista,valor,status)
    VALUES(?,?,?)
    """, (session["motorista"], valor, "pendente"))

    conn.commit()

    return redirect("/motorista")


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

    return render_template(
        "admin.html",
        motoristas=motoristas,
        empresas=empresas,
        entregas=entregas,
        saques=saques,
        total=total
    )


if __name__ == "__main__":
    app.run(debug=True)
