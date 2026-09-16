class NodoPublicacion:
    def __init__(self, id_pub, texto, es_verdadera):
        self.id_pub = id_pub             
        self.texto = texto                
        self.es_verdadera = es_verdadera  
        self.izquierdo = None
        self.derecho = None

class ArbolCivitas:
    def __init__(self):
        self.raiz = None

    def insertar(self, id_pub, texto, es_verdadera):
        nuevo_nodo = NodoPublicacion(id_pub, texto, es_verdadera)
        if self.raiz is None:
            self.raiz = nuevo_nodo
            return
        
        actual = self.raiz
        while True:
            if id_pub < actual.id_pub:
                if actual.izquierdo is None:
                    actual.izquierdo = nuevo_nodo
                    break
                actual = actual.izquierdo
            elif id_pub > actual.id_pub:
                if actual.derecho is None:
                    actual.derecho = nuevo_nodo
                    break
                actual = actual.derecho
            else:
                break

    def buscar(self, id_pub):
        actual = self.raiz
        while actual is not None:
            if id_pub == actual.id_pub:
                return actual # Retorna la publicación encontrada
            elif id_pub < actual.id_pub:
                actual = actual.izquierdo
            else:
                actual = actual.derecho
        return None # No se encontró

    def eliminar(self, id_pub):
        self.raiz, eliminado = self._eliminar_nodo(self.raiz, id_pub)
        return eliminado

    def _eliminar_nodo(self, nodo, id_pub):
        if nodo is None:
            return nodo, False
        
        if id_pub < nodo.id_pub:
            nodo.izquierdo, eliminado = self._eliminar_nodo(nodo.izquierdo, id_pub)
        elif id_pub > nodo.id_pub:
            nodo.derecho, eliminado = self._eliminar_nodo(nodo.derecho, id_pub)
        else:
            if nodo.izquierdo is None:
                return nodo.derecho, True
            elif nodo.derecho is None:
                return nodo.izquierdo, True
            
            sucesor = self._encontrar_minimo(nodo.derecho)
            nodo.id_pub = sucesor.id_pub
            nodo.texto = sucesor.texto
            nodo.es_verdadera = sucesor.es_verdadera
            
            nodo.derecho, _ = self._eliminar_nodo(nodo.derecho, sucesor.id_pub)
            eliminado = True
            
        return nodo, eliminado

    def _encontrar_minimo(self, nodo):
        actual = nodo
        while actual.izquierdo is not None:
            actual = actual.izquierdo
        return actual

    def recorrido_inorden(self):
        publicaciones = []
        pila = []
        actual = self.raiz

        while actual is not None or len(pila) > 0:
            while actual is not None:
                pila.append(actual)
                actual = actual.izquierdo
            
            actual = pila.pop()
            estado = "Verdadera" if actual.es_verdadera else "Falsa"
            publicaciones.append(f"ID: {actual.id_pub} | {actual.texto} ({estado})")
            actual = actual.derecho
            
        return publicaciones