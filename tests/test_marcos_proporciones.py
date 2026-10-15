import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QColor, QImage, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication

from arte import _dibujar_segmentos, geometria_dialogo


class PruebasMarcosProporcionados(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_esquinas_conservan_escala_y_celdas_no_dejan_costuras(self):
        fuente = QPixmap(120, 80)
        fuente.fill(QColor("#102030"))
        p = QPainter(fuente)
        p.fillRect(0, 0, 12, 12, QColor("#ff9900"))
        p.fillRect(108, 68, 12, 12, QColor("#00ccaa"))
        p.end()
        imagen = QImage(647, 213, QImage.Format.Format_ARGB32)
        imagen.fill(QColor(0, 0, 0, 0))
        p = QPainter(imagen)
        _dibujar_segmentos(p, QRectF(imagen.rect()), fuente, 20, 20, 1)
        p.end()
        self.assertEqual(imagen.pixelColor(11, 11), QColor("#ff9900"))
        self.assertEqual(imagen.pixelColor(12, 11), QColor("#102030"))
        self.assertEqual(imagen.pixelColor(635, 201), QColor("#00ccaa"))
        self.assertEqual(imagen.pixelColor(634, 201), QColor("#102030"))
        for x in (19, 20, 626, 627):
            for y in range(imagen.height()):
                self.assertEqual(imagen.pixelColor(x, y).alpha(), 255)
        for y in (19, 20, 192, 193):
            for x in range(imagen.width()):
                self.assertEqual(imagen.pixelColor(x, y).alpha(), 255)

    def test_cartela_no_se_estira_al_ancho_del_dialogo(self):
        pequeno = geometria_dialogo(QRectF(0, 0, 1366, 220))
        grande = geometria_dialogo(QRectF(0, 0, 1920, 220))
        self.assertLess(grande[1].width()/pequeno[1].width(), 1.11)
        for ancho, areas in ((1366, pequeno), (1920, grande)):
            for area in areas:
                self.assertTrue(QRectF(0, 0, ancho, 220).contains(area))
            self.assertLess(areas[1].bottom(), areas[0].top())
            self.assertLess(areas[0].bottom(), areas[2].top())


if __name__ == "__main__":
    unittest.main()
