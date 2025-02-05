from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory
import requests
from datetime import datetime
import yfinance as yf

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
    # Renderizar la plantilla con los datos necesarios
    return render_template("index.html", username=session["name"])

@app.route("/resumen")
def resumen():
    # Recalcular el diccionario agrupadas desde cero
    agrupadas.clear()
    for compra in compras:
        empresa = compra["empresa"]
        cantidad_acciones = compra["cantidad_acciones"]
        valor_compra = compra["valor_compra"]
        precio_compra = compra["precio_compra"]

        # Obtener precio actual de la acción desde la API
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={empresa}&interval=5min&apikey={API_KEY}"
        response = requests.get(url)
        data = response.json()

        try:
            last_refreshed = list(data["Time Series (5min)"].keys())[0]
            precio_actual = float(data["Time Series (5min)"][last_refreshed]["4. close"])
        except KeyError:
            precio_actual = 0  # Manejar errores asignando un valor por defecto

        # Agregar o actualizar datos en agrupadas
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

    # Calcular los detalles de las acciones para mostrar en la página
    detalles = []
    for empresa, datos in agrupadas.items():
        valor_total = datos["valor_total"]
        precio_actual = datos["precio_actual"]
        cantidad_total = datos["cantidad_total"]
        precio_costo = valor_total / cantidad_total if cantidad_total > 0 else 0

        # Cálculo del porcentaje de ganancia/pérdida
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

    # Renderizar la plantilla con los datos necesarios
    return render_template("resumen.html", detalles=detalles, compras=compras)


# Ruta para la página de login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        if email in users and users[email]["password"] == password:
            session["user"] = email
            session["name"] = users[email]["name"]
            return redirect(url_for("index"))
        return "Usuario o contraseña incorrecta", 401
    return render_template("login.html")

# Ruta para la página de registro
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        password_confirm = request.form["password-confirmacion"]
        name = request.form["name"]
        if email in users:
            return "El usuario ya existe", 400
        if password != password_confirm:
            return "Las contraseñas no coinciden", 400
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
    valor_compra = float(request.form["valor-compra"])

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
        "precio_compra": precio_compra,
        "valor_compra": valor_compra
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

        empresa = compra["empresa"]
        cantidad_acciones = compra["cantidad_acciones"]
        valor_compra = compra["valor_compra"]
        precio_compra = compra["precio_compra"]

        # Si ya existe la empresa en el diccionario, actualizar los datos
        if empresa in agrupadas:
            agrupadas[empresa]["cantidad_total"] += cantidad_acciones
            agrupadas[empresa]["valor_total"] += valor_compra
        else:
            # Crear una nueva entrada para la empresa
            agrupadas[empresa] = {
                "cantidad_total": cantidad_acciones,
                "valor_total": valor_compra,
                "precio_actual": precio_actual,
                "precio_compra": precio_compra
            }

    return render_template("compras.html", compras=compras)

# Ruta para obtener el catálogo de acciones usando Finnhub
@app.route("/api/stocks", methods=["GET"])
def obtener_stocks():
    exchange = request.args.get("exchange", "US")
    url = f'https://finnhub.io/api/v1/stock/symbol?exchange={exchange}&token={FINNHUB_API_KEY}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        stocks = response.json()

        data = []
        count = 0

        for stock in stocks:
            if count >= 10:
                break

            symbol = stock["symbol"]

            quote_url = f'https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}'
            quote_response = requests.get(quote_url)
            quote_data = quote_response.json()

            stock_data = {
                "symbol": stock["symbol"],
                "description": stock["description"],
                "exchange": exchange,
                "current_price": quote_data.get("c"),
                "day_high": quote_data.get("h"),
                "day_low": quote_data.get("l"),
                "open_price": quote_data.get("o"),
                "change": quote_data.get("dp") if quote_data.get("dp") is not None else 0
            }

            if None not in stock_data.values():
                data.append(stock_data)
                count += 1

        return jsonify(data)

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/graficos")
def mostrar_graficos():
    if "user" not in session:
        return redirect(url_for("login"))

    # Preparar los datos para los gráficos
    empresas = []
    valores_totales = []
    porcentajes_ganancia = []

    for empresa, datos in agrupadas.items():
        empresas.append(empresa)
        valores_totales.append(datos["valor_total"])

        # Calcular porcentaje de ganancia para cada empresa
        precio_costo = datos["valor_total"] / datos["cantidad_total"] if datos["cantidad_total"] > 0 else 0
        if precio_costo > 0:
            porcentaje_ganancia = ((datos["precio_actual"] - precio_costo) / precio_costo) * 100
        else:
            porcentaje_ganancia = 0
        porcentajes_ganancia.append(round(porcentaje_ganancia, 2))

    return render_template(
        "graficos.html",
        empresas=empresas,
        valores_totales=valores_totales,
        porcentajes_ganancia=porcentajes_ganancia,  # Agregar esta variable
    )

@app.route('/api/company-info', methods=['GET'])
def company_info():
    # Obtener y limpiar el símbolo
    raw_symbol = request.args.get("symbol", "").strip()  # Elimina espacios en blanco
    symbol = raw_symbol.split()[0]  # Tomar solo el símbolo principal

    if not symbol:
        return jsonify({"error": "Símbolo no proporcionado"}), 400

    # Simulación de datos de la empresa (reemplazar con integración real)
    company_data = {
        "TSLA": {
            "name": "Tesla, Inc.",
            "sector": "Automóviles",
            "industry": "Fabricación de vehículos eléctricos",
            "description": "Tesla diseña y fabrica automóviles eléctricos y soluciones de almacenamiento de energía."
        },
        "AAPL": {
            "name": "Apple Inc.",
            "sector": "Tecnología",
            "industry": "Electrónica de consumo",
            "description": "Apple diseña y fabrica productos electrónicos, software y servicios en línea."
        }
    }

    data = company_data.get(symbol.upper())
    if data:
        return jsonify(data)
    else:
        return jsonify({"error": "Empresa no encontrada"}), 404


# Ruta para logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# Ruta para servir archivos estáticos
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)


if __name__ == "__main__":
    app.run(debug=True)