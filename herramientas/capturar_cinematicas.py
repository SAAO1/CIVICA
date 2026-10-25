"""Exporta una muestra con las voces de los cortes y la interfaz real.

python -B herramientas/capturar_cinematicas.py
La muestra renderiza el mismo compositor que produjo los MP4 y los widgets
del juego, con preferencias/biblioteca en memoria. No captura una partida
humana: es una exportación reproducible para revisar imagen, texto y mezcla.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication

from audio.catalogo_voces import cargar_manifest, clave_clip, ruta_clip
from cinematica_visual import DURACION, FPS, RenderizadorCinematica
from herramientas.exportar_ambientes import localizar_ffmpeg
from herramientas.verificar_cinematicas import preparar
from interfaz import VentanaPrincipal
from juego.cinematica import CINEMATICAS
from juego.lectura import BibliotecaLectura
from juego.partida import Juego


AMBIENTES = {"ciudad_48h": "plaza", "mensaje_barrio": "calle",
             "rumor_colegio": "calle", "cafe_alerta": "calle",
             "libreta_cultura": "cafe", "mapa_parque": "plaza",
             "libro_biblioteca": "oficina", "acusacion_lluvia": "interior_lluvia",
             "noche_electoral": "noche"}
for _caso, _ambiente in (("colegio", "calle"), ("cultura", "cafe"), ("parque", "plaza"),
                        ("biblioteca", "oficina"), ("acusacion", "interior_lluvia"), ("voto", "noche")):
    for _sufijo in ("c", "p"):
        AMBIENTES[f"person_{_caso}_{_sufijo}"] = _ambiente


def _comando_audio(ffmpeg, destino, claves, duracion):
    clips = cargar_manifest()["clips"]
    comando = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo",
               "-pix_fmt", "rgb24", "-s", "1280x720", "-r", str(FPS), "-i", "pipe:0"]
    filtros, voces, ambientes = [], [], []
    for numero, clave in enumerate(claves):
        ficha = CINEMATICAS[clave]
        entrada = clips[clave_clip(ficha["nombre"], ficha["texto"])]
        voz = ruta_clip(entrada)
        if voz is None:
            raise FileNotFoundError(f"Falta la voz de {ficha['nombre']}: {clave}")
        comando += ["-i", str(voz)]
        etiqueta = f"v{numero}"
        retraso = round(numero*DURACION*1000)
        filtros.append(f"[{numero+1}:a]aresample=48000,adelay={retraso}:all=1,volume=1[{etiqueta}]")
        voces.append(f"[{etiqueta}]")
    base = len(claves)+1
    for numero, clave in enumerate(claves):
        ambiente = RAIZ / f"assets/audio/expansion/ambientes/{AMBIENTES[clave]}.wav"
        comando += ["-stream_loop", "-1", "-i", str(ambiente)]
        etiqueta = f"a{numero}"
        retraso = round(numero*DURACION*1000)
        filtros.append(f"[{base+numero}:a]atrim=duration={DURACION},asetpts=PTS-STARTPTS,"
                       f"afade=t=in:d=0.25,afade=t=out:st={DURACION-.4}:d=0.4,"
                       f"aresample=48000,adelay={retraso}:all=1,volume=0.19[{etiqueta}]")
        ambientes.append(f"[{etiqueta}]")
    musica = RAIZ / "assets/audio/expansion/musica/ciudad.wav"
    comando += ["-stream_loop", "-1", "-i", str(musica)]
    filtros.append(f"[{2*len(claves)+1}:a]atrim=duration={duracion},volume=0.10,"
                   f"afade=t=out:st={duracion-1}:d=1[musica]")
    entradas = voces+ambientes+["[musica]"]
    filtros.append("".join(entradas)+f"amix=inputs={len(entradas)}:duration=longest:"
                   "normalize=0,alimiter=limit=0.95[mezcla]")
    comando += ["-filter_complex", ";".join(filtros), "-map", "0:v", "-map", "[mezcla]",
                "-t", str(duracion), "-c:v", "libx264", "-preset", "veryfast", "-crf", "25",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
                str(destino)]
    return comando


def exportar(destino, claves):
    app = QApplication.instance() or QApplication([])
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = localizar_ffmpeg()
    duracion = len(claves)*DURACION
    comando = _comando_audio(ffmpeg, destino, claves, duracion)
    # Se desactiva únicamente el decodificador durante el render offline.
    # La herramienta verificar_cinematicas.py comprueba su reproducción real.
    with (patch("interfaz.GestorAudio"), patch("configuracion.cargar", return_value={}),
          patch("interfaz.BibliotecaLectura", lambda: BibliotecaLectura(None)),
          patch("cinematica_narrativa.CapaCinematica._reproducir_si_corresponde")):
        ventana = VentanaPrincipal()
        ventana.resize(1280, 720)
        ventana.sin_limite = True
        ventana.audio.hablando = False
        ventana.velocidad_texto = 0
        ventana.show()
        app.processEvents()
        ventana.mostrar_escena(ventana.ESCENA_NARRACION_1)
        escena = ventana.escenas.currentWidget()
        escena.timer_inicio.stop()
        ventana.animacion_transicion.stop()
        ventana.velo_transicion.hide()
        proceso = subprocess.Popen(comando, stdin=subprocess.PIPE, stderr=subprocess.PIPE,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        try:
            for clave in claves:
                escena = preparar(ventana, clave)
                escena.fondo_label.configurar(activo=False)
                escena.efectos_narrativos.pausar()
                cine = escena.cine_narrativo
                render = RenderizadorCinematica(clave)
                for frame in range(round(DURACION*FPS)):
                    t = frame/FPS
                    cine._poster.imagen = QPixmap.fromImage(render.capturar_fotograma(t))
                    cine._poster.update()
                    escena.efectos_narrativos.establecer_tiempo(t)
                    app.processEvents()
                    imagen = ventana.grab().toImage().convertToFormat(QImage.Format.Format_RGB888)
                    if frame == round(6.5*FPS):
                        imagen.save(str(destino.parent / f"cine_{clave}.jpg"), "JPG", 86)
                    datos = imagen.constBits().asstring(imagen.sizeInBytes())
                    if imagen.bytesPerLine() != 1280*3:
                        datos = b"".join(datos[y*imagen.bytesPerLine():y*imagen.bytesPerLine()+1280*3]
                                         for y in range(720))
                    proceso.stdin.write(datos)
                print(f"Muestra: {clave}", flush=True)
            proceso.stdin.close()
            error = proceso.stderr.read().decode("utf-8", "replace")
            if proceso.wait():
                raise RuntimeError(error)
        except BaseException:
            proceso.kill()
            proceso.wait()
            raise
        finally:
            if not proceso.stdin.closed:
                proceso.stdin.close()
            proceso.stderr.close()
            ventana.close()
            app.processEvents()
    comprobar = subprocess.run([ffmpeg, "-v", "error", "-i", str(destino), "-f", "null", "-"],
                              capture_output=True, text=True)
    if comprobar.returncode:
        raise RuntimeError(comprobar.stderr)
    datos = {"archivo": destino.name, "duracion_segundos": duracion, "fps": FPS,
             "tamano": [1280, 720], "cortes": claves, "decodificacion_completa": True,
             "naturaleza": "Exportación offline de widgets reales y compositor de los MP4; no grabación de una sesión humana.",
             "sonido": "Voces neuronales locales del narrador, ciudadano y periodista + ambientes y música CC0 incluidos."}
    destino.with_suffix(".json").write_text(json.dumps(datos, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(destino, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, default=RAIZ / "docs/vistas/cinematicas_narradas.mp4")
    parser.add_argument("--clave", choices=CINEMATICAS)
    args = parser.parse_args()
    exportar(args.destino, [args.clave] if args.clave else list(CINEMATICAS))
