"""Comprueba los vídeos del narrador y personajes dentro de la interfaz.

Usa el decodificador real de Qt y contrasta el fotograma entregado por
QVideoSink con lo que pinta la ventana; no confunde un cartel con vídeo.
Guarda sólo un contacto pequeño, dos capturas JPG y un resumen JSON.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import sys
import time
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_LOGGING_RULES", "qt.multimedia.*=false")
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtGui import QColor, QImage, QPainter, QFont
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from interfaz import VentanaPrincipal
from juego.cinematica import CINEMATICAS
from juego.lectura import BibliotecaLectura
from juego.partida import Juego


def esperar(condicion, descripcion, limite=8):
    inicio = time.monotonic()
    while not condicion():
        if time.monotonic() - inicio > limite:
            raise AssertionError(f"Tiempo agotado: {descripcion}")
        QTest.qWait(20)


def cubrir(imagen, tamano):
    escalada = imagen.scaled(tamano, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                            Qt.TransformationMode.SmoothTransformation)
    return escalada.copy((escalada.width()-tamano.width())//2,
                         (escalada.height()-tamano.height())//2,
                         tamano.width(), tamano.height())


def diferencia(a, b, rect=None):
    if rect is not None:
        a, b = a.copy(rect), b.copy(rect)
    a = a.scaled(64, 36).convertToFormat(QImage.Format.Format_RGB32)
    b = b.scaled(64, 36).convertToFormat(QImage.Format.Format_RGB32)
    suma = 0
    for y in range(36):
        for x in range(64):
            ca, cb = a.pixelColor(x, y), b.pixelColor(x, y)
            suma += abs(ca.red()-cb.red()) + abs(ca.green()-cb.green()) + abs(ca.blue()-cb.blue())
    return round(suma/(64*36*3), 4)


def preparar(ventana, clave):
    entrada = CINEMATICAS[clave]
    # Cada toma necesita una partida aislada. El catálogo vuelve de la última
    # publicación a la primera al empezar los cortes de personajes.
    juego = Juego(4, eventos=False)
    juego.iniciar_primera_publicacion()
    ventana.establecer_juego(juego)
    if entrada["publicacion"] is None:
        indice = ["ciudad_48h", "mensaje_barrio", "rumor_colegio"].index(clave)
        ventana.mostrar_escena(ventana.ESCENA_NARRACION_1 + indice)
    else:
        while juego.obtener_publicacion_actual() is not None and juego.obtener_publicacion_actual().id != entrada["publicacion"]:
            juego.ejecutar_accion("verificar")
            juego.avanzar_publicacion()
        if juego.obtener_publicacion_actual() is None:
            raise ValueError(f"La campaña no contiene la publicación {entrada['publicacion']}")
        ventana.mostrar_escena(ventana.ESCENA_DIALOGO)
    escena = ventana.escenas.currentWidget()
    escena.timer_inicio.stop()
    escena.iniciar_dialogo(entrada["texto"], entrada["nombre"])
    escena.animacion.setCurrentTime(escena.animacion.duration())
    escena.animacion.stop()
    if not escena._audiovisual_iniciado:
        escena.finalizar_animacion_dialogo()
    escena.timer_texto.stop()
    escena.revelar_texto()
    ventana.animacion_transicion.stop()
    ventana.velo_transicion.hide()
    return escena


def verificar(destino):
    app = QApplication.instance() or QApplication([])
    destino.mkdir(parents=True, exist_ok=True)
    resumen = {"clips": [], "errores": []}
    contacto = QImage(960, math.ceil(len(CINEMATICAS)/3)*204, QImage.Format.Format_RGB32)
    contacto.fill(QColor("#10222a"))
    with (patch("interfaz.GestorAudio"), patch("configuracion.cargar", return_value={}),
          patch("interfaz.BibliotecaLectura", lambda: BibliotecaLectura(None))):
        ventana = VentanaPrincipal()
        ventana.audio.hablando = False
        ventana.sin_limite = True
        ventana.velocidad_texto = 0
        ventana.reducir_movimiento = False
        ventana.animar_fondos = True
        ventana.resize(1366, 768)
        juego = Juego(4, eventos=False)
        juego.iniciar_primera_publicacion()
        ventana.establecer_juego(juego)
        ventana.show()
        app.processEvents()
        try:
            for indice, clave in enumerate(CINEMATICAS):
                escena = preparar(ventana, clave)
                capa = escena.cine_narrativo
                assert capa.clave_actual == clave
                esperar(lambda: capa.estado == "reproduciendo", f"primer fotograma de {clave}")
                reproductor = capa._reproductor
                assert reproductor.audioOutput() is None, "El vídeo no debe duplicar la voz"
                inicial = capa._video.videoSink().videoFrame().toImage().copy()
                reproductor.setPosition(5000)
                esperar(lambda: reproductor.position() >= 4950, f"seek de {clave}")
                esperar(lambda: capa._video.videoSink().videoFrame().startTime() >= 4_900_000,
                        f"fotograma decodificado a cinco segundos de {clave}")
                reproductor.pause()
                QTest.qWait(60)
                fotograma = capa._video.videoSink().videoFrame()
                tiempo_fotograma = fotograma.startTime()/1000
                fuente = fotograma.toImage()
                assert not fuente.isNull(), f"{clave}: QVideoSink no entregó imagen"
                assert abs(tiempo_fotograma-5000) < 800, f"{clave}: el fotograma sigue fuera de la búsqueda ({tiempo_fotograma} ms)"
                movimiento = diferencia(inicial, fuente)
                assert movimiento > .01, f"{clave}: el vídeo no cambió de imagen"
                esperado = cubrir(fuente, capa._video.size())
                pintado = capa._video.grab().toImage()
                diferencia_video = diferencia(pintado, esperado)
                captura = ventana.grab().toImage()
                # El área central evita botones, subtítulos y los márgenes de lectura.
                posicion_capa = capa.mapTo(ventana, QPoint(0, 0))
                captura_capa = captura.copy(QRect(posicion_capa, capa.size()))
                centro = QRect(120, 110, 1120, 270)
                diferencia_ventana = diferencia(captura_capa, esperado, centro)
                if diferencia_video >= 8 or diferencia_ventana >= 18:
                    captura.save(str(destino / "diagnostico_ventana.jpg"), "JPG", 86)
                    esperado.save(str(destino / "diagnostico_sink.jpg"), "JPG", 86)
                    pintado.save(str(destino / "diagnostico_widget.jpg"), "JPG", 86)
                assert diferencia_video < 8, f"{clave}: el widget no muestra el fotograma ({diferencia_video}), ventana={diferencia_ventana}"
                assert diferencia_ventana < 18, f"{clave}: la ventana tapa el vídeo ({diferencia_ventana})"
                assert all(not actor.isVisible() for actor in escena.personajes.values())
                if clave in ("rumor_colegio", "mapa_parque", "person_colegio_c", "person_cultura_c", "person_voto_p"):
                    assert captura.save(str(destino / f"{clave}_1366.jpg"), "JPG", 88)
                pintor = QPainter(contacto)
                x, y = (indice % 3)*320, (indice//3)*204
                pintor.drawImage(QRect(x, y, 320, 180), captura)
                pintor.setPen(QColor("#e9e2c7"))
                pintor.setFont(QFont("Segoe UI", 9))
                pintor.drawText(QRect(x+7, y+180, 306, 24), Qt.AlignmentFlag.AlignVCenter, clave)
                pintor.end()
                posicion = reproductor.position()
                capa.pausar()
                assert reproductor.source().isEmpty() and capa.estado == "pausada"
                capa.reanudar()
                esperar(lambda: capa.estado == "reproduciendo"
                        and abs(reproductor.position()-posicion) < 1000,
                        f"reanudar {clave} en {posicion} ms")
                capa.configurar(reducir_movimiento=True)
                assert reproductor.source().isEmpty() and capa.estado == "poster"
                assert capa._poster.isVisible() and not capa._poster.imagen.isNull()
                capa.configurar(reducir_movimiento=False)
                esperar(lambda: capa.estado == "reproduciendo", f"restaurar movimiento {clave}")
                escena.iniciar_dialogo("Revisemos la fuente antes de decidir.", "PERIODISTA", {"CIUDADANO", "PERIODISTA"})
                assert not capa.activa and reproductor.source().isEmpty()
                assert all(actor.isVisible() for actor in escena.personajes.values())
                resumen["clips"].append({"clave": clave, "posicion_ms": posicion,
                    "fotograma_ms": tiempo_fotograma, "movimiento_rgb": movimiento,
                    "diferencia_widget_rgb": diferencia_video,
                    "diferencia_ventana_rgb": diferencia_ventana,
                    "pausa_reanudar": True, "poster_reducido": True,
                    "fuente_liberada": True, "actores_restaurados": True})
                print(f"OK {clave}: vídeo visible, pausa, cartel y regreso de actores", flush=True)
            contacto.save(str(destino / "contacto_cortes.jpg"), "JPG", 86)
        except BaseException as error:
            resumen["errores"].append(str(error))
            raise
        finally:
            ventana.close()
            app.processEvents()
            (destino / "resultado.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    return resumen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, default=RAIZ / ".tmp/verificacion_cinematicas_real")
    args = parser.parse_args()
    resumen = verificar(args.destino)
    print(json.dumps({"clips_correctos": len(resumen["clips"]), "errores": resumen["errores"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
