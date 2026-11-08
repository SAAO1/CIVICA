"""interfaz.escenas.resultado: presentación separada de las reglas del juego."""
from interfaz.novela.guion import contenido_resultado
from interfaz.novela.guion import caso_actual
from juego.puesta_escena import escenario_actual
from interfaz.componentes.resultados import BalanceAnimado
from audio.catalogo_voces import segmentos_indicadores
from interfaz.escenas.cinematica import EscenaCinematica


class EscenaResultado(EscenaCinematica):

    def __init__(self, fondo, siguiente, tipo, parent=None):
        super().__init__(fondo, parent)

        self.siguiente = siguiente
        self.tipo = tipo
        self.nombre_inicial = ""
        self.balance = BalanceAnimado(self) if tipo == 3 else None
        self._balance_con_voz = False
        self._balance_en_curso = False
        self.boton_detalle = None
        if self.balance is not None:
            self.balance.terminado.connect(self.balance_presentado)

        self.dialogo_terminado.connect(
            self.terminar_escena
        )

    def obtener_contenido(self):
        return contenido_resultado(self.window().juego, self.tipo)

    def comenzar_escena(self):
        if self.balance is not None:
            self.balance.detener()
        self._balance_en_curso = False
        self._balance_con_voz = False
        self.fondo = escenario_actual(self.window().juego)["fondo"]
        self.texto_inicial, self.nombre_inicial = (
            self.obtener_contenido()
        )
        if self.tipo == 3:
            registro = self.window().juego.ultimo_registro or {}
            titulo = registro.get("titulo_accion", registro.get("accion", "Decisión").capitalize())
            caso = caso_actual(self.window().juego)["titulo"]
            self.texto_inicial = f"{caso}. {titulo}. La ciudad responde a nuestra decisión."
            self.nombre_inicial = "NARRADOR"

        super().comenzar_escena()
        if self.tipo == 3:
            self.timer_inicio.stop()
            self.texto_completo = self.texto_inicial
            self.finalizar_animacion_dialogo()

    def actualizar_geometria(self):
        super().actualizar_geometria()
        if getattr(self, "balance", None) is not None:
            self.balance.setGeometry(self.rect())

    def finalizar_animacion_dialogo(self):
        if self.tipo != 3:
            return super().finalizar_animacion_dialogo()
        if self.estado_escena == "inactiva":
            return
        self.animando = False
        self.escribiendo = False
        self.estado_escena = "esperando"
        self.hablante_actual = "NARRADOR"
        self.timer_texto.stop()
        for widget in (self.franja_superior, self.franja_inferior, self.nombre_label,
                       self.texto_label, self.pista_continuar, self.contexto_escena):
            widget.hide()
        if self.window().isMinimized() and not self.lectura_pausada:
            self._reanudar_al_restaurar = self.window().pausar_lectura_modal()
        if self.lectura_pausada:
            return
        self.iniciar_puesta_audiovisual()
        juego = self.window().juego
        registro = dict(juego.ultimo_registro or {})
        jugador = next((j for j in juego.jugadores if j.id == registro.get("jugador_id")), juego.jugador)
        registro.setdefault("puntos_despues", jugador.puntos)
        registro.setdefault("puntos_antes", jugador.puntos-registro.get("puntos", 0))
        self.balance.preparar(registro, jugador.nombre)
        self.balance.configurar(getattr(self.window(), "reducir_movimiento", False))
        self.balance.setGeometry(self.rect())
        self.balance.raise_()
        self.boton_saltar.setChecked(False)
        self.boton_saltar.setEnabled(True)
        self.boton_saltar.setToolTip("Todos los cambios están visibles; puedes continuar en cualquier momento.")
        self._balance_en_curso = True
        self.narrar_balance(escuchar=True)
        self.programar_lectura()

    def narrar_balance(self, escuchar=False):
        if self.balance is None or self.lectura_pausada:
            return
        if self.cine_narrativo.activa and self.cine_narrativo._pausada:
            self.cine_narrativo.reanudar()
        self.efectos_narrativos.reanudar()
        self.balance.comenzar(automatico=True)
        if not escuchar:
            return
        audio = getattr(self.window(), "audio", None)
        segmentos = segmentos_indicadores(self.window().juego.ultimo_registro or {})
        self._balance_con_voz = bool(audio and audio.narrar_secuencia(segmentos, "NARRADOR") is True)

    def segmento_balance(self, clave):
        if (self.balance is not None and self._balance_en_curso
                and self.isVisible() and not self.lectura_pausada):
            self.balance.segmento(clave)

    def fin_balance_voz(self, completada):
        if self.balance is None or not self._balance_en_curso:
            return
        self._balance_con_voz = False
        self.balance.finalizar_voz()
        self.balance_presentado()

    def reanudar_balance(self):
        if self.balance is None:
            return
        if self.cine_narrativo.activa and self.cine_narrativo._pausada:
            self.cine_narrativo.reanudar()
        self.efectos_narrativos.reanudar()
        self._balance_con_voz = False
        self.balance.finalizar_voz()
        self.balance.reanudar()
        self.balance_presentado()

    def balance_presentado(self):
        if self.balance is not None and self.balance.completo:
            self.registrar_lectura()
        self.programar_lectura()

    def balance_listo(self):
        return (self.balance is not None and self._balance_en_curso
                and self.balance.completo)

    def programar_lectura(self, _=None):
        if self.tipo != 3:
            return super().programar_lectura(_)
        self.timer_lectura.stop()
        if (self.balance_listo() and not self.lectura_pausada and not self.animando
                and self.estado_escena == "esperando" and self.boton_auto.isChecked()):
            self.timer_lectura.start(750)

    def revelar_texto(self):
        if self.tipo != 3:
            return super().revelar_texto()
        if self.balance is not None:
            self.balance.revelar()

    def avanzar(self):
        if self.tipo == 3:
            if (self.lectura_pausada or not self._balance_en_curso or not self.isVisible()
                    or self.estado_escena == "inactiva"):
                return
            self.balance.revelar()
            self.timer_inicio.stop()
            self.timer_lectura.stop()
            self.window().audio.detener_voz()
            self._balance_con_voz = False
            self.animando = True
            self.dialogo_terminado.emit()
            return
        super().avanzar()

    def paso_lectura(self):
        if self.tipo == 3:
            if (self.boton_auto.isChecked() and self.balance_listo()
                    and self.isVisible() and not self.lectura_pausada
                    and self.estado_escena == "esperando"):
                if getattr(getattr(self.window(), "audio", None), "hablando", False) is True:
                    self.timer_lectura.start(200)
                    return
                self.avanzar()
            return
        super().paso_lectura()

    def finalizar_escena(self):
        self._balance_en_curso = False
        self._balance_con_voz = False
        if getattr(self, "balance", None) is not None:
            self.balance.detener()
        super().finalizar_escena()

    def terminar_escena(self):
        ventana = self.window()

        if hasattr(ventana, "mostrar_escena"):
            ventana.mostrar_escena(
                self.siguiente
            )
