"""interfaz.escenas.accion: presentación separada de las reglas del juego."""
import math
import time
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QGridLayout, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QEasingCurve
from infraestructura.recursos import pixmap_recurso
from interfaz.componentes.arte import PanelIlustrado, BotonIlustrado, decorar_botones, pixmap_arte, icono_arte, avatar_arte, miniatura_publicacion, FUENTE_UI
from interfaz.componentes.publicaciones import TarjetaPublicacion
from interfaz.novela.guion import caso_actual
from interfaz.cinematica.fondos import FondoEscena
from interfaz.componentes.personajes_animados import SpriteExpresivo
from juego.puesta_escena import escenario_actual
from interfaz.cinematica.efectos import CapaEfectos
from juego.acciones import acciones_para_rol, accion_por_defecto


class EscenaAccion(QWidget):

    def __init__(self, juego, parent=None):
        super().__init__(parent)

        self.juego = juego

        self.fondo = FondoEscena(self)
        self.fondo.setScaledContents(False)
        self.fondo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fondo.lower()
        self.efectos_narrativos = CapaEfectos(self)
        self._pistas_vistas = 0

        self.panel = PanelIlustrado(self)
        self.panel.setStyleSheet("""
            QFrame#panelAccion {
                background-color: rgba(20, 29, 48, 228);
                border: 1px solid rgba(245, 206, 190, 150);
                border-radius: 24px;
            }

            QLabel {
                color: #FFF9F4;
                background: transparent;
                border: none;
            }

            QLabel#titulo {
                color: #F6C6B6;
                font-size: 27px;
                font-weight: bold;
                letter-spacing: 1px;
            }

            QLabel#publicacion {
                color: #FFF9F4;
                font-size: 24px;
                font-weight: bold;
            }

            QLabel#info {
                color: #D8E6F2;
                font-size: 16px;
            }

            QLabel#turno {
                color: #F3D7C9;
                font-size: 15px;
                font-weight: bold;
            }

            QPushButton {
                background-color: rgba(78, 105, 131, 245);
                color: white;
                border: 2px solid #E8C7B5;
                border-radius: 14px;
                padding: 15px 22px;
                font-size: 17px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: rgba(107, 135, 160, 255);
                border-color: #FFF1E8;
            }

            QPushButton:pressed {
                background-color: rgba(57, 79, 101, 255);
            }

            QPushButton:disabled {
                color: #9AA8B5;
                border-color: #667481;
                background-color: rgba(45, 56, 68, 220);
            }
        """)
        self.panel.setObjectName("panelAccion")

        self.titulo = QLabel()
        self.titulo.setObjectName("titulo")
        self.titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.publicacion = QLabel()
        self.publicacion.setObjectName("publicacion")
        self.publicacion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.publicacion.setWordWrap(True)

        self.info = QLabel()
        self.info.setObjectName("info")
        self.info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.turno = QLabel(
            "DECISIÓN DEL CIUDADANO"
        )
        self.turno.setObjectName("turno")
        self.turno.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.boton_compartir = QPushButton("COMPARTIR")
        self.boton_verificar = QPushButton("VERIFICAR")
        self.boton_ignorar = QPushButton("IGNORAR")
        self.boton_reportar = QPushButton("REPORTAR")

        # Los nombres heredados conservan compatibilidad con controles y
        # guardados. Cada botón envía la decisión propia del oficio vigente.
        for boton in (self.boton_compartir, self.boton_verificar, self.boton_ignorar, self.boton_reportar):
            boton.clicked.connect(lambda _=False, b=boton: self.ejecutar_accion(b.property("accion_rol")))

        botones = QGridLayout()
        self.botones_accion = botones
        botones.setHorizontalSpacing(16)
        botones.setVerticalSpacing(16)
        botones.addWidget(self.boton_compartir, 0, 0)
        botones.addWidget(self.boton_verificar, 0, 1)
        botones.addWidget(self.boton_ignorar, 1, 0)
        botones.addWidget(self.boton_reportar, 1, 1)

        layout = QVBoxLayout(self.panel)
        self.layout_accion = layout
        layout.setContentsMargins(25, 23, 25, 33)
        layout.setSpacing(9)
        self.avatar = QLabel()
        self.avatar.setFixedSize(44, 44)
        self.avatar.setPixmap(pixmap_recurso("assets/UI/avatar_unknown.png").scaled(44, 44, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.miniatura = QLabel()
        self.miniatura.setFixedSize(104, 76)
        self.miniatura.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # El mismo componente muestra una publicación completa en ambas escenas.
        self.tarjeta_publicacion = TarjetaPublicacion(self.panel)
        layout.addWidget(self.tarjeta_publicacion, 1)
        for dato in (self.avatar, self.titulo, self.miniatura, self.publicacion, self.info):
            dato.hide()
        layout.addWidget(self.turno)
        layout.addLayout(botones)
        self.aviso = QLabel()
        self.aviso.setWordWrap(True)
        layout.addWidget(self.aviso)
        self.timer_decision = QTimer(self)
        self.timer_decision.setInterval(1000)
        self.timer_decision.timeout.connect(self.cuenta_regresiva)
        self.segundos_restantes = 0
        self.plazo_red = None
        self.efecto_panel = QGraphicsOpacityEffect(self.panel)
        self.panel.setGraphicsEffect(self.efecto_panel)
        self.animacion_panel = QPropertyAnimation(self.efecto_panel, b"opacity", self)
        self.animacion_panel.setStartValue(0.0)
        self.animacion_panel.setEndValue(1.0)
        self.animacion_panel.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.panel.setStyleSheet(f"QFrame#panelAccion {{background:transparent; border:0;}} QLabel {{color:#f6e8cd; background:transparent; border:0; font-family:'{FUENTE_UI}';}} QPushButton {{font:600 17px '{FUENTE_UI}'; min-height:34px; padding:7px;}}")
        self.titulo.setStyleSheet("color:#d7b98b; font:600 17px 'Atkinson Hyperlegible'; letter-spacing:2px;")
        self.publicacion.setStyleSheet("color:#fff3dc; font:24px 'Atkinson Hyperlegible';")
        self.info.setStyleSheet("color:#b6c9ca; font:13px 'Atkinson Hyperlegible';")
        self.info.setWordWrap(True)
        self.turno.setStyleSheet(f"color:#e6cca6; font:600 16px '{FUENTE_UI}';")
        self.turno.setWordWrap(True)
        self.aviso.setStyleSheet(f"color:#dce7e3; font:15px '{FUENTE_UI}';")
        self.aviso.setContentsMargins(12, 0, 12, 4)
        self.retrato_protagonista = SpriteExpresivo(self)
        self.retrato_protagonista.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.retrato_protagonista.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.leyenda_personaje = QLabel("Tu decisión deja huella.", self)
        self.leyenda_personaje.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.leyenda_personaje.setStyleSheet("color:#fff3dc; background:rgba(20,35,47,165); border-radius:10px; padding:12px; font:17px 'Atkinson Hyperlegible';")
        self.capitulo = QLabel(self)
        self.capitulo.setWordWrap(True)
        self.capitulo.setStyleSheet(f"color:#f2d6ad; background:rgba(14,35,47,225); border:1px solid #8d8068; border-radius:12px; padding:14px; font:19px '{FUENTE_UI}';")
        self.panel_mision = PanelIlustrado(self)
        mision = QVBoxLayout(self.panel_mision)
        mision.setContentsMargins(22, 19, 22, 19)
        mision.setSpacing(6)
        self.objetivo = QLabel()
        self.objetivo.setWordWrap(True)
        self.objetivo.setStyleSheet(f"color:#f6e8cd; background:transparent; font:17px '{FUENTE_UI}';")
        self.boton_investigar = BotonIlustrado("Examinar las fuentes")
        self.boton_investigar.setToolTip("")
        self.boton_investigar.clicked.connect(lambda: self.window().abrir_cuaderno(0))
        self.pistas_estado = QLabel()
        self.pistas_estado.setStyleSheet(f"color:#c5d8d0; background:transparent; font:14px '{FUENTE_UI}';")
        mision.addWidget(self.objetivo)
        mision.addWidget(self.boton_investigar)
        mision.addWidget(self.pistas_estado)
        self.boton_compartir.setToolTip("")
        self.boton_verificar.setToolTip("")
        self.boton_ignorar.setToolTip("")
        self.boton_reportar.setToolTip("")
        for nombre, boton in (("compartir", self.boton_compartir), ("verificar", self.boton_verificar), ("ignorar", self.boton_ignorar), ("reportar", self.boton_reportar)):
            boton.setIcon(icono_arte(nombre))
            boton.setIconSize(QSize(27, 27))
        decorar_botones(self.panel)

    def actualizar_acciones_rol(self):
        acciones = acciones_para_rol(self.jugador_de_interfaz().rol)
        etiquetas = {"compartir": "Compartir", "conversar": "Escuchar", "convocar": "Convocar",
                     "ignorar": "No reenviar", "contrastar": "Contrastar", "entrevistar": "Entrevistar",
                     "desmentir": "Desmentir", "reservar": "Reservar"}
        iconos = {"conversar": "nodo", "convocar": "compartir", "entrevistar": "verificar", "reservar": "ignorar"}
        botones = (self.boton_compartir, self.boton_verificar, self.boton_ignorar, self.boton_reportar)
        self.botones_por_accion = {}
        for boton, accion in zip(botones, acciones):
            clave = accion["clave"]
            boton.setProperty("accion_rol", clave)
            boton.setText(accion.get("titulo_corto", etiquetas[clave]))
            boton.setToolTip("")
            boton.setStatusTip("")
            boton.setAccessibleDescription(accion["descripcion"])
            boton.setAccessibleName(accion["titulo"] + ". " + accion["descripcion"])
            boton.setIcon(icono_arte(iconos.get(clave, accion["legacy"])))
            boton.setStyleSheet(f"font:600 17px '{FUENTE_UI}';")
            self.botones_por_accion[clave] = boton

    def jugador_de_interfaz(self):
        ventana = self.window()
        mi_id = getattr(ventana, "mi_id", None)
        if getattr(ventana, "cliente_red", None) is not None and mi_id:
            return next((j for j in self.juego.jugadores if j.id == mi_id), self.juego.jugador)
        return self.juego.jugador

    def actualizar_personaje(self):
        rol = "periodista" if self.jugador_de_interfaz().rol == "periodista" else "ciudadano"
        self.retrato_protagonista.configurar_actor(rol, escenario_actual(self.juego)[rol])
        self.retrato_protagonista.orientar_hacia("derecha")
        self.retrato_protagonista.configurar_movimiento(getattr(self.window(), "reducir_movimiento", False), getattr(self.window(), "animar_personajes", True))
        imagen = pixmap_arte(f"personajes/{rol}_neutral.png")
        self.retrato_protagonista.setGeometry(int(self.width()*.025), 78, int(self.width()*.35), max(220, self.height()-230))
        if not imagen.isNull():
            self.retrato_protagonista.setPixmap(imagen.scaled(self.retrato_protagonista.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.leyenda_personaje.hide()
        self.capitulo.setGeometry(int(self.width()*.025), 14, int(self.width()*.35), 82)
        self.panel_mision.setGeometry(int(self.width()*.025), self.height()-177, int(self.width()*.35), 163)
        self.retrato_protagonista.raise_()
        self.efectos_narrativos.raise_()
        self.capitulo.raise_()
        self.panel_mision.raise_()
        self.panel.raise_()

    def actualizar_pistas(self):
        publicacion = self.juego.obtener_publicacion_actual()
        consultadas = getattr(self.window(), "pistas_consultadas", set())
        vistas = sum((publicacion.id, i) in consultadas for i in range(3)) if publicacion else 0
        self.pistas_estado.setText(f"{vistas}/3 fuentes consultadas · Caso {self.juego.indice_proxima_publicacion} de {len(self.juego.publicaciones_planificadas)}")
        if vistas > self._pistas_vistas:
            self.efectos_narrativos.reproducir("investigar", duracion=3.5, intensidad=.55)
            if getattr(self.window(), "cuaderno", None) is not None:
                self.efectos_narrativos.pausar()
        self._pistas_vistas = vistas

    def resizeEvent(self, event):
        self.actualizar_fondo()
        self.efectos_narrativos.setGeometry(self.rect())

        self.panel.setGeometry(int(self.width()*.40), 14, int(self.width()*.575), self.height()-28)
        compacto = self.height() < 580
        self.layout_accion.setContentsMargins(25, 16 if compacto else 23, 25, 19 if compacto else 33)
        self.layout_accion.setSpacing(5 if compacto else 9)
        self.botones_accion.setVerticalSpacing(8 if compacto else 16)
        for boton in (self.boton_compartir, self.boton_verificar, self.boton_ignorar, self.boton_reportar):
            boton.setFixedHeight(48 if compacto else 52)
        self.actualizar_personaje()

        super().resizeEvent(event)

    def actualizar_fondo(self):
        direccion = escenario_actual(self.juego)
        self.fondo.establecer_escena(direccion["fondo"], direccion["ambiente"])
        pixmap = pixmap_recurso(direccion["fondo"])

        if pixmap.isNull():
            self.fondo.setStyleSheet(
                "background-color: #172236;"
            )
            self.fondo.setGeometry(self.rect())
            return

        pixmap_escalado = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )

        self.fondo.setPixmap(pixmap_escalado)
        self.fondo.setGeometry(self.rect())
        self.fondo.lower()

    def mostrar(self):
        self.efectos_narrativos.detener()
        self.efectos_narrativos.configurar(
            reducir_movimiento=getattr(self.window(), "reducir_movimiento", False),
            activo=getattr(self.window(), "animar_fondos", True))
        self.actualizar_fondo()
        self.actualizar_acciones_rol()
        self.actualizar_personaje()
        caso = caso_actual(self.juego)
        self.capitulo.setText(f"{caso['acto']}\n{caso['titulo']}")
        self.objetivo.setText(caso["objetivo"])
        self.actualizar_pistas()
        publicacion = (
            self.juego.obtener_publicacion_actual()
        )

        if publicacion is None:
            self.titulo.setText(
                "NO HAY PUBLICACIONES DISPONIBLES"
            )
            self.publicacion.setText("")
            self.info.setText("")
            self.turno.setText("")

            for boton in (
                self.boton_compartir,
                self.boton_verificar,
                self.boton_ignorar,
                self.boton_reportar
            ):
                boton.setEnabled(False)

            return

        self.efectos_narrativos.reproducir("decision", duracion=6.5, intensidad=.5)

        for boton in (
            self.boton_compartir,
            self.boton_verificar,
            self.boton_ignorar,
            self.boton_reportar
        ):
            boton.setEnabled(True)

        self.titulo.setText(
            "PUBLICACIÓN DE CIVITAS"
        )
        self.tarjeta_publicacion.mostrar(publicacion, self.juego.grafo)
        retrato = avatar_arte(publicacion.emisor_id)
        if not retrato.isNull():
            self.avatar.setPixmap(retrato.scaled(44, 44, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        miniatura = miniatura_publicacion(publicacion.id)
        if not miniatura.isNull():
            self.miniatura.setPixmap(miniatura.scaled(self.miniatura.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
        else:
            self.miniatura.clear()
        self.animacion_panel.stop()
        self.animacion_panel.setDuration(1 if getattr(self.window(), "reducir_movimiento", False) else 350)
        self.animacion_panel.start()

        self.publicacion.setText(
            f'"{publicacion.texto}"'
        )

        self.info.setText(
            f"Civitas · {self.juego.grafo.nodos.get(publicacion.emisor_id).nombre if publicacion.emisor_id in self.juego.grafo.nodos else 'Comunidad'} · ID #{publicacion.id} · {publicacion.estado}\n"
            f"Impacto {publicacion.impacto} · Compartidos {publicacion.compartidos} · Verificaciones {publicacion.verificaciones} · Alcance {publicacion.alcance}"
        )

        self.turno.setText(
            f"TURNO DE {self.juego.jugador.nombre.upper()} · {self.juego.jugador.rol.upper()} · Puntos {self.juego.jugador.puntos}"
        )

        evento = self.juego.evento_actual
        self.segundos_restantes = evento.segundos
        self.aviso.setText(evento.texto)
        self.timer_decision.stop()
        if self.juego.decision_aplicada:
            for boton in (self.boton_compartir, self.boton_verificar, self.boton_ignorar, self.boton_reportar):
                boton.setEnabled(False)
            return
        if evento.urgente and not getattr(self.window(), "sin_limite", False):
            self.timer_decision.start()
            self.aviso.setText(f"{evento.texto} · {self.segundos_restantes} s")
        if getattr(self.window(), "cliente_red", None) is not None:
            mi_turno = self.juego.jugador.id == self.window().mi_id
            self.timer_decision.stop()  # El servidor decide el timeout oficial.
            self.plazo_red = None
            for boton in (self.boton_compartir, self.boton_verificar, self.boton_ignorar, self.boton_reportar):
                boton.setEnabled(mi_turno and not self.juego.decision_aplicada)
            if not mi_turno:
                self.aviso.setText("Esperando la decisión del jugador de turno…")
            else:
                self.window().cliente_red.enviar({"tipo": "decision_lista", "publicacion_id": publicacion.id})

    def cuenta_regresiva(self):
        if getattr(self.window(), "cliente_red", None) is not None:
            if self.plazo_red is None:
                return
            segundos = max(0, math.ceil(self.plazo_red-time.monotonic()))
            self.aviso.setText(f"{self.juego.evento_actual.texto} · {segundos} s · turno de {self.juego.jugador.nombre}")
            if segundos == 0:
                self.timer_decision.stop()
                self.aviso.setText("Tiempo agotado. Esperando el resultado del servidor…")
            return
        self.segundos_restantes -= 1
        if 0 < self.segundos_restantes <= 3 and hasattr(self.window(), "audio"):
            self.window().audio.reproducir_efecto("cuenta_regresiva")
            self.efectos_narrativos.reproducir("tension", duracion=1.2, intensidad=.5)
        self.aviso.setText(f"{self.juego.evento_actual.texto} · {self.segundos_restantes} s")
        if self.segundos_restantes <= 0:
            self.ejecutar_accion(accion_por_defecto(self.juego.jugador.rol))

    def actualizar_plazo_red(self, segundos):
        if segundos is None:
            self.plazo_red = None
            self.timer_decision.stop()
            return
        self.plazo_red = time.monotonic() + segundos
        self.timer_decision.start()
        self.cuenta_regresiva()

    def finalizar_escena(self):
        self.efectos_narrativos.detener()
        self.timer_decision.stop()
        self.animacion_panel.stop()
        self.efecto_panel.setOpacity(1.0)

    def hideEvent(self, event):
        # Minimizar no equivale a abandonar la decisión: el plazo local sigue
        # contando y el servidor conserva su cuenta autoritativa en una sala.
        if not self.window().isMinimized():
            self.finalizar_escena()
        super().hideEvent(event)

    def ejecutar_accion(self, accion):
        self.timer_decision.stop()
        if getattr(self.window(), "cliente_red", None) is not None:
            self.window().enviar_accion(accion)
            return
        resultado = self.juego.ejecutar_accion(
            accion
        )

        if resultado is False:
            return

        for boton in (self.boton_compartir, self.boton_verificar, self.boton_ignorar, self.boton_reportar):
            boton.setEnabled(False)

        self.window().mostrar_escena(
            self.window().ESCENA_RESULTADO_1
        )
