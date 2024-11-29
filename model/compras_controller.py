from model.compra import Compra

class ComprasController:
    def __init__(self):
        self.compras = []

    def crear_compra(self, usuario, empresa, precio_compra, cantidad_acciones):
        compra = Compra(empresa, precio_compra, cantidad_acciones)
        usuario.registrar_compra(compra)
        self.compras.append(compra)

    def obtener_compras_por_usuario(self, usuario):
        return usuario.consultar_compras()

    def calcular_porcentaje_por_usuario(self, usuario, empresa, precio_actual):
        for compra in usuario.consultar_compras():
            if compra.empresa == empresa:
                return compra.calcular_porcentaje(precio_actual)
        return None
