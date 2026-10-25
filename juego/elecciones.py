"""Apoyos electorales derivados de la evidencia y de su circulación real.

Un índice de apoyo no cuenta votos individuales. Cada candidatura parte del
mismo índice y dispone del mismo peso total de agenda: tener dos noticias en
el guion no concede el doble de oportunidades que tener una. No se consume
azar al consultar el resultado y un empate permanece pendiente de recuento.
"""
from functools import lru_cache
import json
import math

from recursos import RAIZ


@lru_cache(maxsize=1)
def _peso_agenda():
    pesos = {}
    for publicacion in json.loads((RAIZ / "data/publicaciones.json").read_text(encoding="utf-8")):
        candidato = publicacion.get("candidato_id")
        pesos[candidato] = pesos.get(candidato, 0) + max(1, publicacion.get("impacto", 1))
    return pesos


def _alcance_real(registro, grafo):
    propagacion = registro.get("propagacion")
    if propagacion is not None:
        receptores = set(propagacion.get("receptores", []))
        if grafo is not None:
            receptores.intersection_update(grafo.nodos)
        return len(receptores)
    return max(0, int(registro.get("alcance", 0)))


def _respuesta(registro):
    accion = registro["accion"]
    especifica = registro.get("accion_rol", accion)
    verdadera = registro["publicacion"].get("verdadera")
    if especifica in ("conversar", "entrevistar"):
        contactos = _contactos_creados(registro)
        return min(.30, .18 * contactos), (
            f"{contactos} contacto(s) nuevo(s): escuchar evita el rechazo automático por un rumor "
            "y abre espacio al diálogo. No certifica el titular ni convierte un testimonio en un hecho."
        )
    if especifica == "reservar":
        return 0, "Mantener el mensaje en reserva no añade evidencia ni respaldo electoral."
    if registro["publicacion"].get("tipo") == "engañosa" and verdadera is False:
        # Una falsa encuesta de victoria favorece al nombre anunciado por
        # efecto de arrastre. No es una acusación contra esa candidatura.
        if accion == "compartir":
            return .6, "La encuesta sin sustento crea una expectativa de victoria y un efecto de arrastre engañoso."
        if accion == "verificar" or (accion == "reportar" and registro.get("eliminada")):
            return -.35, "La revisión deshace la expectativa creada por la encuesta falsa; no acusa de un delito a la candidatura."
    if accion == "compartir":
        if verdadera is True:
            return .85, "La propuesta verdadera gana visibilidad entre sus receptores."
        if verdadera is False:
            return -1.0, "La acusación falsa perjudica a la candidatura señalada entre quienes la reciben."
    if accion == "verificar":
        if verdadera is True:
            return .9, "La evidencia confirma una propuesta y refuerza su credibilidad."
        if verdadera is False:
            return 1.0, "La corrección devuelve apoyo a la candidatura acusada sin fundamento."
    if accion == "reportar" and registro.get("eliminada"):
        if verdadera is False:
            return (1.0 if especifica == "desmentir" else .35), "Se retira la acusación falsa; una corrección difundida también llega a sus receptores."
        return 0, "Retirar contenido dañino no equivale a apoyar una propuesta electoral."
    return 0, "No se difundió evidencia nueva que cambiara el apoyo electoral."


def _contactos_creados(registro):
    # Dos aristas recíprocas forman un único contacto humano. Una llamada a
    # un vínculo que ya existía no concede un bono nuevo de apoyo.
    return len({tuple(sorted(arista)) for arista in registro.get("efectos_red", {}).get("conexiones_creadas", [])
                if len(arista) == 2 and arista[0] != arista[1]})


def _porcentajes(apoyos):
    """Proporciones exactas; los empates no ganan décimas por orden de nombre.

    La UI redondea para leerlas. Repartir una décima residual alfabéticamente
    haría parecer distintos dos apoyos idénticos y favorecería visualmente al
    primer identificador, aunque no alterase el ganador real.
    """
    total = sum(apoyos.values())
    return {clave: valor * 100 / total for clave, valor in apoyos.items()}


def calcular_eleccion(candidatos, estado, historial, grafo=None, agenda=None):
    candidatos = list(candidatos)
    if not candidatos:
        raise ValueError("La elección necesita al menos una candidatura")
    # Milésimas enteras evitan desempates por redondeo binario.
    indices = {c.id: max(1000, round(c.apoyo * 1000)) for c in candidatos}
    nombres = {c.id: c.nombre for c in candidatos}
    if agenda is None:
        agenda = _peso_agenda()
    else:
        pesos = {}
        for publicacion in agenda:
            datos = publicacion if isinstance(publicacion, dict) else publicacion.datos()
            identificador = datos.get("candidato_id")
            pesos[identificador] = pesos.get(identificador, 0) + max(1, datos.get("impacto", 1))
        agenda = pesos
    razones = []
    evidencia = {c.id: [] for c in candidatos}
    for registro in historial:
        publicacion = registro["publicacion"]
        candidato = publicacion.get("candidato_id")
        if candidato not in indices:
            continue
        fuerza, motivo = _respuesta(registro)
        alcance = _alcance_real(registro, grafo)
        original = registro.get("publicacion_antes")
        impacto = (original.get("impacto", 1) if original is not None else
                   publicacion.get("impacto", 1) - (1 if registro["accion"] == "compartir" else 0))
        impacto = max(1, impacto)
        peso = impacto / max(impacto, agenda.get(candidato, impacto))
        # El origen puede leer una comprobación sin propagarla. Los enlaces
        # amplifican únicamente el alcance realmente conservado en el historial.
        audiencia = 1 + math.sqrt(alcance) / 3
        cambio = round(12000 * peso * fuerza * audiencia)
        previo = indices[candidato]
        indices[candidato] = max(1000, previo + cambio)
        cambio = indices[candidato] - previo
        detalle = {
            "publicacion_id": publicacion["id"],
            "accion": registro.get("titulo_accion", registro.get("accion_rol", registro["accion"])),
            "alcance": alcance, "cambio": cambio / 1000,
            "contactos_creados": _contactos_creados(registro),
            "motivo": motivo, "peso_agenda": round(peso, 4),
        }
        evidencia[candidato].append(detalle)
        razones.append(
            f"#{publicacion['id']} · {nombres[candidato]} · {detalle['accion']} · "
            f"{alcance} receptores · apoyo {cambio/1000:+.3f}. {motivo}"
        )
    apoyos = {clave: valor / 1000 for clave, valor in indices.items()}
    maximo = max(indices.values())
    ganadores = [c.nombre for c in candidatos if indices[c.id] == maximo]
    calidad = (estado.confianza + estado.convivencia + estado.bienestar_digital
               + estado.info_verificada - estado.desinformacion - estado.conflictos) / 4
    final = "Comunidad informada" if calidad >= 50 else "Una ciudad que necesita reconstruir confianza"
    return {
        "ganadores": ganadores, "empate": len(ganadores) > 1,
        "porcentajes": _porcentajes(indices), "apoyos": apoyos, "razones": razones,
        "final": final, "calidad": round(calidad, 1),
        "evidencia_por_candidato": evidencia,
        "metodo": "Índice de apoyo: agenda equilibrada, evidencia, escucha y receptores reales del grafo. Porcentajes redondeados en pantalla.",
        "desempate": "Empate exacto: recuento público pendiente; no se proclama una candidatura." if len(ganadores) > 1 else "Mayor índice de apoyo al cierre de la campaña.",
    }
