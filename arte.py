"""Piel ilustrada compartida por las escenas; la interacción sigue siendo Qt.

Los recursos son opcionales: el juego conserva una presentación legible cuando un
paquete artístico todavía no se encuentra instalado. No se carga arte fuera de
``assets/rediseno`` y ``assets/expansion``; se reconocen recursos nuevos sin reiniciar.
"""
from pathlib import Path

from catalogo_ciudadanos import (COLUMNAS_ATLAS_CIUDADANOS, FILAS_ATLAS_CIUDADANOS,
                                 RUTA_ATLAS_CIUDADANOS, indice_retrato_ciudadano)
from PyQt6.QtCore import QObject, QEvent, QMargins, QRectF, QSize, Qt
from PyQt6.QtGui import (QBitmap, QColor, QFontDatabase, QIcon, QLinearGradient,
                         QPainter, QPen, QPixmap, QRegion)
from PyQt6.QtWidgets import QFrame, QPushButton, QToolButton, QCheckBox, QSlider, QStyle


RAIZ_ARTE = Path(__file__).resolve().parent / "assets" / "rediseno"
RAIZ_EXPANSION = Path(__file__).resolve().parent / "assets" / "expansion"
RAIZ_FUENTES = Path(__file__).resolve().parent / "assets" / "fuentes"
# La misma familia sirve para lectura y controles; viaja con el juego.
FUENTE_UI = "Atkinson Hyperlegible"
FUENTE_DIALOGO = FUENTE_UI
_PIXMAPS = {}
_MARCOS = {}
_ICONOS = {}
_AVATARES = {}
_MINIATURAS = {}
IDS_AVATARES = ("ana", "luis", "pedro", "maria", "carlos", "sofia", "elena", "diego", "ines")
_TIPOGRAFIAS = None
NOMBRES_ICONOS = (
    "compartir", "verificar", "ignorar", "reportar", "ayuda", "ajustes",
    "guardar", "cargar", "portada", "sala", "reconectar", "pantalla",
    "confianza", "convivencia", "bienestar", "info_verificada", "desinformacion", "conflictos",
    "participacion", "puntos", "reputacion", "logro", "tiempo", "pausa",
)

ESTILO_ARTE = """
QWidget { font-family: "@FUENTE_UI@"; font-size: 16px; color: #f6e8cd; }
QDialog { background-color: #182d41; }
QLabel { background: transparent; color: #f6e8cd; }
QPushButton { color: #f6e8cd; background: #294c60; border: 1px solid #bd8855;
  border-radius: 10px; padding: 11px 18px; min-height: 26px; font-weight: 600; }
QToolButton { color: #f6e8cd; padding: 8px 12px; min-height: 26px; }
QPushButton:hover { background: #477f83; border-color: #edc995; }
QPushButton:pressed, QPushButton:checked { background: #305c65; border-color: #f6e8cd; }
QPushButton:focus { border: 2px solid #f6e8cd; }
QPushButton:disabled { color: #9ba9af; background: #283b49; border-color: #69767c; }
QComboBox, QLineEdit { background: #233e50; color: #fff4dc; border: 1px solid #a8855d;
  border-radius: 7px; padding: 9px 12px; selection-background-color: #477f83; }
QComboBox:focus, QLineEdit:focus { border: 2px solid #eac899; }
QComboBox QAbstractItemView { background: #233e50; color: #fff4dc;
  selection-background-color: #477f83; border: 1px solid #bd8855; }
QComboBox::drop-down { border: none; width: 23px; }
QTextBrowser { color: #f6e8cd; background: #20394c; border: 1px solid #756e60;
  border-radius: 9px; padding: 18px; font-size: 17px; }
QCheckBox { color: #f6e8cd; spacing: 10px; padding: 7px 3px; }
QCheckBox::indicator { width: 20px; height: 20px; border: 1px solid #bd8855;
  border-radius: 4px; background: #233e50; }
QCheckBox::indicator:checked { background: #70a59d; border: 4px solid #e7c797; }
QSlider::groove:horizontal { height: 6px; border-radius: 3px; background: #435766; }
QSlider::sub-page:horizontal { background: #83b7ac; border-radius: 3px; }
QSlider::handle:horizontal { width: 18px; margin: -7px 0; background: #f0d7ac;
  border: 2px solid #bd8855; border-radius: 10px; }
QTabWidget::pane { border: none; background: transparent; }
QTabBar::tab { background: #243e50; color: #c5c8bd; border: 1px solid #64736f;
  border-top-left-radius: 7px; border-top-right-radius: 7px; padding: 10px 14px; }
QTabBar::tab:selected { background: #436d71; color: #fff1d6; border-color: #bd8855; }
QTabBar::tab:focus { border: 2px solid #f6e8cd; }
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { width: 10px; background: #1c3445; border: none; margin: 0; }
QScrollBar::handle:vertical { background: #7b9a95; min-height: 25px; border-radius: 5px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QToolTip { color: #182d41; background: #f6e8cd; border: 1px solid #bd8855; padding: 7px; }
""".replace("@FUENTE_UI@", FUENTE_UI)


