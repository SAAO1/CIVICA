"""Resultados y legibilidad del desenlace en el espacio real entre las barras."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QFontInfo, QPixmap
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget

from arte import FUENTE_UI
from final_ui import EscenaFin
from juego.finales import epilogo
from juego.partida import Juego
from models.jugador import Jugador
from recursos import RAIZ


class PruebasFinalElectoral(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.ventana = QWidget()
        self.ventana.juego = Juego(4, eventos=False)
        self.regresos = []
        self.ventana.volver_portada = lambda: self.regresos.append(True)
        layout = QVBoxLayout(self.ventana)
        layout.setContentsMargins(0, 0, 0, 0)
        self.escena = EscenaFin()
        layout.addWidget(self.escena)
        self.ventana.resize(1366, 638)
        self.ventana.show()

    def tearDown(self):
        self.ventana.close()
        self.ventana.deleteLater()
        self.estabilizar()

    def estabilizar(self):
        for _ in range(4):
            self.app.processEvents()

    def test_ganador_y_porcentajes_salen_de_la_partida(self):
        juego = self.ventana.juego
        juego.iniciar_primera_publicacion()
        while not juego.finalizada:
            juego.ejecutar_accion("verificar")
            juego.agregar_siguiente_publicacion()
        resultado = juego.resultado_electoral()
        self.escena.mostrar()
        self.estabilizar()
        for candidato, tarjeta in zip(juego.candidatos, self.escena.tarjetas):
            self.assertEqual(tarjeta.nombre.text(), candidato.nombre)
            self.assertEqual(tarjeta.porcentaje.text(), f"{resultado['porcentajes'][candidato.id]:.1f}%")
        ganador = next(c for c in juego.candidatos if c.nombre == resultado["ganadores"][0])
        self.assertEqual(self.escena.ganador_id, ganador.id)
        self.assertEqual(self.escena.ganador.text(), ganador.nombre)
        self.assertEqual(self.escena.texto_final.text(), epilogo(juego, resultado))
        self.assertEqual(len(self.escena.imagen_ganador.imagenes), 1)
        self.assertFalse(self.escena.imagen_ganador.imagenes[0].isNull())
        self.escena.boton_volver.click()
        self.assertEqual(self.regresos, [True])

    def test_empate_muestra_los_empatados_sin_nominalizar_electo(self):
        # Los cuatro apoyos iniciales son iguales. No debe presentarse una
        # investidura ficticia sólo para llenar el retrato grande.
        self.escena.mostrar()
        self.estabilizar()
        self.assertTrue(self.escena.eleccion["empate"])
        self.assertIsNone(self.escena.ganador_id)
        self.assertIn("EMPATE", self.escena.estado_eleccion.text())
        self.assertEqual(len(self.escena.imagen_ganador.imagenes), 4)
        for candidato in self.ventana.juego.candidatos:
            self.assertIn(candidato.nombre, self.escena.ganador.text())
        self.assertIn("empate", self.escena.texto_final.text())

    def test_cuatro_jugadores_fuente_y_controles_en_tres_resoluciones(self):
        juego = self.ventana.juego
        juego.candidatos[1].apoyo = 45
        juego.jugadores = [
            Jugador(id=f"j{i}", nombre=f"Jugador {i} con nombre largo", puntos=12*i,
                    logros=["Primera verificación", "Difusión responsable"])
            for i in range(1, 5)
        ]
        self.escena.mostrar()
        for ancho, alto in ((1100, 570), (1366, 638), (1920, 950)):
            with self.subTest(ancho=ancho, alto=alto):
                self.ventana.resize(ancho, alto)
                self.estabilizar()
                self.assertEqual(self.ventana.width(), ancho)
                self.assertEqual(self.ventana.height(), alto)
                for tarjeta in self.escena.tarjetas:
                    self.assertGreaterEqual(tarjeta.height(), 90)
                    self.assertTrue(self.escena.rect().contains(tarjeta.mapTo(self.escena, QPoint(0, 0))))
                    self.assertTrue(self.escena.rect().contains(tarjeta.mapTo(self.escena, tarjeta.rect().bottomRight())))
                boton = self.escena.boton_volver
                self.assertGreaterEqual(boton.height(), 48)
                self.assertGreater(boton.width(), boton.fontMetrics().horizontalAdvance(boton.text()) + 30)
                self.assertTrue(self.escena.rect().contains(boton.mapTo(self.escena, boton.rect().bottomRight())))
                for etiqueta in (self.escena.texto_final, self.escena.balance, self.escena.puntuaciones):
                    self.assertEqual(QFontInfo(etiqueta.font()).family(), FUENTE_UI)
                    self.assertGreaterEqual(etiqueta.font().pixelSize(), 16)
                self.assertEqual(self.escena.area_resumen.horizontalScrollBar().maximum(), 0)
                for jugador in juego.jugadores:
                    self.assertIn(jugador.nombre, self.escena.puntuaciones.text())
                # El último balance de jugador se alcanza con el desplazamiento,
                # manteniendo siempre visibles candidatos y botón de regreso.
                barra = self.escena.area_resumen.verticalScrollBar()
                barra.setValue(barra.maximum())
                self.estabilizar()
                posicion = self.escena.puntuaciones.mapTo(self.escena.area_resumen.viewport(),
                                                         self.escena.puntuaciones.rect().bottomLeft())
                self.assertLessEqual(posicion.y(), self.escena.area_resumen.viewport().height())

    def test_integrado_hud_cuatro_electos_y_empate_con_ilustraciones_reales(self):
        from interfaz import VentanaPrincipal
        with patch("configuracion.cargar", return_value={}), patch("interfaz.GestorAudio") as gestor:
            gestor.return_value.volumenes = {"general": .65, "musica": .3, "efectos": .6,
                                             "ambiente": .2, "voces": 1}
            ventana = VentanaPrincipal()
        self.addCleanup(ventana.close)
        ventana.reducir_movimiento = True
        ventana.sin_limite = True
        ventana.show()
        carpeta = RAIZ / ".tmp" / "capturas_final_nuevo"
        carpeta.mkdir(parents=True, exist_ok=True)
        for elegido in ("juan", "adrian", "laura", "camila", None):
            juego = Juego(4, eventos=False)
            juego.jugadores = [
                Jugador(id=f"j{i}", nombre=f"Jugador {i}",
                        logros=["Primera verificación", "Difusión responsable"])
                for i in range(1, 5)
            ]
            juego.iniciar_primera_publicacion()
            while not juego.finalizada:
                juego.ejecutar_accion("ignorar")
                juego.avanzar_publicacion()
            if elegido:
                next(c for c in juego.candidatos if c.id == elegido).apoyo = 70
            ventana.establecer_juego(juego)
            for ancho, alto in ((1100, 700), (1366, 768), (1920, 1080)):
                with self.subTest(electo=elegido, ancho=ancho):
                    ventana.resize(ancho, alto)
                    ventana.mostrar_escena(ventana.ESCENA_FIN)
                    self.estabilizar()
                    escena = ventana.escena_fin
                    self.assertEqual(ventana.width(), ancho)
                    self.assertEqual(ventana.height(), alto)
                    self.assertTrue(ventana.statusBar().isVisible())
                    self.assertEqual(escena.ganador_id, elegido)
                    if elegido:
                        original = QPixmap(str(RAIZ / "assets" / "expansion" / "candidatos" / f"{elegido}_electo.png"))
                        self.assertFalse(original.isNull())
                        self.assertEqual(escena.imagen_ganador.imagenes[0].toImage(), original.toImage())
                    else:
                        self.assertEqual(len(escena.imagen_ganador.imagenes), 4)
                        self.assertIn("EMPATE", escena.estado_eleccion.text())
                    for etiqueta in (escena.texto_final, escena.balance, escena.puntuaciones):
                        self.assertEqual(QFontInfo(etiqueta.font()).family(), FUENTE_UI)
                    self.assertGreaterEqual(escena.boton_volver.height(), 48)
                    self.assertTrue(escena.rect().contains(escena.boton_volver.mapTo(escena, escena.boton_volver.rect().bottomRight())))
                    self.assertEqual(escena.area_resumen.horizontalScrollBar().maximum(), 0)
                    self.assertTrue(ventana.grab().save(str(carpeta / f"{elegido or 'empate'}_{ancho}.png")))


if __name__ == "__main__":
    unittest.main()
