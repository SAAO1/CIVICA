import os
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication
from audio.gestor_audio import GestorAudio


class PruebasVoces(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        # Las reglas de mezcla/cancelación no deben depender del equipo ni sonar
        # durante la suite. El comprobador separado ejercita el motor real.
        with patch.object(GestorAudio, "_inicializar_voces"):
            self.audio = GestorAudio()
        self.motor = Mock()
        self.motor.state.return_value = SimpleNamespace(name="Speaking")
        self.audio._sintetizador = self.motor
        self.audio.voces_disponibles = True
        self.voz = Mock()
        self.audio._voces = [self.voz]
        self.audio.perfiles_voces = {
            "CIUDADANO": {"voz": self.voz, "ritmo": -0.07, "tono": 0.04},
            "PERIODISTA": {"voz": self.voz, "ritmo": -0.10, "tono": 0.03},
            "NARRADOR": {"voz": self.voz, "ritmo": -0.16, "tono": -0.13},
        }
        self.addCleanup(self.audio.detener)

    def test_nuevo_dialogo_cancela_el_anterior_y_no_encola(self):
        self.assertTrue(self.audio.narrar("Primera frase.", "CIUDADANO"))
        self.assertTrue(self.audio.narrar("Segunda\n  frase.", "PERIODISTA"))
        self.assertEqual(self.motor.stop.call_count, 2)
        self.motor.say.assert_called_with("Segunda frase.")
        self.motor.setRate.assert_called_with(-0.10)
        self.motor.setPitch.assert_called_with(0.03)
        self.motor.enqueue.assert_not_called()
        self.assertEqual(self.audio.hablante_actual, "PERIODISTA")

    def test_silencio_cancela_y_no_reanuda_al_quitarlo(self):
        self.audio.narrar("Una frase que se interrumpe.")
        self.audio._estado_voz(SimpleNamespace(name="Speaking"))
        self.audio.silenciar()
        self.assertFalse(self.audio.hablando)
        self.assertEqual(self.audio.ultimo_texto_voz, "")
        self.motor.setVolume.assert_called_with(0)
        self.assertFalse(self.audio.narrar("No debe hablar."))
        self.audio.silenciar(False)
        self.assertEqual(self.motor.say.call_count, 1)

    def test_volumen_general_voces_y_desactivacion_respetan_silencio(self):
        self.audio.configurar("general", 0.5)
        self.audio.configurar("voces", 0.8)
        self.motor.setVolume.assert_called_with(0.4)
        self.audio.narrar("Hola")
        self.audio.configurar_voces(False)
        self.motor.setVolume.assert_called_with(0)
        self.assertFalse(self.audio.narrar("Inaudible"))
        self.audio.configurar_voces(True)
        self.audio.silenciar()
        self.audio.configurar("voces", 1)
        self.motor.setVolume.assert_called_with(0)
        self.audio.silenciar(False)
        self.audio.configurar("general", 0)
        self.assertFalse(self.audio.narrar("También inaudible"))

    def test_musica_baja_mientras_se_oye_la_voz_y_se_recupera(self):
        volumen = self.audio.volumen("musica")
        self.audio._estado_voz(SimpleNamespace(name="Speaking"))
        self.assertAlmostEqual(self.audio.volumen("musica"), volumen * 0.12)
        self.audio._estado_voz(SimpleNamespace(name="Ready"))
        self.assertAlmostEqual(self.audio.volumen("musica"), volumen)

    def test_detener_toda_escena_cancela_la_lectura(self):
        self.audio.narrar("La escena anterior ya terminó.")
        self.audio._estado_voz(SimpleNamespace(name="Speaking"))
        self.audio.detener()
        self.assertFalse(self.audio.hablando)
        self.assertEqual(self.audio.hablante_actual, "")
        self.assertEqual(self.motor.stop.call_count, 2)

    def test_ambiente_y_efectos_dejan_espacio_al_dialogo_y_recuperan_su_nivel(self):
        for categoria in ("general", "voces", "ambiente", "efectos", "musica"):
            self.audio.configurar(categoria, 1)
        niveles = {c: self.audio.volumen(c) for c in ("ambiente", "efectos", "musica")}
        self.audio._estado_voz(SimpleNamespace(name="Speaking"))
        self.assertEqual(self.audio.volumen("voces"), 1)
        for categoria in niveles:
            self.assertLessEqual(self.audio.volumen(categoria), self.audio.volumen("voces") * .3)
        self.audio._estado_voz(SimpleNamespace(name="Ready"))
        for categoria, nivel in niveles.items():
            self.assertEqual(self.audio.volumen(categoria), nivel)

    def test_falta_de_motor_y_texto_vacio_no_impiden_jugar(self):
        self.audio.voces_disponibles = False
        self.assertFalse(self.audio.narrar("Continúa como texto."))
        self.audio.voces_disponibles = True
        self.assertFalse(self.audio.narrar(" \n "))
        self.motor.say.assert_not_called()

    def test_nuevos_personajes_tienen_voz_estable(self):
        self.audio.narrar("Primera aparición", "INFLUENCER")
        tono = self.motor.setPitch.call_args.args[0]
        self.audio.narrar("Nueva aparición", "INFLUENCER")
        self.motor.setPitch.assert_called_with(tono)


if __name__ == "__main__":
    unittest.main()
