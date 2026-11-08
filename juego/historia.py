"""Guion de Civitas: escenas breves y consecuencias del historial real.

Estas funciones sólo presentan la partida. No cambian decisiones, indicadores,
el generador aleatorio ni la red, por lo que guardados y clientes comparten relato.
"""


_DIALOGOS = {
    50: (
        ("NARRADOR", "Una notificación interrumpe la mañana. El ciudadano deja el café sin probar."),
        ("CIUDADANO", "Mi hermana estudia en ese colegio. Si lo cierran, ¿a dónde va a ir?"),
        ("PERIODISTA", "Entiendo la urgencia. Antes de avisar a las familias, necesitamos el comunicado completo."),
        ("CIUDADANO", "Tengo el dedo sobre Compartir. Esperar también cuesta cuando alguien te importa."),
    ),
    30: (
        ("NARRADOR", "El ruido de la plaza entra por la ventana. La periodista abre su libreta por una página nueva."),
        ("CIUDADANO", "Adrián habla de cultura. Mi abuelo lleva años pidiendo un lugar para leer cerca de casa."),
        ("PERIODISTA", "Una propuesta puede ilusionarnos y todavía dejar preguntas: qué ofrece, cuándo y con qué recursos."),
        ("CIUDADANO", "Quiero creerle. También quiero poder explicárselo a mi abuelo sin inventar nada."),
    ),
    70: (
        ("NARRADOR", "Sobre la mesa hay un mapa del parque. El ciudadano señala el camino que usa cada tarde."),
        ("CIUDADANO", "Si hacen mantenimiento, mi hermana y yo tendremos que cambiar la ruta al colegio."),
        ("PERIODISTA", "Busquemos fechas y zonas afectadas. Un aviso sin esos detalles puede confundir al barrio."),
        ("CIUDADANO", "Esta publicación parece pequeña. Para quien cruza el parque todos los días, no lo es."),
    ),
    20: (
        ("NARRADOR", "La periodista aparta un libro gastado para acercar el teléfono. El ciudadano reconoce la portada."),
        ("CIUDADANO", "Es el favorito de mi abuelo. Una biblioteca aquí sería más que otro edificio de campaña."),
        ("PERIODISTA", "Por eso hay que distinguir un anuncio, un proyecto aprobado y una obra terminada."),
        ("CIUDADANO", "Revisemos qué dice de verdad. No quiero prometerle una inauguración que nadie ha anunciado."),
    ),
    60: (
        ("NARRADOR", "La conversación se corta al llegar otra notificación. La periodista deja de escribir."),
        ("CIUDADANO", "Esta acusación ya está en varios grupos. Si pregunto por la fuente, me dicen que todo el mundo lo sabe."),
        ("PERIODISTA", "Me piden publicarla antes que nadie. Ser la primera sirve de poco si termino dañando a alguien."),
        ("CIUDADANO", "¿Y si esperar parece que estamos ocultando algo? Quiero responder sin convertir la duda en una acusación."),
    ),
    80: (
        ("NARRADOR", "La plaza empieza a vaciarse. En el teléfono, un titular promete saber el resultado antes de las urnas."),
        ("CIUDADANO", "Mi abuelo dice que para qué salir a votar si esta encuesta ya decidió por todos."),
        ("PERIODISTA", "Un porcentaje sin fecha, muestra ni método no explica cómo se obtuvo. Necesitamos esas piezas."),
        ("CIUDADANO", "Es nuestra última decisión de la campaña. Quiero que la ciudad llegue a las urnas con preguntas, no con certezas prestadas."),
    ),
}

_ANTECEDENTES = {30: 50, 70: 30, 20: 50, 60: 20, 80: 60}

