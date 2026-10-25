"""Cinco desenlaces distintos, reproducción local y cierres sin efectos de juego."""
import hashlib
import json
import os
import time
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import QCoreApplication, QEvent
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget

from cinematica_final_visual import CLIPS, RenderizadorFinal
from cinematica_narrativa import CapaCinematica
from final_ui import EscenaFin
from juego.cinematica_final import CINEMATICAS_FINALES, clave_final
from juego.partida import Juego
from recursos import RAIZ


class FinalVideosTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.ventana = QWidget()
        self.ventana.juego = Juego(7, eventos=False)
        self.ventana.reducir_movimiento = True
        self.ventana.animar_fondos = True
        self.ventana.volver_portada = lambda: None
        self.ventana.resize(1366, 768)
        layout = QVBoxLayout(self.ventana)
        self.escena = EscenaFin()
        layout.addWidget(self.escena)
        self.ventana.show()
        self.app.processEvents()

    def tearDown(self):
        self.ventana.close()
        self.ventana.deleteLater()
        self.app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_cuatro_electos_y_recuento_tienen_video_real_verificado(self):
        manifest = json.loads((RAIZ / "assets/expansion/finales/manifest.json").read_text(encoding="utf-8"))
        self.assertEqual({c["clave"] for c in manifest["clips"]}, set(CINEMATICAS_FINALES))
        for clip in manifest["clips"]:
            ruta = RAIZ / CINEMATICAS_FINALES[clip["clave"]]["video"]
            self.assertTrue(ruta.is_file())
            self.assertEqual(hashlib.sha256(ruta.read_bytes()).hexdigest(), clip["sha256"])
            self.assertEqual((clip["ancho"], clip["alto"], clip["fps"], clip["duracion"]), (1280, 720, 24, 12))
            self.assertTrue(clip["decodificacion_completa"])

    def test_render_tiene_movimiento_y_cada_candidato_es_distinto(self):
        huellas = []
        for clave in CLIPS:
            render = RenderizadorFinal(clave)
            imagenes = [render.capturar_fotograma(t, (320, 180)) for t in (1, 6, 10)]
            hashes = [hashlib.sha256(i.constBits().asstring(i.sizeInBytes())).hexdigest() for i in imagenes]
            self.assertEqual(len(set(hashes)), 3)
            self.assertTrue(all(f.is_file() for f in render.fuentes))
            huellas.append(hashes[-1])
        self.assertEqual(5, len(set(huellas)))

    def test_escena_selecciona_solo_ganador_real_y_conserva_empate(self):
        for candidato in self.ventana.juego.candidatos:
            for c in self.ventana.juego.candidatos:
                c.apoyo = 70 if c is candidato else 25
            self.escena.mostrar()
            self.assertEqual(self.escena.cine_final.clave_actual, candidato.id)
            self.assertEqual(self.escena.cine_final.estado, "poster")
            self.assertIsNone(self.escena.cine_final._reproductor)
            self.assertIn(candidato.nombre, self.escena.ganador.text())
            self.assertAlmostEqual(self.escena.cine_final.width()/self.escena.cine_final.height(), 16/9, delta=.02)
        for c in self.ventana.juego.candidatos:
            c.apoyo = 25
        self.escena.mostrar()
        self.assertEqual(self.escena.cine_final.clave_actual, "recuento")
        self.assertIsNone(self.escena.ganador_id)

    def test_saltar_y_repetir_dialogo_no_modifican_estado_ni_dejan_reproductor(self):
        self.escena.mostrar()
        antes = self.ventana.juego.datos()
        for _ in range(4):
            self.escena.abrir_video_final()
            dialogo = self.escena.dialogo_video
            self.assertIsNotNone(dialogo)
            self.assertEqual(dialogo.cine.clave_actual, "recuento")
            self.assertTrue(dialogo.cine.activa)
            dialogo.close()
            self.app.processEvents()
            self.assertIsNone(self.escena.dialogo_video)
        self.assertEqual(antes, self.ventana.juego.datos())
        self.escena.hide()
        self.assertFalse(self.escena.cine_final.activa)

    def test_reproductor_real_no_repite_y_libera_fuente_al_salir(self):
        self.ventana.reducir_movimiento = False
        self.escena.mostrar()
        cine = self.escena.cine_final
        fin = time.monotonic()+4
        while cine.estado != "reproduciendo" and time.monotonic() < fin:
            self.app.processEvents()
        self.assertEqual(cine.estado, "reproduciendo")
        self.assertEqual(cine._reproductor.loops(), QMediaPlayer.Loops.Once)
        self.assertFalse(cine._video._imagen.isNull())
        cine._reproductor.setPosition(11800)
        fin = time.monotonic()+4
        while cine.estado != "finalizada" and time.monotonic() < fin:
            self.app.processEvents()
        self.assertEqual(cine.estado, "finalizada")
        self.assertFalse(cine._video._imagen.isNull())
        self.escena.hide()
        self.assertTrue(cine._reproductor.source().isEmpty())
        self.assertFalse(cine.activa)


if __name__ == "__main__":
    unittest.main()
