"""Arranque de la campaña breve de CIVICA."""
import argparse
import sys
from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication
from interfaz.feria.ventana import VentanaInvestigacion


def main():
    parser = argparse.ArgumentParser(description="CIVICA · La última hora — tres capítulos, seis investigaciones.")
    parser.add_argument("--semilla", type=int)
    parser.add_argument("--sin-audio", action="store_true")
    parser.add_argument("--sin-limite", action="store_true")
    parser.add_argument("--sin-eventos", action="store_true")
    parser.add_argument("--rol", choices=("ciudadano", "periodista"), help="Comenzar directamente una investigación individual.")
    parser.add_argument("--captura", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    app = QApplication.instance() or QApplication(sys.argv)
    ventana = VentanaInvestigacion(semilla=args.semilla, sin_audio=args.sin_audio,
                                  sin_limite=args.sin_limite, eventos=not args.sin_eventos)
    if args.rol:
        ventana.nueva_partida(args.rol)
    ventana.showMaximized()
    if args.captura:
        def capturar():
            args.captura.parent.mkdir(parents=True, exist_ok=True)
            ventana.grab().save(str(args.captura))
            ventana.close()
            app.quit()
        QTimer.singleShot(1200, capturar)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
