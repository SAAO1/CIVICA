from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import (
    QPainter,
    QPen,
    QBrush,
    QColor,
    QFont,
)
from PyQt6.QtCore import Qt


class VisualizadorBST(QWidget):

    def __init__(self, arbol, parent=None):
        super().__init__(parent)

        self.arbol = arbol

        self.setMinimumHeight(240)

        self.setStyleSheet(
            """
            background-color: #0B1424;
            border: 2px solid #536A9A;
            border-radius: 15px;
            """
        )

    def actualizar(self):
        self.update()



    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

       
        painter.fillRect(
            self.rect(),
            QColor("#0B1424")
        )

      

        if self.arbol.raiz is None:

            painter.setPen(
                QColor("#FFFFFF")
            )

            painter.setFont(
                QFont(
                    "Arial",
                    18
                )
            )

            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "ÁRBOL VACÍO"
            )

            return

       

        nodos = []

        self._obtener_nodos(
            self.arbol.raiz,
            0,
            nodos
        )

       

        posiciones = {}

        cantidad = len(nodos)

        ancho = self.width()

       
        if cantidad <= 1:
            separacion = ancho
        else:
            separacion = ancho / cantidad

        for indice, (nodo, nivel) in enumerate(nodos):

            x = (
                separacion * indice
                + separacion / 2
            )

            y = (
                55
                + nivel * 75
            )

            posiciones[id(nodo)] = (
                int(x),
                int(y)
            )

       
        # --------------------------------------------------

        pen_linea = QPen(
            QColor("#88A9E8"),
            2
        )

        painter.setPen(
            pen_linea
        )

        for nodo, nivel in nodos:

            x1, y1 = posiciones[
                id(nodo)
            ]

            # Hijo izquierdo
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

       

        radio = 30

        for nodo, nivel in nodos:

            x, y = posiciones[
                id(nodo)
            ]


            estado = (
                nodo.publicacion.estado
            )

            if estado == "FALSA VERIFICADA":

                color = QColor(
                    "#C94C4C"
                )

            elif estado == "VERIFICADA":

                color = QColor(
                    "#39A96B"
                )

            elif estado == "COMPARTIDA":

                color = QColor(
                    "#C58B2C"
                )

            elif estado == "IGNORADA":

                color = QColor(
                    "#61708E"
                )

            else:

                color = QColor(
                    "#15979B"
                )

           

            painter.setBrush(
                QBrush(color)
            )

            painter.setPen(
                QPen(
                    QColor("#FFFFFF"),
                    2
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
                y - 8,
                radio * 2,
                20,
                Qt.AlignmentFlag.AlignCenter,
                f"#{nodo.publicacion.id}"
            )

           
            painter.setFont(
                QFont(
                    "Arial",
                    9
                )
            )

            painter.drawText(
                x - 60,
                y + radio + 3,
                120,
                18,
                Qt.AlignmentFlag.AlignCenter,
                f"Impacto: {nodo.publicacion.impacto}"
            )

  

    def _obtener_nodos(
        self,
        nodo,
        nivel,
        lista
    ):

        if nodo is None:
            return

        self._obtener_nodos(
            nodo.izquierda,
            nivel + 1,
            lista
        )

        lista.append(
            (
                nodo,
                nivel
            )
        )

        self._obtener_nodos(
            nodo.derecha,
            nivel + 1,
            lista
        )