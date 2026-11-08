"""Comprueba los planos contextuales reales y la tipografía portátil."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import unittest

os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from PyQt6.QtGui import QColor,QImage,QRawFont
from PyQt6.QtWidgets import QApplication
from herramientas.producir_pulido_visual import (
    RAIZ,SALIDA,PLANES,ORDEN_FORO,cargar_fuentes,fuente,fotograma,
)
from herramientas.exportar_ambientes import localizar_ffmpeg

MANIFEST=SALIDA/"videos/manifest.json"


def firma(datos):
    return hashlib.sha256(datos).hexdigest()


class PruebasCompositorContextual(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])
        cargar_fuentes()

    def test_siete_contextos_caben_con_tipografia_portatil_y_se_animan(self):
        self.assertEqual(QRawFont.fromFont(fuente(24)).familyName(),"Atkinson Hyperlegible")
        base=QImage(1600,900,QImage.Format.Format_ARGB32)
        base.fill(QColor("#283454"))
        for indice,plan in enumerate(PLANES):
            with self.subTest(clip=plan[0]):
                imagenes=[fotograma(base,t,indice) for t in (0,3)]
                self.assertTrue(all((i.width(),i.height())==(1280,720) for i in imagenes))
                datos=[i.constBits().asstring(i.sizeInBytes()) for i in imagenes]
                self.assertNotEqual(firma(datos[0]),firma(datos[1]))

    def test_orden_de_rotulos_corresponde_a_identidad_original_revisada(self):
        self.assertEqual(ORDEN_FORO,("JUAN","ADRIÁN","LAURA","CAMILA"))


@unittest.skipUnless(MANIFEST.is_file(),"Los siete planos todavía no se han exportado")
class PruebasRecursosPulido(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])
        cls.manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.ffmpeg=localizar_ffmpeg()

    def ejecutar(self,*argumentos,correcto=True):
        r=subprocess.run([self.ffmpeg,"-v","error",*map(str,argumentos)],capture_output=True)
        if correcto:
            self.assertEqual(r.returncode,0,r.stderr.decode(errors="replace"))
        return r

    def test_manifest_conserva_procedencia_y_hashes_reales_de_todos_los_archivos(self):
        def revisar(valor):
            if isinstance(valor,dict):
                if "archivo" in valor and "sha256" in valor:
                    ruta=(RAIZ/valor["archivo"]).resolve()
                    self.assertTrue(ruta.is_relative_to(RAIZ.resolve()))
                    self.assertTrue(ruta.is_file(),str(ruta))
                    self.assertEqual(firma(ruta.read_bytes()),valor["sha256"],str(ruta))
                    self.assertEqual(ruta.stat().st_size,valor["bytes"])
                for item in valor.values():
                    revisar(item)
            elif isinstance(valor,list):
                for item in valor:
                    revisar(item)
        revisar(self.manifest)
        self.assertEqual(len(self.manifest["cg"]),7)
        self.assertTrue(self.manifest["origen_arte"])
        self.assertEqual(self.manifest["orden_visual_foro"],list(ORDEN_FORO))
        self.assertEqual(self.manifest["tipografia"]["familia"],"Atkinson Hyperlegible")

    def test_siete_videos_tienen_144_cuadros_completos_y_no_contienen_voz(self):
        videos=self.manifest["videos"]
        self.assertEqual({v["clave"] for v in videos},{p[0] for p in PLANES})
        for video in videos:
            with self.subTest(clip=video["clave"]):
                ruta=RAIZ/video["archivo"]
                datos=self.ejecutar("-i",ruta,"-vf","scale=1:1","-pix_fmt","gray",
                                   "-f","rawvideo","-").stdout
                self.assertEqual(len(datos),144)
                audio=self.ejecutar("-i",ruta,"-map","0:a","-f","null","-",correcto=False)
                self.assertNotEqual(audio.returncode,0)
                self.assertIn(b"matches no streams",audio.stderr)
                self.assertEqual((video["ancho"],video["alto"],video["fps"],video["duracion"]),
                                 (1280,720,24,6.0))

    def test_muestras_moviles_y_posters_corresponden_a_la_decodificacion_real(self):
        for video in self.manifest["videos"]:
            with self.subTest(clip=video["clave"]):
                cuadros=[self.ejecutar("-ss",t,"-i",RAIZ/video["archivo"],"-frames:v","1",
                                      "-pix_fmt","rgb24","-f","rawvideo","-").stdout
                         for t in (0,3,5)]
                self.assertTrue(all(len(c)==1280*720*3 for c in cuadros))
                self.assertEqual([firma(c) for c in cuadros],video["movimiento"]["rgb_sha256"])
                self.assertEqual(len({firma(c) for c in cuadros}),3)
                inicio=QImage(str(RAIZ/video["primer_fotograma"]["archivo"])).convertToFormat(
                    QImage.Format.Format_RGB888)
                self.assertEqual(cuadros[0],inicio.constBits().asstring(inicio.sizeInBytes()))
                poster=QImage(str(RAIZ/video["poster"]["archivo"]))
                self.assertEqual((poster.width(),poster.height()),(1280,720))


if __name__=="__main__":
    unittest.main()
