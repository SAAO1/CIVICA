"""Cortes del narrador enlazados a la primera frase exacta de cada caso nuevo."""
import unicodedata
from juego.campana_extendida import DIALOGOS_NUEVOS, CASOS_NUEVOS


def _normalizar(texto):
    return " ".join(unicodedata.normalize("NFC", str(texto)).casefold().split())


CINEMATICAS_EXTENSION = {
    f"narrador_{identificador}": {
        "video": f"assets/expansion/siete_actos/videos/narrador_{identificador}.mp4",
        "poster": f"assets/expansion/siete_actos/videos/narrador_{identificador}.jpg",
        "inicio": f"assets/expansion/siete_actos/videos/narrador_{identificador}_inicio.png",
        "nombre": "NARRADOR", "texto": dialogos[0][1], "publicacion": identificador,
        "titulo": CASOS_NUEVOS[identificador]["titulo"], "bucle": True, "duracion": 10.0,
    }
    for identificador, dialogos in DIALOGOS_NUEVOS.items()
}


def clave_extension(texto, nombre="NARRADOR", juego=None):
    if (str(nombre).upper().strip() != "NARRADOR" or juego is None
            or getattr(juego, "campana", "clasica") != "extendida"):
        return None
    actual = juego.obtener_publicacion_actual()
    identificador = getattr(actual, "id", None)
    clave = f"narrador_{identificador}"
    entrada = CINEMATICAS_EXTENSION.get(clave)
    return clave if entrada and _normalizar(texto) == _normalizar(entrada["texto"]) else None
