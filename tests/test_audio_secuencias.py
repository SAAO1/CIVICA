"""Sincronización de contadores con la reproducción real y cancelación inmediata."""
import os
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication
from audio.catalogo_voces import segmentos_indicadores
from audio.catalogo_voces import ruta_clip
from audio.gestor_audio import GestorAudio


PLAYING = SimpleNamespace(name="PlayingState")
END = SimpleNamespace(name="EndOfMedia")


class PruebasSecuenciaContadores(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.audio = GestorAudio()
        self.audio._reproductor_voz = Mock()
        self.addCleanup(self.audio.detener)
        self.segmentos = [{"clave": "confianza", "texto": "Confianza +6."},
                          {"clave": "conflictos", "texto": "Conflictos -1."}]
        self.inicios, self.finales, self.secuencias = [], [], []
        self.audio.segmento_iniciado.connect(self.inicios.append)
        self.audio.segmento_finalizado.connect(self.finales.append)
        self.audio.secuencia_finalizada.connect(self.secuencias.append)

    def test_no_inicia_tarjeta_hasta_que_realmente_suena_el_clip(self):
        self.assertTrue(self.audio.narrar_secuencia(self.segmentos))
        self.assertEqual(self.inicios, [])
        self.audio._estado_clip_voz(SimpleNamespace(name="LoadingMedia"))
        self.assertEqual(self.inicios, [])
        self.audio._estado_reproduccion_voz(PLAYING)
        self.audio._estado_reproduccion_voz(PLAYING)
        self.assertEqual(self.inicios, ["confianza"])

    def test_emite_por_cada_segmento_sin_terminar_voz_entre_cifras(self):
        final_voz = []
        self.audio.voz_finalizada.connect(lambda: final_voz.append(True))
        self.audio.narrar_secuencia(self.segmentos)
        self.audio._estado_reproduccion_voz(PLAYING)
        self.audio._estado_clip_voz(END)
        self.assertTrue(self.audio.hablando)
        self.assertEqual(self.finales, ["confianza"])
        self.app.processEvents()
        self.audio._estado_reproduccion_voz(PLAYING)
        self.assertEqual(self.inicios, ["confianza", "conflictos"])
        self.audio._estado_clip_voz(END)
        self.assertEqual(self.finales, ["confianza", "conflictos"])
        self.assertEqual(self.secuencias, [True])
        self.assertEqual(final_voz, [True])

    def test_clip_faltante_rechaza_toda_la_secuencia_sin_reproduccion_parcial(self):
        self.segmentos.append({"clave": "futuro", "texto": "Una cifra sin grabación +12345."})
        self.assertFalse(self.audio.narrar_secuencia(self.segmentos))
        self.audio._reproductor_voz.play.assert_not_called()
        self.assertEqual(self.audio._cola_voces, [])

    def test_cancelar_invalida_el_siguiente_clip_programado(self):
        self.audio.narrar_secuencia(self.segmentos)
        self.audio._estado_reproduccion_voz(PLAYING)
        self.audio._estado_clip_voz(END)
        self.audio.detener_voz()
        self.app.processEvents()
        self.assertEqual(self.audio._reproductor_voz.play.call_count, 1)
        self.assertEqual(self.secuencias, [False])
        self.assertFalse(self.audio.hablando)

    def test_cancelar_durante_carga_informa_fallback_sin_iniciar_tarjetas(self):
        self.audio.narrar_secuencia(self.segmentos)
        self.audio.detener_voz()
        self.audio._estado_reproduccion_voz(PLAYING)
        self.audio._estado_clip_voz(END)
        self.assertEqual(self.inicios, [])
        self.assertEqual(self.finales, [])
        self.assertEqual(self.secuencias, [False])
        self.assertFalse(self.audio.hablando)

    def test_cancelar_y_arrancar_otra_lectura_no_revive_la_cola_anterior(self):
        self.audio.narrar_secuencia(self.segmentos)
        self.audio._estado_reproduccion_voz(PLAYING)
        self.audio._estado_clip_voz(END)
        self.audio.narrar("Confianza +5.")
        self.app.processEvents()
        self.assertEqual(self.audio._reproductor_voz.play.call_count, 2)
        self.assertEqual(self.audio.ultimo_texto_voz, "Confianza +5.")
        self.assertEqual(self.secuencias, [False])

    def test_silenciar_o_error_finaliza_secuencia_y_notifica_fallback(self):
        for metodo in (lambda: self.audio.silenciar(),
                       lambda: self.audio._error_clip_voz(None, "fallo de prueba")):
            self.audio.silenciar(False)
            self.audio.narrar_secuencia(self.segmentos)
            self.audio._estado_reproduccion_voz(PLAYING)
            metodo()
            self.assertFalse(self.audio.hablando)
            self.assertEqual(self.audio._cola_voces, [])
        self.assertEqual(self.secuencias, [False, False])

    def test_con_voces_desactivadas_devuelve_false_y_no_usa_windows(self):
        self.audio.configurar_voces(False)
        self.assertFalse(self.audio.narrar_secuencia(self.segmentos))
        self.assertIsNone(self.audio._sintetizador)

    def test_deltas_salen_de_los_valores_reales_y_no_de_cambios_solicitados(self):
        r = {"antes": {"confianza": 98, "desinformacion": 0},
             "despues": {"confianza": 100, "desinformacion": 0}, "puntos": 9,
             "cambios": {"confianza": 6, "desinformacion": -8}}
        self.assertEqual(segmentos_indicadores(r), [
            {"clave": "confianza", "texto": "Confianza +2."},
            {"clave": "puntos", "texto": "Puntuación de la acción: +9."}])

    def test_entrada_invalida_no_toca_un_clip_ni_inventa_la_clave(self):
        for segmentos in (None, [], [{"texto": "Confianza +6."}], [("confianza",)],
                          [("", "Confianza +6.")]):
            self.assertFalse(self.audio.narrar_secuencia(segmentos))
        self.audio._reproductor_voz.play.assert_not_called()

    def test_todos_los_deltas_legales_tienen_toma_completa_y_duracion(self):
        from herramientas.producir_voces import inventario_contadores
        catalogo = self.audio._manifest_voces["clips"]
        for clave, texto in inventario_contadores().items():
            with self.subTest(texto=texto["texto"]):
                clip = catalogo.get(clave)
                self.assertIsNotNone(clip)
                self.assertIsNotNone(ruta_clip(clip))
                self.assertGreater(clip["duracion_ms"], 100)
                self.assertTrue(any(v > .01 for v in clip["envolvente"]))
        self.assertTrue(self.audio.narrar_secuencia([
            ("info_verificada", "Información verificada +10."),
            ("desinformacion", "Desinformación +20."),
            ("participacion", "Participación -1."),
            ("puntos", "Puntuación de la acción: -15.")]))

    def test_oficios_reacciones_recuerdos_y_alcance_conservan_doblaje(self):
        from juego.acciones import acciones_para_rol
        from juego.historia import dialogos_publicacion, contenido_resultado
        from juego.partida import Juego
        for rol in ("ciudadano", "periodista"):
            opciones = [a["clave"] for a in acciones_para_rol(rol)]
            for i in range(16):
                juego = Juego(i, eventos=True)
                juego.seleccionar_rol(rol)
                juego.jugador.ciudadano_id = ("ana", "maria", "carlos", "ines")[i % 4]
                juego.iniciar_primera_publicacion()
                for turno in range(6):
                    for nombre, texto in dialogos_publicacion(juego):
                        self.assertTrue(self.audio._buscar_clips_voz(texto, nombre), texto)
                    juego.ejecutar_accion(opciones[(i + turno) % 4])
                    for tipo in (1, 2):
                        texto, nombre = contenido_resultado(juego, tipo)
                        self.assertTrue(self.audio._buscar_clips_voz(texto, nombre), texto)
                    self.assertTrue(self.audio.narrar_secuencia(segmentos_indicadores(juego.ultimo_registro)))
                    juego.avanzar_publicacion()


if __name__ == "__main__":
    unittest.main()
