import json
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtGui import QFont, QFontInfo, QRawFont
from PyQt6.QtWidgets import QApplication

import arte
from juego.partida import Juego
from juego.red_social import ampliar_comunidad, crear_red_social
from paneles import EscenaRed


def estado_serializado(juego):
    """Congela también los registros anidados para detectar mutaciones reales."""
    return json.dumps(juego.datos(), ensure_ascii=False, sort_keys=True)


class PruebasComunidadProgresiva(unittest.TestCase):
    def test_crece_de_nueve_a_diecinueve_sin_aislar_nuevos(self):
        juego = Juego(4, eventos=False)
        self.assertEqual(juego.grafo.cantidad_vertices(), 9)
        self.assertEqual(juego.ciudadanos_nuevos, [])
        self.assertTrue(juego.iniciar_primera_publicacion())
        conocidos = set(juego.grafo.nodos)
        for etapa, cantidad in enumerate((9, 11, 13, 15, 17, 19), start=1):
            with self.subTest(etapa=etapa):
                self.assertEqual(juego.grafo.cantidad_vertices(), cantidad)
                nuevos = juego.ciudadanos_nuevos
                self.assertEqual(len(nuevos), 0 if etapa == 1 else 2)
                self.assertEqual(set(nuevos), set(juego.grafo.nodos) - conocidos)
                alcanzables = juego.grafo.bfs("ana").orden
                for id in nuevos:
                    self.assertGreater(juego.grafo.grado_entrada(id), 0)
                    self.assertGreater(juego.grafo.grado_salida(id), 0)
                    self.assertIn(id, alcanzables)
                conocidos.update(nuevos)
                self.assertEqual(len(juego.grafo.aristas()), len(set(juego.grafo.aristas())))
                self.assertTrue(juego.ejecutar_accion("verificar"))
                self.assertEqual(juego.avanzar_publicacion(), etapa < 6)
        self.assertTrue(juego.finalizada)
        self.assertEqual(len(conocidos), 19)
        self.assertFalse(juego.avanzar_publicacion())
        self.assertEqual(juego.grafo.cantidad_vertices(), 19)

    def test_ampliacion_reproducible_y_repetir_etapas_no_duplica(self):
        a, b = crear_red_social(), crear_red_social()
        for etapa in (-1, 0, 1):
            self.assertEqual(ampliar_comunidad(a, etapa), [])
            self.assertEqual(a.cantidad_vertices(), 9)
        for etapa in range(2, 7):
            self.assertEqual(ampliar_comunidad(a, etapa), ampliar_comunidad(b, etapa))
            self.assertEqual(list(a.nodos), list(b.nodos))
            self.assertEqual(a.aristas(), b.aristas())
            nodos, aristas = list(a.nodos), a.aristas()
            self.assertEqual(ampliar_comunidad(a, etapa), [])
            self.assertEqual(ampliar_comunidad(a, etapa - 1), [])
            self.assertEqual(list(a.nodos), nodos)
            self.assertEqual(a.aristas(), aristas)
        self.assertEqual(ampliar_comunidad(a, 100), [])
        self.assertEqual(a.cantidad_vertices(), 19)

    def test_guardar_cargar_conserva_crecimiento_y_continua_la_misma_partida(self):
        juego = Juego(18, eventos=True)
        juego.iniciar_primera_publicacion()
        for _ in range(3):
            juego.ejecutar_accion("verificar")
            juego.avanzar_publicacion()
        self.assertEqual(juego.grafo.cantidad_vertices(), 15)
        self.assertEqual(len(juego.ciudadanos_nuevos), 2)
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "comunidad.json"
            juego.guardar(ruta)
            copia = Juego.cargar(ruta)
        self.assertEqual(estado_serializado(juego), estado_serializado(copia))
        while juego.obtener_publicacion_actual() is not None:
            for partida in (juego, copia):
                self.assertTrue(partida.ejecutar_accion("verificar"))
            self.assertEqual(juego.avanzar_publicacion(), copia.avanzar_publicacion())
            self.assertEqual(estado_serializado(juego), estado_serializado(copia))
        self.assertTrue(copia.finalizada)
        self.assertEqual(copia.grafo.cantidad_vertices(), 19)


class PruebasExperienciaVisual(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def crear_observatorio(self):
        juego = Juego(4, eventos=False)
        juego.iniciar_primera_publicacion()
        for _ in range(2):
            juego.ejecutar_accion("verificar")
            juego.avanzar_publicacion()
        juego.ejecutar_accion("compartir")
        escena = EscenaRed(juego)
        escena.reducir_movimiento = True
        escena.resize(1366, 768)
        self.addCleanup(escena.close)
        self.addCleanup(escena.finalizar_escena)
        return juego, escena

    def test_reabrir_y_refrescar_observatorio_no_crea_ciudadanos(self):
        juego, escena = self.crear_observatorio()
        antes = estado_serializado(juego)
        for _ in range(3):
            escena.show()
            escena.mostrar()
            escena.rellenar()
            self.app.processEvents()
            self.assertEqual(escena.origen.count(), 13)
            self.assertEqual(escena.visualizador.nuevos, set(juego.ciudadanos_nuevos))
            escena.hide()
        self.assertEqual(estado_serializado(juego), antes)

    def test_comparar_desde_nuevos_origenes_no_altera_puntos_ni_historial(self):
        juego, escena = self.crear_observatorio()
        antes = estado_serializado(juego)
        propagacion = juego.ultima_propagacion
        puntos = juego.jugador.puntos
        for origen in ("ana", *juego.ciudadanos_nuevos):
            with self.subTest(origen=origen):
                escena.origen.setCurrentIndex(escena.origen.findData(origen))
                escena.comparar()
                self.assertIn(origen, escena.visualizador.visitados)
                self.assertIn("Simulación sin aplicar puntos", escena.resumen.text())
                self.assertEqual(juego.jugador.puntos, puntos)
                self.assertIs(juego.ultima_propagacion, propagacion)
                self.assertEqual(estado_serializado(juego), antes)

    def test_fuente_portatil_carga_y_cubre_textos_en_espanol(self):
        familias = arte.cargar_tipografias()
        empaquetadas = {nombre: familia for nombre, familia in familias.items()
                       if nombre.startswith("AtkinsonHyperlegible-")}
        self.assertEqual(len(empaquetadas), 4)
        self.assertTrue(all(arte.FUENTE_UI in familia for familia in empaquetadas.values()))
        self.assertTrue((arte.RAIZ_FUENTES / "OFL.txt").is_file())
        fuente = QFont(arte.FUENTE_UI, 18)
        self.assertEqual(QFontInfo(fuente).family(), arte.FUENTE_UI)
        caracteres = QRawFont.fromFont(fuente)
        for letra in "ñÑáéíóúü¿¡0123456789":
            with self.subTest(letra=letra):
                self.assertTrue(caracteres.supportsCharacter(letra))


if __name__ == "__main__":
    unittest.main()
