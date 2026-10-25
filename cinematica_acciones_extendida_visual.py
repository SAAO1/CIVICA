"""Cámara y efectos de las decisiones de los actos IV–VII."""
from pathlib import Path
import math

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainterPath, QPen

from cinematica_acciones_visual import RenderizadorAccion
from cinematica_visual import _color, _rango, _fuente
from juego.cinematica_acciones_extendida import (
    CASOS_ACCIONES_EXTENDIDOS, CINEMATICAS_ACCIONES_EXTENDIDAS)

CARPETA_EXTENDIDA = Path(__file__).resolve().parent / "assets/expansion/siete_actos/acciones"


class RenderizadorAccionExtendida(RenderizadorAccion):
    def __init__(self, clave):
        super().__init__(clave, catalogo=CINEMATICAS_ACCIONES_EXTENDIDAS,
                         casos=CASOS_ACCIONES_EXTENDIDOS)

    def _objeto_caso(self, p, t):
        if self.ficha["publicacion"] in (120, 35):
            # El CG de las urnas acerca los rostros a la parte superior.
            # Conserva sus ojos libres: título bajo el borde y cautela en
            # el margen inferior izquierdo, encima del diálogo del juego.
            a = _rango(t, .25, .7)*(1-_rango(t, 2.95, 3.4))
            self._rotulo(p, self.caso["titulo"], 70, 40, 490, a, tamano=23)
            if 1.9 <= t <= 3.85:
                a = _rango(t, 2.08, 2.4)*(1-_rango(t, 3.45, 3.85))
                self._rotulo(p, self.caso["cautela"], 70, 475, 650, a, tamano=21)
        else:
            super()._objeto_caso(p, t)
        if not 1.9 <= t < 3.85:
            return
        p.save()
        p.setOpacity(_rango(t, 2.05, 2.4)*(1-_rango(t, 3.42, 3.85)))
        identificador = self.ficha["publicacion"]
        p.setPen(QPen(_color("#b4e5df", 220), 2.5))
        p.setBrush(_color("#102e3b", 185))
        if identificador == 90:
            # Un encuadre móvil recuerda qué parte del video quedó fuera;
            # no añade otro parque cerrado ni un veredicto de autenticidad.
            margen = 12+18*(.5+.5*math.sin(t*2))
            p.drawRoundedRect(QRectF(790-margen, 225, 330+2*margen, 185), 12, 12)
            p.setPen(QPen(_color("#edcc97", 240), 3, Qt.PenStyle.DashLine))
            p.drawRect(QRectF(835, 246, 240, 143))
            p.setFont(_fuente(19, True)); p.setPen(QColor("#edddba"))
            p.drawText(QRectF(800, 418, 330, 35), Qt.AlignmentFlag.AlignCenter, "Recorte / archivo íntegro")
        elif identificador == 40:
            for indice, (x, y) in enumerate(((815, 245), (1035, 320), (820, 405))):
                pulso = .5+.5*math.sin(t*3-indice)
                p.drawEllipse(QPointF(x, y), 15+3*pulso, 15+3*pulso)
                if indice:
                    p.drawLine(QPointF(815, 245), QPointF(x, y))
            self._rotulo(p, "Mensaje · Fuentes · Cambios", 755, 460, 430, tamano=20)
        elif identificador == 100:
            # Un croquis del plan, nunca una escuela ya reparada.
            p.drawRoundedRect(QRectF(805, 270, 330, 150), 7, 7)
            tejado = QPainterPath(QPointF(780, 270))
            tejado.lineTo(970, 205); tejado.lineTo(1160, 270)
            p.drawPath(tejado)
            for indice in range(4):
                p.drawRect(QRectF(835+indice*73, 310, 39, 65))
            self._rotulo(p, "Propuesta por etapas", 795, 445, 350, tamano=20)
        elif identificador == 10:
            self._rotulo(p, "Para mí…", 850, 245, 270, tamano=26)
            self._rotulo(p, "Una prioridad en debate", 780, 370, 390, tamano=22)
        elif identificador == 110:
            # Las mismas ondas se desplazan bajo el marco del fragmento.
            # Las barras no imitan una grabación real de una candidatura.
            for indice in range(37):
                x = 795+indice*10
                altura = 18+70*abs(math.sin(indice*.54-t*3.4))
                p.drawLine(QPointF(x, 335-altura/2), QPointF(x, 335+altura/2))
            p.setPen(QPen(_color("#e7c696", 215), 2, Qt.PenStyle.DashLine))
            p.drawRect(QRectF(880, 255, 150, 160))
            self._rotulo(p, "Antes · Fragmento · Después", 750, 445, 435, tamano=20)
        elif identificador == 25:
            for indice in reversed(range(3)):
                self._papel(p, 825+indice*28, 200+indice*25, "Archivo íntegro" if indice == 0 else "Anexo", -5+indice*4)
        elif identificador == 120:
            camino = QPainterPath(QPointF(815, 425))
            camino.cubicTo(845, 270, 1040, 440, 1115, 240)
            p.setPen(QPen(_color("#d6e9bd", 230), 4, Qt.PenStyle.DashLine))
            p.drawPath(camino)
            for indice, (x, y) in enumerate(((815, 425), (950, 350), (1115, 240))):
                p.drawEllipse(QPointF(x, y), 9+2*math.sin(t*3+indice), 9+2*math.sin(t*3+indice))
            self._rotulo(p, "Mapa de accesos", 830, 445, 330, tamano=20)
        elif identificador == 35:
            self._rotulo(p, "Mensaje en Civitas", 790, 240, 380, tamano=22)
            self._rotulo(p, "Puesto de votación", 790, 395, 380, tamano=22)
            p.setFont(_fuente(40, True)); p.setPen(QColor("#f1d398"))
            p.drawText(QRectF(880, 298, 200, 70), Qt.AlignmentFlag.AlignCenter, "≠")
        p.restore()
