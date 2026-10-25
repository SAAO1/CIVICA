"""Recursos entregables de los cinco NPC y los cuatro lugares de la ampliación."""
import hashlib
import json
import os
import unittest
import wave

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QApplication
from ambiente_visual import FondoVivo
from personajes_animados import ACTORES_NUEVOS, SpriteExpresivo, fotogramas_actor
from recursos import RAIZ


class RecursosSieteActosTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_cinco_personajes_tienen_expresiones_boca_y_parpadeo_reales(self):
        for nombre in ACTORES_NUEVOS:
            huellas = set()
            for estado in ("neutral", "decidido", "preocupado", "hablando", "parpadeo"):
                ruta = RAIZ / f"assets/expansion/siete_actos/personajes/{nombre}_{estado}.png"
                with self.subTest(nombre=nombre, estado=estado):
                    imagen = QImage(str(ruta))
                    self.assertFalse(imagen.isNull(), str(ruta))
                    self.assertTrue(imagen.hasAlphaChannel())
                    self.assertEqual((imagen.width(), imagen.height()), (768, 1536))
                    rgba = imagen.convertToFormat(QImage.Format.Format_RGBA8888)
                    datos = rgba.constBits().asstring(rgba.sizeInBytes())
                    alpha = datos[3::4]
                    self.assertGreater(sum(v < 8 for v in alpha), len(alpha)*.05)
                    self.assertGreater(sum(v > 240 for v in alpha), len(alpha)*.05)
                    huellas.add(hashlib.sha256(datos).digest())
            self.assertEqual(len(huellas), 5, nombre)
            fotogramas = fotogramas_actor(nombre)
            self.assertEqual(len(fotogramas), 5)
            self.assertEqual(len({fotograma.cacheKey() for fotograma in fotogramas}), 5,
                             "El runtime conserva un respaldo duplicado en lugar del gesto real")

    def test_bocas_npc_siguen_voz_y_accesibilidad_detiene_gestos(self):
        for nombre in ACTORES_NUEVOS:
            actor = SpriteExpresivo()
            try:
                actor.configurar_actor(nombre)
                actor.establecer_tiempo(1)
                # Evita la ventana de parpadeo propia de cada actor.
                instante = next(t/10 for t in range(10, 20) if actor.indice_fotograma(t/10) == 0)
                actor.establecer_tiempo(instante)
                actor.establecer_hablando(True, .8)
                self.assertEqual(actor.indice_fotograma(), 3)
                actor.establecer_hablando(False)
                self.assertEqual(actor.indice_fotograma(), 0)
                actor.configurar_movimiento(reducir=True)
                actor.establecer_hablando(True, .8)
                self.assertEqual(actor.indice_fotograma(), 0)
                self.assertFalse(actor._timer.isActive())
                actor.configurar_movimiento(reducir=False)
                fase = sum(map(ord, nombre))*.17
                self.assertEqual(actor.indice_fotograma((-fase) % 4.7 + .01), 4)
            finally:
                actor.close()
                actor.deleteLater()

    def test_cuatro_lugares_tienen_fondo_cg_y_ambiente_sin_fuente_inventada(self):
        for nombre in ("estudio", "debate", "redaccion", "urnas"):
            for carpeta in ("fondos", "ilustraciones"):
                ruta = f"assets/expansion/siete_actos/{carpeta}/{nombre}.jpg"
                imagen = QImage(str(RAIZ / ruta))
                self.assertFalse(imagen.isNull(), ruta)
                self.assertGreaterEqual(imagen.width(), 1280)
            fondo = FondoVivo()
            try:
                fondo.establecer_escena(f"assets/expansion/siete_actos/fondos/{nombre}.jpg", nombre)
                self.assertEqual(fondo.ambiente, nombre)
                a = fondo.capturar_fotograma(1, (320, 180))
                b = fondo.capturar_fotograma(3, (320, 180))
                self.assertNotEqual(a, b)
                fondo.configurar(reducir_movimiento=True)
                self.assertEqual(fondo.capturar_fotograma(1, (320, 180)), fondo.capturar_fotograma(3, (320, 180)))
            finally:
                fondo.close()
                fondo.deleteLater()

    def test_ocho_audios_son_pcm_local_sin_saturacion_y_con_fuentes(self):
        carpeta = RAIZ / "assets/audio/siete_actos"
        manifest = json.loads((carpeta / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["licencia"], "CC0-1.0")
        self.assertEqual(len(manifest["recursos"]), 8)
        for nombre, datos in manifest["recursos"].items():
            ruta = carpeta / (nombre + ".wav")
            self.assertEqual(hashlib.sha256(ruta.read_bytes()).hexdigest(), datos["sha256"])
            self.assertGreater(datos["pico"], .001)
            self.assertLessEqual(datos["pico"], .72)
            self.assertTrue(datos["capas"])
            with wave.open(str(ruta), "rb") as audio:
                self.assertEqual((audio.getnchannels(), audio.getsampwidth(), audio.getframerate()), (1, 2, 32000))
                self.assertAlmostEqual(audio.getnframes()/32000, datos["duracion_s"], places=2)


if __name__ == "__main__":
    unittest.main()
