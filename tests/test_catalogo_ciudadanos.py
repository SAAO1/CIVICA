import os
import tempfile
import unittest
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtGui import QColor, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication

import arte
from catalogo_ciudadanos import (
    CATALOGO_CIUDADANOS, RUTA_ATLAS_CIUDADANOS, indice_retrato_ciudadano,
)
from juego.red_social import ampliar_comunidad, crear_red_social


class PruebasCatalogoCiudadanos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        arte._AVATARES.clear()
        arte._PIXMAPS.clear()

    @staticmethod
    def crear_atlas(raiz, color_extra=0):
        """Cada celda de prueba tiene un color identificable y distinto."""
        ruta = raiz / RUTA_ATLAS_CIUDADANOS
        ruta.parent.mkdir(parents=True, exist_ok=True)
        imagen = QPixmap(80, 80)
        imagen.fill(QColor("transparent"))
        pintor = QPainter(imagen)
        for indice in range(64):
            color = QColor(indice * 3, 30 + color_extra, 255 - indice * 3)
            pintor.fillRect((indice % 8) * 10, (indice // 8) * 10, 10, 10, color)
        pintor.end()
        if not imagen.save(str(ruta)):
            raise AssertionError("No se pudo guardar el atlas sintético de prueba")
        return ruta

    def test_catalogo_tiene_64_identidades_unicas_y_celdas_por_filas(self):
        self.assertEqual(len(CATALOGO_CIUDADANOS), 64)
        self.assertEqual(len({retrato.id for retrato in CATALOGO_CIUDADANOS}), 64)
        self.assertEqual(len({retrato.celda for retrato in CATALOGO_CIUDADANOS}), 64)
        self.assertTrue(set(arte.IDS_AVATARES).isdisjoint(retrato.id for retrato in CATALOGO_CIUDADANOS))
        self.assertEqual(CATALOGO_CIUDADANOS[8].celda, (0, 1))
        self.assertEqual(CATALOGO_CIUDADANOS[63].celda, (7, 7))

    def test_vecinos_actuales_tienen_retratos_reservados_distintos(self):
        grafo = crear_red_social()
        ampliar_comunidad(grafo, 6)
        vecinos = set(grafo.nodos) - set(arte.IDS_AVATARES)
        self.assertEqual(vecinos, {retrato.id for retrato in CATALOGO_CIUDADANOS[:10]})
        self.assertEqual({indice_retrato_ciudadano(id) for id in vecinos}, set(range(10)))

    def test_ids_futuros_repartidos_con_identidad_estable(self):
        id = "ciudadano_futuro_117"
        esperado = int.from_bytes(sha256(("civica:retrato:" + id).encode("utf-8")).digest()[:8], "big") % 64
        self.assertEqual(indice_retrato_ciudadano(id), esperado)
        self.assertEqual(indice_retrato_ciudadano("  " + id.upper() + "  "), esperado)
        # Ni el orden de dibujo ni el hash con sal de Python participan.
        antes = indice_retrato_ciudadano(id)
        for i in range(200):
            indice_retrato_ciudadano(f"otro_{i}")
        self.assertEqual(indice_retrato_ciudadano(id), antes)
        celdas = {indice_retrato_ciudadano(f"guardado_futuro_{i}") for i in range(256)}
        self.assertGreater(len(celdas), 58)

    def test_atlas_ampliado_recorta_todas_las_caras_y_cualquier_id_futuro(self):
        with tempfile.TemporaryDirectory() as temporal:
            raiz = Path(temporal)
            self.crear_atlas(raiz)
            with patch.object(arte, "RAIZ_EXPANSION", raiz):
                for retrato in CATALOGO_CIUDADANOS:
                    with self.subTest(id=retrato.id):
                        cara = arte.avatar_arte(retrato.id)
                        self.assertEqual((cara.width(), cara.height()), (10, 10))
                        self.assertEqual(cara.toImage().pixelColor(5, 5), QColor(retrato.indice * 3, 30, 255 - retrato.indice * 3))
                self.assertFalse(arte.avatar_arte("vecina_futura_de_partida_guardada").isNull())

    def test_atlas_real_tiene_64_fotos_distintas_y_conserva_19_vecinos_sin_repetir(self):
        self.assertTrue((arte.RAIZ_EXPANSION / RUTA_ATLAS_CIUDADANOS).is_file())
        huellas = []
        for retrato in CATALOGO_CIUDADANOS:
            cara = arte.avatar_arte(retrato.id)
            self.assertFalse(cara.isNull(), retrato.id)
            self.assertGreaterEqual(min(cara.width(), cara.height()), 128)
            imagen = cara.scaled(128, 128).toImage()
            huellas.append(sha256(imagen.constBits().asstring(imagen.sizeInBytes())).hexdigest())
        self.assertEqual(len(set(huellas)), 64)
        # También se comparan al mismo tamaño los nueve retratos anteriores.
        for id in arte.IDS_AVATARES:
            imagen = arte.avatar_arte(id).scaled(128, 128).toImage()
            huellas.append(sha256(imagen.constBits().asstring(imagen.sizeInBytes())).hexdigest())
        self.assertEqual(len(set(huellas)), 73)

    def test_reemplazar_atlas_invalida_carga_y_retratos(self):
        with tempfile.TemporaryDirectory() as temporal:
            raiz = Path(temporal)
            ruta = self.crear_atlas(raiz)
            with patch.object(arte, "RAIZ_EXPANSION", raiz):
                antes = arte.avatar_arte("lucia")
                self.assertEqual(antes.cacheKey(), arte.avatar_arte("lucia").cacheKey())
                tiempo = ruta.stat().st_mtime_ns
                self.crear_atlas(raiz, color_extra=80)
                os.utime(ruta, ns=(tiempo + 1_000_000, tiempo + 1_000_000))
                despues = arte.avatar_arte("lucia")
                self.assertNotEqual(antes.cacheKey(), despues.cacheKey())
                self.assertEqual(despues.toImage().pixelColor(5, 5), QColor(0, 110, 255))

    def test_sin_atlas_conserva_originales_y_respaldo_previo(self):
        with tempfile.TemporaryDirectory() as temporal:
            with patch.object(arte, "RAIZ_EXPANSION", Path(temporal)):
                for id in arte.IDS_AVATARES:
                    self.assertFalse(arte.avatar_arte(id).isNull())
                self.assertTrue(arte.avatar_arte("lucia").isNull())

    def test_ruta_atlas_no_depende_del_directorio_de_trabajo(self):
        raiz_esperada = Path(arte.__file__).resolve().parent / "assets" / "expansion"
        self.assertEqual(arte.RAIZ_EXPANSION, raiz_esperada)
        with tempfile.TemporaryDirectory() as temporal:
            raiz = Path(temporal)
            self.crear_atlas(raiz)
            anterior = Path.cwd()
            try:
                os.chdir(raiz)
                with patch.object(arte, "RAIZ_EXPANSION", raiz):
                    self.assertFalse(arte.avatar_arte("samuel").isNull())
            finally:
                os.chdir(anterior)


if __name__ == "__main__":
    unittest.main()
