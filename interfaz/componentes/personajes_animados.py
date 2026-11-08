"""Actores ilustrados: expresiones, parpadeo, respiración y boca por voz.

Los atlas de ImageGen se recortan en memoria en doce celdas regulares. No se
alteran los originales. La sombra comparte exactamente el reloj del actor.
"""
import math
import time

from PyQt6.QtCore import QRectF, Qt, QTimer
from PyQt6.QtGui import QBitmap, QColor, QPainter, QPixmap, QRegion
from PyQt6.QtWidgets import QLabel

from infraestructura.recursos import RAIZ


EXPRESIONES = {
    "neutral": (0, 1, 2), "sonrisa": (3, 4, None),
    "preocupado": (5, 6, None), "sorprendido": (15, 16, 17),
    "enojado": (12, 13, 14), "triste": (18, 19, 20),
    "pensativo": (21, 22, 23),
}
_ATLAS = {}
_SOMBRAS = {}
_NPC_PARCIALES = set()
_EMOCIONES_NPC = {}
_FIRMAS_EMOCIONES_NPC = {}
_ENCUADRES_NPC = {}
EMOCIONES_NPC_NUEVAS = ("pensativo", "sorprendido", "enojado", "triste")
ACTORES_NUEVOS = {"influencer", "juan", "adrian", "laura", "camila"}
# Direcciones observadas en las ilustraciones originales. El espejo se aplica
# al pintar cuerpo, boca y sombra, sin duplicar los recursos de los personajes.
MIRADAS_ORIGINALES = {
    "ciudadano": "derecha", "periodista": "izquierda",
    "influencer": "izquierda", "juan": "derecha", "adrian": "derecha",
    "laura": "izquierda", "camila": "derecha",
}
_EXPRESIONES_NPC = {"neutral": 0, "sonrisa": 1, "decidido": 1, "preocupado": 2, "pensativo": 2,
                    "sorprendido": 2, "enojado": 2, "triste": 2}


def emociones_actor(rol):
    """Emociones ilustradas propias; no dibuja ni altera rasgos del personaje."""
    rol = str(rol).lower()
    if rol not in ACTORES_NUEVOS:
        return {}
    carpeta = RAIZ / "assets/novela/pulido/expresiones"
    rutas = {estado: carpeta / f"{rol}_{estado}.png" for estado in EMOCIONES_NPC_NUEVAS}
    firma = tuple((estado, ruta.stat().st_mtime_ns if ruta.is_file() else None)
                  for estado, ruta in rutas.items())
    if _FIRMAS_EMOCIONES_NPC.get(rol) != firma:
        imagenes = {estado: QPixmap(str(ruta)) for estado, ruta in rutas.items() if ruta.is_file()}
        _EMOCIONES_NPC[rol] = {estado: imagen for estado, imagen in imagenes.items() if not imagen.isNull()}
        _FIRMAS_EMOCIONES_NPC[rol] = firma
    return _EMOCIONES_NPC.get(rol, {})


def fotogramas_actor(rol):
    if str(rol).lower() in ACTORES_NUEVOS:
        rol = str(rol).lower()
        if rol not in _ATLAS or rol in _NPC_PARCIALES:
            carpeta = RAIZ / "assets/expansion/siete_actos/personajes"
            imagenes = [QPixmap(str(carpeta/f"{rol}_{estado}.png"))
                        for estado in ("neutral", "decidido", "preocupado", "hablando", "parpadeo")]
            if imagenes[0].isNull():
                return []
            _ATLAS[rol] = [imagen if not imagen.isNull() else imagenes[0] for imagen in imagenes]
            if any(imagen.isNull() for imagen in imagenes):
                _NPC_PARCIALES.add(rol)
            else:
                _NPC_PARCIALES.discard(rol)
        return _ATLAS[rol]
    rol = "periodista" if str(rol).lower() == "periodista" else "ciudadano"
    if rol not in _ATLAS:
        ruta = RAIZ / "assets/expansion/expresiones" / f"{rol}_atlas.png"
        atlas = QPixmap(str(ruta))
        if atlas.isNull():
            return []
        fotogramas = []
        drama = QPixmap(str(ruta.with_name(f"{rol}_drama_atlas.png")))
        for hoja in (atlas, drama if not drama.isNull() else atlas):
            for indice in range(12):
                col, fila = indice % 4, indice // 4
                x0, x1 = round(col*hoja.width()/4), round((col+1)*hoja.width()/4)
                y0, y1 = round(fila*hoja.height()/3), round((fila+1)*hoja.height()/3)
                fotogramas.append(hoja.copy(x0, y0, x1-x0, y1-y0))
        _ATLAS[rol] = fotogramas
    return _ATLAS[rol]


