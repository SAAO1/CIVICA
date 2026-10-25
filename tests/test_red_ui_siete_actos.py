"""Cuatro ventanas Qt recorren los catorce turnos y su epílogo por TCP local."""
import json
import os
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QPushButton

from interfaz import EscenaCinematica, VentanaPrincipal
from juego.acciones import acciones_para_rol
from juego.campana_extendida import epilogo_extendido
from juego.lectura import BibliotecaLectura
from recursos import RAIZ
from red.servidor import Servidor
from tests.test_balance_roles_ui import AudioConSenales


class RedUISieteActosTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.parches = [
            patch("configuracion.cargar", return_value={}),
            patch("interfaz.GestorAudio", AudioConSenales),
            patch("interfaz.BibliotecaLectura", lambda: BibliotecaLectura(None)),
            patch("cinematica_narrativa.CapaCinematica._reproducir_si_corresponde"),
        ]
        for parche in self.parches:
            parche.start()
        self.ventanas = []
        self.balances = {}
        self.lineas_epilogo = {}
        self.servidor = Servidor(puerto=0, semilla=47, eventos=False, campana="extendida")
        self.servidor.iniciar()

    def tearDown(self):
        for ventana in self.ventanas:
            ventana.close()
            ventana.deleteLater()
        self.servidor.cerrar()
        self.app.processEvents()
        for parche in reversed(self.parches):
            parche.stop()

    def _estado_breve(self):
        return [(v.fase_red, v.revision_red, v.escenas.currentIndex(),
                 len(v.juego.historial), v.juego.publicacion_actual_id)
                for v in self.ventanas]

    def _esperar(self, condicion, limite=10, avanzar=False):
        hasta = time.monotonic() + limite
        while time.monotonic() < hasta:
            if condicion():
                return
            if avanzar:
                for ventana in self.ventanas:
                    self._paso_presentacion(ventana)
            QTest.qWait(2)
        self.fail(f"La presentación o la red no llegaron al estado esperado: {self._estado_breve()}")

    def _paso_presentacion(self, ventana):
        escena = ventana.escenas.currentWidget()
        if isinstance(escena, EscenaCinematica):
            # Se adelanta únicamente el reloj de entrada/salida de los paneles.
            # La cola de cifras conserva su orden y su intervalo por tarjeta.
            if escena.timer_inicio.isActive():
                escena.timer_inicio.stop()
                escena.preparar_dialogo()
                return
            if escena.animando:
                animacion = escena.animacion
                if animacion is not None and animacion.duration() >= 0:
                    animacion.setCurrentTime(animacion.duration())
                return
            if escena is ventana.escena_epilogo:
                self.lineas_epilogo[ventana].add(escena.dialogo_actual)
            if escena is ventana.escena_resultado_3 and escena._balance_en_curso:
                balance = escena.balance
                self.assertFalse(escena._balance_con_voz)
                self.assertFalse(ventana.audio.hablando)
                if not balance.completo:
                    clave = balance.clave_actual
                    self.assertIsNotNone(clave)
                    completadas = set(balance.claves_completadas)
                    escena.avanzar()
                    self.assertIs(ventana.escenas.currentWidget(), escena)
                    self.assertEqual(set(balance.claves_completadas), completadas)
                    balance.establecer_tiempo(balance.DURACION_SIN_VOZ + .1)
                    balance._paso()
                    self.assertEqual(set(balance.claves_completadas) - completadas, {clave})
                identificador = ventana.juego.ultimo_registro["publicacion"]["id"]
                self.balances[ventana][identificador] = balance.claves_completadas
                if not balance.completo:
                    return
                self.assertEqual(balance.claves_completadas,
                                 tuple(t["clave"] for t in balance.tarjetas))
            escena.avanzar()
        elif escena is ventana.escena_arbol:
            escena.boton_continuar.click()
        elif escena is ventana.escena_red:
            escena.completar()

    def test_cuatro_ventanas_completan_catorce_turnos_con_barrera_y_epilogo(self):
        inicio = time.monotonic()
        roles = ("ciudadano", "periodista", "ciudadano", "periodista")
        for numero, rol in enumerate(roles, 1):
            ventana = VentanaPrincipal()
            self.ventanas.append(ventana)
            self.balances[ventana] = {}
            self.lineas_epilogo[ventana] = set()
            ventana.audio.silenciado = True
            ventana.audio.secuencia_disponible = False
            ventana.audio.narrar.return_value = False
            ventana.reducir_movimiento = True
            ventana.sin_limite = True
            ventana.animar_fondos = False
            ventana.animar_personajes = False
            ventana.aplicar_accesibilidad()
            ventana.resize(1366, 768)
            ventana.show()
            # La prueba ejercita widgets, señales y transporte. La pintura se
            # activa al capturar; no es necesario repintar cuatro pantallas por
            # cada paso del reloj de una cifra para comprobar su obligatoriedad.
            ventana.setUpdatesEnabled(False)
            ventana.conectar_red(False, "127.0.0.1", self.servidor.puerto,
                                 f"Persona {numero}", rol)
            self._esperar(lambda: ventana.mi_id is not None)

        self.ventanas[0].cliente_red.enviar({"tipo": "iniciar"})
        ids = [50, 30, 70, 20, 60, 80, 90, 40, 100, 10, 110, 25, 120, 35]
        indices_rol = {"ciudadano": 0, "periodista": 0}
        decisiones = []
        barreras = []
        for turno, identificador in enumerate(ids):
            self._esperar(lambda: all(v.fase_red == "jugando"
                and v.juego.publicacion_actual_id == identificador
                and v.escenas.currentWidget() is v.escena_accion for v in self.ventanas),
                limite=20, avanzar=True)
            self.assertTrue(all(v.juego.campana == "extendida" for v in self.ventanas))
            if turno == 6:
                self.assertTrue(all(len(v.juego.historial) == 6 and not v.juego.finalizada for v in self.ventanas))
            activa = next(v for v in self.ventanas if v.juego.jugador.id == v.mi_id)
            rol = activa.juego.jugador.rol
            opciones = tuple(a["clave"] for a in acciones_para_rol(rol))
            accion = opciones[indices_rol[rol] % len(opciones)]
            indices_rol[rol] += 1
            for ventana, rol_propio in zip(self.ventanas, roles):
                propios = set(a["clave"] for a in acciones_para_rol(rol_propio))
                self.assertEqual(set(ventana.escena_accion.botones_por_accion), propios)
                for boton in ventana.escena_accion.botones_por_accion.values():
                    self.assertNotIn("\n", boton.text())
                    self.assertEqual(boton.isEnabled(), ventana is activa)
            activa.escena_accion.botones_por_accion[accion].click()
            self._esperar(lambda: all(v.fase_red == "resultado" for v in self.ventanas))
            self.assertTrue(all(len(v.juego.historial) == turno + 1 for v in self.ventanas))
            registro = activa.juego.ultimo_registro
            self.assertEqual(registro["accion_rol"], accion)
            self.assertEqual(registro["jugador_id"], activa.mi_id)
            decisiones.append({"publicacion": identificador, "rol": rol, "accion": accion})
            self._esperar(lambda: all(v.escenas.currentWidget() is v.escena_red for v in self.ventanas),
                          limite=15, avanzar=True)
            for ventana in self.ventanas:
                self.assertIn(identificador, self.balances[ventana])
                self.assertIn("puntos", self.balances[ventana][identificador])
            revision = self.ventanas[0].revision_red
            publicacion_pendiente = self.servidor.juego.publicacion_actual_id
            indice_pendiente = self.servidor.juego.indice_proxima_publicacion
            for ventana in self.ventanas[:3]:
                ventana.escena_red.completar()
                ventana.escena_red.boton_continuar.click()
            self._esperar(lambda: len(self.servidor.listos) == 3)
            self.assertEqual(self.servidor.fase, "resultado")
            self.assertEqual(self.servidor.revision, revision)
            # Un reporte fundado puede haber retirado ya el nodo del ABB.
            # La barrera conserva esa situación y no avanza al siguiente caso.
            self.assertEqual(self.servidor.juego.publicacion_actual_id, publicacion_pendiente)
            self.assertEqual(self.servidor.juego.indice_proxima_publicacion, indice_pendiente)
            self.assertEqual(self.servidor.juego.ultimo_registro["publicacion"]["id"], identificador)
            self.assertTrue(all(v.fase_red == "resultado" for v in self.ventanas))
            barreras.append({"publicacion": identificador, "revision": revision, "espera_al_cuarto": True})
            ultima = self.ventanas[3]
            ultima.escena_red.completar()
            ultima.escena_red.boton_continuar.click()
            self._esperar(lambda: all(v.revision_red > revision for v in self.ventanas))
            (RAIZ / ".tmp/qa_red_ui_siete_actos_progreso.json").write_text(json.dumps({
                "turnos_completados": turno + 1, "publicacion": identificador,
                "segundos": round(time.monotonic() - inicio, 3),
            }), encoding="utf-8")

        self.assertTrue(all(v.fase_red == "final" and v.juego.finalizada for v in self.ventanas))
        self.assertTrue(all(v.escenas.currentIndex() == v.ESCENA_EPILOGO for v in self.ventanas))
        datos = self.ventanas[0].juego.datos()
        self.assertTrue(all(v.juego.datos() == datos for v in self.ventanas))
        self.assertEqual([r["publicacion"]["id"] for r in datos["historial"]], ids)
        elecciones = [v.juego.resultado_electoral() for v in self.ventanas]
        self.assertTrue(all(e == elecciones[0] for e in elecciones))
        for ventana in self.ventanas:
            self.assertEqual(ventana.escena_epilogo.dialogos, epilogo_extendido(ventana.juego))
            self.assertEqual(set(self.balances[ventana]), set(ids))
        self._esperar(lambda: all(v.escenas.currentIndex() == v.ESCENA_FIN for v in self.ventanas),
                      limite=20, avanzar=True)
        for ventana in self.ventanas:
            self.assertEqual(self.lineas_epilogo[ventana], set(range(len(ventana.escena_epilogo.dialogos))))

        capturas = []
        carpeta = RAIZ / ".tmp/capturas_siete_actos_red"
        carpeta.mkdir(parents=True, exist_ok=True)
        ventana = self.ventanas[0]
        ventana.setUpdatesEnabled(True)
        for ancho, alto in ((1920, 1080), (1600, 900), (1366, 768)):
            ventana.resize(ancho, alto)
            self.app.processEvents()
            for boton in ventana.escena_fin.findChildren(QPushButton):
                if boton.isVisible():
                    centro = boton.mapTo(ventana.escena_fin, boton.rect().center())
                    self.assertTrue(ventana.escena_fin.rect().contains(centro), boton.text())
            ruta = carpeta / f"final_cuatro_{ancho}.jpg"
            self.assertTrue(ventana.grab().save(str(ruta)))
            capturas.append(str(ruta.relative_to(RAIZ)))
        informe = {
            "correcto": True, "jugadores": 4, "campana": "extendida", "casos": ids,
            "decisiones": decisiones, "barreras": barreras, "estados_identicos": True,
            "epilogo_antes_del_panel": True,
            "lineas_epilogo_por_cliente": [len(self.lineas_epilogo[v]) for v in self.ventanas],
            "balances_completos_por_cliente": [len(self.balances[v]) for v in self.ventanas],
            "resultado_electoral": elecciones[0], "capturas": capturas,
            "transporte": "TCP local real; señales de audio y decodificador aislados para esta prueba",
            "pintura": "Suspendida durante el recorrido funcional; activada para las capturas finales en tres resoluciones",
            "reloj_balance": "Una tarjeta completa por paso; no se modifica la lógica de clic ni se omiten tarjetas",
            "segundos": round(time.monotonic() - inicio, 3),
        }
        (RAIZ / "docs/verificacion_red_ui_siete_actos.json").write_text(
            json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
