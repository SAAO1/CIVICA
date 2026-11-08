"""Verifica clips reales, movimiento, procedencia y vistas de la novela."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtGui import QImage, QImageReader
from PyQt6.QtWidgets import QApplication
from herramientas.exportar_ambientes import localizar_ffmpeg
from infraestructura.recursos import RAIZ


def huella(datos):
    return hashlib.sha256(datos).hexdigest()


class PruebasRecursosNovela(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.manifest = json.loads((RAIZ/"assets/novela/manifest.json").read_text(encoding="utf-8"))
        cls.ffmpeg = localizar_ffmpeg()

    def ejecutar(self, *argumentos, correcto=True):
        resultado = subprocess.run([self.ffmpeg, "-v", "error", *map(str, argumentos)],
                                   capture_output=True)
        if correcto:
            self.assertEqual(resultado.returncode, 0, resultado.stderr.decode(errors="replace"))
        return resultado

    def test_procedencia_y_firmas_corresponden_a_archivos_reales(self):
        def visitar(valor):
            if isinstance(valor, dict):
                if "archivo" in valor and "sha256" in valor:
                    ruta = (RAIZ/valor["archivo"]).resolve()
                    self.assertTrue(ruta.is_relative_to(RAIZ.resolve()))
                    self.assertTrue(ruta.is_file(), str(ruta))
                    self.assertEqual(huella(ruta.read_bytes()), valor["sha256"], str(ruta))
                    self.assertEqual(ruta.stat().st_size, valor["bytes"])
                for item in valor.values():
                    visitar(item)
            elif isinstance(valor, list):
                for item in valor:
                    visitar(item)
        visitar(self.manifest)
        self.assertEqual({x["id"] for x in self.manifest["cg"]},
                         {"archivo", "parque", "redaccion", "urnas"})
        prompts = {x["id"]:x for x in self.manifest["origen_arte"]["prompts"]}
        for entrada in self.manifest["cg"]:
            with self.subTest(cg=entrada["id"]):
                imagen = QImage(str(RAIZ/entrada["archivo"]))
                self.assertFalse(imagen.isNull())
                self.assertEqual((imagen.width(), imagen.height()),
                                 (entrada["ancho"], entrada["alto"]))
                self.assertIn(entrada["original"], prompts[entrada["id"]]["origen"])
                self.assertGreater(len(prompts[entrada["id"]]["prompt"]), 100)

    def test_seis_planos_decodifican_completos_y_carecen_de_audio(self):
        videos = self.manifest["videos"]
        self.assertEqual([v["acto"] for v in videos], list(range(1,7)))
        self.assertEqual([v["caso_id"] for v in videos], [50,90,110,40,120,35])
        self.assertEqual([v["cg"] for v in videos],
                         ["archivo","parque","redaccion","redaccion","urnas","urnas"])
        for video in videos:
            with self.subTest(acto=video["acto"]):
                ruta = RAIZ/video["archivo"]
                # Decodifica todos los cuadros y reduce solo la salida de diagnóstico.
                resultado = self.ejecutar("-i", ruta, "-vf", "scale=1:1", "-pix_fmt",
                                          "gray", "-f", "rawvideo", "-")
                self.assertEqual(len(resultado.stdout), 96)
                sin_pista = self.ejecutar("-i", ruta, "-map", "0:a", "-f", "null", "-",
                                          correcto=False)
                self.assertNotEqual(sin_pista.returncode, 0)
                self.assertIn(b"matches no streams", sin_pista.stderr)
                detalle = subprocess.run([self.ffmpeg,"-hide_banner","-i",str(ruta),
                                          "-f","null","-"], capture_output=True)
                self.assertEqual(detalle.returncode, 0)
                self.assertIn(b"1280x720", detalle.stderr)
                self.assertIn(b"24 fps", detalle.stderr)

    def test_movimiento_visible_y_primer_fotograma_corresponden_al_clip(self):
        for video in self.manifest["videos"]:
            with self.subTest(acto=video["acto"]):
                cuadros = [
                    self.ejecutar("-ss", segundo, "-i", RAIZ/video["archivo"],
                                  "-frames:v", "1", "-pix_fmt", "rgb24",
                                  "-f", "rawvideo", "-").stdout
                    for segundo in (0,2)
                ]
                self.assertTrue(all(len(x)==1280*720*3 for x in cuadros))
                self.assertEqual([huella(x) for x in cuadros],
                                 video["movimiento"]["rgb_sha256"])
                diferencia = sum(abs(a-b)>2 for a,b in zip(*cuadros))/len(cuadros[0])
                self.assertGreater(diferencia, 0.20, "La cámara debe producir movimiento visible")
                portada = QImage(str(RAIZ/video["primer_fotograma"]["archivo"])).convertToFormat(
                    QImage.Format.Format_RGB888)
                self.assertEqual(cuadros[0], portada.constBits().asstring(portada.sizeInBytes()))
                preview = QImage(str(RAIZ/video["preview"]["archivo"]))
                self.assertFalse(preview.isNull())
                self.assertEqual((preview.width(), preview.height()), (1280,720))

    def test_gif_es_un_bucle_animado_completo_y_ligero(self):
        ruta = RAIZ/self.manifest["portada_gif"]["archivo"]
        lector = QImageReader(str(ruta))
        self.assertTrue(lector.supportsAnimation())
        self.assertEqual(lector.imageCount(), 48)
        self.assertLess(ruta.stat().st_size, 8*1024*1024)
        firmas = []
        while lector.canRead():
            imagen = lector.read()
            self.assertFalse(imagen.isNull(), lector.errorString())
            self.assertEqual((imagen.width(), imagen.height()), (640,360))
            firmas.append(huella(imagen.constBits().asstring(imagen.sizeInBytes())))
        self.assertEqual(len(firmas), 48)
        self.assertGreater(len(set(firmas)), 30)
        self.ejecutar("-i", ruta, "-f", "null", "-")


if __name__ == "__main__":
    unittest.main()
