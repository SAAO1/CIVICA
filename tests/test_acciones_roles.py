"""Los oficios cambian decisiones, fuentes y aristas de la partida compartida."""
import copy
import json
import queue
import time
import unittest

from juego.acciones import acciones_para_rol, accion_permitida, accion_por_defecto
from juego.partida import Juego
from models.jugador import Jugador
from red.servidor import Servidor
from red.cliente import Cliente


def juego_en(rol="ciudadano", publicacion=50):
    juego = Juego(8, eventos=False)
    juego.seleccionar_rol(rol)
    juego.iniciar_primera_publicacion()
    while juego.obtener_publicacion_actual().id != publicacion:
        juego.ejecutar_accion(accion_por_defecto(rol))
        juego.avanzar_publicacion()
    return juego


class PruebasAccionesRoles(unittest.TestCase):
    def test_cuatro_decisiones_por_oficio_sin_opciones_compartidas(self):
        ciudadano = acciones_para_rol("ciudadano")
        periodista = acciones_para_rol("periodista")
        self.assertEqual(len(ciudadano), 4)
        self.assertEqual(len(periodista), 4)
        self.assertFalse({a["clave"] for a in ciudadano} & {a["clave"] for a in periodista})
        for rol in ("ciudadano", "periodista"):
            for accion in acciones_para_rol(rol):
                self.assertTrue(accion_permitida(accion["clave"], rol, permitir_legacy=False))
                self.assertTrue(accion["titulo"] and accion["descripcion"])
        ciudadano[0]["titulo"] = "modificado por UI"
        self.assertNotEqual(acciones_para_rol("ciudadano")[0]["titulo"], ciudadano[0]["titulo"])

    def test_rechaza_decisiones_del_otro_oficio_sin_mutacion(self):
        for rol, acciones in (("ciudadano", ("contrastar", "entrevistar", "desmentir", "reservar")),
                              ("periodista", ("conversar", "convocar"))):
            for accion in acciones:
                with self.subTest(rol=rol, accion=accion):
                    juego = juego_en(rol)
                    antes = json.dumps(juego.datos(), sort_keys=True)
                    self.assertFalse(juego.ejecutar_accion(accion))
                    self.assertEqual(antes, json.dumps(juego.datos(), sort_keys=True))
        self.assertFalse(juego.ejecutar_accion(["contrastar"]))
        self.assertFalse(juego.ejecutar_accion(None))

    def test_las_ocho_decisiones_tienen_consecuencias_distintas(self):
        resultados = set()
        for rol in ("ciudadano", "periodista"):
            for opcion in acciones_para_rol(rol):
                juego = juego_en(rol)
                self.assertTrue(juego.ejecutar_accion(opcion["clave"]))
                r = juego.ultimo_registro
                resultados.add((tuple(r["despues"].values()), r["puntos"], r["publicacion"]["estado"],
                                r["alcance"], len(r["efectos_red"]["conexiones_creadas"])))
                self.assertEqual(r["accion_rol"], opcion["clave"])
                self.assertEqual(r["rol"], rol)
                self.assertEqual(r["cambios_reales"],
                                 {k: r["despues"][k] - v for k, v in r["antes"].items() if r["despues"][k] != v})
        self.assertEqual(len(resultados), 8)

    def test_conversar_crea_aristas_reales_y_no_convierte_rumor_en_hecho(self):
        juego = juego_en()
        antes = set(juego.grafo.aristas())
        self.assertTrue(juego.ejecutar_accion("conversar"))
        r = juego.ultimo_registro
        nuevas = {tuple(a) for a in r["efectos_red"]["conexiones_creadas"]}
        self.assertTrue(nuevas)
        self.assertEqual(set(juego.grafo.aristas()) - antes, nuevas)
        vecino = r["efectos_red"]["vecino_id"]
        self.assertTrue(juego.grafo.existe_arista("ana", vecino))
        self.assertTrue(juego.grafo.existe_arista(vecino, "ana"))
        self.assertIsNone(r["propagacion"])
        self.assertEqual(juego.info_verificada, 0)
        self.assertEqual(juego.desinformacion, 0)
        self.assertGreater(juego.participacion, 0)

    def test_entrevista_contacta_emisor_y_no_verifica_sin_pruebas(self):
        juego = juego_en("periodista")
        juego.jugador.ciudadano_id = "maria"
        self.assertFalse(juego.grafo.existe_arista("maria", "ana"))
        juego.ejecutar_accion("entrevistar")
        r = juego.ultimo_registro
        self.assertEqual(r["efectos_red"]["fuente_id"], "ana")
        self.assertFalse(r["efectos_red"]["testimonio_verificado"])
        self.assertTrue(juego.grafo.existe_arista("maria", "ana"))
        self.assertIsNone(r["propagacion"])
        self.assertEqual(r["publicacion"]["verificaciones"], 0)
        self.assertEqual(juego.info_verificada, 0)
        self.assertEqual(r["publicacion"]["estado"], "TESTIMONIO PENDIENTE")

    def test_conexion_vecinal_cambia_la_difusion_futura(self):
        conversar, silencio = juego_en(), juego_en()
        conversar.ejecutar_accion("conversar")
        silencio.ejecutar_accion("ignorar")
        for juego in (conversar, silencio):
            juego.avanzar_publicacion()
            juego.ejecutar_accion("compartir")
        self.assertGreater(conversar.ultimo_registro["alcance"], silencio.ultimo_registro["alcance"])

    def test_convocatoria_tiene_mas_alcance_y_riesgo_que_reenvio(self):
        compartir, convocar = juego_en(), juego_en()
        compartir.ejecutar_accion("compartir")
        convocar.ejecutar_accion("convocar")
        self.assertGreater(convocar.ultimo_registro["alcance"], compartir.ultimo_registro["alcance"])
        self.assertGreater(convocar.desinformacion, compartir.desinformacion)
        self.assertGreater(convocar.participacion, compartir.participacion)
        self.assertLess(convocar.jugador.puntos, compartir.jugador.puntos)

    def test_desmentir_rectifica_y_retira_solo_con_fundamento(self):
        falso, cierto = juego_en("periodista"), juego_en("periodista", 30)
        falso.ejecutar_accion("desmentir")
        self.assertTrue(falso.ultimo_registro["eliminada"])
        self.assertTrue(falso.ultima_propagacion.correccion)
        self.assertIsNone(falso.arbol.buscar(50))
        cierto.ejecutar_accion("desmentir")
        self.assertFalse(cierto.ultimo_registro["eliminada"])
        self.assertIsNone(cierto.ultima_propagacion)
        self.assertIsNotNone(cierto.arbol.buscar(30))
        self.assertLess(cierto.ultimo_registro["puntos"], 0)

    def test_reserva_distinta_de_silencio_y_nunca_publica_automaticamente(self):
        reserva, silencio = juego_en("periodista"), juego_en()
        reserva.ejecutar_accion("reservar")
        silencio.ejecutar_accion("ignorar")
        self.assertIsNone(reserva.ultima_propagacion)
        self.assertEqual(reserva.ultimo_registro["publicacion"]["estado"], "RESERVADA")
        self.assertNotEqual(reserva.estado.datos(), silencio.estado.datos())
        self.assertEqual(accion_por_defecto("periodista"), "reservar")

    def test_guardado_preserva_metodo_fuentes_aristas_y_deltas(self):
        juego = juego_en("periodista")
        juego.ejecutar_accion("entrevistar")
        copia = Juego.desde_datos(json.loads(json.dumps(juego.datos())))
        self.assertEqual(json.dumps(juego.datos(), sort_keys=True), json.dumps(copia.datos(), sort_keys=True))
        self.assertEqual(copia.ultima_accion_rol, "entrevistar")
        self.assertFalse(copia.ejecutar_accion("contrastar"))
        # Guardados de versión 1 sin metadatos nuevos siguen siendo válidos.
        antiguo = copy.deepcopy(juego.datos())
        for r in antiguo["historial"]:
            for clave in ("accion_rol", "rol", "titulo_accion", "efectos_red", "cambios_reales"):
                r.pop(clave, None)
        self.assertEqual(Juego.desde_datos(antiguo).ultima_accion_rol, "ignorar")

    def servidor(self):
        servidor = Servidor(eventos=False)
        servidor.juego.jugadores = [Jugador("a", "Ana", "ciudadano", "ana"),
                                     Jugador("b", "Bea", "periodista", "maria")]
        servidor.juego.iniciar_primera_publicacion()
        servidor.fase = "jugando"
        servidor._publicar = lambda: None
        return servidor

    def test_servidor_valida_oficio_y_turno_antes_de_cambiar_red(self):
        servidor = self.servidor()
        antes = json.dumps(servidor.juego.datos(), sort_keys=True)
        with self.assertRaises(ValueError):
            servidor._procesar("a", {"tipo": "accion", "publicacion_id": 50, "accion": "entrevistar"})
        with self.assertRaises(ValueError):
            servidor._procesar("b", {"tipo": "accion", "publicacion_id": 50, "accion": "conversar"})
        self.assertEqual(antes, json.dumps(servidor.juego.datos(), sort_keys=True))
        servidor._procesar("a", {"tipo": "accion", "publicacion_id": 50, "accion": "conversar"})
        self.assertEqual(servidor.juego.ultimo_registro["accion_rol"], "conversar")
        self.assertEqual(servidor.fase, "resultado")

    def test_plazo_periodista_deja_registro_editorial_en_reserva(self):
        servidor = self.servidor()
        servidor.juego.turno = 1
        servidor.deadline = time.monotonic() - 1
        servidor._timeout()
        self.assertEqual(servidor.fase, "resultado")
        self.assertEqual(servidor.juego.ultimo_registro["accion_rol"], "reservar")
        self.assertEqual(servidor.juego.ultimo_registro["rol"], "periodista")
        self.assertIsNone(servidor.juego.ultima_propagacion)

    def test_sockets_con_oficios_distintos_sincronizan_historial_y_aristas(self):
        def esperar(cola, predicado):
            limite = time.monotonic() + 5
            while time.monotonic() < limite:
                mensaje = cola.get(timeout=max(.01, limite - time.monotonic()))
                if predicado(mensaje):
                    return mensaje
            self.fail("No llegó el estado compartido")

        for cantidad in (2, 3, 4):
            with self.subTest(cantidad=cantidad):
                servidor = Servidor(puerto=0, eventos=False)
                servidor.iniciar()
                clientes, colas, ids = [], [], []
                try:
                    for i in range(cantidad):
                        cola = queue.Queue()
                        cliente = Cliente(cola.put)
                        cliente.conectar("127.0.0.1", servidor.puerto, f"Persona {i}",
                                         "ciudadano" if i % 2 == 0 else "periodista")
                        bienvenida = esperar(cola, lambda m: m["tipo"] == "bienvenida")
                        clientes.append(cliente)
                        colas.append(cola)
                        ids.append(bienvenida["id"])
                    clientes[0].enviar({"tipo": "iniciar"})
                    estado = [esperar(c, lambda m: m["tipo"] == "estado" and m["fase"] == "jugando")
                              for c in colas][0]
                    for turno in range(6):
                        actual = estado["datos"]["jugadores"][turno % cantidad]
                        indice = ids.index(actual["id"])
                        pub = estado["datos"]["publicacion_actual_id"]
                        opcion = ("conversar" if turno % 2 == 0 else "convocar") if actual["rol"] == "ciudadano" else (
                            "entrevistar" if turno < 3 else "contrastar")
                        clientes[indice].enviar({"tipo": "accion", "accion": opcion, "publicacion_id": pub})
                        resultados = [esperar(c, lambda m: m["tipo"] == "estado" and m["fase"] == "resultado")
                                      for c in colas]
                        self.assertTrue(all(r["datos"] == resultados[0]["datos"] for r in resultados))
                        r = resultados[0]["datos"]["historial"][-1]
                        self.assertEqual(r["accion_rol"], opcion)
                        self.assertEqual(r["rol"], actual["rol"])
                        revision = resultados[0]["revision"]
                        for cliente in clientes:
                            cliente.enviar({"tipo": "continuar", "revision": revision})
                        estados = [esperar(c, lambda m: m["tipo"] == "estado" and m["revision"] > revision)
                                   for c in colas]
                        self.assertTrue(all(r["datos"] == estados[0]["datos"] for r in estados))
                        estado = estados[0]
                    self.assertEqual(estado["fase"], "final")
                    copia = Juego.desde_datos(estado["datos"])
                    self.assertEqual(len(copia.historial), 6)
                    self.assertTrue(any(r["efectos_red"]["conexiones_creadas"] for r in copia.historial))
                finally:
                    for cliente in clientes:
                        cliente.cerrar()
                    servidor.cerrar()


if __name__ == "__main__":
    unittest.main()
