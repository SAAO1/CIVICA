"""Efectos decorativos ligados al relato, dibujados sin recursos externos.

La capa debe ocupar el rectángulo de la escena y quedar debajo del diálogo.
Nunca contiene texto ni interpreta la veracidad de una publicación. Los efectos
se apagan al terminar, se pausan al ocultarse y respetan movimiento reducido.
``capturar_fotograma`` permite exportar la misma animación que ve el jugador.
"""
from __future__ import annotations

import math
import time

from PyQt6.QtCore import QEvent, QPointF, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QColor, QImage, QLinearGradient, QPainter, QPainterPath, QPen,
    QRadialGradient,
)
from PyQt6.QtWidgets import QWidget


EFECTOS = (
    "notificacion", "rumor", "investigar", "verificar", "reportar",
    "silencio", "lluvia", "tension", "eleccion", "recuerdo",
    "decision", "archivo", "transicion", "fuente",
    "emision", "foro", "onda", "papeleta",
)
ALIAS = {
    "compartir": "rumor", "ignorar": "silencio", "investigacion": "investigar",
    "verificacion": "verificar", "notificación": "notificacion",
    "elección": "eleccion", "transición": "transicion", "papeles": "archivo",
    "red": "rumor", "hallazgo": "investigar", "memoria": "recuerdo",
}
FPS_EFECTOS = 30


def _limitar(valor, minimo=0.0, maximo=1.0):
    return max(minimo, min(maximo, valor))


def _semilla(indice, canal=0):
    numero = math.sin(indice * 127.1 + canal * 311.7 + 17.73) * 43758.5453
    return numero - math.floor(numero)


def _color(rgb, alfa=255):
    return QColor(*rgb, round(_limitar(alfa, 0, 255)))


def _pluma(rgb, alfa=180, ancho=1.5):
    pluma = QPen(_color(rgb, alfa), ancho)
    pluma.setCapStyle(Qt.PenCapStyle.RoundCap)
    pluma.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pluma


def _suave(valor):
    valor = _limitar(valor)
    return valor * valor * (3 - 2 * valor)


