import sys
import math
import time
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFrame,
    QGraphicsOpacityEffect,
    QToolBar,
    QFileDialog,
    QMessageBox,
    QScrollArea,
    QToolButton,
    QMenu,
    QSizePolicy,
)
from PyQt6.QtGui import (
    QPixmap,
    QImage,
    QFont,
    QFontDatabase,
    QPainter,
    QPen,
    QBrush,
    QColor,
    QFontMetrics,
)
from PyQt6.QtCore import (
    Qt,
    QTimer,
    QSize,
    QRect,
    QRectF,
    QPoint,
    QPropertyAnimation,
    QParallelAnimationGroup,
    QEasingCurve,
    pyqtSignal,
)

from models.publicacion import Publicacion
from estructuras.bst import ArbolPublicaciones
from visualizador_bst import VisualizadorBST
from recursos import ruta_recurso, pixmap_recurso, RAIZ
from arte import PanelIlustrado, BotonIlustrado, aplicar_estilo, decorar_botones, pixmap_arte, dibujar_fondo, icono_arte, cargar_tipografias, avatar_arte, miniatura_publicacion, FUENTE_UI, FUENTE_DIALOGO, geometria_dialogo
from accesibilidad import paleta, MODOS_DALTONISMO
from publicaciones_ui import TarjetaPublicacion
from paneles import EscenaRed, DialogoRol, DialogoRed, mostrar_ayuda, mostrar_configuracion
from juego.historia import contenido_resultado, dialogos_publicacion
from juego.finales import epilogo
from audio.gestor_audio import GestorAudio
from hud import HudCiudad
from final_ui import EscenaFin

_PIXMAPS_OSCUROS = {}