# La rama recuerda un acontecimiento concreto y vuelve a la campaña común.
_RECUERDOS = {
    50: {
        "compartir": "El mensaje del colegio sigue en nuestra conversación. Ahora tenemos otra oportunidad de mirar el contexto.",
        "verificar": "Volver al comunicado del colegio nos obligó a hacer preguntas. Conservemos esa costumbre.",
        "reportar": "Reportar el mensaje del colegio no resolvió todas nuestras dudas. También necesitamos explicar lo que sabemos.",
        "ignorar": "Dejamos pendiente la pregunta del colegio. No quiero acumular otra duda sin escuchar a nadie.",
    },
    30: {
        "compartir": "La propuesta cultural salió de nuestro teléfono. Este aviso del parque también necesita contexto.",
        "verificar": "Leímos la propuesta antes de decidir. Apliquemos el mismo cuidado a este aviso cotidiano.",
        "reportar": "El reporte de la propuesta fue rechazado. Que un anuncio no nos convenza no basta para retirarlo.",
        "ignorar": "La propuesta cultural quedó sin respuesta. Este aviso afecta una ruta que conocemos bien.",
    },
    20: {
        "compartir": "Hablamos de la biblioteca pensando en tu abuelo. Una acusación merece el mismo cuidado que una buena noticia.",
        "verificar": "Distinguimos el proyecto de biblioteca de una obra terminada. Aquí también hay que separar lo dicho de lo probado.",
        "reportar": "Civitas conservó el anuncio de la biblioteca. Esta vez expliquemos qué motivo tenemos para actuar.",
        "ignorar": "No respondimos al anuncio de la biblioteca. Ahora el silencio pesa por una razón distinta.",
    },
    60: {
        "compartir": "La acusación salió de nuestro teléfono. Este último titular exige detenernos antes de repetirlo.",
        "verificar": "Contrastamos la acusación y emitimos una corrección. La encuesta también necesita algo más que un titular.",
        "reportar": "Retiramos la acusación de Civitas. Eso no borra lo que alguien pudo leer antes; queda trabajo por hacer.",
        "ignorar": "Dejamos la acusación sin responder. En esta última publicación todavía podemos pedir contexto.",
    },
}

_REACCIONES = {
    50: {
        "compartir": "Quise proteger a mi hermana y envié el mensaje antes de comprobarlo. Ahora tengo que hacerme cargo de lo que publiqué.",
        "verificar": "La revisión separa el rumor del comunicado. Tu hermana necesita respuestas; ya podemos hablar con ella sin repetir el miedo del titular.",
        "reportar": "El mensaje salió del feed. Mi hermana todavía me pregunta qué pasó; retirarlo no sustituye una explicación.",
        "ignorar": "Apagué la pantalla, pero sigo pensando en mi hermana. No compartir evitó una difusión; la duda no desapareció.",
    },
    30: {
        "compartir": "Envié la propuesta pensando en mi abuelo. Cuando me pregunte qué promete, tendré que hablar de lo escrito, no de lo que imaginé.",
        "verificar": "La propuesta está respaldada en los documentos de la campaña. Ahora podemos discutir sus alcances sin inventarle promesas.",
        "reportar": "El anuncio sigue publicado. Puedo discrepar de Adrián sin pedir que desaparezca su propuesta.",
        "ignorar": "No envié la propuesta. Mi abuelo tendrá que buscarla por otro camino; todavía no sé qué habría opinado.",
    },
    70: {
        "compartir": "Compartí el aviso del parque. Quiero que quienes lo reciban revisen los detalles antes de cambiar sus planes.",
        "verificar": "Ya contrastamos el aviso. Puedes organizar el camino al colegio sin convertir el mantenimiento en un cierre permanente.",
        "reportar": "El aviso del parque permanece. Mi molestia por cambiar de camino no es una razón para retirarlo.",
        "ignorar": "Seguí de largo. El parque seguirá siendo parte de nuestro camino, aunque yo no haya enviado el aviso.",
    },
    20: {
        "compartir": "Envié el anuncio de la biblioteca. Ojalá mi abuelo lo vea como un proyecto para conversar, no como una puerta que ya abrió.",
        "verificar": "El anuncio tiene respaldo. Podemos hablar con tu abuelo de un proyecto, sin inventarle una fecha de inauguración.",
        "reportar": "El anuncio quedó en Civitas. No puedo confundir mis dudas sobre la campaña con motivos para retirar información.",
        "ignorar": "Dejé el anuncio sin responder. El libro de mi abuelo sigue sobre la mesa; la conversación puede esperar, pero me importa.",
    },
    60: {
        "compartir": "Cedí a la prisa y envié la acusación. No puedo usar «todo el mundo lo decía» como si fuera una fuente.",
        "verificar": "Contrastamos la acusación y emitimos una corrección. Llegar primero habría sido más fácil que responder por un error.",
        "reportar": "La acusación fue retirada. Ahora quiero explicar el motivo sin repetir el daño en cada conversación.",
        "ignorar": "No reenvié la acusación. Aun así, no he dado una respuesta a quienes preguntan de dónde salió.",
    },
    80: {
        "compartir": "Envié el pronóstico antes de pedir su método. A mi abuelo le debo algo mejor que presentar una suposición como destino.",
        "verificar": "La revisión no respalda ese pronóstico. Tu abuelo puede decidir qué hacer sin tratar el titular como un resultado electoral.",
        "reportar": "El pronóstico salió del feed. La elección sigue por decidir: un titular no decide por la ciudad.",
        "ignorar": "Dejé pasar la encuesta. No añadí otra copia, pero mi abuelo aún necesita una conversación antes de decidir si va a votar.",
    },
}


