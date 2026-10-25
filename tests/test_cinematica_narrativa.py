"""Correspondencia con el guion y liberación del vídeo entre escenas."""
import os
from pathlib import Path
import tempfile
import unicodedata
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import QCoreApplication, QEvent, QObject, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QColor, QImage
from PyQt6.QtMultimedia import QMediaPlayer, QVideoFrame
from PyQt6.QtWidgets import QApplication, QWidget

from cinematica_narrativa import CapaCinematica, _VideoCompuesto
from juego.cinematica import CINEMATICAS, clave_cinematica
from juego.historia import _DIALOGOS
from recursos import RAIZ


class ReproductorControlado(QObject):
    """El transporte simulado permite probar pausa sin un códec del sistema."""
    Loops = QMediaPlayer.Loops
    MediaStatus = QMediaPlayer.MediaStatus
    mediaStatusChanged = pyqtSignal(object)
    errorOccurred = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.fuente = QUrl()
        self.posicion = 0
        self.reproduciendo = False
        self.reanudaciones = 0

    def setVideoSink(self, sink):
        self.salida = sink

    def setLoops(self, loops):
        self.bucle = loops

    def source(self):
        return self.fuente

    def setSource(self, source):
        self.fuente = source
        if not source.isEmpty():
            self.posicion = 0
            self.mediaStatusChanged.emit(self.MediaStatus.LoadedMedia)

    def play(self):
        self.reproduciendo = True
        self.reanudaciones += 1

    def stop(self):
        self.reproduciendo = False

    def position(self):
        return self.posicion

    def setPosition(self, posicion):
        self.posicion = posicion


class PruebasCatalogoCinematico(unittest.TestCase):
    def test_cada_entrada_del_guion_tiene_su_corte_sin_modificar_el_juego(self):
        claves = {50: "cafe_alerta", 30: "libreta_cultura", 70: "mapa_parque",
                  20: "libro_biblioteca", 60: "acusacion_lluvia", 80: "noche_electoral"}
        for identificador, clave in claves.items():
            nombre, texto = _DIALOGOS[identificador][0]
            self.assertEqual(clave_cinematica(texto, nombre, object()), clave)
            self.assertEqual(CINEMATICAS[clave]["publicacion"], identificador)

    def test_intro_coincide_con_frases_reales_y_todos_los_archivos_son_locales(self):
        interfaz = (RAIZ / "interfaz.py").read_text(encoding="utf-8")
        for clave, entrada in CINEMATICAS.items():
            with self.subTest(clave=clave):
                if entrada["publicacion"] is None:
                    self.assertIn(entrada["texto"], interfaz)
                self.assertEqual(clave_cinematica(entrada["texto"], entrada["nombre"].title()), clave)
                for tipo, sufijo in (("video", ".mp4"), ("poster", ".jpg")):
                    self.assertEqual(entrada[tipo], f"assets/expansion/cinematica/{clave}{sufijo}")
                self.assertEqual(entrada["inicio"], f"assets/expansion/cinematica/{clave}_inicio.png")

    def test_no_muestra_corte_ante_dialogos_o_consecuencias_variables(self):
        texto = CINEMATICAS["cafe_alerta"]["texto"]
        self.assertIsNone(clave_cinematica(texto, "CIUDADANO"))
        self.assertIsNone(clave_cinematica(texto + " Llegó a tres personas.", "NARRADOR"))
        self.assertIsNone(clave_cinematica("La publicación llegó a 5 ciudadanos.", "NARRADOR"))
        self.assertIsNone(clave_cinematica(None, None))
        self.assertEqual(clave_cinematica(unicodedata.normalize("NFD", texto), "  narrador  "),
                         "cafe_alerta")

    def test_intervenciones_de_cada_personaje_respetan_rol_y_frase_completa(self):
        casos = {50: "colegio", 30: "cultura", 70: "parque", 20: "biblioteca",
                 60: "acusacion", 80: "voto"}
        for identificador, caso in casos.items():
            for indice, sufijo in ((1, "c"), (2, "p")):
                nombre, texto = _DIALOGOS[identificador][indice]
                clave = f"person_{caso}_{sufijo}"
                self.assertEqual(clave_cinematica(texto, nombre), clave)
                self.assertEqual(CINEMATICAS[clave]["publicacion"], identificador)
                self.assertFalse(CINEMATICAS[clave]["bucle"])
                self.assertIsNone(clave_cinematica(texto, "NARRADOR"))
                self.assertIsNone(clave_cinematica(texto, "PERIODISTA" if nombre == "CIUDADANO" else "CIUDADANO"))
                self.assertIsNone(clave_cinematica(texto[:-1], nombre))
                self.assertIsNone(clave_cinematica(texto+" Hoy.", nombre))
            nombre, texto = _DIALOGOS[identificador][3]
            self.assertIsNone(clave_cinematica(texto, nombre))