def cargar_tipografias():
    """Registra la familia portátil una sola vez, después de QApplication.

    No requiere instalar fuentes ni conectarse a Internet. Se conservan las
    fuentes del sistema como respaldo para pantallas antiguas del juego.
    """
    global _TIPOGRAFIAS
    if _TIPOGRAFIAS is None:
        _TIPOGRAFIAS = {}
        archivos = sorted(RAIZ_FUENTES.glob("*.ttf"))
        carpeta = Path("C:/Windows/Fonts")
        archivos.extend(carpeta / nombre for nombre in (
            "segoeui.ttf", "segoeuib.ttf", "segoeuii.ttf", "segoeuiz.ttf",
            "georgia.ttf", "georgiab.ttf", "georgiai.ttf", "georgiaz.ttf"))
        for archivo in archivos:
            if archivo.is_file():
                identificador = QFontDatabase.addApplicationFont(str(archivo))
                if identificador >= 0:
                    _TIPOGRAFIAS[archivo.name] = tuple(QFontDatabase.applicationFontFamilies(identificador))
    return dict(_TIPOGRAFIAS)


def _caja_alfa(pixmap):
    if not pixmap.hasAlphaChannel():
        return pixmap.rect()
    mascara = pixmap.toImage().createAlphaMask(Qt.ImageConversionFlag.ThresholdAlphaDither)
    return QRegion(QBitmap.fromImage(mascara)).boundingRect()


def pixmap_arte(rel):
    """Carga un PNG del paquete artístico sin permitir rutas externas."""
    try:
        ruta_relativa = Path(rel)
        if ruta_relativa.is_absolute() or ".." in ruta_relativa.parts:
            return QPixmap()
        ruta = (RAIZ_ARTE / ruta_relativa).resolve()
        if not ruta.is_relative_to(RAIZ_ARTE.resolve()) or not ruta.is_file():
            return QPixmap()
        clave = (str(ruta), ruta.stat().st_mtime_ns)
        if clave not in _PIXMAPS:
            if len(_PIXMAPS) >= 48:
                _PIXMAPS.clear()
            _PIXMAPS[clave] = QPixmap(str(ruta))
        return _PIXMAPS[clave]
    except (OSError, TypeError, ValueError):
        return QPixmap()


def dibujar_fondo(painter, rect, ruta):
    """Dibuja el fondo con recorte centrado, sin deformar la ilustración."""
    pixmap = pixmap_arte(ruta)
    destino = QRectF(rect)
    if pixmap.isNull() or destino.width() <= 0 or destino.height() <= 0:
        return False
    factor = max(destino.width() / pixmap.width(), destino.height() / pixmap.height())
    ancho, alto = destino.width() / factor, destino.height() / factor
    origen = QRectF((pixmap.width() - ancho) / 2, (pixmap.height() - alto) / 2, ancho, alto)
    painter.drawPixmap(destino, pixmap, origen)
    return True


def icono_arte(nombre):
    """Obtiene un icono del atlas de seis columnas por cuatro filas."""
    if nombre not in NOMBRES_ICONOS:
        return QIcon()
    atlas = pixmap_arte("ui/iconos.png")
    if atlas.isNull():
        return QIcon()
    clave = (atlas.cacheKey(), nombre)
    if clave not in _ICONOS:
        indice = NOMBRES_ICONOS.index(nombre)
        columna, fila = indice % 6, indice // 6
        x0, x1 = round(columna * atlas.width()/6), round((columna+1) * atlas.width()/6)
        y0, y1 = round(fila * atlas.height()/4), round((fila+1) * atlas.height()/4)
        celda = atlas.copy(x0, y0, x1-x0, y1-y0)
        if celda.hasAlphaChannel():
            caja = _caja_alfa(celda)
            if caja.isValid():
                margen = max(3, round(min(celda.width(), celda.height()) * .035))
                celda = celda.copy(caja.adjusted(-margen, -margen, margen, margen).intersected(celda.rect()))
        _ICONOS[clave] = QIcon(celda)
        if len(_ICONOS) > 96:
            conservado = _ICONOS[clave]
            _ICONOS.clear()
            _ICONOS[clave] = conservado
    return _ICONOS[clave]


