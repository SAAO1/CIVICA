"""Ejecuta las pruebas con aislamiento del progreso y limpieza de objetos Qt.

python -B herramientas/verificar_proyecto.py
python -B herramientas/verificar_proyecto.py --patron test_cinematica*.py --log .tmp/pruebas_cine.txt

La biblioteca de lectura se mantiene en memoria. Entre pruebas se procesan las
destrucciones diferidas de Qt, como ocurriría al volver a su bucle de eventos.
Con --log se guarda también un resumen JSON junto al archivo de texto.
"""
from __future__ import annotations

import argparse
import faulthandler
import gc
import json
import os
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_LOGGING_RULES", "qt.multimedia.*=false")

from PyQt6.QtCore import QCoreApplication, QEvent
from juego.lectura import BibliotecaLectura


class ResultadoQt(unittest.TextTestResult):
    """Libera ventanas y medios cuyo deleteLater quedó pendiente al cerrar."""

    def stopTest(self, test):
        super().stopTest(test)
        gc.collect()
        if QCoreApplication.instance() is not None:
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def ejecutar(patron="test_*.py", salida=None):
    os.chdir(RAIZ)
    inicio = time.monotonic()
    with patch("interfaz.BibliotecaLectura", lambda: BibliotecaLectura(None)):
        pruebas = unittest.defaultTestLoader.discover(str(RAIZ / "tests"), pattern=patron)
        resultado = unittest.TextTestRunner(stream=salida or sys.stderr, verbosity=2,
                                            resultclass=ResultadoQt).run(pruebas)
    resumen = {
        "pruebas": resultado.testsRun,
        "fallas": len(resultado.failures),
        "errores": len(resultado.errors),
        "omitidas": len(resultado.skipped),
        "segundos": round(time.monotonic()-inicio, 3),
        "limpieza_qt_entre_pruebas": True,
    }
    return resultado.wasSuccessful(), resumen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--patron", default="test_*.py", help="Patrón de archivos de pruebas")
    parser.add_argument("--log", type=Path, help="Archivo de resultados y resumen JSON paralelo")
    args = parser.parse_args()
    if args.log:
        ruta_log = args.log.resolve()
        ruta_log.parent.mkdir(parents=True, exist_ok=True)
        with ruta_log.open("w", encoding="utf-8", buffering=1) as salida:
            faulthandler.enable(salida)
            try:
                correcto, resumen = ejecutar(args.patron, salida)
            finally:
                faulthandler.enable(sys.stderr)
        ruta_log.with_suffix(".json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        faulthandler.enable()
        correcto, resumen = ejecutar(args.patron)
    print(json.dumps(resumen, ensure_ascii=False), flush=True)
    return 0 if correcto else 1


if __name__ == "__main__":
    raise SystemExit(main())
