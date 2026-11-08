"""Controles pintados para la novela: las etiquetas y el teclado siguen vivos."""
from pathlib import Path

from PyQt6.QtCore import QEvent, QObject, QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QPushButton, QToolButton, QWidget

from infraestructura.recursos import RAIZ
from interfaz.componentes.arte import (
    BotonIlustrado, FUENTE_UI, cargar_tipografias, pixmap_arte, _nueve_segmentos,
)

_IMAGENES = {}


def imagen_novela(nombre, respaldo=None):
    """Carga arte local y reconoce reemplazos sin reiniciar la aplicación."""
    ruta = RAIZ / "assets/novela" / nombre
    if ruta.is_file():
        clave = (str(ruta), ruta.stat().st_mtime_ns)
        if clave not in _IMAGENES:
            if len(_IMAGENES) > 48:
                _IMAGENES.clear()
            _IMAGENES[clave] = QPixmap(str(ruta))
        return _IMAGENES[clave]
    return pixmap_arte(respaldo) if respaldo else QPixmap()


def _pintar(boton):
    p = QPainter(boton)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    estado = "inactivo" if not boton.isEnabled() else "pulsado" if boton.isDown() or boton.isChecked() else "hover" if boton.underMouse() else "normal"
    imagen = imagen_novela(f"ui/boton_{estado}.png", "ui/boton.png")
    rect = QRectF(boton.rect()).adjusted(1, 1, -1, -2)
    if not imagen.isNull():
        _nueve_segmentos(p, rect, imagen, .20)
    else:
        p.setPen(QPen(QColor("#c69a66"), 2))
        p.setBrush(QColor("#16243d"))
        p.drawRoundedRect(rect, 12, 12)
    if boton.hasFocus():
        p.setPen(QPen(QColor("#ffe4aa"), 2, Qt.PenStyle.DashLine))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(rect.adjusted(7, 7, -7, -7), 8, 8)
    texto = rect.adjusted(21, 7, -21, -7)
    tiene_menu = isinstance(boton, QToolButton) and boton.menu() is not None
    if tiene_menu:
        texto.adjust(0, 0, -14, 0)
    if not boton.icon().isNull():
        tam = min(28, max(18, boton.height() - 24))
        boton.icon().paint(p, round(texto.left()), round(rect.center().y() - tam / 2), tam, tam)
        texto.adjust(tam + 8, 0, 0, 0)
    fuente = QFont(boton.font())
    if fuente.pixelSize() < 14 and fuente.pointSizeF() < 11:
        fuente.setPixelSize(17)
    fuente.setBold(True)
    p.setFont(fuente)
    flags = Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap | Qt.TextFlag.TextShowMnemonic
    p.setPen(QColor("#101b29"))
    p.drawText(texto.translated(0, 1), flags, boton.text())
    p.setPen(QColor("#fff0d3" if boton.isEnabled() else "#c9c5be"))
    p.drawText(texto, flags, boton.text())
    if tiene_menu:
        x, y = round(rect.right() - 16), round(rect.center().y())
        p.setPen(QPen(QColor("#fff0d3"), 2))
        p.drawLine(x - 4, y - 2, x, y + 2)
        p.drawLine(x, y + 2, x + 4, y - 2)


class BotonNovela(BotonIlustrado):
    def __init__(self, texto="", parent=None):
        super().__init__(texto, parent)
        cargar_tipografias()
        fuente = QFont(FUENTE_UI)
        fuente.setPixelSize(17)
        fuente.setBold(True)
        self.setFont(fuente)
        self.setMinimumHeight(50)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(texto.replace("&", ""))

    def paintEvent(self, event):
        _pintar(self)

    def sizeHint(self):
        icono = 36 if not self.icon().isNull() else 0
        return QSize(max(120, self.fontMetrics().horizontalAdvance(self.text().replace("&", "")) + 48 + icono),
                     max(50, self.fontMetrics().height() + 26))


class _PielNovela(QObject):
    def eventFilter(self, boton, event):
        if event.type() == QEvent.Type.Paint:
            _pintar(boton)
            return True
        if event.type() in (QEvent.Type.Enter, QEvent.Type.Leave, QEvent.Type.FocusIn,
                            QEvent.Type.FocusOut, QEvent.Type.EnabledChange,
                            QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease):
            boton.update()
        return False


def decorar_novela(widget):
    """Reviste botones simples y conserva las tarjetas que pintan su contenido."""
    cargar_tipografias()
    botones = widget.findChildren(QPushButton) + widget.findChildren(QToolButton)
    if isinstance(widget, (QPushButton, QToolButton)):
        botones.append(widget)
    for boton in botones:
        pintura = type(boton).paintEvent
        propia = (bool(boton.property("conservarPintura"))
                  or pintura not in (QPushButton.paintEvent, QToolButton.paintEvent,
                                     BotonIlustrado.paintEvent, BotonNovela.paintEvent))
        if propia:
            piel = getattr(boton, "_piel_novela", None)
            if piel is not None:
                boton.removeEventFilter(piel)
                del boton._piel_novela
                piel.deleteLater()
                boton.update()
            continue
        if isinstance(boton, BotonNovela) or hasattr(boton, "_piel_novela"):
            continue
        boton._piel_novela = _PielNovela(boton)
        boton.installEventFilter(boton._piel_novela)
        boton.setCursor(Qt.CursorShape.PointingHandCursor)
        boton.update()


class MarcoNovela(QWidget):
    """Papel pintado que deja el texto en widgets accesibles."""
    def __init__(self, parent=None, recurso="ui/marco_expediente.png"):
        super().__init__(parent)
        self.recurso = recurso
        self.setObjectName("papelNovela")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        imagen = imagen_novela(self.recurso)
        if imagen.isNull():
            p.setPen(QPen(QColor("#ac885a"), 2))
            p.setBrush(QColor("#f2e5c9"))
            p.drawRoundedRect(QRectF(self.rect()).adjusted(2, 2, -2, -2), 18, 18)
        else:
            _nueve_segmentos(p, QRectF(self.rect()), imagen, .16)
