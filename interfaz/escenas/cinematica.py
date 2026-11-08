"""interfaz.escenas.cinematica: presentación separada de las reglas del juego."""
from PyQt6.QtWidgets import QLabel, QHBoxLayout, QFrame, QToolButton
from PyQt6.QtGui import QFont, QFontMetrics
from PyQt6.QtCore import Qt, QTimer, QRect, QRectF, QPropertyAnimation, QParallelAnimationGroup, QEasingCurve, pyqtSignal
from infraestructura.recursos import pixmap_recurso
from interfaz.componentes.arte import PanelIlustrado, pixmap_arte, cargar_tipografias, FUENTE_UI, FUENTE_DIALOGO, geometria_dialogo
from interfaz.componentes.publicaciones import TarjetaPublicacion
from interfaz.novela.guion import dialogos_publicacion
from interfaz.novela.guion import caso_actual
from interfaz.cinematica.fondos import FondoEscena
from interfaz.componentes.personajes_animados import ACTORES_NUEVOS
from juego.puesta_escena import escenario_actual, expresion_dialogo, efecto_dialogo, efecto_visual_dialogo
from juego.cinematica import CINEMATICAS, clave_cinematica
from juego.cinematica_acciones import CINEMATICAS_ACCIONES
from juego.cinematica_acciones_extendida import CINEMATICAS_ACCIONES_EXTENDIDAS
from interfaz.novela.guion import clave_accion_extendida
from juego.cinematica_personajes_extendida import CINEMATICAS_PERSONAJES_EXTENDIDAS
from interfaz.novela.guion import clave_personaje_extendido
from juego.cinematica_final import CINEMATICAS_FINALES, clave_final
from interfaz.cinematica.reproductor import CapaCinematica
from interfaz.novela.direccion import CATALOGO_PULIDO, campana_visual, elegir_plano, fondo_intervencion, expresion_actor
from interfaz.novela.transiciones import TransicionNarrativa
from interfaz.cinematica.efectos import CapaEfectos
from interfaz.componentes.personaje import PersonajeVisual


NOMBRES_PERSONAJES = {"INFLUENCER": "VALERIA CRUZ", "JUAN": "JUAN TORRES",
                      "ADRIAN": "ADRIÁN MORALES", "LAURA": "LAURA RÍOS", "CAMILA": "CAMILA VEGA"}


CORTES_ACCIONES = {**CINEMATICAS_ACCIONES, **CINEMATICAS_ACCIONES_EXTENDIDAS}


CORTES_EPILOGO = {f"epilogo_{k}": {**v, "titulo": "El recuento continúa" if k == "recuento" else "El encargo de Ciudad Nova", "bucle": False}
                  for k, v in CINEMATICAS_FINALES.items()}


