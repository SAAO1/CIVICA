"""Desenlace electoral y arcos personales a partir de decisiones conservadas."""


def _cierre_colegio(historial):
    registro = next((r for r in historial if r["publicacion"]["id"] == 50), None)
    if registro is None:
        return "El ciudadano guarda el teléfono. La conversación sobre el colegio todavía está por comenzar."
    accion = registro["accion"]
    metodo = registro.get("accion_rol", accion)
    if metodo == "conversar":
        return "El ciudadano recuerda la conversación con el vecindario sobre el colegio. Conservar ese vínculo le importa más que ser el primero en reenviar un mensaje."
    if metodo == "entrevistar":
        return "La periodista conserva el contacto de la fuente del colegio. Su testimonio sigue separado de lo que todavía debe comprobarse."
    if metodo == "reservar":
        return "La periodista deja el mensaje del colegio pendiente de pruebas. El ciudadano sabe que una duda guardada todavía necesita una respuesta."
    if accion == "compartir" and registro["alcance"]:
        return "El ciudadano vuelve al mensaje del colegio y prepara una rectificación para quienes lo recibieron. Quiere hablar con su hermana antes de publicar otra vez."
    if accion == "verificar":
        return "El ciudadano conserva la revisión del mensaje del colegio para hablar con su hermana. Aprendió a acompañar su preocupación con preguntas."
    if accion == "reportar" and registro["eliminada"]:
        return "El ciudadano ya no encuentra el rumor del colegio en Civitas. Decide hablar con su hermana: retirar un mensaje no reemplaza escuchar a quien tuvo miedo."
    return "El ciudadano vuelve a la pregunta de su hermana sobre el colegio. La campaña termina, pero esa conversación sigue pendiente."


def _cierre_periodista(historial):
    verificaciones = sum(r["accion"] == "verificar" for r in historial)
    rumores = sum(r["accion"] == "compartir" and r["publicacion"]["verdadera"] is False
                  and r["alcance"] > 0 for r in historial)
    entrevistas = sum(r.get("accion_rol") == "entrevistar" for r in historial)
    rectificaciones = sum(r.get("accion_rol") == "desmentir" and r.get("eliminada") for r in historial)
    if rectificaciones and not rumores:
        return "La periodista revisa las rectificaciones publicadas y sus destinatarios. El ciudadano conserva los contactos del barrio para que las correcciones no se queden dentro de la redacción."
    if entrevistas and not verificaciones:
        return "La periodista guarda las entrevistas como testimonios, sin presentarlos como hechos comprobados. El ciudadano le propone volver a escuchar a las fuentes después de la elección."
    if verificaciones >= 3 and not rumores:
        return "La periodista deja la libreta junto al teléfono: las revisiones serán el punto de partida de su próximo reportaje. El ciudadano propone seguir contrastando juntos después de las elecciones."
    if verificaciones and rumores:
        return "La periodista abre dos páginas: errores y correcciones. El ciudadano le pide conservar ambas; quieren recordar las decisiones que deberán explicar, además de los aciertos."
    if rumores:
        return "La periodista cierra el borrador sin publicarlo. El ciudadano vuelve a leer sus mensajes: recuperar la confianza exigirá responder por ellos, una conversación a la vez."
    return "La periodista deja una página en blanco para las preguntas que no contestaron. El ciudadano acerca una silla: todavía pueden empezar por escuchar."


def epilogo(juego, eleccion):
    if getattr(juego, "campana", "clasica") == "extendida":
        from juego.campana_extendida import texto_epilogo_extendido
        return texto_epilogo_extendido(juego, eleccion)
    difundidas = [r for r in juego.historial if r["accion"] == "compartir" and r["publicacion"]["verdadera"] is False]
    afectados = {id for r in difundidas if r.get("propagacion") for id in r["propagacion"]["receptores"]}
    verificaciones = sum(r["accion"] == "verificar" for r in juego.historial)
    if eleccion["empate"]:
        cierre = "Ciudad Nova termina con un empate. El recuento será público y los candidatos deberán acordar un proceso transparente."
    else:
        ganador = next(c for c in juego.candidatos if c.nombre == eleccion["ganadores"][0])
        cierre = f"{ganador.nombre} recibe el encargo de gobernar Ciudad Nova con su propuesta de {ganador.propuesta.lower()}."
    if eleccion["calidad"] >= 50:
        reaccion = "En el Café Central quedan voces distintas alrededor de la mesa. La ciudad conserva espacios para conversar y contrastar sus diferencias."
    else:
        reaccion = "En el Café Central quedan sillas vacías entre algunos vecinos. La elección termina, pero recuperar la confianza será el siguiente trabajo de la ciudad."
    evidencia = (f"Las decisiones llevaron información falsa a {len(afectados)} ciudadanos distintos. "
                 f"Se realizaron {verificaciones} verificaciones y se retiraron {len(juego.publicaciones_eliminadas)} publicaciones dañinas.")
    vinculos = {tuple(arista) for r in juego.historial for arista in r.get("efectos_red", {}).get("conexiones_creadas", [])}
    if vinculos:
        evidencia += f" Escuchar e investigar crearon {len(vinculos)} conexiones dirigidas nuevas en el grafo de la comunidad."
    return "\n\n".join((cierre, reaccion, _cierre_colegio(juego.historial),
                        _cierre_periodista(juego.historial), evidencia))
