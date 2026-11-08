"""interfaz.ventana: presentación separada de las reglas del juego."""
from PyQt6.QtWidgets import QMainWindow, QWidget, QLabel, QPushButton, QStackedWidget, QFrame, QGraphicsOpacityEffect, QToolBar, QFileDialog, QMessageBox, QToolButton, QMenu, QSizePolicy
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QAbstractAnimation, QEasingCurve, pyqtSignal
from infraestructura.recursos import ruta_recurso
from interfaz.componentes.arte import aplicar_estilo, decorar_botones, icono_arte, cargar_tipografias, FUENTE_UI
from interfaz.componentes.accesibilidad import MODOS_DALTONISMO
from interfaz.escenas.red import EscenaRed
from interfaz.dialogos import DialogoRol, DialogoRed, mostrar_ayuda, mostrar_configuracion
from juego.cuaderno import recuerdos
from juego.lectura import BibliotecaLectura
from interfaz.dialogo_cuaderno import DialogoCuaderno
from interfaz.cinematica.ambiente import FondoVivo
from interfaz.componentes.personajes_animados import SpriteExpresivo
from juego.puesta_escena import escenario_actual
from interfaz.cinematica.reproductor import CapaCinematica
from interfaz.cinematica.efectos import CapaEfectos
from interfaz.componentes.resultados import BalanceAnimado
from audio.gestor_audio import GestorAudio
from interfaz.componentes.hud import HudCiudad
from interfaz.escenas.final import EscenaFin
from juego.partida import Juego
from interfaz.escenas.accion import EscenaAccion
from interfaz.escenas.arbol import EscenaArbol
from interfaz.escenas.cinematica import EscenaCinematica
from interfaz.escenas.cinematica import EscenaDialogo
from interfaz.escenas.cinematica import EscenaEpilogo
from interfaz.escenas.inicio import EscenaInicio
from interfaz.escenas.cinematica import EscenaNarracion
from interfaz.escenas.resultado import EscenaResultado


