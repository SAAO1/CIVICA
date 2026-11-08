"""El doblaje debe conservar el texto, el personaje y la cancelación local."""
import os
from pathlib import Path
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication
from audio.catalogo_voces import (PERFILES, cargar_manifest, clave_clip,
                                 ruta_clip, texto_grupo)
from audio.gestor_audio import GestorAudio
from juego.historia import (_DIALOGOS, _RECUERDOS, _REACCIONES,
                            contenido_resultado, dialogos_publicacion)
from juego.partida import Juego


class PruebasDoblajeNeuronal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.manifest = cargar_manifest()

    def setUp(self):
        self.audio = GestorAudio()
        self.addCleanup(self.audio.detener)

    def test_paquete_tiene_ocho_identidades_y_envolventes_audibles(self):
        self.assertEqual(len({p["voz"] for p in PERFILES.values()}), 8)
        self.assertEqual(self.audio.motor_voz, "neural-offline")
        self.assertIsNone(self.audio._sintetizador)
        self.assertGreaterEqual(len(self.manifest["clips"]), 119)
        for clave, entrada in self.manifest["clips"].items():
            with self.subTest(clip=clave):
                self.assertEqual(clave, clave_clip(entrada["hablante"], entrada["texto"]))
                self.assertIsNotNone(ruta_clip(entrada))
                self.assertGreater(entrada["duracion_ms"], 100)
                self.assertTrue(any(n > .01 for n in entrada["envolvente"]))
                self.assertLessEqual(abs(len(entrada["envolvente"])*50-entrada["duracion_ms"]), 50)

    def test_dialogos_recuerdos_y_reacciones_tienen_su_interprete(self):
        pares = [par for escena in _DIALOGOS.values() for par in escena]
        pares += [("PERIODISTA", texto) for ramas in _RECUERDOS.values() for texto in ramas.values()]
        pares += [("PERIODISTA" if accion == "verificar" else "CIUDADANO", texto)
                  for ramas in _REACCIONES.values() for accion, texto in ramas.items()]
        for nombre, texto in pares:
            self.assertTrue(self.audio._buscar_clips_voz(texto, nombre), (nombre, texto))

    def test_cambio_rapido_y_silencio_cancelan_el_archivo_anterior(self):
        reproductor = Mock()
        self.audio._reproductor_voz = reproductor
        primero = _DIALOGOS[50][1]
        segundo = _DIALOGOS[50][2]
        self.assertTrue(self.audio.narrar(primero[1], primero[0]))
        self.assertTrue(self.audio.narrar(segundo[1], segundo[0]))
        self.assertEqual(reproductor.stop.call_count, 2)
        self.assertEqual(reproductor.play.call_count, 2)
        self.assertEqual(self.audio.hablante_actual, segundo[0])
        self.audio.silenciar()
        self.assertEqual(reproductor.stop.call_count, 3)
        self.assertFalse(self.audio.narrar(primero[1], primero[0]))
        self.assertEqual(reproductor.play.call_count, 2)
        self.assertEqual(self.audio.ultimo_texto_voz, "")
        self.assertEqual(self.audio._salida_voz.volume(), 0)

    def test_dialogo_importado_sin_grabacion_no_vuelve_a_voz_de_windows(self):
        reproductor = Mock()
        self.audio._reproductor_voz = reproductor
        self.assertFalse(self.audio.narrar("Un texto importado que no existe en el doblaje.", "NARRADOR"))
        reproductor.play.assert_not_called()
        self.assertIsNone(self.audio._sintetizador)

    def test_nombre_personalizado_conserva_las_cifras_del_resultado(self):
        ejemplo = next(c["texto"] for c in self.manifest["clips"].values()
                       if c["texto"].startswith("Ciudad Nova refleja la decisión de Alex:"))
        personalizado = ejemplo.replace("de Alex:", "de Lucía:")
        clips = self.audio._buscar_clips_voz(personalizado, "NARRADOR")
        self.assertTrue(clips)
        self.assertEqual(clips[0]["texto"], texto_grupo(personalizado))

    def test_manifest_no_puede_abrir_un_archivo_fuera_del_paquete(self):
        self.assertIsNone(ruta_clip({"archivo": "../../../interfaz.py"}))
        self.assertIsNone(ruta_clip({"archivo": str(Path(__file__).resolve())}))

    def test_cifras_de_eventos_se_componen_sin_inventar_un_resultado(self):
        texto = ("Ciudad Nova refleja la decisión de Lucía: confianza +5, conflictos -1. "
                 "Puntuación de la acción: +8.")
        clips = self.audio._buscar_clips_voz(texto, "NARRADOR")
        self.assertEqual([c["texto"] for c in clips], [
            "Ciudad Nova refleja la decisión del grupo.", "Confianza +5.",
            "Conflictos -1.", "Puntuación de la acción: +8."])

    def test_partidas_con_eventos_y_emisores_diferentes_conservan_doblaje(self):
        vecinos = ("ana", "luis", "pedro", "maria", "carlos", "sofia", "elena", "diego", "ines")
        acciones = ("compartir", "verificar", "reportar", "ignorar")
        for semilla in range(36):
            juego = Juego(semilla, eventos=True)
            juego.seleccionar_rol("periodista" if semilla % 2 else "ciudadano")
            juego.jugador.nombre = "Valeria"
            juego.jugador.ciudadano_id = vecinos[semilla % len(vecinos)]
            juego.iniciar_primera_publicacion()
            for turno in range(6):
                for nombre, texto in dialogos_publicacion(juego):
                    self.assertTrue(self.audio._buscar_clips_voz(texto, nombre), texto)
                juego.ejecutar_accion(acciones[(semilla + turno) % len(acciones)])
                for tipo in (1, 2, 3):
                    texto, nombre = contenido_resultado(juego, tipo)
                    self.assertTrue(self.audio._buscar_clips_voz(texto, nombre), texto)
                juego.avanzar_publicacion()

    def test_union_de_frases_no_termina_el_turno_entre_clips(self):
        self.audio._cola_voces = [{"archivo": "pendiente.mp3"}]
        self.audio._cambiar_estado_hablando(True)
        finalizadas = []
        self.audio.voz_finalizada.connect(lambda: finalizadas.append(True))
        self.audio._estado_reproduccion_voz(SimpleNamespace(name="StoppedState"))
        self.assertTrue(self.audio.hablando)
        self.assertEqual(finalizadas, [])
        self.audio.detener_voz()
        self.assertFalse(self.audio.hablando)
        self.assertEqual(finalizadas, [True])


if __name__ == "__main__":
    unittest.main()
