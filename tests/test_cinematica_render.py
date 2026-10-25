"""La producción de vídeos conserva movimiento y una procedencia comprobable."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import hashlib
import json
from pathlib import Path
import unittest

from PyQt6.QtWidgets import QApplication

from cinematica_visual import CLIPS, DURACION, CARPETA, FPS, RAIZ, RenderizadorCinematica


class CinematicaRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @staticmethod
    def huella(imagen):
        return hashlib.sha256(imagen.constBits().asstring(imagen.sizeInBytes())).hexdigest()

    def test_veintiun_contextos_con_fuentes_locales(self):
        self.assertEqual(21, len(CLIPS))
        for clave in CLIPS:
            with self.subTest(clave=clave):
                render = RenderizadorCinematica(clave)
                self.assertTrue(render.fuentes)
                self.assertTrue(all(r.is_file() for r in render.fuentes))
                imagen = render.capturar_fotograma(6, (320, 180))
                self.assertFalse(imagen.isNull())
                self.assertEqual((320, 180), (imagen.width(), imagen.height()))

    def test_personajes_tienen_montaje_de_tres_planos_y_temas_propios(self):
        personajes = [ficha for clave, ficha in CLIPS.items() if clave.startswith("person_")]
        self.assertEqual(12, len(personajes))
        self.assertEqual(12, len({ficha["tema"] for ficha in personajes}))
        for ficha in personajes:
            self.assertEqual(3, len(ficha["planos"]))
            self.assertGreaterEqual(len(set(ficha["planos"])), 2)

    def test_archivos_producidos_coinciden_con_el_catalogo_y_su_inventario(self):
        from juego.cinematica import CINEMATICAS
        self.assertEqual(set(CLIPS), set(CINEMATICAS))
        manifest = json.loads((CARPETA / "manifest.json").read_text(encoding="utf-8"))
        registros = {entrada["clave"]: entrada for entrada in manifest["clips"]}
        self.assertEqual(set(CLIPS), set(registros))
        for clave, entrada in registros.items():
            with self.subTest(clave=clave):
                video = CARPETA / entrada["video"]
                poster = CARPETA / entrada["poster"]
                self.assertEqual(video.stat().st_size, entrada["bytes"])
                self.assertEqual(hashlib.sha256(video.read_bytes()).hexdigest(), entrada["sha256"])
                self.assertEqual(hashlib.sha256(poster.read_bytes()).hexdigest(), entrada["poster_sha256"])
                self.assertEqual((1280, 720, FPS, round(DURACION*FPS)),
                                 (entrada["ancho"], entrada["alto"], entrada["fps"], entrada["fotogramas"]))
                self.assertTrue(entrada["decodificacion_completa"])
                for fuente in entrada["fuentes"]:
                    self.assertEqual(hashlib.sha256((RAIZ / fuente["ruta"]).read_bytes()).hexdigest(), fuente["sha256"])

    def test_tiempo_determinista_y_accion_entre_planos(self):
        for clave in CLIPS:
            with self.subTest(clave=clave):
                render = RenderizadorCinematica(clave)
                a = self.huella(render.capturar_fotograma(2, (320, 180)))
                b = self.huella(render.capturar_fotograma(6, (320, 180)))
                c = self.huella(render.capturar_fotograma(10, (320, 180)))
                self.assertEqual(a, self.huella(render.capturar_fotograma(2, (320, 180))))
                self.assertEqual(3, len({a, b, c}))
                self.assertLessEqual(len(render._imagenes), 2)

    def test_tiempo_acotado_y_rechazo_de_claves_ajenas(self):
        render = RenderizadorCinematica("ciudad_48h")
        self.assertEqual(self.huella(render.capturar_fotograma(-20, (160, 90))),
                         self.huella(render.capturar_fotograma(0, (160, 90))))
        self.assertEqual(self.huella(render.capturar_fotograma(10000, (160, 90))),
                         self.huella(render.capturar_fotograma(DURACION, (160, 90))))
        with self.assertRaises(ValueError):
            RenderizadorCinematica("../fuera")
        with self.assertRaises(ValueError):
            render.capturar_fotograma(0, (0, 90))


if __name__ == "__main__":
    unittest.main()
