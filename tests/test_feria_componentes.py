"""Contratos de interacción y privacidad del tablero de investigación."""
from copy import deepcopy
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QMovie, QPixmap
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QWidget

from interfaz.feria.componentes import TableroInvestigacion
from interfaz.feria.expediente import ComparadorPrueba, DialogoPrueba
from interfaz.feria.dialogos import DialogoAjustes, DialogoGaleria


def vista_ejemplo():
    return {
        "fase": "investigacion", "mi_id": "p1", "mi_rol": "ciudadano", "cooperativa": True,
        "jugadores": [{"id": "p1", "nombre": "Ada", "rol": "ciudadano"},
                      {"id": "p2", "nombre": "Sol", "rol": "periodista"}],
        "turno_id": "p1", "decididos": [], "confirmados": [], "acciones_restantes": 2,
        "caso": {
            "id": 50, "numero": 1, "total": 6, "titulo": "El mensaje incompleto", "npc_nombre": "Luis",
            "objetivo": "Busca lo que falta.", "publicacion": {"texto": "La frase que circula por la ciudad."},
            "medio": {"tipo": "captura", "texto_inicial": "Un fragmento", "texto_completo": "CONTEXTO PRIVADO",
                      "consigna": "Busca la fecha del documento.", "revelado": False},
            "preguntas": [{"id": "contexto", "texto": "¿Qué ocurrió antes?"}],
        },
        "lugares": [{"id": "archivo", "nombre": "Archivo público", "descripcion": "Consulta el acta.", "disponible": True},
                    {"id": "barrio", "nombre": "El barrio", "descripcion": "Escucha a una fuente.", "disponible": True}],
        "hallazgos": [], "hallazgos_disponibles": [], "solicitudes": [], "propuestas": [],
        "acciones": [{"clave": "compartir", "titulo": "Compartir", "descripcion": "Difunde tu versión."}],
        "certezas": ["pendiente", "probable", "confirmada"],
        "red": {"nodos": [{"id": "ana", "nombre": "Ana"}, {"id": "luis", "nombre": "Luis"},
                          {"id": "maria", "nombre": "María"}, {"id": "pedro", "nombre": "Pedro"}],
                "aristas": [["ana", "luis"], ["ana", "maria"], ["ana", "pedro"]],
                "vecinos": ["luis", "maria", "pedro"], "seleccionados": [], "alcance": {}},
        "relaciones": [], "estado": {}, "resultado": None,
    }


