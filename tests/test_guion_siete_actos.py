"""Coherencia de ramas, voces y cierres de la campaña completa."""
import copy
import itertools
import json
from types import SimpleNamespace
import unittest

from juego.acciones import accion_por_defecto, acciones_para_rol
from juego.campana_extendida import (
    CASOS_NUEVOS, DIALOGOS_NUEVOS, FRASES_POSIBLES, PUBLICACIONES_NUEVAS,
    dialogos_extendidos, epilogo_extendido, estado_narrativo,
    reaccion_extendida, texto_epilogo_extendido,
)
from juego.partida import Juego
from models.candidato import candidatos_iniciales


class GuionSieteActosTests(unittest.TestCase):
    def test_lectura_del_guion_no_altera_la_partida_ni_el_azar(self):
        juego = Juego(704, eventos=False, campana="extendida")
        juego.iniciar_primera_publicacion()
        vistos = []
        while not juego.finalizada:
            identificador = juego.obtener_publicacion_actual().id
            antes = json.dumps(juego.datos(), sort_keys=True)
            conversacion = dialogos_extendidos(juego)
            if identificador in CASOS_NUEVOS:
                vistos.append(identificador)
                self.assertGreaterEqual(len(conversacion), 8)
                self.assertTrue(any(nombre in {"INFLUENCER", "JUAN", "ADRIAN", "LAURA", "CAMILA"}
                                    for nombre, _ in conversacion))
                self.assertTrue(set(conversacion).issubset(set(FRASES_POSIBLES)))
            self.assertEqual(antes, json.dumps(juego.datos(), sort_keys=True))
            juego.ejecutar_accion("conversar")
            antes = json.dumps(juego.datos(), sort_keys=True)
            for tipo in (1, 2, 3):
                resultado = reaccion_extendida(juego, tipo)
                if resultado is not None:
                    texto, nombre = resultado
                    self.assertIn((nombre, texto), FRASES_POSIBLES)
            self.assertEqual(antes, json.dumps(juego.datos(), sort_keys=True))
            juego.avanzar_publicacion()
        self.assertEqual(vistos, [90, 40, 100, 10, 110, 25, 120, 35])
        antes = json.dumps(juego.datos(), sort_keys=True)
        cierre = epilogo_extendido(juego)
        self.assertTrue(set(cierre).issubset(set(FRASES_POSIBLES)))
        self.assertEqual(texto_epilogo_extendido(juego), "\n\n".join(texto for _, texto in cierre))
        self.assertEqual(antes, json.dumps(juego.datos(), sort_keys=True))

    def test_todos_los_metodos_tienen_reaccion_fiel_y_voz_catalogada(self):
        for rol in ("ciudadano", "periodista"):
            for identificador in CASOS_NUEVOS:
                for accion in acciones_para_rol(rol):
                    with self.subTest(rol=rol, id=identificador, accion=accion["clave"]):
                        juego = Juego(704, eventos=False, campana="extendida")
                        juego.seleccionar_rol(rol)
                        juego.iniciar_primera_publicacion()
                        while juego.obtener_publicacion_actual().id != identificador:
                            juego.ejecutar_accion(accion_por_defecto(rol))
                            juego.avanzar_publicacion()
                        self.assertTrue(juego.ejecutar_accion(accion["clave"]))
                        antes = json.dumps(juego.datos(), sort_keys=True)
                        texto, nombre = reaccion_extendida(juego, 1)
                        self.assertEqual(nombre, rol.upper())
                        self.assertIn((nombre, texto), FRASES_POSIBLES)
                        efecto, voz = reaccion_extendida(juego, 2)
                        self.assertIn((voz, efecto), FRASES_POSIBLES)
                        self.assertEqual(antes, json.dumps(juego.datos(), sort_keys=True))
                        if identificador == 10 and accion["clave"] == "contrastar":
                            self.assertIn("opinión", efecto)
                            self.assertIn("No recibe un sello de verdad", efecto)
                        if accion["clave"] == "desmentir" and not juego.ultimo_registro["eliminada"]:
                            self.assertIn("rechazado", efecto)

    def test_alcance_cero_y_contactos_existentes_no_inventan_resultados(self):
        publicacion = copy.deepcopy(PUBLICACIONES_NUEVAS[0])
        registro = {"publicacion": publicacion, "accion": "compartir", "alcance": 0,
                    "efectos_red": {"conexiones_creadas": []}}
        juego = SimpleNamespace(ultimo_registro=registro)
        self.assertIn("no alcanzó", reaccion_extendida(juego, 1)[0])
        self.assertIn("no alcanzó", reaccion_extendida(juego, 2)[0])
        registro["accion_rol"] = "convocar"
        self.assertIn("Todavía no hay una reunión", reaccion_extendida(juego, 1)[0])
        registro["accion_rol"] = "conversar"
        self.assertIn("ya existían", reaccion_extendida(juego, 2)[0])
        registro["accion_rol"] = "entrevistar"
        self.assertIn("ya estaba", reaccion_extendida(juego, 2)[0])
        registro["accion_rol"] = "desmentir"
        registro["eliminada"] = True
        self.assertIn("no alcanzó", reaccion_extendida(juego, 2)[0])

    def test_cuarenta_y_cinco_combinaciones_de_cierre_conservan_el_resultado(self):
        cierres = set()
        for ganador, calidad, arco in itertools.product(
                ("juan", "adrian", "laura", "camila", "empate"), (65, 35, 5),
                ("responsable", "crisis", "silencio")):
            candidatos = candidatos_iniciales()
            eleccion = {"ganadores": [c.nombre for c in candidatos if c.id == ganador],
                        "empate": ganador == "empate", "calidad": calidad}
            if ganador == "empate":
                eleccion["ganadores"] = [candidatos[0].nombre, candidatos[1].nombre]
            publicacion = copy.deepcopy(PUBLICACIONES_NUEVAS[0])
            accion = {"responsable": "contrastar", "crisis": "compartir", "silencio": "ignorar"}[arco]
            juego = SimpleNamespace(candidatos=candidatos, historial=[{
                "publicacion": publicacion, "accion": "verificar" if accion == "contrastar" else accion,
                "accion_rol": accion, "alcance": 2 if arco == "crisis" else 0,
            }])
            antes = copy.deepcopy((juego.historial, eleccion))
            estado = estado_narrativo(juego, eleccion)
            self.assertEqual(estado["ganador"], ganador)
            self.assertEqual(estado["valeria"], arco)
            cierre = tuple(epilogo_extendido(juego, eleccion))
            cierres.add(cierre)
            self.assertTrue(set(cierre).issubset(set(FRASES_POSIBLES)))
            self.assertEqual(antes, (juego.historial, eleccion))
            if ganador == "empate":
                self.assertIn("recuento público", cierre[0][1])
                self.assertFalse(any("Recibo el encargo" in texto for _, texto in cierre))
            else:
                self.assertEqual(cierre[0][0], ganador.upper())
        self.assertEqual(len(cierres), 45)

    def test_el_cierre_de_la_primera_ola_no_adelanta_las_urnas(self):
        juego = Juego(704, eventos=False, campana="extendida")
        juego.iniciar_primera_publicacion()
        while juego.obtener_publicacion_actual().id != 80:
            juego.ejecutar_accion("ignorar")
            juego.avanzar_publicacion()
        lineas = dialogos_extendidos(juego)
        self.assertIn("influencer", lineas[-1][1])
        self.assertNotIn("última decisión", " ".join(texto for _, texto in lineas))
        self.assertFalse(juego.finalizada)
        for identificador in DIALOGOS_NUEVOS:
            self.assertEqual(DIALOGOS_NUEVOS[identificador][0][0], "NARRADOR")
            self.assertEqual(len(CASOS_NUEVOS[identificador]["pistas"]), 3)


if __name__ == "__main__":
    unittest.main()