def sombra_fotograma(pixmap):
    clave = pixmap.cacheKey()
    if clave not in _SOMBRAS:
        resultado = QPixmap(pixmap.size())
        resultado.fill(Qt.GlobalColor.transparent)
        pintor = QPainter(resultado)
        pintor.drawPixmap(0, 0, pixmap)
        pintor.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        pintor.fillRect(resultado.rect(), QColor(4, 12, 20, 160))
        pintor.end()
        _SOMBRAS[clave] = resultado
    return _SOMBRAS[clave]


def encuadre_actor(pixmap):
    """Iguala el plano medio por la silueta, conservando proporciones y alpha."""
    clave = pixmap.cacheKey()
    if clave not in _ENCUADRES_NPC:
        mascara = pixmap.toImage().createAlphaMask(Qt.ImageConversionFlag.ThresholdAlphaDither)
        caja = QRegion(QBitmap.fromImage(mascara)).boundingRect()
        if caja.isEmpty():
            rect = QRectF(pixmap.width()*.16, 0, pixmap.width()*.68, pixmap.height()*.50)
        else:
            ancho = min(pixmap.width(), caja.width()*1.15)
            izquierda = max(0, min(pixmap.width()-ancho, caja.center().x()-ancho/2))
            arriba = max(0, caja.top()-caja.height()*.025)
            alto = min(pixmap.height()-arriba, caja.height()*.53)
            rect = QRectF(izquierda, arriba, ancho, alto)
        if len(_ENCUADRES_NPC) > 80:
            _ENCUADRES_NPC.clear()
        _ENCUADRES_NPC[clave] = rect
    return QRectF(_ENCUADRES_NPC[clave])


