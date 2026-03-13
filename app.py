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


# =============================
# CRIAR TABELAS
# =============================
def criar_tabelas():

    conn = db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS empresas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT UNIQUE,
        senha TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS motoristas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT UNIQUE,
        senha TEXT,
        veiculo TEXT,
        telefone TEXT,
        latitude REAL,
        longitude REAL,
        status TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE,
        senha TEXT
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

    # ADMIN
    conn.execute("""
    INSERT OR IGNORE INTO admins (id,usuario,senha)
    VALUES (1,'troia','1234')
    """)

    # EMPRESA
    conn.execute("""
    INSERT OR IGNORE INTO empresas (id,nome,email,senha)
    VALUES (1,'Wagner','wagner','1234')
    """)

    # MOTORISTA
    conn.execute("""
    INSERT OR IGNORE INTO motoristas
    (id,nome,email,senha,veiculo,telefone,latitude,longitude,status)
    VALUES
    (1,'Vanderson','vanderson','1234','moto,carro,van','11965144463',0,0,'disponivel')
    """)

    conn.commit()
    conn.close()


# =============================
# HOME
# =============================
@app.route("/")
def home():
    return render_template("login_empresa.html")


# =============================
# LOGIN EMPRESA
# =============================
@app.route("/login_empresa", methods=["POST"])
def login_empresa():

    email = request.form.get("email")
    senha = request.form.get("senha")

    conn = db()

    empresa = conn.execute(
        "SELECT * FROM empresas WHERE email=? AND senha=?",
        (email, senha)
    ).fetchone()

    conn.close()

    if empresa:
        session["empresa_id"] = empresa["id"]
        return redirect("/dashboard_empresa")

    return "Login empresa inválido"


# =============================
# LOGIN MOTORISTA
# =============================
@app.route("/login_motorista", methods=["POST"])
def login_motorista():

    email = request.form.get("email")
    senha = request.form.get("senha")

    conn = db()

    motorista = conn.execute(
        "SELECT * FROM motoristas WHERE email=? AND senha=?",
        (email, senha)
    ).fetchone()

    conn.close()

    if motorista:
        session["motorista_id"] = motorista["id"]
        return redirect("/dashboard_motorista")

    return "Login motorista inválido"


# =============================
# DASHBOARD EMPRESA
# =============================
@app.route("/dashboard_empresa")
def dashboard_empresa():

    if "empresa_id" not in session:
        return redirect("/")

    conn = db()

    entregas = conn.execute(
        "SELECT * FROM entregas WHERE empresa_id=?",
        (session["empresa_id"],)
    ).fetchall()

    conn.close()

    return render_template("dashboard_empresa.html", entregas=entregas)


# =============================
# DASHBOARD MOTORISTA
# =============================
@app.route("/dashboard_motorista")
def dashboard_motorista():

    if "motorista_id" not in session:
        return redirect("/")

    conn = db()

    entregas = conn.execute(
        "SELECT * FROM entregas WHERE status='procurando_motorista'"
    ).fetchall()

    conn.close()

    return render_template("dashboard_motorista.html", entregas=entregas)


# =============================
# CRIAR ENTREGA
# =============================
@app.route("/criar_entrega")
def criar_entrega():

    if "empresa_id" not in session:
        return redirect("/")

    return render_template("criar_entrega.html")


# =============================
# CALCULAR DISTANCIA GOOGLE
# =============================
def calcular_distancia(origem, destino):

    try:

        url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origem}&destinations={destino}&key={GOOGLE_API_KEY}"

        r = requests.get(url)
        data = r.json()

        metros = data["rows"][0]["elements"][0]["distance"]["value"]

        km = metros / 1000

        return km

    except:
        return 5


# =============================
# CALCULAR VALOR
# =============================
def calcular_valor(km, veiculo):

    taxa = {
        "moto": 10,
        "carro": 12,
        "van": 15
    }

    return taxa.get(veiculo, 10) + (km * 1.5)


# =============================
# SALVAR ENTREGA
# =============================
@app.route("/salvar_entrega", methods=["POST"])
def salvar_entrega():

    if "empresa_id" not in session:
        return redirect("/")

    coleta = request.form.get("coleta")
    destino = request.form.get("destino")
    veiculo = request.form.get("veiculo")

    km = calcular_distancia(coleta, destino)

    valor = calcular_valor(km, veiculo)

    conn = db()

    conn.execute("""
        INSERT INTO entregas
        (empresa_id,coleta,destino,distancia,valor,status)
        VALUES (?,?,?,?,?,?)
    """, (session["empresa_id"], coleta, destino, km, valor, "procurando_motorista"))

    conn.commit()
    conn.close()

    return redirect("/dashboard_empresa")


# =============================
# LOGOUT
# =============================
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# =============================
# START APP
# =============================
if __name__ == "__main__":
    criar_tabelas()
    app.run(host="0.0.0.0", port=10000)
