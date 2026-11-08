"""Demostración de las mismas estructuras y reglas que utiliza la interfaz.

Ejecutar desde la raíz: python -B -m ejemplos.demo_integracion
No abre ventanas ni modifica archivos.
"""
import json

from juego.partida import Juego


def comprobar(condicion, mensaje):
    if not condicion:
        raise AssertionError(mensaje)


def forma(nodo):
    if nodo is None:
        return None
    return nodo.publicacion.id, forma(nodo.izquierda), forma(nodo.derecha)


def copia_json(juego):
    return Juego.desde_datos(json.loads(json.dumps(juego.datos())))


def demostrar():
    juego = Juego(semilla=4, eventos=False)
    comprobar(juego.arbol.raiz is None, "El ABB debe comenzar vacío")
    comprobar(juego.iniciar_primera_publicacion(), "Falló la inserción inicial")
    comprobar(juego.arbol.buscar(50) is juego.obtener_publicacion_actual(),
              "La publicación debe provenir del ABB")
    print("1. Juego inserta #50 en el ABB y la recupera mediante buscar().")

    # El único cambio entre estas partidas idénticas es una arista del grafo.
    modificada = copia_json(juego)
    comprobar(modificada.grafo.eliminar_arista("ana", "luis"), "La arista debe existir")
    for partida in (juego, modificada):
        comprobar(partida.ejecutar_accion("compartir"), "Falló compartir")
    comprobar(juego.ultima_propagacion.receptores == ["luis", "pedro", "maria"],
              "La difusión debe corresponder al BFS real")
    comprobar(modificada.ultima_propagacion.receptores == ["pedro", "maria"],
              "Eliminar una arista debe cambiar los receptores")
    comprobar((juego.desinformacion, juego.jugador.puntos) == (9, -6),
              "Las consecuencias deben usar el alcance inicial")
    comprobar((modificada.desinformacion, modificada.jugador.puntos) == (6, -4),
              "Las consecuencias deben usar el alcance reducido")
    comprobar(juego.resultado_electoral()["apoyos"] !=
              modificada.resultado_electoral()["apoyos"],
              "El alcance debe influir en la elección")
    print("2. Compartir: ABB.buscar -> Grafo.bfs -> consecuencias -> elección.")
    print("   Red original: 3 receptores, desinformación 9, puntos -6.")
    print("   Sin ana -> luis: 2 receptores, desinformación 6, puntos -4.")

    while juego.avanzar_publicacion():
        comprobar(juego.ejecutar_accion("ignorar"), "Falló avanzar la campaña")
    esperados = {
        "inorden": [20, 30, 50, 60, 70, 80],
        "preorden": [50, 30, 20, 70, 60, 80],
        "postorden": [20, 30, 60, 80, 70, 50],
    }
    print("3. Recorridos del ABB construido por la campaña:")
    for metodo, esperado in esperados.items():
        resultado = [p.id for p in getattr(juego.arbol, metodo)()]
        comprobar(resultado == esperado, "Recorrido incorrecto: " + metodo)
        print("  ", metodo, resultado)

    antes = json.dumps(juego.datos(), sort_keys=True)
    bfs, dfs = juego.grafo.bfs("ana"), juego.grafo.dfs("ana")
    comprobar(set(bfs.orden) == set(dfs), "BFS y DFS deben alcanzar los mismos nodos")
    comprobar(juego.grafo.camino_minimo("ana", "maria") == ["ana", "luis", "maria"],
              "Camino mínimo incorrecto")
    comprobar(len(bfs.orden) == len(set(bfs.orden)), "BFS repitió ciudadanos")
    comprobar(json.dumps(juego.datos(), sort_keys=True) == antes,
              "Explorar el grafo no debe aplicar otra decisión")
    print("4. BFS:", bfs.orden)
    print("   DFS:", dfs)
    print("   Camino mínimo Ana -> María:", juego.grafo.camino_minimo("ana", "maria"))

    restaurada = copia_json(juego)
    comprobar(forma(restaurada.arbol.raiz) == forma(juego.arbol.raiz),
              "Restaurar debe conservar la forma del ABB")
    comprobar(restaurada.grafo.aristas() == juego.grafo.aristas(),
              "Restaurar debe conservar la topología")
    comprobar(json.dumps(restaurada.datos(), sort_keys=True) == antes,
              "Restaurar debe conservar el estado completo")
    print("5. JSON conserva la forma del ABB, las relaciones y el estado completo.")

    periodista = Juego(semilla=4, eventos=False)
    periodista.seleccionar_rol("periodista")
    comprobar(periodista.iniciar_primera_publicacion(), "Falló iniciar Periodista")
    conexiones = periodista.grafo.aristas()
    comprobar(periodista.ejecutar_accion("desmentir"), "Falló desmentir")
    comprobar(periodista.arbol.buscar(50) is None, "El rumor debe salir del ABB")
    comprobar(periodista.grafo.aristas() == conexiones,
              "Retirar contenido no debe borrar personas ni relaciones")
    retirada = copia_json(periodista)
    try:
        retirada.propagacion.simular(50, "ana")
    except ValueError:
        pass
    else:
        raise AssertionError("Una publicación retirada no debe volver a circular")
    comprobar(retirada.historial[-1]["eliminada"], "Debe conservarse el retiro")
    print("6. Desmentir retira #50 del ABB; incluso tras restaurar no puede circular.")
    print("Todas las comprobaciones fueron correctas; no se escribieron archivos.")


if __name__ == "__main__":
    demostrar()
