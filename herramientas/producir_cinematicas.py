"""Exporta los insertos del narrador y personajes a MP4 H.264 y cartel JPG.

python -B herramientas/producir_cinematicas.py --todos
No conserva fotogramas de trabajo: envía BGRA por pipe a FFmpeg. El juego sólo
necesita los MP4/JPG terminados, no esta herramienta ni FFmpeg.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from PyQt6.QtWidgets import QApplication
from cinematica_visual import CLIPS, DURACION, FPS, CARPETA, RenderizadorCinematica
from herramientas.exportar_ambientes import localizar_ffmpeg


def _hash(ruta):
    h = hashlib.sha256()
    with Path(ruta).open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024*1024), b""):
            h.update(bloque)
    return h.hexdigest()


def guardar_portada_inicio(video, destino, ffmpeg):
    """Extrae el frame 0 del MP4 terminado, incluyendo su conversión de color.

    El render original y el H.264 pueden diferir por la compresión y el color
    YUV. La cubierta debe corresponder al vídeo que realmente se decodifica.
    El cartel de accesibilidad se produce por separado en un plano legible.
    """
    resultado = subprocess.run(
        [str(ffmpeg), "-hide_banner", "-v", "error", "-y", "-i", str(video),
         "-frames:v", "1", "-update", "1", "-pix_fmt", "rgb24", str(destino)],
        capture_output=True, text=True)
    if resultado.returncode or not Path(destino).is_file():
        raise RuntimeError(f"No se pudo extraer la portada inicial de {video}: {resultado.stderr}")
    return Path(destino)


def exportar(clave, destino=CARPETA, ancho=1280, fps=FPS, segundos=DURACION, ffmpeg=None):
    alto = round(ancho*9/16)
    alto += alto % 2
    if ancho % 2 or not 160 <= ancho <= 1920 or not 1 <= fps <= 60 or not 1 <= segundos <= DURACION:
        raise ValueError("Usa ancho par de 160–1920, 1–60 fps y duración de 1–12 s")
    render = RenderizadorCinematica(clave)
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    video = destino / f"{clave}.mp4"
    trabajo = destino / f".{clave}.produccion.mp4"
    poster = destino / f"{clave}.jpg"
    binario = localizar_ffmpeg(ffmpeg)
    comando = [binario, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
               "-pixel_format", "bgra", "-video_size", f"{ancho}x{alto}",
               "-framerate", str(fps), "-i", "pipe:0", "-an", "-c:v", "libx264",
               "-preset", "fast", "-crf", "25", "-pix_fmt", "yuv420p",
               "-movflags", "+faststart", str(trabajo)]
    n = round(segundos*fps)
    inicio = time.monotonic()
    proceso = subprocess.Popen(comando, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                               stderr=subprocess.PIPE)
    try:
        for i in range(n):
            img = render.capturar_fotograma(i/fps, (ancho, alto))
            datos = img.constBits().asstring(img.sizeInBytes())
            if img.bytesPerLine() != ancho*4:
                datos = b"".join(datos[y*img.bytesPerLine():y*img.bytesPerLine()+ancho*4]
                                  for y in range(alto))
            proceso.stdin.write(datos)
        proceso.stdin.close()
        error = proceso.stderr.read().decode("utf-8", "replace")
        codigo = proceso.wait()
        if codigo or not trabajo.is_file() or trabajo.stat().st_size < 1024:
            raise RuntimeError(f"FFmpeg falló al crear {clave}: {error}")
    except BaseException:
        proceso.kill()
        proceso.wait()
        trabajo.unlink(missing_ok=True)
        raise
    finally:
        if not proceso.stdin.closed:
            proceso.stdin.close()
        proceso.stderr.close()
    if not render.capturar_fotograma(6.5, (ancho, alto)).save(str(poster), "JPG", 87):
        raise RuntimeError(f"No se pudo guardar el cartel de {clave}")
    # La decodificación completa detecta archivos truncados, no sólo cabeceras.
    comprobacion = subprocess.run([binario, "-hide_banner", "-v", "error", "-i", str(trabajo),
                                  "-f", "null", "-"], capture_output=True, text=True)
    if comprobacion.returncode:
        trabajo.unlink(missing_ok=True)
        raise RuntimeError(f"El vídeo {clave} no se decodifica: {comprobacion.stderr}")
    trabajo.replace(video)
    portada = guardar_portada_inicio(video, destino / f"{clave}_inicio.png", binario)
    registro = dict(clave=clave, titulo=CLIPS[clave]["titulo"], video=video.name,
                    poster=poster.name, inicio=portada.name, inicio_sha256=_hash(portada),
                    duracion=segundos, fps=fps, ancho=ancho, alto=alto,
                    fotogramas=n, bytes=video.stat().st_size, sha256=_hash(video),
                    poster_sha256=_hash(poster), decodificacion_completa=True,
                    tecnica="Ilustración pintada + objetos animados con QPainter + cámara y disoluciones; H.264 local",
                    fuentes=[dict(ruta=str(r.relative_to(RAIZ)).replace("\\", "/"),
                                  sha256=_hash(r)) for r in render.fuentes])
    print(f"{clave}: {n} fotogramas, {video.stat().st_size/1024:.0f} KiB, {time.monotonic()-inicio:.1f}s", flush=True)
    return registro


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--todos", action="store_true")
    parser.add_argument("--personajes", action="store_true",
                        help="Exporta sólo los doce insertos de ciudadano y periodista")
    parser.add_argument("--rol", choices=("todos", "ciudadano", "periodista"), default="todos",
                        help="Filtra --personajes por el personaje que habla")
    parser.add_argument("--clave", choices=CLIPS, default="ciudad_48h")
    parser.add_argument("--destino", type=Path, default=CARPETA)
    parser.add_argument("--ancho", type=int, default=1280)
    parser.add_argument("--fps", type=int, default=FPS)
    parser.add_argument("--segundos", type=float, default=DURACION)
    parser.add_argument("--ffmpeg", type=Path)
    args = parser.parse_args()
    app = QApplication.instance() or QApplication([])
    elegidas = ([k for k in CLIPS if k.startswith("person_")] if args.personajes
                else list(CLIPS) if args.todos else [args.clave])
    if args.personajes and args.rol != "todos":
        sufijo = "_c" if args.rol == "ciudadano" else "_p"
        elegidas = [k for k in elegidas if k.endswith(sufijo)]
    manifest = args.destino / "manifest.json"
    anterior = {}
    if manifest.is_file():
        anterior = {r["clave"]: r for r in json.loads(manifest.read_text(encoding="utf-8")).get("clips", [])}
    for clave in elegidas:
        anterior[clave] = exportar(clave, args.destino, args.ancho, args.fps, args.segundos, args.ffmpeg)
        documento = dict(version=2, tecnica="Animación cinematográfica compuesta, sin audio incrustado; voces de narrador y personajes y ambientes separados en el juego.",
                         autoria="CIVICA: ilustraciones del paquete y nuevas pinturas generadas con OpenAI ImageGen; animación original QPainter.",
                         tipografia=dict(familia="Atkinson Hyperlegible", licencia="SIL Open Font License 1.1", archivo="assets/fuentes/OFL.txt"),
                         criterios="Representaciones del contexto del guion; los rumores se rotulan como mensajes sin fuente, sin afirmar su contenido.",
                         clips=[anterior[k] for k in CLIPS if k in anterior])
        manifest.write_text(json.dumps(documento, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
