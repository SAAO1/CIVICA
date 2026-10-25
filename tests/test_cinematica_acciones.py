"""Cada decisión reproduce su acción y sus variantes sin inventar consecuencias."""
import hashlib
import json
import os
from types import SimpleNamespace
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication
from juego.acciones import acciones_para_rol, accion_por_defecto
from juego.partida import Juego
from juego.historia import contenido_resultado
from juego.cinematica_acciones import (ACCIONES_VIDEO, CASOS_ACCIONES,
                                       CINEMATICAS_ACCIONES, clave_accion)
from cinematica_acciones_visual import (CARPETA, DURACION, FPS, RAIZ,
                                        RenderizadorAccion)


class SeleccionAccionesVideoTests(unittest.TestCase):
    def test_cada_caso_y_oficio_tiene_su_pelicula_desde_la_decision_real(self):
        seleccionadas = set()
        for rol in ("ciudadano", "periodista"):
            for identificador in CASOS_ACCIONES:
                for accion in acciones_para_rol(rol):
                    with self.subTest(rol=rol, publicacion=identificador, accion=accion["clave"]):
                        juego = Juego(8, eventos=False)
                        juego.seleccionar_rol(rol); juego.iniciar_primera_publicacion()
                        while juego.obtener_publicacion_actual().id != identificador:
                            juego.ejecutar_accion(accion_por_defecto(rol)); juego.avanzar_publicacion()
                        juego.ejecutar_accion(accion["clave"])
                        antes = json.dumps(juego.datos(), sort_keys=True)
                        clave = clave_accion(juego)
                        self.assertIn(clave, CINEMATICAS_ACCIONES)
                        self.assertEqual(identificador, CINEMATICAS_ACCIONES[clave]["publicacion"])
                        self.assertEqual(accion["clave"], CINEMATICAS_ACCIONES[clave]["accion"])
                        self.assertEqual(contenido_resultado(juego, 1)[1], CINEMATICAS_ACCIONES[clave]["nombre"])
                        self.assertEqual(antes, json.dumps(juego.datos(), sort_keys=True))
                        seleccionadas.add(clave)
        self.assertEqual(48, len(seleccionadas))

    def test_no_inventa_reunion_cuando_no_hay_receptores(self):
        for identificador in CASOS_ACCIONES:
            registro = {"publicacion": {"id": identificador}, "accion_rol": "convocar", "alcance": 0}
            clave = clave_accion(None, registro)
            self.assertTrue(clave.endswith("_sin_receptores"))
            render = RenderizadorAccion(clave)
            self.assertEqual("compartir.jpg", render.fuentes[-1].name)
            self.assertNotIn("convocar.jpg", str(render.fuentes))

    def test_reporte_rechazado_no_muestra_retiro(self):
        for identificador in CASOS_ACCIONES:
            r = {"publicacion": {"id": identificador}, "accion_rol": "desmentir", "eliminada": False}
            self.assertTrue(clave_accion(None, r).endswith("_rechazado"))
            r["eliminada"] = True
            self.assertEqual(f"accion_{identificador}_desmentir", clave_accion(None, r))

    def test_grupo_limitado_no_se_convierte_en_multitud(self):
        for alcance in range(1, 8):
            registro = {"publicacion": {"id": 50}, "accion_rol": "convocar", "alcance": alcance}
            clave = clave_accion(None, registro)
            self.assertEqual("accion_50_convocar_alcance_limitado", clave)
            self.assertEqual("compartir.jpg", RenderizadorAccion(clave).fuentes[-1].name)
        registro["alcance"] = 8
        self.assertEqual("accion_50_convocar", clave_accion(None, registro))

    def test_partidas_anteriores_y_casos_importados_no_confunden_escenas(self):
        for antigua, nueva in (("verificar", "contrastar"), ("reportar", "desmentir")):
            r = {"publicacion": {"id": 50}, "accion": antigua, "eliminada": True}
            self.assertEqual(f"accion_50_{nueva}", clave_accion(None, r))
        invalidos = (None, [], {}, {"publicacion": None}, {"publicacion": {"id": 999}, "accion": "compartir"},
                     {"publicacion": {"id": 50}, "accion": "inventada"},
                     {"publicacion": {"id": 50, "texto": "Un asunto importado distinto del colegio"}, "accion": "compartir"},
                     {"publicacion": {"id": []}, "accion": "compartir"},
                     {"publicacion": {"id": 50}, "accion": []},
                     {"publicacion": {"id": 50}, "accion": "convocar", "alcance": "varias personas"},
                     {"publicacion": {"id": 50}, "accion": "convocar", "alcance": -2},
                     {"publicacion": {"id": 50}, "accion": "desmentir", "eliminada": "False"})
        for registro in invalidos:
            self.assertIsNone(clave_accion(SimpleNamespace(ultimo_registro=registro)))


class MontajesAccionesVideoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @staticmethod
    def huella(imagen):
        return hashlib.sha256(imagen.constBits().asstring(imagen.sizeInBytes())).hexdigest()

    def test_sesenta_y_seis_clips_y_objetos_y_contextos_propios(self):
        self.assertEqual(66, len(CINEMATICAS_ACCIONES))
        self.assertEqual(66, len({f["video"] for f in CINEMATICAS_ACCIONES.values()}))
        self.assertEqual(6, len({CASOS_ACCIONES[i]["objeto"] for i in CASOS_ACCIONES}))
        self.assertEqual(6, len({CASOS_ACCIONES[i]["fondo"] for i in CASOS_ACCIONES}))
        for clave, ficha in CINEMATICAS_ACCIONES.items():
            with self.subTest(clave=clave):
                render = RenderizadorAccion(clave)
                self.assertEqual(["lugar", "objeto", "accion"], [p["tipo"] for p in render.planos])
                self.assertEqual(3, len(set(render.fuentes)))
                self.assertTrue(all(r.is_file() for r in render.fuentes))
                self.assertTrue(ficha["inicio"].endswith("_inicio.png"))
                self.assertFalse(ficha["bucle"])

    def test_montaje_determinista_con_movimiento_en_la_accion(self):
        for accion in ACCIONES_VIDEO:
            render = RenderizadorAccion(f"accion_50_{accion}")
            imagenes = [self.huella(render.capturar_fotograma(t, (320, 180))) for t in (0, 2.8, 5, 8)]
            self.assertEqual(4, len(set(imagenes)))
            self.assertEqual(imagenes[2], self.huella(render.capturar_fotograma(5, (320, 180))))
            self.assertLessEqual(len(render._imagenes), 3)
        with self.assertRaises(ValueError):
            RenderizadorAccion("../../no")
        with self.assertRaises(ValueError):
            render.capturar_fotograma(0, (0, 20))

    def test_exportacion_integral_y_hashes_del_inventario(self):
        documento = json.loads((CARPETA/"manifest.json").read_text(encoding="utf-8"))
        clips = {c["clave"]: c for c in documento["clips"]}
        self.assertEqual(set(CINEMATICAS_ACCIONES), set(clips))
        hashes = {}
        for clave, clip in clips.items():
            with self.subTest(clave=clave):
                self.assertEqual((1280, 720, FPS, int(FPS*DURACION)), (clip["ancho"], clip["alto"], clip["fps"], clip["fotogramas"]))
                self.assertTrue(clip["decodificacion_completa"])
                self.assertTrue(clip["inicio_extraido_del_video"])
                for campo in ("video", "poster", "inicio"):
                    ruta = CARPETA/clip[campo]
                    etiqueta = "sha256" if campo == "video" else campo+"_sha256"
                    self.assertEqual(hashlib.sha256(ruta.read_bytes()).hexdigest(), clip[etiqueta])
                for fuente in clip["fuentes"]:
                    ruta = RAIZ/fuente["ruta"]
                    if str(ruta) not in hashes:
                        hashes[str(ruta)] = hashlib.sha256(ruta.read_bytes()).hexdigest()
                    self.assertEqual(hashes[str(ruta)], fuente["sha256"])


if __name__ == "__main__":
    unittest.main()
