"""Renderiza las pantallas reales del juego para revisar composición y tamaños."""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from interfaz import VentanaPrincipal, EscenaCinematica
from juego.partida import Juego
from paneles import DialogoRol, DialogoRed, mostrar_ayuda, mostrar_configuracion
from audio.gestor_audio import GestorAudio
from unittest.mock import patch


def main():
    app = QApplication.instance() or QApplication([])
    destino = RAIZ / ".tmp/capturas_rediseno"
    destino.mkdir(parents=True, exist_ok=True)
    # La captura revisa composición; la reproducción se prueba por separado.
    with patch.object(GestorAudio, "cambiar_pista", return_value=True), patch.object(GestorAudio, "reproducir_efecto", return_value=True):
        ventana = VentanaPrincipal()
        ventana.reducir_movimiento = True
        ventana.sin_limite = True
        ventana.aplicar_accesibilidad()
        ventana.resize(1366, 768)
        ventana.show()
        juego = Juego(4, eventos=False)
        ventana.establecer_juego(juego)

        def capturar(nombre, indice):
            ventana.mostrar_escena(indice)
            app.processEvents()
            escena = ventana.escenas.currentWidget()
            if isinstance(escena, EscenaCinematica):
                for _ in range(20):
                    QTest.qWait(10)
                    if not escena.animando:
                        break
                escena.avanzar()
            if escena is ventana.escena_accion:
                escena.animacion_panel.setCurrentTime(350)
            if escena is ventana.escena_red:
                escena.completar()
            app.processEvents()
            ventana.grab().save(str(destino / f"{nombre}.png"))
            print(nombre, ventana.size().width(), ventana.size().height(), flush=True)

        capturar("01_portada", ventana.ESCENA_INICIO)
        for nombre, indice in (("02_ciudad", 1), ("03_calle", 2), ("04_telefono", 3), ("05_dialogo", 4), ("06_decision", 5)):
            capturar(nombre, indice)
        juego.ejecutar_accion("compartir")
        for nombre, indice in (("07_consecuencia", 6), ("08_investigacion", 7), ("09_balance", 8), ("10_abb", 9), ("11_observatorio", 11)):
            capturar(nombre, indice)
        while not juego.finalizada:
            if not juego.decision_aplicada:
                juego.ejecutar_accion("verificar")
            juego.avanzar_publicacion()
        capturar("12_final", ventana.ESCENA_FIN)
        for clase, nombre in ((DialogoRol, "13_seleccion"), (DialogoRed, "14_sala")):
            dialogo = clase(ventana)
            dialogo.show()
            app.processEvents()
            dialogo.grab().save(str(destino / f"{nombre}.png"))
            dialogo.close()
        # Se capturan los modales sin alterar preferencias de la persona.
        from PyQt6.QtWidgets import QDialog
        def modal(dialogo):
            dialogo.show()
            app.processEvents()
            nombre = "15_ayuda" if "Manual" in dialogo.windowTitle() or "Ayuda" in dialogo.windowTitle() else "16_configuracion"
            dialogo.grab().save(str(destino / f"{nombre}.png"))
            dialogo.close()
            return 0
        with patch.object(QDialog, "exec", modal):
            mostrar_ayuda(ventana)
            mostrar_configuracion(ventana)
        ventana.close()
        app.processEvents()
    print(destino, flush=True)


if __name__ == "__main__":
    main()
