from dataclasses import dataclass
from estructuras.nodo_grafo import NodoGrafo


@dataclass(frozen=True)
class Ciudadano(NodoGrafo):
    avatar: str = "assets/UI/avatar_unknown.png"
    zona: str = "Centro"
