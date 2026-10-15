"""Regresiones de proporción visibles en las capturas Full HD del juego."""
import math
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QPointF, QRect, QRectF, Qt
from PyQt6.QtGui import QFont, QFontMetrics, QFontMetricsF, QPainter
from PyQt6.QtWidgets import QApplication

from interfaz import VentanaPrincipal
from juego.partida import Juego
from paneles import DialogoRol


RESOLUCIONES = ((1100, 700), (1366, 768), (1920, 1080))


class _PintorMedidas(QPainter):
    """Registra el dibujo real, sin mantener un segundo algoritmo de layout."""
    textos = []
    elipses = []

    def drawText(self, *args):
        if len(args) == 3 and isinstance(args[0], (QRect, QRectF)):
            caja, flags, texto = args
            self.textos.append((QRectF(caja), flags, texto, QFont(self.font())))
        elif len(args) == 6:
            x, y, ancho, alto, flags, texto = args
            self.textos.append((QRectF(x, y, ancho, alto), flags, texto, QFont(self.font())))
        return super().drawText(*args)

    def drawEllipse(self, *args):
        if len(args) == 1:
            caja = QRectF(args[0])
        elif len(args) == 3:
            centro, rx, ry = args
            caja = QRectF(centro.x() - rx, centro.y() - ry, 2 * rx, 2 * ry)
        elif len(args) == 4:
            caja = QRectF(*args)
        else:
            return super().drawEllipse(*args)
        self.elipses.append(caja)
        return super().drawEllipse(*args)


