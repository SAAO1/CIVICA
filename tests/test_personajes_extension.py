"""Contrato narrativo y recursos de las conversaciones nuevas."""
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
import subprocess
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage
from juego.campana_extendida import DIALOGOS_NUEVOS, PUBLICACIONES_NUEVAS
from juego.cinematica_personajes_extendida import CINEMATICAS_PERSONAJES_EXTENDIDAS, clave_personaje_extendido
from cinematica_personajes_extendida_visual import RenderizadorPersonajeExtendido


RAIZ = Path(__file__).resolve().parents[1]


class PersonajesExtensionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def juego(self, identificador=90, campana="extendida", titular=None):
        original = next(p for p in PUBLICACIONES_NUEVAS if p["id"] == identificador)
        actual = SimpleNamespace(id=identificador, texto=original["texto"] if titular is None else titular)
        return SimpleNamespace(campana=campana, obtener_publicacion_actual=lambda: actual)

    def test_cada_plano_pertenece_a_su_caso_hablante_y_frase(self):
        self.assertEqual(len(CINEMATICAS_PERSONAJES_EXTENDIDAS), 12)
        self.assertEqual({p["publicacion"] for p in CINEMATICAS_PERSONAJES_EXTENDIDAS.values()},
                         {90, 40, 100, 10, 110, 25, 120, 35})
        for clave, plano in CINEMATICAS_PERSONAJES_EXTENDIDAS.items():
            with self.subTest(clave=clave):
                self.assertEqual((plano["nombre"], plano["texto"]),
                                 DIALOGOS_NUEVOS[plano["publicacion"]][plano["indice_dialogo"]])
                self.assertEqual(clave_personaje_extendido(plano["texto"], plano["nombre"],
                                 self.juego(plano["publicacion"])), clave)

    def test_rechaza_frase_importada_otro_caso_otro_hablante_y_modo_clasico(self):
        plano = CINEMATICAS_PERSONAJES_EXTENDIDAS["personaje_90_valeria_presenta"]
        for juego in (None, self.juego(campana="clasica"), self.juego(40),
                      self.juego(titular="Un contenido importado con el mismo identificador")):
            self.assertIsNone(clave_personaje_extendido(plano["texto"], plano["nombre"], juego))
        self.assertIsNone(clave_personaje_extendido(plano["texto"], "NARRADOR", self.juego()))
        self.assertIsNone(clave_personaje_extendido(plano["texto"]+" Una frase inventada.", plano["nombre"], self.juego()))

    def test_rostro_completo_y_animacion_en_lugar_pintado(self):
        render = RenderizadorPersonajeExtendido("personaje_90_valeria_presenta")
        a = render.capturar_fotograma(2, (640, 360))
        b = render.capturar_fotograma(3, (640, 360))
        self.assertFalse(a.isNull())
        self.assertEqual((a.width(), a.height()), (640, 360))
        self.assertNotEqual(a.constBits().asstring(a.sizeInBytes()), b.constBits().asstring(b.sizeInBytes()))
        self.assertEqual(render.poses["neutral"].size(), render.poses["hablando"].size())
        self.assertTrue(all(r.is_file() for r in render.fuentes))

    def test_exportacion_completa_y_portadas_del_video(self):
        manifest = json.loads((RAIZ/"assets/expansion/siete_actos/personajes_video/manifest.json").read_text(encoding="utf-8"))
        self.assertEqual({c["clave"] for c in manifest["clips"]}, set(CINEMATICAS_PERSONAJES_EXTENDIDAS))
        for clip in manifest["clips"]:
            with self.subTest(clave=clip["clave"]):
                self.assertTrue(clip["decodificacion_completa"])
                self.assertTrue(clip["inicio_extraido_del_video"])
                self.assertEqual((clip["ancho"], clip["alto"], clip["fps"], clip["fotogramas"]), (1280, 720, 24, 216))
                for tipo in ("video", "poster", "inicio"):
                    ruta = RAIZ/"assets/expansion/siete_actos/personajes_video"/clip[tipo]
                    self.assertEqual(ruta.stat().st_size, clip[tipo+"_bytes"])
                    self.assertEqual(hashlib.sha256(ruta.read_bytes()).hexdigest(), clip[tipo+"_sha256"])

    def test_png_inicial_coincide_con_el_primer_frame_decodificado(self):
        from herramientas.exportar_ambientes import localizar_ffmpeg
        try:
            ffmpeg = localizar_ffmpeg()
        except FileNotFoundError:
            self.skipTest("La herramienta de exportación FFmpeg no forma parte del runtime")
        for clave in ("personaje_90_valeria_presenta", "personaje_120_abuelo_entrada"):
            with self.subTest(clave=clave):
                plano = CINEMATICAS_PERSONAJES_EXTENDIDAS[clave]
                salida = subprocess.run([ffmpeg, "-v", "error", "-i", str(RAIZ/plano["video"]),
                                         "-frames:v", "1", "-pix_fmt", "rgb24", "-f", "rawvideo", "pipe:1"],
                                        capture_output=True, check=True)
                inicio = QImage(str(RAIZ/plano["inicio"])).convertToFormat(QImage.Format.Format_RGB888)
                self.assertEqual(salida.stdout, inicio.constBits().asstring(inicio.sizeInBytes()))


if __name__ == "__main__":
    unittest.main()
