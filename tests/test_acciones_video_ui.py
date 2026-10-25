"""Una elección ilustra su acción completa sin permitir saltos de transporte."""
import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QImage
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from interfaz import VentanaPrincipal
from juego.cinematica_acciones import CINEMATICAS_ACCIONES, clave_accion
from juego.lectura import BibliotecaLectura
from juego.partida import Juego


class PruebasAccionCompletaUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.parches = [patch("configuracion.cargar", return_value={}),
                        patch("interfaz.GestorAudio"),
                        patch("interfaz.BibliotecaLectura", lambda: BibliotecaLectura(None)),
                        patch("cinematica_narrativa.CapaCinematica._reproducir_si_corresponde")]
        for parche in self.parches:
            parche.start()
        self.ventana = VentanaPrincipal()
        self.ventana.audio.hablando = False
        self.ventana.sin_limite = True
        self.ventana.resize(1100, 700)
        self.ventana.show()
        self.temporal = tempfile.TemporaryDirectory()
        self.raiz = Path(self.temporal.name)
        self.escena = self.ventana.escena_resultado_1
        self.escena.cine_narrativo._raiz = self.raiz

    def tearDown(self):
        self.ventana.close()
        self.ventana.deleteLater()
        self.app.processEvents()
        self.temporal.cleanup()
        for parche in reversed(self.parches):
            parche.stop()

    def preparar(self, accion="compartir", rol="ciudadano"):
        juego = Juego(7, eventos=False)
        juego.seleccionar_rol(rol)
        juego.iniciar_primera_publicacion()
        self.assertTrue(juego.ejecutar_accion(accion))
        clave = clave_accion(juego)
        ficha = CINEMATICAS_ACCIONES[clave]
        for campo, color in (("inicio", "#395e66"), ("poster", "#af9473")):
            ruta = self.raiz / ficha[campo]
            ruta.parent.mkdir(parents=True, exist_ok=True)
            imagen = QImage(32, 18, QImage.Format.Format_RGB32)
            imagen.fill(QColor(color))
            self.assertTrue(imagen.save(str(ruta)))
        (self.raiz / ficha["video"]).write_bytes(b"transporte aislado por la prueba")
        self.ventana.establecer_juego(juego)
        self.ventana.mostrar_escena(self.ventana.ESCENA_RESULTADO_1)
        self.escena.timer_inicio.stop()
        return juego, clave

    def comenzar_voz(self):
        self.escena.preparar_dialogo()
        self.escena.animacion.stop()
        self.escena.finalizar_animacion_dialogo()
        self.escena.revelar_texto()

    def test_cada_oficio_prepara_su_accion_y_frame_cero_antes_del_panel(self):
        for rol, acciones in (("ciudadano", ("compartir", "conversar", "convocar", "ignorar")),
                              ("periodista", ("contrastar", "entrevistar", "desmentir", "reservar"))):
            for accion in acciones:
                with self.subTest(accion=accion):
                    juego, clave = self.preparar(accion, rol)
                    antes = copy.deepcopy(juego.datos())
                    cine = self.escena.cine_narrativo
                    self.assertEqual(cine.clave_actual, clave)
                    self.assertTrue(cine._pausada)
                    self.assertEqual(cine._poster.imagen.toImage().pixelColor(0, 0), QColor("#395e66"))
                    self.assertFalse(self.escena.fondo_label.isVisible())
                    self.assertTrue(all(not p.isVisible() for p in self.escena.personajes.values()))
                    self.comenzar_voz()
                    self.assertFalse(cine._pausada)
                    self.assertEqual(juego.datos(), antes)

    def test_clic_espacio_enter_y_auto_esperan_el_final_real_del_video(self):
        self.preparar()
        self.comenzar_voz()
        escena = self.escena
        escena.boton_auto.setChecked(True)
        for _ in range(25):
            QTest.keyClick(escena, Qt.Key.Key_Space)
            QTest.keyClick(escena, Qt.Key.Key_Return)
            QTest.mouseClick(escena, Qt.MouseButton.LeftButton)
            escena.paso_lectura()
        self.assertEqual(self.ventana.escenas.currentIndex(), self.ventana.ESCENA_RESULTADO_1)
        self.assertTrue(escena.timer_lectura.isActive())
        escena.cine_narrativo._cambiar_estado("finalizada")
        self.assertFalse(escena.corte_accion_pendiente())
        escena.avanzar()
        self.assertEqual(self.ventana.escenas.currentIndex(), self.ventana.ESCENA_RESULTADO_2)

    def test_error_y_movimiento_reducido_no_crean_bloqueo_sin_salida(self):
        for modo in ("error", "reducido"):
            with self.subTest(modo=modo):
                self.preparar()
                self.comenzar_voz()
                if modo == "error":
                    self.escena.cine_narrativo._cambiar_estado("error")
                else:
                    self.escena.cine_narrativo.configurar(reducir_movimiento=True)
                self.assertFalse(self.escena.corte_accion_pendiente())
                self.escena.avanzar()
                self.assertEqual(self.ventana.escenas.currentIndex(), self.ventana.ESCENA_RESULTADO_2)

    def test_caso_importado_no_muestra_un_video_de_otra_historia(self):
        juego, _ = self.preparar()
        juego.ultimo_registro["publicacion"]["id"] = 999
        self.escena.comenzar_escena()
        self.escena.timer_inicio.stop()
        self.assertFalse(self.escena.cine_narrativo.activa)
        self.assertFalse(self.escena.corte_accion_pendiente())


if __name__ == "__main__":
    unittest.main()