class EscenaCinematica(QFrame):

    dialogo_terminado = pyqtSignal()

    DURACION_FRANJAS = 450
    PAUSA_CINEMATICA = 80
    TIEMPO_ANTES_DE_HABLAR = 650

    RUTA_CIUDADANO = "assets/personajes/Ciudadano.png"
    RUTA_PERIODISTA = "assets/personajes/periodista.png"

    def __init__(self, fondo, parent=None):
        super().__init__(parent)

        self.fondo = fondo
        self.animacion = None
        self.animacion_personajes = None
        self.animacion_ocultar_personajes = None

        self.personajes = {
            "CIUDADANO": PersonajeVisual(
                self.RUTA_CIUDADANO,
                self
            ),
            "PERIODISTA": PersonajeVisual(
                self.RUTA_PERIODISTA,
                self
            )
        }

        self.personajes_activos = set()
        self.personajes_en_escena = set()
        self.hablante_actual = ""

        self.nombre_label = QLabel(self)
        self.texto_label = QLabel(self)

        self.fondo_label = FondoEscena(self)
        self.fondo_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        from juego.cinematica_extension import CINEMATICAS_EXTENSION
        self.cine_narrativo = CapaCinematica(self, catalogo={**CINEMATICAS, **CORTES_ACCIONES,
                                                           **CINEMATICAS_EXTENSION, **CORTES_EPILOGO,
                                                           **CINEMATICAS_PERSONAJES_EXTENDIDAS})
        self.cine_narrativo.estado_cambiado.connect(self.estado_corte_cambiado)
        self._clave_preparada = None
        self.efectos_narrativos = CapaEfectos(self)
        self._audiovisual_iniciado = False
        self._reanudar_al_restaurar = None
        self._balance_pausado_al_minimizar = False

        self.franja_superior = QFrame(self)
        self.franja_superior.setStyleSheet(
            "QFrame { background: transparent; border: none; }"
        )

        self.franja_inferior = PanelIlustrado(self, recurso="ui/dialogo.png")
        self.franja_inferior.setStyleSheet("background:transparent;border:none;")

        self.nombre_label.setStyleSheet(
            """
            QLabel {
                color: #F3CBB8;
                background: transparent;
                font-weight: bold;
            }
            """
        )
        self.nombre_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        self.texto_label.setStyleSheet(
            """
            QLabel {
                color: white;
                background: transparent;
            }
            """
        )
        self.texto_label.setWordWrap(True)
        self.texto_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft |
            Qt.AlignmentFlag.AlignVCenter
        )
        self.pista_continuar = QLabel("ESPACIO · revelar / continuar", self)
        self.pista_continuar.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.pista_continuar.setStyleSheet(f"color:#d3dfdf; font:14px '{FUENTE_UI}'; background:transparent;")
        self.pista_continuar.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.pista_continuar.hide()
        self.publicacion_telefono = None
        if self.fondo.endswith("Escena 3.png") and not pixmap_arte("fondos/telefono.png").isNull():
            self.publicacion_telefono = TarjetaPublicacion(self, telefono=True)

        self.texto_completo = ""
        self.nombre_inicial = ""
        self.escribiendo = False
        self.animando = False

        self.estado_escena = "inactiva"
        self.timer_inicio = QTimer(self)
        self.timer_inicio.setSingleShot(True)
        self.timer_inicio.timeout.connect(self.preparar_dialogo)
        self.timer_texto = QTimer(self)
        self.timer_texto.setInterval(34)
        self.timer_texto.timeout.connect(self.escribir_caracter)
        self.indice_texto = 0

        self.dialogo_era_leido = False
        self.lectura_pausada = False
        self.timer_lectura = QTimer(self)
        self.timer_lectura.setSingleShot(True)
        self.timer_lectura.timeout.connect(self.paso_lectura)
        self.contexto_escena = QLabel(self)
        self.contexto_escena.setWordWrap(True)
        self.contexto_escena.setStyleSheet(f"background:rgba(13,34,45,220); color:#eed2a8; border:1px solid #8c7960; border-radius:10px; padding:10px 15px; font:16px '{FUENTE_UI}';")
        self.contexto_escena.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.controles_lectura = QFrame(self)
        self.controles_lectura.setStyleSheet("QFrame {background:rgba(13,34,45,230); border:1px solid #667d7c; border-radius:10px;} QToolButton {border:0; padding:5px 12px; color:#f6e8cd;} QToolButton:checked {background:#487978; color:white;}")
        controles = QHBoxLayout(self.controles_lectura)
        controles.setContentsMargins(5, 3, 5, 3)
        controles.setSpacing(2)
        self.boton_historial = QToolButton()
        self.boton_historial.setText("Historial")
        self.boton_historial.setMinimumWidth(130)
        self.boton_historial.clicked.connect(lambda: self.window().abrir_cuaderno(2))
        self.boton_auto = QToolButton()
        self.boton_auto.setText("Auto")
        self.boton_auto.setMinimumWidth(95)
        self.boton_auto.setCheckable(True)
        self.boton_auto.setToolTip("Avanza los diálogos automáticamente. Se detiene al llegar a una decisión.")
        self.boton_saltar = QToolButton()
        self.boton_saltar.setText("Saltar leído")
        self.boton_saltar.setMinimumWidth(170)
        self.boton_saltar.setCheckable(True)
        self.boton_saltar.setToolTip("Avanza sólo los diálogos que ya terminaste de leer. Se detiene ante texto nuevo.")
        for boton in (self.boton_historial, self.boton_auto, self.boton_saltar):
            boton.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            controles.addWidget(boton)
        self.boton_auto.toggled.connect(self.programar_lectura)
        self.boton_saltar.toggled.connect(self.programar_lectura)
        self.contexto_escena.hide()
        self.controles_lectura.hide()

        self.cargar_fuente()

        self.setFocusPolicy(
            Qt.FocusPolicy.StrongFocus
        )

    def cargar_fuente(self):
        cargar_tipografias()
        self.fuente_nombre = QFont(FUENTE_UI)
        self.fuente_nombre.setPixelSize(23)
        self.fuente_nombre.setBold(True)
        self.fuente_dialogo = QFont(FUENTE_DIALOGO)
        self.fuente_dialogo.setPixelSize(26)
        self.fuente_dialogo.setBold(False)
        self.nombre_label.setFont(self.fuente_nombre)
        self.texto_label.setFont(self.fuente_dialogo)

    def resizeEvent(self, event):
        self.actualizar_geometria()
        self.actualizar_fondo()
        super().resizeEvent(event)

    def actualizar_fondo(self):
        self.fondo_label.establecer_escena(self.fondo)
        pixmap = pixmap_recurso(self.fondo)

        if pixmap.isNull():
            self.fondo_label.setStyleSheet(
                "background-color: #111111;"
            )
            self.fondo_label.setGeometry(self.rect())
            return

        pixmap_escalado = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )

        self.fondo_label.setPixmap(pixmap_escalado)
        self.fondo_label.setGeometry(self.rect())
        self.fondo_label.lower()

    def actualizar_geometria(self):
        ancho = self.width()
        alto = self.height()

        if ancho <= 0 or alto <= 0:
            return

        self.cine_narrativo.setGeometry(self.rect())
        self.efectos_narrativos.setGeometry(self.rect())

        tam_texto = 24 if ancho < 1200 else 25 if ancho < 1600 else 28
        tam_nombre = 22 if ancho < 1200 else 23 if ancho < 1600 else 25
        self.fuente_dialogo.setPixelSize(tam_texto)
        self.texto_label.setFont(self.fuente_dialogo)
        self.franja_inferior.alto_contraste = getattr(self.window(), "alto_contraste", False)
        self.franja_inferior.update()
        self.texto_label.setStyleSheet(f"color:#fff7e8; background:transparent; font:{tam_texto}px '{FUENTE_DIALOGO}';")
        self.nombre_label.setStyleSheet(f"color:#ffe5bb; background:transparent; font:700 {tam_nombre}px '{FUENTE_UI}';")
        caja_texto, _, _ = geometria_dialogo(QRectF(0, 0, ancho, 176))
        rect_texto = QFontMetrics(self.fuente_dialogo).boundingRect(
            QRect(0, 0, round(caja_texto.width()), 2000), Qt.TextFlag.TextWordWrap,
            self.texto_completo or "Ciudad Nova")
        altura_franja = max(176, rect_texto.height()+132)

        self.altura_franja = altura_franja

        self.franja_superior.setGeometry(
            0,
            0 if self.estado_escena in ("dialogo", "esperando") else -altura_franja,
            ancho,
            altura_franja
        )

        self.franja_inferior.setGeometry(
            0,
            alto - altura_franja if self.estado_escena in ("dialogo", "esperando") else alto,
            ancho,
            altura_franja
        )

        texto, nombre, pista = geometria_dialogo(QRectF(0, alto-altura_franja, ancho, altura_franja))
        self.nombre_label.setGeometry(nombre.toAlignedRect())
        self.nombre_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.texto_label.setGeometry(texto.toAlignedRect())
        self.pista_continuar.setGeometry(pista.toAlignedRect())
        if self.publicacion_telefono is not None:
            imagen = pixmap_arte("fondos/telefono.png")
            factor = max(ancho/imagen.width(), alto/imagen.height())
            desfase_x = (ancho-imagen.width()*factor)/2
            desfase_y = (alto-imagen.height()*factor)/2
            x = int(desfase_x+imagen.width()*.578*factor)
            y = int(desfase_y+imagen.height()*.132*factor) + int(alto*.06)
            ancho_post = int(imagen.width()*.157*factor)
            alto_post = max(225, alto-altura_franja-y-7)
            self.publicacion_telefono.setGeometry(x, y, ancho_post, alto_post)
            self.publicacion_telefono.raise_()

        ancho_personaje = int(ancho * 0.40)
        y_personaje = 78
        alto_personaje = max(220, alto-y_personaje-12)
        separacion = int(ancho * 0.02)

        self.personajes["CIUDADANO"].establecer_encuadre(
            separacion,
            y_personaje,
            ancho_personaje,
            alto_personaje
        )

        self.personajes["PERIODISTA"].establecer_encuadre(
            ancho - ancho_personaje - separacion,
            y_personaje,
            ancho_personaje,
            alto_personaje
        )
        self.personajes["CIUDADANO"].orientar_hacia("derecha")
        self.personajes["PERIODISTA"].orientar_hacia("izquierda")
        for nombre, personaje in self.personajes.items():
            if nombre.lower() in ACTORES_NUEVOS:
                # Plano lateral individual para la influencer y candidaturas.
                # Deja libre el escenario y nunca ocupa el sitio de la reportera.
                ancho_npc = round(ancho*.32)
                personaje.establecer_encuadre(ancho-ancho_npc-separacion,
                                               y_personaje, ancho_npc, alto_personaje)
                personaje.orientar_hacia("izquierda")
        if hasattr(self, "controles_lectura"):
            self.contexto_escena.setGeometry(20, 18, min(495, ancho-485), 48)
            self.controles_lectura.setGeometry(ancho-440, 18, 420, 48)
            self.contexto_escena.raise_()
            self.controles_lectura.raise_()

    def mostrar_fondo(self):
        self.actualizar_fondo()
        self.actualizar_geometria()

    def mostrar_personaje(self, nombre, aparecer=True):
        personaje = self.personajes.get(nombre)

        if personaje is None:
            return

        personaje.raise_()

        if aparecer:
            personaje.aparecer(850)
        else:
            personaje.show()
            personaje.efecto_fade.setOpacity(1.0)

    def configurar_personajes_para_hablante(
        self,
        nombre,
        presentes=None
    ):
        nombre = nombre.upper().strip()
        # Los personajes invitados tienen un plano lateral propio. Cuando
        # hablan los protagonistas vuelve su pareja, sin invitados superpuestos.
        nombres = {n.upper().strip() for n in (presentes or ())} | {nombre}
        for clave in nombres:
            clave = clave.upper().strip()
            if clave.lower() in ACTORES_NUEVOS and clave not in self.personajes:
                self.personajes[clave] = PersonajeVisual(
                    f"assets/expansion/siete_actos/personajes/{clave.lower()}_neutral.png", self)
                self.personajes[clave].reducir_movimiento = bool(
                    getattr(self.window(), "reducir_movimiento", False))
                for lienzo in (self.personajes[clave].imagen, self.personajes[clave].imagen_oscura):
                    lienzo.configurar_movimiento(getattr(self.window(), "reducir_movimiento", False),
                                                 getattr(self.window(), "animar_personajes", True))
                self.personajes[clave].hide()
        if nombre.lower() in ACTORES_NUEVOS:
            presentes = {nombre}
        elif nombre in ("CIUDADANO", "PERIODISTA"):
            presentes = {n for n in nombres if n in ("CIUDADANO", "PERIODISTA")}
        elif nombre in ("", "NARRADOR"):
            presentes = {n for n in nombres if n in ("CIUDADANO", "PERIODISTA")}
        juego = getattr(self.window(), "juego", None)
        if juego is not None:
            for id_personaje in self.personajes:
                personaje = self.personajes[id_personaje]
                if campana_visual(juego) and id_personaje not in (presentes or ()) and id_personaje != nombre:
                    continue
                personaje.establecer_expresion(id_personaje.lower(), expresion_actor(
                    juego, id_personaje, self.texto_completo if id_personaje == nombre else ""))
        compuesto = self.fondo.rsplit("/", 1)[-1] in {"Escena 4.png", "Escena 6.png", "Escena 7.png", "Escena 8.png"}
        if compuesto and pixmap_arte("fondos/cafe_interior.png").isNull() and not getattr(self.window(), "sprites_sobre_ilustracion", False):
            self.ocultar_personajes()
            self.hablante_actual = nombre
            return

        if nombre in ("", "NARRADOR"):
            if not presentes:
                for personaje in self.personajes.values():
                    personaje.ocultar_inmediato()
                self.personajes_activos.clear()
                self.personajes_en_escena.clear()
                self.hablante_actual = "NARRADOR"
                return
        elif nombre not in self.personajes:
            self.ocultar_personajes()
            self.hablante_actual = nombre
            return

        if presentes is None:
            presentes = {nombre}
        else:
            presentes = {
                personaje.upper().strip()
                for personaje in presentes
                if personaje.upper().strip() in self.personajes
            }

            if nombre in self.personajes:
                presentes.add(nombre)

        nuevos = presentes - self.personajes_activos

        for personaje_nombre, personaje in self.personajes.items():
            if personaje_nombre not in presentes:
                personaje.ocultar_inmediato()

        # El destino debe estar calculado ANTES de crear QPropertyAnimation.
        # De lo contrario termina devolviendo al invitado al encuadre anterior.
        self.personajes_activos = set(presentes)
        self.personajes_en_escena = set(presentes)
        self.actualizar_geometria()

        for personaje_nombre in nuevos:
            personaje = self.personajes[personaje_nombre]
            personaje.raise_()
            personaje.aparecer(850)

        for personaje_nombre, personaje in self.personajes.items():
            if personaje_nombre not in presentes:
                continue

            personaje.raise_()

            if personaje_nombre == nombre:
                personaje.enfocar(500)
            else:
                personaje.oscurecer(500, 0.58)

        self.franja_superior.raise_()
        self.franja_inferior.raise_()
        self.nombre_label.raise_()
        self.texto_label.raise_()

        self.hablante_actual = nombre

    def ocultar_personajes(self):
        activos = list(self.personajes_activos)

        self.personajes_activos.clear()
        self.personajes_en_escena.clear()

        if not activos:
            for personaje in self.personajes.values():
                personaje.hide()
            return

        for nombre in activos:
            personaje = self.personajes[nombre]
            personaje.desaparecer(350)

    def comenzar_escena(self):
        self.timer_inicio.stop()
        if self.animacion is not None:
            self.animacion.stop()

        if self.animacion_personajes is not None:
            self.animacion_personajes.stop()

        self.timer_texto = getattr(
            self,
            "timer_texto",
            None
        )

        if self.timer_texto is not None:
            self.timer_texto.stop()

        self.texto_completo = ""
        self.escribiendo = False
        self.animando = True
        self.estado_escena = "preparando"
        self.hablante_actual = ""

        self.ocultar_personajes()

        for personaje in self.personajes.values():
            personaje.efecto_fade.setOpacity(0.0)
            personaje.efecto_dimming.setOpacity(0.0)
            personaje.hide()

        self.nombre_label.clear()
        self.texto_label.clear()
        self.nombre_label.hide()
        self.texto_label.hide()

        self.mostrar_fondo()

        self.franja_superior.raise_()
        self.franja_inferior.raise_()
        self.nombre_label.raise_()
        self.texto_label.raise_()

        self.franja_superior.setGeometry(
            0,
            -self.altura_franja,
            self.width(),
            self.altura_franja
        )

        self.franja_inferior.setGeometry(
            0,
            self.height(),
            self.width(),
            self.altura_franja
        )

        if self.publicacion_telefono is not None and hasattr(self.window(), "juego"):
            self.publicacion_telefono.mostrar(self.window().juego.obtener_publicacion_actual(), self.window().juego.grafo)
        self.preparar_puesta_audiovisual(self.texto_inicial, self.nombre_inicial)
        self.timer_inicio.start(self.TIEMPO_ANTES_DE_HABLAR)

        self.setFocus()

    def preparar_dialogo(self):
        self.iniciar_dialogo(
            self.texto_inicial,
            self.nombre_inicial
        )

    def iniciar_dialogo(
        self,
        texto,
        nombre="",
        presentes=None
    ):
        juego = getattr(self.window(), "juego", None)
        if (campana_visual(juego) and self.isVisible()
                and self.estado_escena in ("dialogo", "esperando")):
            siguiente = elegir_plano(juego, texto, nombre, getattr(self, "tipo", None))
            fondo = fondo_intervencion(juego, texto, nombre)
            if self._clave_preparada != siguiente or (fondo and self.fondo != fondo):
                # Captura lo que se estaba viendo antes de cambiar texto o actores.
                self.transicion_plano.capturar(self)
        self.efectos_narrativos.detener()
        self._audiovisual_iniciado = False
        if self.publicacion_telefono is not None:
            self.publicacion_telefono.show()
        if hasattr(self.window(), "audio"):
            self.window().audio.detener_voz()
        if self.animacion is not None:
            self.animacion.stop()

        self.timer_texto.stop()
        self.timer_lectura.stop()
        self.timer_texto.setInterval(max(1, getattr(self.window(), "velocidad_texto", 34)))
        self.estado_escena = "entrando"

        self.texto_completo = texto
        self.escribiendo = False
        self.animando = True

        nombre_normalizado = nombre.upper().strip()
        biblioteca = getattr(self.window(), "biblioteca", None)
        self.dialogo_era_leido = bool(biblioteca and biblioteca.ya_leido(nombre_normalizado or "NARRADOR", texto))
        self.boton_saltar.setEnabled(self.dialogo_era_leido)
        if not self.dialogo_era_leido:
            self.boton_saltar.setChecked(False)
        juego = getattr(self.window(), "juego", None)
        if juego is not None:
            caso = caso_actual(juego)
            self.contexto_escena.setText(f"{caso['acto'].split(' · ')[0]}  /  {caso['titulo']}" if juego.indice_proxima_publicacion else "CIUDAD NOVA  /  Antes de la elección")
            if isinstance(self, EscenaEpilogo):
                self.contexto_escena.setText("EPÍLOGO  /  Ciudad Nova después de las urnas")
            self.contexto_escena.show()
        self.controles_lectura.show()

        self._nombre_hablante = nombre_normalizado or "NARRADOR"
        self.nombre_label.setText(NOMBRES_PERSONAJES.get(nombre_normalizado, nombre_normalizado or "NARRADOR"))
        self.nombre_label.show()

        self.texto_label.clear()
        self.indice_texto = 0
        self.texto_label.show()
        self.pista_continuar.show()
        self.pista_continuar.raise_()

        self.actualizar_geometria()
        self.configurar_personajes_para_hablante(
            nombre_normalizado,
            presentes
        )
        self.preparar_puesta_audiovisual(texto, nombre_normalizado)

        self.franja_superior.raise_()
        self.franja_inferior.raise_()
        self.nombre_label.raise_()
        self.texto_label.raise_()
        self.contexto_escena.raise_()
        self.controles_lectura.raise_()

        ancho = self.width()
        alto = self.height()

        inicio_superior = QRect(
            0,
            -self.altura_franja,
            ancho,
            self.altura_franja
        )

        final_superior = QRect(
            0,
            0,
            ancho,
            self.altura_franja
        )

        inicio_inferior = QRect(
            0,
            alto,
            ancho,
            self.altura_franja
        )

        final_inferior = QRect(
            0,
            alto - self.altura_franja,
            ancho,
            self.altura_franja
        )

        self.franja_superior.setGeometry(inicio_superior)
        self.franja_inferior.setGeometry(inicio_inferior)

        animacion_superior = QPropertyAnimation(
            self.franja_superior,
            b"geometry",
            self
        )
        animacion_superior.setDuration(
            self.DURACION_FRANJAS
        )
        animacion_superior.setStartValue(
            inicio_superior
        )
        animacion_superior.setEndValue(
            final_superior
        )
        animacion_superior.setEasingCurve(
            QEasingCurve.Type.OutCubic
        )

        animacion_inferior = QPropertyAnimation(
            self.franja_inferior,
            b"geometry",
            self
        )
        animacion_inferior.setDuration(
            self.DURACION_FRANJAS
        )
        animacion_inferior.setStartValue(
            inicio_inferior
        )
        animacion_inferior.setEndValue(
            final_inferior
        )
        animacion_inferior.setEasingCurve(
            QEasingCurve.Type.OutCubic
        )

        self.animacion = QParallelAnimationGroup(self)
        self.animacion.addAnimation(animacion_superior)
        self.animacion.addAnimation(animacion_inferior)
        self.animacion.finished.connect(
            self.finalizar_animacion_dialogo
        )
        self.animacion.start()

    def detener_puesta_audiovisual(self):
        self._clave_preparada = None
        self.cine_narrativo.detener()
        self.efectos_narrativos.detener()
        self.fondo_label.show()
        self._audiovisual_iniciado = False

    def preparar_puesta_audiovisual(self, texto, nombre):
        from interfaz.escenas.resultado import EscenaResultado
        """Cubre la escena con el primer fotograma antes de cualquier espera."""
        ventana = self.window()
        reducir = getattr(ventana, "reducir_movimiento", False)
        activo = getattr(ventana, "animar_fondos", True)
        self.cine_narrativo.configurar(reducir_movimiento=reducir, activo=activo)
        self.efectos_narrativos.configurar(reducir_movimiento=reducir, activo=activo)
        juego = getattr(ventana, "juego", None)
        es_visual = campana_visual(juego)
        cambio_fondo = False
        if es_visual:
            self.cine_narrativo._catalogo.update(CATALOGO_PULIDO)
            nuevo_fondo = fondo_intervencion(juego, texto, nombre)
            cambio_fondo = bool(nuevo_fondo and nuevo_fondo != self.fondo)
            if not hasattr(self, "transicion_plano"):
                self.transicion_plano = TransicionNarrativa(self)
            self.transicion_plano.configurar(reducir_movimiento=reducir)
            if cambio_fondo:
                self.fondo = nuevo_fondo
                self.actualizar_fondo()
        clave = clave_cinematica(texto, nombre, juego)
        if clave is None:
            clave = clave_personaje_extendido(texto, nombre, juego)
        if clave is None:
            from interfaz.novela.guion import clave_extension
            clave = clave_extension(texto, nombre, juego)
        if isinstance(self, EscenaEpilogo) and self.dialogo_actual == 0:
            clave = "epilogo_" + clave_final(juego, juego.resultado_electoral())
        if isinstance(self, EscenaResultado) and self.tipo == 1:
            clave = clave_accion_extendida(juego)
            # Una partida antigua puede tener un narrador distinto al actor.
            # Sólo se ilustra la acción cuyo personaje coincide con esta voz.
            if clave and CORTES_ACCIONES[clave]["nombre"] != nombre.upper().strip():
                clave = None
        apertura_final = isinstance(self, EscenaEpilogo) and self.dialogo_actual == 0
        if es_visual and not apertura_final:
            clave = elegir_plano(juego, texto, nombre,
                                 self.tipo if isinstance(self, EscenaResultado) else None)
        lista = self.cine_narrativo._catalogo
        preparada = (clave and (self._clave_preparada == clave and self.cine_narrativo.activa
                                or self.cine_narrativo.iniciar(clave, reproducir=False)))
        if preparada:
            self._clave_preparada = clave
            # La siguiente intervención volverá a introducir a sus actores.
            for personaje in self.personajes.values():
                for animacion in (personaje.animacion_fade, personaje.animacion_dim,
                                  personaje.animacion_entrada, personaje.animacion_salida):
                    if animacion is not None:
                        animacion.stop()
                personaje.hide()
            self.personajes_activos.clear()
            self.personajes_en_escena.clear()
            if self.publicacion_telefono is not None:
                self.publicacion_telefono.hide()
            # El video y su cartel cubren el fondo: ocultarlo suspende también
            # sus partículas y evita renderizar dos ambientes simultáneos.
            if not self.cine_narrativo._poster.imagen.isNull():
                self.fondo_label.hide()
            self.cine_narrativo.raise_()
            self.contexto_escena.setText(lista[clave]["titulo"])
            # El corte ya incorpora su rótulo; deja el encuadre libre para
            # evitar dos títulos superpuestos sobre la misma imagen.
            self.contexto_escena.hide()
        else:
            self._clave_preparada = None
            self.cine_narrativo.detener()
            self.fondo_label.show()
        self.actualizar_pista_corte()
        for elemento in (self.franja_superior, self.franja_inferior, self.nombre_label,
                         self.texto_label, self.pista_continuar, self.contexto_escena,
                         self.controles_lectura):
            elemento.raise_()

        if es_visual and hasattr(self, "transicion_plano"):
            self.transicion_plano.revelar(reducir_movimiento=reducir)

    def corte_accion_pendiente(self):
        cine = self.cine_narrativo
        return bool(self._clave_preparada in (CORTES_ACCIONES.keys() | CORTES_EPILOGO.keys()) and cine.activa
                    and cine._ruta_video is not None and not cine._reducir
                    and cine._habilitada and cine.estado not in ("finalizada", "error"))

    def actualizar_pista_corte(self):
        if hasattr(self, "pista_continuar"):
            self.pista_continuar.setText("La acción está en curso…" if self.corte_accion_pendiente()
                                         else "ESPACIO · revelar / continuar")

    def estado_corte_cambiado(self, estado):
        self.actualizar_pista_corte()
        if estado in ("finalizada", "error") and hasattr(self, "timer_lectura"):
            self.programar_lectura()

    def iniciar_puesta_audiovisual(self):
        from interfaz.escenas.resultado import EscenaResultado
        """Arranca el plano ya preparado junto con la voz, tras entrar el panel."""
        if self.lectura_pausada or self._audiovisual_iniciado:
            return
        self._audiovisual_iniciado = True
        if self._clave_preparada is None:
            self.preparar_puesta_audiovisual(self.texto_completo, self.hablante_actual)
        clave = self._clave_preparada
        if clave:
            self.cine_narrativo.reanudar()
        juego = getattr(self.window(), "juego", None)
        tipo_resultado = self.tipo if isinstance(self, EscenaResultado) else None
        efecto = efecto_visual_dialogo(juego, self.texto_completo,
                                      self.hablante_actual, tipo_resultado)
        if efecto:
            self.efectos_narrativos.reproducir(efecto, duracion=7.5 if clave else 5.0,
                                             intensidad=.58 if clave else .75)
            self.efectos_narrativos.raise_()
        # Las capas de vídeo y partículas nunca se superponen a la lectura.
        for elemento in (self.franja_superior, self.franja_inferior, self.nombre_label,
                         self.texto_label, self.pista_continuar, self.contexto_escena,
                         self.controles_lectura):
            elemento.raise_()

    def finalizar_animacion_dialogo(self):
        if self.estado_escena == "inactiva":
            return
        self.animando = False
        self.estado_escena = "dialogo"
        # El HUD o un resize pueden cambiar el área disponible durante la
        # entrada. El endValue de la animación conserva la altura anterior;
        # fija marco y etiquetas al mismo rectángulo una vez completada.
        self.actualizar_geometria()
        self.escribiendo = True
        self.hablante_actual = getattr(self, "_nombre_hablante", self.nombre_label.text() or "NARRADOR")
        if self.window().isMinimized() and not self.lectura_pausada:
            self._reanudar_al_restaurar = self.window().pausar_lectura_modal()
        if self.lectura_pausada:
            return
        self.iniciar_puesta_audiovisual()
        if hasattr(self.window(), "audio"):
            self.window().audio.narrar(self.texto_completo, self.hablante_actual)
            efecto = efecto_dialogo(self.texto_completo)
            if efecto:
                self.window().audio.reproducir_efecto(efecto)
        self.pista_continuar.raise_()
        if getattr(self.window(), "velocidad_texto", 34) == 0:
            self.revelar_texto()
        else:
            self.timer_texto.start()
            self.programar_lectura()

    def registrar_lectura(self):
        if self.lectura_pausada:
            return
        ventana = self.window()
        nombre = self.hablante_actual or "NARRADOR"
        if hasattr(ventana, "biblioteca"):
            ventana.biblioteca.marcar(nombre, self.texto_completo)
            entrada = (nombre, self.texto_completo)
            if not ventana.historial_dialogos or ventana.historial_dialogos[-1] != entrada:
                ventana.historial_dialogos.append(entrada)
                ventana.historial_dialogos[:] = ventana.historial_dialogos[-500:]

    def revelar_texto(self):
        self.timer_texto.stop()
        self.indice_texto = len(self.texto_completo)
        self.texto_label.setText(self.texto_completo)
        self.escribiendo = False
        self.estado_escena = "esperando"
        self.registrar_lectura()
        self.programar_lectura()

    def programar_lectura(self, _=None):
        self.timer_lectura.stop()
        if self.estado_escena not in ("dialogo", "esperando") or self.animando:
            return
        if self.boton_saltar.isChecked() and self.dialogo_era_leido:
            self.timer_lectura.start(120)
        elif self.boton_auto.isChecked() and not self.escribiendo:
            self.timer_lectura.start(max(1800, min(14000, len(self.texto_completo)*65)))

    def paso_lectura(self):
        if self.lectura_pausada or not self.isVisible() or self.estado_escena not in ("dialogo", "esperando"):
            return
        if self.corte_accion_pendiente():
            self.timer_lectura.start(200)
            return
        if (self.boton_auto.isChecked() and not self.boton_saltar.isChecked()
                and getattr(getattr(self.window(), "audio", None), "hablando", False) is True):
            self.timer_lectura.start(200)
            return
        if self.boton_auto.isChecked() or (self.boton_saltar.isChecked() and self.dialogo_era_leido):
            self.avanzar()

    def escribir_caracter(self):
        if self.lectura_pausada:
            return
        self.indice_texto = min(len(self.texto_completo), self.indice_texto + 1)
        self.texto_label.setText(self.texto_completo[:self.indice_texto])
        if self.indice_texto >= len(self.texto_completo):
            self.timer_texto.stop()
            self.escribiendo = False
            self.estado_escena = "esperando"
            self.registrar_lectura()
            self.programar_lectura()
        else:
            ultimo = self.texto_completo[self.indice_texto-1]
            velocidad = getattr(self.window(), "velocidad_texto", 34)
            if velocidad == 0:
                self.revelar_texto()
            else:
                self.timer_texto.setInterval(round(velocidad * (5.6 if ultimo in ".!?" else 2.8 if ultimo in ",;:" else 1)))

    def finalizar_escena(self):
        if hasattr(self, "transicion_plano"):
            self.transicion_plano.cancelar()
        self.detener_puesta_audiovisual()
        self._reanudar_al_restaurar = None
        self.estado_escena = "inactiva"
        self.lectura_pausada = False
        self.animando = True
        self.timer_inicio.stop()
        self.timer_texto.stop()
        self.timer_lectura.stop()
        self.boton_auto.setChecked(False)
        self.boton_saltar.setChecked(False)
        self.contexto_escena.hide()
        self.controles_lectura.hide()
        if hasattr(self.window(), "audio"):
            self.window().audio.detener_voz()
        self.pista_continuar.hide()
        if self.animacion is not None:
            self.animacion.stop()
        for personaje in self.personajes.values():
            personaje.establecer_hablando(False)
            for animacion in (personaje.animacion_fade, personaje.animacion_dim,
                              personaje.animacion_entrada, personaje.animacion_salida):
                if animacion is not None:
                    animacion.stop()

    def hideEvent(self, event):
        if self.window().isMinimized() and self.estado_escena != "inactiva":
            if not self.lectura_pausada:
                balance = getattr(self, "balance", None)
                self._balance_pausado_al_minimizar = bool(balance and balance._pausado)
                self._reanudar_al_restaurar = self.window().pausar_lectura_modal()
        else:
            self._reanudar_al_restaurar = None
            self.finalizar_escena()
        super().hideEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        reanudar = getattr(self, "_reanudar_al_restaurar", None)
        if reanudar is not None and not self.window().isMinimized():
            self._reanudar_al_restaurar = None
            reanudar()
            if self._balance_pausado_al_minimizar and getattr(self, "balance", None) is not None:
                self.balance.pausar()

    def avanzar(self):
        if self.animando or self.lectura_pausada:
            return

        if self.estado_escena not in ("dialogo", "esperando"):
            return
        if self.escribiendo:
            self.revelar_texto()
            return

        if self.corte_accion_pendiente():
            return

        self.timer_lectura.stop()
        self.animando = True
        self.dialogo_terminado.emit()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.avanzar()
            event.accept()
            return

        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            event.accept()
            return
        if event.key() in (
            Qt.Key.Key_Space,
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter
        ):
            self.avanzar()
            event.accept()
            return

        super().keyPressEvent(event)


