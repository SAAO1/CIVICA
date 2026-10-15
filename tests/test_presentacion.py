import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import QAbstractAnimation, QRect, QRectF, Qt
from PyQt6.QtGui import QFont, QFontMetrics, QFontMetricsF, QPainter
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from interfaz import VentanaPrincipal
from juego.historia import contenido_resultado, dialogos_publicacion
from juego.partida import Juego


class PruebasPresentacion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.parche_preferencias = patch("configuracion.cargar", return_value={})
        self.parche_audio = patch("interfaz.GestorAudio")
        self.parche_preferencias.start()
        self.audio = self.parche_audio.start().return_value
        self.audio.volumenes = {"general": .65, "musica": .3, "efectos": .6,
                               "ambiente": .2, "voces": 1.0}
        self.ventana = VentanaPrincipal()
        self.ventana.reducir_movimiento = True
        self.ventana.aplicar_accesibilidad()
        self.ventana.resize(1366, 768)
        self.ventana.show()
        self.app.processEvents()

    def tearDown(self):
        self.ventana.close()
        self.ventana.deleteLater()
        self.app.processEvents()
        self.parche_audio.stop()
        self.parche_preferencias.stop()

    def test_controles_de_partida_aparecen_al_jugar_y_desaparecen_en_portada(self):
        v = self.ventana
        self.assertFalse(v.accion_menu_partida.isVisible())
        self.assertFalse(v.menu_partida.isVisible())
        self.assertFalse(v.statusBar().isVisible())
        self.assertTrue(v.boton_configuracion.isVisible())
        for ancho, alto in ((1100, 700), (1366, 768), (1920, 1080)):
            with self.subTest(resolucion=(ancho, alto)):
                v.resize(ancho, alto)
                v.mostrar_escena(v.ESCENA_NARRACION_1)
                self.app.processEvents()
                self.assertTrue(v.menu_partida.isVisible())
                self.assertTrue(v.statusBar().isVisible())
                self.assertTrue(v.hud.isVisible())
                self.assertFalse(v.acciones_partida["reconectar"].isVisible())
                for boton in (v.menu_partida, v.boton_configuracion):
                    self.assertTrue(v.barra.rect().contains(boton.geometry()))
                texto_config = v.boton_configuracion.fontMetrics().horizontalAdvance("Configuración")
                self.assertGreaterEqual(v.boton_configuracion.width(), texto_config + 26 + 34)
        v.mostrar_escena(v.ESCENA_FIN)
        self.assertTrue(v.statusBar().isVisible())
        v.volver_portada()
        self.app.processEvents()
        self.assertFalse(v.menu_partida.isVisible())
        self.assertFalse(v.statusBar().isVisible())
        self.assertTrue(v.boton_configuracion.isVisible())

    def test_todos_los_dialogos_actuales_caben_en_tres_resoluciones(self):
        contenidos = set()
        for accion in ("compartir", "verificar", "ignorar", "reportar"):
            juego = Juego(4, eventos=False)
            juego.iniciar_primera_publicacion()
            while juego.obtener_publicacion_actual() is not None:
                contenidos.update(dialogos_publicacion(juego))
                juego.ejecutar_accion(accion)
                for tipo in (1, 2, 3):
                    texto, nombre = contenido_resultado(juego, tipo)
                    contenidos.add((nombre, texto))
                juego.avanzar_publicacion()
        self.assertGreater(len(contenidos), 35)
        v = self.ventana
        v.juego.iniciar_primera_publicacion()
        v.mostrar_escena(v.ESCENA_DIALOGO)
        escena = v.escena_dialogo
        escena.finalizar_escena()
        for ancho, alto in ((1100, 700), (1366, 768), (1920, 1080)):
            v.resize(ancho, alto)
            self.app.processEvents()
            for nombre, texto in contenidos:
                with self.subTest(resolucion=(ancho, alto), texto=texto):
                    escena.estado_escena = "esperando"
                    escena.texto_completo = texto
                    escena.texto_label.setText(texto)
                    escena.nombre_label.setText(nombre)
                    escena.actualizar_geometria()
                    etiqueta = escena.texto_label
                    caja = etiqueta.contentsRect()
                    ocupado = QFontMetrics(etiqueta.font()).boundingRect(
                        QRect(0, 0, caja.width(), 2000), Qt.TextFlag.TextWordWrap, texto)
                    self.assertLessEqual(ocupado.height(), caja.height())
                    self.assertLessEqual(ocupado.width(), caja.width())
                    self.assertTrue(escena.franja_inferior.geometry().contains(etiqueta.geometry()))
                    # QLabel centra verticalmente los glifos en su caja.
                    final_texto = etiqueta.y() + (caja.height() + ocupado.height()) // 2
                    self.assertLess(final_texto, escena.pista_continuar.y())
                    nombre_ancho = escena.nombre_label.fontMetrics().horizontalAdvance(nombre)
                    self.assertLessEqual(nombre_ancho, escena.nombre_label.contentsRect().width())
                    self.assertGreaterEqual(etiqueta.font().pixelSize(), 24)

    def test_telefono_y_decision_muestran_la_publicacion_actual(self):
        v = self.ventana
        juego = Juego(4, eventos=False)
        juego.iniciar_primera_publicacion()
        v.establecer_juego(juego)
        ids = []
        while juego.obtener_publicacion_actual() is not None:
            publicacion = juego.obtener_publicacion_actual()
            ids.append(publicacion.id)
            v.mostrar_escena(v.ESCENA_NARRACION_3)
            v.escena_narracion_3.timer_inicio.stop()
            telefono = v.escena_narracion_3.publicacion_telefono
            self.assertIs(telefono.publicacion, publicacion)
            self.assertIn(publicacion.texto, telefono.accessibleName())
            self.assertEqual(telefono.autor, juego.grafo.nodos[publicacion.emisor_id].nombre)
            v.mostrar_escena(v.ESCENA_ACCION)
            tarjeta = v.escena_accion.tarjeta_publicacion
            self.assertIs(tarjeta.publicacion, publicacion)
            self.assertIn(publicacion.texto, tarjeta.accessibleName())
            self.assertEqual(tarjeta.autor, telefono.autor)
            juego.ejecutar_accion("verificar")
            juego.avanzar_publicacion()
        self.assertEqual(ids, [50, 30, 70, 20, 60, 80])

    def test_textos_pintados_del_feed_quedan_completos_dentro_del_post(self):
        dibujos = []

        class PintorTexto(QPainter):
            def drawText(self, caja, flags, texto):
                dibujos.append((QRectF(caja), flags, texto, QFont(self.font())))
                return super().drawText(caja, flags, texto)

        v = self.ventana
        v.juego.iniciar_primera_publicacion()
        for ancho, alto in ((1100, 700), (1366, 768), (1920, 1080)):
            v.resize(ancho, alto)
            for indice, obtener_tarjeta in (
                    (v.ESCENA_NARRACION_3, lambda: v.escena_narracion_3.publicacion_telefono),
                    (v.ESCENA_ACCION, lambda: v.escena_accion.tarjeta_publicacion)):
                v.mostrar_escena(indice)
                v.escena_narracion_3.timer_inicio.stop()
                self.app.processEvents()
                tarjeta = obtener_tarjeta()
                dibujos.clear()
                with patch("publicaciones_ui.QPainter", PintorTexto):
                    self.assertFalse(tarjeta.grab().isNull())
                self.assertTrue(dibujos)
                for caja, flags, texto, fuente in dibujos:
                    with self.subTest(resolucion=(ancho, alto), telefono=tarjeta.telefono, texto=texto):
                        self.assertGreaterEqual(caja.top(), 0)
                        self.assertLessEqual(caja.bottom(), tarjeta.height() + 1)
                        self.assertGreaterEqual(caja.left(), 0)
                        self.assertLessEqual(caja.right(), tarjeta.width() + 1)
                        metricas = QFontMetricsF(fuente)
                        ocupado = metricas.boundingRect(caja, flags, texto)
                        self.assertLessEqual(ocupado.height(), caja.height() + 1)
                        if not flags & Qt.TextFlag.TextWordWrap:
                            self.assertLessEqual(metricas.horizontalAdvance(texto), caja.width() + 1)

    def test_escritura_revela_un_caracter_y_pausa_ante_puntuacion(self):
        v = self.ventana
        v.juego.iniciar_primera_publicacion()
        v.mostrar_escena(v.ESCENA_DIALOGO)
        escena = v.escena_dialogo
        escena.timer_inicio.stop()
        escena.iniciar_dialogo("A, b. C", "NARRADOR")
        escena.animacion.setCurrentTime(escena.animacion.duration())
        escena.timer_texto.stop()
        escena.escribir_caracter()
        self.assertEqual(escena.texto_label.text(), "A")
        ritmo = escena.timer_texto.interval()
        self.assertGreaterEqual(ritmo, 30)
        escena.escribir_caracter()
        self.assertEqual(escena.texto_label.text(), "A,")
        self.assertGreater(escena.timer_texto.interval(), ritmo * 2)
        for _ in range(3):
            escena.escribir_caracter()
        self.assertEqual(escena.texto_label.text(), "A, b.")
        self.assertGreater(escena.timer_texto.interval(), ritmo * 4)
        escena.avanzar()
        self.assertEqual(escena.texto_label.text(), "A, b. C")
        self.assertFalse(escena.escribiendo)
        self.assertEqual(escena.dialogo_actual, 0)

    def test_fundido_se_cancela_al_volver_y_con_movimiento_reducido(self):
        v = self.ventana
        v.reducir_movimiento = False
        v.aplicar_accesibilidad()
        v.mostrar_escena(v.ESCENA_NARRACION_1)
        self.assertTrue(v.velo_transicion.isVisible())
        self.assertEqual(v.animacion_transicion.state(), QAbstractAnimation.State.Running)
        self.assertGreaterEqual(v.animacion_transicion.duration(), 1000)
        v.animacion_transicion.setCurrentTime(v.animacion_transicion.duration() // 2)
        self.assertGreater(v.efecto_transicion.opacity(), 0)
        self.assertLess(v.efecto_transicion.opacity(), 1)
        v.mostrar_escena(v.ESCENA_INICIO)
        self.assertFalse(v.velo_transicion.isVisible())
        self.assertEqual(v.animacion_transicion.state(), QAbstractAnimation.State.Stopped)
        v.mostrar_escena(v.ESCENA_NARRACION_1)
        v.reducir_movimiento = True
        v.aplicar_accesibilidad()
        self.assertFalse(v.velo_transicion.isVisible())
        self.assertEqual(v.animacion_transicion.state(), QAbstractAnimation.State.Stopped)

    def test_voces_reciben_dialogo_completo_y_hablante_y_se_detienen_al_salir(self):
        v = self.ventana
        v.juego.iniciar_primera_publicacion()
        v.mostrar_escena(v.ESCENA_DIALOGO)
        escena = v.escena_dialogo
        escena.timer_inicio.stop()
        for nombre in ("NARRADOR", "CIUDADANO", "PERIODISTA"):
            with self.subTest(hablante=nombre):
                self.audio.narrar.reset_mock()
                texto = f"Un diálogo completo de {nombre.lower()}, con una pausa."
                escena.iniciar_dialogo(texto, nombre)
                escena.animacion.setCurrentTime(escena.animacion.duration())
                escena.timer_texto.stop()
                self.audio.narrar.assert_called_once_with(texto, nombre)
                escena.avanzar()
                self.audio.narrar.assert_called_once_with(texto, nombre)
                self.audio.detener_voz.reset_mock()
                escena.finalizar_escena()
                self.audio.detener_voz.assert_called_once()
                self.assertFalse(escena.timer_texto.isActive())


if __name__ == "__main__":
    unittest.main()
