class Usuario:
    def __init__(self, nombre: str, email: str):
        self.nombre = nombre
        self.email = email
        self.compras = []

    def consultar_compras(self):
        return self.compras

    def registrar_compra(self, compra):
        self.compras.append(compra)
