"""Árbol binario de búsqueda propio para el índice de publicaciones activas.

Cada Nodo enlaza una publicación con sus hijos izquierdo y derecho. La llave
es publicacion.id: izquierda < nodo < derecha. No usa un diccionario como
sustituto del árbol. Operaciones O(h); recorridos O(n), con h hasta n porque
este ABB no se autoequilibra.
"""
from estructuras.nodo import Nodo


class ArbolPublicaciones:
    """Índice activo que consulta Juego y exige ServicioPropagacion."""

    def __init__(self):
        self.raiz = None

    def insertar(self, publicacion):
        """Inserta por ID; un duplicado conserva el objeto original."""
        if self.raiz is None:
            self.raiz = Nodo(publicacion)
            return
        actual = self.raiz
        while True:
            if publicacion.id == actual.publicacion.id:
                return
            if publicacion.id < actual.publicacion.id:
                if actual.izquierda is None:
                    actual.izquierda = Nodo(publicacion)
                    return
                actual = actual.izquierda
            else:
                if actual.derecha is None:
                    actual.derecha = Nodo(publicacion)
                    return
                actual = actual.derecha

    def buscar(self, id):
        """Desciende por comparaciones hasta hallar la publicación o None."""
        actual = self.raiz
        while actual is not None:
            if id == actual.publicacion.id:
                return actual.publicacion
            if id < actual.publicacion.id:
                actual = actual.izquierda
            else:
                actual = actual.derecha
        return None

    def eliminar(self, id):
        """Retira el ID; una llave ausente no modifica el árbol."""
        self.raiz = self._eliminar_recursivo(self.raiz, id)

    def _eliminar_recursivo(self, nodo, id):
        if nodo is None:
            return None
        if id < nodo.publicacion.id:
            nodo.izquierda = self._eliminar_recursivo(nodo.izquierda, id)
        elif id > nodo.publicacion.id:
            nodo.derecha = self._eliminar_recursivo(nodo.derecha, id)
        else:
            # Hoja o un solo hijo: el hijo existente reemplaza al nodo.
            if nodo.izquierda is None:
                return nodo.derecha
            if nodo.derecha is None:
                return nodo.izquierda
            # Dos hijos: reemplazo por el sucesor (mínimo del subárbol derecho).
            sucesor = self._encontrar_minimo(nodo.derecha)
            nodo.publicacion = sucesor.publicacion
            nodo.derecha = self._eliminar_recursivo(nodo.derecha, sucesor.publicacion.id)
        return nodo

    def _encontrar_minimo(self, nodo):
        while nodo.izquierda is not None:
            nodo = nodo.izquierda
        return nodo

    def inorden(self):
        """Izquierda, nodo, derecha: publicaciones en orden ascendente de ID."""
        resultado = []
        self._inorden_recursivo(self.raiz, resultado)
        return resultado

    def _inorden_recursivo(self, nodo, resultado):
        if nodo is not None:
            self._inorden_recursivo(nodo.izquierda, resultado)
            resultado.append(nodo.publicacion)
            self._inorden_recursivo(nodo.derecha, resultado)

    def preorden(self):
        """Nodo, izquierda, derecha: permite reconstruir la forma al cargar."""
        resultado = []
        self._preorden_recursivo(self.raiz, resultado)
        return resultado

    def _preorden_recursivo(self, nodo, resultado):
        if nodo is not None:
            resultado.append(nodo.publicacion)
            self._preorden_recursivo(nodo.izquierda, resultado)
            self._preorden_recursivo(nodo.derecha, resultado)

    def postorden(self):
        """Izquierda, derecha, nodo: visita los hijos antes que su padre."""
        resultado = []
        self._postorden_recursivo(self.raiz, resultado)
        return resultado

    def _postorden_recursivo(self, nodo, resultado):
        if nodo is not None:
            self._postorden_recursivo(nodo.izquierda, resultado)
            self._postorden_recursivo(nodo.derecha, resultado)
            resultado.append(nodo.publicacion)
