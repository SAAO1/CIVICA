"""Captura balance central y ocho decisiones usando configuración aislada."""
import os
from pathlib import Path
import sys
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tests"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication
from juego.lectura import BibliotecaLectura
from juego.partida import Juego
from test_balance_roles_ui import AudioConSenales, crear_ventana, preparar_balance


def main():
    app = QApplication.instance() or QApplication([])
    carpeta = RAIZ / "docs/vistas"
    carpeta.mkdir(parents=True, exist_ok=True)
    temporal = RAIZ / ".tmp/capturas_balance_roles"
    temporal.mkdir(parents=True, exist_ok=True)
    with patch("configuracion.cargar", return_value={}), patch("interfaz.GestorAudio", AudioConSenales), patch("interfaz.BibliotecaLectura", lambda: BibliotecaLectura(None)):
        ventana = crear_ventana()
        for rol in ("ciudadano", "periodista"):
            juego = Juego(7, eventos=False)
            juego.seleccionar_rol(rol)
            juego.iniciar_primera_publicacion()
            ventana.establecer_juego(juego)
            ventana.mostrar_escena(ventana.ESCENA_ACCION)
            for ancho, alto in ((1100, 700), (1366, 768), (1920, 1080)):
                ventana.resize(ancho, alto)
                for _ in range(4):
                    app.processEvents()
                ventana.grab().save(str(temporal / f"acciones_{rol}_{ancho}.jpg"), "JPG", 90)
                if ancho == 1366:
                    ventana.grab().save(str(carpeta / f"acciones_{rol}.jpg"), "JPG", 90)
        escena = preparar_balance(ventana, app)
        ventana.audio.segmento_iniciado.emit("confianza")
        for ancho, alto in ((1100, 700), (1366, 768), (1920, 1080)):
            ventana.resize(ancho, alto)
            escena.balance.establecer_tiempo(.27)
            for _ in range(4):
                app.processEvents()
            ventana.grab().save(str(temporal / f"impacto_confianza_{ancho}.jpg"), "JPG", 90)
            if ancho == 1366:
                ventana.grab().save(str(carpeta / "impacto_confianza.jpg"), "JPG", 90)
        ventana.resize(1366, 768)
        for tiempo, nombre in ((0, "antes"), (.95, "despues")):
            escena.balance.establecer_tiempo(tiempo)
            for _ in range(4):
                app.processEvents()
            ventana.grab().save(str(carpeta / f"impacto_confianza_{nombre}.jpg"), "JPG", 90)
        escena.balance.revelar()
        for _ in range(4):
            app.processEvents()
        ventana.grab().save(str(carpeta / "impacto_resumen.jpg"), "JPG", 90)
        ventana.close()
    print("Capturas de balance y roles guardadas en docs/vistas y .tmp/capturas_balance_roles", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
