"""Fuentes sobre el mapa: zonas doradas, coste visible y foco por teclado."""
import math
from PyQt6.QtCore import Qt,QRectF,QTimer,QEvent,pyqtSignal
from PyQt6.QtGui import QPainter,QColor,QPen
from PyQt6.QtWidgets import QWidget
from infraestructura.recursos import pixmap_recurso
from interfaz.novela.componentes import BotonNovela


class MapaNovela(QWidget):
    seleccionado=pyqtSignal(str)
    pista=pyqtSignal(str)
    _POSICIONES={"archivo":(.24,.27),"barrio":(.48,.75),"redaccion":(.78,.28)}

    def __init__(self,parent=None):
        super().__init__(parent)
        self.setMinimumHeight(220)
        self.setMaximumHeight(280)
        self.setAccessibleName("Mapa: elige una fuente; cada visita usa una investigación")
        self.imagen=pixmap_recurso("assets/novela/cg/mapa.png")
        if self.imagen.isNull():
            self.imagen=pixmap_recurso("assets/feria/mapa_ciudad.png")
        self.botones={}
        self._descripciones={}
        self._pulso=0
        self.reloj=QTimer(self)
        self.reloj.setInterval(90)
        self.reloj.timeout.connect(self._animar)
        for id,nombre in (("archivo","Archivo"),("barrio","Vecindario"),("redaccion","Redacción")):
            boton=BotonNovela(nombre+" · 1",self)
            boton.setMinimumHeight(44)
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.setAccessibleName("Visitar "+nombre+": usa una investigación")
            boton.installEventFilter(self)
            boton.clicked.connect(lambda _,lugar=id:self.seleccionado.emit(lugar))
            self.botones[id]=boton

    def actualiza(self,lugares):
        for lugar in lugares:
            id=lugar.get("id")
            boton=self.botones.get(id)
            if boton:
                disponible=bool(lugar.get("disponible"))
                boton.setEnabled(disponible)
                descripcion=lugar.get("descripcion","")
                self._descripciones[id]=descripcion
                boton.setToolTip(descripcion+(" Usa 1 investigación." if disponible else " No disponible ahora."))
                boton.setAccessibleDescription(boton.toolTip())
        self.update()

    def eventFilter(self,obj,event):
        if event.type() in (QEvent.Type.Enter,QEvent.Type.FocusIn):
            id=next((id for id,b in self.botones.items() if b is obj),None)
            if id:
                self.pista.emit(self._descripciones.get(id,"")+" La visita usa 1 investigación.")
        return False

    def _animar(self):
        if getattr(self.window(),"reducir_movimiento",False):
            return
        self._pulso=(self._pulso+1)%50
        self.update()

    def showEvent(self,event):
        self.reloj.start()
        super().showEvent(event)

    def hideEvent(self,event):
        self.reloj.stop()
        super().hideEvent(event)

    def _zona(self):
        return QRectF(self.rect()).adjusted(4,4,-4,-4)

    def resizeEvent(self,event):
        zona=self._zona()
        for id,boton in self.botones.items():
            x,y=self._POSICIONES[id]
            ancho=min(190,max(138,int(zona.width()*.29)))
            boton.setGeometry(int(zona.x()+zona.width()*x-ancho/2),
                               int(zona.y()+zona.height()*y-22),ancho,46)
        super().resizeEvent(event)

    def paintEvent(self,event):
        p=QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        zona=self._zona()
        if not self.imagen.isNull():
            escala=max(zona.width()/self.imagen.width(),zona.height()/self.imagen.height())
            ancho,alto=zona.width()/escala,zona.height()/escala
            fuente=QRectF((self.imagen.width()-ancho)/2,(self.imagen.height()-alto)/2,ancho,alto)
            p.drawPixmap(zona,self.imagen,fuente)
            p.fillRect(zona,QColor(18,30,51,24))
        else:
            p.fillRect(zona,QColor("#17243d"))
        p.setPen(QPen(QColor("#b99249"),2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(zona,7,7)
        pulso=(1+math.sin(self._pulso*math.tau/50))/2
        for boton in self.botones.values():
            if boton.isEnabled():
                caja=QRectF(boton.geometry()).adjusted(-3-pulso*3,-3-pulso*3,3+pulso*3,3+pulso*3)
                p.setPen(QPen(QColor(232,192,104,int(70+80*pulso)),2))
                p.drawRoundedRect(caja,12,12)
        p.end()
