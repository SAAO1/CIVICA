"""Balance central y decisiones por oficio comprobados con señales Qt reales."""
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import QObject, QPoint, Qt, pyqtSignal
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QDialog, QPushButton

from audio.catalogo_voces import segmentos_indicadores
from interfaz.ventana import VentanaPrincipal
from juego.acciones import acciones_para_rol
from juego.eventos import Evento
from juego.lectura import BibliotecaLectura
from juego.partida import Juego
from models.jugador import Jugador
from interfaz.dialogos import mostrar_configuracion, mostrar_ayuda
from infraestructura.recursos import RAIZ
from interfaz.componentes.resultados import BalanceAnimado, tarjetas_resultado


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
        self.hablando = self.secuencia_disponible and not self.silenciado
        return self.hablando

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


def preparar_balance(ventana, app, confianza=50, desinformacion=9, campana="clasica"):
    juego = Juego(7, eventos=False, campana=campana)
    juego.seleccionar_rol("periodista")
    juego.confianza = confianza
    juego.desinformacion = desinformacion
    ventana.establecer_juego(juego)
    juego.iniciar_primera_publicacion()
    juego.ejecutar_accion("contrastar")
    ventana.mostrar_escena(ventana.ESCENA_RESULTADO_3)
    escena = ventana.escena_resultado_3
    escena.timer_inicio.stop()
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
        self.patches = [patch('infraestructura.configuracion.cargar', return_value={}),
                        patch('interfaz.ventana.GestorAudio', AudioConSenales),
                        patch('interfaz.ventana.BibliotecaLectura', lambda: BibliotecaLectura(None))]
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


    def test_todos_los_indicadores_se_pintan_juntos_desde_la_entrada(self):
        escena = preparar_balance(self.ventana, self.app)
        balance = escena.balance
        self.assertEqual(len(balance.tarjetas), 8)
        esperadas = {'info_verificada','confianza','desinformacion','convivencia','bienestar_digital','conflictos','participacion','puntos'}
        self.assertEqual({t['clave'] for t in balance.tarjetas}, esperadas)
        with patch.object(balance, '_texto', wraps=balance._texto) as pintar:
            self.assertFalse(balance.grab().isNull())
        textos = [c.args[2] for c in pintar.call_args_list]
        for tarjeta in balance.tarjetas:
            self.assertIn(tarjeta['nombre'], textos)
            self.assertIn(tarjeta['nombre'], balance.accessibleDescription())
            self.assertIn(f"{tarjeta['antes']:g}  {chr(8594)}  {tarjeta['despues']:g}", textos)
        self.assertEqual(balance.geometry(), escena.rect())
        self.ventana.audio.narrar_secuencia.assert_called_once_with(
            segmentos_indicadores(self.ventana.juego.ultimo_registro), "NARRADOR")

    def test_balance_respeta_topes_signos_y_puntuacion_cero(self):
        escena = preparar_balance(self.ventana, self.app, confianza=99)
        tarjetas = {t['clave']: t for t in escena.balance.tarjetas}
        self.assertEqual((tarjetas['confianza']['delta'], tarjetas['confianza']['despues']), (1,100))
        self.assertTrue(tarjetas['desinformacion']['favorable'])
        self.assertLess(tarjetas['desinformacion']['delta'],0)
        registro = {'antes':{'confianza':50,'desinformacion':1},'despues':{'confianza':48,'desinformacion':3},'puntos':0}
        prueba = {t['clave']:t for t in tarjetas_resultado(registro)}
        self.assertFalse(prueba['confianza']['favorable'])
        self.assertFalse(prueba['desinformacion']['favorable'])
        self.assertEqual(prueba['puntos']['delta'],0)
        self.assertEqual(prueba['participacion']['delta'],0)
        self.assertIsNone(prueba['participacion']['favorable'])

    def test_espacio_continua_inmediatamente_aunque_la_voz_siga_activa(self):
        escena = preparar_balance(self.ventana, self.app)
        self.ventana.audio.hablando = True
        escena._balance_con_voz = True
        escena.balance.establecer_tiempo(.05)
        finales = []
        escena.balance.terminado.connect(lambda: finales.append(True))
        QTest.keyClick(escena, Qt.Key.Key_Space)
        self.assertEqual(finales,[True])
        self.assertEqual(self.ventana.escenas.currentIndex(),self.ventana.ESCENA_ARBOL)
        self.assertFalse(self.ventana.audio.hablando)
        self.assertFalse(escena.balance.isVisible())

    def test_auto_escucha_la_voz_y_continua_tras_ella_sin_bloquear_avance_manual(self):
        escena = preparar_balance(self.ventana,self.app)
        self.ventana.audio.hablando = True
        escena._balance_con_voz = True
        escena.balance.establecer_tiempo(1.25)
        escena.balance._paso()
        self.assertTrue(escena.balance_listo())
        escena.boton_auto.setChecked(True)
        escena.paso_lectura()
        self.assertIs(self.ventana.escenas.currentWidget(), escena)
        self.assertTrue(escena.timer_lectura.isActive())
        self.ventana.audio.hablando = False
        self.ventana.audio.secuencia_finalizada.emit(True)
        escena.paso_lectura()
        self.assertEqual(self.ventana.escenas.currentIndex(),self.ventana.ESCENA_ARBOL)

    def test_auto_sin_voz_o_silenciado_continua_sin_espera_de_audio(self):
        for silenciado, disponible in ((True, True), (False, False)):
            with self.subTest(silenciado=silenciado, grabacion=disponible):
                self.ventana.audio.silenciado = silenciado
                self.ventana.audio.secuencia_disponible = disponible
                escena = preparar_balance(self.ventana, self.app)
                self.assertFalse(self.ventana.audio.hablando)
                escena.balance.revelar()
                escena.boton_auto.setChecked(True)
                escena.paso_lectura()
                self.assertIs(self.ventana.escenas.currentWidget(), self.ventana.escena_arbol)

    def test_narracion_empieza_sola_sin_boton_y_enter_no_espera_a_la_voz(self):
        escena = preparar_balance(self.ventana,self.app)
        self.ventana.audio.narrar_secuencia.assert_called_once()
        self.assertIsNone(escena.boton_detalle)
        self.assertFalse(any("Escuchar explicación" in boton.text()
                             for boton in escena.findChildren(QPushButton)))
        self.assertTrue(self.ventana.audio.hablando)
        escena.balance.establecer_tiempo(.05)
        QTest.keyClick(escena,Qt.Key.Key_Return)
        self.assertEqual(self.ventana.escenas.currentIndex(),self.ventana.ESCENA_ARBOL)
        self.assertFalse(self.ventana.audio.hablando)

    def test_clic_interrumpe_narracion_y_silencio_conserva_avance_inmediato(self):
        for silenciado in (False, True):
            for tecla in (None, Qt.Key.Key_Return, Qt.Key.Key_Space):
                with self.subTest(silenciado=silenciado, entrada=tecla):
                    self.ventana.audio.silenciado = silenciado
                    self.ventana.audio.narrar_secuencia.reset_mock()
                    escena = preparar_balance(self.ventana, self.app)
                    self.assertEqual(self.ventana.audio.hablando, not silenciado)
                    self.ventana.audio.narrar_secuencia.assert_called_once()
                    escena.balance.establecer_tiempo(.01)
                    if tecla is None:
                        QTest.mouseClick(escena, Qt.MouseButton.LeftButton, pos=QPoint(50, 90))
                    else:
                        QTest.keyClick(escena, tecla)
                    self.assertIs(self.ventana.escenas.currentWidget(), self.ventana.escena_arbol)
                    self.assertFalse(self.ventana.audio.hablando)

    def test_ciudad_panel_opaco_y_estadisticas_centradas_en_dos_tamanos_y_fuentes(self):
        for ancho, alto in ((1100,700),(1360,720)):
            for tamano in (16,20):
                with self.subTest(resolucion=(ancho,alto),texto=tamano):
                    self.ventana.resize(ancho,alto)
                    escena=preparar_balance(self.ventana,self.app)
                    balance=escena.balance
                    balance.setStyleSheet(f"font-size:{tamano}px;background:transparent;")
                    with patch.object(balance,"_texto",wraps=balance._texto) as pintar:
                        imagen=balance.grab().toImage()
                    for x in (4,imagen.width()//2,imagen.width()-5):
                        for y in (4,imagen.height()//2,imagen.height()-5):
                            self.assertEqual(imagen.pixelColor(x,y).alpha(),255)
                    self.assertAlmostEqual(balance._panel_rect.center().x(),balance.width()/2)
                    self.assertAlmostEqual(balance._panel_rect.center().y(),balance.height()/2)
                    textos=[c.args[2] for c in pintar.call_args_list]
                    for tarjeta in balance.tarjetas:
                        self.assertIn(tarjeta["nombre"],textos)
                    nombres=[c for c in pintar.call_args_list if c.args[2] in {t["nombre"] for t in balance.tarjetas}]
                    self.assertEqual(len(nombres),8)
                    self.assertTrue(all(c.args[3]>=21 for c in nombres))
                    centros=[c.args[1].center().x() for c in nombres[:4]]
                    self.assertAlmostEqual(sum(centros)/4,balance.width()/2)
                    valores=[c for c in pintar.call_args_list if chr(8594) in str(c.args[2])]
                    self.assertEqual(len(valores),8)
                    self.assertTrue(all(c.args[3]>=33 for c in valores))

    def test_balance_prepara_y_reanuda_el_plano_elegido_incluso_ya_iniciado(self):
        for completo in (False, True):
            with self.subTest(balance_completo=completo):
                with patch('interfaz.escenas.cinematica.elegir_plano', return_value='pulido_caso_50'):
                    escena = preparar_balance(self.ventana, self.app, campana='feria')
                self.assertEqual(escena._clave_preparada, 'pulido_caso_50')
                self.assertTrue(escena._audiovisual_iniciado)
                self.assertTrue(escena.cine_narrativo.activa)
                self.assertFalse(escena.cine_narrativo._pausada)
                if completo:
                    escena.balance.revelar()
                reanudar = self.ventana.pausar_lectura_modal()
                self.assertTrue(escena.cine_narrativo._pausada)
                llamadas = self.ventana.audio.narrar_secuencia.call_count
                reanudar()
                self.assertFalse(escena.cine_narrativo._pausada)
                self.assertFalse(escena.lectura_pausada)
                self.assertEqual(self.ventana.audio.narrar_secuencia.call_count, llamadas)
                self.assertTrue(escena.balance.isVisible())

    def test_un_solo_reloj_anima_valores_reales_sin_reiniciarse_por_segmentos(self):
        escena = preparar_balance(self.ventana,self.app)
        balance = escena.balance
        for tarjeta in balance.tarjetas:
            balance.establecer_tiempo(0)
            balance.segmento(tarjeta['clave'])
            self.assertEqual(balance.valor_actual,tarjeta['antes'])
            balance.establecer_tiempo(.4)
            self.assertGreaterEqual(balance.valor_actual,min(tarjeta['antes'],tarjeta['despues']))
            self.assertLessEqual(balance.valor_actual,max(tarjeta['antes'],tarjeta['despues']))
            self.assertEqual(balance.tiempo_actual(),.4)
        balance.establecer_tiempo(1.25)
        balance._paso()
        self.assertTrue(balance.completo)
        self.assertEqual(balance.claves_completadas,tuple(t['clave'] for t in balance.tarjetas))
        self.assertEqual(balance.valor_actual,balance.tarjetas[-1]['despues'])

    def test_revelar_completa_todos_sin_espera_adicional(self):
        escena = preparar_balance(self.ventana,self.app)
        escena.balance.establecer_tiempo(.05)
        escena.revelar_texto()
        self.assertTrue(escena.balance.completo)
        self.assertEqual(escena.balance.claves_pendientes(),())
        self.assertIs(self.ventana.escenas.currentWidget(),escena)

    def test_reducir_movimiento_muestra_resultado_real_sin_secuencia(self):
        escena = preparar_balance(self.ventana,self.app)
        escena.balance.configurar(True)
        for tarjeta in escena.balance.tarjetas:
            escena.balance.segmento(tarjeta['clave'])
            self.assertEqual(escena.balance.valor_actual,tarjeta['despues'])
        escena.balance.establecer_tiempo(.36)
        escena.balance._paso()
        self.assertTrue(escena.balance.completo)

    def test_temporizador_real_completa_ocho_tarjetas_en_menos_de_cinco_segundos(self):
        import time
        balance = BalanceAnimado()
        try:
            balance.resize(1100,600)
            balance.preparar({'puntos':2,'puntos_antes':4,'puntos_despues':6})
            balance.configurar(False)
            comienzo = time.monotonic()
            balance.comenzar(automatico=True)
            QTest.qWait(1400)
            self.assertTrue(balance.completo)
            self.assertLess(time.monotonic()-comienzo,5)
            self.assertEqual(balance.valor_actual,6)
        finally:
            balance.detener()
            balance.close()
            balance.deleteLater()

    def test_cuaderno_congela_reloj_y_reanuda_sin_arrancar_voz(self):
        escena = preparar_balance(self.ventana,self.app)
        self.ventana.audio.narrar_secuencia.assert_called_once()
        self.ventana.abrir_cuaderno(0)
        self.assertTrue(escena.lectura_pausada)
        self.assertTrue(escena.balance._pausado)
        tiempo = escena.balance.tiempo_actual()
        QTest.qWait(60)
        self.assertAlmostEqual(tiempo,escena.balance.tiempo_actual(),delta=.01)
        self.ventana.cuaderno.close()
        self.app.processEvents()
        self.assertFalse(escena.lectura_pausada)
        self.assertFalse(escena.balance._pausado)
        self.assertTrue(escena.balance._timer.isActive())
        self.ventana.audio.narrar_secuencia.assert_called_once()

    def test_minimizar_congela_reloj_sin_revocar_pausa_modal(self):
        escena = preparar_balance(self.ventana,self.app)
        self.ventana.showMinimized()
        self.app.processEvents()
        tiempo = escena.balance.tiempo_actual()
        QTest.qWait(65)
        self.assertAlmostEqual(tiempo,escena.balance.tiempo_actual(),delta=.03)
        self.assertFalse(escena.balance._timer.isActive())
        self.ventana.showNormal()
        self.app.processEvents()
        self.assertTrue(escena.balance._timer.isActive())
        escena.balance.pausar()
        self.ventana.showMinimized()
        self.app.processEvents()
        self.ventana.showNormal()
        self.app.processEvents()
        self.assertTrue(escena.balance._pausado)
        self.assertFalse(escena.balance._timer.isActive())

    def test_pausa_modal_impide_avance_y_despues_permite_enter(self):
        escena = preparar_balance(self.ventana,self.app)
        reanudar = self.ventana.pausar_lectura_modal()
        QTest.keyClick(escena,Qt.Key.Key_Space)
        self.assertIs(self.ventana.escenas.currentWidget(),escena)
        reanudar()
        QTest.keyClick(escena,Qt.Key.Key_Return)
        self.assertEqual(self.ventana.escenas.currentIndex(),self.ventana.ESCENA_ARBOL)

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
            definiciones = {a["clave"]: a for a in acciones_para_rol(rol)}
            self.assertEqual(set(escena.botones_por_accion), set(definiciones))
            for ancho, alto in ((1100, 700), (1366, 768), (1920, 1080)):
                self.ventana.resize(ancho, alto)
                self.app.processEvents()
                for clave, boton in escena.botones_por_accion.items():
                    with self.subTest(rol=rol, ancho=ancho, clave=clave):
                        self.assertEqual(boton.property("accion_rol"), clave)
                        self.assertEqual(len(boton.text().splitlines()), 1)
                        # El título completo puede superar doce caracteres;
                        # debajo se mide su ancho real con la fuente del botón.
                        self.assertTrue(boton.text())
                        if "titulo_corto" in definiciones[clave]:
                            self.assertEqual(boton.text(), definiciones[clave]["titulo_corto"])
                        self.assertEqual(boton.toolTip(), "")
                        self.assertEqual(boton.statusTip(), "")
                        self.assertTrue(boton.accessibleDescription())
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
