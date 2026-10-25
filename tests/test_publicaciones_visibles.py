"""Los medios de los catorce casos se ven en la acción y en el teléfono."""
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtGui import QColor, QImage, QPixmap
from PyQt6.QtWidgets import QApplication

import arte
from juego.acciones import acciones_para_rol
from juego.partida import Juego
from models.publicacion import Publicacion
from publicaciones_ui import TarjetaPublicacion


def huella(pixmap):
    imagen = pixmap.toImage()
    return hashlib.sha256(imagen.constBits().asstring(imagen.sizeInBytes())).hexdigest()


def colores(imagen, caja=None):
    caja = caja or imagen.rect()
    return {imagen.pixelColor(x, y).rgb() for y in range(int(caja.top()), int(caja.bottom()), 13)
            for x in range(int(caja.left()), int(caja.right()), 13)}


class PruebasPublicacionesVisibles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_los_catorce_casos_tienen_medios_reales_y_distintos(self):
        juego = Juego(7, eventos=False, campana="extendida")
        self.assertEqual(len(juego.publicaciones_planificadas), 14)
        firmas = []
        for publicacion in juego.publicaciones_planificadas:
            with self.subTest(id=publicacion.id):
                miniatura = arte.miniatura_publicacion(publicacion)
                self.assertFalse(miniatura.isNull())
                self.assertGreater(len(colores(miniatura.toImage())), 80)
                self.assertGreater(miniatura.width(), miniatura.height())
                firmas.append(huella(miniatura))
        self.assertEqual(len(set(firmas)), 14)

    def test_feed_y_telefono_cambian_de_publicacion_sin_bloques_vacios(self):
        nuevas = Juego(eventos=False, campana="extendida").publicaciones_planificadas[6:]
        for telefono, ancho, alto in ((False, 1035, 650), (False, 700, 490), (True, 260, 470), (True, 220, 430)):
            tarjeta = TarjetaPublicacion(telefono=telefono)
            tarjeta.resize(ancho, alto)
            self.addCleanup(tarjeta.deleteLater)
            firmas = []
            for publicacion in nuevas:
                tarjeta.mostrar(publicacion)
                imagen = tarjeta.grab().toImage()
                with self.subTest(id=publicacion.id, telefono=telefono, tamano=(ancho, alto)):
                    self.assertGreater(tarjeta.area_medio.height(), 40)
                    self.assertLessEqual(tarjeta.area_medio.bottom(), alto)
                    self.assertGreater(len(colores(imagen, tarjeta.area_medio)), 30)
                    firmas.append(huella(QPixmap.fromImage(imagen)))
            self.assertEqual(len(set(firmas)), 8)
            tarjeta.mostrar(None)
            tarjeta.grab()
            self.assertEqual(tarjeta.autor, "Ciudad Nova")

    def test_partida_importada_elige_respaldo_segun_el_contenido(self):
        parque = Publicacion(987, "El parque de nuestro barrio", None, 1)
        colegio = Publicacion(987, "El colegio reabre sus clases", None, 1)
        self.assertFalse(arte.miniatura_publicacion(parque).isNull())
        self.assertNotEqual(huella(arte.miniatura_publicacion(parque)),
                            huella(arte.miniatura_publicacion(colegio)))
        self.assertFalse(arte.miniatura_publicacion([]).isNull())

    def test_reemplazo_de_recurso_se_recarga_sin_reiniciar_ni_cache_de_nombre(self):
        with tempfile.TemporaryDirectory() as temporal, patch.object(arte, "RAIZ_EXPANSION", Path(temporal)):
            directorio = Path(temporal) / "siete_actos/publicaciones"
            directorio.mkdir(parents=True)
            ruta = directorio / "90.png"
            primera = arte.miniatura_publicacion(90)
            for color in ("red", "green"):
                foto = QImage(480, 270, QImage.Format.Format_RGB32)
                foto.fill(QColor(color))
                self.assertTrue(foto.save(str(ruta)))
                cargada = arte.miniatura_publicacion(90)
                self.assertEqual(cargada.toImage().pixelColor(180, 120), QColor(color))
                self.assertNotEqual(huella(primera), huella(cargada))
                primera = cargada

    def test_la_carga_no_depende_del_directorio_desde_el_que_se_abre_el_juego(self):
        antes = os.getcwd()
        with tempfile.TemporaryDirectory() as temporal:
            try:
                os.chdir(temporal)
                self.assertFalse(arte.miniatura_publicacion(90).isNull())
                self.assertFalse(arte.miniatura_publicacion(50).isNull())
            finally:
                os.chdir(antes)

    def test_convocar_y_escuchar_identifican_al_barrio_sin_cambiar_sus_claves(self):
        acciones = {a["clave"]: a for a in acciones_para_rol("ciudadano")}
        self.assertEqual(acciones["conversar"]["titulo_corto"], "Escuchar al barrio")
        self.assertEqual(acciones["convocar"]["titulo_corto"], "Convocar al barrio")
        for clave in ("conversar", "convocar"):
            juego = Juego(5, eventos=False)
            juego.seleccionar_rol("ciudadano")
            juego.iniciar_primera_publicacion()
            self.assertTrue(juego.ejecutar_accion(clave))
            self.assertEqual(juego.ultimo_registro["accion_rol"], clave)
