"""Aplicación de feria: una investigación breve, individual o entre dos dispositivos."""
from __future__ import annotations

import copy
from contextlib import contextmanager
import json
import random
import time
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QLocale, QUrl
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QApplication, QDialog, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPushButton, QSplitter, QStackedWidget,
    QToolBar, QVBoxLayout, QWidget,
)
from audio.gestor_audio import GestorAudio
from infraestructura.recursos import RAIZ
from interfaz.componentes.arte import cargar_tipografias
from interfaz.feria.componentes import TableroInvestigacion
from interfaz.feria.salon import Portada, SalaCooperativa, EscenaViva, etiqueta, boton
from juego.investigacion import SesionInvestigacion

PREFERENCIAS = RAIZ / ".civica/feria_preferencias.json"
GUARDADO = RAIZ / ".civica/feria_autoguardado.json"
DEFECTO = {"sonido": True, "volumen": 65, "tamano_texto": 16, "alto_contraste": False,
           "reducir_movimiento": False, "sin_limite": False, "narracion": True}
ESTILO = """
QMainWindow, QDialog { background:#102735; color:#f8edda; }
QLabel { color:#f8edda; background:transparent; }
QWidget { font-family:'Atkinson Hyperlegible'; font-size:16px; }
QToolBar { background:#102735; border:0; padding:8px; spacing:9px; }
QToolButton { color:#f8edda; padding:7px 11px; background:#234150; border:1px solid #4e6872; border-radius:6px; }
QToolButton:hover { background:#355e69; }
QToolButton:disabled { color:#80969d; background:#1c3441; }
QPushButton { color:#f8edda; background:#244653; border:1px solid #63828a; padding:9px 18px; border-radius:8px; font-weight:600; }
QPushButton:hover { background:#396773; border-color:#aac9c9; }
QPushButton:focus { border:2px solid #efb49b; }
QPushButton:checked { background:#426c70; border:2px solid #c9e9dc; }
QPushButton:disabled { color:#8b9ca1; background:#243742; border-color:#425760; }
QPushButton#acento { background:#f0b49a; color:#203645; border-color:#f0b49a; }
QPushButton#acento:hover { background:#ffd0b8; }
QPushButton#acento:disabled { color:#a69b92; background:#615b55; border-color:#615b55; }
QFrame#tarjetaOscura { background:rgba(14,38,51,220); border:1px solid #66828a; border-radius:12px; }
QLineEdit, QSpinBox { color:#263d48; background:#f8edda; border:1px solid #cbb99f; border-radius:7px; padding:10px; }
QCheckBox { color:#f8edda; spacing:8px; }
QFrame#cabeceraPartida { background:#1d3947; border-bottom:1px solid #526e76; }
QLabel#avisoGlobal { background:#503c38; color:#ffe5d8; padding:9px; border-radius:6px; }
QSplitter::handle { background:#365362; width:3px; }
QStatusBar { background:#102735; color:#bcd3d4; font-size:13px; }
QToolTip { background:#f8edda; color:#263a47; border:1px solid #b69d80; padding:7px; }
"""


def _leer_preferencias():
    try:
        datos = json.loads(PREFERENCIAS.read_text(encoding="utf-8"))
        return {**DEFECTO, **datos} if isinstance(datos, dict) else dict(DEFECTO)
    except (OSError, ValueError):
        return dict(DEFECTO)


