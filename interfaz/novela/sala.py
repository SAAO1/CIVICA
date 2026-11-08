"""Sala cooperativa ilustrada sobre la presentación de la novela original."""
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QVBoxLayout,
)
from infraestructura.recursos import RAIZ
from interfaz.dialogos import DialogoIlustrado
from interfaz.componentes.arte import (
    BotonIlustrado, aplicar_estilo, pixmap_arte, _nueve_segmentos,
)

ROLES = {"ciudadano": "Ciudadano", "periodista": "Periodista"}


def _boton(texto, parent=None):
    try:
        from interfaz.novela.componentes import BotonNovela
        return BotonNovela(texto, parent=parent)
    except ImportError:
        return BotonIlustrado(texto, parent)


def _etiqueta(texto=""):
    etiqueta = QLabel(texto)
    etiqueta.setWordWrap(True)
    etiqueta.setTextFormat(Qt.TextFormat.PlainText)
    return etiqueta


class SalaCooperativaNovela(DialogoIlustrado):
    conectar = pyqtSignal(bool, str, int, str)
    reservar = pyqtSignal(str)
    soltar = pyqtSignal()
    comenzar = pyqtSignal()
    reconectar = pyqtSignal()
    configurar_sin_limite = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CIVICA · Dos voces en la misma ciudad")
        self.mi_id = None
        self._conectada = False
        self._marco = QPixmap(str(RAIZ/"assets/novela/ui/marco_expediente.png"))
        self.setMinimumSize(680, 530)
        exterior = QVBoxLayout(self)
        exterior.setContentsMargins(38, 29, 38, 27)
        exterior.setSpacing(12)
        titulo = _etiqueta("DOS VOCES · UNA CIUDAD")
        titulo.setStyleSheet("font-size:25px; font-weight:700; color:#f2d4a1;")
        exterior.addWidget(titulo)
        exterior.addWidget(_etiqueta(
            "Conecta dos dispositivos a la misma red. Mira qué personaje está libre antes de elegirlo."))
        campos = QGridLayout()
        campos.setHorizontalSpacing(12)
        self.nombre = QLineEdit("Alex")
        self.nombre.setMaxLength(24)
        self.host = QLineEdit("127.0.0.1")
        self.host.setPlaceholderText("IP del equipo anfitrión")
        self.puerto = QSpinBox()
        self.puerto.setRange(1, 65535)
        self.puerto.setValue(8765)
        for columna, (nombre, widget) in enumerate((
                ("Tu nombre", self.nombre), ("Servidor", self.host), ("Puerto", self.puerto))):
            campos.addWidget(_etiqueta(nombre), 0, columna)
            campos.addWidget(widget, 1, columna)
        exterior.addLayout(campos)
        conexion = QHBoxLayout()
        self.crear = _boton("Crear sala")
        self.unirse = _boton("Unirme")
        self.crear.clicked.connect(lambda: self._conectar(True))
        self.unirse.clicked.connect(lambda: self._conectar(False))
        conexion.addWidget(self.crear)
        conexion.addWidget(self.unirse)
        self.sin_limite = QCheckBox("Decidir sin límite")
        self.sin_limite.setChecked(bool(getattr(parent, "sin_limite", False)))
        self.sin_limite.toggled.connect(self.configurar_sin_limite.emit)
        conexion.addWidget(self.sin_limite)
        exterior.addLayout(conexion)
        tarjetas = QHBoxLayout()
        self.roles, self.descripcion = {}, {}
        for rol, nombre in ROLES.items():
            marco = QFrame()
            marco.setStyleSheet("QFrame {background:rgba(18,39,54,165); border:1px solid #8b7959; border-radius:10px;}")
            layout = QVBoxLayout(marco)
            layout.setContentsMargins(16, 13, 16, 13)
            linea = QHBoxLayout()
            retrato = QLabel()
            imagen = pixmap_arte(f"personajes/{rol}_retrato.png")
            if not imagen.isNull():
                retrato.setPixmap(imagen.scaled(
                    68, 80, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation))
                linea.addWidget(retrato)
            descripcion = _etiqueta(
                "Escucha al barrio y acerca las correcciones a sus vecinos."
                if rol == "ciudadano" else
                "Recupera documentos y contrasta las versiones con sus fuentes.")
            linea.addWidget(descripcion, 1)
            layout.addLayout(linea)
            estado = _etiqueta("Conéctate para ver disponibilidad")
            layout.addWidget(estado)
            boton = _boton("Elegir " + nombre)
            boton.setCheckable(True)
            boton.setEnabled(False)
            boton.clicked.connect(lambda checked=False, elegido=rol: self.reservar.emit(elegido))
            layout.addWidget(boton)
            self.roles[rol], self.descripcion[rol] = boton, estado
            tarjetas.addWidget(marco, 1)
        exterior.addLayout(tarjetas)
        self.estado = _etiqueta("Dos participantes, un Ciudadano y una Periodista. Cada personaje se reserva en tiempo real.")
        exterior.addWidget(self.estado)
        pie = QHBoxLayout()
        self.liberar = _boton("Liberar personaje")
        self.liberar.clicked.connect(self.liberar_personaje)
        self.liberar.setEnabled(False)
        self.reintentar = _boton("Reconectar")
        self.reintentar.clicked.connect(self.reconectar.emit)
        self.reintentar.hide()
        self.iniciar = _boton("Comenzar historia")
        self.iniciar.clicked.connect(self.comenzar.emit)
        self.iniciar.setEnabled(False)
        pie.addWidget(self.liberar)
        pie.addWidget(self.reintentar)
        pie.addStretch()
        pie.addWidget(self.iniciar)
        exterior.addLayout(pie)
        self.red_info = _etiqueta("El anfitrión mantiene abierta la sala. No se modifica el firewall del equipo.")
        self.red_info.setStyleSheet("font-size:13px; color:#b9cbce;")
        exterior.addWidget(self.red_info)
        aplicar_estilo(self)
        self.ajustar_tamano(840, 660)

    def liberar_personaje(self):
        self.soltar.emit()

    def _conectar(self, crear):
        self.conectar.emit(
            crear, self.host.text().strip(), self.puerto.value(), self.nombre.text().strip())

    def actualizar(self, mensaje, mi_id=None):
        self.mi_id = mi_id or mensaje.get("mi_id", self.mi_id)
        self._conectada = True
        for widget in (self.nombre, self.host, self.puerto, self.crear, self.unirse):
            widget.setEnabled(False)
        self.reintentar.hide()
        ocupados = mensaje.get("roles_ocupados", {})
        jugadores = mensaje.get("jugadores", [])
        mi_rol = next((j.get("rol") for j in jugadores if j.get("id") == self.mi_id), None)
        for rol, boton in self.roles.items():
            titular = ocupados.get(rol)
            propio = bool(titular and titular.get("id") == self.mi_id)
            boton.setChecked(propio)
            boton.setEnabled(titular is None or propio)
            boton.setText("Tu personaje ✓" if propio else "Ocupado" if titular else "Elegir " + ROLES[rol])
            self.descripcion[rol].setText(
                "Reservado por ti" if propio else
                "Reservado por " + titular["nombre"] if titular else "Disponible")
            boton.setAccessibleDescription(self.descripcion[rol].text())
        soy_host = mensaje.get("anfitrion") == self.mi_id
        self.iniciar.setEnabled(soy_host and bool(mensaje.get("puede_iniciar")))
        self.liberar.setEnabled(mi_rol is not None)
        self.sin_limite.setEnabled(soy_host)
        bloqueado = self.sin_limite.blockSignals(True)
        self.sin_limite.setChecked(bool(mensaje.get("sin_limite", False)))
        self.sin_limite.blockSignals(bloqueado)
        self.estado.setText(" · ".join(
            f"{j['nombre']}: {ROLES.get(j.get('rol'), 'eligiendo personaje')}" for j in jugadores))
        if mensaje.get("esperando_creador"):
            self.estado.setText(self.estado.text() + "\nEsperando al creador de la sala.")
        elif mensaje.get("puede_iniciar") and not soy_host:
            self.estado.setText(self.estado.text() + "\nTu compañero puede comenzar la historia.")
        direcciones = mensaje.get("direcciones_lan", [])
        if direcciones:
            self.red_info.setText(
                "Dirección para el segundo dispositivo: " + " / ".join(direcciones)
                + f" · Puerto {mensaje.get('puerto', self.puerto.value())}.")

    def desconectada(self, texto):
        self._conectada = False
        for widget in (self.nombre, self.host, self.puerto, self.crear, self.unirse):
            widget.setEnabled(True)
        for boton in self.roles.values():
            boton.setEnabled(False)
            boton.setChecked(False)
        self.iniciar.setEnabled(False)
        self.liberar.setEnabled(False)
        self.reintentar.show()
        self.estado.setText(texto + " Puedes volver a conectar sin cerrar esta sala.")

    def paintEvent(self, event):
        if self._marco.isNull():
            return super().paintEvent(event)
        pintor = QPainter(self)
        pintor.fillRect(self.rect(), QColor("#182d41"))
        _nueve_segmentos(pintor, QRectF(self.rect()).adjusted(4, 4, -4, -4), self._marco)
        pintor.end()
