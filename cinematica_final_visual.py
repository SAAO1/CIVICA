"""Mesa de animación de las cuatro investiduras y del recuento pendiente.

El personaje conserva el retrato original. Cámara, acta, firma, cintas,
destellos suaves y confeti se componen por separado y se exportan a H.264.
"""
from __future__ import annotations

import math
from pathlib import Path

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QFontDatabase, QImage, QLinearGradient, QPainter, QPainterPath, QPen

RAIZ = Path(__file__).resolve().parent
CARPETA = RAIZ / "assets/expansion/finales"
DURACION = 12.0
FPS = 24
CLIPS = {
    "juan": dict(nombre="Juan Torres", propuesta="Educación y espacios seguros", color="#d6ba79"),
    "adrian": dict(nombre="Adrián Morales", propuesta="Bibliotecas y cultura", color="#83c3c6"),
    "laura": dict(nombre="Laura Ríos", propuesta="Parques y convivencia", color="#9ac887"),
    "camila": dict(nombre="Camila Vega", propuesta="Participación y bienestar digital", color="#efb48c"),
    "recuento": dict(nombre="Cada voto cuenta", propuesta="Recuento público pendiente", color="#9fc7dc"),
}


def _suave(x):
    x = max(0., min(1., x))
    return x*x*(3-2*x)


def _azar(n):
    a = math.sin(n*137.13+8.13)*43758.5453
    return a-math.floor(a)


