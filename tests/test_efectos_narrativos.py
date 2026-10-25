"""Efectos del relato: transparencia, diferencias visuales y ciclo de vida."""
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QSignalSpy, QTest
from PyQt6.QtWidgets import QApplication, QWidget

from efectos_narrativos import CapaEfectos, EFECTOS, FPS_EFECTOS


class PruebasEfectosNarrativos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.capa = CapaEfectos()
        self.capa.resize(640, 360)

    def tearDown(self):
        self.capa.detener()
        self.capa.close()
        self.app.processEvents()

    def test_no_roba_foco_ni_clic_y_deja_libre_la_lectura(self):
        self.assertTrue(self.capa.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents))
        self.assertEqual(self.capa.focusPolicy(), Qt.FocusPolicy.NoFocus)
        for tipo in EFECTOS:
            self.capa.reproducir(tipo, 6)
            imagen = self.capa.capturar_fotograma(1, (640, 360))
            with self.subTest(tipo=tipo):
                for y in (250, 300, 359):
                    self.assertTrue(all(imagen.pixelColor(x, y).alpha() == 0
                                        for x in range(0, 640, 17)))

    def test_cada_efecto_tiene_imagenes_distintas_y_animadas(self):
        firmas = set()
        for tipo in EFECTOS:
            self.capa.reproducir(tipo, 8)
            a = self.capa.capturar_fotograma(.9, (320, 180))
            b = self.capa.capturar_fotograma(2.8, (320, 180))
            with self.subTest(tipo=tipo):
                self.assertNotEqual(a, b)
                # Algunas formas son pequeñas: mirar cada pixel, no una grilla.
                self.assertTrue(any(a.pixelColor(x, y).alpha()
                                    for y in range(122) for x in range(320)))
            firmas.add(bytes(a.constBits().asstring(a.sizeInBytes())))
        self.assertEqual(len(firmas), len(EFECTOS))

    def test_tiempo_fijo_es_reproducible_y_exportar_no_cambia_el_reloj(self):
        self.capa.reproducir("rumor", 10)
        self.capa.establecer_tiempo(2)
        self.capa.show()
        self.app.processEvents()
        self.assertFalse(self.capa.animando)
        a = self.capa.capturar_fotograma(1)
        self.assertEqual(a, self.capa.capturar_fotograma(1))
        self.assertEqual(self.capa.tiempo_actual(), 2)
        self.capa.establecer_tiempo(None)
        self.assertTrue(self.capa.animando)
        self.assertGreaterEqual(self.capa.tiempo_actual(), 2)

    def test_pausa_oculta_no_consume_duracion_y_reanuda(self):
        self.capa.reproducir("lluvia", 10)
        self.assertFalse(self.capa.animando)
        self.capa.show()
        self.app.processEvents()
        self.assertTrue(self.capa.animando)
        self.assertGreaterEqual(self.capa._timer.interval(), int(1000/FPS_EFECTOS))
        QTest.qWait(30)
        self.capa.hide()
        congelado = self.capa.tiempo_actual()
        QTest.qWait(40)
        self.assertEqual(self.capa.tiempo_actual(), congelado)
        self.capa.show()
        self.app.processEvents()
        QTest.qWait(20)
        self.assertGreater(self.capa.tiempo_actual(), congelado)
        self.capa.configurar(activo=False)
        congelado = self.capa.tiempo_actual()
        QTest.qWait(20)
        self.assertEqual(self.capa.tiempo_actual(), congelado)
        self.capa.configurar(activo=True)
        self.assertTrue(self.capa.animando)

    def test_reducir_movimiento_conserva_composicion_quieta(self):
        self.capa.reproducir("notificacion", 7)
        self.capa.show()
        self.capa.configurar(reducir_movimiento=True)
        self.assertFalse(self.capa.animando)
        self.assertEqual(self.capa.capturar_fotograma(1), self.capa.capturar_fotograma(6))
        self.capa.configurar(reducir_movimiento=False)
        self.assertTrue(self.capa.animando)

    def test_pausa_modal_no_consume_tiempo_ni_reactiva_preferencia(self):
        self.capa.reproducir("rumor", 10)
        self.capa.show()
        self.app.processEvents()
        QTest.qWait(20)
        self.capa.pausar()
        instante = self.capa.tiempo_actual()
        self.assertFalse(self.capa.animando)
        QTest.qWait(40)
        self.assertEqual(self.capa.tiempo_actual(), instante)
        # Aplicar preferencias durante el modal no debe arrancar el reloj.
        self.capa.configurar(activo=True)
        self.assertFalse(self.capa.animando)
        self.capa.reanudar()
        QTest.qWait(20)
        self.assertGreater(self.capa.tiempo_actual(), instante)
        self.capa.pausar()
        self.capa.configurar(activo=False)
        self.capa.reanudar()
        self.assertFalse(self.capa.animando)
        self.assertFalse(self.capa._activo)
        self.capa.configurar(activo=True)
        self.assertTrue(self.capa.animando)
        self.capa.pausar()
        self.capa.reproducir("verificar")
        self.assertFalse(self.capa._pausada)
        self.assertTrue(self.capa.animando)
        self.capa.pausar()
        self.capa.detener()
        self.assertFalse(self.capa._pausada)

    def test_minimizar_ventana_padre_pausa_y_restaurar_reanuda(self):
        ventana = QWidget()
        try:
            self.capa.setParent(ventana)
            self.capa.reproducir("rumor", 10)
            self.capa.show()
            ventana.show()
            self.app.processEvents()
            self.assertTrue(self.capa.animando)
            ventana.showMinimized()
            self.app.processEvents()
            self.assertFalse(self.capa.animando)
            congelado = self.capa.tiempo_actual()
            QTest.qWait(30)
            self.assertEqual(self.capa.tiempo_actual(), congelado)
            ventana.showNormal()
            self.app.processEvents()
            self.assertTrue(self.capa.animando)
        finally:
            self.capa.setParent(None)
            ventana.close()

    def test_finaliza_una_vez_y_limpia_la_capa(self):
        terminados = QSignalSpy(self.capa.efecto_terminado)
        self.capa.reproducir("eleccion", .2)
        self.capa.show()
        QTest.qWait(290)
        self.assertFalse(self.capa.animando)
        self.assertFalse(self.capa.reproduciendo)
        self.assertEqual(list(terminados), [["eleccion"]])
        QTest.qWait(80)
        self.assertEqual(len(terminados), 1)
        imagen = self.capa.capturar_fotograma(1, (32, 18))
        self.assertTrue(all(imagen.pixelColor(x, y).alpha() == 0
                            for y in range(18) for x in range(32)))

    def test_alias_sustitucion_y_detener_no_emiten_final_falso(self):
        terminados = QSignalSpy(self.capa.efecto_terminado)
        self.assertTrue(self.capa.reproducir("compartir"))
        self.assertEqual(self.capa.tipo, "rumor")
        self.assertFalse(self.capa.reproducir("no-existe"))
        self.assertEqual(self.capa.tipo, "rumor")
        self.capa.reproducir("ignorar")
        self.assertEqual(self.capa.tipo, "silencio")
        self.capa.detener()
        self.assertFalse(self.capa.reproduciendo)
        self.assertEqual(len(terminados), 0)

    def test_rechaza_tiempos_invalidos_sin_corromper_efecto(self):
        self.capa.reproducir("investigar")
        for valor in (float("inf"), float("nan"), -1):
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError):
                    self.capa.establecer_tiempo(valor)
                with self.assertRaises(ValueError):
                    self.capa.reproducir("rumor", valor)
        self.assertEqual(self.capa.tipo, "investigar")
        with self.assertRaises(ValueError):
            self.capa.capturar_fotograma(1, (0, 20))


if __name__ == "__main__":
    unittest.main()
