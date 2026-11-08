"""Planos breves de investigación sobre la escena de la novela."""
from pathlib import Path
from PyQt6.QtCore import Qt,QTimer,QUrl,QEvent,pyqtSignal
from PyQt6.QtGui import QPixmap,QPainter,QColor,QImage
from PyQt6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QStackedWidget
from PyQt6.QtMultimedia import QMediaPlayer,QAudioOutput,QVideoSink
from infraestructura.recursos import ruta_recurso
from interfaz.novela.componentes import BotonNovela


class LienzoVideo(QWidget):
    """Pinta los cuadros en Qt para conservar capas, capturas y compatibilidad."""
    def __init__(self,parent=None):
        super().__init__(parent)
        self._imagen=QImage()
        self._sink=QVideoSink(self)
        self._sink.videoFrameChanged.connect(self._fotograma)

    def videoSink(self):
        return self._sink

    def setAspectRatioMode(self,modo):
        self._aspecto=modo

    def _fotograma(self,frame):
        if frame.isValid():
            imagen=frame.toImage()
            if not imagen.isNull():
                self._imagen=imagen
                self.update()

    def paintEvent(self,event):
        p=QPainter(self)
        p.fillRect(self.rect(),QColor("#050d14"))
        if not self._imagen.isNull():
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            tam=self._imagen.size().scaled(self.size(),Qt.AspectRatioMode.KeepAspectRatio)
            x=(self.width()-tam.width())//2
            y=(self.height()-tam.height())//2
            p.drawImage(x,y,self._imagen.scaled(tam,Qt.AspectRatioMode.KeepAspectRatio,
                                               Qt.TransformationMode.SmoothTransformation))


class PlanoInvestigacion(QWidget):
    terminado=pyqtSignal()
    def __init__(self,numero,parent=None):
        super().__init__(parent)
        self.numero=max(1,min(6,int(numero)))
        self._terminado=False
        self.setObjectName("planoInvestigacion")
        self.setStyleSheet("QWidget#planoInvestigacion{background:#050d14;} QLabel{color:#f7e4c5;background:transparent;font:18px 'Atkinson Hyperlegible';}")
        layout=QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,12)
        self.capas=QStackedWidget()
        layout.addWidget(self.capas,1)
        self.video=LienzoVideo()
        self.video.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.imagen=QLabel()
        self.imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.capas.addWidget(self.video)
        self.capas.addWidget(self.imagen)
        pie=QHBoxLayout()
        pie.setContentsMargins(22,3,22,3)
        pie.addWidget(QLabel("Busca una fuente, descubre un detalle y decide con esa prueba."),1)
        self.boton=BotonNovela("Investigar ahora")
        self.boton.clicked.connect(self.finalizar)
        pie.addWidget(self.boton)
        layout.addLayout(pie)
        self.player=QMediaPlayer(self)
        self.audio=QAudioOutput(self)
        self.audio.setMuted(True)
        self.player.setAudioOutput(self.audio)
        self.player.setVideoSink(self.video.videoSink())
        self.player.mediaStatusChanged.connect(self._estado)
        self.player.errorOccurred.connect(lambda *_:self._respaldo())
        self.seguro=QTimer(self)
        self.seguro.setSingleShot(True)
        self.seguro.timeout.connect(self.finalizar)
        if parent:
            parent.installEventFilter(self)
            self.setGeometry(parent.rect())

    def paintEvent(self,event):
        p=QPainter(self)
        p.fillRect(self.rect(),QColor("#050d14"))

    def abrir(self):
        self.show()
        self.raise_()
        self.boton.setFocus()
        identificador=(50,90,110,40,120,35)[self.numero-1]
        ruta=Path(ruta_recurso(f"assets/novela/pulido/videos/caso_{identificador}.mp4"))
        if not ruta.is_file():
            ruta=Path(ruta_recurso(f"assets/novela/videos/acto_{self.numero}.mp4"))
        self.seguro.start(6800)
        if ruta.is_file():
            self.player.setSource(QUrl.fromLocalFile(str(ruta)))
            self.player.play()
        else:
            self._respaldo()

    def _respaldo(self):
        if self._terminado:
            return
        nombre=("aviso_cafe","parque_contexto","audio_contexto","correccion_contexto","urnas_contexto","voto_contexto")[self.numero-1]
        pix=QPixmap(ruta_recurso(f"assets/novela/pulido/cg/{nombre}.png"))
        if pix.isNull():
            anterior=("archivo","parque","redaccion","redaccion","urnas","urnas")[self.numero-1]
            pix=QPixmap(ruta_recurso(f"assets/novela/cg/{anterior}.png"))
        self.imagen.setPixmap(pix.scaled(self.capas.size(),Qt.AspectRatioMode.KeepAspectRatio,
                                         Qt.TransformationMode.SmoothTransformation))
        self.capas.setCurrentWidget(self.imagen)
        self.seguro.start(1500)

    def _estado(self,estado):
        if estado==QMediaPlayer.MediaStatus.EndOfMedia:
            self.finalizar()

    def eventFilter(self,obj,event):
        if obj is self.parentWidget() and event.type()==QEvent.Type.Resize:
            self.setGeometry(obj.rect())
        return super().eventFilter(obj,event)

    def keyPressEvent(self,event):
        if event.key() in (Qt.Key.Key_Escape,Qt.Key.Key_Space,Qt.Key.Key_Return):
            self.finalizar()
        else:
            super().keyPressEvent(event)

    def cancelar(self):
        self._terminado=True
        self.seguro.stop()
        self.player.stop()
        self.player.setSource(QUrl())
        if self.parentWidget():
            self.parentWidget().removeEventFilter(self)
        self.hide()
        self.deleteLater()

    def finalizar(self):
        if self._terminado:
            return
        self.cancelar()
        self.terminado.emit()
