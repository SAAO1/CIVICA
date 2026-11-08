"""interfaz.escenas.arbol: presentación separada de las reglas del juego."""
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt
from infraestructura.recursos import pixmap_recurso
from interfaz.componentes.arte import PanelIlustrado, BotonIlustrado, decorar_botones, FUENTE_UI
from interfaz.cinematica.fondos import FondoEscena
from interfaz.componentes.arbol import VisualizadorBSTBonito


class EscenaArbol(QWidget):

    def __init__(self, juego, parent=None):
        super().__init__(parent)

        self.juego = juego

        self.fondo = FondoEscena(self)
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
        self.fondo.establecer_escena("assets/fondos/Escena Arbol.jfif", "observatorio")
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
