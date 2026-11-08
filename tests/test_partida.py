import json
import tempfile
import unittest
from pathlib import Path
from juego.partida import Juego


class PruebasPartida(unittest.TestCase):
    def crear(self, rol="ciudadano"):
        juego = Juego(semilla=4, eventos=False)
        if rol in ("ciudadano", "periodista"):
            juego.seleccionar_rol(rol)
        else:
            # Regresión de perfiles históricos; no se ofrecen en partidas nuevas.
            juego.jugador.rol = rol
        juego.iniciar_primera_publicacion()
        return juego

    def test_solo_dos_personajes_seleccionables(self):
        from models.jugador import ROLES_JUGABLES
        self.assertEqual(ROLES_JUGABLES, ("ciudadano", "periodista"))
        juego = Juego(eventos=False)
        for rol in ("influencer", "candidato"):
            with self.assertRaises(ValueError):
                juego.seleccionar_rol(rol)
        self.assertEqual(juego.jugador.rol, "ciudadano")

    def test_decision_unica_progreso_y_reporte(self):
        juego = self.crear()
        self.assertFalse(juego.avanzar_publicacion())
        self.assertTrue(juego.ejecutar_accion("reportar"))
        estado = juego.estado.datos()
        self.assertFalse(juego.ejecutar_accion("verificar"))
        self.assertEqual(estado, juego.estado.datos())
        self.assertIsNone(juego.arbol.buscar(50))
        self.assertEqual(juego.historial[-1]["publicacion"]["id"], 50)
        self.assertEqual(juego.grafo.cantidad_vertices(), 9)
        self.assertTrue(juego.avanzar_publicacion())
        self.assertEqual(juego.obtener_publicacion_actual().id, 30)
        juego.ejecutar_accion("reportar")
        self.assertIsNotNone(juego.arbol.buscar(30))
        self.assertLess(juego.jugador.puntos, 5)

    def test_consecuencias_y_habilidad_influencer(self):
        normal, influencer = self.crear(), self.crear("influencer")
        normal.ejecutar_accion("compartir")
        influencer.ejecutar_accion("compartir")
        self.assertGreater(influencer.ultima_propagacion.alcance, normal.ultima_propagacion.alcance)
        self.assertGreater(influencer.desinformacion, normal.desinformacion)
        normal.avanzar_publicacion()
        antes = normal.desinformacion
        normal.ejecutar_accion("compartir")
        self.assertEqual(normal.desinformacion, antes)
        self.assertGreater(normal.info_verificada, 0)

    def test_ignorar_no_propaga_y_verificar_corrige(self):
        juego = self.crear()
        juego.ejecutar_accion("ignorar")
        self.assertIsNone(juego.ultima_propagacion)
        verificacion = self.crear("periodista")
        verificacion.ejecutar_accion("verificar")
        self.assertTrue(verificacion.ultima_propagacion.correccion)
        self.assertEqual(verificacion.arbol.buscar(50).estado, "FALSA VERIFICADA")
        self.assertEqual(verificacion.jugador.logros, ["Primera verificación"])

    def test_guardado_conserva_abb_grafo_azar_e_historial(self):
        juego = self.crear()
        juego.ejecutar_accion("reportar")
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "partida.json"
            juego.guardar(ruta)
            copia = Juego.cargar(ruta)
        self.assertEqual(json.dumps(juego.datos()), json.dumps(copia.datos()))
        copia.avanzar_publicacion()
        self.assertEqual(copia.obtener_publicacion_actual().id, 30)

    def test_final_depende_de_decisiones_y_semilla(self):
        buenas, malas = self.crear(), self.crear()
        for juego, accion in ((buenas, "verificar"), (malas, "compartir")):
            while juego.obtener_publicacion_actual():
                juego.ejecutar_accion(accion)
                juego.avanzar_publicacion()
        self.assertGreater(buenas.resultado_electoral()["calidad"], malas.resultado_electoral()["calidad"])
        self.assertNotEqual(buenas.resultado_electoral()["apoyos"], malas.resultado_electoral()["apoyos"])
        a, b = Juego(18), Juego(18)
        a.iniciar_primera_publicacion()
        b.iniciar_primera_publicacion()
        self.assertEqual(a.datos(), b.datos())

    def test_final_guardado_no_avanza_y_roles_diferentes(self):
        juego = self.crear()
        for _ in range(6):
            juego.ejecutar_accion("verificar")
            juego.avanzar_publicacion()
        self.assertTrue(juego.finalizada)
        turno = juego.turno
        self.assertFalse(juego.avanzar_publicacion())
        self.assertEqual(juego.turno, turno)
        self.assertTrue(Juego.desde_datos(juego.datos()).finalizada)
        ciudadana, periodista = self.crear(), self.crear("periodista")
        ciudadana.ejecutar_accion("verificar")
        periodista.ejecutar_accion("verificar")
        self.assertGreater(periodista.confianza, ciudadana.confianza)

    def test_candidato_opiniones_y_rangos(self):
        from models.publicacion import Publicacion
        juego = self.crear("candidato")
        juego.ejecutar_accion("verificar")
        juego.avanzar_publicacion()
        juego.ejecutar_accion("compartir")
        adrian = next(c for c in juego.candidatos if c.id == "adrian")
        self.assertEqual(adrian.apoyo, 27)
        opinion = Juego(eventos=False)
        opinion.agregar_publicacion(Publicacion(90, "Prefiero más parques", None, 1, tipo="opinion"))
        opinion.ejecutar_accion("verificar")
        self.assertEqual(opinion.arbol.buscar(90).estado, "OPINIÓN")
        self.assertIsNone(opinion.ultima_propagacion)
        opinion.estado.aplicar({"confianza": 200, "desinformacion": -200})
        self.assertEqual(opinion.confianza, 100)
        self.assertEqual(opinion.desinformacion, 0)

