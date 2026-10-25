"""El desenlace depende de decisiones y receptores; no de un ganador fijo."""
import copy
import json
import unittest

from juego.elecciones import calcular_eleccion
from juego.partida import Juego


class EleccionesEquilibradasTests(unittest.TestCase):
    def campaña(self, candidato, semilla=7):
        juego = Juego(semilla, eventos=False)
        juego.iniciar_primera_publicacion()
        while not juego.finalizada:
            publicacion = juego.obtener_publicacion_actual()
            juego.ejecutar_accion("verificar" if publicacion.candidato_id == candidato else "ignorar")
            juego.avanzar_publicacion()
        return juego

    def test_cada_candidatura_puede_ganar_por_decisiones_reproducibles(self):
        for semilla in (1, 7, 42):
            for candidato in ("juan", "adrian", "laura", "camila"):
                with self.subTest(semilla=semilla, candidato=candidato):
                    juego = self.campaña(candidato, semilla)
                    resultado = juego.resultado_electoral()
                    nombre = next(c.nombre for c in juego.candidatos if c.id == candidato)
                    self.assertFalse(resultado["empate"])
                    self.assertEqual(resultado["ganadores"], [nombre])
                    self.assertAlmostEqual(100, sum(resultado["porcentajes"].values()))

    def test_consultar_guardar_y_recargar_no_cambian_resultado_ni_azar(self):
        juego = self.campaña("camila")
        antes = copy.deepcopy(juego.datos())
        resultado = juego.resultado_electoral()
        for _ in range(5):
            self.assertEqual(resultado, juego.resultado_electoral())
        self.assertEqual(antes, juego.datos())
        restaurada = Juego.desde_datos(json.loads(json.dumps(antes)))
        self.assertEqual(resultado, restaurada.resultado_electoral())

    def test_alcance_grafo_amplifica_la_evidencia_sin_inventar_receptores(self):
        conectada = Juego(1, eventos=False)
        aislada = Juego(1, eventos=False)
        aislada.grafo.adyacencia = {k: {} for k in aislada.grafo.nodos}
        for juego in (conectada, aislada):
            juego.iniciar_primera_publicacion()
            juego.ejecutar_accion("verificar")
        a, b = conectada.resultado_electoral(), aislada.resultado_electoral()
        self.assertGreater(a["apoyos"]["juan"], b["apoyos"]["juan"])
        self.assertGreater(a["evidencia_por_candidato"]["juan"][0]["alcance"], 0)
        self.assertEqual(b["evidencia_por_candidato"]["juan"][0]["alcance"], 0)

    def test_empates_no_se_rompen_por_orden_por_semilla_ni_por_recuento(self):
        for semilla in (None, 1, 7, 42):
            juego = Juego(semilla)
            resultado = juego.resultado_electoral()
            self.assertTrue(resultado["empate"])
            self.assertEqual(len(resultado["ganadores"]), 4)
            self.assertIn("recuento", resultado["desempate"])
            inverso = calcular_eleccion(list(reversed(juego.candidatos)), juego.estado, [])
            self.assertEqual(set(resultado["ganadores"]), set(inverso["ganadores"]))
        juego.candidatos[3].apoyo = 70
        porcentajes = juego.resultado_electoral()["porcentajes"]
        self.assertEqual(porcentajes["juan"], porcentajes["adrian"])
        self.assertEqual(porcentajes["juan"], porcentajes["laura"])

    def test_dos_noticias_no_conceden_doble_peso_de_agenda(self):
        for accion in ("verificar", "compartir"):
            juego = Juego(1, eventos=False)
            while juego.agregar_siguiente_publicacion():
                juego.ejecutar_accion(accion)
            resultado = juego.resultado_electoral()
            for detalles in resultado["evidencia_por_candidato"].values():
                self.assertAlmostEqual(sum(d["peso_agenda"] for d in detalles), 1, places=3)
            # El formato antiguo no tenía publicacion_antes. Su +1 de impacto
            # al compartir no debe convertirse en un premio electoral extra.
            antiguos = copy.deepcopy(juego.historial)
            for registro in antiguos:
                registro.pop("publicacion_antes", None)
            self.assertEqual(resultado, calcular_eleccion(juego.candidatos, juego.estado, antiguos, juego.grafo))

    def test_dialogo_social_modera_rechazo_sin_inventar_verificaciones(self):
        for candidato in ("juan", "adrian", "laura", "camila"):
            juego = Juego(7, eventos=False)
            juego.iniciar_primera_publicacion()
            while not juego.finalizada:
                publicacion = juego.obtener_publicacion_actual()
                juego.ejecutar_accion("conversar" if publicacion.candidato_id == candidato else "ignorar")
                juego.avanzar_publicacion()
            resultado = juego.resultado_electoral()
            self.assertEqual(resultado["ganadores"], [next(c.nombre for c in juego.candidatos if c.id == candidato)])
            for detalle in resultado["evidencia_por_candidato"][candidato]:
                self.assertGreater(detalle["contactos_creados"], 0)
                self.assertIn("No certifica", detalle["motivo"])
            self.assertFalse(any(r["accion"] == "verificar" for r in juego.historial))

    def test_falsa_encuesta_no_se_interpreta_como_una_acusacion(self):
        juego = Juego(7, eventos=False)
        while juego.agregar_siguiente_publicacion():
            juego.ejecutar_accion("verificar")
        detalle = juego.resultado_electoral()["evidencia_por_candidato"]["juan"][-1]
        self.assertEqual(detalle["publicacion_id"], 80)
        self.assertLess(detalle["cambio"], 0)
        self.assertIn("expectativa", detalle["motivo"])


if __name__ == "__main__":
    unittest.main()
