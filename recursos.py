from functools import lru_cache
from pathlib import Path

RAIZ = Path(__file__).resolve().parent

# Los originales siguen siendo respaldo; cada escena consume el nuevo arte
# cuando está instalado en el proyecto, independientemente del directorio actual.
REDISENO = {
    "assets/fondos/fondo escena portada.jfif": "fondos/portada_ciudad.png",
    "assets/fondos/Escena 1.jfif": "fondos/ciudad.png",
    "assets/fondos/Escena 2.png": "fondos/cafe_exterior.png",
    "assets/fondos/Escena 3.png": "fondos/telefono.png",
    "assets/fondos/Escena 4.png": "fondos/cafe_interior.png",
    "assets/fondos/Escena 5.png": "fondos/cafe_interior.png",
    "assets/fondos/Escena 6.png": "fondos/investigacion.png",
    "assets/fondos/Escena 7.png": "fondos/investigacion.png",
    "assets/fondos/Escena 8.png": "fondos/cafe_interior.png",
    "assets/fondos/Escena Arbol.jfif": "fondos/observatorio.png",
    "assets/personajes/Ciudadano.png": "personajes/ciudadano_neutral.png",
    "assets/personajes/periodista.png": "personajes/periodista_neutral.png",
}


def ruta_recurso(ruta):
    return str(RAIZ / ruta)


@lru_cache(maxsize=32)
def pixmap_recurso(ruta):
    from PyQt6.QtGui import QPixmap
    nuevo = REDISENO.get(str(ruta))
    if nuevo:
        candidato = RAIZ / "assets/rediseno" / nuevo
        if candidato.is_file():
            imagen = QPixmap(str(candidato))
            if not imagen.isNull():
                return imagen
    return QPixmap(ruta_recurso(ruta))
