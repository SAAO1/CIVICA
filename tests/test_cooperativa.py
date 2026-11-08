"""TCP real de dos investigadores: reservas, autoridad y recuperación de sesión."""
import json
import socket
import threading
import time
import unittest

from red.cliente_cooperativo import ClienteCooperativo
from red.cooperativa import ServidorCooperativo
from red.protocolo import recibir


class _Par:
    def __init__(self, puerto, nombre, rol=None, token=None, host="127.0.0.1",
                 anfitrion_token=None):
        self.mensajes = []
        self.condicion = threading.Condition()
        self.cliente = ClienteCooperativo(self._recibir)
        self.cliente.conectar(host, puerto, nombre, rol, token, anfitrion_token=anfitrion_token)

    def _recibir(self, mensaje):
        with self.condicion:
            self.mensajes.append(mensaje)
            self.condicion.notify_all()

    def esperar(self, tipo, condicion=lambda mensaje: True, desde=0, segundos=3):
        limite = time.monotonic() + segundos
        with self.condicion:
            while True:
                for mensaje in self.mensajes[desde:]:
                    if mensaje.get("tipo") == tipo and condicion(mensaje):
                        return mensaje
                restante = limite - time.monotonic()
                if restante <= 0:
                    raise AssertionError(
                        f"No llegó {tipo}; mensajes: {self.mensajes[desde:]}")
                self.condicion.wait(restante)

    def enviar(self, mensaje):
        if not self.cliente.enviar(mensaje):
            raise AssertionError("El cliente rechazó el envío")

    def cerrar(self):
        self.cliente.cerrar()
        if self.cliente.hilo is not None:
            self.cliente.hilo.join(timeout=.5)