def _registro_de(juego, identificador):
    return next((r for r in reversed(juego.historial)
                 if r["publicacion"]["id"] == identificador), None)


def _autor_decision(juego, registro):
    return next((j.nombre for j in juego.jugadores if j.id == registro.get("jugador_id")),
                "Un participante")


def _resultado_difusion(registro):
    """Distingue exposición al contenido y recepción de una corrección."""
    propagacion = registro.get("propagacion")
    if not propagacion:
        return "Esta decisión no inició una difusión."
    objeto = "La corrección" if propagacion["correccion"] else "La publicación"
    alcance = registro["alcance"]
    tiempo = propagacion["tiempo_simulado"]
    if not alcance:
        return f"{objeto} no alcanzó a otros ciudadanos: 0 receptores en {tiempo:g} unidades simuladas."
    unidad = "ciudadano" if alcance == 1 else "ciudadanos"
    return f"{objeto} llegó a {alcance} {unidad} en {tiempo:g} unidades simuladas."


def contenido_resultado(juego, tipo):
    if getattr(juego, "campana", "clasica") == "extendida":
        from juego.campana_extendida import reaccion_extendida
        reaccion = reaccion_extendida(juego, tipo)
        if reaccion is not None:
            return reaccion
    registro = juego.ultimo_registro
    if not registro:
        return "Todavía no se ha tomado una decisión.", "NARRADOR"
    publicacion, accion = registro["publicacion"], registro["accion"]
    oficio = registro.get("accion_rol", accion)
    falsas = publicacion["verdadera"] is False or publicacion.get("danina", False)
    if tipo == 1:
        reacciones = {
            "conversar": ("CIUDADANO", "Escuché al vecindario antes de reenviar el mensaje. Conocer una preocupación no significa que el titular sea cierto."),
            "convocar": ("CIUDADANO", ("Convocar al barrio llevó el mensaje más lejos. Si partimos de un rumor, también multiplicamos la preocupación." if falsas else "Convocar al barrio convirtió el aviso en una conversación compartida. Ahora debemos responder a quienes se sumaron.") if registro.get("alcance") else "Intenté convocar al barrio, pero ninguna persona recibió el mensaje. Antes de insistir necesitamos revisar cómo estamos conectados."),
            "entrevistar": ("PERIODISTA", "Abrí una conversación con una fuente. Su testimonio aporta contexto, pero todavía no equivale a una comprobación."),
            "desmentir": ("PERIODISTA", ("La rectificación salió a la red y el contenido fue retirado. Explicar el error importa tanto como corregirlo." if registro.get("alcance") else "Retiramos el contenido, pero la rectificación no alcanzó a otros vecinos. Corregir también exige encontrar una forma de llegar a quienes necesitan la explicación.") if registro["eliminada"] else "Denuncié algo que no debía retirarse. La credibilidad también exige reconocer cuando el reporte no tenía fundamento."),
            "reservar": ("PERIODISTA", "Preferí mantener la publicación en reserva. Esperar protege el rigor, pero el barrio todavía necesita una respuesta."),
        }
        if oficio in reacciones:
            nombre, texto = reacciones[oficio]
            return texto, nombre
    if tipo == 2:
        nuevas = registro.get("efectos_red", {}).get("conexiones_creadas", [])
        if oficio == "conversar":
            return (("La conversación creó un vínculo recíproco entre vecinos. Puedes seguir ambas conexiones en el observatorio. " if nuevas else "La conversación aprovechó los vínculos que ya existían. ")
                    + "El titular no se difundió ni quedó verificado."), "NARRADOR"
        if oficio == "entrevistar":
            return (("La entrevista abrió un contacto directo con una fuente. La relación nueva permanece en el grafo. " if nuevas else "La entrevista utilizó un contacto que ya estaba en la red. ")
                    + "No hubo difusión y el testimonio sigue pendiente de contraste."), "NARRADOR"
        if oficio == "reservar":
            return "La publicación queda en reserva editorial. No se difundió ni se eliminó; esperar también demora la participación del barrio.", "NARRADOR"
        if oficio == "desmentir" and registro["eliminada"]:
            return "El contenido fue retirado del ABB después de enviar una rectificación. " + _resultado_difusion(registro), "NARRADOR"
    if tipo == 1:
        texto = _REACCIONES.get(publicacion["id"], {}).get(accion, registro["explicacion"])
        # Una opinión o un escenario importado conserva su explicación real.
        if publicacion["verdadera"] is None:
            texto = registro["explicacion"]
        if accion == "compartir" and not registro["alcance"]:
            texto = "Pulsé Compartir, pero el mensaje no alcanzó a otros vecinos. Todavía tengo que responder por lo que decidí publicar."
        return texto, "PERIODISTA" if accion == "verificar" else "CIUDADANO"
    if tipo == 2:
        if accion == "verificar":
            if publicacion["verdadera"] is None:
                texto = "Es una opinión: no equivale a un hecho comprobado. Esta decisión no inició una difusión."
            elif publicacion["verdadera"] is False:
                texto = "La revisión desmiente la publicación. " + _resultado_difusion(registro)
            else:
                texto = "La revisión confirma el contenido de la publicación. Esta decisión no inició una difusión."
            return texto, "PERIODISTA"
        if registro.get("propagacion"):
            texto = _resultado_difusion(registro)
            receptores = registro["propagacion"]["receptores"]
            if receptores:
                vecino = juego.grafo.nodos.get(receptores[0])
                if vecino:
                    texto += f" {vecino.nombre} está entre sus receptores."
            return texto, "NARRADOR"
        if registro["eliminada"]:
            return "El contenido fue retirado del ABB. El historial permanece y ninguna persona ni relación fue eliminada de la red.", "NARRADOR"
        if accion == "reportar":
            return "El reporte fue rechazado: no había motivo para retirar la publicación. El contenido permanece en el ABB y no se inició una difusión.", "NARRADOR"
        return "No compartiste la publicación. Permanece en Civitas; esta decisión no inició una difusión ni resolvió su veracidad.", "NARRADOR"
    cambios = [f"{nombre.replace('_', ' ')} {registro['despues'][nombre]-valor:+g}"
               for nombre, valor in registro["antes"].items() if registro["despues"][nombre] != valor]
    return ("Ciudad Nova refleja la decisión de " + _autor_decision(juego, registro) + ": "
            + (", ".join(cambios) or "sin cambios en los indicadores")
            + f". Puntuación de la acción: {registro['puntos']:+d}."), "NARRADOR"


