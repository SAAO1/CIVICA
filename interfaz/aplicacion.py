"""Arranque de CIVICA: novela visual original con seis actos e investigación."""
import sys
from pathlib import Path
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication


def main():
    import argparse
    parser = argparse.ArgumentParser(description="CIVICA — Novela visual · Seis actos")
    parser.add_argument("--semilla", type=int, default=4)
    parser.add_argument("--sin-eventos", action="store_true")
    parser.add_argument("--sin-audio", action="store_true")
    parser.add_argument("--sin-limite", action="store_true")
    parser.add_argument("--clasica", action="store_true", help="Abrir la campaña clásica original.")
    parser.add_argument("--legado", action="store_true", help="Abrir la campaña extendida original.")
    parser.add_argument("--rol", choices=("ciudadano","periodista"), help="Comenzar directamente en solitario.")
    parser.add_argument("--captura", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    app = QApplication.instance() or QApplication(sys.argv)
    if args.clasica or args.legado:
        from interfaz.ventana import VentanaPrincipal
        from juego.partida import Juego
        ventana = VentanaPrincipal()
        ventana.establecer_juego(Juego(args.semilla, eventos=not args.sin_eventos,
                                      campana="clasica" if args.clasica else "extendida"))
    else:
        from interfaz.novela.ventana import VentanaNovela
        ventana = VentanaNovela(args.semilla, eventos=not args.sin_eventos)
    ventana.sin_limite = ventana.sin_limite or args.sin_limite
    if args.sin_audio:
        ventana.audio.silenciar()
    if args.rol and hasattr(ventana,"iniciar_solo"):
        ventana.iniciar_solo(args.rol)
    ventana.showMaximized()
    if args.captura:
        def capturar():
            args.captura.parent.mkdir(parents=True,exist_ok=True)
            ventana.grab().save(str(args.captura))
            ventana.close()
            app.quit()
        QTimer.singleShot(1400,capturar)
    return app.exec()
