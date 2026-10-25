"""Balance escénico: contadores reales, animados al ritmo de cada toma de voz."""
import time

from PyQt6.QtCore import QEvent, QPointF, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen, QRadialGradient
from PyQt6.QtWidgets import QWidget

from arte import FUENTE_UI


ETIQUETAS = {"confianza": "Confianza", "info_verificada": "Información verificada",
             "desinformacion": "Desinformación", "convivencia": "Convivencia",
             "bienestar_digital": "Bienestar digital", "conflictos": "Conflictos",
             "participacion": "Participación", "puntos": "Tu puntuación"}
ORDEN = ("info_verificada", "confianza", "desinformacion", "convivencia",
         "bienestar_digital", "conflictos", "participacion")


def tarjetas_resultado(registro):
    """Sólo cambios efectivos: respeta límites, signos y guardados antiguos."""
    tarjetas = []
    for clave in ORDEN:
        antes = registro.get("antes", {}).get(clave, 0)
        despues = registro.get("despues", {}).get(clave, antes)
        if antes != despues:
            delta = despues-antes
            tarjetas.append(dict(clave=clave, nombre=ETIQUETAS[clave], antes=antes,
                                 despues=despues, delta=delta,
                                 favorable=delta < 0 if clave in ("desinformacion", "conflictos") else delta > 0))
    puntos = registro.get("puntos", 0)
    anterior = registro.get("puntos_antes", 0)
    tarjetas.append(dict(clave="puntos", nombre=ETIQUETAS["puntos"], antes=anterior,
                         despues=registro.get("puntos_despues", anterior+puntos), delta=puntos,
                         favorable=puntos >= 0))
    return tarjetas