class SpriteExpresivo(QLabel):
    """Compatible con QLabel para conservar el ciclo de entradas y fundidos."""
    def __init__(self, parent=None, sombra=False):
        super().__init__(parent)
        self.rol = ""
        self.expresion = "neutral"
        self.hablando = False
        self.nivel = 0.0
        self.sombra = sombra
        self.reducir_movimiento = False
        self.activo = True
        self._tiempo_fijo = None
        self._fotogramas = []
        self._emociones = {}
        self.direccion_mirada = None
        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self.update)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setStyleSheet("background:transparent;")

    def configurar_actor(self, rol, expresion="neutral"):
        clave = str(rol).lower()
        self.rol = clave if clave in ACTORES_NUEVOS else "periodista" if clave == "periodista" else "ciudadano"
        self.expresion = expresion if (expresion in EXPRESIONES or self.rol in ACTORES_NUEVOS and expresion == "decidido") else "neutral"
        self._fotogramas = fotogramas_actor(self.rol)
        self._emociones = emociones_actor(self.rol)
        self._sincronizar()
        self.update()

    def configurar_movimiento(self, reducir=False, activo=True):
        self.reducir_movimiento = bool(reducir)
        self.activo = bool(activo)
        self._sincronizar()
        self.update()

    def establecer_hablando(self, hablando, nivel=None):
        self.hablando = bool(hablando)
        if nivel is not None:
            self.nivel = max(0.0, min(1.0, float(nivel)))
        elif not hablando:
            self.nivel = 0.0
        self.update()

    def orientar_hacia(self, direccion):
        """Orienta todos los fotogramas hacia el interlocutor de la escena."""
        if direccion not in ("izquierda", "derecha"):
            raise ValueError("La mirada debe ser izquierda o derecha")
        self.direccion_mirada = direccion
        self.update()

    @property
    def espejado(self):
        return (self.direccion_mirada is not None
                and self.direccion_mirada != MIRADAS_ORIGINALES.get(self.rol))

    def establecer_tiempo(self, segundos=None):
        self._tiempo_fijo = segundos
        self._sincronizar()
        self.update()

    def _sincronizar(self):
        if (self.isVisible() and self._fotogramas and self.activo
                and not self.reducir_movimiento and self._tiempo_fijo is None):
            self._timer.start()
        else:
            self._timer.stop()

    def showEvent(self, event):
        super().showEvent(event)
        self._sincronizar()

    def hideEvent(self, event):
        self._timer.stop()
        super().hideEvent(event)

    def tiempo(self):
        if self.reducir_movimiento or not self.activo:
            return 0.0
        return self._tiempo_fijo if self._tiempo_fijo is not None else time.monotonic()

    def indice_fotograma(self, segundos=None):
        if self.rol in ACTORES_NUEVOS:
            cerrado = _EXPRESIONES_NPC[self.expresion]
            if self.reducir_movimiento or not self.activo:
                return cerrado
            # Los fotogramas de boca/parpadeo antiguos son neutros. Una emoción
            # propia conserva su rostro hasta disponer de su animación real.
            if self.expresion != "neutral":
                return cerrado
            t = self.tiempo() if segundos is None else segundos
            if self.expresion == "neutral" and (t+sum(map(ord, self.rol))*.17) % 4.7 < .13:
                return 4
            if self.hablando and self.nivel > .10:
                return 3
            return cerrado
        cerrado, abierto, parpadeo = EXPRESIONES[self.expresion]
        if self.reducir_movimiento or not self.activo:
            return cerrado
        t = self.tiempo() if segundos is None else segundos
        desfase = .85 if self.rol == "periodista" else 0.0
        if parpadeo is not None and (t + desfase) % 4.7 < .13:
            return parpadeo
        if self.hablando and self.nivel > .10:
            return abierto
        return cerrado

    def fotograma_actual(self, segundos=None):
        """Prioriza el PNG de la emoción exacta y conserva el atlas original."""
        if self.rol in ACTORES_NUEVOS and self.expresion in self._emociones:
            return self._emociones[self.expresion]
        return self._fotogramas[self.indice_fotograma(segundos)] if self._fotogramas else QPixmap()

    @property
    def expresion_visual(self):
        if self.rol not in ACTORES_NUEVOS or self.expresion in self._emociones:
            return self.expresion
        return ("neutral", "decidido", "preocupado")[_EXPRESIONES_NPC[self.expresion]]

    def paintEvent(self, event):
        if not self._fotogramas:
            return super().paintEvent(event)
        imagen = self.fotograma_actual()
        origen = QRectF(imagen.rect())
        if self.rol in ACTORES_NUEVOS:
            # El recurso conserva el cuerpo completo; la novela usa plano medio.
            origen = encuadre_actor(imagen)
        if self.sombra:
            # Conserva exactamente el encuadre del cuerpo, incluso en bordes
            # semitransparentes: oscurecer no debe desplazar la silueta.
            imagen = sombra_fotograma(imagen)
        t = self.tiempo()
        amplitud = 0.0 if self.reducir_movimiento or not self.activo else 1.0
        fase = t*1.75 + (.9 if self.rol == "periodista" else 0)
        respiro = 1 + amplitud*.0035*math.sin(fase)
        ancho = max(1, self.width()-12)
        alto = max(1, self.height()-6)
        escala = min(ancho/origen.width(), alto/origen.height())
        w, h = origen.width()*escala, origen.height()*escala*respiro
        vaiven = amplitud*.9*math.sin(fase*.6)
        destino = QRectF((self.width()-w)/2+vaiven, self.height()-h-3, w, h)
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if self.espejado:
            pintor.translate(self.width(), 0)
            pintor.scale(-1, 1)
        pintor.drawPixmap(destino, imagen, origen)
        pintor.end()
