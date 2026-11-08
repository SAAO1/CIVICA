"""Ocho decisiones por caso para los actos IV–VII, con resultados reales.

El catálogo clásico conserva sus 66 recursos. Esta extensión añade 88 planos
de acción sin reutilizar una noticia antigua para ilustrar un asunto nuevo.
"""
import unicodedata

from juego.campana_extendida import PUBLICACIONES_NUEVAS
from juego.cinematica_acciones import ACCIONES_VIDEO, clave_accion


_BASE = "assets/expansion/siete_actos/acciones/"
_ARTE = "assets/expansion/siete_actos/"

CASOS_ACCIONES_EXTENDIDOS = {
    90: dict(caso="parques_viral", titulo="El video de los parques", objeto="video", ambiente="interior", acto="estudio",
             tema="Video de los parques", fuente="Video íntegro y boletín", cautela="Un recorte puede cambiar el sentido"),
    40: dict(caso="correcciones", titulo="Un canal para corregir", objeto="canal", ambiente="interior", acto="estudio",
             tema="Canal de correcciones", fuente="Canal público y fuentes", cautela="Corregir también exige mostrar fuentes"),
    100: dict(caso="cubiertas", titulo="El colegio bajo los focos", objeto="colegio", ambiente="interior", acto="debate",
              tema="Obras en el colegio", fuente="Programa y cronograma", cautela="Distinguir propuesta y obra terminada"),
    10: dict(caso="prioridad_cultural", titulo="Una prioridad en debate", objeto="opinion", ambiente="interior", acto="debate",
             tema="La prioridad cultural", fuente="Declaración completa", cautela="Una preferencia no se verifica como hecho"),
    110: dict(caso="audio_voto", titulo="El audio de medianoche", objeto="audio", ambiente="noche", acto="redaccion",
              tema="El audio sobre votar", fuente="Audio íntegro y norma", cautela="Escuchar el contexto de la grabación"),
    25: dict(caso="archivo_colegio", titulo="El archivo que faltaba", objeto="archivo", ambiente="noche", acto="redaccion",
             tema="Clases durante las obras", fuente="Archivo íntegro del plan", cautela="Conservar el documento completo"),
    120: dict(caso="accesos_voto", titulo="Los caminos a las urnas", objeto="mapa", ambiente="interior", acto="urnas",
              tema="Accesos a las urnas", fuente="Mapa electoral oficial", cautela="Revisar sede, acceso y fecha"),
    35: dict(caso="voto_falso", titulo="La última decisión del barrio", objeto="mensaje", ambiente="interior", acto="urnas",
             tema="Comentarios y voto", fuente="Reglas de votación", cautela="Distinguir comentario y voto"),
}

for _caso in CASOS_ACCIONES_EXTENDIDOS.values():
    _caso["fondo"] = _ARTE + f"fondos/{_caso['acto']}.jpg"
    _caso["objeto_ruta"] = _ARTE + f"ilustraciones/{_caso['acto']}.jpg"

_TITULARES = {p["id"]: p["texto"] for p in PUBLICACIONES_NUEVAS}
CINEMATICAS_ACCIONES_EXTENDIDAS = {}
for _identificador, _caso in CASOS_ACCIONES_EXTENDIDOS.items():
    for _accion, (_nombre, _titulo, _descripcion) in ACCIONES_VIDEO.items():
        _variantes = (("", "_rechazado") if _accion == "desmentir" else
                      ("", "_sin_receptores", "_alcance_limitado") if _accion == "convocar" else ("",))
        for _variante in _variantes:
            _clave = f"accion_{_identificador}_{_accion}{_variante}"
            _detalle = _descripcion
            if _variante == "_rechazado":
                _detalle = "La periodista presenta un reporte rechazado. El contenido permanece, sin sello de verificación ni retirada."
            elif _variante == "_sin_receptores":
                _detalle = "El ciudadano intenta convocar desde el teléfono. No se muestra una reunión ni receptores inexistentes."
            elif _variante == "_alcance_limitado":
                _detalle = "El ciudadano envía invitaciones a un grupo reducido. No se muestra una multitud mayor que el alcance real."
            CINEMATICAS_ACCIONES_EXTENDIDAS[_clave] = dict(
                publicacion=_identificador, accion=_accion, variante=_variante.lstrip("_"),
                nombre=_nombre, titulo=f"{_titulo} · {_caso['titulo']}",
                video=_BASE+_clave+".mp4", poster=_BASE+_clave+".jpg",
                inicio=_BASE+_clave+"_inicio.png", duracion=9.0, bucle=False,
                descripcion_lo_que_se_ve=_detalle)


def clave_accion_extendida(juego, registro=None):
    """Resuelve ambas campañas sin confundir títulos importados o resultados."""
    original = clave_accion(juego, registro)
    if original is not None:
        return original
    registro = getattr(juego, "ultimo_registro", None) if registro is None else registro
    if not isinstance(registro, dict) or not isinstance(registro.get("publicacion"), dict):
        return None
    publicacion = registro["publicacion"]
    identificador = publicacion.get("id")
    accion = registro.get("accion_rol") or registro.get("accion")
    if not isinstance(identificador, int) or not isinstance(accion, str):
        return None
    accion = {"verificar": "contrastar", "reportar": "desmentir"}.get(accion, accion)
    if identificador not in CASOS_ACCIONES_EXTENDIDOS or accion not in ACCIONES_VIDEO:
        return None
    texto = publicacion.get("texto")
    if texto is not None:
        if not isinstance(texto, str):
            return None
        normalizar = lambda valor: " ".join(unicodedata.normalize("NFC", valor).casefold().split())
        if normalizar(texto) != normalizar(_TITULARES[identificador]):
            return None
    alcance = registro.get("alcance", 0)
    eliminada = registro.get("eliminada", False)
    if accion == "convocar" and (not isinstance(alcance, int) or isinstance(alcance, bool) or alcance < 0):
        return None
    if accion == "desmentir" and not isinstance(eliminada, bool):
        return None
    variante = ("_rechazado" if accion == "desmentir" and not eliminada else
                "_sin_receptores" if accion == "convocar" and alcance == 0 else
                "_alcance_limitado" if accion == "convocar" and alcance < 8 else "")
    clave = f"accion_{identificador}_{accion}{variante}"
    return clave if clave in CINEMATICAS_ACCIONES_EXTENDIDAS else None
