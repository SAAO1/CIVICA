import sys

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from models.publicacion import Publicacion
from estructuras.bst import ArbolPublicaciones




class AlcaldeDigitalApp(QMainWindow):

    def __init__(self):
        super().__init__()

     

        self.setWindowTitle("Alcalde Digital")

        
        self.setMinimumSize(1280, 720)
        self.showMaximized()

       
        self.estado_juego = "dialogo"

      

        self.arbol = ArbolPublicaciones()

        self.publicaciones = [

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

        # Insertamos las publicaciones en el BST.
        for publicacion in self.publicaciones:
            self.arbol.insertar(publicacion)


        self.indice_publicacion = 0

        self.publicacion_actual = (
            self.publicaciones[
                self.indice_publicacion
            ]
        )


        self.confianza = 50
        self.desinformacion = 20
        self.informacion_verificada = 50
        self.convivencia = 50

        self.dialogos = [

            [
                (
                    "Laura",
                    "Espera un momento, Daniel. Estoy revisando "
                    "una publicación de Civitas que me parece sospechosa."
                ),
                (
                    "Daniel",
                    "¿La del Colegio Central? Ya la vi. "
                    "Tiene cientos de compartidos."
                ),
            ],

            [
                (
                    "Laura",
                    "La cantidad de compartidos no demuestra "
                    "que una publicación sea verdadera."
                ),
                (
                    "Daniel",
                    "Entonces tenemos que decidir qué hacer "
                    "antes de que siga circulando."
                ),
            ],

            [
                (
                    "Laura",
                    "Esta publicación necesita ser revisada "
                    "antes de sacar conclusiones."
                ),
                (
                    "Daniel",
                    "Entiendo. Revisemos la información primero."
                ),
            ],

            [
                (
                    "Daniel",
                    "Cada vez aparecen más publicaciones sobre "
                    "la campaña."
                ),
                (
                    "Laura",
                    "Y cada una puede cambiar la forma en que "
                    "los ciudadanos perciben la información."
                ),
            ],

            [
                (
                    "Laura",
                    "Este rumor está empezando a crecer rápidamente."
                ),
                (
                    "Daniel",
                    "Entonces debemos actuar antes de que llegue "
                    "a más personas."
                ),
            ],

            [
                (
                    "Daniel",
                    "Esta encuesta está circulando por toda Civitas."
                ),
                (
                    "Laura",
                    "Primero tenemos que saber de dónde salió."
                ),
            ],
        ]

        self.indice_dialogo = 0

        self.crear_interfaz()

        self.mostrar_dialogo()

    def crear_interfaz(self):


        contenedor = QWidget()

        self.setCentralWidget(
            contenedor
        )

        self.layout_principal = QVBoxLayout()

        self.layout_principal.setContentsMargins(
            0,
            0,
            0,
            0
        )

        self.layout_principal.setSpacing(
            0
        )

        contenedor.setLayout(
            self.layout_principal
        )


        self.panel_escena = QFrame()

        self.panel_escena.setStyleSheet(
            """
            QFrame {
                background-color: #18243A;
            }
            """
        )

        self.layout_escena = QVBoxLayout()

        self.layout_escena.setContentsMargins(
            40,
            25,
            40,
            25
        )

        self.panel_escena.setLayout(
            self.layout_escena
        )

        self.layout_principal.addWidget(
            self.panel_escena,
            stretch=1
        )


        self.titulo = QLabel(
            "ALCALDE DIGITAL"
        )

        self.titulo.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.titulo.setStyleSheet(
            """
            color: white;
            font-size: 36px;
            font-weight: bold;
            """
        )

        self.layout_escena.addWidget(
            self.titulo
        )


        self.civitas = QLabel(
            "CIVITAS"
        )

        self.civitas.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.civitas.setStyleSheet(
            """
            color: #8EA8FF;
            font-size: 24px;
            font-weight: bold;
            """
        )

        self.layout_escena.addWidget(
            self.civitas
        )


        self.personajes = QLabel(
            " DANIEL                                                                                          LAURA"
        )

        self.personajes.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.personajes.setStyleSheet(
            """
            color: white;
            font-size: 40px;
            padding: 30px;
            """
        )

        self.layout_escena.addWidget(
            self.personajes,
            stretch=1
        )

        self.publicacion_label = QLabel()

        self.publicacion_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.publicacion_label.setWordWrap(
            True
        )

        self.publicacion_label.setStyleSheet(
            """
            color: white;
            background-color: rgba(10, 20, 40, 180);
            border: 2px solid #6179B6;
            border-radius: 18px;
            padding: 20px;
            font-size: 24px;
            """
        )

        self.layout_escena.addWidget(
            self.publicacion_label
        )

        self.panel_inferior = QFrame()

        self.panel_inferior.setMinimumHeight(
            300
        )

        self.panel_inferior.setMaximumHeight(
            360
        )

        self.panel_inferior.setStyleSheet(
            """
            QFrame {
                background-color: #0D1628;
                border-top: 2px solid #536A9A;
            }
            """
        )

        self.layout_inferior = QVBoxLayout()

        self.layout_inferior.setContentsMargins(
            35,
            15,
            35,
            15
        )

        self.layout_inferior.setSpacing(
            8
        )

        self.panel_inferior.setLayout(
            self.layout_inferior
        )

        self.layout_principal.addWidget(
            self.panel_inferior
        )


        self.panel_dialogo = QWidget()

        self.layout_dialogo = QVBoxLayout()

        self.layout_dialogo.setContentsMargins(
            0,
            0,
            0,
            0
        )

        self.panel_dialogo.setLayout(
            self.layout_dialogo
        )

        self.layout_inferior.addWidget(
            self.panel_dialogo
        )


        self.nombre_personaje = QLabel()

        self.nombre_personaje.setStyleSheet(
            """
            color: #8EA8FF;
            font-size: 23px;
            font-weight: bold;
            """
        )

        self.layout_dialogo.addWidget(
            self.nombre_personaje
        )

        self.texto_dialogo = QLabel()

        self.texto_dialogo.setWordWrap(
            True
        )

        self.texto_dialogo.setMaximumHeight(
            75
        )

        self.texto_dialogo.setStyleSheet(
            """
            color: white;
            font-size: 22px;
            padding-top: 5px;
            """
        )

        self.layout_dialogo.addWidget(
            self.texto_dialogo
        )


        self.indicacion = QLabel(
            "CLICK o ESPACIO para continuar"
        )

        self.indicacion.setAlignment(
            Qt.AlignmentFlag.AlignRight
        )

        self.indicacion.setStyleSheet(
            """
            color: #AAB6D1;
            font-size: 16px;
            """
        )

        self.layout_dialogo.addWidget(
            self.indicacion
        )


        self.panel_opciones = QWidget()

        self.layout_opciones = QHBoxLayout()

        self.layout_opciones.setContentsMargins(
            0,
            0,
            0,
            0
        )

        self.layout_opciones.setSpacing(
            15
        )

        self.panel_opciones.setLayout(
            self.layout_opciones
        )

        self.layout_inferior.addWidget(
            self.panel_opciones
        )


        self.panel_resultado = QWidget()

        self.layout_resultado = QVBoxLayout()

        self.layout_resultado.setContentsMargins(
            0,
            0,
            0,
            0
        )

        self.layout_resultado.setSpacing(
            5
        )

        self.panel_resultado.setLayout(
            self.layout_resultado
        )

        self.layout_inferior.addWidget(
            self.panel_resultado
        )


        self.boton_continuar = QPushButton(
            "CONTINUAR"
        )

        self.boton_continuar.setFixedHeight(
            50
        )

        self.boton_continuar.setStyleSheet(
            """
            QPushButton {
                background-color: #5865F2;
                color: white;
                border: none;
                border-radius: 15px;
                font-size: 20px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #7280FF;
            }
            """
        )

        self.boton_continuar.clicked.connect(
            self.continuar
        )

        self.layout_inferior.addWidget(
            self.boton_continuar
        )


        self.panel_opciones.hide()
        self.panel_resultado.hide()
        self.boton_continuar.hide()

    def actualizar_publicacion_visual(
        self
    ):

        publicacion = (
            self.publicacion_actual
        )

        self.publicacion_label.setText(
            f"""
<b>PUBLICACIÓN #{publicacion.id}</b>

"{publicacion.texto}"

Impacto: {publicacion.impacto}
Compartidos: {publicacion.compartidos}
Verificaciones: {publicacion.verificaciones}
Reportes: {publicacion.reportes}
Estado: {publicacion.estado}
"""
        )



    def mostrar_dialogo(self):

        self.estado_juego = "dialogo"

        self.panel_dialogo.show()
        self.panel_opciones.hide()
        self.panel_resultado.hide()
        self.boton_continuar.hide()

        self.actualizar_publicacion_visual()

        escena = self.dialogos[
            self.indice_publicacion
        ]

        personaje, texto = escena[
            self.indice_dialogo
        ]

        self.nombre_personaje.setText(
            personaje
        )

        self.texto_dialogo.setText(
            texto
        )

        self.indicacion.setText(
            "CLICK o ESPACIO para continuar"
        )

    def mostrar_opciones(self):

        self.estado_juego = "opciones"

        self.panel_dialogo.hide()
        self.panel_resultado.hide()
        self.boton_continuar.hide()

        self.panel_opciones.show()

        self.borrar_botones()

        opciones = [

            (
                "COMPARTIR",
                self.accion_compartir
            ),

            (
                "VERIFICAR",
                self.accion_verificar
            ),

            (
                "IGNORAR",
                self.accion_ignorar
            ),

            (
                "REPORTAR",
                self.accion_reportar
            ),
        ]

        for texto, funcion in opciones:

            boton = QPushButton(
                texto
            )

            boton.setFixedHeight(
                55
            )

            boton.setStyleSheet(
                """
                QPushButton {
                    background-color: #25385D;
                    color: white;
                    border: 2px solid #657FB8;
                    border-radius: 14px;
                    font-size: 18px;
                    font-weight: bold;
                }

                QPushButton:hover {
                    background-color: #3E5A91;
                }

                QPushButton:pressed {
                    background-color: #5865F2;
                }
                """
            )

            boton.clicked.connect(
                funcion
            )

            self.layout_opciones.addWidget(
                boton
            )


    def borrar_botones(self):

        while self.layout_opciones.count():

            item = (
                self.layout_opciones.takeAt(
                    0
                )
            )

            widget = item.widget()

            if widget is not None:

                widget.deleteLater()


    def guardar_estado(
        self,
        publicacion
    ):

        return {

            "impacto":
                publicacion.impacto,

            "compartidos":
                publicacion.compartidos,

            "verificaciones":
                publicacion.verificaciones,

            "reportes":
                publicacion.reportes,

            "estado":
                publicacion.estado
        }

    def mostrar_resultado(
        self,
        accion,
        antes
    ):

        self.estado_juego = "resultado"

        self.panel_dialogo.hide()
        self.panel_opciones.hide()

        self.panel_resultado.show()
        self.boton_continuar.show()

        self.limpiar_resultado()

      

        despues = self.arbol.buscar(
            self.publicacion_actual.id
        )

        if despues is None:

            texto_despues = (
                "La publicación fue eliminada "
                "del Árbol Binario de Búsqueda."
            )

        else:

            texto_despues = (
                f"Impacto: {despues.impacto}\n"
                f"Compartidos: {despues.compartidos}\n"
                f"Verificaciones: "
                f"{despues.verificaciones}\n"
                f"Reportes: {despues.reportes}\n"
                f"Estado: {despues.estado}"
            )

        resultado = QLabel()

        resultado.setWordWrap(
            True
        )

        resultado.setStyleSheet(
            """
            color: white;
            font-size: 15px;
            """
        )

        resultado.setText(
            f"""
<b>ACCIÓN REALIZADA: {accion}</b>

PUBLICACIÓN #{self.publicacion_actual.id}

ANTES
Impacto: {antes["impacto"]} |
Compartidos: {antes["compartidos"]} |
Verificaciones: {antes["verificaciones"]} |
Reportes: {antes["reportes"]} |
Estado: {antes["estado"]}

DESPUÉS
{texto_despues}
"""
        )

        self.layout_resultado.addWidget(
            resultado
        )


        titulo_bst = QLabel(
            "ÁRBOL BINARIO DE BÚSQUEDA — ESTADO ACTUAL"
        )

        titulo_bst.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        titulo_bst.setStyleSheet(
            """
            color: #8EA8FF;
            font-size: 17px;
            font-weight: bold;
            """
        )

        self.layout_resultado.addWidget(
            titulo_bst
        )

        arbol = QLabel(
            self.generar_arbol_texto()
        )

        arbol.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        arbol.setStyleSheet(
            """
            color: white;
            background-color: #111B2E;
            border: 2px solid #536A9A;
            border-radius: 12px;
            padding: 8px;
            font-family: Consolas;
            font-size: 14px;
            """
        )

        self.layout_resultado.addWidget(
            arbol
        )


    def generar_arbol_texto(self):

        if self.arbol.raiz is None:

            return "ÁRBOL VACÍO"

        resultado = []

        self._generar_arbol(
            self.arbol.raiz,
            "",
            "",
            resultado
        )

        return "\n".join(
            resultado
        )

    def _generar_arbol(
        self,
        nodo,
        prefijo,
        rama,
        resultado
    ):

        if nodo is None:
            return

        resultado.append(
            f"{prefijo}{rama}"
            f"[#{nodo.publicacion.id}] "
            f"Impacto={nodo.publicacion.impacto} "
            f"Estado={nodo.publicacion.estado}"
        )

        if nodo.izquierda is not None:

            self._generar_arbol(
                nodo.izquierda,
                prefijo + "    ",
                "├── IZQ ",
                resultado
            )

        if nodo.derecha is not None:

            self._generar_arbol(
                nodo.derecha,
                prefijo + "    ",
                "└── DER ",
                resultado
            )


    def accion_compartir(self):

        publicacion = self.arbol.buscar(
            self.publicacion_actual.id
        )

        if publicacion is None:
            return

        antes = self.guardar_estado(
            publicacion
        )

        publicacion.compartidos += 1
        publicacion.impacto += 1

        publicacion.estado = (
            "COMPARTIDA"
        )

        self.desinformacion += 2

        self.mostrar_resultado(
            "COMPARTIR",
            antes
        )


    def accion_verificar(self):

        publicacion = self.arbol.buscar(
            self.publicacion_actual.id
        )

        if publicacion is None:
            return

        antes = self.guardar_estado(
            publicacion
        )

        publicacion.verificaciones += 1

        self.informacion_verificada += 5
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

        self.mostrar_resultado(
            "VERIFICAR",
            antes
        )


    def accion_ignorar(self):

        publicacion = self.arbol.buscar(
            self.publicacion_actual.id
        )

        if publicacion is None:
            return

        antes = self.guardar_estado(
            publicacion
        )

        publicacion.estado = (
            "IGNORADA"
        )

        self.mostrar_resultado(
            "IGNORAR",
            antes
        )


    def accion_reportar(self):

        publicacion = self.arbol.buscar(
            self.publicacion_actual.id
        )

        if publicacion is None:
            return

        antes = self.guardar_estado(
            publicacion
        )

        publicacion.reportes += 1

        self.confianza += 2

        self.desinformacion = max(
            0,
            self.desinformacion - 2
        )

        # Eliminamos la publicación
        # del BST.
        self.arbol.eliminar(
            publicacion.id
        )

        self.mostrar_resultado(
            "REPORTAR",
            antes
        )


    def continuar(self):

        if self.estado_juego != "resultado":
            return

        self.indice_publicacion += 1

        if (
            self.indice_publicacion
            >= len(self.publicaciones)
        ):

            self.indice_publicacion = 0

        self.indice_dialogo = 0

        self.publicacion_actual = (
            self.publicaciones[
                self.indice_publicacion
            ]
        )

        self.mostrar_dialogo()


    def limpiar_resultado(self):

        while self.layout_resultado.count():

            item = (
                self.layout_resultado.takeAt(
                    0
                )
            )

            widget = item.widget()

            if widget is not None:

                widget.deleteLater()


    def mousePressEvent(
        self,
        event
    ):

        if event.button() != (
            Qt.MouseButton.LeftButton
        ):
            return

        if self.estado_juego == "dialogo":

            escena = self.dialogos[
                self.indice_publicacion
            ]

            # Todavía quedan diálogos
            if (
                self.indice_dialogo
                < len(escena) - 1
            ):

                self.indice_dialogo += 1

                self.mostrar_dialogo()

            else:

                self.mostrar_opciones()

        elif self.estado_juego == "resultado":

            self.continuar()

    def keyPressEvent(
        self,
        event
    ):

        if event.key() != (
            Qt.Key.Key_Space
        ):
            return

        if self.estado_juego == "dialogo":

            escena = self.dialogos[
                self.indice_publicacion
            ]

            if (
                self.indice_dialogo
                < len(escena) - 1
            ):

                self.indice_dialogo += 1

                self.mostrar_dialogo()

            else:

                self.mostrar_opciones()

        elif self.estado_juego == "resultado":

            self.continuar()



if __name__ == "__main__":

    app = QApplication(
        sys.argv
    )

    ventana = AlcaldeDigitalApp()

    ventana.show()

    sys.exit(
        app.exec()
    )