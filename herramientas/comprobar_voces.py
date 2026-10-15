"""Comprueba las voces locales y, con --reproducir, su reproducción real.

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
    args = parser.parse_args()
    app = QApplication.instance() or QApplication([])
    audio = GestorAudio()
    datos = audio.estado_voces()
    datos["reproduccion"] = []
    if args.reproducir and audio.voces_disponibles:
        for personaje, texto in (("CIUDADANO", "Hola, soy un vecino de Ciudad Nova."),
                                 ("PERIODISTA", "Revisemos las fuentes antes de compartir."),
                                 ("NARRADOR", "Cada decisión transforma nuestra ciudad.")):
            estados = []
            def registrar(estado):
                estados.append(estado.name)
            audio._sintetizador.stateChanged.connect(registrar)
            inicio = time.monotonic()
            aceptada = audio.narrar(texto, personaje)
            while time.monotonic() - inicio < 8:
                QTest.qWait(20)
                if "Speaking" in estados and audio._sintetizador.state().name == "Ready":
                    break
            audio._sintetizador.stateChanged.disconnect(registrar)
            datos["reproduccion"].append({"personaje": personaje, "aceptada": aceptada,
                                         "estados": estados,
                                         "segundos": round(time.monotonic() - inicio, 2)})
        audio.narrar("Esta frase debe detenerse al silenciar el juego.", "NARRADOR")
        QTest.qWait(100)
        audio.silenciar()
        QTest.qWait(80)
        datos["silencio_detiene"] = not audio.hablando and audio._sintetizador.volume() == 0
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
