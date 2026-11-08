import socket
import threading
import time
import queue
import secrets

from juego.partida import Juego
from juego.acciones import accion_permitida, accion_por_defecto
from models.jugador import Jugador, ROLES_JUGABLES
from red.protocolo import codificar, recibir


class Servidor:
    """Servidor autoritativo local. Una decisión por publicación y barrera de lectura."""

    def __init__(self, host="127.0.0.1", puerto=8765, semilla=None, eventos=True, sin_limite=False,
                 campana="clasica"):
        self.host, self.puerto = host, puerto
        self.juego = Juego(semilla, eventos, campana=campana)
        self.juego.jugadores = []
        self.sin_limite = sin_limite
        self.conexiones = {}
        self.colas = {}
        self.lock = threading.RLock()
        self.detener = threading.Event()
        self.fase = "sala"
        self.revision = 0
        self.listos = set()
        self.secuencia = 0
        self.tokens = {}
        self.fase_antes_pausa = None
        self.tiempo_pausado = None
        self.deadline = None
        self.socket = None

    def iniciar(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.puerto))
        self.puerto = self.socket.getsockname()[1]
        self.socket.listen(4)
        self.socket.settimeout(0.2)
        self.hilo = threading.Thread(target=self._aceptar, daemon=True)
        self.hilo.start()
        return self.puerto

    def _aceptar(self):
        while not self.detener.is_set():
            try:
                cliente, _ = self.socket.accept()
                cliente.settimeout(5)
                threading.Thread(target=self._atender, args=(cliente,), daemon=True).start()
            except socket.timeout:
                pass
            except OSError:
                break
            with self.lock:
                self._timeout()

    def _enviar(self, cliente, mensaje):
        datos = codificar(mensaje)
        if cliente in self.colas:
            try:
                self.colas[cliente].put_nowait(datos)
            except queue.Full:
                try:
                    cliente.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
            return
        try:
            cliente.sendall(datos)
        except OSError:
            pass  # El lector de la conexión ejecuta la limpieza del participante.

    def _escribir(self, cliente, pendientes):
        while not self.detener.is_set() and cliente in self.colas:
            try:
                datos = pendientes.get(timeout=.2)
            except queue.Empty:
                continue
            try:
                cliente.sendall(datos)
            except OSError:
                break

    def _publicar(self):
        if self.fase == "sala":
            mensaje = {"tipo": "sala", "jugadores": [vars(j) for j in self.juego.jugadores],
                       "anfitrion": self.juego.jugadores[0].id if self.juego.jugadores else None}
        else:
            mensaje = {"tipo": "estado", "fase": self.fase, "revision": self.revision,
                       "datos": self.juego.datos(), "esperando": sorted(self.listos),
                       "desconectados": [j.nombre for j in self.juego.jugadores if j.id not in self.conexiones],
                       "plazo_segundos": max(0, self.deadline-time.monotonic()) if self.deadline else None}
        for cliente in list(self.conexiones.values()):
            self._enviar(cliente, mensaje)

    def _plazo(self):
        self.deadline = None
        if self.juego.evento_actual.urgente and not self.sin_limite:
            self.deadline = time.monotonic() + self.juego.evento_actual.segundos

    def _timeout(self):
        if self.fase == "jugando" and self.deadline is not None and time.monotonic() >= self.deadline:
            self.juego.ejecutar_accion(accion_por_defecto(self.juego.jugador.rol), self.juego.jugador.id)
            self.deadline = None
            self.fase = "resultado"
            self.revision += 1
            self._publicar()

    def _atender(self, cliente):
        id = None
        try:
            with cliente.makefile("rb") as archivo:
                registro = recibir(archivo)
                with self.lock:
                    if registro is None or registro["tipo"] != "registro":
                        raise ValueError("Primero debes registrarte")
                    token = registro.get("token")
                    recuperado = next((j for j in self.juego.jugadores
                                       if isinstance(token, str) and secrets.compare_digest(self.tokens.get(j.id, ""), token)), None)
                    if recuperado is not None:
                        if recuperado.id in self.conexiones:
                            raise ValueError("Ese participante ya está conectado")
                        id = recuperado.id
                    else:
                        if token:
                            raise ValueError("No se reconoce esta sesión de reconexión")
                        if self.fase != "sala" or len(self.juego.jugadores) >= 4:
                            raise ValueError("La sala está llena o ya comenzó")
                        id = self._registrar(registro)
                    self.conexiones[id] = cliente
                    pendientes = queue.Queue(maxsize=64)
                    self.colas[cliente] = pendientes
                    threading.Thread(target=self._escribir, args=(cliente, pendientes), daemon=True).start()
                    cliente.settimeout(None)
                    self._enviar(cliente, {"tipo": "bienvenida", "id": id, "token": self.tokens[id],
                                           "recuperada": recuperado is not None})
                    if self.fase == "interrumpida" and len(self.conexiones) == len(self.juego.jugadores):
                        self.fase = self.fase_antes_pausa
                        self.fase_antes_pausa = None
                        if self.tiempo_pausado is not None and self.fase == "jugando":
                            self.deadline = time.monotonic() + self.tiempo_pausado
                        self.tiempo_pausado = None
                        self.revision += 1
                    self._publicar()
                while not self.detener.is_set():
                    mensaje = recibir(archivo)
                    if mensaje is None:
                        break
                    with self.lock:
                        try:
                            self._procesar(id, mensaje)
                        except (ValueError, KeyError, TypeError) as error:
                            self._enviar(cliente, {"tipo": "error", "texto": str(error)})
        except (OSError, ValueError) as error:
            self._enviar(cliente, {"tipo": "error", "texto": str(error)})
        finally:
            with self.lock:
                if self.conexiones.get(id) is cliente:
                    del self.conexiones[id]
                    self.colas.pop(cliente, None)
                    if self.fase == "sala":
                        self.juego.jugadores = [j for j in self.juego.jugadores if j.id != id]
                        self.tokens.pop(id, None)
                    elif self.fase not in ("interrumpida", "final") and not self.detener.is_set():
                        self.fase_antes_pausa = self.fase
                        self.tiempo_pausado = max(0, self.deadline-time.monotonic()) if self.deadline else None
                        self.fase = "interrumpida"
                        self.deadline = None
                        self.revision += 1
                    self._publicar()
            cliente.close()

    def _registrar(self, registro):
        nombre, rol = registro.get("nombre"), registro.get("rol")
        if not isinstance(nombre, str) or not 1 <= len(nombre.strip()) <= 30 or not isinstance(rol, str) or rol not in ROLES_JUGABLES:
            raise ValueError("Nombre o rol inválido")
        self.secuencia += 1
        id = f"jugador_{self.secuencia}"
        ciudadanos = ("ana", "maria", "carlos", "sofia")
        ocupados = {j.ciudadano_id for j in self.juego.jugadores}
        ciudadano = next(c for c in ciudadanos if c not in ocupados)
        self.juego.jugadores.append(Jugador(id, nombre.strip(), rol, ciudadano))
        self.tokens[id] = secrets.token_hex(24)
        return id

    def _procesar(self, id, mensaje):
        self._timeout()
        tipo = mensaje["tipo"]
        if tipo == "iniciar":
            if self.fase != "sala" or len(self.juego.jugadores) < 2 or id != self.juego.jugadores[0].id:
                raise ValueError("El anfitrión inicia con dos a cuatro jugadores")
            self.juego.iniciar_primera_publicacion()
            self.fase = "jugando"
            self.revision += 1
            self.deadline = None  # Se inicia cuando el jugador presenta las opciones.
        elif tipo == "accion":
            if self.fase != "jugando" or mensaje.get("publicacion_id") != self.juego.publicacion_actual_id:
                raise ValueError("La publicación o la fase ya cambió")
            if not accion_permitida(mensaje.get("accion"), self.juego.jugador.rol):
                raise ValueError("Esa decisión no pertenece al oficio del participante de turno")
            if not self.juego.ejecutar_accion(mensaje.get("accion"), id):
                raise ValueError("Acción inválida, repetida o fuera de turno")
            self.deadline = None
            self.fase = "resultado"
            self.revision += 1
        elif tipo == "continuar":
            if self.fase != "resultado" or mensaje.get("revision") != self.revision:
                raise ValueError("Todavía no hay un resultado para continuar")
            self.listos.add(id)
            if self.listos == set(self.conexiones):
                self.listos.clear()
                self.fase = "jugando" if self.juego.avanzar_publicacion() else "final"
                self.revision += 1
                self.deadline = None
        elif tipo == "decision_lista":
            if self.fase == "jugando" and id == self.juego.jugador.id and mensaje.get("publicacion_id") == self.juego.publicacion_actual_id and self.deadline is None:
                self._plazo()
        elif tipo == "sincronizar":
            pass
        else:
            raise ValueError("Tipo de mensaje desconocido")
        self._publicar()

    def cerrar(self):
        self.detener.set()
        if self.socket is not None:
            self.socket.close()
        with self.lock:
            for cliente in self.conexiones.values():
                try:
                    cliente.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                cliente.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Servidor local de CIVICA")
    parser.add_argument("--puerto", type=int, default=8765)
    parser.add_argument("--campana", choices=Juego.CAMPANAS, default="clasica")
    args = parser.parse_args()
    servidor = Servidor(puerto=args.puerto, campana=args.campana)
    servidor.iniciar()
    print(f"Sala CIVICA en 127.0.0.1:{servidor.puerto}")
    try:
        servidor.hilo.join()
    except KeyboardInterrupt:
        servidor.cerrar()
