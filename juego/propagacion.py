from dataclasses import asdict, dataclass

from estructuras.bst import ArbolPublicaciones
from estructuras.grafo import Grafo


@dataclass
class ResultadoPropagacion:
    publicacion_id: int
    emisor: str
    receptores: list[str]
    orden: list[str]
    niveles: list[list[str]]
    distancias: dict[str, int]
    aristas: list[tuple[str, str]]
    tiempo_simulado: float
    verdadera: bool | None
    correccion: bool = False

    @property
    def alcance(self):
        return len(self.receptores)

    def datos(self):
        return asdict(self)


class ServicioPropagacion:
    """Une el índice de contenido activo (ABB) con las relaciones (grafo)."""

    def __init__(self, arbol: ArbolPublicaciones, grafo: Grafo):
        self.arbol = arbol
        self.grafo = grafo

    def simular(self, publicacion_id, emisor, saltos=2, intervalo=1.0, correccion=False, contactos=None):
        # Una publicación retirada del árbol ya no puede circular.
        publicacion = self.arbol.buscar(publicacion_id)
        if publicacion is None:
            raise ValueError("La publicación no está activa en el ABB")
        if intervalo <= 0:
            raise ValueError("El intervalo simulado debe ser positivo")
        # BFS descubre cada receptor una vez y calcula distancia y niveles.
        recorrido = self.grafo.bfs(emisor, saltos, **({"contactos": contactos} if contactos is not None else {}))
        return ResultadoPropagacion(
            publicacion_id, emisor, recorrido.orden[1:], recorrido.orden,
            recorrido.niveles, recorrido.distancias, recorrido.aristas,
            max(recorrido.distancias.values(), default=0) * intervalo,
            publicacion.verdadera, correccion)
