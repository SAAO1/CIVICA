"""La piel de botones no debe borrar retratos ni nombres de tarjetas propias."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter as PintorReal, QPixmap
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QLabel, QWidget

from infraestructura.recursos import RAIZ
from interfaz.dialogos import DialogoRol
from interfaz.componentes.arte import pixmap_arte
from interfaz.novela.componentes import _PielNovela, decorar_novela
from interfaz.novela.sala import SalaCooperativaNovela


class PintorTarjetas:
    RenderHint = PintorReal.RenderHint
    trazas = {}

    def __init__(self, widget):
        self.rol = getattr(widget, "rol", None)
        self.real = PintorReal(widget)

    def __getattr__(self, nombre):
        return getattr(self.real, nombre)

    def drawPixmap(self, *args):
        if self.rol:
            self.trazas.setdefault(self.rol, {"imagenes": [], "textos": []})["imagenes"].extend(
                imagen.cacheKey() for imagen in args if isinstance(imagen, QPixmap) and not imagen.isNull())
            if len(args) == 3 and isinstance(args[1], QPixmap):
                destino, imagen, origen = args
                self.trazas[self.rol].setdefault("encuadres", []).append(
                    (imagen.cacheKey(), origen.width(), origen.height(), destino.width(), destino.height()))
        return self.real.drawPixmap(*args)

    def drawText(self, *args):
        if self.rol:
            self.trazas.setdefault(self.rol, {"imagenes": [], "textos": []})["textos"].append(args[-1])
        return self.real.drawText(*args)


class PruebasSeleccionIlustrada(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.padre = QWidget()
        self.padre.resize(1100, 700)
        self.padre.show()
        self.dialogos = []

    def tearDown(self):
        for dialogo in self.dialogos:
            dialogo.close()
            dialogo.deleteLater()
        self.padre.close()
        self.padre.deleteLater()
        self.app.processEvents()

    def test_dos_tarjetas_pintan_retrato_y_nombre_despues_de_decorar(self):
        dialogo = DialogoRol(self.padre)
        self.dialogos.append(dialogo)
        decorar_novela(dialogo)
        PintorTarjetas.trazas = {}
        with patch("interfaz.dialogos.QPainter", PintorTarjetas):
            dialogo.show()
            self.app.processEvents()
            for tarjeta in dialogo.tarjetas.values():
                self.assertFalse(hasattr(tarjeta, "_piel_novela"))
                self.assertFalse(tarjeta.grab().isNull())
        for rol, nombre in (("ciudadano", "Ciudadano"), ("periodista", "Periodista")):
            with self.subTest(rol=rol):
                traza = PintorTarjetas.trazas[rol]
                self.assertTrue(traza["imagenes"], "La tarjeta perdió el retrato real")
                self.assertIn(nombre, traza["textos"])
                neutral = pixmap_arte(f"personajes/{rol}_neutral.png")
                tarjeta = dialogo.tarjetas[rol]
                fuente, origen = tarjeta._encuadre_retrato
                self.assertEqual(fuente[0], neutral.cacheKey())
                self.assertLess(origen.height(), neutral.height(), "Debe verse el busto, no reducir el cuerpo completo")
                self.assertIn(tarjeta._retrato_escalado[1].cacheKey(), traza["imagenes"])
                for _, _, _, destino_ancho, destino_alto in traza["encuadres"]:
                    self.assertGreaterEqual(min(origen.width()/destino_ancho, origen.height()/destino_alto), 2,
                                            "La fuente debe superar incluso una pantalla de densidad 2x")
        carpeta = RAIZ / ".tmp/novela"
        carpeta.mkdir(parents=True, exist_ok=True)
        dialogo.grab().save(str(carpeta / "seleccion_roles_corregida.png"))
        QTest.mouseClick(dialogo.tarjetas["periodista"], Qt.MouseButton.LeftButton)
        self.assertEqual(dialogo.roles.currentData(), "periodista")
        QTest.mouseClick(dialogo.tarjetas["ciudadano"], Qt.MouseButton.LeftButton)
        self.assertEqual(dialogo.roles.currentData(), "ciudadano")

    def test_decorar_retira_filtro_antiguo_de_una_tarjeta_personalizada(self):
        dialogo = DialogoRol(self.padre)
        self.dialogos.append(dialogo)
        tarjeta = dialogo.tarjetas["ciudadano"]
        tarjeta._piel_novela = _PielNovela(tarjeta)
        tarjeta.installEventFilter(tarjeta._piel_novela)
        decorar_novela(dialogo)
        self.assertFalse(hasattr(tarjeta, "_piel_novela"))
        self.assertTrue(tarjeta.property("conservarPintura"))

    def test_sala_conserva_retratos_dos_roles_y_reserva_exclusiva(self):
        sala = SalaCooperativaNovela(self.padre)
        self.dialogos.append(sala)
        decorar_novela(sala)
        sala.show()
        self.app.processEvents()
        self.assertEqual(set(sala.roles), {"ciudadano", "periodista"})
        retratos = [label for label in sala.findChildren(QLabel)
                    if label.pixmap() is not None and not label.pixmap().isNull()]
        self.assertGreaterEqual(len(retratos), 2)
        mensaje = {"jugadores": [{"id": "c", "nombre": "Prueba", "rol": "ciudadano"},
                                 {"id": "p", "nombre": "Otra voz", "rol": "periodista"}],
                   "roles_ocupados": {"ciudadano": {"id": "c", "nombre": "Prueba"},
                                      "periodista": {"id": "p", "nombre": "Otra voz"}},
                   "anfitrion": "c", "puede_iniciar": True}
        sala.actualizar(mensaje, "c")
        self.assertTrue(sala.roles["ciudadano"].isChecked())
        self.assertFalse(sala.roles["periodista"].isEnabled())
        self.assertTrue(sala.iniciar.isEnabled())

