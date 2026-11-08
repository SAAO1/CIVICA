"""Audita todas las campañas de seis decisiones y guarda ejemplos reproducibles."""
import itertools
import json
from collections import Counter
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from juego.partida import Juego
from models.jugador import Jugador


def recorrer(semilla, rol=None):
    acciones = ("compartir", "verificar", "ignorar", "reportar")
    opciones_por_turno = [acciones]*6
    if rol is not None:
        from juego.acciones import acciones_para_rol
        roles = ("ciudadano", "periodista") if rol == "mixto" else (rol,)
        opciones_por_turno = [tuple(a["clave"] for a in acciones_para_rol(roles[i%len(roles)])) for i in range(6)]
    cuentas = Counter()
    ejemplos = {}
    for secuencia in itertools.product(*opciones_por_turno):
        juego = Juego(semilla, eventos=False)
        if rol == "mixto":
            juego.jugadores = [Jugador(id="c", nombre="Ciudadano", rol="ciudadano", ciudadano_id="ana"), Jugador(id="p", nombre="Periodista", rol="periodista", ciudadano_id="maria")]
        elif rol:
            juego.seleccionar_rol(rol)
        juego.iniciar_primera_publicacion()
        for accion in secuencia:
            if not juego.ejecutar_accion(accion):
                raise AssertionError(f"Acción rechazada: {rol}, {accion}")
            juego.avanzar_publicacion()
        resultado = juego.resultado_electoral()
        etiqueta = "empate" if resultado["empate"] else resultado["ganadores"][0]
        cuentas[etiqueta] += 1
        if etiqueta not in ejemplos:
            ejemplos[etiqueta] = secuencia
            restaurada = Juego.desde_datos(json.loads(json.dumps(juego.datos())))
            if resultado != restaurada.resultado_electoral():
                raise AssertionError("Guardar/recargar cambió el desenlace de una ruta ganadora")
        if round(sum(resultado["porcentajes"].values()), 6) != 100:
            raise AssertionError("Los porcentajes no suman cien")
        if resultado != juego.resultado_electoral():
            raise AssertionError("Consultar el resultado cambió la elección")
    return dict(semilla=semilla, rol=rol or "legacy", campañas=sum(cuentas.values()), resultados=dict(cuentas), ejemplos=ejemplos)


def main():
    registros = [recorrer(semilla, rol) for semilla in (1, 7, 42) for rol in (None, "ciudadano", "periodista", "mixto")]
    destino = RAIZ / ".tmp/auditoria_elecciones.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(registros, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    (RAIZ / "docs/verificacion_elecciones.json").write_text(json.dumps(dict(campañas=sum(r["campañas"] for r in registros), semillas=[1, 7, 42], azar_en_consulta=False, guardados_revisados_por_ruta_ganadora=True, modalidades=registros), ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps([dict(semilla=r["semilla"], rol=r["rol"], campañas=r["campañas"], resultados=r["resultados"]) for r in registros], ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
