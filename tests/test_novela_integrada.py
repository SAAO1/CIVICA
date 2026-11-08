"""Regresión del recorrido de la novela original con investigación y seis actos."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication
from juego.casos_feria import IDS_FERIA
from interfaz.ventana import VentanaPrincipal
from interfaz.escenas.cinematica import EscenaCinematica, EscenaDialogo
from interfaz.novela.ventana import VentanaNovela


class NovelaIntegrada(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        self.guardado=patch.object(VentanaNovela,"_autoguardar")
        self.guardado.start()
        self.ventana=VentanaNovela(semilla=4,eventos=False)
        self.ventana.sin_limite=True
        self.ventana.reducir_movimiento=True
        self.ventana.audio.silenciar()
        self.ventana.resize(1366,768)
        self.ventana.show()
        self.app.processEvents()

    def tearDown(self):
        self.ventana.close()
        self.app.processEvents()
        self.guardado.stop()

    def test_mantiene_escenas_actores_y_motor_neural_original(self):
        self.assertIsInstance(self.ventana,VentanaPrincipal)
        self.assertIsInstance(self.ventana.escena_dialogo,EscenaDialogo)
        self.assertIsInstance(self.ventana.escena_resultado_1,EscenaCinematica)
        self.assertEqual(self.ventana.audio.motor_voz,"neural-offline")
        self.assertIsNone(self.ventana.audio._sintetizador)

    def test_ambos_roles_completan_seis_actos_en_solitario(self):
        for rol,accion in (("ciudadano","ignorar"),("periodista","reservar")):
            self.ventana.iniciar_solo(rol)
            vistos=[]
            for numero in range(1,7):
                v=self.ventana
                vistos.append(v.vista_novela["caso"]["id"])
                self.assertEqual(v.vista_novela["caso"]["numero"],numero)
                v.mostrar_escena(v.ESCENA_DIALOGO)
                self.assertGreater(len(v.escena_dialogo.dialogos),0)
                v.mostrar_escena(v.ESCENA_ACCION)
                self.assertIn("VI",v.escena_accion.capitulo.text())
                self.assertTrue(v.enviar_comando_novela({"tipo":"investigar","lugar":"redaccion"}))
                self.assertEqual(v.vista_novela["acciones_restantes"],1)
                self.assertTrue(v.enviar_comando_novela({"tipo":"decidir","accion":accion,
                                                       "certeza":"pendiente"}))
                self.assertEqual(v.escenas.currentIndex(),v.ESCENA_RESULTADO_1)
                self.assertEqual(len(v.sesion.decisiones),1)
                v.mostrar_escena(v.ESCENA_ARBOL)
                self.assertEqual(v.escenas.currentIndex(),v.ESCENA_ARBOL)
                self.assertEqual(v.vista_novela["caso"]["numero"],numero)
                v.escena_arbol.boton_inorden.click()
                self.assertIn("INORDEN",v.escena_arbol.resultado.text())
                v.escena_arbol.boton_continuar.click()
                self.assertEqual(v.escenas.currentIndex(),v.ESCENA_GRAFO)
                self.assertEqual(v.vista_novela["caso"]["numero"],numero)
                v.escena_red.boton_continuar.click()
                self.app.processEvents()
            self.assertEqual(vistos,list(IDS_FERIA))
            self.assertEqual(self.ventana.sesion.fase,"final")
            self.assertEqual(len(self.ventana.juego.historial),6)

    def test_editor_abre_sobre_la_escena_y_conserva_hallazgos(self):
        v=self.ventana
        v.iniciar_solo("ciudadano")
        v.mostrar_escena(v.ESCENA_ACCION)
        v.enviar_accion("compartir")
        self.assertIsNotNone(v.overlay_investigacion)
        self.assertEqual(v.escenas.currentIndex(),v.ESCENA_ACCION)
        self.assertTrue(v.enviar_comando_novela({"tipo":"investigar","lugar":"redaccion"}))
        self.assertEqual(len(v.vista_novela["hallazgos"]),1)
        v._cerrar_overlay()
        self.assertIsNone(v.overlay_investigacion)
        self.assertEqual(v.vista_novela["acciones_restantes"],1)

    def test_guardado_restaura_evidencia_presupuesto_y_decisiones(self):
        v=self.ventana
        v.iniciar_solo("periodista")
        v.enviar_comando_novela({"tipo":"investigar","lugar":"archivo"})
        esperado=v.sesion.datos()
        with tempfile.TemporaryDirectory() as carpeta:
            ruta=Path(carpeta)/"novela.json"
            v._escribir_guardado(ruta)
            v.iniciar_solo("ciudadano")
            v.cargar_desde_ruta(ruta)
        self.assertEqual(v.sesion.datos(),esperado)
        self.assertEqual(v.vista_novela["mi_rol"],"periodista")
        self.assertEqual(v.vista_novela["acciones_restantes"],1)

    def test_guardado_en_grafo_retoma_revision_sin_repetir_resultado(self):
        v=self.ventana
        v.iniciar_solo("ciudadano")
        v.enviar_comando_novela({"tipo":"decidir","accion":"ignorar"})
        v.continuar_caso()
        self.assertEqual(v.vista_novela["caso"]["id"],50)
        v.mostrar_escena(v.ESCENA_GRAFO)
        self.assertIs(v.escenas.currentWidget(),v.escena_arbol)
        v.escena_arbol.boton_continuar.click()
        self.assertIs(v.escenas.currentWidget(),v.escena_red)
        with tempfile.TemporaryDirectory() as carpeta:
            ruta=Path(carpeta)/"revision.json"
            v._escribir_guardado(ruta)
            v.iniciar_solo("periodista")
            v.cargar_desde_ruta(ruta)
        self.assertIs(v.escenas.currentWidget(),v.escena_red)
        self.assertEqual(v._visores_vistos,{"arbol","grafo"})
        self.assertEqual(v.vista_novela["caso"]["id"],50)
        self.assertEqual(len(v.juego.historial),1)
        v.escena_red.boton_continuar.click()
        self.assertEqual(v.vista_novela["caso"]["id"],90)
        self.assertEqual(len(v.juego.historial),1)

    def test_consulta_estructuras_no_avanza_el_acto(self):
        v=self.ventana
        v.iniciar_solo("ciudadano")
        indice=v.juego.indice_proxima_publicacion
        archivo=[p.id for p in v.juego.arbol.inorden()]
        v.abrir_observatorio("archivo")
        self.app.processEvents()
        v._observatorio_novela.accept()
        self.assertEqual(v.juego.indice_proxima_publicacion,indice)
        self.assertEqual([p.id for p in v.juego.arbol.inorden()],archivo)


    def test_guardados_antiguos_retoman_inicio_o_resultado_sin_bloqueo(self):
        from juego.partida import Juego
        v=self.ventana
        with tempfile.TemporaryDirectory() as carpeta:
            ruta=Path(carpeta)/"legado.json"
            legado=Juego(4,eventos=False,campana="extendida")
            legado.guardar(ruta)
            v.cargar_desde_ruta(ruta)
            self.assertEqual(v.escenas.currentIndex(),v.ESCENA_INICIO)
            legado.iniciar_primera_publicacion()
            legado.ejecutar_accion("ignorar")
            legado.guardar(ruta)
            v.cargar_desde_ruta(ruta)
            self.assertEqual(v.escenas.currentIndex(),v.ESCENA_GRAFO)
            self.assertIsNone(v.sesion)
            v.continuar_desde_arbol()
            self.assertEqual(v.escenas.currentIndex(),v.ESCENA_DIALOGO)
            self.assertFalse(v.juego.decision_aplicada)



    def test_retirar_del_arbol_durante_lectura_conserva_el_acto(self):
        from types import SimpleNamespace
        from juego.partida import Juego
        v=self.ventana
        v.iniciar_solo("periodista")
        v.sesion=None
        v.cliente_red=SimpleNamespace(cerrar=lambda:None,enviar=lambda _:True)
        v.mostrar_escena(v.ESCENA_DIALOGO)
        identidad=v.juego
        overlay=v._abrir_overlay("fuentes")
        self.assertTrue(v.escena_dialogo.lectura_pausada)
        copia=Juego.desde_datos(v.juego.datos())
        copia.ejecutar_accion("desmentir")
        self.assertIsNone(copia.publicacion_actual_id)
        v.establecer_juego(copia)
        self.assertIs(v.juego,identidad)
        overlay.cerrar()
        self.assertFalse(v.escena_dialogo.lectura_pausada)



    def test_sin_limite_detiene_alerta_y_un_tick_pendiente_no_decide(self):
        v=self.ventana
        v._eventos_novela=True
        v.sin_limite=False
        v.iniciar_solo("ciudadano")
        self.assertTrue(v.juego.evento_actual.urgente)
        v.mostrar_escena(v.ESCENA_ACCION)
        self.assertTrue(v.temporizador_novela.isActive())
        v._plazo_local=1
        antes=v.sesion.datos()
        v.sin_limite=True
        v.aplicar_accesibilidad()
        self.assertFalse(v.temporizador_novela.isActive())
        # Un timeout ya encolado tampoco puede decidir tras cambiar el ajuste.
        v._paso_plazo()
        self.assertEqual(v.sesion.datos(),antes)
        self.assertEqual(v._plazo_local,1)
        self.assertEqual(v.escenas.currentIndex(),v.ESCENA_ACCION)


if __name__=="__main__":
    unittest.main()
