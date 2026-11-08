"""interfaz.escenas.inicio: presentación separada de las reglas del juego."""
from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from infraestructura.recursos import pixmap_recurso
from interfaz.componentes.arte import PanelIlustrado, BotonIlustrado, pixmap_arte
from interfaz.cinematica.fondos import FondoEscena


class EscenaInicio(QWidget):
    continuar = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.fondo = FondoEscena(self)
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
        self.fondo.establecer_escena("assets/fondos/fondo escena portada.jfif", "portada")
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