class PruebasTableroFeria(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tablero = TableroInvestigacion()
        self.vista = vista_ejemplo()
        self.comandos = []
        self.tablero.comando.connect(self.comandos.append)
        self.tablero.actualizar(self.vista)

    def tearDown(self):
        self.tablero.close()
        self.tablero.deleteLater()
        self.app.processEvents()

    def test_sincronizar_no_emite_comandos_ni_borra_borrador(self):
        self.tablero.titular.setText("Todavía falta una fuente")
        self.tablero.certeza.setCurrentIndex(1)
        self.tablero.tabs.setCurrentIndex(2)
        self.tablero.actualizar(dict(self.vista, revision=2))
        self.assertEqual(self.tablero.titular.text(), "Todavía falta una fuente")
        self.assertEqual(self.tablero.certeza.currentData(), "probable")
        self.assertEqual(self.tablero.tabs.currentIndex(), 2)
        self.assertEqual(self.comandos, [])

    def test_visita_y_examen_piden_al_motor_los_valores_reales(self):
        self.tablero.botones_lugares["archivo"].click()
        self.tablero.comparador.establecer_valor(82)
        self.tablero.examinar.click()
        self.assertEqual(self.comandos, [{"tipo": "investigar", "lugar": "archivo"},
                                        {"tipo": "examinar", "medio": "captura", "valor": 82}])

    def test_no_muestra_contexto_antes_de_recuperar_y_permite_entrevista_con_prueba(self):
        self.assertNotIn("CONTEXTO PRIVADO", self.tablero.medio_texto.text())
        self.assertNotIn("CONTEXTO PRIVADO", self.tablero.transcripcion.text())
        vista = deepcopy(self.vista)
        vista["caso"]["medio"]["revelado"] = True
        vista["hallazgos"] = [{"id": "50:documento", "titulo": "Acta original", "texto": "El contenido del acta.",
                               "origen": "archivo", "propietario": "p1", "compartido": False}]
        self.tablero.actualizar(vista)
        self.assertIn("CONTEXTO PRIVADO", self.tablero.medio_texto.text())
        self.tablero.prueba_entrevista.setCurrentIndex(1)
        self.tablero.entrevistar.click()
        self.assertEqual(self.comandos[-1], {"tipo": "entrevistar", "pregunta": "contexto", "evidencia": "50:documento"})

    def test_audiencia_limita_seleccion_y_la_envia_en_el_borrador(self):
        for id in ("luis", "maria", "pedro"):
            self.tablero.casillas_contactos[id].setChecked(True)
        self.assertEqual(self.tablero.contactos, ["luis", "maria"])
        self.assertFalse(self.tablero.casillas_contactos["pedro"].isChecked())
        self.tablero.prever.click()
        self.tablero.titular.setText("Hay que leer el documento completo")
        self.tablero.decidir.click()
        self.assertEqual(self.comandos[-2], {"tipo": "prever_alcance", "contactos": ["luis", "maria"]})
        self.assertEqual(self.comandos[-1]["contactos"], ["luis", "maria"])
        self.assertEqual(self.comandos[-1]["accion"], "compartir")

    def test_cambio_de_caso_limpia_contactos_y_borrador_sin_selecciones_fantasma(self):
        self.tablero.casillas_contactos["luis"].setChecked(True)
        self.tablero.titular.setText("Mi respuesta anterior")
        vista = deepcopy(self.vista)
        vista["caso"]["id"] = 90
        self.tablero.actualizar(vista)
        self.assertEqual(self.tablero.titular.text(), "")
        self.assertEqual(self.tablero.contactos, [])
        self.assertFalse(self.tablero.casillas_contactos["luis"].isChecked())

    def test_otro_turno_permite_proponer_y_resultado_espera_confirmacion(self):
        vista = dict(self.vista, turno_id="p2", fase="decision")
        self.tablero.actualizar(vista)
        self.assertFalse(self.tablero.decidir.isEnabled())
        self.assertTrue(self.tablero.proponer.isEnabled())
        self.tablero.actualizar(dict(vista, fase="resultado", confirmados=["p1"], resultado={"resumen": "Luis vuelve a hablar contigo."}))
        self.assertEqual(self.tablero.paginas.currentIndex(), 1)
        self.assertFalse(self.tablero.continuar.isEnabled())
        self.assertIn("Luis", self.tablero.resultado_resumen.text())

    def test_todas_las_pestanas_caben_en_ventana_minima(self):
        self.tablero.resize(1100, 700)
        self.tablero.show()
        self.app.processEvents()
        for indice in range(4):
            with self.subTest(pestana=indice):
                self.tablero.tabs.setCurrentIndex(indice)
                self.app.processEvents()
                area = self.tablero.tabs.currentWidget()
                self.assertLessEqual(area.widget().minimumSizeHint().width(), area.viewport().width())

    def test_audio_comun_explorable_sincroniza_seek_y_fragmento_sin_decidir_ni_mutar_borrador(self):
        vista = deepcopy(self.vista)
        vista["caso"]["medio"].update(
            tipo="audio", inspeccionable=True,
            fragmentos=[{"inicio": 0, "fin": 33, "texto": "Si alguien pretende"},
                        {"inicio": 33, "fin": 65, "texto": "cobrar por votar"},
                        {"inicio": 65, "fin": 100, "texto": "denuncia ese engaño"}],
        )
        original = deepcopy(vista)
        self.tablero.actualizar(vista)
        self.tablero.titular.setText("Un borrador todavía abierto")
        with patch.object(self.tablero.audio, "duration", return_value=10000), \
             patch.object(self.tablero.audio, "setPosition") as seek:
            self.tablero.slider_medio.setValue(70)
            seek.assert_called_with(7000)
            self.assertEqual(self.tablero.transcripcion.text(), "denuncia ese engaño")
            self.tablero._posicion_audio(3500)
            self.assertEqual(self.tablero.transcripcion.text(), "cobrar por votar")
            self.assertEqual(self.tablero.slider_medio.value(), 70)
        self.assertEqual(self.tablero.titular.text(), "Un borrador todavía abierto")
        self.assertEqual(vista, original)
        self.assertEqual(self.comandos, [])
        vista["caso"]["medio"]["inspeccionable"] = False
        self.tablero.actualizar(vista)
        self.assertEqual(self.tablero.transcripcion.text(), "Un fragmento")

    def test_entrada_del_caso_muestra_mapa_desde_arriba_y_preserva_scroll_en_sincronizaciones(self):
        self.tablero.resize(1100, 700)
        self.tablero.show()
        self.app.processEvents()
        barra = self.tablero.tabs.widget(0).verticalScrollBar()
        self.assertEqual(barra.value(), barra.minimum())
        for indice in (1, 2, 3, 0):
            self.tablero.tabs.setCurrentIndex(indice)
            self.app.processEvents()
        self.assertEqual(barra.value(), barra.minimum())
        barra.setValue(min(160, barra.maximum()))
        valor = barra.value()
        self.assertGreater(valor, 0)
        self.tablero.tabs.setCurrentIndex(1)
        self.app.processEvents()
        self.tablero.tabs.setCurrentIndex(0)
        self.app.processEvents()
        self.assertEqual(barra.value(), valor)
        self.tablero.actualizar(dict(self.vista, revision=3))
        self.app.processEvents()
        self.assertEqual(barra.value(), valor)
        siguiente = deepcopy(self.vista)
        siguiente["caso"]["id"] = 90
        self.tablero.actualizar(siguiente)
        self.app.processEvents()
        self.assertEqual(barra.value(), barra.minimum())

    def test_ampliacion_sincroniza_divisor_y_confirma_por_el_mismo_comando(self):
        def interactuar():
            dialogo = self.tablero.dialogo_prueba
            dialogo.slider.setValue(85)
            dialogo.confirmar.click()
            dialogo.accept()
        QTimer.singleShot(0, interactuar)
        self.tablero.abrir_prueba()
        self.assertEqual(self.tablero.slider_medio.value(), 85)
        self.assertEqual(self.comandos, [{"tipo": "examinar", "medio": "captura", "valor": 85}])
        self.assertIsNone(self.tablero.dialogo_prueba)


class PruebasComparadorPrivacidad(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_original_no_se_carga_antes_de_recuperarlo_y_flechas_mueven_el_instrumento(self):
        comparador = ComparadorPrueba()
        imagen = QPixmap(16, 16)
        imagen.fill(Qt.GlobalColor.white)
        with patch.object(comparador, "_imagen", return_value=imagen) as cargar:
            comparador.actualizar("recorte.png", "original.png", recuperado=False)
            cargar.assert_called_once_with("recorte.png")
            self.assertTrue(comparador.original.isNull())
            comparador.actualizar("recorte.png", "original.png", recuperado=True)
            self.assertEqual(cargar.call_args.args, ("original.png",))
            self.assertFalse(comparador.original.isNull())
        QTest.keyClick(comparador, Qt.Key.Key_Right)
        self.assertEqual(comparador.valor, 5)
        QTest.keyClick(comparador, Qt.Key.Key_End)
        self.assertEqual(comparador.valor, 100)
        comparador.close()
        comparador.deleteLater()

    def test_permiso_explicito_explora_original_comun_sin_recuperar_evidencia(self):
        comparador = ComparadorPrueba()
        imagen = QPixmap(16, 16)
        imagen.fill(Qt.GlobalColor.white)
        with patch.object(comparador, "_imagen", return_value=imagen) as cargar:
            comparador.actualizar("recorte.png", "original.png", recuperado=False, inspeccionable=True)
            self.assertEqual(cargar.call_count, 2)
            self.assertFalse(comparador.original.isNull())
            self.assertFalse(comparador.recuperado)
            comparador.establecer_valor(80)
            self.assertEqual(comparador.valor, 80)
            self.assertFalse(comparador.recuperado)
            comparador.actualizar("recorte.png", "original.png", recuperado=False)
            self.assertTrue(comparador.original.isNull())
        comparador.close()
        comparador.deleteLater()

    def test_visor_ampliado_lee_tamano_real_y_conserva_privacidad(self):
        imagen = QPixmap(1400, 900)
        imagen.fill(Qt.GlobalColor.white)
        medio = {"imagen_recortada": "recorte.png", "imagen_completa": "original.png",
                 "inspeccionable": True, "revelado": False}
        with patch.object(ComparadorPrueba, "_imagen", return_value=imagen):
            dialogo = DialogoPrueba(medio, valor=65, puede_examinar=True)
            dialogo.zoom.setCurrentIndex(dialogo.zoom.findData(1))
            self.assertEqual((dialogo.comparador.width(), dialogo.comparador.height()), (1400, 900))
            self.assertFalse(dialogo.comparador.original.isNull())
            self.assertFalse(dialogo.comparador.recuperado)
            solicitudes = []
            dialogo.examinar_solicitado.connect(solicitudes.append)
            dialogo.confirmar.click()
            self.assertEqual(solicitudes, [65])
            dialogo.actualizar(dict(medio, inspeccionable=False), puede_examinar=True)
            self.assertTrue(dialogo.comparador.original.isNull())
            dialogo.close()
            dialogo.deleteLater()


class PruebasDialogosFeria(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_ajustes_personales_no_ofrecen_desactivar_el_plazo_cooperativo(self):
        parent = QWidget()
        parent.cliente_red = object()
        dialogo = DialogoAjustes({"sonido": False, "volumen": 25, "sin_limite": False}, parent)
        self.assertFalse(dialogo.sin_limite.isEnabled())
        self.assertTrue(dialogo.sonido.isEnabled())
        self.assertTrue(dialogo.tamano_texto.isEnabled())
        dialogo.close()
        dialogo.deleteLater()
        parent.close()
        parent.deleteLater()

    def test_gif_es_qmovie_real_respeta_movimiento_reducido_y_sonido(self):
        parent = QWidget()
        parent.preferencias = {"sonido": False, "volumen": 28, "reducir_movimiento": True}
        dialogo = DialogoGaleria(parent)
        galeria = dialogo.galeria
        fila = next((i for i, recurso in enumerate(galeria.recursos) if recurso[2] == "gif"), None)
        if fila is None:
            dialogo.close()
            dialogo.deleteLater()
            parent.deleteLater()
            self.skipTest("El paquete opcional de galería no incluye GIF")
        galeria.lista.setCurrentRow(fila)
        self.assertIsInstance(galeria.movie, QMovie)
        self.assertTrue(galeria.movie.isValid())
        self.assertNotEqual(galeria.movie.state(), QMovie.MovieState.Running)
        self.assertTrue(galeria.audio.isMuted())
        self.assertAlmostEqual(galeria.audio.volume(), .28)
        galeria.reproducir.click()
        self.assertEqual(galeria.movie.state(), QMovie.MovieState.Running)
        galeria.reproducir.click()
        self.assertEqual(galeria.movie.state(), QMovie.MovieState.Paused)
        galeria.detener()
        self.assertEqual(galeria.movie.state(), QMovie.MovieState.NotRunning)
        dialogo.close()
        dialogo.deleteLater()
        parent.close()
        parent.deleteLater()
