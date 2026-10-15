import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt
from interfaz import VentanaPrincipal, Juego


class PruebasInterfaz(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.ventana = VentanaPrincipal()
        self.ventana.resize(1366, 768)
        self.ventana.show()
        self.app.processEvents()

    def tearDown(self):
        self.ventana.close()
        self.ventana.deleteLater()
        self.app.processEvents()

    def test_seleccion_individual_y_red_muestran_solo_dos_personajes(self):
        from paneles import DialogoRol, DialogoRed
        for clase, nombre in ((DialogoRol, "roles"), (DialogoRed, "rol")):
            dialogo = clase(self.ventana)
            combo = getattr(dialogo, nombre)
            self.assertEqual([combo.itemData(i) for i in range(combo.count())], ["ciudadano", "periodista"])
            dialogo.close()

    def test_seis_publicaciones_sin_saltos_ni_doble_accion(self):
        juego = self.ventana.juego
        juego.iniciar_primera_publicacion()
        vistos = []
        while juego.obtener_publicacion_actual() is not None:
            vistos.append(juego.obtener_publicacion_actual().id)
            self.assertTrue(juego.ejecutar_accion("verificar"))
            confianza = juego.confianza
            self.assertFalse(juego.ejecutar_accion("compartir"))
            self.assertEqual(juego.confianza, confianza)
            self.ventana.mostrar_escena(self.ventana.ESCENA_ARBOL)
            self.ventana.escena_arbol.continuar()
            self.assertEqual(self.ventana.escenas.currentIndex(), self.ventana.ESCENA_GRAFO)
            self.ventana.escena_red.continuar.emit()
            # La repetición recibida desde una escena antigua no avanza otra vez.
            self.ventana.continuar_desde_arbol()
        self.assertEqual(vistos, [50, 30, 70, 20, 60, 80])
        self.assertEqual(self.ventana.escenas.currentIndex(), self.ventana.ESCENA_FIN)

    def test_espera_y_salida_bloquean_entradas(self):
        self.ventana.juego.iniciar_primera_publicacion()
        self.ventana.mostrar_escena(self.ventana.ESCENA_DIALOGO)
        escena = self.ventana.escena_dialogo
        escena.avanzar()
        self.assertEqual(escena.dialogo_actual, 0)
        for _ in range(30):
            QTest.qWait(100)
            if not escena.animando:
                break
        self.assertFalse(escena.animando, escena.estado_escena)
        escena.avanzar()  # Revelar texto, sin avanzar.
        self.assertEqual(escena.dialogo_actual, 0)
        escena.avanzar()
        escena.avanzar()
        self.assertEqual(escena.dialogo_actual, 1)
        self.ventana.mostrar_escena(self.ventana.ESCENA_ACCION)
        self.assertFalse(escena.timer_inicio.isActive())
        self.assertFalse(escena.timer_texto.isActive())

