"""Los nuevos casos llegan a la presentación completa, con cinco actores NPC."""
import os
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication
from interfaz import VentanaPrincipal, NOMBRES_PERSONAJES
from juego.acciones import accion_por_defecto
from juego.campana_extendida import CASOS_NUEVOS, epilogo_extendido
from juego.historia import dialogos_publicacion, contenido_resultado
from juego.lectura import BibliotecaLectura
from juego.partida import Juego
from juego.puesta_escena import escenario_actual
from juego.finales import epilogo
from test_balance_roles_ui import AudioConSenales, crear_ventana


class InterfazSieteActosTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.parches = [patch("configuracion.cargar", return_value={}),
                         patch("interfaz.GestorAudio", AudioConSenales),
                         patch("interfaz.BibliotecaLectura", lambda: BibliotecaLectura(None)),
                         patch("cinematica_narrativa.CapaCinematica._reproducir_si_corresponde")]
        for parche in self.parches:
            parche.start()
        self.ventana = crear_ventana()

    def tearDown(self):
        self.ventana.close()
        self.ventana.deleteLater()
        self.app.processEvents()
        for parche in reversed(self.parches):
            parche.stop()

    def test_ui_comienza_extendida_y_el_sexto_caso_no_termina(self):
        juego = self.ventana.juego
        self.assertEqual(juego.campana, "extendida")
        juego.iniciar_primera_publicacion()
        for _ in range(5):
            juego.ejecutar_accion(accion_por_defecto(juego.jugador.rol))
            juego.avanzar_publicacion()
        self.assertEqual(juego.publicacion_actual_id, 80)
        self.assertNotIn("última decisión", " ".join(t for _, t in dialogos_publicacion(juego)))
        juego.ejecutar_accion(accion_por_defecto(juego.jugador.rol))
        self.ventana.mostrar_escena(self.ventana.ESCENA_GRAFO)
        self.ventana.continuar_desde_arbol()
        self.assertEqual(juego.publicacion_actual_id, 90)
        self.assertEqual(self.ventana.escenas.currentIndex(), self.ventana.ESCENA_DIALOGO)

    def test_galeria_nueva_conserva_desbloqueos_al_reabrir_biblioteca(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "biblioteca.json"
            biblioteca = BibliotecaLectura(ruta)
            for identificador in CASOS_NUEVOS:
                biblioteca.desbloquear(identificador)
            self.assertEqual(BibliotecaLectura(ruta).escenas, {str(i) for i in CASOS_NUEVOS})

    def test_ocho_casos_muestran_guion_fondo_reaccion_y_video_correctos(self):
        juego = Juego(7, eventos=False, campana="extendida")
        juego.seleccionar_rol("periodista")
        juego.iniciar_primera_publicacion()
        self.ventana.establecer_juego(juego)
        vistos = set()
        while juego.publicacion_actual_id is not None:
            identificador = juego.publicacion_actual_id
            if identificador in CASOS_NUEVOS:
                self.ventana.mostrar_escena(self.ventana.ESCENA_DIALOGO)
                escena = self.ventana.escena_dialogo
                escena.timer_inicio.stop()
                self.assertEqual(escena.dialogos, dialogos_publicacion(juego))
                self.assertIn("siete_actos", escena.fondo)
                self.assertEqual(escena.fondo, escenario_actual(juego)["fondo"])
                self.assertIn(str(identificador), escena.cine_narrativo.clave_actual)
                for nombre, texto in escena.dialogos:
                    if nombre in NOMBRES_PERSONAJES:
                        escena.texto_completo = texto
                        escena.configurar_personajes_para_hablante(nombre, escena.presentes_dialogo)
                        self.assertIn(nombre, escena.personajes_activos)
                        self.assertLessEqual(len(escena.personajes_activos), 3)
                        self.assertEqual(escena.personajes[nombre].imagen.rol, nombre.lower())
                        vistos.add(nombre)
            juego.ejecutar_accion("contrastar")
            if identificador in CASOS_NUEVOS:
                self.ventana.mostrar_escena(self.ventana.ESCENA_RESULTADO_1)
                resultado = self.ventana.escena_resultado_1
                resultado.timer_inicio.stop()
                self.assertEqual((resultado.texto_inicial, resultado.nombre_inicial), contenido_resultado(juego, 1))
                self.assertEqual(resultado.cine_narrativo.clave_actual, f"accion_{identificador}_contrastar")
            if not juego.avanzar_publicacion():
                break
        self.assertEqual(vistos, set(NOMBRES_PERSONAJES))

    def test_epilogo_hablado_coincide_con_panel_y_lleva_investidura_real(self):
        juego = Juego(3, eventos=False, campana="extendida")
        juego.iniciar_primera_publicacion()
        for _ in range(14):
            juego.ejecutar_accion(accion_por_defecto(juego.jugador.rol))
            juego.avanzar_publicacion()
        self.ventana.establecer_juego(juego)
        self.ventana.mostrar_desenlace()
        self.assertEqual(self.ventana.escenas.currentIndex(), self.ventana.ESCENA_EPILOGO)
        escena = self.ventana.escena_epilogo
        escena.timer_inicio.stop()
        self.assertEqual(escena.dialogos, epilogo_extendido(juego))
        self.assertEqual("\n\n".join(t for _, t in escena.dialogos), epilogo(juego, juego.resultado_electoral()))
        self.assertTrue(escena.cine_narrativo.clave_actual.startswith("epilogo_"))
        escena.terminar_escena()
        self.assertEqual(self.ventana.escenas.currentIndex(), self.ventana.ESCENA_FIN)
        self.assertTrue(self.ventana.escena_fin.boton_epilogo.isVisible())
        self.ventana.escena_fin.boton_epilogo.click()
        self.assertEqual(self.ventana.escenas.currentIndex(), self.ventana.ESCENA_EPILOGO)


if __name__ == "__main__":
    unittest.main()
