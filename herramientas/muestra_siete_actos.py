"""Exporta los cuatro actos nuevos con UI, compositores y voces locales.

Captura por reloj y transporte aislado: no representa una partida humana ni
sustituye las comprobaciones independientes del decodificador multimedia Qt.
"""
import hashlib
import faulthandler
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tests"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_LOGGING_RULES", "qt.multimedia.*=false")

from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication
from audio.catalogo_voces import cargar_manifest
from cinematica_acciones_extendida_visual import RenderizadorAccionExtendida
from cinematica_extension_visual import RenderizadorExtension
from cinematica_final_visual import RenderizadorFinal
from herramientas.auditar_campana_extendida import completar
from herramientas.exportar_ambientes import localizar_ffmpeg
from herramientas.muestra_impacto_roles_finales import _voz, _sin_transicion
from herramientas.muestra_acciones_obligatorias import validar_nivel_audio
from juego.acciones import accion_por_defecto
from juego.campana_extendida import DIALOGOS_NUEVOS, epilogo_extendido
from juego.cinematica_acciones_extendida import clave_accion_extendida
from juego.historia import contenido_resultado
from juego.lectura import BibliotecaLectura
from juego.partida import Juego
from test_balance_roles_ui import AudioConSenales, crear_ventana

FPS, ANCHO, ALTO = 24, 1280, 720
DESTINO = RAIZ / "docs/vistas/muestra_siete_actos.mp4"
AMBIENTES = {90: "estudio", 40: "estudio", 100: "debate", 10: "debate",
             110: "redaccion", 25: "redaccion", 120: "urnas", 35: "urnas"}


def caso(identificador, rol="periodista", accion=None):
    juego = Juego(42, eventos=False, campana="extendida")
    juego.seleccionar_rol(rol)
    juego.iniciar_primera_publicacion()
    while juego.publicacion_actual_id != identificador:
        assert juego.ejecutar_accion(accion_por_defecto(rol))
        assert juego.avanzar_publicacion()
    if accion:
        assert juego.ejecutar_accion(accion)
    return juego


def planificar(clips):
    plan = []
    for identificador in DIALOGOS_NUEVOS:
        nombre, texto = DIALOGOS_NUEVOS[identificador][0]
        plan.append(dict(tipo="narrador", clave=f"narrador_{identificador}",
                         juego=caso(identificador), voz=_voz(clips, nombre, texto), ambiente=AMBIENTES[identificador]))
        reparto = {90: ("INFLUENCER",), 40: ("CAMILA",),
                   100: ("JUAN", "LAURA"), 10: ("ADRIAN",)}.get(identificador, ())
        for nombre in reparto:
            texto = next(t for h, t in DIALOGOS_NUEVOS[identificador] if h == nombre)
            plan.append(dict(tipo="personaje", clave=nombre, juego=caso(identificador),
                             voz=_voz(clips, nombre, texto), ambiente=AMBIENTES[identificador]))
        if identificador in (40, 110):
            rol, accion = ("ciudadano", "convocar") if identificador == 40 else ("periodista", "contrastar")
            juego = caso(identificador, rol, accion)
            texto, nombre = contenido_resultado(juego, 1)
            plan.append(dict(tipo="accion", clave=clave_accion_extendida(juego), juego=juego,
                             voz=_voz(clips, nombre, texto), ambiente=AMBIENTES[identificador]))
    for ganador in ("juan", "adrian", "laura", "camila", "empate"):
        juego, ruta, eleccion = completar(
            lambda j: "contrastar" if ganador != "empate" and j.obtener_publicacion_actual().candidato_id == ganador else "reservar", 42)
        nombre, texto = epilogo_extendido(juego, eleccion)[0]
        plan.append(dict(tipo="epilogo", clave=ganador, juego=juego, ruta=ruta,
                         voz=_voz(clips, nombre, texto), ambiente="noche"))
    inicio = 0
    for tramo in plan:
        minimo = 10 if tramo["tipo"] == "narrador" else 9 if tramo["tipo"] == "accion" else 4
        tramo["fotogramas"] = math.ceil(max(minimo, tramo["voz"]["duracion"]+.6)*FPS)
        tramo["inicio"] = inicio / FPS
        tramo["duracion"] = tramo["fotogramas"] / FPS
        inicio += tramo["fotogramas"]
    return plan, inicio/FPS


