"""Puente TCP para conservar las escenas originales de CIVICA."""
from __future__ import annotations

import base64
import copy
import json
import threading
import zlib

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QDialog

from juego.partida import Juego
from juego.propagacion import ResultadoPropagacion
from red.cliente_cooperativo import ClienteCooperativo
from red.cooperativa import ServidorCooperativo
from interfaz.novela.sala import SalaCooperativaNovela


def reconstruir_juego_novela(mensaje, vista):
    """Copia de presentación: el estado oficial permanece en el servidor."""
    datos = mensaje.get("datos")
    if datos is None and mensaje.get("datos_comprimidos"):
        comprimido = base64.b64decode(mensaje["datos_comprimidos"], validate=True)
        lector = zlib.decompressobj()
        contenido = lector.decompress(comprimido, 2*1024*1024)
        if not lector.eof or lector.unconsumed_tail:
            raise ValueError("La copia de la novela es demasiado grande o está incompleta")
        datos = json.loads(contenido.decode("utf-8"))
    if not isinstance(datos, dict):
        raise ValueError("La sala no envió el estado público de la novela")
    juego = Juego.desde_datos(datos)
    mi_id, caso = vista.get("mi_id"), vista.get("caso", {}).get("id")
    propia = next((r for r in reversed(juego.historial)
                   if r.get("jugador_id") == mi_id
                   and r.get("publicacion", {}).get("id") == caso), None)
    actor = mi_id if propia else vista.get("turno_id")
    if actor is not None:
        juego.turno = next((i for i, j in enumerate(juego.jugadores) if j.id == actor), juego.turno)
    juego.decision_aplicada = propia is not None
    if propia:
        juego.ultimo_registro = copy.deepcopy(propia)
        juego.ultima_accion = propia["accion"]
        juego.ultima_accion_rol = propia.get("accion_rol", propia["accion"])
        publicacion = propia["publicacion"]
        juego.ultima_publicacion_id = publicacion["id"]
        juego.ultima_publicacion_texto = publicacion["texto"]
        juego.ultima_publicacion_verdadera = publicacion["verdadera"]
        juego.ultima_propagacion = (
            ResultadoPropagacion(**propia["propagacion"]) if propia.get("propagacion") else None)
        juego.ultimo_resultado = propia.get("explicacion", "")
    return juego


class _ClienteDeEscena:
    """Traduce mensajes de las escenas históricas sin cambiar su presentación."""
    def __init__(self, control):
        self.control = control
        self._cerrado = threading.Event()
        self._cerrado.set()

    @property
    def cerrado(self):
        cliente = self.control.cliente
        return cliente.cerrado if cliente is not None else self._cerrado

    def enviar(self, mensaje):
        if mensaje.get("tipo") == "accion":
            return self.control.enviar_accion(mensaje.get("accion"))
        if mensaje.get("tipo") == "decision_lista":
            return self.control.opciones_vistas()
        if mensaje.get("tipo") == "continuar":
            return self.control.continuar()
        return self.control.enviar_comando(mensaje)

    def cerrar(self):
        self.control.cerrar()


