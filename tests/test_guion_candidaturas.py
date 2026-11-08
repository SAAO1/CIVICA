"""El foro pertenece a los seis actos y conserva las voces de sus cuatro candidatos."""
import json
import unittest

from juego.casos_feria import IDS_FERIA
from juego.investigacion import SesionInvestigacion
from interfaz.novela.guion import (
    contexto_candidaturas, cobertura_dialogos, datos_capitulo, dialogos_publicacion,
)


class GuionCuatroCandidaturas(unittest.TestCase):
    def nueva(self):
        sesion = SesionInvestigacion(semilla=4)
        identidad = sesion.registrar_jugador("Lector", "ciudadano")
        sesion.comenzar()
        return sesion, identidad

    def test_los_cuatro_hablan_con_prioridades_propias_antes_del_primer_rumor(self):
        sesion, _ = self.nueva()
        foro = contexto_candidaturas(sesion.juego)
        self.assertEqual({n for n, _ in foro} & {"JUAN", "ADRIAN", "LAURA", "CAMILA"},
                         {"JUAN", "ADRIAN", "LAURA", "CAMILA"})
        voces = dict(foro)
        for nombre, tema in (("JUAN", "colegio"), ("ADRIAN", "cultura"),
                             ("LAURA", "espacios"), ("CAMILA", "escuche")):
            self.assertIn(tema, voces[nombre])
        dialogos = dialogos_publicacion(sesion.juego)
        primer_rumor = next(i for i, (_, t) in enumerate(dialogos)
                           if t.startswith("Una notificación interrumpe"))
        self.assertGreaterEqual(primer_rumor, len(foro))

    def test_seis_actos_con_foro_recurrente_doblados_y_sin_mutar_partida(self):
        sesion, identidad = self.nueva()
        vistos = []
        for numero, caso in enumerate(IDS_FERIA, 1):
            antes = json.dumps(sesion.datos(), sort_keys=True)
            metadatos = datos_capitulo(sesion.juego)
            dialogos = dialogos_publicacion(sesion.juego)
            cobertura = cobertura_dialogos(sesion.juego)
            self.assertEqual(json.dumps(sesion.datos(), sort_keys=True), antes)
            self.assertEqual((metadatos["numero"], metadatos["total"]), (numero, 6))
            self.assertGreaterEqual(len(dialogos), 9 if caso != 50 else 11)
            self.assertEqual(cobertura["faltantes"], [], "Falta una voz original en acto "+str(numero))
            vistos.append(sesion.vista(identidad)["caso"]["id"])
            if caso == 40:
                self.assertTrue({"JUAN", "ADRIAN", "LAURA", "CAMILA"} <= {n for n, _ in dialogos})
                self.assertGreaterEqual(len(dialogos), 19)
            sesion.decidir(identidad, "ignorar")
            sesion.continuar(identidad)
        self.assertEqual(vistos, list(IDS_FERIA))
        self.assertEqual(sesion.fase, "final")
        self.assertEqual(len(sesion.juego.historial), 6)


if __name__ == "__main__":
    unittest.main()
