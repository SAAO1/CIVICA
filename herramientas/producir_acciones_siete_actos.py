"""Exporta los 88 videos de decisiones de los actos IV–VII y verifica cada MP4.

Los montajes clásicos se conservan en su carpeta original. La campaña nueva
usa cuatro lugares y cuatro CG propios, junto a los ocho métodos de acción.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from PyQt6.QtWidgets import QApplication
from cinematica_visual import _fuente
from cinematica_acciones_extendida_visual import CARPETA_EXTENDIDA, RenderizadorAccionExtendida
from juego.cinematica_acciones_extendida import CINEMATICAS_ACCIONES_EXTENDIDAS
from herramientas.producir_acciones_video import exportar, sha256, huella_render, preparar_pantallas, usa_telefono


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publicacion", type=int, action="append")
    parser.add_argument("--pendientes", action="store_true")
    parser.add_argument("--trabajadores", type=int, choices=(1, 2), default=1)
    parser.add_argument("--clave", choices=CINEMATICAS_ACCIONES_EXTENDIDAS)
    parser.add_argument("--crf", type=int, choices=range(23, 31), default=25)
    parser.add_argument("--telefonos", action="store_true", help="Sólo los 32 montajes con el teléfono que cambia")
    args = parser.parse_args()
    app = QApplication.instance() or QApplication([])
    _fuente(20)
    preparar_pantallas(f["publicacion"] for k, f in CINEMATICAS_ACCIONES_EXTENDIDAS.items()
                       if (not args.clave or k == args.clave)
                       and (not args.telefonos or usa_telefono(f))
                       and (args.publicacion is None or f["publicacion"] in args.publicacion))
    CARPETA_EXTENDIDA.mkdir(parents=True, exist_ok=True)
    manifest = CARPETA_EXTENDIDA / "manifest.json"
    anterior = {}
    if manifest.is_file():
        anterior = {c["clave"]: c for c in json.loads(manifest.read_text(encoding="utf-8"))["clips"]}
    pendientes = []
    for clave, ficha in CINEMATICAS_ACCIONES_EXTENDIDAS.items():
        if args.clave and clave != args.clave:
            continue
        if args.telefonos and not usa_telefono(ficha):
            continue
        if args.publicacion is not None and ficha["publicacion"] not in args.publicacion:
            continue
        viejo = anterior.get(clave)
        if args.pendientes and viejo and (viejo.get("ancho"), viejo.get("alto"), viejo.get("fps"), viejo.get("duracion")) == (1280, 720, 24, 9.0):
            fuentes = viejo.get("fuentes", [])
            integro = len(fuentes) == 3 and all((RAIZ/f["ruta"]).is_file() and sha256(RAIZ/f["ruta"]) == f["sha256"] for f in fuentes)
            for campo in ("video", "poster", "inicio"):
                ruta = CARPETA_EXTENDIDA/viejo[campo]
                etiqueta = "sha256" if campo == "video" else campo+"_sha256"
                integro = integro and ruta.is_file() and sha256(ruta) == viejo.get(etiqueta)
            firma, _ = huella_render(RenderizadorAccionExtendida(clave))
            if integro and viejo.get("render_sha256") == firma and viejo.get("crf") == args.crf:
                print(f"{clave}: íntegro, se conserva", flush=True)
                continue
        pendientes.append(clave)
    with ThreadPoolExecutor(max_workers=args.trabajadores) as pool:
        trabajos = {pool.submit(exportar, clave, CARPETA_EXTENDIDA, 1280, 24, 9.0,
                               renderizador=RenderizadorAccionExtendida, crf=args.crf): clave for clave in pendientes}
        for trabajo in as_completed(trabajos):
            clave = trabajos[trabajo]
            anterior[clave] = trabajo.result()
            documento = dict(
                version=2, campana="extendida", actos=[4, 5, 6, 7],
                tecnica="Ilustraciones originales de ImageGen, montaje de tres planos, cámara y objetos animados QPainter; teléfonos físicos con publicación canónica de Civitas; H.264 sin voz incrustada. La voz neural se sincroniza en el juego.",
                criterios="La decisión real determina caso, actor y variante. Sin receptores no se muestra reunión; alcance menor de ocho muestra invitaciones; reporte rechazado no retira contenido. Contrastar opiniones no certifica preferencias.",
                clips=[anterior[k] for k in CINEMATICAS_ACCIONES_EXTENDIDAS if k in anterior])
            temporal = manifest.with_suffix(".tmp.json")
            temporal.write_text(json.dumps(documento, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
            temporal.replace(manifest)
    print(json.dumps(dict(clips=len(anterior), pendientes=len(pendientes)), ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
