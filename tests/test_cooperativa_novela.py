"""Dos novelas originales, sala ilustrada y transporte TCP real."""
import base64
import json
import os
import time
import unittest
from unittest.mock import patch
import zlib

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_LOGGING_RULES", "qt.multimedia.*=false")

from PyQt6.QtCore import QCoreApplication, QEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from juego.lectura import BibliotecaLectura
from interfaz.novela.ventana import VentanaNovela
from interfaz.novela.cooperativa import reconstruir_juego_novela


class PruebasCooperativaNovela(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        preferencias = {
            "silenciado": True, "voces_activadas": False, "sin_limite": True,
            "reducir_movimiento": True, "animar_fondos": False,
            "animar_personajes": False, "velocidad_texto": 0,
        }
        self.parches = [
            patch("infraestructura.configuracion.cargar", return_value=preferencias),
            patch("interfaz.ventana.BibliotecaLectura", lambda: BibliotecaLectura(None)),
        ]
        for parche in self.parches:
            parche.start()
            self.addCleanup(parche.stop)
        self.ventanas = []

    def tearDown(self):
        for ventana in reversed(self.ventanas):
            ventana.close()
            ventana.deleteLater()
        self.app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def esperar(self, condicion, texto, segundos=8):
        limite = time.monotonic()+segundos
        while time.monotonic() < limite:
            self.app.processEvents()
            if condicion():
                return
            QTest.qWait(10)
        avisos = [v.statusBar().currentMessage() for v in self.ventanas]
        raise AssertionError(texto+"; avisos: "+repr(avisos))

    def abrir_dos_novelas(self):
        for _ in range(2):
            ventana = VentanaNovela(semilla=4, eventos=False)
            self.ventanas.append(ventana)
            ventana.resize(1366, 830)
            ventana.show()
            ventana.control_cooperativo.abrir_sala(modal=False)
        creador, invitado = self.ventanas
        cc, ci = creador.control_cooperativo, invitado.control_cooperativo
        cc.conectar(True, "127.0.0.1", 0, "Ciudadano")
        self.esperar(lambda: cc.mi_id is not None and cc.sala._conectada,
                     "La sala del creador no recibe disponibilidad")
        servidor = cc.servidor
        ci.conectar(False, "127.0.0.1", servidor.puerto, "Periodista")
        self.esperar(lambda: ci.mi_id is not None and ci.sala._conectada,
                     "La sala del invitado no recibe disponibilidad")
        cc.sala.roles["ciudadano"].click()
        self.esperar(
            lambda: not ci.sala.roles["ciudadano"].isEnabled()
            and ci.sala.roles["ciudadano"].text() == "Ocupado",
            "El rol reservado no aparece gris en la otra sala",
        )
        ci.sala.roles["periodista"].click()
        self.esperar(lambda: cc.sala.iniciar.isEnabled(),
                     "Los roles exclusivos no habilitan el inicio")
        self.assertFalse(ci.sala.iniciar.isEnabled())
        cc.sala.iniciar.click()
        self.esperar(
            lambda: all(v.vista_novela.get("caso", {}).get("id") == 50
                        for v in self.ventanas),
            "Las dos novelas no reciben el mismo primer acto",
        )
        self.assertTrue(all(v.escenas.currentWidget() is v.escena_narracion_1
                            for v in self.ventanas))
        self.assertTrue(all(v.sesion is None for v in self.ventanas))
        self.assertFalse(cc.sala.isVisible())
        self.assertFalse(ci.sala.isVisible())
        return creador, invitado, servidor

    def sincronizadas(self, servidor):
        return all(v.control_cooperativo.revision == servidor.revision for v in self.ventanas)

    def test_editor_y_dos_decisiones_conservan_novela_y_avanzan_al_segundo_acto(self):
        creador, invitado, servidor = self.abrir_dos_novelas()
        for v in self.ventanas:
            v.mostrar_escena(v.ESCENA_ACCION)
        invitado.abrir_fuentes()
        fuentes = invitado.overlay_investigacion
        self.assertIsNotNone(fuentes)
        fuentes.botones_lugares["archivo"].click()
        self.esperar(
            lambda: any(h["id"] == "50:documento"
                        for h in invitado.vista_novela.get("hallazgos", [])),
            "La periodista no recibe su documento privado",
        )
        self.assertNotIn("50:documento",
                         [h["id"] for h in creador.vista_novela["hallazgos"]])
        self.esperar(lambda: self.sincronizadas(servidor),
                     "Las vistas no alcanzan la revisión del documento")
        creador.enviar_accion("compartir")
        editor = creador.overlay_investigacion
        self.assertIsNotNone(editor)
        editor._ir_confirmacion()
        editor.confirmar.click()
        self.esperar(
            lambda: creador.mi_id in invitado.vista_novela.get("decididos", []),
            "La decisión del Ciudadano no se sincroniza",
        )
        self.assertIs(creador.escenas.currentWidget(), creador.escena_resultado_1)
        self.assertEqual(creador.juego.ultimo_registro["jugador_id"], creador.mi_id)
        self.assertFalse(invitado.juego.decision_aplicada)
        self.assertEqual(invitado.juego.jugador.id, invitado.mi_id)
        escena_del_creador = creador.escenas.currentWidget()
        self.esperar(lambda: self.sincronizadas(servidor),
                     "La periodista no recibe su turno")
        invitado.enviar_accion("desmentir")
        editor = invitado.overlay_investigacion
        self.assertTrue(editor.confirmar.isEnabled())
        editor._ir_confirmacion()
        editor.confirmar.click()
        self.esperar(
            lambda: all(v.vista_novela.get("fase") == "resultado" for v in self.ventanas),
            "Ambas decisiones no producen el resultado compartido",
        )
        self.assertEqual(len(servidor.sesion.juego.historial), 2)
        self.assertIsNone(servidor.sesion.juego.arbol.buscar(50))
        self.assertIs(creador.escenas.currentWidget(), escena_del_creador,
                      "La decisión del compañero reinició la consecuencia propia")
        self.assertEqual(creador.juego.ultimo_registro["jugador_id"], creador.mi_id)
        self.assertEqual(invitado.juego.ultimo_registro["jugador_id"], invitado.mi_id)
        for ventana in (creador, invitado):
            ventana.mostrar_escena(ventana.ESCENA_ARBOL)
            self.assertIs(ventana.escenas.currentWidget(), ventana.escena_arbol)
            self.assertEqual(ventana.vista_novela["caso"]["id"], 50)
            self.assertEqual(ventana.vista_novela["confirmados"], [])
            ventana.escena_arbol.boton_inorden.click()
            self.assertIn("INORDEN", ventana.escena_arbol.resultado.text())
            ventana.escena_arbol.boton_continuar.click()
            self.assertIs(ventana.escenas.currentWidget(), ventana.escena_red)
            self.assertEqual(ventana.vista_novela["caso"]["id"], 50)
        creador.escena_red.boton_continuar.click()
        self.esperar(
            lambda: creador.mi_id in invitado.vista_novela.get("confirmados", []),
            "La primera novela no confirma la revisión del grafo",
        )
        self.assertIs(creador.escenas.currentWidget(), creador.escena_red)
        self.assertEqual(creador.vista_novela["caso"]["id"], 50)
        invitado.escena_red.boton_continuar.click()
        self.esperar(
            lambda: all(v.vista_novela.get("caso", {}).get("id") == 90
                        for v in self.ventanas),
            "Las dos novelas no pasan al segundo acto",
        )
        self.assertTrue(all(v.escenas.currentWidget() is v.escena_dialogo
                            for v in self.ventanas))

    def test_grafo_espera_otro_rol_sin_repetir_visores_ni_saltar_turnos(self):
        creador, invitado, servidor = self.abrir_dos_novelas()
        creador.enviar_comando_novela({"tipo": "decidir", "accion": "ignorar"})
        self.esperar(
            lambda: creador.mi_id in invitado.vista_novela.get("decididos", [])
            and self.sincronizadas(servidor),
            "La primera decisión no llega a ambas novelas",
        )
        creador.mostrar_escena(creador.ESCENA_ARBOL)
        creador.escena_arbol.boton_continuar.click()
        creador.escena_red.boton_continuar.click()
        self.assertIs(creador.escenas.currentWidget(), creador.escena_red)
        self.assertEqual(creador.vista_novela["caso"]["id"], 50)
        self.assertEqual(creador.vista_novela["confirmados"], [])
        self.assertFalse(creador.escena_red.boton_continuar.isEnabled())
        invitado.enviar_comando_novela({"tipo": "decidir", "accion": "reservar"})
        self.esperar(
            lambda: creador.mi_id in invitado.vista_novela.get("confirmados", []),
            "El grafo terminado no confirma al cerrar la segunda decisión",
        )
        self.assertIs(creador.escenas.currentWidget(), creador.escena_red)
        self.assertEqual(creador._visores_vistos, {"arbol", "grafo"})
        self.assertEqual(creador.vista_novela["caso"]["id"], 50)
        self.assertIs(invitado.escenas.currentWidget(), invitado.escena_resultado_1)
        invitado.mostrar_escena(invitado.ESCENA_ARBOL)
        self.assertEqual(invitado.vista_novela["caso"]["id"], 50)
        invitado.escena_arbol.boton_continuar.click()
        self.assertIs(invitado.escenas.currentWidget(), invitado.escena_red)
        invitado.escena_red.boton_continuar.click()
        self.esperar(
            lambda: all(v.vista_novela.get("caso", {}).get("id") == 90
                        for v in self.ventanas),
            "La revisión de ambos grafos no abre el segundo acto",
        )
        self.assertTrue(all(not v._visores_vistos for v in self.ventanas))
        self.assertEqual(len(servidor.sesion.juego.historial), 2)

    def test_reconexion_conserva_escena_original_y_perspectiva(self):
        creador, invitado, servidor = self.abrir_dos_novelas()
        escena = invitado.escenas.currentWidget()
        identidad = invitado.mi_id
        with servidor.lock:
            servidor._cerrar_conexion(servidor.conexiones[identidad])
        self.esperar(
            lambda: invitado.control_cooperativo.cliente.cerrado.is_set()
            and all(v.vista_novela.get("fase") == "pausa" for v in self.ventanas),
            "La caída TCP no pausa la novela",
        )
        self.assertIs(invitado.escenas.currentWidget(), escena)
        self.assertEqual(invitado.control_cooperativo.vista["fase"], "pausa",
                         "La vista del socket perdido siguió habilitando la campaña")
        invitado.reconectar_red()
        self.esperar(
            lambda: all(v.vista_novela.get("fase") == "investigacion"
                        for v in self.ventanas)
            and not invitado.control_cooperativo.cliente.cerrado.is_set(),
            "La novela no recupera la conexión",
        )
        self.assertEqual(invitado.control_cooperativo.revision, servidor.revision,
                         "La reconexión mostró una vista del socket anterior")
        self.assertEqual(invitado.mi_id, identidad)
        self.assertEqual(invitado.vista_novela["mi_rol"], "periodista")
        self.assertIs(invitado.escenas.currentWidget(), escena)
        self.assertFalse(escena.lectura_pausada,
                         "La reconexión dejó congelada la lectura original")

    def test_investigar_desde_cuaderno_conserva_dialogo_y_reanuda_lectura(self):
        creador, _, servidor = self.abrir_dos_novelas()
        escena = creador.escenas.currentWidget()
        self.esperar(
            lambda: escena.estado_escena in ("dialogo", "esperando")
            and bool(escena.texto_completo),
            "La introducción no prepara su línea de diálogo",
        )
        juego_original, texto = creador.juego, escena.texto_completo
        creador.abrir_fuentes()
        cuaderno = creador.overlay_investigacion
        self.assertIsNotNone(cuaderno)
        self.assertTrue(escena.lectura_pausada)
        cuaderno.botones_lugares["barrio"].click()
        self.esperar(
            lambda: creador.vista_novela.get("acciones_restantes") == 1
            and self.sincronizadas(servidor),
            "Investigar desde el cuaderno no actualiza la novela",
        )
        self.assertIs(creador.juego, juego_original,
                      "El snapshot sustituyó el juego que mantiene pausada la lectura")
        self.assertIs(creador.escenas.currentWidget(), escena)
        self.assertEqual(escena.texto_completo, texto)
        cuaderno.cerrar()
        self.app.processEvents()
        self.assertIsNone(creador.overlay_investigacion)
        self.assertFalse(escena.lectura_pausada,
                         "Cerrar el cuaderno dejó congelado el diálogo")
        self.assertIs(creador.escenas.currentWidget(), escena)
        self.assertEqual(escena.texto_completo, texto)
        self.esperar(lambda: not escena.animando,
                     "La escena no termina su animación al reanudar")
        if escena.escribiendo:
            escena.revelar_texto()
        escena.avanzar()
        self.esperar(
            lambda: creador.escenas.currentWidget() is not escena
            or escena.texto_completo != texto,
            "La lectura no continúa después de cerrar el cuaderno",
        )

    def preparar_salida_dialogo(self, ventana):
        ventana.mostrar_escena(ventana.ESCENA_DIALOGO)
        escena = ventana.escena_dialogo
        self.esperar(lambda: escena.estado_escena == "esperando",
                     "El diálogo no termina de entrar")
        texto = escena.texto_completo
        escena.avanzar()
        self.assertEqual(escena.estado_escena, "saliendo")
        # Da tiempo a una caída LAN durante la transición real de dos franjas.
        for indice in range(escena.animacion.animationCount()):
            escena.animacion.animationAt(indice).setDuration(600)
        return escena, texto

    def test_cuaderno_durante_salida_congela_transicion_y_permite_seguir(self):
        creador, _, _ = self.abrir_dos_novelas()
        escena, texto = self.preparar_salida_dialogo(creador)
        creador.abrir_cuaderno()
        cuaderno = creador.overlay_investigacion
        self.assertIsNotNone(cuaderno)
        self.assertTrue(escena.lectura_pausada)
        QTest.qWait(700)
        self.assertEqual(escena.texto_completo, texto,
                         "La transición cambió de línea detrás del cuaderno")
        cuaderno.cerrar()
        self.esperar(lambda: escena.texto_completo != texto
                     and not escena.lectura_pausada,
                     "Cerrar el cuaderno no reanuda la siguiente intervención")
        self.assertIs(creador.escenas.currentWidget(), escena)

    def test_reconexion_durante_salida_reanuda_siguiente_intervencion(self):
        creador, invitado, servidor = self.abrir_dos_novelas()
        escena, texto = self.preparar_salida_dialogo(invitado)
        with servidor.lock:
            servidor._cerrar_conexion(servidor.conexiones[invitado.mi_id])
        self.esperar(
            lambda: all(v.vista_novela.get("fase") == "pausa" for v in self.ventanas),
            "La caída LAN no pausa las dos perspectivas",
        )
        QTest.qWait(700)
        self.assertEqual(escena.texto_completo, texto,
                         "La línea avanzó mientras faltaba el compañero")
        invitado.reconectar_red()
        self.esperar(
            lambda: all(v.vista_novela.get("fase") == "investigacion"
                        for v in self.ventanas)
            and escena.texto_completo != texto
            and not escena.lectura_pausada,
            "La reconexión no reanuda la intervención pendiente",
        )
        self.assertIs(invitado.escenas.currentWidget(), escena)

    def test_snapshot_comprimido_reconstruye_arbol_y_grafo_para_presentacion(self):
        creador, _, servidor = self.abrir_dos_novelas()
        datos = servidor.sesion.juego.datos()
        comprimido = base64.b64encode(zlib.compress(
            json.dumps(datos).encode("utf-8"))).decode("ascii")
        vista = creador.control_cooperativo.vista
        copia = reconstruir_juego_novela({"datos_comprimidos": comprimido}, vista)
        self.assertEqual([p.id for p in copia.arbol.preorden()],
                         [p.id for p in servidor.sesion.juego.arbol.preorden()])
        self.assertEqual(copia.grafo.aristas(), servidor.sesion.juego.grafo.aristas())
        self.assertFalse(copia.decision_aplicada)
        self.assertNotIn("hallazgos", datos)
        with self.assertRaises(ValueError):
            reconstruir_juego_novela({"datos_comprimidos": "eA=="}, vista)


if __name__ == "__main__":
    unittest.main()
