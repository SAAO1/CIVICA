"""Cortes visuales asociados a frases concretas, sin alterar la partida.

Las consecuencias variables se dibujan a partir del historial. Estos cortes
ilustran frases concretas del narrador, del ciudadano y de la periodista.
"""
import unicodedata
from juego.historia import _DIALOGOS


CINEMATICAS = {
    "ciudad_48h": {
        "titulo": "Ciudad Nova, cuarenta y ocho horas antes",
        "texto": "Faltan cuarenta y ocho horas para la elección. En Ciudad Nova, cada teléfono cuenta una versión distinta de lo que está pasando.",
        "publicacion": None,
    },
    "mensaje_barrio": {
        "titulo": "El mensaje del barrio",
        "texto": "Una notificación interrumpe la tarde frente al Café Central. En el grupo del barrio, varias familias están compartiendo el mismo mensaje.",
        "publicacion": None,
    },
    "rumor_colegio": {
        "titulo": "Un rumor, todavía sin comunicado",
        "texto": "El mensaje acusa a Juan de querer cerrar el colegio. Nadie adjunta el comunicado original. El botón de compartir está a un toque.",
        "publicacion": None,
    },
    "cafe_alerta": {
        "titulo": "El café sin probar",
        "texto": "Una notificación interrumpe la mañana. El ciudadano deja el café sin probar.",
        "publicacion": 50,
    },
    "libreta_cultura": {
        "titulo": "Una página para las preguntas",
        "texto": "El ruido de la plaza entra por la ventana. La periodista abre su libreta por una página nueva.",
        "publicacion": 30,
    },
    "mapa_parque": {
        "titulo": "El camino de cada tarde",
        "texto": "Sobre la mesa hay un mapa del parque. El ciudadano señala el camino que usa cada tarde.",
        "publicacion": 70,
    },
    "libro_biblioteca": {
        "titulo": "El libro del abuelo",
        "texto": "La periodista aparta un libro gastado para acercar el teléfono. El ciudadano reconoce la portada.",
        "publicacion": 20,
    },
    "acusacion_lluvia": {
        "titulo": "La escritura se detiene",
        "texto": "La conversación se corta al llegar otra notificación. La periodista deja de escribir.",
        "publicacion": 60,
    },
    "noche_electoral": {
        "titulo": "Antes de las urnas",
        "texto": "La plaza empieza a vaciarse. En el teléfono, un titular promete saber el resultado antes de las urnas.",
        "publicacion": 80,
    },
}

# Un inserto por intervención principal de cada personaje y cada caso.
# Reutilizar el guion evita duplicar frases que podrían quedar desactualizadas.
# El rol forma parte del disparador: una cita repetida por otra persona no
# muestra automáticamente la experiencia de quien la dijo originalmente.
_CASOS_PERSONAJES = {50: "colegio", 30: "cultura", 70: "parque",
                    20: "biblioteca", 60: "acusacion", 80: "voto"}
for _publicacion, _caso in _CASOS_PERSONAJES.items():
    for _indice, _sufijo in ((1, "c"), (2, "p")):
        _nombre, _texto = _DIALOGOS[_publicacion][_indice]
        CINEMATICAS[f"person_{_caso}_{_sufijo}"] = {
            "titulo": f"{_nombre.title()}: {_caso}", "texto": _texto,
            "nombre": _nombre, "publicacion": _publicacion, "bucle": False,
        }

for _clave, _entrada in CINEMATICAS.items():
    _entrada.setdefault("nombre", "NARRADOR")
    _entrada["video"] = f"assets/expansion/cinematica/{_clave}.mp4"
    _entrada["poster"] = f"assets/expansion/cinematica/{_clave}.jpg"
    _entrada["inicio"] = f"assets/expansion/cinematica/{_clave}_inicio.png"


def _normalizar(texto):
    return " ".join(unicodedata.normalize("NFC", str(texto or "")).split())


_CLAVES_POR_TEXTO = {(_normalizar(entrada["nombre"]).upper(), _normalizar(entrada["texto"])): clave
                     for clave, entrada in CINEMATICAS.items()}


def clave_cinematica(texto, nombre, juego=None):
    """Devuelve un corte sólo si su hablante dice la frase completa.

    ``juego`` permite invocar esta función junto a otras decisiones de puesta
    en escena; no se consulta ni modifica. Un resultado con cifras variables,
    una reacción variable o un texto importado conserva su escena habitual.
    """
    return _CLAVES_POR_TEXTO.get((_normalizar(nombre).upper(), _normalizar(texto)))
