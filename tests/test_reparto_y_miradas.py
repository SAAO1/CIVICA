"""El reparto conserva su plano al terminar las entradas y redimensionar."""
import os
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import QAbstractAnimation
from PyQt6.QtGui import QImage
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from juego.lectura import BibliotecaLectura
from juego.partida import Juego
from juego.cinematica_personajes_extendida import CINEMATICAS_PERSONAJES_EXTENDIDAS
from herramientas.verificar_acciones_ui_real import comprobar_etiqueta
from personajes_animados import ACTORES_NUEVOS, MIRADAS_ORIGINALES, SpriteExpresivo
from test_balance_roles_ui import AudioConSenales, crear_ventana


class RepartoYMiradasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.parches = [patch("configuracion.cargar", return_value={}),
                         patch("interfaz.GestorAudio", AudioConSenales),
                         patch("interfaz.BibliotecaLectura", lambda: BibliotecaLectura(None)),
                         patch("cinematica_narrativa.CapaCinematica._reproducir_si_corresponde")]
        for parche in self.parches:
            parche.start()
        self.ventana = crear_ventana()
        self.ventana.reducir_movimiento = False
        self.ventana.animar_personajes = True
        self.ventana.aplicar_accesibilidad()
        self.escena = self.ventana.escena_dialogo
        self.ventana.escenas.setCurrentWidget(self.escena)
        self.escena.fondo = "assets/expansion/siete_actos/fondos/estudio.jpg"
        self.escena.estado_escena = "dialogo"
        self.escena.texto_completo = "Una conversación con espacio para escuchar."
        self.reparto = {"CIUDADANO", "PERIODISTA"} | {n.upper() for n in ACTORES_NUEVOS}
        self.app.processEvents()
        self.escena.mostrar_fondo()

    def tearDown(self):
        self.ventana.close()
        self.ventana.deleteLater()
        self.app.processEvents()
        for parche in reversed(self.parches):
            parche.stop()

    def comprobar_solo(self, nombre):
        self.assertEqual(self.escena.personajes_activos, {nombre})
        for clave, actor in self.escena.personajes.items():
            self.assertEqual(actor.isVisible(), clave == nombre, clave)
            if clave != nombre:
                for animacion in (actor.animacion_entrada, actor.animacion_salida,
                                  actor.animacion_dim, actor.animacion_fade):
                    if animacion is not None:
                        self.assertNotEqual(animacion.state(), QAbstractAnimation.State.Running)
        actor = self.escena.personajes[nombre]
        self.assertGreaterEqual(actor.geometry().left(), self.escena.width()*.64)
        self.assertLessEqual(actor.geometry().right(), self.escena.width())
        self.assertLessEqual(actor.width(), self.escena.width()*.33)
        self.assertEqual(actor.imagen.direccion_mirada, "izquierda")
        self.assertEqual(actor.imagen_oscura.direccion_mirada, "izquierda")

    def esperar_entrada(self, nombre):
        limite = time.monotonic() + 4
        entrada = self.escena.personajes[nombre].animacion_entrada
        while entrada.state() == QAbstractAnimation.State.Running and time.monotonic() < limite:
            QTest.qWait(40)
        self.assertNotEqual(entrada.state(), QAbstractAnimation.State.Running)

    def test_cinco_invitados_solos_en_esquina_con_entradas_reales_a_tres_tamanos(self):
        for ancho, alto in ((1100, 700), (1366, 768), (1920, 1080)):
            self.ventana.resize(ancho, alto)
            self.app.processEvents()
            for nombre in sorted(ACTORES_NUEVOS):
                nombre = nombre.upper()
                with self.subTest(resolucion=(ancho, alto), personaje=nombre):
                    self.escena.configurar_personajes_para_hablante(nombre, self.reparto)
                    self.comprobar_solo(nombre)
                    self.esperar_entrada(nombre)
                    self.comprobar_solo(nombre)
                    actor = self.escena.personajes[nombre]
                    self.assertEqual(actor.geometry(), actor._encuadre_objetivo)

    def test_resize_durante_entrada_y_cambio_de_hablante_no_restauran_posicion_vieja(self):
        self.ventana.resize(1100, 700)
        self.app.processEvents()
        self.escena.configurar_personajes_para_hablante("INFLUENCER", self.reparto)
        QTest.qWait(170)
        self.ventana.resize(1920, 1080)
        self.app.processEvents()
        QTest.qWait(730)
        self.comprobar_solo("INFLUENCER")
        invitada = self.escena.personajes["INFLUENCER"]
        self.assertEqual(invitada.geometry(), invitada._encuadre_objetivo)
        self.escena.configurar_personajes_para_hablante("CAMILA", self.reparto)
        QTest.qWait(60)
        self.escena.configurar_personajes_para_hablante("PERIODISTA", self.reparto)
        QTest.qWait(900)
        self.assertEqual(self.escena.personajes_activos, {"CIUDADANO", "PERIODISTA"})
        ciudadano, periodista = (self.escena.personajes[n] for n in ("CIUDADANO", "PERIODISTA"))
        self.assertLess(ciudadano.geometry().right(), periodista.geometry().left())
        self.assertEqual(ciudadano.imagen.direccion_mirada, "derecha")
        self.assertEqual(periodista.imagen.direccion_mirada, "izquierda")
        self.assertTrue(ciudadano.isVisible() and periodista.isVisible())
        self.assertTrue(all(not actor.isVisible() for n, actor in self.escena.personajes.items()
                            if n.lower() in ACTORES_NUEVOS))

    def test_narrador_no_arrastra_al_ultimo_invitado(self):
        self.escena.configurar_personajes_para_hablante("INFLUENCER", self.reparto)
        self.escena.configurar_personajes_para_hablante("NARRADOR")
        self.assertFalse(self.escena.personajes_activos)
        self.assertTrue(all(not actor.isVisible() for actor in self.escena.personajes.values()))

    def test_titulos_del_barrio_y_opciones_de_ambos_roles_caben_a_tres_tamanos(self):
        for rol in ("ciudadano", "periodista"):
            juego = Juego(7, eventos=False)
            juego.seleccionar_rol(rol)
            juego.iniciar_primera_publicacion()
            self.ventana.establecer_juego(juego)
            self.ventana.mostrar_escena(self.ventana.ESCENA_ACCION)
            escena = self.ventana.escena_accion
            escena.timer_decision.stop()
            for ancho, alto in ((1100, 700), (1366, 768), (1920, 1080)):
                self.ventana.resize(ancho, alto)
                self.app.processEvents()
                for clave, boton in escena.botones_por_accion.items():
                    with self.subTest(rol=rol, accion=clave, ancho=ancho):
                        self.assertTrue(comprobar_etiqueta(boton, clave)["sin_recorte"])

    def test_cortes_de_personaje_seleccionan_su_frase_sin_imponer_bloqueo_de_accion(self):
        juego = Juego(7, eventos=False, campana="extendida")
        juego.iniciar_primera_publicacion()
        self.ventana.juego = juego
        while juego.publicacion_actual_id is not None:
            entradas = [(clave, datos) for clave, datos in CINEMATICAS_PERSONAJES_EXTENDIDAS.items()
                        if datos["publicacion"] == juego.publicacion_actual_id]
            for clave, datos in entradas:
                with self.subTest(clave=clave):
                    self.escena.configurar_personajes_para_hablante(datos["nombre"], self.reparto)
                    with patch.object(self.escena.cine_narrativo, "iniciar", return_value=True) as iniciar:
                        self.escena.preparar_puesta_audiovisual(datos["texto"], datos["nombre"])
                    iniciar.assert_called_once_with(clave, reproducir=False)
                    self.assertEqual(self.escena._clave_preparada, clave)
                    self.assertFalse(self.escena.personajes_activos)
                    self.assertTrue(all(not p.isVisible() for p in self.escena.personajes.values()))
                    self.assertFalse(self.escena.corte_accion_pendiente())
            juego.ejecutar_accion("compartir")
            if not juego.avanzar_publicacion():
                break

    def test_espejo_real_conserva_boca_y_sombra_para_cada_personaje(self):
        for rol in MIRADAS_ORIGINALES:
            for sombra in (False, True):
                actor = SpriteExpresivo(sombra=sombra)
                try:
                    actor.resize(280, 400)
                    actor.configurar_actor(rol)
                    actor.configurar_movimiento(reducir=True)
                    actor.orientar_hacia(MIRADAS_ORIGINALES[rol])
                    actor.show()
                    original = actor.grab().toImage()
                    otra = "izquierda" if MIRADAS_ORIGINALES[rol] == "derecha" else "derecha"
                    actor.orientar_hacia(otra)
                    self.assertTrue(actor.espejado)
                    resultado = actor.grab().toImage().convertToFormat(QImage.Format.Format_RGBA8888)
                    espejo = original.mirrored(True, False).convertToFormat(QImage.Format.Format_RGBA8888)
                    datos = resultado.constBits().asstring(resultado.sizeInBytes())
                    esperados = espejo.constBits().asstring(espejo.sizeInBytes())
                    # QPainter puede redondear un borde subpíxel al invertir la
                    # transformación; el encuadre y la figura deben coincidir.
                    error = sum(abs(a-b) for a, b in zip(datos, esperados))/len(datos)
                    self.assertLess(error, 1.0, rol)
                    self.assertNotEqual(resultado, original, rol)
                    actor.configurar_actor(rol, "pensativo")
                    actor.establecer_hablando(True, .8)
                    self.assertEqual(actor.direccion_mirada, otra)
                    self.assertTrue(actor.espejado)
                finally:
                    actor.close()
                    actor.deleteLater()


if __name__ == "__main__":
    unittest.main()