class EscenaInicio(QWidget):
    continuar = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.fondo = QLabel(self)
        self.fondo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cartela = PanelIlustrado(self)
        self.logo = QLabel(self.cartela)
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.leyenda = QLabel("UNA CIUDAD. CADA DECISIÓN CUENTA.", self.cartela)
        self.leyenda.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.leyenda.setWordWrap(True)
        self.leyenda.setStyleSheet("color:#e4c59a; font:11pt 'Atkinson Hyperlegible'; background:transparent;")
        self.descripcion = QLabel("Lee entre líneas. Contrasta las fuentes.\nCuida los vínculos de Ciudad Nova.", self.cartela)
        self.descripcion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.descripcion.setStyleSheet("color:#f6e8cd; font:12pt 'Atkinson Hyperlegible'; background:transparent;")
        self.boton_inicio = BotonIlustrado("Comenzar historia", self.cartela)
        self.boton_inicio.setAccessibleName("Comenzar historia")
        self.boton_inicio.clicked.connect(self.iniciar)
        self.boton_cargar = BotonIlustrado("Continuar partida", self.cartela)
        self.boton_cargar.clicked.connect(lambda: self.window().cargar_partida())
        self.boton_multijugador = BotonIlustrado("Multijugador", self.cartela)
        self.boton_multijugador.clicked.connect(lambda: self.window().abrir_multijugador())
        self.credito = QLabel("Universidad del Norte · Estructura de Datos II", self.cartela)
        self.credito.setStyleSheet("color:#bdc5c7; font:9pt 'Atkinson Hyperlegible'; background:transparent;")
        self.credito.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def resizeEvent(self, event):
        self.actualizar_fondo()
        self.actualizar_boton()
        super().resizeEvent(event)

    def actualizar_fondo(self):
        pixmap = pixmap_recurso("assets/fondos/fondo escena portada.jfif")
        self.fondo.setGeometry(self.rect())
        if not pixmap.isNull():
            self.fondo.setPixmap(pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
        self.fondo.lower()

    def actualizar_boton(self):
        ancho = min(510, max(370, int(self.width() * 0.36)))
        alto = min(650, int(self.height() * 0.83))
        self.cartela.setGeometry(int(self.width() * 0.06), (self.height()-alto)//2, ancho, alto)
        marca = pixmap_arte("ui/logo.png")
        self.logo.setGeometry(45, int(alto*.09), ancho-90, int(alto*.34))
        if marca.isNull():
            self.logo.setText("CIVICA\nAlcalde Digital")
            self.logo.setStyleSheet("color:#f6e8cd; font:30pt 'Atkinson Hyperlegible'; background:transparent;")
        else:
            self.logo.setPixmap(marca.scaled(self.logo.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.leyenda.setGeometry(35, int(alto*.43), ancho-70, 50)
        self.descripcion.setGeometry(35, int(alto*.53), ancho-70, 65)
        self.boton_inicio.setGeometry(35, int(alto*.68), ancho-70, 57)
        self.boton_cargar.setGeometry(35, int(alto*.81), (ancho-80)//2, 48)
        self.boton_multijugador.setGeometry(45+(ancho-80)//2, int(alto*.81), (ancho-80)//2, 48)
        self.credito.setGeometry(25, alto-57, ancho-50, 26)

    def iniciar(self):
        self.continuar.emit()
        self.setFocus()

    def keyPressEvent(self, event):
        if not event.isAutoRepeat() and event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.iniciar()
            event.accept()
            return
        super().keyPressEvent(event)


class PersonajeVisual(QWidget):

    def __init__(self, ruta_imagen, parent=None):
        super().__init__(parent)

        self.ruta_imagen = ruta_imagen
        self.pixmap_original = QPixmap()
        self.pixmap_oscuro = QPixmap()

        self.imagen = QLabel(self)
        self.imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.imagen.setStyleSheet("background: transparent;")
        self.imagen.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )

        self.imagen_oscura = QLabel(self)
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

        if self.animacion_fade is not None:
            self.animacion_fade.stop()

        if self.animacion_dim is not None:
            self.animacion_dim.stop()

        if self.animacion_entrada is not None:
            self.animacion_entrada.stop()

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
        self.animacion_entrada.addAnimation(animacion_fade)
        self.animacion_entrada.addAnimation(animacion_posicion)
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


class EscenaCinematica(QFrame):

    dialogo_terminado = pyqtSignal()

    DURACION_FRANJAS = 450
    PAUSA_CINEMATICA = 80
    TIEMPO_ANTES_DE_HABLAR = 650

    RUTA_CIUDADANO = "assets/personajes/Ciudadano.png"
    RUTA_PERIODISTA = "assets/personajes/periodista.png"

    def __init__(self, fondo, parent=None):
        super().__init__(parent)

        self.fondo = fondo
        self.animacion = None
        self.animacion_personajes = None
        self.animacion_ocultar_personajes = None

        self.personajes = {
            "CIUDADANO": PersonajeVisual(
                self.RUTA_CIUDADANO,
                self
            ),
            "PERIODISTA": PersonajeVisual(
                self.RUTA_PERIODISTA,
                self
            )
        }

        self.personajes_activos = set()
        self.personajes_en_escena = set()
        self.hablante_actual = ""

        self.nombre_label = QLabel(self)
        self.texto_label = QLabel(self)

        self.fondo_label = QLabel(self)
        self.fondo_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.franja_superior = QFrame(self)
        self.franja_superior.setStyleSheet(
            "QFrame { background: transparent; border: none; }"
        )

        self.franja_inferior = PanelIlustrado(self, recurso="ui/dialogo.png")
        self.franja_inferior.setStyleSheet("background:transparent;border:none;")

        self.nombre_label.setStyleSheet(
            """
            QLabel {
                color: #F3CBB8;
                background: transparent;
                font-weight: bold;
            }
            """
        )
        self.nombre_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        self.texto_label.setStyleSheet(
            """
            QLabel {
                color: white;
                background: transparent;
            }
            """
        )
        self.texto_label.setWordWrap(True)
        self.texto_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft |
            Qt.AlignmentFlag.AlignVCenter
        )
        self.pista_continuar = QLabel("ESPACIO · revelar / continuar", self)
        self.pista_continuar.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.pista_continuar.setStyleSheet(f"color:#d3dfdf; font:14px '{FUENTE_UI}'; background:transparent;")
        self.pista_continuar.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.pista_continuar.hide()
        self.publicacion_telefono = None
        if self.fondo.endswith("Escena 3.png") and not pixmap_arte("fondos/telefono.png").isNull():
            self.publicacion_telefono = TarjetaPublicacion(self, telefono=True)

        self.texto_completo = ""
        self.nombre_inicial = ""
        self.escribiendo = False
        self.animando = False

        self.estado_escena = "inactiva"
        self.timer_inicio = QTimer(self)
        self.timer_inicio.setSingleShot(True)
        self.timer_inicio.timeout.connect(self.preparar_dialogo)
        self.timer_texto = QTimer(self)
        self.timer_texto.setInterval(34)
        self.timer_texto.timeout.connect(self.escribir_caracter)
        self.indice_texto = 0

        self.cargar_fuente()

        self.setFocusPolicy(
            Qt.FocusPolicy.StrongFocus
        )

    def cargar_fuente(self):
        cargar_tipografias()
        self.fuente_nombre = QFont(FUENTE_UI)
        self.fuente_nombre.setPixelSize(23)
        self.fuente_nombre.setBold(True)
        self.fuente_dialogo = QFont(FUENTE_DIALOGO)
        self.fuente_dialogo.setPixelSize(26)
        self.fuente_dialogo.setBold(False)
        self.nombre_label.setFont(self.fuente_nombre)
        self.texto_label.setFont(self.fuente_dialogo)

    def resizeEvent(self, event):
        self.actualizar_geometria()
        self.actualizar_fondo()
        super().resizeEvent(event)

    def actualizar_fondo(self):
        pixmap = pixmap_recurso(self.fondo)

        if pixmap.isNull():
            self.fondo_label.setStyleSheet(
                "background-color: #111111;"
            )
            self.fondo_label.setGeometry(self.rect())
            return

        pixmap_escalado = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )

        self.fondo_label.setPixmap(pixmap_escalado)
        self.fondo_label.setGeometry(self.rect())
        self.fondo_label.lower()

    def actualizar_geometria(self):
        ancho = self.width()
        alto = self.height()

        if ancho <= 0 or alto <= 0:
            return

        tam_texto = 24 if ancho < 1200 else 25 if ancho < 1600 else 28
        tam_nombre = 22 if ancho < 1200 else 23 if ancho < 1600 else 25
        self.fuente_dialogo.setPixelSize(tam_texto)
        self.texto_label.setFont(self.fuente_dialogo)
        self.franja_inferior.alto_contraste = getattr(self.window(), "alto_contraste", False)
        self.franja_inferior.update()
        self.texto_label.setStyleSheet(f"color:#fff7e8; background:transparent; font:{tam_texto}px '{FUENTE_DIALOGO}';")
        self.nombre_label.setStyleSheet(f"color:#ffe5bb; background:transparent; font:700 {tam_nombre}px '{FUENTE_UI}';")
        caja_texto, _, _ = geometria_dialogo(QRectF(0, 0, ancho, 176))
        rect_texto = QFontMetrics(self.fuente_dialogo).boundingRect(
            QRect(0, 0, round(caja_texto.width()), 2000), Qt.TextFlag.TextWordWrap,
            self.texto_completo or "Ciudad Nova")
        altura_franja = max(176, rect_texto.height()+132)

        self.altura_franja = altura_franja

        self.franja_superior.setGeometry(
            0,
            0 if self.estado_escena in ("dialogo", "esperando") else -altura_franja,
            ancho,
            altura_franja
        )

        self.franja_inferior.setGeometry(
            0,
            alto - altura_franja if self.estado_escena in ("dialogo", "esperando") else alto,
            ancho,
            altura_franja
        )

        texto, nombre, pista = geometria_dialogo(QRectF(0, alto-altura_franja, ancho, altura_franja))
        self.nombre_label.setGeometry(nombre.toAlignedRect())
        self.nombre_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.texto_label.setGeometry(texto.toAlignedRect())
        self.pista_continuar.setGeometry(pista.toAlignedRect())
        if self.publicacion_telefono is not None:
            imagen = pixmap_arte("fondos/telefono.png")
            factor = max(ancho/imagen.width(), alto/imagen.height())
            desfase_x = (ancho-imagen.width()*factor)/2
            desfase_y = (alto-imagen.height()*factor)/2
            x = int(desfase_x+imagen.width()*.578*factor)
            y = int(desfase_y+imagen.height()*.132*factor) + int(alto*.06)
            ancho_post = int(imagen.width()*.157*factor)
            alto_post = max(225, alto-altura_franja-y-7)
            self.publicacion_telefono.setGeometry(x, y, ancho_post, alto_post)
            self.publicacion_telefono.raise_()

        ancho_personaje = int(ancho * 0.40)
        alto_personaje = int(alto * 0.85)
        y_personaje = int(alto * 0.01)
        separacion = int(ancho * 0.02)

        self.personajes["CIUDADANO"].setGeometry(
            separacion,
            y_personaje,
            ancho_personaje,
            alto_personaje
        )

        self.personajes["PERIODISTA"].setGeometry(
            ancho - ancho_personaje - separacion,
            y_personaje,
            ancho_personaje,
            alto_personaje
        )

    def mostrar_fondo(self):
        self.actualizar_fondo()
        self.actualizar_geometria()

    def mostrar_personaje(self, nombre, aparecer=True):
        personaje = self.personajes.get(nombre)

        if personaje is None:
            return

        personaje.raise_()

        if aparecer:
            personaje.aparecer(850)
        else:
            personaje.show()
            personaje.efecto_fade.setOpacity(1.0)

    def configurar_personajes_para_hablante(
        self,
        nombre,
        presentes=None
    ):
        nombre = nombre.upper().strip()
        juego = getattr(self.window(), "juego", None)
        if juego is not None:
            preocupacion = juego.evento_actual.urgente or juego.conflictos >= 8
            expresiones = {"CIUDADANO": "ciudadano_preocupado" if preocupacion else "ciudadano_neutral",
                           "PERIODISTA": "periodista_pensativa" if nombre == "PERIODISTA" else "periodista_neutral"}
            for id_personaje, expresion in expresiones.items():
                ruta = f"assets/rediseno/personajes/{expresion}.png"
                personaje = self.personajes[id_personaje]
                if (RAIZ/ruta).is_file() and personaje.ruta_imagen != ruta:
                    personaje.ruta_imagen = ruta
                    personaje.cargar_imagen()
        compuesto = self.fondo.rsplit("/", 1)[-1] in {"Escena 4.png", "Escena 6.png", "Escena 7.png", "Escena 8.png"}
        if compuesto and pixmap_arte("fondos/cafe_interior.png").isNull() and not getattr(self.window(), "sprites_sobre_ilustracion", False):
            self.ocultar_personajes()
            self.hablante_actual = nombre
            return

        if nombre in ("", "NARRADOR"):
            self.ocultar_personajes()
            self.hablante_actual = "NARRADOR"
            return

        if nombre not in self.personajes:
            self.ocultar_personajes()
            self.hablante_actual = nombre
            return

        if presentes is None:
            presentes = {nombre}
        else:
            presentes = {
                personaje.upper().strip()
                for personaje in presentes
                if personaje.upper().strip() in self.personajes
            }

            presentes.add(nombre)

        nuevos = presentes - self.personajes_activos

        for personaje_nombre in nuevos:
            personaje = self.personajes[personaje_nombre]
            personaje.raise_()
            personaje.aparecer(850)

        self.personajes_activos = set(presentes)
        self.personajes_en_escena = set(presentes)

        for personaje_nombre, personaje in self.personajes.items():
            if personaje_nombre not in presentes:
                personaje.hide()
                personaje.efecto_fade.setOpacity(0.0)
                personaje.efecto_dimming.setOpacity(0.0)
                continue

            personaje.raise_()

            if personaje_nombre == nombre:
                personaje.enfocar(500)
            else:
                personaje.oscurecer(500, 0.58)

        self.franja_superior.raise_()
        self.franja_inferior.raise_()
        self.nombre_label.raise_()
        self.texto_label.raise_()

        self.hablante_actual = nombre

    def ocultar_personajes(self):
        activos = list(self.personajes_activos)

        self.personajes_activos.clear()
        self.personajes_en_escena.clear()

        if not activos:
            for personaje in self.personajes.values():
                personaje.hide()
            return

        for nombre in activos:
            personaje = self.personajes[nombre]
            personaje.desaparecer(350)

    def comenzar_escena(self):
        self.timer_inicio.stop()
        if self.animacion is not None:
            self.animacion.stop()

        if self.animacion_personajes is not None:
            self.animacion_personajes.stop()

        self.timer_texto = getattr(
            self,
            "timer_texto",
            None
        )

        if self.timer_texto is not None:
            self.timer_texto.stop()

        self.texto_completo = ""
        self.escribiendo = False
        self.animando = True
        self.estado_escena = "preparando"
        self.hablante_actual = ""

        self.ocultar_personajes()

        for personaje in self.personajes.values():
            personaje.efecto_fade.setOpacity(0.0)
            personaje.efecto_dimming.setOpacity(0.0)
            personaje.hide()

        self.nombre_label.clear()
        self.texto_label.clear()
        self.nombre_label.hide()
        self.texto_label.hide()

        self.mostrar_fondo()

        self.franja_superior.raise_()
        self.franja_inferior.raise_()
        self.nombre_label.raise_()
        self.texto_label.raise_()

        self.franja_superior.setGeometry(
            0,
            -self.altura_franja,
            self.width(),
            self.altura_franja
        )

        self.franja_inferior.setGeometry(
            0,
            self.height(),
            self.width(),
            self.altura_franja
        )

        if self.publicacion_telefono is not None and hasattr(self.window(), "juego"):
            self.publicacion_telefono.mostrar(self.window().juego.obtener_publicacion_actual(), self.window().juego.grafo)
        self.timer_inicio.start(self.TIEMPO_ANTES_DE_HABLAR)

        self.setFocus()

    def preparar_dialogo(self):
        self.iniciar_dialogo(
            self.texto_inicial,
            self.nombre_inicial
        )

    def iniciar_dialogo(
        self,
        texto,
        nombre="",
        presentes=None
    ):
        if hasattr(self.window(), "audio"):
            self.window().audio.detener_voz()
        if self.animacion is not None:
            self.animacion.stop()

        self.timer_texto.stop()
        self.timer_texto.setInterval(34)
        self.estado_escena = "entrando"

        self.texto_completo = texto
        self.escribiendo = False
        self.animando = True

        nombre_normalizado = nombre.upper().strip()

        self.nombre_label.setText(nombre_normalizado or "NARRADOR")
        self.nombre_label.show()

        self.texto_label.clear()
        self.indice_texto = 0
        self.texto_label.show()
        self.pista_continuar.show()
        self.pista_continuar.raise_()

        self.actualizar_geometria()
        self.configurar_personajes_para_hablante(
            nombre_normalizado,
            presentes
        )

        self.franja_superior.raise_()
        self.franja_inferior.raise_()
        self.nombre_label.raise_()
        self.texto_label.raise_()

        ancho = self.width()
        alto = self.height()

        inicio_superior = QRect(
            0,
            -self.altura_franja,
            ancho,
            self.altura_franja
        )

        final_superior = QRect(
            0,
            0,
            ancho,
            self.altura_franja
        )

        inicio_inferior = QRect(
            0,
            alto,
            ancho,
            self.altura_franja
        )

        final_inferior = QRect(
            0,
            alto - self.altura_franja,
            ancho,
            self.altura_franja
        )

        self.franja_superior.setGeometry(inicio_superior)
        self.franja_inferior.setGeometry(inicio_inferior)

        animacion_superior = QPropertyAnimation(
            self.franja_superior,
            b"geometry",
            self
        )
        animacion_superior.setDuration(
            self.DURACION_FRANJAS
        )
        animacion_superior.setStartValue(
            inicio_superior
        )
        animacion_superior.setEndValue(
            final_superior
        )
        animacion_superior.setEasingCurve(
            QEasingCurve.Type.OutCubic
        )

        animacion_inferior = QPropertyAnimation(
            self.franja_inferior,
            b"geometry",
            self
        )
        animacion_inferior.setDuration(
            self.DURACION_FRANJAS
        )
        animacion_inferior.setStartValue(
            inicio_inferior
        )
        animacion_inferior.setEndValue(
            final_inferior
        )
        animacion_inferior.setEasingCurve(
            QEasingCurve.Type.OutCubic
        )

        self.animacion = QParallelAnimationGroup(self)
        self.animacion.addAnimation(animacion_superior)
        self.animacion.addAnimation(animacion_inferior)
        self.animacion.finished.connect(
            self.finalizar_animacion_dialogo
        )
        self.animacion.start()

    def finalizar_animacion_dialogo(self):
        if self.estado_escena == "inactiva":
            return
        self.animando = False
        self.estado_escena = "dialogo"
        self.escribiendo = True
        self.hablante_actual = self.nombre_label.text() or "NARRADOR"
        if hasattr(self.window(), "audio"):
            self.window().audio.narrar(self.texto_completo, self.hablante_actual)
        self.pista_continuar.raise_()
        self.timer_texto.start()

    def escribir_caracter(self):
        self.indice_texto = min(len(self.texto_completo), self.indice_texto + 1)
        self.texto_label.setText(self.texto_completo[:self.indice_texto])
        if self.indice_texto >= len(self.texto_completo):
            self.timer_texto.stop()
            self.escribiendo = False
            self.estado_escena = "esperando"
        else:
            ultimo = self.texto_completo[self.indice_texto-1]
            self.timer_texto.setInterval(190 if ultimo in ".!?" else 95 if ultimo in ",;:" else 34)

    def finalizar_escena(self):
        self.estado_escena = "inactiva"
        self.animando = True
        self.timer_inicio.stop()
        self.timer_texto.stop()
        if hasattr(self.window(), "audio"):
            self.window().audio.detener_voz()
        self.pista_continuar.hide()
        if self.animacion is not None:
            self.animacion.stop()
        for personaje in self.personajes.values():
            for animacion in (personaje.animacion_fade, personaje.animacion_dim,
                              personaje.animacion_entrada, personaje.animacion_salida):
                if animacion is not None:
                    animacion.stop()

    def hideEvent(self, event):
        self.finalizar_escena()
        super().hideEvent(event)

    def avanzar(self):
        if self.animando:
            return

        if self.estado_escena not in ("dialogo", "esperando"):
            return
        if self.escribiendo:
            self.timer_texto.stop()
            self.texto_label.setText(self.texto_completo)
            self.escribiendo = False
            self.estado_escena = "esperando"
            return

        self.animando = True
        self.dialogo_terminado.emit()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.avanzar()
            event.accept()
            return

        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            event.accept()
            return
        if event.key() in (
            Qt.Key.Key_Space,
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter
        ):
            self.avanzar()
            event.accept()
            return

        super().keyPressEvent(event)


class EscenaNarracion(EscenaCinematica):

    def __init__(
        self,
        fondo,
        texto,
        siguiente,
        accion_al_comenzar=None,
        parent=None
    ):
        super().__init__(
            fondo,
            parent
        )

        self.texto_inicial = texto
        self.nombre_inicial = "NARRADOR"

        self.siguiente = siguiente
        self.accion_al_comenzar = accion_al_comenzar

        self.dialogo_terminado.connect(
            self.terminar_escena
        )

    def comenzar_escena(self):
        if self.accion_al_comenzar is not None:
            self.accion_al_comenzar()

        super().comenzar_escena()

    def terminar_escena(self):
        ventana = self.window()

        if hasattr(
            ventana,
            "mostrar_escena"
        ):
            ventana.mostrar_escena(
                self.siguiente
            )


class EscenaDialogo(EscenaCinematica):

    def __init__(self, parent=None):
        super().__init__(
            "assets/fondos/Escena 4.png",
            parent
        )

        self.dialogos = []
        self.dialogo_actual = 0
        self.presentes_dialogo = set()

        self.dialogo_terminado.connect(
            self.siguiente_dialogo
        )

    def preparar_dialogos(self):
        ventana = self.window()

        publicacion = None

        if hasattr(ventana, "juego"):
            publicacion = (
                ventana.juego.obtener_publicacion_actual()
            )

        if publicacion is None:
            texto_publicacion = (
                "una publicación que está circulando por Civitas"
            )
        else:
            texto_publicacion = (
                f'"{publicacion.texto}"'
            )

        self.dialogos = dialogos_publicacion(ventana.juego)

        self.presentes_dialogo = {
            nombre.upper()
            for nombre, _ in self.dialogos
            if nombre.upper() in self.personajes
        }

    def comenzar_escena(self):
        self.preparar_dialogos()
        self.timer_inicio.stop()
        self.timer_texto.stop()
        self.dialogo_actual = 0

        if self.animacion is not None:
            self.animacion.stop()

        self.animando = True
        self.estado_escena = "preparando"
        self.escribiendo = False

        self.ocultar_personajes()

        for personaje in self.personajes.values():
            personaje.efecto_fade.setOpacity(0.0)
            personaje.efecto_dimming.setOpacity(0.0)
            personaje.hide()

        self.mostrar_fondo()

        self.nombre_label.clear()
        self.texto_label.clear()
        self.nombre_label.hide()
        self.texto_label.hide()

        self.actualizar_geometria()

        self.franja_superior.setGeometry(
            0,
            -self.altura_franja,
            self.width(),
            self.altura_franja
        )
        self.franja_inferior.setGeometry(
            0,
            self.height(),
            self.width(),
            self.altura_franja
        )

        self.timer_inicio.start(self.TIEMPO_ANTES_DE_HABLAR)

        self.setFocus()

    def preparar_dialogo(self):
        self.mostrar_dialogo_actual()

    def mostrar_dialogo_actual(self):
        if self.dialogo_actual >= len(self.dialogos):
            self.terminar_escena()
            return

        nombre, texto = self.dialogos[
            self.dialogo_actual
        ]

        self.iniciar_dialogo(
            texto,
            nombre,
            self.presentes_dialogo
        )

    def siguiente_dialogo(self):
        self.dialogo_actual += 1

        if self.dialogo_actual >= len(self.dialogos):
            self.ocultar_personajes()
            self.terminar_escena()
            return

        self.ocultar_franjas(
            self.mostrar_dialogo_actual
        )

    def ocultar_franjas(self, siguiente):
        self.animando = True
        self.estado_escena = "saliendo"
        if self.animacion is not None:
            self.animacion.stop()
        ancho = self.width()
        alto = self.height()

        animacion_superior = QPropertyAnimation(
            self.franja_superior,
            b"geometry",
            self
        )
        animacion_superior.setDuration(1 if getattr(self.window(), "reducir_movimiento", False) else 300)
        animacion_superior.setStartValue(
            QRect(
                0,
                0,
                ancho,
                self.altura_franja
            )
        )
        animacion_superior.setEndValue(
            QRect(
                0,
                -self.altura_franja,
                ancho,
                self.altura_franja
            )
        )
        animacion_superior.setEasingCurve(
            QEasingCurve.Type.InCubic
        )

        animacion_inferior = QPropertyAnimation(
            self.franja_inferior,
            b"geometry",
            self
        )
        animacion_inferior.setDuration(1 if getattr(self.window(), "reducir_movimiento", False) else 300)
        animacion_inferior.setStartValue(
            QRect(
                0,
                alto - self.altura_franja,
                ancho,
                self.altura_franja
            )
        )
        animacion_inferior.setEndValue(
            QRect(
                0,
                alto,
                ancho,
                self.altura_franja
            )
        )
        animacion_inferior.setEasingCurve(
            QEasingCurve.Type.InCubic
        )

        grupo = QParallelAnimationGroup(self)
        grupo.addAnimation(animacion_superior)
        grupo.addAnimation(animacion_inferior)
        grupo.finished.connect(siguiente)

        self.animacion = grupo
        grupo.start()

    def terminar_escena(self):
        ventana = self.window()

        if hasattr(ventana, "mostrar_escena"):
            ventana.mostrar_escena(
                ventana.ESCENA_ACCION
            )


class EscenaAccion(QWidget):

    def __init__(self, juego, parent=None):
        super().__init__(parent)

        self.juego = juego

        self.fondo = QLabel(self)
        self.fondo.setScaledContents(False)
        self.fondo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fondo.lower()

        self.panel = PanelIlustrado(self)
        self.panel.setStyleSheet("""
            QFrame#panelAccion {
                background-color: rgba(20, 29, 48, 228);
                border: 1px solid rgba(245, 206, 190, 150);
                border-radius: 24px;
            }

            QLabel {
                color: #FFF9F4;
                background: transparent;
                border: none;
            }

            QLabel#titulo {
                color: #F6C6B6;
                font-size: 27px;
                font-weight: bold;
                letter-spacing: 1px;
            }

            QLabel#publicacion {
                color: #FFF9F4;
                font-size: 24px;
                font-weight: bold;
            }

            QLabel#info {
                color: #D8E6F2;
                font-size: 16px;
            }

            QLabel#turno {
                color: #F3D7C9;
                font-size: 15px;
                font-weight: bold;
            }

            QPushButton {
                background-color: rgba(78, 105, 131, 245);
                color: white;
                border: 2px solid #E8C7B5;
                border-radius: 14px;
                padding: 15px 22px;
                font-size: 17px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: rgba(107, 135, 160, 255);
                border-color: #FFF1E8;
            }

            QPushButton:pressed {
                background-color: rgba(57, 79, 101, 255);
            }

            QPushButton:disabled {
                color: #9AA8B5;
                border-color: #667481;
                background-color: rgba(45, 56, 68, 220);
            }
        """)
        self.panel.setObjectName("panelAccion")

        self.titulo = QLabel()
        self.titulo.setObjectName("titulo")
        self.titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.publicacion = QLabel()
        self.publicacion.setObjectName("publicacion")
        self.publicacion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.publicacion.setWordWrap(True)

        self.info = QLabel()
        self.info.setObjectName("info")
        self.info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.turno = QLabel(
            "DECISIÓN DEL CIUDADANO"
        )
        self.turno.setObjectName("turno")
        self.turno.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.boton_compartir = QPushButton("COMPARTIR")
        self.boton_verificar = QPushButton("VERIFICAR")
        self.boton_ignorar = QPushButton("IGNORAR")
        self.boton_reportar = QPushButton("REPORTAR")

        self.boton_compartir.clicked.connect(
            lambda: self.ejecutar_accion("compartir")
        )
        self.boton_verificar.clicked.connect(
            lambda: self.ejecutar_accion("verificar")
        )
        self.boton_ignorar.clicked.connect(
            lambda: self.ejecutar_accion("ignorar")
        )
        self.boton_reportar.clicked.connect(
            lambda: self.ejecutar_accion("reportar")
        )

        botones = QGridLayout()
        botones.setHorizontalSpacing(16)
        botones.setVerticalSpacing(16)
        botones.addWidget(self.boton_compartir, 0, 0)
        botones.addWidget(self.boton_verificar, 0, 1)
        botones.addWidget(self.boton_ignorar, 1, 0)
        botones.addWidget(self.boton_reportar, 1, 1)

        layout = QVBoxLayout(self.panel)
        layout.setContentsMargins(25, 23, 25, 33)
        layout.setSpacing(9)
        self.avatar = QLabel()
        self.avatar.setFixedSize(44, 44)
        self.avatar.setPixmap(pixmap_recurso("assets/UI/avatar_unknown.png").scaled(44, 44, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.miniatura = QLabel()
        self.miniatura.setFixedSize(104, 76)
        self.miniatura.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # El mismo componente muestra una publicación completa en ambas escenas.
        self.tarjeta_publicacion = TarjetaPublicacion(self.panel)
        layout.addWidget(self.tarjeta_publicacion, 1)
        for dato in (self.avatar, self.titulo, self.miniatura, self.publicacion, self.info):
            dato.hide()
        layout.addWidget(self.turno)
        layout.addLayout(botones)
        self.aviso = QLabel()
        self.aviso.setWordWrap(True)
        layout.addWidget(self.aviso)
        self.timer_decision = QTimer(self)
        self.timer_decision.setInterval(1000)
        self.timer_decision.timeout.connect(self.cuenta_regresiva)
        self.segundos_restantes = 0
        self.plazo_red = None
        self.efecto_panel = QGraphicsOpacityEffect(self.panel)
        self.panel.setGraphicsEffect(self.efecto_panel)
        self.animacion_panel = QPropertyAnimation(self.efecto_panel, b"opacity", self)
        self.animacion_panel.setStartValue(0.0)
        self.animacion_panel.setEndValue(1.0)
        self.animacion_panel.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.panel.setStyleSheet(f"QFrame#panelAccion {{background:transparent; border:0;}} QLabel {{color:#f6e8cd; background:transparent; border:0; font-family:'{FUENTE_UI}';}} QPushButton {{font:600 17px '{FUENTE_UI}'; min-height:34px; padding:7px;}}")
        self.titulo.setStyleSheet("color:#d7b98b; font:600 17px 'Atkinson Hyperlegible'; letter-spacing:2px;")
        self.publicacion.setStyleSheet("color:#fff3dc; font:24px 'Atkinson Hyperlegible';")
        self.info.setStyleSheet("color:#b6c9ca; font:13px 'Atkinson Hyperlegible';")
        self.info.setWordWrap(True)
        self.turno.setStyleSheet(f"color:#e6cca6; font:600 16px '{FUENTE_UI}';")
        self.turno.setWordWrap(True)
        self.aviso.setStyleSheet(f"color:#dce7e3; font:15px '{FUENTE_UI}';")
        self.aviso.setContentsMargins(12, 0, 12, 4)
        self.retrato_protagonista = QLabel(self)
        self.retrato_protagonista.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.retrato_protagonista.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.leyenda_personaje = QLabel("Tu decisión deja huella.", self)
        self.leyenda_personaje.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.leyenda_personaje.setStyleSheet("color:#fff3dc; background:rgba(20,35,47,165); border-radius:10px; padding:12px; font:17px 'Atkinson Hyperlegible';")
        for nombre, boton in (("compartir", self.boton_compartir), ("verificar", self.boton_verificar), ("ignorar", self.boton_ignorar), ("reportar", self.boton_reportar)):
            boton.setIcon(icono_arte(nombre))
            boton.setIconSize(QSize(27, 27))
        decorar_botones(self.panel)

    def actualizar_personaje(self):
        rol = "periodista" if self.juego.jugador.rol == "periodista" else "ciudadano"
        imagen = pixmap_arte(f"personajes/{rol}_neutral.png")
        self.retrato_protagonista.setGeometry(int(self.width()*.01), int(self.height()*.02), int(self.width()*.38), int(self.height()*.91))
        if not imagen.isNull():
            self.retrato_protagonista.setPixmap(imagen.scaled(self.retrato_protagonista.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.leyenda_personaje.setGeometry(int(self.width()*.035), int(self.height()*.86), int(self.width()*.32), 48)
        self.retrato_protagonista.raise_()
        self.leyenda_personaje.raise_()
        self.panel.raise_()

    def resizeEvent(self, event):
        self.actualizar_fondo()

        self.panel.setGeometry(int(self.width()*.40), 14, int(self.width()*.575), self.height()-28)
        self.actualizar_personaje()

        super().resizeEvent(event)

    def actualizar_fondo(self):
        pixmap = pixmap_recurso("assets/fondos/Escena 5.png")

        if pixmap.isNull():
            self.fondo.setStyleSheet(
                "background-color: #172236;"
            )
            self.fondo.setGeometry(self.rect())
            return

        pixmap_escalado = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )

        self.fondo.setPixmap(pixmap_escalado)
        self.fondo.setGeometry(self.rect())
        self.fondo.lower()

    def mostrar(self):
        self.actualizar_personaje()
        publicacion = (
            self.juego.obtener_publicacion_actual()
        )

        if publicacion is None:
            self.titulo.setText(
                "NO HAY PUBLICACIONES DISPONIBLES"
            )
            self.publicacion.setText("")
            self.info.setText("")
            self.turno.setText("")

            for boton in (
                self.boton_compartir,
                self.boton_verificar,
                self.boton_ignorar,
                self.boton_reportar
            ):
                boton.setEnabled(False)

            return

        for boton in (
            self.boton_compartir,
            self.boton_verificar,
            self.boton_ignorar,
            self.boton_reportar
        ):
            boton.setEnabled(True)

        self.titulo.setText(
            "PUBLICACIÓN DE CIVITAS"
        )
        self.tarjeta_publicacion.mostrar(publicacion, self.juego.grafo)
        retrato = avatar_arte(publicacion.emisor_id)
        if not retrato.isNull():
            self.avatar.setPixmap(retrato.scaled(44, 44, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        miniatura = miniatura_publicacion(publicacion.id)
        if not miniatura.isNull():
            self.miniatura.setPixmap(miniatura.scaled(self.miniatura.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
        else:
            self.miniatura.clear()
        self.animacion_panel.stop()
        self.animacion_panel.setDuration(1 if getattr(self.window(), "reducir_movimiento", False) else 350)
        self.animacion_panel.start()

        self.publicacion.setText(
            f'"{publicacion.texto}"'
        )

        self.info.setText(
            f"Civitas · {self.juego.grafo.nodos.get(publicacion.emisor_id).nombre if publicacion.emisor_id in self.juego.grafo.nodos else 'Comunidad'} · ID #{publicacion.id} · {publicacion.estado}\n"
            f"Impacto {publicacion.impacto} · Compartidos {publicacion.compartidos} · Verificaciones {publicacion.verificaciones} · Alcance {publicacion.alcance}"
        )

        self.turno.setText(
            f"TURNO DE {self.juego.jugador.nombre.upper()} · {self.juego.jugador.rol.upper()} · Puntos {self.juego.jugador.puntos}"
        )

        evento = self.juego.evento_actual
        self.segundos_restantes = evento.segundos
        self.aviso.setText(evento.texto)
        self.timer_decision.stop()
        if self.juego.decision_aplicada:
            for boton in (self.boton_compartir, self.boton_verificar, self.boton_ignorar, self.boton_reportar):
                boton.setEnabled(False)
            return
        if evento.urgente and not getattr(self.window(), "sin_limite", False):
            self.timer_decision.start()
            self.aviso.setText(f"{evento.texto} · {self.segundos_restantes} s")
        if getattr(self.window(), "cliente_red", None) is not None:
            mi_turno = self.juego.jugador.id == self.window().mi_id
            self.timer_decision.stop()  # El servidor decide el timeout oficial.
            self.plazo_red = None
            for boton in (self.boton_compartir, self.boton_verificar, self.boton_ignorar, self.boton_reportar):
                boton.setEnabled(mi_turno and not self.juego.decision_aplicada)
            if not mi_turno:
                self.aviso.setText("Esperando la decisión del jugador de turno…")
            else:
                self.window().cliente_red.enviar({"tipo": "decision_lista", "publicacion_id": publicacion.id})

    def cuenta_regresiva(self):
        if getattr(self.window(), "cliente_red", None) is not None:
            if self.plazo_red is None:
                return
            segundos = max(0, math.ceil(self.plazo_red-time.monotonic()))
            self.aviso.setText(f"{self.juego.evento_actual.texto} · {segundos} s · turno de {self.juego.jugador.nombre}")
            if segundos == 0:
                self.timer_decision.stop()
                self.aviso.setText("Tiempo agotado. Esperando el resultado del servidor…")
            return
        self.segundos_restantes -= 1
        if 0 < self.segundos_restantes <= 3 and hasattr(self.window(), "audio"):
            self.window().audio.reproducir_efecto("cuenta_regresiva")
        self.aviso.setText(f"{self.juego.evento_actual.texto} · {self.segundos_restantes} s")
        if self.segundos_restantes <= 0:
            self.ejecutar_accion("ignorar")

    def actualizar_plazo_red(self, segundos):
        if segundos is None:
            self.plazo_red = None
            self.timer_decision.stop()
            return
        self.plazo_red = time.monotonic() + segundos
        self.timer_decision.start()
        self.cuenta_regresiva()

    def finalizar_escena(self):
        self.timer_decision.stop()
        self.animacion_panel.stop()
        self.efecto_panel.setOpacity(1.0)

    def hideEvent(self, event):
        self.finalizar_escena()
        super().hideEvent(event)

    def ejecutar_accion(self, accion):
        self.timer_decision.stop()
        if getattr(self.window(), "cliente_red", None) is not None:
            self.window().enviar_accion(accion)
            return
        resultado = self.juego.ejecutar_accion(
            accion
        )

        if resultado is False:
            return

        for boton in (self.boton_compartir, self.boton_verificar, self.boton_ignorar, self.boton_reportar):
            boton.setEnabled(False)

        self.window().mostrar_escena(
            self.window().ESCENA_RESULTADO_1
        )


class VisualizadorBSTBonito(QWidget):

    def __init__(self, arbol, parent=None):
        super().__init__(parent)

        self.arbol = arbol
        self.posiciones = {}
        self.radio_nodo = 36
        self.setMinimumHeight(210)
        self.setStyleSheet("background: transparent;")

    def actualizar(self):
        self.update()

    def obtener_niveles(self, nodo, nivel, niveles):
        if nodo is None:
            return

        while len(niveles) <= nivel:
            niveles.append([])

        niveles[nivel].append(nodo)

        self.obtener_niveles(
            nodo.izquierda,
            nivel + 1,
            niveles
        )

        self.obtener_niveles(
            nodo.derecha,
            nivel + 1,
            niveles
        )

    def obtener_nodos(self, nodo, lista):
        if nodo is None:
            return

        lista.append(nodo)

        self.obtener_nodos(
            nodo.izquierda,
            lista
        )

        self.obtener_nodos(
            nodo.derecha,
            lista
        )

    def color_estado(self, estado):
        colores = paleta(getattr(self.window(), "modo_daltonismo", "normal"))
        if estado == "FALSA VERIFICADA":
            return QColor(colores["falsa"])

        if estado == "VERIFICADA":
            return QColor(colores["verdadera"])

        if estado == "COMPARTIDA":
            return QColor(colores["exploracion"])

        if estado == "IGNORADA":
            return QColor(colores["neutro"])

        return QColor(colores["correccion"])

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        if self.arbol.raiz is None:
            self.posiciones = {}
            painter.setPen(QColor("#F8EEE7"))
            painter.setFont(
                QFont(
                    "Atkinson Hyperlegible",
                    22,
                    QFont.Weight.Bold
                )
            )
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "EL ÁRBOL DE CIVITAS ESTÁ VACÍO"
            )
            painter.end()
            return

        niveles = []
        self.obtener_niveles(
            self.arbol.raiz,
            0,
            niveles
        )

        todos = []
        self.obtener_nodos(
            self.arbol.raiz,
            todos
        )

        indice_inorden = {}
        ordenados = self.arbol.inorden()

        nodos_por_id = {
            id(n.publicacion): n
            for n in todos
        }

        for indice, publicacion in enumerate(ordenados):
            nodo = nodos_por_id.get(
                id(publicacion)
            )
            if nodo is not None:
                indice_inorden[id(nodo)] = indice

        posiciones = {}
        cantidad_total = max(
            1,
            len(ordenados)
        )

        escala = max(.95, min(1.3, self.window().width()/1366))
        radio = round(36*escala)
        self.radio_nodo = radio
        paso_x = min(200*escala, (self.width()-2*radio-32)/cantidad_total)
        paso_y = min(126*escala, (self.height()-2*radio-46)/max(1, len(niveles)-1))
        alto_grupo = (len(niveles)-1)*paso_y
        y_inicial = (self.height()-alto_grupo-24)/2

        for nivel, nodos in enumerate(niveles):
            y = y_inicial + nivel*paso_y

            for nodo in nodos:
                indice = indice_inorden.get(
                    id(nodo),
                    0
                )

                x = self.width()/2 + (indice-(cantidad_total-1)/2)*paso_x

                posiciones[id(nodo)] = (
                    int(x),
                    int(y)
                )
        self.posiciones = {nodo.publicacion.id: QPoint(*posiciones[id(nodo)]) for nodo in todos}

        painter.setPen(
            QPen(
                QColor("#F1DDCE"),
                3,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin
            )
        )

        for nodo in todos:
            x1, y1 = posiciones[id(nodo)]

            if nodo.izquierda is not None:
                x2, y2 = posiciones[
                    id(nodo.izquierda)
                ]
                painter.drawLine(
                    x1,
                    y1,
                    x2,
                    y2
                )

            if nodo.derecha is not None:
                x2, y2 = posiciones[
                    id(nodo.derecha)
                ]
                painter.drawLine(
                    x1,
                    y1,
                    x2,
                    y2
                )

        for nodo in todos:
            x, y = posiciones[id(nodo)]
            publicacion = nodo.publicacion

            color = self.color_estado(
                publicacion.estado
            )

            painter.setBrush(
                QBrush(
                    QColor(
                        "#172A3B"
                    )
                )
            )
            painter.setPen(Qt.PenStyle.NoPen)

            painter.drawEllipse(
                x - radio + 5,
                y - radio + 6,
                radio * 2,
                radio * 2
            )

            painter.setBrush(
                QBrush(color)
            )

            painter.setPen(
                QPen(
                    QColor("#F7E0D4"),
                    3
                )
            )

            painter.drawEllipse(
                x - radio,
                y - radio,
                radio * 2,
                radio * 2
            )

            medallon = pixmap_arte("ui/nodo.png")
            if not medallon.isNull():
                painter.drawPixmap(QRect(x-radio-4, y-radio-4, (radio+4)*2, (radio+4)*2), medallon)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(color, 3))
                painter.drawEllipse(x-radio+4, y-radio+4, (radio-4)*2, (radio-4)*2)

            painter.setPen(
                QColor("#FFFFFF")
            )

            fuente = QFont(FUENTE_UI)
            fuente.setPixelSize(round(23*escala))
            fuente.setBold(True)
            painter.setFont(fuente)

            painter.drawText(
                x - radio,
                y - radio,
                radio * 2,
                radio * 2,
                Qt.AlignmentFlag.AlignCenter,
                f"#{publicacion.id}"
            )
            fuente.setPixelSize(round(14*escala))
            fuente.setBold(False)
            painter.setFont(fuente)
            painter.setPen(QColor("#e5ded1"))
            painter.drawText(QRect(x-95, y+radio+9, 190, 25), Qt.AlignmentFlag.AlignCenter,
                             publicacion.estado.replace("FALSA VERIFICADA", "Falsa · verificada").capitalize())

        painter.end()


class EscenaArbol(QWidget):

    def __init__(self, juego, parent=None):
        super().__init__(parent)

        self.juego = juego

        self.fondo = QLabel(self)
        self.fondo.setScaledContents(False)
        self.fondo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fondo.lower()

        self.panel = PanelIlustrado(self)
        self.panel.setStyleSheet("QFrame#panelArbol {background:transparent;border:0;} QLabel {color:#f6e8cd;background:transparent;font:14px 'Atkinson Hyperlegible';} QLabel#tituloArbol {color:#e7c496;font:23px 'Atkinson Hyperlegible';} QFrame#acciones {background:transparent;border:0;}")
        self.panel.setObjectName("panelArbol")

        self.titulo = titulo = QLabel(
            "ÁRBOL BINARIO DE BÚSQUEDA"
        )
        titulo.setObjectName("tituloArbol")
        titulo.setWordWrap(True)
        titulo.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.operacion = QLabel()
        self.operacion.setObjectName("operacion")
        self.operacion.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.operacion.setWordWrap(True)

        self.visualizador = VisualizadorBSTBonito(
            self.juego.arbol
        )

        self.acciones = acciones = QFrame()
        acciones.setObjectName("acciones")

        self.boton_inorden = BotonIlustrado(
            "INORDEN"
        )

        self.boton_preorden = BotonIlustrado(
            "PREORDEN"
        )

        self.boton_postorden = BotonIlustrado(
            "POSTORDEN"
        )

        self.boton_continuar = BotonIlustrado(
            "CONTINUAR"
        )
        self.boton_continuar.setObjectName(
            "continuar"
        )

        self.resultado = QLabel()
        self.resultado.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.resultado.setWordWrap(True)
        self.resultado.hide()

        self.boton_inorden.clicked.connect(
            self.mostrar_inorden
        )
        self.boton_preorden.clicked.connect(
            self.mostrar_preorden
        )
        self.boton_postorden.clicked.connect(
            self.mostrar_postorden
        )
        self.boton_continuar.clicked.connect(
            self.continuar
        )

        botones = QHBoxLayout(acciones)
        botones.setContentsMargins(0, 2, 0, 2)
        botones.setSpacing(16)
        botones.addStretch()
        botones.addWidget(
            self.boton_inorden
        )
        botones.addWidget(
            self.boton_preorden
        )
        botones.addWidget(
            self.boton_postorden
        )
        botones.addStretch()

        self.layout_panel = layout = QVBoxLayout(self.panel)
        layout.setContentsMargins(42, 44, 42, 36)
        layout.setSpacing(14)
        layout.addWidget(titulo)
        layout.addWidget(self.operacion)
        layout.addWidget(self.visualizador, 1)
        layout.addWidget(acciones)
        layout.addWidget(self.resultado)
        pie = QHBoxLayout()
        pie.addStretch()
        pie.addWidget(self.boton_continuar)
        layout.addLayout(pie)
        decorar_botones(self.panel)

    def resizeEvent(self, event):
        pixmap = pixmap_recurso("assets/fondos/Escena Arbol.jfif")

        if not pixmap.isNull():
            pixmap_escalado = pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            self.fondo.setPixmap(
                pixmap_escalado
            )
        else:
            self.fondo.setStyleSheet(
                "background-color: #172236;"
            )

        self.fondo.setGeometry(
            self.rect()
        )
        self.fondo.lower()

        ancho_panel = min(1540, self.width()-64)
        alto_panel = min(770, self.height()-40)
        self.panel.setGeometry((self.width()-ancho_panel)//2, (self.height()-alto_panel)//2,
                               ancho_panel, alto_panel)
        escala = max(.95, min(1.25, self.width()/1366))
        compacta = self.height() < 650
        margenes = self.panel.margenes_seguros()
        self.layout_panel.setContentsMargins(32 if compacta else max(38, margenes.left()),
                                            32 if compacta else max(40, margenes.top()),
                                            32 if compacta else max(38, margenes.right()),
                                            32 if compacta else max(34, margenes.bottom()))
        self.layout_panel.setSpacing(8 if compacta else 14)
        self.visualizador.setMinimumHeight(145 if compacta else 210)
        self.titulo.setStyleSheet(f"color:#e7c496; font:700 {round(25*escala)}px '{FUENTE_UI}';")
        self.operacion.setStyleSheet(f"font:{round(16*escala)}px '{FUENTE_UI}'; color:#e5e3d8;")
        self.resultado.setStyleSheet(f"font:{round(17*escala)}px '{FUENTE_UI}'; color:#ffe4b8;")
        for boton in (self.boton_inorden, self.boton_preorden, self.boton_postorden):
            ancho_boton, alto_boton = round(220*escala), round(54*escala)
            boton.setStyleSheet(f"font:700 {round(17*escala)}px '{FUENTE_UI}'; padding:0; border:0; "
                                f"min-width:{ancho_boton}px; max-width:{ancho_boton}px; "
                                f"min-height:{alto_boton}px; max-height:{alto_boton}px;")
            boton.setFixedSize(ancho_boton, alto_boton)
        ancho_boton, alto_boton = round(238*escala), round(56*escala)
        self.boton_continuar.setStyleSheet(f"font:700 {round(17*escala)}px '{FUENTE_UI}'; padding:0; border:0; "
                                         f"min-width:{ancho_boton}px; max-width:{ancho_boton}px; "
                                         f"min-height:{alto_boton}px; max-height:{alto_boton}px;")
        self.boton_continuar.setFixedSize(ancho_boton, alto_boton)

        super().resizeEvent(event)

    def mostrar(self):
        self.visualizador.actualizar()

        self.operacion.setText(
            self.juego.ultimo_resultado
        )

        self.resultado.setText("")
        self.resultado.hide()

        self.setFocus()

    def convertir_texto(
        self,
        publicaciones
    ):
        if not publicaciones:
            return "Árbol vacío"

        return "  →  ".join(
            f"#{p.id}"
            for p in publicaciones
        )

    def mostrar_inorden(self):
        self.resultado.show()
        resultado = (
            self.juego.arbol.inorden()
        )

        self.resultado.setText(
            "INORDEN: "
            + self.convertir_texto(
                resultado
            )
        )

    def mostrar_preorden(self):
        self.resultado.show()
        resultado = (
            self.juego.arbol.preorden()
        )

        self.resultado.setText(
            "PREORDEN: "
            + self.convertir_texto(
                resultado
            )
        )

    def mostrar_postorden(self):
        self.resultado.show()
        resultado = (
            self.juego.arbol.postorden()
        )

        self.resultado.setText(
            "POSTORDEN: "
            + self.convertir_texto(
                resultado
            )
        )

    def continuar(self):
        self.window().mostrar_escena(self.window().ESCENA_GRAFO)


class EscenaResultado(EscenaCinematica):

    def __init__(self, fondo, siguiente, tipo, parent=None):
        super().__init__(fondo, parent)

        self.siguiente = siguiente
        self.tipo = tipo
        self.nombre_inicial = ""

        self.dialogo_terminado.connect(
            self.terminar_escena
        )

    def obtener_contenido(self):
        return contenido_resultado(self.window().juego, self.tipo)

    def comenzar_escena(self):
        self.texto_inicial, self.nombre_inicial = (
            self.obtener_contenido()
        )

        super().comenzar_escena()

    def terminar_escena(self):
        ventana = self.window()

        if hasattr(ventana, "mostrar_escena"):
            ventana.mostrar_escena(
                self.siguiente
            )


from juego.partida import Juego


class VentanaPrincipal(QMainWindow):

    mensaje_red = pyqtSignal(dict)

    ESCENA_INICIO = 0
    ESCENA_NARRACION_1 = 1
    ESCENA_NARRACION_2 = 2
    ESCENA_NARRACION_3 = 3
    ESCENA_DIALOGO = 4
    ESCENA_ACCION = 5
    ESCENA_RESULTADO_1 = 6
    ESCENA_RESULTADO_2 = 7
    ESCENA_RESULTADO_3 = 8
    ESCENA_ARBOL = 9
    ESCENA_FIN = 10
    ESCENA_GRAFO = 11

    def __init__(self):
        super().__init__()
        cargar_tipografias()

        self.setWindowTitle(
            "CIVICA — Alcalde Digital"
        )

        self.setMinimumSize(
            1100,
            700
        )

        self.pantalla_completa = False
        self.sin_limite = False
        self.reducir_movimiento = False
        self.cliente_red = None
        self.mi_id = None
        self.token_red = None
        self.datos_conexion = None
        self.recuperada_red = False
        self.sesion_red = 0
        self.servidor_red = None
        self.revision_red = -1
        self.fase_red = None
        self.alto_contraste = False
        self.sprites_sobre_ilustracion = False
        self.modo_daltonismo = "normal"
        self.voces_activadas = True
        self.dialogo_red = None
        self.mensaje_red.connect(self.recibir_mensaje)
        self.audio = GestorAudio(self)
        from configuracion import cargar
        preferencias = cargar()
        for categoria, valor in preferencias.get("volumenes", {}).items():
            if categoria in self.audio.volumenes and isinstance(valor, (int, float)):
                self.audio.configurar(categoria, valor)
        self.audio.silenciar(preferencias.get("silenciado", False))
        for nombre in ("sin_limite", "reducir_movimiento", "alto_contraste", "sprites_sobre_ilustracion"):
            setattr(self, nombre, bool(preferencias.get(nombre, False)))
        modo = preferencias.get("modo_daltonismo", "normal")
        self.modo_daltonismo = modo if modo in MODOS_DALTONISMO else "normal"
        self.voces_activadas = bool(preferencias.get("voces_activadas", True))
        self.audio.configurar_voces(self.voces_activadas)

        self.juego = Juego()

        self.escenas = QStackedWidget()

        self.escena_inicio = EscenaInicio()

        self.escena_narracion_1 = EscenaNarracion(
            "assets/fondos/Escena 1.jfif",
            "Faltan pocos días para las elecciones en Civitas.",
            self.ESCENA_NARRACION_2
        )

        self.escena_narracion_2 = EscenaNarracion(
            "assets/fondos/Escena 2.png",
            "En Civitas comienzan a aparecer publicaciones polémicas.",
            self.ESCENA_NARRACION_3
        )

        self.escena_narracion_3 = EscenaNarracion(
            "assets/fondos/Escena 3.png",
            "El candidato Juan quiere cerrar el colegio.",
            self.ESCENA_DIALOGO,
            accion_al_comenzar=(
                self.juego.iniciar_primera_publicacion
            )
        )

        self.escena_dialogo = EscenaDialogo()

        self.escena_accion = EscenaAccion(
            self.juego
        )

        self.escena_resultado_1 = EscenaResultado(
            "assets/fondos/Escena 6.png",
            self.ESCENA_RESULTADO_2,
            1
        )

        self.escena_resultado_2 = EscenaResultado(
            "assets/fondos/Escena 7.png",
            self.ESCENA_RESULTADO_3,
            2
        )

        self.escena_resultado_3 = EscenaResultado(
            "assets/fondos/Escena 8.png",
            self.ESCENA_ARBOL,
            3
        )

        self.escena_arbol = EscenaArbol(
            self.juego
        )

        self.escena_fin = EscenaFin()
        self.escena_red = EscenaRed(self.juego)
        self.escena_red.continuar.connect(self.continuar_desde_arbol)

        for escena in (
            self.escena_inicio,
            self.escena_narracion_1,
            self.escena_narracion_2,
            self.escena_narracion_3,
            self.escena_dialogo,
            self.escena_accion,
            self.escena_resultado_1,
            self.escena_resultado_2,
            self.escena_resultado_3,
            self.escena_arbol,
            self.escena_fin,
            self.escena_red
        ):
            self.escenas.addWidget(escena)

        self.setCentralWidget(
            self.escenas
        )

        barra = QToolBar("CIVICA")
        self.barra = barra
        barra.setIconSize(QSize(21, 21))
        barra.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        barra.setMovable(False)
        barra.setStyleSheet(f"QToolBar {{background:#142637; spacing:8px; padding:5px 14px; border-bottom:1px solid #9a744d;}} QToolButton {{color:#f6e8cd; font:16px '{FUENTE_UI}'; padding:6px 15px; min-height:28px; border:0;}}")
        marca = QLabel("CIVICA   /   Ciudad Nova")
        marca.setStyleSheet(f"color:#e5c797; font:700 16px '{FUENTE_UI}'; padding:0 12px;")
        barra.addWidget(marca)
        self.menu_partida = QToolButton()
        self.menu_partida.setText("Partida")
        self.menu_partida.setMinimumWidth(120)
        self.menu_partida.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QMenu(self.menu_partida)
        self.acciones_partida = {}
        for texto, clave, funcion in (("Guardar partida", "guardar", self.guardar_partida),
                                      ("Cargar partida", "cargar", self.cargar_partida),
                                      ("Reconectar sala", "reconectar", self.reconectar_red),
                                      ("Volver a la portada", "portada", self.volver_portada)):
            accion = menu.addAction(icono_arte(clave), texto, funcion)
            self.acciones_partida[clave] = accion
        self.menu_partida.setMenu(menu)
        self.accion_menu_partida = barra.addWidget(self.menu_partida)
        espacio = QWidget()
        espacio.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        barra.addWidget(espacio)
        self.boton_configuracion = QToolButton()
        self.boton_configuracion.setText("Configuración")
        self.boton_configuracion.setMinimumWidth(215)
        self.boton_configuracion.setAccessibleName("Configuración y accesibilidad")
        self.boton_configuracion.setIcon(icono_arte("ajustes"))
        self.boton_configuracion.setIconSize(QSize(26, 26))
        self.boton_configuracion.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.boton_configuracion.clicked.connect(lambda: mostrar_configuracion(self))
        barra.addWidget(self.boton_configuracion)

        self.addToolBar(barra)
        self.statusBar().setStyleSheet("background:#142537;color:#fff4e9;")
        self.indicadores = QLabel()
        self.indicadores.setStyleSheet("color:#fff4e9; padding:3px;")
        self.indicadores.hide()
        self.hud = HudCiudad(self)
        self.statusBar().addPermanentWidget(self.hud, 1)
        self.statusBar().setSizeGripEnabled(False)
        self.audio.aviso.connect(lambda texto: self.statusBar().showMessage("Civitas · " + texto, 2200))
        aplicar_estilo(self)
        menu.setStyleSheet(f"QMenu {{background:#193548; color:#fff2dc; padding:8px; font:17px '{FUENTE_UI}'; border:1px solid #bd8855;}} QMenu::item {{padding:12px 24px;}} QMenu::item:selected {{background:#365e70;}}")
        self.aplicar_accesibilidad()
        self.velo_transicion = QFrame(self.escenas)
        self.velo_transicion.setStyleSheet("background:#02060b;border:0;")
        self.velo_transicion.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.efecto_transicion = QGraphicsOpacityEffect(self.velo_transicion)
        self.velo_transicion.setGraphicsEffect(self.efecto_transicion)
        self.animacion_transicion = QPropertyAnimation(self.efecto_transicion, b"opacity", self)
        self.animacion_transicion.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animacion_transicion.valueChanged.connect(
            lambda _: self.velo_transicion.setGeometry(self.escenas.rect()))
        self.animacion_transicion.finished.connect(self.velo_transicion.hide)
        self.velo_transicion.hide()
        for boton in self.findChildren(QPushButton):
            boton.clicked.connect(lambda: self.audio.reproducir_efecto("clic"))

        self.escena_inicio.continuar.connect(
            self.comenzar_juego
        )

        self.mostrar_escena(
            self.ESCENA_INICIO
        )

    def comenzar_juego(self):
        self.cerrar_red()
        if self.juego.indice_proxima_publicacion:
            self.establecer_juego(Juego())
        dialogo = DialogoRol(self)
        if not dialogo.exec():
            return
        self.juego.seleccionar_rol(dialogo.roles.currentData())
        self.mostrar_escena(
            self.ESCENA_NARRACION_1
        )

    def showEvent(self, event):
        super().showEvent(event)
        # QToolBar puede crear sus botones al mostrarse por primera vez.
        decorar_botones(self.barra)

    def mostrar_escena(self, indice):
        anterior = self.escenas.currentWidget()
        if hasattr(anterior, "finalizar_escena"):
            anterior.finalizar_escena()
        self.escenas.setCurrentIndex(
            indice
        )
        en_partida = indice != self.ESCENA_INICIO
        self.accion_menu_partida.setVisible(en_partida)
        self.statusBar().setVisible(en_partida)
        self.acciones_partida["reconectar"].setVisible(self.datos_conexion is not None)
        for clave in ("guardar", "cargar"):
            self.acciones_partida[clave].setEnabled(self.cliente_red is None)

        escena = (
            self.escenas.currentWidget()
        )

        if hasattr(
            escena,
            "comenzar_escena"
        ):
            escena.comenzar_escena()

        elif hasattr(
            escena,
            "mostrar"
        ):
            escena.mostrar()

        escena.setFocus()
        if hasattr(self, "audio"):
            pista = "eleccion" if indice == self.ESCENA_FIN else "investigacion" if indice in (self.ESCENA_DIALOGO, self.ESCENA_GRAFO) else "ciudad"
            self.audio.cambiar_pista(pista)
            ambiente = "cafe" if indice in (self.ESCENA_DIALOGO, self.ESCENA_ACCION) else "oficina" if indice in (self.ESCENA_RESULTADO_1, self.ESCENA_RESULTADO_2) else "plaza"
            self.audio.cambiar_pista(ambiente, "ambiente")
            if indice == self.ESCENA_ACCION:
                self.audio.reproducir_efecto("notificacion")
            elif indice == self.ESCENA_RESULTADO_1:
                self.audio.reproducir_efecto(self.juego.ultima_accion or "resultado")
            elif indice == self.ESCENA_FIN:
                self.audio.reproducir_efecto("recompensa")
            self.actualizar_estado()
        self.animacion_transicion.stop()
        if en_partida and not self.reducir_movimiento:
            self.velo_transicion.setGeometry(self.escenas.rect())
            self.velo_transicion.show()
            self.velo_transicion.raise_()
            self.animacion_transicion.setDuration(1500 if indice == self.ESCENA_NARRACION_1 else 700)
            self.animacion_transicion.setStartValue(1.0)
            self.animacion_transicion.setEndValue(0.0)
            self.animacion_transicion.start()
        else:
            self.velo_transicion.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "velo_transicion"):
            self.velo_transicion.setGeometry(self.escenas.rect())

    def continuar_desde_arbol(self):
        if self.escenas.currentWidget() is not self.escena_red:
            return
        if self.cliente_red is not None:
            self.cliente_red.enviar({"tipo": "continuar", "revision": self.revision_red})
            self.escena_red.boton_continuar.setEnabled(False)
            self.escena_red.detalle.setText("Esperando que los demás participantes terminen de revisar el resultado…")
            return
        if self.juego.avanzar_publicacion():
            self.mostrar_escena(
                self.ESCENA_DIALOGO
            )
        else:
            self.mostrar_escena(
                self.ESCENA_FIN
            )

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F1:
            mostrar_ayuda(self)
            event.accept()
            return
        if event.key() == Qt.Key.Key_F11:
            self.alternar_pantalla_completa()
            event.accept()
            return

        super().keyPressEvent(event)

    def establecer_juego(self, juego):
        self.juego = juego
        self.escena_accion.juego = juego
        self.escena_arbol.juego = juego
        self.escena_arbol.visualizador.arbol = juego.arbol
        self.escena_red.juego = juego
        self.escena_red.visualizador.grafo = juego.grafo
        self.escena_narracion_3.accion_al_comenzar = juego.iniciar_primera_publicacion
        self.actualizar_estado()

    def actualizar_estado(self):
        if hasattr(self, "hud"):
            self.hud.actualizar(self.juego)
        if hasattr(self, "indicadores"):
            self.indicadores.setText(f"Ciudad Nova · Confianza {self.juego.confianza} · Convivencia {self.juego.convivencia} · Bienestar {self.juego.bienestar_digital} · Información verificada {self.juego.info_verificada} · Desinformación {self.juego.desinformacion} · Conflictos {self.juego.conflictos}")

    def aplicar_accesibilidad(self):
        for escena in self.escenas.findChildren(EscenaCinematica):
            escena.DURACION_FRANJAS = 1 if self.reducir_movimiento else 450
            escena.TIEMPO_ANTES_DE_HABLAR = 1 if self.reducir_movimiento else 650
            for personaje in escena.personajes.values():
                personaje.reducir_movimiento = self.reducir_movimiento
            escena.actualizar_geometria()
        self.audio.configurar_voces(self.voces_activadas)
        if hasattr(self, "hud"):
            self.hud.actualizar(self.juego)
        self.escena_red.visualizador.update()
        self.escena_arbol.visualizador.update()
        if self.reducir_movimiento:
            self.escena_red.completar()
            if hasattr(self, "animacion_transicion"):
                self.animacion_transicion.stop()
                self.velo_transicion.hide()
        if self.sin_limite:
            self.escena_accion.timer_decision.stop()

    def guardar_partida(self):
        if self.cliente_red is not None:
            self.statusBar().showMessage("En multijugador el servidor conserva el estado oficial.")
            return
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar partida", ruta_recurso('saves/partida.json'), "Partidas (*.json)")
        if ruta:
            try:
                self.juego.guardar(ruta)
                self.statusBar().showMessage("Partida guardada.")
            except (OSError, ValueError) as error:
                QMessageBox.warning(self, "Guardado", str(error))

    def cargar_partida(self):
        if self.cliente_red is not None:
            return
        ruta, _ = QFileDialog.getOpenFileName(self, "Cargar partida", ruta_recurso('saves'), "Partidas (*.json)")
        if ruta:
            try:
                juego = Juego.cargar(ruta)
                self.establecer_juego(juego)
                indice = self.ESCENA_GRAFO if juego.decision_aplicada else self.ESCENA_DIALOGO
                if juego.indice_proxima_publicacion == 0:
                    indice = self.ESCENA_INICIO
                if juego.finalizada:
                    indice = self.ESCENA_FIN
                self.mostrar_escena(indice)
            except (OSError, ValueError, KeyError, TypeError) as error:
                QMessageBox.warning(self, "Partida incompatible", str(error))

    def volver_portada(self):
        self.cerrar_red()
        self.mostrar_escena(self.ESCENA_INICIO)

    def abrir_multijugador(self):
        self.dialogo_red = DialogoRed(self)
        if not self.dialogo_red.exec():
            self.cerrar_red()

    def conectar_red(self, crear, host, puerto, nombre, rol):
        from red.servidor import Servidor
        from red.cliente import Cliente
        self.cerrar_red()
        self.revision_red, self.fase_red = -1, None
        if crear:
            self.servidor_red = Servidor(puerto=puerto, sin_limite=self.sin_limite)
            self.servidor_red.iniciar()
            puerto = self.servidor_red.puerto
            host = "127.0.0.1"
        sesion = self.sesion_red
        self.cliente_red = Cliente(lambda mensaje: self.mensaje_red.emit(dict(mensaje, sesion=sesion)))
        self.cliente_red.conectar(host, puerto, nombre, rol)
        self.datos_conexion = (host, puerto, nombre, rol)

    def reconectar_red(self):
        from red.cliente import Cliente
        if not self.token_red or not self.datos_conexion:
            self.statusBar().showMessage("Primero únete a una sala de CIVICA.")
            return
        if self.cliente_red is not None and not self.cliente_red.cerrado.is_set():
            self.statusBar().showMessage("La conexión sigue activa.")
            return
        self.sesion_red += 1
        sesion = self.sesion_red
        self.revision_red = -1
        self.cliente_red = Cliente(lambda mensaje: self.mensaje_red.emit(dict(mensaje, sesion=sesion)))
        self.cliente_red.conectar(*self.datos_conexion, token=self.token_red)
        self.statusBar().showMessage("Recuperando tu lugar en la campaña…")

    def enviar_accion(self, accion):
        if self.cliente_red is None or self.juego.jugador.id != self.mi_id:
            return
        if self.cliente_red.enviar({"tipo": "accion", "accion": accion, "publicacion_id": self.juego.publicacion_actual_id}):
            for boton in (self.escena_accion.boton_compartir, self.escena_accion.boton_verificar, self.escena_accion.boton_ignorar, self.escena_accion.boton_reportar):
                boton.setEnabled(False)

    def recibir_mensaje(self, mensaje):
        if mensaje.get("sesion", self.sesion_red) != self.sesion_red:
            return
        tipo = mensaje["tipo"]
        if tipo == "bienvenida":
            self.mi_id = mensaje["id"]
            self.token_red = mensaje.get("token")
            self.recuperada_red = mensaje.get("recuperada", False)
        elif tipo == "sala":
            if self.dialogo_red:
                self.dialogo_red.estado.setText("\n".join(f"{j['nombre']} · {j['rol']}" for j in mensaje["jugadores"]))
        elif tipo == "estado":
            if mensaje["revision"] == self.revision_red:
                if self.escenas.currentWidget() is self.escena_accion and mensaje["fase"] == "jugando":
                    self.escena_accion.actualizar_plazo_red(mensaje.get("plazo_segundos"))
                return
            if mensaje["revision"] <= self.revision_red:
                return
            primero = self.revision_red < 0
            reanudando = self.fase_red == "interrumpida" or self.recuperada_red
            self.revision_red = mensaje["revision"]
            self.fase_red = mensaje["fase"]
            self.establecer_juego(Juego.desde_datos(mensaje["datos"]))
            self.escena_red.boton_continuar.setEnabled(True)
            if self.dialogo_red:
                self.dialogo_red.accept()
            if self.fase_red == "jugando":
                self.mostrar_escena(self.ESCENA_ACCION if reanudando else self.ESCENA_NARRACION_1 if primero else self.ESCENA_DIALOGO)
                if reanudando:
                    self.escena_accion.actualizar_plazo_red(mensaje.get("plazo_segundos"))
                self.recuperada_red = False
            elif self.fase_red == "resultado":
                self.mostrar_escena(self.ESCENA_RESULTADO_1)
            elif self.fase_red == "final":
                self.mostrar_escena(self.ESCENA_FIN)
            else:
                self.escena_accion.timer_decision.stop()
                ausentes = ", ".join(mensaje.get("desconectados", []))
                self.statusBar().showMessage(f"Campaña pausada. Esperando reconexión de {ausentes}.")
                self.escena_red.boton_continuar.setEnabled(False)
                for boton in (self.escena_accion.boton_compartir, self.escena_accion.boton_verificar, self.escena_accion.boton_ignorar, self.escena_accion.boton_reportar):
                    boton.setEnabled(False)
            self.recuperada_red = False
        elif tipo in ("error", "desconexion"):
            self.audio.reproducir_efecto("error")
            self.statusBar().showMessage(mensaje.get("texto", "Error de red"))
            if self.dialogo_red and self.dialogo_red.isVisible():
                self.dialogo_red.estado.setText(mensaje.get("texto", "Sin conexión"))

    def cerrar_red(self):
        self.sesion_red += 1
        if self.cliente_red is not None:
            self.cliente_red.cerrar()
            self.cliente_red = None
        if self.servidor_red is not None:
            self.servidor_red.cerrar()
            self.servidor_red = None
        self.token_red = None
        self.datos_conexion = None

    def closeEvent(self, event):
        self.cerrar_red()
        self.audio.detener()
        for indice in range(self.escenas.count()):
            escena = self.escenas.widget(indice)
            if hasattr(escena, "finalizar_escena"):
                escena.finalizar_escena()
        super().closeEvent(event)

    def alternar_pantalla_completa(self):
        if self.pantalla_completa:
            self.showMaximized()
            self.pantalla_completa = False
        else:
            self.showFullScreen()
            self.pantalla_completa = True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="CIVICA — Alcalde Digital")
    parser.add_argument("--semilla", type=int)
    parser.add_argument("--sin-eventos", action="store_true")
    parser.add_argument("--sin-audio", action="store_true")
    parser.add_argument("--sin-limite", action="store_true")
    args = parser.parse_args()
    app = QApplication(sys.argv)

    ventana = VentanaPrincipal()
    ventana.establecer_juego(Juego(args.semilla, eventos=not args.sin_eventos))
    ventana.sin_limite = ventana.sin_limite or args.sin_limite
    if args.sin_audio:
        ventana.audio.silenciar()

    ventana.showMaximized()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()
