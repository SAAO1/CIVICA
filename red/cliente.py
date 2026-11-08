import socket
import threading
import queue
from red.protocolo import codificar, recibir


class Cliente:
    def __init__(self, callback):
        self.callback = callback
        self.socket = None
        self.cerrado = threading.Event()
        self.envio_lock = threading.Lock()
        self.pendientes = queue.Queue(maxsize=64)

    def conectar(self, host, puerto, nombre, rol, token=None):
        def trabajo():
            try:
                self.socket = socket.create_connection((host, puerto), timeout=4)
                self.socket.settimeout(None)
                threading.Thread(target=self._escribir, daemon=True).start()
                self.enviar({"tipo": "registro", "nombre": nombre, "rol": rol, "token": token})
                with self.socket.makefile("rb") as archivo:
                    while not self.cerrado.is_set():
                        mensaje = recibir(archivo)
                        if mensaje is None:
                            break
                        self.callback(mensaje)
            except (OSError, ValueError) as error:
                if not self.cerrado.is_set():
                    self.callback({"tipo": "error", "texto": str(error)})
            finally:
                if not self.cerrado.is_set():
                    self.callback({"tipo": "desconexion", "texto": "Se cerró la conexión con el servidor."})
                self.cerrar()
        self.hilo = threading.Thread(target=trabajo, daemon=True)
        self.hilo.start()

    def enviar(self, mensaje):
        if self.socket is None or self.cerrado.is_set():
            return False
        try:
            self.pendientes.put_nowait(codificar(mensaje))
            return True
        except (queue.Full, ValueError) as error:
            self.callback({"tipo": "error", "texto": str(error)})
            return False

    def _escribir(self):
        while not self.cerrado.is_set():
            try:
                datos = self.pendientes.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                self.socket.sendall(datos)
            except OSError as error:
                if not self.cerrado.is_set():
                    self.callback({"tipo": "desconexion", "texto": str(error)})
                self.cerrar()
                break

    def cerrar(self):
        self.cerrado.set()
        if self.socket is not None:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self.socket.close()