class PruebasCooperativa(unittest.TestCase):
    def setUp(self):
        self.servidor = ServidorCooperativo(host="127.0.0.1", puerto=0, semilla=4)
        self.puerto = self.servidor.iniciar()
        self.addCleanup(self.servidor.cerrar)
        self.pares = []

    def entrar(self, nombre, rol=None, token=None, bienvenida=True, anfitrion_token=None):
        par = _Par(self.puerto, nombre, rol, token, anfitrion_token=anfitrion_token)
        self.pares.append(par)
        self.addCleanup(par.cerrar)
        if bienvenida:
            par.esperar("bienvenida")
        return par

    def reservar(self, par, rol):
        desde = len(par.mensajes)
        par.enviar({"tipo": "reservar_rol", "rol": rol})
        return par.esperar("sala", lambda m: (
            rol in m["roles_ocupados"]
            and m["roles_ocupados"][rol]["id"] == par.cliente.id
        ), desde=desde)

    def comenzar(self):
        ciudadano, periodista = self.entrar("Ana"), self.entrar("María")
        self.reservar(ciudadano, "ciudadano")
        self.reservar(periodista, "periodista")
        ciudadano.esperar("sala", lambda m: m["puede_iniciar"])
        ciudadano.enviar({"tipo": "iniciar"})
        primero = ciudadano.esperar("estado")
        segundo = periodista.esperar("estado")
        self.assertEqual(primero["vista"]["caso"]["id"], segundo["vista"]["caso"]["id"])
        return ciudadano, periodista, primero, segundo

    def test_disponibilidad_antes_de_elegir_y_cambio_atomico(self):
        primero = self.entrar("Uno")
        sala = primero.esperar("sala")
        self.assertEqual(sala["roles_disponibles"], ["ciudadano", "periodista"])
        self.assertIsNone(sala["jugadores"][0]["rol"])
        segundo = self.entrar("Dos")
        antes = len(segundo.mensajes)
        reservada = self.reservar(primero, "ciudadano")
        remota = segundo.esperar(
            "sala", lambda m: m["revision"] >= reservada["revision"], desde=antes)
        self.assertEqual(remota["roles_disponibles"], ["periodista"])
        self.assertEqual(remota["roles_ocupados"]["ciudadano"]["nombre"], "Uno")
        antes = len(segundo.mensajes)
        segundo.enviar({"tipo": "reservar_rol", "rol": "ciudadano"})
        segundo.esperar("error", desde=antes)
        self.assertEqual(self.servidor.participantes[primero.cliente.id].rol, "ciudadano")
        self.assertIsNone(self.servidor.participantes[segundo.cliente.id].rol)
        cambio = self.reservar(primero, "periodista")
        segundo.esperar("sala", lambda m: m["revision"] >= cambio["revision"])
        self.assertEqual(cambio["roles_disponibles"], ["ciudadano"])
        self.assertFalse(cambio["puede_iniciar"])

    def test_reservas_simultaneas_dejan_un_unico_titular(self):
        pares = [self.entrar("Uno"), self.entrar("Dos")]
        for par in pares:
            par.esperar("sala", lambda m: len(m["jugadores"]) == 2)
        barrera = threading.Barrier(3)
        def reservar(par):
            barrera.wait()
            par.enviar({"tipo": "reservar_rol", "rol": "ciudadano"})
        hilos = [threading.Thread(target=reservar, args=(par,)) for par in pares]
        for hilo in hilos:
            hilo.start()
        barrera.wait()
        for hilo in hilos:
            hilo.join(timeout=1)
        for par in pares:
            par.esperar("sala", lambda m: "ciudadano" in m["roles_ocupados"])
        limite = time.monotonic() + 2
        while time.monotonic() < limite:
            if any(any(m["tipo"] == "error" for m in p.mensajes) for p in pares):
                break
            time.sleep(.01)
        self.assertEqual(sum(p.rol == "ciudadano"
                             for p in self.servidor.participantes.values()), 1)
        self.assertEqual(sum(any(m["tipo"] == "error" for m in p.mensajes)
                             for p in pares), 1)

    def test_tercero_rechazado_y_desconexion_en_sala_libera_rol(self):
        primero, segundo = self.entrar("Uno"), self.entrar("Dos")
        self.reservar(primero, "ciudadano")
        tercero = self.entrar("Tres", bienvenida=False)
        error = tercero.esperar("error")
        self.assertIn("dos participantes", error["texto"])
        tercero.esperar("desconexion")
        antes = len(segundo.mensajes)
        primero.cerrar()
        liberada = segundo.esperar(
            "sala", lambda m: len(m["jugadores"]) == 1, desde=antes)
        self.assertIn("ciudadano", liberada["roles_disponibles"])
        self.assertEqual(liberada["anfitrion"], segundo.cliente.id)
        reemplazo = self.entrar("Reemplazo")
        nueva = self.reservar(reemplazo, "ciudadano")
        self.assertEqual(len(nueva["jugadores"]), 2)

    def test_inicio_exige_dos_roles_y_solo_anfitrion(self):
        primero, segundo = self.entrar("Uno"), self.entrar("Dos")
        antes = len(primero.mensajes)
        primero.enviar({"tipo": "iniciar"})
        primero.esperar("error", desde=antes)
        self.reservar(primero, "ciudadano")
        self.reservar(segundo, "periodista")
        antes = len(segundo.mensajes)
        segundo.enviar({"tipo": "iniciar"})
        segundo.esperar("error", desde=antes)
        self.assertEqual(self.servidor.fase, "sala")
        primero.enviar({"tipo": "iniciar"})
        vista1, vista2 = primero.esperar("estado"), segundo.esperar("estado")
        self.assertEqual(vista1["vista"]["mi_rol"], "ciudadano")
        self.assertEqual(vista2["vista"]["mi_rol"], "periodista")
        self.assertNotIn(primero.cliente.token, json.dumps(vista2))
        self.assertNotIn(segundo.cliente.token, json.dumps(vista1))

    def test_identidad_replay_y_tramas_invalidas_no_modifican_sala(self):
        primero, segundo = self.entrar("Uno"), self.entrar("Dos")
        antes = len(primero.mensajes)
        primero.enviar({"tipo": "reservar_rol", "rol": "ciudadano",
                        "jugador_id": segundo.cliente.id})
        primero.esperar("error", desde=antes)
        self.assertTrue(all(p.rol is None for p in self.servidor.participantes.values()))
        mensaje = {"tipo": "reservar_rol", "rol": "ciudadano",
                   "solicitud_id": "reserva-unica"}
        primero.enviar(mensaje)
        primero.esperar("sala", lambda m: "ciudadano" in m["roles_ocupados"])
        revision = self.servidor.revision
        antes = len(primero.mensajes)
        primero.enviar(mensaje)
        error = primero.esperar("error", desde=antes)
        self.assertIn("ya fue procesada", error["texto"])
        self.assertEqual(self.servidor.revision, revision)
        antes = len(primero.mensajes)
        primero.enviar({"tipo": "reservar_rol"})
        primero.esperar("error", desde=antes)
        self.assertEqual(self.servidor.participantes[primero.cliente.id].rol, "ciudadano")
        with socket.create_connection(("127.0.0.1", self.puerto), timeout=2) as bruto:
            bruto.settimeout(2)
            bruto.sendall(b"[]\n")
            with bruto.makefile("rb") as archivo:
                self.assertEqual(recibir(archivo)["tipo"], "error")
        self.assertEqual(len(self.servidor.participantes), 2)
        self.assertFalse(primero.cliente.enviar({"tipo": "examinar", "valor": float("nan")}))
        self.assertFalse(primero.cliente.enviar([]))

    def test_reconexion_reserva_identidad_y_reanuda_sin_suplantar(self):
        ciudadano, periodista, inicial, _ = self.comenzar()
        identidad, token = ciudadano.cliente.id, ciudadano.cliente.token
        antes = len(periodista.mensajes)
        ciudadano.cerrar()
        pausa = periodista.esperar("estado", lambda m: m["fase"] == "pausa", desde=antes)
        self.assertIn("Ana", pausa["vista"]["desconectados"])
        impostor = self.entrar("Intruso", token="0"*64, bienvenida=False)
        impostor.esperar("error")
        impostor.esperar("desconexion")
        restaurado = self.entrar("Nombre distinto", rol="periodista", token=token)
        bienvenida = restaurado.esperar("bienvenida")
        self.assertTrue(bienvenida["recuperada"])
        self.assertEqual(bienvenida["id"], identidad)
        estado = restaurado.esperar("estado", lambda m: m["fase"] != "pausa")
        self.assertEqual(estado["vista"]["mi_rol"], "ciudadano")
        self.assertEqual(estado["vista"]["caso"]["id"], inicial["vista"]["caso"]["id"])
        duplicado = self.entrar("Duplicado", token=token, bienvenida=False)
        self.assertIn("ya está conectado", duplicado.esperar("error")["texto"])
        duplicado.esperar("desconexion")
        antes = len(restaurado.mensajes)
        restaurado.enviar({"tipo": "sincronizar"})
        restaurado.esperar("estado", desde=antes)
        self.assertEqual(len(self.servidor.conexiones), 2)

    def test_hallazgos_privados_ambos_deciden_y_ambos_confirman(self):
        ciudadano, periodista, inicial, _ = self.comenzar()
        antes = len(periodista.mensajes)
        periodista.enviar({"tipo": "investigar", "lugar": "archivo"})
        fuente = periodista.esperar(
            "estado", lambda m: any(h["id"] == "50:documento"
                                   for h in m["vista"]["hallazgos"]), desde=antes)
        privada = ciudadano.esperar(
            "estado", lambda m: m["revision"] >= fuente["revision"])
        self.assertNotIn("50:documento", [h["id"] for h in privada["vista"]["hallazgos"]])
        ciudadano.enviar({"tipo": "solicitar_hallazgo", "evidencia_id": "50:documento"})
        periodista.esperar("estado", lambda m: m["revision"] > fuente["revision"])
        periodista.enviar({"tipo": "compartir_hallazgo", "evidencia_id": "50:documento"})
        compartida = ciudadano.esperar(
            "estado", lambda m: any(h["id"] == "50:documento"
                                   for h in m["vista"]["hallazgos"]))
        antes = len(ciudadano.mensajes)
        ciudadano.enviar({"tipo": "decidir", "accion": "compartir",
                         "titular": "El colegio cierra", "certeza": "pendiente",
                         "contactos": ["pedro"]})
        decision1 = ciudadano.esperar(
            "estado", lambda m: ciudadano.cliente.id in m["vista"]["decididos"],
            desde=antes)
        self.assertGreater(decision1["vista"]["estado"]["desinformacion"],
                           inicial["vista"]["estado"]["desinformacion"])
        periodista.esperar("estado", lambda m: m["revision"] >= decision1["revision"])
        antes = len(periodista.mensajes)
        periodista.enviar({"tipo": "decidir", "accion": "desmentir",
                          "titular": "El acta mantiene las clases", "certeza": "confirmada",
                          "evidencia_id": "50:documento", "contactos": ["carlos"]})
        decision2 = periodista.esperar(
            "estado", lambda m: m["fase"] == "resultado", desde=antes)
        self.assertLess(decision2["vista"]["estado"]["desinformacion"],
                        decision1["vista"]["estado"]["desinformacion"])
        self.assertIsNone(self.servidor.sesion.juego.arbol.buscar(50))
        self.assertEqual(len(self.servidor.sesion.juego.historial), 2)
        self.assertEqual({r["jugador_id"] for r in self.servidor.sesion.juego.historial},
                         {ciudadano.cliente.id, periodista.cliente.id})
        ciudadano.esperar("estado", lambda m: m["revision"] >= decision2["revision"])
        antes = len(ciudadano.mensajes)
        ciudadano.enviar({"tipo": "continuar"})
        espera = ciudadano.esperar(
            "estado", lambda m: ciudadano.cliente.id in m["vista"]["confirmados"],
            desde=antes)
        self.assertEqual(espera["vista"]["caso"]["id"], 50)
        periodista.esperar("estado", lambda m: m["revision"] >= espera["revision"])
        periodista.enviar({"tipo": "continuar"})
        siguiente = ciudadano.esperar("estado", lambda m: m["vista"]["caso"]["id"] == 90)
        self.assertEqual(siguiente["fase"], "investigacion")
        antes = len(ciudadano.mensajes)
        ciudadano.enviar({"tipo": "investigar", "lugar": "barrio", "caso_id": 50})
        ciudadano.esperar("error", desde=antes)
        self.assertEqual(self.servidor.sesion.caso_id, 90)

    def test_investigaciones_concurrentes_no_esperan_turno(self):
        ciudadano, periodista, _, _ = self.comenzar()
        barrera = threading.Barrier(3)
        def investigar(par, lugar):
            barrera.wait()
            par.enviar({"tipo": "investigar", "lugar": lugar})
        hilos = [
            threading.Thread(target=investigar, args=(ciudadano, "barrio")),
            threading.Thread(target=investigar, args=(periodista, "archivo")),
        ]
        for hilo in hilos:
            hilo.start()
        barrera.wait()
        for hilo in hilos:
            hilo.join(timeout=1)
        for par in (ciudadano, periodista):
            par.esperar("estado", lambda m: m["vista"]["acciones_restantes"] == 1)
        self.assertEqual(self.servidor.sesion.decisiones, {})
        self.assertEqual(self.servidor.sesion.presupuestos[ciudadano.cliente.id], 1)
        self.assertEqual(self.servidor.sesion.presupuestos[periodista.cliente.id], 1)

    def test_plazo_lo_inicia_actor_y_vence_sin_reenviar(self):
        ciudadano, periodista, inicial, _ = self.comenzar()
        self.assertIsNotNone(inicial["vista"]["segundos_decision"])
        self.assertIsNone(self.servidor.deadline)
        antes = len(periodista.mensajes)
        periodista.enviar({"tipo": "opciones_vistas"})
        periodista.esperar("error", desde=antes)
        self.assertIsNone(self.servidor.deadline)
        antes = len(ciudadano.mensajes)
        ciudadano.enviar({"tipo": "opciones_vistas"})
        reloj = ciudadano.esperar(
            "estado", lambda m: m["plazo_segundos"] is not None, desde=antes)
        self.assertGreater(reloj["plazo_segundos"], 0)
        deadline = self.servidor.deadline
        antes = len(ciudadano.mensajes)
        ciudadano.enviar({"tipo": "opciones_vistas"})
        ciudadano.esperar("estado", desde=antes)
        self.assertEqual(self.servidor.deadline, deadline)
        with self.servidor.lock:
            self.servidor.deadline = time.monotonic() - .01
        vencido = periodista.esperar(
            "estado", lambda m: ciudadano.cliente.id in m["vista"]["decididos"])
        self.assertEqual(vencido["vista"]["turno_id"], periodista.cliente.id)
        registro = self.servidor.sesion.juego.historial[-1]
        self.assertTrue(registro["por_plazo"])
        self.assertEqual(registro["accion_rol"], "ignorar")
        self.assertEqual(registro["alcance"], 0)
        self.assertIsNotNone(self.servidor.sesion.juego.arbol.buscar(50))
        self.assertIsNone(self.servidor.deadline)

    def test_plazo_se_conserva_durante_pausa_y_reconexion(self):
        ciudadano, periodista, _, _ = self.comenzar()
        ciudadano.enviar({"tipo": "opciones_vistas"})
        ciudadano.esperar("estado", lambda m: m["plazo_segundos"] is not None)
        with self.servidor.lock:
            self.servidor.deadline = time.monotonic() + 3
        token = ciudadano.cliente.token
        antes = len(periodista.mensajes)
        ciudadano.cerrar()
        pausa = periodista.esperar("estado", lambda m: m["fase"] == "pausa", desde=antes)
        restante = pausa["plazo_segundos"]
        self.assertGreater(restante, 1)
        self.assertIsNone(self.servidor.deadline)
        threading.Event().wait(.2)
        periodista.enviar({"tipo": "sincronizar"})
        otra = periodista.esperar(
            "estado", lambda m: m["fase"] == "pausa"
            and m["revision"] == pausa["revision"], desde=len(periodista.mensajes)-1)
        self.assertAlmostEqual(otra["plazo_segundos"], restante, places=2)
        recuperado = self.entrar("Ana", token=token)
        estado = recuperado.esperar("estado", lambda m: m["fase"] != "pausa")
        self.assertAlmostEqual(estado["plazo_segundos"], restante, delta=.3)

    def test_sin_limite_se_configura_antes_de_iniciar(self):
        ciudadano, periodista = self.entrar("Ana"), self.entrar("María")
        antes = len(periodista.mensajes)
        periodista.enviar({"tipo": "configurar_sala", "sin_limite": True})
        periodista.esperar("error", desde=antes)
        ciudadano.enviar({"tipo": "configurar_sala", "sin_limite": True})
        ciudadano.esperar("sala", lambda m: m["sin_limite"])
        self.reservar(ciudadano, "ciudadano")
        self.reservar(periodista, "periodista")
        ciudadano.esperar("sala", lambda m: m["puede_iniciar"])
        ciudadano.enviar({"tipo": "iniciar"})
        ciudadano.esperar("estado")
        antes = len(ciudadano.mensajes)
        ciudadano.enviar({"tipo": "opciones_vistas"})
        estado = ciudadano.esperar("estado", desde=antes)
        self.assertTrue(estado["vista"]["sin_limite"])
        self.assertIsNone(estado["plazo_segundos"])
        self.assertIsNone(self.servidor.deadline)


    def test_campana_completa_seis_casos_con_doce_decisiones(self):
        ciudadano, periodista, vista, _ = self.comenzar()
        for caso in (50, 90, 110, 40, 120, 35):
            self.assertEqual(vista["vista"]["caso"]["id"], caso)
            antes = len(ciudadano.mensajes)
            ciudadano.enviar({"tipo": "decidir", "accion": "ignorar"})
            primera = ciudadano.esperar(
                "estado", lambda m: ciudadano.cliente.id in m["vista"]["decididos"]
                and m["vista"]["caso"]["id"] == caso, desde=antes)
            periodista.esperar("estado", lambda m: m["revision"] >= primera["revision"])
            antes = len(periodista.mensajes)
            periodista.enviar({"tipo": "decidir", "accion": "reservar"})
            resultado = periodista.esperar(
                "estado", lambda m: m["fase"] == "resultado", desde=antes)
            ciudadano.esperar("estado", lambda m: m["revision"] >= resultado["revision"])
            antes = len(ciudadano.mensajes)
            ciudadano.enviar({"tipo": "continuar"})
            espera = ciudadano.esperar(
                "estado", lambda m: ciudadano.cliente.id in m["vista"]["confirmados"],
                desde=antes)
            periodista.esperar("estado", lambda m: m["revision"] >= espera["revision"])
            antes = len(ciudadano.mensajes)
            periodista.enviar({"tipo": "continuar"})
            vista = ciudadano.esperar(
                "estado", lambda m: m["fase"] in ("investigacion", "final"), desde=antes)
        self.assertEqual(vista["fase"], "final")
        self.assertIsNotNone(vista["vista"]["resultado_electoral"])
        self.assertEqual(len(self.servidor.sesion.juego.historial), 12)
        self.assertTrue(self.servidor.sesion.juego.finalizada)


    def sala_con_creador_reservado(self):
        self.servidor.cerrar()
        self.servidor = ServidorCooperativo(
            host="127.0.0.1", puerto=0, semilla=4, reservar_anfitrion=True)
        self.puerto = self.servidor.iniciar()
        self.addCleanup(self.servidor.cerrar)
        return self.servidor.token_anfitrion

    def test_invitado_llega_antes_y_solo_token_privado_identifica_creador(self):
        secreto = self.sala_con_creador_reservado()
        invitado = self.entrar("Invitado adelantado")
        sala = invitado.esperar("sala")
        self.assertIsNone(sala["anfitrion"])
        self.assertTrue(sala["esperando_creador"])
        self.reservar(invitado, "periodista")
        falso = self.entrar(
            "Falso creador", anfitrion_token="0"*64, bienvenida=False)
        self.assertIn("token privado", falso.esperar("error")["texto"])
        falso.esperar("desconexion")
        plaza = self.entrar("Segundo invitado", bienvenida=False)
        self.assertIn("plaza del creador", plaza.esperar("error")["texto"])
        plaza.esperar("desconexion")
        creador = self.entrar("Creador real", anfitrion_token=secreto)
        reservada = self.reservar(creador, "ciudadano")
        self.assertEqual(reservada["anfitrion"], creador.cliente.id)
        self.assertFalse(reservada["esperando_creador"])
        self.assertTrue(reservada["puede_iniciar"])
        antes = len(invitado.mensajes)
        invitado.enviar({"tipo": "iniciar"})
        invitado.esperar("error", desde=antes)
        creador.enviar({"tipo": "iniciar"})
        estado = creador.esperar("estado")
        self.assertEqual(estado["anfitrion"], creador.cliente.id)
        for par in (invitado, creador):
            self.assertNotIn(secreto, json.dumps(par.mensajes))
        token, identidad = creador.cliente.token, creador.cliente.id
        antes = len(invitado.mensajes)
        creador.cerrar()
        invitado.esperar("estado", lambda m: m["fase"] == "pausa", desde=antes)
        # La recuperación de una partida usa el token de sesión habitual.
        recuperado = self.entrar("Creador", token=token)
        vista = recuperado.esperar("estado", lambda m: m["fase"] != "pausa")
        self.assertEqual(vista["anfitrion"], identidad)
        self.assertEqual(recuperado.cliente.id, identidad)

    def test_creador_desconectado_en_sala_no_cede_anfitrion_al_invitado(self):
        secreto = self.sala_con_creador_reservado()
        creador = self.entrar("Creador", anfitrion_token=secreto)
        invitado = self.entrar("Invitado")
        self.reservar(creador, "ciudadano")
        self.reservar(invitado, "periodista")
        antes = len(invitado.mensajes)
        creador.cerrar()
        sala = invitado.esperar(
            "sala", lambda m: m["anfitrion"] is None, desde=antes)
        self.assertTrue(sala["esperando_creador"])
        self.assertIn("ciudadano", sala["roles_disponibles"])
        antes = len(invitado.mensajes)
        invitado.enviar({"tipo": "configurar_sala", "sin_limite": True})
        invitado.esperar("error", desde=antes)
        regreso = self.entrar("Creador", anfitrion_token=secreto)
        sala = self.reservar(regreso, "ciudadano")
        self.assertEqual(sala["anfitrion"], regreso.cliente.id)
        self.assertTrue(sala["puede_iniciar"])
        mal_token = self.entrar("Entrada invalida", token="ñ"*64, bienvenida=False)
        mal_token.esperar("error")
        mal_token.esperar("desconexion")

    def test_inicio_conserva_preferencia_de_eventos_de_la_sala(self):
        self.servidor.sesion.juego.eventos_activos = False
        _, _, vista, _ = self.comenzar()
        self.assertFalse(self.servidor.sesion.juego.eventos_activos)
        self.assertFalse(vista["vista"]["evento"]["urgente"])
        self.assertIsNone(vista["vista"]["segundos_decision"])

    def test_cierre_servidor_notifica_desconexion_y_puertos_se_validan(self):
        primero = self.entrar("Uno")
        self.servidor.cerrar()
        primero.esperar("desconexion")
        for puerto in (-1, 65536, True, "8765"):
            with self.subTest(puerto=puerto), self.assertRaises(ValueError):
                ServidorCooperativo(puerto=puerto)
        cliente = ClienteCooperativo(lambda _: None)
        with self.assertRaises(ValueError):
            cliente.conectar("127.0.0.1", 0, "Uno")
        servidor_lan = ServidorCooperativo(puerto=0)
        self.addCleanup(servidor_lan.cerrar)
        servidor_lan.iniciar()
        self.assertEqual(servidor_lan.socket.getsockname()[0], "0.0.0.0")


if __name__ == "__main__":
    unittest.main()
