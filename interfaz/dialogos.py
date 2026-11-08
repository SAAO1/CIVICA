"""interfaz.dialogos: presentación separada de las reglas del juego."""
import html
from PyQt6.QtCore import Qt, QRectF, QSize
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, QGridLayout, QDialog, QTextBrowser, QCheckBox, QSlider, QScrollArea, QTabWidget, QSizePolicy, QButtonGroup
from models.jugador import ROLES, ROLES_JUGABLES
from juego.acciones import acciones_para_rol
from infraestructura.recursos import pixmap_recurso
from interfaz.componentes.arte import BotonIlustrado, aplicar_estilo as _aplicar_estilo_original, dibujar_fondo, pixmap_arte, ESTILO_ARTE, FUENTE_UI, _nueve_segmentos, _caja_alfa


ESTILO = ESTILO_ARTE
for _anterior, _nuevo in (("#294c60", "#233552"), ("#477f83", "#344b73"),
                          ("#305c65", "#233b60"), ("#436d71", "#2f466a"),
                          ("#83b7ac", "#c9a86a"), ("#487978", "#344b73")):
    ESTILO = ESTILO.replace(_anterior, _nuevo)


def aplicar_estilo(widget):
    """Materiales originales con una paleta uniforme de azul marino y dorado."""
    _aplicar_estilo_original(widget)
    widget.setStyleSheet(ESTILO)


class DialogoIlustrado(QDialog):
    def ajustar_tamano(self, ancho, alto):
        """Deja espacio para la ventana y el marco en pantallas pequeñas."""
        referencia = self.parentWidget()
        disponible = referencia.size() if referencia is not None else self.screen().availableGeometry().size()
        self.resize(min(ancho, max(560, disponible.width()-80)),
                    min(alto, max(500, disponible.height()-64)))

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#182d41"))
        if dibujar_fondo(p, self.rect(), "fondos/investigacion.png"):
            p.fillRect(self.rect(), QColor(15, 31, 44, 190))
        panel = pixmap_arte("ui/panel.png")
        if not panel.isNull():
            _nueve_segmentos(p, QRectF(self.rect()).adjusted(7, 7, -7, -7), panel)
        p.end()


