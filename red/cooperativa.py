"""Servidor TCP autoritativo para dos investigadores en la misma LAN.

La sala admite dos observadores antes de reservar roles. Cada mensaje de juego
se aplica con la identidad de su conexión; las vistas nunca incluyen el token
del compañero ni sus hallazgos privados.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import copy
import base64
import json
import zlib
import math
import queue
import secrets
import socket
import threading
import time

from juego.investigacion import SesionInvestigacion
from red.protocolo import codificar, recibir

ROLES_COOPERATIVOS = ("ciudadano", "periodista")
_COMANDOS_CASO = frozenset((
    "investigar", "examinar", "entrevistar", "compartir_hallazgo",
    "solicitar_hallazgo", "proponer", "decidir", "continuar", "prever_alcance", "opciones_vistas",
))


def direcciones_lan():
    """Direcciones del equipo para mostrar en la sala; no modifica la red."""
    try:
        direcciones = {
            dato[4][0] for dato in socket.getaddrinfo(
                socket.gethostname(), None, socket.AF_INET, socket.SOCK_STREAM)
            if not dato[4][0].startswith(("127.", "169.254."))
        }
    except OSError:
        direcciones = set()
    return sorted(direcciones)


@dataclass
class _Participante:
    id: str
    nombre: str
    token: str
    rol: str | None = None
    solicitudes: set[str] = field(default_factory=set)


@dataclass
class _Conexion:
    socket: socket.socket
    pendientes: queue.Queue = field(default_factory=lambda: queue.Queue(maxsize=64))
    cerrada: threading.Event = field(default_factory=threading.Event)


class ServidorCooperativo:
    """Dos participantes, roles exclusivos y decisiones oficiales en el servidor."""

    def __init__(self, host="0.0.0.0", puerto=8765, semilla=4, sin_limite=False,
                 reservar_anfitrion=False):
        if not isinstance(host, str) or not host.strip():
            raise ValueError("La dirección del servidor no es válida")
        if type(puerto) is not int or not 0 <= puerto <= 65535:
            raise ValueError("El puerto debe estar entre 1 y 65535; cero asigna uno libre")
        if type(sin_limite) is not bool:
            raise ValueError("La preferencia sin limite debe ser booleana")
        if type(reservar_anfitrion) is not bool:
            raise ValueError("La reserva del creador debe ser booleana")
        self.reservar_anfitrion = reservar_anfitrion
        self.token_anfitrion = secrets.token_hex(32)
        self.sin_limite = sin_limite
        self.host, self.puerto, self.semilla = host.strip(), puerto, semilla
        self.sesion = SesionInvestigacion(semilla=semilla, cooperativa=True)
        self.lock = threading.RLock()
        self.detener = threading.Event()
        self.socket = None
        self.hilo = None
        self.participantes = {}
        self.conexiones = {}
        self.anfitrion = None
        self.revision = 0
        self._activa = False
        self._pausada = False
        self.deadline = None
        self._turno_reloj = None
        self._tiempo_pausado = None
        self._secuencia = 0
        self._hilos = []
        self._registrando = set()
        self._direcciones_lan = direcciones_lan()

    @property
    def fase(self):
        if not self._activa:
            return "sala"
        return "pausa" if self._pausada else self.sesion.fase

    def iniciar(self):
        if self.socket is not None or self.detener.is_set():
            raise ValueError("Este servidor ya se inició o se cerró")
        escucha = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            escucha.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            escucha.bind((self.host, self.puerto))
            escucha.listen(4)
            escucha.settimeout(.15)
        except OSError:
            escucha.close()
            raise
        self.socket = escucha
        self.puerto = escucha.getsockname()[1]
        self.hilo = self._lanzar(self._aceptar, nombre="civica-coop-aceptar")
        return self.puerto

    def _lanzar(self, funcion, args=(), nombre="civica-coop"):
        hilo = threading.Thread(target=funcion, args=args, name=nombre, daemon=True)
        self._hilos.append(hilo)
        hilo.start()
        return hilo

    def _aceptar(self):
        while not self.detener.is_set():
            try:
                cliente, _ = self.socket.accept()
                cliente.settimeout(4)
                with self.lock:
                    self._registrando.add(cliente)
                self._lanzar(self._atender, (cliente,), "civica-coop-lector")
            except socket.timeout:
                pass
            except OSError:
                break
            with self.lock:
                self._comprobar_plazo()

    def _enviar(self, conexion, mensaje):
        try:
            conexion.pendientes.put_nowait(codificar(mensaje))
        except (queue.Full, ValueError, TypeError):
            self._cerrar_conexion(conexion)

    @staticmethod
    def _cerrar_socket(cliente):
        try:
            cliente.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        cliente.close()

    def _cerrar_conexion(self, conexion):
        conexion.cerrada.set()
        self._cerrar_socket(conexion.socket)

    def _escribir(self, conexion):
        while not self.detener.is_set() and not conexion.cerrada.is_set():
            try:
                datos = conexion.pendientes.get(timeout=.15)
            except queue.Empty:
                continue
            try:
                conexion.socket.sendall(datos)
            except OSError:
                self._cerrar_conexion(conexion)
                break

    def _disponibles(self):
        ocupados = {p.rol for p in self.participantes.values() if p.rol}
        return [rol for rol in ROLES_COOPERATIVOS if rol not in ocupados]

    def _jugadores_publicos(self):
        return [
            {"id": p.id, "nombre": p.nombre, "rol": p.rol,
             "conectado": p.id in self.conexiones}
            for p in self.participantes.values()
        ]

    def _puede_iniciar(self):
        return (not self._activa and len(self.participantes) == 2
                and len(self.conexiones) == 2 and not self._disponibles()
                and self.anfitrion in self.conexiones)

    def _mensaje_sala(self, jugador_id):
        return {
            "tipo": "sala", "jugadores": self._jugadores_publicos(),
            "roles_disponibles": self._disponibles(),
            "roles_ocupados": {
                p.rol: {"id": p.id, "nombre": p.nombre}
                for p in self.participantes.values() if p.rol
            },
            "puede_iniciar": self._puede_iniciar(), "anfitrion": self.anfitrion,
            "sin_limite": self.sin_limite,
            "esperando_creador": self.reservar_anfitrion and self.anfitrion is None,
            "mi_id": jugador_id, "revision": self.revision,
            "puerto": self.puerto, "direcciones_lan": list(self._direcciones_lan),
        }

    def _mensaje_estado(self, jugador_id):
        vista = copy.deepcopy(self.sesion.vista(jugador_id))
        vista["mi_id"] = jugador_id
        vista["revision"] = self.revision
        vista["fase_previa"] = self.sesion.fase
        vista["fase"] = self.fase
        vista["sin_limite"] = self.sin_limite
        vista["plazo_segundos"] = self._plazo_restante()
        vista["desconectados"] = [
            p.nombre for p in self.participantes.values() if p.id not in self.conexiones
        ]
        for jugador in vista.get("jugadores", []):
            jugador["conectado"] = jugador.get("id") in self.conexiones
        mensaje = {"tipo": "estado", "vista": vista, "revision": self.revision,
                   "fase": self.fase, "anfitrion": self.anfitrion, "mi_id": jugador_id,
                   "plazo_segundos": self._plazo_restante()}
        # Juego no contiene el archivo privado de hallazgos de SesionInvestigacion.
        # La copia permite dibujar las escenas originales sin ejecutar reglas locales.
        datos = self.sesion.juego.datos()
        mensaje["datos"] = datos
        try:
            codificar(mensaje)
        except ValueError:
            # Se conserva el límite del protocolo aun al crecer el historial.
            del mensaje["datos"]
            contenido = json.dumps(datos, ensure_ascii=False, allow_nan=False).encode("utf-8")
            mensaje["datos_comprimidos"] = base64.b64encode(
                zlib.compress(contenido, 6)).decode("ascii")
        return mensaje

    def _publicar(self):
        for jugador_id, conexion in list(self.conexiones.items()):
            mensaje = (self._mensaje_estado(jugador_id) if self._activa
                       else self._mensaje_sala(jugador_id))
            self._enviar(conexion, mensaje)

    def _registrar(self, registro):
        token = registro.get("token")
        if token is not None:
            if (not isinstance(token, str) or not token.isascii()
                    or not 16 <= len(token) <= 128):
                raise ValueError("El token de reconexión no es válido")
            participante = next((
                p for p in self.participantes.values()
                if secrets.compare_digest(p.token, token)
            ), None)
            if participante is None:
                raise ValueError("No se reconoce la sesión; vuelve a entrar a la sala")
            if participante.id in self.conexiones:
                raise ValueError("Ese participante ya está conectado")
            return participante, True
        if self._activa:
            raise ValueError("La partida ya comenzó; solo sus participantes pueden reconectar")
        creador = registro.get("anfitrion_token")
        if creador is not None:
            if (not isinstance(creador, str) or not creador.isascii()
                    or len(creador) != 64
                    or not secrets.compare_digest(creador, self.token_anfitrion)):
                raise ValueError("El token privado del creador no es válido")
            if self.anfitrion is not None:
                raise ValueError("El creador de la sala ya está conectado")
        if len(self.participantes) >= 2:
            raise ValueError("Esta sala admite exactamente dos participantes")
        if (self.reservar_anfitrion and self.anfitrion is None
                and creador is None and len(self.participantes) >= 1):
            raise ValueError("La plaza del creador de esta sala está reservada")
        nombre, rol = registro.get("nombre"), registro.get("rol")
        if (not isinstance(nombre, str) or not 1 <= len(nombre.strip()) <= 24
                or any(ord(letra) < 32 for letra in nombre)):
            raise ValueError("Escribe un nombre de entre 1 y 24 caracteres")
        self._validar_rol(rol)
        self._secuencia += 1
        jugador_id = f"investigador_{self._secuencia}"
        participante = _Participante(jugador_id, nombre.strip(), secrets.token_hex(32), rol)
        self.participantes[jugador_id] = participante
        if creador is not None or (self.anfitrion is None and not self.reservar_anfitrion):
            self.anfitrion = jugador_id
        return participante, False

    def _validar_rol(self, rol, jugador_id=None):
        if rol is not None and rol not in ROLES_COOPERATIVOS:
            raise ValueError("Elige Ciudadano o Periodista")
        if rol is not None and any(
                p.rol == rol and p.id != jugador_id for p in self.participantes.values()):
            raise ValueError("Ese rol acaba de ser reservado por tu compañero")

    def _atender(self, cliente):
        jugador_id, conexion = None, None
        try:
            with cliente.makefile("rb") as archivo:
                registro = recibir(archivo)
                if registro is None or registro.get("tipo") != "registro":
                    raise ValueError("Primero debes entrar a la sala")
                with self.lock:
                    if self.detener.is_set():
                        return
                    participante, recuperada = self._registrar(registro)
                    jugador_id = participante.id
                    conexion = _Conexion(cliente)
                    self.conexiones[jugador_id] = conexion
                    self._registrando.discard(cliente)
                    cliente.settimeout(None)
                    self._lanzar(self._escribir, (conexion,), "civica-coop-escritor")
                    if self._activa:
                        self._pausada = len(self.conexiones) != 2
                        if not self._pausada and self._tiempo_pausado is not None:
                            self.deadline = time.monotonic() + self._tiempo_pausado
                            self._tiempo_pausado = None
                    self.revision += 1
                    self._enviar(conexion, {
                        "tipo": "bienvenida", "id": jugador_id,
                        "token": participante.token, "recuperada": recuperada,
                    })
                    self._publicar()
                while not self.detener.is_set():
                    mensaje = recibir(archivo)
                    if mensaje is None:
                        break
                    with self.lock:
                        if self.conexiones.get(jugador_id) is not conexion:
                            break
                        try:
                            self._procesar(jugador_id, mensaje)
                        except (ValueError, KeyError, TypeError) as error:
                            self._enviar(conexion, {
                                "tipo": "error", "texto": str(error),
                                "solicitud_id": mensaje.get("solicitud_id"),
                            })
                            self._enviar(conexion, (
                                self._mensaje_estado(jugador_id) if self._activa
                                else self._mensaje_sala(jugador_id)))
        except (OSError, ValueError, RecursionError) as error:
            if conexion is None:
                try:
                    cliente.settimeout(.5)
                    cliente.sendall(codificar({"tipo": "error", "texto": str(error)}))
                except OSError:
                    pass
        finally:
            with self.lock:
                self._registrando.discard(cliente)
                if jugador_id is not None and self.conexiones.get(jugador_id) is conexion:
                    del self.conexiones[jugador_id]
                    if not self._activa:
                        self.participantes.pop(jugador_id, None)
                        if self.anfitrion == jugador_id:
                            self.anfitrion = (None if self.reservar_anfitrion
                                              else next(iter(self.participantes), None))
                    else:
                        if not self._pausada and self.deadline is not None:
                            self._tiempo_pausado = self._plazo_restante()
                        self.deadline = None
                        self._pausada = True
                    self.revision += 1
                    if not self.detener.is_set():
                        self._publicar()
            if conexion is not None:
                self._cerrar_conexion(conexion)
            else:
                self._cerrar_socket(cliente)

    def _caso_actual(self, jugador_id):
        return self.sesion.vista(jugador_id)["caso"]["id"]

    @staticmethod
    def _validar_numeros(valor):
        if isinstance(valor, float) and not math.isfinite(valor):
            raise ValueError("El mensaje contiene un número no válido")
        if isinstance(valor, dict):
            for item in valor.values():
                ServidorCooperativo._validar_numeros(item)
        elif isinstance(valor, list):
            for item in valor:
                ServidorCooperativo._validar_numeros(item)

    def _solicitud(self, jugador, mensaje):
        solicitud = mensaje.get("solicitud_id")
        if not isinstance(solicitud, str) or not 1 <= len(solicitud) <= 100:
            raise ValueError("La acción necesita un identificador de solicitud")
        if solicitud in jugador.solicitudes:
            raise ValueError("Esta solicitud ya fue procesada")
        if len(jugador.solicitudes) >= 8192:
            raise ValueError("La sesión alcanzó su límite de solicitudes")
        jugador.solicitudes.add(solicitud)

    def _procesar(self, jugador_id, mensaje):
        self._comprobar_plazo()
        tipo = mensaje.get("tipo")
        self._validar_numeros(mensaje)
        jugador = self.participantes[jugador_id]
        if any(mensaje.get(campo, jugador_id) != jugador_id for campo in ("jugador_id", "mi_id")):
            raise ValueError("La acción no pertenece al participante conectado")
        if tipo == "sincronizar":
            self._enviar(self.conexiones[jugador_id], (
                self._mensaje_estado(jugador_id) if self._activa
                else self._mensaje_sala(jugador_id)))
            return
        if tipo == "configurar_sala":
            if self._activa or jugador_id != self.anfitrion:
                raise ValueError("El anfitrion configura el plazo antes de iniciar")
            if type(mensaje.get("sin_limite")) is not bool:
                raise ValueError("La preferencia sin limite debe ser booleana")
            self._solicitud(jugador, mensaje)
            self.sin_limite = mensaje["sin_limite"]
        elif tipo == "reservar_rol":
            if "rol" not in mensaje:
                raise ValueError("La reserva debe indicar un rol, o null para liberarlo")
            if self._activa:
                raise ValueError("Los roles no se cambian durante una partida")
            self._validar_rol(mensaje.get("rol"), jugador_id)
            self._solicitud(jugador, mensaje)
            jugador.rol = mensaje.get("rol")
        elif tipo == "iniciar":
            if jugador_id != self.anfitrion or not self._puede_iniciar():
                raise ValueError("El anfitrión inicia cuando ambos han reservado roles diferentes")
            self._solicitud(jugador, mensaje)
            sesion = SesionInvestigacion(semilla=self.semilla, cooperativa=True)
            sesion.juego.eventos_activos = self.sesion.juego.eventos_activos
            for participante in self.participantes.values():
                sesion.registrar_jugador(participante.nombre, participante.rol, id=participante.id)
            sesion.comenzar()
            self.sesion, self._activa, self._pausada = sesion, True, False
        elif tipo in _COMANDOS_CASO:
            if not self._activa or self._pausada:
                raise ValueError("Esperando a los dos investigadores conectados")
            if mensaje.get("caso_id") != self._caso_actual(jugador_id):
                raise ValueError("El caso ya cambió; actualiza la investigación")
            revision = mensaje.get("revision")
            if type(revision) is not int or not 0 <= revision <= self.revision:
                raise ValueError("La revisión de la partida no es válida")
            if tipo in ("decidir", "continuar") and revision != self.revision:
                raise ValueError("Hay cambios nuevos; revisa el estado antes de confirmar")
            self._solicitud(jugador, mensaje)
            if tipo == "opciones_vistas":
                self._iniciar_plazo(jugador_id)
            else:
                self._aplicar(jugador_id, mensaje)
        else:
            raise ValueError("Comando de la sala desconocido")
        self._actualizar_reloj()
        self.revision += 1
        self._publicar()

    def _aplicar(self, jugador_id, mensaje):
        tipo = mensaje["tipo"]
        if tipo == "investigar":
            self.sesion.investigar(jugador_id, mensaje.get("lugar"), mensaje.get("interaccion"))
        elif tipo == "examinar":
            self.sesion.examinar(jugador_id, mensaje.get("medio"), mensaje.get("valor"))
        elif tipo == "entrevistar":
            self.sesion.entrevistar(jugador_id, mensaje.get("pregunta"), mensaje.get("evidencia"))
        elif tipo in ("compartir_hallazgo", "solicitar_hallazgo"):
            getattr(self.sesion, tipo)(jugador_id, mensaje.get("evidencia_id"))
        elif tipo in ("proponer", "decidir"):
            getattr(self.sesion, tipo)(
                jugador_id, mensaje.get("accion"), titular=mensaje.get("titular", ""),
                certeza=mensaje.get("certeza", "pendiente"),
                evidencia_id=mensaje.get("evidencia_id"), contactos=mensaje.get("contactos"),
            )
        elif tipo == "continuar":
            self.sesion.continuar(jugador_id)
        elif tipo == "prever_alcance":
            self.sesion.prever_alcance(jugador_id, mensaje.get("contactos"))


    def _plazo_restante(self):
        if self._pausada:
            return self._tiempo_pausado
        if self.deadline is None:
            return None
        return max(0., self.deadline-time.monotonic())

    def _actualizar_reloj(self):
        if not self._activa:
            return
        vista = self.sesion.vista(next(iter(self.participantes)))
        clave = (vista["caso"]["id"], vista.get("turno_id"))
        if clave != self._turno_reloj or self.sesion.fase not in ("investigacion", "decision"):
            self._turno_reloj = clave
            self.deadline = None
            self._tiempo_pausado = None

    def _iniciar_plazo(self, jugador_id):
        vista = self.sesion.vista(jugador_id)
        if vista.get("turno_id") != jugador_id:
            raise ValueError("Solo el participante activo presenta sus opciones")
        if self.sin_limite or vista.get("segundos_decision") is None:
            return
        self._actualizar_reloj()
        segundos = vista["segundos_decision"]
        if self.deadline is None and segundos > 0:
            self.deadline = time.monotonic()+segundos

    def _comprobar_plazo(self):
        if (self._activa and not self._pausada and self.deadline is not None
                and time.monotonic() >= self.deadline):
            vista = self.sesion.vista(next(iter(self.participantes)))
            actor = vista.get("turno_id")
            self.deadline = None
            if actor is not None and self.sesion.fase in ("investigacion", "decision"):
                self.sesion.expirar_turno(actor)
                self._actualizar_reloj()
                self.revision += 1
                self._publicar()

    def cerrar(self):
        if self.detener.is_set():
            return
        self.detener.set()
        if self.socket is not None:
            self._cerrar_socket(self.socket)
        with self.lock:
            conexiones = list(self.conexiones.values())
            pendientes = list(self._registrando)
        for conexion in conexiones:
            self._cerrar_conexion(conexion)
        for cliente in pendientes:
            self._cerrar_socket(cliente)
        actual = threading.current_thread()
        for hilo in list(self._hilos):
            if hilo is not actual and hilo.is_alive():
                hilo.join(timeout=.15)