class VentanaPrincipal(QMainWindow):

    mensaje_red = pyqtSignal(dict)

    ESCENA_INICIO = 0
    ESCENA_NARRACION_1 = 1
    ESCENA_NARRACION_2 = 2
    ESCENA_NARRACION_3 = 3
    ESCENA_DIALOGO = 4
    ESCENA_ACCION = 5
    ESCENA_RESULTADO_1 = 6
    ESCENA_RESULTADO_2 = 7
    ESCENA_RESULTADO_3 = 8
    ESCENA_ARBOL = 9
    ESCENA_FIN = 10
    ESCENA_GRAFO = 11
    ESCENA_EPILOGO = 12

    def __init__(self):
        super().__init__()
        cargar_tipografias()

        self.setWindowTitle(
            "CIVICA — Alcalde Digital"
        )

        self.setMinimumSize(
            1100,
            700
        )

        self.pantalla_completa = False
        self.sin_limite = False
        self.reducir_movimiento = False
        self.cliente_red = None
        self.mi_id = None
        self.token_red = None
        self.datos_conexion = None
        self.recuperada_red = False
        self.sesion_red = 0
        self.servidor_red = None
        self.revision_red = -1
        self.fase_red = None
        self.alto_contraste = False
        self.sprites_sobre_ilustracion = False
        self.modo_daltonismo = "normal"
        self.voces_activadas = True
        self.animar_fondos = True
        self.animar_personajes = True
        self.velocidad_texto = 34
        self.biblioteca = BibliotecaLectura()
        self.historial_dialogos = []
        self.pistas_consultadas = set()
        self.cuaderno = None
        self.dialogo_red = None
        self.mensaje_red.connect(self.recibir_mensaje)
        self.audio = GestorAudio(self)
        from infraestructura.configuracion import cargar
        preferencias = cargar()
        velocidad = preferencias.get("velocidad_texto", 34)
        self.velocidad_texto = velocidad if velocidad in (0, 16, 34, 50) else 34
        for categoria, valor in preferencias.get("volumenes", {}).items():
            if categoria in self.audio.volumenes and isinstance(valor, (int, float)):
                self.audio.configurar(categoria, valor)
        self.audio.silenciar(preferencias.get("silenciado", False))
        for nombre in ("sin_limite", "reducir_movimiento", "alto_contraste", "sprites_sobre_ilustracion", "animar_fondos", "animar_personajes"):
            setattr(self, nombre, bool(preferencias.get(nombre, nombre in ("animar_fondos", "animar_personajes"))))
        modo = preferencias.get("modo_daltonismo", "normal")
        self.modo_daltonismo = modo if modo in MODOS_DALTONISMO else "normal"
        self.voces_activadas = bool(preferencias.get("voces_activadas", True))
        self.audio.configurar_voces(self.voces_activadas)

        self.juego = Juego(campana="extendida")

        self.escenas = QStackedWidget()

        self.escena_inicio = EscenaInicio()

        self.escena_narracion_1 = EscenaNarracion(
            "assets/fondos/Escena 1.jfif",
            "Faltan cuarenta y ocho horas para la elección. En Ciudad Nova, cada teléfono cuenta una versión distinta de lo que está pasando.",
            self.ESCENA_NARRACION_2
        )

        self.escena_narracion_2 = EscenaNarracion(
            "assets/fondos/Escena 2.png",
            "Una notificación interrumpe la tarde frente al Café Central. En el grupo del barrio, varias familias están compartiendo el mismo mensaje.",
            self.ESCENA_NARRACION_3
        )

        self.escena_narracion_3 = EscenaNarracion(
            "assets/fondos/Escena 3.png",
            "El mensaje acusa a Juan de querer cerrar el colegio. Nadie adjunta el comunicado original. El botón de compartir está a un toque.",
            self.ESCENA_DIALOGO,
            accion_al_comenzar=(
                self.juego.iniciar_primera_publicacion
            )
        )

        self.escena_dialogo = EscenaDialogo()

        self.escena_accion = EscenaAccion(
            self.juego
        )

        self.escena_resultado_1 = EscenaResultado(
            "assets/fondos/Escena 6.png",
            self.ESCENA_RESULTADO_2,
            1
        )

        self.escena_resultado_2 = EscenaResultado(
            "assets/fondos/Escena 7.png",
            self.ESCENA_RESULTADO_3,
            2
        )

        self.escena_resultado_3 = EscenaResultado(
            "assets/fondos/Escena 8.png",
            self.ESCENA_ARBOL,
            3
        )

        self.escena_arbol = EscenaArbol(
            self.juego
        )

        self.escena_fin = EscenaFin()
        self.escena_epilogo = EscenaEpilogo()
        self.escena_red = EscenaRed(self.juego)
        self.escena_red.continuar.connect(self.continuar_desde_arbol)

        for escena in (
            self.escena_inicio,
            self.escena_narracion_1,
            self.escena_narracion_2,
            self.escena_narracion_3,
            self.escena_dialogo,
            self.escena_accion,
            self.escena_resultado_1,
            self.escena_resultado_2,
            self.escena_resultado_3,
            self.escena_arbol,
            self.escena_fin,
            self.escena_red,
            self.escena_epilogo
        ):
            self.escenas.addWidget(escena)

        self.setCentralWidget(
            self.escenas
        )

        barra = QToolBar("CIVICA")
        self.barra = barra
        barra.setIconSize(QSize(21, 21))
        barra.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        barra.setMovable(False)
        barra.setStyleSheet(f"QToolBar {{background:#142637; spacing:8px; padding:5px 14px; border-bottom:1px solid #9a744d;}} QToolButton {{color:#f6e8cd; font:16px '{FUENTE_UI}'; padding:6px 15px; min-height:28px; border:0;}}")
        marca = QLabel("CIVICA   /   Ciudad Nova")
        marca.setStyleSheet(f"color:#e5c797; font:700 16px '{FUENTE_UI}'; padding:0 12px;")
        barra.addWidget(marca)
        self.menu_partida = QToolButton()
        self.menu_partida.setText("Partida")
        self.menu_partida.setMinimumWidth(120)
        self.menu_partida.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QMenu(self.menu_partida)
        self.acciones_partida = {}
        for texto, clave, funcion in (("Guardar partida", "guardar", self.guardar_partida),
                                      ("Cargar partida", "cargar", self.cargar_partida),
                                      ("Reconectar sala", "reconectar", self.reconectar_red),
                                      ("Volver a la portada", "portada", self.volver_portada)):
            accion = menu.addAction(icono_arte(clave), texto, funcion)
            self.acciones_partida[clave] = accion
        self.menu_partida.setMenu(menu)
        self.accion_menu_partida = barra.addWidget(self.menu_partida)
        self.boton_cuaderno = QToolButton()
        self.boton_cuaderno.setText("Cuaderno")
        self.boton_cuaderno.setMinimumWidth(145)
        self.boton_cuaderno.setToolTip("Fuentes, personajes, historial y galería de escenas")
        self.boton_cuaderno.setAccessibleName("Abrir cuaderno de Ciudad Nova")
        self.boton_cuaderno.clicked.connect(lambda: self.abrir_cuaderno(0))
        barra.addWidget(self.boton_cuaderno)
        espacio = QWidget()
        espacio.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        barra.addWidget(espacio)
        self.boton_configuracion = QToolButton()
        self.boton_configuracion.setText("Configuración")
        self.boton_configuracion.setMinimumWidth(215)
        self.boton_configuracion.setAccessibleName("Configuración y accesibilidad")
        self.boton_configuracion.setIcon(icono_arte("ajustes"))
        self.boton_configuracion.setIconSize(QSize(26, 26))
        self.boton_configuracion.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.boton_configuracion.clicked.connect(lambda: mostrar_configuracion(self))
        barra.addWidget(self.boton_configuracion)

        self.addToolBar(barra)
        self.statusBar().setStyleSheet("background:#142537;color:#fff4e9;")
        self.indicadores = QLabel()
        self.indicadores.setStyleSheet("color:#fff4e9; padding:3px;")
        self.indicadores.hide()
        self.hud = HudCiudad(self)
        self.statusBar().addPermanentWidget(self.hud, 1)
        self.statusBar().setSizeGripEnabled(False)
        self.audio.aviso.connect(lambda texto: self.statusBar().showMessage("Civitas · " + texto, 2200))
        self.audio.voz_iniciada.connect(self.iniciar_gesto_voz)
        self.audio.voz_finalizada.connect(self.terminar_gesto_voz)
        self.audio.segmento_iniciado.connect(self.sincronizar_balance)
        self.audio.secuencia_finalizada.connect(self.finalizar_balance_voz)
        if hasattr(self.audio, "nivel_voz"):
            self.audio.nivel_voz.connect(self.sincronizar_boca)
        aplicar_estilo(self)
        menu.setStyleSheet(f"QMenu {{background:#193548; color:#fff2dc; padding:8px; font:17px '{FUENTE_UI}'; border:1px solid #bd8855;}} QMenu::item {{padding:12px 24px;}} QMenu::item:selected {{background:#365e70;}}")
        self.aplicar_accesibilidad()
        self.velo_transicion = QFrame(self.escenas)
        self.velo_transicion.setStyleSheet("background:#02060b;border:0;")
        self.velo_transicion.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.efecto_transicion = QGraphicsOpacityEffect(self.velo_transicion)
        self.velo_transicion.setGraphicsEffect(self.efecto_transicion)
        self.animacion_transicion = QPropertyAnimation(self.efecto_transicion, b"opacity", self)
        self.animacion_transicion.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animacion_transicion.valueChanged.connect(
            lambda _: self.velo_transicion.setGeometry(self.escenas.rect()))
        self.animacion_transicion.finished.connect(self.velo_transicion.hide)
        self.velo_transicion.hide()
        for boton in self.findChildren(QPushButton):
            boton.clicked.connect(lambda: self.audio.reproducir_efecto("clic"))

        self.escena_inicio.continuar.connect(
            self.comenzar_juego
        )

        self.mostrar_escena(
            self.ESCENA_INICIO
        )

    def comenzar_juego(self):
        self.cerrar_red()
        if self.juego.indice_proxima_publicacion:
            self.establecer_juego(Juego(campana="extendida"))
        dialogo = DialogoRol(self)
        if not dialogo.exec():
            return
        self.pistas_consultadas.clear()
        self.historial_dialogos.clear()
        self.juego.seleccionar_rol(dialogo.roles.currentData())
        self.mostrar_escena(
            self.ESCENA_NARRACION_1
        )

    def showEvent(self, event):
        super().showEvent(event)
        # QToolBar puede crear sus botones al mostrarse por primera vez.
        decorar_botones(self.barra)

    def mostrar_escena(self, indice):
        if self.cuaderno is not None:
            self.cuaderno.close()
            self.cuaderno = None
        for recuerdo in recuerdos(self.juego):
            self.biblioteca.desbloquear(recuerdo["id"])
        anterior = self.escenas.currentWidget()
        if hasattr(anterior, "finalizar_escena"):
            anterior.finalizar_escena()
        self.escenas.setCurrentIndex(
            indice
        )
        en_partida = indice != self.ESCENA_INICIO
        self.accion_menu_partida.setVisible(en_partida)
        self.statusBar().setVisible(en_partida)
        self.acciones_partida["reconectar"].setVisible(self.datos_conexion is not None)
        for clave in ("guardar", "cargar"):
            self.acciones_partida[clave].setEnabled(self.cliente_red is None)

        escena = (
            self.escenas.currentWidget()
        )

        if hasattr(
            escena,
            "comenzar_escena"
        ):
            escena.comenzar_escena()

        elif hasattr(
            escena,
            "mostrar"
        ):
            escena.mostrar()

        escena.setFocus()
        if hasattr(self, "audio"):
            pista = "eleccion" if indice in (self.ESCENA_FIN, self.ESCENA_EPILOGO) else "investigacion" if indice in (self.ESCENA_DIALOGO, self.ESCENA_GRAFO) else "ciudad"
            self.audio.cambiar_pista(pista)
            ambiente = (escenario_actual(self.juego)["sonido"] if indice in
                        (self.ESCENA_DIALOGO, self.ESCENA_ACCION, self.ESCENA_RESULTADO_1,
                         self.ESCENA_RESULTADO_2, self.ESCENA_RESULTADO_3) else
                        "noche" if indice in (self.ESCENA_FIN, self.ESCENA_EPILOGO) else
                        "oficina" if indice in (self.ESCENA_ARBOL, self.ESCENA_GRAFO) else
                        "calle" if indice == self.ESCENA_NARRACION_2 else "plaza")
            self.audio.cambiar_pista(ambiente, "ambiente")
            if indice == self.ESCENA_ACCION:
                self.audio.reproducir_efecto("notificacion")
            elif indice == self.ESCENA_RESULTADO_1:
                self.audio.reproducir_efecto(self.juego.ultima_accion or "resultado")
            elif indice == self.ESCENA_FIN:
                self.audio.reproducir_efecto("recompensa")
            elif indice == self.ESCENA_NARRACION_2:
                self.audio.reproducir_efecto("pasos_calle")
            elif indice == self.ESCENA_DIALOGO and self.juego.indice_proxima_publicacion == 2:
                self.audio.reproducir_efecto("puerta_abrir")
            self.actualizar_estado()
        self.animacion_transicion.stop()
        if en_partida and not self.reducir_movimiento:
            self.velo_transicion.setGeometry(self.escenas.rect())
            self.velo_transicion.show()
            self.velo_transicion.raise_()
            self.animacion_transicion.setDuration(1500 if indice == self.ESCENA_NARRACION_1 else 700)
            self.animacion_transicion.setStartValue(1.0)
            self.animacion_transicion.setEndValue(0.0)
            self.animacion_transicion.start()
        else:
            self.velo_transicion.hide()

    def abrir_cuaderno(self, pestana=0):
        self.audio.reproducir_efecto("pagina")
        if self.cuaderno is not None:
            self.cuaderno.close()
        reanudar = self.pausar_lectura_modal()
        self.cuaderno = DialogoCuaderno(self, pestana)
        dialogo = self.cuaderno
        def volver_a_lectura():
            if self.cuaderno is dialogo:
                self.cuaderno = None
            reanudar()
        self.cuaderno.finished.connect(volver_a_lectura)
        self.cuaderno.show()

    def pausar_lectura_modal(self):
        escena = self.escenas.currentWidget()
        juego_pausado = self.juego
        texto = getattr(escena, "texto_completo", "")
        tenia_voz = getattr(self.audio, "hablando", False) is True
        candidatas = escena.findChildren(QAbstractAnimation)
        for atributo in ("animacion", "animacion_personajes"):
            animacion = getattr(escena, atributo, None)
            if isinstance(animacion, QAbstractAnimation) and animacion not in candidatas:
                candidatas.append(animacion)
        animaciones_pausadas = []
        for animacion in candidatas:
            # Un grupo debe conservar el reloj de todos sus hijos al reanudar.
            while animacion.group() is not None:
                animacion = animacion.group()
            if (animacion not in animaciones_pausadas
                    and animacion.state() == QAbstractAnimation.State.Running):
                animaciones_pausadas.append(animacion)
                animacion.pause()
        if isinstance(escena, EscenaCinematica):
            escena.boton_auto.setChecked(False)
            escena.boton_saltar.setChecked(False)
            escena.lectura_pausada = True
            escena.timer_texto.stop()
            escena.timer_inicio.stop()
            escena.cine_narrativo.pausar()
            if isinstance(escena, EscenaResultado) and escena.balance is not None:
                escena.balance.pausar()
        for capa in escena.findChildren(CapaEfectos):
            capa.pausar()
        self.audio.detener_voz()
        def reanudar():
            if (self.juego is not juego_pausado or self.escenas.currentWidget() is not escena
                    or getattr(escena, "texto_completo", "") != texto):
                return
            self.audio.detener_voz()  # Termina una posible muestra de Configuración.
            for animacion in animaciones_pausadas:
                try:
                    if animacion.state() == QAbstractAnimation.State.Paused:
                        animacion.resume()
                except RuntimeError:
                    # Un cambio visual puede haber destruido una animación transitoria.
                    continue
            if isinstance(escena, EscenaCinematica):
                escena.lectura_pausada = False
                if escena.estado_escena == "preparando":
                    escena.timer_inicio.start(1)
                elif escena.estado_escena in ("dialogo", "esperando"):
                    if isinstance(escena, EscenaResultado) and escena.balance is not None:
                        if not escena._balance_en_curso:
                            escena.finalizar_animacion_dialogo()
                        elif not escena.balance.completo:
                            escena.narrar_balance()
                        else:
                            escena.reanudar_balance()
                        escena.setFocus()
                        return
                    if not escena._audiovisual_iniciado:
                        escena.iniciar_puesta_audiovisual()
                    else:
                        escena.cine_narrativo.reanudar()
                    if tenia_voz or escena.escribiendo:
                        self.audio.narrar(escena.texto_completo, escena.hablante_actual)
                    if escena.escribiendo:
                        if self.velocidad_texto == 0:
                            escena.revelar_texto()
                        else:
                            escena.timer_texto.start()
                escena.setFocus()
            for capa in escena.findChildren(CapaEfectos):
                capa.reanudar()
        return reanudar

    def iniciar_gesto_voz(self, hablante):
        escena = self.escenas.currentWidget()
        if isinstance(escena, EscenaCinematica):
            for nombre, personaje in escena.personajes.items():
                personaje.establecer_hablando(nombre == hablante)

    def sincronizar_balance(self, clave):
        escena = self.escenas.currentWidget()
        if isinstance(escena, EscenaResultado):
            escena.segmento_balance(clave)

    def finalizar_balance_voz(self, completada):
        escena = self.escenas.currentWidget()
        if isinstance(escena, EscenaResultado):
            escena.fin_balance_voz(completada)

    def sincronizar_boca(self, nivel):
        escena = self.escenas.currentWidget()
        if isinstance(escena, EscenaCinematica):
            hablante = getattr(self.audio, "hablante_actual", "")
            for nombre, personaje in escena.personajes.items():
                personaje.establecer_hablando(nombre == hablante, nivel if nombre == hablante else 0.0)

    def terminar_gesto_voz(self):
        escena = self.escenas.currentWidget()
        if isinstance(escena, EscenaCinematica):
            for personaje in escena.personajes.values():
                personaje.establecer_hablando(False)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "velo_transicion"):
            self.velo_transicion.setGeometry(self.escenas.rect())

    def continuar_desde_arbol(self):
        if self.escenas.currentWidget() is not self.escena_red:
            return
        if self.cliente_red is not None:
            self.cliente_red.enviar({"tipo": "continuar", "revision": self.revision_red})
            self.escena_red.boton_continuar.setEnabled(False)
            self.escena_red.detalle.setText("Esperando que los demás participantes terminen de revisar el resultado…")
            return
        if self.juego.avanzar_publicacion():
            self.mostrar_escena(
                self.ESCENA_DIALOGO
            )
        else:
            self.mostrar_desenlace()

    def mostrar_desenlace(self):
        self.mostrar_escena(self.ESCENA_EPILOGO if self.juego.campana == "extendida" else self.ESCENA_FIN)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F1:
            mostrar_ayuda(self)
            event.accept()
            return
        if event.key() == Qt.Key.Key_F11:
            self.alternar_pantalla_completa()
            event.accept()
            return

        super().keyPressEvent(event)

    def establecer_juego(self, juego):
        self.juego = juego
        self.escena_accion.juego = juego
        self.escena_arbol.juego = juego
        self.escena_arbol.visualizador.arbol = juego.arbol
        self.escena_red.juego = juego
        self.escena_red.visualizador.grafo = juego.grafo
        self.escena_narracion_3.accion_al_comenzar = juego.iniciar_primera_publicacion
        self.actualizar_estado()

    def actualizar_estado(self):
        if hasattr(self, "hud"):
            self.hud.actualizar(self.juego)
        if hasattr(self, "indicadores"):
            self.indicadores.setText(f"Ciudad Nova · Confianza {self.juego.confianza} · Convivencia {self.juego.convivencia} · Bienestar {self.juego.bienestar_digital} · Información verificada {self.juego.info_verificada} · Desinformación {self.juego.desinformacion} · Conflictos {self.juego.conflictos}")

    def aplicar_accesibilidad(self):
        for balance in self.findChildren(BalanceAnimado):
            balance.configurar(self.reducir_movimiento)
        for fondo in self.findChildren(FondoVivo):
            fondo.configurar(reducir_movimiento=self.reducir_movimiento, activo=self.animar_fondos)
        for actor in self.findChildren(SpriteExpresivo):
            actor.configurar_movimiento(self.reducir_movimiento, self.animar_personajes)
        for capa in self.findChildren(CapaCinematica):
            capa.configurar(reducir_movimiento=self.reducir_movimiento, activo=self.animar_fondos)
        for capa in self.findChildren(CapaEfectos):
            capa.configurar(reducir_movimiento=self.reducir_movimiento, activo=self.animar_fondos)
        for escena in self.escenas.findChildren(EscenaCinematica):
            escena.DURACION_FRANJAS = 1 if self.reducir_movimiento else 450
            escena.TIEMPO_ANTES_DE_HABLAR = 1 if self.reducir_movimiento else 650
            for personaje in escena.personajes.values():
                personaje.reducir_movimiento = self.reducir_movimiento
            escena.actualizar_geometria()
        self.audio.configurar_voces(self.voces_activadas)
        if hasattr(self, "hud"):
            self.hud.actualizar(self.juego)
        self.escena_red.visualizador.update()
        self.escena_arbol.visualizador.update()
        if self.reducir_movimiento:
            self.escena_red.completar()
            if hasattr(self, "animacion_transicion"):
                self.animacion_transicion.stop()
                self.velo_transicion.hide()
        if self.sin_limite:
            self.escena_accion.timer_decision.stop()

    def guardar_partida(self):
        if self.cliente_red is not None:
            self.statusBar().showMessage("En multijugador el servidor conserva el estado oficial.")
            return
        reanudar = self.pausar_lectura_modal()
        try:
            ruta, _ = QFileDialog.getSaveFileName(self, "Guardar partida", ruta_recurso('saves/partida.json'), "Partidas (*.json)")
            if ruta:
                try:
                    self.juego.guardar(ruta)
                    self.statusBar().showMessage("Partida guardada.")
                except (OSError, ValueError) as error:
                    QMessageBox.warning(self, "Guardado", str(error))
        finally:
            reanudar()

    def cargar_partida(self):
        if self.cliente_red is not None:
            return
        reanudar = self.pausar_lectura_modal()
        try:
            ruta, _ = QFileDialog.getOpenFileName(self, "Cargar partida", ruta_recurso('saves'), "Partidas (*.json)")
            if ruta:
                try:
                    juego = Juego.cargar(ruta)
                    self.pistas_consultadas.clear()
                    self.historial_dialogos.clear()
                    self.establecer_juego(juego)
                    indice = self.ESCENA_GRAFO if juego.decision_aplicada else self.ESCENA_DIALOGO
                    if juego.indice_proxima_publicacion == 0:
                        indice = self.ESCENA_INICIO
                    if juego.finalizada:
                        indice = self.ESCENA_FIN
                    self.mostrar_escena(indice)
                except (OSError, ValueError, KeyError, TypeError) as error:
                    QMessageBox.warning(self, "Partida incompatible", str(error))
        finally:
            reanudar()

    def volver_portada(self):
        self.cerrar_red()
        self.mostrar_escena(self.ESCENA_INICIO)

    def abrir_multijugador(self):
        reanudar = self.pausar_lectura_modal()
        try:
            self.dialogo_red = DialogoRed(self)
            if not self.dialogo_red.exec():
                self.cerrar_red()
        finally:
            reanudar()

    def conectar_red(self, crear, host, puerto, nombre, rol):
        self.pistas_consultadas.clear()
        self.historial_dialogos.clear()
        from red.servidor import Servidor
        from red.cliente import Cliente
        self.cerrar_red()
        self.revision_red, self.fase_red = -1, None
        if crear:
            self.servidor_red = Servidor(puerto=puerto, sin_limite=self.sin_limite, campana="extendida")
            self.servidor_red.iniciar()
            puerto = self.servidor_red.puerto
            host = "127.0.0.1"
        sesion = self.sesion_red
        self.cliente_red = Cliente(lambda mensaje: self.mensaje_red.emit(dict(mensaje, sesion=sesion)))
        self.cliente_red.conectar(host, puerto, nombre, rol)
        self.datos_conexion = (host, puerto, nombre, rol)

    def reconectar_red(self):
        from red.cliente import Cliente
        if not self.token_red or not self.datos_conexion:
            self.statusBar().showMessage("Primero únete a una sala de CIVICA.")
            return
        if self.cliente_red is not None and not self.cliente_red.cerrado.is_set():
            self.statusBar().showMessage("La conexión sigue activa.")
            return
        self.sesion_red += 1
        sesion = self.sesion_red
        self.revision_red = -1
        self.cliente_red = Cliente(lambda mensaje: self.mensaje_red.emit(dict(mensaje, sesion=sesion)))
        self.cliente_red.conectar(*self.datos_conexion, token=self.token_red)
        self.statusBar().showMessage("Recuperando tu lugar en la campaña…")

    def enviar_accion(self, accion):
        if self.cliente_red is None or self.juego.jugador.id != self.mi_id:
            return
        if self.cliente_red.enviar({"tipo": "accion", "accion": accion, "publicacion_id": self.juego.publicacion_actual_id}):
            for boton in (self.escena_accion.boton_compartir, self.escena_accion.boton_verificar, self.escena_accion.boton_ignorar, self.escena_accion.boton_reportar):
                boton.setEnabled(False)

    def recibir_mensaje(self, mensaje):
        if mensaje.get("sesion", self.sesion_red) != self.sesion_red:
            return
        tipo = mensaje["tipo"]
        if tipo == "bienvenida":
            self.mi_id = mensaje["id"]
            self.token_red = mensaje.get("token")
            self.recuperada_red = mensaje.get("recuperada", False)
        elif tipo == "sala":
            if self.dialogo_red:
                self.dialogo_red.estado.setText("\n".join(f"{j['nombre']} · {j['rol']}" for j in mensaje["jugadores"]))
        elif tipo == "estado":
            if mensaje["revision"] == self.revision_red:
                if self.escenas.currentWidget() is self.escena_accion and mensaje["fase"] == "jugando":
                    self.escena_accion.actualizar_plazo_red(mensaje.get("plazo_segundos"))
                return
            if mensaje["revision"] <= self.revision_red:
                return
            primero = self.revision_red < 0
            reanudando = self.fase_red == "interrumpida" or self.recuperada_red
            self.revision_red = mensaje["revision"]
            self.fase_red = mensaje["fase"]
            self.establecer_juego(Juego.desde_datos(mensaje["datos"]))
            self.escena_red.boton_continuar.setEnabled(True)
            if self.dialogo_red:
                self.dialogo_red.accept()
            if self.fase_red == "jugando":
                self.mostrar_escena(self.ESCENA_ACCION if reanudando else self.ESCENA_NARRACION_1 if primero else self.ESCENA_DIALOGO)
                if reanudando:
                    self.escena_accion.actualizar_plazo_red(mensaje.get("plazo_segundos"))
                self.recuperada_red = False
            elif self.fase_red == "resultado":
                self.mostrar_escena(self.ESCENA_RESULTADO_1)
            elif self.fase_red == "final":
                self.mostrar_desenlace()
            else:
                # La barrera de reconexión pausa también la presentación.
                # El siguiente estado del servidor reconstruirá su escena.
                self.pausar_lectura_modal()
                self.escena_accion.timer_decision.stop()
                ausentes = ", ".join(mensaje.get("desconectados", []))
                self.statusBar().showMessage(f"Campaña pausada. Esperando reconexión de {ausentes}.")
                self.escena_red.boton_continuar.setEnabled(False)
                for boton in (self.escena_accion.boton_compartir, self.escena_accion.boton_verificar, self.escena_accion.boton_ignorar, self.escena_accion.boton_reportar):
                    boton.setEnabled(False)
            self.recuperada_red = False
        elif tipo in ("error", "desconexion"):
            if tipo == "desconexion" and self.cliente_red is not None:
                self.pausar_lectura_modal()
            self.audio.reproducir_efecto("error")
            self.statusBar().showMessage(mensaje.get("texto", "Error de red"))
            if self.dialogo_red and self.dialogo_red.isVisible():
                self.dialogo_red.estado.setText(mensaje.get("texto", "Sin conexión"))

    def cerrar_red(self):
        self.sesion_red += 1
        if self.cliente_red is not None:
            self.cliente_red.cerrar()
            self.cliente_red = None
        if self.servidor_red is not None:
            self.servidor_red.cerrar()
            self.servidor_red = None
        self.token_red = None
        self.datos_conexion = None

    def closeEvent(self, event):
        self.cerrar_red()
        self.audio.detener()
        for indice in range(self.escenas.count()):
            escena = self.escenas.widget(indice)
            if hasattr(escena, "finalizar_escena"):
                escena.finalizar_escena()
        for fondo in self.findChildren(FondoVivo):
            fondo.configurar(activo=False)
        for actor in self.findChildren(SpriteExpresivo):
            actor.configurar_movimiento(True, False)
        super().closeEvent(event)

    def alternar_pantalla_completa(self):
        if self.pantalla_completa:
            self.showMaximized()
            self.pantalla_completa = False
        else:
            self.showFullScreen()
            self.pantalla_completa = True
