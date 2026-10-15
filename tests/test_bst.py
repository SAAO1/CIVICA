import unittest

from estructuras.bst import ArbolPublicaciones
from models.publicacion import Publicacion


class PruebasABB(unittest.TestCase):
    def setUp(self):
        self.arbol = ArbolPublicaciones()
        for clave in (50, 30, 70, 20, 40, 60, 80):
            self.arbol.insertar(Publicacion(clave, str(clave), True, 3))

    def ids(self, metodo="inorden"):
        return [p.id for p in getattr(self.arbol, metodo)()]

    def test_recorridos_y_busqueda(self):
        self.assertEqual(self.ids(), [20, 30, 40, 50, 60, 70, 80])
        self.assertEqual(self.ids("preorden"), [50, 30, 20, 40, 70, 60, 80])
        self.assertEqual(self.ids("postorden"), [20, 40, 30, 60, 80, 70, 50])
        self.assertEqual(self.arbol.buscar(40).texto, "40")
        self.assertIsNone(self.arbol.buscar(999))

    def test_eliminar_hoja_un_hijo_dos_hijos_y_raiz(self):
        for clave, esperados in (
            (30, [20, 40, 50, 60, 70, 80]),
            (20, [40, 50, 60, 70, 80]),
            (60, [40, 50, 70, 80]),
            (70, [40, 50, 80]),
            (50, [40, 80]),
        ):
            with self.subTest(clave=clave):
                self.arbol.eliminar(clave)
                self.assertEqual(self.ids(), esperados)
                self.assertIsNone(self.arbol.buscar(clave))

    def test_duplicados_y_vacio(self):
        original = self.arbol.buscar(50)
        self.arbol.insertar(Publicacion(50, "duplicada", False, 9))
        self.assertIs(self.arbol.buscar(50), original)
        self.arbol.eliminar(999)
        for clave in self.ids():
            self.arbol.eliminar(clave)
        self.assertIsNone(self.arbol.raiz)
        self.assertEqual(self.arbol.preorden(), [])
        self.assertEqual(self.arbol.postorden(), [])

