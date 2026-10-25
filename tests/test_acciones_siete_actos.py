"""Los cuatro actos añadidos muestran el método elegido en su propio caso."""
import hashlib
import json
import os
from types import SimpleNamespace
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication
from juego.acciones import acciones_para_rol, accion_por_defecto
from juego.partida import Juego
from juego.cinematica_acciones import CINEMATICAS_ACCIONES
from juego.cinematica_acciones_extendida import (
    CASOS_ACCIONES_EXTENDIDOS, CINEMATICAS_ACCIONES_EXTENDIDAS, clave_accion_extendida)
from cinematica_acciones_extendida_visual import CARPETA_EXTENDIDA, RenderizadorAccionExtendida
from cinematica_acciones_visual import RAIZ


class AccionesSieteActosTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_cada_caso_y_metodo_resuelve_sin_mutar_historia(self):
        seleccionadas = set()
        for rol in ("ciudadano", "periodista"):
            for identificador in CASOS_ACCIONES_EXTENDIDOS:
                for definicion in acciones_para_rol(rol):
                    with self.subTest(rol=rol, publicacion=identificador, accion=definicion["clave"]):
                        juego = Juego(8, eventos=False, campana="extendida")
                        juego.seleccionar_rol(rol)
                        juego.iniciar_primera_publicacion()
                        while juego.obtener_publicacion_actual().id != identificador:
                            juego.ejecutar_accion(accion_por_defecto(rol))
                            juego.avanzar_publicacion()
                        self.assertTrue(juego.ejecutar_accion(definicion["clave"]))
                        antes = json.dumps(juego.datos(), sort_keys=True)
                        clave = clave_accion_extendida(juego)
                        self.assertIn(clave, CINEMATICAS_ACCIONES_EXTENDIDAS)
                        ficha = CINEMATICAS_ACCIONES_EXTENDIDAS[clave]
                        self.assertEqual(ficha["publicacion"], identificador)
                        self.assertEqual(ficha["accion"], definicion["clave"])
                        self.assertEqual(ficha["nombre"], rol.upper())
                        self.assertEqual(antes, json.dumps(juego.datos(), sort_keys=True))
                        seleccionadas.add(clave)
        self.assertEqual(len(seleccionadas), 64)

    def test_variantes_no_inventan_receptores_ni_retiradas(self):
        for identificador in CASOS_ACCIONES_EXTENDIDOS:
            registro = {"publicacion": {"id": identificador}, "accion_rol": "convocar"}
            for alcance in (0, 1, 7, 8, 19):
                registro["alcance"] = alcance
                clave = clave_accion_extendida(None, registro)
                self.assertIn(clave, CINEMATICAS_ACCIONES_EXTENDIDAS)
                if alcance < 8:
                    self.assertEqual(RenderizadorAccionExtendida(clave).fuentes[-1].name, "compartir.jpg")
                else:
                    self.assertEqual(RenderizadorAccionExtendida(clave).fuentes[-1].name, "convocar.jpg")
            registro["accion_rol"] = "desmentir"
            registro["eliminada"] = False
            self.assertTrue(clave_accion_extendida(None, registro).endswith("_rechazado"))
            registro["eliminada"] = True
            self.assertEqual(clave_accion_extendida(None, registro), f"accion_{identificador}_desmentir")

    def test_selector_conserva_clasicos_y_no_confunde_un_titulo_importado(self):
        juego = Juego(8, eventos=False)
        juego.iniciar_primera_publicacion()
        juego.ejecutar_accion("compartir")
        self.assertIn(clave_accion_extendida(juego), CINEMATICAS_ACCIONES)
        for registro in (
            {}, {"publicacion": {"id": 90, "texto": "Otro asunto"}, "accion": "compartir"},
            {"publicacion": {"id": 999}, "accion": "compartir"},
            {"publicacion": {"id": 90}, "accion": "convocar", "alcance": True},
            {"publicacion": {"id": 90}, "accion": "convocar", "alcance": -1},
            {"publicacion": {"id": 90}, "accion": "desmentir", "eliminada": "no"},
        ):
            self.assertIsNone(clave_accion_extendida(SimpleNamespace(ultimo_registro=registro)))

    def test_ochenta_y_ocho_montajes_con_fuentes_nuevas_y_movimiento(self):
        self.assertEqual(len(CINEMATICAS_ACCIONES), 66)
        self.assertEqual(len(CINEMATICAS_ACCIONES_EXTENDIDAS), 88)
        for identificador in CASOS_ACCIONES_EXTENDIDOS:
            clave = f"accion_{identificador}_contrastar"
            render = RenderizadorAccionExtendida(clave)
            self.assertTrue(all(fuente.is_file() for fuente in render.fuentes))
            self.assertTrue(all("siete_actos" in str(fuente) for fuente in render.fuentes[:2]))
            self.assertEqual([plano["tipo"] for plano in render.planos], ["lugar", "objeto", "accion"])
            firmas = set()
            for t in (0, 2.8, 5, 8):
                imagen = render.capturar_fotograma(t, (320, 180))
                firmas.add(hashlib.sha256(imagen.constBits().asstring(imagen.sizeInBytes())).hexdigest())
            self.assertEqual(len(firmas), 4)

    def test_manifest_cubre_todos_los_videos_decodificados_y_primeros_cuadros(self):
        documento = json.loads((CARPETA_EXTENDIDA / "manifest.json").read_text(encoding="utf-8"))
        clips = {clip["clave"]: clip for clip in documento["clips"]}
        self.assertEqual(set(clips), set(CINEMATICAS_ACCIONES_EXTENDIDAS))
        for clave, clip in clips.items():
            with self.subTest(clave=clave):
                self.assertEqual((clip["ancho"], clip["alto"], clip["fps"], clip["fotogramas"]), (1280, 720, 24, 216))
                self.assertTrue(clip["decodificacion_completa"])
                self.assertTrue(clip["inicio_extraido_del_video"])
                for campo in ("video", "poster", "inicio"):
                    ruta = CARPETA_EXTENDIDA / clip[campo]
                    etiqueta = "sha256" if campo == "video" else campo+"_sha256"
                    self.assertEqual(hashlib.sha256(ruta.read_bytes()).hexdigest(), clip[etiqueta])
                self.assertTrue(all((RAIZ/f["ruta"]).is_file() for f in clip["fuentes"]))
