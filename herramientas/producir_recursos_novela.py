"""Exporta planos nativos de cuatro CG para los seis actos de la novela.

Uso: python -X utf8 -B herramientas/producir_recursos_novela.py
Opcional: --origen-imagenes CARPETA con los PNG originales de ImageGen.
Solo escribe dentro de assets/novela. Conserva las pinturas de origen intactas.
No sintetiza voz ni exporta audio. El doblaje neural original queda en su catálogo.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QImage, QLinearGradient, QPainter, QPen
from PyQt6.QtWidgets import QApplication
from herramientas.exportar_ambientes import localizar_ffmpeg

SALIDA = RAIZ / "assets/novela"
MAPA_ACTOS = ("archivo", "parque", "redaccion", "redaccion", "urnas", "urnas")
CASOS = (50, 90, 110, 40, 120, 35)
ORIGINALES = {
    "archivo": "exec-f5f54208-5875-407d-b53d-5092e2aa0974.png",
    "redaccion": "exec-3e60d192-c001-4d7d-b9a3-d1ef662d6fa7.png",
    "parque": "exec-01a8e14c-9a94-4356-a861-4586b3d36705.png",
    "urnas": "exec-75adbcc7-8e3e-4b2c-97a2-77bac8807f7c.png",
}
ANCHO, ALTO, FPS, SEGUNDOS = 1280, 720, 24, 4


def sha256(ruta):
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def relativa(ruta):
    return Path(ruta).resolve().relative_to(RAIZ.resolve()).as_posix()


def inventariar(ruta, **datos):
    ruta = Path(ruta)
    return dict(archivo=relativa(ruta), sha256=sha256(ruta),
                bytes=ruta.stat().st_size, **datos)


def destino(relativo):
    ruta = (SALIDA / relativo).resolve()
    if not ruta.is_relative_to(SALIDA.resolve()):
        raise ValueError("La salida debe permanecer dentro de assets/novela")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    return ruta


def importar_cg(carpeta):
    entradas = []
    for nombre, archivo in ORIGINALES.items():
        ruta = destino(f"cg/{nombre}.png")
        fuente = carpeta / archivo if carpeta else None
        if not ruta.exists():
            if fuente is None or not fuente.is_file():
                raise FileNotFoundError(f"Falta {ruta}; indica --origen-imagenes con los originales")
            shutil.copyfile(fuente, ruta)
        if fuente is not None and fuente.is_file() and sha256(fuente) != sha256(ruta):
            raise ValueError(f"La CG {nombre} difiere del original; no se sobrescribe")
        imagen = QImage(str(ruta))
        if imagen.isNull():
            raise ValueError(f"No se puede decodificar la CG {nombre}")
        entradas.append(inventariar(ruta, id=nombre, ancho=imagen.width(), alto=imagen.height(),
                                   original=archivo, tratamiento="Copia íntegra del PNG de ImageGen"))
    return entradas


def fotograma(imagen, segundo, acto):
    """Cámara y luz periódicas; la pintura se compone sin alterarla en disco."""
    fase = 2 * math.pi * segundo / SEGUNDOS
    zoom = 1.045 + 0.015 * math.cos(fase + acto * 0.39)
    proporcion = ANCHO / ALTO
    if imagen.width() / imagen.height() > proporcion:
        alto = imagen.height() / zoom
        ancho = alto * proporcion
    else:
        ancho = imagen.width() / zoom
        alto = ancho / proporcion
    libre_x = (imagen.width() - ancho) / 2
    libre_y = (imagen.height() - alto) / 2
    centro_x = imagen.width() / 2 + libre_x * 0.48 * math.sin(fase + acto * 0.71)
    centro_y = imagen.height() / 2 + libre_y * 0.35 * math.cos(fase + acto * 0.37)
    salida = QImage(ANCHO, ALTO, QImage.Format.Format_ARGB32)
    salida.fill(QColor("#101e24"))
    pintor = QPainter(salida)
    pintor.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
    pintor.drawImage(QRectF(0, 0, ANCHO, ALTO), imagen,
                    QRectF(centro_x-ancho/2, centro_y-alto/2, ancho, alto))
    # Una luz cálida cambia de forma gradual; no es un flash ni un filtro opaco.
    luz = QLinearGradient(0, 0, ANCHO, ALTO)
    calidez = int(9 + 5 * math.sin(fase + acto))
    luz.setColorAt(0, QColor(255, 205, 137, calidez))
    luz.setColorAt(0.55, QColor(255, 230, 174, 2))
    luz.setColorAt(1, QColor(7, 27, 43, 16))
    pintor.fillRect(QRectF(0, 0, ANCHO, ALTO), luz)
    generador = random.Random(7100 + acto)
    pintor.setPen(QPen(Qt.PenStyle.NoPen))
    for _ in range(24):
        base_x, base_y = generador.random()*ANCHO, generador.random()*ALTO
        desfase = generador.random()*math.tau
        radio = generador.uniform(0.7, 1.9)
        x = base_x + 12*math.sin(fase+desfase)
        y = base_y + 9*math.cos(fase+desfase)
        alpha = int(15+13*(1+math.sin(fase+desfase))/2)
        pintor.setBrush(QColor(255, 232, 177, alpha))
        pintor.drawEllipse(QPointF(x, y), radio, radio)
    pintor.end()
    return salida


def ejecutar(comando):
    return subprocess.run(comando, check=True, capture_output=True)


def decodificar_cuadro(ffmpeg, ruta, segundo):
    resultado = ejecutar([ffmpeg, "-v", "error", "-ss", str(segundo), "-i", str(ruta),
                          "-frames:v", "1", "-pix_fmt", "rgb24", "-f", "rawvideo", "-"])
    if len(resultado.stdout) != ANCHO*ALTO*3:
        raise ValueError(f"Fotograma incompleto en {ruta.name}")
    return resultado.stdout


def exportar_video(ffmpeg, imagen, acto, nombre):
    ruta = destino(f"videos/acto_{acto}.mp4")
    temporal = destino(f"videos/acto_{acto}.temporal.mp4")
    comando = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
               "-pixel_format", "bgra", "-video_size", f"{ANCHO}x{ALTO}",
               "-framerate", str(FPS), "-i", "pipe:0", "-an", "-c:v", "libx264",
               "-preset", "fast", "-crf", "24", "-threads", "2", "-pix_fmt", "yuv420p",
               "-movflags", "+faststart", str(temporal)]
    proceso = subprocess.Popen(comando, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                               stderr=subprocess.PIPE)
    try:
        for cuadro in range(FPS*SEGUNDOS):
            frame = fotograma(imagen, cuadro/FPS, acto)
            proceso.stdin.write(frame.constBits().asstring(frame.sizeInBytes()))
        proceso.stdin.close()
        errores = proceso.stderr.read()
        if proceso.wait(timeout=90):
            raise RuntimeError(errores.decode("utf-8", errors="replace"))
    except BaseException:
        if proceso.poll() is None:
            proceso.terminate()
            proceso.wait(timeout=10)
        raise
    finally:
        proceso.stderr.close()
    temporal.replace(ruta)
    # Decodificación completa, no basta con que exista una cabecera MP4.
    lectura = ejecutar([ffmpeg, "-hide_banner", "-loglevel", "error", "-i", str(ruta),
                         "-progress", "pipe:1", "-nostats", "-f", "null", "-"])
    cuentas = [int(line.split("=", 1)[1]) for line in lectura.stdout.decode().splitlines()
               if line.startswith("frame=")]
    if not cuentas or cuentas[-1] != FPS*SEGUNDOS:
        raise ValueError(f"El clip {acto} no contiene los {FPS*SEGUNDOS} cuadros completos")
    primero = decodificar_cuadro(ffmpeg, ruta, 0)
    medio = decodificar_cuadro(ffmpeg, ruta, 2)
    if primero == medio:
        raise ValueError(f"El plano {acto} no contiene movimiento real")
    png = destino(f"videos/acto_{acto}_inicio.png")
    jpg = destino(f"videos/acto_{acto}_preview.jpg")
    inicio = QImage(primero, ANCHO, ALTO, ANCHO*3, QImage.Format.Format_RGB888).copy()
    preview = QImage(medio, ANCHO, ALTO, ANCHO*3, QImage.Format.Format_RGB888).copy()
    if not inicio.save(str(png)) or not preview.save(str(jpg), "JPG", 86):
        raise RuntimeError("No se pudo guardar una vista previa")
    print(f"Acto {acto}: {nombre}, {cuentas[-1]} cuadros decodificados", flush=True)
    return inventariar(ruta, acto=acto, caso_id=CASOS[acto-1], cg=nombre,
                       ancho=ANCHO, alto=ALTO, fps=FPS, duracion=float(SEGUNDOS),
                       fotogramas=cuentas[-1], audio=False, decodificacion_completa=True,
                       movimiento={"segundos":[0,2],
                                   "rgb_sha256":[hashlib.sha256(x).hexdigest() for x in (primero,medio)]},
                       primer_fotograma=inventariar(png), preview=inventariar(jpg))


def exportar_gif(ffmpeg):
    ruta = destino("portada_animada.gif")
    filtros = ("[0:v]fps=12,scale=640:360:flags=lanczos,split[a][b];"
               "[a]palettegen=max_colors=128:stats_mode=diff[p];"
               "[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle")
    ejecutar([ffmpeg, "-v", "error", "-y", "-i", str(destino("videos/acto_1.mp4")),
              "-filter_complex", filtros, "-loop", "0", str(ruta)])
    ejecutar([ffmpeg, "-v", "error", "-i", str(ruta), "-f", "null", "-"])
    return inventariar(ruta, ancho=640, alto=360, fps=12, fotogramas=48,
                       duracion=float(SEGUNDOS), bucle=True, decodificacion_completa=True)


def producir(carpeta=None):
    app = QApplication.instance() or QApplication([])
    ffmpeg = localizar_ffmpeg()
    ilustraciones = importar_cg(carpeta)
    videos = []
    for acto, nombre in enumerate(MAPA_ACTOS, 1):
        imagen = QImage(str(SALIDA/f"cg/{nombre}.png"))
        videos.append(exportar_video(ffmpeg, imagen, acto, nombre))
    gif = exportar_gif(ffmpeg)
    procedencia = SALIDA / "origen_arte.json"
    if not procedencia.is_file():
        raise FileNotFoundError("Falta origen_arte.json con los prompts reales del arte")
    origen = json.loads(procedencia.read_text(encoding="utf-8"))
    ids = {entrada["id"] for entrada in origen["prompts"]}
    if not set(MAPA_ACTOS).issubset(ids):
        raise ValueError("La procedencia no incluye las cuatro CG utilizadas")
    manifest = {
        "version":1,
        "generado_utc":datetime.now(timezone.utc).isoformat(),
        "productor":inventariar(Path(__file__)),
        "metodo":"Composición nativa QPainter: cámara, luz y partículas sobre CG de ImageGen. Codificación FFmpeg H.264. No es video generado por IA.",
        "audio":"Los seis clips no contienen audio. El juego reutiliza MP3 neurales originales del catálogo, sin síntesis Windows.",
        "origen_arte":origen,
        "archivo_procedencia":inventariar(procedencia),
        "cg":ilustraciones,
        "videos":videos,
        "portada_gif":gif,
    }
    destino("manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n",
                                       encoding="utf-8")
    print("Exportación terminada: assets/novela/manifest.json", flush=True)
    return manifest


if __name__ == "__main__":
    opciones = argparse.ArgumentParser(description=__doc__)
    opciones.add_argument("--origen-imagenes", type=Path)
    args = opciones.parse_args()
    producir(args.origen_imagenes)
