from models.publicacion import Publicacion
from estructuras.bst import ArbolPublicaciones


def mostrar_lista(nombre, lista):
    print(
        f"{nombre}:",
        " -> ".join(
            f"#{p.id}"
            for p in lista
        )
    )


print("=" * 50)
print("PRUEBA DEL ÁRBOL BINARIO DE BÚSQUEDA")
print("=" * 50)


# ============================================================
# 1. CREAR ÁRBOL
# ============================================================

arbol = ArbolPublicaciones()


# ============================================================
# 2. CREAR PUBLICACIONES
# ============================================================

publicaciones = [

    Publicacion(
        50,
        "Publicación principal",
        True,
        5
    ),

    Publicacion(
        30,
        "Publicación izquierda",
        True,
        4
    ),

    Publicacion(
        70,
        "Publicación derecha",
        False,
        6
    ),

    Publicacion(
        20,
        "Publicación izquierda izquierda",
        True,
        2
    ),

    Publicacion(
        40,
        "Publicación izquierda derecha",
        True,
        3
    ),

    Publicacion(
        60,
        "Publicación derecha izquierda",
        False,
        7
    ),

    Publicacion(
        80,
        "Publicación derecha derecha",
        False,
        8
    ),
]


# ============================================================
# 3. INSERTAR
# ============================================================

print("\n[1] INSERTANDO PUBLICACIONES...")

for publicacion in publicaciones:

    arbol.insertar(
        publicacion
    )

print("Publicaciones insertadas correctamente.")


# ============================================================
# 4. MOSTRAR RECORRIDOS
# ============================================================

print("\n[2] RECORRIDOS INICIALES")

mostrar_lista(
    "Inorden",
    arbol.inorden()
)

mostrar_lista(
    "Preorden",
    arbol.preorden()
)

mostrar_lista(
    "Postorden",
    arbol.postorden()
)


# ============================================================
# 5. BUSCAR
# ============================================================

print("\n[3] PRUEBA DE BÚSQUEDA")

buscada = arbol.buscar(40)

if buscada is not None:

    print(
        f"Encontrada publicación #{buscada.id}:"
    )

    print(
        f"Texto: {buscada.texto}"
    )

else:

    print(
        "ERROR: no se encontró la publicación #40"
    )


buscada = arbol.buscar(999)

if buscada is None:

    print(
        "Correcto: la publicación #999 no existe."
    )

else:

    print(
        "ERROR: se encontró una publicación que no existe."
    )


# ============================================================
# 6. ELIMINAR HOJA
# ============================================================

print("\n[4] ELIMINAR NODO HOJA")

print("Eliminando #20...")

arbol.eliminar(20)

mostrar_lista(
    "Inorden después de eliminar #20",
    arbol.inorden()
)


# ============================================================
# 7. ELIMINAR NODO CON UN HIJO
# ============================================================

print("\n[5] ELIMINAR NODO CON UN HIJO")

print("Primero eliminaremos #60 para preparar el ejemplo.")

arbol.eliminar(60)

print("Ahora #70 queda con un solo hijo (#80).")

print("Eliminando #70...")

arbol.eliminar(70)

mostrar_lista(
    "Inorden después de eliminar #70",
    arbol.inorden()
)


# ============================================================
# 8. ELIMINAR NODO CON DOS HIJOS
# ============================================================

print("\n[6] ELIMINAR NODO CON DOS HIJOS")

print("Eliminando #30...")

arbol.eliminar(30)

mostrar_lista(
    "Inorden después de eliminar #30",
    arbol.inorden()
)


# ============================================================
# 9. MOSTRAR RECORRIDOS FINALES
# ============================================================

print("\n[7] RECORRIDOS FINALES")

mostrar_lista(
    "Inorden",
    arbol.inorden()
)

mostrar_lista(
    "Preorden",
    arbol.preorden()
)

mostrar_lista(
    "Postorden",
    arbol.postorden()
)


# ============================================================
# 10. MOSTRAR ÁRBOL FINAL
# ============================================================

print("\n[8] ESTRUCTURA FINAL")

if arbol.raiz is not None:

    print(
        f"Raíz: #{arbol.raiz.publicacion.id}"
    )

    if arbol.raiz.izquierda is not None:

        print(
            f"Izquierda: "
            f"#{arbol.raiz.izquierda.publicacion.id}"
        )

    else:

        print(
            "Izquierda: VACÍO"
        )

    if arbol.raiz.derecha is not None:

        print(
            f"Derecha: "
            f"#{arbol.raiz.derecha.publicacion.id}"
        )

    else:

        print(
            "Derecha: VACÍO"
        )

else:

    print(
        "El árbol está vacío."
    )


print("\n" + "=" * 50)
print("PRUEBA TERMINADA")
print("=" * 50)