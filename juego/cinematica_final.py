"""Investiduras ficticias activadas por el resultado electoral auténtico."""

CINEMATICAS_FINALES = {
    clave: {"video": f"assets/expansion/finales/{clave}.mp4",
            "poster": f"assets/expansion/finales/{clave}.jpg",
            "inicio": f"assets/expansion/finales/{clave}_inicio.png"}
    for clave in ("juan", "adrian", "laura", "camila", "recuento")
}


def clave_final(juego, eleccion):
    if eleccion["empate"]:
        return "recuento"
    return next((c.id for c in juego.candidatos
                 if c.nombre == eleccion["ganadores"][0]), None)
