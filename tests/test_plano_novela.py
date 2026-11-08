"""Comprobacion de los cuadros visibles y el cierre de un plano real."""
import unittest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtTest import QTest,QSignalSpy
from PyQt6.QtWidgets import QApplication,QWidget
from interfaz.novela.plano import PlanoInvestigacion


class PruebasPlanoNovela(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        self.padre=QWidget()
        self.padre.resize(1100,700)
        self.padre.show()

    def tearDown(self):
        self.padre.close()
        self.app.processEvents()

    def test_video_real_pinta_imagen_en_la_ventana(self):
        plano=PlanoInvestigacion(1,self.padre)
        plano.abrir()
        for _ in range(100):
            self.app.processEvents()
            if not plano.video._imagen.isNull():
                break
            QTest.qWait(30)
        self.assertFalse(plano.video._imagen.isNull(),"No se dibujo ningun cuadro")
        captura=plano.video.grab().toImage()
        colores={captura.pixelColor(x,y).rgb()
                 for x in range(captura.width()//4,captura.width()*3//4,20)
                 for y in range(captura.height()//4,captura.height()*3//4,20)}
        self.assertGreater(len(colores),100,"Solo aparece un fondo plano")
        plano.cancelar()

    def test_adelantar_emite_una_sola_continuacion(self):
        plano=PlanoInvestigacion(1,self.padre)
        terminado=QSignalSpy(plano.terminado)
        plano.abrir()
        QTest.mouseClick(plano.boton,Qt.MouseButton.LeftButton)
        plano.finalizar()
        self.assertEqual(len(terminado),1)
        self.assertFalse(plano.isVisible())


if __name__=="__main__":
    unittest.main()