class _TarjetaRol(BotonIlustrado):
    """Tarjeta seleccionable con imagen, sin incrustar texto en el recurso."""
    def __init__(self, rol, parent=None):
        super().__init__("", parent, recurso="ui/panel.png")
        self.rol = rol
        self.setProperty("conservarPintura", True)
        self.setCheckable(True)
        self.setAccessibleName("Seleccionar " + ROLES[rol]["nombre"])
        self._encuadre_retrato = None
        self._retrato_escalado = None
        self.setMinimumSize(220, 260)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        retrato = pixmap_arte(f"personajes/{self.rol}_neutral.png")
        cuerpo = not retrato.isNull()
        if retrato.isNull():
            retrato = pixmap_arte(f"personajes/{self.rol}_retrato.png")
        if retrato.isNull():
            retrato = pixmap_recurso("assets/personajes/" + ("Ciudadano.png" if self.rol == "ciudadano" else "periodista.png"))
        if not retrato.isNull():
            firma = (retrato.cacheKey(), cuerpo)
            if self._encuadre_retrato is None or self._encuadre_retrato[0] != firma:
                origen = QRectF(retrato.rect())
                if cuerpo:
                    caja = _caja_alfa(retrato)
                    if not caja.isEmpty():
                        ancho = min(retrato.width(), caja.width()*1.08)
                        izquierda = max(0, min(retrato.width()-ancho, caja.center().x()-ancho/2))
                        arriba = max(0, caja.top()-caja.height()*.025)
                        alto = min(retrato.height()-arriba, caja.height()*.51)
                        origen = QRectF(izquierda, arriba, ancho, alto)
                self._encuadre_retrato = (firma, origen)
            origen = self._encuadre_retrato[1]
            limite = QRectF(25, 26, self.width()-50, self.height()-126)
            factor = min(limite.width()/origen.width(), limite.height()/origen.height())
            ancho, alto = origen.width()*factor, origen.height()*factor
            # La reducción amplia con drawPixmap usa muestreo bilineal. La
            # reducción suave previa conserva líneas y alpha sin ese moteado.
            densidad = self.devicePixelRatioF()
            tamano = QSize(max(1, round(ancho*densidad)), max(1, round(alto*densidad)))
            firma_escalada = (firma, tamano.width(), tamano.height(), densidad)
            if self._retrato_escalado is None or self._retrato_escalado[0] != firma_escalada:
                imagen = retrato.copy(origen.toAlignedRect()).scaled(
                    tamano, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                imagen.setDevicePixelRatio(densidad)
                self._retrato_escalado = (firma_escalada, imagen)
            imagen = self._retrato_escalado[1]
            p.drawPixmap(QRectF(limite.center().x()-ancho/2, limite.bottom()-alto, ancho, alto),
                         imagen, QRectF(imagen.rect()))
        p.setPen(QColor("#f7dfb5"))
        fuente = QFont(FUENTE_UI)
        fuente.setPixelSize(round(max(23, min(28, self.width()/12))))
        fuente.setWeight(QFont.Weight.DemiBold)
        p.setFont(fuente)
        p.drawText(QRectF(24, self.height()-88, self.width()-48, 34),
                   Qt.AlignmentFlag.AlignCenter, ROLES[self.rol]["nombre"])
        fuente.setPixelSize(16)
        fuente.setWeight(QFont.Weight.Normal)
        p.setFont(fuente)
        p.setPen(QColor("#d7ddec"))
        p.drawText(QRectF(24, self.height()-53, self.width()-48, 27),
                   Qt.AlignmentFlag.AlignCenter, "Seleccionado" if self.isChecked() else "Elegir personaje")
        p.end()


class DialogoRol(DialogoIlustrado):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tu papel en Ciudad Nova")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 54, 48, 40)
        layout.setSpacing(14)
        self.titulo = QLabel("TU VOZ CAMBIA LA CIUDAD")
        self.titulo.setStyleSheet("font-size: 27px; font-weight: 600; color: #f2d1a3;")
        layout.addWidget(self.titulo)
        self.subtitulo = QLabel("Cada personaje tiene cuatro decisiones propias.")
        self.subtitulo.setWordWrap(True)
        self.subtitulo.setStyleSheet("font-size: 18px;")
        layout.addWidget(self.subtitulo)
        self.roles = QComboBox()
        for id in ROLES_JUGABLES:
            rol = ROLES[id]
            self.roles.addItem(rol["nombre"], id)
        self.roles.hide()
        tarjetas = QHBoxLayout()
        tarjetas.setSpacing(22)
        self.tarjetas = {}
        self.grupo_roles = QButtonGroup(self)
        self.grupo_roles.setExclusive(True)
        for indice, id in enumerate(ROLES_JUGABLES):
            tarjeta = _TarjetaRol(id)
            tarjeta.clicked.connect(lambda _, indice=indice: self.roles.setCurrentIndex(indice))
            self.grupo_roles.addButton(tarjeta, indice)
            self.tarjetas[id] = tarjeta
            tarjetas.addWidget(tarjeta)
        layout.addLayout(tarjetas, 1)
        self.detalle = QLabel()
        self.detalle.setWordWrap(True)
        self.detalle.setMinimumHeight(36)
        self.detalle.setStyleSheet("color: #d2daeb; font-size: 17px;")
        self.roles.currentIndexChanged.connect(self.actualizar)
        layout.addWidget(self.detalle)
        boton = BotonIlustrado("Comenzar la historia →")
        boton.clicked.connect(self.accept)
        layout.addWidget(boton)
        self.actualizar()
        aplicar_estilo(self)
        disponible = parent.size() if parent is not None else self.screen().availableGeometry().size()
        ancho = 840 if disponible.width() >= 1600 else 760 if disponible.width() >= 1300 else 700
        alto = 660 if disponible.height() >= 850 else 610 if disponible.height() >= 740 else 570
        self.ajustar_tamano(ancho, alto)

    def actualizar(self):
        rol = self.roles.currentData()
        self.detalle.setText(ROLES[rol]["habilidad"])
        self.detalle.setToolTip("\n\n".join(accion["titulo"]+": "+accion["descripcion"]
                                         for accion in acciones_para_rol(rol)))
        if hasattr(self, "tarjetas"):
            self.tarjetas[rol].setChecked(True)
            for tarjeta in self.tarjetas.values():
                tarjeta.update()


def mostrar_ayuda(parent):
    reanudar = parent.pausar_lectura_modal() if hasattr(parent, "pausar_lectura_modal") else None
    dialogo = DialogoIlustrado(parent)
    dialogo.setWindowTitle("Manual de usuario · CIVICA")
    dialogo.setStyleSheet(ESTILO)
    layout = QVBoxLayout(dialogo)
    layout.setContentsMargins(48, 54, 48, 36)
    layout.setSpacing(16)
    texto = QTextBrowser()
    referencia = parent
    while referencia is not None and not hasattr(referencia, "vista_novela"):
        referencia = referencia.parentWidget()
    guia_novela = """<h3>Tu investigación en tres pasos · seis actos</h3>
    <ol><li><b>Explorar:</b> pulsa un lugar del mapa y lee la fuente que encuentres.
    Tienes dos investigaciones por caso: visitar, preguntar o guardar un hallazgo usa una.</li>
    <li><b>Señalar / escuchar:</b> arrastra el recorte o explora la transcripción.
    Abrir y observar no gasta nada; confirmar el hallazgo usa una investigación.
    Pulsa <b>Usar esta prueba</b> para adjuntarla a tu respuesta.</li>
    <li><b>Decidir:</b> elige qué harás con el mensaje y confirma. La prueba que usaste
    queda adjunta. Tu oficio determina las decisiones que puedes tomar.</li></ol>
    <p>El balance muestra todos los indicadores y tus puntos juntos en 1,2 segundos.
    La explicación se narra automáticamente sobre la escena.
    <b>Espacio, Enter o clic continúa inmediatamente, incluso mientras habla.</b>
    Después revisa el Archivo (árbol)
    y la Red (grafo) antes de pasar al siguiente acto.</p>""" if referencia is not None else ""
    acciones_html = "".join("<h3>"+html.escape(ROLES[rol]["nombre"])+"</h3><ul>"+
                            "".join("<li><b>"+html.escape(accion["titulo"])+":</b> "+
                                    html.escape(accion["descripcion"])+"</li>"
                                    for accion in acciones_para_rol(rol))+"</ul>"
                            for rol in ROLES_JUGABLES)
    texto.setHtml("""<h2>Construye una Ciudad Nova informada</h2>""" + guia_novela + """
    <p>Cuida la confianza, la convivencia y el bienestar antes de la elección.</p>
    <p><b>Espacio, Enter o clic:</b> revelar el texto; otra interacción continúa.
    Tab y Enter permiten seleccionar botones. F11 cambia la pantalla; F1 abre este manual.
    El engranaje de la esquina superior derecha abre Configuración.</p>
    <p>Los siete indicadores y tus puntos se muestran juntos sobre la escena
    mientras el narrador explica lo ocurrido. Espacio, Enter o clic continúa sin esperar a la voz.
    El manual pausa la presentación.</p>
    <p>Ciudadano y periodista tienen cuatro decisiones distintas. En multijugador,
    cada persona actúa con las opciones de su oficio.</p>""" + acciones_html + """
    <p>El influencer y los candidatos pertenecen a la historia.</p>
    <p>Los puntos y la reputación son individuales. Los indicadores pertenecen a toda la ciudad.
    Tus acciones influyen en el apoyo de cuatro candidatos ficticios y en el final narrativo.</p>
    <p><b>Observatorio:</b> conversar y entrevistar destacan los contactos y las conexiones
    nuevas con arcos dorados de puntos y rayas. No se confunden con una difusión ni con
    una verificación. <b>Comparar alcance</b> muestra cuántas personas serían alcanzadas
    con esos vínculos y sin ellos, sin reenviar la publicación ni cambiar tus puntos.</p>
    <p>La difusión avanza automáticamente a un ritmo fijo y se repite
    dos segundos después de terminar. BFS explora por niveles; DFS sigue cada cadena de conexiones.
    Selecciona un ciudadano de origen y usa <b>Comparar alcance</b> para simular desde esa persona
    sin cambiar tus puntos ni aplicar otra decisión.</p>
    <p><b>Una comunidad que crece:</b> nuevos ciudadanos y sus conexiones se incorporan
    a medida que avanza la historia. El observatorio anuncia sus nombres y los marca con un aro punteado.
    Selecciona un retrato para consultar sus conexiones.</p>
    <p>En las alertas urgentes, al agotarse el tiempo el ciudadano sigue sin reenviar y la
    periodista mantiene la información en reserva. Puedes desactivar el límite
    o reducir movimiento desde Configuración; al reducirlo, el observatorio muestra el recorrido completo
    sin repetir la animación. También puedes adaptar los colores al daltonismo, activar alto contraste
    y ajustar por separado las voces de los personajes y del narrador. Toda señal sonora importante
    tiene texto visible.</p>
    <p>En multijugador, espera tu turno. El servidor conserva el estado y sincroniza las decisiones.</p>""")
    texto.append("""<h3>Tu cuaderno de Ciudad Nova</h3>
    <p><b>Cuaderno:</b> consulta fuentes de cada caso, perfiles de los protagonistas,
    diálogos leídos, galería y glosario. <b>Examinar las fuentes</b> abre documentos
    ficticios de la historia; tú eliges después qué hacer con la publicación.
    Las alertas con tiempo continúan mientras el cuaderno está abierto.</p>
    <p><b>Historial:</b> vuelve a leer los diálogos completos de esta sesión.
    <b>Auto:</b> avanza el texto hasta una decisión. <b>Saltar leído:</b> avanza sólo
    las líneas que ya terminaste de leer y se detiene ante contenido nuevo.
    La velocidad de escritura se ajusta en Configuración, incluida la lectura instantánea.</p>
    <p>La galería conserva escenas desbloqueadas en este equipo. Repetir la historia
    con otras decisiones muestra reacciones y epílogos diferentes.</p>""")
    layout.addWidget(texto)
    cerrar = QPushButton("Volver")
    cerrar.clicked.connect(dialogo.accept)
    layout.addWidget(cerrar)
    dialogo.resize(640, 550)
    aplicar_estilo(dialogo)
    try:
        dialogo.exec()
    finally:
        if reanudar is not None:
            reanudar()


def mostrar_configuracion(parent):
    from infraestructura.configuracion import guardar
    reanudar_lectura = parent.pausar_lectura_modal() if hasattr(parent, "pausar_lectura_modal") else None
    dialogo = DialogoIlustrado(parent)
    dialogo.setWindowTitle("Configuración y accesibilidad")
    dialogo.setStyleSheet(ESTILO)
    layout = QVBoxLayout(dialogo)
    layout.setContentsMargins(48, 54, 48, 36)
    layout.setSpacing(14)
    titulo = QLabel("TU EXPERIENCIA EN CIVICA")
    titulo.setStyleSheet("font-size: 24px; color: #f2d1a3; font-weight: 600;")
    layout.addWidget(titulo)
    pestanas = QTabWidget()
    pestanas.setAccessibleName("Categorías de configuración")
    layout.addWidget(pestanas, 1)
    accesibilidad = QWidget()
    opciones = QVBoxLayout(accesibilidad)
    opciones.setContentsMargins(16, 18, 16, 14)
    opciones.setSpacing(14)
    colores = QLabel("Colores para daltonismo")
    opciones.addWidget(colores)
    daltonismo = QComboBox()
    daltonismo.setAccessibleName("Modo de colores para daltonismo")
    daltonismo.setMinimumHeight(42)
    for nombre, clave in (("Colores originales", "normal"),
                          ("Deuteranopia · dificultad con el verde", "deuteranopia"),
                          ("Protanopia · dificultad con el rojo", "protanopia"),
                          ("Tritanopia · dificultad con el azul", "tritanopia")):
        daltonismo.addItem(nombre, clave)
    daltonismo.setCurrentIndex(max(0, daltonismo.findData(getattr(parent, "modo_daltonismo", "normal"))))
    opciones.addWidget(daltonismo)
    ayuda_color = QLabel("Los estados también usan texto, símbolos y distintos trazos para poder reconocerlos sin depender del color.")
    ayuda_color.setWordWrap(True)
    ayuda_color.setStyleSheet("color: #c2d3c9; font-size: 14px;")
    opciones.addWidget(ayuda_color)
    controles = {}
    for clave, texto, valor in (("sin_limite", "Decisiones sin límite de tiempo", parent.sin_limite),
                                ("reducir_movimiento", "Reducir movimiento y evitar recorridos repetidos", parent.reducir_movimiento),
                                ("alto_contraste", "Alto contraste", parent.alto_contraste)):
        check = QCheckBox(texto)
        check.setChecked(valor)
        if clave == "sin_limite" and getattr(parent, "cliente_red", None) is not None:
            check.setEnabled(False)
            check.setToolTip("En cooperación el anfitrión fija el tiempo para toda la sala antes de comenzar.")
        controles[clave] = check
        opciones.addWidget(check)
    opciones.addStretch()
    pestanas.addTab(accesibilidad, "Accesibilidad")
    lectura = QWidget()
    lectura_layout = QVBoxLayout(lectura)
    lectura_layout.setContentsMargins(16, 18, 16, 14)
    lectura_layout.addWidget(QLabel("Velocidad del texto de los diálogos"))
    velocidad_texto = QComboBox()
    velocidad_texto.setAccessibleName("Velocidad de lectura")
    for etiqueta, milisegundos in (("Pausada", 50), ("Normal", 34), ("Ágil", 16), ("Instantánea", 0)):
        velocidad_texto.addItem(etiqueta, milisegundos)
    velocidad_texto.setCurrentIndex(max(0, velocidad_texto.findData(getattr(parent, "velocidad_texto", 34))))
    lectura_layout.addWidget(velocidad_texto)
    ayuda_lectura = QLabel("Espacio o Enter revela la línea completa. Auto avanza los diálogos y Saltar leído se detiene ante una línea nueva. Ambos se detienen al cambiar de escena; las decisiones siempre las tomas tú.")
    ayuda_lectura.setWordWrap(True)
    lectura_layout.addWidget(ayuda_lectura)
    lectura_layout.addStretch()
    pestanas.addTab(lectura, "Lectura")
    visual = QWidget()
    visual_layout = QVBoxLayout(visual)
    visual_layout.setContentsMargins(16, 18, 16, 14)
    for clave, etiqueta in (("animar_fondos", "Fondos vivos: clima, luces y movimiento de cámara"),
                            ("animar_personajes", "Personajes: respiración, parpadeo y gestos al hablar")):
        check = QCheckBox(etiqueta)
        check.setChecked(getattr(parent, clave, True))
        controles[clave] = check
        visual_layout.addWidget(check)
    detalle_visual = QLabel("Reducir movimiento tiene prioridad y deja la escena quieta. Puedes mantener las voces y los ambientes sonoros con cualquiera de estas opciones.")
    detalle_visual.setWordWrap(True)
    visual_layout.addWidget(detalle_visual)
    visual_layout.addStretch()
    pestanas.addTab(visual, "Escenas")
    sonido = QWidget()
    audio_layout = QVBoxLayout(sonido)
    audio_layout.setContentsMargins(16, 18, 16, 14)
    audio_layout.setSpacing(14)
    silenciado = QCheckBox("Silenciar todo el audio")
    silenciado.setChecked(parent.audio.silenciado)
    controles["silenciado"] = silenciado
    audio_layout.addWidget(silenciado)
    voces = QCheckBox("Voces de los personajes y del narrador")
    voces.setChecked(getattr(parent, "voces_activadas", True))
    voces.setEnabled(hasattr(parent.audio, "configurar_voces"))
    audio_layout.addWidget(voces)
    if hasattr(parent.audio, "descripcion_voces"):
        estado_voces = QLabel(parent.audio.descripcion_voces())
        estado_voces.setWordWrap(True)
        estado_voces.setStyleSheet("font-size: 13px; color: #c2d3c9;")
        audio_layout.addWidget(estado_voces)
    muestras = QHBoxLayout()
    ejemplos = (("Ciudadano", "CIUDADANO", "Mi hermana estudia en ese colegio. Si lo cierran, ¿a dónde va a ir?"),
                ("Periodista", "PERIODISTA", "Entiendo la urgencia. Antes de avisar a las familias, necesitamos el comunicado completo."),
                ("Narrador", "NARRADOR", "Una notificación interrumpe la mañana. El ciudadano deja el café sin probar."))
    for etiqueta, hablante, texto_muestra in ejemplos:
        boton_muestra = QPushButton("Probar " + etiqueta)
        boton_muestra.setToolTip("Escuchar el doblaje de " + etiqueta.lower())
        boton_muestra.clicked.connect(lambda _, h=hablante, t=texto_muestra: parent.audio.narrar(t, h) if voces.isChecked() else None)
        muestras.addWidget(boton_muestra)
    audio_layout.addLayout(muestras)
    nuevos = QHBoxLayout()
    selector_voz = QComboBox()
    selector_voz.setAccessibleName("Personaje de los nuevos actos")
    from juego.campana_extendida import FRASES_POSIBLES
    for clave, etiqueta in (("INFLUENCER", "Valeria Cruz"), ("JUAN", "Juan Torres"),
                             ("ADRIAN", "Adrián Morales"), ("LAURA", "Laura Ríos"),
                             ("CAMILA", "Camila Vega")):
        muestra = next(texto for hablante, texto in FRASES_POSIBLES if hablante == clave)
        selector_voz.addItem(etiqueta, (clave, muestra))
    nuevos.addWidget(selector_voz, 1)
    probar_nueva = QPushButton("Escuchar personaje")
    def escuchar_nuevo():
        hablante, texto = selector_voz.currentData()
        if voces.isChecked():
            parent.audio.narrar(texto, hablante)
    probar_nueva.clicked.connect(escuchar_nuevo)
    nuevos.addWidget(probar_nueva)
    audio_layout.addLayout(nuevos)
    for categoria, volumen in parent.audio.volumenes.items():
        fila = QHBoxLayout()
        etiqueta = QLabel("Volumen " + ("de voces" if categoria == "voces" else categoria))
        etiqueta.setMinimumWidth(155)
        fila.addWidget(etiqueta)
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setAccessibleName(etiqueta.text())
        slider.setRange(0, 100)
        slider.setValue(round(volumen*100))
        numero = QLabel(str(slider.value()) + "%")
        numero.setMinimumWidth(45)
        slider.valueChanged.connect(lambda valor, categoria=categoria: parent.audio.configurar(categoria, valor/100))
        slider.valueChanged.connect(lambda valor, numero=numero: numero.setText(str(valor) + "%"))
        fila.addWidget(slider, 1)
        fila.addWidget(numero)
        audio_layout.addLayout(fila)
    audio_layout.addStretch()
    sonido_area = QScrollArea()
    sonido_area.setWidgetResizable(True)
    sonido_area.viewport().setAutoFillBackground(False)
    sonido.setStyleSheet("background:#182d41;")
    sonido_area.setWidget(sonido)
    pestanas.addTab(sonido_area, "Sonido y voces")
    manual = BotonIlustrado("Manual de usuario")
    manual.setToolTip("Controles, decisiones y reglas del juego · F1")
    manual.clicked.connect(lambda: mostrar_ayuda(dialogo))
    layout.addWidget(manual)

    def aplicar():
        parent.audio.silenciar(controles["silenciado"].isChecked())
        parent.sin_limite = controles["sin_limite"].isChecked()
        parent.reducir_movimiento = controles["reducir_movimiento"].isChecked()
        parent.alto_contraste = controles["alto_contraste"].isChecked()
        parent.modo_daltonismo = daltonismo.currentData()
        parent.voces_activadas = voces.isChecked()
        parent.velocidad_texto = velocidad_texto.currentData()
        parent.animar_fondos = controles["animar_fondos"].isChecked()
        parent.animar_personajes = controles["animar_personajes"].isChecked()
        if hasattr(parent.audio, "configurar_voces"):
            parent.audio.configurar_voces(parent.voces_activadas)
        parent.aplicar_accesibilidad()
        guardar({"volumenes": parent.audio.volumenes, "silenciado": parent.audio.silenciado,
                 "sin_limite": parent.sin_limite, "reducir_movimiento": parent.reducir_movimiento,
                 "alto_contraste": parent.alto_contraste,
                 "modo_daltonismo": parent.modo_daltonismo,
                 "voces_activadas": parent.voces_activadas,
                 "velocidad_texto": parent.velocidad_texto,
                 "animar_fondos": parent.animar_fondos,
                 "animar_personajes": parent.animar_personajes,
                 "sprites_sobre_ilustracion": parent.sprites_sobre_ilustracion})
        dialogo.accept()
    boton = BotonIlustrado("Guardar preferencias")
    boton.clicked.connect(aplicar)
    layout.addWidget(boton)
    dialogo.resize(720, 670)
    aplicar_estilo(dialogo)
    try:
        dialogo.exec()
    finally:
        if reanudar_lectura is not None:
            reanudar_lectura()


class DialogoRed(DialogoIlustrado):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("CIVICA · Sala local")
        self.setStyleSheet(ESTILO)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 54, 48, 36)
        layout.setSpacing(12)
        titulo = QLabel("UNA CIUDAD, VARIAS VOCES")
        titulo.setStyleSheet("font-size: 21px; color: #f2d1a3; font-weight: 600;")
        layout.addWidget(titulo)
        self.nombre = QLineEdit("Alex")
        self.nombre.setMaxLength(30)
        self.host = QLineEdit("127.0.0.1")
        self.puerto = QLineEdit("8765")
        self.rol = QComboBox()
        for id in ROLES_JUGABLES:
            datos = ROLES[id]
            self.rol.addItem(datos["nombre"], id)
        campos = QGridLayout()
        campos.setHorizontalSpacing(16)
        campos.setVerticalSpacing(8)
        for fila, (titulo, widget) in enumerate((("Tu nombre", self.nombre), ("Personaje", self.rol),
                                                ("Servidor", self.host), ("Puerto", self.puerto))):
            campos.addWidget(QLabel(titulo), fila, 0)
            campos.addWidget(widget, fila, 1)
        layout.addLayout(campos)
        fila = QHBoxLayout()
        for titulo, crear in (("Crear sala local", True), ("Unirse", False)):
            boton = QPushButton(titulo)
            boton.clicked.connect(lambda _, crear=crear: self.conectar(crear))
            fila.addWidget(boton)
        layout.addLayout(fila)
        self.estado = QLabel("Dos a cuatro participantes. Puedes elegir ciudadano o periodista; los personajes se pueden repetir.")
        self.estado.setWordWrap(True)
        layout.addWidget(self.estado)
        iniciar = QPushButton("Iniciar campaña (anfitrión)")
        iniciar.clicked.connect(lambda: parent.cliente_red.enviar({"tipo": "iniciar"}) if parent.cliente_red else None)
        layout.addWidget(iniciar)
        aplicar_estilo(self)
        self.resize(650, 530)

    def conectar(self, crear):
        try:
            puerto = int(self.puerto.text())
            if not 1 <= puerto <= 65535:
                raise ValueError("Puerto fuera de rango")
            self.parent().conectar_red(crear, self.host.text().strip(), puerto,
                                      self.nombre.text().strip(), self.rol.currentData())
            self.estado.setText("Conectando…")
        except (OSError, ValueError) as error:
            self.estado.setText(str(error))
