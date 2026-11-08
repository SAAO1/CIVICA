"""Comprueba archivos audiovisuales reales de la campaña de investigación."""
import array
import hashlib
import json
import os
from pathlib import Path
import subprocess
import unittest
import wave

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtGui import QImage, QImageReader
from PyQt6.QtWidgets import QApplication
from herramientas.exportar_ambientes import localizar_ffmpeg
from infraestructura.recursos import RAIZ
from juego.casos_feria import IDS_FERIA


def huella(datos):
    return hashlib.sha256(datos).hexdigest()


class PruebasRecursosFeria(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.manifest = json.loads((RAIZ/"assets/feria/manifest.json").read_text(encoding="utf-8"))
        cls.ffmpeg = localizar_ffmpeg()

    def test_inventario_conserva_origen_real_y_hashes_de_los_archivos(self):
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
        self.assertEqual(len(self.manifest["origen_arte"]["images"]), 3)
        self.assertTrue(all(entrada["prompt"] for entrada in self.manifest["origen_arte"]["images"]))
        self.assertTrue((RAIZ/self.manifest["fuente_tipografica"]["archivo"]).is_file())

    def test_recortes_y_originales_son_piezas_diferentes_para_cada_caso(self):
        self.assertEqual(len(self.manifest["pruebas"]), 12)
        firmas = set()
        for id in IDS_FERIA:
            imagenes = []
            for variante in ("recorte", "original"):
                ruta = RAIZ/f"assets/feria/pruebas/{id}_{variante}.png"
                imagen = QImage(str(ruta))
                self.assertFalse(imagen.isNull())
                self.assertEqual((imagen.width(), imagen.height()), (1400, 900))
                datos = imagen.constBits().asstring(imagen.sizeInBytes())
                firmas.add(huella(datos))
                imagenes.append(datos)
            self.assertNotEqual(*imagenes, f"El caso {id} no puede mostrar la misma pieza dos veces")
        self.assertEqual(len(firmas), 12)

    def test_cada_mp4_decodifica_completo_tiene_movimiento_y_cubierta_exacta(self):
        videos = self.manifest["videos"]
        self.assertEqual({v["caso_id"] for v in videos}, set(IDS_FERIA))
        for video in videos:
            with self.subTest(caso=video["caso_id"]):
                ruta = RAIZ/video["archivo"]
                subprocess.run([self.ffmpeg, "-v", "error", "-i", str(ruta), "-f", "null", "-"],
                               capture_output=True, check=True)
                cuadros = []
                for segundo in (0, 3):
                    salida = subprocess.run([self.ffmpeg, "-v", "error", "-ss", str(segundo),
                                             "-i", str(ruta), "-frames:v", "1", "-pix_fmt", "rgb24",
                                             "-f", "rawvideo", "-"], capture_output=True, check=True)
                    self.assertEqual(len(salida.stdout), 1280*720*3)
                    cuadros.append(salida.stdout)
                self.assertNotEqual(huella(cuadros[0]), huella(cuadros[1]))
                cubierta = QImage(str(RAIZ/video["primer_fotograma"]["archivo"])).convertToFormat(
                    QImage.Format.Format_RGB888)
                self.assertEqual(cuadros[0], cubierta.constBits().asstring(cubierta.sizeInBytes()))
                self.assertEqual((video["duracion"], video["fotogramas"], video["fps"]), (6.0, 144, 24))

    def test_portada_es_un_gif_animado_decodificable(self):
        ruta = RAIZ/self.manifest["portada_gif"]["archivo"]
        lector = QImageReader(str(ruta))
        self.assertTrue(lector.supportsAnimation())
        self.assertGreaterEqual(lector.imageCount(), 24)
        cuadros = []
        while lector.canRead() and len(cuadros) < 30:
            imagen = lector.read()
            self.assertFalse(imagen.isNull())
            self.assertEqual((imagen.width(), imagen.height()), (800, 450))
            cuadros.append(huella(imagen.constBits().asstring(imagen.sizeInBytes())))
        self.assertGreater(len(set(cuadros)), 10)
        self.assertLess(ruta.stat().st_size, 10*1024*1024)

    def test_audio_recortado_conserva_exactamente_el_segmento_central_original(self):
        audios = {}
        for nombre in ("recortado", "completo"):
            ruta = RAIZ/f"assets/feria/audio/caso_110_{nombre}.wav"
            with wave.open(str(ruta), "rb") as voz:
                self.assertEqual((voz.getnchannels(), voz.getsampwidth(), voz.getframerate()), (1, 2, 24000))
                datos = voz.readframes(voz.getnframes())
                muestras = array.array("h", datos)
                self.assertGreater(max(map(abs, muestras)), 1000)
                self.assertLess(max(map(abs, muestras)), 32768)
                audios[nombre] = datos
        inicio = self.manifest["audio"]["segmento_central_inicio_frame"]*2
        largo = self.manifest["audio"]["segmento_central_frames"]*2
        self.assertEqual(audios["completo"][inicio:inicio+largo], audios["recortado"])
        self.assertGreater(len(audios["completo"]), len(audios["recortado"])*2)
        self.assertEqual(self.manifest["audio"]["transcripcion_recortada"], "cobrar por votar")
        self.assertEqual(self.manifest["audio"]["transcripcion_completa"],
                         "Si alguien pretende cobrar por votar, denuncia ese engaño.")

    def test_las_seis_aperturas_tienen_sonido_y_voz_identificada(self):
        aperturas = [r for r in self.manifest["audio"]["archivos"] if "_apertura.wav" in r["archivo"]]
        self.assertEqual(len(aperturas), 6)
        for registro in aperturas:
            with wave.open(str(RAIZ/registro["archivo"]), "rb") as entrada:
                datos = entrada.readframes(entrada.getnframes())
                muestras = array.array("h", datos)
                self.assertGreater(len(muestras), 24000)
                self.assertGreater(sum(v*v for v in muestras)/len(muestras), 1000)
            self.assertEqual(registro["voz"], "Microsoft Sabina Desktop")
            self.assertIn("Síntesis", registro["origen"])


if __name__ == "__main__":
    unittest.main()
