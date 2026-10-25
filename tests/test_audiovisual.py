import os
import unittest
import wave
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from audio.gestor_audio import GestorAudio
from interfaz import VentanaPrincipal
from juego.partida import Juego
from recursos import RAIZ


class PruebasAudiovisuales(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        from PyQt6.QtCore import PYQT_VERSION_STR, QT_VERSION_STR
        print(f"\nEntorno comprobado: PyQt {PYQT_VERSION_STR} / Qt {QT_VERSION_STR}")

    def avanzar_cinematica(self, ventana, balances_presentados):
        """Cada iteración deja transcurrir un único contador completo de Qt.

        La campaña usa silencio real; por tanto se ejercita la cola local de
        animaciones. No se omite la escena ni se concluyen cifras con clics.
        """
        escena = ventana.escenas.currentWidget()
        if escena is ventana.escena_resultado_3 and escena._balance_en_curso:
            balance = escena.balance
            self.assertTrue(ventana.audio.silenciado)
            self.assertFalse(escena._balance_con_voz)
            self.assertFalse(ventana.audio.hablando)
            if not balance.completo:
                clave = balance.clave_actual
                self.assertIsNotNone(clave)
                anteriores = set(balance.claves_completadas)
                balance.establecer_tiempo(balance.DURACION_SIN_VOZ+.1)
                balance._paso()
                self.assertEqual(set(balance.claves_completadas)-anteriores, {clave})
            identificador = ventana.juego.ultimo_registro["publicacion"]["id"]
            balances_presentados[identificador] = balance.claves_completadas
            if balance.completo:
                self.assertEqual(balance.claves_completadas,
                                 tuple(tarjeta["clave"] for tarjeta in balance.tarjetas))
        escena.avanzar()

    def test_audio_recursos_volumen_y_faltante_opcional(self):
        audio = GestorAudio()
        self.assertTrue(audio.disponible)
        for archivo in (RAIZ / "assets/audio").rglob("*.wav"):
            with wave.open(str(archivo)) as recurso:
                self.assertGreater(recurso.getnframes(), 0)
        audio.configurar("musica", 0.7)
        audio.silenciar(True)
        self.assertEqual(audio.volumen("musica"), 0)
        self.assertFalse(audio.cambiar_pista("no_existe"))
        self.assertFalse(audio.reproducir_efecto("no_existe"))
        audio.detener()

    def test_timeout_y_clic_aplican_una_decision(self):
        ventana = VentanaPrincipal()
        ventana.audio.silenciar()
        juego = Juego(4, eventos=False)
        juego.iniciar_primera_publicacion()
        juego.evento_actual.urgente = True
        juego.evento_actual.segundos = 1
        ventana.establecer_juego(juego)
        ventana.mostrar_escena(ventana.ESCENA_ACCION)
        ventana.escena_accion.cuenta_regresiva()
        ventana.escena_accion.ejecutar_accion("compartir")
        self.assertEqual(len(juego.historial), 1)
        self.assertEqual(juego.ultima_accion, "ignorar")
        ventana.close()

    def test_render_y_controles_en_tres_resoluciones(self):
        ventana = VentanaPrincipal()
        ventana.audio.silenciar()
        juego = Juego(4, eventos=False)
        juego.iniciar_primera_publicacion()
        juego.ejecutar_accion("compartir")
        ventana.establecer_juego(juego)
        ventana.show()
        carpeta = RAIZ / ".tmp/capturas"
        carpeta.mkdir(parents=True, exist_ok=True)
        for ancho, alto in ((1920,1080), (1600,900), (1366,768)):
            ventana.resize(ancho, alto)
            for nombre, indice in (("accion", ventana.ESCENA_ACCION), ("arbol", ventana.ESCENA_ARBOL),
                                   ("grafo", ventana.ESCENA_GRAFO), ("final", ventana.ESCENA_FIN)):
                ventana.mostrar_escena(indice)
                self.app.processEvents()
                if nombre == "accion":
                    ventana.escena_accion.animacion_panel.setCurrentTime(350)
                if nombre == "grafo":
                    ventana.escena_red.completar()
                    self.assertTrue(ventana.escena_red.visualizador.visitados)
                captura = ventana.grab()
                self.assertFalse(captura.isNull())
                self.assertTrue(captura.save(str(carpeta/f"{nombre}_{ancho}.png")))
                escena = ventana.escenas.currentWidget()
                for boton in escena.findChildren(QPushButton):
                    if boton.isVisible():
                        punto = boton.mapTo(escena, boton.rect().center())
                        self.assertTrue(escena.rect().contains(punto), f"Botón fuera: {boton.text()} {ancho}")
        while not juego.finalizada:
            if not juego.decision_aplicada:
                juego.ejecutar_accion("verificar")
            juego.avanzar_publicacion()
        ventana.resize(1366, 768)
        ventana.mostrar_escena(ventana.ESCENA_ARBOL)
        self.app.processEvents()
        ventana.grab().save(str(carpeta/"arbol_completo_1366.png"))
        ventana.mostrar_escena(ventana.ESCENA_FIN)
        self.app.processEvents()
        ventana.grab().save(str(carpeta/"final_completo_1366.png"))
        ventana.close()

    def test_dialogo_teclado_f11_y_reduccion_movimiento(self):
        ventana = VentanaPrincipal()
        self.addCleanup(ventana.close)
        ventana.audio.silenciar()
        ventana.reducir_movimiento = True
        ventana.aplicar_accesibilidad()
        ventana.juego.iniciar_primera_publicacion()
        ventana.resize(1366, 768)
        ventana.show()
        ventana.mostrar_escena(ventana.ESCENA_DIALOGO)
        escena = ventana.escena_dialogo
        for _ in range(30):
            QTest.qWait(30)
            if not escena.animando:
                break
        self.assertFalse(escena.animando, escena.estado_escena)
        QTest.keyClick(escena, Qt.Key.Key_Space)
        self.assertFalse(escena.escribiendo)
        self.assertEqual(escena.dialogo_actual, 0)
        # El narrador ilustra el café con un cartel al reducir movimiento.
        self.assertTrue(escena.cine_narrativo.activa)
        self.assertEqual(escena.cine_narrativo.estado, "poster")
        self.assertTrue(escena.cine_narrativo._poster.isVisible())
        self.assertFalse(escena.personajes["CIUDADANO"].isVisible())
        QTest.keyClick(escena, Qt.Key.Key_Space)
        for _ in range(30):
            QTest.qWait(30)
            if escena.dialogo_actual == 1 and not escena.animando:
                break
        self.assertEqual(escena.dialogo_actual, 1)
        self.assertTrue(escena.cine_narrativo.activa)
        self.assertEqual(escena.cine_narrativo.clave_actual, "person_colegio_c")
        self.assertEqual(escena.cine_narrativo.estado, "poster")
        self.assertFalse(escena.personajes["CIUDADANO"].isVisible())
        # Los dos insertos de personajes conservan revelar/continuar. La
        # cuarta línea vuelve a los actores porque no tiene corte asignado.
        for indice in (2, 3):
            QTest.keyClick(escena, Qt.Key.Key_Space)
            QTest.keyClick(escena, Qt.Key.Key_Space)
            for _ in range(30):
                QTest.qWait(30)
                if escena.dialogo_actual == indice and not escena.animando:
                    break
            self.assertEqual(escena.dialogo_actual, indice)
        self.assertFalse(escena.cine_narrativo.activa)
        self.assertTrue(escena.personajes["CIUDADANO"].isVisible())
        ventana.resize(1600, 900)
        self.app.processEvents()
        self.assertEqual(escena.franja_superior.y(), 0)
        carpeta = RAIZ / ".tmp/capturas"
        carpeta.mkdir(parents=True, exist_ok=True)
        ventana.grab().save(str(carpeta/"dialogo_1600.png"))
        QTest.keyClick(ventana, Qt.Key.Key_F11)
        self.assertTrue(ventana.pantalla_completa)
        QTest.keyClick(ventana, Qt.Key.Key_F11)
        self.assertFalse(ventana.pantalla_completa)
        ventana.close()

    def test_clientes_qt_reciben_estado_por_senales(self):
        from red.servidor import Servidor
        servidor = Servidor(puerto=0, semilla=1, eventos=False)
        servidor.iniciar()
        ventanas = [VentanaPrincipal(), VentanaPrincipal()]
        try:
            for i, ventana in enumerate(ventanas):
                ventana.audio.silenciar()
                ventana.conectar_red(False, "127.0.0.1", servidor.puerto, f"Persona {i}", ("ciudadano", "periodista")[i])
                for _ in range(50):
                    QTest.qWait(20)
                    if ventana.mi_id:
                        break
                self.assertIsNotNone(ventana.mi_id)
            ventanas[0].cliente_red.enviar({"tipo": "iniciar"})
            for _ in range(100):
                QTest.qWait(20)
                if all(v.fase_red == "jugando" for v in ventanas):
                    break
            self.assertTrue(all(v.fase_red == "jugando" for v in ventanas))
            ventanas[0].mostrar_escena(ventanas[0].ESCENA_ACCION)
            ventanas[0].enviar_accion("compartir")
            for _ in range(100):
                QTest.qWait(20)
                if all(v.fase_red == "resultado" for v in ventanas):
                    break
            self.assertEqual(ventanas[0].juego.datos(), ventanas[1].juego.datos())
            self.assertEqual(len(ventanas[1].juego.historial), 1)
            ventanas[1].cliente_red.cerrar()
            for _ in range(100):
                QTest.qWait(20)
                if ventanas[0].fase_red == "interrumpida":
                    break
            ventanas[1].reconectar_red()
            for _ in range(100):
                QTest.qWait(20)
                if ventanas[0].fase_red == ventanas[1].fase_red == "resultado":
                    break
            self.assertEqual(ventanas[0].fase_red, "resultado")
            self.assertEqual(ventanas[0].juego.datos(), ventanas[1].juego.datos())
        finally:
            for ventana in ventanas:
                ventana.close()

            servidor.cerrar()

    def test_cuatro_ventanas_completan_la_campana_sincronizada(self):
        from red.servidor import Servidor
        from interfaz import EscenaCinematica
        servidor = Servidor(puerto=0, semilla=4, eventos=False)
        servidor.iniciar()
        ventanas = []
        balances_presentados = {}
        try:
            for i, rol in enumerate(("ciudadano", "periodista", "ciudadano", "periodista")):
                ventana = VentanaPrincipal()
                ventanas.append(ventana)
                balances_presentados[ventana] = {}
                ventana.audio.silenciar(True)
                ventana.reducir_movimiento = True
                ventana.aplicar_accesibilidad()
                ventana.show()
                ventana.conectar_red(False, "127.0.0.1", servidor.puerto, f"Persona {i+1}", rol)
                for _ in range(100):
                    QTest.qWait(10)
                    if ventana.mi_id:
                        break
                self.assertIsNotNone(ventana.mi_id)
            ventanas[0].cliente_red.enviar({"tipo": "iniciar"})
            for _ in range(3000):
                QTest.qWait(10)
                if all(v.fase_red == "final" for v in ventanas):
                    break
                for ventana in ventanas:
                    escena = ventana.escenas.currentWidget()
                    if isinstance(escena, EscenaCinematica):
                        self.avanzar_cinematica(ventana, balances_presentados[ventana])
                    elif escena is ventana.escena_accion and escena.boton_verificar.isEnabled():
                        escena.boton_verificar.click()
                    elif escena is ventana.escena_arbol:
                        escena.boton_continuar.click()
                    elif escena is ventana.escena_red:
                        escena.completar()
                        escena.boton_continuar.click()
            self.assertTrue(all(v.fase_red == "final" for v in ventanas))
            self.assertEqual(len(ventanas[0].juego.historial), 6)
            self.assertTrue(all(v.juego.datos() == ventanas[0].juego.datos() for v in ventanas))
            for ventana in ventanas:
                self.assertEqual(set(balances_presentados[ventana]), {50, 30, 70, 20, 60, 80})
                self.assertTrue(all("puntos" in claves for claves in balances_presentados[ventana].values()))
            ventanas[0].resize(1366, 768)
            self.app.processEvents()
            carpeta = RAIZ / ".tmp/capturas"
            carpeta.mkdir(parents=True, exist_ok=True)
            ventanas[0].grab().save(str(carpeta / "final_cuatro_jugadores.png"))
        finally:
            for ventana in ventanas:
                ventana.close()
            servidor.cerrar()

    def test_grafo_distingue_rumor_correccion_y_turno_sin_difusion(self):
        ventana = VentanaPrincipal()
        self.addCleanup(ventana.close)
        ventana.audio.silenciar()
        juego = Juego(4, eventos=False)
        juego.iniciar_primera_publicacion()
        ventana.establecer_juego(juego)
        juego.ejecutar_accion("compartir")
        ventana.mostrar_escena(ventana.ESCENA_GRAFO)
        escena = ventana.escena_red
        self.assertEqual(escena.visualizador.tipo, "falsa")
        self.assertIn("Información falsa", escena.leyenda.text())
        juego.avanzar_publicacion()
        juego.ejecutar_accion("ignorar")
        escena.mostrar()
        escena.pausar()
        escena.completar()
        self.assertFalse(escena.timer.isActive())
        self.assertFalse(escena.visualizador.visitados)
        self.assertFalse(escena.visualizador.aristas_usadas)
        self.assertIn("Sin difusión", escena.leyenda.text())
        juego.avanzar_publicacion()
        juego.ejecutar_accion("compartir")
        escena.mostrar()
        self.assertEqual(escena.visualizador.tipo, "verdadera")
        juego.avanzar_publicacion()
        juego.ejecutar_accion("ignorar")
        juego.avanzar_publicacion()
        juego.ejecutar_accion("verificar")
        escena.mostrar()
        self.assertEqual(escena.visualizador.tipo, "correccion")
        self.assertIn("Corrección", escena.leyenda.text())

    def test_audio_reproduce_respeta_silencio_y_cambio_rapido(self):
        import subprocess
        import sys
        import json
        proceso = subprocess.run([sys.executable, "-B", str(RAIZ / "herramientas/comprobar_audio.py")],
                                 capture_output=True, text=True, timeout=15)
        self.assertEqual(proceso.returncode, 0, proceso.stdout + "\n" + proceso.stderr)
        datos = json.loads(proceso.stdout.strip().splitlines()[-1])
        self.assertTrue(datos["reproduciendo"])
        self.assertTrue(datos["silencio_tras_volumen"])
        self.assertEqual(datos["fuente"], "ciudad.wav")
        self.assertGreater(datos["duracion"], 20000)

    def test_campana_completa_con_cada_rol_por_las_escenas(self):
        from interfaz import EscenaCinematica
        for rol in ("ciudadano", "periodista"):
            with self.subTest(rol=rol):
                ventana = VentanaPrincipal()
                self.addCleanup(ventana.close)
                ventana.audio.silenciar(True)
                balances_presentados = {}
                ventana.reducir_movimiento = True
                ventana.sin_limite = True
                ventana.aplicar_accesibilidad()
                juego = Juego(4, eventos=False)
                juego.seleccionar_rol(rol)
                ventana.establecer_juego(juego)
                ventana.show()
                ventana.mostrar_escena(ventana.ESCENA_NARRACION_1)
                for _ in range(2000):
                    QTest.qWait(10)
                    escena = ventana.escenas.currentWidget()
                    if escena is ventana.escena_fin:
                        break
                    if isinstance(escena, EscenaCinematica):
                        self.avanzar_cinematica(ventana, balances_presentados)
                    elif escena is ventana.escena_accion:
                        accion = ("verificar", "compartir", "ignorar", "reportar", "reportar", "verificar")[len(juego.historial)]
                        escena.ejecutar_accion(accion)
                    elif escena is ventana.escena_arbol:
                        escena.mostrar_inorden()
                        escena.mostrar_preorden()
                        escena.mostrar_postorden()
                        escena.continuar()
                    elif escena is ventana.escena_red:
                        escena.completar()
                        escena.continuar.emit()
                self.assertIs(ventana.escenas.currentWidget(), ventana.escena_fin)
                self.assertTrue(juego.finalizada)
                self.assertEqual([r["publicacion"]["id"] for r in juego.historial], [50,30,70,20,60,80])
                self.assertEqual(set(balances_presentados), {50, 30, 70, 20, 60, 80})
                self.assertTrue(all("puntos" in claves for claves in balances_presentados.values()))
                self.assertIsNone(juego.arbol.buscar(60))
                self.assertIsNotNone(juego.arbol.buscar(20))
                ventana.close()

