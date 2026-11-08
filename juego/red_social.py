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


def ampliar_comunidad(grafo, etapa, campana="clasica"):
    """Dos vecinos por nueva publicación, con relaciones reales y reproducibles.

    El crecimiento no consume el azar de los eventos ni se ejecuta al renderizar.
    Los identificadores estables impiden duplicar ciudadanos al restaurar estado.
    """
    vecinos = (("lucia", "Lucía"), ("mateo", "Mateo"), ("valeria", "Valeria"),
               ("tomas", "Tomás"), ("sara", "Sara"), ("nicolas", "Nicolás"),
               ("gabriela", "Gabriela"), ("andres", "Andrés"),
               ("daniela", "Daniela"), ("samuel", "Samuel"))
    if campana == "extendida":
        # La Valeria de esta campaña es la influencer que conocemos en el
        # acto IV. La vecina genérica conserva una identidad diferente.
        vecinos = tuple(("violeta", "Violeta") if id == "valeria" else (id, nombre)
                        for id, nombre in vecinos)
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


def incorporar_influencer(grafo):
    """La aparición de Valeria abre conexiones concretas y persistentes.

    Su alcance viene de sus flechas en el grafo, sin bonificar una puntuación
    ni fingir receptores. Las entrevistas pueden llegar a su nodo emisor.
    """
    if grafo.existe_vertice("valeria"):
        return []
    grafo.agregar_vertice(Ciudadano(
        "valeria", "Valeria", rol="influencer",
        avatar="assets/expansion/siete_actos/personajes/influencer_neutral.png",
        zona="Estudio comunitario"))
    for destino in tuple(grafo.nodos):
        if destino != "valeria":
            grafo.agregar_arista("valeria", destino)
    for origen in ("ana", "maria", "carlos", "ines"):
        if grafo.existe_vertice(origen):
            grafo.agregar_arista(origen, "valeria")
    return ["valeria"]
