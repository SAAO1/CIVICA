"""Exporta una revisión audiovisual de roles, contexto, balance e investiduras.

Usa widgets reales y el mismo compositor de los MP4 instalados. No graba una
sesión humana ni modifica preferencias, biblioteca o partidas personales.
"""
import hashlib
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
from audio.catalogo_voces import cargar_manifest, clave_clip, ruta_clip, segmentos_indicadores
from cinematica_final_visual import RenderizadorFinal
from cinematica_visual import RenderizadorCinematica
from herramientas.exportar_ambientes import localizar_ffmpeg
from herramientas.verificar_cinematicas import preparar as preparar_cg
from juego.cinematica import CINEMATICAS
from juego.lectura import BibliotecaLectura
from juego.partida import Juego
from test_balance_roles_ui import AudioConSenales, crear_ventana

FPS, ANCHO, ALTO = 24, 1280, 720
DESTINO = RAIZ / "docs/vistas/muestra_impacto_roles_finales.mp4"


def _duracion(entrada):
    return float(entrada.get("duracion", entrada.get("duracion_ms", 0)/1000))


def _voz(clips, hablante, texto):
    clave = clave_clip(hablante, texto)
    entrada = clips.get(clave)
    ruta = ruta_clip(entrada) if entrada else None
    if ruta is None or _duracion(entrada) <= 0:
        raise FileNotFoundError(f"Falta la voz local completa de {hablante}: {texto}")
    return dict(clave=clave, ruta=ruta, duracion=_duracion(entrada), texto=texto, hablante=hablante)


def _juego_balance():
    juego = Juego(7, eventos=False)
    juego.seleccionar_rol("periodista")
    juego.jugador.ciudadano_id = "carlos"  # Cinco receptores reales a dos saltos.
    juego.confianza = 50
    juego.desinformacion = 9
    juego.iniciar_primera_publicacion()
    assert juego.ejecutar_accion("contrastar")
    assert (juego.confianza, juego.desinformacion) == (56, 1)
    return juego


def _plan(clips, juego):
    plan = [dict(tipo="rol", clave=rol, duracion=4.) for rol in ("ciudadano", "periodista")]
    for clave in ("person_cultura_c", "person_cultura_p"):
        ficha = CINEMATICAS[clave]
        voz = _voz(clips, ficha["nombre"], ficha["texto"])
        plan.append(dict(tipo="cg", clave=clave, voz=voz, duracion=max(12., voz["duracion"]+.6)))
    for segmento in segmentos_indicadores(juego.ultimo_registro):
        voz = _voz(clips, "NARRADOR", segmento["texto"])
        plan.append(dict(tipo="balance", clave=segmento["clave"], voz=voz, duracion=max(1.5, voz["duracion"]+.18)))
    plan.append(dict(tipo="resumen", clave="todos", duracion=2.))
    for clave in ("juan", "adrian", "laura", "camila"):
        plan.append(dict(tipo="final", clave=clave, duracion=4.))
    inicio = 0
    for tramo in plan:
        tramo["fotogramas"] = math.ceil(tramo["duracion"]*FPS)
        tramo["duracion"] = tramo["fotogramas"]/FPS
        tramo["inicio"] = inicio/FPS
        inicio += tramo["fotogramas"]
    return plan, inicio/FPS


