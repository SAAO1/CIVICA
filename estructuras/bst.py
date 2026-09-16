from estructuras.nodo import Nodo


class ArbolPublicaciones:
    def __init__(self):
        self.raiz = None

  

    def insertar(self, publicacion):
        nuevo = Nodo(publicacion)

      
        if self.raiz is None:
            self.raiz = nuevo
            return

        actual = self.raiz

        while True:

            if publicacion.id < actual.publicacion.id:

                if actual.izquierda is None:
                    actual.izquierda = nuevo
                    return

                actual = actual.izquierda

            elif publicacion.id > actual.publicacion.id:

                if actual.derecha is None:
                    actual.derecha = nuevo
                    return

                actual = actual.derecha

            else:
                return

   

    def buscar(self, id):
        actual = self.raiz

        while actual is not None:

            if id == actual.publicacion.id:
                return actual.publicacion

            elif id < actual.publicacion.id:
                actual = actual.izquierda

            else:
                actual = actual.derecha

        return None

   

    def eliminar(self, id):
        self.raiz = self._eliminar_recursivo(self.raiz, id)

    def _eliminar_recursivo(self, nodo, id):

        # No encontramos el nodo
        if nodo is None:
            return None

        # Buscamos hacia la izquierda
        if id < nodo.publicacion.id:

            nodo.izquierda = self._eliminar_recursivo(
                nodo.izquierda,
                id
            )

        # buscamos hacia la derecha
        elif id > nodo.publicacion.id:

            nodo.derecha = self._eliminar_recursivo(
                nodo.derecha,
                id
            )

        else:

            # Caso 1: no tiene hijos
            if nodo.izquierda is None and nodo.derecha is None:
                return None

            # Caso 2: solo tiene hijo derechoo
          
            if nodo.izquierda is None:
                return nodo.derecha

            # Caso 3: en el que tiene 2 hijos izquierdos
            if nodo.derecha is None:
                return nodo.izquierda

            # Caso 4: en el cual tiene dos hijos
            sucesor = self._encontrar_minimo(nodo.derecha)

            nodo.publicacion = sucesor.publicacion

            nodo.derecha = self._eliminar_recursivo(
                nodo.derecha,
                sucesor.publicacion.id
            )

        return nodo

    def _encontrar_minimo(self, nodo):
        actual = nodo

        while actual.izquierda is not None:
            actual = actual.izquierda

        return actual

  

    def inorden(self):
        resultado = []
        self._inorden_recursivo(self.raiz, resultado)
        return resultado

    def _inorden_recursivo(self, nodo, resultado):

        if nodo is not None:

            self._inorden_recursivo(
                nodo.izquierda,
                resultado
            )

            resultado.append(nodo.publicacion)

            self._inorden_recursivo(
                nodo.derecha,
                resultado
            )

   

    def preorden(self):
        resultado = []
        self._preorden_recursivo(self.raiz, resultado)
        return resultado

    def _preorden_recursivo(self, nodo, resultado):

        if nodo is not None:

            resultado.append(nodo.publicacion)

            self._preorden_recursivo(
                nodo.izquierda,
                resultado
            )

            self._preorden_recursivo(
                nodo.derecha,
                resultado
            )

  

    def postorden(self):
        resultado = []
        self._postorden_recursivo(self.raiz, resultado)
        return resultado

    def _postorden_recursivo(self, nodo, resultado):

        if nodo is not None:

            self._postorden_recursivo(
                nodo.izquierda,
                resultado
            )

            self._postorden_recursivo(
                nodo.derecha,
                resultado
            )

            resultado.append(nodo.publicacion)