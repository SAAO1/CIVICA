"""Ocho insertos dibujados por caso: pintura, cámara y objetos en movimiento.

No sintetiza movimiento corporal. Los planos de detalle se dibujan en capas
para conservar el objeto exacto que describe cada primera frase del narrador.
"""
from __future__ import annotations

import math
from pathlib import Path

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFontDatabase, QImage, QLinearGradient, QPainter, QPen

RAIZ = Path(__file__).resolve().parent
CARPETA = RAIZ / "assets/expansion/siete_actos/videos"
FPS, DURACION = 24, 10.0
ESCENARIOS = {90:"estudio",40:"estudio",100:"debate",10:"debate",110:"redaccion",25:"redaccion",120:"urnas",35:"urnas"}
_FUENTES_CARGADAS=False


def _suave(x):
    x = max(0.0, min(1.0, x))
    return x*x*(3-2*x)


class RenderizadorExtension:
    def __init__(self, clave):
        global _FUENTES_CARGADAS
        if not _FUENTES_CARGADAS:
            for archivo in ('AtkinsonHyperlegible-Regular.ttf','AtkinsonHyperlegible-Bold.ttf'):
                if QFontDatabase.addApplicationFont(str(RAIZ/'assets/fuentes'/archivo))<0:
                    raise ValueError(f'No se pudo cargar la tipografía: {archivo}')
            _FUENTES_CARGADAS=True
        self.clave = clave
        self.identificador = int(clave.rsplit("_",1)[1])
        self.escenario = ESCENARIOS[self.identificador]
        self.fuentes = [RAIZ / f"assets/expansion/siete_actos/{carpeta}/{self.escenario}.jpg" for carpeta in ("fondos","ilustraciones")]
        self.fondo, self.cg = (QImage(str(r)) for r in self.fuentes)
        if self.fondo.isNull() or self.cg.isNull():
            raise ValueError(f"Falta arte de {clave}")

    @staticmethod
    def _imagen(p, imagen, zoom=1.0, dx=0, dy=0):
        escala = max(1280/imagen.width(),720/imagen.height())*zoom
        w,h=imagen.width()*escala, imagen.height()*escala
        p.drawImage(QRectF((1280-w)/2+dx,(720-h)/2+dy,w,h), imagen)

    def capturar_fotograma(self,segundos=0,tamano=(1280,720)):
        t=max(0,min(DURACION,float(segundos)));ancho,alto=tamano
        imagen=QImage(ancho,alto,QImage.Format.Format_ARGB32);imagen.fill(QColor("#102532"))
        p=QPainter(imagen);p.setRenderHints(QPainter.RenderHint.Antialiasing|QPainter.RenderHint.SmoothPixmapTransform)
        p.scale(ancho/1280,alto/720)
        detalle=2.5<=t<5.7
        telefono = detalle and self.identificador in (90, 40, 110, 35)
        zoom = 1.025+0.012*math.sin(t*.25)
        if detalle and not telefono:
            # Acercamiento al personaje u objeto de la pintura: el debate,
            # el archivo y el abuelo siguen siendo escenas de la historia.
            zoom += .10*math.sin((t-2.5)/3.2*math.pi)
        self._imagen(p,self.fondo if telefono else self.cg,zoom,math.sin(t*.4)*7,math.cos(t*.3)*3)
        if telefono:
            from cine_telefono import pintar_telefono
            p.save()
            p.translate(640,350);p.rotate(-4+math.sin(t*.6))
            pintar_telefono(p,-158,-250,316,536,self.identificador)
            p.restore()
        else:
            # Polvo de estudio / lluvia / hojas separados de las pinturas.
            if self.escenario=="redaccion":
                p.setPen(QPen(QColor(169,205,223,45),1))
                for i in range(48):
                    x=(i*83+23)%1280;y=(i*37+t*135)%590
                    p.drawLine(QPointF(x,y),QPointF(x-4,y+16))
            else:
                p.setPen(Qt.PenStyle.NoPen)
                for i in range(16):
                    x=(i*137+t*(3+i%3))%1280;y=(i*73-t*5)%570
                    p.setBrush(QColor(245,211,148,35));p.drawEllipse(QPointF(x,y),1.6,1.6)
        # Oscurecimiento suave estable para diálogo, sin destellos ni pantallas negras.
        grad=QLinearGradient(0,500,0,720);grad.setColorAt(0,QColor(8,20,30,0));grad.setColorAt(1,QColor(8,20,30,105))
        p.fillRect(QRectF(0,500,1280,220),grad);p.end()
        return imagen
