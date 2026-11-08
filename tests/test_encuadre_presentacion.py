"""Anclaje y recorte de fuente coinciden en video, cubierta y pausa."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import QRectF, QSize
from PyQt6.QtGui import QColor, QImage, QPainter, QPixmap
from PyQt6.QtMultimedia import QVideoFrame
from PyQt6.QtWidgets import QApplication, QWidget

from interfaz.cinematica.reproductor import (
    CapaCinematica, _Poster, _VideoCompuesto, _opciones_presentacion, _rectangulos_presentacion,
)
from tests.test_cinematica_narrativa import ReproductorControlado


class PruebasEncuadrePresentacion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.padre = QWidget()
        self.padre.resize(1360, 649)
        self.padre.show()
        self.imagen = QImage(1280, 720, QImage.Format.Format_RGB32)
        self.imagen.fill(QColor("#246348"))
        p = QPainter(self.imagen)
        p.fillRect(0, 0, 1280, 36, QColor("#d35432"))
        p.fillRect(0, 614, 1280, 106, QColor("#de29b3"))
        p.end()

    def tearDown(self):
        self.padre.close()
        self.padre.deleteLater()
        self.app.processEvents()

    def superficies(self, anclaje=.5, recorte=0):
        poster = _Poster(self.padre)
        video = _VideoCompuesto(self.padre)
        for capa in (poster, video):
            capa.resize(self.padre.size())
            capa.anclaje_y = anclaje
            capa.recorte_inferior = recorte
        poster.imagen = QPixmap.fromImage(self.imagen)
        video.videoSink().setVideoFrame(QVideoFrame(self.imagen))
        return poster, video

    def captura_rgb(self, widget):
        # La cubierta opaca entrega RGB32 y QWidget con video entrega ARGB32.
        # Compara todos los píxeles visibles en el mismo formato, sin tolerancia.
        return widget.grab().toImage().convertToFormat(QImage.Format.Format_RGB32)

    def test_anclaje_superior_conserva_cabello_que_centrado_recorta(self):
        centrado = self.superficies()
        superior = self.superficies(anclaje=0)
        for medio in range(2):
            with self.subTest(medio=medio):
                self.assertEqual(centrado[medio].grab().toImage().pixelColor(680, 1), QColor("#246348"))
                self.assertEqual(superior[medio].grab().toImage().pixelColor(680, 1), QColor("#d35432"))

    def test_recorte_excluye_pie_de_la_fuente_sin_franja_negra_ni_modificar_imagen(self):
        original = self.imagen.copy()
        completas = self.superficies()
        recortadas = self.superficies(recorte=.155)
        for medio in range(2):
            with self.subTest(medio=medio):
                completa = completas[medio].grab().toImage()
                recortada = recortadas[medio].grab().toImage()
                self.assertEqual(completa.pixelColor(680, 648), QColor("#de29b3"))
                self.assertEqual(recortada.pixelColor(680, 648), QColor("#246348"))
                for x in (0, 679, 1359):
                    for y in (0, 324, 648):
                        self.assertNotEqual(recortada.pixelColor(x, y), QColor("black"))
        self.assertEqual(self.imagen, original)

    def test_video_y_cubierta_tienen_mismo_encuadre_y_proporcion_en_tres_aspectos(self):
        for ancho, alto in ((1360, 649), (600, 600), (400, 700)):
            self.padre.resize(ancho, alto)
            for anclaje, recorte in ((.5, 0), (0, 0), (0, .155), (.5, .155), (1, .2)):
                with self.subTest(tamano=(ancho, alto), anclaje=anclaje, recorte=recorte):
                    poster, video = self.superficies(anclaje, recorte)
                    self.assertEqual(self.captura_rgb(poster), self.captura_rgb(video))
                    destino, origen = _rectangulos_presentacion(
                        self.imagen.size(), self.padre.size(), anclaje, recorte)
                    self.assertAlmostEqual(origen.height(), 720*(1-recorte))
                    self.assertAlmostEqual(destino.width()/origen.width(),
                                           destino.height()/origen.height(), delta=.002)
                    self.assertTrue(QRectF(destino).contains(QRectF(0, 0, ancho, alto)))

    def test_opciones_omitidas_o_invalidas_conservan_centrado_y_fuente_valida(self):
        self.assertEqual(_opciones_presentacion({}), (.5, 0))
        self.assertEqual(_opciones_presentacion({"anclaje_y":0, "recorte_inferior":.155}), (0, .155))
        for dato in (None, "invalido", float("nan"), float("inf")):
            self.assertEqual(_opciones_presentacion({"anclaje_y":dato, "recorte_inferior":dato}), (.5, 0))
        for dato in (-.1, 1, 2):
            self.assertEqual(_opciones_presentacion({"recorte_inferior":dato})[1], 0)

    def test_cambio_de_clave_no_conserva_opciones_anteriores_y_pausa_no_recorta_dos_veces(self):
        with tempfile.TemporaryDirectory() as temporal:
            raiz = Path(temporal)
            self.imagen.save(str(raiz/"poster.png"))
            (raiz/"video.mp4").write_bytes(b"transporte aislado por la prueba")
            base = {"video":"video.mp4", "poster":"poster.png", "inicio":"poster.png"}
            catalogo = {"nuevo":dict(base, anclaje_y=0, recorte_inferior=.155), "legado":dict(base)}
            with patch('interfaz.cinematica.reproductor.QMediaPlayer', ReproductorControlado):
                capa = CapaCinematica(self.padre, raiz=raiz, catalogo=catalogo)
                capa.resize(self.padre.size())
                self.assertTrue(capa.iniciar("nuevo", reproducir=False))
                self.assertIsNone(capa._video)
                self.assertEqual((capa._poster.anclaje_y, capa._poster.recorte_inferior), (0, .155))
                cubierta = self.captura_rgb(capa._poster)
                capa.reanudar()
                self.assertEqual((capa._video.anclaje_y, capa._video.recorte_inferior), (0, .155))
                capa._reproductor.salida.setVideoFrame(QVideoFrame(self.imagen))
                self.assertEqual(self.captura_rgb(capa._video), cubierta)
                capa.pausar()
                self.assertEqual(self.captura_rgb(capa._poster), cubierta)
                video_existente = capa._video
                capa.iniciar("legado")
                self.assertIs(capa._video, video_existente)
                for superficie in (capa._poster, capa._video):
                    self.assertEqual((superficie.anclaje_y, superficie.recorte_inferior), (.5, 0))
                self.assertEqual(capa._poster.grab().toImage().pixelColor(680, 1), QColor("#246348"))
                capa.detener()
                self.assertEqual((capa._anclaje_y, capa._recorte_inferior), (.5, 0))
                capa.close()


if __name__ == "__main__":
    unittest.main()
