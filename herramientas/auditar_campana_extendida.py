"""Audita rutas válidas de catorce decisiones, sin enumerar 8**14 campañas."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import random
import sys

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from juego.acciones import acciones_para_rol
from juego.partida import Juego
from models.jugador import Jugador
from red.protocolo import codificar


def completar(elegir, semilla, roles=("periodista",), eventos=False):
    juego = Juego(semilla, eventos=eventos, campana="extendida")
    juego.jugadores = [Jugador(id=f"persona_{i}", nombre=f"Persona {i+1}", rol=rol,
                              ciudadano_id=("ana", "luis", "pedro", "maria")[i])
                       for i, rol in enumerate(roles)]
    juego.iniciar_primera_publicacion()
    ruta = []
    while not juego.finalizada:
        accion = elegir(juego)
        if not juego.ejecutar_accion(accion, juego.jugador.id):
            raise AssertionError(f"Acción inválida en el caso {juego.publicacion_actual_id}: {accion}")
        registro = juego.ultimo_registro
        ruta.append(dict(publicacion=registro["publicacion"]["id"], accion=accion,
                         jugador=registro["jugador_id"], rol=registro["rol"]))
        juego.avanzar_publicacion()
    if len(ruta) != 14:
        raise AssertionError("Una ruta no llegó a catorce decisiones")
    resultado = juego.resultado_electoral()
    copia = Juego.desde_datos(json.loads(json.dumps(juego.datos())))
    if resultado != copia.resultado_electoral():
        raise AssertionError("El resultado cambió al recargar")
    return juego, ruta, resultado


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--muestras", type=int, default=768)
    parser.add_argument("--salida", type=Path, default=RAIZ/".tmp/auditoria_campana_extendida.json")
    args = parser.parse_args()
    if args.muestras < 1:
        parser.error("La muestra debe contener al menos una campaña")
    demostraciones = {}
    for candidato in ("juan", "adrian", "laura", "camila"):
        juego, ruta, resultado = completar(
            lambda j: "contrastar" if j.obtener_publicacion_actual().candidato_id == candidato else "reservar", 42)
        nombre = next(c.nombre for c in juego.candidatos if c.id == candidato)
        if resultado["ganadores"] != [nombre] or resultado["empate"]:
            raise AssertionError(f"No se encontró una ruta válida para {nombre}")
        demostraciones[candidato] = dict(semilla=42, eventos=False, roles=["periodista"],
                                         ruta=ruta, ganadores=resultado["ganadores"], apoyos=resultado["apoyos"])
    juego, ruta, resultado = completar(lambda j: "reservar", 42)
    if not resultado["empate"]:
        raise AssertionError("La reserva sin evidencia debería conservar el empate")
    demostraciones["empate"] = dict(semilla=42, eventos=False, roles=["periodista"],
                                    ruta=ruta, ganadores=resultado["ganadores"], apoyos=resultado["apoyos"])
    conteo = Counter()
    distribucion = Counter()
    maximo_bytes = 0
    for indice in range(args.muestras):
        azar = random.Random(1000+indice)
        roles = (("ciudadano",), ("periodista",), ("ciudadano", "periodista"),
                 ("ciudadano", "periodista", "ciudadano"),
                 ("ciudadano", "periodista", "ciudadano", "periodista"))[indice % 5]
        juego, _, resultado = completar(
            lambda j: azar.choice(acciones_para_rol(j.jugador.rol))["clave"], indice,
            roles=roles, eventos=bool(indice % 2))
        ganador = "empate" if resultado["empate"] else resultado["ganadores"][0]
        conteo[ganador] += 1
        distribucion[f"{len(roles)} participante{'s' if len(roles) != 1 else ''}"] += 1
        maximo_bytes = max(maximo_bytes, len(codificar({"tipo": "estado", "datos": juego.datos()})))
    documento = dict(campana="extendida", casos=14, actos=7, muestras=args.muestras,
                     muestreo_reproducible=True, no_es_enumeracion_exhaustiva=True,
                     decisiones_validas=True, recargas_invariantes=True,
                     distribucion_participantes=dict(distribucion), ganadores_en_muestra=dict(conteo),
                     mayor_trama_bytes=maximo_bytes, demostraciones=demostraciones)
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(documento, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in documento.items() if k != "demostraciones"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
