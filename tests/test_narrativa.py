"""El relato reconoce decisiones reales sin modificar el estado de la partida."""
import json
import unittest

from juego.finales import epilogo
from juego.historia import contenido_resultado, dialogos_publicacion
from juego.partida import Juego
from models.jugador import Jugador
from models.publicacion import Publicacion


def congelar(juego):
    return json.dumps(juego.datos(), ensure_ascii=False, sort_keys=True)


def crear_campana(acciones):
    juego = Juego(4, eventos=False)
    juego.iniciar_primera_publicacion()
    for accion in acciones:
        juego.ejecutar_accion(accion)
        juego.avanzar_publicacion()
    return juego


class PruebasNarrativa(unittest.TestCase):
    def test_seis_escenas_distintas_y_reacciones_para_cada_decision(self):
        aperturas = set()
        for accion in ("compartir", "verificar", "reportar", "ignorar"):
            juego = Juego(4, eventos=False)
            juego.iniciar_primera_publicacion()
            reacciones = set()
            for identificador in (50, 30, 70, 20, 60, 80):
                with self.subTest(accion=accion, publicacion=identificador):
                    self.assertEqual(juego.obtener_publicacion_actual().id, identificador)
                    dialogos = dialogos_publicacion(juego)
                    aperturas.add(dialogos[0][1])
                    self.assertGreaterEqual(len(dialogos), 4)
                    self.assertTrue(all(nombre in ("CIUDADANO", "PERIODISTA", "NARRADOR")
                                        and texto.strip() for nombre, texto in dialogos))
                    self.assertTrue(juego.ejecutar_accion(accion))
                    reacciones.add(contenido_resultado(juego, 1)[0])
                    juego.avanzar_publicacion()
            self.assertEqual(len(reacciones), 6)
            self.assertTrue(juego.finalizada)
        self.assertEqual(len(aperturas), 6)

    def test_publicacion_siguiente_recuerda_la_accion_del_colegio(self):
        versiones = []
        for accion in ("compartir", "verificar", "reportar", "ignorar"):
            juego = crear_campana([accion])
            versiones.append(dialogos_publicacion(juego)[1][1])
        self.assertEqual(len(set(versiones)), 4)
        self.assertTrue(all("colegio" in texto for texto in versiones))

    def test_correccion_y_rumor_tienen_receptores_y_tiempos_exactos(self):
        for accion, sujeto in (("compartir", "La publicación"), ("verificar", "La corrección")):
            with self.subTest(accion=accion):
                juego = Juego(4, eventos=False)
                juego.iniciar_primera_publicacion()
                juego.ejecutar_accion(accion)
                registro = juego.ultimo_registro
                texto, _ = contenido_resultado(juego, 2)
                self.assertIn(f"{sujeto} llegó a {registro['alcance']} ciudadanos", texto)
                tiempo = registro["propagacion"]["tiempo_simulado"]
                self.assertIn(f"{tiempo:g} unidades simuladas", texto)
                if accion == "compartir":
                    receptor = juego.grafo.nodos[registro["propagacion"]["receptores"][0]].nombre
                    self.assertIn(receptor, texto)

    def test_aislado_no_genera_receptores_ficticios(self):
        juego = Juego(4, eventos=False)
        juego.jugador.ciudadano_id = "ines"
        juego.iniciar_primera_publicacion()
        juego.ejecutar_accion("compartir")
        reaccion, _ = contenido_resultado(juego, 1)
        texto, _ = contenido_resultado(juego, 2)
        self.assertIn("no alcanzó", reaccion)
        self.assertIn("0 receptores", texto)
        self.assertNotIn("está entre sus receptores", texto)

    def test_verificar_opinion_no_la_presenta_como_hecho_o_correccion(self):
        juego = Juego(4, eventos=False)
        juego.agregar_publicacion(Publicacion(99, "Prefiero las plazas pequeñas.", None, 1))
        juego.ejecutar_accion("verificar")
        texto, _ = contenido_resultado(juego, 2)
        self.assertIn("opinión", texto)
        self.assertIn("no inició una difusión", texto)
        self.assertNotIn("desmiente", texto)
        self.assertNotIn("confirma", texto)

    def test_retiro_y_reporte_rechazado_no_se_confunden(self):
        retirado = Juego(4, eventos=False)
        retirado.iniciar_primera_publicacion()
        retirado.ejecutar_accion("reportar")
        self.assertIn("retirado del ABB", contenido_resultado(retirado, 2)[0])
        rechazado = crear_campana(["ignorar"])
        rechazado.ejecutar_accion("reportar")
        texto, _ = contenido_resultado(rechazado, 2)
        self.assertIn("rechazado", texto)
        self.assertIn("permanece en el ABB", texto)

    def test_resultado_identifica_al_participante_del_registro(self):
        juego = Juego(4, eventos=False)
        juego.jugadores = [Jugador(id="uno", nombre="Carolina"), Jugador(id="dos", nombre="Mateo")]
        juego.iniciar_primera_publicacion()
        juego.ejecutar_accion("verificar")
        juego.turno = 1
        self.assertIn("Carolina", contenido_resultado(juego, 3)[0])
        self.assertNotIn("Mateo", contenido_resultado(juego, 3)[0])

    def test_epilogos_cierran_rutas_personales_y_cuentan_afectados_unicos(self):
        cuidadoso = crear_campana(["verificar"] * 6)
        arriesgado = crear_campana(["compartir"] * 6)
        texto_cuidadoso = epilogo(cuidadoso, cuidadoso.resultado_electoral())
        texto_arriesgado = epilogo(arriesgado, arriesgado.resultado_electoral())
        self.assertIn("seguir contrastando juntos", texto_cuidadoso)
        self.assertIn("prepara una rectificación", texto_arriesgado)
        afectados = {receptor for registro in arriesgado.historial
                     if registro["publicacion"]["verdadera"] is False
                     for receptor in registro["propagacion"]["receptores"]}
        self.assertIn(f"falsa a {len(afectados)} ciudadanos distintos", texto_arriesgado)
        self.assertIn("6 verificaciones", texto_cuidadoso)
        self.assertNotEqual(texto_cuidadoso, texto_arriesgado)

    def test_presentacion_es_pura_y_coincide_despues_de_restaurar(self):
        juego = crear_campana(["compartir", "verificar", "ignorar"])
        copia = Juego.desde_datos(juego.datos())
        antes = congelar(juego)
        copia_antes = congelar(copia)
        for _ in range(3):
            self.assertEqual(dialogos_publicacion(juego), dialogos_publicacion(copia))
            for tipo in (1, 2, 3):
                self.assertEqual(contenido_resultado(juego, tipo), contenido_resultado(copia, tipo))
            self.assertEqual(epilogo(juego, juego.resultado_electoral()),
                             epilogo(copia, copia.resultado_electoral()))
        self.assertEqual(congelar(juego), antes)
        self.assertEqual(congelar(copia), copia_antes)

    def test_inicio_y_cierre_sin_publicacion_pendiente(self):
        juego = Juego(4, eventos=False)
        self.assertIn("pendientes", dialogos_publicacion(juego)[0][1])
        self.assertIn("Todavía", contenido_resultado(juego, 1)[0])
        self.assertIn("empate", epilogo(juego, juego.resultado_electoral()))


if __name__ == "__main__":
    unittest.main()
