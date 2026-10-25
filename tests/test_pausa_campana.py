"""La presentación se pausa aunque el plazo o la sala cambien de escena."""
import os
import time
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import QCoreApplication, QEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from interfaz import VentanaPrincipal
from juego.eventos import Evento
from juego.lectura import BibliotecaLectura
from juego.partida import Juego


class PruebasPausaCampana(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.parches = [patch("interfaz.GestorAudio"), patch("configuracion.cargar", return_value={}),
                        patch("interfaz.BibliotecaLectura", lambda: BibliotecaLectura(None))]
        for parche in self.parches:
            parche.start()
        self.ventana = VentanaPrincipal()
        self.ventana.audio.hablando = False
        self.ventana.reducir_movimiento = True
        self.ventana.aplicar_accesibilidad()
        juego = Juego(4, eventos=False)
        juego.iniciar_primera_publicacion()
        self.ventana.establecer_juego(juego)
        self.ventana.show()
        self.app.processEvents()

    def tearDown(self):
        self.ventana.close()
        self.ventana.deleteLater()
        self.app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        for parche in reversed(self.parches):
            parche.stop()

    def esperar_hasta(self, condicion, mensaje):
        """Espera el estado de Qt, sin asumir un primer pintado de 70 ms."""
        limite = time.monotonic() + 5
        while not condicion() and time.monotonic() < limite:
            QTest.qWait(10)
        self.assertTrue(condicion(), mensaje)

    def test_timeout_minimizado_aplica_decision_pero_difiere_narracion_hasta_restaurar(self):
        v = self.ventana
        v.juego.evento_actual = Evento("urgente", "Una alerta necesita tu decisión.", 1)
        v.mostrar_escena(v.ESCENA_ACCION)
        self.app.processEvents()
        v.showMinimized()
        self.app.processEvents()
        self.assertTrue(v.escena_accion.timer_decision.isActive())
        v.audio.narrar.reset_mock()
        v.escena_accion.segundos_restantes = 1
        v.escena_accion.cuenta_regresiva()
        self.esperar_hasta(lambda: v.escenas.currentIndex() == v.ESCENA_RESULTADO_1
                          and v.escena_resultado_1.lectura_pausada
                          and not v.escena_resultado_1.timer_texto.isActive(),
                          "El resultado nuevo debe quedar pausado mientras la ventana está minimizada")
        self.assertEqual(v.escenas.currentIndex(), v.ESCENA_RESULTADO_1)
        self.assertEqual(len(v.juego.historial), 1)
        self.assertEqual(v.juego.ultimo_registro["accion_rol"], "ignorar")
        self.assertTrue(v.isMinimized())
        v.audio.narrar.assert_not_called()
        self.assertTrue(v.escena_resultado_1.lectura_pausada)
        self.assertFalse(v.escena_resultado_1.timer_texto.isActive())
        v.showNormal()
        self.esperar_hasta(lambda: not v.escena_resultado_1.lectura_pausada and v.audio.narrar.called,
                          "Restaurar debe reanudar la lectura y la narración vigentes")
        self.assertFalse(v.escena_resultado_1.lectura_pausada)
        self.assertTrue(v.audio.narrar.called)
        self.assertEqual(len(v.juego.historial), 1)

    def test_interrupcion_de_sala_pausa_dialogo_y_reconexion_recupera_estado_autoritativo(self):
        v = self.ventana
        v.mostrar_escena(v.ESCENA_DIALOGO)
        escena = v.escena_dialogo
        self.esperar_hasta(escena.timer_texto.isActive,
                          "El diálogo debe comenzar a escribir antes de interrumpir la sala")
        self.assertTrue(escena.timer_texto.isActive())
        v.audio.hablando = True
        v.cliente_red = MagicMock()
        v.mi_id = v.juego.jugador.id
        v.revision_red = 1
        v.fase_red = "jugando"
        datos = v.juego.datos()
        v.audio.detener_voz.reset_mock()
        v.recibir_mensaje(dict(tipo="estado", revision=2, fase="interrumpida", datos=datos,
                              desconectados=["Otro participante"]))
        self.app.processEvents()
        self.assertTrue(escena.lectura_pausada)
        self.assertFalse(escena.timer_texto.isActive())
        self.assertTrue(escena.cine_narrativo._pausada)
        self.assertTrue(v.audio.detener_voz.called)
        self.assertFalse(v.escena_red.boton_continuar.isEnabled())
        v.recibir_mensaje(dict(tipo="estado", revision=3, fase="jugando", datos=datos,
                              desconectados=[], plazo_segundos=None))
        self.app.processEvents()
        self.assertEqual(v.escenas.currentWidget(), v.escena_accion)
        self.assertTrue(all(b.isEnabled() for b in v.escena_accion.botones_por_accion.values()))
        self.assertEqual(v.juego.datos(), datos)


if __name__ == "__main__":
    unittest.main()
