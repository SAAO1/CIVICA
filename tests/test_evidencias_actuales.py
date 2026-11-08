"""Pruebas actuales y fuentes atribuidas durante los seis actos, sin interfaz."""
import copy
import json
import unittest

from juego.casos_feria import IDS_FERIA, crear_caso
from juego.investigacion import SesionInvestigacion


def firma(sesion):
    return json.dumps(sesion.datos(),sort_keys=True,ensure_ascii=False)


class EvidenciasDelActoActual(unittest.TestCase):
    def nueva(self, rol="ciudadano", cooperativa=False):
        sesion=SesionInvestigacion(semilla=4,cooperativa=cooperativa)
        sesion.registrar_jugador("Vecino" if rol=="ciudadano" else "Reportera",rol,id="c")
        if cooperativa:
            sesion.registrar_jugador("Reportera","periodista",id="p")
        sesion.comenzar()
        return sesion

    def test_ambos_roles_avanzan_seis_actos_con_prueba_actual_y_presupuesto_agotado(self):
        for rol in ("ciudadano","periodista"):
            with self.subTest(rol=rol):
                sesion=self.nueva(rol)
                anterior=None
                for caso_id in IDS_FERIA:
                    sesion.investigar("c","archivo")
                    sesion.investigar("c","redaccion")
                    vista=sesion.vista("c")
                    self.assertEqual(vista["acciones_restantes"],0)
                    pertinentes=vista["evidencias_pertinentes"]
                    self.assertTrue(pertinentes)
                    self.assertTrue(all(h["caso_id"]==caso_id and h["pertinente"] for h in pertinentes))
                    self.assertEqual(pertinentes[0]["id"],str(caso_id)+":documento")
                    if anterior:
                        antes=firma(sesion)
                        critica="rectificar" if rol=="ciudadano" else "desmentir"
                        with self.assertRaisesRegex(ValueError,"pertenece al acto"):
                            sesion.proponer("c",critica,evidencia_id=anterior,certeza="confirmada")
                        self.assertEqual(firma(sesion),antes)
                        self.assertFalse(next(h for h in vista["hallazgos"] if h["id"]==anterior)["pertinente"])
                    publicacion=sesion.juego.obtener_publicacion_actual()
                    accion=("rectificar" if publicacion.verdadera is False else "compartir") if rol=="ciudadano" else "desmentir"
                    opcion=next(a for a in vista["acciones"] if a["clave"]==accion)
                    self.assertTrue(opcion["disponible"],opcion["motivo_no_disponible"])
                    adjunto=opcion["evidencia_sugerida"]
                    self.assertEqual(adjunto,str(caso_id)+":documento")
                    sesion.proponer("c",accion,evidencia_id=adjunto,certeza="confirmada")
                    sesion.decidir("c",accion,evidencia_id=adjunto,certeza="confirmada")
                    self.assertEqual(sesion.fase,"resultado")
                    self.assertEqual(sesion.juego.historial[-1]["editor"]["evidencia_id"],adjunto)
                    sesion.continuar("c")
                    anterior=adjunto
                self.assertEqual(sesion.fase,"final")
                self.assertEqual(len(sesion.juego.historial),6)

    def test_regresion_audio110_no_respalda_mapa120_que_si_se_puede_confirmar(self):
        sesion=self.nueva("periodista")
        while sesion.caso_id!=120:
            sesion.investigar("c","archivo")
            if sesion.caso_id==110:
                sesion.investigar("c","redaccion")
            sesion.decidir("c","contrastar",evidencia_id=str(sesion.caso_id)+":documento")
            sesion.continuar("c")
        sesion.investigar("c","archivo")
        antigua=next(h for h in sesion.vista("c")["hallazgos"] if h["id"]=="110:contexto")
        self.assertIn("La pregunta del público",antigua["titulo"])
        self.assertFalse(antigua["pertinente"])
        antes=firma(sesion)
        with self.assertRaisesRegex(ValueError,r"acto 3 \(#110\).*acto 5 \(#120\)"):
            sesion.decidir("c","desmentir",evidencia_id="110:contexto",certeza="confirmada")
        self.assertEqual(firma(sesion),antes)
        sesion.decidir("c","desmentir",evidencia_id="120:documento",certeza="confirmada")
        self.assertEqual(sesion.fase,"resultado")
        sesion.continuar("c")
        self.assertEqual(sesion.caso_id,35)

    def test_doce_decisiones_cooperativas_con_pruebas_privadas_actuales(self):
        sesion=self.nueva(cooperativa=True)
        anterior=None
        for caso_id in IDS_FERIA:
            sesion.investigar("c","redaccion")
            sesion.investigar("p","archivo")
            documento=str(caso_id)+":documento"
            contexto=str(caso_id)+":contexto"
            c,p=sesion.vista("c"),sesion.vista("p")
            self.assertEqual([h["id"] for h in c["evidencias_pertinentes"]],[contexto])
            self.assertEqual([h["id"] for h in p["evidencias_pertinentes"]],[documento])
            ajena=next(h for h in c["hallazgos_disponibles"] if h["id"]==documento)
            self.assertNotIn("texto",ajena)
            self.assertEqual(ajena["caso_id"],caso_id)
            self.assertFalse(next(a for a in p["acciones"] if a["clave"]=="desmentir")["disponible"])
            with self.assertRaisesRegex(ValueError,"privada"):
                sesion.proponer("c","compartir",evidencia_id=documento)
            sesion.compartir_hallazgo("p",documento)
            self.assertIn(documento,[h["id"] for h in sesion.vista("c")["evidencias_pertinentes"]])
            if anterior:
                self.assertNotIn(anterior,[h["id"] for h in sesion.vista("c")["evidencias_pertinentes"]])
            sesion.decidir("c","compartir",evidencia_id=contexto,certeza="confirmada")
            self.assertTrue(next(a for a in sesion.vista("p")["acciones"] if a["clave"]=="desmentir")["disponible"])
            sesion.decidir("p","desmentir",evidencia_id=documento,certeza="confirmada")
            sesion.continuar("c")
            self.assertEqual(sesion.caso_id,caso_id)
            sesion.continuar("p")
            anterior=documento
        self.assertEqual(sesion.fase,"final")
        self.assertEqual(len(sesion.juego.historial),12)
        self.assertEqual({j.rol for j in sesion.juego.jugadores},{"ciudadano","periodista"})

    def test_fuentes_de_madre_abuelo_y_valeria_preservan_texto_y_nodos(self):
        for caso_id,npc,fuente in ((50,"luis","madre_colegio"),(120,"ines","abuelo"),(35,"luis","valeria")):
            caso=crear_caso(caso_id)
            testimonio=next(e for e in caso["evidencias"] if e["tipo"]=="testimonio")
            self.assertEqual(caso["npc_id"],npc)
            self.assertEqual(testimonio["fuente_id"],fuente)
            self.assertEqual(testimonio["fuente_id"],caso["fuente_id"])
        madre=next(e for e in crear_caso(50)["evidencias"] if e["tipo"]=="testimonio")
        self.assertIn("madre",madre["titulo"])
        self.assertEqual(madre["fuente_retrato"],"avatar:maria")
        abuelo=next(e for e in crear_caso(120)["evidencias"] if e["tipo"]=="testimonio")
        self.assertIn("abuelo",abuelo["titulo"])
        self.assertEqual(abuelo["fuente_retrato"],"assets/novela/pulido/cg/urnas_contexto.png")
        self.assertEqual(abuelo["fuente_recorte"],{"x":.03,"y":.10,"ancho":.23,"alto":.72})
        valeria=next(e for e in crear_caso(35)["evidencias"] if e["tipo"]=="testimonio")
        self.assertIn("Valeria",valeria["titulo"])
        self.assertIn("influencer_neutral.png",valeria["fuente_retrato"])

    def test_guardado_antiguo_recibe_atribuciones_actuales_sin_mutar_persistencia(self):
        sesion=self.nueva()
        for _ in IDS_FERIA:
            sesion.investigar("c","barrio")
            sesion.decidir("c","ignorar")
            sesion.continuar("c")
        datos=sesion.datos()
        for h in datos["hallazgos"]:
            for clave in list(h):
                if clave.startswith("fuente_"):
                    del h[clave]
        restaurada=SesionInvestigacion.desde_datos(datos)
        antes=firma(restaurada)
        vistos={h["id"]:h for h in restaurada.vista("c")["hallazgos"]}
        self.assertEqual(vistos["50:testimonio"]["fuente_retrato"],"avatar:maria")
        self.assertEqual(vistos["120:testimonio"]["fuente_id"],"abuelo")
        self.assertEqual(vistos["35:testimonio"]["fuente_id"],"valeria")
        self.assertEqual(firma(restaurada),antes)

    def test_preserva_respuestas_seguras_y_penalizacion_original_sin_documentos(self):
        for rol,accion in (("ciudadano","ignorar"),("periodista","reservar")):
            sesion=self.nueva(rol)
            opciones=sesion.vista("c")["acciones"]
            self.assertTrue(next(a for a in opciones if a["clave"]==accion)["disponible"])
            criticas=[a for a in opciones if a["requiere_prueba"]]
            self.assertTrue(all(not a["disponible"] and a["motivo_no_disponible"] for a in criticas))
            sesion.decidir("c",accion,certeza="pendiente")
            self.assertEqual(sesion.fase,"resultado")
        sesion=self.nueva()
        sesion.decidir("c","compartir",certeza="confirmada")
        self.assertIn("sin respaldo",sesion.juego.historial[-1]["editorial"])


if __name__=="__main__":
    unittest.main()
