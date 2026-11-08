"""El libro responde con pruebas del acto actual sin formularios editoriales."""
import os
import unittest
from unittest.mock import patch
from PyQt6.QtCore import QPoint,QRect
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication,QComboBox,QLineEdit,QWidget
from juego.investigacion import SesionInvestigacion
from interfaz.novela.interacciones import OverlayInvestigacion


class LibroGuiado(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
        cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        self.padres=[]
        self.libros=[]
        self.libros_sesion=[]
        self.comandos=[]

    def tearDown(self):
        for libro in self.libros:
            libro.cerrar()
        for padre in self.padres:
            padre.close()
        self.app.processEvents()

    def sesion(self,rol="ciudadano",coop=False):
        s=SesionInvestigacion(4,cooperativa=coop)
        s.juego.eventos_activos=False
        if coop:
            s.registrar_jugador("Ana","ciudadano","c")
            s.registrar_jugador("Sol","periodista","p")
        else:
            s.registrar_jugador("Ana",rol,"j")
        s.comenzar()
        return s

    def libro(self,s,id="j",ancho=1100,alto=700):
        padre=QWidget()
        padre.reducir_movimiento=True
        padre.resize(ancho,alto)
        padre.show()
        self.padres.append(padre)
        def enviar(comando):
            self.comandos.append(comando)
            args={k:v for k,v in comando.items() if k!="tipo"}
            if comando["tipo"]=="examinar":
                args["tipo"]=args.pop("medio")
            try:
                getattr(s,comando["tipo"])(id,**args)
            except ValueError as error:
                libro.mostrar_mensaje(str(error))
                return False
            for otro,actor in self.libros_sesion:
                otro.actualiza(s.vista(actor))
            return True
        libro=OverlayInvestigacion(s.vista(id),enviar,padre)
        self.libros.append(libro)
        self.libros_sesion.append((libro,id))
        libro.abrir()
        self.app.processEvents()
        return libro

    def confirmar(self,libro,accion):
        libro.decision(accion)
        libro.siguiente_paso.click()
        self.assertEqual(libro.paginas.currentIndex(),libro.secciones["confirmacion"])
        self.assertTrue(libro.confirmar.isVisible())
        self.assertTrue(libro.confirmar.isEnabled())
        libro.confirmar.click()

    def test_tres_pasos_tres_respuestas_y_ningun_formulario_opcional(self):
        for rol in ("ciudadano","periodista"):
            with self.subTest(rol=rol):
                self.libros_sesion=[]
                libro=self.libro(self.sesion(rol))
                self.assertEqual(list(libro.botones_seccion),["fuentes","decision","confirmacion"])
                self.assertEqual(len(libro.botones_accion),3)
                self.assertEqual(libro.findChildren(QLineEdit),[])
                self.assertEqual(libro.findChildren(QComboBox),[])
                self.assertIn("2/2",libro.presupuesto.text())
                self.assertFalse(hasattr(libro,"opciones"))
                self.assertFalse(hasattr(libro,"titular"))

    def test_ambos_roles_adjuntan_prueba_actual_y_confirman_sin_rellenar_campos(self):
        for rol,accion in (("ciudadano","ignorar"),("periodista","contrastar")):
            with self.subTest(rol=rol):
                self.libros_sesion=[]
                s=self.sesion(rol)
                libro=self.libro(s)
                libro.botones_lugares["redaccion"].click()
                self.assertEqual(s.presupuestos["j"],1)
                self.assertEqual(libro.paginas.currentIndex(),libro.secciones["pista"])
                self.assertTrue(libro.pista_texto.text())
                libro.siguiente_paso.click()
                self.assertEqual(libro.paginas.currentIndex(),libro.secciones["decision"])
                self.confirmar(libro,accion)
                self.assertEqual(s.fase,"resultado")
                self.assertEqual(self.comandos[-1]["evidencia_id"],"50:contexto")
                self.assertEqual(self.comandos[-1]["certeza"],"confirmada")

    def test_sin_documento_y_con_cero_investigaciones_sigue_habiendo_salida_segura(self):
        s=self.sesion("periodista")
        s.investigar("j","barrio")
        # Un guardado válido puede conservar solo testimonios y el presupuesto agotado.
        datos=s.datos()
        datos["presupuestos"]["j"]=0
        s=SesionInvestigacion.desde_datos(datos)
        libro=self.libro(s)
        self.assertEqual(s.presupuestos["j"],0)
        self.assertIsNone(libro._prueba)
        self.assertFalse(libro.botones_accion["contrastar"].isEnabled())
        self.assertIn("Falta",libro.motivos_accion["contrastar"].text())
        libro.decision("contrastar")
        self.assertFalse(libro.siguiente_paso.isEnabled())
        self.assertTrue(libro.botones_accion["reservar"].isEnabled())
        self.confirmar(libro,"reservar")
        self.assertEqual(s.fase,"resultado")
        self.assertIsNone(self.comandos[-1]["evidencia_id"])
        self.assertEqual(self.comandos[-1]["certeza"],"pendiente")

    def test_120_y_35_no_adjuntan_hallazgos_historicos_y_confirmar_funciona(self):
        s=self.sesion("periodista")
        while s.caso_id!=120:
            s.investigar("j","archivo")
            s.decidir("j","reservar")
            s.continuar("j")
        libro=self.libro(s)
        self.assertGreater(len(s.hallazgos),0)
        self.assertIsNone(libro._prueba)
        self.assertFalse(libro.botones_accion["desmentir"].isEnabled())
        for caso in (120,35):
            with self.subTest(caso=caso):
                self.assertEqual(s.caso_id,caso)
                s.investigar("j","archivo")
                libro.actualiza(s.vista("j"))
                self.assertEqual(libro._prueba["caso_id"],caso)
                self.confirmar(libro,"desmentir")
                self.assertEqual(s.fase,"resultado")
                self.assertEqual(self.comandos[-1]["evidencia_id"],str(caso)+":documento")
                if caso==120:
                    s.continuar("j")
                    libro.actualiza(s.vista("j"))
                    self.assertIsNone(libro._prueba)

    def test_revision_cooperativa_preserva_respuesta_y_compartir_no_filtra_privados(self):
        s=self.sesion(coop=True)
        ciudadano=self.libro(s,"c")
        periodista=self.libro(s,"p")
        ciudadano.decision("compartir")
        ciudadano.slider.setValue(42)
        periodista.botones_lugares["archivo"].click()
        self.assertNotIn("50:documento",[h["id"] for h in ciudadano._hallazgos_visibles()])
        self.assertEqual(ciudadano._accion,"compartir")
        self.assertEqual(ciudadano.slider.value(),42)
        self.assertEqual(ciudadano.paginas.currentIndex(),ciudadano.secciones["decision"])
        self.assertTrue(periodista.compartir_pista.isVisible())
        periodista.compartir_pista.click()
        self.assertEqual(ciudadano._prueba["id"],"50:documento")
        self.assertEqual(ciudadano._accion,"compartir")
        self.assertFalse(periodista.compartir_pista.isVisible())

    def test_testimonio_usa_retrato_femenino_y_abuelo_segun_metadata(self):
        s=self.sesion()
        s.investigar("j","barrio")
        libro=self.libro(s)
        madre=next(h for h in libro._actuales() if h["tipo"]=="testimonio")
        muestra=QPixmap(30,50)
        with patch("interfaz.novela.interacciones.avatar_arte",return_value=muestra) as avatar:
            libro._imagen_hallazgo(madre)
        avatar.assert_called_once_with("maria")
        libro.ver_hallazgo(madre)
        self.assertIn("Madre",libro.pista_titulo.text())
        while s.caso_id!=120:
            s.decidir("j","ignorar")
            s.continuar("j")
        s.investigar("j","barrio")
        libro.actualiza(s.vista("j"))
        abuelo=next(h for h in libro._actuales() if h["tipo"]=="testimonio")
        imagen=libro._imagen_hallazgo(abuelo)
        self.assertFalse(imagen.isNull())
        self.assertLess(imagen.width(),imagen.height())
        libro.ver_hallazgo(abuelo)
        self.assertIn("abuelo",libro.pista_titulo.text())

    def test_arrastrar_y_confirmar_punto_erroneo_no_gastan_investigacion(self):
        s=self.sesion()
        libro=self.libro(s)
        libro.abrir("material")
        antes=s.datos()
        libro.slider.setValue(20)
        self.assertEqual(s.datos(),antes)
        libro.siguiente_paso.click()
        self.assertEqual(s.datos(),antes)
        libro.slider.setValue(85)
        libro.siguiente_paso.click()
        self.assertEqual(s.presupuestos["j"],1)

    def test_prueba_texto_y_confirmacion_visibles_en_tamanos_reales(self):
        for ancho,alto in ((1100,700),(1360,720)):
            with self.subTest(tamano=(ancho,alto)):
                self.libros_sesion=[]
                s=self.sesion()
                libro=self.libro(s,ancho=ancho,alto=alto)
                libro.abrir("material")
                self.app.processEvents()
                for control in (libro.area_prueba,libro.slider,libro.ampliar,libro.siguiente_paso):
                    self.assertTrue(control.isVisible())
                    rect=QRect(control.mapTo(libro,QPoint(0,0)),control.size())
                    self.assertTrue(libro.rect().contains(rect),str(rect))
                    self.assertEqual(control.visibleRegion().boundingRect().height(),control.height())
                s.investigar("j","barrio")
                libro.actualiza(s.vista("j"))
                libro.ver_hallazgo(libro._actuales()[0])
                self.app.processEvents()
                self.assertTrue(libro.pista_imagen.isVisible())
                self.assertGreaterEqual(libro.pista_imagen.height(),200)
                self.assertTrue(libro.pista_texto.isVisible())
                self.assertTrue(libro.siguiente_paso.isVisible())
                self.confirmar(libro,"ignorar")


    def test_contexto_del_audio_110_recupera_la_transcripcion_con_un_clic(self):
        s=self.sesion()
        while s.caso_id!=110:
            s.decidir("j","ignorar")
            s.continuar("j")
        libro=self.libro(s)
        libro.abrir("material")
        self.assertFalse(libro.escuchar.isEnabled())
        self.assertTrue(libro.fragmento.text())
        libro.botones_zona[-1].click()
        self.assertEqual(libro.slider.value(),65)
        libro.siguiente_paso.click()
        self.assertEqual(s.presupuestos["j"],1)
        self.assertEqual(libro.paginas.currentIndex(),libro.secciones["pista"])
        self.assertEqual(libro._prueba["id"],"110:medio")


    def test_confirmacion_actualiza_prueba_compartida_sin_cambiar_accion_pagina_o_foco(self):
        s=self.sesion(coop=True)
        ciudadano=self.libro(s,"c")
        ciudadano.botones_lugares["redaccion"].click()
        ciudadano.decision("compartir")
        ciudadano.siguiente_paso.click()
        ciudadano.confirmar.setFocus()
        self.app.processEvents()
        self.assertTrue(ciudadano.confirmar.hasFocus())
        detalle_anterior=ciudadano.confirmacion_detalle.text()
        # La otra persona actúa en su dispositivo; aquí llega únicamente la vista.
        s.investigar("p","archivo")
        s.compartir_hallazgo("p","50:documento")
        ciudadano.actualiza(s.vista("c"))
        self.assertEqual(ciudadano._accion,"compartir")
        self.assertEqual(ciudadano._prueba["id"],"50:documento")
        self.assertEqual(ciudadano.paginas.currentIndex(),ciudadano.secciones["confirmacion"])
        self.assertIn(ciudadano._prueba["titulo"],ciudadano.confirmacion_detalle.text())
        self.assertNotEqual(ciudadano.confirmacion_detalle.text(),detalle_anterior)
        self.assertTrue(ciudadano.confirmar.hasFocus())
        ciudadano.confirmar.click()
        self.assertEqual(s.juego.historial[-1]["editor"]["evidencia_id"],"50:documento")


if __name__=="__main__":
    unittest.main()
