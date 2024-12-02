from datetime import datetime

class Accion:
    def __init__(self, empresa: str, precio_actual: float, ultima_actualizacion=None):
        self.empresa = empresa
        self.precio_actual = precio_actual
        self.ultima_actualizacion = ultima_actualizacion if ultima_actualizacion else datetime.now()

    def actualizar_precio(self, nuevo_precio):
        self.precio_actual = nuevo_precio
        self.ultima_actualizacion = datetime.now()

    def obtener_precio(self):
        return self.precio_actual
