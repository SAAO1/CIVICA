"""interfaz.componentes.grafo: presentación separada de las reglas del juego."""
import math
from PyQt6.QtCore import Qt, QTimer, QElapsedTimer, QEvent, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QPolygonF, QPainterPath, QRadialGradient
from PyQt6.QtWidgets import QWidget, QSizePolicy
from interfaz.componentes.accesibilidad import paleta
from interfaz.componentes.arte import pixmap_arte, avatar_arte


class VisualizadorGrafo(QWidget):
    nodo_seleccionado = pyqtSignal(str)

    def __init__(self, grafo, parent=None):
        super().__init__(parent)
        self.grafo = grafo
        self.visitados = set()
        self.aristas_usadas = set()
        self.emisor = "ana"
        self.etiqueta = "Red social de Ciudad Nova"
        self.tipo = "exploracion"
        self.nuevos = set()
        self.conexiones_nuevas = set()
        self.focos_contacto = set()
        self.etiquetas_contacto = {}
        self.progreso_contacto = 1.0
        self._tiempo_contacto = 0.0
        self._reloj_contacto = QElapsedTimer()
        self._ventana_observada = None
        self.timer_contacto = QTimer(self)
        self.timer_contacto.setInterval(34)
        self.timer_contacto.timeout.connect(self._paso_contacto)
        self.posiciones = {}
        self.radio_nodo = 28
        self.cajas_nombres = {}
        self.setMinimumSize(460, 310)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setToolTip("Selecciona un retrato para consultar sus conexiones. Las flechas indican quién recibe la información.")

    def establecer_contactos(self, aristas=(), origen=None, vecino=None, accion=None):
        """Resalta sólo vínculos que constan en el registro y en el grafo real."""
        self.timer_contacto.stop()
        self.conexiones_nuevas = {tuple(a) for a in aristas if len(a) == 2
                                  and self.grafo.existe_arista(*a)}
        self.focos_contacto = {id for id in (origen, vecino) if id in self.grafo.nodos}
        self.etiquetas_contacto = {}
        if origen in self.focos_contacto:
            self.etiquetas_contacto[origen] = "ORIGEN"
        if vecino in self.focos_contacto:
            self.etiquetas_contacto[vecino] = "FUENTE" if accion == "entrevistar" else "VECINO"
        self.progreso_contacto = 0.0 if self.conexiones_nuevas else 1.0
        self._tiempo_contacto = 0.0
        self._reloj_contacto.invalidate()
        self._sincronizar_contacto()
        self.update()

    def _sincronizar_contacto(self):
        if getattr(self.window(), "reducir_movimiento", False):
            self.progreso_contacto = 1.0
        if (self.conexiones_nuevas and self.progreso_contacto < 1 and self.isVisible()
                and not self.window().isMinimized()):
            if not self._reloj_contacto.isValid():
                self._reloj_contacto.start()
            self.timer_contacto.start()
        else:
            self._pausar_reloj_contacto()
        self.update()

    def _pausar_reloj_contacto(self):
        if self._reloj_contacto.isValid():
            self._tiempo_contacto += self._reloj_contacto.elapsed()
            self._reloj_contacto.invalidate()
        self.timer_contacto.stop()

    def _paso_contacto(self):
        if not self.isVisible() or self.window().isMinimized():
            self._pausar_reloj_contacto()
            return
        if getattr(self.window(), "reducir_movimiento", False):
            self.progreso_contacto = 1.0
        else:
            self.progreso_contacto = min(1.0, (self._tiempo_contacto+self._reloj_contacto.elapsed())/2200)
        if self.progreso_contacto >= 1:
            self.timer_contacto.stop()
        self.update()

    def completar_contactos(self):
        self._pausar_reloj_contacto()
        self.progreso_contacto = 1.0
        self.update()

    def _dibujar_contactos(self, p, radio, escala, colores):
        # Dos arcos separan las direcciones de una relación recíproca. El
        # trazo se une de un retrato al otro y termina con una flecha real.
        avance = self.progreso_contacto
        avance = avance*avance*(3-2*avance)
        for a, b in sorted(self.conexiones_nuevas):
            if a not in self.posiciones or b not in self.posiciones:
                continue
            inicio, fin = self.posiciones[a], self.posiciones[b]
            vector = fin-inicio
            largo = math.hypot(vector.x(), vector.y())
            if largo < 1:
                continue
            unidad = vector/largo
            normal = QPointF(-unidad.y(), unidad.x())
            salida = inicio+unidad*(radio+6)
            llegada = fin-unidad*(radio+8)
            control = (salida+llegada)/2+normal*min(58*escala, largo*.22)
            curva = QPainterPath(salida)
            curva.quadTo(control, llegada)
            trazo = QPainterPath(salida)
            for n in range(1, 49):
                trazo.lineTo(curva.pointAtPercent(avance*n/48))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(QColor(8, 21, 29, 200), 8*escala,
                          Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawPath(trazo)
            p.setPen(QPen(QColor(colores["acento"]), 3.1*escala,
                          Qt.PenStyle.DashDotLine, Qt.PenCapStyle.RoundCap))
            p.drawPath(trazo)
            punta = curva.pointAtPercent(avance)
            if avance < 1:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(255, 234, 186, 55))
                p.drawEllipse(punta, 12*escala, 12*escala)
                p.setBrush(QColor("#fff1ce"))
                p.drawEllipse(punta, 4*escala, 4*escala)
            else:
                tangente = llegada-curva.pointAtPercent(.96)
                magnitud = max(.01, math.hypot(tangente.x(), tangente.y()))
                tangente /= magnitud
                perpendicular = QPointF(-tangente.y(), tangente.x())
                p.setBrush(QColor(colores["acento"]))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawPolygon(QPolygonF([llegada, llegada-tangente*12+perpendicular*5,
                                        llegada-tangente*12-perpendicular*5]))

    def showEvent(self, event):
        super().showEvent(event)
        ventana = self.window()
        if self._ventana_observada is not ventana:
            if self._ventana_observada is not None:
                self._ventana_observada.removeEventFilter(self)
            self._ventana_observada = ventana
            if ventana is not self:
                ventana.installEventFilter(self)
        self._sincronizar_contacto()

    def hideEvent(self, event):
        self._pausar_reloj_contacto()
        super().hideEvent(event)

    def eventFilter(self, objeto, event):
        if objeto is self._ventana_observada and event.type() == QEvent.Type.WindowStateChange:
            self._sincronizar_contacto()
        return super().eventFilter(objeto, event)

    def paintEvent(self, event):
        if getattr(self.window(), "reducir_movimiento", False) and self.progreso_contacto < 1:
            self.timer_contacto.stop()
            self.progreso_contacto = 1.0
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        tablero = QRectF(self.rect()).adjusted(5, 5, -5, -5)
        fondo = QRadialGradient(tablero.center(), max(self.width(), self.height()) * .65)
        fondo.setColorAt(0, QColor("#243451"))
        fondo.setColorAt(1, QColor("#101b32"))
        p.setBrush(fondo)
        p.setPen(QPen(QColor("#a2835b"), 1))
        p.drawRoundedRect(tablero, 18, 18)
        p.setPen(QPen(QColor(187, 163, 119, 20), 1))
        for x in range(25, self.width() - 10, 34):
            p.drawLine(x, 17, x, self.height()-17)
        for y in range(25, self.height() - 10, 34):
            p.drawLine(17, y, self.width()-17, y)
        colores = paleta(getattr(self.window(), "modo_daltonismo", "normal"))
        ids = self.grafo.vertices()
        self.posiciones = {}
        # El espacio libre rodea la red: no separa las filas hasta los extremos.
        escala = max(.86, min(1.42, self.window().width() / 1366))
        radio = 30 * escala
        ancho_nombre, alto_nombre = 114 * min(escala, 1.25), 24 * escala
        if self.width() < 800:
            ancho_nombre = min(ancho_nombre, max(84, (self.width()-24-6*12*escala)/7))
        paso_x = ancho_nombre + 12 * escala
        columnas_max = max(1, int((self.width() - ancho_nombre - 24) / paso_x) + 1)
        columnas = max(1, min(math.ceil(len(ids) / 2), columnas_max))
        filas = max(1, math.ceil(len(ids) / columnas))
        # En ventanas bajas se reduce el retrato antes de superponer etiquetas.
        radio = min(radio, max(20, (self.height() / filas - alto_nombre - 19) / 2))
        self.radio_nodo = radio
        self.cajas_nombres = {}
        paso_y = min(156 * escala, (self.height() - 2*radio - alto_nombre - 30) / max(1, filas-1))
        inicio_y = (self.height() - (filas-1)*paso_y - alto_nombre - 9) / 2
        base, sobrantes = divmod(len(ids), filas)
        indice = 0
        for fila in range(filas):
            cantidad_fila = base + (fila < sobrantes)
            inicio_x = (self.width() - (cantidad_fila-1)*paso_x) / 2
            for columna in range(cantidad_fila):
                self.posiciones[ids[indice]] = QPointF(inicio_x + columna*paso_x, inicio_y + fila*paso_y)
                indice += 1
        for a, b in self.grafo.aristas():
            inicio, fin = self.posiciones[a], self.posiciones[b]
            vector = fin - inicio
            largo = math.hypot(vector.x(), vector.y())
            if largo < 1:
                continue
            unidad = vector / largo
            salida, llegada = inicio + unidad * (radio+4), fin - unidad * (radio+7)
            color_difusion = colores.get(self.tipo, colores["exploracion"])
            p.setPen(QPen(QColor(8, 21, 29, 145), 5))
            p.drawLine(salida + QPointF(0, 2), llegada + QPointF(0, 2))
            activa = (a, b) in self.aristas_usadas
            estilo = {"falsa": Qt.PenStyle.DashLine, "correccion": Qt.PenStyle.DashDotLine}.get(self.tipo, Qt.PenStyle.SolidLine)
            p.setPen(QPen(QColor(color_difusion if activa else colores["neutro"]),
                          3.4*escala if activa else 1.4*escala, estilo if activa else Qt.PenStyle.SolidLine))
            p.drawLine(salida, llegada)
            normal = QPointF(-unidad.y(), unidad.x())
            p.setBrush(p.pen().color())
            p.drawPolygon(QPolygonF([llegada, llegada - unidad * 12 + normal * 5,
                                    llegada - unidad * 12 - normal * 5]))
        self._dibujar_contactos(p, radio, escala, colores)
        for id, centro in self.posiciones.items():
            activo = id in self.visitados
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(5, 17, 26, 160))
            p.drawEllipse(centro + QPointF(0, 5), radio+2, radio+2)
            p.setBrush(QColor(colores.get(self.tipo, colores["exploracion"]) if activo else "#263e57"))
            p.setPen(QPen(QColor("#f5c9a3" if id == self.emisor else "#b5bca7"), 2))
            p.drawEllipse(centro, radio, radio)
            retrato = avatar_arte(id)
            if not retrato.isNull():
                p.save()
                mascara = QPainterPath()
                interior = radio-3
                mascara.addEllipse(centro, interior, interior)
                p.setClipPath(mascara)
                destino = QRectF(centro.x()-interior, centro.y()-interior, interior*2, interior*2)
                factor = max(interior*2 / retrato.width(), interior*2 / retrato.height())
                ancho, alto = interior*2 / factor, interior*2 / factor
                origen = QRectF((retrato.width()-ancho)/2, (retrato.height()-alto)/2, ancho, alto)
                p.drawPixmap(destino, retrato, origen)
                p.restore()
            marco = pixmap_arte("ui/nodo.png")
            if not marco.isNull() and marco.hasAlphaChannel():
                p.save()
                anillo = QPainterPath()
                anillo.addEllipse(centro, radio+5, radio+5)
                anillo.addEllipse(centro, radio-4, radio-4)
                p.setClipPath(anillo)
                p.drawPixmap(QRectF(centro.x()-radio-4, centro.y()-radio-4, (radio+4)*2, (radio+4)*2), marco, QRectF(marco.rect()))
                p.restore()
            if activo:
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(QColor(colores.get(self.tipo, colores["exploracion"])), 3))
                p.drawEllipse(centro, radio+1, radio+1)
            if id == self.emisor:
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(QColor("#f5c9a3"), 2))
                p.drawEllipse(centro, radio+5, radio+5)
            if id in self.nuevos:
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(QColor(colores["acento"]), 2, Qt.PenStyle.DotLine))
                p.drawEllipse(centro, radio+7, radio+7)
            if id in self.focos_contacto:
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(QColor(colores["acento"]), 2.5*escala, Qt.PenStyle.DashDotLine))
                p.drawEllipse(centro, radio+10, radio+10)
            p.setPen(QColor("white"))
            fuente = QFont(self.font())
            fuente.setPixelSize(round(16 * escala))
            fuente.setBold(True)
            p.setFont(fuente)
            nombre = self.grafo.nodos[id].nombre
            if retrato.isNull():
                p.drawText(QRectF(centro.x()-radio, centro.y()-radio, radio*2, radio*2),
                           Qt.AlignmentFlag.AlignCenter, nombre[:2].upper())
            if activo:
                distintivo = centro + QPointF(radio*.75, radio*.68)
                p.setBrush(QColor(colores.get(self.tipo, colores["exploracion"])))
                p.setPen(QPen(QColor("#f6e8cd"), 1.5))
                marca = 10*escala
                p.drawEllipse(distintivo, marca, marca)
                p.drawText(QRectF(distintivo.x()-marca, distintivo.y()-marca, marca*2, marca*2),
                           Qt.AlignmentFlag.AlignCenter, {"falsa": "!", "verdadera": "V", "correccion": "C", "vinculo": "+", "entrevista": "+"}.get(self.tipo, "R"))
            distintivo_contacto = self.etiquetas_contacto.get(id)
            etiqueta = nombre + (" · EMISOR" if id == self.emisor and self.tipo not in ("vinculo", "entrevista")
                                 else " · "+distintivo_contacto if distintivo_contacto else "")
            caja_nombre = QRectF(centro.x()-ancho_nombre/2, centro.y()+radio+9, ancho_nombre, alto_nombre)
            self.cajas_nombres[id] = caja_nombre
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(16, 27, 48, 225))
            p.drawRoundedRect(caja_nombre, 5, 5)
            p.setPen(QColor("#fff0d1"))
            fuente.setPixelSize(max(13, round(14 * escala)))
            fuente.setBold(False)
            p.setFont(fuente)
            p.drawText(caja_nombre, Qt.AlignmentFlag.AlignCenter,
                       p.fontMetrics().elidedText(etiqueta, Qt.TextElideMode.ElideRight, round(ancho_nombre-8)))
        p.end()

    def mousePressEvent(self, event):
        for id, posicion in self.posiciones.items():
            if (math.hypot(event.position().x()-posicion.x(), event.position().y()-posicion.y()) <= self.radio_nodo+7
                    or self.cajas_nombres.get(id, QRectF()).contains(event.position())):
                self.nodo_seleccionado.emit(id)
                break
        super().mousePressEvent(event)
