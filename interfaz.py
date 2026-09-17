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
)
from PyQt6.QtGui import (
    QPixmap,
    QFont,
    QFontDatabase,
)
from PyQt6.QtCore import (
    Qt,
    QTimer,
    QRect,
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


class EscenaCinematica(QFrame):

    dialogo_terminado = pyqtSignal()

    VELOCIDAD_TEXTO = 38
    DURACION_FRANJAS = 550
    PAUSA_CINEMATICA = 180
    TIEMPO_ANTES_DE_HABLAR = 1000

    def __init__(self, fondo, parent=None):
        super().__init__(parent)

        self.fondo = fondo

        self.texto_completo = ""
        self.posicion_texto = 0

        self.escribiendo = False
        self.animando = False

        self.altura_franja = 0
        self.animacion = None

        self.fondo_label = QLabel(self)
        self.fondo_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.franja_superior = QFrame(self)
        self.franja_superior.setStyleSheet(
            """
            QFrame {
                background-color: #000000;
                border: none;
            }
            """
        )

        self.franja_inferior = QFrame(self)
        self.franja_inferior.setStyleSheet(
            """
            QFrame {
                background-color: #000000;
                border: none;
            }
            """
        )

        self.nombre_label = QLabel(self)
        self.nombre_label.setStyleSheet(
            """
            QLabel {
                color: white;
                background: transparent;
            }
            """
        )

        self.nombre_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft |
            Qt.AlignmentFlag.AlignVCenter
        )

        self.texto_label = QLabel(self)
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
            Qt.AlignmentFlag.AlignTop
        )

        self.timer_texto = QTimer(self)

        self.timer_texto.timeout.connect(
            self.escribir_siguiente_letra
        )

        self.cargar_fuente()

        self.setFocusPolicy(
            Qt.FocusPolicy.StrongFocus
        )

    def cargar_fuente(self):
        ruta_fuente = (
            "assets/Fuente Letra/Anton.ttf"
        )

        fuente_id = (
            QFontDatabase.addApplicationFont(
                ruta_fuente
            )
        )

        if fuente_id != -1:

            familias = (
                QFontDatabase.applicationFontFamilies(
                    fuente_id
                )
            )

            if familias:
                familia = familias[0]
            else:
                familia = "Arial"

        else:
            familia = "Arial"

        self.fuente_nombre = QFont(
            familia
        )

        self.fuente_nombre.setPointSize(
            20
        )

        self.fuente_nombre.setBold(
            True
        )

        self.fuente_dialogo = QFont(
            familia
        )

        self.fuente_dialogo.setPointSize(
            25
        )

        self.fuente_dialogo.setBold(
            False
        )

        self.nombre_label.setFont(
            self.fuente_nombre
        )

        self.texto_label.setFont(
            self.fuente_dialogo
        )

    def resizeEvent(self, event):

        self.actualizar_geometria()
        self.actualizar_fondo()

        super().resizeEvent(event)

    def actualizar_fondo(self):

        pixmap = QPixmap(
            self.fondo
        )

        if pixmap.isNull():

            self.fondo_label.clear()

            self.fondo_label.setStyleSheet(
                """
                QLabel {
                    background-color: #111111;
                    color: white;
                }
                """
            )

            return

        pixmap_escalado = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )

        self.fondo_label.setPixmap(
            pixmap_escalado
        )

        self.fondo_label.setGeometry(
            self.rect()
        )

        self.fondo_label.lower()

    def actualizar_geometria(self):

        ancho = self.width()
        alto = self.height()

        if ancho <= 0 or alto <= 0:
            return

        self.altura_franja = max(
            95,
            int(alto * 0.16)
        )

        margen = int(
            ancho * 0.09
        )

        self.franja_superior.setGeometry(
            0,
            -self.altura_franja,
            ancho,
            self.altura_franja
        )

        self.franja_inferior.setGeometry(
            0,
            alto,
            ancho,
            self.altura_franja
        )

        self.nombre_label.setGeometry(
            margen,
            alto - self.altura_franja + 18,
            ancho - margen * 2,
            30
        )

        self.texto_label.setGeometry(
            margen,
            alto - self.altura_franja + 53,
            ancho - margen * 2,
            self.altura_franja - 65
        )

    def mostrar_fondo(self):

        self.actualizar_fondo()
        self.actualizar_geometria()

    def comenzar_escena(self):

        self.timer_texto.stop()

        if self.animacion is not None:
            self.animacion.stop()

        self.escribiendo = False
        self.animando = False

        self.texto_completo = ""
        self.posicion_texto = 0

        self.nombre_label.setText("")
        self.texto_label.setText("")

        self.nombre_label.hide()
        self.texto_label.hide()

        self.mostrar_fondo()

        self.franja_superior.raise_()
        self.franja_inferior.raise_()
        self.nombre_label.raise_()
        self.texto_label.raise_()

        ancho = self.width()
        alto = self.height()

        self.franja_superior.setGeometry(
            0,
            -self.altura_franja,
            ancho,
            self.altura_franja
        )

        self.franja_inferior.setGeometry(
            0,
            alto,
            ancho,
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
        nombre=""
    ):

        self.timer_texto.stop()

        if self.animacion is not None:
            self.animacion.stop()

        self.texto_completo = texto
        self.posicion_texto = 0

        self.escribiendo = False
        self.animando = True

        self.nombre_label.setText(
            nombre
        )

        self.texto_label.setText("")

        if nombre:
            self.nombre_label.show()
        else:
            self.nombre_label.hide()

        self.texto_label.hide()

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

        self.franja_superior.setGeometry(
            inicio_superior
        )

        self.franja_inferior.setGeometry(
            inicio_inferior
        )

        animacion_superior = QPropertyAnimation(
            self.franja_superior,
            b"geometry"
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
            b"geometry"
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

        self.animacion = (
            QParallelAnimationGroup(self)
        )

        self.animacion.addAnimation(
            animacion_superior
        )

        self.animacion.addAnimation(
            animacion_inferior
        )

        self.animacion.finished.connect(
            self.comenzar_escritura
        )

        self.animacion.start()

    def comenzar_escritura(self):

        self.animando = False

        QTimer.singleShot(
            self.PAUSA_CINEMATICA,
            self.iniciar_escritura
        )

    def iniciar_escritura(self):

        if not self.texto_completo:

            self.escribiendo = False
            return

        self.posicion_texto = 0
        self.escribiendo = True

        self.texto_label.setText("")
        self.texto_label.show()

        self.texto_label.raise_()

        self.timer_texto.start(
            self.VELOCIDAD_TEXTO
        )

    def escribir_siguiente_letra(self):

        if (
            self.posicion_texto
            >= len(self.texto_completo)
        ):

            self.timer_texto.stop()
            self.escribiendo = False

            return

        self.posicion_texto += 1

        self.texto_label.setText(
            self.texto_completo[
                :self.posicion_texto
            ]
        )

    def avanzar(self):

        if self.animando:
            return

        if self.escribiendo:

            self.timer_texto.stop()

            self.posicion_texto = len(
                self.texto_completo
            )

            self.texto_label.setText(
                self.texto_completo
            )

            self.escribiendo = False
            return

        self.dialogo_terminado.emit()

    def mousePressEvent(self, event):

        if (
            event.button()
            == Qt.MouseButton.LeftButton
        ):

            self.avanzar()

            event.accept()
            return

        super().mousePressEvent(event)

    def keyPressEvent(self, event):

        if event.key() in (
            Qt.Key.Key_Space,
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
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
        parent=None
    ):

        super().__init__(
            fondo,
            parent
        )

        self.texto_inicial = texto
        self.nombre_inicial = ""

        self.siguiente = siguiente

        self.dialogo_terminado.connect(
            self.terminar_escena
        )

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
            "assets/fondos/Escena 2 Telefono.jfif",
            parent
        )

        self.dialogos = [
            (
                "LAURA",
                "Espera un momento, Daniel. Estoy revisando una publicación de Civitas que me parece sospechosa."
            ),
            (
                "DANIEL",
                "¿La del Colegio Central? Ya la vi. Tiene cientos de compartidos."
            ),
        ]

        self.dialogo_actual = 0

        self.dialogo_terminado.connect(
            self.siguiente_dialogo
        )

    def comenzar_escena(self):

        self.dialogo_actual = 0

        self.mostrar_fondo()

        self.timer_texto.stop()

        if self.animacion is not None:
            self.animacion.stop()

        self.escribiendo = False
        self.animando = False

        self.texto_label.setText("")
        self.nombre_label.setText("")

        self.nombre_label.hide()
        self.texto_label.hide()

        self.actualizar_geometria()

        ancho = self.width()
        alto = self.height()

        self.franja_superior.setGeometry(
            0,
            -self.altura_franja,
            ancho,
            self.altura_franja
        )

        self.franja_inferior.setGeometry(
            0,
            alto,
            ancho,
            self.altura_franja
        )

        QTimer.singleShot(
            self.TIEMPO_ANTES_DE_HABLAR,
            self.mostrar_dialogo_actual
        )

        self.setFocus()

    def mostrar_dialogo_actual(self):

        if (
            self.dialogo_actual
            >= len(self.dialogos)
        ):

            self.terminar_escena()
            return

        nombre, texto = self.dialogos[
            self.dialogo_actual
        ]

        self.iniciar_dialogo(
            texto,
            nombre
        )

    def siguiente_dialogo(self):

        self.dialogo_actual += 1

        if (
            self.dialogo_actual
            >= len(self.dialogos)
        ):

            self.terminar_escena()
            return

        self.ocultar_franjas(
            self.mostrar_dialogo_actual
        )

    def ocultar_franjas(
        self,
        siguiente
    ):

        ancho = self.width()
        alto = self.height()

        animacion_superior = QPropertyAnimation(
            self.franja_superior,
            b"geometry"
        )

        animacion_superior.setDuration(
            350
        )

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

        animacion_inferior = QPropertyAnimation(
            self.franja_inferior,
            b"geometry"
        )

        animacion_inferior.setDuration(
            350
        )

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

        grupo = QParallelAnimationGroup(
            self
        )

        grupo.addAnimation(
            animacion_superior
        )

        grupo.addAnimation(
            animacion_inferior
        )

        grupo.finished.connect(
            siguiente
        )

        grupo.start()

        self.animacion = grupo

    def terminar_escena(self):

        ventana = self.window()

        if hasattr(
            ventana,
            "mostrar_escena"
        ):

            ventana.mostrar_escena(
                ventana.ESCENA_ACCION
            )


