"""Fundidos que no bloquean controles y sonidos ligados a cambios efectivos."""
import copy
import os
import time
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QSignalSpy, QTest
from PyQt6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget

from interfaz.novela.feedback import efectos_de_cambio, reproducir_cambios
from interfaz.novela.transiciones import TransicionNarrativa


class TransicionesNarrativas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.fondo = QWidget()
        self.fondo.resize(520, 300)
        self.fondo.setStyleSheet("background:#153548;")
        self.fondo.reducir_movimiento = False
        self.boton = QPushButton("Continuar", self.fondo)
        QVBoxLayout(self.fondo).addWidget(self.boton)
        self.fondo.show()
        self.capa = TransicionNarrativa(self.fondo)
        self.app.processEvents()

    def tearDown(self):
        self.fondo.close()
        self.fondo.deleteLater()
        self.app.processEvents()

    def test_fundido_termina_en_medio_segundo_y_no_intercepta_click(self):
        self.assertTrue(self.capa.capturar(self.fondo))
        self.fondo.setStyleSheet("background:#315c52;")
        fin = QSignalSpy(self.capa.terminada)
        clicks = QSignalSpy(self.boton.clicked)
        inicio = time.monotonic()
        self.assertTrue(self.capa.revelar())
        self.assertTrue(self.capa.animando)
        self.assertTrue(self.capa.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents))
        QTest.mouseClick(self.boton, Qt.MouseButton.LeftButton)
        self.assertEqual(len(clicks), 1)
        QTest.qWait(620)
        self.assertLess(time.monotonic()-inicio, .9)
        self.assertFalse(self.capa.isVisible())
        self.assertEqual(len(fin), 1)

    def test_otro_cuadro_interrumpe_sin_dejar_capa_vieja_y_reducido_es_inmediato(self):
        self.capa.capturar(self.fondo)
        self.capa.revelar()
        QTest.qWait(100)
        self.assertTrue(self.capa.capturar(self.fondo))
        self.fondo.setStyleSheet("background:#624b35;")
        self.assertTrue(self.capa.revelar())
        QTest.qWait(620)
        self.assertFalse(self.capa.animando)
        self.assertFalse(self.capa.isVisible())
        self.capa.configurar(reducir_movimiento=True)
        self.capa.capturar(self.fondo)
        self.assertFalse(self.capa.revelar())
        self.assertFalse(self.capa.isVisible())

    def test_captura_solo_se_revela_una_vez_aunque_se_prepare_el_mismo_plano(self):
        self.assertTrue(self.capa.capturar(self.fondo))
        self.assertTrue(self.capa.revelar())
        QTest.qWait(100)
        avance=self.capa._avance
        self.assertFalse(self.capa.revelar())
        self.assertGreaterEqual(self.capa._avance,avance)
        self.assertTrue(self.capa.animando)
        QTest.qWait(550)
        self.assertFalse(self.capa.animando)
        self.assertFalse(self.capa.revelar())
        self.assertFalse(self.capa.isVisible())

    def test_resize_sigue_al_contenedor_y_ocultar_cancela(self):
        self.capa.capturar(self.fondo)
        self.capa.revelar()
        self.fondo.resize(610, 360)
        self.app.processEvents()
        self.assertEqual(self.capa.geometry(), self.fondo.rect())
        self.fondo.hide()
        self.assertFalse(self.capa.animando)
        self.assertFalse(self.capa.isVisible())


class FeedbackConfirmado(unittest.TestCase):
    def vista(self):
        return {"mi_id":"c", "fase":"investigacion", "caso":{"id":50},
                "hallazgos":[], "propuestas":[], "decididos":[],
                "red":{"aristas":[["ana","pedro"]]}, "revision":4}

    def test_revision_reloj_pausa_y_cambio_de_acto_no_emiten_efectos(self):
        antes = self.vista()
        for cambios in ({"revision":5}, {"plazo_segundos":4}, {"fase":"pausa"},
                        {"caso":{"id":90}}):
            actual = copy.deepcopy(antes)
            actual.update(cambios)
            self.assertEqual(efectos_de_cambio(antes, actual), ())
        self.assertEqual(efectos_de_cambio({}, antes), ())

    def test_hallazgo_entrevista_borrador_compartido_y_conexion_suenan_una_vez(self):
        antes = self.vista()
        despues = copy.deepcopy(antes)
        despues["hallazgos"] = [{"id":"50:documento","tipo":"documento",
                                "propietario":"c","compartido":False}]
        self.assertEqual(efectos_de_cambio(antes, despues), (("pulido_hallazgo","hallazgo"),))
        self.assertEqual(efectos_de_cambio(despues, despues), ())
        compartido = copy.deepcopy(despues)
        compartido["hallazgos"][0]["compartido"] = True
        self.assertEqual(efectos_de_cambio(despues, compartido), (("papeles",),))
        entrevista = copy.deepcopy(antes)
        entrevista["hallazgos"] = [{"id":"50:testimonio","tipo":"testimonio",
                                   "propietario":"c","compartido":False}]
        entrevista["red"]["aristas"].append(["carlos","ana"])
        self.assertEqual(efectos_de_cambio(antes, entrevista),
                         (("taza",),("pulido_red","nodo")))
        borrador = copy.deepcopy(antes)
        borrador["propuestas"] = [{"jugador_id":"c","titular":"Un borrador"}]
        self.assertEqual(efectos_de_cambio(antes,borrador), (("lapiz",),))
        borrador["decididos"] = ["c"]
        self.assertEqual(efectos_de_cambio(antes,borrador), ())

    def test_usa_motor_audio_existente_con_fallback_sin_sintesis(self):
        class Audio:
            def __init__(self):
                self.llamadas = []
            def reproducir_efecto(self, nombre):
                self.llamadas.append(nombre)
                return nombre == "hallazgo"
        audio = Audio()
        antes = self.vista()
        actual = copy.deepcopy(antes)
        actual["hallazgos"] = [{"id":"50:medio","propietario":"c","tipo":"medio"}]
        reproducir_cambios(audio, antes, actual)
        self.assertEqual(audio.llamadas, ["pulido_hallazgo","hallazgo"])


if __name__ == "__main__":
    unittest.main()
