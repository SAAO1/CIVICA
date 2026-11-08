"""Visor de pruebas recuperadas y del material común habilitado para explorar."""
from pathlib import Path

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QSizePolicy, QSlider, QVBoxLayout, QWidget,
)

from infraestructura.recursos import RAIZ
from interfaz.feria.estilos import ESTILO_FERIA


class ComparadorPrueba(QWidget):
    """Divisor arrastrable; el original exige recuperación o permiso explícito.

    Arrastrar y usar las flechas modifica el mismo valor que se envía al
    comando examinar. Un material común inspeccionable se puede explorar sin
    registrarlo como hallazgo; recuperar una prueba sigue siendo una regla del motor.
    """

    valor_cambiado = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.valor = 0
        self.recuperado = False
        self.inspeccionable = False
        self.recorte = QPixmap()
        self.original = QPixmap()
        self._firma = None
        self.setMinimumSize(360, 255)
        self.setMaximumHeight(380)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.SplitHCursor)
        self.setAccessibleName("Comparar recorte y documento original")
        self.setAccessibleDescription("Arrastra el divisor o usa las flechas. Confirma con Examinar este punto para recuperar el contexto.")

    @staticmethod
    def _imagen(ruta):
        if not ruta:
            return QPixmap()
        archivo = Path(ruta)
        archivo = archivo if archivo.is_absolute() else RAIZ / archivo
        return QPixmap(str(archivo)) if archivo.is_file() else QPixmap()

    def actualizar(self, recorte, original, recuperado=False, inspeccionable=False):
        firma = (str(recorte), str(original), bool(recuperado), bool(inspeccionable))
        if self._firma != firma or self.recorte.isNull():
            self._firma = firma
            self.recuperado = bool(recuperado)
            self.inspeccionable = bool(inspeccionable)
            self.recorte = self._imagen(recorte)
            self.original = self._imagen(original) if self.recuperado or self.inspeccionable else QPixmap()
        self.update()

    def establecer_valor(self, valor):
        valor = max(0, min(100, int(valor)))
        if valor != self.valor:
            self.valor = valor
            self.update()
            self.valor_cambiado.emit(valor)

    def _desde_posicion(self, posicion):
        self.establecer_valor(round(max(0, min(self.width(), posicion)) * 100 / max(1, self.width())))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setFocus()
            self._desde_posicion(event.position().x())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._desde_posicion(event.position().x())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Home, Qt.Key.Key_End):
            if event.key() == Qt.Key.Key_Home:
                valor = 0
            elif event.key() == Qt.Key.Key_End:
                valor = 100
            else:
                valor = self.valor + (-5 if event.key() == Qt.Key.Key_Left else 5)
            self.establecer_valor(valor)
            event.accept()
            return
        super().keyPressEvent(event)

    def _pintar_imagen(self, pintor, imagen):
        if imagen.isNull():
            return
        escalada = imagen.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                 Qt.TransformationMode.SmoothTransformation)
        pintor.drawPixmap((self.width() - escalada.width()) // 2,
                          (self.height() - escalada.height()) // 2, escalada)

    def paintEvent(self, event):
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        pintor.fillRect(self.rect(), QColor("#ebdec6"))
        if self.recorte.isNull():
            pintor.setPen(QColor("#273746"))
            pintor.drawText(self.rect().adjusted(18, 45, -18, -20),
                            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                            "El recorte está en el texto de esta prueba.\nMueve el divisor para buscar su contexto.")
        else:
            self._pintar_imagen(pintor, self.recorte)
        corte = self.width() * self.valor / 100
        pintor.save()
        pintor.setClipRect(QRectF(0, 0, corte, self.height()))
        pintor.fillRect(self.rect(), QColor("#f8edda"))
        if (self.recuperado or self.inspeccionable) and not self.original.isNull():
            self._pintar_imagen(pintor, self.original)
        else:
            pintor.setPen(QColor("#42555f"))
            pintor.drawText(self.rect().adjusted(18, 50, -18, -25),
                            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                            "El original todavía no está en tu expediente.\nAmplía y confirma el punto que quieres examinar.")
        pintor.restore()
        pintor.fillRect(0, 0, self.width(), 34, QColor("#203d4d"))
        fuente = QFont(self.font())
        fuente.setPixelSize(14)
        fuente.setBold(True)
        pintor.setFont(fuente)
        pintor.setPen(QColor("#f8edda"))
        izquierda = "ORIGINAL RECUPERADO" if self.recuperado else "BUSCA EL CONTEXTO" if self.inspeccionable else "CONTEXTO POR RECUPERAR"
        pintor.drawText(self.rect().adjusted(12, 0, -12, -self.height() + 34),
                        Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, izquierda)
        pintor.drawText(self.rect().adjusted(12, 0, -12, -self.height() + 34),
                        Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, "RECORTE")
        pintor.setPen(QPen(QColor("#ec9b87"), 3))
        pintor.drawLine(QPointF(corte, 34), QPointF(corte, self.height()))
        pintor.setBrush(QColor("#203d4d"))
        pintor.drawEllipse(QPointF(corte, self.height() / 2), 18, 18)
        pintor.setPen(QColor("#f8edda"))
        pintor.drawText(QRectF(corte - 18, self.height() / 2 - 18, 36, 36),
                        Qt.AlignmentFlag.AlignCenter, "↔")


class DialogoPrueba(QDialog):
    """El mismo instrumento, ampliado para leer el documento y confirmar."""

    valor_cambiado = pyqtSignal(int)
    examinar_solicitado = pyqtSignal(int)

    def __init__(self, medio, valor=0, puede_examinar=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ampliar prueba · CIVICA")
        self.setObjectName("tableroInvestigacion")
        self.setStyleSheet(parent.styleSheet() if parent is not None else ESTILO_FERIA)
        self.resize(1040, 680)
        self.setMinimumSize(780, 520)
        self.setSizeGripEnabled(True)
        self._tamano_base = QSize(1400, 900)
        self._medio = dict(medio)
        contenido = QVBoxLayout(self)
        contenido.setContentsMargins(20, 16, 20, 16)
        titulo = QLabel("El contexto, de cerca")
        titulo.setObjectName("tituloCaso")
        contenido.addWidget(titulo)
        self.consigna = QLabel()
        self.consigna.setWordWrap(True)
        self.consigna.setTextFormat(Qt.TextFormat.PlainText)
        contenido.addWidget(self.consigna)
        fila = QHBoxLayout()
        fila.addWidget(QLabel("Tamaño de lectura"))
        self.zoom = QComboBox()
        self.zoom.setAccessibleName("Ampliación del documento")
        for texto, escala in (("Ajustar al ancho", 0), ("75 %", .75), ("Tamaño real · 100 %", 1), ("125 %", 1.25), ("150 %", 1.5)):
            self.zoom.addItem(texto, escala)
        fila.addWidget(self.zoom)
        fila.addStretch()
        contenido.addLayout(fila)
        self.area = QScrollArea()
        self.area.setWidgetResizable(False)
        self.comparador = ComparadorPrueba()
        self.comparador.setMaximumHeight(16777215)
        self.area.setWidget(self.comparador)
        contenido.addWidget(self.area, 1)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setAccessibleName("Divisor del documento ampliado")
        self.slider.setValue(valor)
        self.comparador.establecer_valor(valor)
        self.slider.valueChanged.connect(self.comparador.establecer_valor)
        self.comparador.valor_cambiado.connect(self.slider.setValue)
        self.slider.valueChanged.connect(self.valor_cambiado)
        contenido.addWidget(self.slider)
        self.estado = QLabel("Arrastra el divisor o usa las flechas. Puedes ampliar y desplazarte para leer cada detalle.")
        self.estado.setWordWrap(True)
        self.estado.setTextFormat(Qt.TextFormat.PlainText)
        contenido.addWidget(self.estado)
        botones = QHBoxLayout()
        self.confirmar = QPushButton("Examinar este punto")
        self.confirmar.setObjectName("principal")
        self.confirmar.clicked.connect(lambda: self.examinar_solicitado.emit(self.slider.value()))
        cerrar = QPushButton("Volver al expediente")
        cerrar.clicked.connect(self.accept)
        botones.addWidget(self.confirmar)
        botones.addStretch()
        botones.addWidget(cerrar)
        contenido.addLayout(botones)
        self.zoom.currentIndexChanged.connect(self._ajustar_tamano)
        self.actualizar(medio, puede_examinar)

    def actualizar(self, medio, puede_examinar=False):
        self._medio = dict(medio)
        recuperado = bool(medio.get("revelado") or medio.get("recuperado"))
        self.comparador.actualizar(medio.get("imagen_recortada"), medio.get("imagen_completa"),
                                   recuperado=recuperado, inspeccionable=bool(medio.get("inspeccionable")))
        imagen = self.comparador.original if not self.comparador.original.isNull() else self.comparador.recorte
        if not imagen.isNull():
            self._tamano_base = imagen.size()
        self.consigna.setText(medio.get("consigna", "Busca el contexto que falta en el recorte."))
        self.confirmar.setEnabled(bool(puede_examinar and not recuperado))
        self.confirmar.setText("Contexto recuperado" if recuperado else "Examinar este punto")
        if recuperado:
            self.estado.setText("La pieza completa ya está en tu expediente. Puedes seguir comparando el original y el recorte.")
        self._ajustar_tamano()

    def establecer_valor(self, valor):
        self.slider.setValue(valor)

    def mostrar_estado(self, texto):
        self.estado.setText(str(texto))

    def _ajustar_tamano(self, *args):
        escala = self.zoom.currentData()
        if escala == 0:
            escala = max(360, self.area.viewport().width() - 4) / max(1, self._tamano_base.width())
        self.comparador.setFixedSize(max(360, round(self._tamano_base.width() * escala)),
                                    max(255, round(self._tamano_base.height() * escala)))

    def resizeEvent(self, event):
        if hasattr(self, "zoom"):
            self._ajustar_tamano()
        super().resizeEvent(event)
