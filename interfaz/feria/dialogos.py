"""Ayuda, preferencias e inspección de una instantánea de la partida de feria.

Los diálogos no escriben configuración ni mutan la sesión. El observatorio
ejecuta las estructuras propias sobre una copia pública de su estado.
"""
from copy import deepcopy
from pathlib import Path

from PyQt6.QtCore import QSize, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QMovie, QPixmap
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton,
    QScrollArea, QSlider, QSplitter, QStackedWidget, QTabWidget, QTextBrowser,
    QVBoxLayout, QWidget,
)

from estructuras.bst import ArbolPublicaciones
from estructuras.grafo import Grafo
from infraestructura.recursos import RAIZ
from interfaz.componentes.arbol import VisualizadorBSTBonito
from interfaz.componentes.arte import cargar_tipografias
from interfaz.componentes.grafo import VisualizadorGrafo
from interfaz.feria.estilos import ESTILO_FERIA
from models.publicacion import Publicacion


def _texto(texto="", nombre=None):
    etiqueta = QLabel(str(texto))
    etiqueta.setWordWrap(True)
    etiqueta.setTextFormat(Qt.TextFormat.PlainText)
    etiqueta.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    if nombre:
        etiqueta.setObjectName(nombre)
    return etiqueta


def _boton(texto, callback):
    boton = QPushButton(texto)
    boton.clicked.connect(callback)
    return boton


def _pagina():
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    cuerpo = QWidget()
    contenido = QVBoxLayout(cuerpo)
    contenido.setContentsMargins(5, 12, 14, 12)
    contenido.setSpacing(16)
    area.setWidget(cuerpo)
    return area, contenido


def _bloque(titulo, texto):
    marco = QFrame()
    marco.setObjectName("tarjeta")
    contenido = QVBoxLayout(marco)
    contenido.setContentsMargins(18, 15, 18, 16)
    contenido.addWidget(_texto(titulo, "ceja"))
    contenido.addWidget(_texto(texto))
    return marco


class _DialogoFeria(QDialog):
    def __init__(self, titulo, descripcion, parent=None):
        super().__init__(parent)
        cargar_tipografias()
        self.setWindowTitle(titulo + " · CIVICA")
        self.setObjectName("tableroInvestigacion")
        self._preferencias = dict(getattr(parent, "preferencias", {}))
        tamano = self._preferencias.get("tamano_texto", 16)
        estilo = ESTILO_FERIA.replace("font-size: 16px", f"font-size: {tamano}px")
        if self._preferencias.get("alto_contraste"):
            estilo = estilo.replace("#142936", "#070e15").replace("#f8edda", "#ffffff")
            estilo = estilo.replace("#cbd5d8", "#ffffff").replace("#223d4d", "#111c27")
        self.setStyleSheet(estilo)
        self.resize(1040, 680)
        self.setMinimumSize(780, 500)
        self.contenido = QVBoxLayout(self)
        self.contenido.setContentsMargins(22, 18, 22, 16)
        self.contenido.setSpacing(11)
        self.contenido.addWidget(_texto(titulo, "tituloCaso"))
        self.contenido.addWidget(_texto(descripcion, "subtitulo"))

    def _cerrar(self):
        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        botones.button(QDialogButtonBox.StandardButton.Close).setText("Volver a la historia")
        botones.rejected.connect(self.reject)
        self.contenido.addWidget(botones)