def comando(ffmpeg, plan, duracion):
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
           "-pix_fmt", "rgb24", "-s", "1280x720", "-r", str(FPS), "-i", "pipe:0"]
    filtros, etiquetas = [], []
    for i, tramo in enumerate(plan, 1):
        cmd += ["-i", str(tramo["voz"]["ruta"])]
        filtros.append(f"[{i}:a]aresample=48000,adelay={round(tramo['inicio']*1000)}:all=1,volume=1[v{i}]")
        etiquetas.append(f"[v{i}]")
    for i, tramo in enumerate(plan, len(plan)+1):
        nombre = tramo["ambiente"]
        ruta = RAIZ / (f"assets/audio/siete_actos/{nombre}.wav" if nombre != "noche" else "assets/audio/expansion/ambientes/noche.wav")
        cmd += ["-stream_loop", "-1", "-i", str(ruta)]
        filtros.append(f"[{i}:a]aresample=48000,atrim=duration={tramo['duracion']},asetpts=PTS-STARTPTS,volume=.12,afade=t=in:d=0.25,afade=t=out:st={tramo['duracion']-.3}:d=0.3,adelay={round(tramo['inicio']*1000)}:all=1[a{i}]")
        etiquetas.append(f"[a{i}]")
    cmd += ["-stream_loop", "-1", "-i", str(RAIZ / "assets/audio/expansion/musica/ciudad.wav")]
    filtros.append(f"[{len(plan)*2+1}:a]aresample=48000,atrim=duration={duracion},volume=.08,afade=t=in:d=0.5,afade=t=out:st={duracion-1}:d=1[m]")
    etiquetas.append("[m]")
    filtros.append("".join(etiquetas) + f"amix=inputs={len(etiquetas)}:duration=longest:normalize=0,alimiter=limit=.92[audio]")
    cmd += ["-filter_complex", ";".join(filtros), "-map", "0:v", "-map", "[audio]", "-t", str(duracion),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(DESTINO)]
    return cmd


def preparar(ventana, tramo, app):
    ventana.establecer_juego(tramo["juego"])
    tipo = tramo["tipo"]
    indice = ventana.ESCENA_RESULTADO_1 if tipo == "accion" else ventana.ESCENA_EPILOGO if tipo == "epilogo" else ventana.ESCENA_DIALOGO
    ventana.mostrar_escena(indice)
    escena = ventana.escenas.currentWidget()
    escena.timer_inicio.stop()
    if tipo == "personaje":
        escena.dialogo_actual = next(i for i, (h, t) in enumerate(escena.dialogos) if h == tramo["voz"]["hablante"] and t == tramo["voz"]["texto"])
    escena.iniciar_dialogo(tramo["voz"]["texto"], tramo["voz"]["hablante"], getattr(escena, "presentes_dialogo", None))
    escena.animacion.setCurrentTime(escena.animacion.duration())
    escena.animacion.stop()
    escena.finalizar_animacion_dialogo()
    escena.timer_texto.stop()
    escena.revelar_texto()
    escena.efectos_narrativos.pausar()
    for actor in escena.personajes.values():
        for animacion in (actor.animacion_fade, actor.animacion_dim, actor.animacion_entrada, actor.animacion_salida):
            if animacion:
                animacion.stop()
        if actor.isVisible():
            actor.efecto_fade.setOpacity(1)
    _sin_transicion(ventana)
    app.processEvents()
    render = (RenderizadorExtension(tramo["clave"]) if tipo == "narrador" else
              RenderizadorAccionExtendida(tramo["clave"]) if tipo == "accion" else
              RenderizadorFinal("recuento" if tramo["clave"] == "empate" else tramo["clave"]) if tipo == "epilogo" else None)
    return escena, render


