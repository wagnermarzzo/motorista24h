from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "motorista24h"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def db():
    return sqlite3.connect("database.db")

def criar_db():

    conn = db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS motoristas(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    cidade TEXT,
    veiculo TEXT,
    telefone TEXT
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
    foto TEXT,
    status TEXT
    )
    """)

    conn.commit()

criar_db()

@app.route("/")
def index():

    conn = db()
    c = conn.cursor()

    moto = c.execute("SELECT count(*) FROM motoristas WHERE veiculo='moto'").fetchone()[0]
    carro = c.execute("SELECT count(*) FROM motoristas WHERE veiculo='carro'").fetchone()[0]
    van = c.execute("SELECT count(*) FROM motoristas WHERE veiculo='van'").fetchone()[0]

    return render_template("index.html", moto=moto, carro=carro, van=van)

@app.route("/cadastro_motorista", methods=["GET","POST"])
def cadastro_motorista():

    if request.method == "POST":

        nome = request.form["nome"]
        cidade = request.form["cidade"]
        veiculo = request.form["veiculo"]
        telefone = request.form["telefone"]

        conn = db()
        conn.execute("INSERT INTO motoristas(nome,cidade,veiculo,telefone) VALUES(?,?,?,?)",
        (nome,cidade,veiculo,telefone))
        conn.commit()

        return redirect("/login")

    return render_template("cadastro_motorista.html")

@app.route("/cadastro_empresa", methods=["GET","POST"])
def cadastro_empresa():

    if request.method == "POST":

        nome = request.form["nome"]
        cidade = request.form["cidade"]
        telefone = request.form["telefone"]

        conn = db()
        conn.execute("INSERT INTO empresas(nome,cidade,telefone) VALUES(?,?,?)",
        (nome,cidade,telefone))
        conn.commit()

        return redirect("/login")

    return render_template("cadastro_empresa.html")

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        telefone = request.form["telefone"]

        conn = db()

        motorista = conn.execute("SELECT * FROM motoristas WHERE telefone=?",(telefone,)).fetchone()
        empresa = conn.execute("SELECT * FROM empresas WHERE telefone=?",(telefone,)).fetchone()

        if motorista:

            session["tipo"]="motorista"
            session["id"]=motorista[0]

            return redirect("/motorista")

        if empresa:

            session["tipo"]="empresa"
            session["id"]=empresa[0]

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
        "moto":(10,1.5),
        "carro":(15,2),
        "van":(20,2.8)
        }

        base,km = tabela[veiculo]

        valor = base + distancia*km

        conn = db()
        conn.execute("""
        INSERT INTO entregas(coleta,entrega,distancia,veiculo,valor,status)
        VALUES(?,?,?,?,?,?)
        """,(coleta,entrega,distancia,veiculo,valor,"aguardando"))

        conn.commit()

    conn = db()
    entregas = conn.execute("SELECT * FROM entregas").fetchall()

    return render_template("dashboard_empresa.html",entregas=entregas)

@app.route("/motorista", methods=["GET","POST"])
def motorista():

    if request.method == "POST":

        entrega_id = request.form["id"]
        foto = request.files["foto"]

        path = os.path.join(UPLOAD_FOLDER,foto.filename)
        foto.save(path)

        conn = db()
        conn.execute("UPDATE entregas SET foto=?,status='entregue' WHERE id=?",(path,entrega_id))
        conn.commit()

    conn = db()
    entregas = conn.execute("SELECT * FROM entregas").fetchall()

    return render_template("dashboard_motorista.html",entregas=entregas)

app.run()