class CapaEfectos(QWidget):
    """Capa transparente de un efecto breve; no intercepta controles ni foco.

    ``reproducir`` devuelve False si el nombre no existe. Cambiar de efecto
    cancela el anterior sin emitir finalización. En movimiento reducido queda
    una composición quieta y tenue hasta que la escena la retire con detener().
    ``activo=False`` pausa; ``detener()`` limpia por completo el lienzo.
    ``pausar()/reanudar()`` suspenden el relato sin alterar las preferencias.
    """

    efecto_terminado = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAccessibleName("Efectos ambientales del relato")
        self._tipo = ""
        self._duracion = 3.8
        self._intensidad = 1.0
        self._activo = True
        self._pausada = False
        self._reducir_movimiento = False
        self._transcurrido = 0.0
        self._inicio = None
        self._tiempo_fijo = None
        self._ventana_observada = None
        self._timer = QTimer(self)
        self._timer.setInterval(math.ceil(1000 / FPS_EFECTOS))
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.timeout.connect(self._avanzar)

    @property
    def tipo(self):
        return self._tipo

    @property
    def reproduciendo(self):
        return bool(self._tipo)

    @property
    def animando(self):
        return self._timer.isActive()

    def reproducir(self, tipo, duracion=3.8, intensidad=1.0):
        """Sustituye el efecto. Duración en segundos, intensidad entre 0 y 1.3."""
        nombre = str(tipo).strip().lower()
        nombre = ALIAS.get(nombre, nombre)
        if nombre not in EFECTOS:
            return False
        try:
            duracion, intensidad = float(duracion), float(intensidad)
        except (TypeError, ValueError):
            raise ValueError("La duración y la intensidad deben ser números finitos") from None
        if not math.isfinite(duracion) or not math.isfinite(intensidad) or duracion <= 0:
            raise ValueError("La duración debe ser positiva y los valores finitos")
        self._pausar_reloj()
        self._tipo = nombre
        self._duracion = _limitar(duracion, .2, 120)
        self._intensidad = _limitar(intensidad, 0, 1.3)
        self._transcurrido = 0.0
        self._tiempo_fijo = None
        self._pausada = False
        if self.isVisible():
            self._observar_ventana()
        self._sincronizar_reloj()
        self.update()
        return True

    def detener(self):
        self._pausar_reloj()
        self._desvincular_ventana()
        self._tipo = ""
        self._transcurrido = 0.0
        self._tiempo_fijo = None
        self._pausada = False
        self.update()

    def pausar(self):
        """Congela el instante mientras se consulta el cuaderno o un modal."""
        self._pausada = True
        self._pausar_reloj()

    def reanudar(self):
        """Reanuda si la capa es visible y sus preferencias permiten animación."""
        self._pausada = False
        self._sincronizar_reloj()
        self.update()

    def configurar(self, reducir_movimiento=None, activo=None):
        self._pausar_reloj()
        if reducir_movimiento is not None:
            self._reducir_movimiento = bool(reducir_movimiento)
        if activo is not None:
            self._activo = bool(activo)
        self._sincronizar_reloj()
        self.update()

    def establecer_tiempo(self, segundos=None):
        """Fija un instante para QA; None devuelve el control al reloj visible."""
        if segundos is not None:
            segundos = float(segundos)
            if not math.isfinite(segundos) or segundos < 0:
                raise ValueError("El tiempo debe ser finito y no negativo")
        anterior = self.tiempo_actual()
        self._pausar_reloj()
        self._tiempo_fijo = segundos
        if segundos is None:
            self._transcurrido = anterior
        self._sincronizar_reloj()
        self.update()

    def tiempo_actual(self):
        if self._tiempo_fijo is not None:
            return self._tiempo_fijo
        if self._inicio is not None:
            return self._transcurrido + time.monotonic() - self._inicio
        return self._transcurrido

    def _pausar_reloj(self):
        if self._inicio is not None:
            self._transcurrido += time.monotonic() - self._inicio
        self._inicio = None
        self._timer.stop()

    def _sincronizar_reloj(self):
        visible = self.isVisible() and not self.window().isMinimized()
        correr = (self.reproduciendo and self._activo and not self._pausada and visible
                  and not self._reducir_movimiento and self._tiempo_fijo is None)
        if correr and not self.animando:
            self._inicio = time.monotonic()
            self._timer.start()
        elif not correr:
            self._pausar_reloj()

    def _avanzar(self):
        if self.window().isMinimized():
            self._sincronizar_reloj()
            return
        if self.tiempo_actual() >= self._duracion:
            tipo = self._tipo
            self.detener()
            self.efecto_terminado.emit(tipo)
        else:
            self.update()

    def _desvincular_ventana(self):
        ventana = getattr(self, "_ventana_observada", None)
        self._ventana_observada = None
        if ventana is not None and ventana is not self:
            try:
                ventana.removeEventFilter(self)
            except RuntimeError:
                pass

    def _observar_ventana(self):
        ventana = self.window()
        if getattr(self, "_ventana_observada", None) is not ventana:
            self._desvincular_ventana()
            self._ventana_observada = ventana
            if ventana is not self:
                ventana.installEventFilter(self)

    def showEvent(self, event):
        super().showEvent(event)
        self._observar_ventana()
        self._sincronizar_reloj()

    def hideEvent(self, event):
        self._pausar_reloj()
        super().hideEvent(event)

    def changeEvent(self, event):
        super().changeEvent(event)
        # La ventana principal puede minimizarse sin ocultar a todos sus hijos.
        self._sincronizar_reloj()

    def eventFilter(self, objeto, event):
        observada = getattr(self, "_ventana_observada", None)
        if (observada is not None and objeto is observada
                and event.type() == QEvent.Type.WindowStateChange):
            self._sincronizar_reloj()
        return super().eventFilter(objeto, event)

    def paintEvent(self, event):
        pintor = QPainter(self)
        self._pintar(pintor, self.width(), self.height(), self.tiempo_actual())
        pintor.end()

    def capturar_fotograma(self, segundos=None, tamano=(1280, 720)):
        """QImage RGBA transparente sin cambiar reproducción, visibilidad ni reloj."""
        ancho, alto = int(tamano[0]), int(tamano[1])
        if ancho <= 0 or alto <= 0:
            raise ValueError("El tamaño debe ser positivo")
        tiempo = self.tiempo_actual() if segundos is None else float(segundos)
        if not math.isfinite(tiempo) or tiempo < 0:
            raise ValueError("El tiempo debe ser finito y no negativo")
        imagen = QImage(ancho, alto, QImage.Format.Format_ARGB32_Premultiplied)
        imagen.fill(Qt.GlobalColor.transparent)
        pintor = QPainter(imagen)
        self._pintar(pintor, ancho, alto, tiempo)
        pintor.end()
        return imagen

    def _pintar(self, p, ancho, alto, tiempo):
        if not self._tipo or not ancho or not alto or not self._intensidad:
            return
        reducido = self._reducir_movimiento
        if reducido:
            tiempo = min(.85, self._duracion * .4)
        elif tiempo >= self._duracion:
            return
        entrada = _suave(tiempo / min(.42, self._duracion / 3))
        salida = _suave((self._duracion - tiempo) / min(.85, self._duracion / 3))
        opacidad = entrada * salida * self._intensidad * (.38 if reducido else .86)
        p.save()
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.scale(ancho / 1280.0, alto / 720.0)
        # Ni partículas ni destellos pasan por encima de la caja de lectura.
        p.setClipRect(QRectF(0, 0, 1280, 485))
        p.setOpacity(min(.95, opacidad))
        getattr(self, "_" + self._tipo)(p, tiempo)
        p.restore()

    @staticmethod
    def _halo(p, x, y, radio, rgb, alfa=75):
        gradiente = QRadialGradient(QPointF(x, y), radio)
        gradiente.setColorAt(0, _color(rgb, alfa))
        gradiente.setColorAt(.45, _color(rgb, alfa * .36))
        gradiente.setColorAt(1, _color(rgb, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(gradiente)
        p.drawEllipse(QPointF(x, y), radio, radio)

    def _emision(self, p, t):
        """Pulsos de una emisión: representan alcance, nunca veracidad."""
        color = (211, 150, 196)
        self._halo(p, 1050, 185, 185, color, 42)
        for i in range(4):
            fase = (t * .28 + i / 4) % 1
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(_pluma(color, 115 * (1-fase), 2))
            radio = 25 + fase * 135
            p.drawEllipse(QPointF(1050, 185), radio, radio)
        for i in range(8):
            fase = (t * .22 + i / 8) % 1
            p.setBrush(_color(color, 100 * (1-fase)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(QRectF(960+i*20, 360-fase*130, 12, 7), 3, 3)

    def _foro(self, p, t):
        """Cuatro haces de idéntico peso para las cuatro candidaturas."""
        for i in range(4):
            x = 760 + i * 125
            angulo = math.sin(t * .5 + i) * 16
            color = (211, 197, 161)
            haz = QPainterPath(QPointF(x, 15))
            haz.lineTo(x-65+angulo, 400)
            haz.lineTo(x+65+angulo, 400)
            haz.closeSubpath()
            p.setBrush(_color(color, 12))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPath(haz)
            self._halo(p, x, 18, 40, color, 45)

    def _onda(self, p, t):
        color = (118, 200, 211)
        p.setPen(_pluma(color, 150, 2))
        for i in range(74):
            alto = 5 + abs(math.sin(i*.73+t*2.1)*math.sin(i*.19-t*.7))*55
            x = 795+i*5
            p.drawLine(QPointF(x, 245-alto), QPointF(x, 245+alto))
        p.setPen(_pluma((240, 193, 135), 170, 2))
        x = 795 + (t*.17 % 1) * 365
        p.drawLine(QPointF(x, 168), QPointF(x, 322))

    def _papeleta(self, p, t):
        """Documentos y ruta: sin confeti ni victoria antes del recuento."""
        color = (206, 211, 181)
        for i in range(4):
            fase = (t*.16+i*.23) % 1
            self._documento(p, 930+i*55, 125+fase*175,
                            math.sin(t+i)*8, .32, color, 110*(1-fase*.6))
        p.setPen(_pluma(color, 110, 2))
        for i in range(9):
            x = 850 + i*33
            y = 370 - math.sin(i*.35)*42
            p.drawEllipse(QPointF(x, y), 2.5, 2.5)

    @staticmethod
    def _documento(p, x, y, giro=0, escala=1, rgb=(176, 215, 222), alfa=125):
        p.save()
        p.translate(x, y)
        p.rotate(giro)
        p.scale(escala, escala)
        p.setBrush(_color((28, 47, 58), alfa * .35))
        p.setPen(_pluma(rgb, alfa, 1.5))
        p.drawRoundedRect(QRectF(-42, -54, 84, 108), 5, 5)
        p.setPen(_pluma(rgb, alfa * .72, 2))
        for i, largo in enumerate((40, 57, 52, 57, 30)):
            p.drawLine(QPointF(-28, -30 + i * 15), QPointF(-28 + largo, -30 + i * 15))
        p.restore()

    def _notificacion(self, p, t):
        azul = (133, 215, 232)
        self._halo(p, 1040, 129, 205, azul, 75)
        for i in range(3):
            fase = (t * .55 + i / 3) % 1
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(_pluma(azul, (1-fase) * 110, 1.6))
            p.drawEllipse(QPointF(1040, 129), 25 + fase * 150, 25 + fase * 150)
        for i in range(3):
            x = 1010 - i * 46 + 28 * math.exp(-t * 2)
            y = 108 + i * 57 + math.sin(t * 1.3 + i) * 3
            p.setBrush(_color((34, 66, 79), 135 - i * 23))
            p.setPen(_pluma(azul, 170 - i * 35))
            p.drawRoundedRect(QRectF(x - 113, y - 22, 204, 44), 12, 12)
            p.setBrush(_color(azul, 190 - i * 30))
            p.drawEllipse(QPointF(x - 87, y), 5, 5)
            p.drawLine(QPointF(x - 68, y - 5), QPointF(x + 58, y - 5))
            p.setPen(_pluma(azul, 85 - i * 15))
            p.drawLine(QPointF(x - 68, y + 7), QPointF(x + 15, y + 7))

    def _rumor(self, p, t):
        naranja = (234, 171, 112)
        puntos = [QPointF(190 + _semilla(i, 1) * 900,
                          70 + _semilla(i, 2) * 340) for i in range(16)]
        for i, a in enumerate(puntos):
            b = puntos[(i * 5 + 3) % len(puntos)]
            fase = (t * .32 + i * .17) % 1
            p.setPen(_pluma(naranja, 58, 1.1))
            p.drawLine(a, b)
            viajero = a + (b - a) * fase
            self._halo(p, viajero.x(), viajero.y(), 15, naranja, 125)
            p.setBrush(_color(naranja, 155))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(viajero, 2.7, 2.7)
            radio = 4 + 1.3 * math.sin(t * 1.5 + i)
            p.setBrush(_color((45, 43, 44), 125))
            p.setPen(_pluma(naranja, 145, 1.4))
            p.drawEllipse(a, radio, radio)
        for i in range(5):
            fase = (t * .17 + i * .2) % 1
            self._documento(p, 420 + fase * 430, 150 + i * 39,
                            -9 + i * 5, .36, naranja, (1-fase) * 120)

    def _investigar(self, p, t):
        azul = (149, 205, 221)
        x = 240 + ((t * 86) % 850)
        gradiente = QLinearGradient(x-105, 0, x+105, 0)
        gradiente.setColorAt(0, _color(azul, 0))
        gradiente.setColorAt(.5, _color(azul, 24))
        gradiente.setColorAt(1, _color(azul, 0))
        p.fillRect(QRectF(x-105, 35, 210, 415), gradiente)
        for i in range(3):
            self._documento(p, 780 + i * 93, 160 + i * 41,
                            -8 + i * 8, .95, azul, 155 - i * 22)
        centro = QPointF(850 + 30 * math.sin(t * .7), 215 + 25 * math.cos(t * .6))
        self._halo(p, centro.x(), centro.y(), 110, azul, 46)
        p.setBrush(_color(azul, 12))
        p.setPen(_pluma(azul, 190, 2.3))
        p.drawEllipse(centro, 40, 40)
        p.drawLine(centro + QPointF(29, 29), centro + QPointF(67, 67))
        for dx, dy in ((-19, -19), (19, -19), (-19, 19), (19, 19)):
            a = centro + QPointF(dx * 2.8, dy * 2.8)
            p.drawLine(a, a + QPointF(-math.copysign(13, dx), 0))
            p.drawLine(a, a + QPointF(0, -math.copysign(13, dy)))

    def _verificar(self, p, t):
        verde = (137, 218, 178)
        cx, cy = 1010, 195
        self._halo(p, cx, cy, 180, verde, 64)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(_pluma(verde, 125, 1.6))
        p.drawEllipse(QPointF(cx, cy), 64, 64)
        p.setPen(_pluma(verde, 60, 1))
        p.drawEllipse(QPointF(cx, cy), 82, 82)
        for i in range(12):
            angulo = i * math.tau / 12 + t * .05
            a = QPointF(cx + math.cos(angulo) * 89, cy + math.sin(angulo) * 89)
            b = QPointF(cx + math.cos(angulo) * 97, cy + math.sin(angulo) * 97)
            p.drawLine(a, b)
        trazo = QPainterPath(QPointF(cx - 29, cy))
        avance = _suave((t - .15) / .8)
        if avance < .35:
            trazo.lineTo(cx - 29 + 22 * avance / .35, cy + 24 * avance / .35)
        else:
            trazo.lineTo(cx - 7, cy + 24)
            trazo.lineTo(cx - 7 + 43 * (avance-.35)/.65,
                         cy + 24 - 52 * (avance-.35)/.65)
        p.setPen(_pluma(verde, 210, 4))
        p.drawPath(trazo)
        for i in range(5):
            fase = (t * .2 + i * .2) % 1
            p.setPen(_pluma(verde, (1-fase) * 100))
            p.drawLine(QPointF(770 + fase*150, 125 + i*34),
                       QPointF(805 + fase*150, 125 + i*34))

    def _reportar(self, p, t):
        ambar = (225, 179, 130)
        cx, cy = 1005, 210
        self._halo(p, cx, cy, 155, ambar, 58)
        escudo = QPainterPath(QPointF(cx, cy-61))
        escudo.lineTo(cx+48, cy-43)
        escudo.lineTo(cx+43, cy+13)
        escudo.quadTo(cx+30, cy+43, cx, cy+63)
        escudo.quadTo(cx-30, cy+43, cx-43, cy+13)
        escudo.lineTo(cx-48, cy-43)
        escudo.closeSubpath()
        p.setBrush(_color(ambar, 13))
        p.setPen(_pluma(ambar, 180, 2))
        p.drawPath(escudo)
        p.setPen(_pluma(ambar, 125, 1.3))
        for dx in (-13, 0, 13):
            p.drawLine(QPointF(cx+dx, cy-19), QPointF(cx+dx, cy+21))
        for i in range(18):
            angulo = _semilla(i, 8) * math.tau
            radio = 84 + ((t*14 + _semilla(i, 9)*80) % 125)
            p.save()
            p.translate(cx + math.cos(angulo)*radio, cy + math.sin(angulo)*radio*.8)
            p.rotate(t*9+i*31)
            p.setBrush(_color(ambar, max(0, 105-radio*.33)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(QRectF(-4, -1.5, 8, 3), 1, 1)
            p.restore()

    def _silencio(self, p, t):
        gris = (155, 188, 201)
        for i in range(5):
            fase = (t*.16 + i*.18) % 1
            centro = QPointF(1040 + fase*80, 210)
            radio = 35 + fase*185
            p.setPen(_pluma(gris, (1-fase)*95, 1.7))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(QRectF(centro.x()-radio, centro.y()-radio, radio*2, radio*2),
                      -70*16, 140*16)
        gradiente = QLinearGradient(620, 0, 1280, 0)
        gradiente.setColorAt(0, _color((31, 54, 68), 0))
        gradiente.setColorAt(1, _color((31, 54, 68), 36))
        p.fillRect(QRectF(620, 0, 660, 485), gradiente)
        for i in range(10):
            x = 800 + _semilla(i, 2)*390 + t*6
            y = 100 + _semilla(i, 4)*290 + math.sin(t*.4+i)*6
            p.setBrush(_color(gris, 50))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(x % 1280, y), 1.5, 1.5)

    def _lluvia(self, p, t):
        azul = (161, 196, 213)
        for i in range(85):
            largo = 7 + _semilla(i, 3)*19
            x = (_semilla(i, 1)*1360 - t*(30+_semilla(i, 4)*22)) % 1360-40
            y = (_semilla(i, 2)*560 + t*(170+_semilla(i, 5)*150)) % 560-45
            p.setPen(_pluma(azul, 34+_semilla(i, 6)*46, .7+_semilla(i)*.8))
            p.drawLine(QPointF(x, y), QPointF(x-3, y+largo))
        for i in range(13):
            fase = (t*.5+_semilla(i, 8)) % 1
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(_pluma(azul, (1-fase)*54, 1))
            p.drawEllipse(QPointF(100+_semilla(i, 9)*1080,
                                 370+_semilla(i, 10)*105), 3+fase*21, 1+fase*4)
        for i in range(7):
            x = 90 + _semilla(i, 11)*1100
            self._halo(p, x, 455, 35, (226, 183, 134), 18)

    def _tension(self, p, t):
        vino = (83, 37, 42)
        for x in (-140, 1420):
            self._halo(p, x, 240, 460, vino, 115)
        for i in range(4):
            camino = QPainterPath(QPointF(0, 95+i*77))
            for x in range(0, 1281, 16):
                y = 95+i*77+math.sin(x/180+t*.7+i)*10
                camino.lineTo(x, y)
            p.setPen(_pluma((216, 152, 126), 22+i*3, 1.1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(camino)
        for i in range(16):
            x = _semilla(i, 4)*1280+math.sin(t*.3+i)*6
            y = (_semilla(i, 7)*480-t*3) % 480
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(_color((230, 186, 156), 40))
            p.drawEllipse(QPointF(x, y), 1.2, 1.2)

    def _eleccion(self, p, t):
        colores = ((224, 191, 117), (140, 199, 200), (207, 153, 133))
        for i in range(42):
            y = (_semilla(i, 1)*620+t*(27+_semilla(i, 3)*33)) % 620-70
            x = _semilla(i, 2)*1280+math.sin(t*.7+i)*22
            p.save()
            p.translate(x, y)
            p.rotate(i*37+t*(15+_semilla(i)*38))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(_color(colores[i % 3], 85+_semilla(i, 5)*70))
            p.drawRoundedRect(QRectF(-3, -1, 6, 2.7), .8, .8)
            p.restore()
        for i in range(6):
            self._halo(p, 100+i*213+math.sin(t*.25+i)*28,
                       80+_semilla(i, 6)*320, 32+_semilla(i, 7)*32,
                       colores[i % 3], 26)

    def _recuerdo(self, p, t):
        oro = (244, 196, 132)
        self._halo(p, 40+math.sin(t*.15)*40, 100, 450, oro, 67)
        self._halo(p, 1230, 350, 340, (219, 158, 131), 48)
        for i in range(30):
            x = (_semilla(i, 2)*1320+t*(4+_semilla(i, 4)*6)) % 1320-20
            y = (_semilla(i, 3)*520-t*(3+_semilla(i, 5)*5)) % 520-20
            radio = .7+_semilla(i, 6)*1.7
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(_color(oro, 44+_semilla(i, 7)*63))
            p.drawEllipse(QPointF(x, y), radio, radio)
        p.setPen(_pluma(oro, 40, 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(48, 42, 1184, 418), 14, 14)

    def _decision(self, p, t):
        azul = (160, 206, 216)
        centro = QPointF(640, 235)
        self._halo(p, 640, 235, 170, azul, 30)
        p.setBrush(Qt.BrushStyle.NoBrush)
        for i in range(3):
            angulo = -.5*math.pi + i*math.tau/3
            fin = centro+QPointF(math.cos(angulo)*180, math.sin(angulo)*145)
            p.setPen(_pluma(azul, 70, 1.3))
            p.drawLine(centro, fin)
            fase = (t*.27+i*.33) % 1
            dot = centro+(fin-centro)*fase
            p.setBrush(_color(azul, 150))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(dot, 3, 3)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(_pluma(azul, 105, 1.7))
            p.drawEllipse(fin, 11, 11)
        p.setPen(_pluma(azul, 85, 1.5))
        p.drawEllipse(centro, 27, 27)
        p.drawArc(QRectF(596, 191, 88, 88), round(t*11*16), 210*16)

    def _archivo(self, p, t):
        crema = (225, 206, 169)
        for i in range(4):
            self._documento(p, 890+i*43, 205+i*14,
                            -15+i*9+math.sin(t*.45)*2, 1.25,
                            crema, 145-i*20)
        y = 85+((t*52) % 275)
        gradiente = QLinearGradient(0, y-20, 0, y+20)
        gradiente.setColorAt(0, _color(crema, 0))
        gradiente.setColorAt(.5, _color(crema, 33))
        gradiente.setColorAt(1, _color(crema, 0))
        p.fillRect(QRectF(775, y-20, 320, 40), gradiente)
        p.setPen(_pluma(crema, 80, 1))
        for x in (755, 1125):
            p.drawLine(QPointF(x, 65), QPointF(x, 370))
            p.drawLine(QPointF(x-7, 65), QPointF(x+7, 65))
            p.drawLine(QPointF(x-7, 370), QPointF(x+7, 370))

    def _transicion(self, p, t):
        fase = _limitar(t / max(.2, self._duracion))
        x = -300+fase*1880
        gradiente = QLinearGradient(x-250, 0, x+250, 0)
        gradiente.setColorAt(0, _color((215, 189, 146), 0))
        gradiente.setColorAt(.45, _color((215, 189, 146), 18))
        gradiente.setColorAt(.5, _color((240, 216, 176), 38))
        gradiente.setColorAt(1, _color((215, 189, 146), 0))
        p.fillRect(QRectF(x-250, 0, 500, 485), gradiente)
        for i in range(14):
            y = 40+_semilla(i, 1)*400
            self._halo(p, x+(_semilla(i, 2)-.5)*330, y,
                       10+_semilla(i, 3)*24, (240, 210, 167), 27)

    def _fuente(self, p, t):
        """Subrayado de consulta: también legible en una franja de 16 píxeles.

        El grosor en coordenadas del lienzo compensa el formato muy bajo de la
        franja. No representa una valoración de la fuente ni una recompensa.
        """
        azul = (153, 208, 211)
        y = 350
        p.setPen(_pluma(azul, 65, 19))
        p.drawLine(QPointF(16, y), QPointF(1264, y))
        avance = _suave(t / 1.6)
        x = 16 + avance * 1248
        gradiente = QLinearGradient(x-200, 0, x+50, 0)
        gradiente.setColorAt(0, _color(azul, 0))
        gradiente.setColorAt(.8, _color(azul, 180))
        gradiente.setColorAt(1, _color(azul, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(gradiente)
        p.drawRoundedRect(QRectF(max(16, x-200), y-23, min(250, x), 46), 20, 20)
        for i in range(6):
            px = 60+i*230
            brillo = max(0, 1-abs(x-px)/130)
            p.setBrush(_color((231, 204, 155), 150*brillo))
            p.drawEllipse(QPointF(px, y), 5+brillo*3, 30+brillo*42)
