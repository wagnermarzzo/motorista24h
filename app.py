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
        telefone TEXT,
        status TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT,
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

    conn.execute("""
    INSERT OR IGNORE INTO admins (id,usuario,senha)
    VALUES (1,'troia','1234')
    """)

    conn.execute("""
    INSERT OR IGNORE INTO empresas (id,nome,email,senha)
    VALUES (1,'Wagner','wagner','1234')
    """)

    conn.execute("""
    INSERT OR IGNORE INTO motoristas 
    (id,nome,email,senha,veiculo,telefone,status)
    VALUES
    (1,'Vanderson','vanderson','1234','moto,carro,van','11965144463','disponivel')
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

    conn.close()

    if empresa:
        session["empresa_id"] = empresa["id"]
        return redirect("/dashboard_empresa")

    return "Login empresa inválido"


@app.route("/login_motorista", methods=["POST"])
def login_motorista():

    email = request.form["email"]
    senha = request.form["senha"]

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


@app.route("/login_admin", methods=["POST"])
def login_admin():

    usuario = request.form["usuario"]
    senha = request.form["senha"]

    conn = db()

    admin = conn.execute(
        "SELECT * FROM admins WHERE usuario=? AND senha=?",
        (usuario, senha)
    ).fetchone()

    conn.close()

    if admin:
        session["admin_id"] = admin["id"]
        return redirect("/dashboard_admin")

    return "Login admin inválido"


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


@app.route("/dashboard_admin")
def dashboard_admin():

    if "admin_id" not in session:
        return redirect("/")

    conn = db()

    empresas = conn.execute("SELECT * FROM empresas").fetchall()
    motoristas = conn.execute("SELECT * FROM motoristas").fetchall()
    entregas = conn.execute("SELECT * FROM entregas").fetchall()

    conn.close()

    return render_template(
        "dashboard_admin.html",
        empresas=empresas,
        motoristas=motoristas,
        entregas=entregas
    )


@app.route("/criar_entrega")
def criar_entrega():

    if "empresa_id" not in session:
        return redirect("/")

    return render_template("criar_entrega.html")


def calcular_distancia(origem, destino):

    try:

        url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origem}&destinations={destino}&key={GOOGLE_API_KEY}"

        r = requests.get(url).json()

        metros = r["rows"][0]["elements"][0]["distance"]["value"]

        km = metros / 1000

        return km

    except:

        return 5


def calcular_valor(km, veiculo):

    taxa = {
        "moto": 10,
        "carro": 12,
        "van": 15
    }

    return taxa[veiculo] + (km * 1.5)


@app.route("/salvar_entrega", methods=["POST"])
def salvar_entrega():

    if "empresa_id" not in session:
        return redirect("/")

    coleta = request.form["coleta"]
    destino = request.form["destino"]
    veiculo = request.form["veiculo"]

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


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


if __name__ == "__main__":
    criar_tabelas()
    app.run(host="0.0.0.0", port=10000)
