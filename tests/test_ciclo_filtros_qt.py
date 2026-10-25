"""Los filtros de ventana toleran la limpieza parcial de wrappers por GC."""
import gc
import os
import unittest
import weakref

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import QCoreApplication, QEvent
from PyQt6.QtWidgets import QApplication, QWidget
from cinematica_narrativa import CapaCinematica
from efectos_narrativos import CapaEfectos
from resultados_visual import BalanceAnimado


class PruebasCicloFiltrosQt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def crear_capas(self, ventana):
        capas = [CapaCinematica(ventana), BalanceAnimado(ventana), CapaEfectos(ventana)]
        for capa in capas:
            capa.resize(320, 180)
        ventana.show()
        for capa in capas:
            capa.show()
        self.app.processEvents()
        return capas

    def test_evento_nativo_con_atributo_borrado_no_escapa_del_callback(self):
        ventana = QWidget()
        capas = self.crear_capas(ventana)
        try:
            for capa in capas:
                with self.subTest(capa=type(capa).__name__):
                    self.assertIs(capa._ventana_observada, ventana)
                    del capa._ventana_observada
                    # Es un filtro instalado de verdad. Un AttributeError
                    # aquí terminaría el proceso PyQt fuera de unittest.
                    QCoreApplication.sendEvent(ventana, QEvent(QEvent.Type.WindowStateChange))
                    capa._ventana_observada = ventana
        finally:
            for capa in capas:
                capa.detener()
            ventana.close()
            ventana.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_detener_desvincula_y_nuevo_uso_vuelve_a_observar(self):
        ventana = QWidget()
        capas = self.crear_capas(ventana)
        try:
            for capa in capas:
                capa.detener()
                self.assertIsNone(capa._ventana_observada)
            capas[0].show()
            capas[1].preparar({"puntos": 1})
            self.assertTrue(capas[2].reproducir("rumor"))
            for capa in capas:
                self.assertIs(capa._ventana_observada, ventana)
            QCoreApplication.sendEvent(ventana, QEvent(QEvent.Type.WindowStateChange))
        finally:
            for capa in capas:
                capa.detener()
            ventana.close()
            ventana.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_cerrar_y_recolectar_ciclos_de_capas_no_conserva_ventana_observada(self):
        referencias = []
        for _ in range(8):
            ventana = QWidget()
            capas = self.crear_capas(ventana)
            ventana.capas = capas
            referencias.append(weakref.ref(ventana))
            capas[1].preparar({"puntos": 2})
            capas[2].reproducir("rumor")
            ventana.close()
            for capa in capas:
                capa.detener()
                self.assertIsNone(capa._ventana_observada)
            del capa, capas, ventana
            gc.collect()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            self.app.processEvents()
        gc.collect()
        self.assertTrue(all(referencia() is None for referencia in referencias))


if __name__ == "__main__":
    unittest.main()
