"""Desenlace electoral: resultados reales, retrato electo y balance legible."""
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from arte import (
    BotonIlustrado, FUENTE_UI, PanelIlustrado, aplicar_estilo,
    dibujar_fondo, pixmap_arte,
)
from juego.finales import epilogo
from recursos import RAIZ


IDS_CANDIDATOS = ("juan", "adrian", "laura", "camila")


def retrato_candidato(identificador, electo=False):
    """El arte de investidura es opcional; el atlas original sigue disponible."""
    if identificador not in IDS_CANDIDATOS:
        return QPixmap()
    if electo:
        ruta = RAIZ / "assets" / "expansion" / "candidatos" / f"{identificador}_electo.png"
        if ruta.is_file():
            imagen = QPixmap(str(ruta))
            if not imagen.isNull():
                return imagen
    atlas = pixmap_arte("personajes/candidatos.png")
    if atlas.isNull():
        return QPixmap()
    indice = IDS_CANDIDATOS.index(identificador)
    x0, x1 = round((indice % 2) * atlas.width() / 2), round((indice % 2 + 1) * atlas.width() / 2)
    y0, y1 = round((indice // 2) * atlas.height() / 2), round((indice // 2 + 1) * atlas.height() / 2)
    return atlas.copy(x0, y0, x1 - x0, y1 - y0)


def _tipografia(etiqueta, tamano, color="#f6e8cd", negrita=False):
    # El stylesheet global de la ventana también declara fuentes. Es necesario
    # definirla en cada etiqueta, incluido el contenido del área desplazable.
    etiqueta.setFont(QFont(FUENTE_UI, 12))
    etiqueta.setStyleSheet(
        f"font-family:'{FUENTE_UI}'; font-size:{tamano}px; "
        f"font-weight:{700 if negrita else 400}; color:{color}; background:transparent;"
    )


class _ImagenFinal(QWidget):
    """Ilustración sin estirar y composición múltiple cuando existe empate."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.imagenes = []
        self.retrato_electo = False
        self.setMinimumSize(140, 100)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def establecer(self, imagenes, retrato_electo=False):
        self.imagenes = list(imagenes)
        self.retrato_electo = retrato_electo
        self.update()

    def paintEvent(self, event):
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        marco = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        recorte = QPainterPath()
        recorte.addRoundedRect(marco, 12, 12)
        pintor.setClipPath(recorte)
        gradiente = QLinearGradient(marco.topLeft(), marco.bottomRight())
        gradiente.setColorAt(0, QColor("#355268"))
        gradiente.setColorAt(.55, QColor("#1b3348"))
        gradiente.setColorAt(1, QColor("#102230"))
        pintor.fillRect(marco, gradiente)
        cantidad = len(self.imagenes)
        columnas = 1 if cantidad <= 1 else 2
        filas = 2 if cantidad > 2 else 1
        for indice, imagen in enumerate(self.imagenes):
            if imagen.isNull():
                continue
            celda = QRectF(
                marco.left() + (indice % columnas) * marco.width() / columnas,
                marco.top() + (indice // columnas) * marco.height() / filas,
                marco.width() / columnas, marco.height() / filas,
            )
            if self.retrato_electo and cantidad == 1:
                # La ilustración de investidura es vertical. En una ventana
                # corta mostramos el rostro y el torso, conservando al menos
                # media imagen en altura para no cortar la cabeza. El recorte
                # se ancla cerca del borde superior, donde está el personaje.
                escala = min(max(celda.width() / imagen.width(), celda.height() / imagen.height()),
                             celda.height() / (imagen.height() * .5))
                ancho = imagen.width() * escala
                alto_origen = min(imagen.height(), celda.height() / escala)
                y_origen = (imagen.height() - alto_origen) * .12
                origen = QRectF(0, y_origen, imagen.width(), alto_origen)
                destino = QRectF(celda.center().x() - ancho / 2, celda.top(), ancho, celda.height())
                pintor.drawPixmap(destino, imagen, origen)
            else:
                # Los retratos de respaldo y la composición de empate se
                # muestran completos, sin alterar sus proporciones.
                escala = min(celda.width() / imagen.width(), celda.height() / imagen.height())
                ancho, alto = imagen.width() * escala, imagen.height() * escala
                destino = QRectF(celda.center().x() - ancho / 2, celda.bottom() - alto, ancho, alto)
                pintor.drawPixmap(destino, imagen, QRectF(imagen.rect()))
        pintor.setClipping(False)
        pintor.setPen(QPen(QColor("#aa895c"), 1))
        pintor.setBrush(Qt.BrushStyle.NoBrush)
        pintor.drawRoundedRect(marco, 12, 12)


class _TarjetaCandidato(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tarjetaCandidato")
        self.retrato_original = QPixmap()
        self.candidato_id = None
        self.elegido = False
        fila = QHBoxLayout(self)
        fila.setContentsMargins(12, 10, 12, 10)
        fila.setSpacing(10)
        self.retrato = QLabel()
        self.retrato.setFixedSize(58, 66)
        self.retrato.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fila.addWidget(self.retrato)
        datos = QVBoxLayout()
        datos.setSpacing(1)
        self.nombre = QLabel()
        self.nombre.setWordWrap(True)
        self.nombre.setMinimumWidth(0)
        self.nombre.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.porcentaje = QLabel()
        datos.addWidget(self.nombre)
        datos.addWidget(self.porcentaje)
        fila.addLayout(datos, 1)

    def establecer(self, candidato, porcentaje, elegido):
        self.candidato_id = candidato.id
        self.elegido = elegido
        self.nombre.setText(candidato.nombre)
        self.porcentaje.setText(f"{porcentaje:.1f}%")
        self.retrato_original = retrato_candidato(candidato.id)
        self.retrato.setPixmap(self.retrato_original.scaled(
            self.retrato.size(), Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        ))
        self.setAccessibleName(f"{candidato.nombre}, {porcentaje:.1f} por ciento" + (", mayor votación" if elegido else ""))
        borde = "#e8c78f" if elegido else "#5d7178"
        fondo = "rgba(74,91,94,135)" if elegido else "rgba(8,25,39,140)"
        self.setStyleSheet(f"QFrame#tarjetaCandidato {{background:{fondo}; border:1px solid {borde}; border-radius:12px;}}")


class EscenaFin(QWidget):
    """Muestra los cuatro porcentajes y el epílogo de la misma elección."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.eleccion = None
        self.ganador_id = None
        self.exterior = QVBoxLayout(self)
        self.exterior.setContentsMargins(24, 18, 24, 18)
        self.panel = PanelIlustrado()
        self.contenido = QVBoxLayout(self.panel)
        self.contenido.setContentsMargins(30, 24, 30, 24)
        self.contenido.setSpacing(14)
        self.titulo_final = QLabel("El futuro de Ciudad Nova")
        self.titulo_final.setWordWrap(True)
        self.titulo_final.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.contenido.addWidget(self.titulo_final)

        self.fila_candidatos = QHBoxLayout()
        self.fila_candidatos.setSpacing(12)
        self.tarjetas = [_TarjetaCandidato() for _ in IDS_CANDIDATOS]
        # Se conserva el acceso a los retratos para integraciones existentes.
        self.tarjetas_candidatos = [(tarjeta.retrato, tarjeta.nombre) for tarjeta in self.tarjetas]
        for tarjeta in self.tarjetas:
            self.fila_candidatos.addWidget(tarjeta, 1)
        self.contenido.addLayout(self.fila_candidatos)

        self.fila_desenlace = QHBoxLayout()
        self.fila_desenlace.setSpacing(22)
        self.panel_ganador = QFrame()
        self.panel_ganador.setMinimumWidth(240)
        self.fila_hero = QVBoxLayout(self.panel_ganador)
        self.fila_hero.setContentsMargins(0, 0, 0, 0)
        self.fila_hero.setSpacing(7)
        self.imagen_ganador = _ImagenFinal()
        self.imagen_ganador.setAccessibleName("Retrato de la candidatura electa")
        self.fila_hero.addWidget(self.imagen_ganador, 1)
        self.estado_eleccion = QLabel("ALCALDÍA ELECTA")
        self.estado_eleccion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fila_hero.addWidget(self.estado_eleccion)
        self.ganador = QLabel()
        self.ganador.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ganador.setWordWrap(True)
        self.fila_hero.addWidget(self.ganador)
        self.fila_desenlace.addWidget(self.panel_ganador, 4)

        self.area_resumen = QScrollArea()
        self.area_resumen.setWidgetResizable(True)
        self.area_resumen.setFrameShape(QFrame.Shape.NoFrame)
        self.area_resumen.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.area_resumen.setStyleSheet("QScrollArea {background:transparent; border:0;}")
        self.area_resumen.viewport().setAutoFillBackground(False)
        self.relato = QWidget()
        self.relato.setStyleSheet("background:transparent;")
        self.relato_layout = QVBoxLayout(self.relato)
        self.relato_layout.setContentsMargins(4, 4, 12, 4)
        self.relato_layout.setSpacing(14)
        self.leyenda_cierre = QLabel("EL FUTURO QUE CONSTRUIMOS")
        self.relato_layout.addWidget(self.leyenda_cierre)
        self.texto_final = QLabel()
        self.texto_final.setWordWrap(True)
        self.texto_final.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.texto_final.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.relato_layout.addWidget(self.texto_final)
        self.balance = QLabel()
        self.balance.setWordWrap(True)
        self.relato_layout.addWidget(self.balance)
        self.leyenda_jugadores = QLabel("TU HUELLA EN CIUDAD NOVA")
        self.relato_layout.addWidget(self.leyenda_jugadores)
        self.puntuaciones = QLabel()
        self.puntuaciones.setWordWrap(True)
        self.puntuaciones.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.relato_layout.addWidget(self.puntuaciones)
        self.relato_layout.addStretch(1)
        self.area_resumen.setWidget(self.relato)
        self.fila_desenlace.addWidget(self.area_resumen, 6)
        self.contenido.addLayout(self.fila_desenlace, 1)

        self.boton_volver = BotonIlustrado("Regresar a Ciudad Nova")
        self.boton_volver.setFixedSize(284, 52)
        self.boton_volver.clicked.connect(lambda: self.window().volver_portada())
        self.contenido.addWidget(self.boton_volver, 0, Qt.AlignmentFlag.AlignRight)
        self.exterior.addWidget(self.panel)
        aplicar_estilo(self)
        self._ajustar_presentacion()

    def _ajustar_presentacion(self):
        compacto = self.width() < 1250 or self.height() < 640
        grande = self.width() >= 1700 and self.height() >= 800
        margen = 20 if compacto else 30
        self.contenido.setContentsMargins(margen, 18 if compacto else 24, margen, 18 if compacto else 24)
        self.contenido.setSpacing(10 if compacto else 14)
        self.fila_desenlace.setStretch(0, 3 if compacto else 4)
        self.fila_desenlace.setStretch(1, 7 if compacto else 6)
        self.exterior.setContentsMargins(18 if compacto else 24, 14 if compacto else 18,
                                        18 if compacto else 24, 14 if compacto else 18)
        _tipografia(self.titulo_final, 25 if compacto else 32 if grande else 28, "#f2d6a5", True)
        _tipografia(self.estado_eleccion, 13 if compacto else 15, "#cfb07e", True)
        _tipografia(self.ganador, 22 if compacto else 30 if grande else 25, "#fff1d7", True)
        _tipografia(self.leyenda_cierre, 13 if compacto else 15, "#d7ba8b", True)
        _tipografia(self.texto_final, 18 if compacto else 22 if grande else 20)
        _tipografia(self.balance, 16 if compacto else 18, "#b7cfd0")
        _tipografia(self.leyenda_jugadores, 13 if compacto else 15, "#d7ba8b", True)
        _tipografia(self.puntuaciones, 16 if compacto else 19 if grande else 17, "#e4dbc7")
        _tipografia(self.boton_volver, 18, "#fff0d1", True)
        self.boton_volver.setStyleSheet(
            self.boton_volver.styleSheet()
            + "min-height:52px; max-height:52px; padding:0; border:0;"
        )
        for tarjeta in self.tarjetas:
            _tipografia(tarjeta.nombre, 17 if compacto else 21 if grande else 19)
            _tipografia(tarjeta.porcentaje, 24 if compacto else 30 if grande else 27, "#f2d6a5", True)
            tarjeta.setFixedHeight(96 if compacto else 108 if grande else 102)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._ajustar_presentacion()

    def paintEvent(self, event):
        pintor = QPainter(self)
        if not dibujar_fondo(pintor, self.rect(), "fondos/ciudad.png"):
            pintor.fillRect(self.rect(), QColor("#182d41"))
        pintor.fillRect(self.rect(), QColor(10, 20, 34, 100))

    def mostrar(self):
        juego = self.window().juego
        self.eleccion = eleccion = juego.resultado_electoral()
        self.titulo_final.setText(eleccion["final"])
        ganadores = [c for c in juego.candidatos if c.nombre in eleccion["ganadores"]]
        self.ganador_id = None if eleccion["empate"] else ganadores[0].id
        self.estado_eleccion.setText("EMPATE ELECTORAL · RECUENTO PENDIENTE" if eleccion["empate"] else "ALCALDÍA ELECTA")
        self.estado_eleccion.setWordWrap(True)
        self.ganador.setText(" · ".join(c.nombre for c in ganadores))
        self.imagen_ganador.setAccessibleName("Candidaturas empatadas" if eleccion["empate"] else f"Retrato de {ganadores[0].nombre}, candidatura electa")
        tiene_investidura = self.ganador_id is not None and (
            RAIZ / "assets" / "expansion" / "candidatos" / f"{self.ganador_id}_electo.png"
        ).is_file()
        self.imagen_ganador.establecer(
            [retrato_candidato(c.id, electo=not eleccion["empate"]) for c in ganadores],
            retrato_electo=tiene_investidura,
        )
        for candidato, tarjeta in zip(juego.candidatos, self.tarjetas):
            tarjeta.establecer(candidato, eleccion["porcentajes"][candidato.id], candidato in ganadores)
        self.texto_final.setText(epilogo(juego, eleccion))
        self.balance.setText(
            f"{len(juego.historial)} decisiones registradas · Confianza {juego.confianza} · "
            f"Convivencia {juego.convivencia} · Desinformación {juego.desinformacion}."
        )
        self.puntuaciones.setText("\n\n".join(
            f"{jugador.nombre} · {jugador.puntos} puntos · Reputación {jugador.reputacion}\n"
            + (", ".join(jugador.logros) or "Nuevos aprendizajes")
            for jugador in juego.jugadores
        ))
        self._ajustar_presentacion()
        self.area_resumen.verticalScrollBar().setValue(0)
        self.setFocus()
