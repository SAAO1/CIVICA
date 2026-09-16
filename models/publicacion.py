class Publicacion:
    def __init__(
        self,
        id,
        texto,
        verdadera,
        impacto
    ):
        self.id = id
        self.texto = texto
        self.verdadera = verdadera
        self.impacto = impacto

        self.compartidos = 0
        self.verificaciones = 0
        self.reportes = 0

        self.estado = "ACTIVA"