def _comando(ffmpeg, plan, duracion):
    voces = [tramo for tramo in plan if "voz" in tramo]
    comando = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1280x720", "-r", str(FPS), "-i", "pipe:0"]
    filtros, etiquetas = [], []
    for i, tramo in enumerate(voces, 1):
        comando += ["-i", str(tramo["voz"]["ruta"])]
        filtros.append(f"[{i}:a]aresample=48000,adelay={round(tramo['inicio']*1000)}:all=1,volume=1[v{i}]")
        etiquetas.append(f"[v{i}]")
    musica = RAIZ / "assets/audio/expansion/musica/ciudad.wav"
    ambiente = RAIZ / "assets/audio/expansion/ambientes/cafe.wav"
    comando += ["-stream_loop", "-1", "-i", str(musica), "-stream_loop", "-1", "-i", str(ambiente)]
    base = len(voces)+1
    filtros += [f"[{base}:a]atrim=duration={duracion},volume=0.11,afade=t=in:d=0.5,afade=t=out:st={duracion-1}:d=1[m]",
                f"[{base+1}:a]atrim=duration={duracion},volume=0.12,afade=t=in:d=0.4,afade=t=out:st={duracion-1}:d=1[a]"]
    etiquetas += ["[m]", "[a]"]
    filtros.append("".join(etiquetas)+f"amix=inputs={len(etiquetas)}:duration=longest:normalize=0,alimiter=limit=.95[mezcla]")
    comando += ["-filter_complex", ";".join(filtros), "-map", "0:v", "-map", "[mezcla]", "-t", str(duracion), "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(DESTINO)]
    return comando


def _sin_transicion(ventana):
    ventana.animacion_transicion.stop()
    ventana.velo_transicion.hide()


def _preparar_balance(ventana, juego, app):
    ventana.establecer_juego(juego)
    ventana.mostrar_escena(ventana.ESCENA_RESULTADO_3)
    escena = ventana.escena_resultado_3
    escena.timer_inicio.stop()
    escena.preparar_dialogo()
    escena.animacion.stop()
    escena.finalizar_animacion_dialogo()
    escena.balance.configurar(False)
    _sin_transicion(ventana)
    app.processEvents()
    return escena


def _ruta_ganadora(clave, auditoria):
    juego = Juego(7, eventos=False)
    nombre = next(c.nombre for c in juego.candidatos if c.id == clave)
    secuencia = auditoria["ejemplos"][nombre]
    juego.iniciar_primera_publicacion()
    for accion in secuencia:
        assert juego.ejecutar_accion(accion)
        juego.avanzar_publicacion()
    assert juego.resultado_electoral()["ganadores"] == [nombre]
    return juego, secuencia


def main():
    app = QApplication.instance() or QApplication([])
    juego_balance = _juego_balance()
    plan, duracion = _plan(cargar_manifest()["clips"], juego_balance)
    print(f"Plan: {duracion:.3f}s, {sum(t['fotogramas'] for t in plan)} fotogramas, voces completas.", flush=True)
    ffmpeg = localizar_ffmpeg()
    datos_auditoria = json.loads((RAIZ / "docs/verificacion_elecciones.json").read_text(encoding="utf-8"))
    auditoria = next(r for r in datos_auditoria["modalidades"] if r["rol"] == "ciudadano" and r["semilla"] == 7)
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    fuentes_victoria = {}
    with (patch("configuracion.cargar", return_value={}), patch("interfaz.GestorAudio", AudioConSenales),
          patch("interfaz.BibliotecaLectura", lambda: BibliotecaLectura(None)),
          patch("cinematica_narrativa.CapaCinematica._reproducir_si_corresponde")):
        ventana = crear_ventana()
        ventana.resize(ANCHO, ALTO)
        ventana.velocidad_texto = 0
        app.processEvents()
        proceso = subprocess.Popen(_comando(ffmpeg, plan, duracion), stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        escena_balance = None
        try:
            for tramo in plan:
                tipo, clave = tramo["tipo"], tramo["clave"]
                render = None
                if tipo == "rol":
                    juego = Juego(7, eventos=False)
                    juego.seleccionar_rol(clave)
                    juego.iniciar_primera_publicacion()
                    ventana.establecer_juego(juego)
                    ventana.mostrar_escena(ventana.ESCENA_ACCION)
                    escena = ventana.escena_accion
                    escena.animacion_panel.stop()
                    escena.efecto_panel.setOpacity(1.)
                    _sin_transicion(ventana)
                elif tipo == "cg":
                    escena = preparar_cg(ventana, clave)
                    escena.efectos_narrativos.pausar()
                    render = RenderizadorCinematica(clave)
                    _sin_transicion(ventana)
                elif tipo == "balance":
                    if escena_balance is None:
                        escena_balance = _preparar_balance(ventana, juego_balance, app)
                    escena = escena_balance
                    ventana.audio.segmento_iniciado.emit(clave)
                elif tipo == "resumen":
                    escena = escena_balance
                    escena.balance.revelar()
                elif tipo == "final":
                    juego, secuencia = _ruta_ganadora(clave, auditoria)
                    fuentes_victoria[clave] = list(secuencia)
                    ventana.establecer_juego(juego)
                    ventana.mostrar_escena(ventana.ESCENA_FIN)
                    escena = ventana.escena_fin
                    render = RenderizadorFinal(clave)
                    _sin_transicion(ventana)
                for numero in range(tramo["fotogramas"]):
                    t = numero/FPS
                    if tipo == "cg":
                        escena.cine_narrativo._poster.imagen = QPixmap.fromImage(render.capturar_fotograma(t))
                        escena.cine_narrativo._poster.update()
                        escena.efectos_narrativos.establecer_tiempo(t)
                    elif tipo == "balance":
                        escena.balance.establecer_tiempo(t)
                    elif tipo == "final" and t < 1:
                        escena.cine_final._poster.imagen = QPixmap.fromImage(render.capturar_fotograma(t+5))
                        escena.cine_final._poster.update()
                    app.processEvents()
                    if tipo == "final" and t >= 1:
                        imagen = render.capturar_fotograma(t+5)
                    else:
                        imagen = ventana.grab().toImage()
                    imagen = imagen.convertToFormat(QImage.Format.Format_RGB888)
                    if (tipo == "cg" and clave == "person_cultura_c" and numero == 6*FPS):
                        imagen.save(str(DESTINO.parent / "muestra_contexto_personaje.jpg"), "JPG", 88)
                    if tipo == "balance" and clave == "confianza" and numero == 7:
                        imagen.save(str(DESTINO.parent / "muestra_contador_central.jpg"), "JPG", 88)
                    if tipo == "final" and clave == "camila" and numero == 3*FPS:
                        imagen.save(str(DESTINO.parent / "muestra_investidura.jpg"), "JPG", 88)
                    datos = imagen.constBits().asstring(imagen.sizeInBytes())
                    if imagen.bytesPerLine() != ANCHO*3:
                        datos = b"".join(datos[y*imagen.bytesPerLine():y*imagen.bytesPerLine()+ANCHO*3] for y in range(ALTO))
                    proceso.stdin.write(datos)
                print(f"{tramo['inicio']:6.2f}s · {tipo}: {clave} ({tramo['duracion']:.2f}s)", flush=True)
            proceso.stdin.close()
            error = proceso.stderr.read().decode("utf-8", "replace")
            if proceso.wait():
                raise RuntimeError(error)
        except BaseException as error_exportacion:
            proceso.kill()
            proceso.wait()
            detalle = proceso.stderr.read().decode("utf-8", "replace")
            raise RuntimeError(detalle or str(error_exportacion)) from error_exportacion
        finally:
            if not proceso.stdin.closed:
                proceso.stdin.close()
            proceso.stderr.close()
            ventana.close()
            app.processEvents()
    validacion = subprocess.run([ffmpeg, "-v", "error", "-i", str(DESTINO), "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-"], capture_output=True, text=True)
    if validacion.returncode:
        raise RuntimeError(validacion.stderr)
    metadata = dict(archivo=DESTINO.name, duracion_segundos=duracion, fps=FPS, tamano=[ANCHO, ALTO], bytes=DESTINO.stat().st_size, sha256=hashlib.sha256(DESTINO.read_bytes()).hexdigest(), decodificacion_completa=True, flujo_audio_verificado=True, naturaleza="Exportación reproducible de widgets reales y de los mismos compositores que produjeron los MP4 del juego; no grabación de una sesión humana.", sonido="Voces neuronales locales completas, música y ambiente CC0 incluidos, mezcla AAC estéreo. No se realizó evaluación auditiva humana.", balance=dict(accion="contrastar", rol="periodista", vertice_emisor="carlos", alcance=juego_balance.ultimo_registro["alcance"], antes=juego_balance.ultimo_registro["antes"], despues=juego_balance.ultimo_registro["despues"]), victorias_reales=fuentes_victoria, cortes=[dict(tipo=t["tipo"], clave=t["clave"], inicio=t["inicio"], duracion=t["duracion"], voz={k:v for k,v in t["voz"].items() if k != "ruta"} if "voz" in t else None) for t in plan])
    DESTINO.with_suffix(".json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"Verificado: {DESTINO} · {duracion:.2f}s · {DESTINO.stat().st_size/1024/1024:.2f} MiB", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
