import unittest
from estructuras.grafo import Grafo
from juego.red_social import crear_red_social
from juego.propagacion import ServicioPropagacion
from estructuras.bst import ArbolPublicaciones
from models.publicacion import Publicacion


class PruebasGrafo(unittest.TestCase):
    def setUp(self):
        self.grafo = crear_red_social()

    def test_bfs_dfs_ciclos_y_camino(self):
        recorrido = self.grafo.bfs("ana")
        self.assertEqual(recorrido.orden, ["ana", "luis", "pedro", "maria", "carlos", "sofia", "elena", "diego"])
        self.assertEqual(recorrido.distancias["maria"], 2)
        self.assertEqual(self.grafo.camino_minimo("ana", "maria"), ["ana", "luis", "maria"])
        self.assertEqual(self.grafo.dfs("ana"), ["ana", "luis", "maria", "carlos", "sofia", "elena", "diego", "pedro"])
        self.assertEqual(len(recorrido.orden), len(set(recorrido.orden)))
        self.assertEqual(self.grafo.bfs("ana", 1).niveles, [["ana"], ["luis", "pedro"]])

    def test_aislado_componentes_y_direccion(self):
        self.assertEqual(self.grafo.bfs("ines").orden, ["ines"])
        self.assertEqual(self.grafo.camino_minimo("ana", "ines"), [])
        self.assertFalse(self.grafo.es_alcanzable("diego", "ana"))
        self.assertEqual(len(self.grafo.componentes_debiles()), 2)
        self.assertEqual(self.grafo.grado_salida("ana"), 2)
        self.assertEqual(self.grafo.grado_entrada("maria"), 2)

    def test_operaciones_invalidas_no_modifican(self):
        anteriores = self.grafo.aristas()
        with self.assertRaises(KeyError):
            self.grafo.agregar_arista("ana", "inexistente")
        with self.assertRaises(ValueError):
            self.grafo.agregar_arista("ana", "ana")
        self.assertEqual(anteriores, self.grafo.aristas())
        self.assertFalse(self.grafo.agregar_arista("ana", "luis"))
        self.grafo.eliminar_vertice("maria")
        self.assertFalse(any("maria" in arista for arista in self.grafo.aristas()))
        self.assertEqual(self.grafo.cantidad_aristas(), len(self.grafo.aristas()))

    def test_vacio(self):
        vacio = Grafo()
        self.assertEqual(vacio.componentes_debiles(), [])
        with self.assertRaises(KeyError):
            vacio.bfs("ana")

    def test_propagacion_consulta_abb_y_cambio_topologia(self):
        arbol = ArbolPublicaciones()
        arbol.insertar(Publicacion(50, "Rumor", False, 7))
        servicio = ServicioPropagacion(arbol, self.grafo)
        inicial = servicio.simular(50, "ana")
        self.assertEqual(inicial.alcance, 3)
        self.grafo.agregar_arista("ana", "ines")
        self.assertEqual(servicio.simular(50, "ana").alcance, 4)
        self.assertEqual(inicial.alcance, 3)
        arbol.eliminar(50)
        with self.assertRaises(ValueError):
            servicio.simular(50, "ana")
        self.assertEqual(self.grafo.cantidad_vertices(), 9)

