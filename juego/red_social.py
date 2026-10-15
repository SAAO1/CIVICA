from estructuras.grafo import Grafo
from models.ciudadano import Ciudadano


def crear_red_social():
    grafo = Grafo()
    for id, nombre in (("ana", "Ana"), ("luis", "Luis"), ("pedro", "Pedro"),
                       ("maria", "María"), ("carlos", "Carlos"), ("sofia", "Sofía"),
                       ("elena", "Elena"), ("diego", "Diego"), ("ines", "Inés")):
        avatar = "assets/UI/avatar_janghaein.png" if id == "maria" else "assets/UI/avatar_unknown.png"
        grafo.agregar_vertice(Ciudadano(id, nombre, avatar=avatar))
    for a, b in (("ana", "luis"), ("ana", "pedro"), ("luis", "maria"),
                 ("pedro", "maria"), ("maria", "carlos"), ("carlos", "ana"),
                 ("carlos", "sofia"), ("sofia", "elena"), ("elena", "diego")):
        grafo.agregar_arista(a, b)
    return grafo


def ampliar_comunidad(grafo, etapa):
    """Dos vecinos por nueva publicación, con relaciones reales y reproducibles.

    El crecimiento no consume el azar de los eventos ni se ejecuta al renderizar.
    Los identificadores estables impiden duplicar ciudadanos al restaurar estado.
    """
    vecinos = (("lucia", "Lucía"), ("mateo", "Mateo"), ("valeria", "Valeria"),
               ("tomas", "Tomás"), ("sara", "Sara"), ("nicolas", "Nicolás"),
               ("gabriela", "Gabriela"), ("andres", "Andrés"),
               ("daniela", "Daniela"), ("samuel", "Samuel"))
    mentores = ("ana", "luis", "pedro", "maria", "carlos", "sofia", "elena", "diego", "ines")
    nuevos = []
    limite = min(len(vecinos), max(0, (etapa-1)*2))
    for i, (id, nombre) in enumerate(vecinos[:limite]):
        if grafo.existe_vertice(id):
            continue
        grafo.agregar_vertice(Ciudadano(id, nombre))
        nuevos.append(id)
        for origen, destino in ((mentores[i % len(mentores)], id),
                                (id, mentores[(i+3) % len(mentores)])):
            if grafo.existe_vertice(origen) and grafo.existe_vertice(destino):
                grafo.agregar_arista(origen, destino)
        if i and grafo.existe_vertice(vecinos[i-1][0]):
            grafo.agregar_arista(vecinos[i-1][0], id)
    return nuevos
