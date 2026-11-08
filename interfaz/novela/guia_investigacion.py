"""Guía visual local: progreso y viaje de una prueba, sin alterar la sesión."""
from PyQt6.QtCore import QPoint, QRect, QPropertyAnimation, QEasingCurve, Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QLabel, QWidget


class ProgresoInvestigacion(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.paso = 1
        self.completos = set()
        self.setFixedHeight(22)
        self.setAccessibleName("Progreso de la investigación")

    def actualizar(self, paso, completos):
        self.paso = paso
        self.completos = set(completos)
        self.setAccessibleDescription(f"Paso {paso} de 3; {len(completos)} completados")
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        centros = [round(self.width()*(i+.5)/3) for i in range(3)]
        p.setPen(QPen(QColor("#cbb991"), 3))
        centro_y = self.height()//2
        p.drawLine(centros[0], centro_y, centros[-1], centro_y)
        for i,x in enumerate(centros,1):
            p.setPen(QPen(QColor("#b18a41") if i <= self.paso else QColor("#a99d85"), 2))
            p.setBrush(QColor("#b18a41") if i in self.completos else QColor("#17243d") if i == self.paso else QColor("#f3ead6"))
            p.drawEllipse(QPoint(x,centro_y),6,6)
        p.end()


def viajar_prueba(parent, origen, destino, terminado):
    """Anima una etiqueta hasta Decidir; el resultado es el mismo sin movimiento."""
    if getattr(parent.window(), "reducir_movimiento", False):
        terminado()
        return
    etiqueta = QLabel("PRUEBA  →  TU RESPUESTA", parent)
    etiqueta.setStyleSheet("background:#17243d;color:#f5e4ba;border:2px solid #b99249;border-radius:12px;padding:6px;font:bold 15px 'Atkinson Hyperlegible';")
    etiqueta.setAlignment(Qt.AlignmentFlag.AlignCenter)
    ancho, alto = 260, 44
    etiqueta.setGeometry(QRect(origen-QPoint(ancho//2,alto//2), etiqueta.size()))
    etiqueta.resize(ancho,alto)
    etiqueta.show()
    etiqueta.raise_()
    animacion = QPropertyAnimation(etiqueta,b"pos",etiqueta)
    animacion.setDuration(520)
    animacion.setStartValue(etiqueta.pos())
    animacion.setEndValue(destino-QPoint(ancho//2,alto//2))
    animacion.setEasingCurve(QEasingCurve.Type.InOutCubic)
    def finalizar():
        etiqueta.deleteLater()
        terminado()
    animacion.finished.connect(finalizar)
    etiqueta._viaje = animacion
    animacion.start()
