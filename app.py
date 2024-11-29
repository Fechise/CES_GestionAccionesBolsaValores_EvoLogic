from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = "7C6UMRE9EL8UA0XL" 

users = {}
compras = []

API_KEY = "7C6UMRE9EL8UA0XL"

# Ruta para mostrar la página de inicio
@app.route("/")
def index():
    if "user" in session:
        return render_template("index.html", compras=compras, user=session["user"])
    return redirect(url_for("login"))

# Ruta para la página de login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        if email in users and users[email]["password"] == password:
            session["user"] = email
            return redirect(url_for("index"))
        return "Usuario o contraseña incorrecta", 401
    return render_template("login.html")

# Ruta para la página de registro
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        name = request.form["name"]
        if email in users:
            return "El usuario ya existe", 400
        users[email] = {"name": name, "password": password}
        return redirect(url_for("login"))
    return render_template("register.html")

# Ruta para realizar compras
@app.route("/comprar", methods=["POST"])
def comprar():
    if "user" not in session:
        return redirect(url_for("login"))

    empresa = request.form["empresa"].upper()
    cantidad = int(request.form["cantidad"])
    fecha_compra = datetime.now()

    # Obtener precio de compra usando la API
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={empresa}&interval=5min&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()

    try:
        last_refreshed = list(data["Time Series (5min)"].keys())[0]
        precio_compra = float(data["Time Series (5min)"][last_refreshed]["4. close"])
    except KeyError:
        precio_compra = 0  # Si no se puede obtener el precio, se asigna 0

    compras.append({
        "empresa": empresa,
        "cantidad_acciones": cantidad,
        "fecha_compra": fecha_compra,
        "precio_compra": precio_compra
    })
    return redirect(url_for("index"))

# API para obtener datos de acciones
@app.route("/api/daily-stock-data")
def get_stock_data():
    symbol = request.args.get("symbol")
    if not symbol:
        return jsonify({"error": "El símbolo es obligatorio"}), 400

    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()

    if "Error Message" in data:
        return jsonify({"error": "Símbolo no válido o error en la API"}), 400

    try:
        time_series = data["Time Series (Daily)"]
        result = [
            {
                "date": date,
                "open": values["1. open"],
                "high": values["2. high"],
                "low": values["3. low"],
                "close": values["4. close"],
                "volume": values["5. volume"]
            }
            for date, values in time_series.items()
        ]
        return jsonify(result[:10])  # Retornar los últimos 10 días
    except KeyError:
        return jsonify({"error": "Error al procesar los datos"}), 500

# Ruta para ver las compras con detalles
@app.route("/compras")
def mostrar_compras():
    if "user" not in session:
        return redirect(url_for("login"))

    detalles = []
    for compra in compras:
        # Llamar a la API para obtener el precio actual
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={compra['empresa']}&interval=5min&apikey={API_KEY}"
        response = requests.get(url)
        data = response.json()

        try:
            # Obtener el precio más reciente
            last_refreshed = list(data["Time Series (5min)"].keys())[0]
            precio_actual = float(data["Time Series (5min)"][last_refreshed]["4. close"])
        except KeyError:
            precio_actual = 0  # Si hay un error, asignar 0 o manejar como desees

        # Calcular porcentaje de ganancia/pérdida
        precio_compra = compra["precio_compra"]
        porcentaje_ganancia = ((precio_actual - precio_compra) / precio_compra) * 100 if precio_compra > 0 else 0

        detalles.append({
            "empresa": compra["empresa"],
            "cantidad_acciones": compra["cantidad_acciones"],
            "precio_actual": precio_actual,
            "porcentaje_ganancia": round(porcentaje_ganancia, 2)
        })

    return render_template("compras.html", compras=compras, detalles=detalles)

# Ruta para logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