class EscenaAccion(QWidget):

    def __init__(self, juego, parent=None):

        super().__init__(parent)

        self.juego = juego

        self.setStyleSheet(
            """
            QWidget {
                background-color: #101827;
            }

            QLabel {
                color: white;
            }

            QPushButton {
                background-color: #1D2B42;
                color: white;
                border: 2px solid #40546F;
                border-radius: 12px;
                padding: 16px;
                font-size: 18px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #2B405F;
            }

            QPushButton:pressed {
                background-color: #172236;
            }
            """
        )

        self.titulo = QLabel()

        self.titulo.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.titulo.setFont(
            QFont(
                "Arial",
                25,
                QFont.Weight.Bold
            )
        )

        self.publicacion = QLabel()

        self.publicacion.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.publicacion.setWordWrap(True)

        self.publicacion.setMinimumHeight(
            150
        )

        self.publicacion.setMaximumWidth(
            1000
        )

        self.publicacion.setFont(
            QFont(
                "Arial",
                22
            )
        )

        self.info = QLabel()

        self.info.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.info.setFont(
            QFont(
                "Arial",
                16
            )
        )

        self.boton_compartir = QPushButton(
            "COMPARTIR"
        )

        self.boton_verificar = QPushButton(
            "VERIFICAR"
        )

        self.boton_ignorar = QPushButton(
            "IGNORAR"
        )

        self.boton_reportar = QPushButton(
            "REPORTAR"
        )

        self.boton_compartir.clicked.connect(
            lambda: self.ejecutar_accion(
                "compartir"
            )
        )

        self.boton_verificar.clicked.connect(
            lambda: self.ejecutar_accion(
                "verificar"
            )
        )

        self.boton_ignorar.clicked.connect(
            lambda: self.ejecutar_accion(
                "ignorar"
            )
        )

        self.boton_reportar.clicked.connect(
            lambda: self.ejecutar_accion(
                "reportar"
            )
        )

        layout_principal = QVBoxLayout(
            self
        )

        layout_principal.setContentsMargins(
            70,
            45,
            70,
            45
        )

        layout_principal.setSpacing(
            25
        )

        layout_principal.addWidget(
            self.titulo
        )

        layout_principal.addWidget(
            self.publicacion
        )

        layout_principal.addWidget(
            self.info
        )

        botones = QGridLayout()

        botones.setSpacing(18)

        botones.addWidget(
            self.boton_compartir,
            0,
            0
        )

        botones.addWidget(
            self.boton_verificar,
            0,
            1
        )

        botones.addWidget(
            self.boton_ignorar,
            1,
            0
        )

        botones.addWidget(
            self.boton_reportar,
            1,
            1
        )

        layout_principal.addLayout(
            botones
        )

    def mostrar(self):

        publicacion = (
            self.juego.obtener_publicacion_actual()
        )

        if publicacion is None:

            self.titulo.setText(
                "No hay publicaciones disponibles"
            )

            self.publicacion.setText("")
            self.info.setText("")

            return

        self.titulo.setText(
            "PUBLICACIÓN DE CIVITAS"
        )

        self.publicacion.setText(
            f'"{publicacion.texto}"'
        )

        self.info.setText(
            f"ID: #{publicacion.id}    "
            f"Impacto: {publicacion.impacto}"
        )

    def ejecutar_accion(
        self,
        accion
    ):

        self.juego.ejecutar_accion(
            accion
        )

        self.window().mostrar_escena(
            self.window().ESCENA_ARBOL
        )


