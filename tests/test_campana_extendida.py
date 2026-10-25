"""La campaña de siete actos progresa, conserva memoria y llega al cierre real."""
import copy
import json
import queue
import time
import unittest

from juego.partida import Juego
from juego.acciones import acciones_para_rol
from red.cliente import Cliente
from red.servidor import Servidor
from red.protocolo import MAX_MENSAJE, codificar


PLAN = [50, 30, 70, 20, 60, 80, 90, 40, 100, 10, 110, 25, 120, 35]


class CampanaExtendidaTests(unittest.TestCase):
    def completar(self, elegir, rol="periodista", eventos=False, semilla=21):
        juego = Juego(semilla, eventos=eventos, campana="extendida")
        juego.seleccionar_rol(rol)
        juego.iniciar_primera_publicacion()
        while not juego.finalizada:
            accion = elegir(juego)
            self.assertTrue(juego.ejecutar_accion(accion))
            juego.avanzar_publicacion()
        return juego

    def test_catorce_casos_y_final_solo_despues_del_acto_siete(self):
        juego = Juego(21, eventos=False, campana="extendida")
        self.assertEqual([p.id for p in juego.publicaciones_planificadas], PLAN)
        juego.iniciar_primera_publicacion()
        for indice, identificador in enumerate(PLAN):
            self.assertFalse(juego.finalizada)
            self.assertEqual(juego.obtener_publicacion_actual().id, identificador)
            self.assertTrue(juego.ejecutar_accion("ignorar"))
            self.assertFalse(juego.ejecutar_accion("convocar"))
            self.assertEqual(len(juego.historial), indice + 1)
            self.assertEqual(juego.avanzar_publicacion(), indice < 13)
        self.assertTrue(juego.finalizada)
        self.assertIsNone(juego.obtener_publicacion_actual())
        self.assertEqual(juego.turno, 14)
        self.assertFalse(juego.avanzar_publicacion())

    def test_v1_antiguo_sigue_siendo_clasico_y_plan_invalido_se_rechaza(self):
        juego = Juego(21, eventos=False)
        datos = juego.datos()
        datos.pop("campana")
        datos.pop("plan_publicaciones")
        restaurada = Juego.desde_datos(datos)
        self.assertEqual(restaurada.campana, "clasica")
        self.assertEqual(len(restaurada.publicaciones_planificadas), 6)
        datos["campana"] = "extendida"
        with self.assertRaises(ValueError):
            Juego.desde_datos(datos)
        datos["plan_publicaciones"] = [50, 30, 70, 20, 60, 80]
        with self.assertRaises(ValueError):
            Juego.desde_datos(datos)
        with self.assertRaises(ValueError):
            Juego(campana="siete-casos-inventados")
        datos = Juego(campana="extendida").datos()
        datos["finalizada"] = True
        with self.assertRaises(ValueError):
            Juego.desde_datos(datos)

    def test_guardado_en_cada_caso_conserva_azar_red_memorias_y_siguiente(self):
        juego = Juego(88, campana="extendida")
        juego.iniciar_primera_publicacion()
        for identificador in PLAN:
            self.assertEqual(juego.obtener_publicacion_actual().id, identificador)
            juego.ejecutar_accion("convocar")
            datos = json.loads(json.dumps(juego.datos()))
            restaurada = Juego.desde_datos(datos)
            self.assertEqual(datos, json.loads(json.dumps(restaurada.datos())))
            self.assertEqual(juego.resultado_electoral(), restaurada.resultado_electoral())
            self.assertEqual(juego.avanzar_publicacion(), restaurada.avanzar_publicacion())
            self.assertEqual(json.loads(json.dumps(juego.datos())),
                             json.loads(json.dumps(restaurada.datos())))
            juego = restaurada
        self.assertTrue(Juego.desde_datos(juego.datos()).finalizada)

    def test_valeria_aparece_al_acto_iv_y_la_entrevista_toca_su_nodo(self):
        juego = Juego(1, eventos=False, campana="extendida")
        juego.seleccionar_rol("periodista")
        juego.iniciar_primera_publicacion()
        for _ in range(6):
            self.assertNotIn("valeria", juego.grafo.nodos)
            juego.ejecutar_accion("reservar")
            juego.avanzar_publicacion()
        self.assertEqual(juego.obtener_publicacion_actual().id, 90)
        self.assertEqual(juego.grafo.nodos["valeria"].rol, "influencer")
        self.assertIn("violeta", juego.grafo.nodos)
        self.assertGreaterEqual(juego.grafo.grado_salida("valeria"), 10)
        self.assertIn("valeria", juego.ciudadanos_nuevos)
        juego.ejecutar_accion("entrevistar")
        self.assertEqual(juego.ultimo_registro["efectos_red"]["fuente_id"], "valeria")
        self.assertTrue(juego.grafo.existe_arista(juego.jugador.ciudadano_id, "valeria"))
        self.assertTrue(juego.grafo.existe_arista("valeria", juego.jugador.ciudadano_id))
        recargada = Juego.desde_datos(json.loads(json.dumps(juego.datos())))
        self.assertEqual(juego.grafo.aristas(), recargada.grafo.aristas())
        with self.assertRaises(ValueError):
            Juego(campana="extendida").seleccionar_rol("influencer")

    def test_ocho_acciones_tienen_consecuencias_validas_en_los_catorce_casos(self):
        for rol in ("ciudadano", "periodista"):
            for definicion in acciones_para_rol(rol):
                with self.subTest(rol=rol, accion=definicion["clave"]):
                    juego = self.completar(lambda j: definicion["clave"], rol)
                    self.assertEqual([r["publicacion"]["id"] for r in juego.historial], PLAN)
                    self.assertEqual({r["accion_rol"] for r in juego.historial}, {definicion["clave"]})
                    self.assertTrue(all(0 <= valor <= 100 for valor in juego.estado.datos().values()))

    def test_cuatro_ganadores_y_empate_son_alcanzables_por_acciones_reales(self):
        for semilla in (1, 42):
            for rol, activa, pasiva in (("periodista", "contrastar", "reservar"),
                                        ("ciudadano", "conversar", "ignorar")):
                for identificador in ("juan", "adrian", "laura", "camila"):
                    with self.subTest(candidato=identificador, semilla=semilla, rol=rol):
                        juego = self.completar(
                            lambda j: activa if j.obtener_publicacion_actual().candidato_id == identificador
                            else pasiva, semilla=semilla, rol=rol)
                        resultado = juego.resultado_electoral()
                        nombre = next(c.nombre for c in juego.candidatos if c.id == identificador)
                        self.assertEqual(resultado["ganadores"], [nombre])
                        self.assertFalse(resultado["empate"])
                        self.assertAlmostEqual(sum(resultado["porcentajes"].values()), 100)
                        antes = copy.deepcopy(juego.datos())
                        self.assertEqual(resultado, Juego.desde_datos(antes).resultado_electoral())
                        self.assertEqual(juego.datos(), antes)
        for rol, accion in (("periodista", "reservar"), ("ciudadano", "ignorar")):
            empate = self.completar(lambda j: accion, rol=rol).resultado_electoral()
            self.assertTrue(empate["empate"])
            self.assertEqual(len(empate["ganadores"]), 4)

    def test_agenda_reparte_el_mismo_peso_y_no_cambia_por_compartidos(self):
        juego = self.completar(lambda j: "compartir", rol="ciudadano")
        resultado = juego.resultado_electoral()
        for detalles in resultado["evidencia_por_candidato"].values():
            self.assertAlmostEqual(sum(d["peso_agenda"] for d in detalles), 1, places=3)
        self.assertEqual(resultado, Juego.desde_datos(juego.datos()).resultado_electoral())
        trama = codificar({"tipo": "estado", "datos": juego.datos()})
        self.assertLessEqual(len(trama) - 1, MAX_MENSAJE)

    def test_cuaderno_cubre_siete_actos_y_recuerda_las_catorce_decisiones(self):
        from juego.cuaderno import CASOS, PERFILES, caso_actual, recuerdos
        self.assertTrue(set(PLAN).issubset(CASOS))
        self.assertEqual(len({CASOS[identificador]["acto"] for identificador in PLAN}), 7)
        for identificador in PLAN:
            caso = CASOS[identificador]
            self.assertEqual(len(caso["pistas"]), 3)
            self.assertTrue(all(set(("titulo", "texto", "pregunta")).issubset(pista) for pista in caso["pistas"]))
        nombres = {perfil["nombre"] for perfil in PERFILES}
        self.assertTrue({"INFLUENCER", "JUAN", "ADRIAN", "LAURA", "CAMILA"}.issubset(nombres))
        juego = self.completar(lambda j: "reservar")
        self.assertEqual(caso_actual(juego), CASOS[35])
        galeria = recuerdos(juego)
        self.assertEqual(len(galeria), 15)  # Catorce decisiones y el cierre.

    def test_el_sexto_caso_no_anuncia_el_cierre_de_la_campana_extendida(self):
        from juego.cuaderno import CASOS, caso_actual, recuerdos
        original = copy.deepcopy(CASOS[80])
        for campana, titulo in (("clasica", "La última captura"),
                                ("extendida", "La cifra sin método")):
            juego = Juego(7, eventos=False, campana=campana)
            juego.iniciar_primera_publicacion()
            for _ in range(5):
                juego.ejecutar_accion("ignorar")
                juego.avanzar_publicacion()
            self.assertEqual(juego.publicacion_actual_id, 80)
            self.assertEqual(caso_actual(juego)["titulo"], titulo)
            juego.ejecutar_accion("ignorar")
            self.assertEqual(recuerdos(juego)[-1]["titulo"], titulo)
            if campana == "extendida":
                self.assertNotIn("última", recuerdos(juego)[-1]["texto"].lower())
        self.assertEqual(CASOS[80], original)