class DialogoAjustes(_DialogoFeria):
    """Devuelve preferencias al propietario mediante cambios; nunca las guarda."""

    cambios = pyqtSignal(dict)

    def __init__(self, preferencias, parent=None):
        super().__init__("A tu ritmo", "Ajusta la lectura y el sonido para seguir la investigación con comodidad.", parent)
        self.preferencias = dict(preferencias)
        pagina, contenido = _pagina()
        formulario = QFormLayout()
        formulario.setHorizontalSpacing(25)
        formulario.setVerticalSpacing(18)
        self.sonido = QCheckBox("Activar el sonido")
        self.sonido.setChecked(bool(preferencias.get("sonido", True)))
        self.volumen = QSlider(Qt.Orientation.Horizontal)
        self.volumen.setRange(0, 100)
        self.volumen.setAccessibleName("Volumen general")
        volumen = preferencias.get("volumen", 65)
        self.volumen.setValue(max(0, min(100, int(volumen))))
        self.volumen_valor = _texto(f"{self.volumen.value()} %")
        volumen_panel = QWidget()
        volumen_layout = QHBoxLayout(volumen_panel)
        volumen_layout.setContentsMargins(0, 0, 0, 0)
        volumen_layout.addWidget(self.volumen, 1)
        volumen_layout.addWidget(self.volumen_valor)
        self.volumen.valueChanged.connect(lambda valor: self.volumen_valor.setText(f"{valor} %"))
        self.sonido.toggled.connect(self.volumen.setEnabled)
        self.volumen.setEnabled(self.sonido.isChecked())
        self.tamano_texto = QComboBox()
        self.tamano_texto.setAccessibleName("Tamaño del texto")
        for tamano, nombre in ((14, "Compacto · 14"), (16, "Habitual · 16"), (18, "Grande · 18"), (20, "Muy grande · 20")):
            self.tamano_texto.addItem(nombre, tamano)
        indice = self.tamano_texto.findData(preferencias.get("tamano_texto", 16))
        self.tamano_texto.setCurrentIndex(indice if indice >= 0 else 1)
        self.contraste = QCheckBox("Usar contraste alto")
        self.contraste.setChecked(bool(preferencias.get("alto_contraste", False)))
        self.movimiento = QCheckBox("Reducir los movimientos y las transiciones")
        self.movimiento.setChecked(bool(preferencias.get("reducir_movimiento", False)))
        self.sin_limite = QCheckBox("Decidir sin límite de tiempo")
        self.sin_limite.setChecked(bool(preferencias.get("sin_limite", False)))
        if getattr(parent, "cliente_red", None) is not None:
            self.sin_limite.setEnabled(False)
            self.sin_limite.setToolTip("El plazo común se configura en la sala antes de comenzar")
        self.narracion = QCheckBox("Escuchar la narración cuando esté disponible")
        self.narracion.setChecked(bool(preferencias.get("narracion", True)))
        formulario.addRow("Sonido", self.sonido)
        formulario.addRow("Volumen", volumen_panel)
        formulario.addRow("Lectura", self.tamano_texto)
        formulario.addRow("Contraste", self.contraste)
        formulario.addRow("Movimiento", self.movimiento)
        formulario.addRow("Tiempo", self.sin_limite)
        formulario.addRow("Narración", self.narracion)
        contenido.addLayout(formulario)
        self.muestra = _bloque("VISTA PREVIA", "Una duda bien contada también cuida a la ciudad. Puedes leer con calma y volver a tus fuentes.")
        contenido.addWidget(self.muestra)
        contenido.addWidget(_texto("En una sala cooperativa, el plazo de la decisión lo coordina la persona que creó la sala.", "subtitulo"))
        contenido.addStretch()
        self.contenido.addWidget(pagina, 1)
        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Apply)
        botones.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botones.button(QDialogButtonBox.StandardButton.Apply).setText("Aplicar ajustes")
        botones.rejected.connect(self.reject)
        botones.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.aplicar)
        self.contenido.addWidget(botones)
        self.tamano_texto.currentIndexChanged.connect(self._previsualizar)
        self.contraste.toggled.connect(self._previsualizar)
        self._previsualizar()

    def _previsualizar(self, *args):
        estilo = ESTILO_FERIA.replace("font-size: 16px", f"font-size: {self.tamano_texto.currentData()}px")
        if self.contraste.isChecked():
            estilo = estilo.replace("#142936", "#070e15").replace("#f8edda", "#ffffff")
            estilo = estilo.replace("#cbd5d8", "#ffffff").replace("#223d4d", "#111c27")
        self.setStyleSheet(estilo)

    def aplicar(self):
        self.preferencias.update(
            sonido=self.sonido.isChecked(), volumen=self.volumen.value(),
            tamano_texto=self.tamano_texto.currentData(), alto_contraste=self.contraste.isChecked(),
            reducir_movimiento=self.movimiento.isChecked(), sin_limite=self.sin_limite.isChecked(),
            narracion=self.narracion.isChecked(),
        )
        self.cambios.emit(dict(self.preferencias))
        self.accept()


