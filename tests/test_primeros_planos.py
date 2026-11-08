"""Los cuatro candidatos tienen planos reales, móviles y vinculados a sus CG."""
import hashlib
import json
import os
import subprocess
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QApplication

from herramientas.exportar_ambientes import localizar_ffmpeg
from herramientas.producir_primeros_planos import ACTORES, RAIZ, SALIDA, encuadre, fotograma


def firma(datos):
    return hashlib.sha256(datos).hexdigest()


class PruebasPrimerosPlanos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.ffmpeg = localizar_ffmpeg()
        cls.manifest = json.loads((SALIDA/"videos/manifest.json").read_text(encoding="utf-8"))

    def ejecutar(self, *args, correcto=True):
        r = subprocess.run([self.ffmpeg, "-hide_banner", "-v", "error", *map(str, args)],
                           capture_output=True, timeout=30)
        if correcto:
            self.assertEqual(r.returncode, 0, r.stderr.decode(errors="replace"))
        return r

    def test_procedencia_y_hashes_de_cuatro_identidades_y_medios(self):
        def revisar(objeto):
            if isinstance(objeto, dict):
                if "archivo" in objeto and "sha256" in objeto:
                    ruta = (RAIZ/objeto["archivo"]).resolve()
                    self.assertTrue(ruta.is_relative_to(RAIZ.resolve()))
                    self.assertEqual(firma(ruta.read_bytes()), objeto["sha256"], str(ruta))
                    self.assertEqual(ruta.stat().st_size, objeto["bytes"])
                for valor in objeto.values():
                    revisar(valor)
            elif isinstance(objeto, list):
                for valor in objeto:
                    revisar(valor)
        revisar(self.manifest)
        self.assertEqual({cg["id"] for cg in self.manifest["cg"]}, set(ACTORES))
        self.assertEqual({v["clave"] for v in self.manifest["videos"]}, set(ACTORES))
        procedencia = {r["id"]:r for r in self.manifest["origen_arte"]["recursos"]}
        for cg in self.manifest["cg"]:
            self.assertEqual(cg["sha256"], procedencia[cg["id"]]["sha256"])

    def test_camara_conserva_proporcion_y_encuadre_y_cierra_el_bucle(self):
        for actor in ACTORES:
            with self.subTest(actor=actor):
                ruta = SALIDA/"cg"/(actor+".png")
                antes = firma(ruta.read_bytes())
                imagen = QImage(str(ruta))
                for segundo in (0, 1, 2, 3, 4, 5, 6):
                    caja = encuadre(imagen, segundo)
                    self.assertTrue(QRectF(imagen.rect()).contains(caja))
                    self.assertAlmostEqual(caja.width()/caja.height(), 1280/720, places=7)
                    self.assertLess(caja.top(), imagen.height()*.005)
                primero, ultimo = fotograma(imagen, 0), fotograma(imagen, 6)
                self.assertEqual(primero, ultimo)
                self.assertNotEqual(primero, fotograma(imagen, 3))
                self.assertEqual(firma(ruta.read_bytes()), antes)

    def test_decodificacion_estricta_144_cuadros_6_segundos_24fps_sin_audio(self):
        for video in self.manifest["videos"]:
            with self.subTest(actor=video["clave"]):
                ruta = RAIZ/video["archivo"]
                datos = self.ejecutar("-xerror", "-err_detect", "explode", "-i", ruta,
                                     "-vf", "scale=1:1", "-pix_fmt", "gray", "-f", "rawvideo", "-").stdout
                self.assertEqual(len(datos), 144)
                audio = self.ejecutar("-i", ruta, "-map", "0:a", "-f", "null", "-", correcto=False)
                self.assertNotEqual(audio.returncode, 0)
                self.assertIn(b"matches no streams", audio.stderr)
                metadatos = subprocess.run([self.ffmpeg, "-hide_banner", "-i", str(ruta),
                                          "-frames:v", "1", "-f", "null", "-"],
                                         capture_output=True, timeout=30)
                self.assertEqual(metadatos.returncode, 0)
                self.assertIn(b"1280x720", metadatos.stderr)
                self.assertIn(b"24 fps", metadatos.stderr)
                self.assertIn(b"Duration: 00:00:06.00", metadatos.stderr)
                self.assertEqual((video["ancho"], video["alto"], video["fps"], video["duracion"],
                                  video["fotogramas"]), (1280, 720, 24, 6.0, 144))
                self.assertEqual(video["textos"], [])
                self.assertFalse(video["botones"])

    def test_inicio_exacto_poster_del_plano_y_tres_muestras_de_movimiento_real(self):
        for video in self.manifest["videos"]:
            with self.subTest(actor=video["clave"]):
                cuadros = [self.ejecutar("-ss", t, "-i", RAIZ/video["archivo"], "-frames:v", "1",
                                        "-pix_fmt", "rgb24", "-f", "rawvideo", "-").stdout
                           for t in (0, 3, 5)]
                self.assertTrue(all(len(c) == 1280*720*3 for c in cuadros))
                self.assertEqual([firma(c) for c in cuadros], video["movimiento"]["rgb_sha256"])
                self.assertEqual(len({firma(c) for c in cuadros}), 3)
                for cuadro in cuadros[1:]:
                    diferencia = sum(abs(a-b) for a, b in zip(cuadros[0][::97], cuadro[::97]))/len(cuadro[::97])
                    self.assertGreater(diferencia, .2)
                inicio = QImage(str(RAIZ/video["primer_fotograma"]["archivo"])).convertToFormat(
                    QImage.Format.Format_RGB888)
                self.assertEqual(inicio.constBits().asstring(inicio.sizeInBytes()), cuadros[0])
                poster = QImage(str(RAIZ/video["poster"]["archivo"])).convertToFormat(QImage.Format.Format_RGB888)
                self.assertEqual((poster.width(), poster.height()), (1280, 720))
                rgb = poster.constBits().asstring(poster.sizeInBytes())
                perdida_jpeg = sum(abs(a-b) for a, b in zip(rgb[::97], cuadros[1][::97]))/len(rgb[::97])
                self.assertLess(perdida_jpeg, 4, "El cartel debe corresponder al plano real del segundo 3")


if __name__ == "__main__":
    unittest.main()
