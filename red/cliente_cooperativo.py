"""Cliente TCP asíncrono de la investigación cooperativa.

El callback se ejecuta en un hilo de red. Una interfaz Qt debe reenviarlo a
una señal antes de actualizar sus widgets.
"""
from __future__ import annotations

import queue
import secrets
import socket
import threading

from red.protocolo import codificar, recibir

_COMANDOS_CASO = frozenset((
    "investigar", "examinar", "entrevistar", "compartir_hallazgo",
    "solicitar_hallazgo", "proponer", "decidir", "continuar", "prever_alcance", "opciones_vistas",
))


class ClienteCooperativo:
    def __init__(self, callback):
        if not callable(callback):
            raise ValueError("El cliente necesita un receptor de mensajes")
        self.callback = callback
        self.socket = None
        self.cerrado = threading.Event()
        self.hilo = None
        self._hilo_envio = None
        self._pendientes = queue.Queue(maxsize=64)
        self._lock = threading.Lock()
        self._prefijo = secrets.token_hex(8)
        self._secuencia = 0
        self._revision = None
        self._caso_id = None
        self.id = None
        self.token = None

    def conectar(self, host, puerto, nombre, rol=None, token=None, anfitrion_token=None):
        if self.hilo is not None or self.cerrado.is_set():
            raise ValueError("Crea un cliente nuevo para otra conexión")
        if not isinstance(host, str) or not host.strip() or len(host) > 253:
            raise ValueError("Escribe la dirección del servidor")
        if type(puerto) is not int or not 1 <= puerto <= 65535:
            raise ValueError("El puerto debe estar entre 1 y 65535")
        if not isinstance(nombre, str) or not 1 <= len(nombre.strip()) <= 24:
            raise ValueError("Escribe un nombre de entre 1 y 24 caracteres")
        self.hilo = threading.Thread(
            target=self._leer, args=(host.strip(), puerto, nombre.strip(), rol, token, anfitrion_token),
            name="civica-coop-cliente", daemon=True)
        self.hilo.start()

    def _leer(self, host, puerto, nombre, rol, token, anfitrion_token):
        try:
            conexion = socket.create_connection((host, puerto), timeout=4)
            with self._lock:
                if self.cerrado.is_set():
                    conexion.close()
                    return
                self.socket = conexion
            conexion.settimeout(None)
            self._hilo_envio = threading.Thread(
                target=self._escribir, name="civica-coop-envio", daemon=True)
            self._hilo_envio.start()
            self.enviar({"tipo": "registro", "nombre": nombre, "rol": rol, "token": token,
                         "anfitrion_token": anfitrion_token})
            with conexion.makefile("rb") as archivo:
                while not self.cerrado.is_set():
                    mensaje = recibir(archivo)
                    if mensaje is None:
                        break
                    self._actualizar_contexto(mensaje)
                    self.callback(mensaje)
        except (OSError, ValueError, RecursionError) as error:
            if not self.cerrado.is_set():
                self.callback({"tipo": "error", "texto": str(error)})
        finally:
            avisar = not self.cerrado.is_set()
            self.cerrar()
            if avisar:
                self.callback({"tipo": "desconexion",
                               "texto": "Se cerró la conexión con la sala de investigación."})

    def _actualizar_contexto(self, mensaje):
        with self._lock:
            tipo = mensaje.get("tipo")
            if tipo == "bienvenida":
                self.id, self.token = mensaje["id"], mensaje["token"]
            elif tipo in ("sala", "estado"):
                self._revision = mensaje.get("revision")
                vista = mensaje.get("vista", {})
                caso = vista.get("caso") or {}
                self._caso_id = caso.get("id")

    def enviar(self, mensaje):
        if not isinstance(mensaje, dict) or not isinstance(mensaje.get("tipo"), str):
            return False
        with self._lock:
            if self.socket is None or self.cerrado.is_set():
                return False
            datos = dict(mensaje)
            tipo = datos["tipo"]
            if tipo not in ("registro", "sincronizar"):
                self._secuencia += 1
                datos.setdefault("solicitud_id", f"{self._prefijo}:{self._secuencia}")
            if tipo in _COMANDOS_CASO:
                datos.setdefault("revision", self._revision)
                datos.setdefault("caso_id", self._caso_id)
        try:
            self._pendientes.put_nowait(codificar(datos))
            return True
        except (queue.Full, ValueError, TypeError):
            return False

    def _escribir(self):
        while not self.cerrado.is_set():
            try:
                datos = self._pendientes.get(timeout=.15)
            except queue.Empty:
                continue
            try:
                self.socket.sendall(datos)
            except OSError:
                # El lector recibirá el cierre y emitirá una sola desconexión.
                try:
                    self.socket.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                break

    def cerrar(self):
        self.cerrado.set()
        with self._lock:
            conexion = self.socket
        if conexion is not None:
            try:
                conexion.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            conexion.close()
