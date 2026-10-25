"""Adaptador de fondo vivo para las escenas que conservan la API de QLabel."""
from PyQt6.QtGui import QPixmap, QPainter, QColor
from ambiente_visual import FondoVivo


class FondoEscena(FondoVivo):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._foto_respaldo = QPixmap()
        self.oscuridad = 0

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.oscuridad:
            pintor = QPainter(self)
            pintor.fillRect(self.rect(), QColor(4, 13, 23, self.oscuridad))

    def setAlignment(self, _alineacion):
        pass  # FondoVivo conserva siempre el recorte proporcional centrado.

    def setScaledContents(self, _escalar):
        pass

    def setPixmap(self, imagen):
        self._foto_respaldo = imagen
        if not self._ruta:
            self._pixmap = imagen
            self._cache_clave = None
            self.update()

    def pixmap(self):
        return self._foto_respaldo if not self._foto_respaldo.isNull() else self._pixmap
