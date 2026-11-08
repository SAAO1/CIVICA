"""Interacciones reales y privacidad del expediente ilustrado de la novela."""
from copy import deepcopy
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_LOGGING_RULES", "qt.multimedia.*=false")

from PyQt6 import sip
from PyQt6.QtCore import QCoreApplication, QEvent, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QPushButton, QWidget

from audio.catalogo_voces import clave_clip, ruta_clip
from audio.gestor_audio import GestorAudio
from juego.campana_extendida import DIALOGOS_NUEVOS
from juego.investigacion import SesionInvestigacion
from interfaz.novela.componentes import BotonNovela, decorar_novela
from interfaz.novela.interacciones import OverlayInvestigacion


class PruebasOverlayNovela(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.padre = QWidget()
        self.padre.resize(1100, 700)
        self.padre.audio = GestorAudio(self.padre)
        self.padre.audio.silenciar()
        self.padre.show()
        self.overlays = []

    def tearDown(self):
        for overlay in self.overlays:
            if not sip.isdeleted(overlay):
                overlay.cerrar()
        self.padre.audio.detener()
        self.padre.close()
        self.padre.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    @staticmethod
    def sesion(cooperativa=False):
        sesion = SesionInvestigacion(semilla=4, cooperativa=cooperativa)
        sesion.registrar_jugador("Prueba", "ciudadano", id="c")
        if cooperativa:
            sesion.registrar_jugador("Otra voz", "periodista", id="p")
        sesion.comenzar()
        return sesion

    def overlay(self, vista, callback=None):
        overlay = OverlayInvestigacion(vista, callback, self.padre)
        self.overlays.append(overlay)
        overlay.abrir("material")
        self.app.processEvents()
        return overlay

    def test_inspeccionar_mueve_el_original_sin_gastar_y_confirmar_cuesta_una_accion(self):
        sesion = self.sesion()
        enviados = []
        def recibir(comando):
            enviados.append(comando)
            sesion.examinar("c", comando["medio"], comando["valor"])
            overlay.actualiza(sesion.vista("c"))
        overlay = self.overlay(sesion.vista("c"), recibir)
        antes = deepcopy(sesion.datos())
        overlay.slider.setValue(80)
        self.assertEqual(sesion.datos(), antes)
        self.assertEqual(enviados, [])
        self.assertFalse(overlay.comparador.original.isNull())
        self.assertFalse(overlay.comparador.recuperado)
        overlay.examinar.click()
        self.assertEqual(len(enviados), 1)
        self.assertEqual(sesion.vista("c")["acciones_restantes"], 1)
        self.assertTrue(overlay.comparador.recuperado)
        self.assertTrue(sesion.vista("c")["caso"]["medio"]["revelado"])
        overlay.examinar.click()
        self.assertEqual(len(enviados), 1)
        self.assertEqual(sesion.vista("c")["acciones_restantes"], 1)

    def test_original_bloqueado_y_hallazgo_ajeno_exigen_permiso_o_compartir(self):
        sesion = self.sesion(cooperativa=True)
        sesion.investigar("p", "archivo")
        hallazgo_ajeno = sesion.vista("p")["hallazgos"][0]
        vista = sesion.vista("c")
        vista["caso"]["medio"]["inspeccionable"] = False
        overlay = self.overlay(vista)
        overlay.slider.setValue(95)
        self.assertTrue(overlay.comparador.original.isNull())
        self.assertIsNone(overlay._prueba)
        self.assertNotIn(hallazgo_ajeno["id"], [h["id"] for h in overlay._actuales()])
        self.assertFalse(overlay.ver_hallazgo(hallazgo_ajeno))
        self.assertNotIn(hallazgo_ajeno["texto"], overlay.pista_texto.text())
        sesion.compartir_hallazgo("p", hallazgo_ajeno["id"])
        overlay.actualiza(sesion.vista("c"))
        self.assertEqual(overlay._prueba["id"], hallazgo_ajeno["id"])
        self.assertIn(hallazgo_ajeno["id"], [h["id"] for h in overlay._actuales()])
        self.assertTrue(overlay.ver_hallazgo(hallazgo_ajeno))
        self.assertEqual(overlay.pista_texto.text(), hallazgo_ajeno["texto"])

    def test_revisiones_del_companero_conservan_respuesta_foco_y_punto_de_prueba(self):
        sesion = self.sesion(cooperativa=True)
        overlay = self.overlay(sesion.vista("c"))
        overlay.decision("compartir")
        tarjeta = overlay.botones_accion["compartir"]
        tarjeta.setFocus()
        overlay.slider.setValue(42)
        self.app.processEvents()
        sesion.investigar("p", "archivo")
        overlay.actualiza(sesion.vista("c"))
        self.assertEqual(overlay._accion, "compartir")
        self.assertEqual(overlay.slider.value(), 42)
        self.assertIs(overlay.botones_accion["compartir"], tarjeta)
        self.assertTrue(tarjeta.isChecked())
        self.assertTrue(tarjeta.hasFocus())
        self.assertEqual(overlay.paginas.currentIndex(), overlay.secciones["decision"])

    def test_audio_110_habilita_solo_una_grabacion_original_existente(self):
        sesion = self.sesion()
        for _ in range(2):
            sesion.decidir("c", "ignorar")
            sesion.continuar("c")
        vista = sesion.vista("c")
        self.assertEqual(vista["caso"]["id"], 110)
        self.padre.audio.silenciar(False)
        overlay = self.overlay(vista)
        self.assertFalse(overlay.escuchar.isEnabled())
        self.assertEqual(overlay.escuchar.text(), "Solo transcripción")
        catalogo = self.padre.audio._manifest_voces["clips"]
        original = next(((nombre, texto) for nombre, texto in DIALOGOS_NUEVOS[110]
                         if ruta_clip(catalogo.get(clave_clip(nombre, texto))) is not None), None)
        self.assertIsNotNone(original, "El paquete debe conservar el doblaje original del caso 110")
        nombre, texto = original
        medio = vista["caso"]["medio"]
        medio.update(voz_texto=texto, voz_hablante=nombre, inspeccionable=True)
        overlay.actualiza(vista)
        self.assertTrue(overlay.escuchar.isEnabled())
        with patch.object(self.padre.audio, "narrar", return_value=True) as narrar:
            overlay.escuchar.click()
            narrar.assert_called_once_with(texto, nombre)
        self.padre.audio.configurar("voces", 0)
        overlay.actualiza(vista)
        self.assertFalse(overlay.escuchar.isEnabled())
        self.padre.audio.configurar("voces", 1)
        medio["voz_texto"] = "Esta frase nueva no pertenece a una grabación original."
        overlay.actualiza(vista)
        self.assertFalse(overlay.escuchar.isEnabled())
        medio.update(voz_texto=texto, inspeccionable=False)
        overlay.actualiza(vista)
        self.assertFalse(overlay.escuchar.isEnabled())
        self.assertIsNone(self.padre.audio._sintetizador)

    def test_botones_conservan_teclado_y_cierre_libera_la_escena(self):
        boton = BotonNovela("Una decisión", self.padre)
        boton.setGeometry(30, 30, 220, 60)
        boton.show()
        pulsaciones = []
        boton.clicked.connect(lambda: pulsaciones.append(True))
        QTest.keyClick(boton, Qt.Key.Key_Space)
        self.assertEqual(pulsaciones, [True])
        nativo = QPushButton("Control original", self.padre)
        nativo.setGeometry(30, 110, 220, 60)
        nativo.show()
        decorar_novela(self.padre)
        piel = nativo._piel_novela
        decorar_novela(self.padre)
        self.assertIs(nativo._piel_novela, piel)
        overlay = self.overlay(self.sesion().vista("c"))
        cierres = []
        overlay.cerrado.connect(lambda: cierres.append(True))
        QTest.keyClick(overlay, Qt.Key.Key_Escape)
        self.assertEqual(cierres, [True])
        self.assertFalse(overlay.isVisible())
