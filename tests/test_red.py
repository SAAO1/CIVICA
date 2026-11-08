import queue
import time
import unittest
from red.cliente import Cliente
from red.servidor import Servidor
from red.protocolo import codificar, decodificar, MAX_MENSAJE


class PruebasRed(unittest.TestCase):
    def esperar(self, cola, predicado):
        limite = time.monotonic() + 5
        while time.monotonic() < limite:
            mensaje = cola.get(timeout=max(.01, limite-time.monotonic()))
            if predicado(mensaje):
                return mensaje
        self.fail("No llegó el estado esperado")

    def sala(self, cantidad):
        servidor = Servidor(puerto=0, semilla=8, eventos=False)
        servidor.iniciar()
        clientes, colas, ids = [], [], []
        self.addCleanup(servidor.cerrar)
        for i, rol in enumerate(("ciudadano", "periodista", "ciudadano", "periodista")[:cantidad]):
            cola = queue.Queue()
            cliente = Cliente(cola.put)
            self.addCleanup(cliente.cerrar)
            cliente.conectar("127.0.0.1", servidor.puerto, f"Persona {i+1}", rol)
            bienvenida = self.esperar(cola, lambda m: m["tipo"] == "bienvenida")
            clientes.append(cliente)
            colas.append(cola)
            ids.append(bienvenida["id"])
        for cola in colas:
            self.esperar(cola, lambda m: m["tipo"] == "sala" and len(m["jugadores"]) == cantidad)
        clientes[0].enviar({"tipo": "iniciar"})
        estados = [self.esperar(c, lambda m: m["tipo"] == "estado" and m["fase"] == "jugando") for c in colas]
        return servidor, clientes, colas, ids, estados[0]

    def test_sala_solo_admite_personajes_jugables(self):
        servidor = Servidor(puerto=0)
        for rol in ("influencer", "candidato"):
            with self.assertRaises(ValueError):
                servidor._registrar({"nombre": "Alex", "rol": rol})
        self.assertEqual(servidor.juego.jugadores, [])
        self.assertFalse(servidor.tokens)

    def test_campana_sincronizada_dos_tres_y_cuatro_jugadores(self):
        for cantidad in (2, 3, 4):
            with self.subTest(cantidad=cantidad):
                servidor, clientes, colas, ids, estado = self.sala(cantidad)
                vistos = []
                for turno in range(6):
                    datos = estado["datos"]
                    pub = datos["publicacion_actual_id"]
                    vistos.append(pub)
                    jugador = datos["jugadores"][datos["turno"] % cantidad]["id"]
                    indice = ids.index(jugador)
                    # Rechazar a otro participante sin alterar el estado.
                    otro = (indice+1) % cantidad
                    clientes[otro].enviar({"tipo": "accion", "accion": "compartir", "publicacion_id": pub})
                    self.esperar(colas[otro], lambda m: m["tipo"] == "error")
                    clientes[indice].enviar({"tipo": "accion", "accion": "verificar", "publicacion_id": pub})
                    resultados = [self.esperar(c, lambda m: m["tipo"] == "estado" and m["fase"] == "resultado") for c in colas]
                    self.assertTrue(all(r["datos"] == resultados[0]["datos"] for r in resultados))
                    revision = resultados[0]["revision"]
                    clientes[indice].enviar({"tipo": "accion", "accion": "compartir", "publicacion_id": pub})
                    self.esperar(colas[indice], lambda m: m["tipo"] == "error")
                    for cliente in clientes:
                        cliente.enviar({"tipo": "continuar", "revision": revision})
                    estados = [self.esperar(c, lambda m: m["tipo"] == "estado" and m["revision"] > revision) for c in colas]
                    self.assertTrue(all(r["datos"] == estados[0]["datos"] for r in estados))
                    estado = estados[0]
                self.assertEqual(vistos, [50, 30, 70, 20, 60, 80])
                self.assertEqual(estado["fase"], "final")
                self.assertEqual(len(estado["datos"]["historial"]), 6)
                for cliente in clientes:
                    cliente.cerrar()
                servidor.cerrar()

    def test_desconexion_interrumpe_controladamente(self):
        servidor, clientes, colas, _, _ = self.sala(2)
        clientes[1].cerrar()
        estado = self.esperar(colas[0], lambda m: m["tipo"] == "estado" and m["fase"] == "interrumpida")
        self.assertEqual(len(estado["datos"]["jugadores"]), 2)
        self.assertEqual(estado["desconectados"], ["Persona 2"])

    def test_reconexion_conserva_turno_e_historial(self):
        servidor, clientes, colas, ids, estado = self.sala(2)
        token = servidor.tokens[ids[1]]
        clientes[1].cerrar()
        pausa = self.esperar(colas[0], lambda m: m["tipo"] == "estado" and m["fase"] == "interrumpida")
        cola = queue.Queue()
        recuperado = Cliente(cola.put)
        self.addCleanup(recuperado.cerrar)
        recuperado.conectar("127.0.0.1", servidor.puerto, "", "", token=token)
        bienvenida = self.esperar(cola, lambda m: m["tipo"] == "bienvenida")
        self.assertTrue(bienvenida["recuperada"])
        self.assertEqual(bienvenida["id"], ids[1])
        reanudado = self.esperar(cola, lambda m: m["tipo"] == "estado" and m["fase"] == "jugando")
        self.assertEqual(reanudado["datos"], estado["datos"])
        self.assertGreater(reanudado["revision"], pausa["revision"])

    def test_protocolo_rechaza_datos_invalidos(self):
        for mensaje in (b"[]", b"{}", b"{mal}", b"x"*(MAX_MENSAJE+1)):
            with self.subTest(mensaje=mensaje[:20]):
                with self.assertRaises(ValueError):
                    decodificar(mensaje)
        with self.assertRaises(ValueError):
            codificar({"tipo": "registro", "nombre": "x"*(MAX_MENSAJE+1)})

    def test_timeout_autoritativo_y_revision_obsoleta(self):
        servidor, clientes, colas, _, estado = self.sala(2)
        with servidor.lock:
            servidor.juego.evento_actual.urgente = True
            servidor.juego.evento_actual.segundos = .1
        clientes[0].enviar({"tipo": "decision_lista", "publicacion_id": 50})
        resultados = [self.esperar(c, lambda m: m["tipo"] == "estado" and m["fase"] == "resultado") for c in colas]
        self.assertEqual(resultados[0]["datos"]["historial"][0]["accion"], "ignorar")
        self.assertEqual(len(resultados[0]["datos"]["historial"]), 1)
        clientes[0].enviar({"tipo": "continuar", "revision": estado["revision"]})
        self.esperar(colas[0], lambda m: m["tipo"] == "error")
        self.assertEqual(servidor.juego.indice_proxima_publicacion, 1)