class BalanceAnimado(QWidget):
    """La voz dispara cada contador; sin voz, una secuencia local lo presenta.

    Cada cambio ocupa el centro y completa su tiempo de lectura. Las señales
    de voz se encolan: ni un clip corto ni una pulsación omiten un contador.
    El reloj se suspende al ocultar, minimizar o pausar.
    """
    terminado = pyqtSignal()
    DURACION_CONTADOR = 1.2
    DURACION_REDUCIDA = .9
    DURACION_SIN_VOZ = 1.6

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.tarjetas = []
        self.titulo = "La ciudad responde"
        self.subtitulo = ""
        self._indice = -1
        self._tiempo = 0.0
        self._inicio = None
        self._tiempo_fijo = None
        self._automatico = False
        self._esperando_voz = False
        self._pausado = False
        self._reducir = False
        self._completo = False
        self._vistos = set()
        self._ultimo_solicitado = -1
        self._ventana_observada = None
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._paso)
        self.hide()

    @property
    def completo(self):
        return self._completo

    @property
    def clave_actual(self):
        return self.tarjetas[self._indice]["clave"] if 0 <= self._indice < len(self.tarjetas) else None

    @property
    def claves_completadas(self):
        return tuple(t["clave"] for t in self.tarjetas if t["clave"] in self._vistos)

    def claves_pendientes(self):
        return tuple(t["clave"] for t in self.tarjetas if t["clave"] not in self._vistos)

    @property
    def valor_actual(self):
        if self._indice < 0:
            return self.tarjetas[0]["antes"] if self.tarjetas else None
        tarjeta = self.tarjetas[self._indice]
        return round(tarjeta["antes"] + tarjeta["delta"]*self._progreso())

    def preparar(self, registro, nombre=""):
        self.detener()
        self.tarjetas = tarjetas_resultado(registro)
        self.titulo = registro.get("titulo_accion", "Tu decisión deja huella")
        self.subtitulo = (nombre + " · " if nombre else "") + (
            "Ciudad Nova cambia contigo" if any(t["delta"] for t in self.tarjetas)
            else "Sin cambios en los indicadores")
        self._completo = False
        self._vistos.clear()
        self._ultimo_solicitado = -1
        self.setAccessibleName("Balance de la decisión")
        self.setAccessibleDescription(". ".join(
            f"{t['nombre']}: de {t['antes']:g} a {t['despues']:g}, cambio {t['delta']:+g}"
            for t in self.tarjetas))
        self.show()
        self.update()

    def configurar(self, reducir_movimiento=False):
        self._reducir = bool(reducir_movimiento)
        self.update()

    def comenzar(self, automatico=False):
        self._automatico = bool(automatico)
        self._esperando_voz = not automatico
        self._pausado = False
        if self.tarjetas and self._indice < 0 and (automatico or self._ultimo_solicitado >= 0):
            self._mostrar(0)
        elif self._indice >= 0 and self._inicio is None:
            self._inicio = time.monotonic()
        self._sincronizar()

    def segmento(self, clave):
        if not self.isVisible() or self._completo:
            return
        indice = next((i for i, t in enumerate(self.tarjetas) if t["clave"] == clave), None)
        if indice is None:
            return
        self._ultimo_solicitado = max(self._ultimo_solicitado, indice)
        if self._indice < 0:
            self._mostrar(0)
        else:
            self._paso()

    def _mostrar(self, indice):
        """Se entra una sola vez a cada contador; nunca reinicia los ya vistos."""
        self._indice = indice
        tarjeta = self.tarjetas[indice]
        self.setAccessibleName(f"{tarjeta['nombre']}: de {tarjeta['antes']:g} a {tarjeta['despues']:g}, cambio {tarjeta['delta']:+g}")
        self._tiempo = 0.0
        self._tiempo_fijo = None
        self._inicio = None if self._pausado else time.monotonic()
        self._sincronizar()
        self.update()

    def tiempo_actual(self):
        if self._tiempo_fijo is not None:
            return self._tiempo_fijo
        return self._tiempo + (time.monotonic()-self._inicio if self._inicio is not None else 0)

    def establecer_tiempo(self, segundos=None):
        self._tiempo_fijo = segundos
        self.update()

    def _sincronizar(self):
        if (self.isVisible() and self._indice >= 0 and not self.window().isMinimized()
                and not self._pausado and not self._completo):
            self._timer.setInterval(100 if self._reducir else 33)
            self._timer.start()
        else:
            self._timer.stop()

    def _paso(self):
        if self.window().isMinimized() or self._pausado or self._indice < 0 or self._completo:
            self._sincronizar()
            return
        duracion = (self.DURACION_SIN_VOZ if self._automatico else
                    self.DURACION_REDUCIDA if self._reducir else self.DURACION_CONTADOR)
        if self.tiempo_actual() >= duracion:
            self._vistos.add(self.clave_actual)
            siguiente = self._indice+1
            if siguiente == len(self.tarjetas):
                self._completo = len(self._vistos) == len(self.tarjetas)
                if self._completo:
                    self._timer.stop()
                    self.terminado.emit()
            elif self._automatico or siguiente <= self._ultimo_solicitado:
                self._mostrar(siguiente)
        self.update()

    def revelar(self):
        """Compatibilidad con consumidores anteriores: no salta la presentación."""
        self.update()

    def finalizar_voz(self):
        """El fin o cancelación de audio deja terminar todos los cambios pendientes."""
        self._automatico = True
        self._esperando_voz = False
        if self._indice < 0 and self.tarjetas:
            self._mostrar(0)
        self._sincronizar()
        self.update()

    def _progreso(self):
        if self._indice < 0:
            return 0.0
        if self._completo or self._reducir:
            return 1.0
        progreso = min(1, max(0, self.tiempo_actual()/.95))
        return 1-(1-progreso)**3

    def pausar(self):
        if self._inicio is not None:
            self._tiempo += time.monotonic()-self._inicio
        self._inicio = None
        self._pausado = True
        self._timer.stop()

    def reanudar(self):
        self._pausado = False
        if self._inicio is None:
            self._inicio = time.monotonic()
        self._sincronizar()

    def detener(self):
        self.pausar()
        self._desvincular_ventana()
        self._indice = -1
        self._tiempo = 0
        self._tiempo_fijo = None
        self._automatico = False
        self._esperando_voz = False
        self._completo = False
        self._ultimo_solicitado = -1
        self._vistos.clear()
        self.hide()

    def _desvincular_ventana(self):
        ventana = getattr(self, "_ventana_observada", None)
        self._ventana_observada = None
        if ventana is not None and ventana is not self:
            try:
                ventana.removeEventFilter(self)
            except RuntimeError:
                pass

    def hideEvent(self, event):
        if self.window().isMinimized():
            if self._inicio is not None:
                self._tiempo += time.monotonic()-self._inicio
            self._inicio = None
            self._timer.stop()
        else:
            self.pausar()
        super().hideEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        ventana = self.window()
        if ventana is not self and self._ventana_observada is not ventana:
            if self._ventana_observada is not None:
                self._ventana_observada.removeEventFilter(self)
            self._ventana_observada = ventana
            ventana.installEventFilter(self)
        self._sincronizar()

    def eventFilter(self, objeto, event):
        observada = getattr(self, "_ventana_observada", None)
        if observada is not None and objeto is observada and event.type() == QEvent.Type.WindowStateChange:
            if objeto.isMinimized():
                if self._inicio is not None:
                    self._tiempo += time.monotonic()-self._inicio
                self._inicio = None
                self._timer.stop()
            elif not self._pausado:
                self.reanudar()
        return super().eventFilter(objeto, event)

    def _texto(self, p, caja, texto, tamano, color="#f8eedb", negrita=False, alineacion=Qt.AlignmentFlag.AlignCenter):
        f = QFont(FUENTE_UI)
        f.setPixelSize(tamano)
        f.setBold(negrita)
        p.setFont(f)
        p.setPen(QColor(color))
        p.drawText(caja, alineacion, str(texto))

    def paintEvent(self, event):
        if not self.tarjetas:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        sx, sy = self.width()/1280, self.height()/640
        p.scale(sx, sy)
        fondo = QLinearGradient(0, 0, 1280, 640)
        fondo.setColorAt(0, QColor(8, 23, 36, 247))
        fondo.setColorAt(.5, QColor(14, 37, 48, 240))
        fondo.setColorAt(1, QColor(6, 21, 33, 251))
        p.fillRect(QRectF(0, 0, 1280, 640), fondo)
        t = self.tiempo_actual() if not self._reducir else 1
        for n in range(25):
            x = (n*157.3+t*7) % 1280
            y = 112+(n*79.7) % 470
            p.setBrush(QColor(213, 190, 135, 25))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(x, y), 1.5, 1.5)
        self._texto(p, QRectF(110, 80, 1060, 36), self.titulo, 26, "#ead4a7", True)
        self._texto(p, QRectF(110, 119, 1060, 28), self.subtitulo, 16, "#b0c9c8")
        self._foco(p, t)
        pista = ("ESPACIO / ENTER · continuar" if self._completo and not self._esperando_voz
                 else "Escuchando el balance…" if self._completo else "Cada decisión deja huella")
        self._texto(p, QRectF(80, 596, 1120, 26), pista, 15, "#c7d7d1")
        p.end()

    def _foco(self, p, t):
        indice = max(0, self._indice)
        tarjeta = self.tarjetas[indice]
        color = "#79ddbd" if tarjeta["favorable"] else "#ffb09b"
        glow = QRadialGradient(QPointF(640, 305), 285)
        glow.setColorAt(0, QColor(80, 164, 155, 40) if tarjeta["favorable"] else QColor(185, 100, 86, 40))
        glow.setColorAt(1, QColor(20, 38, 45, 0))
        p.fillRect(QRectF(220, 155, 840, 365), glow)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(180, 205, 192, 35), 2))
        p.drawEllipse(QPointF(640, 322), 126, 126)
        suave = self._progreso()
        p.setPen(QPen(QColor(color), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawArc(QRectF(514, 196, 252, 252), 90*16, round(-360*16*suave))
        valor = self.valor_actual
        self._texto(p, QRectF(240, 157, 800, 35), tarjeta["nombre"].upper(), 25, color, True)
        self._texto(p, QRectF(510, 260, 260, 108), valor, 86, "#fff2d8", True)
        self._texto(p, QRectF(510, 367, 260, 36), f"{tarjeta['delta']:+g}", 29, color, True)
        self._texto(p, QRectF(250, 286, 240, 32), f"ANTES  {tarjeta['antes']:g}", 21, "#a6c0bf")
        self._texto(p, QRectF(790, 286, 240, 32), f"AHORA  {tarjeta['despues']:g}", 21, color, True)
        for i, item in enumerate(self.tarjetas):
            x = 640+(i-(len(self.tarjetas)-1)/2)*115
            activo = i == indice
            p.setPen(QPen(QColor(color if activo else "#516c77"), 2))
            p.setBrush(QColor(color if item["clave"] in self._vistos else "#223e4b"))
            p.drawEllipse(QPointF(x, 494), 6 if activo else 4, 6 if activo else 4)
            self._texto(p, QRectF(x-55, 511, 110, 46),
                        item["nombre"].replace("Información verificada", "Verificada").replace("Bienestar digital", "Bienestar").replace("Tu puntuación", "Puntos"),
                        12, "#d5ded3", False, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap)
