"""Planos narrativos exportables: ilustración, objetos y cámara independientes.

El juego reproduce MP4 locales; este módulo es la mesa de animación que los
produce. No necesita Internet ni bibliotecas de vídeo. Los objetos añadidos son
reconstrucciones gráficas del relato, nunca documentos o resultados reales.
``RenderizadorCinematica(clave).capturar_fotograma(t, (1280, 720))`` devuelve
un QImage y permite comprobar/exportar exactamente la misma puesta en escena.
"""
from __future__ import annotations

from collections import OrderedDict
import math
from pathlib import Path

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (QColor, QFont, QFontDatabase, QImage, QLinearGradient,
                         QPainter, QPainterPath, QPen, QRadialGradient)

RAIZ = Path(__file__).resolve().parent
CARPETA = RAIZ / "assets/expansion/cinematica"
DURACION = 12.0
FPS = 24

# Las claves son estables y coinciden con el catálogo de disparadores narrativos.
CLIPS = {
    "ciudad_48h": dict(titulo="Cuarenta y ocho horas", arte="", fondo="portada_ciudad",
                       tipo="reloj", ambiente="tarde"),
    "mensaje_barrio": dict(titulo="Un mensaje recorre el barrio", arte="", fondo="telefono",
                           tipo="red", ambiente="tarde"),
    "rumor_colegio": dict(titulo="El rumor del colegio", arte="colegio", fondo="telefono",
                          tipo="colegio", ambiente="tarde"),
    "cafe_alerta": dict(titulo="La primera alerta", arte="colegio", fondo="cafe_exterior",
                        tipo="cafe", ambiente="tarde"),
    "libreta_cultura": dict(titulo="Las preguntas de la periodista", arte="libreta", fondo="cafe_interior",
                            tipo="libreta", ambiente="interior"),
    "mapa_parque": dict(titulo="El camino del parque", arte="mapa", fondo="investigacion",
                        tipo="mapa", ambiente="tarde"),
    "libro_biblioteca": dict(titulo="La memoria de un libro", arte="libro", fondo="investigacion",
                             tipo="libro", ambiente="interior"),
    "acusacion_lluvia": dict(titulo="Una acusación bajo la lluvia", arte="acusacion", fondo="cafe_interior",
                             tipo="lluvia", ambiente="lluvia"),
    "noche_electoral": dict(titulo="La decisión sigue en las urnas", arte="urna", fondo="ciudad",
                            tipo="urna", ambiente="noche"),
}

# Las intervenciones de los personajes tienen montaje propio: situación
# humana, objeto del relato y regreso al contexto. Las pinturas no presentan
# una acusación como un hecho ni una propuesta como una obra ya construida.
_IL = "assets/expansion/cinematica/ilustraciones/"
_FO = "assets/rediseno/fondos/"
_EX = "assets/expansion/fondos/"
_PLANOS_PERSONAJES = {
    "colegio_c": ("Mi hermana y el colegio", (_IL+"hermana_parque.jpg", _IL+"colegio.jpg", _IL+"hermana_parque.jpg"), "familia_colegio", "tarde"),
    "colegio_p": ("Buscar el comunicado completo", (_IL+"periodista_calle.jpg", _IL+"libreta.jpg", _IL+"colegio.jpg"), "comunicado", "tarde"),
    "cultura_c": ("Un lugar para leer", (_IL+"familia.jpg", _IL+"libro.jpg", _IL+"familia.jpg"), "lectura", "interior"),
    "cultura_p": ("Preguntas para una propuesta", (_IL+"periodista_calle.jpg", _IL+"libreta.jpg", _FO+"investigacion.png"), "propuesta", "interior"),
    "parque_c": ("El camino al colegio", (_IL+"hermana_parque.jpg", _IL+"mapa.jpg", _EX+"parque_tarde.png"), "camino", "tarde"),
    "parque_p": ("Fechas y zonas del aviso", (_IL+"periodista_calle.jpg", _IL+"mapa.jpg", _EX+"parque_tarde.png"), "zonas", "tarde"),
    "biblioteca_c": ("El libro de mi abuelo", (_IL+"familia.jpg", _IL+"libro.jpg", _FO+"investigacion.png"), "memoria", "interior"),
    "biblioteca_p": ("De un anuncio a una obra", (_IL+"periodista_calle.jpg", _IL+"libro.jpg", _IL+"libreta.jpg"), "etapas", "interior"),
    "acusacion_c": ("Todo el mundo lo dice", (_FO+"telefono.png", _IL+"acusacion.jpg", _EX+"cafe_lluvia.png"), "grupos", "lluvia"),
    "acusacion_p": ("La prisa no es una fuente", (_IL+"periodista_calle.jpg", _IL+"acusacion.jpg", _IL+"libreta.jpg"), "contrastar", "lluvia"),
    "voto_c": ("Conversar antes de votar", (_IL+"familia.jpg", _IL+"urna.jpg", _EX+"plaza_noche.png"), "participar", "noche"),
    "voto_p": ("Las piezas de una encuesta", (_IL+"periodista_calle.jpg", _IL+"urna.jpg", _IL+"libreta.jpg"), "metodo", "noche"),
}
for _clave, (_titulo, _planos, _tema, _ambiente) in _PLANOS_PERSONAJES.items():
    CLIPS["person_"+_clave] = dict(titulo=_titulo, planos=_planos,
                                  tipo="persona", tema=_tema, ambiente=_ambiente)

_FUENTES_CARGADAS = False


def _suave(x):
    x = max(0.0, min(1.0, x))
    return x*x*(3-2*x)


def _rango(t, inicio, fin):
    return _suave((t-inicio)/max(.01, fin-inicio))


