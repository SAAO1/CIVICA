"""El dispositivo de cada decisión conserva la publicación real del caso."""
import hashlib
import json
import os
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtGui import QColor, QImage, QPainter
from PyQt6.QtWidgets import QApplication

from cine_telefono import imagen_feed
from cinematica_acciones_visual import RenderizadorAccion
from cinematica_acciones_extendida_visual import RenderizadorAccionExtendida
from herramientas.producir_acciones_video import huella_render, preparar_pantallas, usa_telefono


RAIZ = Path(__file__).resolve().parents[1]


class TelefonosAccionesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        preparar_pantallas((50, 30, 70, 20, 60, 80, 90, 40, 100, 10, 110, 25, 120, 35))

    def test_cada_telefono_recibe_el_identificador_del_caso(self):
        imagen = QImage(300, 500, QImage.Format.Format_ARGB32)
        imagen.fill(QColor("#201e1a"))
        p = QPainter(imagen)
        try:
            for identificador in (50, 30, 70, 20, 60, 80, 90, 40, 100, 10, 110, 25, 120, 35):
                renderizador = RenderizadorAccion if identificador in (50, 30, 70, 20, 60, 80) else RenderizadorAccionExtendida
                with self.subTest(publicacion=identificador), patch("cinematica_acciones_visual.pintar_telefono") as pintar:
                    renderizador(f"accion_{identificador}_compartir")._telefono(p, 0, 0, "", 2)
                    self.assertEqual(pintar.call_args.args[-1], identificador)
        finally:
            p.end()

    def test_telefono_contiene_feed_claro_con_contenido_en_lugar_de_azul_vacio(self):
        imagen = QImage(270, 460, QImage.Format.Format_ARGB32)
        imagen.fill(QColor("#201e1a"))
        p = QPainter(imagen)
        RenderizadorAccion("accion_50_compartir")._telefono(p, 10, 10, "", 0, quieto=True)
        p.end()
        claros = 0
        colores = set()
        for y in range(30, 400, 5):
            for x in range(30, 220, 5):
                color = imagen.pixelColor(x, y)
                claros += min(color.red(), color.green(), color.blue()) > 185
                colores.add(color.rgb())
        self.assertGreater(claros, 700)
        self.assertGreater(len(colores), 100)
        self.assertNotEqual(hashlib.sha256(imagen_feed(50).constBits().asstring(imagen_feed(50).sizeInBytes())).hexdigest(),
                            hashlib.sha256(imagen_feed(90).constBits().asstring(imagen_feed(90).sizeInBytes())).hexdigest())

    def test_inventarios_registran_render_y_feed_del_caso(self):
        actualizados = 0
        for carpeta, renderizador in (("assets/expansion/acciones_video", RenderizadorAccion),
                                      ("assets/expansion/siete_actos/acciones", RenderizadorAccionExtendida)):
            clips = json.loads((RAIZ/carpeta/"manifest.json").read_text(encoding="utf-8"))["clips"]
            for clip in clips:
                render = renderizador(clip["clave"])
                if not usa_telefono(render.ficha):
                    continue
                actualizados += 1
                with self.subTest(clave=clip["clave"]):
                    firma, pantalla = huella_render(render)
                    self.assertEqual(clip["render_sha256"], firma)
                    self.assertEqual(clip["pantalla_sha256"], pantalla)
                    self.assertEqual(clip["pantalla_publicacion"], clip["publicacion"])
        self.assertEqual(actualizados, 56)
