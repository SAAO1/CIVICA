import sys

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
)
from PyQt6.QtCore import (
    Qt,
    QTimer,
    QRect,
    QPoint,
    QPropertyAnimation,
    QParallelAnimationGroup,
    QEasingCurve,
    pyqtSignal,
)

from models.publicacion import Publicacion
from estructuras.bst import ArbolPublicaciones
from visualizador_bst import VisualizadorBST


class EscenaInicio(QWidget):
    continuar = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.fondo = QLabel(self)
        self.fondo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fondo.setScaledContents(False)

        self.boton_inicio = QPushButton(self)
        self.boton_inicio.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 12);
            }
            """
        )
        self.boton_inicio.clicked.connect(self.iniciar)

        self.setFocusPolicy(
            Qt.FocusPolicy.StrongFocus
        )

    def resizeEvent(self, event):
        self.actualizar_fondo()
        self.actualizar_boton()
        super().resizeEvent(event)

    def actualizar_fondo(self):
        pixmap = QPixmap(
            "assets/fondos/fondo escena portada.jfif"
        )

        if pixmap.isNull():
            self.fondo.setText(
                "ALCALDE DIGITAL"
            )
            self.fondo.setStyleSheet(
                "color: white; background: black; font-size: 40px;"
            )
            self.fondo.setGeometry(
                self.rect()
            )
            return

        pixmap_escalado = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )

        self.fondo.setPixmap(
            pixmap_escalado
        )

        self.fondo.setGeometry(
            self.rect()
        )

    def actualizar_boton(self):
        ancho = self.width()
        alto = self.height()

        x = int(ancho * 0.296)
        y = int(alto * 0.829)
        w = int(ancho * 0.438)
        h = int(alto * 0.110)

        self.boton_inicio.setGeometry(
            x,
            y,
            w,
            h
        )

    def iniciar(self):
        self.continuar.emit()
        self.setFocus()

    def keyPressEvent(self, event):
        if event.key() in (
            Qt.Key.Key_Space,
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
        ):
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
        pixmap = QPixmap(self.ruta_imagen)

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
            "QFrame { background-color: #000000; border: none; }"
        )

        self.franja_inferior = QFrame(self)
        self.franja_inferior.setStyleSheet(
            "QFrame { background-color: #000000; border: none; }"
        )

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
            Qt.AlignmentFlag.AlignCenter
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
            Qt.AlignmentFlag.AlignCenter |
            Qt.AlignmentFlag.AlignVCenter
        )

        self.texto_completo = ""
        self.nombre_inicial = ""
        self.escribiendo = False
        self.animando = False

        self.cargar_fuente()

        self.setFocusPolicy(
            Qt.FocusPolicy.StrongFocus
        )

    def cargar_fuente(self):
        ruta_fuente = "assets/Fuente Letra/Anton.ttf"

        fuente_id = QFontDatabase.addApplicationFont(
            ruta_fuente
        )

        if fuente_id != -1:
            familias = QFontDatabase.applicationFontFamilies(
                fuente_id
            )
            familia = familias[0] if familias else "Arial"
        else:
            familia = "Arial"

        self.fuente_nombre = QFont(familia)
        self.fuente_nombre.setPointSize(19)
        self.fuente_nombre.setBold(True)

        self.fuente_dialogo = QFont(familia)
        self.fuente_dialogo.setPointSize(23)
        self.fuente_dialogo.setBold(False)

        self.nombre_label.setFont(self.fuente_nombre)
        self.texto_label.setFont(self.fuente_dialogo)

    def resizeEvent(self, event):
        self.actualizar_geometria()
        self.actualizar_fondo()
        super().resizeEvent(event)

    def actualizar_fondo(self):
        pixmap = QPixmap(self.fondo)

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

        altura_franja = max(105, int(alto * 0.18))
        margen = int(ancho * 0.08)

        self.altura_franja = altura_franja

        self.franja_superior.setGeometry(
            0,
            -altura_franja,
            ancho,
            altura_franja
        )

        self.franja_inferior.setGeometry(
            0,
            alto,
            ancho,
            altura_franja
        )

        self.nombre_label.setGeometry(
            margen,
            alto - altura_franja + 14,
            ancho - margen * 2,
            32
        )

        self.texto_label.setGeometry(
            margen,
            alto - altura_franja + 49,
            ancho - margen * 2,
            altura_franja - 58
        )

        ancho_personaje = int(ancho * 0.40)
        alto_personaje = int(alto * 0.72)
        y_personaje = int(alto * 0.10)
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
        self.animando = False
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

        QTimer.singleShot(
            self.TIEMPO_ANTES_DE_HABLAR,
            self.preparar_dialogo
        )

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
        if self.animacion is not None:
            self.animacion.stop()

        self.texto_completo = texto
        self.escribiendo = False
        self.animando = True

        nombre_normalizado = nombre.upper().strip()

        if nombre_normalizado in ("", "NARRADOR"):
            self.nombre_label.clear()
            self.nombre_label.hide()
        else:
            self.nombre_label.setText(
                nombre_normalizado
            )
            self.nombre_label.show()

        self.texto_label.setText(texto)
        self.texto_label.show()

        self.configurar_personajes_para_hablante(
            nombre_normalizado,
            presentes
        )

        self.actualizar_geometria()

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
        self.animando = False

    def avanzar(self):
        if self.animando:
            return

        self.dialogo_terminado.emit()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.avanzar()
            event.accept()
            return

        super().mousePressEvent(event)

    def keyPressEvent(self, event):
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

        self.dialogos = [
            (
                "CIUDADANO",
                f"Mira esto. {texto_publicacion}"
            ),
            (
                "PERIODISTA",
                "No deberíamos compartirla todavía. Primero tenemos que comprobar si la información es cierta."
            ),
            (
                "CIUDADANO",
                "Entonces tenemos que decidir qué hacer antes de que más personas la vean."
            )
        ]

        self.presentes_dialogo = {
            nombre.upper()
            for nombre, _ in self.dialogos
            if nombre.upper() in self.personajes
        }

    def comenzar_escena(self):
        self.preparar_dialogos()
        self.dialogo_actual = 0

        if self.animacion is not None:
            self.animacion.stop()

        self.animando = False
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

        QTimer.singleShot(
            self.TIEMPO_ANTES_DE_HABLAR,
            self.mostrar_dialogo_actual
        )

        self.setFocus()

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
        ancho = self.width()
        alto = self.height()

        animacion_superior = QPropertyAnimation(
            self.franja_superior,
            b"geometry",
            self
        )
        animacion_superior.setDuration(300)
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
        animacion_inferior.setDuration(300)
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

        self.panel = QFrame(self)
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
        layout.setContentsMargins(38, 28, 38, 32)
        layout.setSpacing(15)
        layout.addWidget(self.titulo)
        layout.addWidget(self.publicacion)
        layout.addWidget(self.info)
        layout.addWidget(self.turno)
        layout.addLayout(botones)

    def resizeEvent(self, event):
        self.actualizar_fondo()

        margen_x = int(self.width() * 0.12)
        ancho_panel = self.width() - margen_x * 2

        self.panel.setGeometry(
            margen_x,
            int(self.height() * 0.10),
            ancho_panel,
            int(self.height() * 0.80)
        )

        super().resizeEvent(event)

    def actualizar_fondo(self):
        pixmap = QPixmap(
            "assets/fondos/Escena 5.png"
        )

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

        self.publicacion.setText(
            f'"{publicacion.texto}"'
        )

        self.info.setText(
            f"ID #{publicacion.id}   •   Impacto {publicacion.impacto}"
        )

        self.turno.setText(
            "DECISIÓN DEL CIUDADANO"
        )

    def ejecutar_accion(self, accion):
        resultado = self.juego.ejecutar_accion(
            accion
        )

        if resultado is False:
            return

        self.window().mostrar_escena(
            self.window().ESCENA_RESULTADO_1
        )


class VisualizadorBSTBonito(QWidget):

    def __init__(self, arbol, parent=None):
        super().__init__(parent)

        self.arbol = arbol
        self.setMinimumHeight(380)
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
        if estado == "FALSA VERIFICADA":
            return QColor("#D97F7F")

        if estado == "VERIFICADA":
            return QColor("#73A89A")

        if estado == "COMPARTIDA":
            return QColor("#D5A45F")

        if estado == "IGNORADA":
            return QColor("#78899A")

        return QColor("#6F88A3")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        if self.arbol.raiz is None:
            painter.setPen(QColor("#F8EEE7"))
            painter.setFont(
                QFont(
                    "Arial",
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

        ancho_util = self.width() - 120

        for nivel, nodos in enumerate(niveles):
            y = 68 + nivel * 108

            for nodo in nodos:
                indice = indice_inorden.get(
                    id(nodo),
                    0
                )

                x = (
                    60
                    + ancho_util *
                    (indice + 0.5) /
                    cantidad_total
                )

                posiciones[id(nodo)] = (
                    int(x),
                    int(y)
                )

        painter.setPen(
            QPen(
                QColor("#F1DDCE"),
                5,
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

        radio = 35

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

            painter.setPen(
                QColor("#FFFFFF")
            )

            painter.setFont(
                QFont(
                    "Arial",
                    13,
                    QFont.Weight.Bold
                )
            )

            painter.drawText(
                x - radio,
                y - 12,
                radio * 2,
                24,
                Qt.AlignmentFlag.AlignCenter,
                f"#{publicacion.id}"
            )

        painter.end()


class EscenaArbol(QWidget):

    def __init__(self, juego, parent=None):
        super().__init__(parent)

        self.juego = juego

        self.fondo = QLabel(self)
        self.fondo.setScaledContents(False)
        self.fondo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fondo.lower()

        self.panel = QFrame(self)
        self.panel.setStyleSheet("""
            QFrame#panelArbol {
                background-color: rgba(19, 31, 43, 210);
                border: 1px solid rgba(242, 207, 191, 145);
                border-radius: 24px;
            }

            QLabel {
                color: #FFF8F3;
                background: transparent;
                border: none;
            }

            QLabel#tituloArbol {
                color: #F4C7B5;
                font-size: 26px;
                font-weight: bold;
            }

            QLabel#operacion {
                color: #E6D8CF;
                font-size: 14px;
                font-weight: bold;
            }

            QPushButton {
                background-color: rgba(91, 107, 124, 245);
                color: white;
                border: 2px solid #E7C8B8;
                border-radius: 13px;
                padding: 11px 18px;
                font-size: 15px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: rgba(117, 136, 156, 255);
                border-color: #FFF2E9;
            }

            QPushButton:pressed {
                background-color: rgba(63, 78, 93, 255);
            }

            QPushButton#continuar {
                background-color: rgba(185, 111, 103, 250);
                border-color: #F5D4C5;
            }

            QPushButton#continuar:hover {
                background-color: rgba(210, 127, 115, 255);
            }

            QFrame#acciones {
                background-color: rgba(15, 24, 35, 170);
                border-radius: 18px;
                border: 1px solid rgba(245, 222, 210, 70);
            }
        """)
        self.panel.setObjectName("panelArbol")

        titulo = QLabel(
            "ÁRBOL BINARIO DE BÚSQUEDA"
        )
        titulo.setObjectName("tituloArbol")
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

        acciones = QFrame()
        acciones.setObjectName("acciones")

        self.boton_inorden = QPushButton(
            "INORDEN"
        )

        self.boton_preorden = QPushButton(
            "PREORDEN"
        )

        self.boton_postorden = QPushButton(
            "POSTORDEN"
        )

        self.boton_continuar = QPushButton(
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
        botones.setContentsMargins(
            12,
            10,
            12,
            10
        )
        botones.setSpacing(12)
        botones.addWidget(
            self.boton_inorden
        )
        botones.addWidget(
            self.boton_preorden
        )
        botones.addWidget(
            self.boton_postorden
        )

        layout = QVBoxLayout(self.panel)
        layout.setContentsMargins(
            25,
            18,
            25,
            20
        )
        layout.setSpacing(10)
        layout.addWidget(titulo)
        layout.addWidget(self.operacion)
        layout.addWidget(self.visualizador, 1)
        layout.addWidget(acciones)
        layout.addWidget(self.resultado)
        layout.addWidget(self.boton_continuar)

    def resizeEvent(self, event):
        pixmap = QPixmap(
            "assets/fondos/Escena Arbol.jfif"
        )

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

        self.panel.setGeometry(
            int(self.width() * 0.06),
            int(self.height() * 0.04),
            int(self.width() * 0.88),
            int(self.height() * 0.92)
        )

        super().resizeEvent(event)

    def mostrar(self):
        self.visualizador.actualizar()

        self.operacion.setText(
            self.juego.ultimo_resultado
        )

        self.resultado.setText("")

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
        self.window().continuar_desde_arbol()


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
        ventana = self.window()

        if not hasattr(ventana, "juego"):
            return "", ""

        juego = ventana.juego
        publicacion = juego.obtener_publicacion_actual()
        accion = juego.ultima_accion

        publicacion_id = (
            publicacion.id
            if publicacion is not None
            else juego.ultima_publicacion_id
        )

        publicacion_verdadera = (
            publicacion.verdadera
            if publicacion is not None
            else juego.ultima_publicacion_verdadera
        )

        if publicacion_id is None:
            return (
                "No hay una publicación disponible para mostrar.",
                ""
            )

        if self.tipo == 1:
            if accion == "compartir":
                return (
                    "La publicación comenzó a circular con mayor fuerza. La periodista decide comprobar la información antes de que el rumor siga creciendo.",
                    "PERIODISTA"
                )

            if accion == "verificar":
                return (
                    "La periodista contrasta la publicación con fuentes oficiales para determinar si la afirmación tiene fundamento.",
                    "PERIODISTA"
                )

            if accion == "reportar":
                return (
                    "El reporte fue enviado. La periodista revisa la publicación para confirmar que la información debía ser retirada.",
                    "PERIODISTA"
                )

            return (
                "La publicación permanece en Civitas mientras la periodista decide comprobar qué hay detrás del mensaje.",
                "PERIODISTA"
            )

        if self.tipo == 2:
            if publicacion_verdadera:
                return (
                    f"La publicación #{publicacion_id} corresponde con la información disponible. La verificación ayudó a separar una noticia real de un simple rumor.",
                    "PERIODISTA"
                )

            return (
                f"La publicación #{publicacion_id} no coincide con la información oficial. El rumor es falso y ya fue identificado.",
                "PERIODISTA"
            )

        if accion == "compartir":
            return (
                "La publicación obtuvo mayor alcance. La desinformación aumentó y ahora los dos jugadores deberán prestar más atención a las próximas publicaciones.",
                ""
            )

        if accion == "verificar":
            return (
                "La verificación ayudó a aumentar la información confiable y a reducir parte de la desinformación que circulaba por Civitas.",
                ""
            )

        if accion == "reportar":
            return (
                "La publicación fue retirada del Árbol Binario de Búsqueda. La siguiente información que aparezca será incorporada al árbol cuando avance la partida.",
                ""
            )

        return (
            "La publicación permanece en Civitas. El árbol conserva el nodo porque la información todavía no ha sido retirada.",
            ""
        )

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


class Juego:

    def __init__(self):

        self.arbol = ArbolPublicaciones()

        self.indice_proxima_publicacion = 0
        self.publicacion_actual_id = None

        self.publicaciones_eliminadas = []

        self.info_verificada = 0
        self.confianza = 0
        self.desinformacion = 0
        self.convivencia = 0
        self.bienestar_digital = 0
        self.conflictos = 0

        self.ultima_accion = None
        self.ultima_publicacion_id = None
        self.ultima_publicacion_texto = ""
        self.ultima_publicacion_verdadera = None
        self.ultimo_resultado = (
            "El árbol comenzará vacío."
        )

        self.publicaciones_planificadas = (
            self.crear_publicaciones()
        )

    def crear_publicaciones(self):

        return [
            Publicacion(
                50,
                "El candidato Juan quiere cerrar el colegio.",
                False,
                7
            ),

            Publicacion(
                70,
                "El parque central tendrá mantenimiento.",
                True,
                3
            ),

            Publicacion(
                30,
                "Adrián Morales presentó una nueva propuesta.",
                True,
                4
            ),

            Publicacion(
                20,
                "La ciudad construirá una nueva biblioteca.",
                True,
                2
            ),

            Publicacion(
                60,
                "Circula un rumor sobre uno de los candidatos.",
                False,
                8
            ),

            Publicacion(
                80,
                "Una encuesta afirma conocer al próximo alcalde.",
                False,
                6
            ),
        ]

    def agregar_publicacion(self, publicacion):

        if publicacion is None:
            return False

        if self.arbol.buscar(publicacion.id) is not None:
            self.publicacion_actual_id = publicacion.id
            self.ultimo_resultado = (
                f"La publicación #{publicacion.id} ya existe en el ABB."
            )
            return False

        self.arbol.insertar(publicacion)
        self.publicacion_actual_id = publicacion.id

        self.ultimo_resultado = (
            f"INSERTAR: publicación #{publicacion.id} "
            "agregada al ABB."
        )

        return True

    def agregar_siguiente_publicacion(self):

        if (
            self.indice_proxima_publicacion
            >= len(self.publicaciones_planificadas)
        ):
            self.publicacion_actual_id = None

            self.ultimo_resultado = (
                "No quedan más publicaciones por insertar."
            )

            return False

        publicacion = self.publicaciones_planificadas[
            self.indice_proxima_publicacion
        ]

        self.indice_proxima_publicacion += 1

        return self.agregar_publicacion(publicacion)

    def iniciar_primera_publicacion(self):

        if self.publicacion_actual_id is not None:
            return True

        return self.agregar_siguiente_publicacion()

    def obtener_publicaciones_activas(self):

        return self.arbol.inorden()

    def obtener_publicacion_actual(self):

        if self.publicacion_actual_id is None:
            return None

        publicacion = self.arbol.buscar(
            self.publicacion_actual_id
        )

        return publicacion

    def ejecutar_accion(self, accion):

        publicacion_actual = (
            self.obtener_publicacion_actual()
        )

        if publicacion_actual is None:
            return False

        publicacion = self.arbol.buscar(
            publicacion_actual.id
        )

        if publicacion is None:
            return False

        self.ultima_accion = accion
        self.ultima_publicacion_id = publicacion.id
        self.ultima_publicacion_texto = publicacion.texto
        self.ultima_publicacion_verdadera = publicacion.verdadera

        if accion == "compartir":

            publicacion.compartidos += 1
            publicacion.impacto += 1

            publicacion.estado = (
                "COMPARTIDA"
            )

            self.desinformacion += 2

            self.ultimo_resultado = (
                f"COMPARTIR: publicación #{publicacion.id} "
                "encontrada con buscar() y actualizada."
            )

        elif accion == "verificar":

            publicacion.verificaciones += 1

            self.info_verificada += 5
            self.confianza += 3

            self.desinformacion = max(
                0,
                self.desinformacion - 3
            )

            if publicacion.verdadera:

                publicacion.estado = (
                    "VERIFICADA"
                )

                self.ultimo_resultado = (
                    f"VERIFICAR: publicación #{publicacion.id} "
                    "encontrada con buscar(); es verdadera."
                )

            else:

                publicacion.estado = (
                    "FALSA VERIFICADA"
                )

                self.ultimo_resultado = (
                    f"VERIFICAR: publicación #{publicacion.id} "
                    "encontrada con buscar(); es falsa."
                )

        elif accion == "ignorar":

            publicacion.estado = (
                "IGNORADA"
            )

            self.ultimo_resultado = (
                f"IGNORAR: publicación #{publicacion.id} "
                "encontrada con buscar(); permanece en el ABB."
            )

        elif accion == "reportar":

            publicacion.reportes += 1

            self.confianza += 2

            self.desinformacion = max(
                0,
                self.desinformacion - 2
            )

            self.publicaciones_eliminadas.append(
                publicacion.id
            )

            id_eliminado = publicacion.id

            self.arbol.eliminar(
                id_eliminado
            )

            if self.arbol.buscar(
                id_eliminado
            ) is None:

                self.ultimo_resultado = (
                    f"REPORTAR: publicación #{id_eliminado} "
                    "encontrada y eliminada del ABB con eliminar()."
                )

            else:

                self.ultimo_resultado = (
                    f"REPORTAR: no se pudo eliminar "
                    f"la publicación #{id_eliminado}."
                )

            self.publicacion_actual_id = None

        return True

    def avanzar_publicacion(self):

        if self.publicacion_actual_id is not None:

            publicacion = (
                self.obtener_publicacion_actual()
            )

            if publicacion is not None:
                publicacion.estado = (
                    publicacion.estado
                )

        return self.agregar_siguiente_publicacion()

    def hay_publicaciones(self):

        return (
            self.publicacion_actual_id
            is not None
        )


class EscenaFin(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setStyleSheet(
            """
            QWidget {
                background-color: #101827;
            }

            QLabel {
                color: white;
            }
            """
        )

        titulo = QLabel(
            "FIN DE LA DEMOSTRACIÓN"
        )

        titulo.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        titulo.setFont(
            QFont(
                "Arial",
                30,
                QFont.Weight.Bold
            )
        )

        texto = QLabel(
            "Las publicaciones de Civitas fueron "
            "procesadas mediante el Árbol Binario de Búsqueda."
        )

        texto.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        texto.setWordWrap(True)

        texto.setFont(
            QFont(
                "Arial",
                20
            )
        )

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            80,
            80,
            80,
            80
        )

        layout.setSpacing(30)

        layout.addStretch()

        layout.addWidget(
            titulo
        )

        layout.addWidget(
            texto
        )

        layout.addStretch()

        self.setLayout(layout)

    def mostrar(self):
        self.setFocus()


class VentanaPrincipal(QMainWindow):

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

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "Alcalde Digital"
        )

        self.setMinimumSize(
            1100,
            700
        )

        self.pantalla_completa = False

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
            self.escena_fin
        ):
            self.escenas.addWidget(escena)

        self.setCentralWidget(
            self.escenas
        )

        self.escena_inicio.continuar.connect(
            self.comenzar_juego
        )

        self.mostrar_escena(
            self.ESCENA_INICIO
        )

    def comenzar_juego(self):
        self.mostrar_escena(
            self.ESCENA_NARRACION_1
        )

    def mostrar_escena(self, indice):
        self.escenas.setCurrentIndex(
            indice
        )

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

    def continuar_desde_arbol(self):
        if self.juego.agregar_siguiente_publicacion():
            self.mostrar_escena(
                self.ESCENA_DIALOGO
            )
        else:
            self.mostrar_escena(
                self.ESCENA_FIN
            )

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F11:
            self.alternar_pantalla_completa()
            event.accept()
            return

        super().keyPressEvent(event)

    def alternar_pantalla_completa(self):
        if self.pantalla_completa:
            self.showMaximized()
            self.pantalla_completa = False
        else:
            self.showFullScreen()
            self.pantalla_completa = True


def main():

    app = QApplication(sys.argv)

    ventana = VentanaPrincipal()

    ventana.showMaximized()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()



