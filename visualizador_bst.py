from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import (
    QPainter,
    QPen,
    QBrush,
    QColor,
    QFont
)
from PyQt6.QtCore import Qt


class VisualizadorBST(QWidget):

    def __init__(self, arbol, parent=None):
        super().__init__(parent)

        self.arbol = arbol

        self.setMinimumHeight(240)

    # ========================================================
    # ACTUALIZAR
    # ========================================================

    def actualizar(self):
        self.update()

    # ========================================================
    # OBTENER NODOS POR NIVEL
    # ========================================================

    def _obtener_nodos(
        self,
        nodo,
        nivel,
        posiciones_nivel,
        resultado
    ):

        if nodo is None:
            return

        while len(posiciones_nivel) <= nivel:
            posiciones_nivel.append([])

        posiciones_nivel[nivel].append(nodo)

        resultado.append(nodo)

        self._obtener_nodos(
            nodo.izquierda,
            nivel + 1,
            posiciones_nivel,
            resultado
        )

        self._obtener_nodos(
            nodo.derecha,
            nivel + 1,
            posiciones_nivel,
            resultado
        )

    # ========================================================
    # OBTENER PROFUNDIDAD
    # ========================================================

    def _obtener_profundidad(self, nodo):

        if nodo is None:
            return 0

        izquierda = self._obtener_profundidad(
            nodo.izquierda
        )

        derecha = self._obtener_profundidad(
            nodo.derecha
        )

        return max(
            izquierda,
            derecha
        ) + 1

    # ========================================================
    # INORDEN PARA POSICIONAR NODOS
    # ========================================================

    def _inorden_nodos(self, nodo, lista):

        if nodo is None:
            return

        self._inorden_nodos(
            nodo.izquierda,
            lista
        )

        lista.append(nodo)

        self._inorden_nodos(
            nodo.derecha,
            lista
        )

    # ========================================================
    # OBTENER NIVEL DE UN NODO
    # ========================================================

    def _niveles(
        self,
        nodo,
        nivel,
        mapa
    ):

        if nodo is None:
            return

        mapa[id(nodo)] = nivel

        self._niveles(
            nodo.izquierda,
            nivel + 1,
            mapa
        )

        self._niveles(
            nodo.derecha,
            nivel + 1,
            mapa
        )

    # ========================================================
    # PINTAR
    # ========================================================

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        # ----------------------------------------------------
        # FONDO
        # ----------------------------------------------------

        painter.fillRect(
            self.rect(),
            QColor("#101827")
        )

        # ----------------------------------------------------
        # ÁRBOL VACÍO
        # ----------------------------------------------------

        if self.arbol.raiz is None:

            painter.setPen(
                QColor("#AAB6D1")
            )

            painter.setFont(
                QFont(
                    "Arial",
                    17,
                    QFont.Weight.Bold
                )
            )

            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "ÁRBOL BINARIO DE BÚSQUEDA VACÍO"
            )

            painter.end()

            return

        # ----------------------------------------------------
        # NODOS
        # ----------------------------------------------------

        todos_los_nodos = []

        niveles = []

        self._obtener_nodos(
            self.arbol.raiz,
            0,
            niveles,
            todos_los_nodos
        )

        # ----------------------------------------------------
        # ORDEN INORDEN PARA POSICIÓN HORIZONTAL
        # ----------------------------------------------------

        lista_inorden = []

        self._inorden_nodos(
            self.arbol.raiz,
            lista_inorden
        )

        # ----------------------------------------------------
        # NIVEL DE CADA NODO
        # ----------------------------------------------------

        mapa_nivel = {}

        self._niveles(
            self.arbol.raiz,
            0,
            mapa_nivel
        )

        # ----------------------------------------------------
        # POSICIONES
        # ----------------------------------------------------

        posiciones = {}

        ancho = self.width()

        cantidad_nodos = len(
            lista_inorden
        )

        margen = 70

        if cantidad_nodos == 1:

            espacio_x = 0

        else:

            espacio_x = (
                ancho - (margen * 2)
            ) / (
                cantidad_nodos - 1
            )

        espacio_x = max(
            95,
            espacio_x
        )

        # Si hay muchos nodos,
        # calculamos un ancho virtual.
        ancho_virtual = max(
            ancho,
            int(
                margen * 2
                + espacio_x
                * (cantidad_nodos - 1)
            )
        )

        offset_x = max(
            0,
            int(
                (ancho_virtual - ancho) / 2
            )
        )

        altura_nivel = 78

        for indice, nodo in enumerate(
            lista_inorden
        ):

            x = (
                margen
                + indice * espacio_x
                - offset_x
            )

            nivel = mapa_nivel[
                id(nodo)
            ]

            y = (
                35
                + nivel * altura_nivel
            )

            posiciones[
                id(nodo)
            ] = (
                int(x),
                int(y)
            )

        # ----------------------------------------------------
        # CONEXIONES
        # ----------------------------------------------------

        painter.setPen(
            QPen(
                QColor("#60749A"),
                3
            )
        )

        for nodo in todos_los_nodos:

            x1, y1 = posiciones[
                id(nodo)
            ]

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

        # ----------------------------------------------------
        # NODOS
        # ----------------------------------------------------

        radio = 27

        for nodo in todos_los_nodos:

            x, y = posiciones[
                id(nodo)
            ]

            publicacion = (
                nodo.publicacion
            )

            estado = (
                publicacion.estado
            )

            # -----------------------------------------------
            # COLOR DEL NODO
            # -----------------------------------------------

            if estado == "FALSA VERIFICADA":

                color = QColor("#D9534F")

            elif estado == "VERIFICADA":

                color = QColor("#2FBF71")

            elif estado == "COMPARTIDA":

                color = QColor("#D69E2E")

            elif estado == "IGNORADA":

                color = QColor("#64748B")

            else:

                color = QColor("#178C96")

            # -----------------------------------------------
            # SOMBRA
            # -----------------------------------------------

            painter.setBrush(
                QBrush(
                    QColor("#080D17")
                )
            )

            painter.setPen(
                Qt.PenStyle.NoPen
            )

            painter.drawEllipse(
                x - radio + 3,
                y - radio + 4,
                radio * 2,
                radio * 2
            )

            # -----------------------------------------------
            # CÍRCULO PRINCIPAL
            # -----------------------------------------------

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

            # -----------------------------------------------
            # ID
            # -----------------------------------------------

            painter.setPen(
                QColor("#FFFFFF")
            )

            painter.setFont(
                QFont(
                    "Arial",
                    11,
                    QFont.Weight.Bold
                )
            )

            painter.drawText(
                x - radio,
                y - 10,
                radio * 2,
                20,
                Qt.AlignmentFlag.AlignCenter,
                f"#{publicacion.id}"
            )

            # -----------------------------------------------
            # IMPACTO
            # -----------------------------------------------

            painter.setFont(
                QFont(
                    "Arial",
                    8,
                    QFont.Weight.Bold
                )
            )

            painter.drawText(
                x - 50,
                y + radio + 2,
                100,
                16,
                Qt.AlignmentFlag.AlignCenter,
                f"Impacto: {publicacion.impacto}"
            )

        painter.end()