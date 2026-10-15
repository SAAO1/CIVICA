class Publicacion:
    def __init__(
        self,
        id,
        texto,
        verdadera,
        impacto,
        tipo="noticia",
        emisor_id="ana",
        candidato_id=None,
        danina=False
    ):
        self.id = id
        self.texto = texto
        self.verdadera = verdadera
        self.impacto = impacto

        self.compartidos = 0
        self.verificaciones = 0
        self.reportes = 0

        self.estado = "ACTIVA"
        self.tipo = tipo
        self.emisor_id = emisor_id
        self.candidato_id = candidato_id
        self.danina = danina
        self.alcance = 0

    def datos(self):
        return dict(vars(self))