class RenderizadorFinal:
    def __init__(self, clave):
        if clave not in CLIPS:
            raise ValueError(f"Desenlace desconocido: {clave}")
        self.clave = clave
        self.ficha = CLIPS[clave]
        self.fondo = QImage(str(RAIZ / "assets/expansion/fondos/plaza_noche.png"))
        self.retrato = QImage(str(RAIZ / f"assets/expansion/candidatos/{clave}_electo.png")) if clave != "recuento" else QImage()
        QFontDatabase.addApplicationFont(str(RAIZ / "assets/fuentes/AtkinsonHyperlegible-Regular.ttf"))
        QFontDatabase.addApplicationFont(str(RAIZ / "assets/fuentes/AtkinsonHyperlegible-Bold.ttf"))

    @property
    def fuentes(self):
        rutas = [RAIZ / "assets/expansion/fondos/plaza_noche.png"]
        if self.clave != "recuento":
            rutas.append(RAIZ / f"assets/expansion/candidatos/{self.clave}_electo.png")
        return rutas

    @staticmethod
    def _texto(p, rect, texto, tamano, color="#f8e7c8", negrita=False):
        f = QFont("Atkinson Hyperlegible")
        f.setPixelSize(tamano)
        f.setBold(negrita)
        p.setFont(f)
        p.setPen(QColor(color))
        p.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap, texto)

    def _palacio(self, p, t):
        zoom = 1.05 + .018*t
        origen = QRectF((self.fondo.width()-self.fondo.width()/zoom)*(.5+.05*math.sin(t*.4)),
                        self.fondo.height()*.07, self.fondo.width()/zoom, self.fondo.width()/zoom*720/1280)
        p.drawImage(QRectF(0, 0, 1280, 720), self.fondo, origen)
        grad = QLinearGradient(0, 0, 1100, 0)
        grad.setColorAt(0, QColor(6, 19, 31, 245))
        grad.setColorAt(.5, QColor(6, 19, 31, 205))
        grad.setColorAt(1, QColor(6, 19, 31, 50))
        p.fillRect(QRectF(0, 0, 1280, 720), grad)

    def _persona(self, p, t):
        entrada = _suave((t-.7)/1.8)
        p.save()
        p.setOpacity(entrada)
        p.translate(34*(1-entrada), 0)
        # El retrato ocupa todo el alto, con rostro y manos intactos. Un leve
        # acercamiento cambia el plano sin fingir animación corporal.
        zoom = 1 + .006*t
        src = QRectF(self.retrato.width()*(1-1/zoom)*.5,
                     self.retrato.height()*(1-1/zoom)*.20,
                     self.retrato.width()/zoom, self.retrato.height()/zoom)
        destino = QRectF(735, -3, 552, 828)
        p.drawImage(destino, self.retrato, src)
        sombreado = QLinearGradient(700, 0, 860, 0)
        sombreado.setColorAt(0, QColor(8, 23, 34, 255))
        sombreado.setColorAt(1, QColor(8, 23, 34, 0))
        p.fillRect(QRectF(700, 0, 180, 720), sombreado)
        p.restore()

    def _acta(self, p, t):
        entrada = _suave((t-3.8)/1.1)
        p.save()
        p.setOpacity(entrada)
        p.translate(0, 22*(1-entrada))
        p.setPen(QPen(QColor("#bba777"), 1))
        p.setBrush(QColor(237, 222, 183, 245))
        p.drawRoundedRect(QRectF(72, 382, 568, 240), 9, 9)
        self._texto(p, QRectF(100, 397, 510, 33), "ACTA DE POSESIÓN · CIUDAD NOVA", 20, "#655237", True)
        self._texto(p, QRectF(100, 438, 510, 42), self.ficha["nombre"], 29, "#233f4c", True)
        self._texto(p, QRectF(100, 480, 510, 34), "Al servicio de una ciudad con voces distintas", 19, "#655237")
        p.setPen(QPen(QColor("#938169"), 1))
        p.drawLine(QPointF(108, 575), QPointF(600, 575))
        # Firma original ilustrativa: trazo que se descubre progresivamente.
        progreso = _suave((t-5.2)/2.5)
        puntos = [QPointF(120+i*3.8, 550+math.sin(i*.43)*9+math.sin(i*.14)*13-i*.10) for i in range(116)]
        cantidad = max(0, min(len(puntos), round(progreso*len(puntos))))
        p.setPen(QPen(QColor("#244c5f"), 2.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for a, b in zip(puntos[:cantidad], puntos[1:cantidad]):
            p.drawLine(a, b)
        self._texto(p, QRectF(102, 582, 510, 24), "Ceremonia ficticia · Palacio Municipal", 16, "#766449")
        p.restore()

    def _confeti(self, p, t):
        for i in range(95):
            fase = (t*(.045+.035*_azar(i+2)) + _azar(i+83)) % 1
            x = _azar(i+300)*1320-20 + math.sin(t*.8+i)*21
            y = fase*820-60
            p.save()
            p.translate(x, y)
            p.rotate(i*31+t*(18+28*_azar(i+401)))
            col = QColor(("#e2c88e", self.ficha["color"], "#f9e6bb")[i%3])
            col.setAlpha(140 if x < 680 else 205)
            p.setBrush(col)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRect(QRectF(-3, -2, 5+2*math.sin(t+i), 3))
            p.restore()

    def _recuento(self, p, t):
        for i in range(4):
            x = 105+i*280
            p.setBrush(QColor(24, 57, 72, 220))
            p.setPen(QPen(QColor("#93b7c8"), 2))
            p.drawRoundedRect(QRectF(x, 335, 235, 150), 12, 12)
            p.drawLine(QPointF(x+70, 358), QPointF(x+165, 358))
            fase = ((t+i*.7)*.32)%1
            p.save()
            p.setOpacity(1-abs(fase-.5)*.8)
            p.translate(x+110, 270+fase*70)
            p.rotate(-12+fase*18)
            p.setBrush(QColor("#eee1c5"))
            p.drawRect(QRectF(-28, -25, 56, 43))
            p.restore()
        self._texto(p, QRectF(100, 505, 1090, 90), "Ninguna candidatura ha sido proclamada.\nLas actas se revisarán en un recuento público.", 29, "#d7e5e6")

    def capturar_fotograma(self, segundos, tamano=(1280, 720)):
        w, h = map(int, tamano)
        if min(w, h) <= 0:
            raise ValueError("El fotograma necesita dimensiones positivas")
        t = max(0., min(DURACION, float(segundos)))
        img = QImage(w, h, QImage.Format.Format_ARGB32)
        img.fill(QColor("#0a1d2e"))
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.scale(w/1280, h/720)
        self._palacio(p, t)
        if self.clave != "recuento":
            self._persona(p, t)
        p.save()
        p.setOpacity(_suave(t/1.2))
        self._texto(p, QRectF(72, 67, 850, 37), "CIUDAD NOVA · PALACIO MUNICIPAL" if self.clave != "recuento" else "CIUDAD NOVA · RECUENTO ELECTORAL", 22, self.ficha["color"], True)
        ancho = 665 if self.clave != "recuento" else 1100
        self._texto(p, QRectF(72, 120, ancho, 142), self.ficha["nombre"], 62, negrita=True)
        self._texto(p, QRectF(74, 272, ancho, 68), "ALCALDÍA ELECTA\n"+self.ficha["propuesta"] if self.clave != "recuento" else self.ficha["propuesta"], 24, self.ficha["color"])
        p.restore()
        if self.clave == "recuento":
            self._recuento(p, t)
        else:
            self._acta(p, t)
            self._confeti(p, t)
        # Cintas de luz recorren el borde, sin fogonazos ni blancos de pantalla.
        p.setPen(QPen(QColor(self.ficha["color"]), 2))
        longitud = 260
        x = (t*120)%1540-longitud
        p.drawLine(QPointF(x, 25), QPointF(x+longitud, 25))
        p.fillRect(QRectF(0, 684, 1280, 36), QColor(7, 21, 32, 210))
        self._texto(p, QRectF(72, 686, 1136, 30), "Un nuevo mandato. La conversación de la ciudad continúa." if self.clave != "recuento" else "El empate conserva a todas las candidaturas en igualdad de condiciones.", 18, "#dbd7c8")
        p.end()
        return img
