"""Puesta en escena local: doce planos humanos de los actos IV–VII.

Reutiliza las cuatro pinturas originales y los sprites transparentes de la
campaña. Anima cámara, cambios de boca/parpadeo, luz y objetos del rodaje.
No sintetiza movimiento corporal ni sustituye una conversación por diagramas.
"""
from __future__ import annotations

import math
from pathlib import Path

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QImage, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient

from juego.cinematica_personajes_extendida import CINEMATICAS_PERSONAJES_EXTENDIDAS


RAIZ = Path(__file__).resolve().parent
CARPETA = RAIZ / "assets/expansion/siete_actos/personajes_video"
FPS, DURACION = 24, 9.0
_ARTE = RAIZ / "assets/expansion/siete_actos"


def _suave(x):
    x = min(1.0, max(0.0, x))
    return x*x*(3-2*x)


class RenderizadorPersonajeExtendido:
    def __init__(self, clave):
        self.clave = clave
        self.entrada = CINEMATICAS_PERSONAJES_EXTENDIDAS[clave]
        self.identificador = self.entrada["publicacion"]
        self.escenario = self.entrada["escenario"]
        self.personaje = self.entrada["personaje"]
        self.accion = self.entrada["accion"]
        self.fuentes = [_ARTE / carpeta / f"{self.escenario}.jpg"
                        for carpeta in ("fondos", "ilustraciones")]
        self.fondo, self.cg = [self._leer(r) for r in self.fuentes]
        self.poses = {}
        if self.personaje != "ciudadano":
            for pose in ("neutral", "hablando", "parpadeo", "preocupado", "decidido"):
                ruta = _ARTE / "personajes" / f"{self.personaje}_{pose}.png"
                self.fuentes.append(ruta)
                self.poses[pose] = self._leer(ruta)
            # Hablar y parpadear son parches faciales con el mismo lienzo que
            # neutral. Se componen sobre éste; usarlos solos borraría el cuerpo.
            for pose in ("hablando", "parpadeo"):
                imagen = self.poses["neutral"].copy()
                p = QPainter(imagen)
                p.drawImage(0, 0, self.poses[pose])
                p.end()
                self.poses[pose] = imagen

    @staticmethod
    def _leer(ruta):
        imagen = QImage(str(ruta))
        if imagen.isNull():
            raise ValueError(f"Falta arte: {ruta}")
        return imagen

    @staticmethod
    def _imagen(p, imagen, zoom=1.0, foco=(.5, .5)):
        escala = max(1280/imagen.width(), 720/imagen.height()) * zoom
        w, h = imagen.width()*escala, imagen.height()*escala
        x = min(0, max(1280-w, 640-foco[0]*w))
        y = min(0, max(720-h, 360-foco[1]*h))
        p.drawImage(QRectF(x, y, w, h), imagen)

    def _plano_conjunto(self, p, t):
        if self.accion == "familia":
            foco, zoom = (.26, .57), 1.12 + .016*t
        elif self.accion == "abuelo":
            foco, zoom = (.48, .47), 1.045 + .016*t
        elif self.accion == "llamada":
            foco, zoom = (.27, .42), 1.07 + .017*t
        elif self.escenario == "estudio":
            foco, zoom = (.52, .44), 1.035 + .004*t
        elif self.escenario == "debate":
            foco, zoom = (.5, .41), 1.025 + .004*t
        else:
            foco, zoom = (.5, .46), 1.025 + .005*t
        self._imagen(p, self.cg, zoom, (foco[0]+.004*math.sin(t*.24), foco[1]))

    def _rostro(self, t):
        if t % 3.7 > 3.52:
            return self.poses["parpadeo"]
        # Dos estados de boca con pausas: el audio del juego sigue siendo la
        # grabación exacta; estas poses acompañan la voz sin fingir fonemas.
        hablando = (math.sin(t*8.1)+.43*math.sin(t*17.3) > -.08
                     and not 4.45 < t < 4.82)
        return self.poses["hablando" if hablando else "neutral"]

    def _actor(self, p, t):
        imagen = self._rostro(t)
        derecha = self.personaje in ("influencer", "laura")
        # Se conserva la orientación pintada: sus ojos quedan hacia el objeto
        # o el interlocutor, dentro del encuadre de esta conversación.
        alto = 1460 if self.accion == "recorte" else 1420 if self.personaje == "influencer" else 1370
        ancho = imagen.width()*alto/imagen.height()
        x = 580 if derecha else -35
        y = 25 + math.sin(t*1.7)*1.4
        p.drawImage(QRectF(x, y, ancho, alto), imagen)

    def _telefono_camara(self, p, t):
        # Cámara física en primer término: la pantalla contiene el mismo rostro
        # y lugar, nunca una tarjeta azul ni una noticia ajena a este caso.
        x, y, w, h = 218, 231, 144, 250
        p.setPen(QPen(QColor("#292019"), 7))
        p.drawLine(QPointF(x+w/2, y+h), QPointF(x+w/2, 692))
        p.drawLine(QPointF(x+w/2, 635), QPointF(184, 719))
        p.drawLine(QPointF(x+w/2, 635), QPointF(405, 719))
        aro = QColor(255, 231, 178, round(115+105*_suave(t/1.2)))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(255, 216, 145, 35), 29))
        p.drawEllipse(QPointF(x+w/2, y+h/2), 150, 164)
        p.setPen(QPen(aro, 13))
        p.drawEllipse(QPointF(x+w/2, y+h/2), 150, 164)
        p.setPen(QPen(QColor("#5b5145"), 2)); p.setBrush(QColor("#151414"))
        p.drawRoundedRect(QRectF(x, y, w, h), 17, 17)
        p.save(); p.setClipRect(QRectF(x+8, y+13, w-16, h-27))
        p.drawImage(QRectF(x+8, y+13, w-16, h-27), self.fondo,
                    QRectF(self.fondo.width()*.33, 0, self.fondo.width()*.4, self.fondo.height()))
        actor = self._rostro(t)
        p.drawImage(QRectF(x-10, y+20, 180, 360), actor)
        p.restore()
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor("#0f1010"))
        p.drawRoundedRect(QRectF(x+43, y+5, 58, 9), 4, 4)
        if t > .65:
            p.setBrush(QColor("#e65f49")); p.drawEllipse(QPointF(x+22, y+30), 4, 4)
        # El botón adquiere presencia al encenderse la toma, sin flashes.
        p.setPen(QPen(QColor("#f3e4c9"), 2)); p.setBrush(QColor("#b64135"))
        p.drawEllipse(QPointF(x+w/2, y+h-23), 9, 9)

    @staticmethod
    def _microfono(p, x, y):
        p.setPen(QPen(QColor("#2b2825"), 7))
        p.drawLine(QPointF(x+85, y+198), QPointF(x+85, y+60))
        p.drawLine(QPointF(x+85, y+60), QPointF(x+8, y))
        p.setPen(QPen(QColor("#847a68"), 2)); p.setBrush(QColor("#29282a"))
        p.drawRoundedRect(QRectF(x-25, y-14, 60, 31), 12, 12)

    def _objetos(self, p, t):
        if self.escenario == "estudio" and self.personaje == "influencer":
            self._telefono_camara(p, t)
        elif self.escenario == "debate":
            self._microfono(p, 493, 454)
        elif self.escenario == "redaccion":
            # Grabadora de mesa y carpeta en el lugar de la escucha; el objeto
            # mantiene el archivo íntegro sin dibujar una pantalla explicativa.
            mesa = QPainterPath(QPointF(720, 611))
            mesa.lineTo(1280, 513); mesa.lineTo(1280, 720); mesa.lineTo(668, 720); mesa.closeSubpath()
            madera = QLinearGradient(800, 540, 890, 720)
            madera.setColorAt(0, QColor("#8b5c35")); madera.setColorAt(1, QColor("#4b3020"))
            p.setPen(QPen(QColor("#38261a"), 3)); p.setBrush(madera); p.drawPath(mesa)
            p.setPen(QPen(QColor(204, 151, 88, 65), 1))
            for i in range(5): p.drawLine(750, 625+i*19, 1280, 536+i*28)
            p.setPen(QPen(QColor("#7c593c"), 2)); p.setBrush(QColor("#c7a779"))
            p.drawRoundedRect(QRectF(800, 571, 353, 117), 5, 5)
            p.setBrush(QColor("#ead8b6")); p.drawRect(QRectF(817, 569, 318, 91))
            p.setPen(QPen(QColor("#b29874"), 1))
            for i in range(5): p.drawLine(840, 588+i*11, 1095-i*15, 588+i*11)
            p.setPen(QPen(QColor("#73675b"), 2)); p.setBrush(QColor("#353331"))
            p.drawRoundedRect(QRectF(914, 516, 205, 73), 9, 9)
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor("#1a1a19"))
            p.drawEllipse(QPointF(957, 552), 23, 23)
            p.drawEllipse(QPointF(1076, 552), 23, 23)
            p.setPen(QPen(QColor("#81796c"), 1))
            for i in range(6): p.drawLine(985, 537+i*6, 1040, 537+i*6)
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor("#c38046"))
            p.drawEllipse(QPointF(1055, 529), 2.4, 2.4)
        elif self.accion == "mapa":
            # Se conserva el mapa pintado del punto de información a la izquierda.
            self._microfono(p, 468, 518)

    def _plano_hablante(self, p, t):
        p.save()
        zoom = 1.0+.0028*t
        p.translate(640, 360); p.scale(zoom, zoom); p.translate(-640, -360)
        self._imagen(p, self.fondo, 1.045+.0018*t, (.5, .5))
        # Luz cálida continua del lugar, sin fundidos a una pantalla vacía.
        luz = QRadialGradient(QPointF(250, 190), 800)
        luz.setColorAt(0, QColor(255, 202, 126, 17))
        luz.setColorAt(1, QColor(255, 202, 126, 0))
        p.fillRect(QRectF(0, 0, 1280, 720), luz)
        self._actor(p, t)
        self._objetos(p, t)
        p.restore()

    def _ambiente(self, p, t):
        if self.escenario == "redaccion":
            # Lluvia sólo en el ventanal del lugar. Las caras y los documentos
            # no reciben trazos de lluvia dentro de la habitación.
            p.save(); p.setClipRect(QRectF(601, 0, 490, 205))
            p.setPen(QPen(QColor(191, 211, 219, 40), 1))
            for i in range(34):
                x = 600+(i*73)%490; y = (i*39+t*113)%220
                p.drawLine(QPointF(x, y), QPointF(x-2, y+12))
            p.restore()
        else:
            p.setPen(Qt.PenStyle.NoPen)
            for i in range(13):
                x = (i*107+t*(2+i%3))%1280
                y = (i*59-t*2.7)%630
                p.setBrush(QColor(255, 231, 180, 25))
                p.drawEllipse(QPointF(x, y), 1.2, 1.2)

    def capturar_fotograma(self, segundos=0, tamano=(1280, 720)):
        t = max(0, min(DURACION, float(segundos)))
        ancho, alto = tamano
        if ancho <= 0 or alto <= 0:
            raise ValueError("El fotograma necesita dimensiones positivas")
        imagen = QImage(ancho, alto, QImage.Format.Format_ARGB32)
        imagen.fill(QColor("#30271f"))
        p = QPainter(imagen)
        p.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        p.scale(ancho/1280, alto/720)
        self._plano_conjunto(p, t)
        if self.poses:
            # Dos encuadres de la misma escena con disolución corta: primero
            # interlocutores/contexto y después el personaje que tiene la voz.
            opacidad = _suave((t-.55)/.65) * (1-_suave((t-8.05)/.7))
            if opacidad:
                p.save(); p.setOpacity(opacidad)
                self._plano_hablante(p, t)
                p.restore()
        self._ambiente(p, t)
        sombra = QLinearGradient(0, 565, 0, 720)
        sombra.setColorAt(0, QColor(25, 18, 14, 0))
        sombra.setColorAt(1, QColor(25, 18, 14, 65))
        p.fillRect(QRectF(0, 565, 1280, 155), sombra)
        p.end()
        return imagen
