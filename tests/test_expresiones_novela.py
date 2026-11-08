"""Emociones propias de candidatos sin sustituirlas por boca o parpadeo neutro."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBitmap, QPixmap, QRegion
from PyQt6.QtWidgets import QApplication

from infraestructura.recursos import RAIZ
from interfaz.componentes.personajes_animados import (
    ACTORES_NUEVOS, EMOCIONES_NPC_NUEVAS, SpriteExpresivo, emociones_actor, encuadre_actor,
    fotogramas_actor,
)


class PruebasExpresionesNovela(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def actor(self, rol, expresion):
        actor = SpriteExpresivo()
        actor.configurar_actor(rol, expresion)
        self.addCleanup(actor.close)
        return actor

    def test_cada_png_propio_existente_se_usa_sin_alterarlo_y_conserva_atlas_original(self):
        encontradas = 0
        for rol in sorted(ACTORES_NUEVOS):
            self.assertEqual(len(fotogramas_actor(rol)), 5)
            disponibles = emociones_actor(rol)
            for estado in EMOCIONES_NPC_NUEVAS:
                ruta = RAIZ / f"assets/novela/pulido/expresiones/{rol}_{estado}.png"
                if not ruta.is_file():
                    continue
                with self.subTest(actor=rol, estado=estado):
                    encontradas += 1
                    self.assertIn(estado, disponibles)
                    actor = self.actor(rol, estado)
                    self.assertEqual(actor.expresion_visual, estado)
                    # Ambos pasan por QPixmap: Qt premultiplica el alpha al
                    # subir una imagen y QImage conserva el PNG sin esa conversión.
                    self.assertEqual(actor.fotograma_actual().toImage(), QPixmap(str(ruta)).toImage())
        self.assertEqual(encontradas, 20, "Cada uno de los cinco personajes necesita cuatro emociones propias")

    def test_encuadre_real_por_silueta_conserva_escala_de_los_cinco_personajes(self):
        for rol in sorted(ACTORES_NUEVOS):
            for estado in ("neutral",) + EMOCIONES_NPC_NUEVAS:
                with self.subTest(actor=rol, estado=estado):
                    actor = self.actor(rol, estado)
                    actor.resize(215, 235)
                    actor.configurar_movimiento(reducir=True)
                    imagen = actor.fotograma_actual()
                    caja = QRegion(QBitmap.fromImage(imagen.toImage().createAlphaMask(
                        Qt.ImageConversionFlag.ThresholdAlphaDither))).boundingRect()
                    encuadre = encuadre_actor(imagen)
                    self.assertAlmostEqual(encuadre.height()/caja.height(), .53, places=3)
                    self.assertTrue(imagen.rect().contains(encuadre.toAlignedRect()))
                    actor.show()
                    self.app.processEvents()
                    captura = actor.grab().toImage()
                    visible = QRegion(QBitmap.fromImage(captura.createAlphaMask(
                        Qt.ImageConversionFlag.ThresholdAlphaDither))).boundingRect()
                    self.assertGreater(visible.height(), actor.height()*.85)
                    self.assertGreater(visible.width(), actor.width()*.5)

    def test_hablar_y_parpadear_no_borran_ninguna_emocion_del_invitado(self):
        for rol in sorted(ACTORES_NUEVOS):
            for estado in ("sonrisa", "decidido", "preocupado") + EMOCIONES_NPC_NUEVAS:
                with self.subTest(actor=rol, estado=estado):
                    actor = self.actor(rol, estado)
                    actor.establecer_hablando(False)
                    imagen = actor.fotograma_actual(1).cacheKey()
                    actor.establecer_hablando(True, .9)
                    for instante in (0, .05, 1, 4.7):
                        self.assertEqual(actor.fotograma_actual(instante).cacheKey(), imagen)
                    actor.configurar_movimiento(reducir=True)
                    self.assertEqual(actor.fotograma_actual().cacheKey(), imagen)

    def test_si_falta_png_de_enojo_se_usa_preocupado_real_y_nunca_sonrisa(self):
        with patch("interfaz.componentes.personajes_animados.emociones_actor", return_value={}):
            actor = self.actor("camila", "enojado")
        self.assertEqual(actor.expresion_visual, "preocupado")
        self.assertEqual(actor.fotograma_actual().cacheKey(), actor._fotogramas[2].cacheKey())
        self.assertNotEqual(actor.fotograma_actual().cacheKey(), actor._fotogramas[1].cacheKey())

    def test_protagonistas_conservan_24_celdas_y_animacion_facial_por_emocion(self):
        for rol, parpadeo in (("ciudadano", .05), ("periodista", 3.9)):
            actor = self.actor(rol, "enojado")
            self.assertEqual(len(actor._fotogramas), 24)
            actor.establecer_hablando(False)
            cerrada = actor.fotograma_actual(1).cacheKey()
            actor.establecer_hablando(True, .9)
            self.assertNotEqual(actor.fotograma_actual(1).cacheKey(), cerrada)
            self.assertNotEqual(actor.fotograma_actual(parpadeo).cacheKey(), cerrada)
            self.assertEqual(actor.expresion_visual, "enojado")
