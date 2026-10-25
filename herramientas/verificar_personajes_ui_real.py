"""Doce videos de personajes dentro del diálogo Qt, con voces aisladas.

Comprueba la cubierta anterior a la entrada del panel, reproducción nativa,
ocultamiento del reparto, continuidad al siguiente diálogo y avance normal
antes de los nueve segundos. No modifica preferencias, partidas ni voces.
"""
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
from PyQt6.QtGui import QImage
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication
from herramientas.verificar_reparto_siete_actos import caso, esperar
from herramientas.verificar_inicio_video import datos, diferencia
from juego.cinematica_personajes_extendida import CINEMATICAS_PERSONAJES_EXTENDIDAS
from juego.lectura import BibliotecaLectura
from test_balance_roles_ui import AudioConSenales, crear_ventana


def main():
    catalogo = CINEMATICAS_PERSONAJES_EXTENDIDAS
    for entrada in catalogo.values():
        for tipo in ("video", "poster", "inicio"):
            assert (RAIZ / entrada[tipo]).is_file(), entrada[tipo]
    app = QApplication.instance() or QApplication([])
    registros = []
    with (patch("configuracion.cargar", return_value={}),
          patch("configuracion.guardar") as guardar,
          patch("interfaz.GestorAudio", AudioConSenales),
          patch("interfaz.BibliotecaLectura", lambda: BibliotecaLectura(None))):
        ventana = crear_ventana()
        ventana.resize(1920, 1080)
        ventana.reducir_movimiento = False
        ventana.animar_fondos = True
        ventana.animar_personajes = True
        ventana.velocidad_texto = 0
        ventana.aplicar_accesibilidad()
        app.processEvents()
        try:
            for clave, entrada in catalogo.items():
                juego = caso(entrada["publicacion"])
                ventana.establecer_juego(juego)
                ventana.mostrar_escena(ventana.ESCENA_DIALOGO)
                escena = ventana.escena_dialogo
                escena.timer_inicio.stop()
                escena.dialogo_actual = next(i for i, par in enumerate(escena.dialogos)
                                            if par == (entrada["nombre"], entrada["texto"]))
                indice = escena.dialogo_actual
                escena.mostrar_dialogo_actual()
                cine = escena.cine_narrativo
                assert cine.clave_actual == clave, (clave, cine.clave_actual)
                assert cine._pausada and cine._poster.isVisible()
                assert cine._reproductor is None or cine._reproductor.source().isEmpty()
                cubierta = QImage(str(RAIZ / entrada["inicio"]))
                assert datos(cine._poster.imagen.toImage()) == datos(cubierta), clave
                assert not escena.personajes_activos
                assert all(not p.isVisible() for p in escena.personajes.values())
                primeros = []

                def primer_frame(actual):
                    if actual == clave:
                        frame = cine._video.videoSink().videoFrame()
                        primeros.append((frame.startTime()/1000, cine._video._imagen.copy()))

                cine.video_preparado.connect(primer_frame)
                try:
                    esperar(lambda: cine.estado == "reproduciendo" and primeros,
                            f"corte nativo {clave}", 10)
                    error = diferencia(cubierta, primeros[0][1])
                    assert error < 5, (clave, error)
                    assert not escena.corte_accion_pendiente(), clave
                    esperar(lambda: cine._video.videoSink().videoFrame().startTime() >= 1_000_000,
                            f"reproducción continua de {clave}", 10)
                    posicion = cine._reproductor.position()
                    assert posicion < 5000, (clave, posicion)
                    if escena.escribiendo:
                        escena.revelar_texto()
                    assert not escena.animando
                    QTest.keyClick(escena, Qt.Key.Key_Space)
                    assert escena.dialogo_actual == indice+1, (clave, indice, escena.dialogo_actual)
                    esperar(lambda: cine.clave_actual != clave, f"salida del corte {clave}")
                    esperar(lambda: not escena.animando, f"diálogo siguiente a {clave}")
                    siguiente = escena.dialogos[escena.dialogo_actual][0]
                    if not cine.activa:
                        esperar(lambda: all(p.animacion_entrada is None or p.animacion_entrada.state()
                                            != QAbstractAnimation.State.Running
                                            for p in escena.personajes.values()), "reparto del siguiente plano")
                        visibles = {n for n, p in escena.personajes.items() if p.isVisible()}
                        esperado = ({siguiente} if siguiente not in ("CIUDADANO", "PERIODISTA", "NARRADOR")
                                    else {"CIUDADANO", "PERIODISTA"})
                        assert visibles == esperado, (clave, siguiente, visibles)
                    registros.append(dict(clave=clave, publicacion=entrada["publicacion"],
                                          hablante=entrada["nombre"], resolucion=[1920, 1080],
                                          cubierta_exacta_antes_del_panel=True,
                                          primer_frame_ms=primeros[0][0], diferencia_inicio_rgb=error,
                                          reparto_oculto_durante_video=True,
                                          avance_normal_a_los_ms=posicion,
                                          sin_bloqueo_de_accion=True,
                                          siguiente_dialogo=siguiente, reproduccion_nativa=True))
                    print(f"OK {clave}: portada exacta, video nativo y avance a {posicion} ms", flush=True)
                finally:
                    cine.video_preparado.disconnect(primer_frame)
        finally:
            ventana.close()
            ventana.deleteLater()
            app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert not guardar.called
    documento = dict(correcto=len(registros) == len(catalogo), cantidad=len(registros),
                     audio="Señales y voces aisladas; no se reproducen ni modifican MP3.",
                     transporte="QMediaPlayer nativo y MP4 reales a 1920 × 1080.",
                     guardado_config_no_invocado=True, casos=registros)
    (RAIZ / "docs/verificacion_personajes_ui_real.json").write_text(
        json.dumps(documento, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(dict(correcto=True, videos=len(registros)), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
