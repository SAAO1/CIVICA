"""Doce planos de personajes enlazados al guion de los actos IV–VII.

La identidad del caso, su publicación canónica, el hablante y la frase se
comprueban juntos: un titular importado nunca hereda una escena de campaña.
"""
import unicodedata

from juego.campana_extendida import DIALOGOS_NUEVOS, PUBLICACIONES_NUEVAS


_BASE = "assets/expansion/siete_actos/personajes_video/"
_PLANOS = (
    (90, 1, "valeria_presenta", "Valeria prepara el directo", "estudio", "influencer", "camara"),
    (90, 5, "valeria_recorte", "El encuadre y su responsabilidad", "estudio", "influencer", "recorte"),
    (40, 3, "camila_canal", "Camila conserva las dos versiones", "estudio", "camila", "fuentes"),
    (100, 3, "juan_plan", "Juan explica las etapas", "debate", "juan", "atriles"),
    (10, 1, "adrian_cultura", "Adrián defiende su prioridad", "debate", "adrian", "atriles"),
    (110, 3, "camila_audio", "La advertencia de Camila", "redaccion", "camila", "audio"),
    (110, 6, "valeria_pausa", "Valeria deja respirar el directo", "redaccion", "influencer", "escucha"),
    (25, 1, "juan_archivo", "La pregunta permanece en el archivo", "redaccion", "juan", "fuentes"),
    (25, 6, "llamada_hermana", "Una llamada que la carpeta no sustituye", "redaccion", "ciudadano", "llamada"),
    (120, 1, "abuelo_entrada", "El abuelo y el camino accesible", "urnas", "ciudadano", "abuelo"),
    (120, 2, "laura_mapa", "Laura conserva la fuente del mapa", "urnas", "laura", "mapa"),
    (35, 1, "valeria_urna", "El teléfono no es una urna", "urnas", "influencer", "camara"),
)

CINEMATICAS_PERSONAJES_EXTENDIDAS = {}
for _id, _indice, _sufijo, _titulo, _escenario, _personaje, _accion in _PLANOS:
    _nombre, _texto = DIALOGOS_NUEVOS[_id][_indice]
    _clave = f"personaje_{_id}_{_sufijo}"
    CINEMATICAS_PERSONAJES_EXTENDIDAS[_clave] = {
        "publicacion": _id, "indice_dialogo": _indice, "nombre": _nombre,
        "texto": _texto, "titulo": _titulo, "escenario": _escenario,
        "personaje": _personaje, "accion": _accion,
        "video": _BASE + _clave + ".mp4", "poster": _BASE + _clave + ".jpg",
        "inicio": _BASE + _clave + "_inicio.png", "duracion": 9.0, "bucle": True,
        "descripcion_lo_que_se_ve": (
            "Escena ilustrada del lugar y sus interlocutores; cámara suave, "
            "luz ambiental, escucha y rostro en dos poses cuando hay sprite."
        ),
    }


def _normalizar(texto):
    return " ".join(unicodedata.normalize("NFC", texto).casefold().split())


_TITULARES = {p["id"]: p["texto"] for p in PUBLICACIONES_NUEVAS}
_INDICE = {(p["publicacion"], p["nombre"], _normalizar(p["texto"])): clave
           for clave, p in CINEMATICAS_PERSONAJES_EXTENDIDAS.items()}


def clave_personaje_extendido(texto, nombre, juego=None):
    """Selecciona sólo la frase de la publicación original del modo extendido."""
    if (juego is None or getattr(juego, "campana", "clasica") != "extendida"
            or not isinstance(texto, str) or not isinstance(nombre, str)):
        return None
    obtener = getattr(juego, "obtener_publicacion_actual", None)
    if not callable(obtener):
        return None
    actual = obtener()
    identificador = getattr(actual, "id", None)
    titular = getattr(actual, "texto", None)
    if (type(identificador) is not int or identificador not in _TITULARES
            or not isinstance(titular, str)
            or _normalizar(titular) != _normalizar(_TITULARES[identificador])):
        return None
    return _INDICE.get((identificador, nombre.upper().strip(), _normalizar(texto)))
