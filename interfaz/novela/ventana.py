"""La novela original con investigación sobre sus escenas, sin sustituir su presentación."""
from __future__ import annotations
import json
from pathlib import Path
from types import MethodType
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from infraestructura.recursos import ruta_recurso
from juego.partida import Juego
from juego.investigacion import SesionInvestigacion
from interfaz.ventana import VentanaPrincipal
from interfaz.dialogos import DialogoRol
from interfaz.novela.componentes import decorar_novela, BotonNovela
from interfaz.novela.interacciones import OverlayInvestigacion
from interfaz.novela.transiciones import TransicionNarrativa
from interfaz.novela.feedback import reproducir_cambios
from audio.sonidos_novela import instalar_sonidos_novela


class VentanaNovela(VentanaPrincipal):
    """Conserva escenas, actores, teléfono, lectura y voces de VentanaPrincipal."""

    def __init__(self, semilla=4, eventos=True):
        self.sesion = None
        self.vista_novela = {}
        self.control_cooperativo = None
        self.overlay_investigacion = None
        self._resultado_presentado = None
        self._caso_presentacion = None
        self._quiere_continuar = False
        self._visores_vistos = set()
        self._semilla_novela = semilla
        self._eventos_novela = eventos
        self._plazo_local = None
        self.planos_vistos = set()
        self.plano_investigacion = None
        super().__init__()
        from interfaz.novela.cooperativa import ControlCooperativaNovela
        self.control_cooperativo = ControlCooperativaNovela(self)
        self.transicion_narrativa = TransicionNarrativa(self.escenas)
        self.temporizador_novela = QTimer(self)
        self.temporizador_novela.setInterval(1000)
        self.temporizador_novela.timeout.connect(self._paso_plazo)
        self._accion_original = self.escena_accion.ejecutar_accion
        self.escena_accion.ejecutar_accion = MethodType(
            lambda escena, accion: self.enviar_accion(accion), self.escena_accion)
        self.escena_accion.boton_investigar.clicked.disconnect()
        self.escena_accion.boton_investigar.clicked.connect(lambda _=False: self.abrir_fuentes())
        self.boton_rectificar = BotonNovela("Rectificar con una prueba")
        self.boton_rectificar.setAccessibleName("Rectificar con una prueba recuperada")
        self.boton_rectificar.clicked.connect(lambda: self.enviar_accion("rectificar"))
        self.escena_accion.botones_accion.addWidget(self.boton_rectificar, 2, 0, 1, 2)
        self.boton_rectificar.hide()
        self.menu_partida.menu().addSeparator()
        self.menu_partida.menu().addAction("Examinar archivo (ABB)", lambda: self.abrir_observatorio("archivo"))
        self.menu_partida.menu().addAction("Examinar conexiones (grafo)", lambda: self.abrir_observatorio("red"))
        self.establecer_juego(Juego(semilla, eventos=eventos, campana="feria"))
        decorar_novela(self)
        instalar_sonidos_novela(self.audio)
        self.statusBar().messageChanged.connect(self._mostrar_solo_avisos)
        self._mostrar_solo_avisos(self.statusBar().currentMessage())

    def _mostrar_solo_avisos(self, texto=""):
        # Los indicadores se presentan en las consecuencias, sin una barra fija.
        if hasattr(self, "hud"):
            self.hud.hide()
        if hasattr(self, "indicadores"):
            self.indicadores.hide()
        self.statusBar().setVisible(bool(texto))

    def establecer_juego(self, juego):
        anterior = getattr(self, "juego", None)
        caso_presentacion = self.vista_novela.get("caso", {}).get("id")
        misma_escena = (
            anterior is not None and anterior is not juego
            and self.sesion is None and getattr(self, "cliente_red", None) is not None
            and anterior.campana == juego.campana == "feria"
            and caso_presentacion is not None
            and caso_presentacion == self._caso_presentacion
        )
        if misma_escena:
            # Conserva las pausas y el foco de lectura mientras llega otro snapshot.
            anterior.__dict__.clear()
            anterior.__dict__.update(juego.__dict__)
            juego = anterior
        super().establecer_juego(juego)
        self._caso_presentacion = caso_presentacion
        if juego.campana == "feria":
            # La sesión ya insertó el primer caso en el ABB antes de la introducción.
            self.escena_narracion_3.accion_al_comenzar = None

    def comenzar_juego(self):
        self.cerrar_red()
        dialogo = DialogoRol(self)
        decorar_novela(dialogo)
        if not dialogo.exec():
            return
        self.iniciar_solo(dialogo.roles.currentData())

    def iniciar_solo(self, rol="ciudadano", nombre=None):
        """Entrada común de la portada y de las verificaciones con una sola voz."""
        self.cerrar_red()
        sesion = SesionInvestigacion(self._semilla_novela)
        sesion.juego = Juego(self._semilla_novela, eventos=self._eventos_novela, campana="feria")
        sesion.juego.jugadores = []
        id_jugador = sesion.registrar_jugador(nombre or ("Ciudadano" if rol == "ciudadano" else "Periodista"), rol)
        sesion.comenzar()
        self.sesion = sesion
        self.mi_id = id_jugador
        self._resultado_presentado = None
        self._quiere_continuar = False
        self.planos_vistos.clear()
        self.historial_dialogos.clear()
        self.pistas_consultadas.clear()
        self.vista_novela = {}
        self.recibir_estado_novela(sesion.vista(id_jugador), sesion.juego)

    def mostrar_escena(self, indice):
        activa = bool(getattr(self, "vista_novela", {}))
        if activa and indice == self.ESCENA_GRAFO and "arbol" not in self._visores_vistos:
            indice = self.ESCENA_ARBOL
        transicion = getattr(self, "transicion_narrativa", None)
        cambia = hasattr(self, "escenas") and self.escenas.currentIndex() != indice
        if transicion is not None and cambia:
            transicion.configurar(self.reducir_movimiento)
            if not self.reducir_movimiento:
                transicion.capturar(self.escenas)
        actualizaciones = self.escenas.updatesEnabled()
        self.escenas.setUpdatesEnabled(False)
        try:
            super().mostrar_escena(indice)
            self._mostrar_solo_avisos(self.statusBar().currentMessage())
        finally:
            self.escenas.setUpdatesEnabled(actualizaciones)
        if transicion is not None:
            self.animacion_transicion.stop()
            self.velo_transicion.hide()
            if cambia:
                transicion.revelar(self.reducir_movimiento)
        if activa and indice == self.ESCENA_ARBOL:
            self._visores_vistos.add("arbol")
        elif activa and indice == self.ESCENA_GRAFO:
            self._visores_vistos.add("grafo")
            self.escena_red.boton_continuar.setText("Siguiente acto →")
        if activa and indice == self.ESCENA_ACCION:
            self._actualizar_elecciones()
            self.escena_accion.timer_decision.stop()
            self._activar_plazo()
        elif hasattr(self, "temporizador_novela"):
            self.temporizador_novela.stop()
        if hasattr(self, "boton_rectificar"):
            self.boton_rectificar.setVisible(activa and indice == self.ESCENA_ACCION
                                             and self.vista_novela.get("mi_rol") == "ciudadano")
        if hasattr(self, "control_cooperativo") and self.control_cooperativo:
            self.control_cooperativo.sincronizar_escena(indice) if hasattr(self.control_cooperativo, "sincronizar_escena") else None
        if activa:
            self._rotular_acto()
        decorar_novela(self)

    def _rotular_acto(self):
        caso = self.vista_novela.get("caso", {})
        numero = caso.get("numero", self.juego.indice_proxima_publicacion)
        romanos = ("I", "II", "III", "IV", "V", "VI")
        romano = romanos[max(0, min(5, numero-1))]
        self.escena_accion.capitulo.setText(f"ACTO {romano} / VI\n{caso.get('titulo', '')}")
        self.setWindowTitle(f"CIVICA — Acto {romano} de VI · Novela visual")

    def _actualizar_elecciones(self):
        self.escena_accion.actualizar_acciones_rol()
        vista = self.vista_novela
        mi_id = vista.get("mi_id")
        puede = (vista.get("fase") in ("investigacion", "decision")
                 and vista.get("turno_id") == mi_id
                 and mi_id not in vista.get("decididos", []))
        for boton in self.escena_accion.botones_por_accion.values():
            boton.setEnabled(puede)
        self.boton_rectificar.setEnabled(puede)
        self.escena_accion.boton_investigar.setEnabled(
            vista.get("fase") in ("investigacion", "decision") and mi_id not in vista.get("decididos", []))
        self.escena_accion.pistas_estado.setText(
            f"{len(vista.get('hallazgos', []))} hallazgos · {vista.get('acciones_restantes', 0)} investigaciones disponibles")
        if vista.get("fase") == "pausa":
            aviso = "La escena está en pausa. Reconecta a tu compañero desde Partida."
        elif mi_id in vista.get("decididos", []):
            aviso = "Tu decisión está registrada. La ciudad espera a tu compañero."
        elif not puede:
            aviso = "Puedes investigar mientras el Ciudadano prepara su decisión."
        else:
            aviso = "Examina una prueba, escucha a una fuente o decide cómo responder."
        self.escena_accion.aviso.setText(aviso)
        if self.sesion is not None:
            self.escena_accion.turno.setText(
                f"TU PERSPECTIVA · {vista.get('mi_rol', '').upper()} · Una decisión transforma la ciudad")

    def abrir_cuaderno(self, pestana=0):
        if self.vista_novela and pestana == 0:
            self.abrir_fuentes()
        else:
            super().abrir_cuaderno(pestana)
            if self.cuaderno:
                decorar_novela(self.cuaderno)

    def abrir_fuentes(self, seccion="fuentes"):
        if not self.vista_novela:
            return super().abrir_cuaderno(0)
        caso = self.vista_novela.get("caso", {})
        clave = caso.get("id")
        if clave not in self.planos_vistos and not self.reducir_movimiento:
            from interfaz.novela.plano import PlanoInvestigacion
            self.planos_vistos.add(clave)
            self.temporizador_novela.stop()
            self.audio.detener_voz()
            self.plano_investigacion = PlanoInvestigacion(caso.get("numero", 1), self.escenas)
            plano = self.plano_investigacion
            def abrir_expediente():
                if self.plano_investigacion is plano:
                    self.plano_investigacion = None
                    self._abrir_overlay(seccion)
            plano.terminado.connect(abrir_expediente)
            plano.abrir()
            return
        self._abrir_overlay(seccion)

    def _abrir_overlay(self, seccion):
        if self.overlay_investigacion is not None:
            self.overlay_investigacion.actualiza(self.vista_novela)
            self.overlay_investigacion.abrir(seccion)
            return self.overlay_investigacion
        self.temporizador_novela.stop()
        reanudar = self.pausar_lectura_modal()
        overlay = OverlayInvestigacion(self.vista_novela, self.enviar_comando_novela, self)
        self.overlay_investigacion = overlay
        def cerrar():
            if self.overlay_investigacion is overlay:
                self.overlay_investigacion = None
            reanudar()
            if self.escenas.currentWidget() is self.escena_accion:
                self._activar_plazo()
        overlay.cerrado.connect(cerrar)
        overlay.abrir(seccion)
        return overlay

    def enviar_accion(self, accion):
        if not self.vista_novela:
            return self._accion_original(accion)
        vista = self.vista_novela
        if (vista.get("fase") not in ("investigacion", "decision")
                or vista.get("turno_id") != vista.get("mi_id")):
            return
        overlay = self._abrir_overlay("decision")
        overlay.decision(accion)

    def enviar_comando_novela(self, comando):
        if self.control_cooperativo and self.control_cooperativo.cliente:
            return self.control_cooperativo.enviar_comando(comando)
        if self.sesion is None:
            return False
        tipo = comando.get("tipo")
        args = {k:v for k,v in comando.items() if k not in ("tipo", "revision", "caso_id", "solicitud_id")}
        if tipo == "examinar":
            args["tipo"] = args.pop("medio", args.pop("tipo_medio", self.vista_novela["caso"]["medio"]["tipo"]))
        try:
            metodo = getattr(self.sesion, tipo, None)
            if tipo not in ("investigar", "examinar", "entrevistar", "compartir_hallazgo",
                            "solicitar_hallazgo", "proponer", "decidir", "prever_alcance", "continuar") or not callable(metodo):
                raise ValueError("Esta interacción no está disponible.")
            metodo(self.mi_id, **args)
            self.recibir_estado_novela(self.sesion.vista(self.mi_id), self.sesion.juego)
            return True
        except (ValueError, TypeError) as error:
            self.statusBar().showMessage(str(error), 6500)
            if self.overlay_investigacion:
                self.overlay_investigacion.mostrar_mensaje(str(error))
            return False

    def recibir_estado_novela(self, vista, juego):
        """Actualiza consecuencias sin reiniciar diálogos al llegar cada mensaje de red."""
        anterior = self.vista_novela
        previo_caso = anterior.get("caso", {}).get("id")
        caso = vista.get("caso", {}).get("id")
        primer_estado = not anterior
        reproducir_cambios(self.audio, anterior, vista)
        self.vista_novela = vista
        self.mi_id = vista.get("mi_id", self.mi_id)
        self.establecer_juego(juego)
        if self.overlay_investigacion:
            self.overlay_investigacion.actualiza(vista)
        if vista.get("fase") == "pausa":
            self.temporizador_novela.stop()
            self.escena_accion.timer_decision.stop()
            self.statusBar().showMessage("Conexión interrumpida. Partida → Reconectar sala.")
            self._actualizar_elecciones()
            if self.escenas.currentWidget() is self.escena_red:
                self.escena_red.boton_continuar.setEnabled(False)
                self.escena_red.detalle.setText("La revisión queda en pausa. Reconecta al compañero desde Partida.")
            return
        if vista.get("fase") == "final":
            self._cerrar_overlay()
            self.mostrar_desenlace()
            self._autoguardar()
            return
        if primer_estado or caso != previo_caso:
            self._cerrar_overlay()
            self._resultado_presentado = None
            self._quiere_continuar = False
            self._visores_vistos.clear()
            self._plazo_local = None
            self.mostrar_escena(self.ESCENA_NARRACION_1 if primer_estado
                               and juego.indice_proxima_publicacion == 1 else self.ESCENA_DIALOGO)
        clave = (caso, self.mi_id)
        if self.mi_id in vista.get("decididos", []) and self._resultado_presentado != clave:
            self._resultado_presentado = clave
            self._cerrar_overlay()
            self.mostrar_escena(self.ESCENA_RESULTADO_1)
        elif self.escenas.currentWidget() is self.escena_accion:
            self._actualizar_elecciones()
        if self.escenas.currentWidget() is self.escena_red:
            self.escena_red.boton_continuar.setEnabled(
                self.mi_id not in vista.get("confirmados", []) and not self._quiere_continuar)
        if self._quiere_continuar and vista.get("fase") == "resultado" and self.mi_id not in vista.get("confirmados", []):
            self.continuar_caso()
        self._autoguardar()

    def _cerrar_overlay(self):
        if self.plano_investigacion:
            self.plano_investigacion.cancelar()
            self.plano_investigacion = None
        overlay = self.overlay_investigacion
        if overlay:
            overlay.cerrar()

    def continuar_caso(self):
        vista = self.vista_novela
        if (self.escenas.currentWidget() is not self.escena_red
                or not {"arbol", "grafo"} <= self._visores_vistos):
            self.statusBar().showMessage("Revisa el archivo de publicaciones y el recorrido de la red antes del siguiente acto.", 6500)
            return
        if vista.get("fase") != "resultado":
            self.escena_red.boton_continuar.setEnabled(False)
            self.escena_red.detalle.setText("Tu revisión terminó. Esperando la decisión de tu compañero…")
            self.statusBar().showMessage("Tu compañero sigue investigando; tu decisión ya transformó la ciudad.", 6500)
            return
        if self.control_cooperativo and self.control_cooperativo.cliente:
            if self.control_cooperativo.continuar():
                self.escena_red.boton_continuar.setEnabled(False)
                self.escena_red.detalle.setText("Revisión confirmada. Esperando que tu compañero termine…")
                self.statusBar().showMessage("Esperando que tu compañero termine de leer sus consecuencias…")
            else:
                self._quiere_continuar = False
                self.escena_red.boton_continuar.setEnabled(True)
        else:
            self.enviar_comando_novela({"tipo": "continuar"})

    def error_cooperativo(self, texto):
        if (self.escenas.currentWidget() is self.escena_red
                and self.vista_novela.get("fase") != "pausa"
                and self.mi_id not in self.vista_novela.get("confirmados", [])):
            self._quiere_continuar = False
            self.escena_red.boton_continuar.setEnabled(True)
            self.escena_red.detalle.setText(texto)

    def continuar_desde_arbol(self):
        if self.vista_novela:
            if self.escenas.currentWidget() is not self.escena_red:
                return
            self._quiere_continuar = True
            self.continuar_caso()
        else:
            super().continuar_desde_arbol()

    def mostrar_desenlace(self):
        self.mostrar_escena(self.ESCENA_EPILOGO if self.juego.campana in ("feria", "extendida") else self.ESCENA_FIN)

    def abrir_multijugador(self):
        self._cerrar_overlay()
        self.control_cooperativo.abrir_sala()

    def reconectar_red(self):
        if self.control_cooperativo:
            self.control_cooperativo.reconectar()

    def cerrar_red(self):
        control = getattr(self, "control_cooperativo", None)
        if control:
            control.cerrar()
        super().cerrar_red()

    def volver_portada(self):
        self._cerrar_overlay()
        self.temporizador_novela.stop()
        self.cerrar_red()
        self.sesion = None
        self.vista_novela = {}
        self._resultado_presentado = None
        self.mostrar_escena(self.ESCENA_INICIO)

    def aplicar_accesibilidad(self):
        super().aplicar_accesibilidad()
        if self.sin_limite and hasattr(self, "temporizador_novela"):
            self.temporizador_novela.stop()

    def _activar_plazo(self):
        if not hasattr(self, "temporizador_novela") or self.sin_limite:
            return
        vista = self.vista_novela
        if self.control_cooperativo and self.control_cooperativo.cliente:
            return
        if vista.get("turno_id") != vista.get("mi_id") or vista.get("fase") not in ("investigacion", "decision"):
            return
        segundos = vista.get("segundos_decision")
        if segundos is None:
            return
        if self._plazo_local is None:
            self._plazo_local = segundos
        self.temporizador_novela.start()

    def _paso_plazo(self):
        if self.sin_limite or self.overlay_investigacion or self.sesion is None:
            self.temporizador_novela.stop()
            return
        self._plazo_local = max(0, (self._plazo_local or 0)-1)
        self.escena_accion.aviso.setText(f"Una reacción está creciendo · {self._plazo_local} s para decidir")
        if self._plazo_local == 0:
            self.temporizador_novela.stop()
            try:
                self.sesion.expirar_turno(self.mi_id)
                self.recibir_estado_novela(self.sesion.vista(self.mi_id), self.sesion.juego)
            except ValueError as error:
                self.statusBar().showMessage(str(error), 5000)

    def _guardado(self):
        return {"formato":"civica_novela", "version":1, "sesion":self.sesion.datos(),
                "escena":self.escenas.currentIndex(), "visores":sorted(self._visores_vistos)}

    def _escribir_guardado(self, ruta):
        archivo = Path(ruta)
        archivo.parent.mkdir(parents=True, exist_ok=True)
        temporal = archivo.with_suffix(archivo.suffix+".tmp")
        temporal.write_text(json.dumps(self._guardado(), ensure_ascii=False, indent=2), encoding="utf-8")
        temporal.replace(archivo)

    def _autoguardar(self):
        if self.sesion is None or self.sesion.cooperativa:
            return
        try:
            self._escribir_guardado(ruta_recurso(".civica/novela_autoguardado.json"))
        except OSError as error:
            self.statusBar().showMessage("No fue posible guardar automáticamente: "+str(error), 6500)

    def guardar_partida(self):
        if self.sesion is None:
            return super().guardar_partida()
        if self.cliente_red:
            self.statusBar().showMessage("El anfitrión conserva la partida cooperativa.")
            return
        reanudar = self.pausar_lectura_modal()
        try:
            ruta, _ = QFileDialog.getSaveFileName(self, "Guardar novela", ruta_recurso("saves/novela.json"), "Partidas (*.json)")
            if ruta:
                self._escribir_guardado(ruta)
                self.statusBar().showMessage("Novela guardada con sus hallazgos y relaciones.")
        except OSError as error:
            QMessageBox.warning(self, "Guardado", str(error))
        finally:
            reanudar()

    def cargar_partida(self):
        if self.cliente_red:
            return
        reanudar = self.pausar_lectura_modal()
        try:
            ruta, _ = QFileDialog.getOpenFileName(self, "Cargar novela", ruta_recurso("saves"), "Partidas (*.json)")
            if ruta:
                self.cargar_desde_ruta(ruta)
        except (OSError, ValueError, KeyError, TypeError) as error:
            QMessageBox.warning(self, "Partida incompatible", str(error))
        finally:
            reanudar()

    def cargar_desde_ruta(self, ruta):
        datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
        if not isinstance(datos, dict):
            raise ValueError("El archivo no contiene una partida de CIVICA.")
        if datos.get("formato") != "civica_novela":
            juego = Juego.desde_datos(datos)
            self.sesion = None
            self.vista_novela = {}
            self.establecer_juego(juego)
            indice = self.ESCENA_DIALOGO
            if juego.decision_aplicada:
                indice = self.ESCENA_GRAFO
            if juego.indice_proxima_publicacion == 0:
                indice = self.ESCENA_INICIO
            if juego.finalizada:
                indice = self.ESCENA_EPILOGO if juego.campana == "extendida" else self.ESCENA_FIN
            self.mostrar_escena(indice)
            return
        sesion = SesionInvestigacion.desde_datos(datos["sesion"])
        if sesion.cooperativa:
            raise ValueError("Reconecta al anfitrión para recuperar una partida cooperativa.")
        self.cerrar_red()
        self.sesion = sesion
        self.vista_novela = {}
        self._resultado_presentado = None
        self.recibir_estado_novela(sesion.vista(), sesion.juego)
        indice = datos.get("escena")
        if isinstance(indice,int) and 1 <= indice <= self.ESCENA_EPILOGO and sesion.fase != "final":
            if sesion.fase == "resultado" and indice not in (6,7,8,9,11):
                indice = self.ESCENA_RESULTADO_1
            guardados = datos.get("visores", [])
            self._visores_vistos = {v for v in guardados if v in ("arbol", "grafo")} if isinstance(guardados, list) else set()
            if indice == self.ESCENA_GRAFO:
                self._visores_vistos.update(("arbol", "grafo"))
            self.mostrar_escena(indice)

    def abrir_observatorio(self, seccion="archivo"):
        if not self.vista_novela:
            return self.abrir_cuaderno(3)
        from interfaz.novela.observatorio import ObservatorioNovela
        reanudar = self.pausar_lectura_modal()
        dialogo = ObservatorioNovela(self.juego, self.vista_novela, seccion, self)
        dialogo.finished.connect(lambda _: reanudar())
        dialogo.show()
        self._observatorio_novela = dialogo

    def closeEvent(self, event):
        self._cerrar_overlay()
        if hasattr(self, "temporizador_novela"):
            self.temporizador_novela.stop()
        self._autoguardar()
        super().closeEvent(event)
