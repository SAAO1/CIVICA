def epilogo(juego, eleccion):
    difundidas = [r for r in juego.historial if r["accion"] == "compartir" and r["publicacion"]["verdadera"] is False]
    afectados = {id for r in difundidas if r["propagacion"] for id in r["propagacion"]["receptores"]}
    verificaciones = sum(r["accion"] == "verificar" for r in juego.historial)
    if eleccion["empate"]:
        cierre = "Ciudad Nova termina con un empate. El recuento será público y los candidatos deberán acordar un proceso transparente."
    else:
        ganador = next(c for c in juego.candidatos if c.nombre == eleccion["ganadores"][0])
        cierre = f"{ganador.nombre} recibe el encargo de gobernar Ciudad Nova con su propuesta de {ganador.propuesta.lower()}."
    if eleccion["calidad"] >= 50:
        reaccion = "En el Café Central, la periodista publica el balance de la campaña. La ciudad conserva espacios para conversar y contrastar sus diferencias."
    else:
        reaccion = "En el Café Central, la periodista encuentra vecinos distanciados por los rumores. La elección termina, pero recuperar la confianza será el siguiente trabajo de la ciudad."
    evidencia = (f"Las decisiones llevaron información falsa a {len(afectados)} ciudadanos distintos. "
                 f"Se realizaron {verificaciones} verificaciones y se retiraron {len(juego.publicaciones_eliminadas)} publicaciones dañinas.")
    return cierre + "\n\n" + reaccion + "\n\n" + evidencia
