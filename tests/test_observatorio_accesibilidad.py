import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import QRectF
from PyQt6.QtWidgets import QApplication, QCheckBox, QComboBox, QPushButton, QTabWidget, QWidget

from juego.partida import Juego
from paneles import EscenaRed, mostrar_configuracion
from recursos import RAIZ


class PruebasObservatorioAccesible(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_repeticion_sin_puntos_y_limpieza_al_ocultar(self):
        juego = Juego(4, eventos=False)
        juego.iniciar_primera_publicacion()
        juego.ejecutar_accion("compartir")
        escena = EscenaRed(juego)
        self.addCleanup(escena.close)
        escena.show()
        escena.mostrar()
        antes = juego.datos()
        escena.comparar()
        for _ in range(3):
            while escena.indice < len(escena.pasos):
                escena.paso()
            self.assertTrue(escena.timer_repeticion.isActive())
            self.assertEqual(escena.timer_repeticion.interval(), 2000)
            escena.repetir()
            self.assertEqual(escena.indice, 1)
        self.assertEqual(juego.datos(), antes)
        escena.hide()
        self.assertFalse(escena.timer.isActive())
        self.assertFalse(escena.timer_repeticion.isActive())

    def test_movimiento_reducido_no_anima_ni_repite_y_dfs_dibuja_aristas(self):
        juego = Juego(4, eventos=False)
        escena = EscenaRed(juego)
        self.addCleanup(escena.close)
        escena.reducir_movimiento = True
        escena.recorrer("dfs")
        self.assertEqual(escena.indice, len(escena.pasos))
        self.assertTrue(escena.visualizador.aristas_usadas)
        self.assertFalse(escena.timer.isActive())
        self.assertFalse(escena.timer_repeticion.isActive())

    def test_diecinueve_ciudadanos_tienen_etiquetas_separadas(self):
        juego = Juego(4, eventos=False)
        for indice in range(10):
            juego.grafo.agregar_vertice(f"vecina_{indice}", f"Vecina {indice}")
        escena = EscenaRed(juego)
        self.addCleanup(escena.close)
        escena.resize(1366, 768)
        escena.show()
        self.app.processEvents()
        escena.grab()
        posiciones = list(escena.visualizador.posiciones.values())
        cajas = [QRectF(p.x() - 57, p.y() + 36, 114, 21) for p in posiciones]
        self.assertEqual(len(cajas), 19)
        for indice, caja in enumerate(cajas):
            self.assertTrue(QRectF(escena.visualizador.rect()).contains(caja))
            for otra in cajas[indice + 1:]:
                self.assertFalse(caja.intersects(otra))
        carpeta = RAIZ / ".tmp/capturas"
        carpeta.mkdir(parents=True, exist_ok=True)
        escena.grab().save(str(carpeta / "observatorio_19_ciudadanos.png"))

    def test_configuracion_guarda_colores_voces_y_ofrece_manual(self):
        parent = QWidget()
        self.addCleanup(parent.close)
        for clave in ("sin_limite", "reducir_movimiento", "alto_contraste", "sprites_sobre_ilustracion"):
            setattr(parent, clave, False)
        parent.modo_daltonismo = "normal"
        parent.voces_activadas = True
        cambios_voces = []
        parent.audio = SimpleNamespace(volumenes={"general": 0.5, "musica": 0.3, "ambiente": 0.2, "efectos": 0.6, "voces": 0.8}, silenciado=False,
                                       configurar=lambda *args: None,
                                       silenciar=lambda valor: setattr(parent.audio, "silenciado", valor),
                                       configurar_voces=cambios_voces.append)
        parent.aplicar_accesibilidad = lambda: None

        def editar(dialogo):
            dialogo.show()
            self.app.processEvents()
            carpeta = RAIZ / ".tmp/capturas"
            carpeta.mkdir(parents=True, exist_ok=True)
            dialogo.grab().save(str(carpeta / "configuracion_accesibilidad.png"))
            color = next(c for c in dialogo.findChildren(QComboBox) if c.accessibleName() == "Modo de colores para daltonismo")
            color.setCurrentIndex(color.findData("tritanopia"))
            voz = next(c for c in dialogo.findChildren(QCheckBox) if c.text() == "Voces de los personajes y del narrador")
            voz.setChecked(False)
            botones = {boton.text(): boton for boton in dialogo.findChildren(QPushButton)}
            self.assertIn("Manual de usuario", botones)
            dialogo.findChild(QTabWidget).setCurrentIndex(1)
            self.app.processEvents()
            dialogo.grab().save(str(carpeta / "configuracion_voces.png"))
            botones["Guardar preferencias"].click()
            return 1

        with patch("paneles.DialogoIlustrado.exec", editar), patch("configuracion.guardar") as guardar:
            mostrar_configuracion(parent)
        preferencias = guardar.call_args.args[0]
        self.assertEqual(preferencias["modo_daltonismo"], "tritanopia")
        self.assertFalse(preferencias["voces_activadas"])
        self.assertEqual(cambios_voces, [False])


if __name__ == "__main__":
    unittest.main()
