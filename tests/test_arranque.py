import ast
import contextlib
import importlib
import io
import os
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication
from recursos import RAIZ


class PruebasArranque(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Qt requiere una sola QApplication con vida durante toda la suite.
        cls.app = QApplication.instance() or QApplication([])

    def test_fuentes_compilan_y_main_no_se_ejecuta_al_importar(self):
        for ruta in RAIZ.rglob("*.py"):
            if any(p in {".venv", "venv", ".tmp"} for p in ruta.parts):
                continue
            with self.subTest(archivo=str(ruta.relative_to(RAIZ))):
                ast.parse(ruta.read_text(encoding="utf-8-sig"), filename=str(ruta))
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            demo = importlib.import_module("main")
        self.assertEqual(salida.getvalue(), "")
        with contextlib.redirect_stdout(salida):
            demo.main()
        self.assertIn("Raíz: #80", salida.getvalue())

    def test_recursos_desde_otro_directorio(self):
        from interfaz import VentanaPrincipal
        app = self.app
        original = os.getcwd()
        with tempfile.TemporaryDirectory() as carpeta:
            try:
                os.chdir(carpeta)
                ventana = VentanaPrincipal()
                ventana.audio.silenciar()
                ventana.resize(1366, 768)
                ventana.show()
                app.processEvents()
                self.assertFalse(ventana.escena_inicio.fondo.pixmap().isNull())
                self.assertEqual(len(ventana.juego.publicaciones_planificadas), 6)
                ventana.close()
            finally:
                os.chdir(original)
