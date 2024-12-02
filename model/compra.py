from datetime import datetime

class Compra:
    def __init__(self, empresa: str, precio_compra: float, cantidad_acciones: int, fecha_compra=None, valor_compra= float):
        self.empresa = empresa
        self.precio_compra = precio_compra
        self.cantidad_acciones = cantidad_acciones
        self.fecha_compra = fecha_compra if fecha_compra else datetime.now()
        self.valor_compra = valor_compra

    def calcular_porcentaje(self, precio_actual):
        if self.precio_compra == 0:
            return 0
        return ((precio_actual - self.precio_compra) / self.precio_compra) * 100
