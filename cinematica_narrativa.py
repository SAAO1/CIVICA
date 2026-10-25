"""Video narrativo silencioso, con póster y ciclo de vida acotado a la escena.

La voz y la mezcla ambiental pertenecen al gestor de audio del juego. Esta
capa no dispone de salida de audio, así que nunca duplica la narración.
"""
from pathlib import Path

from PyQt6.QtCore import QEvent, QRect, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QImage, QPainter, QPixmap
from PyQt6.QtMultimedia import QMediaPlayer, QVideoFrame, QVideoSink
from PyQt6.QtWidgets import QWidget

from juego.cinematica import CINEMATICAS
from recursos import RAIZ


class _Poster(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.imagen = QPixmap()
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)

    def paintEvent(self, event):
        pintor = QPainter(self)
        pintor.fillRect(self.rect(), Qt.GlobalColor.black)
        if self.imagen.isNull():
            return
        pintor.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        imagen = self.imagen.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                   Qt.TransformationMode.SmoothTransformation)
        pintor.drawPixmap((self.width()-imagen.width())//2,
                          (self.height()-imagen.height())//2, imagen)


class _VideoCompuesto(QWidget):
    """Pinta los fotogramas en el mismo lienzo que subtítulos y partículas.

    QVideoWidget usa una superficie nativa que puede quedar fuera de la
    composición de QWidget. Un sink pintado conserva las capas de la novela,
    incluido su orden, y permite capturar exactamente la imagen presentada.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._imagen = QImage()
        self._sink = None
        self._canal = 0
        self.renovar_canal()

    def videoSink(self):
        return self._sink

    def invalidar_canal(self):
        """Los callbacks ya encolados de otro transporte dejan de ser válidos."""
        self._canal += 1
        if self._sink is not None:
            try:
                self._sink.videoFrameChanged.disconnect()
            except (TypeError, RuntimeError):
                pass

    def renovar_canal(self, receptor=None):
        # El reproductor debe haberse separado del sink anterior antes de
        # sustituirlo. Cada carga recibe su propio canal y su propio token.
        anterior = self._sink
        self.invalidar_canal()
        self._sink = QVideoSink(self)
        canal = self._canal
        recibir = receptor or self._recibir_frame

        def recibir_vigente(frame):
            if canal == self._canal:
                recibir(frame)

        self._sink.videoFrameChanged.connect(recibir_vigente)
        if anterior is not None:
            anterior.setVideoFrame(QVideoFrame())
            anterior.deleteLater()

    def _recibir_frame(self, frame):
        # EndOfMedia puede entregar un frame vacío. Conservamos el último
        # plano hasta que detener/liberar lo borre expresamente.
        if not frame.isValid():
            return
        imagen = frame.toImage()
        if imagen.isNull():
            return
        # Una copia conserva el mismo plano al liberar el decodificador.
        self._imagen = imagen.copy()
        self.update()

    def paintEvent(self, event):
        if self._imagen.isNull():
            return
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        escala = max(self.width()/self._imagen.width(), self.height()/self._imagen.height())
        ancho, alto = round(self._imagen.width()*escala), round(self._imagen.height()*escala)
        pintor.drawImage(QRect((self.width()-ancho)//2, (self.height()-alto)//2,
                              ancho, alto), self._imagen)


class CapaCinematica(QWidget):
    """Capa de fondo para un único corte, sin temporizadores de avance.

    ``activa`` indica que hay un corte seleccionado. Reducir movimiento o
    configurar ``activo=False`` conserva su póster y libera el decodificador.
    ``pausar`` conserva la posición; ``detener`` también olvida la selección.
    Ocultarla libera el vídeo y vuelve a cargarlo al mostrarse, si corresponde.
    """
    estado_cambiado = pyqtSignal(str)
    video_preparado = pyqtSignal(str)

    def __init__(self, parent=None, raiz=None, catalogo=None, bucle=True):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self._raiz = Path(raiz) if raiz is not None else RAIZ
        self._catalogo = CINEMATICAS if catalogo is None else catalogo
        self._bucle = bool(bucle)
        self._bucle_actual = self._bucle
        self._clave = None
        self._ruta_video = None
        self._reproductor = None
        self._conexion_media = None
        self._conexion_error = None
        self._video = None
        self._poster = _Poster(self)
        self._reducir = False
        self._habilitada = True
        self._pausada = False
        self._posicion = 0
        self._buscar_posicion = 0
        self._primer_frame = False
        self._generacion = 0
        self._objetivo_frame = 0
        self._poster_estatico = QPixmap()
        self._portada_inicio = QPixmap()
        self._ultimo_frame = QPixmap()
        self._estado = "inactiva"
        self._ventana_observada = None
        self.hide()

    @property
    def activa(self):
        return self._clave is not None

    @property
    def clave_actual(self):
        return self._clave

    @property
    def estado(self):
        return self._estado

    def _cambiar_estado(self, estado):
        if self._estado != estado:
            self._estado = estado
            self.estado_cambiado.emit(estado)

    def iniciar(self, clave, reproducir=True):
        """Prepara la cubierta antes de cambiar la fuente del vídeo.

        ``reproducir=False`` permite componer este primer plano durante la
        entrada del panel; ``reanudar`` arranca después junto con la voz.
        """
        entrada = self._catalogo.get(clave)
        if entrada is None:
            self.detener()
            return False
        self._bucle_actual = bool(entrada.get("bucle", self._bucle))
        ruta_video = self._raiz / entrada["video"]
        poster = QPixmap(str(self._raiz / entrada["poster"]))
        inicio = QPixmap(str(self._raiz / entrada["inicio"])) if entrada.get("inicio") else QPixmap()
        if not ruta_video.is_file() and poster.isNull():
            self.detener()
            return False
        # No ocultamos la capa entre dos fuentes: la próxima cubierta tapa
        # al transporte anterior antes de detenerlo. Es el frame 0 real,
        # no el cartel tomado varios segundos después en la película.
        self._poster_estatico = poster
        self._portada_inicio = inicio if not inicio.isNull() else poster
        self._ultimo_frame = QPixmap()
        self._mostrar_cubierta()
        self._liberar_video(conservar=False)
        self._clave = clave
        self._ruta_video = ruta_video if ruta_video.is_file() else None
        self._posicion = 0
        self._pausada = not reproducir
        self._poster.setGeometry(self.rect())
        self._cambiar_estado("pausada" if self._pausada else "poster")
        self.show()
        self._reproducir_si_corresponde()
        return True

    def _mostrar_cubierta(self):
        if self._reducir or not self._habilitada:
            imagen = self._poster_estatico
        elif not self._ultimo_frame.isNull():
            imagen = self._ultimo_frame
        else:
            imagen = self._portada_inicio
        if imagen.isNull():
            imagen = self._poster_estatico
        self._poster.imagen = imagen
        self._poster.update()
        self._poster.show()
        self._poster.raise_()

    def _asegurar_video(self):
        if self._reproductor is not None:
            return
        # QObject destruye sus hijos por orden de la lista de hijos. El reproductor
        # debe cerrar su transporte antes de que desaparezcan el sink y el
        # widget que reciben sus fotogramas. No se debe bajar el widget de
        # video: QWidget.lower() lo movería al principio de esa misma lista.
        self._reproductor = QMediaPlayer(self)
        self._video = _VideoCompuesto(self)
        self._video.setGeometry(self.rect())
        self._video.hide()

    def _reproducir_si_corresponde(self):
        if (not self.activa or self._pausada or not self.isVisible()
                or self.window().isMinimized()
                or self._reducir or not self._habilitada or self._ruta_video is None):
            return
        self._asegurar_video()
        self._reproductor.setLoops(QMediaPlayer.Loops.Infinite if self._bucle_actual else QMediaPlayer.Loops.Once)
        fuente = QUrl.fromLocalFile(str(self._ruta_video.resolve()))
        if self._reproductor.source() != fuente:
            self._generacion += 1
            generacion = self._generacion
            self._buscar_posicion = self._posicion
            self._objetivo_frame = self._posicion
            self._primer_frame = False
            self._reproductor.setVideoSink(None)
            self._video.renovar_canal(lambda frame: self._nuevo_frame(frame, generacion))
            for senal, conexion in ((self._reproductor.mediaStatusChanged, self._conexion_media),
                                     (self._reproductor.errorOccurred, self._conexion_error)):
                try:
                    if conexion is not None:
                        senal.disconnect(conexion)
                except (TypeError, RuntimeError):
                    pass
            self._conexion_media = lambda estado: self._cambio_media(estado, generacion)
            self._conexion_error = lambda *args: self._error_video(generacion=generacion)
            self._reproductor.mediaStatusChanged.connect(self._conexion_media)
            self._reproductor.errorOccurred.connect(self._conexion_error)
            self._reproductor.setVideoSink(self._video.videoSink())
            self._reproductor.setSource(fuente)
        self._reproductor.play()

    def _fuente_vigente(self, generacion=None):
        return (self.activa and self._reproductor is not None
                and self._ruta_video is not None
                and (generacion is None or generacion == self._generacion)
                and self._reproductor.source() == QUrl.fromLocalFile(str(self._ruta_video.resolve())))

    def _cambio_media(self, estado, generacion=None):
        if not self._fuente_vigente(generacion):
            return
        if estado in (QMediaPlayer.MediaStatus.LoadedMedia,
                      QMediaPlayer.MediaStatus.BufferedMedia):
            if self._buscar_posicion:
                posicion, self._buscar_posicion = self._buscar_posicion, 0
                self._reproductor.setPosition(posicion)
        elif estado == QMediaPlayer.MediaStatus.InvalidMedia:
            self._error_video()
        elif estado == QMediaPlayer.MediaStatus.EndOfMedia and not self._bucle_actual:
            # El último fotograma permanece visible junto al resumen. No se
            # dispara navegación ni una nueva elección al terminar el vídeo.
            self._cambiar_estado("finalizada")

    def _nuevo_frame(self, frame, generacion=None):
        if (not frame.isValid() or not self.activa or self._pausada
                or self._reducir or not self._habilitada or not self.isVisible()
                or not self._fuente_vigente(generacion)):
            return
        # Al recargar una pausa, algunos transportes entregan el frame 0
        # antes de completar el seek. La cubierta sigue congelada hasta el
        # plano correspondiente a la posición guardada.
        if not self._primer_frame and self._objetivo_frame:
            inicio = frame.startTime()
            if inicio >= 0 and inicio < max(0, self._objetivo_frame-125)*1000:
                return
            if inicio < 0 and self._reproductor.position() < self._objetivo_frame-125:
                return
        self._video._recibir_frame(frame)
        if self._video._imagen.isNull():
            return
        if not self._primer_frame:
            self._primer_frame = True
            self._objetivo_frame = 0
            self._video.show()
            self._video.raise_()
            self._poster.hide()
            self._cambiar_estado("reproduciendo")
            self.video_preparado.emit(self._clave)

    def _error_video(self, *args, generacion=None):
        if not self._fuente_vigente(generacion):
            return
        self._liberar_video()
        # El póster sigue mostrando el contexto; el juego continúa narrando.
        self._cambiar_estado("error")

    def _liberar_video(self, conservar=True):
        self._generacion += 1
        if self._reproductor is not None:
            if conservar and self._primer_frame and not self._video._imagen.isNull():
                self._ultimo_frame = QPixmap.fromImage(self._video._imagen)
            if not self._reproductor.source().isEmpty():
                self._posicion = max(0, self._reproductor.position())
            if conservar:
                self._mostrar_cubierta()
            self._video.invalidar_canal()
            self._reproductor.setVideoSink(None)
            self._reproductor.stop()
            self._reproductor.setSource(QUrl())
            self._video.hide()
            self._video._imagen = QImage()
            self._video.videoSink().setVideoFrame(QVideoFrame())
        self._primer_frame = False
        self._buscar_posicion = 0
        self._objetivo_frame = 0

    def detener(self):
        self._liberar_video(conservar=False)
        self._desvincular_ventana()
        self._clave = None
        self._ruta_video = None
        self._posicion = 0
        self._pausada = False
        self._poster.imagen = QPixmap()
        self._poster_estatico = QPixmap()
        self._portada_inicio = QPixmap()
        self._ultimo_frame = QPixmap()
        self._poster.update()
        self._cambiar_estado("inactiva")
        self.hide()

    def pausar(self):
        if not self.activa:
            return
        self._pausada = True
        self._liberar_video()
        self._cambiar_estado("pausada")

    def reanudar(self):
        if not self.activa:
            return
        necesita_cubierta = self._pausada or not self._primer_frame
        self._pausada = False
        if necesita_cubierta:
            self._mostrar_cubierta()
            self._cambiar_estado("poster")
        self._reproducir_si_corresponde()

    def configurar(self, reducir_movimiento=False, activo=True):
        self._reducir = bool(reducir_movimiento)
        self._habilitada = bool(activo)
        if self._reducir or not self._habilitada:
            self._liberar_video()
            self._mostrar_cubierta()
            if self.activa and not self._pausada:
                self._cambiar_estado("poster")
        else:
            if not self._primer_frame:
                self._mostrar_cubierta()
            self._reproducir_si_corresponde()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._poster.setGeometry(self.rect())
        if self._video is not None:
            self._video.setGeometry(self.rect())

    def _desvincular_ventana(self):
        ventana = getattr(self, "_ventana_observada", None)
        self._ventana_observada = None
        if ventana is not None and ventana is not self:
            try:
                ventana.removeEventFilter(self)
            except RuntimeError:
                # Qt puede haber destruido ya la ventana observada.
                pass

    def showEvent(self, event):
        super().showEvent(event)
        ventana = self.window()
        if self._ventana_observada is not ventana:
            if self._ventana_observada is not None:
                self._ventana_observada.removeEventFilter(self)
            self._ventana_observada = ventana
            if ventana is not self:
                ventana.installEventFilter(self)
        self._reproducir_si_corresponde()

    def _sincronizar_minimizacion(self):
        if self.window().isMinimized():
            self._liberar_video()
            if self.activa:
                self._cambiar_estado("pausada" if self._pausada else "poster")
        else:
            self._reproducir_si_corresponde()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            self._sincronizar_minimizacion()

    def eventFilter(self, objeto, event):
        # Qt puede entregar un último evento mientras GC ya ha limpiado el
        # diccionario Python del filtro. No debe escapar un AttributeError
        # desde este callback nativo y terminar el proceso completo.
        observada = getattr(self, "_ventana_observada", None)
        if (observada is not None and objeto is observada
                and event.type() == QEvent.Type.WindowStateChange):
            self._sincronizar_minimizacion()
        return super().eventFilter(objeto, event)

    def hideEvent(self, event):
        self._liberar_video()
        if self.activa:
            self._cambiar_estado("pausada" if self._pausada else "poster")
        super().hideEvent(event)

    def closeEvent(self, event):
        self.detener()
        super().closeEvent(event)
