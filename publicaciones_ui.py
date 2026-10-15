"""Publicación reutilizable de Civitas para el teléfono y las decisiones."""
from PyQt6.QtCore import Qt, QRectF, QSize
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen, QFont, QFontMetricsF
from PyQt6.QtWidgets import QWidget, QSizePolicy

from arte import avatar_arte, miniatura_publicacion, FUENTE_UI


class TarjetaPublicacion(QWidget):
    def __init__(self, parent=None, telefono=False):
        super().__init__(parent)
        self.telefono = telefono
        self.publicacion = None
        self.autor = "Ana"
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(150 if telefono else 180, 180 if telefono else 260)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def sizeHint(self):
        return QSize(260, 380) if self.telefono else QSize(580, 330)

    def mostrar(self, publicacion, grafo=None):
        self.publicacion = publicacion
        if publicacion:
            nodo = grafo.nodos.get(publicacion.emisor_id) if grafo else None
            self.autor = nodo.nombre if nodo else "Ana"
            self.setAccessibleName(f"Civitas. Publicación de {self.autor}. {publicacion.texto}. "
                                   f"{publicacion.compartidos} compartidos, {publicacion.verificaciones} verificaciones.")
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        w, h = self.width(), self.height()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#f7fafb"))
        p.drawRoundedRect(QRectF(0, 0, w, h), 16, 16)
        margen = 11 if self.telefono else 22
        fuente = 12 if self.telefono else 17

        def texto(cadena, caja, tam=fuente, color="#1c3446", negrita=False, flags=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter):
            f = QFont(FUENTE_UI)
            f.setPixelSize(tam)
            f.setBold(negrita)
            p.setFont(f)
            p.setPen(QColor(color))
            p.drawText(QRectF(caja), flags, cadena)

        # Cabecera de aplicación y navegación del feed.
        marca_h = 29 if self.telefono else 42
        texto("civitas", QRectF(margen, 4, w-2*margen, marca_h), fuente+7, "#176b76", True)
        texto("•••", QRectF(w-48, 4, 30, marca_h), fuente+2, "#586f7e")
        tabs_y = marca_h + 3
        if not self.telefono or h >= 280:
            texto("Para ti", QRectF(margen, tabs_y, w/2-margen, 25), fuente, "#176b76", True)
            texto("Siguiendo", QRectF(w/2+5, tabs_y, w/2-margen, 25), fuente, "#71818a")
            p.fillRect(margen, tabs_y+26, max(38, int(w*.21)), 3, QColor("#238e9b"))
            p.fillRect(0, tabs_y+30, w, 1, QColor("#dae4e8"))
            y = tabs_y + 40
        else:
            p.fillRect(margen, tabs_y+5, w-margen*2, 1, QColor("#dae4e8"))
            y = tabs_y+12
        avatar_tam = 26 if self.telefono else 38
        imagen = avatar_arte(self.publicacion.emisor_id if self.publicacion else "ana")
        circ = QRectF(margen, y, avatar_tam, avatar_tam)
        p.save()
        clip = QPainterPath()
        clip.addEllipse(circ)
        p.setClipPath(clip)
        p.fillRect(circ, QColor("#c9e2e4"))
        if not imagen.isNull():
            lado = min(imagen.width(), imagen.height())
            p.drawPixmap(circ, imagen, QRectF((imagen.width()-lado)/2, (imagen.height()-lado)/2, lado, lado))
        p.restore()
        x_nombre = margen + avatar_tam + 9
        texto(self.autor, QRectF(x_nombre, y-3, w-x_nombre-margen, 22), fuente, negrita=True)
        texto("Ahora · Público", QRectF(x_nombre, y+17, w-x_nombre-margen, 18), max(10, fuente-3), "#667e8a")
        y += avatar_tam + (7 if self.telefono else 10)
        contenido = self.publicacion.texto if self.publicacion else "Una nueva publicación llega a Ciudad Nova."
        f = QFont(FUENTE_UI)
        f.setPixelSize(fuente+1)
        fm = QFontMetricsF(f)
        ancho_texto = w-margen*2
        alto_texto = fm.boundingRect(QRectF(0, 0, ancho_texto, 1000), Qt.TextFlag.TextWordWrap, contenido).height()+9
        texto(contenido, QRectF(margen, y, ancho_texto, alto_texto), fuente+1,
              flags=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap)
        y += alto_texto+5
        pie_h = 77 if self.telefono else 65
        foto_h = max(1, h-y-pie_h)
        foto = miniatura_publicacion(self.publicacion.id if self.publicacion else 50)
        foto_rect = QRectF(margen, y, ancho_texto, foto_h)
        p.save()
        clip = QPainterPath()
        clip.addRoundedRect(foto_rect, 9, 9)
        p.setClipPath(clip)
        if not foto.isNull():
            factor = max(ancho_texto/foto.width(), foto_h/foto.height())
            sw, sh = ancho_texto/factor, foto_h/factor
            p.drawPixmap(foto_rect, foto, QRectF((foto.width()-sw)/2, (foto.height()-sh)/2, sw, sh))
        else:
            p.fillRect(foto_rect, QColor("#d8e7eb"))
        p.restore()
        y += foto_h + 5
        compartidos = self.publicacion.compartidos if self.publicacion else 0
        verificaciones = self.publicacion.verificaciones if self.publicacion else 0
        texto(f"{compartidos} compartidos · {verificaciones} verificaciones", QRectF(margen, y, ancho_texto, 20),
              max(10, fuente-3), "#607b88")
        y += 24
        p.fillRect(margen, int(y), int(ancho_texto), 1, QColor("#dce5e8"))
        # Iconos dibujados en Qt: no dependen de emoji ni de una fuente de símbolos.
        for i, (rotulo, simbolo) in enumerate((("Me gusta", "corazon"), ("Comentar", "comentario"), ("Compartir", "compartir"))):
            columna = margen + i*ancho_texto/3
            x = columna + ancho_texto/6 - 8 if self.telefono else columna
            iy = y+12
            p.setPen(QPen(QColor("#597682"), 1.4))
            p.setBrush(Qt.BrushStyle.NoBrush)
            if simbolo == "comentario":
                p.drawRoundedRect(QRectF(x+2, iy, 12, 10), 3, 3)
                p.drawLine(int(x+4), int(iy+10), int(x+2), int(iy+13))
            elif simbolo == "compartir":
                p.drawLine(int(x+2), int(iy+9), int(x+13), int(iy+2))
                p.drawLine(int(x+7), int(iy+1), int(x+13), int(iy+2))
                p.drawLine(int(x+13), int(iy+2), int(x+12), int(iy+8))
            else:
                corazon = QPainterPath()
                corazon.moveTo(x+8, iy+12)
                corazon.cubicTo(x-9, iy+1, x+5, iy-5, x+8, iy+1)
                corazon.cubicTo(x+14, iy-5, x+23, iy+1, x+8, iy+12)
                p.drawPath(corazon)
            if self.telefono:
                texto(rotulo, QRectF(columna, iy+13, ancho_texto/3, 16), 9, "#426371",
                      flags=Qt.AlignmentFlag.AlignCenter)
            else:
                texto(rotulo, QRectF(x+21, iy-4, ancho_texto/3-21, 22), max(9, fuente-4), "#426371")
        p.end()