def _atlas_ciudadanos_expandido():
    """Carga sólo el atlas local; reconoce reemplazos sin reiniciar el juego."""
    try:
        raiz = RAIZ_EXPANSION.resolve()
        ruta = (raiz / RUTA_ATLAS_CIUDADANOS).resolve()
        if not ruta.is_relative_to(raiz) or not ruta.is_file():
            return QPixmap()
        estado = ruta.stat()
        clave = (str(ruta), estado.st_mtime_ns, estado.st_size)
        if clave not in _PIXMAPS:
            if len(_PIXMAPS) >= 48:
                _PIXMAPS.clear()
            imagen = QPixmap()
            # Evita la caché interna por nombre de Qt al reemplazar el atlas.
            imagen.loadFromData(ruta.read_bytes())
            _PIXMAPS[clave] = imagen
        return _PIXMAPS[clave]
    except (OSError, TypeError, ValueError):
        return QPixmap()


def avatar_arte(id):
    """Retrato individual o celda del atlas ciudadano; no genera archivos.

    Conserva las nueve caras originales. Los demás ciudadanos reciben una
    fotografía del catálogo ampliado, incluidos los IDs de partidas futuras.
    """
    individual = pixmap_arte(f"avatares/{id}.png")
    if not individual.isNull():
        return individual
    if id in IDS_AVATARES:
        atlas = pixmap_arte("avatares/ciudadanos.png")
        indice = IDS_AVATARES.index(id)
        columnas = filas = 3
    else:
        atlas = _atlas_ciudadanos_expandido()
        indice = indice_retrato_ciudadano(id)
        columnas, filas = COLUMNAS_ATLAS_CIUDADANOS, FILAS_ATLAS_CIUDADANOS
    if atlas.isNull():
        return QPixmap()
    clave = (atlas.cacheKey(), indice, columnas, filas)
    if clave not in _AVATARES:
        columna, fila = indice % columnas, indice // columnas
        x0, x1 = round(columna*atlas.width()/columnas), round((columna+1)*atlas.width()/columnas)
        y0, y1 = round(fila*atlas.height()/filas), round((fila+1)*atlas.height()/filas)
        _AVATARES[clave] = atlas.copy(x0, y0, x1-x0, y1-y0)
        if len(_AVATARES) > 128:
            conservado = _AVATARES[clave]
            _AVATARES.clear()
            _AVATARES[clave] = conservado
    return _AVATARES[clave]


def miniatura_publicacion(id):
    ids = (50, 30, 70, 20, 60, 80)
    atlas = pixmap_arte("publicaciones/noticias.png")
    if atlas.isNull() or id not in ids:
        return QPixmap()
    clave = (atlas.cacheKey(), id)
    if clave not in _MINIATURAS:
        indice = ids.index(id)
        columna, fila = indice % 3, indice // 3
        x0, x1 = round(columna*atlas.width()/3), round((columna+1)*atlas.width()/3)
        y0, y1 = round(fila*atlas.height()/2), round((fila+1)*atlas.height()/2)
        _MINIATURAS[clave] = atlas.copy(x0+3, y0+3, max(1, x1-x0-6), max(1, y1-y0-6))
    return _MINIATURAS[clave]


def _marco_recortado(pixmap):
    """Reutiliza el marco sin el espacio transparente que rodea al PNG."""
    clave = pixmap.cacheKey()
    if clave not in _MARCOS:
        caja = _caja_alfa(pixmap)
        if caja.isValid():
            _MARCOS[clave] = pixmap.copy(caja)
        else:
            _MARCOS[clave] = pixmap
        if len(_MARCOS) > 48:
            conservado = _MARCOS[clave]
            _MARCOS.clear()
            _MARCOS[clave] = conservado
    return _MARCOS[clave]


