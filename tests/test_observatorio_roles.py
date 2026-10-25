"""Los contactos del oficio se ven como aristas reales, sin repetir decisiones."""
import copy
import hashlib
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import QCoreApplication, QEvent, QRect, QRectF, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget, QTextBrowser

from juego.acciones import acciones_para_rol
from juego.partida import Juego
from paneles import DialogoRol, EscenaRed, mostrar_ayuda


def huella(imagen):
    return hashlib.sha256(imagen.constBits().asstring(imagen.sizeInBytes())).hexdigest()


class PruebasObservatorioRoles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.ventanas = []

    def tearDown(self):
        for ventana in self.ventanas:
            ventana.close()
            ventana.deleteLater()
        self.app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def crear(self, accion="conversar", rol="ciudadano", origen="ana", reducir=True, preparar=None):
        juego = Juego(4, eventos=False)
        juego.seleccionar_rol(rol)
        juego.jugador.ciudadano_id = origen
        juego.iniciar_primera_publicacion()
        if preparar is not None:
            preparar(juego)
        aristas_antes = set(juego.grafo.aristas())
        self.assertTrue(juego.ejecutar_accion(accion))
        ventana = QWidget()
        self.ventanas.append(ventana)
        ventana.reducir_movimiento = reducir
        ventana.resize(1366, 768)
        layout = QVBoxLayout(ventana)
        layout.setContentsMargins(0, 0, 0, 0)
        escena = EscenaRed(juego, ventana)
        layout.addWidget(escena)
        ventana.show()
        self.app.processEvents()
        escena.mostrar()
        self.app.processEvents()
        return juego, ventana, escena, aristas_antes

    def test_conversacion_resalta_exactamente_las_aristas_creadas_y_sus_participantes(self):
        juego, ventana, escena, anteriores = self.crear()
        visual = escena.visualizador
        nuevas = set(juego.grafo.aristas())-anteriores
        self.assertEqual(visual.conexiones_nuevas, nuevas)
        self.assertTrue(nuevas)
        vecino = juego.ultimo_registro["efectos_red"]["vecino_id"]
        self.assertEqual(visual.focos_contacto, {"ana", vecino})
        self.assertEqual(visual.visitados, visual.focos_contacto)
        self.assertEqual(visual.tipo, "vinculo")
        self.assertIn("Escuchar al vecindario", escena.resumen.text())
        self.assertIn("no se difundió", escena.detalle.text())
        self.assertFalse(escena.timer.isActive())
        self.assertFalse(visual.timer_contacto.isActive())
        con_vinculo = huella(visual.grab().toImage())
        visual.conexiones_nuevas.clear()
        sin_vinculo = huella(visual.grab().toImage())
        self.assertNotEqual(con_vinculo, sin_vinculo, "El vínculo debe cambiar la pintura real del grafo")

    def test_entrevista_muestra_su_fuente_sin_convertirla_en_hecho_verificado(self):
        juego, ventana, escena, anteriores = self.crear("entrevistar", "periodista", "maria")
        self.assertEqual(escena.visualizador.conexiones_nuevas, set(juego.grafo.aristas())-anteriores)
        self.assertEqual(escena.visualizador.etiquetas_contacto["ana"], "FUENTE")
        self.assertEqual(escena.visualizador.focos_contacto, {"maria", "ana"})
        self.assertEqual(escena.visualizador.tipo, "entrevista")
        self.assertIn("Entrevistar a una fuente", escena.resumen.text())
        self.assertIn("pendiente de contraste", escena.detalle.text())
        self.assertNotIn("Ignorar", escena.resumen.text())
        self.assertEqual(juego.info_verificada, 0)

    def test_ignorar_y_reservar_no_se_presentan_como_una_conversacion(self):
        for accion, rol, fragmento in (("ignorar", "ciudadano", "sin reenviar"),
                                       ("reservar", "periodista", "reserva")):
            with self.subTest(accion=accion):
                juego, ventana, escena, anteriores = self.crear(accion, rol)
                self.assertFalse(escena.visualizador.conexiones_nuevas)
                self.assertFalse(escena.visualizador.focos_contacto)
                self.assertEqual(set(juego.grafo.aristas()), anteriores)
                self.assertIn(fragmento, escena.detalle.text())
                self.assertIn("Sin difusión", escena.leyenda.text())
                self.assertNotIn("vecindario", escena.resumen.text())

    def test_comparacion_muestra_el_cambio_de_alcance_real_sin_modificar_la_partida(self):
        juego, ventana, escena, anteriores = self.crear()
        antes = copy.deepcopy(juego.datos())
        grafo_sin_contacto = copy.deepcopy(juego.grafo)
        for a, b in escena.visualizador.conexiones_nuevas:
            grafo_sin_contacto.eliminar_arista(a, b)
        origen = escena.origen.currentData()
        esperado_sin = len(grafo_sin_contacto.bfs(origen, 2).orden)-1
        esperado_con = len(juego.grafo.bfs(origen, 2).orden)-1
        self.assertGreater(esperado_con, esperado_sin)
        for _ in range(3):
            escena.comparar()
            self.assertEqual(escena.comparacion_alcances,
                             {"sin_conexiones": esperado_sin, "con_conexiones": esperado_con})
            self.assertEqual(escena.visualizador.visitados, set(juego.grafo.bfs(origen, 2).orden))
            self.assertIn("Simulación sin aplicar puntos", escena.resumen.text())
            self.assertEqual(juego.datos(), antes)
        for tipo in ("bfs", "dfs"):
            escena.recorrer(tipo)
        escena.mostrar()
        escena.consultar(origen)
        self.assertEqual(juego.datos(), antes)

    def test_la_animacion_se_detiene_oculta_minimizada_y_con_movimiento_reducido(self):
        juego, ventana, escena, anteriores = self.crear(reducir=False)
        visual = escena.visualizador
        self.assertTrue(visual.timer_contacto.isActive())
        QTest.qWait(85)
        self.assertGreater(visual.progreso_contacto, 0)
        ventana.showMinimized()
        self.app.processEvents()
        self.assertFalse(visual.timer_contacto.isActive())
        detenido = visual.progreso_contacto
        QTest.qWait(80)
        self.assertEqual(visual.progreso_contacto, detenido)
        ventana.showNormal()
        self.app.processEvents()
        self.assertTrue(visual.timer_contacto.isActive())
        ventana.reducir_movimiento = True
        visual.grab()
        self.assertFalse(visual.timer_contacto.isActive())
        self.assertEqual(visual.progreso_contacto, 1)
        escena.hide()
        self.assertFalse(visual.timer_contacto.isActive())
        self.assertFalse(escena.timer.isActive())

    def test_una_entrevista_sin_aristas_nuevas_no_inventa_un_enlace(self):
        def conectar(juego):
            juego.grafo.agregar_arista("maria", "ana")
            juego.grafo.agregar_arista("ana", "maria")
        juego, ventana, escena, anteriores = self.crear("entrevistar", "periodista", "maria", preparar=conectar)
        self.assertEqual(juego.ultimo_registro["efectos_red"]["fuente_id"], "ana")
        self.assertTrue(escena.visualizador.focos_contacto)
        self.assertEqual(escena.visualizador.conexiones_nuevas, set(juego.grafo.aristas())-anteriores)
        self.assertFalse(escena.visualizador.conexiones_nuevas)
        self.assertIn("Contacto ya existente", escena.detalle.text())
        escena.completar()
        self.assertIn("Contacto completo", escena.estado_reproduccion.text())

    def test_geometria_de_contactos_en_tres_resoluciones(self):
        juego, ventana, escena, anteriores = self.crear()
        for ancho, alto in ((1100, 620), (1366, 688), (1920, 980)):
            with self.subTest(resolucion=(ancho, alto)):
                ventana.resize(ancho, alto)
                for _ in range(3):
                    self.app.processEvents()
                visual = escena.visualizador
                visual.grab()
                self.assertEqual(len(visual.posiciones), len(juego.grafo.nodos))
                for widget in (visual, escena.detalle, escena.boton_continuar):
                    origen = widget.mapTo(escena.panel, widget.rect().topLeft())
                    self.assertTrue(escena.panel.rect().contains(QRect(origen, widget.size())))
                for caja in visual.cajas_nombres.values():
                    self.assertTrue(QRectF(visual.rect()).contains(caja))
                ocupada = escena.detalle.fontMetrics().boundingRect(
                    escena.detalle.contentsRect(), Qt.TextFlag.TextWordWrap, escena.detalle.text())
                self.assertLessEqual(ocupada.height(), escena.detalle.height())

    def test_manual_y_selector_describen_las_ocho_acciones_actuales(self):
        juego, ventana, escena, anteriores = self.crear()
        with patch("paneles.DialogoIlustrado.exec", return_value=0):
            mostrar_ayuda(ventana)
        navegador = ventana.findChildren(QTextBrowser)[-1]
        manual = navegador.toPlainText()
        self.assertNotIn("bonificación al verificar", manual)
        self.assertIn("periodista mantiene la información en reserva", manual.replace("\n", " "))
        selector = DialogoRol(ventana)
        for rol in ("ciudadano", "periodista"):
            selector.roles.setCurrentIndex(selector.roles.findData(rol))
            for accion in acciones_para_rol(rol):
                self.assertIn(accion["titulo"], manual)
                self.assertIn(accion["titulo"], selector.detalle.toolTip())


if __name__ == "__main__":
    unittest.main()
