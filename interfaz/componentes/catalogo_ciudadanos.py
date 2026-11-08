"""Identidades visuales disponibles para ampliar la historia de Ciudad Nova.

El atlas se lee por filas, de izquierda a derecha. Los primeros diez retratos
pertenecen a los vecinos que ya se incorporan a la partida. Los restantes están
reservados para historias futuras; este catálogo no modifica el grafo del juego.
"""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path


COLUMNAS_ATLAS_CIUDADANOS = 8
FILAS_ATLAS_CIUDADANOS = 8
RUTA_ATLAS_CIUDADANOS = Path("avatares") / "ciudadanos_64.png"


@dataclass(frozen=True)
class RetratoCiudadano:
    id: str
    nombre: str
    indice: int

    @property
    def celda(self):
        """Columna y fila, ambas empezando en cero."""
        return self.indice % COLUMNAS_ATLAS_CIUDADANOS, self.indice // COLUMNAS_ATLAS_CIUDADANOS


_IDENTIDADES = (
    ("lucia", "Lucía"), ("mateo", "Mateo"), ("valeria", "Valeria"), ("tomas", "Tomás"),
    ("sara", "Sara"), ("nicolas", "Nicolás"), ("gabriela", "Gabriela"), ("andres", "Andrés"),
    ("daniela", "Daniela"), ("samuel", "Samuel"), ("mariana", "Mariana"), ("sebastian", "Sebastián"),
    ("natalia", "Natalia"), ("julian", "Julián"), ("paula", "Paula"), ("emilio", "Emilio"),
    ("alejandra", "Alejandra"), ("camilo", "Camilo"), ("isabel", "Isabel"), ("martin", "Martín"),
    ("aurora", "Aurora"), ("adrian", "Adrián"), ("juana", "Juana"), ("felipe", "Felipe"),
    ("carmen", "Carmen"), ("ricardo", "Ricardo"), ("pilar", "Pilar"), ("esteban", "Esteban"),
    ("teresa", "Teresa"), ("hugo", "Hugo"), ("manuela", "Manuela"), ("oscar", "Óscar"),
    ("jimena", "Jimena"), ("david", "David"), ("alicia", "Alicia"), ("jorge", "Jorge"),
    ("lorena", "Lorena"), ("rafael", "Rafael"), ("beatriz", "Beatriz"), ("victor", "Víctor"),
    ("eva", "Eva"), ("miguel", "Miguel"), ("irene", "Irene"), ("cristian", "Cristian"),
    ("noelia", "Noelia"), ("fernando", "Fernando"), ("clara", "Clara"), ("sergio", "Sergio"),
    ("ruth", "Ruth"), ("daniel", "Daniel"), ("amelia", "Amelia"), ("javier", "Javier"),
    ("diana", "Diana"), ("alberto", "Alberto"), ("patricia", "Patricia"), ("bruno", "Bruno"),
    ("rocio", "Rocío"), ("salvador", "Salvador"), ("mercedes", "Mercedes"), ("ivan", "Iván"),
    ("angela", "Ángela"), ("manuel", "Manuel"), ("vanessa", "Vanessa"), ("agustin", "Agustín"),
)

CATALOGO_CIUDADANOS = tuple(
    RetratoCiudadano(identificador, nombre, indice)
    for indice, (identificador, nombre) in enumerate(_IDENTIDADES)
)
_INDICES_CIUDADANOS = {retrato.id: retrato.indice for retrato in CATALOGO_CIUDADANOS}


def indice_retrato_ciudadano(identificador):
    """Asigna una celda estable incluso a un ID de una partida futura.

    Los IDs del catálogo tienen fotografías distintas. Para cualquier otro ID
    se reparte el atlas con SHA-256, sin depender del hash aleatorio de Python,
    del orden de dibujo ni de la semilla de los eventos. Más de 64 identidades
    ajenas al catálogo pueden compartir fotografía.
    """
    identificador = str(identificador).strip().casefold()
    if identificador in _INDICES_CIUDADANOS:
        return _INDICES_CIUDADANOS[identificador]
    huella = sha256(("civica:retrato:" + identificador).encode("utf-8")).digest()
    return int.from_bytes(huella[:8], "big") % len(CATALOGO_CIUDADANOS)
