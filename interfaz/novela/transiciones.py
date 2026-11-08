"""Fundido narrativo interrumpible que mantiene activa la interfaz de la novela."""
import math

from PyQt6.QtCore import QAbstractAnimation, QEvent, QRectF, Qt, QVariantAnimation, pyqtSignal
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QWidget


class TransicionNarrativa(QWidget):
    """Disuelve el cuadro anterior sobre el siguiente sin capturar la entrada."""
    terminada = pyqtSignal()
    DURACION_MS = 520

    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAccessibleName("Transición suave de escena")
        self._captura = QPixmap()
        self._avance = 0.0
        self._pendiente = False
        self._reducir = False
        self._animacion = QVariantAnimation(self)
        self._animacion.setDuration(self.DURACION_MS)
        self._animacion.setStartValue(0.0)
        self._animacion.setEndValue(1.0)
        self._animacion.valueChanged.connect(self._actualizar)
        self._animacion.finished.connect(self._terminar)
        parent.installEventFilter(self)
        self.hide()

    @property
    def animando(self):
        return self._animacion.state() == QAbstractAnimation.State.Running

    def configurar(self, reducir_movimiento=False):
        self._reducir = bool(reducir_movimiento)
        if self._reducir:
            self.cancelar()

    def capturar(self, widget):
        """Una captura nueva conserva incluso el fundido anterior a medio mostrar."""
        if widget is None or not widget.isVisible() or widget.size().isEmpty():
            self.cancelar()
            return False
        captura = widget.grab()
        self._animacion.stop()
        self.hide()
        self._captura = captura
        self._avance = 0.0
        self.setGeometry(self.parentWidget().rect())
        self._pendiente = not captura.isNull()
        return self._pendiente

    def revelar(self, reducir_movimiento=None):
        reducir = self._reducir if reducir_movimiento is None else bool(reducir_movimiento)
        reducir = reducir or bool(getattr(self.window(), "reducir_movimiento", False))
        if reducir:
            self.cancelar()
            return False
        if not self._pendiente:
            return False
        self._pendiente = False
        if self._captura.isNull() or not self.parentWidget().isVisible():
            self.cancelar()
            return False
        self._animacion.stop()
        self.setGeometry(self.parentWidget().rect())
        self._avance = 0.0
        self.show()
        self.raise_()
        self._animacion.start()
        return True

    def cancelar(self):
        self._pendiente = False
        self._animacion.stop()
        self._captura = QPixmap()
        self.hide()

    def _terminar(self):
        self._pendiente = False
        self._captura = QPixmap()
        self.hide()
        self.terminada.emit()

    def _actualizar(self, valor):
        self._avance = float(valor)
        self.update()

    def eventFilter(self, objeto, evento):
        if objeto is self.parentWidget():
            if evento.type() == QEvent.Type.Resize:
                self.setGeometry(objeto.rect())
            elif evento.type() == QEvent.Type.Hide:
                self.cancelar()
        return super().eventFilter(objeto, evento)

    def paintEvent(self, evento):
        if self._captura.isNull():
            return
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        avance = max(0.0, min(1.0, self._avance))
        suave = avance*avance*(3-2*avance)
        pintor.setOpacity(1-suave)
        pintor.drawPixmap(self.rect(), self._captura)
        pintor.setOpacity(1.0)
        # Una senda cálida muy tenue acompaña el relevo, sin cubrir el texto.
        intensidad = round(24*math.sin(math.pi*avance))
        x = -60+(self.width()+120)*avance
        luz = QLinearGradient(x-34, 0, x+34, 0)
        luz.setColorAt(0, QColor(221, 179, 106, 0))
        luz.setColorAt(.5, QColor(236, 203, 142, intensidad))
        luz.setColorAt(1, QColor(221, 179, 106, 0))
        pintor.fillRect(QRectF(x-34, 0, 68, self.height()), luz)
        pintor.setPen(QPen(QColor(10, 22, 29, intensidad//2), 1))
        pintor.drawLine(round(x+2), 0, round(x+2), self.height())
        pintor.end()
