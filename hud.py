"""Indicadores legibles que se distribuyen según el espacio disponible."""
import math

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import QWidget, QLabel, QFrame, QHBoxLayout, QVBoxLayout, QGridLayout, QSizePolicy
from arte import FUENTE_UI, cargar_tipografias, icono_arte
from accesibilidad import paleta


class HudCiudad(QWidget):
    CAMPOS = (("confianza", "Confianza"), ("convivencia", "Convivencia"),
              ("bienestar_digital", "Bienestar"), ("info_verificada", "Verificada"),
              ("desinformacion", "Desinformación"), ("conflictos", "Conflictos"),
              ("participacion", "Participación"))

    def __init__(self, parent=None):
        super().__init__(parent)
        cargar_tipografias()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(0)
        self.setMinimumHeight(68)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 6, 14, 6)
        layout.setSpacing(14)
        self.marca = marca = QLabel("CIUDAD\nNOVA")
        marca.setStyleSheet(f"color:#e4c69d; font:700 12px '{FUENTE_UI}'; letter-spacing:1px;")
        marca.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(marca)
        self.rejilla = QGridLayout()
        self.rejilla.setContentsMargins(0, 0, 0, 0)
        self.rejilla.setHorizontalSpacing(8)
        self.rejilla.setVerticalSpacing(6)
        layout.addLayout(self.rejilla, 1)
        self.valores = {}
        self.etiquetas = {}
        self.iconos = {}
        self.tarjetas = {}
        self._columnas = 0
        self._ancho_tarjeta = 132
        self._modo = None
        for clave, nombre in self.CAMPOS:
            tarjeta = QFrame()
            tarjeta.setObjectName("indicadorCiudad")
            tarjeta.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            tarjeta.setMinimumWidth(0)
            tarjeta.setToolTip(f"{nombre}: estado actual de la ciudad")
            fila = QHBoxLayout(tarjeta)
            fila.setContentsMargins(9, 4, 9, 4)
            fila.setSpacing(7)
            icono = QLabel()
            id_icono = "bienestar" if clave == "bienestar_digital" else clave
            icono.setPixmap(icono_arte(id_icono).pixmap(QSize(25, 25)))
            icono.setFixedWidth(25)
            fila.addWidget(icono)
            texto = QVBoxLayout()
            texto.setSpacing(0)
            etiqueta = QLabel(nombre)
            etiqueta.setStyleSheet(f"color:#c7d7db; font:12px '{FUENTE_UI}'; background:transparent;")
            valor = QLabel("0")
            valor.setStyleSheet(f"color:#fff4dc; font:700 21px '{FUENTE_UI}'; background:transparent;")
            texto.addWidget(etiqueta)
            texto.addWidget(valor)
            fila.addLayout(texto, 1)
            self.valores[clave] = valor
            self.etiquetas[clave] = etiqueta
            self.iconos[clave] = icono
            self.tarjetas[clave] = tarjeta
            self._ancho_tarjeta = max(self._ancho_tarjeta, etiqueta.sizeHint().width() + 50)
        self._distribuir()

    def _distribuir(self):
        # Antes del primer layout Qt asigna sólo 100 px al widget. Usar ese
        # ancho produciría siete filas y reduciría la escena durante el arranque.
        ancho_referencia = self.width()
        if ancho_referencia < 640:
            ancho_referencia = max(1100, self.window().width())
        escala = max(1.0, min(1.3, ancho_referencia/1366))
        self.marca.setStyleSheet(f"color:#e4c69d; font:700 {round(12*escala)}px '{FUENTE_UI}'; letter-spacing:1px;")
        self._ancho_tarjeta = 132
        for clave, nombre in self.CAMPOS:
            self.etiquetas[clave].setStyleSheet(f"color:#c7d7db; font:{round(12*escala)}px '{FUENTE_UI}'; background:transparent;")
            self.valores[clave].setStyleSheet(f"color:#fff4dc; font:700 {round(21*escala)}px '{FUENTE_UI}'; background:transparent;")
            tam = round(25*escala)
            id_icono = "bienestar" if clave == "bienestar_digital" else clave
            self.iconos[clave].setPixmap(icono_arte(id_icono).pixmap(QSize(tam, tam)))
            self.iconos[clave].setFixedWidth(tam)
            self._ancho_tarjeta = max(self._ancho_tarjeta, self.etiquetas[clave].sizeHint().width()+tam+28)
        disponible = max(1, ancho_referencia - 108)
        caben = max(1, min(len(self.CAMPOS), (disponible + 8) // (self._ancho_tarjeta + 8)))
        filas = math.ceil(len(self.CAMPOS) / caben)
        columnas = math.ceil(len(self.CAMPOS) / filas)
        if columnas != self._columnas:
            for tarjeta in self.tarjetas.values():
                self.rejilla.removeWidget(tarjeta)
            for columna in range(self._columnas):
                self.rejilla.setColumnStretch(columna, 0)
            for indice, tarjeta in enumerate(self.tarjetas.values()):
                self.rejilla.addWidget(tarjeta, indice // columnas, indice % columnas)
            for columna in range(columnas):
                self.rejilla.setColumnStretch(columna, 1)
            self._columnas = columnas
        self.setMinimumHeight(filas * round(54*escala) + (filas - 1) * 6 + 12)
        self.updateGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._distribuir()

    def actualizar(self, juego):
        modo = getattr(self.window(), "modo_daltonismo", "normal")
        colores = paleta(modo)
        for clave, nombre in self.CAMPOS:
            valor = getattr(juego.estado, clave)
            self.valores[clave].setText(str(valor))
            self.valores[clave].setAccessibleName(f"{nombre}: {valor}")
            self.tarjetas[clave].setAccessibleName(f"{nombre}: {valor}")
            if modo != self._modo:
                # El nombre y la cifra siempre expresan el significado del color.
                color = colores["falsa" if clave in ("desinformacion", "conflictos") else "verdadera"]
                self.tarjetas[clave].setStyleSheet(
                    f"QFrame#indicadorCiudad {{background:rgba(255,255,255,12);"
                    f"border:0; border-left:3px solid {color}; border-radius:7px;}}")
        self._modo = modo
