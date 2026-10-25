"""Capturas reproducibles de la novela sin modificar preferencias ni biblioteca."""
import os
import sys
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from PyQt6.QtWidgets import QApplication
from interfaz import VentanaPrincipal
from juego.lectura import BibliotecaLectura
from juego.partida import Juego


def main():
    app = QApplication.instance() or QApplication([])
    destino = RAIZ / ".tmp/capturas_novela"
    destino.mkdir(parents=True, exist_ok=True)
    with (patch("interfaz.GestorAudio"), patch("configuracion.cargar", return_value={}),
          patch("interfaz.BibliotecaLectura", lambda: BibliotecaLectura(None))):
        ventana = VentanaPrincipal()
        ventana.reducir_movimiento = True
        ventana.sin_limite = True
        ventana.velocidad_texto = 0
        ventana.aplicar_accesibilidad()
        ventana.show()

        def capturar(nombre, ancho):
            app.processEvents()
            ventana.grab().save(str(destino / f"{nombre}_{ancho}.png"))

        for ancho, alto in ((1100, 700), (1366, 768), (1920, 1080)):
            ventana.resize(ancho, alto)
            juego = Juego(4, eventos=False)
            juego.iniciar_primera_publicacion()
            ventana.establecer_juego(juego)
            ventana.mostrar_escena(ventana.ESCENA_DIALOGO)
            escena = ventana.escena_dialogo
            escena.timer_inicio.stop()
            escena.dialogo_actual = 1
            escena.mostrar_dialogo_actual()
            escena.animacion.setCurrentTime(escena.animacion.duration())
            for personaje in escena.personajes.values():
                for animacion in (personaje.animacion_fade, personaje.animacion_entrada):
                    if animacion:
                        animacion.setCurrentTime(animacion.duration())
            capturar("dialogo", ancho)
            ventana.mostrar_escena(ventana.ESCENA_ACCION)
            ventana.escena_accion.animacion_panel.setCurrentTime(350)
            capturar("decision", ancho)
            ventana.abrir_cuaderno()
            app.processEvents()
            cuaderno = ventana.cuaderno
            cuaderno.pistas[0].setChecked(True)
            app.processEvents()
            cuaderno.grab().save(str(destino / f"fuentes_{ancho}.png"))
            cuaderno.pestanas.setCurrentIndex(1)
            app.processEvents()
            cuaderno.grab().save(str(destino / f"personajes_{ancho}.png"))
            cuaderno.close()
            juego.ejecutar_accion("compartir")
            ventana.mostrar_escena(ventana.ESCENA_RESULTADO_1)
            ventana.abrir_cuaderno(3)
            app.processEvents()
            ventana.cuaderno.grab().save(str(destino / f"galeria_{ancho}.png"))
            ventana.cuaderno.close()
            print(f"Cinco vistas: {ancho}x{alto}", flush=True)
        ventana.close()
        app.processEvents()
    print(destino, flush=True)


if __name__ == "__main__":
    main()
