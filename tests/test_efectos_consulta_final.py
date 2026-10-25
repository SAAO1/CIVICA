"""Efectos discretos del desenlace y las fuentes, con estado de juego aislado."""
import json
import os
from types import SimpleNamespace
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget

from final_ui import EscenaFin
from juego.lectura import BibliotecaLectura
from juego.partida import Juego
from novela_ui import DialogoCuaderno


class PruebasEfectosConsultaFinal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.ventana = QWidget()
        self.ventana.resize(1100, 700)
        self.ventana.juego = Juego(4, eventos=False)
        self.ventana.juego.iniciar_primera_publicacion()
        self.ventana.reducir_movimiento = False
        self.ventana.animar_fondos = True
        self.ventana.pistas_consultadas = set()
        self.ventana.historial_dialogos = []
        self.ventana.biblioteca = BibliotecaLectura(None)
        self.ventana.escena_accion = object()
        self.ventana.escenas = SimpleNamespace(currentWidget=lambda: None)
        self.ventana.volver_portada = lambda: None
        self.cuaderno = None

    def tearDown(self):
        if self.cuaderno is not None:
            self.cuaderno.close()
        self.ventana.close()
        self.ventana.deleteLater()
        self.app.processEvents()

    def final(self):
        layout = QVBoxLayout(self.ventana)
        escena = EscenaFin()
        layout.addWidget(escena)
        self.ventana.show()
        escena.mostrar()
        self.app.processEvents()
        return escena

    def abrir_cuaderno(self):
        self.ventana.show()
        self.cuaderno = DialogoCuaderno(self.ventana)
        self.cuaderno.show()
        self.app.processEvents()
        return self.cuaderno

    def test_final_celebra_solo_sobre_arte_y_limpia_al_salir(self):
        self.ventana.juego.candidatos[0].apoyo = 80
        escena = self.final()
        self.assertEqual(escena.efectos_final.tipo, "eleccion")
        self.assertTrue(escena.efectos_final.animando)
        self.assertIs(escena.efectos_final.parent(), escena.imagen_ganador)
        self.assertTrue(escena.efectos_final.testAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents))
        for ancho, alto in ((1100, 570), (1366, 768)):
            self.ventana.resize(ancho, alto)
            self.app.processEvents()
            self.assertEqual(escena.efectos_final.geometry(), escena.imagen_ganador.rect())
        escena.hide()
        self.assertFalse(escena.efectos_final.reproduciendo)
        self.assertFalse(escena.efectos_final.animando)
        self.assertFalse(escena.ambiente_vivo.animando)

    def test_empate_muestra_archivo_y_respeta_preferencias(self):
        escena = self.final()
        self.assertTrue(escena.eleccion["empate"])
        self.assertEqual(escena.efectos_final.tipo, "archivo")
        self.ventana.reducir_movimiento = True
        escena.mostrar()
        self.assertFalse(escena.efectos_final.reproduciendo)
        self.assertFalse(escena.efectos_final.animando)
        self.assertFalse(escena.ambiente_vivo.animando)
        self.ventana.reducir_movimiento = False
        self.ventana.animar_fondos = False
        escena.mostrar()
        self.assertFalse(escena.efectos_final.reproduciendo)
        self.assertFalse(escena.ambiente_vivo.animando)

    def test_fuente_anima_franja_sin_cambiar_reglas_y_limpia_tab_y_cierre(self):
        antes = json.dumps(self.ventana.juego.datos(), ensure_ascii=False, sort_keys=True)
        cuaderno = self.abrir_cuaderno()
        cuaderno.pistas[0].click()
        self.app.processEvents()
        self.assertEqual(cuaderno.efectos_pista.tipo, "fuente")
        self.assertTrue(cuaderno.efectos_pista.animando)
        self.assertEqual(cuaderno.efectos_pista.height(), 16)
        self.assertEqual(self.ventana.pistas_consultadas, {(50, 0)})
        self.assertEqual(json.dumps(self.ventana.juego.datos(), ensure_ascii=False, sort_keys=True), antes)
        cuaderno.pestanas.setCurrentIndex(1)
        self.assertFalse(cuaderno.efectos_pista.reproduciendo)
        cuaderno.pestanas.setCurrentIndex(0)
        cuaderno.pistas[1].click()
        self.assertTrue(cuaderno.efectos_pista.reproduciendo)
        capa = cuaderno.efectos_pista
        cuaderno.close()
        self.assertFalse(capa.reproduciendo)
        self.assertFalse(capa.animando)
        self.cuaderno = None  # WA_DeleteOnClose la elimina al procesar eventos.

    def test_consulta_queda_quieta_si_se_desactiva_movimiento(self):
        cuaderno = self.abrir_cuaderno()
        cuaderno.pistas[0].click()
        self.assertTrue(cuaderno.efectos_pista.animando)
        # Es la misma llamada que recibe desde aplicar_accesibilidad global.
        cuaderno.efectos_pista.configurar(reducir_movimiento=True)
        self.assertFalse(cuaderno.efectos_pista.animando)
        self.assertFalse(cuaderno.efectos_pista.reproduciendo)
        self.ventana.reducir_movimiento = True
        cuaderno.pistas[1].click()
        self.assertFalse(cuaderno.efectos_pista.reproduciendo)
        self.ventana.reducir_movimiento = False
        self.ventana.animar_fondos = False
        cuaderno.pistas[2].click()
        self.assertFalse(cuaderno.efectos_pista.reproduciendo)


if __name__ == "__main__":
    unittest.main()