class DialogoAyuda(_DialogoFeria):
    def __init__(self, parent=None):
        super().__init__("Antes de compartir", "Investiga lo que falta, elige cómo contarlo y cuida los vínculos de Ciudad Nova.", parent)
        pestañas = QTabWidget()
        pagina, contenido = _pagina()
        for titulo, texto in (
            ("1 · ESCUCHA EL CASO", "Seis casos forman tres capítulos. Lee el mensaje que circula y el objetivo; una captura o un audio pueden dejar fuera su contexto."),
            ("2 · ELIGE DOS COMPROBACIONES", "Cada persona tiene dos acciones por caso. Visitar el archivo, el barrio o la redacción, recuperar un medio y entrevistar consumen oportunidades cuando obtienes un hallazgo. No hace falta gastar ambas para decidir."),
            ("3 · RECUPERA UNA PRUEBA", "En Expediente, arrastra el divisor de una imagen o busca un tramo del audio y pulsa Examinar. Una entrevista permite elegir una pregunta y presentar una prueba. Las pistas propias y las que te compartieron quedan en tu mesa."),
            ("4 · CUENTA LO QUE PUEDES SOSTENER", "En Redacción elige tu acción, escribe un titular y distingue lo pendiente, lo probable y lo confirmado. Adjunta una evidencia pertinente: una certeza sin respaldo también tiene consecuencias."),
            ("5 · PIENSA EN QUIÉN LO RECIBE", "En Audiencia elige uno o dos contactos directos y prevé la circulación. Si un rumor ya hizo daño, una corrección necesita llegar a las personas que lo recibieron. La reacción de la ciudad muestra qué cambió."),
        ):
            contenido.addWidget(_bloque(titulo, texto))
        contenido.addStretch()
        pestañas.addTab(pagina, "Primeros pasos")
        pagina, contenido = _pagina()
        contenido.addWidget(_bloque("DOS MIRADAS, UNA INVESTIGACIÓN", "En cooperación LAN juegan dos personas: un Ciudadano y una Periodista. Cada rol tiene fuentes y acciones propias; no se repiten dentro de la sala."))
        contenido.addWidget(_bloque("PISTAS QUE NO VIAJAN SOLAS", "Ver que tu compañero encontró una pista no revela su contenido. Pídesela y espera a que la comparta. Puedes compartir un borrador para comparar titulares y grados de certeza antes de publicar."))
        contenido.addWidget(_bloque("DECIDIR Y VOLVER A LEER", "Primero decide el Ciudadano; después, la Periodista. Mientras esperas puedes preparar tu trabajo. Para pasar de una reacción al siguiente caso, ambos confirman que terminaron de leer."))
        contenido.addWidget(_bloque("UNIRSE A LA SALA", "La persona anfitriona crea la sala y comunica su dirección local y puerto. La segunda persona se conecta desde la misma red. Si se pierde la conexión, usa Reconectar y conserva la misma ventana."))
        contenido.addStretch()
        pestañas.addTab(pagina, "En pareja")
        pagina, contenido = _pagina()
        contenido.addWidget(_bloque("LECTURA Y SONIDO", "En Ajustes puedes cambiar el tamaño del texto, subir el contraste, reducir el movimiento, silenciar el sonido y jugar sin límite. Los audios tienen transcripción; los videos se pueden pausar y nunca bloquean una decisión."))
        contenido.addWidget(_bloque("TECLADO", "Tab / Mayús+Tab: moverte entre controles.\nEnter o Espacio: activar el control elegido.\nFlechas: ajustar el divisor y los controles deslizantes.\nAlt+1…4: cambiar entre las cuatro pestañas.\nEscape: cerrar un diálogo; en la historia abre los ajustes."))
        contenido.addWidget(_bloque("VOLVER A TUS FUENTES", "F1: ayuda.\nF2: observatorio del grafo y del árbol.\nF3: historial de la investigación.\nF11: pantalla completa.\nCtrl+S / Ctrl+O: guardar o abrir una partida individual."))
        contenido.addStretch()
        pestañas.addTab(pagina, "A tu ritmo")
        self.galeria = GaleriaRecursos(self)
        pestañas.addTab(self.galeria, "La ciudad")
        self.contenido.addWidget(pestañas, 1)
        self._cerrar()

    def done(self, resultado):
        self.galeria.detener()
        super().done(resultado)


