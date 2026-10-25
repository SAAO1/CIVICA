"""Lectura, consulta y plazos de la novela con preferencias aisladas."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from interfaz import VentanaPrincipal
from juego.eventos import Evento
from juego.lectura import BibliotecaLectura
from juego.partida import Juego
from paneles import mostrar_configuracion


class PruebasBibliotecaLectura(unittest.TestCase):
    def test_guardado_recupera_lectura_y_une_actualizaciones_de_otras_ventanas(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "biblioteca.json"
            primera = BibliotecaLectura(ruta)
            segunda = BibliotecaLectura(ruta)
            primera.marcar(" ciudadano ", "Una conversación del barrio.")
            primera.desbloquear(50)
            segunda.marcar("PERIODISTA", "Una revisión diferente.")
            segunda.desbloquear("final")
            recuperada = BibliotecaLectura(ruta)
            self.assertTrue(recuperada.ya_leido("CIUDADANO", "Una conversación del barrio."))
            self.assertTrue(recuperada.ya_leido("periodista", "Una revisión diferente."))
            self.assertFalse(recuperada.ya_leido("CIUDADANO", "Una conversación modificada."))
            self.assertEqual(recuperada.escenas, {"50", "final"})
            self.assertEqual(len(recuperada.leidos), 2)
            self.assertEqual(list(Path(carpeta).glob("*.tmp")), [])

    def test_archivo_corrupto_o_con_datos_invalidos_permite_seguir_leyendo(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "biblioteca.json"
            clave = BibliotecaLectura.clave("NARRADOR", "Texto conservado.")
            for contenido, leidos, escenas in (
                ("{", set(), set()),
                ("[]", set(), set()),
                (json.dumps({"leidos": [clave, "invalida", 7, None],
                             "escenas": ["50", "final", "desconocida", None]}),
                 {clave}, {"50", "final"}),
                (json.dumps({"leidos": {}, "escenas": 12}), set(), set()),
            ):
                with self.subTest(contenido=contenido):
                    ruta.write_text(contenido, encoding="utf-8")
                    biblioteca = BibliotecaLectura(ruta)
                    self.assertEqual(biblioteca.leidos, leidos)
                    self.assertEqual(biblioteca.escenas, escenas)
                    biblioteca.marcar("CIUDADANO", "Todavía podemos continuar.")
                    self.assertTrue(BibliotecaLectura(ruta).ya_leido(
                        "CIUDADANO", "Todavía podemos continuar."))


class PruebasNovelaUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.preferencias = patch("configuracion.cargar", return_value={})
        self.gestor_audio = patch("interfaz.GestorAudio")
        self.biblioteca = patch("interfaz.BibliotecaLectura",
                                return_value=BibliotecaLectura(None))
        self.preferencias.start()
        self.audio = self.gestor_audio.start().return_value
        self.audio.volumenes = {"general": .65, "musica": .3, "efectos": .6,
                                "ambiente": .2, "voces": 1.0}
        self.biblioteca.start()
        self.ventana = VentanaPrincipal()
        self.ventana.reducir_movimiento = True
        self.ventana.sin_limite = True
        self.ventana.velocidad_texto = 34
        self.ventana.aplicar_accesibilidad()
        self.ventana.resize(1366, 768)
        self.ventana.establecer_juego(Juego(4, eventos=False))
        self.ventana.juego.iniciar_primera_publicacion()
        self.ventana.show()
        self.app.processEvents()

    def tearDown(self):
        self.ventana.close()
        self.ventana.deleteLater()
        self.app.processEvents()
        self.biblioteca.stop()
        self.gestor_audio.stop()
        self.preferencias.stop()

    def preparar_linea(self, texto):
        """Entra por el flujo real y termina la transición, sin esperar al reloj."""
        self.ventana.mostrar_escena(self.ventana.ESCENA_DIALOGO)
        escena = self.ventana.escena_dialogo
        escena.timer_inicio.stop()
        escena.dialogos = [("NARRADOR", texto)]
        escena.presentes_dialogo = set()
        escena.mostrar_dialogo_actual()
        escena.animacion.stop()
        escena.finalizar_animacion_dialogo()
        return escena

    def test_solo_registra_la_linea_tras_mostrarse_completa(self):
        texto = "Una línea nueva merece poder leerse antes de quedar en el historial."
        escena = self.preparar_linea(texto)
        escena.timer_texto.stop()
        escena.escribir_caracter()
        self.assertEqual(escena.texto_label.text(), texto[:1])
        self.assertFalse(self.ventana.biblioteca.ya_leido("NARRADOR", texto))
        self.assertEqual(self.ventana.historial_dialogos, [])
        QTest.keyClick(escena, Qt.Key.Key_Space)
        self.assertEqual(escena.texto_label.text(), texto)
        self.assertTrue(self.ventana.biblioteca.ya_leido("NARRADOR", texto))
        self.assertEqual(self.ventana.historial_dialogos, [("NARRADOR", texto)])
        self.assertEqual(escena.dialogo_actual, 0)

    def test_saltar_leido_se_detiene_en_una_linea_nueva(self):
        primera = "Esta línea ya apareció en una partida anterior."
        segunda = "Esta línea nueva debe permanecer para que puedas leerla por primera vez."
        self.ventana.biblioteca.marcar("NARRADOR", primera)
        escena = self.preparar_linea(primera)
        escena.dialogos.append(("NARRADOR", segunda))
        self.assertTrue(escena.boton_saltar.isEnabled())
        escena.boton_saltar.click()
        QTest.qWait(420)
        self.assertEqual(escena.dialogo_actual, 1)
        self.assertEqual(escena.texto_completo, segunda)
        self.assertFalse(escena.boton_saltar.isChecked())
        self.assertFalse(escena.boton_saltar.isEnabled())
        self.assertFalse(escena.timer_lectura.isActive())
        self.assertFalse(self.ventana.biblioteca.ya_leido("NARRADOR", segunda))
        QTest.qWait(170)
        self.assertEqual(escena.dialogo_actual, 1)
        self.assertFalse(self.ventana.juego.decision_aplicada)

    def test_auto_se_cancela_al_salir_y_al_llegar_a_la_decision(self):
        escena = self.preparar_linea("Una línea antes de salir.")
        escena.revelar_texto()
        escena.boton_auto.click()
        self.assertTrue(escena.timer_lectura.isActive())
        self.ventana.mostrar_escena(self.ventana.ESCENA_INICIO)
        self.assertFalse(escena.boton_auto.isChecked())
        self.assertFalse(escena.timer_lectura.isActive())
        escena = self.preparar_linea("La próxima pantalla necesita una elección.")
        escena.revelar_texto()
        escena.boton_auto.click()
        escena.paso_lectura()
        self.assertEqual(self.ventana.escenas.currentIndex(), self.ventana.ESCENA_ACCION)
        self.assertFalse(escena.boton_auto.isChecked())
        self.assertFalse(escena.timer_lectura.isActive())
        escena.paso_lectura()
        self.assertEqual(self.ventana.juego.historial, [])
        self.assertFalse(self.ventana.juego.decision_aplicada)

    def test_velocidad_instantanea_muestra_y_registra_sin_saltar_la_linea(self):
        self.ventana.velocidad_texto = 0
        texto = "El texto completo aparece, la decisión todavía te pertenece."
        escena = self.preparar_linea(texto)
        self.assertEqual(escena.texto_label.text(), texto)
        self.assertEqual(escena.indice_texto, len(texto))
        self.assertFalse(escena.escribiendo)
        self.assertFalse(escena.timer_texto.isActive())
        self.assertTrue(self.ventana.biblioteca.ya_leido("NARRADOR", texto))
        self.assertEqual(escena.dialogo_actual, 0)
        self.assertFalse(self.ventana.juego.decision_aplicada)

    def test_cuaderno_pausa_la_lectura_y_reanuda_la_misma_linea(self):
        texto = "Una línea parcialmente mostrada debe esperar mientras consultas el cuaderno."
        escena = self.preparar_linea(texto)
        escena.timer_texto.stop()
        escena.escribir_caracter()
        parcial = escena.texto_label.text()
        self.ventana.abrir_cuaderno(2)
        self.assertTrue(self.ventana.cuaderno.isVisible())
        self.assertFalse(escena.timer_texto.isActive())
        QTest.qWait(140)
        escena.escribir_caracter()  # También debe ignorar un callback atrasado.
        escena.registrar_lectura()
        escena.avanzar()
        self.assertEqual(escena.texto_label.text(), parcial)
        self.assertFalse(self.ventana.biblioteca.ya_leido("NARRADOR", texto))
        self.assertEqual(self.ventana.historial_dialogos, [])
        self.ventana.cuaderno.close()
        self.assertTrue(escena.timer_texto.isActive())
        self.assertEqual(escena.dialogo_actual, 0)
        QTest.keyClick(escena, Qt.Key.Key_Space)
        self.assertEqual(escena.texto_label.text(), texto)
        self.assertTrue(self.ventana.biblioteca.ya_leido("NARRADOR", texto))

    def test_configuracion_pausa_auto_y_conserva_la_linea_al_cerrar(self):
        texto = "La configuración debe esperar antes de pasar a otra línea."
        escena = self.preparar_linea(texto)
        escena.dialogos.append(("PERIODISTA", "Una línea posterior todavía no debe aparecer."))
        escena.revelar_texto()
        self.audio.hablando = False
        self.audio.silenciado = False
        self.audio.descripcion_voces.return_value = "Doblaje aislado de la prueba"
        escena.boton_auto.setChecked(True)
        escena.timer_lectura.start(20)

        def revisar_modal(dialogo):
            dialogo.show()
            self.assertTrue(escena.lectura_pausada)
            self.assertFalse(escena.timer_texto.isActive())
            self.assertFalse(escena.timer_lectura.isActive())
            QTest.qWait(90)
            escena.paso_lectura()  # Un callback previo al modal tampoco avanza.
            self.assertEqual(escena.dialogo_actual, 0)
            self.assertEqual(escena.texto_completo, texto)
            dialogo.reject()
            return 0

        with patch("paneles.DialogoIlustrado.exec", revisar_modal):
            mostrar_configuracion(self.ventana)
        self.assertFalse(escena.lectura_pausada)
        self.assertFalse(escena.boton_auto.isChecked())
        self.assertEqual(escena.dialogo_actual, 0)
        self.assertEqual(escena.texto_label.text(), texto)
        self.assertIs(self.ventana.escenas.currentWidget(), escena)

    def test_cuaderno_reanuda_voz_activa_aunque_el_subtitulo_este_completo(self):
        texto = "La voz sigue hablando después de que el subtítulo ya se mostró completo."
        escena = self.preparar_linea(texto)
        escena.revelar_texto()
        self.assertEqual(escena.estado_escena, "esperando")
        self.audio.hablando = True
        self.audio.narrar.reset_mock()
        self.audio.detener_voz.reset_mock()
        self.ventana.abrir_cuaderno(2)
        self.assertTrue(escena.lectura_pausada)
        self.audio.detener_voz.assert_called()
        self.audio.narrar.assert_not_called()
        self.ventana.cuaderno.close()
        self.audio.narrar.assert_called_once_with(texto, "NARRADOR")
        self.assertFalse(escena.lectura_pausada)
        self.assertFalse(escena.timer_texto.isActive())
        self.assertEqual(escena.estado_escena, "esperando")
        self.assertEqual(escena.texto_label.text(), texto)
        self.assertEqual(escena.dialogo_actual, 0)

    def test_auto_espera_a_que_termine_la_voz_antes_de_avanzar(self):
        escena = self.preparar_linea("El doblaje de esta línea todavía no ha terminado.")
        escena.dialogos.append(("PERIODISTA", "La línea siguiente empieza después de la voz."))
        escena.revelar_texto()
        escena.boton_auto.setChecked(True)
        self.audio.hablando = True
        escena.paso_lectura()
        self.assertEqual(escena.dialogo_actual, 0)
        self.assertTrue(escena.timer_lectura.isActive())
        self.audio.hablando = False
        escena.paso_lectura()
        self.assertEqual(escena.dialogo_actual, 1)
        self.assertIs(self.ventana.escenas.currentWidget(), escena)
        self.assertEqual(self.ventana.juego.historial, [])

    def test_investigar_cuenta_fuentes_sin_cambiar_partida_ni_puntos(self):
        self.ventana.mostrar_escena(self.ventana.ESCENA_ACCION)
        juego = self.ventana.juego
        antes = json.dumps(juego.datos(), ensure_ascii=False, sort_keys=True)
        puntos = juego.jugador.puntos
        self.ventana.escena_accion.boton_investigar.click()
        cuaderno = self.ventana.cuaderno
        for boton in cuaderno.pistas:
            boton.click()
        self.assertEqual(self.ventana.pistas_consultadas, {(50, 0), (50, 1), (50, 2)})
        self.assertIn("3 de 3", cuaderno.progreso_pistas.text())
        self.assertIn("3/3", self.ventana.escena_accion.pistas_estado.text())
        cuaderno.pistas[0].click()  # Plegar una fuente no elimina la consulta.
        self.assertIn("3 de 3", cuaderno.progreso_pistas.text())
        cuaderno.close()
        self.ventana.abrir_cuaderno()
        self.assertTrue(all(boton.isChecked() for boton in self.ventana.cuaderno.pistas))
        self.assertEqual(juego.jugador.puntos, puntos)
        self.assertEqual(json.dumps(juego.datos(), ensure_ascii=False, sort_keys=True), antes)

    def test_timeout_con_cuaderno_cierra_y_aplica_una_sola_decision(self):
        self.ventana.sin_limite = False
        juego = self.ventana.juego
        juego.evento_actual = Evento("viral", "El plazo de la publicación está por terminar.", True, 1)
        self.ventana.mostrar_escena(self.ventana.ESCENA_ACCION)
        escena = self.ventana.escena_accion
        self.assertTrue(escena.timer_decision.isActive())
        self.ventana.abrir_cuaderno()
        self.assertTrue(self.ventana.cuaderno.isVisible())
        escena.cuenta_regresiva()
        self.assertIsNone(self.ventana.cuaderno)
        self.assertEqual(self.ventana.escenas.currentIndex(), self.ventana.ESCENA_RESULTADO_1)
        self.assertEqual(len(juego.historial), 1)
        self.assertEqual(juego.ultima_accion, "ignorar")
        self.assertEqual(juego.jugador.puntos, 0)
        despues = json.dumps(juego.datos(), ensure_ascii=False, sort_keys=True)
        escena.cuenta_regresiva()  # Un tick atrasado no duplica la acción.
        escena.ejecutar_accion("compartir")
        self.assertEqual(json.dumps(juego.datos(), ensure_ascii=False, sort_keys=True), despues)
        self.assertFalse(escena.timer_decision.isActive())


if __name__ == "__main__":
    unittest.main()
