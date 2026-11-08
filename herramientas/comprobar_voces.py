"""Comprueba el doblaje neuronal local y su reproducción real en Qt.

Ejemplo: python herramientas/comprobar_voces.py --reproducir
No usa red ni descarga voces. La última línea es un diagnóstico JSON.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from audio.gestor_audio import GestorAudio


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reproducir", action="store_true")
    parser.add_argument("--composicion", action="store_true",
                        help="Comprueba también cifras recompuestas con nombre personalizado.")
    args = parser.parse_args()
    app = QApplication.instance() or QApplication([])
    audio = GestorAudio()
    datos = audio.estado_voces()
    datos["reproduccion"] = []
    if args.reproducir and audio.voces_disponibles:
        muestras = [("CIUDADANO", "Hola, soy un vecino de Ciudad Nova."),
                    ("PERIODISTA", "Revisemos las fuentes antes de compartir."),
                    ("NARRADOR", "Cada decisión transforma nuestra ciudad.")]
        if args.composicion:
            muestras.append(("NARRADOR", "Ciudad Nova refleja la decisión de Lucía: confianza +5, "
                             "conflictos -1. Puntuación de la acción: +8."))
        for personaje, texto in muestras:
            estados = []
            niveles = []
            archivos = []
            def comenzar(_nombre):
                estados.append("Speaking")
            def terminar():
                estados.append("Ready")
            audio.voz_iniciada.connect(comenzar)
            audio.voz_finalizada.connect(terminar)
            audio.nivel_voz.connect(niveles.append)
            def registrar_archivo(fuente):
                archivos.append(Path(fuente.toLocalFile()).name)
            audio._reproductor_voz.sourceChanged.connect(registrar_archivo)
            inicio = time.monotonic()
            aceptada = audio.narrar(texto, personaje)
            posicion_maxima = 0
            limite = 22 if texto.startswith("Ciudad Nova refleja") else 8
            while time.monotonic() - inicio < limite:
                QTest.qWait(20)
                posicion_maxima = max(posicion_maxima, audio._reproductor_voz.position())
                if "Speaking" in estados and "Ready" in estados:
                    break
            audio.voz_iniciada.disconnect(comenzar)
            audio.voz_finalizada.disconnect(terminar)
            audio.nivel_voz.disconnect(niveles.append)
            audio._reproductor_voz.sourceChanged.disconnect(registrar_archivo)
            datos["reproduccion"].append({"personaje": personaje, "aceptada": aceptada,
                                         "estados": estados,
                                         "posicion_ms": posicion_maxima,
                                         "duracion_ms": audio._reproductor_voz.duration(),
                                         "envolvente_activa": any(n > 0 for n in niveles),
                                         "archivos": archivos,
                                         "segundos": round(time.monotonic() - inicio, 2)})
        audio.narrar("Esta frase debe detenerse al silenciar el juego.", "NARRADOR")
        QTest.qWait(100)
        audio.silenciar()
        QTest.qWait(80)
        datos["silencio_detiene"] = not audio.hablando and audio._salida_voz.volume() == 0
        datos["silencio_impide_nueva_lectura"] = not audio.narrar("No debe oírse.", "CIUDADANO")
    audio.detener()
    print(json.dumps(datos, ensure_ascii=False))
    if not datos["disponibles"]:
        return 1
    if args.reproducir and (not all("Speaking" in r["estados"] and "Ready" in r["estados"]
                                   for r in datos["reproduccion"])
                            or not datos["silencio_detiene"]):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
