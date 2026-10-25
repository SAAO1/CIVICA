"""Verificación del reloj, accesibilidad y fotogramas reales del ambiente."""
import os
from pathlib import Path
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImageReader
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from ambiente_visual import FondoVivo, FPS_AMBIENTE, _perfil


class PruebasFondoVivo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.fondo = FondoVivo()
        self.fondo.resize(640, 360)
        self.fondo.establecer_escena("assets/fondos/Escena 1.jfif")

    def tearDown(self):
        self.fondo.close()

    def test_ambiente_se_adapta_al_arte_y_alias(self):
        self.assertEqual(_perfil("assets/fondos/Escena 2.png", "plaza"), "cafe_exterior")
        self.assertEqual(_perfil("fondos/investigacion.png", "plaza"), "investigacion")
        self.assertEqual(_perfil("otro.png", "oficina"), "investigacion")
        self.assertEqual(_perfil("otro.png", "desconocido"), "ciudad")
        self.assertEqual(_perfil("fondos/cafe_interior.png", "lluvia"), "lluvia")
        self.assertEqual(_perfil("assets/expansion/fondos/plaza_noche.png", "plaza"), "noche")
        self.assertEqual(_perfil("assets/expansion/fondos/cafe_lluvia.png", "plaza"), "cafe_lluvia")
        self.assertEqual(_perfil("assets/expansion/fondos/parque_tarde.png", "plaza"), "parque")

    def test_reloj_solo_corre_visible_y_a_30_fps(self):
        self.assertFalse(self.fondo.animando)
        self.fondo.show()
        self.app.processEvents()
        self.assertTrue(self.fondo.animando)
        self.assertGreaterEqual(self.fondo._timer.interval(), int(1000/FPS_AMBIENTE))
        self.fondo.hide()
        self.app.processEvents()
        self.assertFalse(self.fondo.animando)
        self.assertTrue(self.fondo.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents))

    def test_reducir_movimiento_detiene_y_genera_frame_estatico(self):
        self.fondo.show()
        self.fondo.configurar(reducir_movimiento=True)
        self.assertFalse(self.fondo.animando)
        a = self.fondo.capturar_fotograma(0)
        b = self.fondo.capturar_fotograma(20)
        self.assertEqual(a, b)
        self.fondo.configurar(reducir_movimiento=False)
        self.assertTrue(self.fondo.animando)

    def test_objetos_cambian_y_captura_no_muta_el_reloj(self):
        self.fondo.establecer_tiempo(3)
        a = self.fondo.capturar_fotograma(1, (640, 360))
        b = self.fondo.capturar_fotograma(8, (640, 360))
        self.assertFalse(a.isNull())
        self.assertNotEqual(a, b)
        self.assertEqual(self.fondo.tiempo_actual(), 3)
        self.assertEqual(a, self.fondo.capturar_fotograma(1, (640, 360)))

    def test_todos_los_ambientes_renderizan_sin_error(self):
        for ambiente in ("ciudad", "portada", "cafe_exterior", "cafe", "telefono",
                         "investigacion", "observatorio", "lluvia", "noche", "parque", "cafe_lluvia"):
            self.fondo.establecer_escena("assets/rediseno/fondos/ciudad.png", ambiente)
            with self.subTest(ambiente=ambiente):
                imagen = self.fondo.capturar_fotograma(4, (853, 480))
                self.assertFalse(imagen.isNull())
                self.assertNotEqual(imagen.pixelColor(426, 240).name(), "#172b3b")

    def test_pausa_y_reanudacion_no_incluye_tiempo_oculto(self):
        self.fondo.show()
        self.app.processEvents()
        QTest.qWait(35)
        self.fondo.configurar(activo=False)
        antes = self.fondo.tiempo_actual()
        QTest.qWait(35)
        self.assertEqual(antes, self.fondo.tiempo_actual())
        self.fondo.configurar(activo=True)
        QTest.qWait(20)
        self.assertGreater(self.fondo.tiempo_actual(), antes)

    def test_fondo_faltante_no_rompe_la_escena(self):
        self.fondo.establecer_escena("assets/no_existe.png", intensidad=float("nan"))
        imagen = self.fondo.capturar_fotograma(2)
        self.assertEqual(imagen.pixelColor(10, 10).name(), "#172b3b")
        self.fondo.establecer_tiempo(4)
        self.assertFalse(self.fondo.animando)
        with self.assertRaises(ValueError):
            self.fondo.establecer_tiempo(float("inf"))

    def test_exportacion_gif_reproduce_cuadros_distintos_en_qt(self):
        from herramientas.exportar_ambientes import exportar_gif
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / "escena.gif"
            self.assertEqual(exportar_gif(self.fondo, ruta, 240, 135, 1, 3), 3)
            lector = QImageReader(str(ruta))
            self.assertEqual(lector.imageCount(), 3)
            a = lector.read()
            self.assertFalse(a.isNull(), lector.errorString())
            b = lector.read()
            self.assertFalse(b.isNull(), lector.errorString())
            self.assertEqual((a.width(), a.height()), (240, 135))
            self.assertNotEqual(a, b)
            lector.setFileName("")


if __name__ == "__main__":
    unittest.main()
