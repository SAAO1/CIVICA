"""Montajes de las decisiones: selección exclusivamente desde el registro real.

Cada oficio tiene ocho métodos en total y cada caso conserva su lugar y objeto.
Las variantes sin receptores y de reporte rechazado evitan ilustrar resultados
que la partida no produjo. Este catálogo no cambia la red ni los indicadores.
"""

import unicodedata

_TITULARES_ORIGINALES = {
    50: "El candidato Juan quiere cerrar el colegio.",
    30: "Adrián Morales presentó una nueva propuesta.",
    70: "El parque central tendrá mantenimiento.",
    20: "La ciudad construirá una nueva biblioteca.",
    60: "Circula un rumor sobre uno de los candidatos.",
    80: "Una encuesta afirma conocer al próximo alcalde.",
}

CASOS_ACCIONES = {
    50: {"caso": "colegio", "titulo": "El mensaje del colegio", "objeto": "colegio", "ambiente": "manana", "fondo": "assets/rediseno/fondos/cafe_exterior.png", "tema": "Mensaje del colegio", "fuente": "Comunicado original", "cautela": "Un mensaje no es una prueba"},
    30: {"caso": "cultura", "titulo": "La propuesta cultural", "objeto": "libreta", "ambiente": "interior", "fondo": "assets/rediseno/fondos/cafe_interior.png", "tema": "Propuesta cultural", "fuente": "Programa de campaña", "cautela": "Una propuesta tiene alcances"},
    70: {"caso": "parque", "titulo": "El camino del parque", "objeto": "mapa", "ambiente": "tarde", "fondo": "assets/expansion/fondos/parque_tarde.png", "tema": "Aviso del parque", "fuente": "Boletín de mantenimiento", "cautela": "Revisar fechas y zonas"},
    20: {"caso": "biblioteca", "titulo": "La biblioteca por construir", "objeto": "libro", "ambiente": "interior", "fondo": "assets/rediseno/fondos/investigacion.png", "tema": "Proyecto de biblioteca", "fuente": "Expediente del proyecto", "cautela": "Proyecto no significa inauguración"},
    60: {"caso": "acusacion", "titulo": "La acusación bajo la lluvia", "objeto": "acusacion", "ambiente": "lluvia", "fondo": "assets/expansion/fondos/cafe_lluvia.png", "tema": "Acusación en los grupos", "fuente": "Pruebas y fuente original", "cautela": "Acusación sin pruebas"},
    80: {"caso": "voto", "titulo": "La víspera de las urnas", "objeto": "urna", "ambiente": "noche", "fondo": "assets/expansion/fondos/plaza_noche.png", "tema": "Pronóstico electoral", "fuente": "Fecha, muestra y método", "cautela": "El titular no decide la elección"},
}

ACCIONES_VIDEO = {
    "compartir": ("CIUDADANO", "Compartir", "El ciudadano utiliza su teléfono para reenviar el mensaje del caso."),
    "conversar": ("CIUDADANO", "Escuchar", "El ciudadano escucha a una persona del vecindario sobre el caso; no presenta el testimonio como prueba."),
    "convocar": ("CIUDADANO", "Convocar", "El ciudadano invita al vecindario y conversa con quienes se suman; el contenido sigue necesitando contexto."),
    "ignorar": ("CIUDADANO", "No reenviar", "El ciudadano aparta el teléfono y continúa sin enviar el mensaje del caso."),
    "contrastar": ("PERIODISTA", "Contrastar", "La periodista coteja el mensaje con documentos y anotaciones, sin inventar obras o resultados electorales."),
    "entrevistar": ("PERIODISTA", "Entrevistar", "La periodista escucha una fuente y toma notas; el testimonio permanece pendiente de contraste."),
    "desmentir": ("PERIODISTA", "Rectificar", "La periodista redacta una rectificación del contenido y presenta el reporte autorizado por el resultado real."),
    "reservar": ("PERIODISTA", "Reservar", "La periodista cierra una carpeta pendiente de pruebas, sin publicar ni retirar el mensaje."),
}

_BASE = "assets/expansion/acciones_video/"
CINEMATICAS_ACCIONES = {}
for _id, _caso in CASOS_ACCIONES.items():
    for _accion, (_nombre, _titulo, _descripcion) in ACCIONES_VIDEO.items():
        _variantes = ("", "_rechazado") if _accion == "desmentir" else (("", "_sin_receptores", "_alcance_limitado") if _accion == "convocar" else ("",))
        for _variante in _variantes:
            _clave = f"accion_{_id}_{_accion}{_variante}"
            _descripcion_real = _descripcion
            if _variante == "_rechazado":
                _descripcion_real = "La periodista presenta un reporte que se rechaza: la publicación permanece, sin sello de verificación ni retirada."
            elif _variante == "_sin_receptores":
                _descripcion_real = "El ciudadano intenta invitar al barrio desde el teléfono; no aparece una reunión ni personas que reciban el mensaje."
            elif _variante == "_alcance_limitado":
                _descripcion_real = "El ciudadano envía invitaciones desde el teléfono a un grupo reducido; no se representa una multitud ni una reunión mayor que el alcance real."
            CINEMATICAS_ACCIONES[_clave] = {
                "publicacion": _id, "accion": _accion, "variante": _variante.lstrip("_"),
                "nombre": _nombre, "titulo": f"{_titulo} · {_caso['titulo']}",
                "video": _BASE+_clave+".mp4", "poster": _BASE+_clave+".jpg",
                "inicio": _BASE+_clave+"_inicio.png", "duracion": 9.0,
                "bucle": False, "descripcion_lo_que_se_ve": _descripcion_real,
            }


def clave_accion(juego, registro=None):
    """Sólo devuelve una película compatible con el resultado ya aplicado.

    Un caso importado o una acción desconocida conserva la escena normal en
    lugar de asociarse a una ilustración de otra historia. Admite los nombres
    anteriores de verificar/reportar para las partidas guardadas antiguas.
    """
    if registro is None:
        registro = getattr(juego, "ultimo_registro", None)
    if not isinstance(registro, dict):
        return None
    publicacion = registro.get("publicacion")
    if not isinstance(publicacion, dict):
        return None
    identificador = publicacion.get("id")
    accion = registro.get("accion_rol") or registro.get("accion")
    if not isinstance(identificador, int) or not isinstance(accion, str):
        return None
    accion = {"verificar": "contrastar", "reportar": "desmentir"}.get(accion, accion)
    if identificador not in CASOS_ACCIONES or accion not in ACCIONES_VIDEO:
        return None
    texto = publicacion.get("texto")
    if texto is not None:
        if not isinstance(texto, str):
            return None
        normalizar = lambda valor: " ".join(unicodedata.normalize("NFC", valor).casefold().split())
        if normalizar(texto) != normalizar(_TITULARES_ORIGINALES[identificador]):
            return None
    variante = ""
    alcance = registro.get("alcance", 0)
    if accion == "convocar" and (not isinstance(alcance, int) or isinstance(alcance, bool) or alcance < 0):
        return None
    if accion == "desmentir" and not isinstance(registro.get("eliminada", False), bool):
        return None
    if accion == "desmentir" and not registro.get("eliminada", False):
        variante = "_rechazado"
    elif accion == "convocar" and not alcance:
        variante = "_sin_receptores"
    elif accion == "convocar" and alcance < 8:
        variante = "_alcance_limitado"
    clave = f"accion_{identificador}_{accion}{variante}"
    return clave if clave in CINEMATICAS_ACCIONES else None
