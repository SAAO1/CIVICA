"""La campaña completa conserva voz y texto para sus ramas finitas."""
import unittest

from audio.catalogo_voces import PERFILES, cargar_manifest, clave_clip, frases_texto
from herramientas.producir_voces_siete_actos import inventario_siete_actos, verificar_cobertura
from juego.campana_extendida import FRASES_POSIBLES


class VocesSieteActosTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventario = inventario_siete_actos()

    def test_ocho_identidades_distintas_y_todas_las_lineas_con_sus_fragmentos(self):
        self.assertEqual(set(PERFILES), {
            "CIUDADANO", "PERIODISTA", "NARRADOR", "INFLUENCER", "JUAN", "ADRIAN", "LAURA", "CAMILA"})
        self.assertEqual(len({perfil["voz"] for perfil in PERFILES.values()}), 8)
        for nombre, texto in FRASES_POSIBLES:
            for parte in (texto, *frases_texto(texto)):
                with self.subTest(nombre=nombre, texto=parte):
                    clave = clave_clip(nombre, parte)
                    self.assertIn(clave, self.inventario)
                    self.assertEqual(self.inventario[clave], {"hablante": nombre, "texto": parte})

    def test_nueva_comunidad_y_limites_de_difusion_tienen_vocabulario_local(self):
        claves = set(self.inventario)
        self.assertIn(clave_clip("NARRADOR", "Violeta está entre sus receptores."), claves)
        self.assertIn(clave_clip("NARRADOR", "Valeria está entre sus receptores."), claves)
        for nombre, texto in (
            ("NARRADOR", "La publicación llegó a 19 ciudadanos en 3 unidades simuladas."),
            ("PERIODISTA", "La corrección llegó a 19 ciudadanos en 1.6 unidades simuladas."),
            ("NARRADOR", "Desinformación +20."),
            ("NARRADOR", "Puntuación de la acción: -15."),
        ):
            self.assertIn(clave_clip(nombre, texto), claves)

    def test_paquete_neural_cubre_todo_el_inventario_sin_prestar_interpretes(self):
        informe = verificar_cobertura(self.inventario)
        self.assertTrue(informe["correcto"], informe["errores"][:5])
        manifest = cargar_manifest()
        self.assertEqual(manifest["perfiles"], PERFILES)


if __name__ == "__main__":
    unittest.main()
