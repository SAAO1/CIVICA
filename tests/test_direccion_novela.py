"""Dirección real de las escenas originales, con planos propios sólo en feria."""
import os
from pathlib import Path
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_LOGGING_RULES", "qt.multimedia.*=false")
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from infraestructura.recursos import RAIZ
from juego.casos_feria import IDS_FERIA
from juego.lectura import BibliotecaLectura
from interfaz.novela.direccion import CATALOGO_PULIDO, elegir_plano, fondo_intervencion, expresion_actor
from interfaz.novela.ventana import VentanaNovela


class DireccionEscenasOriginales(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        preferencias = {"silenciado":True, "voces_activadas":False,
                        "sin_limite":True, "reducir_movimiento":True,
                        "animar_fondos":False, "animar_personajes":False,
                        "velocidad_texto":0}
        for parche in (
            patch("infraestructura.configuracion.cargar",return_value=preferencias),
            patch("interfaz.ventana.BibliotecaLectura",lambda:BibliotecaLectura(None)),
            patch.object(VentanaNovela,"_autoguardar"),
        ):
            parche.start()
            self.addCleanup(parche.stop)
        self.ventana = VentanaNovela(semilla=4,eventos=False)
        self.ventana.resize(1366,830)
        self.ventana.show()
        self.ventana.iniciar_solo()
        self.ventana.mostrar_escena(self.ventana.ESCENA_DIALOGO)
        self.app.processEvents()
        self.escena = self.ventana.escena_dialogo

    def tearDown(self):
        self.ventana.close()
        self.ventana.deleteLater()
        self.app.processEvents()

    def linea(self, indice):
        escena = self.escena
        escena.timer_inicio.stop()
        escena.dialogo_actual = indice
        escena.mostrar_dialogo_actual()
        escena.animacion.setCurrentTime(escena.animacion.duration())
        QTest.qWait(25)
        self.app.processEvents()
        nombre, texto = escena.dialogos[indice]
        self.assertEqual(escena.texto_completo,texto)
        return nombre,texto

    def captura(self, nombre):
        destino = RAIZ/".tmp"/("direccion_"+nombre+".png")
        destino.parent.mkdir(exist_ok=True)
        self.assertTrue(self.escena.grab().save(str(destino)))

    def test_foro_cuatro_voces_con_video_propio_y_regreso_real_al_cafe(self):
        escena = self.escena
        self.linea(0)
        self.assertEqual(escena._clave_preparada,"pulido_foro")
        self.assertTrue(escena.cine_narrativo.activa)
        self.assertTrue(all(not p.isVisible() for p in escena.personajes.values()))
        self.captura("foro")
        vistos = set()
        for indice,(nombre,_) in enumerate(escena.dialogos):
            if nombre not in ("JUAN","ADRIAN","LAURA","CAMILA"):
                continue
            self.linea(indice)
            self.assertEqual(escena._clave_preparada,"pulido_foro_"+nombre.lower())
            self.assertTrue(escena.cine_narrativo.activa)
            self.assertTrue(escena.fondo.endswith("/debate.jpg"))
            self.assertTrue(all(not p.isVisible() for p in escena.personajes.values()))
            self.assertFalse(escena.cine_narrativo._poster.imagen.isNull())
            vistos.add(nombre)
            if nombre=="JUAN":
                self.captura("juan")
        self.assertEqual(vistos,{"JUAN","ADRIAN","LAURA","CAMILA"})
        cafe = next(i for i,(_,texto) in enumerate(escena.dialogos)
                    if texto.startswith("Una notificación interrumpe la mañana"))
        self.linea(cafe)
        self.assertEqual(escena._clave_preparada,"pulido_caso_50")
        self.assertFalse(escena.fondo.endswith("/debate.jpg"))
        self.assertTrue(escena.cine_narrativo.activa)
        self.captura("cafe")

    def test_seis_casos_solo_usan_planos_propios_o_sprites_y_conservan_estado(self):
        v=self.ventana
        hablantes=set()
        for caso in IDS_FERIA:
            self.assertEqual(v.vista_novela["caso"]["id"],caso)
            v.mostrar_escena(v.ESCENA_DIALOGO)
            self.escena=v.escena_dialogo
            estado=v.sesion.datos()
            for indice,(nombre,texto) in enumerate(self.escena.dialogos):
                self.linea(indice)
                clave=self.escena._clave_preparada
                self.assertTrue(clave is None or clave.startswith("pulido_"),repr((caso,nombre,clave)))
                esperado=elegir_plano(v.juego,texto,nombre)
                if esperado and (RAIZ/CATALOGO_PULIDO[esperado]["poster"]).is_file():
                    self.assertEqual(clave,esperado)
                if nombre in ("JUAN","ADRIAN","LAURA","CAMILA","INFLUENCER"):
                    hablantes.add(nombre)
                    if clave and clave.startswith("pulido_foro_"):
                        self.assertTrue(self.escena.cine_narrativo.activa)
                        self.assertFalse(self.escena.personajes[nombre].isVisible())
                    else:
                        self.assertTrue(self.escena.personajes[nombre].isVisible(),repr((caso,nombre)))
                        self.assertIsNone(clave)
                if nombre == "NARRADOR":
                    self.assertIsNotNone(clave,repr((caso,texto)))
                    self.assertTrue(self.escena.cine_narrativo.activa)
            self.assertEqual(v.sesion.datos(),estado)
            v.enviar_comando_novela({"tipo":"decidir","accion":"ignorar"})
            v.mostrar_escena(v.ESCENA_ARBOL)
            v.escena_arbol.boton_continuar.click()
            v.escena_red.boton_continuar.click()
        self.assertEqual(hablantes,{"JUAN","ADRIAN","LAURA","CAMILA","INFLUENCER"})
        self.assertEqual(v.sesion.fase,"final")

    def test_narrador_con_video_y_balance_con_fondo_de_ciudad(self):
        v=self.ventana
        for indice in (v.ESCENA_NARRACION_1,v.ESCENA_NARRACION_2,v.ESCENA_NARRACION_3):
            v.mostrar_escena(indice)
            escena=v.escenas.currentWidget()
            self.assertIsNotNone(escena._clave_preparada)
            self.assertTrue(escena.cine_narrativo.activa)
        for caso in IDS_FERIA:
            self.assertEqual(v.vista_novela["caso"]["id"],caso)
            self.assertTrue(v.enviar_comando_novela({"tipo":"decidir","accion":"ignorar"}))
            for tipo in (1,2):
                self.assertEqual(elegir_plano(v.juego,"La ciudad responde.","NARRADOR",tipo),"pulido_caso_"+str(caso))
            v.mostrar_escena(v.ESCENA_RESULTADO_3)
            escena=v.escena_resultado_3
            self.assertIsNone(escena._clave_preparada)
            self.assertFalse(escena.cine_narrativo.activa)
            self.assertTrue(escena.balance.isVisible())
            self.assertIsNone(escena.boton_detalle)
            v.mostrar_escena(v.ESCENA_ARBOL)
            v.escena_arbol.boton_continuar.click()
            v.escena_red.boton_continuar.click()
        v.mostrar_escena(v.ESCENA_EPILOGO)
        escena=v.escena_epilogo
        escena.timer_inicio.stop()
        narraciones=0
        for i,(nombre,texto) in enumerate(escena.dialogos):
            if nombre!="NARRADOR":
                continue
            narraciones+=1
            escena.dialogo_actual=i
            escena.mostrar_dialogo_actual()
            self.assertIsNotNone(escena._clave_preparada,texto)
            self.assertTrue(escena.cine_narrativo.activa)
        self.assertGreater(narraciones,0)

    def test_los_presentes_reaccionan_al_dano_real_sin_mostrar_actores_ausentes(self):
        v=self.ventana
        v.enviar_comando_novela({"tipo":"decidir", "accion":"compartir",
                                "contactos":["pedro"], "certeza":"pendiente"})
        registro=v.juego.ultimo_registro
        self.assertGreater(registro["cambios_reales"]["desinformacion"],0)
        v.mostrar_escena(v.ESCENA_DIALOGO)
        escena=v.escena_dialogo
        escena.timer_inicio.stop()
        escena.iniciar_dialogo("La conversación continúa.","CIUDADANO",
                                {"CIUDADANO","PERIODISTA"})
        self.assertEqual(escena.personajes["CIUDADANO"].imagen.expresion,"preocupado")
        self.assertEqual(escena.personajes["PERIODISTA"].imagen.expresion,"enojado")
        self.assertTrue(escena.personajes["PERIODISTA"].isVisible())
        self.assertTrue(all(not p.isVisible() for n,p in escena.personajes.items()
                            if n not in ("CIUDADANO","PERIODISTA")))
        escena.iniciar_dialogo("Escucho lo que ocurrió.","JUAN",{"JUAN"})
        self.assertEqual(escena.personajes["JUAN"].imagen.expresion,"sorprendido")
        self.assertEqual(escena.personajes_activos,{"JUAN"})
        self.assertTrue(escena.personajes["JUAN"].isVisible())

    def test_fuente_y_correccion_real_producen_alivio_y_no_mutan_motor(self):
        v=self.ventana
        v.iniciar_solo("periodista")
        v.enviar_comando_novela({"tipo":"investigar","lugar":"archivo"})
        v.enviar_comando_novela({"tipo":"decidir","accion":"desmentir",
                                "certeza":"confirmada","evidencia_id":"50:documento"})
        self.assertTrue(v.juego.ultimo_registro["editor"]["evidencia_pertinente"])
        self.assertTrue(v.juego.ultimo_registro["eliminada"])
        antes=v.sesion.datos()
        for nombre in ("CIUDADANO","PERIODISTA","JUAN","ADRIAN","LAURA","CAMILA","INFLUENCER"):
            self.assertEqual(expresion_actor(v.juego,nombre,""),"sonrisa")
        self.assertEqual(v.sesion.datos(),antes)

    def test_conversar_y_entrevistar_conservan_plano_de_su_oficio_real(self):
        v=self.ventana
        for rol,accion in (("ciudadano","conversar"),("periodista","entrevistar")):
            v.iniciar_solo(rol)
            self.assertTrue(v.enviar_comando_novela({"tipo":"decidir","accion":accion}))
            self.assertEqual(v.juego.ultima_accion,"ignorar")
            self.assertEqual(v.juego.ultimo_registro["accion_rol"],accion)
            self.assertEqual(elegir_plano(v.juego,"Una reacción.","CIUDADANO",1),"pulido_caso_50")
            escena=v.escena_resultado_1
            self.assertEqual(escena._clave_preparada,"pulido_caso_50")

    def test_fundido_entre_planos_no_tapa_controles_ni_introduce_negro(self):
        escena=self.escena
        self.ventana.reducir_movimiento=False
        self.ventana.animar_fondos=False
        self.linea(0)
        juan=next(i for i,(nombre,_) in enumerate(escena.dialogos) if nombre=="JUAN")
        self.linea(juan)
        self.assertTrue(escena.transicion_plano.animando)
        self.assertTrue(escena.transicion_plano.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents))
        imagen=escena.grab().toImage()
        valores=[imagen.pixelColor(x,y).lightness() for x in range(100,imagen.width()-100,80)
                 for y in range(90,imagen.height()-180,80)]
        self.assertGreater(sum(valores)/len(valores),10,"El plano quedó cubierto de negro")
        self.assertTrue(escena.boton_historial.isEnabled())
        QTest.qWait(650)
        self.assertFalse(escena.transicion_plano.isVisible())
        self.assertIs(self.ventana.escenas.currentWidget(),escena)


if __name__=="__main__":
    unittest.main()
