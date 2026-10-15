from collections import deque
from dataclasses import dataclass
from estructuras.nodo_grafo import NodoGrafo


@dataclass
class Recorrido:
    orden: list[str]
    distancias: dict[str, int]
    padres: dict[str, str | None]
    niveles: list[list[str]]
    aristas: list[tuple[str, str]]


class Grafo:
    """A -> B permite difundir de A hacia B; orden estable, sin bucles.

    Duplicados devuelven False; referencias inexistentes generan KeyError.
    """

    def __init__(self):
        self.nodos = {}
        self.adyacencia = {}

    def agregar_vertice(self, nodo, nombre=None):
        if isinstance(nodo, str):
            nodo = NodoGrafo(nodo, nombre or nodo)
        if not isinstance(nodo, NodoGrafo) or not nodo.id:
            raise ValueError("El ciudadano necesita un identificador estable")
        if nodo.id in self.nodos:
            return False
        self.nodos[nodo.id] = nodo
        self.adyacencia[nodo.id] = {}
        return True

    def existe_vertice(self, id):
        return id in self.nodos

    def _comprobar(self, id):
        if id not in self.nodos:
            raise KeyError(f"Ciudadano inexistente: {id}")

    def eliminar_vertice(self, id):
        self._comprobar(id)
        del self.nodos[id]
        del self.adyacencia[id]
        for vecinos in self.adyacencia.values():
            vecinos.pop(id, None)

    def agregar_arista(self, origen, destino):
        self._comprobar(origen)
        self._comprobar(destino)
        if origen == destino:
            raise ValueError("No se permiten conexiones consigo mismo")
        if destino in self.adyacencia[origen]:
            return False
        self.adyacencia[origen][destino] = None
        return True

    def eliminar_arista(self, origen, destino):
        self._comprobar(origen)
        self._comprobar(destino)
        if destino not in self.adyacencia[origen]:
            return False
        del self.adyacencia[origen][destino]
        return True

    def existe_arista(self, origen, destino):
        return destino in self.adyacencia.get(origen, {})

    def vecinos(self, id):
        self._comprobar(id)
        return list(self.adyacencia[id])

    def vertices(self):
        return list(self.nodos)

    def aristas(self):
        return [(a, b) for a, vecinos in self.adyacencia.items() for b in vecinos]

    def grado_salida(self, id):
        self._comprobar(id)
        return len(self.adyacencia[id])

    def grado_entrada(self, id):
        self._comprobar(id)
        return sum(id in vecinos for vecinos in self.adyacencia.values())

    def cantidad_vertices(self):
        return len(self.nodos)

    def cantidad_aristas(self):
        return sum(len(vecinos) for vecinos in self.adyacencia.values())

    def bfs(self, origen, profundidad=None):
        self._comprobar(origen)
        if profundidad is not None and (not isinstance(profundidad, int) or profundidad < 0):
            raise ValueError("La profundidad debe ser un entero no negativo")
        cola = deque([origen])
        distancias, padres = {origen: 0}, {origen: None}
        orden, niveles, aristas = [], [], []
        while cola:
            actual = cola.popleft()
            nivel = distancias[actual]
            orden.append(actual)
            if len(niveles) <= nivel:
                niveles.append([])
            niveles[nivel].append(actual)
            if profundidad is not None and nivel >= profundidad:
                continue
            for vecino in self.adyacencia[actual]:
                if vecino not in distancias:
                    distancias[vecino] = nivel + 1
                    padres[vecino] = actual
                    aristas.append((actual, vecino))
                    cola.append(vecino)
        return Recorrido(orden, distancias, padres, niveles, aristas)

    def dfs(self, origen):
        self._comprobar(origen)
        pila, visitados, orden = [origen], set(), []
        while pila:
            actual = pila.pop()
            if actual in visitados:
                continue
            visitados.add(actual)
            orden.append(actual)
            pila.extend(reversed(list(self.adyacencia[actual])))
        return orden

    def alcanzables(self, origen):
        return set(self.bfs(origen).orden)

    def es_alcanzable(self, origen, destino):
        self._comprobar(destino)
        return destino in self.bfs(origen).distancias

    def camino_minimo(self, origen, destino):
        self._comprobar(destino)
        recorrido = self.bfs(origen)
        if destino not in recorrido.padres:
            return []
        camino = []
        while destino is not None:
            camino.append(destino)
            destino = recorrido.padres[destino]
        return camino[::-1]

    def componentes_debiles(self):
        vecinos = {v: set(self.vecinos(v)) for v in self.vertices()}
        for a, b in self.aristas():
            vecinos[b].add(a)
        pendientes, resultado = set(self.vertices()), []
        for inicio in self.vertices():
            if inicio not in pendientes:
                continue
            componente, pila = set(), [inicio]
            while pila:
                actual = pila.pop()
                if actual in componente:
                    continue
                componente.add(actual)
                pila.extend(vecinos[actual] - componente)
            pendientes -= componente
            resultado.append(componente)
        return resultado
