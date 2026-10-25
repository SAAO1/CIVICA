"""Mesa de animación de las 66 decisiones audiovisuales de Ciudad Nova.

El montaje sitúa el acto, acerca su objeto y muestra al personaje desempeñando
el método elegido. Las capas animadas corresponden a esa actividad concreta;
no incluyen cifras ficticias ni convierten una acusación en un hecho.
"""
from __future__ import annotations

from collections import OrderedDict
import math
from pathlib import Path

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (QColor, QImage, QLinearGradient, QPainter, QPainterPath,
                         QPen, QRadialGradient)

from cinematica_visual import _color, _fuente, _rango, _suave, _azar
from juego.cinematica_acciones import CASOS_ACCIONES, CINEMATICAS_ACCIONES
from cine_telefono import pintar_telefono

RAIZ = Path(__file__).resolve().parent
CARPETA = RAIZ / "assets/expansion/acciones_video"
DURACION = 9.0
FPS = 24


class RenderizadorAccion:
    def __init__(self, clave, catalogo=None, casos=None):
        catalogo = CINEMATICAS_ACCIONES if catalogo is None else catalogo
        casos = CASOS_ACCIONES if casos is None else casos
        if clave not in catalogo:
            raise ValueError(f"Decisión audiovisual desconocida: {clave}")
        self.clave = clave
        self.ficha = catalogo[clave]
        self.caso = casos[self.ficha["publicacion"]]
        self._imagenes = OrderedDict()

    @property
    def fuentes(self):
        accion = self.ficha["accion"]
        # Una convocatoria sin recepción no representa una multitud reunida.
        arte = "compartir" if self.ficha["variante"] in ("sin_receptores", "alcance_limitado") else accion
        return [RAIZ/self.caso["fondo"],
                RAIZ/self.caso.get("objeto_ruta", f"assets/expansion/cinematica/ilustraciones/{self.caso['objeto']}.jpg"),
                CARPETA/f"ilustraciones/{arte}.jpg"]

    @property
    def planos(self):
        return [dict(inicio=0.0, fin=1.9, tipo="lugar", descripcion=self.caso["titulo"], fuente=str(self.fuentes[0].relative_to(RAIZ)).replace("\\", "/")),
                dict(inicio=1.9, fin=3.7, tipo="objeto", descripcion=self.caso["tema"], fuente=str(self.fuentes[1].relative_to(RAIZ)).replace("\\", "/")),
                dict(inicio=3.7, fin=DURACION, tipo="accion", descripcion=self.ficha["descripcion_lo_que_se_ve"], fuente=str(self.fuentes[2].relative_to(RAIZ)).replace("\\", "/"))]

    def _imagen(self, ruta):
        clave = str(ruta)
        if clave not in self._imagenes:
            imagen = QImage(clave)
            if imagen.isNull():
                raise FileNotFoundError(f"Falta una ilustración de la decisión: {ruta}")
            self._imagenes[clave] = imagen
        self._imagenes.move_to_end(clave)
        while len(self._imagenes) > 3:
            self._imagenes.popitem(last=False)
        return self._imagenes[clave]

    def _recorte(self, indice, tiempo):
        imagen = self._imagen(self.fuentes[indice])
        # Movimiento continuo del plano y puntos de interés propios de cada caso.
        id_caso = self.ficha["publicacion"]
        sesgo = {50: -.03, 30: .02, 70: -.05, 20: .04, 60: -.02, 80: .03}.get(id_caso, .015)
        progreso = min(1, max(0, (tiempo-(0, 1.9, 3.7)[indice])/(1.9, 1.8, 5.3)[indice]))
        zoom = (1.02, 1.12, 1.055)[indice]+(.045 if indice == 2 else .065)*_suave(progreso)
        ancho = min(imagen.width()/zoom, imagen.height()/zoom*16/9)
        alto = ancho*9/16
        cx = .5+sesgo+(progreso-.5)*(.025 if indice != 1 else -.03)
        cy = (.47, .65, .43)[indice]-.012*progreso
        x = min(imagen.width()-ancho, max(0, imagen.width()*cx-ancho/2))
        y = min(imagen.height()-alto, max(0, imagen.height()*cy-alto/2))
        return QRectF(x, y, ancho, alto)

    def _pintura(self, p, indice, tiempo, alfa=1):
        imagen = self._imagen(self.fuentes[indice])
        recorte = self._recorte(indice, tiempo)
        p.save()
        p.setOpacity(alfa)
        p.drawImage(QRectF(0, 0, 1280, 720), imagen, recorte)
        p.restore()

    def _montaje(self, p, t):
        indice = 0 if t < 1.9 else 1 if t < 3.7 else 2
        self._pintura(p, indice, t)
        if indice:
            comienzo = (0, 1.9, 3.7)[indice]
            if t < comienzo+.45:
                self._pintura(p, indice-1, t, 1-_rango(t, comienzo, comienzo+.45))

    def _ambiente(self, p, t):
        ambiente = self.caso["ambiente"]
        noche = ambiente in ("noche", "lluvia")
        p.fillRect(QRectF(0, 0, 1280, 720), _color("#164966" if noche else "#ffcd8b", 23 if noche else 7))
        luz = QRadialGradient(QPointF(1050+20*math.sin(t*.2), 100), 550)
        luz.setColorAt(0, _color("#efc17c", 30 if noche else 22))
        luz.setColorAt(1, QColor(0, 0, 0, 0))
        p.fillRect(QRectF(0, 0, 1280, 720), luz)
        for i in range(18):
            x = (_azar(i, 17)*1320+t*(2+_azar(i, 9)*5)) % 1320-20
            y = 45+_azar(i, 21)*410+math.sin(t*.55+i)*9
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(_color("#f5dba8", 20+_azar(i, 3)*33))
            p.drawEllipse(QPointF(x, y), 1.1, 1.1)
        # Lluvia sólo en el exterior de la ventana del plano de situación.
        if ambiente == "lluvia" and t < 1.9:
            p.save()
            imagen = self._imagen(self.fuentes[0])
            recorte = self._recorte(0, t)
            ventanas = QPainterPath()
            for x, y, w, h in ((.557, .13, .067, .35), (.659, 0, .071, .397),
                                (.744, 0, .081, .39), (.858, 0, .142, .34)):
                ventanas.addRect(QRectF((x*imagen.width()-recorte.x())*1280/recorte.width(),
                                        (y*imagen.height()-recorte.y())*720/recorte.height(),
                                        w*imagen.width()*1280/recorte.width(), h*imagen.height()*720/recorte.height()))
            p.setClipPath(ventanas)
            p.setPen(QPen(_color("#c1e5ed", 70), 1.25))
            for i in range(65):
                x = _azar(i, 41)*1280
                y = (_azar(i, 43)*400+t*190)%400
                p.drawLine(QPointF(x, y), QPointF(x-3, y+17))
            p.restore()

    def _rotulo(self, p, texto, x, y, ancho, alfa=1, acento="#f7d79a", tamano=22):
        p.save()
        p.setOpacity(alfa)
        p.setPen(QPen(_color(acento, 125), 1.3))
        p.setBrush(_color("#0c2330", 227))
        p.drawRoundedRect(QRectF(x, y, ancho, 44), 13, 13)
        p.setFont(_fuente(tamano, True))
        p.setPen(QColor(acento))
        p.drawText(QRectF(x+13, y, ancho-26, 44), Qt.AlignmentFlag.AlignCenter, texto)
        p.restore()

    def _lineas(self, p, x, y, n=4, ancho=205, color="#94afb5"):
        p.setPen(QPen(QColor(color), 3.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for i in range(n):
            p.drawLine(QPointF(x, y+i*21), QPointF(x+ancho*(.75 if i == n-1 else 1), y+i*21))

    def _telefono(self, p, x, y, titulo, t, enviar=False, quieto=False):
        p.save()
        p.translate(x, y)
        if not quieto:
            p.rotate(-3+1.2*math.sin(t*.7))
        # El mismo contenido canónico que se está leyendo en el juego queda
        # dentro de un dispositivo físico. La acción conserva su montaje y
        # sus interlocutores; el teléfono ya no inventa otra tarjeta azul.
        pintar_telefono(p, 0, 0, 240, 420, self.ficha["publicacion"])
        p.restore()

    def _papel(self, p, x, y, titulo, giro=0):
        p.save(); p.translate(x, y); p.rotate(giro)
        p.setPen(QPen(QColor("#d6bc91"), 1.4)); p.setBrush(_color("#f1e4c6", 247))
        p.drawRoundedRect(QRectF(0, 0, 260, 255), 7, 7)
        p.setPen(QColor("#243e49")); p.setFont(_fuente(19, True))
        p.drawText(QRectF(17, 15, 226, 55), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, titulo)
        self._lineas(p, 25, 92, 6, 206, "#8e9990")
        p.restore()

    def _objeto_caso(self, p, t):
        # La marca de contexto se mantiene pequeña, encima del diálogo del juego.
        a = _rango(t, .25, .7)*(1-_rango(t, 2.95, 3.4))
        self._rotulo(p, self.caso["titulo"], 70, 102, 490, a, tamano=23)
        if not 1.9 <= t <= 3.85:
            return
        a = _rango(t, 2.08, 2.4)*(1-_rango(t, 3.45, 3.85))
        p.save(); p.setOpacity(a*.95)
        self._rotulo(p, self.caso["cautela"], 650, 128, 535, 1, tamano=21)
        if self.ficha["publicacion"] == 70:
            # El trazo recorre un mapa; no dibuja un cierre total del parque.
            p.setPen(QPen(_color("#fff0bf", 225), 4, Qt.PenStyle.DashLine, Qt.PenCapStyle.RoundCap))
            camino = QPainterPath(QPointF(310, 415)); camino.cubicTo(450, 240, 600, 460, 825, 285)
            p.drawPath(camino)
            for i, (x, y) in enumerate(((310, 415), (560, 355), (825, 285))):
                r = 8+4*math.sin(t*4+i)
                p.setBrush(_color("#77ded2", 150)); p.drawEllipse(QPointF(x, y), r, r)
        elif self.ficha["publicacion"] == 20:
            for i in range(4):
                x = 825+i*60
                p.setPen(QPen(_color("#a0d4d4", 130), 2))
                p.drawRect(QRectF(x, 220, 42, 190))
        elif self.ficha["publicacion"] == 80:
            self._rotulo(p, "Fecha  ·  Muestra  ·  Método", 765, 210, 400, 1, "#a5dbdc", 21)
        p.restore()

    def _compartir(self, p, u, invitacion=False):
        self._telefono(p, 894, 150, self.caso["tema"], u, True)
        if invitacion:
            titulo = "Invitación enviada" if self.ficha["variante"] == "alcance_limitado" else "Invitación pendiente"
            self._rotulo(p, titulo, 870, 120, 315, _rango(u, .4, 1), "#b5d7dd", 21)
            return
        for i in range(3):
            avance = (u*.48-i*.25)%1
            if u < .3+i*.4:
                continue
            x = 1038-225*avance; y = 375-155*avance-22*math.sin(avance*math.pi)
            p.save(); p.setOpacity(math.sin(avance*math.pi)*.92)
            p.setPen(QPen(QColor("#c4f2df"), 1.5)); p.setBrush(_color("#234c54", 245))
            p.drawRoundedRect(QRectF(x, y, 92, 48), 12, 12)
            p.drawLine(QPointF(x+19, y+16), QPointF(x+46, y+16)); p.drawLine(QPointF(x+19, y+29), QPointF(x+70, y+29))
            p.restore()

    def _conversacion(self, p, u, entrevista=False):
        # Una burbuja responde a otra; son turnos de escucha, no difusión viral.
        posiciones = ((970, 120, 230), (970, 205, 230)) if entrevista else ((795, 342, 260), (875, 423, 280))
        for i, (x, y, w) in enumerate(posiciones):
            a = _rango(u, .2+i*.8, .65+i*.8)
            p.save(); p.setOpacity(a*(.88+.08*math.sin(u*2-i)))
            p.setPen(QPen(_color("#bfe8df", 210), 2)); p.setBrush(_color("#193c49", 215))
            p.drawRoundedRect(QRectF(x, y+4*math.sin(u*1.2+i), w, 74), 18, 18)
            self._lineas(p, x+24, y+25, 2, w-52, "#b4ded6")
            p.restore()
        if entrevista:
            a = _rango(u, 1.3, 1.9)
            p.save(); p.setOpacity(a)
            self._papel(p, 950, 315, "Testimonio", -7)
            p.setPen(QPen(QColor("#287d82"), 3))
            longitud = 170*_rango(u, 1.8, 3.9)
            p.drawLine(QPointF(985, 405), QPointF(985+longitud, 405))
            p.restore()

    def _convocar(self, p, u):
        if self.ficha["variante"] in ("sin_receptores", "alcance_limitado"):
            self._compartir(p, u, True)

    def _invitaciones_previas(self, p, t):
        """Invitar precede a la reunión: las tarjetas nunca tapan a sus vecinos."""
        if self.ficha["accion"] != "convocar" or self.ficha["variante"] or not 2.2 <= t < 3.7:
            return
        salida = 1-_rango(t, 3.2, 3.7)
        u = t-2.2
        # Estas tarjetas se montan exclusivamente sobre el objeto/documento.
        # Al entrar la reunión ya desaparecieron, dejando libres los rostros.
        for i, (x, y, giro) in enumerate(((825, 180, -9), (940, 255, 5), (805, 340, -3))):
            a = _rango(u, i*.15, .35+i*.15)*salida
            p.save(); p.setOpacity(a); p.translate(x, y-14*(1-a)); p.rotate(giro)
            p.setPen(QPen(QColor("#d2c192"), 1.4)); p.setBrush(_color("#f0dfb8", 242))
            p.drawRoundedRect(QRectF(0, 0, 245, 100), 9, 9)
            p.setPen(QColor("#23414a")); p.setFont(_fuente(20, True))
            p.drawText(QRectF(12, 10, 220, 30), Qt.AlignmentFlag.AlignCenter, "Encuentro vecinal")
            self._lineas(p, 25, 58, 2, 170, "#8e9c8d"); p.restore()

    def _ignorar(self, p, u):
        a = 1-.8*_rango(u, .2, 2.8)
        p.save(); p.setOpacity(a)
        self._telefono(p, 900, 145, self.caso["tema"], u, quieto=True)
        p.restore()
        self._rotulo(p, "Sin reenvío", 900, 130, 260, _rango(u, .7, 1.35), "#c3d5dc", 22)

    def _contrastar(self, p, u):
        p.save(); p.setOpacity(_rango(u, .15, .7))
        self._papel(p, 785, 180, self.caso["fuente"], -5)
        self._papel(p, 925, 225, "Anotaciones", 6)
        p.restore()
        # El círculo sigue líneas del documento y una marca enlaza las fuentes.
        x = 970+38*math.sin(u*1.4); y = 315+24*math.sin(u*.9)
        p.setBrush(_color("#94d4d9", 35)); p.setPen(QPen(QColor("#b4e4dc"), 4))
        p.drawEllipse(QPointF(x, y), 43, 43)
        p.drawLine(QPointF(x+31, y+31), QPointF(x+64, y+66))
        self._rotulo(p, "Revisión de fuentes", 820, 130, 350, _rango(u, .5, 1.1), "#b6e5de", 22)

    def _desmentir(self, p, u):
        rechazado = self.ficha["variante"] == "rechazado"
        p.save(); p.setOpacity(_rango(u, .1, .65))
        self._papel(p, 865, 180, "Reporte" if rechazado else "Rectificación", -3)
        p.restore()
        progreso = _rango(u, .5, 2.6)
        p.setPen(QPen(QColor("#287878"), 3.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for i in range(3):
            parcial = min(1, max(0, progreso*3-i))
            if parcial:
                p.drawLine(QPointF(893, 286+i*20), QPointF(893+174*parcial, 286+i*20))
        texto = "Contenido permanece" if rechazado else "Contenido retirado"
        acento = "#efcc9d" if rechazado else "#afe1da"
        self._rotulo(p, texto, 795, 400, 390, _rango(u, 2.6, 3.25), acento, 23)
        if rechazado:
            self._rotulo(p, "Reporte rechazado", 825, 130, 350, _rango(u, 2, 2.6), acento, 22)

    def _reservar(self, p, u):
        p.save(); p.setOpacity(_rango(u, .1, .6))
        self._papel(p, 888, 175, self.caso["tema"], -4)
        # La tapa cubre el documento en vez de enviarlo a una red.
        cierre = _rango(u, .9, 3.5)
        p.setPen(QPen(QColor("#d4ba86"), 2)); p.setBrush(_color("#324d56", 248))
        p.drawRoundedRect(QRectF(842, 212-45*cierre, 342, 255*cierre), 10, 10)
        p.setBrush(QColor("#d8bc83")); p.drawRoundedRect(QRectF(858, 151, 138, 37), 6, 6)
        p.restore()
        self._rotulo(p, "Pendiente de pruebas", 845, 340, 330, _rango(u, 2.3, 3), "#f2d6a3", 22)

    def _accion(self, p, t):
        if t < 3.7:
            return
        if self.ficha["accion"] == "convocar" and not self.ficha["variante"]:
            # La reunión es el resultado visible: no necesita una lámina de
            # contraste ni rótulos que oscurezcan la cara de sus participantes.
            return
        u = t-3.7
        p.save(); p.setOpacity(_rango(u, .2, .75))
        # Las capas se sitúan en el costado derecho para preservar el rostro.
        gradiente = QLinearGradient(710, 0, 1280, 0)
        gradiente.setColorAt(0, QColor(0, 0, 0, 0)); gradiente.setColorAt(1, _color("#061924", 85))
        p.fillRect(QRectF(710, 100, 570, 440), gradiente)
        accion = self.ficha["accion"]
        if accion == "compartir": self._compartir(p, u)
        elif accion == "conversar": self._conversacion(p, u)
        elif accion == "convocar": self._convocar(p, u)
        elif accion == "ignorar": self._ignorar(p, u)
        elif accion == "contrastar": self._contrastar(p, u)
        elif accion == "entrevistar": self._conversacion(p, u, True)
        elif accion == "desmentir": self._desmentir(p, u)
        elif accion == "reservar": self._reservar(p, u)
        p.restore()

    def capturar_fotograma(self, segundos=0, tamano=(1280, 720)):
        ancho, alto = map(int, tamano)
        if ancho <= 0 or alto <= 0:
            raise ValueError("El tamaño de fotograma debe ser positivo")
        t = min(DURACION-1/FPS, max(0, float(segundos)))
        imagen = QImage(ancho, alto, QImage.Format.Format_ARGB32)
        imagen.fill(QColor("#102330"))
        p = QPainter(imagen)
        p.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        p.scale(ancho/1280, alto/720)
        self._montaje(p, t)
        self._ambiente(p, t)
        self._objeto_caso(p, t)
        self._invitaciones_previas(p, t)
        self._accion(p, t)
        # Un viñeteado leve integra las capas sin tapar la acción o los rostros.
        bordes = QRadialGradient(QPointF(625, 315), 800)
        bordes.setColorAt(.45, QColor(0, 0, 0, 0)); bordes.setColorAt(1, _color("#020b14", 105))
        p.fillRect(QRectF(0, 0, 1280, 720), bordes)
        p.end()
        return imagen
