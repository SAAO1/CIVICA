"""Integración del relato audiovisual con lectura, decisiones y pausa modal."""
import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtGui import QColor, QImage
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from interfaz import VentanaPrincipal
from juego.cinematica import CINEMATICAS
from juego.lectura import BibliotecaLectura
from juego.partida import Juego
from juego.puesta_escena import efecto_visual_dialogo


class PruebasEfectosConsecuencias(unittest.TestCase):
    def juego(self):
        juego = Juego(4, eventos=False)
        juego.iniciar_primera_publicacion()
        return juego

    def test_retiro_y_reporte_rechazado_reciben_imagenes_distintas(self):
        juego = self.juego()
        juego.ejecutar_accion("reportar")
        self.assertTrue(juego.ultimo_registro["eliminada"])
        self.assertEqual(efecto_visual_dialogo(juego, "", "NARRADOR", 2), "reportar")
        juego.avanzar_publicacion()
        juego.ejecutar_accion("reportar")
        self.assertFalse(juego.ultimo_registro["eliminada"])
        self.assertEqual(efecto_visual_dialogo(juego, "", "NARRADOR", 2), "archivo")

    def test_red_de_particulas_solo_si_realmente_hubo_receptores(self):
        juego = self.juego()
        juego.ejecutar_accion("compartir")
        self.assertGreater(juego.ultimo_registro["alcance"], 0)
        antes = copy.deepcopy(juego.datos())
        self.assertEqual(efecto_visual_dialogo(juego, "", "NARRADOR", 2), "rumor")
        self.assertEqual(juego.datos(), antes)
        aislado = self.juego()
        for origen, destino in list(aislado.grafo.aristas()):
            aislado.grafo.eliminar_arista(origen, destino)
        aislado.ejecutar_accion("compartir")
        self.assertEqual(aislado.ultimo_registro["alcance"], 0)
        self.assertEqual(efecto_visual_dialogo(aislado, "", "NARRADOR", 2), "silencio")

    def test_opinion_no_recibe_visto_bueno_y_vigilia_no_recibe_confeti(self):
        juego = self.juego()
        juego.obtener_publicacion_actual().verdadera = None
        juego.ejecutar_accion("verificar")
        self.assertEqual(efecto_visual_dialogo(juego, "", "PERIODISTA", 2), "investigar")
        texto = CINEMATICAS["noche_electoral"]["texto"]
        self.assertEqual(efecto_visual_dialogo(juego, texto, "NARRADOR"), "tension")


class PruebasPuestaCinematicaUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.parches = [patch("configuracion.cargar", return_value={}),
                        patch("interfaz.GestorAudio"),
                        patch("interfaz.BibliotecaLectura", return_value=BibliotecaLectura(None))]
        for parche in self.parches:
            parche.start()
        self.ventana = VentanaPrincipal()
        self.audio = self.ventana.audio
        self.audio.hablando = False
        self.ventana.reducir_movimiento = True
        self.ventana.sin_limite = True
        self.ventana.aplicar_accesibilidad()
        self.ventana.resize(1100, 700)
        self.ventana.establecer_juego(Juego(4, eventos=False))
        self.ventana.juego.iniciar_primera_publicacion()
        self.ventana.show()
        self.app.processEvents()
        self.temporal = tempfile.TemporaryDirectory()
        raiz = Path(self.temporal.name)
        for entrada in CINEMATICAS.values():
            destino = raiz / entrada["poster"]
            destino.parent.mkdir(parents=True, exist_ok=True)
            imagen = QImage(32, 18, QImage.Format.Format_RGB32)
            imagen.fill(QColor("#6d907d"))
            self.assertTrue(imagen.save(str(destino)))
        for escena in (self.ventana.escena_dialogo, self.ventana.escena_narracion_1,
                       self.ventana.escena_narracion_2, self.ventana.escena_narracion_3):
            escena.cine_narrativo._raiz = raiz

    def tearDown(self):
        self.ventana.close()
        self.ventana.deleteLater()
        self.app.processEvents()
        self.temporal.cleanup()
        for parche in reversed(self.parches):
            parche.stop()

    def preparar(self, terminar=True):
        self.ventana.mostrar_escena(self.ventana.ESCENA_DIALOGO)
        escena = self.ventana.escena_dialogo
        escena.timer_inicio.stop()
        escena.mostrar_dialogo_actual()
        escena.animacion.stop()
        if terminar:
            escena.finalizar_animacion_dialogo()
            escena.timer_texto.stop()
        return escena

    def test_corte_espera_a_la_voz_y_actores_regresan_tras_el_narrador(self):
        escena = self.preparar(terminar=False)
        self.assertTrue(escena.cine_narrativo.activa)
        self.assertTrue(escena.cine_narrativo._pausada)
        self.assertIsNone(escena.cine_narrativo._reproductor)
        eventos = []
        reanudar = escena.cine_narrativo.reanudar
        def iniciar_video():
            eventos.append("video")
            return reanudar()
        with patch.object(escena.cine_narrativo, "reanudar", side_effect=iniciar_video):
            self.audio.narrar.side_effect = lambda *_: eventos.append("voz")
            escena.finalizar_animacion_dialogo()
        self.assertEqual(eventos, ["video", "voz"])
        self.assertEqual(escena.cine_narrativo.clave_actual, "cafe_alerta")
        self.assertEqual(escena.efectos_narrativos.tipo, "notificacion")
        self.assertTrue(all(not p.isVisible() for p in escena.personajes.values()))
        self.assertFalse(escena.contexto_escena.isVisible())
        self.assertFalse(escena.fondo_label.isVisible())
        self.assertEqual(escena.cine_narrativo.geometry(), escena.rect())
        hijos = escena.children()
        self.assertLess(hijos.index(escena.cine_narrativo), hijos.index(escena.efectos_narrativos))
        self.assertLess(hijos.index(escena.efectos_narrativos), hijos.index(escena.texto_label))
        escena.iniciar_dialogo("Mi hermana estudia en ese colegio.", "CIUDADANO", {"CIUDADANO", "PERIODISTA"})
        self.assertFalse(escena.cine_narrativo.activa)
        self.assertTrue(escena.contexto_escena.isVisible())
        self.assertTrue(escena.fondo_label.isVisible())
        self.assertTrue(all(p.isVisible() for p in escena.personajes.values()))
        self.assertEqual(escena.personajes_activos, {"CIUDADANO", "PERIODISTA"})

    def test_pausa_durante_entrada_no_empieza_corte_hasta_cerrar_modal(self):
        escena = self.preparar(terminar=False)
        self.audio.narrar.reset_mock()
        reanudar = self.ventana.pausar_lectura_modal()
        escena.finalizar_animacion_dialogo()
        self.assertTrue(escena.cine_narrativo.activa)
        self.assertTrue(escena.cine_narrativo._pausada)
        self.assertFalse(escena.efectos_narrativos.reproduciendo)
        self.audio.narrar.assert_not_called()
        reanudar()
        self.assertTrue(escena.cine_narrativo.activa)
        self.assertEqual(escena.efectos_narrativos.tipo, "notificacion")
        self.audio.narrar.assert_called_once_with(escena.texto_completo, "NARRADOR")

    def test_pausa_y_cambio_de_linea_no_reanudan_corte_viejo(self):
        escena = self.preparar()
        reanudar = self.ventana.pausar_lectura_modal()
        self.assertTrue(escena.cine_narrativo._pausada)
        self.assertTrue(escena.efectos_narrativos._pausada)
        escena.iniciar_dialogo("Una intervención nueva.", "PERIODISTA", {"PERIODISTA"})
        with patch.object(escena.cine_narrativo, "reanudar") as volver:
            reanudar()
        volver.assert_not_called()
        self.assertFalse(escena.cine_narrativo.activa)
        self.assertFalse(escena.efectos_narrativos.reproduciendo)

    def test_reanudar_y_finalizar_limpian_las_dos_capas(self):
        escena = self.preparar()
        self.ventana.reducir_movimiento = False
        self.ventana.aplicar_accesibilidad()
        reanudar = self.ventana.pausar_lectura_modal()
        tiempo = escena.efectos_narrativos.tiempo_actual()
        QTest.qWait(55)
        self.assertAlmostEqual(escena.efectos_narrativos.tiempo_actual(), tiempo, places=4)
        reanudar()
        self.assertFalse(escena.cine_narrativo._pausada)
        self.assertTrue(escena.efectos_narrativos.animando)
        self.ventana.mostrar_escena(self.ventana.ESCENA_ACCION)
        self.assertFalse(escena.cine_narrativo.activa)
        self.assertFalse(escena.efectos_narrativos.reproduciendo)
        self.assertEqual(self.ventana.escena_accion.efectos_narrativos.tipo, "decision")

    def test_resultado_dinamico_no_reproduce_video_y_consulta_no_cambia_juego(self):
        self.ventana.juego.ejecutar_accion("reportar")
        self.ventana.mostrar_escena(self.ventana.ESCENA_RESULTADO_2)
        escena = self.ventana.escenas.currentWidget()
        escena.timer_inicio.stop()
        escena.preparar_dialogo()
        escena.animacion.stop()
        antes = copy.deepcopy(self.ventana.juego.datos())
        escena.finalizar_animacion_dialogo()
        self.assertFalse(escena.cine_narrativo.activa)
        self.assertEqual(escena.efectos_narrativos.tipo, "reportar")
        self.assertEqual(self.ventana.juego.datos(), antes)

    def test_resize_durante_entrada_alinea_marco_nombre_texto_y_pista_al_terminar(self):
        escena = self.preparar(terminar=False)
        escena.iniciar_dialogo(
            "Convocar al barrio convirtió el aviso en una conversación compartida. "
            "Ahora debemos responder a quienes se sumaron.", "CIUDADANO")
        self.ventana.resize(1366, 900)
        self.app.processEvents()
        self.assertTrue(escena.animando)
        QTest.qWait(escena.DURACION_FRANJAS+100)
        self.assertFalse(escena.animando)
        self.assertEqual(escena.franja_inferior.geometry().bottom(), escena.height()-1)
        from arte import geometria_dialogo
        from PyQt6.QtCore import QRectF
        texto, nombre, pista = geometria_dialogo(QRectF(escena.franja_inferior.geometry()))
        self.assertEqual(escena.nombre_label.geometry(), nombre.toAlignedRect())
        self.assertEqual(escena.texto_label.geometry(), texto.toAlignedRect())
        self.assertEqual(escena.pista_continuar.geometry(), pista.toAlignedRect())


if __name__ == "__main__":
    unittest.main()