class VentanaInvestigacion(QMainWindow):
    mensaje_red = pyqtSignal(dict)

    def __init__(self, semilla=None, sin_audio=False, sin_limite=False, eventos=True,
                 guardar_automatico=True, ruta_guardado=None):
        super().__init__()
        cargar_tipografias()
        self.setWindowTitle("CIVICA · La última hora")
        self.setMinimumSize(1100, 700)
        self.resize(1366, 830)
        self.semilla = semilla if semilla is not None else random.SystemRandom().randrange(1, 10**8)
        self.eventos = eventos
        self.sesion = None
        self.mi_id = None
        self.cliente_red = None
        self.servidor_red = None
        self.token_red = None
        self.datos_conexion = None
        self.generacion_red = 0
        self.revision_red = -1
        self.vista_actual = {}
        self.preferencias = _leer_preferencias()
        self.preferencias["sonido"] = self.preferencias["sonido"] and not sin_audio
        self.preferencias["sin_limite"] = self.preferencias["sin_limite"] or sin_limite
        self.guardar_automatico = guardar_automatico
        self.ruta_guardado = Path(ruta_guardado) if ruta_guardado is not None else GUARDADO
        self._deadline = None
        self._clave_reloj = None
        self._peticiones_reloj = set()
        self._cerrando = False
        self._voz = None
        self._voz_caso = None
        self._salida_voz_caso = None
        self._ultimo_caso = None
        self.audio = GestorAudio(self)
        self.audio.silenciar(not self.preferencias["sonido"])
        self.audio.configurar("general", self.preferencias["volumen"]/100)
        self.reloj = QTimer(self)
        self.reloj.setInterval(200)
        self.reloj.timeout.connect(self._paso_reloj)
        self.mensaje_red.connect(self.recibir_mensaje)
        self._construir()
        self.aplicar_preferencias(self.preferencias, guardar=False)
        self.mostrar_portada(cerrar=False)

    def _construir(self):
        self.setStyleSheet(ESTILO)
        self.paginas = QStackedWidget()
        self.setCentralWidget(self.paginas)
        self.portada = Portada()
        self.portada.iniciar.connect(self.elegir_personaje)
        self.portada.cooperar.connect(self.abrir_sala)
        self.portada.continuar.connect(self.cargar_rapido)
        self.portada.ayuda.connect(self.ayuda)
        self.portada.ajustes.connect(self.ajustes)
        self.paginas.addWidget(self.portada)
        self.sala = SalaCooperativa()
        self.sala.conectar.connect(self.conectar_red)
        self.sala.reservar.connect(lambda rol: self._enviar({"tipo": "reservar_rol", "rol": rol}))
        self.sala.reconectar.connect(self.reconectar_red)
        self.sala.soltar.connect(lambda: self._enviar({"tipo": "reservar_rol", "rol": None}))
        self.sala.comenzar.connect(lambda: self._enviar({"tipo": "iniciar"}))
        self.sala.volver.connect(self.mostrar_portada)
        self.sala.configurar_sin_limite.connect(
            lambda valor: self._enviar({"tipo": "configurar_sala", "sin_limite": valor}))
        self.paginas.addWidget(self.sala)
        juego = QWidget()
        outer = QVBoxLayout(juego)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        header = QFrame()
        header.setObjectName("cabeceraPartida")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 11, 20, 11)
        self.indicadores = etiqueta("", 15, "#d1e5dd")
        self.puntuaciones = etiqueta("", 14, "#f2b79f", True)
        self.tiempo = etiqueta("", 15, "#ffd1be", True)
        hl.addWidget(self.indicadores, 3)
        hl.addWidget(self.puntuaciones, 2)
        hl.addWidget(self.tiempo, 1)
        self.boton_ciudad = boton('Ciudad ↗', self.ver_ciudad)
        hl.addWidget(self.boton_ciudad)
        outer.addWidget(header)
        self.aviso = QLabel()
        self.aviso.setObjectName("avisoGlobal")
        self.aviso.setWordWrap(True)
        self.aviso.hide()
        outer.addWidget(self.aviso)
        body = QSplitter(Qt.Orientation.Horizontal)
        self.escena = EscenaViva()
        self.escena.narrar.connect(self.narrar)
        self.escena.apertura_solicitada.connect(self.reproducir_apertura)
        self.tablero = TableroInvestigacion()
        self.tablero.comando.connect(self.comando)
        self.tablero.tabs.currentChanged.connect(self._cambio_pestana)
        body.addWidget(self.escena)
        body.addWidget(self.tablero)
        body.setStretchFactor(0, 0)
        body.setStretchFactor(1, 1)
        body.setSizes([260, 1100])
        outer.addWidget(body, 1)
        self.pagina_juego = juego
        self.paginas.addWidget(juego)
        barra = QToolBar("Herramientas")
        barra.setMovable(False)
        self.addToolBar(barra)
        self.barra = barra
        self.acciones = {}
        for clave, texto, metodo, atajo in (
            ("portada", "← Portada", self.mostrar_portada, None),
            ("guardar", "Guardar", self.guardar_rapido, "Ctrl+S"),
            ("cargar", "Cargar", self.abrir_guardado, "Ctrl+O"),
            ("historial", "Historial", self.historial, "F3"),
            ("galeria", "Galería", self.galeria, None),
            ("observatorio", "Observatorio", self.observatorio, "F2"),
            ("ayuda", "Ayuda", self.ayuda, "F1"),
            ("ajustes", "Pausa / Ajustes", self.ajustes, "Escape"),
            ("reconectar", "Reconectar", self.reconectar_red, None),
        ):
            a = QAction(texto, self)
            a.triggered.connect(metodo)
            if atajo:
                a.setShortcut(QKeySequence(atajo))
            self.acciones[clave] = a
            barra.addAction(a)
        full = QAction("Pantalla completa", self)
        full.setShortcut(QKeySequence("F11"))
        full.triggered.connect(lambda: self.showNormal() if self.isFullScreen() else self.showFullScreen())
        self.addAction(full)
        for i in range(4):
            a = QAction(f"Espacio de investigación {i+1}", self)
            a.setShortcut(QKeySequence(f"Alt+{i+1}"))
            a.triggered.connect(lambda checked=False, indice=i: self.tablero.tabs.setCurrentIndex(indice))
            self.addAction(a)
        self.statusBar().showMessage("CIVICA · Una investigación breve. Tus decisiones afectan a Ciudad Nova.")

    def elegir_personaje(self):
        d = QDialog(self)
        d.setWindowTitle("Tu perspectiva")
        d.setMinimumWidth(570)
        layout = QVBoxLayout(d)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.addWidget(etiqueta("¿DESDE DÓNDE MIRAS LA CIUDAD?", 24, bold=True))
        layout.addWidget(etiqueta("En individual juegas toda la historia desde el personaje que elijas.", 17, "#c4d9db"))
        nombre = QLineEdit("Alex")
        nombre.setMaxLength(24)
        nombre.setPlaceholderText("Tu nombre")
        layout.addWidget(nombre)
        for rol, titulo, texto in (
            ("ciudadano", "Ciudadano", "Tu barrio te conoce. Escucha, reúne testimonios y organiza una respuesta."),
            ("periodista", "Periodista", "Recupera documentos, compara las versiones y construye una rectificación."),
        ):
            b = boton(titulo + "\n" + texto, principal=True)
            b.setMinimumHeight(90)
            b.clicked.connect(lambda checked=False, r=rol: (d.setProperty("rol", r), d.accept()))
            layout.addWidget(b)
        layout.addWidget(boton("Volver", d.reject))
        if d.exec() == QDialog.DialogCode.Accepted:
            self.nueva_partida(d.property("rol"), nombre.text().strip() or "Alex")

    def nueva_partida(self, rol="ciudadano", nombre="Alex"):
        self.cerrar_red()
        self.reloj.stop()
        self._deadline = None
        self._clave_reloj = None
        self.detener_narracion()
        self._peticiones_reloj.clear()
        self._ultimo_caso = None
        self.sesion = SesionInvestigacion(semilla=self.semilla, cooperativa=False)
        self.sesion.juego.eventos_activos = self.eventos
        self.mi_id = self.sesion.registrar_jugador(nombre, rol)
        self.sesion.comenzar()
        self.actualizar_vista(self.sesion.vista(self.mi_id))
        self._guardar_auto()

    def mostrar_portada(self, checked=False, cerrar=True):
        if cerrar:
            self._guardar_auto()
            self.cerrar_red()
        self.reloj.stop()
        self._deadline = None
        self.tablero.detener_audio()
        self.detener_narracion()
        self.audio.detener_voz()
        if self._voz is not None:
            self._voz.stop()
        self.paginas.setCurrentWidget(self.portada)
        self.barra.hide()
        self.portada.seguir.setVisible(self.ruta_guardado.is_file())
        if self.preferencias["sonido"]:
            self.audio.cambiar_pista("investigacion")
            self.audio.cambiar_pista("lluvia", "ambiente")

    def abrir_sala(self):
        self._guardar_auto()
        self.cerrar_red()
        self.tablero.detener_audio()
        self.detener_narracion()
        self.sesion = None
        self.sala.reiniciar()
        self.sala.sin_limite.setChecked(bool(self.preferencias["sin_limite"]))
        self.paginas.setCurrentWidget(self.sala)
        self.barra.hide()

    def conectar_red(self, crear, host, puerto, nombre):
        from red.cliente_cooperativo import ClienteCooperativo
        from red.cooperativa import ServidorCooperativo, direcciones_lan
        try:
            if not nombre or len(nombre) > 24:
                raise ValueError("Escribe un nombre de hasta 24 caracteres.")
            self.cerrar_red()
            self.sesion = None
            self.revision_red = -1
            self.mi_id = None
            if crear:
                self.servidor_red = ServidorCooperativo(
                    host="0.0.0.0", puerto=puerto, semilla=self.semilla,
                    sin_limite=self.sala.sin_limite.isChecked(), reservar_anfitrion=True)
                self.servidor_red.sesion.juego.eventos_activos = self.eventos
                puerto = self.servidor_red.iniciar()
                host = "127.0.0.1"
                direcciones = direcciones_lan()
                self.sala.red_info.setText(
                    ("IP para el segundo dispositivo: " + " / ".join(direcciones) if direcciones else
                     "No se detectó una dirección LAN. Comprueba la conexión Wi-Fi o Ethernet.") +
                    f" · Puerto {puerto}. Ambos equipos deben estar en la misma red.")
            generacion = self.generacion_red
            self.cliente_red = ClienteCooperativo(
                lambda m: self.mensaje_red.emit({**m, "_generacion": generacion}))
            self.datos_conexion = (host, puerto, nombre)
            self.cliente_red.conectar(host, puerto, nombre,
                                      anfitrion_token=self.servidor_red.token_anfitrion if crear else None)
            self.sala.estado.setText("Conectando con la sala…")
        except (OSError, ValueError) as error:
            self.cerrar_red()
            self.sala.reiniciar()
            self.sala.estado.setText(str(error))

    def _enviar(self, mensaje):
        if self.cliente_red is not None:
            return self.cliente_red.enviar(mensaje)
        return False

    def recibir_mensaje(self, mensaje):
        if self._cerrando or mensaje.get("_generacion", self.generacion_red) != self.generacion_red:
            return
        tipo = mensaje.get("tipo")
        if tipo == "bienvenida":
            self.mi_id = mensaje["id"]
            self.token_red = mensaje.get("token")
            self.sala.mi_id = self.mi_id
            self.acciones["reconectar"].setVisible(False)
            self.sala.reintentar.hide()
        elif tipo == "sala":
            self.sala.actualizar(mensaje, self.mi_id)
        elif tipo == "estado":
            revision = mensaje.get("revision", -1)
            if revision < self.revision_red:
                return
            self.revision_red = revision
            self.actualizar_vista(mensaje.get("vista", {}))
        elif tipo in ("error", "desconexion"):
            texto = mensaje.get("texto", "La conexión se interrumpió.")
            if self.paginas.currentWidget() is self.sala:
                self.sala.estado.setText(texto)
                if tipo == "desconexion":
                    self.token_red = None
                    self.sala.reiniciar()
                    self.sala.reintentar.setVisible(self.datos_conexion is not None)
                    self.sala.estado.setText(texto + " Puedes volver a conectar sin cerrar la sala.")
            else:
                self.mostrar_aviso(texto)
                if tipo == "desconexion":
                    self.tablero.setEnabled(False)
                    self.reloj.stop()
                    self.tablero.detener_audio()
            self.acciones["reconectar"].setVisible(bool(self.token_red))
            self.statusBar().showMessage(texto)

    def reconectar_red(self):
        from red.cliente_cooperativo import ClienteCooperativo
        if not self.datos_conexion or (not self.token_red and self.paginas.currentWidget() is not self.sala):
            self.mostrar_aviso("Primero entra a una sala para recuperar tu personaje.")
            return
        if self.cliente_red is not None and not self.cliente_red.cerrado.is_set():
            self._enviar({"tipo": "sincronizar"})
            return
        self.generacion_red += 1
        gen = self.generacion_red
        self.revision_red = -1
        self._peticiones_reloj.clear()
        self._deadline = None
        self._clave_reloj = None
        self.reloj.stop()
        self.cliente_red = ClienteCooperativo(
            lambda m: self.mensaje_red.emit({**m, "_generacion": gen}))
        self.cliente_red.conectar(*self.datos_conexion, token=self.token_red,
            anfitrion_token=self.servidor_red.token_anfitrion if self.servidor_red is not None else None)
        self.mostrar_aviso("Recuperando tu personaje y el estado de la investigación…")

    def cerrar_red(self):
        self.generacion_red += 1
        if self.cliente_red is not None:
            self.cliente_red.cerrar()
            self.cliente_red = None
        if self.servidor_red is not None:
            self.servidor_red.cerrar()
            self.servidor_red = None
        self.token_red = None
        self.datos_conexion = None
        self.revision_red = -1
        self._peticiones_reloj.clear()

    def comando(self, mensaje):
        if self._cerrando:
            return
        tipo = mensaje.get("tipo")
        if tipo in ('investigar','examinar','entrevistar','decidir','continuar'):
            self.detener_narracion()
        if tipo == "opciones_vistas":
            self._opciones_vistas()
            return
        if self.cliente_red is not None:
            if not self._enviar(mensaje):
                self.mostrar_aviso("La sala está desconectada. Usa Reconectar para continuar.")
            return
        if self.sesion is None or not self.mi_id:
            return
        permitidos = {
            "investigar", "examinar", "entrevistar", "compartir_hallazgo", "solicitar_hallazgo",
            "proponer", "decidir", "continuar", "prever_alcance",
        }
        if tipo not in permitidos:
            self.mostrar_aviso("Esa acción no está disponible.")
            return
        campos = {k: v for k, v in mensaje.items() if k != "tipo"}
        if tipo == "examinar":
            campos["tipo"] = campos.pop("medio", campos.pop("tipo_medio", "captura"))
        try:
            getattr(self.sesion, tipo)(self.mi_id, **campos)
            self.actualizar_vista(self.sesion.vista(self.mi_id))
            self._guardar_auto()
            if tipo in ("decidir", "investigar", "examinar"):
                self.audio.reproducir_efecto("verificar" if tipo == "examinar" else "clic")
        except (ValueError, TypeError, KeyError) as error:
            self.mostrar_aviso(str(error))

    def _enriquecer(self, vista):
        v = copy.deepcopy(vista)
        caso = v.get("caso") or {}
        if caso.get("id"):
            identificador = caso["id"]
            medio = caso.setdefault("medio", {})
            medio["inspeccionable"] = (v.get("fase") in ("investigacion", "decision")
                                      and v.get("mi_id") not in v.get("decididos", [])
                                      and v.get("acciones_restantes", 0) > 0)
            medio["imagen_recortada"] = f"assets/feria/pruebas/{identificador}_recorte.png"
            medio["imagen_completa"] = f"assets/feria/pruebas/{identificador}_original.png"
            medio["video"] = f"assets/feria/videos/caso_{identificador}.mp4"
            if identificador == 110:
                medio["audio_recortado"] = "assets/feria/audio/caso_110_recortado.wav"
                medio["audio_completo"] = "assets/feria/audio/caso_110_completo.wav"
                medio["fragmentos"] = [
                    {"inicio": 0, "fin": 35, "texto": "Si alguien pretende"},
                    {"inicio": 35, "fin": 63, "texto": "cobrar por votar"},
                    {"inicio": 63, "fin": 100, "texto": "denuncia ese engaño."},
                ]
        return v

    def actualizar_vista(self, vista):
        if self._cerrando or not vista:
            return
        vista = self._enriquecer(vista)
        anterior = self.vista_actual
        self.vista_actual = vista
        self.mi_id = vista.get("mi_id") or self.mi_id
        caso = vista.get("caso") or {}
        fase = vista.get("fase")
        self.paginas.setCurrentWidget(self.pagina_juego)
        self.barra.show()
        self.acciones["guardar"].setEnabled(self.cliente_red is None)
        self.acciones["cargar"].setEnabled(self.cliente_red is None)
        self.acciones["reconectar"].setVisible(fase == "pausa" or (
            self.cliente_red is not None and self.cliente_red.cerrado.is_set()))
        self.tablero.setEnabled(fase != "pausa")
        self.tablero.actualizar(vista)
        self.tablero.mensaje.hide()
        self.escena.actualizar(vista)
        estado = vista.get("estado", {})
        self.indicadores.setText(
            f"Confianza {estado.get('confianza', 50)}   ·   Información {estado.get('info_verificada', 0)}"
            f"   ·   Desinformación {estado.get('desinformacion', 0)}")
        self.puntuaciones.setText("  |  ".join(
            f"{j['nombre']} · {j.get('puntos', 0):+d}" for j in vista.get("jugadores", [])))
        if fase == "pausa":
            self.mostrar_aviso("La investigación está pausada. Esperando a " +
                               ", ".join(vista.get("desconectados", ["tu compañero"])) + ".")
            self.tablero.detener_audio()
            self.reloj.stop()
        else:
            self.aviso.hide()
        clave = (caso.get("id"), vista.get("turno_id"))
        if clave != self._clave_reloj or fase not in ("investigacion", "decision"):
            self.reloj.stop()
            self._deadline = None
            self.tiempo.clear()
            self._clave_reloj = clave
        if self.cliente_red is not None:
            restante = vista.get("plazo_segundos")
            if restante is not None and fase in ("investigacion", "decision"):
                self._deadline = time.monotonic() + max(0, restante)
                self.reloj.start()
        if caso.get("id") != self._ultimo_caso:
            self._ultimo_caso = caso.get("id")
            self.audio.detener_voz()
            if self._voz is not None:
                self._voz.stop()
            self.audio.cambiar_pista("eleccion" if fase == "final" else "investigacion")
            self.audio.cambiar_pista("oficina", "ambiente")
        if fase == "final":
            self.reloj.stop()
            self.audio.cambiar_pista("eleccion")
        if (fase in ("investigacion", "decision") and self.tablero.tabs.currentIndex() == 2
                and vista.get("turno_id") == self.mi_id):
            QTimer.singleShot(0, self._opciones_vistas)
        if anterior.get("fase") != "resultado" and fase == "resultado":
            self.statusBar().showMessage("La ciudad responde. Puedes revisar el detalle o continuar.")

    def mostrar_aviso(self, texto):
        if self._cerrando:
            return
        self.tablero.mostrar_aviso_prueba(texto)
        self.aviso.setText(texto)
        self.aviso.show()
        self.statusBar().showMessage(texto, 12000)

    def _cambio_pestana(self, indice):
        if indice == 2:
            self._opciones_vistas()

    def _opciones_vistas(self):
        if self._cerrando:
            return
        vista = self.vista_actual
        if vista.get("turno_id") != self.mi_id or vista.get("fase") not in ("investigacion", "decision"):
            return
        clave = ((vista.get("caso") or {}).get("id"), self.mi_id)
        if clave in self._peticiones_reloj:
            return
        self._peticiones_reloj.add(clave)
        if self.cliente_red is not None:
            self._enviar({"tipo": "opciones_vistas"})
        elif not self.preferencias["sin_limite"] and vista.get("segundos_decision"):
            self._deadline = time.monotonic() + vista["segundos_decision"]
            self.reloj.start()

    def _paso_reloj(self):
        if self._cerrando:
            self.reloj.stop()
            return
        if self._deadline is None:
            self.reloj.stop()
            return
        restante = max(0, self._deadline - time.monotonic())
        self.tiempo.setText(f"ALERTA · {restante:.0f} s")
        if restante <= 0:
            self.reloj.stop()
            self._deadline = None
            if self.cliente_red is not None:
                self.tiempo.setText("Esperando a la sala…")
            elif self.sesion is not None:
                try:
                    self.sesion.expirar_turno(self.mi_id)
                    self.actualizar_vista(self.sesion.vista(self.mi_id))
                    self._guardar_auto()
                except ValueError:
                    pass

    def _guardar_auto(self):
        if self.sesion is None or self.cliente_red is not None or not self.guardar_automatico:
            return
        try:
            self._guardar_en(self.ruta_guardado)
        except (OSError, ValueError) as error:
            self.statusBar().showMessage("No se pudo guardar automáticamente: " + str(error))

    def _guardar_en(self, ruta):
        if self.sesion is None or self.sesion.cooperativa:
            raise ValueError("Los estados cooperativos pertenecen al servidor.")
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        temporal = ruta.with_name(ruta.name + ".tmp")
        temporal.write_text(json.dumps(self.sesion.datos(), ensure_ascii=False, indent=2), encoding="utf-8")
        temporal.replace(ruta)

    def guardar_rapido(self):
        if self.cliente_red is not None:
            self.mostrar_aviso("La sala mantiene la investigación de ambos jugadores.")
        elif self.sesion is not None:
            try:
                self._guardar_en(self.ruta_guardado)
                self.statusBar().showMessage("Partida guardada.", 4000)
            except (OSError, ValueError) as error:
                self.mostrar_aviso(str(error))

    def cargar_rapido(self):
        self.cargar_desde(self.ruta_guardado)

    def abrir_guardado(self):
        if self.cliente_red is not None:
            return
        with self.pausa_dialogo():
            ruta, _ = QFileDialog.getOpenFileName(self, "Abrir investigación", str(RAIZ / ".civica"), "Investigación (*.json)")
        if ruta:
            self.cargar_desde(ruta)

    def cargar_desde(self, ruta):
        try:
            datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
            sesion = SesionInvestigacion.desde_datos(datos)
            if sesion.cooperativa:
                raise ValueError("Una sala se recupera con Reconectar, no con un archivo individual.")
            self.cerrar_red()
            self.sesion = sesion
            self.mi_id = sesion.juego.jugadores[0].id
            self.reloj.stop()
            self._deadline = None
            self._clave_reloj = None
            self._peticiones_reloj.clear()
            self.actualizar_vista(sesion.vista(self.mi_id))
        except (OSError, ValueError, KeyError, TypeError) as error:
            self.mostrar_aviso("No se pudo abrir la investigación: " + str(error))

    @contextmanager
    def pausa_dialogo(self):
        clave = self._clave_reloj
        restante = (max(0, self._deadline-time.monotonic())
                    if self._deadline is not None and self.cliente_red is None else None)
        self.tablero.detener_audio()
        self.detener_narracion()
        self.audio.detener_voz()
        if self._voz is not None:
            self._voz.stop()
        if self.cliente_red is None:
            self.reloj.stop()
            self._deadline = None
        try:
            yield
        finally:
            if (not self._cerrando and restante is not None and clave == self._clave_reloj
                    and self.vista_actual.get("fase") in ("investigacion", "decision")
                    and not self.preferencias["sin_limite"]):
                self._deadline = time.monotonic()+restante
                self.reloj.start()

    def ajustes(self):
        from interfaz.feria.dialogos import DialogoAjustes
        with self.pausa_dialogo():
            d = DialogoAjustes(self.preferencias, parent=self)
            d.cambios.connect(self.aplicar_preferencias)
            d.exec()

    def aplicar_preferencias(self, preferencias, guardar=True):
        self.preferencias = {**DEFECTO, **preferencias}
        self.tablero.configurar_preferencias(self.preferencias)
        self.audio.silenciar(not self.preferencias["sonido"])
        self.audio.configurar("general", max(0, min(100, self.preferencias["volumen"]))/100)
        if self._salida_voz_caso is not None:
            self._salida_voz_caso.setVolume(max(0,min(100,self.preferencias["volumen"]))/100)
            self._salida_voz_caso.setMuted(not self.preferencias["sonido"])
        if not self.preferencias["narracion"] or not self.preferencias["sonido"]:
            self.detener_narracion()
        reducir = bool(self.preferencias["reducir_movimiento"])
        for fondo in (self.portada, self.sala, self.escena):
            fondo.configurar(reducir)
        self.escena.actor.configurar_movimiento(reducir, not reducir)
        if self.preferencias["sin_limite"] and self.cliente_red is None:
            self.reloj.stop()
            self._deadline = None
            self.tiempo.clear()
        tamaño = self.preferencias["tamano_texto"]
        extra = f"\nQWidget {{font-size:{tamaño}px;}}\n"
        if self.preferencias["alto_contraste"]:
            extra += "QMainWindow, QDialog {background:#071017;} QLabel {color:#ffffff;} QPushButton {border-color:#ffffff;}"
        self.setStyleSheet(ESTILO + extra)
        if guardar:
            try:
                PREFERENCIAS.parent.mkdir(parents=True, exist_ok=True)
                PREFERENCIAS.write_text(json.dumps(self.preferencias, ensure_ascii=False, indent=2), encoding="utf-8")
            except OSError:
                self.statusBar().showMessage("No se pudieron conservar los ajustes.")
        if not self.preferencias["narracion"] and self._voz is not None:
            self._voz.stop()

    def ayuda(self):
        from interfaz.feria.dialogos import DialogoAyuda
        with self.pausa_dialogo():
            DialogoAyuda(parent=self).exec()

    def observatorio(self):
        from interfaz.feria.dialogos import DialogoObservatorio
        if self.vista_actual:
            with self.pausa_dialogo():
                DialogoObservatorio(self.vista_actual, parent=self).exec()

    def historial(self):
        from interfaz.feria.dialogos import DialogoHistorial
        if self.vista_actual:
            with self.pausa_dialogo():
                DialogoHistorial(self.vista_actual, parent=self).exec()

    def galeria(self):
        from interfaz.feria.dialogos import DialogoGaleria
        with self.pausa_dialogo():
            DialogoGaleria(parent=self).exec()


    def ver_ciudad(self):
        etiquetas = {"confianza":"Confianza ciudadana", "info_verificada":"Información verificada",
                     "desinformacion":"Desinformación", "convivencia":"Convivencia",
                     "bienestar_digital":"Bienestar digital", "conflictos":"Conflictos", "participacion":"Participación"}
        texto = "\n".join(f"{nombre}: {self.vista_actual.get('estado',{}).get(clave,0)}"
                           for clave,nombre in etiquetas.items())
        with self.pausa_dialogo():
            QMessageBox.information(self,"Así está Ciudad Nova",texto)

    def detener_narracion(self):
        if self._voz_caso is not None:
            self._voz_caso.stop()
        if self._voz is not None:
            self._voz.stop()
        if hasattr(self,"audio"):
            self.audio.detener_voz()

    def reproducir_apertura(self, identificador):
        if not self.preferencias["sonido"] or not self.preferencias["narracion"]:
            return
        from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
        ruta = RAIZ / f"assets/feria/audio/caso_{identificador}_apertura.wav"
        if not ruta.is_file():
            self.mostrar_aviso("La introducción escrita sigue disponible en la escena.")
            return
        if self._voz_caso is not None and self._voz_caso.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._voz_caso.stop()
            return
        self.detener_narracion()
        self.tablero.detener_audio()
        if self._voz_caso is None:
            self._voz_caso = QMediaPlayer(self)
            self._salida_voz_caso = QAudioOutput(self)
            self._voz_caso.setAudioOutput(self._salida_voz_caso)
        self._salida_voz_caso.setVolume(self.preferencias["volumen"]/100)
        self._voz_caso.setSource(QUrl.fromLocalFile(str(ruta)))
        self._voz_caso.play()
        self.statusBar().showMessage("Escuchando la introducción de este caso. Puedes detenerla o seguir investigando.")

    def narrar(self, nombre, texto):
        if not self.preferencias["narracion"] or not self.preferencias["sonido"]:
            return
        if self._voz_caso is not None:
            self._voz_caso.stop()
        try:
            from PyQt6.QtTextToSpeech import QTextToSpeech
            if self._voz is None:
                self._voz = QTextToSpeech(self)
                self._voz.setLocale(QLocale("es_MX"))
                voces = self._voz.availableVoices()
                españolas = [v for v in voces if v.locale().language() == QLocale.Language.Spanish]
                if españolas:
                    self._voz.setVoice(españolas[0])
            if self._voz.state() == QTextToSpeech.State.Speaking:
                self._voz.stop()
            else:
                self._voz.say(texto)
        except (ImportError, RuntimeError):
            self.audio.narrar(texto, nombre)

    def closeEvent(self, event):
        self._cerrando = True
        self.detener_narracion()
        self._guardar_auto()
        self.reloj.stop()
        self.cerrar_red()
        self.tablero.detener_audio()
        self.audio.detener()
        if self._voz is not None:
            self._voz.stop()
        for fondo in (self.portada, self.sala, self.escena):
            fondo.reloj.stop()
        self.escena.actor.configurar_movimiento(True, False)
        super().closeEvent(event)
