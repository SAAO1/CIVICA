"""Exporta cuatro primeros planos originales, sin rótulos, botones ni sonido.

Uso: python -X utf8 -B herramientas/producir_primeros_planos.py
Sólo escribe assets/novela/prologo/videos; conserva intactas sus cuatro CG.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QColor, QImage, QPainter, QRadialGradient
from PyQt6.QtWidgets import QApplication

from herramientas.exportar_ambientes import localizar_ffmpeg
from herramientas.producir_pulido_visual import cuadro_decodificado, ejecutar, huella, inventario

SALIDA = RAIZ / "assets/novela/prologo"
ACTORES = ("juan", "adrian", "laura", "camila")
ANCHO, ALTO, FPS, SEGUNDOS = 1280, 720, 24, 6


def destino(nombre):
    carpeta = (SALIDA / "videos").resolve()
    ruta = (carpeta / nombre).resolve()
    if not ruta.is_relative_to(carpeta):
        raise ValueError("El archivo debe permanecer en prologo/videos")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    return ruta


def encuadre(imagen, segundo):
    """Desplazamiento cíclico sin deformación; deja margen sobre el cabello."""
    if imagen.isNull():
        raise ValueError("No se puede encuadrar una CG vacía")
    fase = 2*math.pi*(float(segundo) % SEGUNDOS)/SEGUNDOS
    zoom = 1.012+.008*(1-math.cos(fase))/2
    escala = max(ANCHO/imagen.width(), ALTO/imagen.height())*zoom
    ancho, alto = ANCHO/escala, ALTO/escala
    libre_x, libre_y = imagen.width()-ancho, imagen.height()-alto
    x = libre_x*(.5+.15*math.sin(fase))
    y = libre_y*(.10+.04*math.sin(fase))
    return QRectF(x, y, ancho, alto)


def fotograma(imagen, segundo):
    """Sólo cámara y variación tenue de la luz sobre la ilustración original."""
    salida = QImage(ANCHO, ALTO, QImage.Format.Format_RGB32)
    salida.fill(QColor("#131a2c"))
    p = QPainter(salida)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    p.drawImage(QRectF(0, 0, ANCHO, ALTO), imagen, encuadre(imagen, segundo))
    fase = 2*math.pi*(float(segundo) % SEGUNDOS)/SEGUNDOS
    centro = QPointF(ANCHO*(.78+.025*math.sin(fase)), ALTO*.22)
    luz = QRadialGradient(centro, ANCHO*.65)
    luz.setColorAt(0, QColor(246, 213, 151, round(4+2*math.sin(fase))))
    luz.setColorAt(1, QColor(246, 213, 151, 0))
    p.fillRect(salida.rect(), luz)
    p.end()
    return salida


def _diferencia(a, b):
    # Muestreo RGB repartido por el cuadro; no basta comparar metadatos del MP4.
    return sum(abs(x-y) for x, y in zip(a[::97], b[::97]))/len(a[::97])


def exportar(ffmpeg, imagen, actor):
    if actor not in ACTORES:
        raise ValueError("Candidato no reconocido")
    ruta = destino(actor+".mp4")
    temporal = destino(actor+".parcial.mp4")
    proceso = subprocess.Popen([
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
        "-pixel_format", "bgra", "-video_size", f"{ANCHO}x{ALTO}",
        "-framerate", str(FPS), "-i", "pipe:0", "-an", "-c:v", "libx264",
        "-preset", "fast", "-crf", "20", "-threads", "2", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(temporal),
    ], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        for indice in range(FPS*SEGUNDOS):
            cuadro = fotograma(imagen, indice/FPS)
            proceso.stdin.write(cuadro.constBits().asstring(cuadro.sizeInBytes()))
        proceso.stdin.close()
        errores = proceso.stderr.read()
        if proceso.wait(timeout=120):
            raise RuntimeError(errores.decode(errors="replace"))
    except BaseException:
        if not proceso.stdin.closed:
            proceso.stdin.close()
        if proceso.poll() is None:
            proceso.terminate()
            proceso.wait(timeout=10)
        raise
    finally:
        proceso.stderr.close()
    temporal.replace(ruta)
    lectura = ejecutar([ffmpeg, "-v", "error", "-i", str(ruta), "-progress", "pipe:1",
                        "-nostats", "-f", "null", "-"]).stdout.decode()
    conteos = [int(linea.split("=", 1)[1]) for linea in lectura.splitlines()
               if linea.startswith("frame=")]
    if not conteos or conteos[-1] != FPS*SEGUNDOS:
        raise ValueError("No se pudieron decodificar los 144 cuadros de "+actor)
    muestras = [cuadro_decodificado(ffmpeg, ruta, segundo) for segundo in (0, 3, 5)]
    firmas = [hashlib.sha256(datos).hexdigest() for datos in muestras]
    diferencias = [_diferencia(muestras[0], datos) for datos in muestras[1:]]
    if len(set(firmas)) != 3 or min(diferencias) <= .2:
        raise ValueError("La cámara no produce movimiento visible en "+actor)
    inicio, poster = destino(actor+"_inicio.png"), destino(actor+"_poster.jpg")
    for archivo, datos, formato, calidad in (
        (inicio, muestras[0], "PNG", -1), (poster, muestras[1], "JPG", 94),
    ):
        cuadro = QImage(datos, ANCHO, ALTO, ANCHO*3, QImage.Format.Format_RGB888).copy()
        if not cuadro.save(str(archivo), formato, calidad):
            raise RuntimeError("No se pudo guardar "+str(archivo))
    print(actor+": 144 fotogramas completos; inicio, cartel y movimiento verificados", flush=True)
    return inventario(
        ruta, clave=actor, cg=actor, ancho=ANCHO, alto=ALTO, fps=FPS, duracion=float(SEGUNDOS),
        fotogramas=conteos[-1], audio=False, textos=[], botones=False, decodificacion_completa=True,
        primer_fotograma=inventario(inicio), poster=inventario(poster),
        movimiento={"segundos":[0, 3, 5], "rgb_sha256":firmas,
                    "diferencia_rgb_media":diferencias, "camara_ciclica":True},
    )


def producir():
    app = QApplication.instance() or QApplication([])
    procedencia = SALIDA / "origen_arte.json"
    origen = json.loads(procedencia.read_text(encoding="utf-8"))
    imagenes, cg = [], []
    for actor in ACTORES:
        ruta = SALIDA / "cg" / (actor+".png")
        imagen = QImage(str(ruta))
        if imagen.isNull():
            raise FileNotFoundError("Falta la CG original de "+actor)
        referencia = next((r for r in origen.get("recursos", []) if r.get("id") == actor), None)
        if referencia is None or referencia.get("sha256") != huella(ruta):
            raise ValueError("La procedencia no coincide con la CG de "+actor)
        imagenes.append(imagen)
        cg.append(inventario(ruta, id=actor, ancho=imagen.width(), alto=imagen.height()))
    ffmpeg = localizar_ffmpeg()
    videos = [exportar(ffmpeg, imagen, actor) for imagen, actor in zip(imagenes, ACTORES)]
    for fuente in cg:
        if huella(RAIZ/fuente["archivo"]) != fuente["sha256"]:
            raise ValueError("Una CG cambió durante la exportación")
    manifest = {
        "version":1, "generado_utc":datetime.now(timezone.utc).isoformat(),
        "productor":inventario(Path(__file__)),
        "dependencias":[inventario(RAIZ/"herramientas/producir_pulido_visual.py")],
        "metodo":"Cámara cíclica y luz tenue con QPainter sobre cuatro CG originales de ImageGen; H.264 por FFmpeg. Sin rótulos, botones, deformación facial ni video generativo.",
        "audio":"Sin pista de audio; el doblaje neural se conserva por separado.",
        "archivo_procedencia":inventario(procedencia), "origen_arte":origen,
        "cg":cg, "videos":videos,
    }
    destino("manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print("Manifiesto independiente: assets/novela/prologo/videos/manifest.json", flush=True)
    return manifest


if __name__ == "__main__":
    producir()
