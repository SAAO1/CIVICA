"""Revisa los seis escenarios y exporta una muestra real de CIVICA con voz.

No cambia preferencias ni progreso personal. La exportación de vídeo requiere
FFmpeg de producción; jugar sólo requiere PyQt6.
"""
import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QApplication
from interfaz import VentanaPrincipal
from juego.lectura import BibliotecaLectura
from juego.partida import Juego
from personajes_animados import SpriteExpresivo
from audio.catalogo_voces import cargar_manifest, clave_clip, CARPETA_VOCES


def preparar_escena(ventana, app, dialogo=1):
    ventana.mostrar_escena(ventana.ESCENA_DIALOGO)
    escena = ventana.escena_dialogo
    escena.timer_inicio.stop()
    escena.dialogo_actual = min(dialogo, len(escena.dialogos)-1)
    escena.mostrar_dialogo_actual()
    escena.animacion.setCurrentTime(escena.animacion.duration())
    escena.revelar_texto()
    escena.timer_texto.stop()
    ventana.animacion_transicion.stop()
    ventana.velo_transicion.hide()
    for personaje in escena.personajes.values():
        for animacion in (personaje.animacion_fade, personaje.animacion_entrada,
                          personaje.animacion_dim):
            if animacion:
                animacion.setCurrentTime(animacion.duration())
    escena.fondo_label.establecer_tiempo(2)
    for actor in escena.findChildren(SpriteExpresivo):
        actor.establecer_tiempo(2)
    app.processEvents()
    return escena


def video_muestra(ventana, app, destino):
    binarios = list((RAIZ / ".tmp").glob("**/ffmpeg-win-*.exe"))
    if not binarios:
        raise RuntimeError("FFmpeg de producción no está disponible para exportar la muestra")
    ffmpeg = str(binarios[0])
    ventana.resize(1280, 720)
    ventana.establecer_juego(Juego(4, eventos=False))
    ventana.juego.iniciar_primera_publicacion()
    escena = preparar_escena(ventana, app, 1)
    hablante = escena.nombre_label.text()
    voz = cargar_manifest()["clips"][clave_clip(hablante, escena.texto_completo)]
    clip = CARPETA_VOCES / voz["archivo"]
    duracion = max(4.0, min(20.0, voz.get("duracion_ms", 7000)/1000+.9))
    # El manifest conserva duración en segundos en algunas versiones.
    if "duracion" in voz:
        duracion = min(20.0, float(voz["duracion"])+.9)
    fps = 24
    ancho, alto = ventana.width(), ventana.height()
    ruta = destino / "muestra_civica.mp4"
    musica = RAIZ / "assets/audio/expansion/musica/ciudad.wav"
    ambiente = RAIZ / "assets/audio/expansion/ambientes/calle.wav"
    comando = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{ancho}x{alto}", "-r", str(fps), "-i", "pipe:0",
               "-i", str(clip), "-stream_loop", "-1", "-i", str(musica),
               "-stream_loop", "-1", "-i", str(ambiente),
               "-filter_complex", "[1:a]volume=1[v];[2:a]volume=0.12[m];[3:a]volume=0.22[a];[v][m][a]amix=inputs=3:duration=longest:normalize=0[sonido]",
               "-map", "0:v", "-map", "[sonido]", "-t", str(duracion),
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(ruta)]
    proceso = subprocess.Popen(comando, stdin=subprocess.PIPE, stderr=subprocess.PIPE,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    envolvente = voz.get("envolvente", [])
    paso = max(1, voz.get("paso_envolvente_ms", 50))
    for frame in range(math.ceil(duracion*fps)):
        t = frame/fps
        escena.fondo_label.establecer_tiempo(t)
        nivel = envolvente[min(len(envolvente)-1, int(t*1000/paso))] if envolvente else .5*(1+math.sin(t*18))
        for nombre, personaje in escena.personajes.items():
            personaje.establecer_hablando(nombre == hablante, nivel if nombre == hablante else 0)
            for actor in (personaje.imagen, personaje.imagen_oscura):
                actor.establecer_tiempo(t+1)
        app.processEvents()
        imagen = ventana.grab().toImage().convertToFormat(QImage.Format.Format_RGB888)
        datos = imagen.constBits().asstring(imagen.sizeInBytes())
        if imagen.bytesPerLine() != ancho*3:
            datos = b"".join(datos[i*imagen.bytesPerLine():i*imagen.bytesPerLine()+ancho*3] for i in range(alto))
        proceso.stdin.write(datos)
    proceso.stdin.close()
    error = proceso.stderr.read().decode("utf-8", errors="replace")
    if proceso.wait() != 0:
        raise RuntimeError(error)
    print(ruta, flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", action="store_true")
    args = parser.parse_args()
    app = QApplication.instance() or QApplication([])
    destino = RAIZ / ".tmp/capturas_audiovisual"
    destino.mkdir(parents=True, exist_ok=True)
    with (patch("interfaz.GestorAudio"), patch("configuracion.cargar", return_value={}),
          patch("interfaz.BibliotecaLectura", lambda: BibliotecaLectura(None))):
        ventana = VentanaPrincipal()
        ventana.sin_limite = True
        ventana.velocidad_texto = 0
        ventana.resize(1366, 768)
        ventana.show()
        for ancho, alto in ((1100, 700), (1366, 768), (1920, 1080)):
            ventana.resize(ancho, alto)
            juego = Juego(4, eventos=False)
            juego.iniciar_primera_publicacion()
            ventana.establecer_juego(juego)
            while juego.obtener_publicacion_actual():
                identificador = juego.obtener_publicacion_actual().id
                preparar_escena(ventana, app)
                ventana.grab().save(str(destino / f"caso_{identificador}_{ancho}.png"))
                juego.ejecutar_accion("verificar")
                juego.avanzar_publicacion()
            print(f"Seis escenas: {ancho}x{alto}", flush=True)
        if args.video:
            video_muestra(ventana, app, destino)
        ventana.close()
        app.processEvents()


if __name__ == "__main__":
    main()
