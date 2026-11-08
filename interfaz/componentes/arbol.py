"""interfaz.componentes.arbol: presentación separada de las reglas del juego."""
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QFont, QPainter, QPen, QBrush, QColor
from PyQt6.QtCore import Qt, QRect, QPoint
from interfaz.componentes.arte import pixmap_arte, FUENTE_UI
from interfaz.componentes.accesibilidad import paleta


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
