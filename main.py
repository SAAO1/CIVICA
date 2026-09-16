from models.publicacion import Publicacion
from estructuras.bst import ArbolPublicaciones


arbol = ArbolPublicaciones()


publicacion1 = Publicacion(
    50,
    "El colegio sera cerrado manana",
    False,
    7
)

publicacion2 = Publicacion(
    30,
    "Adrian presento una propuesta",
    True,
    4
)

publicacion3 = Publicacion(
    70,
    "El parque tendra mantenimiento",
    True,
    3
)

publicacion4 = Publicacion(
    20,
    "Habra una nueva biblioteca",
    True,
    2
)


arbol.insertar(publicacion1)
arbol.insertar(publicacion2)
arbol.insertar(publicacion3)
arbol.insertar(publicacion4)


print("Arbol creado correctamente")

print("Raiz:", arbol.raiz.publicacion.id)

print(
    "Izquierda:",
    arbol.raiz.izquierda.publicacion.id
)

print(
    "Derecha:",
    arbol.raiz.derecha.publicacion.id
)


resultado = arbol.buscar(30)

if resultado is not None:
    print("Publicacion encontrada:")
    print(resultado.texto)
else:
    print("Publicacion no encontrada")

    print("\nINORDEN")

for publicacion in arbol.inorden():
    print(
        publicacion.id,
        "-",
        publicacion.texto
    )


print("\nPREORDEN")

for publicacion in arbol.preorden():
    print(
        publicacion.id,
        "-",
        publicacion.texto
    )


print("\nPOSTORDEN")

for publicacion in arbol.postorden():
    print(
        publicacion.id,
        "-",
        publicacion.texto
    )

    print("\n--- ELIMINANDO PUBLICACION #20 ---")

arbol.eliminar(20)


print("INORDEN DESPUES DE ELIMINAR:")

for publicacion in arbol.inorden():
    print(
        publicacion.id,
        "-",
        publicacion.texto
    )