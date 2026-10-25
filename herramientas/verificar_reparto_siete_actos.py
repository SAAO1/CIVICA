"""Comprueba cinco invitados solos a tres resoluciones, con entradas Qt reales.

Las voces y el transporte cinematográfico se aíslan para inspeccionar el reparto.
El contacto JPG reúne quince capturas nativas reducidas; --individuales guarda
además los encuadres completos.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import time
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tests"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_LOGGING_RULES", "qt.multimedia.*=false")

from PyQt6.QtCore import QAbstractAnimation, QCoreApplication, QEvent, Qt
from PyQt6.QtGui import QColor, QFont, QImage, QPainter
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication
from juego.acciones import accion_por_defecto
from juego.campana_extendida import DIALOGOS_NUEVOS
from juego.cinematica_personajes_extendida import clave_personaje_extendido
from juego.lectura import BibliotecaLectura
from juego.partida import Juego
from test_balance_roles_ui import AudioConSenales, crear_ventana

REPARTO = ((90, "INFLUENCER"), (100, "JUAN"), (10, "ADRIAN"),
           (100, "LAURA"), (40, "CAMILA"))
TAMANOS = ((1100, 700), (1366, 768), (1920, 1080))


def esperar(condicion, descripcion, segundos=5):
    fin = time.monotonic() + segundos
    while not condicion():
        if time.monotonic() >= fin:
            raise AssertionError(f"Tiempo agotado: {descripcion}")
        QTest.qWait(15)


def caso(identificador):
    juego = Juego(4, eventos=False, campana="extendida")
    juego.iniciar_primera_publicacion()
    while juego.publicacion_actual_id != identificador:
        assert juego.ejecutar_accion(accion_por_defecto(juego.jugador.rol))
        assert juego.avanzar_publicacion()
    return juego


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--individuales", action="store_true")
    args = parser.parse_args()
    app = QApplication.instance() or QApplication([])
    vistas = RAIZ / "docs/vistas"
    vistas.mkdir(parents=True, exist_ok=True)
    contacto = QImage(1440, 1490, QImage.Format.Format_RGB32)
    contacto.fill(QColor("#0d2432"))
    pintor = QPainter(contacto)
    registros, parejas = [], []
    try:
        with (patch("configuracion.cargar", return_value={}),
              patch("configuracion.guardar"),
              patch("interfaz.GestorAudio", AudioConSenales),
              patch("interfaz.BibliotecaLectura", lambda: BibliotecaLectura(None)),
              patch("cinematica_narrativa.CapaCinematica._reproducir_si_corresponde")):
            ventana = crear_ventana()
            ventana.animar_personajes = True
            ventana.reducir_movimiento = False
            ventana.aplicar_accesibilidad()
            ventana.velocidad_texto = 0
            try:
                for columna, (ancho, alto) in enumerate(TAMANOS):
                    ventana.resize(ancho, alto)
                    app.processEvents()
                    for fila, (identificador, nombre) in enumerate(REPARTO):
                        juego = caso(identificador)
                        texto = next(t for h, t in DIALOGOS_NUEVOS[identificador]
                                     if h == nombre and clave_personaje_extendido(t, h, juego) is None)
                        ventana.establecer_juego(juego)
                        ventana.mostrar_escena(ventana.ESCENA_DIALOGO)
                        escena = ventana.escena_dialogo
                        escena.timer_inicio.stop()
                        escena.dialogo_actual = next(i for i, par in enumerate(escena.dialogos)
                                                    if par == (nombre, texto))
                        escena.iniciar_dialogo(texto, nombre, escena.presentes_dialogo)
                        actor = escena.personajes[nombre]
                        esperar(lambda: actor.animacion_entrada.state() != QAbstractAnimation.State.Running,
                                f"entrada real de {nombre}")
                        esperar(lambda: not escena.animando, f"panel de {nombre}")
                        escena.revelar_texto()
                        app.processEvents()
                        activos = [n for n, p in escena.personajes.items() if p.isVisible()]
                        assert activos == [nombre], activos
                        assert actor.geometry() == actor._encuadre_objetivo
                        assert actor.x() >= escena.width() * .64
                        assert actor.geometry().right() < escena.width()
                        assert actor.imagen.direccion_mirada == "izquierda"
                        assert actor.imagen_oscura.direccion_mirada == "izquierda"
                        captura = ventana.grab().toImage()
                        archivo = None
                        if args.individuales:
                            archivo = vistas / f"reparto_{ancho}_{nombre}.jpg"
                            assert captura.save(str(archivo), "JPG", 87)
                        mini = captura.scaled(468, 268, Qt.AspectRatioMode.KeepAspectRatio,
                                              Qt.TransformationMode.SmoothTransformation)
                        x = columna * 480 + (480-mini.width())//2
                        y = fila * 298 + 27
                        pintor.setPen(QColor("#f4d293"))
                        pintor.setFont(QFont("Atkinson Hyperlegible", 11))
                        pintor.drawText(columna*480+10, fila*298+20,
                                        f"{nombre} · {ancho} × {alto}")
                        pintor.drawImage(x, y, mini)
                        registros.append(dict(resolucion=[ancho, alto], hablante=nombre,
                                              actores_visibles=activos,
                                              actor_rect=actor.geometry().getRect(), mirada="izquierda",
                                              entrada_real_finalizada=True, movimiento_activado=True,
                                              captura=archivo.relative_to(RAIZ).as_posix() if archivo else None,
                                              contacto_rect=[x, y, mini.width(), mini.height()]))
                    escena.configurar_personajes_para_hablante("PERIODISTA", {"CIUDADANO", "PERIODISTA"})
                    esperar(lambda: all(p.animacion_entrada is None or p.animacion_entrada.state()
                                        != QAbstractAnimation.State.Running
                                        for p in escena.personajes.values()), "retorno de protagonistas")
                    ciudadano, periodista = (escena.personajes[n] for n in ("CIUDADANO", "PERIODISTA"))
                    assert ciudadano.isVisible() and periodista.isVisible()
                    assert ciudadano.geometry().right() < periodista.geometry().left()
                    assert ciudadano.imagen.direccion_mirada == "derecha"
                    assert periodista.imagen.direccion_mirada == "izquierda"
                    parejas.append(dict(resolucion=[ancho, alto], actores_visibles=["CIUDADANO", "PERIODISTA"],
                                        miradas_hacia_centro=True, sin_superposicion=True))
            finally:
                ventana.close()
                ventana.deleteLater()
                app.processEvents()
                QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    finally:
        pintor.end()
    assert contacto.save(str(vistas / "reparto_siete_actos.jpg"), "JPG", 88)
    documento = dict(version=2, correcto=True,
                     naturaleza="Quince encuadres de widgets Qt reales; voces y transporte aislados. "
                                "Cinco NPC solos a tres resoluciones, con entradas completadas en tiempo real.",
                     contacto="docs/vistas/reparto_siete_actos.jpg",
                     capturas=registros, protagonistas=parejas)
    (RAIZ / "docs/verificacion_reparto_siete_actos.json").write_text(
        json.dumps(documento, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print("15 encuadres y 3 retornos comprobados a 1100, 1366 y 1920 píxeles.", flush=True)


if __name__ == "__main__":
    main()
