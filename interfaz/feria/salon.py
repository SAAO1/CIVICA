"""Portada ilustrada, sala de dos roles y escena viva de investigación."""
from __future__ import annotations

import math
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QSpinBox, QToolButton, QVBoxLayout, QWidget,
)
from infraestructura.recursos import RAIZ
from interfaz.componentes.personajes_animados import SpriteExpresivo

ROLES = {"ciudadano": "Ciudadano", "periodista": "Periodista"}


def etiqueta(texto="", size=16, color="#f8edda", bold=False):
    w = QLabel(texto)
    w.setWordWrap(True)
    w.setTextFormat(Qt.TextFormat.PlainText)
    w.setStyleSheet(f"color:{color}; background:transparent; font-size:{size}px; font-weight:{700 if bold else 400};")
    return w


def boton(texto, callback=None, principal=False):
    w = QPushButton(texto)
    w.setCursor(Qt.CursorShape.PointingHandCursor)
    w.setMinimumHeight(43)
    if principal:
        w.setObjectName("acento")
    if callback is not None:
        w.clicked.connect(callback)
    return w


class FondoIlustrado(QWidget):
    """El arte es un recurso local; el movimiento nunca bloquea una acción."""
    def __init__(self, imagen="assets/feria/portada.png", parent=None):
        super().__init__(parent)
        self.imagen = QPixmap(str(RAIZ / imagen))
        if self.imagen.isNull():
            self.imagen = QPixmap(str(RAIZ / "assets/expansion/fondos/plaza_noche.png"))
        self.reducir = False
        self.fase = 0.0
        self.reloj = QTimer(self)
        self.reloj.setInterval(75)
        self.reloj.timeout.connect(self._paso)

    def _paso(self):
        self.fase += .007
        self.update()

    def configurar(self, reducir):
        self.reducir = reducir
        if reducir or not self.isVisible():
            self.reloj.stop()
        else:
            self.reloj.start()
        self.update()

    def showEvent(self, event):
        super().showEvent(event)
        self.configurar(self.reducir)

    def hideEvent(self, event):
        self.reloj.stop()
        super().hideEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#102837"))
        if not self.imagen.isNull():
            zoom = 1.0 if self.reducir else 1.02 + .008*math.sin(self.fase)
            s = max(self.width()/self.imagen.width(), self.height()/self.imagen.height())*zoom
            w, h = round(self.imagen.width()*s), round(self.imagen.height()*s)
            image = self.imagen.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
            p.drawPixmap((self.width()-w)//2, (self.height()-h)//2, image)
        veil = QLinearGradient(0, 0, self.width(), 0)
        veil.setColorAt(0, QColor(8, 26, 38, 205))
        veil.setColorAt(.48, QColor(8, 26, 38, 135))
        veil.setColorAt(1, QColor(8, 26, 38, 20))
        p.fillRect(self.rect(), veil)


class Portada(FondoIlustrado):
    iniciar = pyqtSignal()
    cooperar = pyqtSignal()
    continuar = pyqtSignal()
    ayuda = pyqtSignal()
    ajustes = pyqtSignal()

    def __init__(self):
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(58, 38, 54, 30)
        outer.setSpacing(14)
        top = QHBoxLayout()
        top.addWidget(etiqueta("CIUDAD NOVA  /  FALTAN HORAS PARA LAS ELECCIONES", 13, "#a9d2cc", True))
        top.addStretch()
        b = boton("Cómo jugar", self.ayuda.emit)
        top.addWidget(b)
        top.addWidget(boton("Ajustes", self.ajustes.emit))
        outer.addLayout(top)
        outer.addStretch(2)
        self.marca = etiqueta("CIVICA", 88, "#fff0d6", True)
        outer.addWidget(self.marca)
        outer.addWidget(etiqueta("LA ÚLTIMA HORA", 26, "#edb09a", True))
        sinopsis = etiqueta("Un mensaje puede dividir una ciudad.\nEl contexto puede volver a reunirla.", 24)
        sinopsis.setMaximumWidth(590)
        outer.addWidget(sinopsis)
        outer.addSpacing(12)
        self.historia = boton("Comenzar investigación  →", self.iniciar.emit, True)
        self.historia.setMaximumWidth(360)
        outer.addWidget(self.historia)
        self.cooperativo = boton("Dos voces · Cooperativo en LAN", self.cooperar.emit)
        self.cooperativo.setMaximumWidth(360)
        outer.addWidget(self.cooperativo)
        self.seguir = boton("Continuar mi partida", self.continuar.emit)
        self.seguir.setMaximumWidth(360)
        self.seguir.setVisible(False)
        outer.addWidget(self.seguir)
        outer.addSpacing(8)
        outer.addWidget(etiqueta("3 capítulos · 6 casos · Tus decisiones dejan huella", 15, "#c0d1d4"))
        outer.addStretch(3)
        foot = etiqueta("Investiga el recorte. Escucha a las personas. Elige qué contar.", 14, "#b8cfd0")
        outer.addWidget(foot)


class SalaCooperativa(FondoIlustrado):
    conectar = pyqtSignal(bool, str, int, str)
    reservar = pyqtSignal(str)
    soltar = pyqtSignal()
    comenzar = pyqtSignal()
    volver = pyqtSignal()
    configurar_sin_limite = pyqtSignal(bool)
    reconectar = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.mi_id = None
        self._conectada = False
        outer = QVBoxLayout(self)
        outer.setContentsMargins(44, 28, 44, 28)
        title = QHBoxLayout()
        title.addWidget(etiqueta("DOS VOCES. UNA CIUDAD.", 32, bold=True))
        title.addStretch()
        title.addWidget(boton("← Portada", self.volver.emit))
        outer.addLayout(title)
        outer.addWidget(etiqueta("Dos dispositivos conectados a la misma red. Cada investigador tiene una perspectiva.", 17, "#c5d9dc"))
        form = QFrame()
        form.setObjectName("tarjetaOscura")
        fl = QGridLayout(form)
        fl.setContentsMargins(20, 16, 20, 16)
        self.nombre = QLineEdit("Alex")
        self.nombre.setMaxLength(24)
        self.host = QLineEdit("127.0.0.1")
        self.host.setPlaceholderText("IP del equipo anfitrión")
        self.puerto = QSpinBox()
        self.puerto.setRange(1, 65535)
        self.puerto.setValue(8765)
        for col, (label, w) in enumerate((("Tu nombre", self.nombre), ("Dirección del anfitrión", self.host), ("Puerto", self.puerto))):
            fl.addWidget(etiqueta(label, 14, "#c6d4d9"), 0, col)
            fl.addWidget(w, 1, col)
        self.crear = boton("Crear sala", lambda: self._conectar(True), True)
        self.unirse = boton("Unirme a la sala", lambda: self._conectar(False))
        fl.addWidget(self.crear, 2, 0)
        fl.addWidget(self.unirse, 2, 1)
        self.sin_limite = QCheckBox("Sin límite de decisión")
        self.sin_limite.setToolTip("La preferencia del anfitrión se aplica a ambos investigadores.")
        self.sin_limite.toggled.connect(self.configurar_sin_limite.emit)
        fl.addWidget(self.sin_limite, 2, 2)
        outer.addWidget(form)
        self.estado = etiqueta("Conéctate para ver qué personaje está disponible. Los roles se reservan en tiempo real.", 17, "#fac6b1")
        outer.addWidget(self.estado)
        cards = QHBoxLayout()
        self.roles = {}
        self.descripcion = {}
        for rol, texto in ROLES.items():
            frame = QFrame()
            frame.setObjectName("tarjetaOscura")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(20, 17, 20, 17)
            layout.addWidget(etiqueta(texto.upper(), 23, bold=True))
            desc = ("Escucha al vecindario, recupera testimonios y lleva las correcciones a tu comunidad."
                    if rol == "ciudadano" else
                    "Investiga documentos, contrasta el contexto y publica rectificaciones fundamentadas.")
            layout.addWidget(etiqueta(desc, 16, "#cfdbde"))
            status = etiqueta("Conéctate primero", 16, "#abc1c7")
            layout.addWidget(status)
            b = boton("Elegir " + texto, lambda checked=False, r=rol: self.reservar.emit(r), True)
            b.setCheckable(True)
            b.setEnabled(False)
            self.roles[rol] = b
            self.descripcion[rol] = status
            layout.addWidget(b)
            cards.addWidget(frame)
        outer.addLayout(cards)
        row = QHBoxLayout()
        self.liberar = boton("Liberar mi personaje", self.soltar.emit)
        self.liberar.setEnabled(False)
        row.addWidget(self.liberar)
        self.reintentar = boton("Volver a conectar", self.reconectar.emit)
        self.reintentar.hide()
        row.addWidget(self.reintentar)
        row.addStretch()
        self.iniciar = boton("Empezar la investigación  →", self.comenzar.emit, True)
        self.iniciar.setEnabled(False)
        row.addWidget(self.iniciar)
        outer.addLayout(row)
        self.red_info = etiqueta("El anfitrión debe mantener abierta su partida. No se necesitan cuentas ni Internet para jugar.", 14, "#b5cbd0")
        outer.addWidget(self.red_info)
        outer.addStretch()

    def _conectar(self, crear):
        self.conectar.emit(crear, self.host.text().strip(), self.puerto.value(), self.nombre.text().strip())

    def actualizar(self, mensaje, mi_id=None):
        self.mi_id = mi_id or mensaje.get("mi_id", self.mi_id)
        jugadores = mensaje.get("jugadores", [])
        ocupados = mensaje.get("roles_ocupados", {})
        if not ocupados:
            ocupados = {j["rol"]: j for j in jugadores if j.get("rol")}
        self._conectada = True
        for w in (self.crear, self.unirse, self.nombre, self.host, self.puerto):
            w.setEnabled(False)
        mi_rol = next((j.get("rol") for j in jugadores if j.get("id") == self.mi_id), None)
        for rol, b in self.roles.items():
            dueño = ocupados.get(rol)
            propio = bool(dueño and dueño.get("id") == self.mi_id)
            b.setChecked(propio)
            b.setEnabled(dueño is None or propio)
            b.setText("Tu personaje ✓" if propio else "Ocupado" if dueño else "Elegir " + ROLES[rol])
            self.descripcion[rol].setText(
                ("Reservado por ti" if propio else "Reservado por " + dueño.get("nombre", "tu compañero")) if dueño else "Disponible")
            b.setAccessibleDescription(self.descripcion[rol].text())
        anfitrion = mensaje.get("anfitrion")
        soy_host = anfitrion == self.mi_id
        self.iniciar.setEnabled(soy_host and bool(mensaje.get("puede_iniciar")))
        self.liberar.setEnabled(mi_rol is not None)
        self.sin_limite.setEnabled(soy_host)
        bloqueadas = self.sin_limite.blockSignals(True)
        if "sin_limite" in mensaje:
            self.sin_limite.setChecked(bool(mensaje["sin_limite"]))
        self.sin_limite.blockSignals(bloqueadas)
        self.estado.setText(" · ".join(f"{j['nombre']}: {ROLES.get(j.get('rol'), 'eligiendo personaje')}" for j in jugadores))
        if not soy_host and mensaje.get("puede_iniciar"):
            self.estado.setText(self.estado.text() + "\nTodo listo. Tu compañero puede comenzar.")
        if mensaje.get("direcciones_lan"):
            self.red_info.setText("Conecta el segundo dispositivo a " + " / ".join(mensaje["direcciones_lan"]) +
                                  f" · Puerto {mensaje.get('puerto', self.puerto.value())}. Mantén abierto este equipo.")

    def reiniciar(self):
        self._conectada = False
        self.mi_id = None
        for w in (self.crear, self.unirse, self.nombre, self.host, self.puerto):
            w.setEnabled(True)
        for rol, b in self.roles.items():
            b.setEnabled(False)
            b.setChecked(False)
            b.setText("Elegir " + ROLES[rol])
            self.descripcion[rol].setText("Conéctate primero")
        self.iniciar.setEnabled(False)
        self.liberar.setEnabled(False)
        self.estado.setText("Conéctate para reservar uno de los dos personajes.")


class EscenaViva(FondoIlustrado):
    narrar = pyqtSignal(str, str)
    apertura_solicitada = pyqtSignal(int)
    def __init__(self):
        super().__init__("assets/rediseno/fondos/cafe_exterior.png")
        self.setMinimumWidth(220)
        self.setMaximumWidth(340)
        self._caso = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 23, 20, 20)
        self.capitulo = etiqueta("EL PRIMER REENVÍO", 13, "#c6e1d9", True)
        self.contexto = etiqueta("Ciudad Nova", 18, bold=True)
        layout.addWidget(self.capitulo)
        layout.addWidget(self.contexto)
        self.actor = SpriteExpresivo(self)
        self.actor.setMinimumHeight(230)
        self.actor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.actor, 1)
        self.nombre = etiqueta("TU PERSPECTIVA", 13, "#f2b39c", True)
        self.mensaje = etiqueta("", 17)
        layout.addWidget(self.nombre)
        layout.addWidget(self.mensaje)
        self.escuchar = QToolButton()
        self.escuchar.setText("Leer reacción / detener")
        self.escuchar.clicked.connect(lambda: self.narrar.emit(self.nombre.text(), self.mensaje.text()))
        layout.addWidget(self.escuchar)
        self.escuchar_caso = QToolButton()
        self.escuchar_caso.setText("Escuchar introducción")
        self.escuchar_caso.clicked.connect(
            lambda: self.apertura_solicitada.emit((self.vista.get("caso") or {}).get("id",50)))
        layout.addWidget(self.escuchar_caso)
        self.vista = {}

    def actualizar(self, vista):
        self.vista = vista
        caso = vista.get("caso") or {}
        cap = max(1, min(3, caso.get("capitulo", 1)))
        self.capitulo.setText(f"CAPÍTULO {cap} / 3\n" + ("EL PRIMER REENVÍO", "LO QUE QUEDÓ FUERA", "LA CIUDAD RESPONDE")[cap-1])
        self.contexto.setText(caso.get("lugar", "Ciudad Nova"))
        rol = vista.get("mi_rol", "ciudadano")
        self.nombre.setText(ROLES.get(rol, "Tu perspectiva").upper())
        self.mensaje.setText(vista.get("mensaje") or caso.get("objetivo", ""))
        if caso.get("id") != self._caso:
            self._caso = caso.get("id")
            ruta = RAIZ / caso.get("fondo", "assets/feria/portada.png")
            pix = QPixmap(str(ruta))
            if not pix.isNull():
                self.imagen = pix
            try:
                self.actor.configurar_actor(rol, "neutral")
            except (ValueError, KeyError):
                self.actor.configurar_actor("ciudadano", "neutral")
        self.actor.configurar_movimiento(self.reducir, not self.reducir)
        self.update()
