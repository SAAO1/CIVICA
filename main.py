import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextBrowser
from PyQt6.QtCore import Qt

class AlcaldeDigitalApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Alcalde Digital - Ciudad Nova")
        self.setGeometry(100, 100, 800, 600) 
        
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        
        layout_principal = QVBoxLayout()
        widget_central.setLayout(layout_principal)
        
        self.crear_panel_indicadores(layout_principal)
        self.crear_panel_escenario(layout_principal)
        self.crear_panel_publicacion(layout_principal)
        self.crear_panel_botones(layout_principal)

    def crear_panel_indicadores(self, layout_principal):
        self.label_indicadores = QLabel("Información: 50 | Confianza: 50 | Desinformación: 10")
        self.label_indicadores.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_indicadores.setStyleSheet("font-size: 14px; font-weight: bold; color: blue;")
        layout_principal.addWidget(self.label_indicadores)

    def crear_panel_escenario(self, layout_principal):
        self.label_escenario = QLabel("Aquí irá la imagen de fondo y el personaje (Ej. Lucía)")
        self.label_escenario.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_escenario.setStyleSheet("background-color: lightgray; font-size: 18px;")
        self.label_escenario.setMinimumHeight(300) 
        layout_principal.addWidget(self.label_escenario)

    def crear_panel_publicacion(self, layout_principal):
        self.caja_texto = QTextBrowser()
        self.caja_texto.setText("CIVITAS\n\n@UsuarioNova ha publicado:\n«URGENTE: El Colegio Central será cerrado después de las elecciones.»")
        self.caja_texto.setStyleSheet("font-size: 16px; background-color: white;")
        self.caja_texto.setMaximumHeight(150)
        layout_principal.addWidget(self.caja_texto)

    def crear_panel_botones(self, layout_principal):
        layout_botones = QHBoxLayout()
        
        btn_compartir = QPushButton("COMPARTIR")
        btn_verificar = QPushButton("VERIFICAR")
        btn_ignorar = QPushButton("IGNORAR")
        btn_reportar = QPushButton("REPORTAR")
        
        btn_compartir.setMinimumHeight(40)
        btn_verificar.setMinimumHeight(40)
        btn_ignorar.setMinimumHeight(40)
        btn_reportar.setMinimumHeight(40)
        
        # Conectar el botón de verificar a una acción de prueba
        btn_verificar.clicked.connect(self.accion_verificar)
        
        # Añadirlos al layout horizontal
        layout_botones.addWidget(btn_compartir)
        layout_botones.addWidget(btn_verificar)
        layout_botones.addWidget(btn_ignorar)
        layout_botones.addWidget(btn_reportar)
        
        layout_principal.addLayout(layout_botones)
        
    def accion_verificar(self):
        self.caja_texto.append("\n\n[SISTEMA]: Has verificado la publicación. Es FALSA.")
        self.label_indicadores.setText("Información: 55 | Confianza: 53 | Desinformación: 7")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = AlcaldeDigitalApp()
    ventana.show()
    sys.exit(app.exec())