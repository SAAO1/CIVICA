from dataclasses import dataclass


@dataclass(frozen=True)
class NodoGrafo:
    id: str
    nombre: str
    rol: str = "ciudadano"
