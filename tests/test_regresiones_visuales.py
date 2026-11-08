"""Regresiones de hover y capturas durante el cambio real de escenas."""
import os
import unittest
from unittest.mock import patch
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
os.environ.setdefault("QT_LOGGING_RULES","qt.multimedia.*=false")
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication,QToolTip
from interfaz.novela.ventana import VentanaNovela
from juego.lectura import BibliotecaLectura

class RegresionesVisuales(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        preferencias={"silenciado":True,"voces_activadas":False,"sin_limite":True,
            "reducir_movimiento":False,"animar_fondos":False,
            "animar_personajes":False,"velocidad_texto":0}
        for p in (patch.object(VentanaNovela,"_autoguardar"),
                  patch("interfaz.ventana.BibliotecaLectura",lambda:BibliotecaLectura(None)),
                  patch("infraestructura.configuracion.cargar",return_value=preferencias)):
            p.start()
            self.addCleanup(p.stop)
        self.v=VentanaNovela(4,eventos=False)
        self.v.resize(1360,720)
        self.v.show()
        self.v.iniciar_solo()
        self.app.processEvents()

    def tearDown(self):
        self.v.close()
        self.v.deleteLater()
        self.app.processEvents()

    def test_hover_de_cada_decision_no_muestra_descripcion_ni_cambia_altura(self):
        for rol in ("ciudadano","periodista"):
            self.v.iniciar_solo(rol)
            self.v.mostrar_escena(self.v.ESCENA_ACCION)
            self.v.statusBar().clearMessage()
            self.app.processEvents()
            escena=self.v.escena_accion
            alto=escena.height()
            botones=[*escena.botones_por_accion.values(),escena.boton_investigar]
            if rol=="ciudadano":
                botones.append(self.v.boton_rectificar)
            for boton in botones:
                with self.subTest(rol=rol,boton=boton.text()):
                    self.assertEqual(boton.toolTip(),"")
                    self.assertEqual(boton.statusTip(),"")
                    QTest.mouseMove(boton,boton.rect().center())
                    QTest.qWait(100)
                    self.assertFalse(QToolTip.isVisible())
                    self.assertEqual(self.v.statusBar().currentMessage(),"")
                    self.assertFalse(self.v.statusBar().isVisible())
                    self.assertEqual(escena.height(),alto)

    def test_entrada_no_captura_el_fondo_por_defecto_de_la_escena_destino(self):
        v=self.v
        v.mostrar_escena(v.ESCENA_DIALOGO)
        escena=v.escena_dialogo
        v.mostrar_escena(v.ESCENA_ACCION)
        with patch.object(escena.transicion_plano,"capturar",wraps=escena.transicion_plano.capturar) as capturar:
            v.mostrar_escena(v.ESCENA_DIALOGO)
        capturar.assert_not_called()
        self.assertTrue(escena.transicion_plano._captura.isNull())
        self.assertFalse(escena.transicion_plano.animando)
        self.assertEqual(escena._clave_preparada,"pulido_foro")
        self.assertTrue(v.escenas.updatesEnabled())

    def test_cambio_de_plano_captura_el_dialogo_anterior_antes_de_modificarlo(self):
        v=self.v
        v.mostrar_escena(v.ESCENA_DIALOGO)
        escena=v.escena_dialogo
        escena.timer_inicio.stop()
        escena.dialogo_actual=0
        escena.mostrar_dialogo_actual()
        escena.animacion.setCurrentTime(escena.animacion.duration())
        escena.revelar_texto()
        anterior=(escena.texto_completo,escena.texto_label.text(),escena._clave_preparada)
        vistos=[]
        original=escena.transicion_plano.capturar
        def capturar(widget):
            vistos.append((escena.texto_completo,escena.texto_label.text(),escena._clave_preparada))
            return original(widget)
        with patch.object(escena.transicion_plano,"capturar",side_effect=capturar):
            escena.dialogo_actual=next(i for i,(n,_) in enumerate(escena.dialogos) if n=="JUAN")
            escena.mostrar_dialogo_actual()
        self.assertEqual(vistos,[anterior])
        self.assertEqual(escena._clave_preparada,"pulido_foro_juan")
        self.assertTrue(escena.transicion_plano.animando)
        QTest.qWait(100)
        tiempo=escena.transicion_plano._animacion.currentTime()
        escena.preparar_puesta_audiovisual(escena.texto_completo,"JUAN")
        self.assertGreaterEqual(escena.transicion_plano._animacion.currentTime(),tiempo)
        self.assertFalse(escena.transicion_plano._pendiente)

    def test_cambio_rapido_de_escenas_no_conserva_un_fundido_interno_anterior(self):
        v=self.v
        for indice in (v.ESCENA_DIALOGO,v.ESCENA_ACCION,v.ESCENA_NARRACION_2,v.ESCENA_DIALOGO):
            v.mostrar_escena(indice)
            self.app.processEvents()
            escena=v.escenas.currentWidget()
            self.assertTrue(v.escenas.updatesEnabled())
            if hasattr(escena,"transicion_plano"):
                self.assertFalse(escena.transicion_plano.animando)
                self.assertTrue(escena.transicion_plano._captura.isNull())
        QTest.qWait(620)
        self.assertFalse(v.transicion_narrativa.isVisible())
        self.assertEqual(v.escena_dialogo._clave_preparada,"pulido_foro")

if __name__=="__main__":
    unittest.main()
