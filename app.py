from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import os
import requests

app = Flask(__name__)
app.secret_key="motorista24h"

UPLOAD="static/uploads"
os.makedirs(UPLOAD, exist_ok=True)

ADMIN_USER="Troia"
ADMIN_PASS="88691553"

def db():
    return sqlite3.connect("database.db")

def init_db():

    conn=db()
    c=conn.cursor()

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
    status TEXT,
    foto TEXT
    )
    """)

    conn.commit()

init_db()

@app.route("/")
def index():

    conn=db()

    moto=conn.execute("SELECT count(*) FROM motoristas WHERE veiculo='moto'").fetchone()[0]
    carro=conn.execute("SELECT count(*) FROM motoristas WHERE veiculo='carro'").fetchone()[0]
    van=conn.execute("SELECT count(*) FROM motoristas WHERE veiculo='van'").fetchone()[0]

    return render_template("index.html",moto=moto,carro=carro,van=van)

@app.route("/login",methods=["GET","POST"])
def login():

    if request.method=="POST":

        user=request.form["usuario"]
        senha=request.form["senha"]

        if user==ADMIN_USER and senha==ADMIN_PASS:
            session["admin"]=True
            return redirect("/admin")

        conn=db()

        motorista=conn.execute("SELECT * FROM motoristas WHERE telefone=?",(user,)).fetchone()
        empresa=conn.execute("SELECT * FROM empresas WHERE telefone=?",(user,)).fetchone()

        if motorista:
            session["motorista"]=motorista[0]
            return redirect("/motorista")

        if empresa:
            session["empresa"]=empresa[0]
            return redirect("/empresa")

    return render_template("login.html")

@app.route("/cadastro_motorista",methods=["GET","POST"])
def cadastro_motorista():

    if request.method=="POST":

        nome=request.form["nome"]
        cidade=request.form["cidade"]
        veiculo=request.form["veiculo"]
        telefone=request.form["telefone"]

        conn=db()
        conn.execute("INSERT INTO motoristas(nome,cidade,veiculo,telefone) VALUES(?,?,?,?)",
        (nome,cidade,veiculo,telefone))
        conn.commit()

        return redirect("/login")

    return render_template("cadastro_motorista.html")

@app.route("/cadastro_empresa",methods=["GET","POST"])
def cadastro_empresa():

    if request.method=="POST":

        nome=request.form["nome"]
        cidade=request.form["cidade"]
        telefone=request.form["telefone"]

        conn=db()
        conn.execute("INSERT INTO empresas(nome,cidade,telefone) VALUES(?,?,?)",
        (nome,cidade,telefone))
        conn.commit()

        return redirect("/login")

    return render_template("cadastro_empresa.html")

@app.route("/calcular_distancia",methods=["POST"])
def calcular_distancia():

    coleta=request.form["coleta"]
    entrega=request.form["entrega"]

    url=f"https://nominatim.openstreetmap.org/search?q={coleta}&format=json"
    r1=requests.get(url).json()

    url=f"https://nominatim.openstreetmap.org/search?q={entrega}&format=json"
    r2=requests.get(url).json()

    if not r1 or not r2:
        return jsonify({"erro":"endereço não encontrado"})

    lat1=float(r1[0]["lat"])
    lon1=float(r1[0]["lon"])
    lat2=float(r2[0]["lat"])
    lon2=float(r2[0]["lon"])

    distancia=((lat1-lat2)**2+(lon1-lon2)**2)**0.5*111

    return jsonify({"km":round(distancia,2)})

@app.route("/empresa",methods=["GET","POST"])
def empresa():

    if request.method=="POST":

        coleta=request.form["coleta"]
        entrega=request.form["entrega"]
        distancia=float(request.form["distancia"])
        veiculo=request.form["veiculo"]

        tabela={
        "moto":(10,1.5),
        "carro":(15,2),
        "van":(20,2.8)
        }

        base,km=tabela[veiculo]
        valor=base+distancia*km

        conn=db()
        conn.execute("""
        INSERT INTO entregas(coleta,entrega,distancia,veiculo,valor,status)
        VALUES(?,?,?,?,?,?)
        """,(coleta,entrega,distancia,veiculo,valor,"aguardando"))

        conn.commit()

    conn=db()
    entregas=conn.execute("SELECT * FROM entregas").fetchall()

    return render_template("dashboard_empresa.html",entregas=entregas)

@app.route("/motorista",methods=["GET","POST"])
def motorista():

    if request.method=="POST":

        id=request.form["id"]
        foto=request.files["foto"]

        path=os.path.join(UPLOAD,foto.filename)
        foto.save(path)

        conn=db()
        conn.execute("UPDATE entregas SET foto=?,status='entregue' WHERE id=?",(path,id))
        conn.commit()

    conn=db()
    entregas=conn.execute("SELECT * FROM entregas").fetchall()

    return render_template("dashboard_motorista.html",entregas=entregas)

@app.route("/admin")
def admin():

    if "admin" not in session:
        return redirect("/login")

    conn=db()

    motoristas=conn.execute("SELECT * FROM motoristas").fetchall()
    empresas=conn.execute("SELECT * FROM empresas").fetchall()
    entregas=conn.execute("SELECT * FROM entregas").fetchall()

    return render_template("admin.html",
    motoristas=motoristas,
    empresas=empresas,
    entregas=entregas)

app.run()