class PruebasEscalado(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def estabilizar_layout(self):
        # ResizeEvent cambia fuentes/mínimos y Qt publica un LayoutRequest
        # adicional. Medimos el resultado estable del bucle de eventos.
        for _ in range(3):
            self.app.processEvents()

    def setUp(self):
        self.preferencias = patch("configuracion.cargar", return_value={})
        self.audio = patch("interfaz.GestorAudio")
        self.preferencias.start()
        gestor = self.audio.start().return_value
        gestor.volumenes = {"general": .65, "musica": .3, "efectos": .6,
                            "ambiente": .2, "voces": 1}
        self.ventana = VentanaPrincipal()
        self.ventana.reducir_movimiento = True
        self.ventana.sin_limite = True
        self.ventana.aplicar_accesibilidad()
        self.ventana.show()
        self.estabilizar_layout()

    def tearDown(self):
        self.ventana.close()
        self.ventana.deleteLater()
        self.estabilizar_layout()
        self.audio.stop()
        self.preferencias.stop()

    def arbol(self, ids, ancho, alto):
        juego = Juego(4, eventos=False)
        publicaciones = {p.id: p for p in juego.publicaciones_planificadas}
        for id in ids:
            juego.arbol.insertar(publicaciones[id])
        self.ventana.resize(ancho, alto)
        self.ventana.establecer_juego(juego)
        self.ventana.mostrar_escena(self.ventana.ESCENA_ARBOL)
        self.estabilizar_layout()
        visualizador = self.ventana.escena_arbol.visualizador
        _PintorMedidas.textos = []
        _PintorMedidas.elipses = []
        with patch("interfaz.QPainter", _PintorMedidas):
            visualizador.grab()
        nodos = []
        for caja, flags, texto, fuente in _PintorMedidas.textos:
            if not texto.startswith("#"):
                continue
            centro = caja.center()
            circulos = [elipse for elipse in _PintorMedidas.elipses
                        if math.hypot(elipse.center().x() - centro.x(),
                                      elipse.center().y() - centro.y()) <= 2]
            self.assertTrue(circulos, f"El identificador {texto} debe quedar centrado en su nodo")
            nodo = max(circulos, key=lambda rect: rect.width())
            nodos.append((nodo, caja, flags, texto, fuente))
        self.assertEqual(len(nodos), len(ids))
        return visualizador, nodos

    def test_arbol_de_dos_nodos_usa_escala_legible_y_conexiones_cortas(self):
        for ancho, alto in RESOLUCIONES:
            with self.subTest(resolucion=(ancho, alto)):
                visualizador, nodos = self.arbol((30, 70), ancho, alto)
                a, b = [nodo[0] for nodo in nodos]
                diametro = min(a.width(), b.width())
                self.assertGreaterEqual(diametro, 80 if ancho == 1920 else 62)
                distancia = math.hypot(a.center().x() - b.center().x(),
                                       a.center().y() - b.center().y())
                self.assertGreater(distancia, diametro * 1.25)
                self.assertLessEqual(distancia, diametro * 6)
                self.assertLessEqual(distancia, visualizador.width() * .65)
                for nodo, caja, flags, texto, fuente in nodos:
                    self.assertTrue(QRectF(visualizador.rect()).contains(nodo))
                    glifos = QFontMetricsF(fuente).boundingRect(caja, flags, texto)
                    self.assertLessEqual(glifos.width(), nodo.width() - 12)
                    self.assertGreaterEqual(QFontMetricsF(fuente).height(), 22)

    def test_arbol_de_seis_nodos_cabe_sin_superposicion(self):
        for ancho, alto in RESOLUCIONES:
            with self.subTest(resolucion=(ancho, alto)):
                visualizador, nodos = self.arbol((50, 30, 70, 20, 60, 80), ancho, alto)
                circulos = [nodo[0] for nodo in nodos]
                for indice, circulo in enumerate(circulos):
                    self.assertTrue(QRectF(visualizador.rect()).contains(circulo))
                    for otro in circulos[indice + 1:]:
                        self.assertFalse(circulo.intersects(otro))

    def test_botones_arbol_tienen_proporcion_y_margen_interior(self):
        for ancho, alto in RESOLUCIONES:
            self.arbol((30, 70), ancho, alto)
            escena = self.ventana.escena_arbol
            with self.subTest(resolucion=(ancho, alto)):
                seguir = escena.boton_continuar
                self.assertLessEqual(seguir.width(), 360)
                self.assertGreaterEqual(seguir.height(), 44)
                posicion = seguir.mapTo(escena.panel, seguir.rect().topLeft())
                self.assertGreaterEqual(posicion.x(), 28)
                self.assertGreaterEqual(escena.panel.height() - posicion.y() - seguir.height(), 26)
                for boton in (escena.boton_inorden, escena.boton_preorden, escena.boton_postorden):
                    self.assertGreaterEqual(boton.height(), 44)
                    self.assertLessEqual(boton.width(), 320)

    def test_dialogo_corto_no_ocupa_un_tercio_de_pantalla_ni_pinta_rectangulo_negro(self):
        texto = "En Civitas comienzan a aparecer publicaciones polémicas."
        for ancho, alto in RESOLUCIONES:
            self.ventana.resize(ancho, alto)
            self.ventana.mostrar_escena(self.ventana.ESCENA_NARRACION_1)
            self.estabilizar_layout()
            escena = self.ventana.escena_narracion_1
            escena.finalizar_escena()
            escena.estado_escena = "esperando"
            escena.texto_completo = texto
            escena.texto_label.setText(texto)
            escena.nombre_label.setText("NARRADOR")
            for contraste in (False, True):
                with self.subTest(resolucion=(ancho, alto), alto_contraste=contraste):
                    self.ventana.alto_contraste = contraste
                    escena.actualizar_geometria()
                    etiqueta = escena.texto_label
                    self.assertLessEqual(escena.altura_franja, 220)
                    if ancho == 1920:
                        self.assertLessEqual(escena.altura_franja, escena.height() * .27)
                    self.assertIn("background:transparent", etiqueta.styleSheet().replace(" ", ""))
                    self.assertLessEqual(etiqueta.height(), etiqueta.fontMetrics().height() * 2 + 24)
                    ocupado = etiqueta.fontMetrics().boundingRect(
                        etiqueta.contentsRect(), Qt.TextFlag.TextWordWrap, texto)
                    self.assertLessEqual(ocupado.height(), etiqueta.contentsRect().height())
                    self.assertLess(etiqueta.geometry().bottom(), escena.pista_continuar.y())
                    nombre = escena.nombre_label
                    self.assertLessEqual(nombre.fontMetrics().horizontalAdvance(nombre.text()), nombre.width())
                    self.assertLessEqual(nombre.fontMetrics().height(), nombre.height())

    def test_observatorio_creciente_conserva_retratos_nombres_y_filas_compactas(self):
        for cantidad_etapas, cantidad in ((3, 13), (6, 19)):
            juego = Juego(4, eventos=False)
            juego.iniciar_primera_publicacion()
            for _ in range(cantidad_etapas - 1):
                juego.ejecutar_accion("verificar")
                juego.avanzar_publicacion()
            for ancho, alto in RESOLUCIONES:
                with self.subTest(resolucion=(ancho, alto), ciudadanos=cantidad):
                    self.ventana.resize(ancho, alto)
                    self.ventana.establecer_juego(juego)
                    self.ventana.mostrar_escena(self.ventana.ESCENA_GRAFO)
                    self.estabilizar_layout()
                    escena = self.ventana.escena_red
                    visualizador = escena.visualizador
                    for widget in (visualizador, escena.detalle, escena.boton_continuar):
                        origen = widget.mapTo(escena.panel, widget.rect().topLeft())
                        caja_panel = QRect(origen, widget.size())
                        self.assertTrue(escena.panel.rect().contains(caja_panel),
                                        f"{type(widget).__name__} debe caber dentro del panel")
                    origen_detalle = escena.detalle.mapTo(visualizador, escena.detalle.rect().topLeft())
                    self.assertGreaterEqual(origen_detalle.y(), visualizador.height())
                    _PintorMedidas.textos = []
                    _PintorMedidas.elipses = []
                    with patch("paneles.QPainter", _PintorMedidas):
                        visualizador.grab()
                    radio = visualizador.radio_nodo
                    self.assertGreaterEqual(radio, 36 if ancho == 1920 else 24 if ancho == 1366 else 20)
                    self.assertEqual(len(visualizador.posiciones), cantidad)
                    filas = sorted({round(p.y(), 2) for p in visualizador.posiciones.values()})
                    for a, b in zip(filas, filas[1:]):
                        self.assertLessEqual(b - a, radio * 6)
                    cajas = list(visualizador.cajas_nombres.values())
                    self.assertEqual(len(cajas), cantidad)
                    for indice, caja in enumerate(cajas):
                        self.assertTrue(QRectF(visualizador.rect()).contains(caja))
                        for otra in cajas[indice + 1:]:
                            self.assertFalse(caja.intersects(otra))
                    nombres = set(n.nombre for n in juego.grafo.nodos.values())
                    etiquetas = [(caja, fuente) for caja, _, texto, fuente in _PintorMedidas.textos
                                 if any(texto.startswith(nombre) for nombre in nombres)]
                    self.assertEqual(len(etiquetas), cantidad)
                    for caja, fuente in etiquetas:
                        self.assertGreaterEqual(QFontMetricsF(fuente).height(), 17 if ancho == 1920 else 14)

    def test_seleccion_de_rol_reserva_borde_para_titulo_y_boton(self):
        dialogo = DialogoRol(self.ventana)
        self.addCleanup(dialogo.close)
        dialogo.show()
        self.estabilizar_layout()
        titulo = dialogo.titulo
        self.assertGreaterEqual(titulo.x(), 40)
        self.assertGreaterEqual(titulo.y(), 40)
        self.assertLessEqual(titulo.fontMetrics().horizontalAdvance(titulo.text()), titulo.width())
        self.assertGreaterEqual(titulo.height(), titulo.fontMetrics().height())
        for tarjeta in dialogo.tarjetas.values():
            self.assertGreater(tarjeta.y(), titulo.geometry().bottom() + 24)


if __name__ == "__main__":
    unittest.main()
