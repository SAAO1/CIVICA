"""Casos de sustentación que unen operaciones, ABB, reglas y observatorio."""

import json
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication

from juego.partida import Juego
from juego.red_social import crear_red_social
from paneles import EscenaRed


class PruebasSegundaEntrega(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def crear(self):
        juego = Juego(4, eventos=False)
        juego.iniciar_primera_publicacion()
        return juego

    def test_eliminar_arista_cambia_ruta_y_eliminar_vertice_limpia_conexiones(self):
        grafo = crear_red_social()
        self.assertEqual(grafo.camino_minimo("ana", "maria"), ["ana", "luis", "maria"])
        self.assertTrue(grafo.eliminar_arista("ana", "luis"))
        self.assertFalse(grafo.eliminar_arista("ana", "luis"))
        self.assertEqual(grafo.camino_minimo("ana", "maria"), ["ana", "pedro", "maria"])
        self.assertEqual(grafo.grado_entrada("luis"), 0)
        self.assertEqual(grafo.cantidad_vertices(), 9)
        grafo.eliminar_vertice("pedro")
        self.assertFalse(grafo.existe_vertice("pedro"))
        self.assertFalse(any("pedro" in arista for arista in grafo.aristas()))
        self.assertEqual(grafo.bfs("ana").orden, ["ana"])
        self.assertEqual(grafo.camino_minimo("ana", "maria"), [])

    def test_cambiar_topologia_modifica_consecuencias_de_la_decision(self):
        original, modificada = self.crear(), self.crear()
        modificada.grafo.eliminar_arista("ana", "luis")
        for juego in (original, modificada):
            self.assertTrue(juego.ejecutar_accion("compartir"))
            self.assertIsNotNone(juego.arbol.buscar(50))
        self.assertEqual(original.ultima_propagacion.alcance, 3)
        self.assertEqual(modificada.ultima_propagacion.alcance, 2)
        self.assertEqual(original.desinformacion, 9)
        self.assertEqual(modificada.desinformacion, 6)
        self.assertEqual(original.jugador.puntos, -6)
        self.assertEqual(modificada.jugador.puntos, -4)
        self.assertEqual(original.historial[-1]["alcance"], 3)
        self.assertEqual(modificada.historial[-1]["alcance"], 2)

    def test_retirar_del_abb_bloquea_comparacion_pero_conserva_red_explorable(self):
        juego = self.crear()
        ciudadanos, conexiones = juego.grafo.vertices(), juego.grafo.aristas()
        self.assertTrue(juego.ejecutar_accion("reportar"))
        self.assertIsNone(juego.arbol.buscar(50))
        self.assertTrue(juego.historial[-1]["eliminada"])
        self.assertEqual(juego.grafo.vertices(), ciudadanos)
        self.assertEqual(juego.grafo.aristas(), conexiones)
        escena = EscenaRed(juego)
        escena.reducir_movimiento = True
        self.addCleanup(escena.close)
        self.addCleanup(escena.finalizar_escena)
        escena.mostrar()
        antes = json.dumps(juego.datos(), sort_keys=True)
        with patch.object(juego.propagacion, "simular", wraps=juego.propagacion.simular) as simular:
            escena.comparar()
            simular.assert_not_called()
        self.assertIn("retirada", escena.detalle.text())
        self.assertEqual(escena.pasos, [])
        for tipo in ("bfs", "dfs"):
            escena.recorrer(tipo)
            self.assertEqual(escena.visualizador.visitados, juego.grafo.alcanzables("ana"))
        self.assertEqual(json.dumps(juego.datos(), sort_keys=True), antes)
        self.assertEqual(len(juego.historial), 1)


if __name__ == "__main__":
    unittest.main()
