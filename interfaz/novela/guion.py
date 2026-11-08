"""Guion de seis actos que conserva diálogos, cortes y doblaje originales.

El adaptador proyecta un contexto de lectura para los selectores históricos.
Nunca cambia campana, publicaciones, estado aleatorio ni decisiones de Juego.
No utiliza voces del sistema ni recursos del tablero descartado.
"""
from copy import deepcopy
from functools import lru_cache

from audio.catalogo_voces import (
    cargar_manifest, clave_clip, frases_texto, partes_resultado, ruta_clip, texto_grupo,
)
from juego.casos_feria import IDS_FERIA
from juego.cuaderno import caso_actual as _caso_original
from juego.historia import (
    contenido_resultado as _resultado_original,
    dialogos_publicacion as _dialogos_originales,
)
from juego.campana_extendida import epilogo_extendido, _CIERRE_PERSONAL, DIALOGOS_NUEVOS
from juego.puesta_escena import escenario_actual as _escenario_original
from juego.cinematica import CINEMATICAS, clave_cinematica
from juego.cinematica_extension import CINEMATICAS_EXTENSION, clave_extension as _clave_extension
from juego.cinematica_personajes_extendida import (
    CINEMATICAS_PERSONAJES_EXTENDIDAS,
    clave_personaje_extendido as _clave_personaje,
)
from juego.cinematica_acciones_extendida import clave_accion_extendida as _clave_accion

_ROMANOS = ("I", "II", "III", "IV", "V", "VI")


def es_campana_breve(juego):
    return getattr(juego, "campana", None) == "feria"


def _registro_original(registro):
    if not isinstance(registro, dict):
        return registro
    copia = deepcopy(registro)
    if copia.get("accion_rol") == "rectificar":
        # El Ciudadano puede rectificar; la respuesta grabada de la Periodista
        # conserva la explicación original del contraste y la corrección real.
        copia["accion_rol"] = "contrastar"
    return copia


class _ContextoLectura:
    campana = "extendida"

    def __init__(self, juego):
        self._juego = juego

    @property
    def ultimo_registro(self):
        return _registro_original(self._juego.ultimo_registro)

    @property
    def historial(self):
        return [_registro_original(r) for r in self._juego.historial]

    def __getattr__(self, nombre):
        return getattr(self._juego, nombre)


def _contexto(juego):
    return _ContextoLectura(juego) if es_campana_breve(juego) else juego


def _identificador(juego):
    publicacion = juego.obtener_publicacion_actual()
    return getattr(publicacion, "id", None) or getattr(juego, "ultima_publicacion_id", None) or 50


def datos_capitulo(juego):
    """Metadatos de seis actos; el nombre de función conserva el contrato UI."""
    identificador = _identificador(juego)
    numero = IDS_FERIA.index(identificador)+1 if identificador in IDS_FERIA else 1
    caso = _caso_original(juego)
    titulo = caso["titulo"]
    return {
        "id": identificador, "numero": numero, "total": 6,
        "acto": f"ACTO {_ROMANOS[numero-1]}", "numero_acto": numero,
        "capitulo": numero, "total_actos": 6, "titulo": titulo,
        "rotulo": f"ACTO {_ROMANOS[numero-1]} · {titulo}",
    }


def caso_actual(juego):
    caso = deepcopy(_caso_original(juego))
    if es_campana_breve(juego):
        datos = datos_capitulo(juego)
        caso.update(acto=datos["rotulo"], capitulo=datos["numero"],
                    numero=datos["numero"], total=6, total_actos=6)
    return caso


def escenario_actual(juego):
    """Los seis fondos y ambientes ya existen en la puesta en escena original."""
    return dict(_escenario_original(juego))


def contexto_candidaturas(juego):
    """El foro entra en el relato antes del primer rumor y vuelve a mitad de campaña.

    Conserva frases e intérpretes ya grabados. Son conversaciones de los seis
    actos existentes: no insertan publicaciones ni anticipan una elección.
    """
    if not es_campana_breve(juego):
        return ()
    identificador = _identificador(juego)
    if identificador == 50:
        foro, prioridades = DIALOGOS_NUEVOS[100], DIALOGOS_NUEVOS[10]
        return (foro[0], foro[1], foro[2], *prioridades[1:5])
    if identificador == 40:
        return DIALOGOS_NUEVOS[10]
    return ()


def dialogos_publicacion(juego):
    """Conversaciones del foro y del caso con memoria de decisiones anteriores."""
    return [*contexto_candidaturas(juego), *_dialogos_originales(_contexto(juego))]


def apertura_caso(juego):
    dialogos = dialogos_publicacion(juego)
    return dialogos[0] if dialogos else None


def contenido_resultado(juego, tipo):
    return _resultado_original(_contexto(juego), tipo)


def clave_extension(texto, nombre="NARRADOR", juego=None):
    return _clave_extension(texto, nombre, _contexto(juego) if juego is not None else None)


def clave_personaje_extendido(texto, nombre, juego=None):
    return _clave_personaje(texto, nombre, _contexto(juego) if juego is not None else None)


def clave_accion_extendida(juego, registro=None):
    return _clave_accion(_contexto(juego), _registro_original(registro) if registro is not None else None)


def corte_dialogo(texto, nombre, juego):
    """Selecciona únicamente películas originales vinculadas a la frase exacta."""
    clave = (clave_cinematica(texto, nombre, juego)
             or clave_personaje_extendido(texto, nombre, juego)
             or clave_extension(texto, nombre, juego))
    if not clave:
        return None
    catalogo = {**CINEMATICAS, **CINEMATICAS_PERSONAJES_EXTENDIDAS, **CINEMATICAS_EXTENSION}
    return dict(catalogo[clave], clave=clave)


def dialogos_epilogo(juego, eleccion=None):
    contexto = _contexto(juego)
    lineas = list(epilogo_extendido(contexto, eleccion))
    if es_campana_breve(juego):
        # La campaña breve recupera el colegio en #50, no contiene el caso #25.
        colegio = next((r for r in reversed(contexto.historial)
                        if r.get("publicacion", {}).get("id") == 50), None)
        reparado = bool(colegio and (
            colegio.get("accion") == "verificar"
            or colegio.get("accion_rol") in ("conversar", "entrevistar")
            or colegio.get("accion") == "reportar" and colegio.get("eliminada")))
        if reparado:
            lineas = [_CIERRE_PERSONAL["reparacion"] if linea == _CIERRE_PERSONAL["pendiente"] else linea
                      for linea in lineas]
    return lineas


@lru_cache(maxsize=1)
def _manifest_neuronal():
    return cargar_manifest().get("clips", {})


def rutas_neuronales(hablante, texto):
    """Sólo devuelve MP3 del catálogo neuronal original; nunca sintetiza."""
    catalogo = _manifest_neuronal()
    nombre = str(hablante or "NARRADOR").strip().upper()
    for variantes in ((texto,), (texto_grupo(texto),), tuple(partes_resultado(texto)), tuple(frases_texto(texto))):
        if not variantes:
            continue
        entradas = [catalogo.get(clave_clip(nombre, frase)) for frase in variantes]
        rutas = [ruta_clip(entrada) for entrada in entradas]
        if all(rutas):
            return tuple(rutas)
    return ()


def cobertura_dialogos(juego):
    dialogos = dialogos_publicacion(juego)
    faltantes = [(nombre, texto) for nombre, texto in dialogos if not rutas_neuronales(nombre, texto)]
    return {"frases": len(dialogos), "faltantes": faltantes}