class DialogoObservatorio(_DialogoFeria):
    """Inspección de estructuras propias sin modificar puntos ni relaciones."""

    def __init__(self, vista, parent=None):
        super().__init__("Cómo se conecta la ciudad", "Explora las conexiones y el índice de publicaciones de esta partida. Estos recorridos son consultas.", parent)
        self.vista = deepcopy(vista)
        self.grafo = Grafo()
        red = self.vista.get("red") or {}
        for nodo in red.get("nodos", []):
            self.grafo.agregar_vertice(nodo["id"], nodo.get("nombre", nodo["id"]))
        for origen, destino in red.get("aristas", []):
            self.grafo.agregar_arista(origen, destino)
        self.arbol = ArbolPublicaciones()
        self.forma_disponible = isinstance(self.vista.get("archivo_preorden"), list)
        if self.forma_disponible:
            entradas = self.vista["archivo_preorden"]
            ids = [entrada["id"] for entrada in entradas]
            if len(ids) != len(set(ids)):
                self.forma_disponible = False
            else:
                for entrada in entradas:
                    publicacion = Publicacion(entrada["id"], entrada.get("texto", ""), None, 0)
                    publicacion.estado = entrada.get("estado", "ACTIVA")
                    self.arbol.insertar(publicacion)
                self.forma_disponible = [p.id for p in self.arbol.preorden()] == ids
        pestañas = QTabWidget()
        self._crear_grafo(pestañas)
        self._crear_arbol(pestañas)
        self.contenido.addWidget(pestañas, 1)
        self._cerrar()

    def _crear_grafo(self, pestañas):
        pagina, contenido = _pagina()
        self.visualizador_grafo = VisualizadorGrafo(self.grafo)
        self.visualizador_grafo.setMinimumHeight(335)
        self.visualizador_grafo.nodo_seleccionado.connect(self._seleccionar_origen)
        contenido.addWidget(self.visualizador_grafo)
        fila = QHBoxLayout()
        fila.addWidget(_texto("Comenzar en"))
        self.origen = QComboBox()
        self.origen.setAccessibleName("Persona desde la que recorrer la red")
        for id, nodo in self.grafo.nodos.items():
            self.origen.addItem(nodo.nombre, id)
        fila.addWidget(self.origen, 1)
        self.boton_bfs = _boton("BFS · por niveles", lambda: self.recorrer_grafo("bfs"))
        self.boton_dfs = _boton("DFS · en profundidad", lambda: self.recorrer_grafo("dfs"))
        self.boton_bfs.setEnabled(bool(self.grafo.nodos))
        self.boton_dfs.setEnabled(bool(self.grafo.nodos))
        fila.addWidget(self.boton_bfs)
        fila.addWidget(self.boton_dfs)
        contenido.addLayout(fila)
        self.recorrido_grafo = _texto("Selecciona una persona y elige un recorrido. Las flechas conservan la dirección real de cada conexión.")
        contenido.addWidget(self.recorrido_grafo)
        contenido.addWidget(_texto("La exploración completa permite comparar algoritmos; la difusión de cada decisión utiliza su audiencia y sus límites propios.", "subtitulo"))
        contenido.addStretch()
        pestañas.addTab(pagina, "Red social")

    def _seleccionar_origen(self, id):
        indice = self.origen.findData(id)
        if indice >= 0:
            self.origen.setCurrentIndex(indice)

    def recorrer_grafo(self, algoritmo):
        origen = self.origen.currentData()
        if origen not in self.grafo.nodos:
            return
        if algoritmo == "bfs":
            resultado = self.grafo.bfs(origen)
            orden = resultado.orden
            self.visualizador_grafo.aristas_usadas = set(resultado.aristas)
            niveles = ["Nivel " + str(i) + ": " + ", ".join(self.grafo.nodos[id].nombre for id in nivel)
                       for i, nivel in enumerate(resultado.niveles)]
            explicacion = "BFS recorre primero las personas más cercanas.\n" + "\n".join(niveles)
        elif algoritmo == "dfs":
            orden = self.grafo.dfs(origen)
            self.visualizador_grafo.aristas_usadas = set()
            explicacion = "DFS sigue una rama antes de regresar. No garantiza un camino mínimo."
        else:
            raise ValueError("Recorrido de grafo desconocido")
        self.visualizador_grafo.emisor = origen
        self.visualizador_grafo.visitados = set(orden)
        self.visualizador_grafo.update()
        self.recorrido_grafo.setText(" → ".join(self.grafo.nodos[id].nombre for id in orden) + "\n\n" + explicacion)

    def _crear_arbol(self, pestañas):
        pagina, contenido = _pagina()
        self.visualizador_arbol = VisualizadorBSTBonito(self.arbol)
        self.visualizador_arbol.setMinimumHeight(290)
        self.visualizador_arbol.setVisible(self.forma_disponible)
        contenido.addWidget(self.visualizador_arbol)
        self.aviso_arbol = _texto(
            "La forma conserva el recorrido preorden recibido de la partida. Las publicaciones retiradas ya no pertenecen al índice activo."
            if self.forma_disponible else
            "Esta vista incluye el catálogo de publicaciones, pero no su preorden. Se muestra la lista; la forma del árbol no está disponible.", "subtitulo")
        contenido.addWidget(self.aviso_arbol)
        fila = QHBoxLayout()
        self.botones_arbol = {}
        for clave, texto in (("inorden", "Inorden"), ("preorden", "Preorden"), ("postorden", "Postorden")):
            boton = _boton(texto, lambda checked=False, clave=clave: self.recorrer_arbol(clave))
            boton.setEnabled(self.forma_disponible)
            self.botones_arbol[clave] = boton
            fila.addWidget(boton)
        contenido.addLayout(fila)
        self.recorrido_arbol = _texto()
        contenido.addWidget(self.recorrido_arbol)
        busqueda = QHBoxLayout()
        self.id_busqueda = QLineEdit()
        self.id_busqueda.setPlaceholderText("ID de una publicación")
        self.id_busqueda.setAccessibleName("Identificador que buscar en el árbol")
        self.id_busqueda.setMaximumWidth(240)
        self.id_busqueda.returnPressed.connect(self.buscar_publicacion)
        boton_buscar = _boton("Buscar en el árbol", self.buscar_publicacion)
        self.id_busqueda.setEnabled(self.forma_disponible)
        boton_buscar.setEnabled(self.forma_disponible)
        busqueda.addWidget(self.id_busqueda)
        busqueda.addWidget(boton_buscar)
        busqueda.addStretch()
        contenido.addLayout(busqueda)
        self.archivo_lista = QTextBrowser()
        self.archivo_lista.setMinimumHeight(150)
        archivo = self.vista.get("archivo", self.vista.get("archivo_preorden", []))
        self.archivo_lista.setPlainText("\n\n".join(f"#{x['id']} · {x.get('estado', 'ACTIVA')}\n{x.get('texto', '')}" for x in archivo)
                                        or "No hay publicaciones activas en este índice.")
        contenido.addWidget(self.archivo_lista)
        contenido.addStretch()
        pestañas.addTab(pagina, "Árbol de publicaciones")

    def recorrer_arbol(self, recorrido):
        if not self.forma_disponible:
            return
        if recorrido not in ("inorden", "preorden", "postorden"):
            raise ValueError("Recorrido de árbol desconocido")
        publicaciones = getattr(self.arbol, recorrido)()
        explicaciones = {"inorden": "Izquierda, raíz, derecha: los ID quedan ordenados.",
                         "preorden": "Raíz, izquierda, derecha: conserva el orden necesario para reconstruir la forma.",
                         "postorden": "Izquierda, derecha, raíz: los hijos aparecen antes que su padre."}
        self.recorrido_arbol.setText((" → ".join(f"#{p.id}" for p in publicaciones) or "Árbol vacío") + "\n" + explicaciones[recorrido])

    def buscar_publicacion(self):
        if not self.forma_disponible:
            return
        try:
            id = int(self.id_busqueda.text())
        except ValueError:
            self.recorrido_arbol.setText("Escribe el número identificador de la publicación.")
            return
        publicacion = self.arbol.buscar(id)
        self.recorrido_arbol.setText(f"#{id}: {publicacion.texto}" if publicacion else f"La publicación #{id} no está en el índice activo.")


