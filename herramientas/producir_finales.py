"""Produce y decodifica las cuatro investiduras y el recuento: MP4 locales."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication
from cinematica_final_visual import CARPETA, CLIPS, DURACION, FPS, RenderizadorFinal
from herramientas.exportar_ambientes import localizar_ffmpeg
from herramientas.producir_cinematicas import guardar_portada_inicio


def producir(clave, ffmpeg):
    render = RenderizadorFinal(clave)
    video = CARPETA / f"{clave}.mp4"
    temporal = CARPETA / f".{clave}.produccion.mp4"
    poster = CARPETA / f"{clave}.jpg"
    proceso = subprocess.Popen([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pixel_format", "bgra", "-video_size", "1280x720", "-framerate", str(FPS), "-i", "pipe:0", "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "24", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(temporal)], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        for i in range(round(DURACION*FPS)):
            imagen = render.capturar_fotograma(i/FPS)
            proceso.stdin.write(imagen.constBits().asstring(imagen.sizeInBytes()))
        proceso.stdin.close()
        error = proceso.stderr.read().decode("utf-8", "replace")
        if proceso.wait():
            raise RuntimeError(error)
        decodificar = subprocess.run([ffmpeg, "-v", "error", "-i", str(temporal), "-f", "null", "-"], capture_output=True, text=True)
        if decodificar.returncode:
            raise RuntimeError(decodificar.stderr)
        temporal.replace(video)
    except BaseException:
        proceso.kill()
        proceso.wait()
        temporal.unlink(missing_ok=True)
        raise
    finally:
        if not proceso.stdin.closed:
            proceso.stdin.close()
        proceso.stderr.close()
    if not render.capturar_fotograma(8.5).save(str(poster), "JPG", 88):
        raise RuntimeError(f"No se pudo guardar {poster}")
    portada = guardar_portada_inicio(video, CARPETA / f"{clave}_inicio.png", ffmpeg)
    registro = dict(clave=clave, video=video.name, poster=poster.name,
                    inicio=portada.name, inicio_sha256=hashlib.sha256(portada.read_bytes()).hexdigest(),
                    duracion=DURACION, fps=FPS, ancho=1280, alto=720, fotogramas=round(DURACION*FPS), bytes=video.stat().st_size, sha256=hashlib.sha256(video.read_bytes()).hexdigest(), decodificacion_completa=True, fuentes=[dict(ruta=r.relative_to(RAIZ).as_posix(), sha256=hashlib.sha256(r.read_bytes()).hexdigest()) for r in render.fuentes])
    print(f"{clave}: {registro['fotogramas']} fotogramas · {registro['bytes']} bytes", flush=True)
    return registro


def main():
    app = QApplication.instance() or QApplication([])
    CARPETA.mkdir(parents=True, exist_ok=True)
    ffmpeg = localizar_ffmpeg()
    clips = []
    for clave in CLIPS:
        clips.append(producir(clave, ffmpeg))
        (CARPETA / "manifest.json").write_text(json.dumps(dict(version=1, tecnica="Retratos originales de investidura y plaza nocturna; cámara, acta, firma ilustrativa, confeti y luces animados con QPainter. MP4 H.264 sin audio; mezcla musical del juego.", criterio="Se reproduce exclusivamente el desenlace real de la partida. Un empate muestra recuento, sin proclamar ganador.", tipografia="Atkinson Hyperlegible · SIL Open Font License 1.1 · assets/fuentes/OFL.txt", clips=clips), ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