def _dibujar_segmentos(painter, rect, pixmap, corte_x, corte_y, escala):
    """Estira las superficies centrales; todas las esquinas comparten escala.

    Los límites del destino se redondean una sola vez y se comparten entre
    celdas contiguas. Así no aparecen líneas transparentes entre segmentos.
    """
    destino = QRectF(rect)
    if pixmap.isNull() or destino.width() <= 0 or destino.height() <= 0:
        return
    ancho, alto = pixmap.width(), pixmap.height()
    corte_x = max(1, min(int(corte_x), (ancho-1)//2))
    corte_y = max(1, min(int(corte_y), (alto-1)//2))
    escala = min(escala, destino.width()/(2*corte_x), destino.height()/(2*corte_y))
    xs = (0, corte_x, ancho-corte_x, ancho)
    ys = (0, corte_y, alto-corte_y, alto)
    dx = (destino.left(), round(destino.left()+corte_x*escala),
          round(destino.right()-corte_x*escala), destino.right())
    dy = (destino.top(), round(destino.top()+corte_y*escala),
          round(destino.bottom()-corte_y*escala), destino.bottom())
    for fila in range(3):
        for columna in range(3):
            if dx[columna+1] <= dx[columna] or dy[fila+1] <= dy[fila]:
                continue
            origen = QRectF(xs[columna], ys[fila], xs[columna+1]-xs[columna], ys[fila+1]-ys[fila])
            celda = QRectF(dx[columna], dy[fila], dx[columna+1]-dx[columna], dy[fila+1]-dy[fila])
            painter.drawPixmap(celda, pixmap, origen)


def _nueve_segmentos(painter, rect, pixmap, fraccion=.15):
    """Redimensiona el material conservando las proporciones de sus adornos."""
    if pixmap.isNull():
        return
    pixmap = _marco_recortado(pixmap)
    destino = QRectF(rect)
    corte_x = round(pixmap.width()*fraccion)
    corte_y = round(pixmap.height()*fraccion)
    escala = min(destino.width()/pixmap.width(), destino.height()/pixmap.height())
    if fraccion <= .20:
        # Un panel grande no necesita esquinas gigantes. Las superficies
        # centrales pueden crecer mientras el marco sigue siendo discreto.
        escala = min(escala, 64/max(1, corte_x, corte_y))
    _dibujar_segmentos(painter, destino, pixmap, corte_x, corte_y, escala)


def margenes_marco(recurso, tamano):
    """Márgenes de contenido, en píxeles lógicos, libres de los adornos.

    Se pueden pasar directamente a ``layout.setContentsMargins``. No se
    alteran los márgenes de los widgets ni sus áreas de interacción Qt.
    """
    ancho, alto = tamano.width(), tamano.height()
    if recurso == "ui/dialogo.png":
        texto, _, pista = geometria_dialogo(QRectF(0, 0, ancho, alto))
        return QMargins(round(texto.left()), round(texto.top()),
                        round(ancho-texto.right()), round(alto-pista.bottom()))
    if recurso == "ui/boton.png":
        lateral = max(16, min(30, round(alto*.52)))
        return QMargins(lateral, 7, lateral, 7)
    # Las hojas de las esquinas terminan antes de estos límites incluso en
    # paneles muy anchos. En paneles pequeños los márgenes también se reducen.
    lateral = max(22, min(38, round(min(ancho, alto)*.075)))
    superior = max(28, min(42, round(min(ancho, alto)*.085)))
    return QMargins(lateral, superior, lateral, superior)


def _escala_dialogo(rect):
    rect = QRectF(rect)
    return min(max(230, min(360, rect.width()*.24))/650,
               max(0, rect.width())/1580, max(0, rect.height())/296)


def geometria_dialogo(rect):
    """Devuelve áreas seguras para texto, nombre y pista dentro del diálogo.

    La cartela conserva la misma escala uniforme que el fragmento original
    que la contiene; su ancho deja de depender del estiramiento del panel.
    """
    rect = QRectF(rect)
    escala = _escala_dialogo(rect)
    lateral = max(36, rect.width()*.045)
    nombre = QRectF(rect.left()+120*escala, rect.top()+7*escala,
                    602*escala, 66*escala)
    pista = QRectF(rect.left()+lateral, rect.bottom()-55,
                   max(1, rect.width()-2*lateral), 20)
    texto = QRectF(rect.left()+lateral, rect.top()+max(60, 102*escala),
                   max(1, rect.width()-2*lateral),
                   max(1, pista.top()-rect.top()-max(60, 102*escala)-12))
    return texto, nombre, pista


def dibujar_dialogo(painter, rect, alto_contraste=False):
    """Conserva la cartela integrada y las cuatro esquinas del diálogo."""
    pixmap = pixmap_arte("ui/dialogo.png")
    if pixmap.isNull():
        return False
    pixmap = _marco_recortado(pixmap)
    # La primera región incluye toda la cartela, de modo que ningún corte
    # atraviese su contorno. El centro superior sólo contiene borde recto.
    _dibujar_segmentos(painter, rect, pixmap, 790, 148, _escala_dialogo(rect))
    if alto_contraste:
        contenido, _, pista = geometria_dialogo(rect)
        interior = contenido.united(pista).adjusted(-12, -7, 12, 7)
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(2, 8, 15, 150))
        painter.drawRoundedRect(interior, 10, 10)
        painter.restore()
    return True


class PanelIlustrado(QFrame):
    def __init__(self, parent=None, recurso="ui/panel.png"):
        super().__init__(parent)
        self.recurso = recurso
        self.alto_contraste = False
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def margenes_seguros(self):
        return margenes_marco(self.recurso, self.size())

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        pixmap = pixmap_arte(self.recurso)
        if pixmap.isNull():
            gradiente = QLinearGradient(rect.topLeft(), rect.bottomRight())
            gradiente.setColorAt(0, QColor(24, 45, 65, 242))
            gradiente.setColorAt(1, QColor(31, 58, 72, 246))
            p.setBrush(gradiente)
            p.setPen(QPen(QColor("#bd8855"), 1))
            p.drawRoundedRect(rect, 18, 18)
        elif self.recurso == "ui/dialogo.png":
            dibujar_dialogo(p, rect, self.alto_contraste)
        else:
            _nueve_segmentos(p, rect, pixmap)
        p.end()


def _pintar_boton(boton):
    p = QPainter(boton)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    rect = QRectF(boton.rect()).adjusted(2, 2, -2, -3)
    presionado = boton.isDown() or boton.isChecked()
    recurso = boton.property("recursoArte") or "ui/boton.png"
    pixmap = pixmap_arte(recurso)
    if pixmap.isNull():
        p.setPen(QPen(QColor("#bd8855"), 1))
        p.setBrush(QColor("#294b5d"))
        p.drawRoundedRect(rect, 10, 10)
    else:
        if not boton.isEnabled():
            p.setOpacity(.55)
        elif presionado:
            p.setOpacity(.82)
        _nueve_segmentos(p, rect, pixmap, .22)
        p.setOpacity(1)
    if boton.isEnabled() and (presionado or boton.underMouse()):
        p.setPen(QPen(QColor("#f2d4a1"), 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(rect, 10, 10)
    if boton.hasFocus():
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor("#fff4d7"), 2, Qt.PenStyle.DashLine))
        p.drawRoundedRect(rect.adjusted(4, 4, -4, -4), 7, 7)
    margenes = margenes_marco(recurso, boton.size())
    texto_rect = rect.adjusted(margenes.left(), margenes.top(),
                               -margenes.right(), -margenes.bottom())
    tiene_menu = isinstance(boton, QToolButton) and boton.menu() is not None
    if tiene_menu:
        texto_rect.adjust(0, 0, -16, 0)
    if not boton.icon().isNull():
        tam = boton.iconSize()
        ancho_texto = boton.fontMetrics().horizontalAdvance(boton.text().replace("&", ""))
        grupo = tam.width() + 9 + ancho_texto
        x = int(max(texto_rect.left(), rect.center().x() - grupo / 2)
                if boton.text() else rect.center().x() - tam.width()/2)
        y = int(rect.center().y() - tam.height()/2)
        boton.icon().paint(p, x, y, tam.width(), tam.height())
        texto_rect.setLeft(x + tam.width() + 9)
        if grupo <= rect.width() - 34:
            texto_rect.setWidth(ancho_texto + 2)
    p.setFont(boton.font())
    color = QColor("#fff0d1") if boton.isEnabled() else QColor("#b9bfb9")
    flags = (Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextShowMnemonic
             | Qt.TextFlag.TextWordWrap)
    p.setPen(QColor(15, 30, 39, 230))
    p.drawText(texto_rect.translated(0, 1), flags, boton.text())
    p.setPen(color)
    p.drawText(texto_rect, flags, boton.text())
    if tiene_menu:
        p.setPen(QPen(color, 2))
        x, y = int(rect.right()-15), int(rect.center().y())
        p.drawLine(x-4, y-2, x, y+2)
        p.drawLine(x, y+2, x+4, y-2)
    p.end()


class _PielBoton(QObject):
    def eventFilter(self, boton, evento):
        if evento.type() == QEvent.Type.Paint:
            _pintar_boton(boton)
            return True
        if evento.type() in (QEvent.Type.Enter, QEvent.Type.Leave, QEvent.Type.FocusIn,
                             QEvent.Type.FocusOut, QEvent.Type.EnabledChange):
            boton.update()
        return False


class _PielControl(QObject):
    """Pinta materiales ilustrados manteniendo el teclado y ratón nativos."""
    def eventFilter(self, control, evento):
        if evento.type() != QEvent.Type.Paint:
            return False
        if isinstance(control, QSlider) and control.orientation() != Qt.Orientation.Horizontal:
            return False
        p = QPainter(control)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if not control.isEnabled():
            p.setOpacity(.5)
        if isinstance(control, QCheckBox):
            caja = QRectF(2, (control.height()-25)/2, 25, 25)
            medallon = pixmap_arte("ui/nodo.png")
            if not medallon.isNull():
                p.drawPixmap(caja, medallon, QRectF(medallon.rect()))
            if control.isChecked():
                marca = pixmap_arte("ui/check.png")
                if not marca.isNull():
                    marca = _marco_recortado(marca)
                    disponible = caja.adjusted(3, 3, -3, -3)
                    factor = min(disponible.width()/marca.width(), disponible.height()/marca.height())
                    ancho, alto = marca.width()*factor, marca.height()*factor
                    destino = QRectF(disponible.center().x()-ancho/2,
                                      disponible.center().y()-alto/2, ancho, alto)
                    p.drawPixmap(destino, marca, QRectF(marca.rect()))
            p.setFont(control.font())
            p.setPen(QColor("#f6e8cd"))
            p.drawText(QRectF(38, 0, control.width()-40, control.height()),
                       Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
                       | Qt.TextFlag.TextWordWrap, control.text())
        else:
            y = control.height()/2
            ancho = max(1, control.width()-24)
            inverso = control.invertedAppearance() ^ (control.layoutDirection() == Qt.LayoutDirection.RightToLeft)
            posicion = QStyle.sliderPositionFromValue(control.minimum(), control.maximum(), control.value(), ancho, inverso)
            p.setPen(QPen(QColor("#0c1b29"), 9, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(12, int(y), control.width()-12, int(y))
            p.setPen(QPen(QColor("#b38b5e"), 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(12, int(y), control.width()-12, int(y))
            p.setPen(QPen(QColor("#5d9999"), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(12, int(y), 12+posicion, int(y))
            medallon = pixmap_arte("ui/nodo.png")
            if not medallon.isNull():
                p.drawPixmap(QRectF(posicion, y-12, 24, 24), medallon, QRectF(medallon.rect()))
        if control.hasFocus():
            p.setPen(QPen(QColor("#f6e8cd"), 1, Qt.PenStyle.DashLine))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(QRectF(control.rect()).adjusted(1, 1, -1, -1), 5, 5)
        p.end()
        return True


class BotonIlustrado(QPushButton):
    def __init__(self, texto="", parent=None, recurso="ui/boton.png"):
        super().__init__(texto, parent)
        self.setProperty("recursoArte", recurso)
        self.setMinimumHeight(48)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def sizeHint(self):
        tam = super().sizeHint()
        texto = self.fontMetrics().size(Qt.TextFlag.TextShowMnemonic, self.text())
        extra = self.iconSize().width() + 9 if not self.icon().isNull() else 0
        return QSize(max(tam.width(), texto.width() + 42 + extra),
                     max(tam.height(), texto.height() + 22, 48))

    def paintEvent(self, event):
        _pintar_boton(self)


def decorar_botones(parent):
    """Aplica arte a botones existentes conservando sus señales y atributos."""
    botones = parent.findChildren(QPushButton)
    botones.extend(parent.findChildren(QToolButton))
    if isinstance(parent, (QPushButton, QToolButton)):
        botones.append(parent)
    for boton in botones:
        if isinstance(boton, BotonIlustrado) or hasattr(boton, "_piel_ilustrada"):
            continue
        boton._piel_ilustrada = _PielBoton(boton)
        boton.installEventFilter(boton._piel_ilustrada)
        boton.setCursor(Qt.CursorShape.PointingHandCursor)
        boton.update()


def aplicar_estilo(widget):
    cargar_tipografias()
    widget.setStyleSheet(ESTILO_ARTE)
    decorar_botones(widget)
    for control in widget.findChildren(QCheckBox) + widget.findChildren(QSlider):
        if not hasattr(control, "_piel_control"):
            control._piel_control = _PielControl(control)
            control.installEventFilter(control._piel_control)