class PruebasCapaCinematica(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.raiz = Path(self.temporal.name)
        self.capa = CapaCinematica(raiz=self.raiz)
        self.capa.resize(640, 360)
        self.parche = patch("cinematica_narrativa.QMediaPlayer", ReproductorControlado)
        self.parche.start()

    def tearDown(self):
        self.capa.close()
        self.capa.deleteLater()
        self.app.processEvents()
        self.parche.stop()
        self.temporal.cleanup()

    def escribir_recursos(self, video=True, poster=True, clave="cafe_alerta"):
        entrada = CINEMATICAS[clave]
        carpeta = self.raiz / Path(entrada["video"]).parent
        carpeta.mkdir(parents=True, exist_ok=True)
        if video:
            (self.raiz / entrada["video"]).write_bytes(b"transporte simulado")
        if poster:
            imagen = QImage(32, 18, QImage.Format.Format_RGB32)
            imagen.fill(QColor("#387980"))
            self.assertTrue(imagen.save(str(self.raiz / entrada["poster"])))
            imagen.fill(QColor("#234767"))
            self.assertTrue(imagen.save(str(self.raiz / entrada["inicio"])))

    def primer_frame(self):
        imagen = QImage(32, 18, QImage.Format.Format_RGB32)
        imagen.fill(QColor("#9e715c"))
        self.capa._nuevo_frame(QVideoFrame(imagen))

    def test_recursos_ausentes_no_tapan_el_escenario(self):
        self.assertFalse(self.capa.iniciar("cafe_alerta"))
        self.assertFalse(self.capa.activa)
        self.assertFalse(self.capa.isVisible())
        self.assertIsNone(self.capa._reproductor)

    def test_fotograma_sink_se_compone_en_la_captura_del_widget(self):
        video = _VideoCompuesto(self.capa)
        video.resize(320, 180)
        imagen = QImage(64, 36, QImage.Format.Format_RGB32)
        color = QColor("#af6438")
        imagen.fill(color)
        video.videoSink().setVideoFrame(QVideoFrame(imagen))
        captura = video.grab().toImage()
        self.assertEqual(captura.pixelColor(160, 90), color)
        self.assertEqual(captura.pixelColor(0, 0), color)
        video.videoSink().setVideoFrame(QVideoFrame())
        self.assertEqual(video.grab().toImage().pixelColor(160, 90), color)

    def test_personaje_termina_con_su_ultimo_plano_y_reutiliza_player_sin_bucle(self):
        self.escribir_recursos()
        self.escribir_recursos(clave="person_colegio_c")
        self.capa.iniciar("cafe_alerta")
        reproductor = self.capa._reproductor
        self.assertEqual(reproductor.bucle, QMediaPlayer.Loops.Infinite)
        self.capa.iniciar("person_colegio_c")
        self.assertIs(self.capa._reproductor, reproductor)
        self.assertEqual(reproductor.bucle, QMediaPlayer.Loops.Once)
        imagen = QImage(32, 18, QImage.Format.Format_RGB32)
        imagen.fill(QColor("#9e715c"))
        reproductor.salida.setVideoFrame(QVideoFrame(imagen))
        reproductor.mediaStatusChanged.emit(QMediaPlayer.MediaStatus.EndOfMedia)
        reproductor.salida.setVideoFrame(QVideoFrame())
        self.assertEqual(self.capa.estado, "finalizada")
        self.assertFalse(self.capa._video._imagen.isNull())
        self.assertTrue(self.capa.activa)
        self.capa.detener()
        self.assertTrue(self.capa._video._imagen.isNull())
        self.capa.iniciar("cafe_alerta")
        self.assertEqual(reproductor.bucle, QMediaPlayer.Loops.Infinite)

    def test_poster_sin_video_funciona_sin_crear_decodificador(self):
        self.escribir_recursos(video=False)
        self.assertTrue(self.capa.iniciar("cafe_alerta"))
        self.assertTrue(self.capa.activa)
        self.assertEqual(self.capa.estado, "poster")
        self.assertIsNone(self.capa._reproductor)
        self.assertFalse(self.capa._poster.imagen.isNull())
        self.assertTrue(self.capa.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents))

    def test_poster_cubre_carga_y_video_se_revela_solo_con_frame_valido(self):
        self.escribir_recursos()
        preparados = []
        self.capa.video_preparado.connect(preparados.append)
        self.assertTrue(self.capa.iniciar("cafe_alerta"))
        self.assertTrue(self.capa._poster.isVisible())
        self.assertEqual(self.capa._poster.imagen.toImage().pixelColor(4, 4), QColor("#234767"))
        self.assertFalse(self.capa._video.isVisible())
        self.capa._nuevo_frame(QVideoFrame())
        self.assertEqual(preparados, [])
        self.primer_frame()
        self.assertEqual(preparados, ["cafe_alerta"])
        self.assertTrue(self.capa._video.isVisible())
        self.assertFalse(self.capa._poster.isVisible())
        self.assertEqual(self.capa.estado, "reproduciendo")
        self.assertEqual(self.capa._reproductor.bucle, QMediaPlayer.Loops.Infinite)

    def test_reproductor_se_destruye_antes_que_el_sink_al_cerrar_capa(self):
        self.escribir_recursos()
        capa = CapaCinematica(raiz=self.raiz)
        orden = []
        try:
            capa.iniciar("cafe_alerta")
            reproductor, video = capa._reproductor, capa._video
            reproductor.destroyed.connect(lambda: orden.append("reproductor"))
            video.videoSink().destroyed.connect(lambda: orden.append("sink"))
            imagen = QImage(32, 18, QImage.Format.Format_RGB32)
            imagen.fill(QColor("#9e715c"))
            capa._nuevo_frame(QVideoFrame(imagen))
            self.assertEqual(capa.estado, "reproduciendo")
            self.assertTrue(video.isVisible())
            hijos = capa.children()
            self.assertLess(hijos.index(reproductor), hijos.index(video))
            self.assertIs(video.videoSink().parent(), video)
            capa.close()
            self.assertTrue(reproductor.source().isEmpty())
            self.assertFalse(reproductor.reproduciendo)
            self.assertFalse(capa.activa)
        finally:
            capa.close()
            capa.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.assertEqual(orden, ["reproductor", "sink"])

    def test_pausa_libera_fuente_y_reanuda_desde_la_posicion(self):
        self.escribir_recursos()
        self.capa.iniciar("cafe_alerta")
        self.primer_frame()
        reproductor = self.capa._reproductor
        reproductor.posicion = 3210
        self.capa.pausar()
        self.assertEqual(self.capa.estado, "pausada")
        self.assertTrue(reproductor.source().isEmpty())
        self.assertFalse(reproductor.reproduciendo)
        self.assertTrue(self.capa._poster.isVisible())
        self.assertEqual(self.capa._poster.imagen.toImage().pixelColor(4, 4), QColor("#9e715c"))
        self.capa.reanudar()
        self.assertFalse(reproductor.source().isEmpty())
        self.assertEqual(reproductor.position(), 3210)
        self.assertTrue(reproductor.reproduciendo)
        self.assertEqual(self.capa._poster.imagen.toImage().pixelColor(4, 4), QColor("#9e715c"))

    def test_preparar_instala_el_primer_plano_sin_reproducir_hasta_la_voz(self):
        self.escribir_recursos()
        self.assertTrue(self.capa.iniciar("cafe_alerta", reproducir=False))
        self.assertIsNone(self.capa._reproductor)
        self.assertTrue(self.capa.isVisible())
        self.assertTrue(self.capa._poster.isVisible())
        self.assertEqual(self.capa._poster.imagen.toImage().pixelColor(4, 4), QColor("#234767"))
        self.capa.reanudar()
        self.assertTrue(self.capa._reproductor.reproduciendo)

    def test_movimiento_reducido_usa_el_cartel_legible_y_no_el_frame_de_carga(self):
        self.escribir_recursos()
        self.capa.configurar(reducir_movimiento=True)
        self.capa.iniciar("cafe_alerta")
        esperado = QImage(str(self.raiz / CINEMATICAS["cafe_alerta"]["poster"]))
        self.assertEqual(self.capa._poster.imagen.toImage().pixelColor(4, 4), esperado.pixelColor(4, 4))
        self.capa.configurar(reducir_movimiento=False)
        self.assertEqual(self.capa._poster.imagen.toImage().pixelColor(4, 4), QColor("#234767"))

    def test_cambiar_fuente_no_oculta_capa_ni_acepta_frame_del_canal_anterior(self):
        self.escribir_recursos()
        self.escribir_recursos(clave="person_colegio_c")
        self.capa.iniciar("cafe_alerta")
        self.primer_frame()
        canal_anterior = self.capa._video.videoSink()
        generacion_anterior = self.capa._generacion
        with patch.object(self.capa, "hide", wraps=self.capa.hide) as ocultar:
            self.capa.iniciar("person_colegio_c")
        ocultar.assert_not_called()
        imagen = QImage(32, 18, QImage.Format.Format_RGB32)
        imagen.fill(QColor("#ff00ff"))
        viejo = QVideoFrame(imagen)
        canal_anterior.setVideoFrame(viejo)
        self.capa._nuevo_frame(viejo, generacion_anterior)
        self.assertTrue(self.capa._video._imagen.isNull())
        self.assertTrue(self.capa._poster.isVisible())
        self.assertEqual(self.capa._poster.imagen.toImage().pixelColor(4, 4), QColor("#234767"))
        self.primer_frame()
        self.assertEqual(self.capa._video._imagen.pixelColor(4, 4), QColor("#9e715c"))

    def test_reanudar_no_muestra_frame_cero_antes_de_completar_el_seek(self):
        self.escribir_recursos()
        self.capa.iniciar("cafe_alerta")
        self.primer_frame()
        self.capa._reproductor.posicion = 3210
        self.capa.pausar()
        self.capa.reanudar()
        imagen = QImage(32, 18, QImage.Format.Format_RGB32)
        imagen.fill(QColor("#ff00ff"))
        inicio = QVideoFrame(imagen)
        inicio.setStartTime(0)
        self.capa._video.videoSink().setVideoFrame(inicio)
        self.assertTrue(self.capa._poster.isVisible())
        self.assertTrue(self.capa._video._imagen.isNull())
        self.assertEqual(self.capa._poster.imagen.toImage().pixelColor(4, 4), QColor("#9e715c"))
        imagen.fill(QColor("#56b28c"))
        reanudado = QVideoFrame(imagen)
        reanudado.setStartTime(3210000)
        self.capa._video.videoSink().setVideoFrame(reanudado)
        self.assertFalse(self.capa._poster.isVisible())
        self.assertEqual(self.capa._video._imagen.pixelColor(4, 4), QColor("#56b28c"))

    def test_callbacks_enviados_antes_del_cambio_no_invalidan_la_nueva_fuente(self):
        self.escribir_recursos()
        self.escribir_recursos(clave="person_colegio_c")
        self.capa.iniciar("cafe_alerta")
        vieja = self.capa._generacion
        self.capa.iniciar("person_colegio_c")
        self.capa._error_video(generacion=vieja)
        self.capa._cambio_media(QMediaPlayer.MediaStatus.EndOfMedia, vieja)
        self.assertFalse(self.capa._reproductor.source().isEmpty())
        self.assertNotEqual(self.capa.estado, "error")
        self.assertNotEqual(self.capa.estado, "finalizada")

    def test_reanudar_y_reaplicar_opciones_no_tapan_un_video_que_ya_reproduce(self):
        self.escribir_recursos()
        self.capa.iniciar("cafe_alerta")
        self.primer_frame()
        sink = self.capa._video.videoSink()
        self.capa.reanudar()
        self.capa.configurar(reducir_movimiento=False, activo=True)
        self.assertIs(self.capa._video.videoSink(), sink)
        self.assertFalse(self.capa._poster.isVisible())
        self.assertTrue(self.capa._video.isVisible())
        self.assertEqual(self.capa.estado, "reproduciendo")

    def test_renovar_fuente_no_desconecta_observadores_externos_del_transporte(self):
        self.escribir_recursos()
        self.capa.iniciar("cafe_alerta")
        estados = []
        self.capa._reproductor.mediaStatusChanged.connect(estados.append)
        self.capa.pausar()
        self.capa.reanudar()
        self.assertIn(QMediaPlayer.MediaStatus.LoadedMedia, estados)

    def test_reduccion_y_desactivacion_conservan_poster_sin_video(self):
        self.escribir_recursos()
        self.capa.configurar(reducir_movimiento=True)
        self.capa.iniciar("cafe_alerta")
        self.assertIsNone(self.capa._reproductor)
        self.capa.configurar(reducir_movimiento=False)
        reproductor = self.capa._reproductor
        self.assertFalse(reproductor.source().isEmpty())
        self.capa.configurar(activo=False)
        self.assertTrue(reproductor.source().isEmpty())
        self.assertTrue(self.capa.activa)
        self.assertEqual(self.capa.estado, "poster")
        self.capa.configurar(activo=True)
        self.assertTrue(reproductor.reproduciendo)

    def test_ocultar_cierra_decoder_y_no_reinicia_si_estaba_pausado(self):
        self.escribir_recursos()
        self.capa.iniciar("cafe_alerta")
        reproductor = self.capa._reproductor
        reproductor.posicion = 765
        self.capa.hide()
        self.assertTrue(reproductor.source().isEmpty())
        self.capa.show()
        self.assertEqual(reproductor.position(), 765)
        self.capa.pausar()
        self.capa.hide()
        self.capa.show()
        self.assertTrue(reproductor.source().isEmpty())

    def test_error_usa_poster_y_detener_olvida_seleccion_y_posicion(self):
        self.escribir_recursos()
        self.capa.iniciar("cafe_alerta")
        self.primer_frame()
        self.capa._reproductor.errorOccurred.emit()
        self.assertEqual(self.capa.estado, "error")
        self.assertTrue(self.capa._reproductor.source().isEmpty())
        self.assertTrue(self.capa._poster.isVisible())
        self.assertTrue(self.capa.activa)
        self.capa.detener()
        self.assertFalse(self.capa.activa)
        self.assertIsNone(self.capa.clave_actual)
        self.assertEqual(self.capa._posicion, 0)
        self.assertFalse(self.capa.isVisible())
        self.assertFalse(self.capa.iniciar("../../../otro"))

    def test_minimizar_padre_libera_video_y_restaurar_conserva_posicion(self):
        ventana = QWidget()
        self.addCleanup(ventana.close)
        self.capa.setParent(ventana)
        ventana.resize(640, 360)
        ventana.show()
        self.escribir_recursos()
        self.capa.iniciar("cafe_alerta")
        reproductor = self.capa._reproductor
        reproductor.posicion = 1220
        ventana.showMinimized()
        self.app.processEvents()
        self.assertTrue(reproductor.source().isEmpty())
        ventana.showNormal()
        self.app.processEvents()
        self.assertFalse(reproductor.source().isEmpty())
        self.assertEqual(reproductor.position(), 1220)


if __name__ == "__main__":
    unittest.main()
