from dataclasses import asdict, dataclass


@dataclass
class Evento:
    tipo: str
    texto: str
    urgente: bool = False
    segundos: int = 15

    def datos(self):
        return asdict(self)


def generar_evento(azar, partida):
    tipo = azar.choice(("normal", "viral", "convivencia", "discusion", "conexion"))
    if tipo == "viral":
        return Evento(tipo, "Civitas alerta: la publicación puede volverse viral. Decide con cuidado.", True)
    if tipo == "convivencia":
        partida.estado.aplicar({"convivencia": 2, "bienestar_digital": 1})
        return Evento(tipo, "Una campaña vecinal promueve conversaciones respetuosas.")
    if tipo == "discusion":
        partida.estado.aplicar({"conflictos": 1, "confianza": -1})
        return Evento(tipo, "Una discusión electoral aumenta la tensión en Ciudad Nova.")
    if tipo == "conexion":
        if partida.grafo.existe_vertice("pedro") and partida.grafo.existe_vertice("ines"):
            cambio = partida.grafo.agregar_arista("pedro", "ines")
            if cambio:
                return Evento(tipo, "Inés se conecta con Pedro: ahora puede recibir sus publicaciones.")
    return Evento(tipo, "Una nueva publicación llega a Civitas.")