def dialogos_publicacion(juego):
    if getattr(juego, "campana", "clasica") == "extendida":
        from juego.campana_extendida import dialogos_extendidos
        dialogos = dialogos_extendidos(juego)
        if dialogos is not None:
            return dialogos
    publicacion = juego.obtener_publicacion_actual()
    if publicacion is None:
        return [("NARRADOR", "La campaña ya no tiene publicaciones pendientes.")]
    dialogos = list(_DIALOGOS.get(publicacion.id, (
        ("NARRADOR", "Una nueva publicación interrumpe la conversación."),
        ("CIUDADANO", "Este mensaje puede cambiar lo que piensan nuestros vecinos."),
        ("PERIODISTA", "Revisemos su autor, su fecha y el contexto antes de actuar."),
    )))
    anterior = getattr(juego, "ultimo_registro", None) or {}
    metodo = anterior.get("accion_rol")
    recuerdos_oficio = {
        "conversar": ("El vínculo que abriste con el vecindario sigue en la red. Escuchar puede cambiar a quién llegará nuestra próxima conversación."
                      if anterior.get("efectos_red", {}).get("conexiones_creadas") else "Escuchaste al vecindario usando los vínculos que ya existían. Esa conversación no convirtió el titular en un hecho."),
        "convocar": ("La convocatoria tuvo un alcance que ahora nos toca explicar. Una red más activa también exige más responsabilidad."
                     if anterior.get("alcance") else "La convocatoria no llegó a otros vecinos. El alcance depende de las conexiones de la red, además de nuestra intención."),
        "entrevistar": "La fuente que entrevisté sigue siendo un contacto de la red. Su voz es una pista, no un certificado de verdad.",
        "desmentir": ("La rectificación y su recepción quedaron en el historial. Corregir una publicación no borra todo lo que alguien leyó antes."
                      if anterior.get("eliminada") else "El reporte rechazado también quedó en el historial. Revisar nuestras propias decisiones es parte del trabajo."),
        "reservar": "Dejé una publicación en reserva. Para informar todavía hay que volver con pruebas y una explicación.",
    }
    if metodo in recuerdos_oficio:
        dialogos.insert(1, ("PERIODISTA", recuerdos_oficio[metodo]))
    # La tarjeta social muestra el titular; el guion añade lo que está en juego.
    antecedente = _registro_de(juego, _ANTECEDENTES.get(publicacion.id))
    if antecedente and metodo not in recuerdos_oficio:
        recuerdo = _RECUERDOS.get(antecedente["publicacion"]["id"], {}).get(antecedente["accion"])
        if recuerdo:
            dialogos.insert(1, ("PERIODISTA", recuerdo))
    if juego.conflictos >= 8:
        dialogos.append(("PERIODISTA", "Cada conversación se vuelve más difícil. Antes de responder, escuchemos qué preocupa al otro."))
    return dialogos
