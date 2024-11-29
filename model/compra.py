from datetime import datetime

class Compra:
    def __init__(self, empresa: str, precio_compra: float, cantidad_acciones: int, fecha_compra=None):
        self.empresa = empresa
        self.precio_compra = precio_compra
        self.cantidad_acciones = cantidad_acciones
        self.fecha_compra = fecha_compra if fecha_compra else datetime.now()

    def calcular_porcentaje(self, precio_actual):
        if self.precio_compra == 0:
            return 0
        return ((precio_actual - self.precio_compra) / self.precio_compra) * 100
