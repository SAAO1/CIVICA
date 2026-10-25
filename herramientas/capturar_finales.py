"""Capturas reproducibles del cierre; no modifica preferencias ni partidas."""
import os
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget
from final_ui import EscenaFin
from juego.partida import Juego


def main():
    app = QApplication.instance() or QApplication([])
    ventana = QWidget()
    ventana.juego = Juego(7, eventos=False)
    ventana.reducir_movimiento = True
    ventana.animar_fondos = True
    ventana.volver_portada = lambda: None
    layout = QVBoxLayout(ventana)
    layout.setContentsMargins(0, 0, 0, 0)
    escena = EscenaFin()
    layout.addWidget(escena)
    ventana.resize(1366, 768)
    ventana.show()
    carpeta = RAIZ / "docs/vistas"
    carpeta.mkdir(parents=True, exist_ok=True)
    for identificador in ("juan", "adrian", "laura", "camila", "recuento"):
        ventana.juego = Juego(7, eventos=False)
        ventana.juego.seleccionar_rol("periodista")
        ventana.juego.iniciar_primera_publicacion()
        while not ventana.juego.finalizada:
            publicacion = ventana.juego.obtener_publicacion_actual()
            ventana.juego.ejecutar_accion("contrastar" if publicacion.candidato_id == identificador else "reservar")
            ventana.juego.avanzar_publicacion()
        escena.mostrar()
        for _ in range(5):
            app.processEvents()
        if not ventana.grab().save(str(carpeta / f"final_{identificador}.jpg"), "JPG", 88):
            raise RuntimeError(f"No se guardó {identificador}")
    ventana.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