class CampanaExtendidaRedTests(unittest.TestCase):
    def esperar(self, cola, predicado):
        limite = time.monotonic() + 8
        while time.monotonic() < limite:
            mensaje = cola.get(timeout=max(.01, limite - time.monotonic()))
            if predicado(mensaje):
                return mensaje
        self.fail("No llegó el estado esperado")

    def test_tcp_catorce_turnos_con_dos_tres_y_cuatro_participantes(self):
        for cantidad in (2, 3, 4):
            with self.subTest(cantidad=cantidad):
                servidor = Servidor(puerto=0, semilla=8, eventos=False, campana="extendida")
                servidor.iniciar()
                self.addCleanup(servidor.cerrar)
                clientes, colas, identificadores = [], [], []
                for indice in range(cantidad):
                    cola = queue.Queue()
                    cliente = Cliente(cola.put)
                    self.addCleanup(cliente.cerrar)
                    rol = "periodista" if indice % 2 else "ciudadano"
                    cliente.conectar("127.0.0.1", servidor.puerto, f"Persona {indice + 1}", rol)
                    bienvenida = self.esperar(cola, lambda m: m["tipo"] == "bienvenida")
                    clientes.append(cliente)
                    colas.append(cola)
                    identificadores.append(bienvenida["id"])
                for cola in colas:
                    self.esperar(cola, lambda m: m["tipo"] == "sala" and len(m["jugadores"]) == cantidad)
                clientes[0].enviar({"tipo": "iniciar"})
                estados = [self.esperar(c, lambda m: m["tipo"] == "estado" and m["fase"] == "jugando")
                           for c in colas]
                estado = estados[0]
                for numero, publicacion_id in enumerate(PLAN):
                    datos = estado["datos"]
                    self.assertEqual(datos["campana"], "extendida")
                    self.assertEqual(datos["publicacion_actual_id"], publicacion_id)
                    self.assertEqual(datos["turno"], numero)
                    participante = datos["jugadores"][numero % cantidad]
                    indice = identificadores.index(participante["id"])
                    accion = "contrastar" if participante["rol"] == "periodista" else "convocar"
                    clientes[indice].enviar({"tipo": "accion", "accion": accion,
                                             "publicacion_id": publicacion_id})
                    resultados = [self.esperar(c, lambda m: m["tipo"] == "estado" and m["fase"] == "resultado")
                                  for c in colas]
                    self.assertTrue(all(r["datos"] == resultados[0]["datos"] for r in resultados))
                    revision = resultados[0]["revision"]
                    for cliente in clientes:
                        cliente.enviar({"tipo": "continuar", "revision": revision})
                    estados = [self.esperar(c, lambda m: m["tipo"] == "estado" and m["revision"] > revision)
                               for c in colas]
                    self.assertTrue(all(r["datos"] == estados[0]["datos"] for r in estados))
                    estado = estados[0]
                self.assertEqual(estado["fase"], "final")
                self.assertEqual(len(estado["datos"]["historial"]), 14)
                self.assertTrue(Juego.desde_datos(estado["datos"]).finalizada)
                for cliente in clientes:
                    cliente.cerrar()
                servidor.cerrar()
