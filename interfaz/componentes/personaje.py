"""interfaz.componentes.personaje: presentación separada de las reglas del juego."""
from pathlib import Path
from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect
from PyQt6.QtGui import QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt, QRect, QPoint, QPropertyAnimation, QParallelAnimationGroup, QAbstractAnimation, QEasingCurve
from infraestructura.recursos import pixmap_recurso
from interfaz.componentes.personajes_animados import SpriteExpresivo, ACTORES_NUEVOS


_PIXMAPS_OSCUROS = {}


class PersonajeVisual(QWidget):

    def __init__(self, ruta_imagen, parent=None):
        super().__init__(parent)

        self.ruta_imagen = ruta_imagen
        self.pixmap_original = QPixmap()
        self.pixmap_oscuro = QPixmap()

        self.imagen = SpriteExpresivo(self)
        self.imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.imagen.setStyleSheet("background: transparent;")
        self.imagen.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )

        self.imagen_oscura = SpriteExpresivo(self, sombra=True)
        self.imagen_oscura.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.imagen_oscura.setStyleSheet("background: transparent;")
        self.imagen_oscura.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )

        self.efecto_fade = QGraphicsOpacityEffect(self.imagen)
        self.efecto_fade.setOpacity(0.0)
        self.imagen.setGraphicsEffect(self.efecto_fade)

        self.efecto_dimming = QGraphicsOpacityEffect(
            self.imagen_oscura
        )
        self.efecto_dimming.setOpacity(0.0)
        self.imagen_oscura.setGraphicsEffect(
            self.efecto_dimming
        )

        self.animacion_fade = None
        self.animacion_dim = None
        self.animacion_entrada = None
        self.animacion_salida = None

        self.cargar_imagen()
        clave = Path(ruta_imagen).stem.split("_")[0].lower()
        rol = clave if clave in ACTORES_NUEVOS else "periodista" if "periodista" in ruta_imagen.lower() else "ciudadano"
        self.establecer_expresion(rol, "neutral")

    def establecer_expresion(self, rol, expresion):
        for lienzo in (self.imagen, self.imagen_oscura):
            lienzo.configurar_actor(rol, expresion)

    def establecer_hablando(self, hablando, nivel=None):
        for lienzo in (self.imagen, self.imagen_oscura):
            lienzo.establecer_hablando(hablando, nivel)

    def orientar_hacia(self, direccion):
        for lienzo in (self.imagen, self.imagen_oscura):
            lienzo.orientar_hacia(direccion)

    def establecer_encuadre(self, x, y, ancho, alto):
        """Actualiza también el destino de una entrada que sigue en curso."""
        self._encuadre_objetivo = QRect(x, y, ancho, alto)
        self.setGeometry(self._encuadre_objetivo)
        entrada = self.animacion_entrada
        posicion = getattr(self, "_posicion_entrada", None)
        if (entrada is not None and posicion is not None
                and entrada.state() == QAbstractAnimation.State.Running):
            posicion.setStartValue(self._encuadre_objetivo.topLeft() + QPoint(0, 55))
            posicion.setEndValue(self._encuadre_objetivo.topLeft())

    def _detener_animaciones(self):
        for animacion in (self.animacion_fade, self.animacion_dim,
                          self.animacion_entrada, self.animacion_salida):
            if animacion is not None:
                animacion.stop()

    def ocultar_inmediato(self):
        """Un cambio de plano no deja fundidos ni salidas del reparto previo."""
        self._detener_animaciones()
        self.establecer_hablando(False)
        self.hide()
        self.efecto_fade.setOpacity(0.0)
        self.efecto_dimming.setOpacity(0.0)

    def _finalizar_entrada(self):
        encuadre = getattr(self, "_encuadre_objetivo", None)
        if encuadre is not None:
            self.setGeometry(encuadre)

    def cargar_imagen(self):
        pixmap = pixmap_recurso(self.ruta_imagen)

        if pixmap.isNull():
            self.imagen.setText(
                f"No se encontró el personaje:\n{self.ruta_imagen}"
            )
            self.imagen.setStyleSheet(
                "color: white; background: transparent;"
            )
            return

        self.pixmap_original = pixmap
        self.pixmap_oscuro = self.crear_pixmap_oscuro(
            pixmap,
            0.48
        )

        self.actualizar_imagenes()

    def crear_pixmap_oscuro(self, pixmap, factor):
        clave = (pixmap.cacheKey(), factor)
        if clave in _PIXMAPS_OSCUROS:
            return _PIXMAPS_OSCUROS[clave]
        oscuro = QPixmap(pixmap.size())
        oscuro.fill(Qt.GlobalColor.transparent)

        painter = QPainter(oscuro)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )
        painter.setCompositionMode(
            QPainter.CompositionMode.CompositionMode_Source
        )
        painter.drawPixmap(
            0,
            0,
            pixmap
        )

        painter.setCompositionMode(
            QPainter.CompositionMode.CompositionMode_SourceIn
        )

        intensidad = max(0.0, min(1.0, 1.0 - factor))
        alpha = int(255 * intensidad)

        painter.fillRect(
            oscuro.rect(),
            QColor(0, 0, 0, alpha)
        )

        painter.end()
        if len(_PIXMAPS_OSCUROS) >= 12:
            _PIXMAPS_OSCUROS.clear()
        _PIXMAPS_OSCUROS[clave] = oscuro
        return oscuro

    def actualizar_imagenes(self):
        if self.pixmap_original.isNull():
            return

        margen_x = 10
        margen_y = 5

        ancho = max(1, self.width() - margen_x * 2)
        alto = max(1, self.height() - margen_y * 2)

        pixmap = self.pixmap_original.scaled(
            ancho,
            alto,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        pixmap_oscuro = self.pixmap_oscuro.scaled(
            ancho,
            alto,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.imagen.setPixmap(pixmap)
        self.imagen_oscura.setPixmap(pixmap_oscuro)

    def resizeEvent(self, event):
        self.imagen.setGeometry(self.rect())
        self.imagen_oscura.setGeometry(self.rect())
        self.actualizar_imagenes()
        super().resizeEvent(event)

    def aparecer(self, duracion=850):
        if getattr(self, "reducir_movimiento", False):
            duracion = 1
        self.show()
        self.raise_()

        self._detener_animaciones()

        self.efecto_fade.setOpacity(0.0)
        self.efecto_dimming.setOpacity(0.0)

        posicion_final = self.pos()
        posicion_inicial = posicion_final + QPoint(0, 55)
        self.move(posicion_inicial)

        animacion_fade = QPropertyAnimation(
            self.efecto_fade,
            b"opacity",
            self
        )
        animacion_fade.setDuration(duracion)
        animacion_fade.setStartValue(0.0)
        animacion_fade.setEndValue(1.0)
        animacion_fade.setEasingCurve(
            QEasingCurve.Type.OutCubic
        )

        animacion_posicion = QPropertyAnimation(
            self,
            b"pos",
            self
        )
        animacion_posicion.setDuration(duracion)
        animacion_posicion.setStartValue(posicion_inicial)
        animacion_posicion.setEndValue(posicion_final)
        animacion_posicion.setEasingCurve(
            QEasingCurve.Type.OutCubic
        )

        self.animacion_entrada = QParallelAnimationGroup(self)
        self._posicion_entrada = animacion_posicion
        self.animacion_entrada.addAnimation(animacion_fade)
        self.animacion_entrada.addAnimation(animacion_posicion)
        self.animacion_entrada.finished.connect(self._finalizar_entrada)
        self.animacion_fade = self.animacion_entrada
        self.animacion_entrada.start()

    def desaparecer(self, duracion=650):
        if getattr(self, "reducir_movimiento", False):
            duracion = 1
        if not self.isVisible():
            return

        if self.animacion_fade is not None:
            self.animacion_fade.stop()

        if self.animacion_entrada is not None:
            self.animacion_entrada.stop()

        posicion_inicial = self.pos()
        posicion_final = posicion_inicial + QPoint(0, 45)

        animacion_fade = QPropertyAnimation(
            self.efecto_fade,
            b"opacity",
            self
        )
        animacion_fade.setDuration(duracion)
        animacion_fade.setStartValue(
            self.efecto_fade.opacity()
        )
        animacion_fade.setEndValue(0.0)
        animacion_fade.setEasingCurve(
            QEasingCurve.Type.InCubic
        )

        animacion_posicion = QPropertyAnimation(
            self,
            b"pos",
            self
        )
        animacion_posicion.setDuration(duracion)
        animacion_posicion.setStartValue(posicion_inicial)
        animacion_posicion.setEndValue(posicion_final)
        animacion_posicion.setEasingCurve(
            QEasingCurve.Type.InCubic
        )

        grupo = QParallelAnimationGroup(self)
        grupo.addAnimation(animacion_fade)
        grupo.addAnimation(animacion_posicion)
        grupo.finished.connect(self.ocultar_y_restablecer)

        self.animacion_salida = grupo
        self.animacion_fade = grupo
        grupo.start()

    def ocultar_y_restablecer(self):
        self.hide()
        self.efecto_fade.setOpacity(0.0)
        self.efecto_dimming.setOpacity(0.0)

    def enfocar(self, duracion=350):
        if getattr(self, "reducir_movimiento", False):
            duracion = 1
        if not self.isVisible():
            return

        if self.animacion_dim is not None:
            self.animacion_dim.stop()

        self.animacion_dim = QPropertyAnimation(
            self.efecto_dimming,
            b"opacity",
            self
        )
        self.animacion_dim.setDuration(duracion)
        self.animacion_dim.setStartValue(
            self.efecto_dimming.opacity()
        )
        self.animacion_dim.setEndValue(0.0)
        self.animacion_dim.setEasingCurve(
            QEasingCurve.Type.InOutQuad
        )
        self.animacion_dim.start()

    def oscurecer(self, duracion=350, intensidad=0.58):
        if getattr(self, "reducir_movimiento", False):
            duracion = 1
        if not self.isVisible():
            return

        if self.animacion_dim is not None:
            self.animacion_dim.stop()

        self.animacion_dim = QPropertyAnimation(
            self.efecto_dimming,
            b"opacity",
            self
        )
        self.animacion_dim.setDuration(duracion)
        self.animacion_dim.setStartValue(
            self.efecto_dimming.opacity()
        )
        self.animacion_dim.setEndValue(intensidad)
        self.animacion_dim.setEasingCurve(
            QEasingCurve.Type.InOutQuad
        )
        self.animacion_dim.start()