class EscenaNarracion(EscenaCinematica):

    def __init__(
        self,
        fondo,
        texto,
        siguiente,
        accion_al_comenzar=None,
        parent=None
    ):
        super().__init__(
            fondo,
            parent
        )

        self.texto_inicial = texto
        self.nombre_inicial = "NARRADOR"

        self.siguiente = siguiente
        self.accion_al_comenzar = accion_al_comenzar

        self.dialogo_terminado.connect(
            self.terminar_escena
        )

    def comenzar_escena(self):
        if self.accion_al_comenzar is not None:
            self.accion_al_comenzar()

        super().comenzar_escena()

    def terminar_escena(self):
        ventana = self.window()

        if hasattr(
            ventana,
            "mostrar_escena"
        ):
            ventana.mostrar_escena(
                self.siguiente
            )


class EscenaDialogo(EscenaCinematica):

    def __init__(self, parent=None):
        super().__init__(
            "assets/fondos/Escena 4.png",
            parent
        )

        self.dialogos = []
        self.dialogo_actual = 0
        self.presentes_dialogo = set()

        self.dialogo_terminado.connect(
            self.siguiente_dialogo
        )

    def preparar_dialogos(self):
        ventana = self.window()
        self.fondo = escenario_actual(ventana.juego)["fondo"]

        publicacion = None

        if hasattr(ventana, "juego"):
            publicacion = (
                ventana.juego.obtener_publicacion_actual()
            )

        if publicacion is None:
            texto_publicacion = (
                "una publicación que está circulando por Civitas"
            )
        else:
            texto_publicacion = (
                f'"{publicacion.texto}"'
            )

        self.dialogos = dialogos_publicacion(ventana.juego)

        self.presentes_dialogo = {
            nombre.upper()
            for nombre, _ in self.dialogos
            if nombre.upper() in self.personajes or nombre.lower() in ACTORES_NUEVOS
        }
        self._npc_interlocutor = None

    def comenzar_escena(self):
        self.preparar_dialogos()
        self.timer_inicio.stop()
        self.timer_texto.stop()
        self.dialogo_actual = 0

        if self.animacion is not None:
            self.animacion.stop()

        self.animando = True
        self.estado_escena = "preparando"
        self.escribiendo = False

        self.ocultar_personajes()

        for personaje in self.personajes.values():
            personaje.efecto_fade.setOpacity(0.0)
            personaje.efecto_dimming.setOpacity(0.0)
            personaje.hide()

        self.mostrar_fondo()

        self.nombre_label.clear()
        self.texto_label.clear()
        self.nombre_label.hide()
        self.texto_label.hide()

        self.actualizar_geometria()

        self.franja_superior.setGeometry(
            0,
            -self.altura_franja,
            self.width(),
            self.altura_franja
        )
        self.franja_inferior.setGeometry(
            0,
            self.height(),
            self.width(),
            self.altura_franja
        )

        if self.dialogos:
            nombre, texto = self.dialogos[0]
            self.preparar_puesta_audiovisual(texto, nombre)
        self.timer_inicio.start(self.TIEMPO_ANTES_DE_HABLAR)

        self.setFocus()

    def preparar_dialogo(self):
        self.mostrar_dialogo_actual()

    def mostrar_dialogo_actual(self):
        if self.dialogo_actual >= len(self.dialogos):
            self.terminar_escena()
            return

        nombre, texto = self.dialogos[
            self.dialogo_actual
        ]

        self.iniciar_dialogo(
            texto,
            nombre,
            self.presentes_dialogo
        )

    def siguiente_dialogo(self):
        self.dialogo_actual += 1

        if self.dialogo_actual >= len(self.dialogos):
            self.ocultar_personajes()
            self.terminar_escena()
            return

        self.ocultar_franjas(
            self.mostrar_dialogo_actual
        )

    def ocultar_franjas(self, siguiente):
        self.animando = True
        self.estado_escena = "saliendo"
        if self.animacion is not None:
            self.animacion.stop()
        ancho = self.width()
        alto = self.height()

        animacion_superior = QPropertyAnimation(
            self.franja_superior,
            b"geometry",
            self
        )
        animacion_superior.setDuration(1 if getattr(self.window(), "reducir_movimiento", False) else 300)
        animacion_superior.setStartValue(
            QRect(
                0,
                0,
                ancho,
                self.altura_franja
            )
        )
        animacion_superior.setEndValue(
            QRect(
                0,
                -self.altura_franja,
                ancho,
                self.altura_franja
            )
        )
        animacion_superior.setEasingCurve(
            QEasingCurve.Type.InCubic
        )

        animacion_inferior = QPropertyAnimation(
            self.franja_inferior,
            b"geometry",
            self
        )
        animacion_inferior.setDuration(1 if getattr(self.window(), "reducir_movimiento", False) else 300)
        animacion_inferior.setStartValue(
            QRect(
                0,
                alto - self.altura_franja,
                ancho,
                self.altura_franja
            )
        )
        animacion_inferior.setEndValue(
            QRect(
                0,
                alto,
                ancho,
                self.altura_franja
            )
        )
        animacion_inferior.setEasingCurve(
            QEasingCurve.Type.InCubic
        )

        grupo = QParallelAnimationGroup(self)
        grupo.addAnimation(animacion_superior)
        grupo.addAnimation(animacion_inferior)
        grupo.finished.connect(siguiente)

        self.animacion = grupo
        grupo.start()

    def terminar_escena(self):
        ventana = self.window()

        if hasattr(ventana, "mostrar_escena"):
            ventana.mostrar_escena(
                ventana.ESCENA_ACCION
            )


class EscenaEpilogo(EscenaDialogo):
    """Desenlace hablado con las mismas ramas que conserva el panel final."""
    def preparar_dialogos(self):
        from interfaz.novela.guion import dialogos_epilogo as epilogo_extendido
        self.fondo = "assets/expansion/fondos/plaza_noche.png"
        self.dialogos = epilogo_extendido(self.window().juego)
        self.presentes_dialogo = {nombre for nombre, _ in self.dialogos if nombre != "NARRADOR"}
        self._npc_interlocutor = None

    def terminar_escena(self):
        self.window().mostrar_escena(self.window().ESCENA_FIN)
