"""Combina revisiones Qt y exige hashes actuales de toda la campaña ampliada."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from juego.cinematica_extension import CINEMATICAS_EXTENSION
from juego.cinematica_acciones_extendida import CINEMATICAS_ACCIONES_EXTENDIDAS
from juego.cinematica_personajes_extendida import CINEMATICAS_PERSONAJES_EXTENDIDAS


def sha256(ruta):
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=RAIZ/"docs/verificacion_inicios_siete_actos.json")
    parser.add_argument("--actualizacion", type=Path, action="append", required=True)
    parser.add_argument("--destino", type=Path, default=RAIZ/"docs/verificacion_inicios_siete_actos.json")
    args = parser.parse_args()
    catalogo = {**CINEMATICAS_EXTENSION, **CINEMATICAS_ACCIONES_EXTENDIDAS,
                **CINEMATICAS_PERSONAJES_EXTENDIDAS}
    reproductor = sha256(RAIZ/"cinematica_narrativa.py")
    registros = {}
    lotes = [args.base, *args.actualizacion]
    for ruta in lotes:
        documento = json.loads(ruta.read_text(encoding="utf-8"))
        if documento.get("reproductor_sha256") != reproductor:
            raise ValueError(f"El reproductor cambió después de esta revisión: {ruta}")
        clips = documento["clips"]
        if documento["cantidad"] != len(clips) or documento["esperados"] != len(clips):
            raise ValueError(f"Lote Qt incompleto: {ruta}")
        for registro in clips:
            registros[registro["clave"]] = registro
    if set(registros) != set(catalogo):
        raise ValueError("Los lotes no cubren exactamente el catálogo completo de siete actos")
    for clave, entrada in catalogo.items():
        registro = registros[clave]
        if registro["video_sha256"] != sha256(RAIZ/entrada["video"]):
            raise ValueError(f"Falta reverificar el MP4 modificado: {clave}")
        if registro["inicio_sha256"] != sha256(RAIZ/entrada["inicio"]):
            raise ValueError(f"Falta reverificar la portada modificada: {clave}")
        if not all(registro[campo] is True for campo in (
                "cubierta_inicial_exacta", "pausa_congela_ultimo_plano", "fuente_anterior_liberada")):
            raise ValueError(f"Una comprobación visual no aprobó: {clave}")
        if registro["diferencia_inicio_rgb"] >= 5:
            raise ValueError(f"Diferencia excesiva del primer fotograma: {clave}")
        if registro["primer_frame_reanudado_ms"] < registro["posicion_guardada_ms"]-125:
            raise ValueError(f"La reanudación retrocede a un plano anterior: {clave}")
    salida = dict(cantidad=len(registros), esperados=len(catalogo), catalogo="extension",
                  reproductor_sha256=reproductor, verificacion_completa=True,
                  mp4_y_portadas_corresponden_a_hashes_actuales=True,
                  lotes_combinados=[str(ruta.resolve().relative_to(RAIZ)).replace("\\", "/") for ruta in lotes],
                  clips=[registros[clave] for clave in catalogo])
    args.destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = args.destino.with_suffix(".tmp.json")
    temporal.write_text(json.dumps(salida, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    temporal.replace(args.destino)
    print(json.dumps(dict(clips=len(registros), verificacion_completa=True,
                          mayor_diferencia_rgb=max(r["diferencia_inicio_rgb"] for r in registros.values())), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
