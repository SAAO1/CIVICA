"""Pantallas reales de Civitas dentro de los teléfonos de los cortos.

Reutiliza el mismo componente del juego; no cambia las pinturas originales.
Las superficies del dispositivo conservan reflejos y bordes, sin un lienzo
azul vacío ni un dibujo que sustituya la publicación que se está leyendo.
"""
from PyQt6.QtCore import QRectF, QPointF, Qt
from PyQt6.QtGui import QColor, QImage, QLinearGradient, QPainter, QPainterPath, QPen

_FEEDS = {}


def imagen_feed(identificador=50):
    if identificador not in _FEEDS:
        from juego.partida import Juego
        from publicaciones_ui import TarjetaPublicacion
        juego = Juego(42, eventos=False, campana="extendida")
        publicacion = next((p for p in juego.publicaciones_planificadas if p.id == identificador),
                           juego.publicaciones_planificadas[0])
        tarjeta = TarjetaPublicacion(telefono=True)
        tarjeta.resize(420, 810)
        tarjeta.mostrar(publicacion, juego.grafo)
        if publicacion.emisor_id == "valeria":
            tarjeta.autor = "Valeria Cruz"
        tarjeta.ensurePolished()
        imagen = QImage(420, 810, QImage.Format.Format_ARGB32_Premultiplied)
        imagen.fill(QColor("#f7fafb"))
        pintor = QPainter(imagen)
        tarjeta.render(pintor)
        pintor.end()
        tarjeta.deleteLater()
        _FEEDS[identificador] = imagen
    return _FEEDS[identificador]


def pintar_pantalla(p, rect, identificador=50, reflejo=True):
    rect = QRectF(rect)
    p.save()
    mascara = QPainterPath()
    mascara.addRoundedRect(rect, rect.width()*.055, rect.width()*.055)
    p.setClipPath(mascara, Qt.ClipOperation.IntersectClip)
    p.drawImage(rect, imagen_feed(identificador))
    if reflejo:
        brillo = QLinearGradient(rect.topLeft(), rect.bottomRight())
        brillo.setColorAt(0, QColor(255, 255, 255, 21))
        brillo.setColorAt(.46, QColor(255, 255, 255, 0))
        brillo.setColorAt(1, QColor(255, 255, 255, 14))
        p.fillRect(rect, brillo)
    p.restore()


def pintar_telefono(p, x, y, ancho=260, alto=470, identificador=50):
    p.save()
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(8, 10, 13, 68))
    p.drawRoundedRect(QRectF(x+6, y+9, ancho, alto), ancho*.09, ancho*.09)
    borde = QLinearGradient(x, y, x+ancho, y+alto)
    borde.setColorAt(0, QColor("#c4c1b9"))
    borde.setColorAt(.08, QColor("#343333"))
    borde.setColorAt(.88, QColor("#16191c"))
    borde.setColorAt(1, QColor("#9c9a92"))
    p.setBrush(borde)
    p.setPen(QPen(QColor("#0b0b0d"), 2))
    p.drawRoundedRect(QRectF(x, y, ancho, alto), ancho*.09, ancho*.09)
    margen = ancho*.045
    pantalla = QRectF(x+margen, y+alto*.025, ancho-2*margen, alto*.95)
    pintar_pantalla(p, pantalla, identificador)
    p.setBrush(QColor("#111113")); p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(QRectF(x+ancho*.35, y+alto*.018, ancho*.30, alto*.018), 4, 4)
    p.setPen(QPen(QColor(34, 37, 39, 210), 3))
    p.drawLine(QPointF(x+ancho*.36, y+alto*.959), QPointF(x+ancho*.64, y+alto*.959))
    p.restore()


def pintar_en_foto(p, imagen, recorte, identificador=50):
    """Sigue el recorte de cámara del teléfono pintado de 1672×941."""
    origen = QRectF(imagen.width()*.577, imagen.height()*.174,
                    imagen.width()*.155, imagen.height()*.570)
    destino = QRectF((origen.x()-recorte.x())*1280/recorte.width(),
                     (origen.y()-recorte.y())*720/recorte.height(),
                     origen.width()*1280/recorte.width(), origen.height()*720/recorte.height())
    pintar_pantalla(p, destino, identificador)
