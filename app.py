from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory, flash
import requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = "7C6UMRE9EL8UA0XL" 
API_KEY = "7C6UMRE9EL8UA0XL"
FINNHUB_API_KEY = 'ct4h7u9r01qo7vqammh0ct4h7u9r01qo7vqammhg'

users = {}
compras = []
agrupadas = {}

@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", username=session["name"])

@app.route("/resumen")
def resumen():
    agrupadas.clear()
    for compra in compras:
        empresa = compra["empresa"]
        cantidad_acciones = compra["cantidad_acciones"]
        valor_compra = compra["valor_compra"]
        precio_compra = compra["precio_compra"]

        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={empresa}&interval=5min&apikey={API_KEY}"
        response = requests.get(url)
        data = response.json()

        try:
            last_refreshed = list(data["Time Series (5min)"].keys())[0]
            precio_actual = float(data["Time Series (5min)"][last_refreshed]["4. close"])
        except KeyError:
            flash(f"Error al obtener el precio actual para {empresa}", "error")
            precio_actual = 0

        if empresa in agrupadas:
            agrupadas[empresa]["cantidad_total"] += cantidad_acciones
            agrupadas[empresa]["valor_total"] += valor_compra
        else:
            agrupadas[empresa] = {
                "cantidad_total": cantidad_acciones,
                "valor_total": valor_compra,
                "precio_actual": precio_actual,
                "precio_compra": precio_compra,
            }

    detalles = []
    for empresa, datos in agrupadas.items():
        valor_total = datos["valor_total"]
        precio_actual = datos["precio_actual"]
        cantidad_total = datos["cantidad_total"]
        precio_costo = valor_total / cantidad_total if cantidad_total > 0 else 0

        porcentaje_ganancia = 0
        ganancia_perdida = 0

        if precio_costo > 0:
            porcentaje_ganancia = ((precio_actual - precio_costo) / precio_costo) * 100
            ganancia_perdida = (precio_actual * cantidad_total) - valor_total

        detalles.append({
            "empresa": empresa,
            "cantidad_total": cantidad_total,
            "valor_usd": round(valor_total, 2),
            "precio_costo": round(precio_costo, 2),
            "porcentaje_ganancia": round(porcentaje_ganancia, 2),
            "ganancia_perdida": round(ganancia_perdida, 2)
        })

    return render_template("resumen.html", detalles=detalles, compras=compras)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        if email in users and users[email]["password"] == password:
            session["user"] = email
            session["name"] = users[email]["name"]
            return "<script>alert('Inicio de sesión exitoso'); window.location.href='/';</script>"
        return "<script>alert('Usuario o contraseña incorrecta'); window.location.href='/login';</script>", 401
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        password_confirm = request.form["password-confirmacion"]
        name = request.form["name"]
        if email in users:
            return "<script>alert('El usuario ya existe'); window.location.href='/register';</script>", 400
        if password != password_confirm:
            return "<script>alert('Las contraseñas no coinciden'); window.location.href='/register';</script>", 400
        users[email] = {"name": name, "password": password}
        return "<script>alert('Registro exitoso'); window.location.href='/login';</script>"
    return render_template("register.html")


@app.route("/comprar", methods=["POST"])
def comprar():
    if "user" not in session:
        return redirect(url_for("login"))

    empresa = request.form["empresa"].upper()
    cantidad = int(request.form["cantidad"])
    fecha_compra = datetime.now()
    valor_compra = float(request.form["valor-compra"])

    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={empresa}&interval=5min&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()

    try:
        last_refreshed = list(data["Time Series (5min)"].keys())[0]
        precio_compra = float(data["Time Series (5min)"][last_refreshed]["4. close"])
    except KeyError:
        return "<script>alert('Error al obtener el precio de compra'); window.location.href='/';</script>", 400

    compras.append({
        "empresa": empresa,
        "cantidad_acciones": cantidad,
        "fecha_compra": fecha_compra,
        "precio_compra": precio_compra,
        "valor_compra": valor_compra
    })
    return "<script>alert('Compra realizada con éxito'); window.location.href='/';</script>"

@app.route("/logout")
def logout():
    session.pop("user", None)
    return "<script>alert('Sesión cerrada exitosamente'); window.location.href='/login';</script>"

if __name__ == "__main__":
    app.run(debug=True)
