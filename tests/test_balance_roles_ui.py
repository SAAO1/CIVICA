"""Balance central y decisiones por oficio comprobados con señales Qt reales."""
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import QObject, QPoint, Qt, pyqtSignal
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QDialog

from audio.catalogo_voces import segmentos_indicadores
from interfaz import VentanaPrincipal
from juego.acciones import acciones_para_rol
from juego.eventos import Evento
from juego.lectura import BibliotecaLectura
from juego.partida import Juego
from models.jugador import Jugador
from paneles import mostrar_configuracion, mostrar_ayuda
from recursos import RAIZ
from resultados_visual import BalanceAnimado, tarjetas_resultado


class AudioConSenales(QObject):
    aviso = pyqtSignal(str)
    voz_iniciada = pyqtSignal(str)
    voz_finalizada = pyqtSignal()
    nivel_voz = pyqtSignal(float)
    segmento_iniciado = pyqtSignal(str)
    secuencia_finalizada = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.volumenes = {"general": .65, "musica": .3, "efectos": .6, "ambiente": .2, "voces": 1.}
        self.silenciado = False
        self.hablando = False
        self.hablante_actual = "NARRADOR"
        self.secuencia_disponible = True
        for nombre in ("configurar", "silenciar", "configurar_voces", "cambiar_pista", "reproducir_efecto", "detener", "narrar"):
            setattr(self, nombre, Mock())
        self.descripcion_voces = Mock(return_value="Voces de prueba aisladas")
        self.narrar_secuencia = Mock(side_effect=self._narrar_secuencia)
        self.detener_voz = Mock(side_effect=self._detener_voz)

    def _narrar_secuencia(self, segmentos, hablante):
        self.hablando = self.secuencia_disponible
        return self.secuencia_disponible

    def _detener_voz(self):
        estaba = self.hablando
        self.hablando = False
        if estaba:
            self.secuencia_finalizada.emit(False)


def crear_ventana():
    ventana = VentanaPrincipal()
    ventana.reducir_movimiento = True
    ventana.sin_limite = True
    ventana.animar_fondos = False
    ventana.animar_personajes = False
    ventana.aplicar_accesibilidad()
    ventana.resize(1366, 768)
    ventana.show()
    return ventana


def preparar_balance(ventana, app, confianza=50, desinformacion=9):
    juego = Juego(7, eventos=False)
    juego.seleccionar_rol("periodista")
    juego.confianza = confianza
    juego.desinformacion = desinformacion
    ventana.establecer_juego(juego)
    juego.iniciar_primera_publicacion()
    juego.ejecutar_accion("contrastar")
    ventana.mostrar_escena(ventana.ESCENA_RESULTADO_3)
    escena = ventana.escena_resultado_3
    escena.timer_inicio.stop()
    escena.preparar_dialogo()
    escena.animacion.stop()
    escena.finalizar_animacion_dialogo()
    escena.balance.configurar(reducir_movimiento=False)
    app.processEvents()
    return escena


def presentar_todos(escena, audio):
    """Reloj de prueba: cada cifra recibe su foco y su intervalo completo."""
    for tarjeta in escena.balance.tarjetas:
        audio.segmento_iniciado.emit(tarjeta["clave"])
        escena.balance.establecer_tiempo(1.61)
        escena.balance._paso()


class BalanceRolesUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.patches = [patch("configuracion.cargar", return_value={}),
                        patch("interfaz.GestorAudio", AudioConSenales),
                        patch("interfaz.BibliotecaLectura", lambda: BibliotecaLectura(None))]
        for p in self.patches:
            p.start()
        self.ventanas = [crear_ventana()]
        self.ventana = self.ventanas[0]
        self.app.processEvents()

    def tearDown(self):
        for ventana in self.ventanas:
            ventana.close()
            ventana.deleteLater()
        self.app.processEvents()
        for p in reversed(self.patches):
            p.stop()

    def test_senales_voz_enfocan_numero_central_sin_subtitulo_estadistico(self):
        escena = preparar_balance(self.ventana, self.app)
        primera = escena.balance.tarjetas[0]["clave"]
        self.ventana.audio.segmento_iniciado.emit(primera)
        escena.balance.establecer_tiempo(1.21)
        escena.balance._paso()
        self.ventana.audio.segmento_iniciado.emit("confianza")
        self.assertEqual(escena.balance.clave_actual, "confianza")
        tarjeta = escena.balance.tarjetas[escena.balance._indice]
        self.assertEqual((tarjeta["antes"], tarjeta["despues"], tarjeta["delta"]), (50, 56, 6))
        for etiqueta in (escena.texto_label, escena.nombre_label, escena.franja_inferior, escena.franja_superior):
            self.assertFalse(etiqueta.isVisible())
        self.assertNotIn("+6", escena.texto_completo)
        self.assertNotIn("Confianza", escena.texto_completo)
        self.assertIn("Confianza: de 50 a 56, cambio +6", escena.balance.accessibleName())
        self.assertIn("Desinformación", escena.balance.accessibleDescription())
        self.assertEqual(escena.balance.geometry(), escena.rect())
        self.assertTrue(escena.balance._timer.isActive())

    def test_balance_respeta_topes_signos_y_puntuacion_cero(self):
        escena = preparar_balance(self.ventana, self.app, confianza=99)
        tarjetas = {t["clave"]: t for t in escena.balance.tarjetas}
        self.assertEqual((tarjetas["confianza"]["delta"], tarjetas["confianza"]["despues"]), (1, 100))
        self.assertTrue(tarjetas["desinformacion"]["favorable"])
        self.assertLess(tarjetas["desinformacion"]["delta"], 0)
        segmentos = {s["clave"]: s["texto"] for s in segmentos_indicadores(self.ventana.juego.ultimo_registro)}
        self.assertEqual(segmentos["confianza"], "Confianza +1.")
        registro = {"antes": {"confianza": 50, "desinformacion": 1}, "despues": {"confianza": 48, "desinformacion": 3}, "puntos": 0}
        prueba = {t["clave"]: t for t in tarjetas_resultado(registro)}
        self.assertFalse(prueba["confianza"]["favorable"])
        self.assertFalse(prueba["desinformacion"]["favorable"])
        self.assertEqual(prueba["puntos"]["delta"], 0)
        escena.revelar_texto()
        self.assertFalse(escena.balance.completo)
        presentar_todos(escena, self.ventana.audio)
        self.assertTrue(escena.balance.completo)

    def test_espacio_click_enter_y_saltar_no_omiten_contadores_ni_acumulan_avance(self):
        escena = preparar_balance(self.ventana, self.app)
        primera = escena.balance.tarjetas[0]["clave"]
        self.ventana.audio.segmento_iniciado.emit(primera)
        escena.balance.establecer_tiempo(.15)
        valor = escena.balance.valor_actual
        for _ in range(100):
            QTest.keyClick(escena, Qt.Key.Key_Space)
            QTest.keyClick(escena, Qt.Key.Key_Return)
            QTest.mouseClick(escena, Qt.MouseButton.LeftButton, pos=escena.rect().center())
            escena.revelar_texto()
            escena.balance.revelar()
            escena.paso_lectura()
            self.assertIs(self.ventana.escenas.currentWidget(), escena)
            self.assertEqual(escena.balance.clave_actual, primera)
            self.assertEqual(escena.balance.valor_actual, valor)
            self.assertFalse(escena.balance.completo)
        self.assertFalse(escena.boton_saltar.isEnabled())
        presentar_todos(escena, self.ventana.audio)
        self.ventana.audio.secuencia_finalizada.emit(True)
        self.ventana.audio.hablando = False
        self.app.processEvents()
        self.assertIs(self.ventana.escenas.currentWidget(), escena)
        self.assertEqual(escena.balance.clave_actual, "puntos")
        QTest.keyClick(escena, Qt.Key.Key_Space)
        self.assertEqual(self.ventana.escenas.currentIndex(), self.ventana.ESCENA_ARBOL)

    def test_auto_espera_todas_las_cifras_y_el_fin_de_la_voz(self):
        escena = preparar_balance(self.ventana, self.app)
        escena.boton_auto.setChecked(True)
        presentar_todos(escena, self.ventana.audio)
        self.assertTrue(escena.balance.completo)
        escena.paso_lectura()
        self.assertIs(self.ventana.escenas.currentWidget(), escena)
        self.ventana.audio.hablando = False
        self.ventana.audio.secuencia_finalizada.emit(True)
        escena.paso_lectura()
        self.assertEqual(self.ventana.escenas.currentIndex(), self.ventana.ESCENA_ARBOL)
        self.assertFalse(escena.balance.isVisible())
        self.assertFalse(escena.balance._timer.isActive())
        self.ventana.audio.segmento_iniciado.emit("confianza")
        self.assertFalse(escena._balance_en_curso)

    def test_voz_muy_corta_no_completa_la_ultima_animacion_ni_omite_anteriores(self):
        escena = preparar_balance(self.ventana, self.app)
        for tarjeta in escena.balance.tarjetas:
            self.ventana.audio.segmento_iniciado.emit(tarjeta["clave"])
        self.ventana.audio.hablando = False
        self.ventana.audio.secuencia_finalizada.emit(True)
        escena.boton_auto.setChecked(True)
        primera = escena.balance.tarjetas[0]["clave"]
        self.assertEqual(escena.balance.clave_actual, primera)
        observadas = []
        for tarjeta in escena.balance.tarjetas:
            self.assertEqual(escena.balance.clave_actual, tarjeta["clave"])
            self.assertFalse(escena.balance.completo)
            observadas.append(escena.balance.clave_actual)
            escena.balance.establecer_tiempo(.85)
            escena.balance._paso()
            escena.avanzar()
            escena.paso_lectura()
            self.assertIs(self.ventana.escenas.currentWidget(), escena)
            self.assertFalse(escena.balance.completo)
            escena.balance.establecer_tiempo(1.61)
            escena.balance._paso()
        self.assertEqual(escena.balance.claves_completadas, tuple(observadas))
        self.assertTrue(escena.balance.completo)
        self.assertEqual(escena.balance.clave_actual, "puntos")
        self.assertEqual(escena.balance.valor_actual, escena.balance.tarjetas[-1]["despues"])
        self.assertIs(self.ventana.escenas.currentWidget(), escena)
        escena.paso_lectura()
        self.assertEqual(self.ventana.escenas.currentIndex(), self.ventana.ESCENA_ARBOL)

    def test_cancelar_voz_activa_secuencia_local_y_completa_sin_bloqueo(self):
        escena = preparar_balance(self.ventana, self.app)
        self.ventana.audio.segmento_iniciado.emit("confianza")
        self.ventana.audio.detener_voz()
        self.assertTrue(escena.balance._automatico)
        for _ in range(len(escena.balance.tarjetas)+1):
            escena.balance.establecer_tiempo(2)
            escena.balance._paso()
        self.assertTrue(escena.balance.completo)

    def test_minimizar_congela_reloj_y_restaurar_reanuda_sin_revocar_pausa_modal(self):
        self.ventana.audio.secuencia_disponible = False
        escena = preparar_balance(self.ventana, self.app)
        self.assertTrue(escena.balance._automatico)
        self.ventana.showMinimized()
        self.app.processEvents()
        tiempo = escena.balance.tiempo_actual()
        QTest.qWait(75)
        self.assertAlmostEqual(tiempo, escena.balance.tiempo_actual(), delta=.025)
        self.assertFalse(escena.balance._timer.isActive())
        self.ventana.showNormal()
        self.app.processEvents()
        self.assertTrue(escena.balance._timer.isActive(), repr(dict(pausado=escena.balance._pausado, estado=escena.estado_escena, en_curso=escena._balance_en_curso, visible=escena.balance.isVisible(), indice=escena.balance._indice)))
        escena.balance.pausar()
        self.ventana.showMinimized()
        self.app.processEvents()
        self.ventana.showNormal()
        self.app.processEvents()
        self.assertTrue(escena.balance._pausado)
        self.assertFalse(escena.balance._timer.isActive())

    def test_cuaderno_y_configuracion_pausan_balance_y_reinician_voz_sin_avanzar(self):
        escena = preparar_balance(self.ventana, self.app)
        primera = escena.balance.tarjetas[0]["clave"]
        self.ventana.audio.segmento_iniciado.emit(primera)
        escena.balance.establecer_tiempo(1.21)
        escena.balance._paso()
        self.ventana.audio.segmento_iniciado.emit("confianza")
        self.ventana.abrir_cuaderno(0)
        self.assertTrue(escena.lectura_pausada)
        self.assertFalse(escena.balance._timer.isActive())
        self.ventana.audio.segmento_iniciado.emit("desinformacion")
        self.assertEqual(escena.balance.clave_actual, "confianza")
        self.ventana.cuaderno.close()
        self.app.processEvents()
        self.assertFalse(escena.lectura_pausada)
        self.assertTrue(escena.balance._timer.isActive())
        segmentos_reanudados = self.ventana.audio.narrar_secuencia.call_args.args[0]
        self.assertNotIn(primera, {s["clave"] for s in segmentos_reanudados})
        self.assertIn(primera, escena.balance.claves_completadas)
        def durante_configuracion():
            self.assertTrue(escena.lectura_pausada)
            self.assertFalse(escena.balance._timer.isActive())
            return QDialog.DialogCode.Rejected
        with patch("paneles.DialogoIlustrado.exec", side_effect=durante_configuracion), patch("configuracion.guardar") as guardar:
            mostrar_configuracion(self.ventana)
        self.assertFalse(escena.lectura_pausada)
        self.assertIs(self.ventana.escenas.currentWidget(), escena)
        guardar.assert_not_called()
        self.assertGreaterEqual(self.ventana.audio.narrar_secuencia.call_count, 3)

    def test_manual_guardar_y_cargar_cancelado_congelan_el_balance_obligatorio(self):
        self.ventana.audio.secuencia_disponible = False
        for opcion in ("manual", "guardar", "cargar", "sala"):
            with self.subTest(opcion=opcion):
                escena = preparar_balance(self.ventana, self.app)
                clave = escena.balance.clave_actual
                def durante_modal(*_args, **_kwargs):
                    self.assertTrue(escena.lectura_pausada)
                    self.assertTrue(escena.balance._pausado)
                    self.assertFalse(escena.balance._timer.isActive())
                    tiempo = escena.balance.tiempo_actual()
                    QTest.qWait(45)
                    self.assertAlmostEqual(escena.balance.tiempo_actual(), tiempo, delta=.005)
                    self.assertEqual(escena.balance.clave_actual, clave)
                    return QDialog.DialogCode.Rejected if opcion in ("manual", "sala") else ("", "")
                if opcion == "manual":
                    with patch("paneles.DialogoIlustrado.exec", side_effect=durante_modal):
                        mostrar_ayuda(self.ventana)
                elif opcion == "sala":
                    with patch("interfaz.DialogoRed.exec", side_effect=durante_modal):
                        self.ventana.abrir_multijugador()
                else:
                    funcion = "getSaveFileName" if opcion == "guardar" else "getOpenFileName"
                    with patch("interfaz.QFileDialog."+funcion, side_effect=durante_modal):
                        getattr(self.ventana, opcion+"_partida")()
                self.assertFalse(escena.lectura_pausada)
                self.assertTrue(escena.balance._timer.isActive())
                self.assertIs(self.ventana.escenas.currentWidget(), escena)
                self.assertEqual(escena.balance.clave_actual, clave)

    def test_secuencia_sin_voz_recupera_reloj_al_cerrar_el_cuaderno(self):
        self.ventana.audio.secuencia_disponible = False
        escena = preparar_balance(self.ventana, self.app)
        self.ventana.abrir_cuaderno(0)
        self.assertTrue(escena.balance._pausado)
        self.ventana.cuaderno.close()
        self.app.processEvents()
        antes = escena.balance.tiempo_actual()
        QTest.qWait(80)
        self.assertGreater(escena.balance.tiempo_actual(), antes+.025)
        self.assertTrue(escena.balance._automatico)

    def test_reducir_movimiento_conserva_cada_foco_legible_y_valor_real(self):
        escena = preparar_balance(self.ventana, self.app)
        escena.balance.configurar(reducir_movimiento=True)
        for tarjeta in escena.balance.tarjetas:
            self.ventana.audio.segmento_iniciado.emit(tarjeta["clave"])
        for tarjeta in escena.balance.tarjetas:
            self.assertEqual(escena.balance.clave_actual, tarjeta["clave"])
            self.assertEqual(escena.balance.valor_actual, tarjeta["despues"])
            escena.balance.establecer_tiempo(.8)
            escena.balance._paso()
            self.assertEqual(escena.balance.clave_actual, tarjeta["clave"])
            self.assertFalse(escena.balance.completo)
            escena.balance.establecer_tiempo(.91)
            escena.balance._paso()
        self.assertTrue(escena.balance.completo)
        self.assertEqual(len(escena.balance.claves_completadas), len(escena.balance.tarjetas))

    def test_todas_las_animaciones_parten_del_valor_anterior_y_llegan_al_real(self):
        escena = preparar_balance(self.ventana, self.app)
        for tarjeta in escena.balance.tarjetas:
            self.ventana.audio.segmento_iniciado.emit(tarjeta["clave"])
        for tarjeta in escena.balance.tarjetas:
            self.assertEqual(escena.balance.clave_actual, tarjeta["clave"])
            escena.balance.establecer_tiempo(0)
            self.assertEqual(escena.balance.valor_actual, tarjeta["antes"])
            escena.balance.establecer_tiempo(.4)
            self.assertGreaterEqual(escena.balance.valor_actual, min(tarjeta["antes"], tarjeta["despues"]))
            self.assertLessEqual(escena.balance.valor_actual, max(tarjeta["antes"], tarjeta["despues"]))
            escena.balance.establecer_tiempo(1.19)
            escena.balance._paso()
            self.assertEqual(escena.balance.clave_actual, tarjeta["clave"])
            self.assertEqual(escena.balance.valor_actual, tarjeta["despues"])
            self.assertFalse(escena.balance.completo)
            escena.balance.establecer_tiempo(1.21)
            escena.balance._paso()
        self.assertTrue(escena.balance.completo)
        self.assertEqual(escena.balance.claves_completadas, tuple(t["clave"] for t in escena.balance.tarjetas))

    def test_temporizador_sin_voz_completa_solo_tras_intervalo_visible_real(self):
        balance = BalanceAnimado()
        try:
            balance.resize(800, 500)
            balance.preparar({"puntos": 2, "puntos_antes": 4, "puntos_despues": 6})
            balance.comenzar(automatico=True)
            QTest.qWait(700)
            self.assertFalse(balance.completo)
            balance.revelar()
            self.assertFalse(balance.completo)
            QTest.qWait(1000)
            self.assertTrue(balance.completo)
            self.assertEqual(balance.clave_actual, "puntos")
            self.assertEqual(balance.valor_actual, 6)
        finally:
            balance.detener()
            balance.close()
            balance.deleteLater()

    def test_pausa_con_todos_presentados_no_deja_esperando_voz_cancelada(self):
        escena = preparar_balance(self.ventana, self.app)
        presentar_todos(escena, self.ventana.audio)
        self.assertTrue(escena.balance.completo)
        self.assertFalse(escena.balance_listo())
        self.ventana.abrir_cuaderno(0)
        self.ventana.cuaderno.close()
        self.app.processEvents()
        self.assertTrue(escena.balance_listo())
        QTest.keyClick(escena, Qt.Key.Key_Return)
        self.assertEqual(self.ventana.escenas.currentIndex(), self.ventana.ESCENA_ARBOL)

    def test_minimizar_conserva_dialogo_ordinario_y_reanuda_escritura(self):
        self.ventana.establecer_juego(Juego(7, eventos=False))
        self.ventana.juego.iniciar_primera_publicacion()
        self.ventana.mostrar_escena(self.ventana.ESCENA_DIALOGO)
        escena = self.ventana.escena_dialogo
        escena.timer_inicio.stop()
        texto = "Necesitamos escuchar las distintas voces del barrio antes de reenviar otro mensaje. La conversación puede esperar a que volvamos a la ventana, sin perder su lugar ni inventar una decisión."
        escena.dialogos = [("CIUDADANO", texto)]
        escena.presentes_dialogo = {"CIUDADANO"}
        escena.mostrar_dialogo_actual()
        escena.animacion.stop()
        escena.finalizar_animacion_dialogo()
        self.ventana.showMinimized()
        self.app.processEvents()
        self.assertTrue(escena.lectura_pausada)
        self.assertFalse(escena.timer_texto.isActive())
        self.assertNotEqual(escena.estado_escena, "inactiva")
        self.ventana.showNormal()
        self.app.processEvents()
        self.assertFalse(escena.lectura_pausada)
        self.assertTrue(escena.timer_texto.isActive())
        self.assertEqual(escena.texto_completo, texto)

    def test_minimizar_no_cancela_el_plazo_local_de_decision(self):
        juego = Juego(7, eventos=False)
        juego.iniciar_primera_publicacion()
        juego.evento_actual = Evento("viral", "Hay un plazo para decidir.", True, 10)
        self.ventana.sin_limite = False
        self.ventana.establecer_juego(juego)
        self.ventana.mostrar_escena(self.ventana.ESCENA_ACCION)
        escena = self.ventana.escena_accion
        self.assertTrue(escena.timer_decision.isActive())
        self.ventana.showMinimized()
        self.app.processEvents()
        self.assertTrue(escena.timer_decision.isActive())
        anterior = escena.segundos_restantes
        escena.cuenta_regresiva()
        self.assertEqual(escena.segundos_restantes, anterior-1)
        self.ventana.showNormal()
        self.app.processEvents()
        self.assertTrue(escena.timer_decision.isActive())
        self.assertFalse(juego.decision_aplicada)

    def test_botones_por_rol_tienen_texto_completo_y_geometria_en_tres_tamanos(self):
        for rol in ("ciudadano", "periodista"):
            juego = Juego(7, eventos=False)
            juego.seleccionar_rol(rol)
            juego.iniciar_primera_publicacion()
            self.ventana.establecer_juego(juego)
            self.ventana.mostrar_escena(self.ventana.ESCENA_ACCION)
            escena = self.ventana.escena_accion
            esperadas = {a["clave"] for a in acciones_para_rol(rol)}
            self.assertEqual(set(escena.botones_por_accion), esperadas)
            for ancho, alto in ((1100, 700), (1366, 768), (1920, 1080)):
                self.ventana.resize(ancho, alto)
                self.app.processEvents()
                for clave, boton in escena.botones_por_accion.items():
                    with self.subTest(rol=rol, ancho=ancho, clave=clave):
                        self.assertEqual(boton.property("accion_rol"), clave)
                        self.assertEqual(len(boton.text().splitlines()), 1)
                        self.assertLessEqual(len(boton.text()), 12)
                        self.assertTrue(boton.toolTip())
                        self.assertTrue(boton.isVisible())
                        self.assertTrue(boton.isEnabled())
                        self.assertTrue(escena.rect().contains(boton.mapTo(escena, QPoint(0, 0))))
                        self.assertTrue(escena.rect().contains(boton.mapTo(escena, boton.rect().bottomRight())))
                        for linea in boton.text().splitlines():
                            self.assertLessEqual(boton.fontMetrics().horizontalAdvance(linea)+boton.iconSize().width()+15, boton.width())

    def test_dos_clientes_ven_su_oficio_y_solo_el_turno_activo_envia_accion(self):
        otra = crear_ventana()
        self.ventanas.append(otra)
        juego = Juego(7, eventos=False)
        juego.jugadores = [Jugador(id="c", rol="ciudadano", ciudadano_id="ana"), Jugador(id="p", rol="periodista", ciudadano_id="maria")]
        juego.iniciar_primera_publicacion()
        for ventana, identificador in ((self.ventana, "c"), (otra, "p")):
            ventana.establecer_juego(Juego.desde_datos(juego.datos()))
            ventana.cliente_red = SimpleNamespace(enviar=Mock(return_value=True), cerrar=Mock())
            ventana.mi_id = identificador
            ventana.mostrar_escena(ventana.ESCENA_ACCION)
        c, p = self.ventana.escena_accion, otra.escena_accion
        self.assertEqual(set(c.botones_por_accion), {"compartir", "conversar", "convocar", "ignorar"})
        self.assertEqual(set(p.botones_por_accion), {"contrastar", "entrevistar", "desmentir", "reservar"})
        self.assertTrue(all(b.isEnabled() for b in c.botones_por_accion.values()))
        self.assertTrue(all(not b.isEnabled() for b in p.botones_por_accion.values()))
        for ventana in self.ventanas:
            ventana.juego.turno = 1
            ventana.escena_accion.mostrar()
        p.botones_por_accion["entrevistar"].click()
        mensajes = [llamada.args[0] for llamada in otra.cliente_red.enviar.call_args_list]
        self.assertIn({"tipo": "accion", "accion": "entrevistar", "publicacion_id": 50}, mensajes)
        self.assertTrue(all(not b.isEnabled() for b in c.botones_por_accion.values()))


if __name__ == "__main__":
    unittest.main()
