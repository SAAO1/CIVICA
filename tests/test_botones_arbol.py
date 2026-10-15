"""Evita que el estilo Qt aplaste los botones al enfocarlos o revelar un recorrido."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from arte import BotonIlustrado, aplicar_estilo, margenes_marco
from interfaz import VentanaPrincipal


class PruebasBotonesArbol(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.preferencias = patch("configuracion.cargar", return_value={})
        self.audio = patch("interfaz.GestorAudio")
        self.preferencias.start()
        self.audio.start().return_value.volumenes = {}
        self.ventana = VentanaPrincipal()
        self.ventana.reducir_movimiento = True
        self.ventana.sin_limite = True
        self.ventana.aplicar_accesibilidad()
        self.ventana.juego.iniciar_primera_publicacion()
        self.ventana.juego.ejecutar_accion("compartir")
        self.ventana.show()

    def tearDown(self):
        self.ventana.close()
        self.app.processEvents()
        self.audio.stop()
        self.preferencias.stop()

    def asentar(self):
        for _ in range(4):
            self.app.processEvents()

    def comprobar(self):
        escena = self.ventana.escena_arbol
        for boton in (escena.boton_inorden, escena.boton_preorden,
                      escena.boton_postorden, escena.boton_continuar):
            self.assertIsInstance(boton, BotonIlustrado)
            self.assertGreaterEqual(boton.height(), 48)
            margenes = margenes_marco("ui/boton.png", boton.size())
            alto_texto = boton.height()-5-margenes.top()-margenes.bottom()
            self.assertGreaterEqual(alto_texto, boton.fontMetrics().height())
            self.assertLessEqual(boton.width(), 320)

    def test_recorridos_clic_foco_y_teclado_conservan_la_altura(self):
        escena = self.ventana.escena_arbol
        for ancho, alto in ((1100, 700), (1366, 768), (1920, 1080)):
            self.ventana.resize(ancho, alto)
            self.ventana.mostrar_escena(self.ventana.ESCENA_ARBOL)
            self.asentar()
            tamanos = [b.size() for b in (escena.boton_inorden, escena.boton_preorden, escena.boton_postorden)]
            for _ in range(2):
                for indice, boton in enumerate((escena.boton_inorden, escena.boton_preorden, escena.boton_postorden)):
                    QTest.mouseClick(boton, Qt.MouseButton.LeftButton)
                    boton.setFocus()
                    QTest.keyClick(boton, Qt.Key.Key_Space)
                    self.asentar()
                    self.comprobar()
                    self.assertEqual(boton.size(), tamanos[indice])
            self.assertEqual(escena.resultado.text(), "POSTORDEN: #50")

    def test_reaplicar_estilo_y_volver_a_la_escena_no_aplasta(self):
        for ancho, alto in ((1920, 1080), (1366, 768), (1100, 700)):
            self.ventana.resize(ancho, alto)
            self.ventana.mostrar_escena(self.ventana.ESCENA_ARBOL)
            self.asentar()
            self.ventana.escena_arbol.boton_postorden.click()
            aplicar_estilo(self.ventana)
            self.asentar()
            self.comprobar()
            self.ventana.mostrar_escena(self.ventana.ESCENA_GRAFO)
            self.ventana.mostrar_escena(self.ventana.ESCENA_ARBOL)
            self.asentar()
            self.comprobar()


if __name__ == "__main__":
    unittest.main()
