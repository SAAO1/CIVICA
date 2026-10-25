"""Exporta doce conversaciones a H.264 por streaming y reanuda por hashes.

Ejemplo: python -B herramientas/producir_personajes_extension.py --todos
No guarda secuencias de imágenes: sólo MP4, cartel y PNG del primer frame real.
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

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication
from cinematica_personajes_extendida_visual import CARPETA, DURACION, FPS, RenderizadorPersonajeExtendido
from juego.cinematica_personajes_extendida import CINEMATICAS_PERSONAJES_EXTENDIDAS
from herramientas.exportar_ambientes import localizar_ffmpeg


def _hash(ruta):
    resumen = hashlib.sha256()
    with Path(ruta).open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024*1024), b""):
            resumen.update(bloque)
    return resumen.hexdigest()


def _hash_entrada(render):
    fuentes = [RAIZ/"cinematica_personajes_extendida_visual.py",
               RAIZ/"juego/cinematica_personajes_extendida.py", Path(__file__), *render.fuentes]
    contenido = json.dumps({"clave": render.clave, "entrada": render.entrada,
                            "fps": FPS, "duracion": DURACION, "crf": 28, "preset": "medium"},
                           ensure_ascii=False, sort_keys=True)
    return hashlib.sha256((contenido+"".join(_hash(r) for r in fuentes)).encode()).hexdigest()


def _verificar(video, ffmpeg):
    salida = subprocess.run([ffmpeg, "-hide_banner", "-v", "error", "-i", str(video),
                             "-f", "null", "-"], capture_output=True, text=True)
    if salida.returncode or salida.stderr.strip():
        raise RuntimeError(f"No se decodifica íntegro {video.name}: {salida.stderr}")


def _inicio_real(video, destino, ffmpeg):
    salida = subprocess.run([ffmpeg, "-hide_banner", "-v", "error", "-y", "-i", str(video),
                             "-frames:v", "1", "-update", "1", "-pix_fmt", "rgb24",
                             "-compression_level", "9", str(destino)], capture_output=True, text=True)
    if salida.returncode or not destino.is_file():
        raise RuntimeError(f"No se pudo extraer el frame cero: {salida.stderr}")


def producir(clave, ffmpeg, anterior=None, forzar=False, verificar=False):
    render = RenderizadorPersonajeExtendido(clave)
    entrada_hash = _hash_entrada(render)
    archivos = {tipo: CARPETA/f"{clave}{sufijo}" for tipo, sufijo in
                (("video", ".mp4"), ("poster", ".jpg"), ("inicio", "_inicio.png"))}
    if (not forzar and anterior and anterior.get("entrada_sha256") == entrada_hash
            and anterior.get("decodificacion_completa") is True
            and all(r.is_file() and _hash(r) == anterior.get(tipo+"_sha256")
                    for tipo, r in archivos.items())):
        if verificar:
            _verificar(archivos["video"], ffmpeg)
        print(f"{clave}: vigente, hashes coinciden", flush=True)
        return anterior
    comienzo = time.monotonic()
    temporal = CARPETA/f".{clave}.produccion.mp4"
    proceso = subprocess.Popen(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
         "-pixel_format", "bgra", "-video_size", "1280x720", "-framerate", str(FPS),
         "-i", "pipe:0", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "28",
         "-threads", "2", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(temporal)],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        for i in range(round(FPS*DURACION)):
            img = render.capturar_fotograma(i/FPS)
            proceso.stdin.write(img.constBits().asstring(img.sizeInBytes()))
        proceso.stdin.close()
        error = proceso.stderr.read().decode("utf-8", "replace")
        if proceso.wait() or temporal.stat().st_size < 1024:
            raise RuntimeError(error)
        _verificar(temporal, ffmpeg)
        temporal.replace(archivos["video"])
    except BaseException:
        proceso.kill(); proceso.wait(); temporal.unlink(missing_ok=True)
        raise
    finally:
        if not proceso.stdin.closed:
            proceso.stdin.close()
        proceso.stderr.close()
    if not render.capturar_fotograma(4.2).save(str(archivos["poster"]), "JPG", 85):
        raise RuntimeError(f"No se pudo guardar el cartel de {clave}")
    _inicio_real(archivos["video"], archivos["inicio"], ffmpeg)
    registro = {"clave": clave, "publicacion": render.identificador,
                "nombre": render.entrada["nombre"], "texto": render.entrada["texto"],
                "titulo": render.entrada["titulo"], "duracion": DURACION, "fps": FPS,
                "fotogramas": round(FPS*DURACION), "ancho": 1280, "alto": 720,
                "entrada_sha256": entrada_hash, "decodificacion_completa": True,
                "inicio_extraido_del_video": True,
                "fuentes": [{"ruta": r.relative_to(RAIZ).as_posix(), "sha256": _hash(r)}
                            for r in render.fuentes]}
    for tipo, ruta in archivos.items():
        registro[tipo] = ruta.name
        registro[tipo+"_sha256"] = _hash(ruta)
        registro[tipo+"_bytes"] = ruta.stat().st_size
    registro["sha256"] = registro["video_sha256"]
    registro["bytes"] = registro["video_bytes"]
    print(f"{clave}: {registro['fotogramas']} frames, "
          f"{sum(r.stat().st_size for r in archivos.values())/1048576:.2f} MiB, "
          f"{time.monotonic()-comienzo:.1f}s", flush=True)
    return registro


def _documentar_procedencia():
    original = RAIZ/"assets/expansion/siete_actos"
    pinturas = json.loads((original/"ilustraciones/prompts.json").read_text(encoding="utf-8"))
    procedencia = {
        "fecha": "2026-10-24", "nueva_generacion_ia": False,
        "tecnica": "Cámara y composición QPainter, dos poses faciales existentes y objetos físicos del lugar; H.264 local.",
        "limite": "Cine ilustrado; no contiene animación corporal sintetizada ni vídeo importado.",
        "prompts_originales_pinturas": pinturas["assets"],
        "prompts_personajes": "assets/expansion/siete_actos/personajes/prompts.json",
        "prompts_poses_faciales": "assets/expansion/siete_actos/personajes/prompts_animacion.json",
        "fuentes_poses": "assets/expansion/siete_actos/personajes/manifest_animacion.json",
        "animacion_nueva": "cinematica_personajes_extendida_visual.py",
        "voz": "El juego reproduce la voz neuronal exacta del guion; los MP4 no agregan otra pista.",
    }
    (CARPETA/"procedencia.json").write_text(json.dumps(procedencia, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--todos", action="store_true")
    parser.add_argument("--clave", action="append", choices=CINEMATICAS_PERSONAJES_EXTENDIDAS)
    parser.add_argument("--forzar", action="store_true")
    parser.add_argument("--verificar", action="store_true")
    parser.add_argument("--ffmpeg")
    opciones = parser.parse_args()
    app = QApplication.instance() or QApplication([])
    CARPETA.mkdir(parents=True, exist_ok=True)
    ffmpeg = localizar_ffmpeg(opciones.ffmpeg)
    ruta_manifest = CARPETA/"manifest.json"
    anterior = json.loads(ruta_manifest.read_text(encoding="utf-8")) if ruta_manifest.is_file() else {}
    clips = {r["clave"]: r for r in anterior.get("clips", [])}
    _documentar_procedencia()
    for clave in opciones.clave or CINEMATICAS_PERSONAJES_EXTENDIDAS:
        clips[clave] = producir(clave, ffmpeg, clips.get(clave), opciones.forzar, opciones.verificar)
        manifest = {"version": 1, "tecnica": "Cine ilustrado contextual con cámara, rostros y luz de escena",
                    "procedencia": "procedencia.json", "codec": "h264", "pixel_format": "yuv420p",
                    "crf": 28, "preset": "medium",
                    "clips": [clips[k] for k in CINEMATICAS_PERSONAJES_EXTENDIDAS if k in clips]}
        temporal = ruta_manifest.with_suffix(".json.tmp")
        temporal.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        temporal.replace(ruta_manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
