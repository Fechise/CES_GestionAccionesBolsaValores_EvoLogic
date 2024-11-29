from model.accion import Accion

class AccionesController:
    def __init__(self, api):
        self.acciones = []
        self.api = api

    def registrar_accion(self, empresa, precio_actual):
        accion = Accion(empresa, precio_actual)
        self.acciones.append(accion)

    def actualizar_precio_accion(self, empresa, nuevo_precio):
        for accion in self.acciones:
            if accion.empresa == empresa:
                accion.actualizar_precio(nuevo_precio)

    def obtener_precio_actual(self, empresa):
        for accion in self.acciones:
            if accion.empresa == empresa:
                return accion.obtener_precio()
        return None