class DialogoHistorial(_DialogoFeria):
    def __init__(self, vista, parent=None):
        super().__init__("Lo que quedó registrado", "Vuelve a tus decisiones y a las pistas compartidas sin cambiar la investigación.", parent)
        self.vista = deepcopy(vista)
        self.jugadores = {j["id"]: j.get("nombre", "Participante") for j in vista.get("jugadores", [])}
        pestañas = QTabWidget()
        pagina, contenido = _pagina()
        divisor = QSplitter(Qt.Orientation.Horizontal)
        divisor.setChildrenCollapsible(False)
        self.lista_decisiones = QListWidget()
        self.lista_decisiones.setMinimumWidth(230)
        self.lista_decisiones.setAccessibleName("Decisiones registradas de los participantes")
        self.detalle_decision = QTextBrowser()
        self.detalle_decision.setMinimumWidth(310)
        divisor.addWidget(self.lista_decisiones)
        divisor.addWidget(self.detalle_decision)
        divisor.setStretchFactor(1, 2)
        self.registros = vista.get("historial") or (vista.get("resultado") or {}).get("registros", [])
        for registro in self.registros:
            publicacion = registro.get("publicacion") or {}
            nombre = self.jugadores.get(registro.get("jugador_id"), registro.get("nombre", "Participante"))
            titulo = registro.get("titulo_accion") or registro.get("titulo") or registro.get("accion_rol") or registro.get("accion", "Decisión")
            id = publicacion.get("id", registro.get("publicacion_id", registro.get("investigacion_caso", "?")))
            item = QListWidgetItem(f"#{id} · {nombre}\n{titulo}")
            self.lista_decisiones.addItem(item)
        self.lista_decisiones.currentRowChanged.connect(self._mostrar_decision)
        if self.registros:
            self.lista_decisiones.setCurrentRow(0)
        else:
            self.detalle_decision.setPlainText("Tus decisiones aparecerán aquí cuando las registres. Los borradores siguen en Redacción.")
        contenido.addWidget(divisor, 1)
        pestañas.addTab(pagina, "Decisiones")
        pagina, contenido = _pagina()
        compartidos = [h for h in vista.get("hallazgos", []) if h.get("compartido")]
        for hallazgo in compartidos:
            nombre = self.jugadores.get(hallazgo.get("propietario"), "Tu compañero")
            contenido.addWidget(_bloque(hallazgo.get("titulo", "Pista compartida"),
                                       f"Compartida por {nombre}\n\n{hallazgo.get('texto', '')}"))
        if not compartidos:
            contenido.addWidget(_bloque("LA MESA COMÚN", "Todavía no se compartieron hallazgos. Tus pistas propias permanecen en el Expediente."))
        contenido.addStretch()
        pestañas.addTab(pagina, "Pistas compartidas")
        pagina, contenido = _pagina()
        nombres = {n["id"]: n.get("nombre", n["id"]) for n in (vista.get("red") or {}).get("nodos", [])}
        reparacion = vista.get("mision_reparacion") or {}
        for clave, titulo, vacio in (
            ("afectados", "RECIBIERON EL RUMOR", "No hay personas afectadas registradas para este caso."),
            ("corregidos", "RECIBIERON LA CORRECCIÓN", "La corrección todavía no alcanzó a esas personas."),
            ("pendientes", "AÚN NECESITAN EL CONTEXTO", "No quedan personas pendientes de recibir la corrección."),
        ):
            ids = reparacion.get(clave, [])
            contenido.addWidget(_bloque(titulo, ", ".join(nombres.get(id, id) for id in ids) or vacio))
        contenido.addWidget(_texto("Cambiar de contactos cambia las rutas posibles de la corrección. Puedes comprobarlas en Audiencia.", "subtitulo"))
        contenido.addStretch()
        pestañas.addTab(pagina, "Reparar el daño")
        self.contenido.addWidget(pestañas, 1)
        self._cerrar()

    def _mostrar_decision(self, fila):
        if not 0 <= fila < len(self.registros):
            return
        registro = self.registros[fila]
        editor = registro.get("editor") or {}
        nombre = self.jugadores.get(registro.get("jugador_id"), registro.get("nombre", "Participante"))
        titulo = registro.get("titulo_accion") or registro.get("titulo") or registro.get("accion_rol") or registro.get("accion", "Decisión registrada")
        lineas = [nombre, titulo]
        if editor.get("titular"):
            lineas.append("«" + editor["titular"] + "»")
        if editor.get("certeza"):
            lineas.append("Certeza declarada: " + editor["certeza"])
        lineas.append(registro.get("editorial") or registro.get("explicacion", ""))
        lineas.append(f"La publicación llegó a {registro.get('alcance', 0)} personas.")
        etiquetas = {"confianza": "Confianza", "convivencia": "Convivencia", "bienestar_digital": "Bienestar digital",
                     "info_verificada": "Información contrastada", "desinformacion": "Desinformación",
                     "conflictos": "Conflictos", "participacion": "Participación"}
        for clave, valor in (registro.get("cambios_reales") or registro.get("cambios") or {}).items():
            lineas.append(f"{etiquetas.get(clave, clave.replace('_', ' '))}: {valor:+g}")
        lineas.append(f"Puntos: {registro.get('puntos', 0):+g}")
        self.detalle_decision.setPlainText("\n\n".join(linea for linea in lineas if linea))