def _azar(n, canal=0):
    a = math.sin(n*127.1+canal*311.7+8.13)*43758.5453
    return a-math.floor(a)


def _color(c, alfa=255):
    color = QColor(c)
    color.setAlpha(round(max(0, min(255, alfa))))
    return color


def _fuente(tamano, negrita=False):
    global _FUENTES_CARGADAS
    if not _FUENTES_CARGADAS:
        for nombre in ("Regular", "Bold"):
            QFontDatabase.addApplicationFont(str(RAIZ / f"assets/fuentes/AtkinsonHyperlegible-{nombre}.ttf"))
        _FUENTES_CARGADAS = True
    f = QFont("Atkinson Hyperlegible")
    f.setPixelSize(tamano)
    f.setBold(negrita)
    return f


class RenderizadorCinematica:
    """Caché acotada a dos ilustraciones; el tiempo es completamente determinista."""

    def __init__(self, clave):
        if clave not in CLIPS:
            raise ValueError(f"Cinemática desconocida: {clave}")
        self.clave = clave
        self.ficha = CLIPS[clave]
        self._imagenes = OrderedDict()
        self._claves_pantalla_telefono = set()

    @property
    def fuentes(self):
        if "planos" in self.ficha:
            # Mantener el orden de montaje y eliminar duplicados del inventario.
            return list(dict.fromkeys(RAIZ / ruta for ruta in self.ficha["planos"]))
        arte = self.ficha["arte"]
        rutas = []
        if arte:
            ruta = CARPETA / f"ilustraciones/{arte}.jpg"
            if ruta.is_file():
                rutas.append(ruta)
        fallback = RAIZ / f"assets/rediseno/fondos/{self.ficha['fondo']}.png"
        if self.clave == "acusacion_lluvia":
            fallback = RAIZ / "assets/expansion/fondos/cafe_lluvia.png"
        elif self.clave == "noche_electoral":
            fallback = RAIZ / "assets/expansion/fondos/plaza_noche.png"
        if fallback.is_file():
            rutas.append(fallback)
        return rutas

    def _imagen(self, ruta):
        clave = str(ruta)
        if clave not in self._imagenes:
            img = QImage(clave)
            if img.isNull():
                raise FileNotFoundError(f"No se pudo cargar {ruta}")
            self._imagenes[clave] = img
            while len(self._imagenes) > 2:
                self._imagenes.popitem(last=False)
        self._imagenes.move_to_end(clave)
        if Path(ruta).name == "telefono.png":
            self._claves_pantalla_telefono.add(self._imagenes[clave].cacheKey())
        return self._imagenes[clave]

    def _recorte(self, img, t, encuadre, inserto=False):
        # Tres planos con puntos de interés distintos y corte por disolución.
        planos = ((.51, .43, 1.035), (.66, .40, 1.18), (.43, .41, 1.10))
        if inserto and (self.ficha["tipo"] in ("libreta", "mapa", "libro", "urna")
                        or self.ficha.get("tema") in ("lectura", "propuesta", "camino", "zonas", "memoria", "etapas", "participar", "metodo")):
            # Los objetos están sobre una mesa. Acercarse también baja la
            # cámara, llevándolos al área que dejan libre los subtítulos.
            planos = ((.51, .55, 1.035), (.52, .78, 1.36), (.56, .70, 1.23))
        cx, cy, zoom = planos[encuadre]
        zoom += .025*math.sin((t/4)*math.pi/2)
        sw = img.width()/zoom
        sh = sw*720/1280
        if sh > img.height():
            sh = img.height()/zoom
            sw = sh*1280/720
        x = max(0, min(img.width()-sw, img.width()*cx-sw/2))
        y = max(0, min(img.height()-sh, img.height()*cy-sh/2))
        return QRectF(x, y, sw, sh)

    def _plano(self, p, img, t, encuadre, alfa=1.0, inserto=False):
        recorte = self._recorte(img, t, encuadre, inserto)
        p.save()
        p.setOpacity(alfa)
        p.drawImage(QRectF(0, 0, 1280, 720), img, recorte)
        if img.cacheKey() in self._claves_pantalla_telefono:
            from cine_telefono import pintar_en_foto
            from juego.cinematica import CINEMATICAS
            identificador = CINEMATICAS.get(self.clave, {}).get("publicacion") or 50
            pintar_en_foto(p, img, recorte, identificador)
        p.restore()

    def _punto_inserto(self, x, y, t):
        ruta = (RAIZ / self.ficha["planos"][min(2, int(t//4))]
                if "planos" in self.ficha else self.fuentes[0])
        imagen = self._imagen(ruta)
        recorte = self._recorte(imagen, t, min(2, int(t//4)), True)
        return ((imagen.width()*x-recorte.x())*1280/recorte.width(),
                (imagen.height()*y-recorte.y())*720/recorte.height())

    def _fondo(self, p, t):
        if "planos" in self.ficha:
            return self._fondo_personaje(p, t)
        rutas = self.fuentes
        if not rutas:
            p.fillRect(0, 0, 1280, 720, QColor("#203649"))
            return
        # En clips con pinturas nuevas, el inicio sitúa el lugar y el inserto
        # acerca el objeto narrado; después regresamos con el objeto visible.
        tiene_inserto = len(rutas) == 2
        fase = min(2, int(t//4))
        principal = self._imagen(rutas[0])
        entorno = self._imagen(rutas[-1])
        if tiene_inserto:
            mezcla = _rango(t, 2.5, 3.4)*(1-.28*_rango(t, 9.3, 10.5))
            self._plano(p, entorno, t, min(fase, 1))
            self._plano(p, principal, t, fase, mezcla, inserto=True)
        else:
            self._plano(p, principal, t, fase)
            if fase:
                solape = 1-_rango(t % 4, 0, .65)
                self._plano(p, principal, t, fase-1, solape)

    def _fondo_personaje(self, p, t):
        """Tres planos con cambio de pintura, además del movimiento de cámara."""
        rutas = self.ficha["planos"]
        fase = min(2, int(t//4))
        actual = self._imagen(RAIZ / rutas[fase])
        # Las pinturas existentes sitúan sus objetos hacia abajo: el inserto
        # los sube al espacio visible entre la cabecera y el diálogo.
        objeto = fase == 1 and self.ficha["tema"] not in ("familia_colegio", "grupos", "contrastar")
        self._plano(p, actual, t, fase if not objeto else 1, inserto=objeto)
        if fase and t % 4 < .7:
            anterior = self._imagen(RAIZ / rutas[fase-1])
            self._plano(p, anterior, t, fase-1, 1-_rango(t % 4, 0, .7), inserto=False)

    def _atmosfera(self, p, t):
        ambiente = self.ficha["ambiente"]
        # Iluminación independiente de la cámara y del fondo.
        calor = QColor("#ffdca0") if ambiente != "noche" else QColor("#83baca")
        g = QRadialGradient(QPointF(975+25*math.sin(t*.17), 130), 570)
        g.setColorAt(0, _color(calor, 28+5*math.sin(t*.8)))
        g.setColorAt(1, _color(calor, 0))
        p.fillRect(QRectF(0, 0, 1280, 720), g)
        # Motas, brisa y polvo son objetos, no un filtro fijo sobre la imagen.
        for n in range(37 if ambiente == "interior" else 22):
            x = (_azar(n, 1)*1350+t*(2+_azar(n, 3)*8)) % 1350-35
            y = 35+_azar(n, 2)*420+8*math.sin(t*.5+n)
            a = (32+48*_azar(n, 6))*(.55+.45*math.sin(t*.4+n)**2)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(_color("#f8e6bd", a))
            r = 1+_azar(n, 4)*1.9
            p.drawEllipse(QPointF(x, y), r, r)
        if ambiente in ("tarde", "noche"):
            for n in range(9):
                x = (_azar(n, 7)*1400+t*(8+8*_azar(n, 8))) % 1400-60
                y = 70+_azar(n, 9)*370+16*math.sin(t*.7+n)
                p.save()
                p.translate(x, y)
                p.rotate(math.sin(t*.6+n)*50+25)
                p.setBrush(_color("#b9a174", 105))
                p.drawEllipse(QRectF(-5, -1.8, 10, 3.6))
                p.restore()

    def _rotulo(self, p, texto, t, inicio, x=68, y=84, ancho=650):
        a = _rango(t, inicio, inicio+.65)
        if a <= 0:
            return
        p.save()
        p.setOpacity(a)
        p.translate(0, 12*(1-a))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(_color("#142b37", 217))
        p.drawRoundedRect(QRectF(x, y, ancho, 56), 10, 10)
        p.setBrush(QColor("#e9c68e"))
        p.drawRoundedRect(QRectF(x, y, 4, 56), 2, 2)
        p.setPen(QColor("#fff0d1"))
        p.setFont(_fuente(23, True))
        p.drawText(QRectF(x+22, y+4, ancho-36, 48), Qt.AlignmentFlag.AlignVCenter, texto)
        p.restore()

    def _notificacion(self, p, x, y, a, escala=1, largo=305):
        p.save()
        p.setOpacity(a)
        p.translate(x, y)
        p.scale(escala, escala)
        p.setPen(QPen(_color("#e8bd84", 115), 1))
        p.setBrush(_color("#173442", 221))
        p.drawRoundedRect(QRectF(0, 0, largo, 70), 12, 12)
        p.setPen(QPen(QColor("#e5c18f"), 2))
        p.drawRoundedRect(QRectF(17, 20, 33, 26), 4, 4)
        p.drawLine(QPointF(17, 20), QPointF(33, 33))
        p.drawLine(QPointF(50, 20), QPointF(33, 33))
        p.setPen(QPen(_color("#e8dfc8", 205), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(69, 26), QPointF(largo-28, 26))
        p.setPen(QPen(_color("#e8dfc8", 100), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(69, 42), QPointF(largo-71, 42))
        p.restore()

    def _red(self, p, t, lluvia=False):
        # La difusión ya se explora en el observatorio. Aquí se ve la red
        # social del teléfono, sobre el dispositivo y su publicación real.
        self._rotulo(p, "EN EL GRUPO DEL BARRIO" if not lluvia else "UN MENSAJE SIN CONTRASTAR",
                     t, .2, ancho=465)

    def _reloj(self, p, t):
        c = QPointF(1045, 212)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(_color("#152c39", 176))
        p.drawEllipse(c, 117, 117)
        p.setPen(QPen(_color("#eacb98", 210), 2))
        p.drawEllipse(c, 104, 104)
        for n in range(12):
            a = n*math.tau/12-math.pi/2
            p.setPen(QPen(_color("#efd7ae", 210), 3 if n%3 == 0 else 1.5))
            p.drawLine(QPointF(c.x()+math.cos(a)*87, c.y()+math.sin(a)*87),
                       QPointF(c.x()+math.cos(a)*96, c.y()+math.sin(a)*96))
        # El giro expresa el paso del tiempo, sin falsear un reloj electoral.
        a = -math.pi/2+t*.25
        p.setPen(QPen(QColor("#f7e6c6"), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(c, QPointF(c.x()+math.cos(a)*65, c.y()+math.sin(a)*65))
        p.setPen(QPen(QColor("#d8ac71"), 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(c, QPointF(c.x()+math.cos(a*.21+1)*43, c.y()+math.sin(a*.21+1)*43))
        self._rotulo(p, "48 HORAS PARA ELEGIR", t, .5, x=70, y=100, ancho=420)
        if t > 4:
            for n in range(3):
                a = _rango(t, 4+n, 4.6+n)
                self._notificacion(p, 84+35*n, 205+78*n, .78*a, .92)

    def _colegio(self, p, t):
        self._rotulo(p, "UN RUMOR INQUIETA A LAS FAMILIAS", t, .3, ancho=610)
        self._notificacion(p, 850, 132+math.sin(t*2)*2, _rango(t, 1.5, 2.1)*.9, 1.03)
        if t > 4:
            p.save()
            a = _rango(t, 4, 5)
            p.setOpacity(a)
            p.translate(940, 340+18*(1-a))
            p.rotate(-5+2*math.sin(t*.4))
            p.setBrush(_color("#efe4cb", 230))
            p.setPen(QPen(QColor("#ba9f77"), 2))
            p.drawRoundedRect(QRectF(-116, -96, 232, 192), 5, 5)
            p.setFont(_fuente(18, True))
            p.setPen(QColor("#564d44"))
            p.drawText(QRectF(-100, -65, 200, 76), Qt.AlignmentFlag.AlignCenter, "FALTA EL\nCOMUNICADO")
            for n in range(3):
                p.setPen(QPen(_color("#6d6758", 75), 3))
                p.drawLine(QPointF(-80, 32+n*14), QPointF(80-n*16, 32+n*14))
            p.restore()
        self._rotulo(p, "MENSAJE SIN FUENTE", t, 7.3, x=72, y=389, ancho=390)

    def _cafe(self, p, t):
        self._rotulo(p, "UNA NOTIFICACIÓN INTERRUMPE LA MAÑANA", t, .2, ancho=730)
        # Al acercarnos al colegio, el teléfono pintado toma el relevo del
        # inserto gráfico. Así no aparecen dos teléfonos a la vez ni vapor
        # delante del colegio: cada objeto pertenece a su lugar narrativo.
        presencia = 1-_rango(t, 2.8, 3.7)
        p.save()
        p.setOpacity(presencia)
        # Ondas de una vibración concreta, no parpadeos de toda la pantalla.
        for n in range(3):
            fase = ((t+n*.55) % 2.8)/2.8
            p.setPen(QPen(_color("#f6d09a", (1-fase)*110), 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(1004, 258), 48+fase*80, 76+fase*80)
        p.save()
        p.translate(1004+math.sin(t*25)*1.7*math.exp(-((t%3)*1.7)), 254)
        p.rotate(7)
        from cine_telefono import pintar_telefono
        pintar_telefono(p, -62, -110, 124, 220, 50)
        p.restore()
        p.restore()
        for n in range(3):
            path = QPainterPath()
            x = 166+18*n
            path.moveTo(x, 424)
            for j in range(20):
                k = j/19
                path.lineTo(x+math.sin(k*7+t*1.8+n)*9, 424-k*122)
            p.setPen(QPen(_color("#fff0d5", (50-n*9)*presencia), 2.5))
            p.drawPath(path)

    def _papel(self, p, t, libro=False):
        inicio = _rango(t, 1.2, 2.1)
        # El esquema inicial desaparece al entrar en el objeto pintado;
        # mantener ambos creaba un segundo libro flotando sobre el primero.
        presencia = 1-_rango(t, 2.8, 3.7) if len(self.fuentes) == 2 else 1
        p.save()
        p.setOpacity(.95*inicio*presencia)
        p.translate(847, 268+30*(1-inicio))
        p.rotate(-5+math.sin(t*.3)*.7)
        p.setPen(QPen(_color("#806e55", 180), 1.5))
        grad = QLinearGradient(-260, -160, 220, 190)
        grad.setColorAt(0, QColor("#f3ead5"))
        grad.setColorAt(1, QColor("#d3bf9b"))
        p.setBrush(grad)
        p.drawRoundedRect(QRectF(-268, -153, 536, 308), 7, 7)
        if libro:
            p.setPen(QPen(_color("#715d44", 105), 2))
            p.drawLine(QPointF(0, -143), QPointF(0, 148))
            for lado in (-1, 1):
                for n in range(10):
                    p.setPen(QPen(_color("#5f5549", 68), 2))
                    p.drawLine(QPointF(lado*25, -108+n*22), QPointF(lado*(225-15*(n%3)), -108+n*22))
            # Hoja con silueta y sombra que recorre el libro, una acción real.
            progreso = max(0, min(1, (t-4.0)/3.1))
            if 0 < progreso < 1:
                ancho = 240*math.cos(progreso*math.pi)
                ala = QPainterPath(QPointF(0, -150))
                ala.cubicTo(ancho*.6, -178, ancho, -128, ancho, -102)
                ala.lineTo(ancho, 141)
                ala.cubicTo(ancho*.6, 120, ancho*.3, 140, 0, 150)
                ala.closeSubpath()
                p.setPen(QPen(_color("#a58e6c", 190), 1))
                p.setBrush(QColor("#f1e4c9"))
                p.drawPath(ala)
        else:
            p.setFont(_fuente(26, True))
            p.setPen(QColor("#3e4a4b"))
            p.drawText(QRectF(-232, -125, 455, 36), "LIBRETA DE LA PERIODISTA")
            preguntas = ("¿Qué propone?", "¿Cuándo se realizaría?", "¿Con qué recursos?")
            for n, texto in enumerate(preguntas):
                a = _rango(t, 2.0+n*1.6, 2.6+n*1.6)
                p.setOpacity(.95*inicio*a*presencia)
                p.setFont(_fuente(25))
                p.drawText(QRectF(-230, -58+n*72, 450, 44), texto)
                sub = _rango(t, 2.7+n*1.6, 3.5+n*1.6)
                p.setPen(QPen(QColor("#a66b38"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawLine(QPointF(-230, -14+n*72), QPointF(-230+370*sub, -18+n*72))
                p.setPen(QColor("#3e4a4b"))
            p.setOpacity(.95*inicio*presencia)
        p.restore()
        if len(self.fuentes) == 2 and t > 3.7:
            self._animar_pagina_pintada(p, t, libro)
        self._rotulo(p, "UN LIBRO CONECTA LA HISTORIA" if libro else "ABRIR LA LIBRETA. HACER PREGUNTAS.", t, .2,
                     ancho=580 if libro else 680)

    def _animar_pagina_pintada(self, p, t, libro):
        """La tinta y la hoja siguen las coordenadas del papel en la pintura."""
        punto = lambda x, y: QPointF(*self._punto_inserto(x, y, t))
        if not libro:
            # Subrayados que nacen sobre las notas, con punta en movimiento.
            # No se superpone otra libreta ni se inventa un documento oficial.
            for n, (a, b) in enumerate((((.275, .571), (.428, .549)),
                                       ((.286, .613), (.449, .587)),
                                       ((.301, .654), (.465, .628)))):
                fr = _rango(t, 3.8+n*1.25, 4.8+n*1.25)
                if fr <= 0:
                    continue
                inicio = punto(*a)
                fin = punto(a[0]+(b[0]-a[0])*fr, a[1]+(b[1]-a[1])*fr)
                p.setPen(QPen(_color("#6c4930", 185), 2.5,
                              Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawLine(inicio, fin)
                if fr < 1:
                    p.setBrush(QColor("#5b412f"))
                    p.setPen(Qt.PenStyle.NoPen)
                    p.drawEllipse(fin, 2.8, 2.8)
            return
        progreso = _rango(t, 4.0, 7.5)
        if not 0 < progreso < 1:
            return
        # Una hoja gira alrededor del lomo real. Los puntos se calculan en
        # la ilustración antes de aplicar el mismo recorte de cámara.
        arriba = punto(.441, .409)
        abajo = punto(.522, .630)
        exterior_arriba = punto(.617-(.617-.248)*progreso,
                                 .403-.055*math.sin(progreso*math.pi))
        exterior_abajo = punto(.730-(.730-.313)*progreso,
                                .588-.055*math.sin(progreso*math.pi))
        curva = QPainterPath(arriba)
        curva.cubicTo(QPointF((arriba.x()+exterior_arriba.x())/2,
                              arriba.y()-32*math.sin(progreso*math.pi)),
                       exterior_arriba, exterior_arriba)
        curva.lineTo(exterior_abajo)
        curva.cubicTo(exterior_abajo,
                       QPointF((abajo.x()+exterior_abajo.x())/2,
                               abajo.y()-24*math.sin(progreso*math.pi)), abajo)
        curva.closeSubpath()
        p.save()
        p.setOpacity(.92)
        gradiente = QLinearGradient(arriba, exterior_abajo)
        gradiente.setColorAt(0, QColor("#b79a6a"))
        gradiente.setColorAt(.18, QColor("#e7c792"))
        gradiente.setColorAt(1, QColor("#f4dfb8"))
        p.setBrush(gradiente)
        p.setPen(QPen(_color("#aa8756", 185), 1))
        p.drawPath(curva)
        p.restore()

    def _mapa(self, p, t):
        self._rotulo(p, "EL CAMINO QUE USA CADA TARDE", t, .3, ancho=565)
        # Una ruta ilustrativa, sin presentar trazados inventados como evidencia.
        puntos = [(636, 355), (688, 326), (727, 330), (773, 278), (838, 272),
                  (876, 224), (946, 229), (1001, 170), (1110, 157)]
        if len(self.fuentes) == 2:
            # La ruta está fijada al papel y termina junto al dedo pintado;
            # no flota encima de la mano ni se desplaza al cortar de plano.
            puntos = [self._punto_inserto(x, y, t) for x, y in
                      ((.27, .66), (.31, .63), (.34, .59), (.38, .56), (.43, .55),
                       (.48, .58), (.52, .61), (.57, .61), (.61, .60))]
        progreso = _rango(t, 1.8, 7.8)*(len(puntos)-1)
        p.setPen(QPen(_color("#172f36", 150), 11, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        path = QPainterPath(QPointF(*puntos[0]))
        pos = puntos[0]
        for n in range(len(puntos)-1):
            fr = max(0, min(1, progreso-n))
            x, y = puntos[n]
            bx, by = puntos[n+1]
            pos = (x+(bx-x)*fr, y+(by-y)*fr)
            path.lineTo(QPointF(*pos))
            if fr < 1:
                break
        p.drawPath(path)
        p.setPen(QPen(QColor("#f0bf72"), 5, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.drawPath(path)
        p.setPen(QPen(QColor("#fff0c5"), 2))
        p.setBrush(QColor("#ba733e"))
        p.drawEllipse(QPointF(*pos), 10, 10)
        p.setBrush(Qt.BrushStyle.NoBrush)
        a = (t*.9)%1
        p.setPen(QPen(_color("#ffe5b1", 190*(1-a)), 2))
        p.drawEllipse(QPointF(*pos), 12+a*28, 12+a*28)
        self._rotulo(p, "RECONSTRUCCIÓN DEL RECORRIDO", t, 7.9, x=72, y=389, ancho=550)

    def _lluvia(self, p, t):
        # Gotas de vidrio con trayectorias independientes del decorado.
        for n in range(84):
            x = _azar(n, 12)*1280+7*math.sin(t*.5+n)
            y = (_azar(n, 13)*530+t*(22+_azar(n, 14)*42)) % 590-60
            largo = 7+_azar(n, 15)*15
            p.setPen(QPen(_color("#c1dbe0", 35+50*_azar(n, 16)), .8+_azar(n, 17)))
            p.drawLine(QPointF(x, y), QPointF(x-1.8, y+largo))
        self._red(p, t, True)

    def _urna(self, p, t):
        self._rotulo(p, "LA PLAZA SE VACÍA. LA ELECCIÓN SIGUE.", t, .3, ancho=685)
        if t > 2:
            a = _rango(t, 1.5, 2.2)*(1-_rango(t, 2.8, 3.7))
            p.save()
            p.setOpacity(a*.94)
            p.translate(1005, 270)
            p.setPen(QPen(QColor("#e3c799"), 2))
            p.setBrush(_color("#173743", 215))
            p.drawRoundedRect(QRectF(-115, -15, 230, 142), 8, 8)
            p.setBrush(_color("#40606b", 235))
            tapa = QPainterPath(QPointF(-130, -15))
            tapa.lineTo(-105, -48)
            tapa.lineTo(104, -48)
            tapa.lineTo(130, -15)
            tapa.closeSubpath()
            p.drawPath(tapa)
            p.setPen(QPen(QColor("#102633"), 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(-45, -32), QPointF(45, -32))
            cae = _rango(t, 3.2, 6.4)
            if cae < .99:
                p.save()
                p.setClipRect(QRectF(-100, -230, 200, 198))
                p.translate(0, -153+160*cae)
                p.rotate(-8+8*cae)
                p.setBrush(QColor("#eddfc1"))
                p.setPen(QPen(QColor("#b49a73"), 1))
                p.drawRoundedRect(QRectF(-38, -44, 76, 86), 3, 3)
                p.setPen(QPen(QColor("#536768"), 3))
                p.drawLine(QPointF(-13, -5), QPointF(-2, 6))
                p.drawLine(QPointF(-2, 6), QPointF(18, -16))
                p.restore()
            p.setFont(_fuente(19, True))
            p.setPen(QColor("#f5dfb7"))
            p.drawText(QRectF(-105, 45, 210, 50), Qt.AlignmentFlag.AlignCenter, "TU DECISIÓN CUENTA")
            p.restore()
        # Después del inserto gráfico, una papeleta entra en la urna pintada.
        # Su posición sigue el mismo recorte de cámara que la ilustración.
        if t > 3.8 and len(self.fuentes) == 2:
            x, y = self._punto_inserto(.485, .555, t)
            cae = _rango(t, 3.8, 7.2)
            if cae < .999:
                p.save()
                p.setOpacity(_rango(t, 3.8, 4.3))
                p.setClipRect(QRectF(x-100, y-240, 200, 240))
                p.translate(x, y-158+220*cae)
                p.rotate(-7+7*cae)
                p.setPen(QPen(QColor("#bca680"), 1))
                p.setBrush(QColor("#f3e6c8"))
                p.drawRoundedRect(QRectF(-40, -48, 80, 96), 3, 3)
                p.setPen(QPen(QColor("#536968"), 3))
                p.drawLine(QPointF(-14, -4), QPointF(-3, 7))
                p.drawLine(QPointF(-3, 7), QPointF(18, -17))
                p.restore()
        self._rotulo(p, "UN TITULAR NO ES UN RESULTADO", t, 7, x=70, y=389, ancho=590)

    def _documento_fuentes(self, p, t, titulo, filas):
        """Papel en primer plano: aparecen preguntas, nunca una falsa prueba."""
        a = _rango(t, 7.7, 8.7)
        if a <= 0:
            return
        p.save()
        p.setOpacity(a*.95)
        p.translate(1000+22*(1-a), 263+6*math.sin(t*.5))
        p.rotate(-3+math.sin(t*.3)*.4)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(_color("#071c27", 120))
        p.drawRoundedRect(QRectF(-172, -147, 354, 298), 7, 7)
        g = QLinearGradient(-180, -150, 170, 145)
        g.setColorAt(0, QColor("#f0e2c6"))
        g.setColorAt(1, QColor("#d6bf94"))
        p.setBrush(g)
        p.setPen(QPen(_color("#a48d66", 210), 1))
        p.drawRoundedRect(QRectF(-180, -154, 354, 298), 6, 6)
        p.setFont(_fuente(21, True))
        p.setPen(QColor("#3a4f50"))
        p.drawText(QRectF(-154, -132, 307, 54), Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, titulo)
        for n, fila in enumerate(filas):
            fr = _rango(t, 8.3+n*.58, 8.9+n*.58)
            p.setOpacity(a*fr)
            p.setFont(_fuente(22))
            p.drawText(QRectF(-131, -57+n*52, 278, 42), Qt.AlignmentFlag.AlignVCenter, fila)
            p.setPen(QPen(QColor("#96713f"), 2))
            p.drawEllipse(QPointF(-145, -36+n*52), 5, 5)
            # Tinta que se traza al lado de cada pregunta; ninguna marca de
            # verificado aparece antes de que la partida resuelva el caso.
            p.setPen(QPen(_color("#94733f", 130), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(-127, -11+n*52), QPointF(-127+244*fr, -11+n*52))
            p.setPen(QColor("#3a4f50"))
        p.setOpacity(a*.75)
        p.setFont(_fuente(13))
        p.drawText(QRectF(-154, 113, 300, 20), "PREGUNTAS DE LA INVESTIGACIÓN")
        p.restore()

    def _trazos_recorrido(self, p, t):
        if not 4.2 <= t < 8:
            return
        puntos = [self._punto_inserto(x, y, t) for x, y in
                  ((.27, .66), (.31, .63), (.34, .59), (.38, .56), (.43, .55),
                   (.48, .58), (.52, .61), (.57, .61), (.61, .60))]
        progreso = _rango(t, 4.3, 7.6)*(len(puntos)-1)
        path = QPainterPath(QPointF(*puntos[0]))
        fin = puntos[0]
        for n in range(len(puntos)-1):
            fr = max(0, min(1, progreso-n))
            x, y = puntos[n]
            bx, by = puntos[n+1]
            fin = x+(bx-x)*fr, y+(by-y)*fr
            path.lineTo(QPointF(*fin))
            if fr < 1:
                break
        p.setBrush(Qt.BrushStyle.NoBrush)
        for color, grosor in (("#243d40", 10), ("#efd39d", 4)):
            p.setPen(QPen(_color(color, 220), grosor, Qt.PenStyle.SolidLine,
                          Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            p.drawPath(path)
        p.setPen(QPen(_color("#ffe8bc", 190), 2))
        p.setBrush(_color("#9f673b", 240))
        p.drawEllipse(QPointF(*fin), 8, 8)
        p.setBrush(Qt.BrushStyle.NoBrush)
        fr = (t*.75)%1
        p.setPen(QPen(_color("#ffe8bc", 170*(1-fr)), 2))
        p.drawEllipse(QPointF(*fin), 11+fr*23, 11+fr*23)

    def _hilos_pregunta(self, p, t, pregunta="¿FUENTE?"):
        """Un recorrido de mensajes termina en una pregunta, no en un veredicto."""
        inicio = 4.2
        nodos = ((795, 165), (1044, 200), (884, 328), (1116, 363))
        for n, (x, y) in enumerate(nodos):
            a = _rango(t, inicio+n*.8, inicio+.6+n*.8)
            if a <= 0:
                continue
            if n:
                ox, oy = nodos[n-1]
                p.setPen(QPen(_color("#f0c790", a*160), 2, Qt.PenStyle.DashLine))
                p.drawLine(QPointF(ox, oy), QPointF(ox+(x-ox)*a, oy+(y-oy)*a))
                pulso = ((t*.45-n*.2) % 1)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(_color("#ffe2aa", 220*a))
                p.drawEllipse(QPointF(ox+(x-ox)*pulso, oy+(y-oy)*pulso), 4, 4)
            p.setPen(QPen(_color("#eccb95", 210*a), 1.5))
            p.setBrush(_color("#183a46", 225*a))
            p.drawEllipse(QPointF(x, y), 23, 23)
            p.setPen(_color("#ffe9c4", 240*a))
            p.setFont(_fuente(26, True))
            p.drawText(QRectF(x-20, y-20, 40, 40), Qt.AlignmentFlag.AlignCenter, "?" if n == 3 else "…")
        if t > 7.4:
            self._rotulo(p, pregunta, t, 7.4, x=823, y=405, ancho=350)

    def _recuerdo_luminoso(self, p, t):
        # Un reflejo avanza sobre el libro durante el recuerdo familiar. La
        # página giratoria se fija a la pintura y no duplica el objeto.
        if 4 <= t < 8:
            self._animar_pagina_pintada(p, t, True)
        if t < 4:
            g = QLinearGradient(180+t*23, 60, 650+t*23, 540)
            g.setColorAt(0, _color("#f7dfb3", 0))
            g.setColorAt(.5, _color("#f7dfb3", 23))
            g.setColorAt(1, _color("#f7dfb3", 0))
            p.fillRect(QRectF(0, 60, 1280, 450), g)

    def _etapas_proyecto(self, p, t):
        if t < 8:
            return
        # Una progresión comparativa: no marca las tres etapas como cumplidas.
        etapas = (("ANUNCIO", "¿Qué se propone?"), ("PROYECTO", "¿Está aprobado?"),
                  ("OBRA", "¿Está terminada?"))
        for n, (titulo, pregunta) in enumerate(etapas):
            a = _rango(t, 8+n*.65, 8.7+n*.65)
            x, y = 647+172*n, 182+63*n
            if n:
                p.setPen(QPen(_color("#e7c28c", a*150), 2, Qt.PenStyle.DashLine))
                p.drawLine(QPointF(x-35, y+12), QPointF(x+8, y+12))
            p.save()
            p.setOpacity(a)
            p.translate(0, 14*(1-a))
            p.setPen(QPen(_color("#d9bb88", 155), 1))
            p.setBrush(_color("#173541", 234))
            p.drawRoundedRect(QRectF(x, y, 164, 111), 9, 9)
            p.setPen(QColor("#f1d4a1"))
            p.setFont(_fuente(18, True))
            p.drawText(QRectF(x+12, y+11, 140, 28), Qt.AlignmentFlag.AlignCenter, titulo)
            p.setPen(QColor("#f0e5ce"))
            p.setFont(_fuente(17))
            p.drawText(QRectF(x+10, y+45, 144, 53), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, pregunta)
            p.restore()

    def _personaje(self, p, t):
        tema = self.ficha["tema"]
        if tema == "familia_colegio":
            if 4 < t < 8:
                self._hilos_pregunta(p, t, "MENSAJE SIN CONFIRMAR")
            if t > 8:
                self._rotulo(p, "LA PREOCUPACIÓN ES REAL. EL RUMOR, UNA PREGUNTA.", t, 8,
                             x=410, y=400, ancho=797)
        elif tema == "comunicado":
            if 4 < t < 8:
                self._animar_pagina_pintada(p, t, False)
            self._documento_fuentes(p, t, "BUSCAR EL COMUNICADO", ("Autor original", "Texto completo", "Fecha y contexto"))
        elif tema in ("lectura", "memoria"):
            self._recuerdo_luminoso(p, t)
            if t > 8:
                self._rotulo(p, "UNA PROPUESTA, TODAVÍA NO UNA INAUGURACIÓN", t, 8,
                             x=479, y=400, ancho=728)
        elif tema == "propuesta":
            if 4 < t < 8:
                self._animar_pagina_pintada(p, t, False)
            self._documento_fuentes(p, t, "ENTENDER LA PROPUESTA", ("¿Qué ofrece?", "¿Para cuándo?", "¿Con qué recursos?"))
        elif tema == "camino":
            self._trazos_recorrido(p, t)
            if t > 8:
                # Huellas breves sobre el sendero, sin simular un cierre real.
                for n in range(7):
                    a = _rango(t, 8+n*.35, 8.5+n*.35)*(1-_rango(t, 10.5+n*.12, 11.8+n*.12))
                    p.save()
                    p.translate(613+n*62, 427-n*19)
                    p.rotate(-51)
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(_color("#ffe2b0", 125*a))
                    p.drawEllipse(QRectF(-5, -12, 10, 24))
                    p.restore()
                self._rotulo(p, "UN AVISO CAMBIA LOS PLANES DE UNA FAMILIA", t, 8.3,
                             x=510, y=135, ancho=695)
        elif tema == "zonas":
            self._trazos_recorrido(p, t)
            self._documento_fuentes(p, t, "PRECISAR EL AVISO", ("Fechas de mantenimiento", "Zonas afectadas", "Ruta alternativa"))
        elif tema == "etapas":
            self._recuerdo_luminoso(p, t)
            self._etapas_proyecto(p, t)
        elif tema in ("grupos", "contrastar"):
            if 4 < t < 8:
                self._hilos_pregunta(p, t, "REPETIR NO ES PROBAR")
            if tema == "contrastar":
                self._documento_fuentes(p, t, "ANTES DE PUBLICAR", ("Pedir la fuente", "Contrastar versiones", "Evitar un daño"))
            elif t > 8:
                self._rotulo(p, "UNA ACUSACIÓN AÚN SIN VERIFICAR", t, 8,
                             x=620, y=400, ancho=585)
        elif tema == "participar":
            # Se muestra la intención de conversar/votar: la papeleta aún no
            # cae a la urna porque este diálogo ocurre antes de la elección.
            if 4 < t < 8:
                x, y = self._punto_inserto(.485, .555, t)
                pulso = (t*.55)%1
                p.setPen(QPen(_color("#f5d49c", 150*(1-pulso)), 2))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(QPointF(x, y), 12+pulso*41, 8+pulso*25)
            if t > 8:
                self._rotulo(p, "EL VOTO AÚN ESTÁ EN MANOS DE LA CIUDAD", t, 8,
                             x=537, y=400, ancho=670)
        elif tema == "metodo":
            if 4 < t < 8:
                self._hilos_pregunta(p, t, "UN PORCENTAJE NO BASTA")
            self._documento_fuentes(p, t, "LEER UNA ENCUESTA", ("Fecha del estudio", "Muestra consultada", "Método utilizado"))

    def capturar_fotograma(self, segundos=0.0, tamano=(1280, 720)):
        """Renderiza sin reloj global, disco temporal ni modificar la partida."""
        t = max(0.0, min(DURACION-1/FPS, float(segundos)))
        ancho, alto = map(int, tamano)
        if ancho < 2 or alto < 2:
            raise ValueError("El tamaño debe ser positivo")
        imagen = QImage(ancho, alto, QImage.Format.Format_ARGB32)
        imagen.fill(QColor("#132b39"))
        p = QPainter(imagen)
        try:
            p.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform |
                             QPainter.RenderHint.TextAntialiasing)
            p.scale(ancho/1280, alto/720)
            self._fondo(p, t)
            self._atmosfera(p, t)
            tipo = self.ficha["tipo"]
            if tipo == "reloj": self._reloj(p, t)
            elif tipo == "red": self._red(p, t)
            elif tipo == "colegio": self._colegio(p, t)
            elif tipo == "cafe": self._cafe(p, t)
            elif tipo == "libreta": self._papel(p, t)
            elif tipo == "mapa": self._mapa(p, t)
            elif tipo == "libro": self._papel(p, t, True)
            elif tipo == "lluvia": self._lluvia(p, t)
            elif tipo == "urna": self._urna(p, t)
            elif tipo == "persona": self._personaje(p, t)
            # Gradiente inferior deja respirar los subtítulos del juego.
            sombra = QLinearGradient(0, 420, 0, 720)
            sombra.setColorAt(0, _color("#0c2230", 0))
            sombra.setColorAt(1, _color("#0c2230", 150))
            p.fillRect(QRectF(0, 420, 1280, 300), sombra)
            # Vigneta discreta, sin flash ni vibración de pantalla.
            borde = QRadialGradient(QPointF(640, 290), 830)
            borde.setColorAt(0, _color("#081b28", 0))
            borde.setColorAt(.6, _color("#081b28", 0))
            borde.setColorAt(1, _color("#081b28", 112))
            p.fillRect(QRectF(0, 0, 1280, 720), borde)
        finally:
            p.end()
        return imagen