class ControlCooperativaNovela(QObject):
    """Dos perspectivas privadas que comparten la novela, su ABB y su grafo."""
    mensaje_entrada = pyqtSignal(dict)

    def __init__(self, ventana):
        super().__init__(ventana)
        self.ventana = ventana
        self.cliente = None
        self.servidor = None
        self.sala = None
        self.vista = {}
        self.mi_id = None
        self.token = None
        self.datos_conexion = None
        self.revision = -1
        self._generacion = 0
        self._cerrando = False
        self._opciones = set()
        self._reanudar_lectura = None
        self._juego_pausado = None
        self._proxy = _ClienteDeEscena(self)
        self.mensaje_entrada.connect(self._recibir)

    @property
    def activa(self):
        return bool(self.cliente and not self.cliente.cerrado.is_set())

    def abrir_sala(self, modal=True):
        reanudar = self.ventana.pausar_lectura_modal()
        self.sala = SalaCooperativaNovela(self.ventana)
        self.ventana.dialogo_red = self.sala
        self.sala.conectar.connect(self.conectar)
        self.sala.reservar.connect(self.reservar_rol)
        self.sala.soltar.connect(lambda: self.reservar_rol(None))
        self.sala.comenzar.connect(lambda: self.enviar_comando({"tipo": "iniciar"}))
        self.sala.reconectar.connect(self.reconectar)
        self.sala.configurar_sin_limite.connect(
            lambda valor: self.enviar_comando({"tipo": "configurar_sala", "sin_limite": valor}))
        if not modal:
            def terminado(resultado):
                if resultado != QDialog.DialogCode.Accepted and not self.vista:
                    self.cerrar()
                reanudar()
            self.sala.finished.connect(terminado)
            self.sala.show()
            return self.sala
        try:
            resultado = self.sala.exec()
            if resultado != QDialog.DialogCode.Accepted and not self.vista:
                self.cerrar()
        finally:
            reanudar()
        return self.sala

    def conectar(self, crear, host, puerto, nombre):
        try:
            self._limpiar_red()
            self.vista = {}
            self.revision = -1
            self.mi_id, self.token = None, None
            sin_limite = (self.sala.sin_limite.isChecked() if self.sala is not None
                          else bool(self.ventana.sin_limite))
            if crear:
                self.servidor = ServidorCooperativo(
                    host="0.0.0.0", puerto=puerto,
                    semilla=getattr(self.ventana, "_semilla_novela", 4),
                    sin_limite=sin_limite, reservar_anfitrion=True)
                self.servidor.sesion.juego.eventos_activos = getattr(
                    self.ventana, "_eventos_novela", True)
                puerto = self.servidor.iniciar()
                host = "127.0.0.1"
            self.datos_conexion = (host, puerto, nombre)
            self._crear_cliente(
                anfitrion_token=self.servidor.token_anfitrion if crear else None)
            self.ventana.datos_conexion = self.datos_conexion
            self.ventana.servidor_red = self.servidor
            if self.sala is not None:
                self.sala.estado.setText("Conectando con la ciudad…")
        except (OSError, ValueError) as error:
            self._limpiar_red()
            self._error(str(error))

    def _crear_cliente(self, token=None, anfitrion_token=None):
        self._generacion += 1
        generacion = self._generacion
        self.cliente = ClienteCooperativo(
            lambda mensaje: self.mensaje_entrada.emit(
                dict(mensaje, _generacion=generacion)))
        self.ventana.cliente_red = self._proxy
        self.cliente.conectar(
            *self.datos_conexion, token=token, anfitrion_token=anfitrion_token)

    def reservar_rol(self, rol):
        return self.enviar_comando({"tipo": "reservar_rol", "rol": rol})

    def enviar_accion(self, accion, **editor):
        return self.enviar_comando(dict(editor, tipo="decidir", accion=accion))

    def enviar_comando(self, mensaje):
        if self.cliente is None or self.cliente.cerrado.is_set():
            self._error("La sala está desconectada. Usa Partida → Reconectar sala.")
            return False
        comando = dict(mensaje)
        if comando.get("tipo") not in ("reservar_rol", "iniciar", "configurar_sala", "sincronizar"):
            if self.vista:
                comando.setdefault("revision", self.revision)
                comando.setdefault("caso_id", self.vista.get("caso", {}).get("id"))
        enviado = self.cliente.enviar(comando)
        if not enviado:
            self._error("No fue posible enviar la acción a la sala.")
        return enviado

    def continuar(self):
        if self.vista.get("fase") != "resultado":
            self._error("Tu compañero todavía está preparando su decisión.")
            return False
        if self.mi_id in self.vista.get("confirmados", []):
            return True
        return self.enviar_comando({"tipo": "continuar"})

    def opciones_vistas(self):
        if (self.vista.get("turno_id") != self.mi_id
                or self.vista.get("fase") not in ("investigacion", "decision")):
            return False
        clave = (self.vista.get("caso", {}).get("id"), self.mi_id)
        if clave in self._opciones:
            return True
        if self.enviar_comando({"tipo": "opciones_vistas"}):
            self._opciones.add(clave)
            return True
        return False

    def sincronizar_escena(self, indice):
        if not self.vista or self.cliente is None:
            return
        if self.vista.get("fase") == "pausa":
            self.ventana.escena_accion.timer_decision.stop()
            return
        if indice == self.ventana.ESCENA_ACCION:
            self.opciones_vistas()
            self.ventana.escena_accion.actualizar_plazo_red(self.vista.get("plazo_segundos"))

    def reconectar(self):
        if self.datos_conexion is None:
            self._error("Primero entra a una sala de CIVICA.")
            return False
        if self.activa:
            return self.enviar_comando({"tipo": "sincronizar"})
        self.revision = -1
        self._opciones.clear()
        self._crear_cliente(
            token=self.token if self.vista else None,
            anfitrion_token=self.servidor.token_anfitrion if self.servidor is not None else None)
        self._error("Recuperando tu personaje y la escena…")
        return True

    def _recibir(self, mensaje):
        if mensaje.get("_generacion") != self._generacion or self._cerrando:
            return
        tipo = mensaje.get("tipo")
        if tipo == "bienvenida":
            self.mi_id, self.token = mensaje["id"], mensaje["token"]
            self.ventana.mi_id, self.ventana.token_red = self.mi_id, self.token
        elif tipo == "sala":
            if self.sala is not None:
                self.sala.actualizar(mensaje, self.mi_id)
            self.ventana.sin_limite = bool(mensaje.get("sin_limite", False))
        elif tipo == "estado":
            revision = mensaje.get("revision", -1)
            if revision < self.revision:
                return
            vista = mensaje.get("vista", {})
            try:
                juego = reconstruir_juego_novela(mensaje, vista)
            except (ValueError, KeyError, TypeError, zlib.error) as error:
                self._error("No se pudo recuperar la escena: " + str(error))
                return
            primero, anterior = not self.vista, self.vista
            self.vista, self.revision = vista, revision
            self.ventana.revision_red = revision
            self.ventana.fase_red = mensaje.get("fase")
            self.ventana.sin_limite = bool(vista.get("sin_limite", False))
            if primero:
                if hasattr(self.ventana, "sesion"):
                    self.ventana.sesion = None
                if hasattr(self.ventana, "vista_novela"):
                    self.ventana.vista_novela = {}
                self.ventana.pistas_consultadas.clear()
                self.ventana.historial_dialogos.clear()
            pausada = vista.get("fase") == "pausa"
            if pausada and self._juego_pausado is not None:
                juego = self._juego_pausado
            elif not pausada and self._reanudar_lectura is not None:
                self._reanudar_lectura()
                self._reanudar_lectura = None
                self._juego_pausado = None
            callback = getattr(self.ventana, "recibir_estado_novela", None)
            if callable(callback):
                callback(vista, juego)
            else:
                self._mostrar_original(vista, juego, anterior, primero)
            if pausada:
                self._pausar_lectura()
            if self.sala is not None and self.sala.isVisible():
                self.sala.accept()
            self.sincronizar_escena(self.ventana.escenas.currentIndex())
        elif tipo in ("error", "desconexion"):
            texto = mensaje.get("texto", "Se interrumpió la conexión.")
            if tipo == "desconexion":
                self._opciones.clear()
                self.ventana.escena_accion.timer_decision.stop()
                if not self.vista:
                    self.token = None
                    if self.sala is not None:
                        self.sala.desconectada(texto)
                else:
                    self._pausar_lectura()
                    # El socket nuevo no confirma que ya se recibió el estado recuperado.
                    # Invalida la vista anterior hasta que llegue ese snapshot autoritativo.
                    self.vista = dict(self.vista, fase="pausa")
                    self.ventana.fase_red = "pausa"
                    callback = getattr(self.ventana, "recibir_estado_novela", None)
                    if callable(callback):
                        callback(self.vista, self.ventana.juego)
            self._error(texto)
            if tipo == "error":
                callback = getattr(self.ventana, "error_cooperativo", None)
                if callable(callback):
                    callback(texto)

    def _pausar_lectura(self):
        if self._reanudar_lectura is None:
            self._juego_pausado = self.ventana.juego
            self._reanudar_lectura = self.ventana.pausar_lectura_modal()

    def _mostrar_original(self, vista, juego, anterior, primero):
        self.ventana.establecer_juego(juego)
        if vista.get("fase") == "pausa":
            self.ventana.pausar_lectura_modal()
            self.ventana.escena_accion.timer_decision.stop()
            self._error("Campaña en pausa. Esperando a tu compañero.")
        elif vista.get("fase") == "final":
            self.ventana.mostrar_desenlace()
        elif primero or vista.get("caso", {}).get("id") != anterior.get("caso", {}).get("id"):
            self.ventana.mostrar_escena(
                self.ventana.ESCENA_NARRACION_1 if primero else self.ventana.ESCENA_DIALOGO)
        elif self.mi_id in vista.get("decididos", []) and self.mi_id not in anterior.get("decididos", []):
            self.ventana.mostrar_escena(self.ventana.ESCENA_RESULTADO_1)
        elif self.ventana.escenas.currentWidget() is self.ventana.escena_accion:
            self.ventana.escena_accion.mostrar()

    def _error(self, texto):
        self.ventana.statusBar().showMessage(texto, 9000)
        if self.sala is not None and self.sala.isVisible():
            self.sala.estado.setText(texto)
        overlay = getattr(self.ventana, "overlay_investigacion", None)
        if overlay is not None:
            overlay.mostrar_mensaje(texto)

    def _limpiar_red(self):
        self._generacion += 1
        if self.cliente is not None:
            self.cliente.cerrar()
        if self.servidor is not None:
            self.servidor.cerrar()
        self.cliente = self.servidor = None
        self._opciones.clear()
        self._reanudar_lectura = None
        self._juego_pausado = None
        if self.ventana.cliente_red is self._proxy:
            self.ventana.cliente_red = None
        self.ventana.servidor_red = None
        self.ventana.token_red = None
        self.ventana.datos_conexion = None

    def cerrar(self):
        if self._cerrando:
            return
        self._cerrando = True
        try:
            self._limpiar_red()
            self.vista = {}
            self.token, self.datos_conexion = None, None
            self.mi_id = None
            self.revision = -1
            if self.sala is not None and self.sala.isVisible():
                self.sala.reject()
        finally:
            self._cerrando = False
