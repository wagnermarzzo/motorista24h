from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

motoristas_online = {
    "moto": 42,
    "carro": 18,
    "van": 6
}

@app.route("/")
def index():
    return render_template("index.html", motoristas=motoristas_online)

@app.route("/calcular", methods=["POST"])
def calcular():

    distancia = float(request.form["distancia"])
    veiculo = request.form["veiculo"]

    tabela = {
        "moto": {"base":10, "km":1.5},
        "carro": {"base":15, "km":2},
        "van": {"base":20, "km":2.8}
    }

    preco = tabela[veiculo]["base"] + distancia * tabela[veiculo]["km"]

    return jsonify({"valor": round(preco,2)})

if __name__ == "__main__":
    app.run()
