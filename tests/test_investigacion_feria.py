"""Pruebas causales del modo de investigación, sin Qt ni sockets."""
import json
import unittest

from juego.eventos import Evento
from juego.investigacion import SesionInvestigacion
from juego.partida import Juego


def copia(sesion):
    return SesionInvestigacion.desde_datos(json.loads(json.dumps(sesion.datos())))


class PruebasInvestigacionFeria(unittest.TestCase):
    def crear(self, cooperativa=False, rol="ciudadano"):
        sesion = SesionInvestigacion(semilla=4, cooperativa=cooperativa)
        if cooperativa:
            # Registrar en orden inverso no altera la secuencia de decisiones.
            sesion.registrar_jugador("Reportera", "periodista", id="p")
            sesion.registrar_jugador("Vecino", "ciudadano", id="c")
        else:
            sesion.registrar_jugador("Alex", rol, id="c")
        sesion.comenzar()
        return sesion

    def test_roles_exclusivos_y_exactamente_dos_en_cooperativa(self):
        sesion = SesionInvestigacion(cooperativa=True)
        sesion.registrar_jugador("Vecino", "ciudadano", id="c")
        with self.assertRaises(ValueError):
            sesion.comenzar()
        with self.assertRaises(ValueError):
            sesion.registrar_jugador("Otro", "ciudadano")
        with self.assertRaises(ValueError):
            sesion.registrar_jugador("Extra", "influencer")
        sesion.registrar_jugador("Reportera", "periodista", id="p")
        with self.assertRaises(ValueError):
            sesion.registrar_jugador("Tercero", "ciudadano")
        sesion.comenzar()
        with self.assertRaises(ValueError):
            sesion.cambiar_rol("c", "periodista")

    def test_evidencia_privada_se_solicita_y_comparte_sin_filtrar_texto(self):
        sesion = self.crear(True)
        sesion.investigar("p", "archivo")
        propia = sesion.vista("p")["hallazgos"][0]
        self.assertEqual(propia["id"], "50:documento")
        self.assertEqual(sesion.vista("c")["hallazgos"], [])
        ajena = sesion.vista("c")["hallazgos_disponibles"][0]
        self.assertEqual(ajena["id"], propia["id"])
        self.assertNotIn("texto", ajena)
        self.assertEqual(sesion.vista()["hallazgos"], [])
        with self.assertRaises(ValueError):
            sesion.proponer("c", "rectificar", evidencia_id=propia["id"])
        sesion.solicitar_hallazgo("c", propia["id"])
        self.assertFalse(sesion.solicitudes[0]["atendida"])
        sesion.compartir_hallazgo("p", propia["id"])
        self.assertTrue(sesion.solicitudes[0]["atendida"])
        self.assertEqual(sesion.vista("c")["hallazgos"][0]["texto"], propia["texto"])
        sesion.proponer("c", "rectificar", certeza="confirmada", evidencia_id=propia["id"])
        sesion.decidir("c", "rectificar", certeza="confirmada", evidencia_id=propia["id"])
        registro = sesion.juego.historial[-1]
        self.assertEqual(registro["accion"], "verificar")
        self.assertEqual(registro["accion_rol"], "rectificar")
        self.assertEqual(registro["titulo_accion"], "Rectificar con una prueba")
        self.assertEqual(sesion.juego.ultima_accion_rol, "rectificar")
        self.assertEqual(copia(sesion).juego.ultima_accion_rol, "rectificar")

    def test_dos_acciones_y_el_control_recupera_una_pieza_real(self):
        sesion = self.crear()
        self.assertEqual(sesion.vista("c")["caso"]["medio"]["texto_completo"], "")
        antes = json.dumps(sesion.datos(), sort_keys=True)
        with self.assertRaises(ValueError):
            sesion.examinar("c", "captura", 10)
        self.assertEqual(json.dumps(sesion.datos(), sort_keys=True), antes)
        sesion.examinar("c", "captura", 90)
        self.assertTrue(sesion.vista("c")["caso"]["medio"]["revelado"])
        self.assertIn("mantener las clases", sesion.vista("c")["caso"]["medio"]["texto_completo"])
        sesion.investigar("c", "archivo")
        self.assertEqual(sesion.presupuestos["c"], 0)
        with self.assertRaises(ValueError):
            sesion.investigar("c", "redaccion")
        self.assertEqual(len(sesion.hallazgos), 2)

    def test_dos_decisiones_reales_y_barrera_para_pasar_el_caso(self):
        sesion = self.crear(True)
        sesion.investigar("p", "archivo")
        antes = json.dumps(sesion.datos(), sort_keys=True)
        with self.assertRaises(ValueError):
            sesion.decidir("p", "desmentir", certeza="confirmada", evidencia_id="50:documento")
        self.assertEqual(json.dumps(sesion.datos(), sort_keys=True), antes)
        sesion.decidir("c", "compartir", contactos=["pedro"])
        self.assertEqual(sesion.fase, "decision")
        self.assertEqual(sesion.juego.historial[0]["jugador_id"], "c")
        self.assertEqual(sesion.juego.historial[0]["propagacion"]["receptores"], ["pedro", "maria"])
        with self.assertRaises(ValueError):
            sesion.decidir("c", "compartir")
        sesion.decidir("p", "desmentir", certeza="confirmada",
                       evidencia_id="50:documento", contactos=["carlos"])
        self.assertEqual(sesion.fase, "resultado")
        self.assertEqual(len(sesion.juego.historial), 2)
        self.assertIsNone(sesion.juego.arbol.buscar(50))
        self.assertEqual(sesion.juego.publicaciones_eliminadas, [50])
        self.assertNotEqual(sesion.juego.jugadores[0].puntos, sesion.juego.jugadores[1].puntos)
        sesion.continuar("c")
        self.assertEqual(sesion.caso_id, 50)
        sesion.continuar("p")
        self.assertEqual(sesion.caso_id, 90)
        self.assertEqual(sesion.presupuestos, {"c": 2, "p": 2})

    def test_audiencia_usa_bfs_restringido_y_prevision_no_cambia_puntos(self):
        sesion = self.crear()
        antes = json.dumps(sesion.juego.datos(), sort_keys=True)
        sesion.prever_alcance("c", ["pedro"])
        vista = sesion.vista("c")
        self.assertEqual(vista["red"]["alcance"]["receptores"], ["pedro", "maria"])
        self.assertEqual(json.dumps(sesion.juego.datos(), sort_keys=True), antes)
        with self.assertRaises(ValueError):
            sesion.prever_alcance("c", ["ines"])
        with self.assertRaises(ValueError):
            sesion.prever_alcance("c", ["pedro", "pedro"])
        sesion.decidir("c", "compartir", certeza="pendiente", contactos=[])
        self.assertEqual(sesion.juego.ultima_propagacion.alcance, 0)

    def test_certeza_sin_pruebas_tiene_costo_y_no_verifica_magicamente(self):
        prudente, temeraria = self.crear(), self.crear()
        prudente.decidir("c", "compartir", certeza="pendiente")
        temeraria.decidir("c", "compartir", certeza="confirmada")
        self.assertEqual(temeraria.juego.jugadores[0].puntos,
                         prudente.juego.jugadores[0].puntos-3)
        self.assertLess(temeraria.juego.confianza, prudente.juego.confianza)
        periodista = self.crear(rol="periodista")
        with self.assertRaises(ValueError):
            periodista.decidir("c", "contrastar", certeza="confirmada")
        self.assertEqual(len(periodista.juego.historial), 0)
        periodista.investigar("c", "archivo")
        periodista.decidir("c", "contrastar", certeza="confirmada", evidencia_id="50:documento")
        self.assertTrue(periodista.juego.ultima_propagacion.correccion)

    def test_relacion_distante_quita_arista_y_prueba_reabre_fuente(self):
        sesion = self.crear()
        self.assertTrue(sesion.juego.grafo.existe_arista("ana", "luis"))
        sesion.decidir("c", "compartir")
        self.assertFalse(sesion.juego.grafo.existe_arista("ana", "luis"))
        self.assertEqual(sesion.relaciones["luis"]["confianza"], 30)
        self.assertIn(["ana", "luis"],
                      sesion.juego.historial[0]["efectos_red"]["conexiones_eliminadas"])
        otra = self.crear()
        otra.relaciones["luis"]["confianza"] = 30
        with self.assertRaises(ValueError):
            otra.investigar("c", "barrio")
        otra.investigar("c", "archivo")
        otra.entrevistar("c", "origen", evidencia="50:documento")
        self.assertEqual(otra.relaciones["luis"]["confianza"], 45)
        self.assertEqual(next(r for r in otra.vista("c")["relaciones"] if r["id"] == "luis")["estado"], "duda")

    def test_restauracion_conserva_privacidad_turno_arbol_y_continuacion(self):
        sesion = self.crear(True)
        sesion.investigar("p", "archivo")
        sesion.decidir("c", "ignorar")
        restaurada = copia(sesion)
        self.assertEqual(json.dumps(restaurada.datos(), sort_keys=True),
                         json.dumps(sesion.datos(), sort_keys=True))
        self.assertEqual(restaurada.vista("c")["hallazgos"], [])
        for partida in (sesion, restaurada):
            partida.decidir("p", "desmentir", certeza="confirmada", evidencia_id="50:documento")
            partida.continuar("c")
            partida.continuar("p")
        self.assertEqual(json.dumps(restaurada.datos(), sort_keys=True),
                         json.dumps(sesion.datos(), sort_keys=True))

    def test_seis_casos_doce_decisiones_y_eleccion_real(self):
        sesion = self.crear(True)
        ids = []
        while sesion.fase != "final":
            ids.append(sesion.caso_id)
            sesion.decidir("c", "ignorar")
            sesion.decidir("p", "reservar")
            sesion.continuar("c")
            sesion.continuar("p")
        self.assertEqual(ids, [50, 90, 110, 40, 120, 35])
        self.assertEqual(len(sesion.juego.historial), 12)
        self.assertEqual(len(sesion.juego.arbol.inorden()), 6)
        self.assertEqual(sesion.vista("c")["resultado_electoral"], sesion.juego.resultado_electoral())
        self.assertTrue(sesion.juego.finalizada)
        self.assertEqual(copia(sesion).vista("c")["resultado_electoral"],
                         sesion.vista("c")["resultado_electoral"])

    def test_expiracion_nunca_publica_y_no_se_puede_aplicar_dos_veces(self):
        sesion = self.crear()
        sesion.juego.evento_actual = Evento("viral", "Una cadena circula", True, 15)
        sesion.expirar_turno("c")
        self.assertEqual(sesion.juego.historial[-1]["accion_rol"], "ignorar")
        self.assertTrue(sesion.juego.historial[-1]["por_plazo"])
        self.assertIsNone(sesion.juego.ultima_propagacion)
        with self.assertRaises(ValueError):
            sesion.expirar_turno("c")

    def test_errores_de_turno_no_consumen_presupuesto_ni_modifican_la_ciudad(self):
        sesion = self.crear(True)
        sesion.investigar("p", "archivo")
        sesion.juego.evento_actual = Evento("viral", "Una cadena circula", True, 15)
        antes = json.dumps(sesion.datos(), sort_keys=True)
        with self.assertRaises(ValueError):
            sesion.expirar_turno("p")
        self.assertEqual(json.dumps(sesion.datos(), sort_keys=True), antes)
        with self.assertRaises(ValueError):
            sesion.decidir("p", "desmentir", certeza="confirmada", evidencia_id="50:documento")
        self.assertEqual(json.dumps(sesion.datos(), sort_keys=True), antes)
        self.assertEqual(sesion.presupuestos, {"c": 2, "p": 1})
        self.assertEqual(sesion.juego.historial, [])
        sesion.expirar_turno("c")
        despues = json.dumps(sesion.datos(), sort_keys=True)
        with self.assertRaises(ValueError):
            sesion.expirar_turno("c")
        self.assertEqual(json.dumps(sesion.datos(), sort_keys=True), despues)
        sesion.expirar_turno("p")
        self.assertEqual([r["accion_rol"] for r in sesion.juego.historial], ["ignorar", "reservar"])
        self.assertTrue(all(r["por_plazo"] for r in sesion.juego.historial))
        self.assertEqual(sesion.presupuestos, {"c": 2, "p": 1})

    def test_sala_vacia_y_planes_de_juego_son_serializables(self):
        sala = SesionInvestigacion(cooperativa=True)
        self.assertEqual(copia(sala).fase, "sala")
        juego = Juego(4, campana="feria")
        self.assertEqual([p.id for p in juego.publicaciones_planificadas],
                         [50, 90, 110, 40, 120, 35])


if __name__ == "__main__":
    unittest.main()
