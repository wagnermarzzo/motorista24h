from flask import Flask, render_template, request, redirect, session
import sqlite3
import requests
import math

app = Flask(__name__)
app.secret_key = "motorista24h"

DATABASE = "database.db"

GOOGLE_API_KEY = "AIzaSyBnpIgc5k0bckNxjW4y4mDM4W-C9VRP8EQ"


def db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# -------------------------------
# CRIAR TABELAS
# -------------------------------
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
        telefone TEXT,
        veiculo TEXT,
        latitude REAL,
        longitude REAL,
        status_online TEXT
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
        valor_motorista REAL,
        taxa_plataforma REAL,
        valor_empresa REAL,
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
    INSERT OR IGNORE INTO admins VALUES (1,'troia','1234')
    """)

    conn.execute("""
    INSERT OR IGNORE INTO empresas VALUES (1,'Wagner','wagner','1234')
    """)

    conn.execute("""
    INSERT OR IGNORE INTO motoristas VALUES
    (1,'Vanderson','vanderson','1234','11965144463','moto,carro,van',-23.185,-46.897,'offline')
    """)

    conn.commit()
    conn.close()


# -------------------------------
# HOME
# -------------------------------
@app.route("/")
def home():
    return render_template("login_empresa.html")


# -------------------------------
# LOGIN EMPRESA
# -------------------------------
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

    return "Login inválido"


# -------------------------------
# LOGIN MOTORISTA
# -------------------------------
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

    return "Login inválido"


# -------------------------------
# DASHBOARD EMPRESA
# -------------------------------
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

    return render_template(
        "dashboard_empresa.html",
        entregas=entregas
    )


# -------------------------------
# DASHBOARD MOTORISTA
# -------------------------------
@app.route("/dashboard_motorista")
def dashboard_motorista():

    if "motorista_id" not in session:
        return redirect("/")

    conn = db()

    entregas = conn.execute(
        "SELECT * FROM entregas WHERE status='procurando_motorista'"
    ).fetchall()

    conn.close()

    return render_template(
        "dashboard_motorista.html",
        entregas=entregas
    )


# -------------------------------
# MOTORISTA ONLINE / OFFLINE
# -------------------------------
@app.route("/status_online/<status>")
def status_online(status):

    if "motorista_id" not in session:
        return redirect("/")

    conn = db()

    conn.execute("""
    UPDATE motoristas
    SET status_online=?
    WHERE id=?
    """,(status,session["motorista_id"]))

    conn.commit()
    conn.close()

    return redirect("/dashboard_motorista")


# -------------------------------
# CALCULAR DISTANCIA GOOGLE
# -------------------------------
def calcular_distancia(origem, destino):

    try:

        url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origem}&destinations={destino}&key={GOOGLE_API_KEY}"

        r = requests.get(url).json()

        metros = r["rows"][0]["elements"][0]["distance"]["value"]

        km = metros / 1000

        return km

    except:

        return 5


# -------------------------------
# CALCULAR VALOR
# -------------------------------
def calcular_valor(km, veiculo):

    taxa = {
        "moto": 10,
        "carro": 12,
        "van": 15
    }

    valor_base = taxa[veiculo] + (km * 1.5)

    taxa_plataforma = valor_base * 0.10

    valor_empresa = valor_base + taxa_plataforma

    return valor_base, taxa_plataforma, valor_empresa


# -------------------------------
# DISTANCIA ENTRE MOTORISTAS
# -------------------------------
def distancia(lat1, lon1, lat2, lon2):

    return math.sqrt(
        (lat1 - lat2) ** 2 +
        (lon1 - lon2) ** 2
    )


def buscar_motoristas_proximos():

    conn = db()

    motoristas = conn.execute("""
    SELECT * FROM motoristas
    WHERE status_online='online'
    """).fetchall()

    conn.close()

    lista = []

    for m in motoristas:

        d = distancia(
            -23.185,
            -46.897,
            m["latitude"],
            m["longitude"]
        )

        lista.append((d, m))

    lista.sort(key=lambda x: x[0])

    return [m[1] for m in lista[:3]]


# -------------------------------
# GERAR LINK WHATSAPP
# -------------------------------
def gerar_link_whatsapp(telefone, coleta, destino, valor, entrega_id):

    mensagem = f"""
🚚 Nova corrida disponível

📍 Coleta: {coleta}
🏁 Destino: {destino}

💰 Ganho: R$ {valor}

Aceitar corrida:
https://motorista24h.onrender.com/aceitar_entrega/{entrega_id}
"""

    mensagem = mensagem.replace(" ", "%20").replace("\n", "%0A")

    return f"https://wa.me/55{telefone}?text={mensagem}"


# -------------------------------
# CRIAR ENTREGA
# -------------------------------
@app.route("/criar_entrega")
def criar_entrega():

    if "empresa_id" not in session:
        return redirect("/")

    return render_template("criar_entrega.html")


# -------------------------------
# SALVAR ENTREGA
# -------------------------------
@app.route("/salvar_entrega", methods=["POST"])
def salvar_entrega():

    if "empresa_id" not in session:
        return redirect("/")

    coleta = request.form["coleta"]
    destino = request.form["destino"]
    veiculo = request.form["veiculo"]

    km = calcular_distancia(coleta, destino)

    valor_motorista, taxa_plataforma, valor_empresa = calcular_valor(km, veiculo)

    conn = db()

    cursor = conn.execute("""
    INSERT INTO entregas
    (empresa_id,coleta,destino,distancia,valor_motorista,taxa_plataforma,valor_empresa,status)
    VALUES (?,?,?,?,?,?,?,?)
    """,(session["empresa_id"],coleta,destino,km,valor_motorista,taxa_plataforma,valor_empresa,"procurando_motorista"))

    entrega_id = cursor.lastrowid

    conn.commit()
    conn.close()

    motoristas = buscar_motoristas_proximos()

    links = []

    for m in motoristas:

        link = gerar_link_whatsapp(
            m["telefone"],
            coleta,
            destino,
            valor_motorista,
            entrega_id
        )

        links.append(link)

    return render_template(
        "dashboard_empresa.html",
        entregas=[],
        links_whatsapp=links
    )


# -------------------------------
# ACEITAR ENTREGA
# -------------------------------
@app.route("/aceitar_entrega/<int:id>")
def aceitar_entrega(id):

    if "motorista_id" not in session:
        return redirect("/")

    conn = db()

    entrega = conn.execute(
        "SELECT * FROM entregas WHERE id=?",
        (id,)
    ).fetchone()

    if entrega["status"] != "procurando_motorista":

        conn.close()

        return "Corrida já aceita"

    conn.execute("""
    UPDATE entregas
    SET motorista_id=?, status='em_entrega'
    WHERE id=?
    """,(session["motorista_id"],id))

    conn.commit()
    conn.close()

    return redirect("/dashboard_motorista")


# -------------------------------
# LOGOUT
# -------------------------------
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


if __name__ == "__main__":
    criar_tabelas()
    app.run(host="0.0.0.0", port=10000)
