"""Balance escénico: todos los cambios comparables en una sola mirada."""
import time

from PyQt6.QtCore import QEvent, QRectF, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from interfaz.componentes.arte import FUENTE_UI, icono_arte, dibujar_fondo, pixmap_arte, _nueve_segmentos


ETIQUETAS = {"confianza": "Confianza", "info_verificada": "Información verificada",
             "desinformacion": "Desinformación", "convivencia": "Convivencia",
             "bienestar_digital": "Bienestar digital", "conflictos": "Conflictos",
             "participacion": "Participación", "puntos": "Tu puntuación"}
ORDEN = ("info_verificada", "confianza", "desinformacion", "convivencia",
         "bienestar_digital", "conflictos", "participacion")


def tarjetas_resultado(registro):
    """Los siete indicadores y los puntos, incluidos los que no cambiaron."""
    tarjetas = []
    for clave in ORDEN:
        antes = registro.get("antes", {}).get(clave, 0)
        despues = registro.get("despues", {}).get(clave, antes)
        delta = despues-antes
        tarjetas.append(dict(clave=clave, nombre=ETIQUETAS[clave], antes=antes,
                             despues=despues, delta=delta,
                             favorable=None if delta == 0 else delta < 0 if clave in ("desinformacion", "conflictos") else delta > 0))
    puntos = registro.get("puntos", 0)
    anterior = registro.get("puntos_antes", 0)
    tarjetas.append(dict(clave="puntos", nombre=ETIQUETAS["puntos"], antes=anterior,
                         despues=registro.get("puntos_despues", anterior+puntos), delta=puntos,
                         favorable=puntos >= 0))
    return tarjetas


class BalanceAnimado(QWidget):
    """Anima todos los valores juntos; la voz nunca bloquea su lectura.

    Los valores anteriores y finales están visibles desde el primer dibujo.
    El reloj compartido se suspende al ocultar, minimizar o pausar.
    """
    terminado = pyqtSignal()
    DURACION_CONTADOR = 1.2
    DURACION_REDUCIDA = .9
    DURACION_SIN_VOZ = 1.6
    DURACION_TOTAL = 1.2

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
        self._automatico = True
        self._esperando_voz = False
        self._pausado = False
        if self.tarjetas and self._indice < 0:
            self._mostrar(0)
        elif self._indice >= 0 and self._inicio is None:
            self._inicio = time.monotonic()
        self._sincronizar()

    def segmento(self, clave):
        if not self.isVisible() or self._pausado:
            return
        indice = next((i for i, t in enumerate(self.tarjetas) if t["clave"] == clave), None)
        if indice is None:
            return
        self._ultimo_solicitado = max(self._ultimo_solicitado, indice)
        self._mostrar(indice)

    def _mostrar(self, indice):
        """La narración puede destacar una tarjeta sin reiniciar el reloj común."""
        self._indice = indice
        tarjeta = self.tarjetas[indice]
        self.setAccessibleName(f"{tarjeta['nombre']}: de {tarjeta['antes']:g} a {tarjeta['despues']:g}, cambio {tarjeta['delta']:+g}")
        if self._inicio is None and not self._pausado and not self._completo:
            self._inicio = time.monotonic()
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
        duracion = .35 if self._reducir else self.DURACION_TOTAL
        if self.tiempo_actual() >= duracion:
            self.revelar()
        self.update()

    def revelar(self):
        """Completa todos los valores inmediatamente cuando lo pide la persona."""
        if not self.tarjetas or self._completo:
            return
        self._vistos = {t["clave"] for t in self.tarjetas}
        self._indice = len(self.tarjetas)-1
        self._completo = True
        self._esperando_voz = False
        self._timer.stop()
        self.terminado.emit()
        self.update()

    def finalizar_voz(self):
        """La voz no modifica el avance manual ni el reloj visual."""
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
        p.setPen(QColor(0, 0, 0, 190))
        p.drawText(caja.translated(1, 1), alineacion, str(texto))
        p.setPen(QColor(color))
        p.drawText(caja, alineacion, str(texto))


    def _geometria_balance(self):
        ancho, alto = self.width(), self.height()
        panel = QRectF(0, 0, min(1240, ancho-64), min(600, alto-36))
        panel.moveCenter(QRectF(self.rect()).center())
        self._panel_rect = panel
        self._escala_texto = max(1.0, min(1.18, self.font().pixelSize()/16 if self.font().pixelSize()>0 else 1))
        self._inicio_texto = panel.top()+126
        self._alto_fila = (panel.height()-186)/2
        return panel

    def paintEvent(self, event):
        if not self.tarjetas:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        # Una escena de ciudad propia para el balance, con el material original.
        p.fillRect(self.rect(), QColor("#152438"))
        dibujar_fondo(p, self.rect(), "fondos/ciudad.png")
        panel = self._geometria_balance()
        # La base opaca impide que el plano anterior atraviese el panel.
        p.fillRect(panel.adjusted(12,12,-12,-12), QColor("#132139"))
        _nueve_segmentos(p, panel, pixmap_arte("ui/panel.png"))
        self._texto(p, QRectF(panel.left()+42,panel.top()+35,panel.width()-84,43),
                    self.titulo, 32, "#f1d39c", True)
        self._texto(p, QRectF(panel.left()+42,panel.top()+81,panel.width()-84,30),
                    self.subtitulo, 20, "#f1e9dd")
        self._foco(p, self.tiempo_actual())
        self._texto(p, QRectF(panel.left()+42,panel.bottom()-48,panel.width()-84,29),
                    "ESPACIO / ENTER / CLIC · continuar", 18, "#f3e9d8")
        p.end()

    def _foco(self, p, t):
        panel = self._panel_rect
        margen = panel.left()+42
        paso = (panel.width()-84)/4
        escala = self._escala_texto
        nombre_px = round(21*escala)
        valor_px = round(33*escala)
        for i, tarjeta in enumerate(self.tarjetas):
            columna, fila = i % 4, i // 4
            x = margen+columna*paso
            y = self._inicio_texto+fila*self._alto_fila
            icono = "bienestar" if tarjeta["clave"] == "bienestar_digital" else tarjeta["clave"]
            imagen = icono_arte(icono).pixmap(QSize(32,32))
            p.drawPixmap(round(x+paso/2-16),round(y),imagen)
            color = "#d4d0c8" if not tarjeta["delta"] else "#f1d39c" if tarjeta["favorable"] else "#efb0a0"
            self._texto(p,QRectF(x+6,y+36,paso-12,57),tarjeta["nombre"],
                        nombre_px,"#f7ead5",True,
                        Qt.AlignmentFlag.AlignCenter|Qt.TextFlag.TextWordWrap)
            self._texto(p,QRectF(x+3,y+96,paso-6,44),
                        f"{tarjeta['antes']:g}  →  {tarjeta['despues']:g}",
                        valor_px,"#fff3dd",True)
            self._texto(p,QRectF(x+8,y+143,paso-16,32),
                        f"{tarjeta['delta']:+g}" if tarjeta["delta"] else "Sin cambio",
                        round(23*escala),color,True)
            if i == self._indice and self._balance_hablado():
                p.setPen(QPen(QColor("#d4ad69"),2))
                p.drawLine(round(x+32),round(y+178),round(x+paso-32),round(y+178))

    def _balance_hablado(self):
        return bool(getattr(self.parent(), "_balance_con_voz", False))
