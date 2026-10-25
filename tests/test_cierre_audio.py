"""El cierre descarga los tres transportes sin reproducir audio real."""
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QApplication
from audio.gestor_audio import GestorAudio


class SenalFalsa:
    def __init__(self):
        self.receptores = []

    def connect(self, receptor):
        self.receptores.append(receptor)

    def emit(self, valor):
        for receptor in self.receptores:
            receptor(SimpleNamespace(name=valor))


class ReproductorFalso:
    Loops = SimpleNamespace(Infinite=-1)

    def __init__(self, parent=None):
        self.playbackStateChanged = SenalFalsa()
        self.mediaStatusChanged = SenalFalsa()
        self.errorOccurred = SenalFalsa()
        self._fuente = QUrl()
        self.salida = None
        self.paradas = 0
        self.reproducciones = 0

    def setAudioOutput(self, salida):
        self.salida = salida

    def setLoops(self, valor):
        pass

    def setSource(self, fuente):
        self._fuente = QUrl(fuente)
        self.mediaStatusChanged.emit("NoMedia" if fuente.isEmpty() else "LoadingMedia")

    def source(self):
        return QUrl(self._fuente)

    def stop(self):
        self.paradas += 1
        self.playbackStateChanged.emit("StoppedState")

    def play(self):
        self.reproducciones += 1
        self.playbackStateChanged.emit("PlayingState")

    def position(self):
        return 0


class SalidaFalsa:
    def __init__(self, parent=None):
        self.valor = 0.0

    def setVolume(self, valor):
        self.valor = valor

    def volume(self):
        return self.valor


class PruebasCierreAudio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        # Toda la interfaz del reproductor es falsa. Ni siquiera se asigna
        # una fuente a un transporte nativo durante estas pruebas.
        with (patch.object(GestorAudio, "_inicializar_voces"),
              patch("PyQt6.QtMultimedia.QMediaPlayer", ReproductorFalso),
              patch("PyQt6.QtMultimedia.QAudioOutput", SalidaFalsa)):
            self.audio = GestorAudio()
        self.addCleanup(self.audio.detener)

    def test_cierre_descarga_tres_fuentes_y_es_idempotente(self):
        reproductores = [self.audio._reproductor_voz] + [p for p, _ in self.audio.pistas.values()]
        salidas = [p.salida for p in reproductores]
        for i, reproductor in enumerate(reproductores):
            reproductor.setSource(QUrl.fromLocalFile(str(Path(f"transporte_{i}.wav").resolve())))
        fundidos = [Mock(), Mock()]
        self.audio.fundidos.update(zip(("musica", "ambiente"), fundidos))
        self.audio.objetivos["musica"] = reproductores[1].source()
        self.audio._cola_voces = [{"pendiente": True}]
        self.audio._secuencia_activa = True
        finalizadas = []
        self.audio.secuencia_finalizada.connect(finalizadas.append)
        self.audio._cambiar_estado_hablando(True)
        generacion = self.audio._generacion_voz
        for _ in range(2):
            self.audio.detener()
            self.assertTrue(all(p.source().isEmpty() for p in reproductores))
            self.assertEqual([p.salida for p in reproductores], salidas)
            self.assertFalse(self.audio.hablando)
            self.assertFalse(self.audio._temporizador_labios.isActive())
            self.assertEqual(self.audio._cola_voces, [])
            self.assertEqual(self.audio.fundidos, {})
            self.assertEqual(self.audio.objetivos, {})
        self.assertEqual(finalizadas, [False])
        self.assertGreater(self.audio._generacion_voz, generacion)
        for fundido in fundidos:
            fundido.stop.assert_called_once()

    def test_cancelar_solo_la_linea_conserva_su_fuente(self):
        reproductor = self.audio._reproductor_voz
        fuente = QUrl.fromLocalFile(str(Path("voz_pendiente.mp3").resolve()))
        reproductor.setSource(fuente)
        self.audio.detener_voz()
        self.assertEqual(reproductor.source(), fuente)
        self.assertEqual(reproductor.paradas, 1)

    def test_despues_del_cierre_se_puede_narrar_y_cargar_musica_otra_vez(self):
        self.audio.detener()
        self.audio.voces_disponibles = True
        ruta = Path("nueva_voz.mp3").resolve()
        with (patch.object(self.audio, "_buscar_clips_voz", return_value=[{"envolvente": []}]),
              patch("audio.gestor_audio.ruta_clip", return_value=ruta)):
            self.assertTrue(self.audio.narrar("Nueva lectura.", "NARRADOR"))
        self.assertEqual(self.audio._reproductor_voz.source(), QUrl.fromLocalFile(str(ruta)))
        self.assertTrue(self.audio.hablando)
        self.assertTrue(self.audio.cambiar_pista("ciudad"))
        fundido = self.audio.fundidos["musica"]
        fundido.setCurrentTime(fundido.duration())
        reproductor, salida = self.audio.pistas["musica"]
        self.assertEqual(reproductor.source(), self.audio.objetivos["musica"])
        self.assertFalse(reproductor.source().isEmpty())
        self.assertIs(reproductor.salida, salida)
        self.assertEqual(reproductor.reproducciones, 1)
        self.audio.detener()
        self.assertTrue(self.audio.cambiar_pista("ciudad"))
        fundido = self.audio.fundidos["musica"]
        fundido.setCurrentTime(fundido.duration())
        self.assertEqual(reproductor.reproducciones, 2)


if __name__ == "__main__":
    unittest.main()
