"""Integración de la nueva ventana con la sesión, persistencia y TCP reales."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_LOGGING_RULES", "qt.multimedia.*=false")

from PyQt6.QtCore import QCoreApplication, QEvent, Qt, QTimer
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QPushButton

from infraestructura.recursos import RAIZ
from interfaz.feria.ventana import VentanaInvestigacion
from red.cooperativa import ServidorCooperativo


class PruebasVentanaFeria(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory(prefix="civica_prueba_feria_")
        self.carpeta = Path(self.temporal.name)
        self.preferencias = patch("interfaz.feria.ventana.PREFERENCIAS", self.carpeta / "ajustes.json")
        self.preferencias.start()
        self.ventanas = []

    def tearDown(self):
        for ventana in reversed(self.ventanas):
            ventana.close()
        self.app.processEvents()
        for ventana in self.ventanas:
            ventana.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()
        self.preferencias.stop()
        self.temporal.cleanup()

    def ventana(self, nombre="partida"):
        ventana = VentanaInvestigacion(
            semilla=4, sin_audio=True, sin_limite=True, eventos=False,
            guardar_automatico=False, ruta_guardado=self.carpeta / f"{nombre}.json",
        )
        self.ventanas.append(ventana)
        ventana.resize(1100, 700)
        ventana.show()
        self.app.processEvents()
        return ventana

    def esperar(self, condicion, mensaje, segundos=6):
        limite = time.monotonic() + segundos
        while time.monotonic() < limite:
            self.app.processEvents()
            if condicion():
                return
            QTest.qWait(12)
        estados = " | ".join(v.sala.estado.text() for v in self.ventanas)
        self.fail(mensaje + ": " + estados)

    def sincronizadas(self, servidor, *ventanas):
        return all(v.vista_actual and v.revision_red == servidor.revision for v in ventanas)

    @staticmethod
    def seleccionar_hallazgo(tablero, evidencia_id):
        for fila in range(tablero.lista_hallazgos.count()):
            item = tablero.lista_hallazgos.item(fila)
            if item.data(Qt.ItemDataRole.UserRole) == evidencia_id:
                tablero.lista_hallazgos.setCurrentRow(fila)
                return
        raise AssertionError("La pista no está disponible en el expediente")

    def test_portada_y_cuatro_espacios_en_dos_resoluciones(self):
        ventana = self.ventana()
        capturas = RAIZ / ".tmp/feria"
        capturas.mkdir(parents=True, exist_ok=True)
        for ancho, alto in ((1100, 700), (1366, 768)):
            with self.subTest(resolucion=(ancho, alto), pagina="portada"):
                ventana.resize(ancho, alto)
                self.app.processEvents()
                self.assertEqual((ventana.width(), ventana.height()), (ancho, alto))
                self.assertTrue(ventana.portada.historia.isVisible())
                self.assertTrue(ventana.portada.cooperativo.isVisible())
                self.assertTrue(ventana.grab().save(str(capturas / f"ventana_portada_{ancho}.png")))
        ventana.nueva_partida("ciudadano", "Prueba")
        for ancho, alto in ((1100, 700), (1366, 768)):
            ventana.resize(ancho, alto)
            for indice in range(4):
                with self.subTest(resolucion=(ancho, alto), pestana=indice):
                    ventana.tablero.tabs.setCurrentIndex(indice)
                    self.app.processEvents()
                    area = ventana.tablero.tabs.currentWidget()
                    self.assertLessEqual(area.widget().minimumSizeHint().width(), area.viewport().width())
                    self.assertEqual((ventana.width(), ventana.height()), (ancho, alto))
            ventana.tablero.tabs.setCurrentIndex(0)
            self.app.processEvents()
            self.assertTrue(ventana.grab().save(str(capturas / f"ventana_juego_{ancho}.png")))
        self.assertFalse(ventana.ruta_guardado.exists())

    def test_seis_casos_por_controles_preservan_rama_puntos_y_guardado_real(self):
        ventana = self.ventana()
        ventana.nueva_partida("periodista", "Prueba")
        ids = []
        for _ in range(6):
            caso = ventana.vista_actual["caso"]
            ids.append(caso["id"])
            ventana.tablero.tabs.setCurrentIndex(1)
            ventana.tablero.slider_medio.setValue(65 if caso["id"] == 110 else 80)
            ventana.tablero.examinar.click()
            self.assertTrue(ventana.vista_actual["caso"]["medio"]["revelado"])
            ventana.tablero.tabs.setCurrentIndex(2)
            ventana.tablero.accion.setCurrentIndex(ventana.tablero.accion.findData("contrastar"))
            ventana.tablero.evidencia.setCurrentIndex(ventana.tablero.evidencia.findData(f"{caso['id']}:medio"))
            ventana.tablero.certeza.setCurrentIndex(ventana.tablero.certeza.findData("confirmada"))
            ventana.tablero.titular.setText("El contexto necesita una fuente completa")
            ventana.tablero.decidir.click()
            self.assertEqual(ventana.vista_actual["fase"], "resultado")
            self.assertGreater(ventana.vista_actual["jugadores"][0]["puntos"], 0)
            self.assertTrue(ventana.tablero.continuar.isEnabled())
            ventana.tablero.continuar.click()
            self.app.processEvents()
        self.assertEqual(ids, [50, 90, 110, 40, 120, 35])
        self.assertEqual(ventana.vista_actual["fase"], "final")
        self.assertEqual(ventana.tablero.paginas.currentIndex(), 1)
        self.assertEqual(len(ventana.vista_actual["historial"]), 6)
        self.assertTrue(ventana.vista_actual["resultado_electoral"]["ganadores"])
        puntos = ventana.vista_actual["jugadores"][0]["puntos"]
        self.assertEqual(puntos, sum(r["puntos"] for r in ventana.vista_actual["historial"]))
        luis = next(r for r in ventana.vista_actual["relaciones"] if r["id"] == "luis")
        self.assertEqual(luis["estado"], "abierto")
        self.assertFalse(ventana.ruta_guardado.exists())
        ventana.guardar_rapido()
        guardado = json.loads(ventana.ruta_guardado.read_text(encoding="utf-8"))
        recuperada = self.ventana("otra")
        recuperada.cargar_desde(ventana.ruta_guardado)
        self.assertEqual(json.loads(json.dumps(recuperada.sesion.datos())), guardado)
        self.assertEqual(recuperada.vista_actual["jugadores"][0]["puntos"], puntos)
        self.assertEqual(recuperada.vista_actual["resultado_electoral"], ventana.vista_actual["resultado_electoral"])

    def test_ajustes_alcanzan_texto_y_reproductores_del_expediente(self):
        ventana = self.ventana()
        preferencias = {**ventana.preferencias, "sonido": False, "volumen": 30,
                        "tamano_texto": 20, "alto_contraste": True, "reducir_movimiento": True}
        ventana.aplicar_preferencias(preferencias, guardar=False)
        self.assertIn("font-size: 20px", ventana.tablero.styleSheet())
        self.assertIn("#ffffff", ventana.tablero.styleSheet())
        for salida in (ventana.tablero.audio_salida, ventana.tablero.video_salida):
            self.assertTrue(salida.isMuted())
            self.assertAlmostEqual(salida.volume(), .3)
        self.assertFalse((self.carpeta / "ajustes.json").exists())

    def test_dos_ventanas_reservan_roles_comparten_pistas_y_conservan_la_misma_ciudad(self):
        anfitriona, invitada = self.ventana("anfitriona"), self.ventana("invitada")
        anfitriona.abrir_sala()
        anfitriona.sala.conectar.emit(True, "127.0.0.1", 0, "Prueba A")
        self.esperar(lambda: anfitriona.mi_id is not None and anfitriona.sala._conectada,
                     "La anfitriona no entró como observadora")
        servidor = anfitriona.servidor_red
        self.assertIsInstance(servidor, ServidorCooperativo)
        invitada.abrir_sala()
        invitada.sala.conectar.emit(False, "127.0.0.1", servidor.puerto, "Prueba B")
        self.esperar(lambda: invitada.mi_id is not None and invitada.sala._conectada,
                     "La invitada no entró como observadora")
        self.assertTrue(all(p.rol is None for p in servidor.participantes.values()))
        anfitriona.sala.roles["ciudadano"].click()
        self.esperar(lambda: not invitada.sala.roles["ciudadano"].isEnabled(),
                     "La reserva del Ciudadano no llegó a la otra ventana")
        invitada.sala.roles["periodista"].click()
        self.esperar(lambda: anfitriona.sala.iniciar.isEnabled(), "Los roles distintos no habilitaron el inicio")
        self.assertFalse(anfitriona.sala.roles["periodista"].isEnabled())
        self.assertFalse(invitada.sala.roles["ciudadano"].isEnabled())
        anfitriona.sala.iniciar.click()
        self.esperar(lambda: self.sincronizadas(servidor, anfitriona, invitada), "No comenzó la investigación compartida")
        self.assertEqual(anfitriona.vista_actual["mi_rol"], "ciudadano")
        self.assertEqual(invitada.vista_actual["mi_rol"], "periodista")
        anfitriona.tablero.botones_lugares["barrio"].click()
        self.esperar(lambda: bool(anfitriona.vista_actual.get("hallazgos")) and self.sincronizadas(servidor, anfitriona, invitada),
                     "El testimonio no llegó al expediente del Ciudadano")
        testimonio = anfitriona.vista_actual["hallazgos"][0]
        self.assertNotIn(testimonio["id"], [h["id"] for h in invitada.vista_actual["hallazgos"]])
        metadato = next(h for h in invitada.vista_actual["hallazgos_disponibles"] if h["id"] == testimonio["id"])
        self.assertNotIn("texto", metadato)
        invitada.tablero.botones_lugares["archivo"].click()
        self.esperar(lambda: bool(invitada.vista_actual.get("hallazgos")) and self.sincronizadas(servidor, anfitriona, invitada),
                     "El documento no llegó al expediente de la Periodista")
        documento = invitada.vista_actual["hallazgos"][0]
        self.assertNotIn(documento["id"], [h["id"] for h in anfitriona.vista_actual["hallazgos"]])
        self.seleccionar_hallazgo(anfitriona.tablero, testimonio["id"])
        anfitriona.tablero.compartir.click()
        self.esperar(lambda: any(h["id"] == testimonio["id"] for h in invitada.vista_actual["hallazgos"])
                     and self.sincronizadas(servidor, anfitriona, invitada), "No se compartió el testimonio")
        pedidos = anfitriona.tablero.pistas_ajenas.findChildren(QPushButton)
        self.assertTrue(pedidos)
        pedidos[0].click()
        self.esperar(lambda: any(s["evidencia_id"] == documento["id"] for s in invitada.vista_actual["solicitudes"]),
                     "No llegó la solicitud de evidencia")
        self.seleccionar_hallazgo(invitada.tablero, documento["id"])
        invitada.tablero.compartir.click()
        self.esperar(lambda: any(h["id"] == documento["id"] for h in anfitriona.vista_actual["hallazgos"])
                     and self.sincronizadas(servidor, anfitriona, invitada), "No se compartió el documento")
        self.assertFalse(invitada.tablero.decidir.isEnabled())
        anfitriona.tablero.titular.setText("Se dice que el colegio cerrará")
        anfitriona.tablero.certeza.setCurrentIndex(anfitriona.tablero.certeza.findData("probable"))
        anfitriona.tablero.decidir.click()
        self.esperar(lambda: anfitriona.mi_id in anfitriona.vista_actual.get("decididos", [])
                     and invitada.tablero.decidir.isEnabled() and self.sincronizadas(servidor, anfitriona, invitada),
                     "No se transfirió la decisión a la Periodista")
        self.assertTrue(invitada.vista_actual["mision_reparacion"]["afectados"])
        invitada.tablero.accion.setCurrentIndex(invitada.tablero.accion.findData("contrastar"))
        invitada.tablero.evidencia.setCurrentIndex(invitada.tablero.evidencia.findData(documento["id"]))
        invitada.tablero.certeza.setCurrentIndex(invitada.tablero.certeza.findData("confirmada"))
        invitada.tablero.titular.setText("El acta conserva las clases y cambia el acceso")
        invitada.tablero.decidir.click()
        self.esperar(lambda: anfitriona.vista_actual.get("fase") == invitada.vista_actual.get("fase") == "resultado"
                     and self.sincronizadas(servidor, anfitriona, invitada), "No llegó la reacción conjunta")
        for clave in ("estado", "jugadores", "relaciones", "archivo_preorden", "historial", "mision_reparacion"):
            self.assertEqual(anfitriona.vista_actual[clave], invitada.vista_actual[clave], clave)
        self.assertEqual(anfitriona.vista_actual["red"]["aristas"], invitada.vista_actual["red"]["aristas"])
        anfitriona.tablero.continuar.click()
        self.esperar(lambda: not anfitriona.tablero.continuar.isEnabled() and self.sincronizadas(servidor, anfitriona, invitada),
                     "No se conservó la confirmación de lectura")
        self.assertEqual(anfitriona.vista_actual["caso"]["id"], 50)
        invitada.tablero.continuar.click()
        self.esperar(lambda: anfitriona.vista_actual["caso"]["id"] == invitada.vista_actual["caso"]["id"] == 90,
                     "La barrera de lectura no avanzó a ambos investigadores")
        clientes = (anfitriona.cliente_red, invitada.cliente_red)
        estado_cerrado = deepcopy(anfitriona.vista_actual)
        invitada.close()
        anfitriona.close()
        QTimer.singleShot(0, lambda: anfitriona.recibir_mensaje({"tipo": "estado", "revision": 10**6,
                                                              "vista": {"fase": "final"}}))
        self.esperar(lambda: all(c.cerrado.is_set() and not c.hilo.is_alive() for c in clientes),
                     "Quedaron lectores TCP después de cerrar las ventanas")
        self.assertTrue(servidor.detener.is_set())
        self.assertEqual(anfitriona.vista_actual, estado_cerrado)
        self.assertFalse(anfitriona.reloj.isActive())
        self.assertFalse(invitada.reloj.isActive())

