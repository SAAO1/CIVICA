"""Muestra reproducible de decisiones completas y contadores obligatorios.

Renderiza los widgets reales y el compositor instalado, con sus voces locales.
El transporte multimedia y las preferencias se aíslan para exportar por reloj:
es evidencia visual de composición/UI, no grabación de una sesión humana.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import re
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
from audio.catalogo_voces import cargar_manifest, segmentos_indicadores
from cinematica_acciones_visual import RenderizadorAccion
from herramientas.exportar_ambientes import localizar_ffmpeg
import herramientas.muestra_impacto_roles_finales as anterior
from juego.acciones import accion_por_defecto
from juego.cinematica_acciones import clave_accion
from juego.historia import contenido_resultado
from juego.lectura import BibliotecaLectura
from juego.partida import Juego
from models.jugador import Jugador
from test_balance_roles_ui import AudioConSenales, crear_ventana

FPS, ANCHO, ALTO = 24, 1280, 720
DESTINO = RAIZ / "docs/vistas/muestra_acciones_obligatorias.mp4"


def partida_accion(rol, caso, accion):
    juego = Juego(7, eventos=False)
    juego.seleccionar_rol(rol)
    juego.iniciar_primera_publicacion()
    while juego.obtener_publicacion_actual().id != caso:
        assert juego.ejecutar_accion(accion_por_defecto(rol))
        juego.avanzar_publicacion()
    if accion == "convocar":
        # Selección de un emisor real: no se añaden personas ni conexiones.
        juego.jugador.ciudadano_id = max(juego.grafo.nodos,
            key=lambda id: juego.propagacion.simular(caso, id, 3).alcance)
    assert juego.ejecutar_accion(accion)
    if accion == "convocar":
        assert juego.ultimo_registro["alcance"] >= 8
        assert not clave_accion(juego).endswith(("_sin_receptores", "_alcance_limitado"))
    return juego


def partida_correccion():
    """Dos oficios, turnos y consecuencias válidos; se corrige un rumor previo."""
    juego = Juego(7, eventos=False)
    juego.jugadores = [Jugador(id="c", nombre="Alex", rol="ciudadano", ciudadano_id="carlos"),
                       Jugador(id="p", nombre="Lina", rol="periodista", ciudadano_id="maria")]
    juego.iniciar_primera_publicacion()
    for accion in ("compartir", "reservar", "ignorar", "reservar", "ignorar", "contrastar"):
        assert juego.ejecutar_accion(accion)
        if accion != "contrastar":
            juego.avanzar_publicacion()
    registro = juego.ultimo_registro
    assert registro["publicacion"]["id"] == 80
    assert registro["antes"]["desinformacion"] > registro["despues"]["desinformacion"]
    return juego


def planificar(clips):
    negativo = partida_accion("ciudadano", 50, "compartir")
    positivo = partida_correccion()
    acciones = [("ciudadano", 50, "compartir", negativo),
                ("ciudadano", 30, "conversar", None),
                ("ciudadano", 70, "convocar", None),
                ("ciudadano", 20, "ignorar", None),
                ("periodista", 80, "contrastar", positivo),
                ("periodista", 20, "entrevistar", None),
                ("periodista", 60, "desmentir", None),
                ("periodista", 80, "reservar", None)]
    plan = []
    for i, (rol, caso, accion, juego) in enumerate(acciones):
        if i in (0, 4):
            plan.append(dict(tipo="rol", clave=rol, duracion=2.5))
        juego = juego or partida_accion(rol, caso, accion)
        texto, nombre = contenido_resultado(juego, 1)
        voz = anterior._voz(clips, nombre, texto)
        plan.append(dict(tipo="accion", clave=clave_accion(juego), juego=juego,
                         voz=voz, duracion=max(9., voz["duracion"]+.22)))
        if accion in ("compartir", "contrastar"):
            grupo = accion
            for segmento in segmentos_indicadores(juego.ultimo_registro):
                voz = anterior._voz(clips, "NARRADOR", segmento["texto"])
                plan.append(dict(tipo="balance", clave=segmento["clave"], juego=juego,
                                 grupo=grupo, voz=voz, duracion=max(1.65, voz["duracion"]+.18)))
            plan.append(dict(tipo="foco_final", clave="puntos", grupo=grupo,
                             juego=juego, duracion=1.))
    fotogramas = 0
    for tramo in plan:
        tramo["fotogramas"] = math.ceil(tramo["duracion"]*FPS)
        tramo["duracion"] = tramo["fotogramas"]/FPS
        tramo["inicio"] = fotogramas/FPS
        fotogramas += tramo["fotogramas"]
    return plan, fotogramas/FPS


def preparar_accion(ventana, juego, app):
    ventana.establecer_juego(juego)
    ventana.mostrar_escena(ventana.ESCENA_RESULTADO_1)
    escena = ventana.escena_resultado_1
    escena.timer_inicio.stop()
    escena.preparar_dialogo()
    escena.animacion.setCurrentTime(escena.animacion.duration())
    escena.animacion.stop()
    if not escena._audiovisual_iniciado:
        escena.finalizar_animacion_dialogo()
    escena.revelar_texto()
    escena.timer_texto.stop()
    escena.efectos_narrativos.pausar()
    anterior._sin_transicion(ventana)
    app.processEvents()
    return escena


def bytes_rgb(imagen):
    imagen = imagen.convertToFormat(QImage.Format.Format_RGB888)
    datos = imagen.constBits().asstring(imagen.sizeInBytes())
    if imagen.bytesPerLine() != ANCHO*3:
        datos = b"".join(datos[y*imagen.bytesPerLine():y*imagen.bytesPerLine()+ANCHO*3]
                         for y in range(ALTO))
    return datos


def validar_nivel_audio(ffmpeg, ruta):
    resultado = subprocess.run([ffmpeg, "-hide_banner", "-i", str(ruta), "-vn",
                               "-af", "volumedetect", "-f", "null", "-"],
                              capture_output=True, text=True)
    if resultado.returncode:
        raise RuntimeError(resultado.stderr)
    medias = re.findall(r"mean_volume: (-?[\d.]+) dB", resultado.stderr)
    picos = re.findall(r"max_volume: (-?[\d.]+) dB", resultado.stderr)
    if not medias or not picos:
        raise AssertionError("No se pudo medir la señal de audio")
    media, pico = float(medias[-1]), float(picos[-1])
    assert -60 < media < 0 and pico < 0, "Audio ausente o saturado"
    return dict(metodo="FFmpeg volumedetect", media_db=media, pico_db=pico,
                senal_presente=True, pico_sin_saturacion=True)


def main():
    app = QApplication.instance() or QApplication([])
    plan, duracion = planificar(cargar_manifest()["clips"])
    print(f"Plan: {duracion:.3f}s; ocho acciones completas y dos balances íntegros.", flush=True)
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = localizar_ffmpeg()
    anterior.DESTINO = DESTINO
    balances = {}
    with (patch("configuracion.cargar", return_value={}),
          patch("interfaz.GestorAudio", AudioConSenales),
          patch("interfaz.BibliotecaLectura", lambda: BibliotecaLectura(None)),
          patch("cinematica_narrativa.CapaCinematica._reproducir_si_corresponde")):
        ventana = crear_ventana()
        ventana.resize(ANCHO, ALTO)
        ventana.reducir_movimiento = False
        ventana.animar_fondos = True
        ventana.animar_personajes = True
        ventana.velocidad_texto = 0
        ventana.aplicar_accesibilidad()
        app.processEvents()
        proceso = subprocess.Popen(anterior._comando(ffmpeg, plan, duracion), stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        balance_grupo = None
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
                    anterior._sin_transicion(ventana)
                elif tipo == "accion":
                    escena = preparar_accion(ventana, tramo["juego"], app)
                    render = RenderizadorAccion(clave)
                    assert escena.cine_narrativo.clave_actual == clave
                elif tipo == "balance":
                    if balance_grupo != tramo["grupo"]:
                        balance_grupo = tramo["grupo"]
                        escena_balance = anterior._preparar_balance(ventana, tramo["juego"], app)
                        escena_balance.balance._timer.stop()
                    escena = escena_balance
                    ventana.audio.segmento_iniciado.emit(clave)
                    assert escena.balance.clave_actual == clave
                else:
                    escena = escena_balance
                    ventana.audio.hablando = False
                    ventana.audio.secuencia_finalizada.emit(True)
                    assert escena.balance.completo
                    assert escena.balance.clave_actual == "puntos"
                    balances[tramo["grupo"]] = dict(
                        presentados=list(escena.balance.claves_completadas),
                        tarjetas=escena.balance.tarjetas,
                        todos_completos=escena.balance.completo,
                        ultimo_foco=escena.balance.clave_actual)
                for numero in range(tramo["fotogramas"]):
                    t = numero/FPS
                    if tipo == "accion":
                        escena.cine_narrativo._poster.imagen = QPixmap.fromImage(render.capturar_fotograma(t))
                        escena.cine_narrativo._poster.update()
                        escena.efectos_narrativos.establecer_tiempo(t)
                    elif tipo == "balance":
                        escena.balance.establecer_tiempo(t)
                        escena.balance._paso()
                    app.processEvents()
                    imagen = ventana.grab().toImage()
                    if numero == 6*FPS and tipo == "accion":
                        imagen.save(str(DESTINO.parent/f"accion_organizada_{tramo['juego'].ultimo_registro['accion_rol']}.jpg"), "JPG", 88)
                    if tipo == "balance" and clave in ("confianza", "desinformacion") and numero == 7:
                        imagen.save(str(DESTINO.parent/f"contador_obligatorio_{balance_grupo}_{clave}.jpg"), "JPG", 88)
                    proceso.stdin.write(bytes_rgb(imagen))
                if tipo == "accion":
                    escena.cine_narrativo._cambiar_estado("finalizada")
                print(f"{tramo['inicio']:6.2f}s · {tipo}: {clave} ({tramo['duracion']:.2f}s)", flush=True)
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
    validacion = subprocess.run([ffmpeg, "-v", "error", "-i", str(DESTINO), "-map", "0:v:0",
                                "-map", "0:a:0", "-f", "null", "-"], capture_output=True, text=True)
    if validacion.returncode:
        raise RuntimeError(validacion.stderr)
    niveles = validar_nivel_audio(ffmpeg, DESTINO)
    cortes = []
    for tramo in plan:
        corte = {k: tramo[k] for k in ("tipo", "clave", "inicio", "duracion")}
        if "voz" in tramo:
            corte["voz"] = {k: v for k, v in tramo["voz"].items() if k != "ruta"}
        if tramo["tipo"] == "accion":
            corte["registro_real"] = tramo["juego"].ultimo_registro
        cortes.append(corte)
    metadata = dict(archivo=DESTINO.name, duracion_segundos=duracion, fps=FPS,
        tamano=[ANCHO, ALTO], bytes=DESTINO.stat().st_size,
        sha256=hashlib.sha256(DESTINO.read_bytes()).hexdigest(),
        decodificacion_completa=True, flujo_audio_verificado=True,
        audio_niveles=niveles,
        naturaleza="Exportación por reloj de los widgets reales y del compositor instalado; transporte multimedia y audio del widget aislados con mocks. No es grabación humana ni evidencia de reproducción real del decodificador.",
        sonido="Mezcla AAC de voces neuronales locales completas, música y ambiente CC0. Sin evaluación auditiva humana.",
        botones="Una línea por elección; explicación en ayuda contextual.",
        ejemplos="Las ocho elecciones se ilustran con partidas independientes. El balance de corrección procede de una campaña válida de seis turnos entre dos oficios.",
        balances=balances, cortes=cortes)
    DESTINO.with_suffix(".json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"Verificado: {DESTINO} · {duracion:.2f}s · {DESTINO.stat().st_size/1024/1024:.2f} MiB", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
