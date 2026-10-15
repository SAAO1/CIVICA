import math

from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF, QSize, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QIcon, QPen, QFont, QPolygonF, QPainterPath, QRadialGradient
from PyQt6.QtWidgets import (QWidget, QFrame, QLabel, QPushButton, QVBoxLayout,
                            QHBoxLayout, QComboBox, QLineEdit, QGridLayout, QDialog,
                            QTextBrowser, QCheckBox, QSlider, QScrollArea, QTabWidget,
                            QSizePolicy, QButtonGroup)
from models.jugador import ROLES, ROLES_JUGABLES
from recursos import pixmap_recurso
from accesibilidad import paleta
from arte import (PanelIlustrado, BotonIlustrado, aplicar_estilo, dibujar_fondo,
                  pixmap_arte, avatar_arte, ESTILO_ARTE, FUENTE_UI, _nueve_segmentos)

ESTILO = ESTILO_ARTE


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
        self.posiciones = {}
        self.radio_nodo = 28
        self.cajas_nombres = {}
        self.setMinimumSize(460, 310)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setToolTip("Selecciona un retrato para consultar sus conexiones. Las flechas indican quién recibe la información.")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        tablero = QRectF(self.rect()).adjusted(5, 5, -5, -5)
        fondo = QRadialGradient(tablero.center(), max(self.width(), self.height()) * .65)
        fondo.setColorAt(0, QColor("#294b59"))
        fondo.setColorAt(1, QColor("#152c3c"))
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
                           Qt.AlignmentFlag.AlignCenter, {"falsa": "!", "verdadera": "V", "correccion": "C"}.get(self.tipo, "R"))
            etiqueta = nombre + (" · EMISOR" if id == self.emisor else "")
            caja_nombre = QRectF(centro.x()-ancho_nombre/2, centro.y()+radio+9, ancho_nombre, alto_nombre)
            self.cajas_nombres[id] = caja_nombre
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(16, 33, 45, 225))
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


