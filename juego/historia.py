def contenido_resultado(juego, tipo):
    registro = juego.ultimo_registro
    if not registro:
        return "Todavía no se ha tomado una decisión.", "NARRADOR"
    p, accion = registro["publicacion"], registro["accion"]
    if tipo == 1:
        return registro["explicacion"], "PERIODISTA" if accion == "verificar" else "CIUDADANO"
    if tipo == 2:
        if accion == "verificar":
            veredicto = "verdadera" if p["verdadera"] else "falsa"
            if p["verdadera"] is None:
                veredicto = "una opinión, que debemos distinguir de un hecho comprobado"
            return f"La publicación #{p['id']} es {veredicto}. Las fuentes y el contexto importan.", "PERIODISTA"
        if registro["propagacion"]:
            r = registro["propagacion"]
            return f"La publicación llegó a {registro['alcance']} ciudadanos en {r['tiempo_simulado']:g} unidades simuladas. El observatorio de Civitas permite seguir su recorrido.", "NARRADOR"
        return ("El contenido fue retirado. Su historial se conserva y la red social permanece intacta."
                if registro["eliminada"] else "Esta decisión no inició una difusión. Verificar sigue siendo importante antes de compartir."), "NARRADOR"
    cambios = [f"{nombre.replace('_', ' ')} {registro['despues'][nombre]-valor:+g}"
               for nombre, valor in registro["antes"].items() if registro["despues"][nombre] != valor]
    return ("Ciudad Nova refleja tu decisión: " + (", ".join(cambios) or "sin cambios en los indicadores")
            + f". Puntuación de la acción: {registro['puntos']:+d}."), "NARRADOR"


def dialogos_publicacion(juego):
    publicacion = juego.obtener_publicacion_actual()
    if publicacion is None:
        return [("NARRADOR", "La campaña ya no tiene publicaciones pendientes.")]
    contexto = {
        50: "Una afirmación sobre el colegio puede preocupar a muchas familias. Busquemos el comunicado original antes de actuar.",
        30: "Una propuesta merece una lectura completa: su autor, su fecha y lo que realmente promete.",
        70: "La información del parque puede ser útil. Comprobar los horarios evita confundir a los vecinos.",
        20: "La biblioteca ilusiona al barrio. Una fuente oficial nos ayudará a distinguir el proyecto de una promesa sin respaldo.",
        60: "Este mensaje acusa sin explicar de dónde salió la información. Difundirlo puede dañar a personas de la ciudad.",
        80: "Una encuesta necesita fecha, muestra y método. Un titular por sí solo no permite saber quién ganará.",
    }
    conversacion = [
        ("CIUDADANO", f'Mira esto. "{publicacion.texto}"'),
        ("PERIODISTA", contexto.get(publicacion.id, "Revisemos las fuentes y el contexto antes de compartir.")),
        ("CIUDADANO", "Entonces tenemos que decidir qué hacer antes de que más personas la vean."),
    ]
    if juego.conflictos >= 8:
        conversacion.append(("PERIODISTA", "La tensión está creciendo. Una corrección a tiempo puede evitar que más vecinos se enfrenten."))
    elif juego.info_verificada >= 15:
        conversacion.append(("PERIODISTA", "Las verificaciones anteriores están ayudando. Mantengamos ese cuidado con cada nueva publicación."))
    return conversacion
