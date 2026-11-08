"""Recorrido por controles reales y mezcla de los cuatro efectos breves."""
import array
import os
import unittest
import wave
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_LOGGING_RULES", "qt.multimedia.*=false")

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QDialog, QLineEdit, QVBoxLayout, QAbstractButton

from infraestructura.recursos import RAIZ
from interfaz.novela.ventana import VentanaNovela


class EngancheSonidosNovela(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.guardado = patch.object(VentanaNovela, "_autoguardar")
        self.guardado.start()
        self.v = VentanaNovela(4, eventos=False)
        self.v.sin_limite = True
        self.v.reducir_movimiento = True
        self.v.audio.silenciar()
        self.v.show()
        self.app.processEvents()

    def tearDown(self):
        self.v.close()
        self.app.processEvents()
        self.guardado.stop()

    def pulsar(self, boton):
        self.app.processEvents()
        self.assertTrue(boton.isVisible(), boton.text())
        self.assertTrue(boton.visibleRegion().contains(boton.rect().center()), boton.text())
        QTest.mouseClick(boton, Qt.MouseButton.LeftButton)
        self.app.processEvents()

    def captura(self, nombre):
        salida = RAIZ / ".tmp/novela/recorrido_usuario"
        salida.mkdir(parents=True, exist_ok=True)
        self.v.grab().save(str(salida / (nombre + ".png")))

    def test_cuatro_efectos_realmente_resueltos_con_mezcla_silencio_y_sin_clipping(self):
        audio = self.v.audio
        claves = ("hallazgo", "paso", "red", "transicion")
        self.assertTrue(all("pulido_"+c in audio.efectos for c in claves))
        for clave in claves:
            nombre = "pulido_" + clave
            ruta = RAIZ / "assets/novela/pulido/audio" / (clave + ".wav")
            self.assertEqual(Path(audio.efectos[nombre].source().toLocalFile()), ruta)
            with wave.open(str(ruta), "rb") as archivo:
                self.assertEqual(archivo.getsampwidth(), 2)
                self.assertLessEqual(archivo.getnframes()/archivo.getframerate(), .51)
                valores = array.array("h", archivo.readframes(archivo.getnframes()))
                self.assertGreater(max(map(abs, valores)), 0)
                self.assertLess(max(map(abs, valores)), 32767)
            with patch.object(QSoundEffect, "play") as play:
                self.assertTrue(audio.reproducir_efecto(nombre))
                play.assert_called_once()
                self.assertEqual(audio.efectos[nombre].volume(), 0)
        audio.silenciar(False)
        audio.configurar("general", .5)
        audio.configurar("efectos", .6)
        self.assertAlmostEqual(audio.efectos["pulido_hallazgo"].volume(), .3, places=6)
        audio._cambiar_estado_hablando(True)
        self.assertAlmostEqual(audio.efectos["pulido_hallazgo"].volume(), .3*.28, places=6)
        audio.silenciar()
        self.assertTrue(all(e.volume() == 0 for e in audio.efectos.values()))

    def test_hallazgo_confirmado_usa_efecto_nuevo_una_vez(self):
        self.v.iniciar_solo("ciudadano")
        with patch.object(self.v.audio, "reproducir_efecto", wraps=self.v.audio.reproducir_efecto) as play:
            self.assertTrue(self.v.enviar_comando_novela({"tipo":"investigar", "lugar":"redaccion"}))
            llamadas = [c.args[0] for c in play.call_args_list]
            self.assertEqual(llamadas.count("pulido_hallazgo"), 1)
            self.assertNotIn("hallazgo", llamadas)


    def test_inicio_sin_invitaciones_flotantes_y_lectura_sin_gastar_investigaciones(self):
        v=self.v
        v.iniciar_solo("ciudadano")
        v.mostrar_escena(v.ESCENA_NARRACION_2)
        self.app.processEvents()
        self.assertFalse(hasattr(v,"enganche_inicial"))
        antes=deepcopy(v.sesion.datos())
        for escena in (v.escena_narracion_2,v.escena_narracion_3):
            textos=[b.text() for b in escena.findChildren(QAbstractButton)]
            self.assertFalse(any("Abrir el mensaje" in t or "Examinar esta prueba" in t for t in textos))
        v.escena_narracion_2.timer_inicio.stop()
        v.escena_narracion_2.iniciar_dialogo(v.escena_narracion_2.texto_inicial,"NARRADOR")
        v.escena_narracion_2.animacion.setCurrentTime(v.escena_narracion_2.animacion.duration())
        v.escena_narracion_2.revelar_texto()
        QTest.keyClick(v.escena_narracion_2,Qt.Key.Key_Return)
        self.app.processEvents()
        self.assertEqual(v.escenas.currentIndex(),v.ESCENA_NARRACION_3)
        self.assertEqual(v.sesion.datos(),antes)

    def test_barra_inferior_oculta_en_escenas_y_valores_reales_conservados(self):
        v=self.v
        v.iniciar_solo("ciudadano")
        for indice in (v.ESCENA_NARRACION_1,v.ESCENA_NARRACION_2,v.ESCENA_DIALOGO,v.ESCENA_ACCION):
            v.mostrar_escena(indice)
            self.app.processEvents()
            self.assertFalse(v.hud.isVisible())
            self.assertFalse(v.indicadores.isVisible())
        self.assertTrue(v.enviar_comando_novela({"tipo":"decidir","accion":"conversar"}))
        for indice in (v.ESCENA_RESULTADO_1,v.ESCENA_RESULTADO_2,v.ESCENA_RESULTADO_3,v.ESCENA_ARBOL,v.ESCENA_GRAFO):
            v.mostrar_escena(indice)
            self.app.processEvents()
            self.assertFalse(v.hud.isVisible())
            self.assertFalse(v.indicadores.isVisible())
        self.assertTrue(v.juego.ultimo_registro["cambios_reales"])
        self.assertTrue(v.juego.arbol.inorden())

    def test_buscar_leer_responder_y_confirmar_sin_formulario_en_dos_tamanos(self):
        for ancho,alto in ((1100,700),(1360,720)):
            with self.subTest(tamano=(ancho,alto)):
                v=self.v
                v.resize(ancho,alto)
                v.iniciar_solo("ciudadano")
                v.mostrar_escena(v.ESCENA_ACCION)
                self.pulsar(v.escena_accion.boton_investigar)
                libro=v.overlay_investigacion
                self.pulsar(libro.mapa.botones["redaccion"])
                self.assertEqual(v.vista_novela["acciones_restantes"],1)
                self.assertEqual(libro.paginas.currentIndex(),libro.secciones["pista"])
                self.pulsar(libro.siguiente_paso)
                self.assertEqual(libro._prueba["id"],"50:contexto")
                for nombre in ("opciones","avanzadas","titular","certeza","evidencia","contactos"):
                    self.assertFalse(hasattr(libro,nombre),nombre)
                self.assertEqual(set(libro.botones_accion),{"conversar","compartir","ignorar"})
                self.pulsar(libro.botones_accion["conversar"])
                self.pulsar(libro.siguiente_paso)
                self.assertEqual(libro.paginas.currentIndex(),libro.secciones["confirmacion"])
                self.assertTrue(libro.confirmar.isEnabled())
                self.pulsar(libro.confirmar)
                self.assertEqual(v.sesion.fase,"resultado")
                self.assertEqual(v.vista_novela["acciones_restantes"],1)
                self.assertEqual(v.escenas.currentIndex(),v.ESCENA_RESULTADO_1)

    def test_pausa_impide_confirmacion_y_no_modifica_sesion(self):
        v=self.v
        v.iniciar_solo("ciudadano")
        v.mostrar_escena(v.ESCENA_ACCION)
        libro=v._abrir_overlay("decision")
        libro.decision("ignorar")
        libro._ir_confirmacion()
        vista=deepcopy(v.vista_novela)
        vista["fase"]="pausa"
        libro.actualiza(vista)
        self.assertFalse(libro.confirmar.isEnabled())
        self.assertFalse(libro.siguiente_paso.isEnabled())
        antes=deepcopy(v.sesion.datos())
        libro._confirmar()
        self.assertEqual(v.sesion.datos(),antes)

    def test_letras_m_p_son_texto_normal_en_dialogo_y_no_activan_invitaciones(self):
        v=self.v
        v.iniciar_solo("ciudadano")
        v.mostrar_escena(v.ESCENA_NARRACION_2)
        antes=deepcopy(v.sesion.datos())
        dialogo=QDialog(v)
        dialogo.setModal(True)
        editor=QLineEdit()
        QVBoxLayout(dialogo).addWidget(editor)
        dialogo.show()
        editor.setFocus()
        self.app.processEvents()
        QTest.keyClicks(editor,"mi mapa pendiente")
        self.assertEqual(editor.text(),"mi mapa pendiente")
        self.assertEqual(v.escenas.currentIndex(),v.ESCENA_NARRACION_2)
        self.assertEqual(v.sesion.datos(),antes)
        self.assertFalse(hasattr(v,"enganche_inicial"))
        dialogo.close()


if __name__ == "__main__":
    unittest.main()