class EscenaRed(QWidget):
    continuar = pyqtSignal()

    def __init__(self, juego, parent=None):
        super().__init__(parent)
        self.juego = juego
        self.setStyleSheet(ESTILO)
        self.panel = PanelIlustrado()
        self.panel.setObjectName("panelRed")
        self.panel.setMaximumSize(1600, 800)
        layout = self.layout_panel = QVBoxLayout(self.panel)
        layout.setContentsMargins(48, 48, 48, 36)
        layout.setSpacing(12)
        cabecera = QHBoxLayout()
        self.titulo = QLabel("<span style='font-size:25px;font-weight:600;'>OBSERVATORIO</span><br>"
                             "<span style='font-size:15px;font-weight:400;color:#c2d4cb;'>Así viaja una publicación por la ciudad</span>")
        self.titulo.setStyleSheet("color: #f2d1a3;")
        cabecera.addWidget(self.titulo, 1)
        self.contador = QLabel()
        self.contador.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.contador.setStyleSheet("font-size: 14px; color: #c9dacd;")
        cabecera.addWidget(self.contador)
        layout.addLayout(cabecera)
        self.resumen = QLabel()
        self.resumen.setWordWrap(True)
        self.resumen.setStyleSheet("color: #f2e5d0; font-size: 16px; padding-bottom: 3px;")
        layout.addWidget(self.resumen)
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(18)
        mapa = QVBoxLayout()
        mapa.setSpacing(8)
        self.visualizador = VisualizadorGrafo(juego.grafo)
        self.visualizador.nodo_seleccionado.connect(self.consultar)
        mapa.addWidget(self.visualizador, 1)
        self.leyenda = QLabel("R: recorrido · Doble borde: emisor · Flechas: dirección de difusión")
        self.leyenda.setWordWrap(True)
        self.leyenda.setStyleSheet("font-size: 13px; color: #c2d3c9;")
        self.detalle = QLabel("Selecciona un ciudadano para consultar sus conexiones.")
        self.detalle.setWordWrap(True)
        self.detalle.setMinimumHeight(42)
        self.detalle.setStyleSheet("font-size: 15px; color: #e7e4d3;")
        mapa.addWidget(self.leyenda)
        mapa.addWidget(self.detalle)
        cuerpo.addLayout(mapa, 1)
        inspector = self.inspector = QWidget()
        inspector.setMinimumWidth(245)
        inspector.setMaximumWidth(300)
        herramientas = QVBoxLayout(inspector)
        herramientas.setContentsMargins(0, 0, 0, 0)
        herramientas.setSpacing(12)
        self.etiqueta_inspector = QLabel("EXPLORA LA RED")
        self.etiqueta_inspector.setStyleSheet("font-size: 16px; font-weight: 600; color: #f2d1a3;")
        herramientas.addWidget(self.etiqueta_inspector)
        self.etiqueta_origen = QLabel("Ciudadano de origen")
        herramientas.addWidget(self.etiqueta_origen)
        self.origen = QComboBox()
        self.origen.setIconSize(QSize(30, 30))
        self.origen.setMinimumHeight(44)
        self.origen.setAccessibleName("Ciudadano de origen")
        herramientas.addWidget(self.origen)
        self.botones_red = []
        for texto, descripcion, metodo in (
                ("BFS · Por niveles", "Visita primero a las personas más cercanas al origen.", lambda: self.recorrer("bfs")),
                ("DFS · En profundidad", "Sigue una cadena de conexiones antes de explorar otra.", lambda: self.recorrer("dfs")),
                ("Comparar alcance", "Simula la última publicación desde este origen sin cambiar los puntos.", self.comparar)):
            boton = BotonIlustrado(texto)
            boton.setMinimumHeight(49)
            boton.setToolTip(descripcion)
            boton.setAccessibleDescription(descripcion)
            boton.clicked.connect(metodo)
            herramientas.addWidget(boton)
            self.botones_red.append(boton)
        self.explicacion = QLabel("BFS avanza por niveles.\nDFS sigue cada camino hasta el fondo.")
        self.explicacion.setWordWrap(True)
        self.explicacion.setStyleSheet("font-size: 14px; color: #c2d3c9;")
        herramientas.addWidget(self.explicacion)
        herramientas.addStretch()
        cuerpo.addWidget(inspector)
        layout.addLayout(cuerpo, 1)
        pie = QHBoxLayout()
        self.estado_reproduccion = QLabel("Recorrido automático · se repite tras 2 segundos")
        self.estado_reproduccion.setWordWrap(True)
        self.estado_reproduccion.setStyleSheet("font-size: 13px; color: #c2d3c9;")
        pie.addWidget(self.estado_reproduccion, 1)
        self.boton_continuar = BotonIlustrado("Continuar →")
        self.boton_continuar.setMinimumWidth(190)
        self.boton_continuar.setToolTip("Continuar la historia")
        self.boton_continuar.clicked.connect(self.continuar.emit)
        pie.addWidget(self.boton_continuar)
        layout.addLayout(pie)
        exterior = self.exterior = QVBoxLayout(self)
        exterior.setContentsMargins(18, 14, 18, 14)
        fila_panel = QHBoxLayout()
        fila_panel.setSpacing(0)
        fila_panel.addStretch()
        fila_panel.addWidget(self.panel, 1)
        fila_panel.addStretch()
        exterior.addLayout(fila_panel, 1)
        self.timer = QTimer(self)
        self.timer.setInterval(700)
        self.timer.timeout.connect(self.paso)
        self.timer_repeticion = QTimer(self)
        self.timer_repeticion.setSingleShot(True)
        self.timer_repeticion.setInterval(2000)
        self.timer_repeticion.timeout.connect(self.repetir)
        self.repeticion_activada = False
        self.pasos, self.indice, self.aristas_animacion = [], 0, []
        self.rellenar()
        aplicar_estilo(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not hasattr(self, "inspector"):
            return
        escala = max(.94, min(1.35, self.width()/1366))
        compacto = self.height() < 660
        muy_compacto = self.height() < 600
        seguros = self.panel.margenes_seguros()
        lateral = max(round(42*escala), seguros.left())
        self.layout_panel.setContentsMargins(lateral, max(34 if muy_compacto else round(46*escala), seguros.top()),
                                            lateral, max(22 if muy_compacto else round(32*escala), seguros.bottom()))
        self.layout_panel.setSpacing(8 if compacto else 12)
        self.inspector.setMinimumWidth(round(245*escala))
        self.inspector.setMaximumWidth(round(285*escala))
        subtitulo = "" if muy_compacto else (
            f"<br><span style='font-size:{round(15*escala)}px;font-weight:400;color:#c2d4cb;'>Así viaja una publicación por la ciudad</span>")
        self.titulo.setText(
            f"<span style='font-size:{round(25*escala)}px;font-weight:600;'>OBSERVATORIO</span>" + subtitulo)
        self.titulo.setToolTip("Así viaja una publicación por la ciudad")
        self.leyenda.setVisible(not muy_compacto)
        self.visualizador.setMinimumHeight(240 if muy_compacto else 310)
        for etiqueta, tamano, color in (
                (self.contador, 14, "#c9dacd"), (self.resumen, 16, "#f2e5d0"),
                (self.leyenda, 13, "#c2d3c9"), (self.detalle, 15, "#e7e4d3"),
                (self.estado_reproduccion, 13, "#c2d3c9"), (self.explicacion, 14, "#c2d3c9"),
                (self.etiqueta_origen, 16, "#f6e8cd")):
            etiqueta.setStyleSheet(f"font-size:{round(tamano*escala)}px;color:{color};")
        self.etiqueta_inspector.setStyleSheet(f"font-size:{round(16*escala)}px;font-weight:600;color:#f2d1a3;")
        self.origen.setStyleSheet(f"font-size:{round(16*escala)}px;")
        self.origen.setMinimumHeight(round(44*escala))
        self.origen.setIconSize(QSize(round(30*escala), round(30*escala)))
        for boton in self.botones_red + [self.boton_continuar]:
            boton.setStyleSheet(f"font-size:{round(16*escala)}px;")
            boton.setMinimumHeight(round((46 if compacto else 49)*escala))
        self.boton_continuar.setMinimumWidth(round(190*escala))
        self.detalle.setMinimumHeight(round((22 if muy_compacto else 34 if compacto else 42)*escala))
        self.visualizador.update()

    def paintEvent(self, event):
        p = QPainter(self)
        if not dibujar_fondo(p, self.rect(), "fondos/observatorio.png"):
            fondo = pixmap_recurso("assets/fondos/Escena Arbol.jfif")
            if not fondo.isNull():
                p.drawPixmap(self.rect(), fondo)
            else:
                p.fillRect(self.rect(), QColor("#182d41"))
        p.fillRect(self.rect(), QColor(11, 27, 39, 100))
        p.end()
        super().paintEvent(event)

    def rellenar(self):
        anterior = self.origen.currentData()
        self.origen.clear()
        for id, nodo in self.juego.grafo.nodos.items():
            self.origen.addItem(QIcon(avatar_arte(id)), nodo.nombre, id)
        self.origen.setCurrentIndex(max(0, self.origen.findData(anterior)))
        nuevos = getattr(self.juego, "ciudadanos_nuevos", [])
        nombres = [self.juego.grafo.nodos[id].nombre for id in nuevos if id in self.juego.grafo.nodos]
        crecimiento = "\nSe unieron: " + " y ".join(nombres) if nombres else ""
        self.contador.setText(f"{len(self.juego.grafo.nodos)} ciudadanos · {len(self.juego.grafo.aristas())} conexiones" + crecimiento)
        self.visualizador.nuevos = set(nuevos)
        self.visualizador.grafo = self.juego.grafo
        self.visualizador.update()

    def mostrar(self):
        self.finalizar_escena()
        self.rellenar()
        self.resumen.setText(self.juego.ultimo_resultado)
        self.boton_continuar.setEnabled(True)
        resultado = self.juego.ultima_propagacion
        if resultado:
            tipo = "correccion" if resultado.correccion else "falsa" if resultado.verdadera is False else "verdadera" if resultado.verdadera is True else "exploracion"
            self.iniciar_animacion(resultado.niveles, resultado.aristas, resultado.emisor, tipo)
        else:
            self.pasos, self.indice, self.aristas_animacion = [], 0, []
            self.visualizador.tipo = "exploracion"
            self.visualizador.visitados.clear()
            self.visualizador.aristas_usadas.clear()
            self.visualizador.update()
            self.leyenda.setText("Sin difusión · Retratos: ciudadanos · Flechas: dirección de las relaciones")
            self.detalle.setText("Esta decisión no inició una difusión. Puedes explorar la red con BFS y DFS.")
            self.estado_reproduccion.setText("Elige BFS, DFS o compara el alcance para explorar.")

    def iniciar_animacion(self, niveles, aristas, emisor, tipo="exploracion"):
        self.timer.stop()
        self.timer_repeticion.stop()
        self.repeticion_activada = not getattr(self.window(), "reducir_movimiento", False)
        self.pasos, self.indice = [list(n) for n in niveles], 0
        self.aristas_animacion = [tuple(a) for a in aristas]
        self.visualizador.emisor = emisor
        self.visualizador.tipo = tipo
        self.leyenda.setText({"falsa": "! Información falsa · Trazo discontinuo",
                             "verdadera": "V Información verdadera · Trazo continuo",
                             "correccion": "C Corrección informativa · Trazo de puntos y rayas"}.get(tipo, "R Recorrido de exploración") + " · Doble borde: emisor · Flechas: dirección de difusión")
        self.visualizador.visitados.clear()
        self.visualizador.aristas_usadas.clear()
        self.estado_reproduccion.setText("Recorrido automático · se repite tras 2 segundos" if self.repeticion_activada else "Movimiento reducido · recorrido completo")
        if not self.repeticion_activada:
            self.completar()
            return
        self.paso()
        if self.indice < len(self.pasos):
            self.timer.start()

    def paso(self):
        if self.indice >= len(self.pasos):
            self.timer.stop()
            return
        self.visualizador.visitados.update(self.pasos[self.indice])
        self.visualizador.aristas_usadas = {a for a in self.aristas_animacion if a[0] in self.visualizador.visitados and a[1] in self.visualizador.visitados}
        nombres = [self.juego.grafo.nodos[id].nombre for id in self.pasos[self.indice] if id in self.juego.grafo.nodos]
        self.detalle.setText(f"Paso {self.indice + 1}/{len(self.pasos)} · Receptores: {max(0, len(self.visualizador.visitados)-1)} · " + ", ".join(nombres))
        self.indice += 1
        self.visualizador.update()
        if hasattr(self.window(), "audio"):
            self.window().audio.reproducir_efecto("nodo")
        if self.indice >= len(self.pasos):
            self.timer.stop()
            if self.repeticion_activada:
                self.estado_reproduccion.setText("Recorrido completo · vuelve a comenzar en 2 segundos")
                self.timer_repeticion.start()

    def repetir(self):
        self.timer_repeticion.stop()
        if not self.isVisible() or not self.repeticion_activada or not self.pasos:
            return
        if getattr(self.window(), "reducir_movimiento", False):
            self.completar()
            return
        self.indice = 0
        self.visualizador.visitados.clear()
        self.visualizador.aristas_usadas.clear()
        self.estado_reproduccion.setText("Recorrido automático · se repite tras 2 segundos")
        self.paso()
        if self.indice < len(self.pasos):
            self.timer.start()

    def pausar(self):
        self.timer_repeticion.stop()
        self.repeticion_activada = False
        if self.timer.isActive():
            self.timer.stop()
        elif self.indice < len(self.pasos):
            self.timer.start()

    def completar(self):
        self.repeticion_activada = False
        self.timer.stop()
        self.timer_repeticion.stop()
        while self.indice < len(self.pasos):
            self.paso()
        self.estado_reproduccion.setText("Recorrido completo" if self.pasos else "Sin difusión en esta decisión")

    def finalizar_escena(self):
        self.repeticion_activada = False
        self.timer.stop()
        self.timer_repeticion.stop()

    def hideEvent(self, event):
        self.finalizar_escena()
        super().hideEvent(event)

    def consultar(self, id):
        g = self.juego.grafo
        vecinos = ", ".join(g.nodos[vecino].nombre for vecino in g.vecinos(id)) or "ninguno"
        self.detalle.setText(f"{g.nodos[id].nombre} · Entradas: {g.grado_entrada(id)} · Salidas: {g.grado_salida(id)} · Conecta con: {vecinos}")

    def recorrer(self, tipo):
        origen = self.origen.currentData()
        if not origen:
            return
        if tipo == "bfs":
            r = self.juego.grafo.bfs(origen)
            self.iniciar_animacion(r.niveles, r.aristas, origen)
            self.resumen.setText("BFS · " + " → ".join(self.juego.grafo.nodos[id].nombre for id in r.orden))
        else:
            orden = self.juego.grafo.dfs(origen)
            # Reconstruye las aristas del árbol DFS para mostrar el camino real.
            pila, visitados, aristas = [(origen, None)], set(), []
            while pila:
                actual, padre = pila.pop()
                if actual in visitados:
                    continue
                visitados.add(actual)
                if padre is not None:
                    aristas.append((padre, actual))
                pila.extend((vecino, actual) for vecino in reversed(self.juego.grafo.vecinos(actual)) if vecino not in visitados)
            self.iniciar_animacion([[id] for id in orden], aristas, origen)
            self.resumen.setText("DFS · " + " → ".join(self.juego.grafo.nodos[id].nombre for id in orden) + " · No garantiza el camino mínimo.")

    def comparar(self):
        id = self.juego.ultima_publicacion_id
        if id is None:
            self.detalle.setText("Primero toma una decisión sobre una publicación para comparar su alcance.")
            return
        if self.juego.arbol.buscar(id) is None:
            self.detalle.setText("La publicación fue retirada: su historial permanece, pero no puede iniciar una nueva difusión.")
            return
        anterior = self.juego.ultima_propagacion
        from models.jugador import ROLES
        habilidad = ROLES[self.juego.jugador.rol]
        r = self.juego.propagacion.simular(id, self.origen.currentData(), habilidad["saltos"], habilidad["intervalo"], bool(anterior and anterior.correccion))
        self.resumen.setText(f"Simulación sin aplicar puntos · Antes: {anterior.alcance if anterior else 0} · Ahora: {r.alcance} · Emisor {r.emisor}")
        tipo = "correccion" if r.correccion else "falsa" if r.verdadera is False else "verdadera" if r.verdadera is True else "exploracion"
        self.iniciar_animacion(r.niveles, r.aristas, r.emisor, tipo)

class DialogoIlustrado(QDialog):
    def ajustar_tamano(self, ancho, alto):
        """Deja espacio para la ventana y el marco en pantallas pequeñas."""
        referencia = self.parentWidget()
        disponible = referencia.size() if referencia is not None else self.screen().availableGeometry().size()
        self.resize(min(ancho, max(560, disponible.width()-80)),
                    min(alto, max(500, disponible.height()-64)))

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#182d41"))
        if dibujar_fondo(p, self.rect(), "fondos/investigacion.png"):
            p.fillRect(self.rect(), QColor(15, 31, 44, 190))
        panel = pixmap_arte("ui/panel.png")
        if not panel.isNull():
            _nueve_segmentos(p, QRectF(self.rect()).adjusted(7, 7, -7, -7), panel)
        p.end()


class _TarjetaRol(BotonIlustrado):
    """Tarjeta seleccionable con imagen, sin incrustar texto en el recurso."""
    def __init__(self, rol, parent=None):
        super().__init__("", parent, recurso="ui/panel.png")
        self.rol = rol
        self.setCheckable(True)
        self.setAccessibleName("Seleccionar " + ROLES[rol]["nombre"])
        self.setMinimumSize(220, 260)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        retrato = pixmap_arte(f"personajes/{self.rol}_retrato.png")
        if retrato.isNull():
            retrato = pixmap_arte(f"personajes/{self.rol}_neutral.png")
        if retrato.isNull():
            retrato = pixmap_recurso("assets/personajes/" + ("Ciudadano.png" if self.rol == "ciudadano" else "periodista.png"))
        if not retrato.isNull():
            limite = QRectF(25, 26, self.width()-50, self.height()-126)
            factor = min(limite.width()/retrato.width(), limite.height()/retrato.height())
            ancho, alto = retrato.width()*factor, retrato.height()*factor
            p.drawPixmap(QRectF(limite.center().x()-ancho/2, limite.bottom()-alto, ancho, alto),
                         retrato, QRectF(retrato.rect()))
        p.setPen(QColor("#f7dfb5"))
        fuente = QFont(FUENTE_UI)
        fuente.setPixelSize(round(max(23, min(28, self.width()/12))))
        fuente.setWeight(QFont.Weight.DemiBold)
        p.setFont(fuente)
        p.drawText(QRectF(24, self.height()-88, self.width()-48, 34),
                   Qt.AlignmentFlag.AlignCenter, ROLES[self.rol]["nombre"])
        fuente.setPixelSize(16)
        fuente.setWeight(QFont.Weight.Normal)
        p.setFont(fuente)
        p.setPen(QColor("#c0d0c2"))
        p.drawText(QRectF(24, self.height()-53, self.width()-48, 27),
                   Qt.AlignmentFlag.AlignCenter, "Seleccionado" if self.isChecked() else "Elegir personaje")
        p.end()


class DialogoRol(DialogoIlustrado):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tu papel en Ciudad Nova")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 54, 48, 40)
        layout.setSpacing(14)
        self.titulo = QLabel("TU VOZ CAMBIA LA CIUDAD")
        self.titulo.setStyleSheet("font-size: 27px; font-weight: 600; color: #f2d1a3;")
        layout.addWidget(self.titulo)
        self.subtitulo = QLabel("Elige a quién acompañarás durante esta historia.")
        self.subtitulo.setWordWrap(True)
        self.subtitulo.setStyleSheet("font-size: 18px;")
        layout.addWidget(self.subtitulo)
        self.roles = QComboBox()
        for id in ROLES_JUGABLES:
            rol = ROLES[id]
            self.roles.addItem(rol["nombre"], id)
        self.roles.hide()
        tarjetas = QHBoxLayout()
        tarjetas.setSpacing(22)
        self.tarjetas = {}
        self.grupo_roles = QButtonGroup(self)
        self.grupo_roles.setExclusive(True)
        for indice, id in enumerate(ROLES_JUGABLES):
            tarjeta = _TarjetaRol(id)
            tarjeta.clicked.connect(lambda _, indice=indice: self.roles.setCurrentIndex(indice))
            self.grupo_roles.addButton(tarjeta, indice)
            self.tarjetas[id] = tarjeta
            tarjetas.addWidget(tarjeta)
        layout.addLayout(tarjetas, 1)
        self.detalle = QLabel()
        self.detalle.setWordWrap(True)
        self.detalle.setMinimumHeight(36)
        self.detalle.setStyleSheet("color: #c5dbc9; font-size: 17px;")
        self.roles.currentIndexChanged.connect(self.actualizar)
        layout.addWidget(self.detalle)
        boton = BotonIlustrado("Comenzar la historia →")
        boton.clicked.connect(self.accept)
        layout.addWidget(boton)
        self.actualizar()
        aplicar_estilo(self)
        disponible = parent.size() if parent is not None else self.screen().availableGeometry().size()
        ancho = 840 if disponible.width() >= 1600 else 760 if disponible.width() >= 1300 else 700
        alto = 660 if disponible.height() >= 850 else 610 if disponible.height() >= 740 else 570
        self.ajustar_tamano(ancho, alto)

    def actualizar(self):
        rol = self.roles.currentData()
        self.detalle.setText(ROLES[rol]["habilidad"])
        if hasattr(self, "tarjetas"):
            self.tarjetas[rol].setChecked(True)
            for tarjeta in self.tarjetas.values():
                tarjeta.update()


def mostrar_ayuda(parent):
    dialogo = DialogoIlustrado(parent)
    dialogo.setWindowTitle("Manual de usuario · CIVICA")
    dialogo.setStyleSheet(ESTILO)
    layout = QVBoxLayout(dialogo)
    layout.setContentsMargins(48, 54, 48, 36)
    layout.setSpacing(16)
    texto = QTextBrowser()
    texto.setHtml("""<h2>Construye una Ciudad Nova informada</h2>
    <p>Cuida la confianza, la convivencia y el bienestar antes de la elección.</p>
    <p><b>Espacio, Enter o clic:</b> revelar el texto; otra interacción continúa.
    Tab y Enter permiten seleccionar botones. F11 cambia la pantalla; F1 abre este manual.
    El engranaje de la esquina superior derecha abre Configuración.</p>
    <p><b>Compartir:</b> difunde entre tus conexiones. Las noticias falsas perjudican a la ciudad;
    la información verdadera favorece la participación. El alcance depende de la red.</p>
    <p><b>Verificar:</b> consulta las fuentes y, ante un rumor falso, difunde una corrección.</p>
    <p><b>Ignorar:</b> no inicia difusión. <b>Reportar:</b> retira contenido falso o dañino;
    denunciar noticias verdaderas sin fundamento perjudica tu reputación.</p>
    <p>Los personajes seleccionables son el ciudadano y la periodista.
    Ciudadano: bonificación al verificar. Periodista: más confianza por verificar.
    El influencer y los candidatos pertenecen a la historia.</p>
    <p>Los puntos y la reputación son individuales. Los indicadores pertenecen a toda la ciudad.
    Tus acciones influyen en el apoyo de cuatro candidatos ficticios y en el final narrativo.</p>
    <p><b>Observatorio:</b> la difusión avanza automáticamente a un ritmo fijo y se repite
    dos segundos después de terminar. BFS explora por niveles; DFS sigue cada cadena de conexiones.
    Selecciona un ciudadano de origen y usa <b>Comparar alcance</b> para simular desde esa persona
    sin cambiar tus puntos ni aplicar otra decisión.</p>
    <p><b>Una comunidad que crece:</b> nuevos ciudadanos y sus conexiones se incorporan
    a medida que avanza la historia. El observatorio anuncia sus nombres y los marca con un aro punteado.
    Selecciona un retrato para consultar sus conexiones.</p>
    <p>En las alertas urgentes, el tiempo agotado equivale a ignorar. Puedes desactivar el límite
    o reducir movimiento desde Configuración; al reducirlo, el observatorio muestra el recorrido completo
    sin repetir la animación. También puedes adaptar los colores al daltonismo, activar alto contraste
    y ajustar por separado las voces de los personajes y del narrador. Toda señal sonora importante
    tiene texto visible.</p>
    <p>En multijugador, espera tu turno. El servidor conserva el estado y sincroniza las decisiones.</p>""")
    layout.addWidget(texto)
    cerrar = QPushButton("Volver")
    cerrar.clicked.connect(dialogo.accept)
    layout.addWidget(cerrar)
    dialogo.resize(640, 550)
    aplicar_estilo(dialogo)
    dialogo.exec()


def mostrar_configuracion(parent):
    from configuracion import guardar
    dialogo = DialogoIlustrado(parent)
    dialogo.setWindowTitle("Configuración y accesibilidad")
    dialogo.setStyleSheet(ESTILO)
    layout = QVBoxLayout(dialogo)
    layout.setContentsMargins(48, 54, 48, 36)
    layout.setSpacing(14)
    titulo = QLabel("TU EXPERIENCIA EN CIVICA")
    titulo.setStyleSheet("font-size: 24px; color: #f2d1a3; font-weight: 600;")
    layout.addWidget(titulo)
    pestanas = QTabWidget()
    pestanas.setAccessibleName("Categorías de configuración")
    layout.addWidget(pestanas, 1)
    accesibilidad = QWidget()
    opciones = QVBoxLayout(accesibilidad)
    opciones.setContentsMargins(16, 18, 16, 14)
    opciones.setSpacing(14)
    colores = QLabel("Colores para daltonismo")
    opciones.addWidget(colores)
    daltonismo = QComboBox()
    daltonismo.setAccessibleName("Modo de colores para daltonismo")
    daltonismo.setMinimumHeight(42)
    for nombre, clave in (("Colores originales", "normal"),
                          ("Deuteranopia · dificultad con el verde", "deuteranopia"),
                          ("Protanopia · dificultad con el rojo", "protanopia"),
                          ("Tritanopia · dificultad con el azul", "tritanopia")):
        daltonismo.addItem(nombre, clave)
    daltonismo.setCurrentIndex(max(0, daltonismo.findData(getattr(parent, "modo_daltonismo", "normal"))))
    opciones.addWidget(daltonismo)
    ayuda_color = QLabel("Los estados también usan texto, símbolos y distintos trazos para poder reconocerlos sin depender del color.")
    ayuda_color.setWordWrap(True)
    ayuda_color.setStyleSheet("color: #c2d3c9; font-size: 14px;")
    opciones.addWidget(ayuda_color)
    controles = {}
    for clave, texto, valor in (("sin_limite", "Decisiones sin límite de tiempo", parent.sin_limite),
                                ("reducir_movimiento", "Reducir movimiento y evitar recorridos repetidos", parent.reducir_movimiento),
                                ("alto_contraste", "Alto contraste", parent.alto_contraste)):
        check = QCheckBox(texto)
        check.setChecked(valor)
        controles[clave] = check
        opciones.addWidget(check)
    opciones.addStretch()
    pestanas.addTab(accesibilidad, "Accesibilidad")
    sonido = QWidget()
    audio_layout = QVBoxLayout(sonido)
    audio_layout.setContentsMargins(16, 18, 16, 14)
    audio_layout.setSpacing(14)
    silenciado = QCheckBox("Silenciar todo el audio")
    silenciado.setChecked(parent.audio.silenciado)
    controles["silenciado"] = silenciado
    audio_layout.addWidget(silenciado)
    voces = QCheckBox("Voces de los personajes y del narrador")
    voces.setChecked(getattr(parent, "voces_activadas", True))
    voces.setEnabled(hasattr(parent.audio, "configurar_voces"))
    audio_layout.addWidget(voces)
    if hasattr(parent.audio, "descripcion_voces"):
        estado_voces = QLabel(parent.audio.descripcion_voces())
        estado_voces.setWordWrap(True)
        estado_voces.setStyleSheet("font-size: 13px; color: #c2d3c9;")
        audio_layout.addWidget(estado_voces)
    for categoria, volumen in parent.audio.volumenes.items():
        fila = QHBoxLayout()
        etiqueta = QLabel("Volumen " + ("de voces" if categoria == "voces" else categoria))
        etiqueta.setMinimumWidth(155)
        fila.addWidget(etiqueta)
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setAccessibleName(etiqueta.text())
        slider.setRange(0, 100)
        slider.setValue(round(volumen*100))
        numero = QLabel(str(slider.value()) + "%")
        numero.setMinimumWidth(45)
        slider.valueChanged.connect(lambda valor, categoria=categoria: parent.audio.configurar(categoria, valor/100))
        slider.valueChanged.connect(lambda valor, numero=numero: numero.setText(str(valor) + "%"))
        fila.addWidget(slider, 1)
        fila.addWidget(numero)
        audio_layout.addLayout(fila)
    audio_layout.addStretch()
    pestanas.addTab(sonido, "Sonido y voces")
    manual = BotonIlustrado("Manual de usuario")
    manual.setToolTip("Controles, decisiones y reglas del juego · F1")
    manual.clicked.connect(lambda: mostrar_ayuda(dialogo))
    layout.addWidget(manual)

    def aplicar():
        parent.audio.silenciar(controles["silenciado"].isChecked())
        parent.sin_limite = controles["sin_limite"].isChecked()
        parent.reducir_movimiento = controles["reducir_movimiento"].isChecked()
        parent.alto_contraste = controles["alto_contraste"].isChecked()
        parent.modo_daltonismo = daltonismo.currentData()
        parent.voces_activadas = voces.isChecked()
        if hasattr(parent.audio, "configurar_voces"):
            parent.audio.configurar_voces(parent.voces_activadas)
        parent.aplicar_accesibilidad()
        guardar({"volumenes": parent.audio.volumenes, "silenciado": parent.audio.silenciado,
                 "sin_limite": parent.sin_limite, "reducir_movimiento": parent.reducir_movimiento,
                 "alto_contraste": parent.alto_contraste,
                 "modo_daltonismo": parent.modo_daltonismo,
                 "voces_activadas": parent.voces_activadas,
                 "sprites_sobre_ilustracion": parent.sprites_sobre_ilustracion})
        dialogo.accept()
    boton = BotonIlustrado("Guardar preferencias")
    boton.clicked.connect(aplicar)
    layout.addWidget(boton)
    dialogo.resize(720, 670)
    aplicar_estilo(dialogo)
    dialogo.exec()


class DialogoRed(DialogoIlustrado):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("CIVICA · Sala local")
        self.setStyleSheet(ESTILO)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 54, 48, 36)
        layout.setSpacing(12)
        titulo = QLabel("UNA CIUDAD, VARIAS VOCES")
        titulo.setStyleSheet("font-size: 21px; color: #f2d1a3; font-weight: 600;")
        layout.addWidget(titulo)
        self.nombre = QLineEdit("Alex")
        self.nombre.setMaxLength(30)
        self.host = QLineEdit("127.0.0.1")
        self.puerto = QLineEdit("8765")
        self.rol = QComboBox()
        for id in ROLES_JUGABLES:
            datos = ROLES[id]
            self.rol.addItem(datos["nombre"], id)
        campos = QGridLayout()
        campos.setHorizontalSpacing(16)
        campos.setVerticalSpacing(8)
        for fila, (titulo, widget) in enumerate((("Tu nombre", self.nombre), ("Personaje", self.rol),
                                                ("Servidor", self.host), ("Puerto", self.puerto))):
            campos.addWidget(QLabel(titulo), fila, 0)
            campos.addWidget(widget, fila, 1)
        layout.addLayout(campos)
        fila = QHBoxLayout()
        for titulo, crear in (("Crear sala local", True), ("Unirse", False)):
            boton = QPushButton(titulo)
            boton.clicked.connect(lambda _, crear=crear: self.conectar(crear))
            fila.addWidget(boton)
        layout.addLayout(fila)
        self.estado = QLabel("Dos a cuatro participantes. Puedes elegir ciudadano o periodista; los personajes se pueden repetir.")
        self.estado.setWordWrap(True)
        layout.addWidget(self.estado)
        iniciar = QPushButton("Iniciar campaña (anfitrión)")
        iniciar.clicked.connect(lambda: parent.cliente_red.enviar({"tipo": "iniciar"}) if parent.cliente_red else None)
        layout.addWidget(iniciar)
        aplicar_estilo(self)
        self.resize(650, 530)

    def conectar(self, crear):
        try:
            puerto = int(self.puerto.text())
            if not 1 <= puerto <= 65535:
                raise ValueError("Puerto fuera de rango")
            self.parent().conectar_red(crear, self.host.text().strip(), puerto,
                                      self.nombre.text().strip(), self.rol.currentData())
            self.estado.setText("Conectando…")
        except (OSError, ValueError) as error:
            self.estado.setText(str(error))
