"""interfaz.escenas.red: presentación separada de las reglas del juego."""
import copy
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QIcon
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QComboBox
from models.jugador import ROLES
from infraestructura.recursos import pixmap_recurso
from interfaz.cinematica.fondos import FondoEscena
from interfaz.componentes.arte import PanelIlustrado, BotonIlustrado, aplicar_estilo, dibujar_fondo, avatar_arte
from interfaz.dialogos import ESTILO
from interfaz.componentes.grafo import VisualizadorGrafo


class EscenaRed(QWidget):
    continuar = pyqtSignal()

    def __init__(self, juego, parent=None):
        super().__init__(parent)
        self.juego = juego
        self.setStyleSheet(ESTILO)
        self.ambiente_vivo = FondoEscena(self)
        self.ambiente_vivo.oscuridad = 75
        self.ambiente_vivo.establecer_escena("assets/rediseno/fondos/observatorio.png", "observatorio")
        self.panel = PanelIlustrado()
        self.panel.setObjectName("panelRed")
        self.panel.setMaximumSize(1600, 800)
        layout = self.layout_panel = QVBoxLayout(self.panel)
        layout.setContentsMargins(48, 48, 48, 36)
        layout.setSpacing(12)
        cabecera = QHBoxLayout()
        self.titulo = QLabel("<span style='font-size:25px;font-weight:600;'>OBSERVATORIO</span><br>"
                             "<span style='font-size:15px;font-weight:400;color:#c2d4cb;'>Las decisiones cambian la comunidad</span>")
        self.titulo.setStyleSheet("color: #f2d1a3;")
        cabecera.addWidget(self.titulo, 1)
        self.contador = QLabel()
        self.contador.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.contador.setStyleSheet("font-size: 14px; color: #c9dacd;")
        cabecera.addWidget(self.contador)
        layout.addLayout(cabecera)
        self.resumen = QLabel()
        self.resumen.setWordWrap(True)
        self.resumen.setStyleSheet("color: #f2e5d0; font-size: 16px; padding-bottom: 3px;")
        layout.addWidget(self.resumen)
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(18)
        mapa = QVBoxLayout()
        mapa.setSpacing(8)
        self.visualizador = VisualizadorGrafo(juego.grafo)
        self.visualizador.nodo_seleccionado.connect(self.consultar)
        mapa.addWidget(self.visualizador, 1)
        self.leyenda = QLabel("R: recorrido · Doble borde: emisor · Flechas: dirección de difusión")
        self.leyenda.setWordWrap(True)
        self.leyenda.setStyleSheet("font-size: 13px; color: #c2d3c9;")
        self.detalle = QLabel("Selecciona un ciudadano para consultar sus conexiones.")
        self.detalle.setWordWrap(True)
        self.detalle.setMinimumHeight(42)
        self.detalle.setStyleSheet("font-size: 15px; color: #e7e4d3;")
        mapa.addWidget(self.leyenda)
        mapa.addWidget(self.detalle)
        cuerpo.addLayout(mapa, 1)
        inspector = self.inspector = QWidget()
        inspector.setMinimumWidth(245)
        inspector.setMaximumWidth(300)
        herramientas = QVBoxLayout(inspector)
        herramientas.setContentsMargins(0, 0, 0, 0)
        herramientas.setSpacing(12)
        self.etiqueta_inspector = QLabel("EXPLORA LA RED")
        self.etiqueta_inspector.setStyleSheet("font-size: 16px; font-weight: 600; color: #f2d1a3;")
        herramientas.addWidget(self.etiqueta_inspector)
        self.etiqueta_origen = QLabel("Ciudadano de origen")
        herramientas.addWidget(self.etiqueta_origen)
        self.origen = QComboBox()
        self.origen.setStyleSheet("QComboBox{background:#1b2a43;color:#f6e8cd;border:1px solid #a98756;border-radius:6px;padding:8px;}")
        self.origen.setIconSize(QSize(30, 30))
        self.origen.setMinimumHeight(44)
        self.origen.setAccessibleName("Ciudadano de origen")
        herramientas.addWidget(self.origen)
        self.botones_red = []
        for texto, descripcion, metodo in (
                ("BFS · Por niveles", "Visita primero a las personas más cercanas al origen.", lambda: self.recorrer("bfs")),
                ("DFS · En profundidad", "Sigue una cadena de conexiones antes de explorar otra.", lambda: self.recorrer("dfs")),
                ("Comparar alcance", "Simula la última publicación desde este origen sin cambiar los puntos.", self.comparar)):
            boton = BotonIlustrado(texto)
            boton.setMinimumHeight(49)
            boton.setToolTip(descripcion)
            boton.setAccessibleDescription(descripcion)
            boton.clicked.connect(metodo)
            herramientas.addWidget(boton)
            self.botones_red.append(boton)
        self.explicacion = QLabel("BFS avanza por niveles.\nDFS sigue cada camino hasta el fondo.")
        self.explicacion.setWordWrap(True)
        self.explicacion.setStyleSheet("font-size: 14px; color: #c2d3c9;")
        herramientas.addWidget(self.explicacion)
        herramientas.addStretch()
        cuerpo.addWidget(inspector)
        layout.addLayout(cuerpo, 1)
        pie = QHBoxLayout()
        self.estado_reproduccion = QLabel("Recorrido automático · se repite tras 2 segundos")
        self.estado_reproduccion.setWordWrap(True)
        self.estado_reproduccion.setStyleSheet("font-size: 13px; color: #c2d3c9;")
        pie.addWidget(self.estado_reproduccion, 1)
        self.boton_continuar = BotonIlustrado("Continuar →")
        self.boton_continuar.setMinimumWidth(190)
        self.boton_continuar.setToolTip("Continuar la historia")
        self.boton_continuar.clicked.connect(self.continuar.emit)
        pie.addWidget(self.boton_continuar)
        layout.addLayout(pie)
        exterior = self.exterior = QVBoxLayout(self)
        exterior.setContentsMargins(18, 14, 18, 14)
        fila_panel = QHBoxLayout()
        fila_panel.setSpacing(0)
        fila_panel.addStretch()
        fila_panel.addWidget(self.panel, 1)
        fila_panel.addStretch()
        exterior.addLayout(fila_panel, 1)
        self.timer = QTimer(self)
        self.timer.setInterval(700)
        self.timer.timeout.connect(self.paso)
        self.timer_repeticion = QTimer(self)
        self.timer_repeticion.setSingleShot(True)
        self.timer_repeticion.setInterval(2000)
        self.timer_repeticion.timeout.connect(self.repetir)
        self.repeticion_activada = False
        self.comparacion_alcances = None
        self.pasos, self.indice, self.aristas_animacion = [], 0, []
        self.rellenar()
        aplicar_estilo(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not hasattr(self, "inspector"):
            return
        self.ambiente_vivo.setGeometry(self.rect())
        self.ambiente_vivo.lower()
        escala = max(.94, min(1.35, self.width()/1366))
        compacto = self.height() < 660
        muy_compacto = self.height() < 600
        seguros = self.panel.margenes_seguros()
        lateral = max(round(42*escala), seguros.left())
        self.layout_panel.setContentsMargins(lateral, max(34 if muy_compacto else round(46*escala), seguros.top()),
                                            lateral, max(22 if muy_compacto else round(32*escala), seguros.bottom()))
        self.layout_panel.setSpacing(8 if compacto else 12)
        self.inspector.setMinimumWidth(round(245*escala))
        self.inspector.setMaximumWidth(round(285*escala))
        subtitulo = "" if muy_compacto else (
            f"<br><span style='font-size:{round(15*escala)}px;font-weight:400;color:#c2d4cb;'>Las decisiones cambian la comunidad</span>")
        self.titulo.setText(
            f"<span style='font-size:{round(25*escala)}px;font-weight:600;'>OBSERVATORIO</span>" + subtitulo)
        self.titulo.setToolTip("Difusión, conversaciones y fuentes de Ciudad Nova")
        self.leyenda.setVisible(not muy_compacto)
        self.visualizador.setMinimumHeight(240 if muy_compacto else 310)
        for etiqueta, tamano, color in (
                (self.contador, 14, "#c9dacd"), (self.resumen, 16, "#f2e5d0"),
                (self.leyenda, 13, "#c2d3c9"), (self.detalle, 15, "#e7e4d3"),
                (self.estado_reproduccion, 13, "#c2d3c9"), (self.explicacion, 14, "#c2d3c9"),
                (self.etiqueta_origen, 16, "#f6e8cd")):
            etiqueta.setStyleSheet(f"font-size:{round(tamano*escala)}px;color:{color};")
        self.etiqueta_inspector.setStyleSheet(f"font-size:{round(16*escala)}px;font-weight:600;color:#f2d1a3;")
        self.origen.setStyleSheet(f"font-size:{round(16*escala)}px;")
        self.origen.setMinimumHeight(round(44*escala))
        self.origen.setIconSize(QSize(round(30*escala), round(30*escala)))
        for boton in self.botones_red + [self.boton_continuar]:
            boton.setStyleSheet(f"font-size:{round(16*escala)}px;")
            boton.setMinimumHeight(round((46 if compacto else 49)*escala))
        self.boton_continuar.setMinimumWidth(round(190*escala))
        self.detalle.setMinimumHeight(round((22 if muy_compacto else 34 if compacto else 42)*escala))
        self.visualizador.update()

    def paintEvent(self, event):
        p = QPainter(self)
        if not dibujar_fondo(p, self.rect(), "fondos/observatorio.png"):
            fondo = pixmap_recurso("assets/fondos/Escena Arbol.jfif")
            if not fondo.isNull():
                p.drawPixmap(self.rect(), fondo)
            else:
                p.fillRect(self.rect(), QColor("#182d41"))
        p.fillRect(self.rect(), QColor(11, 27, 39, 100))
        p.end()
        super().paintEvent(event)

    def rellenar(self):
        anterior = self.origen.currentData()
        self.origen.clear()
        for id, nodo in self.juego.grafo.nodos.items():
            self.origen.addItem(QIcon(avatar_arte(id)), nodo.nombre, id)
        self.origen.setCurrentIndex(max(0, self.origen.findData(anterior)))
        nuevos = getattr(self.juego, "ciudadanos_nuevos", [])
        nombres = [self.juego.grafo.nodos[id].nombre for id in nuevos if id in self.juego.grafo.nodos]
        crecimiento = "\nSe unieron: " + " y ".join(nombres) if nombres else ""
        self.contador.setText(f"{len(self.juego.grafo.nodos)} ciudadanos · {len(self.juego.grafo.aristas())} conexiones" + crecimiento)
        self.visualizador.nuevos = set(nuevos)
        self.visualizador.grafo = self.juego.grafo
        self.visualizador.update()

    def mostrar(self):
        self.finalizar_escena()
        self.rellenar()
        self.comparacion_alcances = None
        self.visualizador.establecer_contactos()
        self.explicacion.setText("BFS avanza por niveles.\nDFS sigue cada camino hasta el fondo.")
        self.resumen.setText(self.juego.ultimo_resultado)
        self.boton_continuar.setEnabled(True)
        registro = self.juego.ultimo_registro or {}
        accion = registro.get("accion_rol", registro.get("accion"))
        if accion in ("conversar", "entrevistar"):
            self.mostrar_contacto(registro)
            return
        resultado = self.juego.ultima_propagacion
        if resultado:
            tipo = "correccion" if resultado.correccion else "falsa" if resultado.verdadera is False else "verdadera" if resultado.verdadera is True else "exploracion"
            self.iniciar_animacion(resultado.niveles, resultado.aristas, resultado.emisor, tipo)
        else:
            self.pasos, self.indice, self.aristas_animacion = [], 0, []
            self.visualizador.tipo = "exploracion"
            self.visualizador.visitados.clear()
            self.visualizador.aristas_usadas.clear()
            self.visualizador.update()
            self.leyenda.setText("Sin difusión · Retratos: ciudadanos · Flechas: dirección de las relaciones")
            self.detalle.setText({
                "ignorar": "Seguiste sin reenviar: no hubo difusión ni nuevos contactos.",
                "reservar": "La información quedó en reserva, pendiente de pruebas. No hubo difusión ni nuevos contactos.",
                "contrastar": "El contraste no requirió difundir una corrección. Puedes explorar las relaciones de la comunidad.",
                "desmentir": "La denuncia no inició una rectificación. Las relaciones de la comunidad se conservan.",
            }.get(accion, "Esta decisión no inició una difusión. Puedes explorar la red con BFS y DFS."))
            self.estado_reproduccion.setText("Elige BFS, DFS o compara el alcance para explorar.")

    def mostrar_contacto(self, registro):
        accion = registro["accion_rol"]
        efectos = registro.get("efectos_red", {})
        autor = next((j for j in self.juego.jugadores if j.id == registro.get("jugador_id")), self.juego.jugador)
        origen = autor.ciudadano_id
        vecino = efectos.get("fuente_id") if accion == "entrevistar" else efectos.get("vecino_id")
        aristas = efectos.get("conexiones_creadas", [])
        self.pasos, self.indice, self.aristas_animacion = [], 0, []
        self.visualizador.tipo = "entrevista" if accion == "entrevistar" else "vinculo"
        self.visualizador.emisor = origen
        self.visualizador.aristas_usadas.clear()
        self.visualizador.establecer_contactos(aristas, origen, vecino, accion)
        self.visualizador.visitados = set(self.visualizador.focos_contacto)
        self.origen.setCurrentIndex(max(0, self.origen.findData(origen)))
        titulo = registro.get("titulo_accion", "Entrevistar a una fuente" if accion == "entrevistar" else "Escuchar al vecindario")
        rol = ROLES.get(registro.get("rol", autor.rol), ROLES[autor.rol])["nombre"]
        self.resumen.setText(f"{rol} · {titulo} · Publicación #{registro['publicacion']['id']}")
        self.leyenda.setText("+ Contacto · Arcos dorados con puntos y rayas: conexiones nuevas · Flechas: dirección")
        nodos = self.juego.grafo.nodos
        nombre_origen = nodos[origen].nombre if origen in nodos else autor.nombre
        nombre_vecino = nodos[vecino].nombre if vecino in nodos else "sin contacto disponible"
        cantidad = len(self.visualizador.conexiones_nuevas)
        cambio = (f"{cantidad} conexión nueva" if cantidad == 1 else f"{cantidad} conexiones nuevas") if cantidad else "Contacto ya existente"
        cierre = "Testimonio pendiente de contraste." if accion == "entrevistar" else "La publicación no se difundió."
        self.detalle.setText(f"{nombre_origen} ↔ {nombre_vecino} · {cambio}. {cierre}")
        self.estado_reproduccion.setText("Movimiento reducido · Vínculo completo" if getattr(self.window(), "reducir_movimiento", False)
                                        else "Contacto destacado · Explorar no aplica más puntos")
        self.explicacion.setText("El vínculo cambia las rutas futuras.\nCompara su alcance sin reenviar.")
        self.visualizador.update()

    def iniciar_animacion(self, niveles, aristas, emisor, tipo="exploracion"):
        self.timer.stop()
        self.timer_repeticion.stop()
        self.visualizador.completar_contactos()
        self.repeticion_activada = not getattr(self.window(), "reducir_movimiento", False)
        self.pasos, self.indice = [list(n) for n in niveles], 0
        self.aristas_animacion = [tuple(a) for a in aristas]
        self.visualizador.emisor = emisor
        self.visualizador.tipo = tipo
        self.leyenda.setText({"falsa": "! Información falsa · Trazo discontinuo",
                             "verdadera": "V Información verdadera · Trazo continuo",
                             "correccion": "C Corrección informativa · Trazo de puntos y rayas"}.get(tipo, "R Recorrido de exploración") + " · Doble borde: emisor · Flechas: dirección de difusión")
        self.visualizador.visitados.clear()
        self.visualizador.aristas_usadas.clear()
        self.estado_reproduccion.setText("Recorrido automático · se repite tras 2 segundos" if self.repeticion_activada else "Movimiento reducido · recorrido completo")
        if not self.repeticion_activada:
            self.completar()
            return
        self.paso()
        if self.indice < len(self.pasos):
            self.timer.start()

    def paso(self):
        if self.indice >= len(self.pasos):
            self.timer.stop()
            return
        self.visualizador.visitados.update(self.pasos[self.indice])
        self.visualizador.aristas_usadas = {a for a in self.aristas_animacion if a[0] in self.visualizador.visitados and a[1] in self.visualizador.visitados}
        nombres = [self.juego.grafo.nodos[id].nombre for id in self.pasos[self.indice] if id in self.juego.grafo.nodos]
        self.detalle.setText(f"Paso {self.indice + 1}/{len(self.pasos)} · Receptores: {max(0, len(self.visualizador.visitados)-1)} · " + ", ".join(nombres))
        self.indice += 1
        self.visualizador.update()
        if hasattr(self.window(), "audio"):
            self.window().audio.reproducir_efecto("nodo")
        if self.indice >= len(self.pasos):
            self.timer.stop()
            if self.repeticion_activada:
                self.estado_reproduccion.setText("Recorrido completo · vuelve a comenzar en 2 segundos")
                self.timer_repeticion.start()

    def repetir(self):
        self.timer_repeticion.stop()
        if not self.isVisible() or not self.repeticion_activada or not self.pasos:
            return
        if getattr(self.window(), "reducir_movimiento", False):
            self.completar()
            return
        self.indice = 0
        self.visualizador.visitados.clear()
        self.visualizador.aristas_usadas.clear()
        self.estado_reproduccion.setText("Recorrido automático · se repite tras 2 segundos")
        self.paso()
        if self.indice < len(self.pasos):
            self.timer.start()

    def pausar(self):
        self.timer_repeticion.stop()
        self.repeticion_activada = False
        if self.timer.isActive():
            self.timer.stop()
        elif self.indice < len(self.pasos):
            self.timer.start()

    def completar(self):
        self.repeticion_activada = False
        self.timer.stop()
        self.timer_repeticion.stop()
        while self.indice < len(self.pasos):
            self.paso()
        if not self.pasos and self.visualizador.focos_contacto:
            self.visualizador.completar_contactos()
            self.estado_reproduccion.setText("Contacto completo · Sin difusión en esta decisión")
        else:
            self.estado_reproduccion.setText("Recorrido completo" if self.pasos else "Sin difusión en esta decisión")

    def finalizar_escena(self):
        self.repeticion_activada = False
        self.timer.stop()
        self.timer_repeticion.stop()
        self.visualizador.completar_contactos()

    def hideEvent(self, event):
        if self.window().isMinimized():
            # Minimizar pausa el enlace; salir de la escena sí lo termina.
            self.timer.stop()
            self.timer_repeticion.stop()
        else:
            self.finalizar_escena()
        super().hideEvent(event)

    def consultar(self, id):
        g = self.juego.grafo
        vecinos = ", ".join(g.nodos[vecino].nombre for vecino in g.vecinos(id)) or "ninguno"
        self.detalle.setText(f"{g.nodos[id].nombre} · Entradas: {g.grado_entrada(id)} · Salidas: {g.grado_salida(id)} · Conecta con: {vecinos}")

    def recorrer(self, tipo):
        origen = self.origen.currentData()
        if not origen:
            return
        if tipo == "bfs":
            r = self.juego.grafo.bfs(origen)
            self.iniciar_animacion(r.niveles, r.aristas, origen)
            self.resumen.setText("BFS · " + " → ".join(self.juego.grafo.nodos[id].nombre for id in r.orden))
        else:
            orden = self.juego.grafo.dfs(origen)
            # Reconstruye las aristas del árbol DFS para mostrar el camino real.
            pila, visitados, aristas = [(origen, None)], set(), []
            while pila:
                actual, padre = pila.pop()
                if actual in visitados:
                    continue
                visitados.add(actual)
                if padre is not None:
                    aristas.append((padre, actual))
                pila.extend((vecino, actual) for vecino in reversed(self.juego.grafo.vecinos(actual)) if vecino not in visitados)
            self.iniciar_animacion([[id] for id in orden], aristas, origen)
            self.resumen.setText("DFS · " + " → ".join(self.juego.grafo.nodos[id].nombre for id in orden) + " · No garantiza el camino mínimo.")

    def comparar(self):
        id = self.juego.ultima_publicacion_id
        if id is None:
            self.detalle.setText("Primero toma una decisión sobre una publicación para comparar su alcance.")
            return
        if self.juego.arbol.buscar(id) is None:
            self.detalle.setText("La publicación fue retirada: su historial permanece, pero no puede iniciar una nueva difusión.")
            return
        anterior = self.juego.ultima_propagacion
        from models.jugador import ROLES
        registro = self.juego.ultimo_registro or {}
        habilidad = ROLES.get(registro.get("rol"), ROLES[self.juego.jugador.rol])
        saltos = 3 if registro.get("accion_rol") == "convocar" else habilidad["saltos"]
        origen = self.origen.currentData()
        if origen not in self.juego.grafo.nodos:
            return
        r = self.juego.propagacion.simular(id, origen, saltos, habilidad["intervalo"], bool(anterior and anterior.correccion))
        conexiones = self.visualizador.conexiones_nuevas
        if conexiones:
            # La comparación se hace en una copia; consultar nunca elimina un
            # vínculo real ni vuelve a aplicar consecuencias a la comunidad.
            sin_vinculos = copy.deepcopy(self.juego.grafo)
            for a, b in conexiones:
                sin_vinculos.eliminar_arista(a, b)
            antes = max(0, len(sin_vinculos.bfs(origen, saltos).orden)-1)
            self.comparacion_alcances = {"sin_conexiones": antes, "con_conexiones": r.alcance}
            self.resumen.setText(f"Simulación sin aplicar puntos · Sin nuevas conexiones: {antes} · Con ellas: {r.alcance}")
        else:
            self.comparacion_alcances = None
            self.resumen.setText(f"Simulación sin aplicar puntos · Difusión previa: {anterior.alcance if anterior else 0} · Simulada: {r.alcance}")
        tipo = "correccion" if r.correccion else "falsa" if r.verdadera is False else "verdadera" if r.verdadera is True else "exploracion"
        self.iniciar_animacion(r.niveles, r.aristas, r.emisor, tipo)
