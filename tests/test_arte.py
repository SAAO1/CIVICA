import os
import json
import hashlib
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QImage, QPainter, QPixmap
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QPushButton, QCheckBox, QSlider, QVBoxLayout, QWidget

import arte
from paneles import DialogoRol, EscenaRed
from juego.partida import Juego


class PruebasArte(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_arte_no_carga_rutas_externas_y_fondo_recorta_sin_deformar(self):
        self.assertTrue(arte.pixmap_arte("../fondos/no.png").isNull())
        self.assertTrue(arte.pixmap_arte("C:/Windows/no.png").isNull())
        self.assertTrue(arte.icono_arte("desconocido").isNull())
        raiz_original = arte.RAIZ_ARTE
        try:
            with tempfile.TemporaryDirectory() as temporal:
                arte.RAIZ_ARTE = Path(temporal)
                fuente = QPixmap(300, 100)
                fuente.fill(QColor("blue"))
                p = QPainter(fuente)
                p.fillRect(0, 0, 100, 100, QColor("red"))
                p.fillRect(200, 0, 100, 100, QColor("green"))
                p.end()
                fuente.save(str(arte.RAIZ_ARTE / "fondo.png"))
                imagen = QImage(100, 100, QImage.Format.Format_ARGB32)
                imagen.fill(QColor("black"))
                p = QPainter(imagen)
                self.assertTrue(arte.dibujar_fondo(p, imagen.rect(), "fondo.png"))
                p.end()
                self.assertEqual(imagen.pixelColor(0, 50), QColor("blue"))
                self.assertEqual(imagen.pixelColor(99, 50), QColor("blue"))
        finally:
            arte.RAIZ_ARTE = raiz_original

    def test_paquete_instalado_y_atlases_validos(self):
        manifiesto = json.loads((arte.RAIZ_ARTE / "manifiesto.json").read_text(encoding="utf-8"))
        self.assertEqual(manifiesto["cantidad"], len(list(arte.RAIZ_ARTE.rglob("*.png"))))
        for recurso in manifiesto["recursos"]:
            ruta = arte.RAIZ_ARTE / recurso["archivo"]
            with self.subTest(recurso=recurso["archivo"]):
                self.assertEqual(hashlib.sha256(ruta.read_bytes()).hexdigest(), recurso["sha256"])
                imagen = QImage(str(ruta))
                self.assertFalse(imagen.isNull())
                self.assertEqual((imagen.width(), imagen.height()), (recurso["ancho"], recurso["alto"]))
                if recurso["archivo"].startswith(("ui/", "personajes/", "avatares/")):
                    self.assertTrue(imagen.hasAlphaChannel())
                    self.assertLessEqual(imagen.pixelColor(0, 0).alpha(), 8)
        self.assertFalse(arte.avatar_arte("ines").isNull())
        self.assertFalse(arte.icono_arte("verificar").isNull())
        for id in (50, 30, 70, 20, 60, 80):
            self.assertFalse(arte.miniatura_publicacion(id).isNull())

    def test_decorar_conserva_boton_senal_teclado_y_estado(self):
        ventana = QWidget()
        layout = QVBoxLayout(ventana)
        boton = QPushButton("Continuar")
        layout.addWidget(boton)
        activaciones = []
        boton.clicked.connect(lambda: activaciones.append(True))
        arte.aplicar_estilo(ventana)
        arte.decorar_botones(ventana)
        ventana.show()
        boton.setFocus()
        self.app.processEvents()
        QTest.keyClick(boton, Qt.Key.Key_Space)
        self.assertEqual(len(activaciones), 1)
        boton.setEnabled(False)
        QTest.mouseClick(boton, Qt.MouseButton.LeftButton)
        self.assertEqual(len(activaciones), 1)
        self.assertFalse(ventana.grab().isNull())
        ventana.close()

    def test_tarjetas_conservan_combo_dos_roles_y_sincronizan(self):
        dialogo = DialogoRol()
        dialogo.show()
        self.app.processEvents()
        self.assertEqual(dialogo.roles.count(), 2)
        self.assertTrue(dialogo.tarjetas["ciudadano"].isChecked())
        QTest.mouseClick(dialogo.tarjetas["periodista"], Qt.MouseButton.LeftButton)
        self.assertEqual(dialogo.roles.currentData(), "periodista")
        self.assertTrue(dialogo.tarjetas["periodista"].isChecked())
        dialogo.roles.setCurrentIndex(0)
        self.assertTrue(dialogo.tarjetas["ciudadano"].isChecked())
        self.assertFalse(dialogo.tarjetas["periodista"].isChecked())
        dialogo.close()

    def test_controles_ilustrados_conservan_teclado_y_valores(self):
        ventana = QWidget()
        self.addCleanup(ventana.close)
        layout = QVBoxLayout(ventana)
        check = QCheckBox("Reducir movimiento")
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(30)
        layout.addWidget(check)
        layout.addWidget(slider)
        arte.aplicar_estilo(ventana)
        ventana.show()
        self.app.processEvents()
        QTest.keyClick(check, Qt.Key.Key_Space)
        self.assertTrue(check.isChecked())
        QTest.keyClick(slider, Qt.Key.Key_Right)
        self.assertEqual(slider.value(), 31)
        check.setEnabled(False)
        QTest.keyClick(check, Qt.Key.Key_Space)
        self.assertTrue(check.isChecked())
        self.assertFalse(ventana.grab().isNull())

    def test_observatorio_prioriza_recorridos_y_oculta_edicion_manual(self):
        juego = Juego(4, eventos=False)
        escena = EscenaRed(juego)
        escena.resize(1366, 768)
        escena.show()
        self.app.processEvents()
        self.assertEqual(len(escena.botones_red), 3)
        escena.botones_red[0].click()
        escena.completar()
        self.assertIn(escena.origen.currentData(), escena.visualizador.visitados)
        textos = {boton.text() for boton in escena.findChildren(QPushButton)}
        self.assertIn("Comparar alcance", textos)
        self.assertTrue(textos.isdisjoint({"Pausar", "Completar", "Conectar", "Desconectar", "Agregar ciudadano", "Retirar seleccionado"}))
        self.assertFalse(hasattr(escena, "velocidad"))
        self.assertFalse(escena.grab().isNull())
        escena.close()