class GaleriaRecursos(QWidget):
    """Recursos locales de la campaña; reproducción opcional y cancelable."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.movie = None
        self._tamano_gif = QSize()
        self.tipo_actual = "imagen"
        self.preferencias = dict(getattr(parent, "_preferencias", getattr(parent, "preferencias", {})))
        contenido = QVBoxLayout(self)
        contenido.addWidget(_texto("Los lugares y los momentos de esta investigación.", "subtitulo"))
        divisor = QSplitter(Qt.Orientation.Horizontal)
        self.lista = QListWidget()
        self.lista.setMinimumWidth(220)
        self.lista.setAccessibleName("Ilustraciones y momentos de Ciudad Nova")
        self.reproductores = QStackedWidget()
        self.imagen = QLabel()
        self.imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.imagen.setMinimumSize(360, 240)
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(360, 240)
        self.reproductores.addWidget(self.imagen)
        self.reproductores.addWidget(self.video_widget)
        divisor.addWidget(self.lista)
        divisor.addWidget(self.reproductores)
        divisor.setStretchFactor(1, 2)
        contenido.addWidget(divisor, 1)
        fila = QHBoxLayout()
        self.descripcion = _texto()
        self.reproducir = _boton("Reproducir", self._alternar_video)
        self.reproducir.hide()
        fila.addWidget(self.descripcion, 1)
        fila.addWidget(self.reproducir)
        contenido.addLayout(fila)
        self.audio = QAudioOutput(self)
        preferencias = self.preferencias
        self.audio.setVolume(max(0, min(100, preferencias.get("volumen", 50))) / 100)
        self.audio.setMuted(not preferencias.get("sonido", True))
        self.video = QMediaPlayer(self)
        self.video.setAudioOutput(self.audio)
        self.video.setVideoOutput(self.video_widget)
        self.video.playbackStateChanged.connect(self._estado_video)
        self.video.errorOccurred.connect(self._error_video)
        self.pixmap = QPixmap()
        self.recursos = []
        for nombre, ruta in (("El mapa de la ciudad", "assets/feria/mapa_ciudad.png"),
                             ("La mesa de investigación", "assets/feria/mesa_investigacion.png"),
                             ("Un lugar para cada voz", "assets/feria/portada.png")):
            if (RAIZ / ruta).is_file():
                self.recursos.append((nombre, ruta, "imagen"))
        if (RAIZ / "assets/feria/portada_animada.gif").is_file():
            self.recursos.append(("Una ciudad en movimiento", "assets/feria/portada_animada.gif", "gif"))
        if (RAIZ / "assets/feria/videos/portada_loop.mp4").is_file():
            self.recursos.append(("La última hora", "assets/feria/videos/portada_loop.mp4", "video"))
        for id, nombre in ((50, "La puerta del colegio"), (90, "El parque fuera de cuadro"), (110, "Los segundos que faltan"),
                           (40, "Un canal que recuerda"), (120, "Una entrada para el abuelo"), (35, "La palabra que borraron")):
            ruta = f"assets/feria/videos/caso_{id}.mp4"
            if (RAIZ / ruta).is_file():
                self.recursos.append((nombre, ruta, "video"))
        for nombre, ruta, tipo in self.recursos:
            self.lista.addItem(({"video": "Momento · ", "gif": "Animación · "}.get(tipo, "Lugar · ")) + nombre)
        self.lista.currentRowChanged.connect(self._seleccionar)
        if self.recursos:
            self.lista.setCurrentRow(0)
        else:
            self.descripcion.setText("Las imágenes de la ciudad están disponibles desde la historia.")

    def _seleccionar(self, fila):
        self.video.stop()
        if self.movie is not None:
            self.movie.stop()
            self.movie.deleteLater()
            self.movie = None
        if not 0 <= fila < len(self.recursos):
            return
        nombre, ruta, tipo = self.recursos[fila]
        self.tipo_actual = tipo
        self.pixmap = QPixmap()
        self.descripcion.setText(nombre)
        self.reproducir.setVisible(tipo in ("video", "gif"))
        self.reproducir.setEnabled(True)
        if tipo == "video":
            self.reproductores.setCurrentIndex(1)
            self.video.setSource(QUrl.fromLocalFile(str(RAIZ / ruta)))
            self.reproducir.setText("Reproducir")
        elif tipo == "gif":
            self.reproductores.setCurrentIndex(0)
            self.movie = QMovie(str(RAIZ / ruta), parent=self)
            self.movie.stateChanged.connect(self._estado_gif)
            self.movie.jumpToFrame(0)
            self._tamano_gif = self.movie.currentImage().size()
            self.imagen.setMovie(self.movie)
            self._ajustar_imagen()
            self.reproducir.setText("Reproducir animación")
            if not self.preferencias.get("reducir_movimiento", False):
                self.movie.start()
        else:
            self.reproductores.setCurrentIndex(0)
            self.pixmap = QPixmap(str(RAIZ / ruta))
            self._ajustar_imagen()

    def _ajustar_imagen(self):
        if self.movie is not None and not self._tamano_gif.isEmpty():
            self.movie.setScaledSize(self._tamano_gif.scaled(self.imagen.size(), Qt.AspectRatioMode.KeepAspectRatio))
        elif not self.pixmap.isNull():
            self.imagen.setPixmap(self.pixmap.scaled(self.imagen.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                                     Qt.TransformationMode.SmoothTransformation))

    def resizeEvent(self, event):
        self._ajustar_imagen()
        super().resizeEvent(event)

    def _alternar_video(self):
        if self.tipo_actual == "gif" and self.movie is not None:
            if self.movie.state() == QMovie.MovieState.Running:
                self.movie.setPaused(True)
            elif self.movie.state() == QMovie.MovieState.Paused:
                self.movie.setPaused(False)
            else:
                self.movie.start()
            return
        if self.video.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.video.pause()
        else:
            self.video.play()

    def _estado_video(self, estado):
        if self.tipo_actual == "video":
            self.reproducir.setText("Pausar" if estado == QMediaPlayer.PlaybackState.PlayingState else "Reproducir")

    def _estado_gif(self, estado):
        if self.tipo_actual == "gif":
            self.reproducir.setText("Pausar animación" if estado == QMovie.MovieState.Running else "Reproducir animación")

    def _error_video(self, *args):
        self.reproducir.setEnabled(False)
        self.descripcion.setText("Este momento no se pudo reproducir. Puedes seguir leyendo la investigación.")

    def detener(self):
        self.video.stop()
        if self.movie is not None:
            self.movie.stop()

    def hideEvent(self, event):
        self.video.pause()
        if self.movie is not None and self.movie.state() == QMovie.MovieState.Running:
            self.movie.setPaused(True)
        super().hideEvent(event)


class DialogoGaleria(_DialogoFeria):
    def __init__(self, parent=None):
        super().__init__("Un lugar para cada voz", "Recorre las ilustraciones y los momentos de esta ciudad.", parent)
        self.galeria = GaleriaRecursos(self)
        self.contenido.addWidget(self.galeria, 1)
        self._cerrar()

    def done(self, resultado):
        self.galeria.detener()
        super().done(resultado)