class EscenaArbol(QWidget):

    def __init__(self, juego, parent=None):

        super().__init__(parent)

        self.juego = juego

        self.setStyleSheet(
            """
            QWidget {
                background-color: #101827;
            }

            QLabel {
                color: white;
            }

            QPushButton {
                background-color: #1D2B42;
                color: white;
                border: 2px solid #40546F;
                border-radius: 10px;
                padding: 12px 20px;
                font-size: 16px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #2B405F;
            }
            """
        )

        titulo = QLabel(
            "ÁRBOL BINARIO DE BÚSQUEDA"
        )

        titulo.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        titulo.setFont(
            QFont(
                "Arial",
                25,
                QFont.Weight.Bold
            )
        )

        self.visualizador = VisualizadorBST(
            self.juego.arbol
        )

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

        self.resultado = QLabel()

        self.resultado.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.resultado.setFont(
            QFont(
                "Arial",
                15
            )
        )

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

        botones = QHBoxLayout()

        botones.setSpacing(15)

        botones.addWidget(
            self.boton_inorden
        )

        botones.addWidget(
            self.boton_preorden
        )

        botones.addWidget(
            self.boton_postorden
        )

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            40,
            25,
            40,
            25
        )

        layout.setSpacing(
            15
        )

        layout.addWidget(
            titulo
        )

        layout.addWidget(
            self.visualizador,
            1
        )

        layout.addLayout(
            botones
        )

        layout.addWidget(
            self.resultado
        )

        layout.addWidget(
            self.boton_continuar
        )

    def mostrar(self):

        self.visualizador.actualizar()

        self.resultado.setText(
            ""
        )

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

        self.juego.avanzar_publicacion()

        self.window().continuar_desde_arbol()


