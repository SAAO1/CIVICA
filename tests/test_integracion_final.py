"""Causalidad entre estructuras, consecuencias y persistencia; sin PyQt."""
import json
import unittest

from juego.partida import Juego
from models.publicacion import Publicacion


def forma(nodo):
    if nodo is None:
        return None
    return nodo.publicacion.id, forma(nodo.izquierda), forma(nodo.derecha)


def serializar(juego):
    return json.dumps(juego.datos(), sort_keys=True)


def restaurar(juego):
    return Juego.desde_datos(json.loads(serializar(juego)))


class PruebasIntegracionFinal(unittest.TestCase):
    def crear(self, rol="ciudadano"):
        juego = Juego(semilla=4, eventos=False)
        juego.seleccionar_rol(rol)
        self.assertTrue(juego.iniciar_primera_publicacion())
        return juego

    def test_topologia_restaurada_cambia_bfs_consecuencias_y_eleccion(self):
        original = self.crear()
        modificada = restaurar(original)
        self.assertEqual(serializar(original), serializar(modificada))
        self.assertTrue(modificada.grafo.eliminar_arista("ana", "luis"))
        for juego in (original, modificada):
            self.assertTrue(juego.ejecutar_accion("compartir"))
            self.assertIs(juego.obtener_publicacion_actual(), juego.arbol.buscar(50))
            self.assertEqual(juego.historial[-1]["alcance"], juego.ultima_propagacion.alcance)
            self.assertEqual(juego.historial[-1]["propagacion"]["receptores"],
                             juego.grafo.bfs("ana", 2).orden[1:])
        self.assertEqual(original.ultima_propagacion.receptores, ["luis", "pedro", "maria"])
        self.assertEqual(modificada.ultima_propagacion.receptores, ["pedro", "maria"])
        self.assertEqual((original.desinformacion, original.jugador.puntos), (9, -6))
        self.assertEqual((modificada.desinformacion, modificada.jugador.puntos), (6, -4))
        self.assertNotEqual(original.resultado_electoral()["apoyos"],
                            modificada.resultado_electoral()["apoyos"])

    def test_retiro_persistido_bloquea_difusion_y_conserva_red_e_historial(self):
        juego = self.crear("periodista")
        vertices, aristas = juego.grafo.vertices(), juego.grafo.aristas()
        self.assertTrue(juego.ejecutar_accion("desmentir"))
        self.assertTrue(juego.ultima_propagacion.correccion)
        self.assertIsNone(juego.arbol.buscar(50))
        self.assertTrue(juego.historial[-1]["eliminada"])
        copia = restaurar(juego)
        self.assertIsNone(copia.arbol.buscar(50))
        self.assertEqual(copia.grafo.vertices(), vertices)
        self.assertEqual(copia.grafo.aristas(), aristas)
        self.assertEqual(copia.historial[-1]["accion_rol"], "desmentir")
        self.assertEqual(copia.publicaciones_eliminadas, [50])
        antes = serializar(copia)
        with self.assertRaises(ValueError):
            copia.propagacion.simular(50, "ana")
        self.assertFalse(copia.ejecutar_accion("desmentir"))
        self.assertEqual(serializar(copia), antes)
        self.assertTrue(copia.avanzar_publicacion())
        self.assertEqual(copia.obtener_publicacion_actual().id, 30)

    def test_borrados_abb_conservan_forma_exacta_al_restaurar(self):
        juego = Juego(semilla=4, eventos=False)
        for clave in (50, 30, 70, 20, 40, 60, 80):
            self.assertTrue(juego.agregar_publicacion(
                Publicacion(clave, f"Publicación {clave}", True, 1)))
        casos = (
            ("hoja", 20, (50, (30, None, (40, None, None)),
                          (70, (60, None, None), (80, None, None)))),
            ("un hijo", 30, (50, (40, None, None),
                             (70, (60, None, None), (80, None, None)))),
            ("dos hijos", 70, (50, (40, None, None), (80, (60, None, None), None))),
            ("raíz", 50, (60, (40, None, None), (80, None, None))),
        )
        for caso, clave, esperada in casos:
            with self.subTest(caso=caso):
                juego.arbol.eliminar(clave)
                self.assertIsNone(juego.arbol.buscar(clave))
                self.assertEqual(forma(juego.arbol.raiz), esperada)
                copia = restaurar(juego)
                self.assertEqual(forma(copia.arbol.raiz), esperada)
                self.assertEqual(serializar(copia), serializar(juego))
                juego = copia

    def test_consultar_no_duplica_efectos_y_restaurar_conserva_continuacion(self):
        juego = self.crear()
        self.assertTrue(juego.ejecutar_accion("compartir"))
        self.assertTrue(juego.avanzar_publicacion())
        self.assertTrue(juego.ejecutar_accion("conversar"))
        self.assertTrue(juego.avanzar_publicacion())
        antes, forma_antes = serializar(juego), forma(juego.arbol.raiz)
        self.assertEqual([p.id for p in juego.arbol.inorden()], [30, 50, 70])
        self.assertEqual([p.id for p in juego.arbol.preorden()], [50, 30, 70])
        self.assertEqual([p.id for p in juego.arbol.postorden()], [30, 70, 50])
        self.assertEqual(set(juego.grafo.bfs("ana").orden), set(juego.grafo.dfs("ana")))
        simulacion = juego.propagacion.simular(70, "ana")
        self.assertEqual(simulacion.receptores, juego.grafo.bfs("ana", 2).orden[1:])
        self.assertEqual(serializar(juego), antes)
        copia = restaurar(juego)
        self.assertEqual(forma(copia.arbol.raiz), forma_antes)
        self.assertEqual(copia.grafo.aristas(), juego.grafo.aristas())
        self.assertEqual(serializar(copia), antes)
        for partida in (juego, copia):
            self.assertTrue(partida.ejecutar_accion("compartir"))
            self.assertTrue(partida.avanzar_publicacion())
        self.assertEqual(serializar(copia), serializar(juego))
        self.assertEqual(copia.resultado_electoral(), juego.resultado_electoral())


if __name__ == "__main__":
    unittest.main()
