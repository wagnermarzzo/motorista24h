from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "motorista24h"

def db():
    return sqlite3.connect("database.db")

@app.route("/")
def index():
    return render_template("index.html")

# CADASTRO MOTORISTA

@app.route("/cadastro_motorista", methods=["GET","POST"])
def cadastro_motorista():

    if request.method == "POST":

        nome = request.form["nome"]
        cidade = request.form["cidade"]
        veiculo = request.form["veiculo"]
        telefone = request.form["telefone"]

        conn = db()
        c = conn.cursor()

        c.execute("INSERT INTO motoristas VALUES (NULL,?,?,?,?)",
        (nome,cidade,veiculo,telefone))

        conn.commit()

        return redirect("/login")

    return render_template("cadastro_motorista.html")

# CADASTRO EMPRESA

@app.route("/cadastro_empresa", methods=["GET","POST"])
def cadastro_empresa():

    if request.method == "POST":

        nome = request.form["nome"]
        cidade = request.form["cidade"]
        telefone = request.form["telefone"]

        conn = db()
        c = conn.cursor()

        c.execute("INSERT INTO empresas VALUES (NULL,?,?,?)",
        (nome,cidade,telefone))

        conn.commit()

        return redirect("/login")

    return render_template("cadastro_empresa.html")

# LOGIN

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        telefone = request.form["telefone"]

        conn = db()
        c = conn.cursor()

        motorista = c.execute("SELECT * FROM motoristas WHERE telefone=?",(telefone,)).fetchone()

        empresa = c.execute("SELECT * FROM empresas WHERE telefone=?",(telefone,)).fetchone()

        if motorista:
            session["tipo"] = "motorista"
            session["id"] = motorista[0]
            return redirect("/motorista")

        if empresa:
            session["tipo"] = "empresa"
            session["id"] = empresa[0]
            return redirect("/empresa")

    return render_template("login.html")

# DASHBOARD EMPRESA

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

        valor = base + distancia * km

        conn = db()
        c = conn.cursor()

        c.execute("INSERT INTO entregas VALUES (NULL,?,?,?,?,?)",
        (coleta,entrega,distancia,veiculo,valor))

        conn.commit()

    conn = db()
    entregas = conn.execute("SELECT * FROM entregas").fetchall()

    return render_template("dashboard_empresa.html",entregas=entregas)

# DASHBOARD MOTORISTA

@app.route("/motorista")
def motorista():

    conn = db()
    entregas = conn.execute("SELECT * FROM entregas").fetchall()

    return render_template("dashboard_motorista.html",entregas=entregas)

app.run()
