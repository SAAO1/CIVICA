"""Contratos visuales y de ciclo de vida de los actores y la dirección de escena."""
import copy
import hashlib
import os
import unittest
import wave

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QWidget

from ambiente_visual import _perfil
from juego.partida import Juego
from juego.puesta_escena import escenario_actual, expresion_dialogo, efecto_dialogo
from personajes_animados import SpriteExpresivo, fotogramas_actor
from recursos import RAIZ


def pixeles(imagen):
    imagen = imagen.convertToFormat(QImage.Format.Format_RGBA8888)
    return imagen.constBits().asstring(imagen.sizeInBytes())


class PruebasActoresVivos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def actor(self, rol="ciudadano", parent=None):
        actor = SpriteExpresivo(parent)
        actor.resize(280, 400)
        actor.configurar_actor(rol)
        self.addCleanup(actor.close)
        return actor

    def test_dos_actores_tienen_veinticuatro_celdas_visibles_y_transparentes(self):
        for rol in ("ciudadano", "periodista"):
            celdas = fotogramas_actor(rol)
            self.assertEqual(len(celdas), 24, rol)
            huellas = set()
            for indice, celda in enumerate(celdas):
                with self.subTest(rol=rol, fotograma=indice):
                    self.assertFalse(celda.isNull())
                    imagen = celda.toImage()
                    self.assertTrue(imagen.hasAlphaChannel())
                    self.assertGreater(imagen.width(), 100)
                    self.assertGreater(imagen.height(), imagen.width())
                    datos = pixeles(imagen)
                    alfa = datos[3::4]
                    self.assertGreater(sum(a <= 8 for a in alfa), len(alfa) * .05, "Falta el recorte transparente")
                    self.assertGreater(sum(a >= 240 for a in alfa), len(alfa) * .05, "El actor no es visible")
                    huellas.add(hashlib.sha256(datos).digest())
            self.assertEqual(len(huellas), 24, f"Fotogramas duplicados en {rol}")

    def test_siete_emociones_producen_ilustraciones_diferentes(self):
        for rol in ("ciudadano", "periodista"):
            actor = self.actor(rol)
            actor.establecer_tiempo(1.0)
            actor.show()
            imagenes = set()
            for emocion in ("neutral", "sonrisa", "preocupado", "sorprendido", "enojado", "triste", "pensativo"):
                actor.configurar_actor(rol, emocion)
                actor.establecer_hablando(False)
                imagenes.add(hashlib.sha256(pixeles(actor.grab().toImage())).digest())
            self.assertEqual(len(imagenes), 7, f"Emociones visualmente iguales en {rol}")

    def test_boca_neutral_sigue_el_nivel_y_se_cierra_al_terminar(self):
        for rol in ("ciudadano", "periodista"):
            actor = self.actor(rol)
            actor.establecer_tiempo(1.0)  # Fuera de la ventana de parpadeo.
            actor.show()
            cerrada = actor.grab().toImage()
            actor.establecer_hablando(True, nivel=.05)
            self.assertEqual(actor.grab().toImage(), cerrada, rol)
            actor.establecer_hablando(True, nivel=.8)
            self.assertNotEqual(actor.grab().toImage(), cerrada, rol)
            actor.establecer_hablando(True, nivel=0.0)
            self.assertEqual(actor.grab().toImage(), cerrada, rol)
            actor.establecer_hablando(True, nivel=.8)
            actor.establecer_hablando(False)
            self.assertEqual(actor.grab().toImage(), cerrada, rol)
            self.assertEqual(actor.nivel, 0.0)

    def test_parpadeo_y_tiempo_fijo_son_reproducibles(self):
        for rol, instante in (("ciudadano", .05), ("periodista", 3.9)):
            actor = self.actor(rol)
            actor.establecer_tiempo(1.0)
            actor.show()
            abierta = actor.grab().toImage()
            actor.establecer_tiempo(instante)
            parpadeo = actor.grab().toImage()
            self.assertNotEqual(parpadeo, abierta, rol)
            QTest.qWait(15)
            self.assertEqual(parpadeo, actor.grab().toImage(), rol)
            self.assertFalse(actor._timer.isActive())
            actor.establecer_tiempo(instante + 4.7)
            self.assertEqual(actor.indice_fotograma(), 2)
            actor.establecer_tiempo(1.0)
            self.assertEqual(actor.grab().toImage(), abierta, rol)

    def test_emociones_dramaticas_tienen_boca_y_parpadeo_propios(self):
        estados = {"enojado": (12, 13, 14), "sorprendido": (15, 16, 17),
                   "triste": (18, 19, 20), "pensativo": (21, 22, 23)}
        for rol, instante_parpadeo in (("ciudadano", .05), ("periodista", 3.9)):
            actor = self.actor(rol)
            actor.show()
            for emocion, (cerrado, abierto, parpadeo) in estados.items():
                with self.subTest(rol=rol, emocion=emocion):
                    actor.configurar_actor(rol, emocion)
                    actor.establecer_tiempo(1.0)
                    actor.establecer_hablando(False)
                    self.assertEqual(actor.indice_fotograma(), cerrado)
                    imagen_cerrada = actor.grab().toImage()
                    actor.establecer_hablando(True, nivel=.8)
                    self.assertEqual(actor.indice_fotograma(), abierto)
                    imagen_abierta = actor.grab().toImage()
                    self.assertNotEqual(imagen_abierta, imagen_cerrada)
                    actor.establecer_hablando(True, nivel=0)
                    self.assertEqual(actor.indice_fotograma(), cerrado)
                    self.assertEqual(actor.grab().toImage(), imagen_cerrada)
                    # Un parpadeo conserva su emoción incluso mientras habla.
                    actor.establecer_hablando(True, nivel=.8)
                    actor.establecer_tiempo(instante_parpadeo)
                    self.assertEqual(actor.indice_fotograma(), parpadeo)
                    imagen_parpadeo = actor.grab().toImage()
                    self.assertNotEqual(imagen_parpadeo, imagen_abierta)
                    self.assertNotEqual(imagen_parpadeo, imagen_cerrada)
                    self.assertEqual(imagen_parpadeo, actor.grab().toImage())
                    self.assertFalse(actor._timer.isActive())
                    actor.establecer_tiempo(1.0)
                    actor.establecer_hablando(False)
                    self.assertEqual(actor.grab().toImage(), imagen_cerrada)

    def test_timer_se_detiene_oculto_reducido_y_desactivado(self):
        contenedor = QWidget()
        self.addCleanup(contenedor.close)
        actor = self.actor(parent=contenedor)
        self.assertFalse(actor._timer.isActive())
        contenedor.show()
        actor.show()
        self.app.processEvents()
        self.assertTrue(actor._timer.isActive())
        self.assertTrue(actor.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents))
        contenedor.hide()
        self.app.processEvents()
        self.assertFalse(actor._timer.isActive())
        contenedor.show()
        self.app.processEvents()
        self.assertTrue(actor._timer.isActive())
        actor.configurar_movimiento(reducir=True)
        self.assertFalse(actor._timer.isActive())
        actor.configurar_movimiento(reducir=False, activo=True)
        self.assertTrue(actor._timer.isActive())
        actor.configurar_movimiento(activo=False)
        self.assertFalse(actor._timer.isActive())
        actor.configurar_movimiento(activo=True)
        self.assertTrue(actor._timer.isActive())
        actor.hide()
        self.assertFalse(actor._timer.isActive())

    def test_reduccion_congela_boca_parpadeo_y_respiracion(self):
        for rol in ("ciudadano", "periodista"):
            actor = self.actor(rol)
            actor.show()
            for reducir, activo in ((True, True), (False, False)):
                with self.subTest(rol=rol, reducir=reducir, activo=activo):
                    actor.configurar_movimiento(reducir=reducir, activo=activo)
                    actor.establecer_tiempo(.05)
                    actor.establecer_hablando(True, nivel=.9)
                    primera = actor.grab().toImage()
                    actor.establecer_tiempo(20.5)
                    actor.establecer_hablando(True, nivel=0)
                    self.assertEqual(primera, actor.grab().toImage())
                    self.assertEqual(actor.indice_fotograma(.05), actor.indice_fotograma(20.5))
                    self.assertFalse(actor._timer.isActive())

    def test_seis_casos_tienen_fondo_movimiento_y_audio_coherentes_sin_mutar_juego(self):
        esperado = {
            50: ("cafe_exterior", "calle"), 30: ("cafe", "cafe"),
            70: ("parque", "plaza"), 20: ("investigacion", "oficina"),
            60: ("cafe_lluvia", "interior_lluvia"), 80: ("noche", "noche"),
        }
        juego = Juego(4, eventos=False)
        juego.iniciar_primera_publicacion()
        visitados, fondos = set(), set()
        while not juego.finalizada:
            identificador = juego.obtener_publicacion_actual().id
            antes = copy.deepcopy(juego.datos())
            plan = copy.deepcopy([p.datos() for p in juego.publicaciones_planificadas])
            datos = escenario_actual(juego)
            with self.subTest(caso=identificador):
                self.assertEqual((datos["ambiente"], datos["sonido"]), esperado[identificador])
                ruta = (RAIZ / datos["fondo"]).resolve()
                self.assertTrue(ruta.is_relative_to(RAIZ.resolve()))
                self.assertTrue(ruta.is_file())
                self.assertFalse(QImage(str(ruta)).isNull())
                self.assertEqual(_perfil(datos["fondo"], datos["ambiente"]), datos["ambiente"])
                self.assertTrue(datos["lugar"].strip())
                for rol in ("ciudadano", "periodista"):
                    actor = self.actor(rol)
                    actor.configurar_actor(rol, datos[rol])
                    self.assertEqual(actor.expresion, datos[rol])
                with wave.open(str(RAIZ / "assets/audio/expansion/ambientes" / (datos["sonido"] + ".wav"))) as sonido:
                    self.assertEqual(sonido.getnchannels(), 2)
                    self.assertGreaterEqual(sonido.getnframes() / sonido.getframerate(), 30)
                self.assertEqual(juego.datos(), antes)
                self.assertEqual([p.datos() for p in juego.publicaciones_planificadas], plan)
                datos["sonido"] = "valor ajeno"
                self.assertEqual(escenario_actual(juego)["sonido"], esperado[identificador][1])
            visitados.add(identificador)
            fondos.add(ruta)
            juego.ejecutar_accion("verificar")
            juego.avanzar_publicacion()
        self.assertEqual(visitados, set(esperado))
        self.assertEqual(len(fondos), 6)

    def test_direccion_del_texto_elige_reaccion_y_foley_existentes_sin_alterar_partida(self):
        juego = Juego(4, eventos=False)
        juego.iniciar_primera_publicacion()
        antes = copy.deepcopy(juego.datos())
        ejemplos = {
            "Me equivoqué y le debo una explicación.": "triste",
            "Me preocupa lo que pase con el colegio.": "preocupado",
            "No basta con una captura.": "enojado",
            "Gracias; ya podemos hablar con esperanza.": "sonrisa",
            "Revisemos la fuente y su contexto.": "pensativo",
            "Llega otra notificación.": "sorprendido",
        }
        for texto, emocion in ejemplos.items():
            for rol in ("CIUDADANO", "PERIODISTA"):
                self.assertEqual(expresion_dialogo(juego, rol, texto), emocion, texto)
        for texto in ("Suena una notificación.", "Abre su libreta.", "Deja de escribir.",
                      "Sobre la mesa hay un mapa.", "Sigue el café sin probar.",
                      "La plaza empieza a vaciarse."):
            efecto = efecto_dialogo(texto)
            self.assertIsNotNone(efecto, texto)
            self.assertTrue((RAIZ / "assets/audio/expansion/efectos" / (efecto + ".wav")).is_file())
        self.assertIsNone(efecto_dialogo("La conversación continúa."))
        self.assertEqual(juego.datos(), antes)


if __name__ == "__main__":
    unittest.main()
