"""Consulta opcional del archivo y las conexiones reales de la partida."""
from PyQt6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QLabel,QStackedWidget
from interfaz.componentes.arte import PanelIlustrado
from interfaz.componentes.arbol import VisualizadorBSTBonito
from interfaz.componentes.grafo import VisualizadorGrafo
from interfaz.novela.componentes import BotonNovela,decorar_novela


class ObservatorioNovela(QDialog):
    def __init__(self,juego,vista,seccion="archivo",parent=None):
        super().__init__(parent)
        self.setWindowTitle("El cuaderno de Ciudad Nova")
        self.resize(1050,660)
        self.setStyleSheet("QDialog{background:#102632;} QLabel{color:#f6e4c4;background:transparent;font:17px 'Atkinson Hyperlegible';}")
        self.juego=juego
        exterior=QVBoxLayout(self)
        panel=PanelIlustrado(self)
        exterior.addWidget(panel)
        layout=QVBoxLayout(panel)
        layout.setContentsMargins(40,38,40,36)
        menu=QHBoxLayout()
        self.pagina=QStackedWidget()
        for texto,indice in (("Archivo de publicaciones",0),("Conexiones de la ciudad",1)):
            b=BotonNovela(texto)
            b.clicked.connect(lambda _,i=indice:self.pagina.setCurrentIndex(i))
            menu.addWidget(b)
        layout.addLayout(menu)
        archivo=QStackedWidget()
        arbol=VisualizadorBSTBonito(juego.arbol)
        red=VisualizadorGrafo(juego.grafo)
        self.pagina.addWidget(arbol)
        self.pagina.addWidget(red)
        layout.addWidget(self.pagina,1)
        self.detalle=QLabel()
        self.detalle.setWordWrap(True)
        self.detalle.setText("Archivo activo: "+", ".join("#"+str(p.id) for p in juego.arbol.inorden()))
        layout.addWidget(self.detalle)
        red.nodo_seleccionado.connect(lambda id:self.detalle.setText(
            juego.grafo.nodos[id].nombre+" → "+
            ", ".join(juego.grafo.nodos[n].nombre for n in juego.grafo.vecinos(id))))
        def pagina(indice):
            if indice==0:
                self.detalle.setText("Archivo activo: "+", ".join("#"+str(p.id) for p in juego.arbol.inorden()))
            else:
                alcance=vista.get("red",{}).get("alcance",{})
                self.detalle.setText("Audiencia prevista: "+str(alcance.get("alcance",0))+" personas. Selecciona un retrato para seguir sus conexiones.")
        self.pagina.currentChanged.connect(pagina)
        self.pagina.setCurrentIndex(1 if seccion=="red" else 0)
        salir=BotonNovela("Volver a la escena")
        salir.clicked.connect(self.accept)
        layout.addWidget(salir)
        decorar_novela(self)
