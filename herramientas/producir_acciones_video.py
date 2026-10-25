"""Produce los 66 montajes de acciones y sus primeros fotogramas exactos.

No guarda secuencias intermedias: los BGRA entran directamente a FFmpeg. El
cartel de espera se extrae del vídeo terminado para evitar un salto visual al
recibir el primer fotograma. Los JPG muestran la acción como miniatura quieta.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import subprocess
import shutil
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from PyQt6.QtWidgets import QApplication
from cinematica_visual import _fuente
from cinematica_acciones_visual import CARPETA, DURACION, FPS, RenderizadorAccion
from juego.cinematica_acciones import ACCIONES_VIDEO, CINEMATICAS_ACCIONES
from herramientas.exportar_ambientes import localizar_ffmpeg
from cine_telefono import imagen_feed

_HASHES = {}


def usa_telefono(ficha):
    return (ficha["accion"] in ("compartir", "ignorar")
            or ficha["accion"] == "convocar" and ficha["variante"] in ("sin_receptores", "alcance_limitado"))


def sha256(ruta):
    ruta = Path(ruta)
    estado = ruta.stat()
    clave = (str(ruta), estado.st_size, estado.st_mtime_ns)
    if clave not in _HASHES:
        h = hashlib.sha256()
        with ruta.open("rb") as archivo:
            for bloque in iter(lambda: archivo.read(1024*1024), b""):
                h.update(bloque)
        _HASHES[clave] = h.hexdigest()
    return _HASHES[clave]


def preparar_pantallas(identificadores):
    """QWidget se rasteriza una vez en el hilo de QApplication, antes del pool."""
    _fuente(20)
    for identificador in sorted(set(identificadores)):
        imagen_feed(identificador)


def huella_render(render):
    """Incluye el código y el feed real, además de las tres pinturas del plano."""
    imagen = imagen_feed(render.ficha["publicacion"])
    pantalla = hashlib.sha256(imagen.constBits().asstring(imagen.sizeInBytes())).hexdigest()
    rutas = ("cinematica_acciones_visual.py", "cinematica_acciones_extendida_visual.py",
             "cine_telefono.py", "publicaciones_ui.py")
    codigo = "".join(sha256(RAIZ/r) for r in rutas)
    ficha = json.dumps(render.ficha, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256((codigo+ficha+pantalla).encode("utf-8")).hexdigest(), pantalla


def exportar(clave, destino=CARPETA, ancho=1280, fps=FPS, segundos=DURACION, ffmpeg=None,
             renderizador=None, crf=25):
    if not 160 <= ancho <= 1920 or ancho % 2 or not 1 <= fps <= 60 or not 1 <= segundos <= DURACION:
        raise ValueError("Se requiere ancho par de 160–1920, 1–60 fps y 1–9 segundos")
    alto = round(ancho*9/16); alto += alto % 2
    destino = Path(destino); destino.mkdir(parents=True, exist_ok=True)
    libre = shutil.disk_usage(destino).free
    if libre < 4*1024*1024:
        raise OSError(f"Se detiene antes de producir {clave}: sólo quedan {libre} bytes libres")
    render = (renderizador or RenderizadorAccion)(clave)
    firma, pantalla_hash = huella_render(render)
    for fuente in render.fuentes:
        if not fuente.is_file():
            raise FileNotFoundError(f"No se puede producir {clave}: falta {fuente}")
    binario = localizar_ffmpeg(ffmpeg)
    video = destino / f"{clave}.mp4"
    trabajo = destino / f".{clave}.produccion.mp4"
    poster = destino / f"{clave}.jpg"
    inicio = destino / f"{clave}_inicio.png"
    comando = [binario, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
               "-pixel_format", "bgra", "-video_size", f"{ancho}x{alto}", "-framerate", str(fps),
               "-i", "pipe:0", "-an", "-c:v", "libx264", "-preset", "fast", "-crf", str(crf),
               "-threads", "2", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(trabajo)]
    n = round(segundos*fps)
    comienzo = time.monotonic()
    proceso = subprocess.Popen(comando, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        for i in range(n):
            imagen = render.capturar_fotograma(i/fps, (ancho, alto))
            datos = imagen.constBits().asstring(imagen.sizeInBytes())
            if imagen.bytesPerLine() != ancho*4:
                datos = b"".join(datos[y*imagen.bytesPerLine():y*imagen.bytesPerLine()+ancho*4] for y in range(alto))
            proceso.stdin.write(datos)
        proceso.stdin.close()
        error = proceso.stderr.read().decode("utf-8", "replace")
        codigo = proceso.wait()
        if codigo or not trabajo.is_file() or trabajo.stat().st_size < 1024:
            raise RuntimeError(f"FFmpeg falló en {clave}: {error}")
    except BaseException:
        proceso.kill(); proceso.wait(); trabajo.unlink(missing_ok=True)
        raise
    finally:
        if not proceso.stdin.closed:
            proceso.stdin.close()
        proceso.stderr.close()
    comprobacion = subprocess.run([binario, "-hide_banner", "-v", "error", "-i", str(trabajo), "-f", "null", "-"], capture_output=True, text=True)
    if comprobacion.returncode:
        trabajo.unlink(missing_ok=True)
        raise RuntimeError(f"Vídeo truncado o ilegible: {clave}: {comprobacion.stderr}")
    # Este PNG representa exactamente el primer cuadro decodificado, no una
    # pintura distinta ni un póster de la mitad del montaje.
    primer_cuadro = subprocess.run([binario, "-hide_banner", "-loglevel", "error", "-y", "-i", str(trabajo), "-frames:v", "1", "-compression_level", "9", "-update", "1", str(inicio)], capture_output=True, text=True)
    if primer_cuadro.returncode or not inicio.is_file():
        trabajo.unlink(missing_ok=True)
        raise RuntimeError(f"No se pudo extraer el primer cuadro de {clave}: {primer_cuadro.stderr}")
    if not render.capturar_fotograma(min(7.5, segundos-1/fps), (ancho, alto)).save(str(poster), "JPG", 88):
        raise RuntimeError(f"No se pudo guardar la miniatura de {clave}")
    trabajo.replace(video)
    ficha = render.ficha
    registro = dict(clave=clave, publicacion=ficha["publicacion"], accion=ficha["accion"], variante=ficha["variante"],
                    titulo=ficha["titulo"], descripcion_lo_que_se_ve=ficha["descripcion_lo_que_se_ve"],
                    video=video.name, poster=poster.name, inicio=inicio.name, duracion=segundos,
                    fps=fps, ancho=ancho, alto=alto, fotogramas=n, bytes=video.stat().st_size,
                    sha256=sha256(video), poster_sha256=sha256(poster), inicio_sha256=sha256(inicio),
                    inicio_extraido_del_video=True, decodificacion_completa=True, planos=render.planos,
                    render_sha256=firma, pantalla_publicacion=ficha["publicacion"],
                    pantalla_sha256=pantalla_hash,
                    crf=crf, preset="fast",
                    fuentes=[dict(ruta=str(r.relative_to(RAIZ)).replace("\\", "/"), sha256=sha256(r)) for r in render.fuentes])
    print(f"{clave}: {n} fotogramas, {video.stat().st_size/1024:.0f} KiB, {time.monotonic()-comienzo:.1f}s", flush=True)
    return registro


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--todos", action="store_true")
    parser.add_argument("--clave", choices=CINEMATICAS_ACCIONES)
    parser.add_argument("--accion", action="append", choices=ACCIONES_VIDEO,
                        help="Puede repetirse para producir varias acciones disponibles")
    parser.add_argument("--publicacion", type=int)
    parser.add_argument("--sin-variantes", action="store_true",
                        help="Produce sólo el montaje principal de cada acción seleccionada")
    parser.add_argument("--pendientes", action="store_true", help="Omite producciones íntegras del manifiesto anterior")
    parser.add_argument("--destino", type=Path, default=CARPETA)
    parser.add_argument("--ancho", type=int, default=1280)
    parser.add_argument("--fps", type=int, default=FPS)
    parser.add_argument("--segundos", type=float, default=DURACION)
    parser.add_argument("--ffmpeg", type=Path)
    parser.add_argument("--crf", type=int, choices=range(23, 31), default=25)
    parser.add_argument("--telefonos", action="store_true", help="Sólo los 24 montajes con el teléfono que cambia")
    parser.add_argument("--trabajadores", type=int, choices=(1, 2), default=1,
                        help="Dos renderizadores QImage independientes; un único escritor del inventario")
    args = parser.parse_args()
    if not (args.todos or args.clave or args.accion or args.publicacion or args.telefonos):
        parser.error("Elige --todos, --clave, --accion o --publicacion")
    app = QApplication.instance() or QApplication([])
    elegidas = [k for k, v in CINEMATICAS_ACCIONES.items()
                if (not args.clave or k == args.clave) and (not args.accion or v["accion"] in args.accion)
                and (not args.publicacion or v["publicacion"] == args.publicacion)
                and (not args.telefonos or usa_telefono(v))
                and (not args.sin_variantes or not v["variante"])]
    preparar_pantallas(CINEMATICAS_ACCIONES[k]["publicacion"] for k in elegidas)
    args.destino.mkdir(parents=True, exist_ok=True)
    manifest = args.destino/"manifest.json"
    anterior = {}
    if manifest.is_file():
        anterior = {r["clave"]: r for r in json.loads(manifest.read_text(encoding="utf-8")).get("clips", [])}
    pendientes = []
    for clave in elegidas:
        viejo = anterior.get(clave)
        if args.pendientes and viejo and viejo.get("ancho") == args.ancho and viejo.get("fps") == args.fps and viejo.get("duracion") == args.segundos:
            rutas = [(args.destino/viejo[c], viejo.get(c+"_sha256") if c != "video" else viejo.get("sha256")) for c in ("video", "poster", "inicio")]
            fuentes_intactas = all((RAIZ/r["ruta"]).is_file() and sha256(RAIZ/r["ruta"]) == r["sha256"] for r in viejo.get("fuentes", []))
            firma, _ = huella_render(RenderizadorAccion(clave))
            if viejo.get("render_sha256") == firma and viejo.get("crf") == args.crf and fuentes_intactas and all(r.is_file() and sha256(r) == h for r, h in rutas):
                print(f"{clave}: íntegro, se conserva", flush=True)
                continue
        pendientes.append(clave)
    # Registrar tipografías en el hilo de QApplication antes de dibujar QImages
    # independientes. Sólo el hilo principal escribe el manifiesto, por lo que
    # no hay dos escritores compitiendo ni se necesita un cerrojo del sistema.
    _fuente(20)
    with ThreadPoolExecutor(max_workers=args.trabajadores) as pool:
        trabajos = {pool.submit(exportar, clave, args.destino, args.ancho, args.fps, args.segundos, args.ffmpeg, crf=args.crf): clave for clave in pendientes}
        for trabajo in as_completed(trabajos):
            clave = trabajos[trabajo]
            anterior[clave] = trabajo.result()
            documento = dict(version=2, tecnica="Ilustraciones originales generadas con OpenAI ImageGen, montaje de tres planos, cámara y objetos animados QPainter; teléfonos físicos con la publicación canónica de Civitas; exportación local H.264, sin audio incrustado.",
                             autoria="CIVICA — Alcalde Digital", criterios="Se selecciona por registro de decisión real. Reporte rechazado conserva el contenido y convocatoria sin receptores no muestra personas reunidas. El grupo limitado recibe invitaciones, sin una multitud mayor que sus receptores. No se afirma que un proyecto esté construido ni que un rumor sea verdadero.",
                             tipografia=dict(familia="Atkinson Hyperlegible", licencia="SIL Open Font License 1.1", archivo="assets/fuentes/OFL.txt"),
                             clips=[anterior[k] for k in CINEMATICAS_ACCIONES if k in anterior])
            temporal = manifest.with_suffix(".tmp.json")
            temporal.write_text(json.dumps(documento, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
            temporal.replace(manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
