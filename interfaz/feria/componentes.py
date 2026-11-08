"""Mesa narrativa de investigación: emite intenciones y muestra vistas del motor.

Las reglas y la visibilidad de las pistas pertenecen a SesionInvestigacion.
Este módulo no resuelve decisiones ni calcula alcance: solicita ambos al motor.
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPixmap
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QFormLayout, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QPushButton, QScrollArea,
    QSizePolicy, QSlider, QSplitter, QStackedWidget, QTabWidget,
    QTextBrowser, QToolButton, QVBoxLayout, QWidget,
)

from estructuras.grafo import Grafo
from infraestructura.recursos import RAIZ
from interfaz.componentes.arte import cargar_tipografias
from interfaz.componentes.grafo import VisualizadorGrafo
from interfaz.feria.expediente import ComparadorPrueba, DialogoPrueba
from interfaz.feria.estilos import ESTILO_FERIA


def _etiqueta(texto="", nombre=None):
    etiqueta = QLabel(texto)
    etiqueta.setWordWrap(True)
    etiqueta.setTextFormat(Qt.TextFormat.PlainText)
    etiqueta.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    if nombre:
        etiqueta.setObjectName(nombre)
    return etiqueta


def _boton(texto, funcion, principal=False):
    boton = QPushButton(texto)
    boton.setCursor(Qt.CursorShape.PointingHandCursor)
    boton.clicked.connect(funcion)
    if principal:
        boton.setObjectName("principal")
    return boton


def _tarjeta(papel=False):
    tarjeta = QFrame()
    tarjeta.setObjectName("papel" if papel else "tarjeta")
    distribucion = QVBoxLayout(tarjeta)
    distribucion.setContentsMargins(18, 17, 18, 17)
    distribucion.setSpacing(11)
    return tarjeta, distribucion


def _pagina_scroll():
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    pagina = QWidget()
    distribucion = QVBoxLayout(pagina)
    distribucion.setContentsMargins(2, 5, 12, 10)
    distribucion.setSpacing(15)
    area.setWidget(pagina)
    return area, distribucion


def _vaciar(distribucion):
    while distribucion.count():
        elemento = distribucion.takeAt(0)
        if elemento.widget() is not None:
            elemento.widget().deleteLater()
        elif elemento.layout() is not None:
            _vaciar(elemento.layout())


class IlustracionMesa(QWidget):
    """Ilustración adaptable con respaldo local; el texto permanece en widgets."""

    def __init__(self, ruta, respaldo, parent=None):
        super().__init__(parent)
        self.rutas = (ruta, respaldo)
        self.pixmap = QPixmap()
        self.setMinimumHeight(160)
        self.setMaximumHeight(230)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def paintEvent(self, event):
        if self.pixmap.isNull():
            for ruta in self.rutas:
                candidato = QPixmap(str(RAIZ / ruta))
                if not candidato.isNull():
                    self.pixmap = candidato
                    break
        pintor = QPainter(self)
        pintor.fillRect(self.rect(), QColor("#223d4d"))
        if not self.pixmap.isNull():
            imagen = self.pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                        Qt.TransformationMode.SmoothTransformation)
            pintor.drawPixmap((self.width() - imagen.width()) // 2,
                              (self.height() - imagen.height()) // 2, imagen)


class MapaCiudad(IlustracionMesa):
    """Los tres puntos del mapa son también controles accesibles por teclado."""

    lugar_seleccionado = pyqtSignal(str)
    POSICIONES = {"archivo": (.19, .25), "barrio": (.50, .77), "redaccion": (.81, .25)}

    def __init__(self, parent=None):
        super().__init__("assets/feria/mapa_ciudad.png", "assets/rediseno/fondos/ciudad.png", parent)
        self.setMinimumHeight(290)
        self.setMaximumHeight(360)
        self.botones = {}
        for id, nombre in (("archivo", "Archivo público"), ("barrio", "El vecindario"), ("redaccion", "Redacción")):
            boton = _boton(nombre, lambda checked=False, id=id: self.lugar_seleccionado.emit(id))
            boton.setParent(self)
            boton.setAccessibleName(f"Visitar {nombre} desde el mapa")
            self.botones[id] = boton

    def establecer_lugares(self, lugares, activa):
        for lugar in lugares:
            boton = self.botones.get(lugar.get("id"))
            if boton:
                boton.setEnabled(activa and lugar.get("disponible", True))
                boton.setToolTip(lugar.get("descripcion", ""))

    def resizeEvent(self, event):
        for id, boton in self.botones.items():
            x, y = self.POSICIONES[id]
            ancho = min(190, max(130, self.width() // 5))
            boton.setGeometry(round(self.width() * x - ancho / 2), round(self.height() * y), ancho, 49)
        super().resizeEvent(event)


class TableroInvestigacion(QWidget):
    """Cuatro espacios para investigar, cooperar y decidir sin salir del caso."""

    comando = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        cargar_tipografias()
        self.setObjectName("tableroInvestigacion")
        self.setStyleSheet(ESTILO_FERIA)
        self.vista = {}
        self._caso_id = None
        self._firma_hallazgos = None
        self._firma_red = None
        self._firma_contactos = None
        self._archivo_audio = None
        self._archivo_video = None
        self._actualizando = False
        self.dialogo_prueba = None
        self._caso_entrada = None
        self._pestana_activa = 0
        self._scroll_guardados = {i: 0 for i in range(4)}
        self._pestana_a_restaurar = None
        self._timer_entrada = QTimer(self)
        self._timer_entrada.setSingleShot(True)
        self._timer_entrada.timeout.connect(self._restablecer_mapa)
        self._timer_pestana = QTimer(self)
        self._timer_pestana.setSingleShot(True)
        self._timer_pestana.timeout.connect(self._restablecer_scroll_pestana)
        self.contactos = []
        self.botones_lugares = {}
        self.casillas_contactos = {}

        distribucion = QVBoxLayout(self)
        distribucion.setContentsMargins(24, 15, 22, 12)
        distribucion.setSpacing(9)
        self.ceja = _etiqueta("CIUDAD NOVA  /  UNA HISTORIA POR CONTRASTAR", "ceja")
        self.titulo = _etiqueta("La mesa de investigación", "tituloCaso")
        self.objetivo = _etiqueta("Escucha, reúne contexto y elige qué contar.", "subtitulo")
        self.indicacion = _etiqueta()
        self.mensaje = _etiqueta("", "aviso")
        distribucion.addWidget(self.ceja)
        distribucion.addWidget(self.titulo)
        distribucion.addWidget(self.objetivo)
        distribucion.addWidget(self.indicacion)
        distribucion.addWidget(self.mensaje)

        self.paginas = QStackedWidget()
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setAccessibleName("Espacios de investigación")
        self._crear_mapa()
        self._crear_expediente()
        self._crear_redaccion()
        self._crear_audiencia()
        self.paginas.addWidget(self.tabs)
        self._crear_resultado()
        distribucion.addWidget(self.paginas, 1)
        self.tabs.currentChanged.connect(self._cambio_pestana)

    def _emitir(self, tipo, **campos):
        if not self._actualizando:
            self.comando.emit({"tipo": tipo, **campos})

    def _crear_mapa(self):
        pagina, contenido = _pagina_scroll()
        self.ilustracion_mapa = MapaCiudad()
        self.ilustracion_mapa.lugar_seleccionado.connect(lambda lugar: self._emitir("investigar", lugar=lugar))
        self.ilustracion_mapa.setAccessibleName("Mapa de los lugares de Ciudad Nova")
        contenido.addWidget(self.ilustracion_mapa)
        publicacion, publicacion_layout = _tarjeta(papel=True)
        publicacion_layout.addWidget(_etiqueta("EL MENSAJE QUE ESTÁ CIRCULANDO", "tituloPapel"))
        self.publicacion_texto = _etiqueta()
        publicacion_layout.addWidget(self.publicacion_texto)
        contenido.addWidget(publicacion)
        self.restantes = _etiqueta()
        contenido.addWidget(self.restantes)
        self.lugares_layout = QHBoxLayout()
        self.lugares_layout.setSpacing(14)
        contenido.addLayout(self.lugares_layout)
        contenido.addWidget(_etiqueta(
            "Cada visita abre una fuente distinta. En el Expediente puedes revisar un medio "
            "o hacer una pregunta; también puedes decidir con las pistas que ya tienes.", "subtitulo"))
        self.cooperacion = _etiqueta()
        contenido.addWidget(self.cooperacion)
        contenido.addStretch()
        self.tabs.addTab(pagina, "&Mapa")

    def _crear_expediente(self):
        pagina, contenido = _pagina_scroll()
        divisor = QSplitter(Qt.Orientation.Horizontal)
        divisor.setChildrenCollapsible(False)
        lista_panel = QWidget()
        lista_layout = QVBoxLayout(lista_panel)
        lista_layout.setContentsMargins(0, 0, 9, 0)
        lista_layout.addWidget(_etiqueta("PISTAS EN TU MESA", "ceja"))
        self.lista_hallazgos = QListWidget()
        self.lista_hallazgos.setAccessibleName("Pistas propias y compartidas")
        self.lista_hallazgos.setMinimumWidth(220)
        self.lista_hallazgos.setMinimumHeight(205)
        self.lista_hallazgos.currentRowChanged.connect(self._mostrar_hallazgo)
        lista_layout.addWidget(self.lista_hallazgos)
        self.compartir = _boton("Compartir esta pista", self._compartir_hallazgo)
        lista_layout.addWidget(self.compartir)
        divisor.addWidget(lista_panel)
        documento, documento_layout = _tarjeta(papel=True)
        self.hallazgo_titulo = _etiqueta("Todavía no hay pistas", "tituloPapel")
        self.hallazgo_origen = _etiqueta()
        self.hallazgo_texto = _etiqueta("Visita un lugar del mapa o contrasta el material del caso.")
        documento_layout.addWidget(self.hallazgo_titulo)
        documento_layout.addWidget(self.hallazgo_origen)
        documento_layout.addWidget(self.hallazgo_texto)
        documento_layout.addStretch()
        divisor.addWidget(documento)
        divisor.setStretchFactor(0, 1)
        divisor.setStretchFactor(1, 2)
        contenido.addWidget(divisor)

        medio, medio_layout = _tarjeta()
        self.medio_titulo = _etiqueta("REVISA EL MATERIAL", "ceja")
        self.medio_consigna = _etiqueta()
        self.medio_texto = _etiqueta()
        self.comparador = ComparadorPrueba()
        self.slider_medio = QSlider(Qt.Orientation.Horizontal)
        self.slider_medio.setRange(0, 100)
        self.slider_medio.setAccessibleName("Ampliar encuadre o buscar contexto en el material")
        self.slider_medio.valueChanged.connect(self._mover_lupa)
        self.slider_medio.valueChanged.connect(self.comparador.establecer_valor)
        self.comparador.valor_cambiado.connect(self.slider_medio.setValue)
        self.lupa_lectura = _etiqueta("Encuadre: 0 %", "subtitulo")
        self.examinar = _boton("Examinar este punto", self._examinar)
        self.ampliar = _boton("Ampliar prueba", self.abrir_prueba)
        medio_layout.addWidget(self.medio_titulo)
        medio_layout.addWidget(self.medio_consigna)
        medio_layout.addWidget(self.medio_texto)
        medio_layout.addWidget(self.comparador)
        medio_layout.addWidget(self.slider_medio)
        lupa_fila = QHBoxLayout()
        lupa_fila.addWidget(self.lupa_lectura, 1)
        lupa_fila.addWidget(self.ampliar)
        lupa_fila.addWidget(self.examinar)
        medio_layout.addLayout(lupa_fila)

        self.audio_panel = QWidget()
        audio_layout = QHBoxLayout(self.audio_panel)
        audio_layout.setContentsMargins(0, 0, 0, 0)
        self.audio_boton = _boton("Escuchar", self._alternar_audio)
        self.audio_posicion = QSlider(Qt.Orientation.Horizontal)
        self.audio_posicion.setAccessibleName("Posición del audio")
        self.audio_posicion.sliderMoved.connect(self._buscar_audio)
        self.audio_tiempo = _etiqueta("0:00 / 0:00")
        self.transcripcion_boton = QToolButton()
        self.transcripcion_boton.setText("Transcripción")
        self.transcripcion_boton.setCheckable(True)
        self.transcripcion_boton.toggled.connect(self._alternar_transcripcion)
        audio_layout.addWidget(self.audio_boton)
        audio_layout.addWidget(self.audio_posicion, 1)
        audio_layout.addWidget(self.audio_tiempo)
        audio_layout.addWidget(self.transcripcion_boton)
        medio_layout.addWidget(self.audio_panel)
        self.transcripcion = _etiqueta()
        self.transcripcion.hide()
        medio_layout.addWidget(self.transcripcion)
        self.audio_salida = QAudioOutput(self)
        self.audio_salida.setVolume(.75)
        self.audio = QMediaPlayer(self)
        self.audio.setAudioOutput(self.audio_salida)
        self.audio.durationChanged.connect(self._duracion_audio)
        self.audio.positionChanged.connect(self._posicion_audio)
        self.audio.playbackStateChanged.connect(self._estado_audio)
        self.audio.errorOccurred.connect(self._error_audio)

        self.video_panel = QWidget()
        video_layout = QVBoxLayout(self.video_panel)
        video_layout.setContentsMargins(0, 0, 0, 0)
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(200)
        self.video_widget.setMaximumHeight(300)
        self.video_widget.setAccessibleName("Video del contexto del caso")
        self.video_boton = _boton("Ver el momento", self._alternar_video)
        video_layout.addWidget(self.video_widget)
        video_layout.addWidget(self.video_boton, alignment=Qt.AlignmentFlag.AlignLeft)
        medio_layout.addWidget(self.video_panel)
        self.video_salida = QAudioOutput(self)
        self.video_salida.setVolume(.6)
        self.video = QMediaPlayer(self)
        self.video.setAudioOutput(self.video_salida)
        self.video.setVideoOutput(self.video_widget)
        self.video.playbackStateChanged.connect(self._estado_video)
        self.video.errorOccurred.connect(self._error_video)
        contenido.addWidget(medio)

        entrevista, entrevista_layout = _tarjeta()
        self.entrevista_titulo = _etiqueta("UNA CONVERSACIÓN", "ceja")
        entrevista_layout.addWidget(self.entrevista_titulo)
        self.preguntas = QComboBox()
        self.preguntas.setAccessibleName("Pregunta para la entrevista")
        self.prueba_entrevista = QComboBox()
        self.prueba_entrevista.setAccessibleName("Prueba que presentar en la entrevista")
        entrevista_layout.addWidget(self.preguntas)
        entrevista_layout.addWidget(self.prueba_entrevista)
        self.entrevistar = _boton("Hacer la pregunta", self._entrevistar)
        entrevista_layout.addWidget(self.entrevistar)
        contenido.addWidget(entrevista)
        self.pistas_ajenas, self.pistas_ajenas_layout = _tarjeta()
        contenido.addWidget(self.pistas_ajenas)
        contenido.addStretch()
        self.tabs.addTab(pagina, "&Expediente")

    def _crear_redaccion(self):
        pagina, contenido = _pagina_scroll()
        self.rol_ayuda = _etiqueta()
        contenido.addWidget(self.rol_ayuda)
        formulario, formulario_layout = _tarjeta()
        campos = QFormLayout()
        campos.setHorizontalSpacing(15)
        campos.setVerticalSpacing(13)
        self.accion = QComboBox()
        self.accion.setAccessibleName("Qué hacer con la publicación")
        self.titular = QLineEdit()
        self.titular.setMaxLength(160)
        self.titular.setPlaceholderText("Escribe lo que te atreves a afirmar…")
        self.titular.setAccessibleName("Titular de tu publicación")
        self.certeza = QComboBox()
        self.certeza.setAccessibleName("Grado de certeza")
        self.evidencia = QComboBox()
        self.evidencia.setAccessibleName("Evidencia para fundamentar la decisión")
        campos.addRow("Tu acción", self.accion)
        campos.addRow("Tu titular", self.titular)
        campos.addRow("Tu certeza", self.certeza)
        campos.addRow("Tu fundamento", self.evidencia)
        formulario_layout.addLayout(campos)
        self.descripcion_accion = _etiqueta("", "subtitulo")
        formulario_layout.addWidget(self.descripcion_accion)
        contenido.addWidget(formulario)
        previa, previa_layout = _tarjeta(papel=True)
        previa_layout.addWidget(_etiqueta("ANTES DE ENVIAR", "tituloPapel"))
        self.vista_previa = _etiqueta()
        previa_layout.addWidget(self.vista_previa)
        contenido.addWidget(previa)
        self.propuestas_panel, self.propuestas_layout = _tarjeta()
        contenido.addWidget(self.propuestas_panel)
        fila = QHBoxLayout()
        self.proponer = _boton("Compartir borrador", lambda: self._redactar("proponer"))
        self.decidir = _boton("Tomar esta decisión", lambda: self._redactar("decidir"), principal=True)
        fila.addWidget(self.proponer)
        fila.addStretch()
        fila.addWidget(self.decidir)
        contenido.addLayout(fila)
        self.turno_ayuda = _etiqueta("", "subtitulo")
        contenido.addWidget(self.turno_ayuda)
        contenido.addStretch()
        self.accion.currentIndexChanged.connect(self._actualizar_previa)
        self.titular.textChanged.connect(self._actualizar_previa)
        self.certeza.currentIndexChanged.connect(self._actualizar_previa)
        self.evidencia.currentIndexChanged.connect(self._actualizar_previa)
        self.tabs.addTab(pagina, "&Redacción")

    def _crear_audiencia(self):
        pagina, contenido = _pagina_scroll()
        contenido.addWidget(_etiqueta(
            "Una historia llega a personas, no a un contador. Elige uno o dos contactos "
            "directos y mira cómo puede circular antes de enviarla."))
        self.grafo = Grafo()
        self.visualizador = VisualizadorGrafo(self.grafo)
        self.visualizador.setMinimumHeight(340)
        self.visualizador.setAccessibleName("Red social: selecciona un contacto directo")
        self.visualizador.nodo_seleccionado.connect(self._seleccionar_nodo)
        contenido.addWidget(self.visualizador)
        self.contactos_panel, self.contactos_layout = _tarjeta()
        contenido.addWidget(self.contactos_panel)
        self.prever = _boton("Ver a quién podría llegar", self._prever_alcance)
        contenido.addWidget(self.prever)
        self.alcance = _etiqueta("Elige contactos para prever la circulación.")
        contenido.addWidget(self.alcance)
        self.reparacion = _etiqueta("", "aviso")
        contenido.addWidget(self.reparacion)
        self.relaciones_panel, self.relaciones_layout = _tarjeta()
        contenido.addWidget(self.relaciones_panel)
        contenido.addStretch()
        self.tabs.addTab(pagina, "&Audiencia")

    def _crear_resultado(self):
        pagina, contenido = _pagina_scroll()
        self.resultado_ceja = _etiqueta("LO QUE QUEDÓ EN LA CIUDAD", "ceja")
        self.resultado_titulo = _etiqueta("La ciudad responde", "tituloCaso")
        self.resultado_resumen = _etiqueta()
        contenido.addWidget(self.resultado_ceja)
        contenido.addWidget(self.resultado_titulo)
        contenido.addWidget(self.resultado_resumen)
        self.resultado_personajes, self.resultado_personajes_layout = _tarjeta(papel=True)
        contenido.addWidget(self.resultado_personajes)
        self.detalle_boton = QToolButton()
        self.detalle_boton.setText("Ver los cambios y las decisiones")
        self.detalle_boton.setCheckable(True)
        self.detalle_boton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.detalle_boton.setArrowType(Qt.ArrowType.RightArrow)
        contenido.addWidget(self.detalle_boton)
        self.resultado_detalles = QTextBrowser()
        self.resultado_detalles.setOpenExternalLinks(False)
        self.resultado_detalles.setMinimumHeight(170)
        self.resultado_detalles.hide()
        self.detalle_boton.toggled.connect(self._mostrar_detalles)
        contenido.addWidget(self.resultado_detalles)
        self.continuar = _boton("Seguir con la historia", lambda: self._emitir("continuar"), principal=True)
        contenido.addWidget(self.continuar, alignment=Qt.AlignmentFlag.AlignRight)
        self.confirmacion = _etiqueta("", "subtitulo")
        contenido.addWidget(self.confirmacion)
        contenido.addStretch()
        self.paginas.addWidget(pagina)

    def actualizar(self, vista):
        """Actualiza datos sin borrar el borrador ni mover la pestaña del usuario."""
        if not isinstance(vista, dict):
            raise TypeError("La vista de investigación debe ser un diccionario")
        self._actualizando = True
        try:
            self.vista = vista
            caso = vista.get("caso") or {}
            nuevo_caso = caso.get("id") != self._caso_id
            if nuevo_caso:
                if self.dialogo_prueba is not None:
                    self.dialogo_prueba.close()
                self._caso_id = caso.get("id")
                self.titular.clear()
                self.slider_medio.setValue(0)
                self.contactos = []
                self._firma_hallazgos = None
                self.audio.stop()
                self.video.stop()
                self.transcripcion_boton.setChecked(False)
                self.detalle_boton.setChecked(False)
                self._scroll_guardados[0] = 0
                self.tabs.setCurrentIndex(0)
            numero, total = caso.get("numero", 1), caso.get("total", 6)
            self.ceja.setText(f"CIUDAD NOVA  /  CAPÍTULO {caso.get('capitulo', 1)}  /  CASO {numero} DE {total}")
            self.titulo.setText(caso.get("titulo", "La mesa de investigación"))
            self.objetivo.setText(caso.get("objetivo", "Escucha, reúne contexto y elige qué contar."))
            restantes = int(vista.get("acciones_restantes", 0))
            rol = "Periodista" if vista.get("mi_rol") == "periodista" else "Ciudadano"
            self.indicacion.setText(f"{rol}  ·  {restantes} oportunidades de investigación disponibles")
            self.mensaje.setText(vista.get("mensaje") or "")
            self.mensaje.setVisible(bool(self.mensaje.text()))
            activa = (vista.get("fase") in ("investigacion", "decision")
                      and vista.get("mi_id") not in vista.get("decididos", []))
            self._actualizar_mapa(activa, restantes)
            self._actualizar_hallazgos()
            self._actualizar_medio(activa, restantes)
            self._actualizar_redaccion(activa, nuevo_caso)
            self._actualizar_audiencia(activa, nuevo_caso)
            self._actualizar_resultado()
            self.paginas.setCurrentIndex(1 if vista.get("fase") in ("resultado", "final") else 0)
            self._actualizar_previa()
        finally:
            self._actualizando = False
        if nuevo_caso and vista.get("fase") in ("investigacion", "decision"):
            self._caso_entrada = self._caso_id
            self._timer_entrada.start(0)

    def _restablecer_mapa(self):
        if (self._caso_entrada != self._caso_id or self.tabs.currentIndex() != 0
                or self.vista.get("fase") not in ("investigacion", "decision") or not self.isVisible()):
            return
        self.tabs.tabBar().setFocus(Qt.FocusReason.OtherFocusReason)
        area = self.tabs.widget(0)
        area.verticalScrollBar().setValue(area.verticalScrollBar().minimum())
        self._scroll_guardados[0] = 0

    def configurar_preferencias(self, preferencias):
        """Aplica lectura y sonido también a los reproductores del expediente."""
        tamano = preferencias.get("tamano_texto", 16)
        tamano = tamano if tamano in (14, 16, 18, 20) else 16
        estilo = ESTILO_FERIA.replace("font-size: 16px", f"font-size: {tamano}px")
        if preferencias.get("alto_contraste"):
            estilo = estilo.replace("#142936", "#070e15").replace("#f8edda", "#ffffff")
            estilo = estilo.replace("#cbd5d8", "#ffffff").replace("#223d4d", "#111c27")
        self.setStyleSheet(estilo)
        volumen = max(0, min(100, preferencias.get("volumen", 65))) / 100
        for salida in (self.audio_salida, self.video_salida):
            salida.setMuted(not preferencias.get("sonido", True))
            salida.setVolume(volumen)
        if preferencias.get("reducir_movimiento"):
            self.visualizador.completar_contactos()

    def _actualizar_mapa(self, activa, restantes):
        caso = self.vista.get("caso") or {}
        self.publicacion_texto.setText((caso.get("publicacion") or {}).get("texto", ""))
        lugares = self.vista.get("lugares", [])
        firma = tuple((x.get("id"), x.get("nombre"), x.get("descripcion")) for x in lugares)
        if getattr(self, "_firma_lugares", None) != firma:
            self._firma_lugares = firma
            _vaciar(self.lugares_layout)
            self.botones_lugares = {}
            for lugar in lugares:
                tarjeta, contenido = _tarjeta()
                contenido.addWidget(_etiqueta(lugar.get("nombre", "Un lugar"), "ceja"))
                descripcion = _etiqueta(lugar.get("descripcion", "Busca otra versión de la historia."))
                descripcion.setMinimumHeight(65)
                contenido.addWidget(descripcion)
                contenido.addStretch()
                identificador = lugar["id"]
                boton = _boton("Visitar", lambda checked=False, id=identificador: self._emitir("investigar", lugar=id))
                boton.setAccessibleName(f"Investigar en {lugar.get('nombre', identificador)}")
                contenido.addWidget(boton)
                self.botones_lugares[identificador] = boton
                self.lugares_layout.addWidget(tarjeta, 1)
        for lugar in lugares:
            self.botones_lugares[lugar["id"]].setEnabled(activa and restantes > 0 and lugar.get("disponible", True))
        self.ilustracion_mapa.establecer_lugares(lugares, activa and restantes > 0)
        self.restantes.setText(f"Tienes {restantes} visitas o comprobaciones para este caso. Elige qué fuente necesitas.")
        self.cooperacion.setText(
            "Tu compañero puede encontrar otras pistas. Compártelas en el Expediente y discutan un borrador antes de decidir."
            if self.vista.get("cooperativa") else
            "La información puede cambiar cuando encuentras su contexto. Conserva la duda si todavía falta una fuente.")

    def _actualizar_hallazgos(self):
        hallazgos = self.vista.get("hallazgos", [])
        firma = repr(hallazgos)
        seleccionado = self._hallazgo_seleccionado()
        id_anterior = seleccionado.get("id") if seleccionado else None
        if firma != self._firma_hallazgos:
            self._firma_hallazgos = firma
            self.lista_hallazgos.clear()
            fila = 0
            for indice, hallazgo in enumerate(hallazgos):
                sufijo = " · compartida" if hallazgo.get("compartido") else ""
                elemento = QListWidgetItem(hallazgo.get("titulo", "Pista") + sufijo)
                elemento.setData(Qt.ItemDataRole.UserRole, hallazgo["id"])
                self.lista_hallazgos.addItem(elemento)
                if hallazgo["id"] == id_anterior:
                    fila = indice
            self.lista_hallazgos.setCurrentRow(fila if hallazgos else -1)
        self._mostrar_hallazgo(self.lista_hallazgos.currentRow())
        opciones = [("Sin prueba adjunta", None)] + [(x.get("titulo", x["id"]), x["id"]) for x in hallazgos]
        self._poblar_combo(self.evidencia, opciones)
        self._poblar_combo(self.prueba_entrevista, opciones)
        _vaciar(self.pistas_ajenas_layout)
        disponibles = [h for h in self.vista.get("hallazgos_disponibles", [])
                       if h.get("propietario") != self.vista.get("mi_id") and not h.get("compartido")]
        self.pistas_ajenas.setVisible(bool(disponibles))
        if disponibles:
            self.pistas_ajenas_layout.addWidget(_etiqueta("TU COMPAÑERO ENCONTRÓ ALGO", "ceja"))
            for hallazgo in disponibles:
                fila = QHBoxLayout()
                fila.addWidget(_etiqueta(hallazgo.get("titulo", "Una pista pendiente de compartir")), 1)
                id = hallazgo["id"]
                fila.addWidget(_boton("Pedir pista", lambda checked=False, id=id: self._emitir("solicitar_hallazgo", evidencia_id=id)))
                self.pistas_ajenas_layout.addLayout(fila)

    def _actualizar_medio(self, activa, restantes):
        caso = self.vista.get("caso") or {}
        medio = caso.get("medio") or {}
        formato = medio.get("tipo", "captura")
        nombres = {"captura": "LA CAPTURA Y SU CONTEXTO", "audio": "ESCUCHA LO QUE FALTA", "mapa": "LEE EL MAPA COMPLETO"}
        self.medio_titulo.setText(nombres.get(formato, "REVISA EL MATERIAL"))
        self.medio_consigna.setText(medio.get("consigna", "Busca un detalle que falte en la publicación."))
        revelado = bool(medio.get("revelado") or medio.get("recuperado"))
        texto = medio.get("texto_completo") if revelado else medio.get("texto_inicial")
        self.medio_texto.setText(texto or "Todavía no tienes el contexto de este material.")
        self.examinar.setEnabled(activa and restantes > 0 and not revelado)
        self.examinar.setText("Contexto recuperado" if revelado else "Examinar este punto")
        self.slider_medio.setEnabled(activa)
        self.comparador.setEnabled(activa)
        self.comparador.setVisible(formato in ("captura", "mapa"))
        self.ampliar.setVisible(formato in ("captura", "mapa"))
        id = caso.get("id", "")
        self.comparador.actualizar(
            medio.get("imagen_recortada", f"assets/feria/pruebas/{id}_recorte.png"),
            medio.get("imagen_completa", f"assets/feria/pruebas/{id}_original.png"), revelado,
            inspeccionable=bool(medio.get("inspeccionable")))
        if self.dialogo_prueba is not None:
            material = dict(medio)
            material.setdefault("imagen_recortada", f"assets/feria/pruebas/{id}_recorte.png")
            material.setdefault("imagen_completa", f"assets/feria/pruebas/{id}_original.png")
            self.dialogo_prueba.actualizar(material, activa and restantes > 0)
        self.audio_panel.setVisible(formato == "audio")
        self.transcripcion.setText(texto or "No hay transcripción disponible.")
        self.transcripcion.setVisible(formato == "audio" and self.transcripcion_boton.isChecked())
        explorable = revelado or medio.get("inspeccionable")
        ruta = ((medio.get("audio_completo") or medio.get("archivo_completo")) if explorable
                else medio.get("audio_recortado")) or medio.get("audio")
        self._cargar_audio(ruta if formato == "audio" else None)
        self._actualizar_fragmento(self.slider_medio.value())
        self.audio_boton.setEnabled(bool(self._archivo_audio))
        self._cargar_video(medio.get("video"))
        self.video_panel.setVisible(bool(self._archivo_video))
        self._poblar_combo(self.preguntas, [(x.get("texto", x["id"]), x["id"]) for x in caso.get("preguntas", [])])
        nombre = caso.get("npc_nombre", "una fuente")
        self.entrevista_titulo.setText(f"CONVERSA CON {nombre.upper()}")
        self.entrevistar.setEnabled(activa and restantes > 0 and self.preguntas.count() > 0)

    def _actualizar_redaccion(self, activa, nuevo_caso):
        periodista = self.vista.get("mi_rol") == "periodista"
        self.rol_ayuda.setText(
            "Tu trabajo es contrastar lo que puedes sostener. Cita una prueba y deja visible lo que aún no sabes."
            if periodista else
            "Tu voz mueve a tus vecinos. Decide qué compartir, a quién escuchar y cuándo cuidar una duda.")
        self._poblar_combo(self.accion, [(a.get("titulo", a["clave"]), a["clave"]) for a in self.vista.get("acciones", [])])
        etiquetas = {"pendiente": "Pendiente de comprobar", "probable": "Probable, con dudas", "confirmada": "Confirmada por una fuente"}
        self._poblar_combo(self.certeza, [(etiquetas.get(x, x), x) for x in self.vista.get("certezas", ["pendiente", "probable", "confirmada"])])
        if nuevo_caso:
            self.certeza.setCurrentIndex(0)
            self.accion.setCurrentIndex(0)
            self.evidencia.setCurrentIndex(0)
            self.prueba_entrevista.setCurrentIndex(0)
        mi_id = self.vista.get("mi_id")
        decidio = mi_id in self.vista.get("decididos", [])
        turno = self.vista.get("turno_id")
        mi_turno = turno is None or turno == mi_id
        self.decidir.setEnabled(activa and mi_turno and not decidio and self.accion.count() > 0)
        self.proponer.setVisible(bool(self.vista.get("cooperativa")))
        self.proponer.setEnabled(activa and not decidio)
        if decidio:
            texto = "Tu decisión está registrada. Espera a tu compañero para conocer la reacción de la ciudad."
        elif not mi_turno:
            nombre = next((j.get("nombre", "tu compañero") for j in self.vista.get("jugadores", []) if j.get("id") == turno), "tu compañero")
            texto = f"Ahora decide {nombre}. Puedes seguir preparando y compartir tu borrador."
        else:
            texto = "Es tu momento de decidir. El borrador todavía se puede cambiar hasta enviarlo."
        self.turno_ayuda.setText(texto)
        _vaciar(self.propuestas_layout)
        propuestas = self.vista.get("propuestas", [])
        self.propuestas_panel.setVisible(bool(propuestas))
        if propuestas:
            self.propuestas_layout.addWidget(_etiqueta("BORRADORES SOBRE LA MESA", "ceja"))
            jugadores = {j["id"]: j.get("nombre", j["id"]) for j in self.vista.get("jugadores", [])}
            for propuesta in propuestas:
                nombre = jugadores.get(propuesta.get("jugador_id"), "Tu compañero")
                texto = propuesta.get("titular") or "Sin titular todavía"
                self.propuestas_layout.addWidget(_etiqueta(f"{nombre}: «{texto}»\n{propuesta.get('accion', '')} · {etiquetas.get(propuesta.get('certeza'), 'Pendiente')}"))

    def _actualizar_audiencia(self, activa, nuevo_caso=False):
        red = self.vista.get("red") or {}
        nodos, aristas = red.get("nodos", []), red.get("aristas", [])
        firma = repr((nodos, aristas))
        if firma != self._firma_red:
            self._firma_red = firma
            grafo = Grafo()
            for nodo in nodos:
                grafo.agregar_vertice(nodo["id"], nodo.get("nombre", nodo["id"]))
            for origen, destino in aristas:
                grafo.agregar_arista(origen, destino)
            self.grafo = grafo
            self.visualizador.grafo = grafo
        vecinos = red.get("vecinos", [])
        self.contactos = [id for id in self.contactos if id in vecinos]
        if nuevo_caso:
            self.contactos = [id for id in red.get("seleccionados", []) if id in vecinos][:2]
        firma_contactos = repr((vecinos, nodos))
        if firma_contactos != self._firma_contactos:
            self._firma_contactos = firma_contactos
            _vaciar(self.contactos_layout)
            self.casillas_contactos = {}
            self.contactos_layout.addWidget(_etiqueta("¿A QUIÉN LE CONTARÍAS ESTA HISTORIA?", "ceja"))
            fila = QGridLayout()
            for indice, id in enumerate(vecinos):
                nombre = self.grafo.nodos[id].nombre if id in self.grafo.nodos else id
                casilla = QCheckBox(nombre)
                casilla.setChecked(id in self.contactos)
                casilla.toggled.connect(lambda marcado, id=id: self._cambiar_contacto(id, marcado))
                self.casillas_contactos[id] = casilla
                fila.addWidget(casilla, indice // 3, indice % 3)
            for columna in range(3):
                fila.setColumnStretch(columna, 1)
            self.contactos_layout.addLayout(fila)
        for id, casilla in self.casillas_contactos.items():
            casilla.blockSignals(True)
            casilla.setChecked(id in self.contactos)
            casilla.blockSignals(False)
            casilla.setEnabled(activa)
        self.prever.setEnabled(activa and bool(self.contactos))
        alcance = red.get("alcance") or {}
        receptores = alcance.get("receptores", [])
        self.visualizador.visitados = set(alcance.get("orden", []))
        self.visualizador.aristas_usadas = {tuple(a) for a in alcance.get("aristas", [])}
        self.visualizador.focos_contacto = set(self.contactos)
        jugador = next((j for j in self.vista.get("jugadores", []) if j.get("id") == self.vista.get("mi_id")), {})
        self.visualizador.emisor = red.get("emisor_id", jugador.get("ciudadano_id", ""))
        self.visualizador.update()
        if alcance.get("orden"):
            nombres = [self.grafo.nodos[id].nombre if id in self.grafo.nodos else str(id) for id in receptores]
            self.alcance.setText("Podría llegar a: " + (", ".join(nombres) if nombres else "ninguna otra persona por esta ruta") + ".")
        else:
            self.alcance.setText("Elige uno o dos contactos directos y comprueba el alcance antes de enviar.")
        reparacion = self.vista.get("mision_reparacion") or {}
        pendientes = [self.grafo.nodos[id].nombre if id in self.grafo.nodos else id
                      for id in reparacion.get("pendientes", [])]
        self.reparacion.setVisible(bool(reparacion.get("afectados")))
        self.reparacion.setText(
            "El rumor ya llegó a algunas personas. Falta que la corrección alcance a: " + ", ".join(pendientes) + "."
            if pendientes else "La corrección alcanzó a las personas que habían recibido este rumor.")
        _vaciar(self.relaciones_layout)
        relaciones = self.vista.get("relaciones", [])
        self.relaciones_panel.setVisible(bool(relaciones))
        if relaciones:
            self.relaciones_layout.addWidget(_etiqueta("ASÍ ESTÁN LOS VÍNCULOS", "ceja"))
            for relacion in relaciones:
                nombre = relacion.get("nombre", "Una persona de la ciudad")
                self.relaciones_layout.addWidget(_etiqueta(f"{nombre} · {relacion.get('estado', 'abierto')}\n{relacion.get('respuesta', '')}"))

    def _actualizar_resultado(self):
        final = self.vista.get("fase") == "final"
        resultado = self.vista.get("resultado") or {}
        self.resultado_ceja.setText("DESPUÉS DE LAS URNAS" if final else "DESPUÉS DE TU DECISIÓN")
        self.resultado_titulo.setText("La ciudad que ayudaste a construir" if final else "La ciudad responde")
        resumen = resultado.get("resumen") or ("El recuento reúne las voces que se escucharon en la ciudad." if final else "Tu decisión ya forma parte de esta historia.")
        eleccion = self.vista.get("resultado_electoral") or {}
        ganador = eleccion.get("ganador")
        ganadores = eleccion.get("ganadores", [])
        if final and eleccion.get("empate"):
            resumen += "\nHay un empate. El recuento público sigue abierto entre " + ", ".join(ganadores) + "."
        elif final and ganadores:
            resumen += f"\nLas urnas señalan a {ganadores[0]}."
        elif final and ganador:
            nombre = ganador.get("nombre", ganador.get("id", "")) if isinstance(ganador, dict) else str(ganador)
            resumen += f"\nLas urnas señalan a {nombre}."
        self.resultado_resumen.setText(resumen)
        _vaciar(self.resultado_personajes_layout)
        relaciones = self.vista.get("relaciones", [])
        self.resultado_personajes.setVisible(bool(relaciones))
        for relacion in relaciones:
            self.resultado_personajes_layout.addWidget(_etiqueta(relacion.get("nombre", "Una voz de Ciudad Nova"), "tituloPapel"))
            self.resultado_personajes_layout.addWidget(_etiqueta(relacion.get("respuesta") or f"El vínculo queda {relacion.get('estado', 'abierto')}."))
        etiquetas = {"confianza": "Confianza", "convivencia": "Convivencia", "bienestar_digital": "Bienestar digital",
                     "info_verificada": "Información contrastada", "desinformacion": "Desinformación",
                     "conflictos": "Conflictos", "participacion": "Participación"}
        jugadores = {j["id"]: j.get("nombre", "Participante") for j in self.vista.get("jugadores", [])}
        detalles = []
        for registro in resultado.get("registros", []):
            if isinstance(registro, dict):
                nombre = jugadores.get(registro.get("jugador_id"), "Participante")
                titulo = registro.get("titulo_accion") or registro.get("accion_rol") or "Una decisión"
                editor = registro.get("editor") or {}
                lineas = [f"{nombre} · {titulo}"]
                if editor.get("titular"):
                    lineas.append("«" + editor["titular"] + "»")
                if registro.get("editorial"):
                    lineas.append(registro["editorial"])
                for clave, cambio in (registro.get("cambios_reales") or {}).items():
                    lineas.append(f"{etiquetas.get(clave, clave.replace('_', ' ').capitalize())}: {cambio:+g}")
                lineas.append(f"Puntos: {registro.get('puntos', 0):+g} · Llegó a {registro.get('alcance', 0)} personas")
                detalles.append("\n".join(lineas))
            else:
                detalles.append(str(registro))
        if final:
            detalles.extend(f"{j.get('nombre', 'Participante')}: {j.get('puntos', 0)} puntos · reputación {j.get('reputacion', 0)}"
                            for j in self.vista.get("jugadores", []))
        estado = self.vista.get("estado") or {}
        detalles.extend(f"{etiquetas.get(clave, str(clave).replace('_', ' ').capitalize())}: {valor}" for clave, valor in estado.items())
        if final and eleccion.get("porcentajes"):
            detalles.append("Recuento de las urnas")
            detalles.extend(f"{nombre}: {porcentaje:g} %" for nombre, porcentaje in eleccion["porcentajes"].items())
        self.resultado_detalles.setPlainText("\n\n".join(detalles) or "La decisión quedó registrada en el historial de esta partida.")
        confirmo = self.vista.get("mi_id") in self.vista.get("confirmados", [])
        self.continuar.setVisible(not final)
        self.continuar.setEnabled(not confirmo)
        self.continuar.setText("Listo para continuar" if self.vista.get("cooperativa") else "Seguir con la historia")
        self.confirmacion.setText("Tu compañero aún está leyendo. La historia sigue cuando ambos estén listos." if confirmo and not final else "")

    @staticmethod
    def _poblar_combo(combo, opciones):
        anteriores = [(combo.itemText(i), combo.itemData(i)) for i in range(combo.count())]
        if anteriores == opciones:
            return
        elegido = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        for texto, valor in opciones:
            combo.addItem(str(texto), valor)
        indice = combo.findData(elegido)
        combo.setCurrentIndex(indice if indice >= 0 else (0 if opciones else -1))
        combo.blockSignals(False)

    def _hallazgo_seleccionado(self):
        elemento = self.lista_hallazgos.currentItem()
        id = elemento.data(Qt.ItemDataRole.UserRole) if elemento else None
        return next((x for x in self.vista.get("hallazgos", []) if x.get("id") == id), None)

    def _mostrar_hallazgo(self, fila):
        hallazgo = self._hallazgo_seleccionado()
        if hallazgo:
            self.hallazgo_titulo.setText(hallazgo.get("titulo", "Una pista"))
            origen = "Fuente: " + str(hallazgo.get("origen", "sin identificar"))
            solicitada = any(s.get("evidencia_id") == hallazgo["id"] and not s.get("atendida")
                             for s in self.vista.get("solicitudes", []))
            if solicitada and hallazgo.get("propietario") == self.vista.get("mi_id"):
                origen += " · Tu compañero te pidió esta pista."
            self.hallazgo_origen.setText(origen)
            self.hallazgo_texto.setText(hallazgo.get("texto", ""))
        else:
            self.hallazgo_titulo.setText("Todavía no hay pistas")
            self.hallazgo_origen.clear()
            self.hallazgo_texto.setText("Visita un lugar del mapa o contrasta el material del caso.")
        propia = hallazgo and hallazgo.get("propietario") == self.vista.get("mi_id")
        self.compartir.setVisible(bool(self.vista.get("cooperativa")))
        self.compartir.setEnabled(bool(propia and not hallazgo.get("compartido")))

    def _compartir_hallazgo(self):
        hallazgo = self._hallazgo_seleccionado()
        if hallazgo:
            self._emitir("compartir_hallazgo", evidencia_id=hallazgo["id"])

    def _examinar(self):
        medio = (self.vista.get("caso") or {}).get("medio") or {}
        self._emitir("examinar", medio=medio.get("tipo", "captura"), valor=self.slider_medio.value())

    def abrir_prueba(self):
        if self.dialogo_prueba is not None:
            self.dialogo_prueba.raise_()
            return
        caso = self.vista.get("caso") or {}
        medio = dict(caso.get("medio") or {})
        id = caso.get("id", "")
        medio.setdefault("imagen_recortada", f"assets/feria/pruebas/{id}_recorte.png")
        medio.setdefault("imagen_completa", f"assets/feria/pruebas/{id}_original.png")
        dialogo = DialogoPrueba(medio, self.slider_medio.value(), self.examinar.isEnabled(), parent=self)
        self.dialogo_prueba = dialogo
        dialogo.valor_cambiado.connect(self.slider_medio.setValue)
        self.slider_medio.valueChanged.connect(dialogo.establecer_valor)
        dialogo.examinar_solicitado.connect(self._examinar_ampliacion)
        dialogo.finished.connect(self._cerrar_ampliacion)
        pausa = getattr(self.window(), "pausa_dialogo", None)
        if callable(pausa):
            with pausa():
                dialogo.exec()
        else:
            dialogo.exec()

    def _examinar_ampliacion(self, valor):
        self.slider_medio.setValue(valor)
        self._examinar()

    def mostrar_aviso_prueba(self, texto):
        if self.dialogo_prueba is not None:
            self.dialogo_prueba.mostrar_estado(texto)

    def _cerrar_ampliacion(self, resultado):
        dialogo = self.dialogo_prueba
        self.dialogo_prueba = None
        if dialogo is not None:
            dialogo.deleteLater()

    def _mover_lupa(self, valor):
        medio = (self.vista.get("caso") or {}).get("medio") or {}
        objeto = {"captura": "Encuadre", "audio": "Contexto de escucha", "mapa": "Ampliación"}.get(medio.get("tipo"), "Detalle")
        self.lupa_lectura.setText(f"{objeto}: {valor} %")
        if medio.get("tipo") == "audio":
            self._actualizar_fragmento(valor)
            if self.audio.duration() > 0:
                self.audio.setPosition(round(self.audio.duration() * valor / 100))

    def _actualizar_fragmento(self, porcentaje):
        medio = (self.vista.get("caso") or {}).get("medio") or {}
        if medio.get("tipo") != "audio":
            return
        accesible = medio.get("inspeccionable") or medio.get("revelado") or medio.get("recuperado")
        fragmentos = medio.get("fragmentos", []) if accesible else []
        fragmento = next((f for f in fragmentos
                          if f.get("inicio", 0) <= porcentaje < f.get("fin", 100)
                          or porcentaje == 100 and f.get("fin") == 100), None)
        if fragmento:
            self.transcripcion.setText(fragmento.get("texto", ""))
        else:
            texto = medio.get("texto_completo") if medio.get("revelado") or medio.get("recuperado") else medio.get("texto_inicial")
            self.transcripcion.setText(texto or "No hay transcripción disponible.")

    def _entrevistar(self):
        campos = {"pregunta": self.preguntas.currentData()}
        if self.prueba_entrevista.currentData() is not None:
            campos["evidencia"] = self.prueba_entrevista.currentData()
        self._emitir("entrevistar", **campos)

    def _redactar(self, tipo):
        self._emitir(tipo, accion=self.accion.currentData(), titular=self.titular.text().strip(),
                     certeza=self.certeza.currentData(), evidencia_id=self.evidencia.currentData(),
                     contactos=list(self.contactos))

    def _actualizar_previa(self):
        accion = self.accion.currentData()
        descripcion = next((x.get("descripcion", "") for x in self.vista.get("acciones", []) if x.get("clave") == accion), "")
        self.descripcion_accion.setText(descripcion)
        titulo = self.titular.text().strip() or "Tu titular aparecerá aquí"
        caso = self.vista.get("caso") or {}
        fuente = self.evidencia.currentText() if self.evidencia.currentData() else "Ninguna prueba adjunta"
        audiencia = ", ".join(self.grafo.nodos[id].nombre if id in self.grafo.nodos else id for id in self.contactos)
        self.vista_previa.setText(f"{titulo}\n\n{self.certeza.currentText()} · {fuente}\n"
                                 f"Personaje: {caso.get('npc_nombre', 'Una voz de Ciudad Nova')}\n"
                                 f"Destinatarios: {audiencia or 'Aún sin seleccionar'}")
        if hasattr(self, "visualizador"):
            self.visualizador.tipo = "correccion" if accion in ("rectificar", "contrastar", "desmentir") else "exploracion"
            self.visualizador.update()

    def _cambiar_contacto(self, id, marcado):
        if self._actualizando:
            return
        if marcado and id not in self.contactos:
            if len(self.contactos) >= 2:
                casilla = self.casillas_contactos[id]
                casilla.blockSignals(True)
                casilla.setChecked(False)
                casilla.blockSignals(False)
                self.mensaje.setText("Elige como máximo dos contactos para esta historia.")
                self.mensaje.show()
                return
            self.contactos.append(id)
        elif not marcado and id in self.contactos:
            self.contactos.remove(id)
        self.visualizador.focos_contacto = set(self.contactos)
        self.visualizador.update()
        self.prever.setEnabled(bool(self.contactos))
        self._actualizar_previa()

    def _seleccionar_nodo(self, id):
        casilla = self.casillas_contactos.get(id)
        if casilla and casilla.isEnabled():
            casilla.toggle()
        else:
            nombre = self.grafo.nodos[id].nombre if id in self.grafo.nodos else id
            self.mensaje.setText(f"{nombre} puede recibir la historia por otros vínculos. Elige un contacto directo para comenzar.")
            self.mensaje.show()

    def _prever_alcance(self):
        self._emitir("prever_alcance", contactos=list(self.contactos))

    def _mostrar_detalles(self, visible):
        self.detalle_boton.setArrowType(Qt.ArrowType.DownArrow if visible else Qt.ArrowType.RightArrow)
        self.resultado_detalles.setVisible(visible)

    def _cargar_audio(self, ruta):
        archivo = None
        if ruta:
            candidato = Path(ruta)
            candidato = candidato if candidato.is_absolute() else RAIZ / candidato
            if candidato.is_file():
                archivo = str(candidato.resolve())
        if archivo != self._archivo_audio:
            self.audio.stop()
            self._archivo_audio = archivo
            self.audio.setSource(QUrl.fromLocalFile(archivo) if archivo else QUrl())

    def _alternar_audio(self):
        if self.audio.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.audio.pause()
        elif self._archivo_audio:
            self.video.pause()
            self.audio.play()

    def _cargar_video(self, ruta):
        archivo = None
        if ruta:
            candidato = Path(ruta)
            candidato = candidato if candidato.is_absolute() else RAIZ / candidato
            if candidato.is_file():
                archivo = str(candidato.resolve())
        if archivo != self._archivo_video:
            self.video.stop()
            self._archivo_video = archivo
            self.video.setSource(QUrl.fromLocalFile(archivo) if archivo else QUrl())
            self.video_boton.setEnabled(bool(archivo))

    def _alternar_video(self):
        if self.video.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.video.pause()
        elif self._archivo_video:
            self.audio.pause()
            self.video.play()

    def _estado_video(self, estado):
        self.video_boton.setText("Pausar el video" if estado == QMediaPlayer.PlaybackState.PlayingState else "Ver el momento")

    def _error_video(self, *args):
        self.video_boton.setEnabled(False)
        self.video_boton.setText("Continúa con el documento y la transcripción")

    def _buscar_audio(self, valor):
        self.audio.setPosition(valor)
        duracion = self.audio.duration()
        if duracion > 0:
            porcentaje = round(valor * 100 / duracion)
            bloqueadas = self.slider_medio.blockSignals(True)
            self.slider_medio.setValue(porcentaje)
            self.slider_medio.blockSignals(bloqueadas)
            self.lupa_lectura.setText(f"Contexto de escucha: {porcentaje} %")
            self._actualizar_fragmento(porcentaje)

    def _duracion_audio(self, duracion):
        self.audio_posicion.setRange(0, max(0, duracion))
        if duracion > 0:
            self.audio.setPosition(round(duracion * self.slider_medio.value() / 100))
        self._posicion_audio(self.audio.position())

    def _posicion_audio(self, posicion):
        if not self.audio_posicion.isSliderDown():
            self.audio_posicion.setValue(posicion)
        def tiempo(ms):
            minutos, segundos = divmod(max(0, ms) // 1000, 60)
            return f"{minutos}:{segundos:02d}"
        self.audio_tiempo.setText(f"{tiempo(posicion)} / {tiempo(self.audio.duration())}")
        if self.audio.duration() > 0:
            self._actualizar_fragmento(posicion * 100 / self.audio.duration())

    def _estado_audio(self, estado):
        self.audio_boton.setText("Pausar" if estado == QMediaPlayer.PlaybackState.PlayingState else "Escuchar")

    def _error_audio(self, *args):
        self.audio_boton.setEnabled(False)
        self.transcripcion_boton.setChecked(True)
        self.audio_tiempo.setText("Usa la transcripción")

    def _alternar_transcripcion(self, visible):
        medio = (self.vista.get("caso") or {}).get("medio") or {}
        if visible:
            self._actualizar_fragmento(self.slider_medio.value())
        self.transcripcion.setVisible(visible and medio.get("tipo") == "audio")

    def _cambio_pestana(self, indice):
        if indice != self._pestana_activa:
            anterior = self.tabs.widget(self._pestana_activa)
            self._scroll_guardados[self._pestana_activa] = anterior.verticalScrollBar().value()
            self._pestana_activa = indice
            self._pestana_a_restaurar = indice
            self._timer_pestana.start(0)
        if indice != 1:
            self.audio.pause()
            self.video.pause()

    def _restablecer_scroll_pestana(self):
        indice = self._pestana_a_restaurar
        if indice != self.tabs.currentIndex() or not self.tabs.isVisible():
            return
        self.tabs.tabBar().setFocus(Qt.FocusReason.OtherFocusReason)
        self.tabs.widget(indice).verticalScrollBar().setValue(self._scroll_guardados.get(indice, 0))

    def detener_audio(self):
        self.audio.stop()
        self.video.stop()

    def hideEvent(self, event):
        self.audio.pause()
        self.video.pause()
        super().hideEvent(event)

    def closeEvent(self, event):
        self._timer_entrada.stop()
        self._timer_pestana.stop()
        if self.dialogo_prueba is not None:
            self.dialogo_prueba.close()
        self.audio.stop()
        self.video.stop()
        super().closeEvent(event)