def main():
    faulthandler.enable()
    faulthandler.dump_traceback_later(90)
    app = QApplication.instance() or QApplication([])
    clips = cargar_manifest()["clips"]
    plan, duracion = planificar(clips)
    ffmpeg = localizar_ffmpeg()
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    print(f"Muestra: {len(plan)} planos, {duracion:.2f}s, voces completas", flush=True)
    mezcla = RAIZ / ".tmp/siete_actos_mezcla.wav"
    video_temporal = RAIZ / ".tmp/muestra_siete_actos_render.mp4"
    log_ffmpeg = RAIZ / ".tmp/siete_actos_muestra_ffmpeg.txt"
    original = comando(ffmpeg, plan, duracion)
    primero = original.index("-i", original.index("pipe:0")+1)
    filtro = original.index("-filter_complex")
    audio_cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-filter_complex_threads", "2",
                 "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=mono:d={duracion}"]
    audio_cmd += original[primero:filtro+2]
    audio_cmd += ["-map", "[audio]", "-vn", "-t", str(duracion), "-c:a", "pcm_s16le", str(mezcla)]
    with log_ffmpeg.open("w", encoding="utf-8") as log_audio:
        resultado = subprocess.run(audio_cmd, stdout=subprocess.DEVNULL, stderr=log_audio, timeout=180,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if resultado.returncode:
        raise RuntimeError(log_ffmpeg.read_text(encoding="utf-8"))
    print("Mezcla de voces y ambientes terminada", flush=True)
    video_cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                 "-s", "1280x720", "-r", str(FPS), "-i", "pipe:0", "-i", str(mezcla),
                 "-map", "0:v", "-map", "1:a", "-t", str(duracion), "-c:v", "libx264",
                 "-threads", "2", "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p",
                 "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(video_temporal)]
    with (patch("configuracion.cargar", return_value={}), patch("configuracion.guardar"),
          patch("interfaz.GestorAudio", AudioConSenales),
          patch("interfaz.BibliotecaLectura", lambda: BibliotecaLectura(None)),
          patch("cinematica_narrativa.CapaCinematica._reproducir_si_corresponde")):
        ventana = crear_ventana()
        ventana.resize(ANCHO, ALTO)
        ventana.animar_personajes = True
        ventana.reducir_movimiento = False
        ventana.aplicar_accesibilidad()
        ventana.velocidad_texto = 0
        salida_ffmpeg = log_ffmpeg.open("a", encoding="utf-8")
        proceso = subprocess.Popen(video_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                   stderr=salida_ffmpeg, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        try:
            for tramo in plan:
                # El plazo vigila un plano bloqueado, no la duración total
                # de una exportación que puede tardar varios minutos.
                faulthandler.cancel_dump_traceback_later()
                faulthandler.dump_traceback_later(90)
                print(f"Preparando {tramo['tipo']} {tramo['clave']}", flush=True)
                escena, render = preparar(ventana, tramo, app)
                entrada = clips[tramo["voz"]["clave"]]
                for numero in range(tramo["fotogramas"]):
                    t = numero / FPS
                    if render:
                        instante = min(t, 8.95) if tramo["tipo"] == "accion" else t % 10 if tramo["tipo"] == "narrador" else min(t+2, 11.95)
                        escena.cine_narrativo._poster.imagen = QPixmap.fromImage(render.capturar_fotograma(instante))
                        escena.cine_narrativo._poster.update()
                    for nombre, actor in escena.personajes.items():
                        actor.imagen.establecer_tiempo(t+1)
                        actor.imagen_oscura.establecer_tiempo(t+1)
                        envolvente = entrada["envolvente"]
                        posicion = int(t*1000/entrada["paso_envolvente_ms"])
                        nivel = envolvente[posicion] if posicion < len(envolvente) else 0
                        actor.establecer_hablando(nombre == tramo["voz"]["hablante"], nivel)
                    escena.fondo_label.establecer_tiempo(t)
                    escena.efectos_narrativos.establecer_tiempo(t)
                    app.processEvents()
                    imagen = ventana.grab().toImage().convertToFormat(QImage.Format.Format_RGB888)
                    if numero == min(48, tramo["fotogramas"]-1):
                        imagen.save(str(DESTINO.parent / f"siete_{tramo['clave']}.jpg"), "JPG", 88)
                    datos = imagen.constBits().asstring(imagen.sizeInBytes())
                    if imagen.bytesPerLine() != ANCHO * 3:
                        datos = b"".join(datos[y*imagen.bytesPerLine():y*imagen.bytesPerLine()+ANCHO*3] for y in range(ALTO))
                    proceso.stdin.write(datos)
                print(f"{tramo['inicio']:.2f}s {tramo['tipo']} {tramo['clave']}", flush=True)
            proceso.stdin.close()
            if proceso.wait():
                raise RuntimeError(log_ffmpeg.read_text(encoding="utf-8"))
        except BaseException:
            proceso.kill()
            proceso.wait()
            raise
        finally:
            if not proceso.stdin.closed:
                proceso.stdin.close()
            salida_ffmpeg.close()
            ventana.close()
            app.processEvents()
    verificacion = subprocess.run([ffmpeg, "-v", "error", "-i", str(video_temporal), "-map", "0:v", "-map", "0:a", "-f", "null", "-"], capture_output=True)
    if verificacion.returncode:
        raise RuntimeError(verificacion.stderr.decode("utf-8", "replace"))
    video_temporal.replace(DESTINO)
    metadata = dict(archivo=DESTINO.name, duracion_segundos=duracion, fps=FPS, tamano=[ANCHO, ALTO],
                    bytes=DESTINO.stat().st_size, sha256=hashlib.sha256(DESTINO.read_bytes()).hexdigest(),
                    naturaleza="Widgets reales y compositores del juego por reloj; audio y transporte de los widgets aislados. No es grabación humana ni prueba del decodificador Qt.",
                    sonido="Voces neuronales locales completas, cuatro ambientes nuevos CC0, música; sin valoración auditiva humana.",
                    audio_niveles=validar_nivel_audio(ffmpeg, DESTINO), decodificacion_completa=True,
                    cortes=[{**{k:v for k,v in t.items() if k not in ("juego", "voz")},
                             "voz": {k:v for k,v in t["voz"].items() if k != "ruta"}} for t in plan])
    DESTINO.with_suffix(".json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Muestra verificada {DESTINO.name}: {duracion:.2f}s", flush=True)
    faulthandler.cancel_dump_traceback_later()


if __name__ == "__main__":
    main()
