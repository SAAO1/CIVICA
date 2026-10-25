"""Fondos cinematográficos en tiempo real, sin dependencias ni vídeo remoto.

``FondoVivo(parent)`` se coloca detrás de los controles y recibe
``establecer_escena(ruta, ambiente="ciudad", intensidad=1.0)``. Conserva el recorte
de la ilustración original y anima objetos independientes en coordenadas de esa
ilustración: agua de las fuentes, brisa, aves, polvo iluminado, vapor y lluvia.

Ambientes: ciudad/plaza, portada/atardecer, cafe_exterior, cafe/cafe_interior,
telefono, investigacion/oficina, observatorio, lluvia, cafe_lluvia,
noche/plaza_noche y parque/parque_tarde. Los alias se deducen
también de la ruta, para que «plaza» no ponga agua sobre un café.

``configurar(reducir_movimiento=True)`` conserva un fotograma quieto y detiene
el temporizador. ``configurar(activo=False)`` pausa sin saltos al reanudar. El
temporizador sólo corre si el widget es visible. Para exportar o comprobar una
escena: ``capturar_fotograma(segundos=2.0, tamano=(1280, 720))`` devuelve QImage;
``establecer_tiempo(2.0)`` fija el reloj y ``establecer_tiempo(None)`` lo libera.
No se modifica ningún recurso artístico ni se estiran edificios/personas.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import time

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from PyQt6.QtGui import (QColor, QImage, QLinearGradient, QPainter,
                         QPainterPath, QPen, QPixmap, QRadialGradient)
from PyQt6.QtWidgets import QWidget

from recursos import pixmap_recurso


TAU = math.tau
FPS_AMBIENTE = 30


@dataclass(frozen=True)
class PerfilAmbiente:
    exterior: bool = False
    cielo: tuple[float, float, float, float] = (0, 0, 0, 0)
    hojas: int = 0
    motas: int = 18
    calidez: float = .4
    fuente: tuple[float, float, float, float] | None = None
    vapor: tuple[tuple[float, float], ...] = ()
    lamparas: tuple[tuple[float, float, float], ...] = ()
    nocturno: bool = False
    region_lluvia: tuple[float, float, float, float] | None = None


PERFILES = {
    "ciudad": PerfilAmbiente(True, (.28, 0, .65, .22), 15, 14, .35,
                              (.512, .58, .091, .108)),
    "portada": PerfilAmbiente(True, (.36, 0, .28, .38), 16, 23, .9,
                               (.903, .70, .12, .11),
                               lamparas=((.067, .34, .026), (.13, .52, .015))),
    "cafe_exterior": PerfilAmbiente(True, (.66, 0, .17, .20), 18, 18, .65,
                                     vapor=((.098, .584), (.315, .59)),
                                     lamparas=((.165, .365, .02), (.93, .11, .028))),
    "cafe": PerfilAmbiente(False, motas=34, calidez=.85,
                           vapor=((.845, .461), (.047, .453)),
                           lamparas=((.024, .101, .029), (.192, .174, .024),
                                     (.32, .197, .023), (.589, .17, .025),
                                     (.92, .072, .034))),
    "telefono": PerfilAmbiente(True, (.52, 0, .30, .14), 7, 9, .8,
                               vapor=((.078, .674),),
                               lamparas=((.937, .303, .023), (.497, .364, .013))),
    "investigacion": PerfilAmbiente(False, motas=29, calidez=.7,
                                    lamparas=((.956, .479, .035),)),
    "observatorio": PerfilAmbiente(False, motas=14, calidez=.65,
                                    lamparas=((.155, .24, .031), (.937, .25, .031))),
    "lluvia": PerfilAmbiente(True, (.28, 0, .65, .22), 4, 0, .15,
                             region_lluvia=(0, 0, 1, 1)),
    "cafe_lluvia": PerfilAmbiente(False, motas=18, calidez=.75,
                                  vapor=((.845, .461), (.047, .453)),
                                  lamparas=((.024, .101, .029), (.192, .174, .024),
                                            (.32, .197, .023), (.589, .17, .025),
                                            (.92, .072, .034)),
                                  region_lluvia=(.56, .0, .44, .48)),
    "noche": PerfilAmbiente(True, (.31, 0, .46, .20), 10, 12, .25,
                            fuente=(.512, .58, .091, .108),
                            lamparas=((.062, .29, .037), (.094, .31, .03),
                                      (.17, .38, .023), (.916, .32, .035),
                                      (.961, .25, .038)),
                            nocturno=True),
    "parque": PerfilAmbiente(True, (.31, 0, .46, .2), 24, 22, .85,
                             fuente=(.517, .594, .090, .095)),
    "estudio": PerfilAmbiente(False, motas=20, calidez=.7,
                              lamparas=((.17, .29, .065), (.81, .18, .028))),
    "debate": PerfilAmbiente(False, motas=14, calidez=.35,
                             lamparas=((.2, .08, .042), (.4, .08, .042),
                                       (.6, .08, .042), (.8, .08, .042))),
    "redaccion": PerfilAmbiente(False, motas=17, calidez=.3, nocturno=True,
                                lamparas=((.74, .39, .035),),
                                region_lluvia=(.05, .02, .7, .45)),
    "urnas": PerfilAmbiente(True, (.02, .0, .4, .3), 7, 19, .75),
}


def _fraccion(numero: float) -> float:
    return numero - math.floor(numero)


def _semilla(indice: int, canal: int = 0) -> float:
    """Ruido estable por objeto: capturas y partidas reproducibles."""
    return _fraccion(math.sin(indice * 127.1 + canal * 311.7 + 8.13) * 43758.5453)


def _color(r, g, b, alfa):
    return QColor(r, g, b, max(0, min(255, round(alfa))))


def _perfil(ruta: str, ambiente: str) -> str:
    nombre = str(ruta).lower().replace("\\", "/")
    if "/siete_actos/" in nombre:
        for clave in ("estudio", "debate", "redaccion", "urnas"):
            if clave in nombre:
                return clave
    if ambiente == "lluvia":
        return "lluvia"
    for patron, clave in (("portada", "portada"), ("escena 2", "cafe_exterior"),
                          ("cafe_lluvia", "cafe_lluvia"),
                          ("plaza_noche", "noche"), ("parque_tarde", "parque"),
                          ("cafe_exterior", "cafe_exterior"),
                          ("telefono", "telefono"), ("escena 3", "telefono"),
                          ("cafe_interior", "cafe"), ("escena 4", "cafe"),
                          ("escena 5", "cafe"), ("escena 8", "cafe"),
                          ("investigacion", "investigacion"),
                          ("escena 6", "investigacion"), ("escena 7", "investigacion"),
                          ("observatorio", "observatorio"), ("escena arbol", "observatorio")):
        if patron in nombre:
            return clave
    alias = {"plaza": "ciudad", "atardecer": "portada", "oficina": "investigacion",
             "cafe_interior": "cafe", "plaza_noche": "noche", "parque_tarde": "parque"}
    clave = alias.get(ambiente, ambiente)
    return clave if clave in PERFILES else "ciudad"


class FondoVivo(QWidget):
    """Lienzo decorativo ligero. No roba clics ni foco a la novela."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAccessibleName("Ambientación de la escena")
        self._ruta = ""
        self._pixmap = QPixmap()
        self._ambiente = "ciudad"
        self._intensidad = 1.0
        self._reducir_movimiento = False
        self._activo = True
        self._presentado = False
        self._tiempo_fijo = None
        self._transcurrido = 0.0
        self._inicio = None
        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.setInterval(math.ceil(1000 / FPS_AMBIENTE))
        self._timer.timeout.connect(self.update)
        # El arte escalado se reutiliza: un QPainter no interpola 2MP cada tick.
        self._cache_arte = None
        self._cache_clave = None

    @property
    def ambiente(self):
        return self._ambiente

    @property
    def animando(self):
        return self._timer.isActive()

    def establecer_escena(self, ruta, ambiente="ciudad", intensidad=1.0):
        """Carga el fondo local y reinicia sus ciclos sólo cuando cambia."""
        ruta = str(ruta)
        try:
            intensidad = float(intensidad)
        except (TypeError, ValueError):
            intensidad = 1.0
        if not math.isfinite(intensidad):
            intensidad = 1.0
        intensidad = max(0.0, min(2.0, intensidad))
        nuevo = _perfil(ruta, str(ambiente).lower())
        if (ruta, nuevo) != (self._ruta, self._ambiente):
            self._ruta, self._ambiente = ruta, nuevo
            self._pixmap = pixmap_recurso(ruta)
            self._cache_clave = None
            self._cache_arte = None
            self._transcurrido = 0.0
            self._inicio = time.monotonic() if self._timer.isActive() else None
        self._intensidad = intensidad
        self._sincronizar_reloj()
        self.update()

    def configurar(self, reducir_movimiento=None, activo=None):
        """Pausa accesible o por escena, sin perder la posición del reloj."""
        if reducir_movimiento is not None:
            self._reducir_movimiento = bool(reducir_movimiento)
        if activo is not None:
            self._activo = bool(activo)
        self._sincronizar_reloj()
        self.update()

    def establecer_tiempo(self, segundos=None):
        """Fija un instante sin esperar al reloj; None devuelve el control al reloj."""
        if segundos is None:
            self._tiempo_fijo = None
        else:
            segundos = float(segundos)
            if not math.isfinite(segundos):
                raise ValueError("El tiempo debe ser finito")
            self._tiempo_fijo = max(0.0, segundos)
        self._sincronizar_reloj()
        self.update()

    def tiempo_actual(self):
        if self._tiempo_fijo is not None:
            return self._tiempo_fijo
        if self._reducir_movimiento:
            return 0.0
        return self._transcurrido + (time.monotonic() - self._inicio if self._inicio else 0)

    def _sincronizar_reloj(self):
        debe = (self._presentado and self.isVisible() and self._activo and not self._reducir_movimiento
                and self._tiempo_fijo is None and self._intensidad > 0)
        if debe and not self._timer.isActive():
            self._inicio = time.monotonic()
            self._timer.start()
        elif not debe and self._timer.isActive():
            self._transcurrido += time.monotonic() - self._inicio
            self._inicio = None
            self._timer.stop()

    def showEvent(self, evento):
        self._presentado = True
        super().showEvent(evento)
        self._sincronizar_reloj()

    def hideEvent(self, evento):
        # Un Hide espontáneo al minimizar puede conservar isVisible() == True.
        self._presentado = False
        self._sincronizar_reloj()
        super().hideEvent(evento)

    def closeEvent(self, evento):
        self._activo = False
        self._sincronizar_reloj()
        super().closeEvent(evento)

    def resizeEvent(self, evento):
        self._cache_clave = None
        super().resizeEvent(evento)

    def capturar_fotograma(self, segundos=None, tamano=None):
        """Renderiza sin mutar visibilidad, reproducción ni preferencias."""
        if tamano is None:
            tamano = self.size()
        elif not isinstance(tamano, QSize):
            tamano = QSize(*tamano)
        imagen = QImage(tamano, QImage.Format.Format_ARGB32_Premultiplied)
        imagen.fill(QColor("#172b3b"))
        pintor = QPainter(imagen)
        instante = self.tiempo_actual() if segundos is None else max(0, float(segundos))
        self._dibujar(pintor, QRectF(imagen.rect()), instante)
        pintor.end()
        return imagen

    def paintEvent(self, evento):
        pintor = QPainter(self)
        self._dibujar(pintor, QRectF(self.rect()), self.tiempo_actual())
        pintor.end()

    def _dibujar(self, p, destino, t):
        if destino.width() <= 0 or destino.height() <= 0:
            return
        p.fillRect(destino, QColor("#172b3b"))
        if self._pixmap.isNull():
            return
        p.save()
        p.setClipRect(destino)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Toda geometría artística usa el lienzo 1672x941, con recorte cover.
        factor = max(destino.width()/1672, destino.height()/941)
        intensidad = self._intensidad if not self._reducir_movimiento else 0
        zoom = 1.018 + .0035 * math.sin(t * TAU / 26) * intensidad
        dx = 3.3 * math.sin(t * TAU / 32) * intensidad
        dy = 2.2 * math.sin(t * TAU / 24) * intensidad
        p.translate(destino.center().x() + dx, destino.center().y() + dy)
        p.scale(factor * zoom, factor * zoom)
        p.translate(-836, -470.5)
        # Cache por resolución de salida. Se desplaza la superficie, no sus píxeles.
        objetivo = QSize(max(1, round(1672 * factor * 1.025)),
                         max(1, round(941 * factor * 1.025)))
        clave = (objetivo.width(), objetivo.height(), self._pixmap.cacheKey())
        if clave != self._cache_clave:
            self._cache_arte = self._pixmap.scaled(
                objetivo, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation)
            self._cache_clave = clave
        ancho = min(self._cache_arte.width(), self._cache_arte.height()*1672/941)
        alto = ancho * 941/1672
        origen = QRectF((self._cache_arte.width()-ancho)/2,
                        (self._cache_arte.height()-alto)/2, ancho, alto)
        p.drawPixmap(QRectF(0, 0, 1672, 941), self._cache_arte,
                     origen)
        perfil = PERFILES[self._ambiente]
        # En modo accesible sólo queda la ilustración, sin objetos superpuestos.
        if intensidad > 0:
            self._luz(p, t, perfil, intensidad)
            if perfil.exterior:
                self._brisa(p, t, perfil, intensidad)
            self._motas(p, t, perfil, intensidad)
            if perfil.fuente:
                self._fuente(p, t, perfil.fuente, intensidad)
            for i, origen in enumerate(perfil.vapor):
                self._vapor(p, t + i * 1.2, origen, intensidad)
            if perfil.nocturno:
                self._luciernagas(p, t, intensidad)
                self._reflejos(p, t, intensidad)
            if perfil.region_lluvia:
                self._lluvia(p, t, intensidad, perfil)
        p.restore()

    def _luz(self, p, t, perfil, intensidad):
        # Variaciones de luz lentas y continuas; no hay destellos ni parpadeos.
        if not perfil.exterior:
            desplazamiento = 32 * math.sin(t * TAU / 38)
            rayo = QPainterPath()
            rayo.moveTo(1130 + desplazamiento, -50)
            rayo.lineTo(1460 + desplazamiento, -50)
            rayo.lineTo(790 + desplazamiento, 941)
            rayo.lineTo(420 + desplazamiento, 941)
            rayo.closeSubpath()
            luz = QLinearGradient(1300, 0, 600, 900)
            luz.setColorAt(0, _color(255, 228, 178, 5 * intensidad))
            luz.setColorAt(.55, _color(255, 229, 185, 10 * intensidad))
            luz.setColorAt(1, QColor(255, 229, 185, 0))
            p.fillPath(rayo, luz)
        for i, (x, y, radio) in enumerate(perfil.lamparas):
            r = radio * 1672
            brillo = (10 + 2.5 * math.sin(t * .48 + i * 1.4)) * intensidad
            luz = QRadialGradient(QPointF(x*1672, y*941), r * 2.4)
            luz.setColorAt(0, _color(255, 217, 142, brillo))
            luz.setColorAt(.5, _color(255, 194, 96, brillo * .6))
            luz.setColorAt(1, QColor(255, 180, 90, 0))
            p.fillRect(QRectF(x*1672-r*2.4, y*941-r*2.4, r*4.8, r*4.8), luz)

    def _brisa(self, p, t, perfil, intensidad):
        # Nubes translúcidas confinadas al cielo libre de cada ilustración.
        x, y, w, h = perfil.cielo
        if w:
            p.save()
            p.setClipRect(QRectF(x*1672, y*941, w*1672, h*941))
            for i in range(3):
                cx = x*1672 + _fraccion(_semilla(i, 0) + t*.005) * w*1672
                cy = (y + h * (.2 + .3*_semilla(i, 1))) * 941
                nube = QRadialGradient(QPointF(cx, cy), 160 + i*32)
                nube.setColorAt(0, _color(255, 244, 218, 9*intensidad))
                nube.setColorAt(1, QColor(255, 244, 218, 0))
                p.fillRect(QRectF(cx-225, cy-225, 450, 450), nube)
            # Aves muy lejanas; ciclos de 24s con entrada/salida fuera del cielo.
            for i in range(0 if perfil.nocturno else 4):
                avance = _fraccion(t / 27 + i * .032)
                bx = x*1672 - 50 + avance * (w*1672 + 120)
                by = (y + h * (.23 + i*.10)) * 941 + 5*math.sin(t*.42+i)
                ala = 1.2 + 2.8*math.sin(t*6.0+i)
                p.setPen(QPen(_color(40, 57, 59, 108*intensidad), 1.2))
                ave = QPainterPath(QPointF(bx-5, by-ala))
                ave.quadTo(bx-2, by-2, bx, by)
                ave.quadTo(bx+2, by-2, bx+5, by-ala)
                p.drawPath(ave)
            p.restore()
        # Cada hoja tiene su caída, giro, profundidad y ráfaga independiente.
        for i in range(perfil.hojas):
            profundidad = .35 + .8*_semilla(i, 3)
            caida = _fraccion(_semilla(i, 2) + t * (.019 + .012*profundidad))
            x = _fraccion(_semilla(i, 1) + t*.012*profundidad)*1872 - 100
            x += math.sin(t*(.5 + .1*profundidad) + i)*30*profundidad
            y = -70 + caida*1100
            # Teléfono: mantener el objeto central despejado.
            if self._ambiente == "telefono" and 750 < x < 1300:
                continue
            p.save()
            p.translate(x, y)
            p.rotate(t * (22+12*profundidad) + i*83)
            lado = (3.4 + 3.6*profundidad)
            p.scale(1, .22 + .78*abs(math.sin(t*1.3+i)))
            hoja = QPainterPath(QPointF(-lado, 0))
            hoja.cubicTo(-lado*.3, -lado*.65, lado*.5, -lado*.4, lado, 0)
            hoja.cubicTo(lado*.2, lado*.5, -lado*.2, lado*.55, -lado, 0)
            tono = _semilla(i, 4)
            p.fillPath(hoja, _color(137+round(42*tono), 135+round(22*tono), 58,
                                    (90+80*profundidad)*intensidad))
            p.setPen(QPen(_color(88, 100, 39, 75*intensidad), .65))
            p.drawLine(QPointF(-lado*.7, 0), QPointF(lado*.65, 0))
            p.restore()

    def _motas(self, p, t, perfil, intensidad):
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(perfil.motas):
            z = .3 + _semilla(i, 2)
            x = _fraccion(_semilla(i, 0) + t * .0025*z)*1672
            y = _fraccion(_semilla(i, 1) - t * .006*z)*941
            x += math.sin(t*.7+i)*9*z
            visible = .35 + .65*(.5+.5*math.sin(t*.55+i))
            if not perfil.exterior:
                # Mayor visibilidad en el haz de la ventana, no confeti.
                visible *= max(.12, 1-abs(x-1050)/650)
            p.setBrush(_color(255, 235, 193, (30+32*z)*visible*intensidad))
            radio = .6 + z*.7
            p.drawEllipse(QPointF(x, y), radio, radio)

    def _fuente(self, p, t, geometria, intensidad):
        cx, cy, radio, altura = geometria
        cx, cy, radio, altura = cx*1672, cy*941, radio*1672, altura*941
        p.save()
        # Filamentos de agua y gotas siguen trayectorias, sin mover la piedra.
        for i in range(27):
            fase = _semilla(i, 0)
            lado = -1 if i % 2 else 1
            apertura = (.22+.72*_semilla(i, 1)) * radio
            inicio = QPointF(cx + math.sin(i)*radio*.12, cy-altura*.44)
            fin = QPointF(cx+lado*apertura, cy+altura*.38)
            trayectoria = QPainterPath(inicio)
            trayectoria.cubicTo(cx+lado*apertura*.42, cy-altura*1.05,
                                  fin.x(), cy-altura*.18, fin.x(), fin.y())
            pluma = QPen(_color(235, 246, 237, (28+28*fase)*intensidad),
                         .6 + .55*fase)
            pluma.setStyle(Qt.PenStyle.CustomDashLine)
            pluma.setDashPattern([3.0+fase*4, 3.0+fase*7])
            pluma.setDashOffset(-t*(16+fase*9))
            p.setPen(pluma)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(trayectoria)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(_color(250, 252, 232, 105*intensidad))
            punto = trayectoria.pointAtPercent(_fraccion(t*(.36+.16*fase)+fase))
            p.drawEllipse(punto, .8+fase*.55, 1.3+fase*.7)
        for i in range(9):
            progreso = _fraccion(t*.45 + i/9)
            x = cx + (i-4) * radio*.19
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(_color(228, 247, 240, (1-progreso)*26*intensidad), .7))
            p.drawEllipse(QPointF(x, cy+altura*.43), 2+progreso*11, 1+progreso*2)
        p.restore()

    def _vapor(self, p, t, origen, intensidad):
        x, y = origen[0]*1672, origen[1]*941
        p.save()
        p.setBrush(Qt.BrushStyle.NoBrush)
        for i in range(4):
            edad = _fraccion(t*.19+i*.25)
            altura = edad*64
            opacidad = math.sin(edad*math.pi)*23*intensidad
            curva = QPainterPath(QPointF(x+math.sin(t*.8+i)*3, y-altura))
            curva.cubicTo(x-5+math.sin(t+i)*6, y-altura-10,
                          x+12+math.cos(t*.7+i)*5, y-altura-22,
                          x+math.sin(t*.6+i)*9, y-altura-33)
            p.setPen(QPen(_color(255, 249, 226, opacidad), 2.2+edad*2.7,
                          Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawPath(curva)
        p.restore()

    def _luciernagas(self, p, t, intensidad):
        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(14):
            x = _semilla(i, 1)*1672 + 19*math.sin(t*.35+i)
            y = 340 + _semilla(i, 2)*330 + 13*math.cos(t*.46+i*2)
            brillo = (.5 + .5*math.sin(t*.8+i*1.7))**3
            halo = QRadialGradient(QPointF(x, y), 6)
            halo.setColorAt(0, _color(255, 232, 140, 135*brillo*intensidad))
            halo.setColorAt(.25, _color(232, 216, 130, 55*brillo*intensidad))
            halo.setColorAt(1, QColor(232, 216, 130, 0))
            p.fillRect(QRectF(x-6, y-6, 12, 12), halo)
        p.restore()

    def _lluvia(self, p, t, intensidad, perfil):
        p.save()
        x0, y0, ancho, alto = perfil.region_lluvia
        region = QRectF(x0*1672, y0*941, ancho*1672, alto*941)
        p.setClipRect(region)
        if self._ambiente == "cafe_lluvia":
            ventanas = QPainterPath()
            for x, y, w, h in ((.557, .13, .067, .35), (.659, 0, .071, .397),
                                (.744, 0, .081, .39), (.858, 0, .142, .34)):
                ventanas.addRect(QRectF(x*1672, y*941, w*1672, h*941))
            p.setClipPath(ventanas, Qt.ClipOperation.IntersectClip)
        if perfil.exterior:
            p.fillRect(region, QColor(26, 48, 65, 32))
        for i in range(145):
            z = .4 + .8*_semilla(i, 2)
            x = _fraccion(_semilla(i, 0) - t*.08*z)*1800 - 60
            y = _fraccion(_semilla(i, 1) + t*.9*z)*1100 - 80
            p.setPen(QPen(_color(192, 219, 232, (22+31*z)*intensidad), .6+.6*z))
            p.drawLine(QPointF(x, y), QPointF(x-6*z, y+24*z))
        for i in range(22 if perfil.exterior else 0):
            fase = _fraccion(t*.8+_semilla(i))
            x = _semilla(i, 3)*1672
            y = 690+_semilla(i, 4)*251
            p.setPen(QPen(_color(197, 225, 233, 40*(1-fase)*intensidad), .7))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(x, y), 2+fase*13, 1+fase*3)
        p.restore()

    def _reflejos(self, p, t, intensidad):
        """Ondulación luminosa sobre el suelo húmedo, sin desplazar baldosas."""
        p.save()
        p.setBrush(Qt.BrushStyle.NoBrush)
        for i, x in enumerate((.062, .094, .17, .39, .49, .54, .72, .916, .961)):
            for j in range(3):
                y = 675 + j*65
                centro = x*1672 + 3*math.sin(t*.7+i+j)
                radio = (4+j*4) * (.75 + .25*math.sin(t*.8+i))
                reflejo = QPainterPath(QPointF(centro-radio, y))
                reflejo.quadTo(centro, y+2*math.sin(t+i), centro+radio, y)
                p.setPen(QPen(_color(255, 203, 115, (7-j)*intensidad), 2+j))
                p.drawPath(reflejo)
        p.restore()
