"""Dirección audiovisual derivada del caso y del texto, sin alterar la partida."""
from recursos import RAIZ


ESCENARIOS = {
    50: {"fondo": "assets/rediseno/fondos/cafe_exterior.png", "ambiente": "cafe_exterior", "sonido": "calle", "lugar": "Café Central · Mañana", "ciudadano": "preocupado", "periodista": "pensativo"},
    30: {"fondo": "assets/rediseno/fondos/cafe_interior.png", "ambiente": "cafe", "sonido": "cafe", "lugar": "Café Central · Mediodía", "ciudadano": "sonrisa", "periodista": "neutral"},
    70: {"fondo": "assets/expansion/fondos/parque_tarde.png", "ambiente": "parque", "sonido": "plaza", "lugar": "Parque central · La tarde", "ciudadano": "neutral", "periodista": "pensativo"},
    20: {"fondo": "assets/rediseno/fondos/investigacion.png", "ambiente": "investigacion", "sonido": "oficina", "lugar": "Mesa de investigación · Al caer la tarde", "ciudadano": "sonrisa", "periodista": "pensativo"},
    60: {"fondo": "assets/expansion/fondos/cafe_lluvia.png", "ambiente": "cafe_lluvia", "sonido": "interior_lluvia", "lugar": "Café Central · La lluvia", "ciudadano": "preocupado", "periodista": "enojado"},
    80: {"fondo": "assets/expansion/fondos/plaza_noche.png", "ambiente": "noche", "sonido": "noche", "lugar": "Plaza de Ciudad Nova · La víspera", "ciudadano": "pensativo", "periodista": "preocupado"},
}

for _ids, _fondo, _sonido, _lugar in (
    ((90, 40), "estudio", "estudio", "Estudio de Valeria · La segunda ola"),
    ((100, 10), "debate", "debate", "Foro de Ciudad Nova · Cuatro promesas"),
    ((110, 25), "redaccion", "redaccion", "Redacción · La noche del archivo"),
    ((120, 35), "urnas", "urnas", "Puesto de votación · La mañana decisiva"),
):
    for _id in _ids:
        ESCENARIOS[_id] = {
            "fondo": f"assets/expansion/siete_actos/fondos/{_fondo}.jpg",
            "ambiente": _fondo,
            "sonido": _sonido, "lugar": _lugar,
            "ciudadano": "preocupado" if _fondo == "redaccion" else "neutral",
            "periodista": "pensativo",
        }


def escenario_actual(juego):
    publicacion = juego.obtener_publicacion_actual()
    identificador = publicacion.id if publicacion else juego.ultima_publicacion_id
    datos = dict(ESCENARIOS.get(identificador, ESCENARIOS[50]))
    if not (RAIZ / datos["fondo"]).is_file():
        datos["fondo"] = "assets/rediseno/fondos/cafe_interior.png"
        datos["ambiente"] = "cafe"
        datos["sonido"] = "cafe"
    return datos


def expresion_dialogo(juego, nombre, texto):
    rol = "periodista" if nombre == "PERIODISTA" else "ciudadano"
    base = "neutral" if nombre in ("INFLUENCER", "JUAN", "ADRIAN", "LAURA", "CAMILA") else escenario_actual(juego)[rol]
    t = texto.lower()
    if any(p in t for p in ("cedí", "quise proteger", "me equivo", "hice daño", "perdón", "me hago cargo", "le debo")):
        return "triste"
    if any(p in t for p in ("antes que nadie", "nadie adjunta", "acusación", "urgencia", "si lo cierran", "miedo", "preocupa")):
        return "preocupado"
    if any(p in t for p in ("no basta", "fue rechazado", "sin motivos", "no puedo usar", "injust")):
        return "enojado"
    if any(p in t for p in ("ilusion", "alegr", "gracias", "favorito", "ya podemos", "tiene respaldo", "esperanza")):
        return "sonrisa"
    if any(p in t for p in ("revis", "contrast", "método", "contexto", "fuente", "distinguir", "preguntas")):
        return "pensativo"
    if any(p in t for p in ("otra notificación", "se corta", "resultado antes", "no alcanzó")):
        return "sorprendido"
    return base


def efecto_dialogo(texto):
    """Una acción material reconocible, sin convertir cada frase en un aviso."""
    t = texto.lower()
    for fragmento, efecto in (("notificación", "notificacion_suave"),
                              ("aro de luz", "directo"),
                              ("cuatro atriles", "microfono"),
                              ("onda del audio", "archivo_audio"),
                              ("bastón", "papeleta"),
                              ("abre su libreta", "pagina"),
                              ("deja de escribir", "lapiz"),
                              ("aparta un libro", "pagina"),
                              ("sobre la mesa hay un mapa", "papeles"),
                              ("café sin probar", "taza"),
                              ("plaza empieza a vaciarse", "pasos_calle")):
        if fragmento in t:
            return efecto
    return None


def efecto_visual_dialogo(juego, texto, nombre="", tipo_resultado=None):
    """Elige una imagen decorativa a partir del guion o del resultado real.

    Un escudo representa un retiro efectivo, nunca un reporte rechazado. Las
    conexiones sólo aparecen si hubo receptores. El visto bueno se reserva a
    una verificación de un hecho, sin convertir una opinión en certeza.
    """
    registro = getattr(juego, "ultimo_registro", None)
    if tipo_resultado in (1, 2, 3) and registro:
        accion = registro["accion"]
        metodo = registro.get("accion_rol", accion)
        if tipo_resultado == 3:
            cambios = any(registro["despues"].get(k) != v
                          for k, v in registro["antes"].items())
            return "recuerdo" if cambios else "silencio"
        if metodo in ("conversar", "entrevistar"):
            return "investigar" if registro.get("efectos_red", {}).get("conexiones_creadas") else "recuerdo"
        if metodo == "reservar":
            return "archivo"
        propagacion = registro.get("propagacion")
        if accion == "compartir":
            return "rumor" if propagacion and registro.get("alcance", 0) > 0 else "silencio"
        if accion == "reportar":
            return "reportar" if registro.get("eliminada") else "archivo"
        if accion == "verificar":
            return "verificar" if registro["publicacion"]["verdadera"] is not None else "investigar"
        return "silencio"
    from juego.cinematica import clave_cinematica
    clave = clave_cinematica(texto, nombre, juego)
    efecto = {
        "ciudad_48h": "transicion", "mensaje_barrio": "rumor",
        "rumor_colegio": "tension", "cafe_alerta": "notificacion",
        "libreta_cultura": "archivo", "mapa_parque": "investigar",
        "libro_biblioteca": "recuerdo", "acusacion_lluvia": "tension",
        "noche_electoral": "tension",
    }.get(clave)
    if efecto:
        return efecto
    t = texto.lower()
    if nombre == "NARRADOR":
        for palabras, efecto in ((("aro de luz", "directo", "valeria"), "emision"),
                                (("atriles", "debate", "focos"), "foro"),
                                (("audio", "redacción", "archivo íntegro"), "onda"),
                                (("urna", "puestos de votación", "bastón"), "papeleta")):
            if any(p in t for p in palabras):
                return efecto
    if any(p in t for p in ("abuelo", "mi hermana", "favorito")):
        return "recuerdo"
    if any(p in t for p in ("fuente", "revis", "contrasta", "método", "comunicado", "preguntas")):
        return "investigar"
    if any(p in t for p in ("acusación", "urgencia", "miedo", "antes que nadie")):
        return "tension"
    return None