class Juego:

    def __init__(self):

        self.arbol = ArbolPublicaciones()

        self.indice_publicacion = 0

        self.publicaciones_eliminadas = []

        self.info_verificada = 0
        self.confianza = 0
        self.desinformacion = 0
        self.conviencia = 0
        self.bienestar_digital = 0
        self.conflictos = 0

        self.crear_publicaciones()

    def crear_publicaciones(self):

        publicaciones = [
            Publicacion(
                50,
                "El Colegio Central será cerrado mañana.",
                False,
                7
            ),

            Publicacion(
                30,
                "Adrián Morales presentó una nueva propuesta.",
                True,
                4
            ),

            Publicacion(
                70,
                "El parque central tendrá mantenimiento.",
                True,
                3
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

        for publicacion in publicaciones:

            self.arbol.insertar(
                publicacion
            )

    def obtener_publicaciones_activas(
        self
    ):

        publicaciones = (
            self.arbol.inorden()
        )

        return [
            p
            for p in publicaciones
            if p.id
            not in self.publicaciones_eliminadas
        ]

    def obtener_publicacion_actual(
        self
    ):

        activas = (
            self.obtener_publicaciones_activas()
        )

        if (
            self.indice_publicacion
            >= len(activas)
        ):
            return None

        return activas[
            self.indice_publicacion
        ]

    def ejecutar_accion(
        self,
        accion
    ):

        publicacion = (
            self.obtener_publicacion_actual()
        )

        if publicacion is None:
            return

        if accion == "compartir":

            publicacion.compartidos += 1
            publicacion.impacto += 1
            publicacion.estado = (
                "COMPARTIDA"
            )

            self.desinformacion += 2

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

            else:

                publicacion.estado = (
                    "FALSA VERIFICADA"
                )

        elif accion == "ignorar":

            publicacion.estado = (
                "IGNORADA"
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

            self.arbol.eliminar(
                publicacion.id
            )

    def avanzar_publicacion(self):

        self.indice_publicacion += 1

    def hay_publicaciones(self):

        return (
            self.obtener_publicacion_actual()
            is not None
        )


class VentanaPrincipal(QMainWindow):

    ESCENA_INICIO = 0
    ESCENA_NARRACION_1 = 1
    ESCENA_NARRACION_2 = 2
    ESCENA_NARRACION_3 = 3
    ESCENA_DIALOGO = 4
    ESCENA_ACCION = 5
    ESCENA_ARBOL = 6

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "Alcalde Digital"
        )

        self.setMinimumSize(
            1000,
            700
        )

        self.pantalla_completa = False

        self.juego = Juego()

        self.escenas = QStackedWidget()

        self.escena_inicio = (
            EscenaInicio()
        )

        self.escena_narracion_1 = (
            EscenaNarracion(
                "assets/fondos/Fondo escena 1.jfif",
                "Faltan pocos días para las elecciones.",
                self.ESCENA_NARRACION_2
            )
        )

        self.escena_narracion_2 = (
            EscenaNarracion(
                "assets/fondos/Fondo escena 2.png",
                "En Civitas comienzan a aparecer publicaciones polémicas.",
                self.ESCENA_NARRACION_3
            )
        )

        self.escena_narracion_3 = (
            EscenaNarracion(
                "assets/fondos/Escena 2 Telefono.jfif",
                "El candidato Juan quiere cerrar el colegio.",
                self.ESCENA_DIALOGO
            )
        )

        self.escena_dialogo = (
            EscenaDialogo()
        )

        self.escena_accion = (
            EscenaAccion(
                self.juego
            )
        )

        self.escena_arbol = (
            EscenaArbol(
                self.juego
            )
        )

        self.escenas.addWidget(
            self.escena_inicio
        )

        self.escenas.addWidget(
            self.escena_narracion_1
        )

        self.escenas.addWidget(
            self.escena_narracion_2
        )

        self.escenas.addWidget(
            self.escena_narracion_3
        )

        self.escenas.addWidget(
            self.escena_dialogo
        )

        self.escenas.addWidget(
            self.escena_accion
        )

        self.escenas.addWidget(
            self.escena_arbol
        )

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

    def mostrar_escena(
        self,
        indice
    ):

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

    def continuar_desde_arbol(
        self
    ):

        if self.juego.hay_publicaciones():

            self.mostrar_escena(
                self.ESCENA_DIALOGO
            )

        else:

            self.mostrar_escena(
                self.ESCENA_NARRACION_1
            )

    def keyPressEvent(
        self,
        event
    ):

        if event.key() == Qt.Key.Key_F11:

            self.alternar_pantalla_completa()

            event.accept()
            return

        super().keyPressEvent(event)

    def alternar_pantalla_completa(
        self
    ):

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