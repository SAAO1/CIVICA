"""Guion de los actos IV a VII, sin alterar la simulación de la partida.

El llamador decide cuándo utilizar esta campaña. El modo clásico conserva sus
seis publicaciones y sus diálogos. Aquí se reúnen publicaciones, fuentes
ficticias, conversaciones y desenlaces finitos para producir todas sus voces.

``dialogos_extendidos`` devuelve [(hablante, texto)] o None;
``reaccion_extendida`` devuelve (texto, hablante) o None;
``epilogo_extendido`` devuelve [(hablante, texto)]. ``FRASES_POSIBLES`` contiene
todas las parejas distintas que esas funciones pueden presentar, sin nombres
de jugadores, cifras de alcance ni resultados electorales inventados.
"""


ACTOS_NUEVOS = {
    4: "ACTO IV · La voz que amplifica",
    5: "ACTO V · Cuatro promesas bajo los focos",
    6: "ACTO VI · La noche del audio recortado",
    7: "ACTO VII · La ciudad decide",
}

PUBLICACIONES_NUEVAS = (
    {"id": 90, "texto": "Un video asegura que Laura Ríos cerrará todos los parques hasta después de las elecciones.",
     "verdadera": False, "impacto": 7, "tipo": "rumor", "emisor_id": "valeria", "candidato_id": "laura"},
    {"id": 40, "texto": "Camila Vega presenta un canal público de correcciones con fuentes.",
     "verdadera": True, "impacto": 4, "tipo": "propuesta", "emisor_id": "valeria", "candidato_id": "camila"},
    {"id": 100, "texto": "Juan Torres propone reparar las cubiertas del colegio manteniendo las clases.",
     "verdadera": True, "impacto": 5, "tipo": "propuesta", "emisor_id": "ana", "candidato_id": "juan"},
    {"id": 10, "texto": "Para mí, la cultura debe ser la primera prioridad de la próxima alcaldía, afirma Adrián Morales.",
     "verdadera": None, "impacto": 4, "tipo": "opinion", "emisor_id": "luis", "candidato_id": "adrian"},
    {"id": 110, "texto": "Un audio asegura que Camila Vega cobrará por votar.",
     "verdadera": False, "impacto": 8, "tipo": "rumor", "emisor_id": "maria", "candidato_id": "camila"},
    {"id": 25, "texto": "El archivo íntegro de Juan Torres aclara cómo continuar las clases durante las obras.",
     "verdadera": True, "impacto": 5, "tipo": "noticia", "emisor_id": "carlos", "candidato_id": "juan"},
    {"id": 120, "texto": "Laura Ríos comparte el mapa oficial de accesos a los puestos de votación.",
     "verdadera": True, "impacto": 4, "tipo": "noticia", "emisor_id": "ana", "candidato_id": "laura"},
    {"id": 35, "texto": "Un mensaje atribuido a Adrián Morales afirma que comentar en Civitas sustituye el voto.",
     "verdadera": False, "impacto": 8, "tipo": "rumor", "emisor_id": "luis", "candidato_id": "adrian"},
)

_FONDO = "../expansion/siete_actos/fondos/"
_PERSONAJE = "../expansion/siete_actos/personajes/"

CASOS_NUEVOS = {
    90: {
        "acto": ACTOS_NUEVOS[4], "titulo": "El video que se quedó sin bordes",
        "lugar": "Estudio de Valeria · La segunda ola de la campaña",
        "objetivo": "Acompañar a Valeria cuando el alcance de un recorte supera lo que su imagen permite afirmar.",
        "fondo": _FONDO + "estudio.jpg",
        "pistas": [
            {"titulo": "Fuente original · La grabación completa del parque",
             "texto": "Archivo de la cuadrilla municipal: el video completo muestra una cinta junto a los juegos y un sendero lateral abierto. Al final, la cámara enfoca el calendario de mantenimiento por sectores.",
             "pregunta": "Recupera los bordes y el final de la grabación antes de extender el cierre a todos los parques."},
            {"titulo": "Fecha y contexto · El calendario detrás de la cámara",
             "texto": "El calendario coincide con el aviso de mantenimiento revisado durante el acto II. No contiene una orden de Laura Ríos para cerrar todos los parques ni extiende las obras hasta después de la elección.",
             "pregunta": "Compara la duración del trabajo con la duración que anuncia el titular."},
            {"titulo": "Testimonio · La operadora de la cámara",
             "texto": "«Grabé los juegos para enseñar dónde estaban trabajando. Recortaron el paso lateral porque la imagen quedaba más dramática. No filmé los otros parques de la ciudad».",
             "pregunta": "Distingue lo que una persona vio de lo que puede saber sobre toda la ciudad."},
        ],
        "cierre": "El aro de luz de Valeria deja de parecer una garantía: también ilumina lo que quedó fuera del encuadre.",
    },
    40: {
        "acto": ACTOS_NUEVOS[4], "titulo": "Volver a quienes escucharon",
        "lugar": "Estudio de Valeria · Una transmisión pendiente",
        "objetivo": "Distinguir la existencia de un canal de correcciones de la promesa de que toda la red verá sus respuestas.",
        "fondo": _FONDO + "estudio.jpg",
        "pistas": [
            {"titulo": "Fuente original · Presentación del canal de correcciones",
             "texto": "El programa de Camila Vega presenta un canal público: cada rectificación debe enlazar al mensaje original, a sus fuentes y a un registro visible de cambios. La propuesta no borra el historial de errores.",
             "pregunta": "Observa qué se ha presentado y qué condiciones se proponen para publicar una corrección."},
            {"titulo": "Fecha y contexto · Una prueba abierta, no cobertura universal",
             "texto": "La presentación incluye una demostración con un mensaje de prueba. No afirma que el canal esté instalado en todos los teléfonos ni que pueda alcanzar automáticamente a quienes recibieron un rumor.",
             "pregunta": "Separa la presentación pública del alcance real que una corrección tendrá en el grafo."},
            {"titulo": "Testimonio · Valeria ante su registro de publicaciones",
             "texto": "«Yo puedo fijar una aclaración. Eso no hace que vuelva a verla cada persona que salió de mi directo. Necesito conservar el enlace y buscar los grupos donde se perdió el contexto».",
             "pregunta": "Relaciona la reparación con las rutas de recepción, además de la intención de corregir."},
        ],
        "cierre": "Una corrección deja de ser un botón mágico cuando hay que volver a encontrar a quienes escucharon primero.",
    },
    100: {
        "acto": ACTOS_NUEVOS[5], "titulo": "El colegio entra en el debate",
        "lugar": "Foro de Ciudad Nova · Las cuatro candidaturas",
        "objetivo": "Escuchar propuestas concretas sin confundir la respuesta del escenario con una obra terminada.",
        "fondo": _FONDO + "debate.jpg",
        "pistas": [
            {"titulo": "Fuente original · El programa educativo de Juan Torres",
             "texto": "La propuesta escrita de Juan prevé reparar cubiertas por etapas y mantener las clases usando aulas alternas. El programa permite consultar el documento completo que acompaña su intervención en el foro.",
             "pregunta": "Compara la propuesta firmada con la frase del titular y con el antiguo rumor del colegio."},
            {"titulo": "Fecha y contexto · Un compromiso todavía por ejecutar",
             "texto": "La mesa del foro conserva la pregunta completa de una familia: «¿Cómo continuarán las clases durante las obras?». La respuesta de Juan plantea un procedimiento futuro; no certifica que las reparaciones ya terminaron.",
             "pregunta": "Conserva la pregunta original y el tiempo verbal de la respuesta."},
            {"titulo": "Testimonio · La hermana del ciudadano",
             "texto": "«Quiero que dejen de caer goteras. También quiero saber si seguiré viendo a mis amigas. Me sirve que expliquen el plan, pero todavía quiero conocer el aula que nos tocaría».",
             "pregunta": "Reconoce qué preocupación resuelve una propuesta y qué detalles siguen abiertos."},
        ],
        "cierre": "La pregunta que empezó en una mesa del café alcanza los micrófonos del foro.",
    },
    10: {
        "acto": ACTOS_NUEVOS[5], "titulo": "Una prioridad no es una prueba",
        "lugar": "Foro de Ciudad Nova · El turno de las diferencias",
        "objetivo": "Discutir una preferencia política sin presentarla como hecho comprobable ni como motivo para censurar.",
        "fondo": _FONDO + "debate.jpg",
        "pistas": [
            {"titulo": "Fuente original · La intervención de Adrián Morales",
             "texto": "La transcripción completa dice: «Para mí, la cultura debe ser la primera prioridad de la próxima alcaldía». Adrián presenta una preferencia de su programa, no una estadística que demuestre una única prioridad correcta.",
             "pregunta": "Observa a quién se atribuye la valoración y qué expresa la frase «para mí»."},
            {"titulo": "Fecha y contexto · La ronda de prioridades",
             "texto": "La moderación pidió a cada candidatura ordenar sus prioridades. Juan habló de educación; Laura, de accesibilidad y convivencia; Camila, de participación y bienestar digital. Ninguna respuesta convierte las otras en noticias falsas.",
             "pregunta": "Distingue una diferencia de valores de una afirmación factual que requiera una comprobación."},
            {"titulo": "Testimonio · El abuelo junto a la radio",
             "texto": "«Yo pondría una biblioteca primero. Mi vecina prefiere reparar el parque. Llevamos media hora discutiendo y seguimos compartiendo el mismo termo».",
             "pregunta": "Escucha cómo un desacuerdo puede mantenerse sin retirar la voz de la otra persona."},
        ],
        "cierre": "El foro no deja una única prioridad, pero sí cuatro voces a las que se puede pedir cuentas.",
    },
    110: {
        "acto": ACTOS_NUEVOS[6], "titulo": "Los segundos que faltan",
        "lugar": "Redacción provisional · Lluvia tras el debate",
        "objetivo": "Responder a un audio alarmante sin dar por auténtico su sentido solo porque la voz resulta reconocible.",
        "fondo": _FONDO + "redaccion.jpg",
        "pistas": [
            {"titulo": "Fuente original · El audio completo de Camila Vega",
             "texto": "La grabación íntegra conserva la advertencia: «Si alguien les dice que les cobrará por votar, está mintiendo». El fragmento que circula elimina el comienzo y corta la frase antes de la aclaración final.",
             "pregunta": "Escucha qué cambia cuando se recuperan los segundos anteriores y posteriores al recorte."},
            {"titulo": "Fecha y contexto · La pregunta del público",
             "texto": "El audio pertenece a la ronda sobre mensajes engañosos recibidos por los vecinos. El archivo del foro incluye pregunta, respuesta y una marca continua de tiempo. La cadena de Civitas conserva solo una parte.",
             "pregunta": "Compara la continuidad del registro y el tema de la pregunta con el titular reenviado."},
            {"titulo": "Testimonio · La técnica de sonido",
             "texto": "«Conservo la toma de la mesa. La voz sí es de Camila, pero identificar una voz no confirma el significado de un recorte. Prefiero entregar el archivo y que puedan oírlo entero».",
             "pregunta": "Separa la identidad de una voz de la integridad de su mensaje."},
        ],
        "cierre": "La onda del audio vuelve a ser una conversación cuando aparecen los segundos que le faltaban.",
    },
    25: {
        "acto": ACTOS_NUEVOS[6], "titulo": "La carpeta del principio",
        "lugar": "Redacción provisional · El archivo antes de cerrar",
        "objetivo": "Volver al colegio y a las decisiones iniciales con un registro íntegro que pueda consultarse.",
        "fondo": _FONDO + "redaccion.jpg",
        "pistas": [
            {"titulo": "Fuente original · La entrevista íntegra de Juan Torres",
             "texto": "El archivo del foro conserva la explicación de Juan sobre aulas alternas, reparación por etapas y continuidad de las clases. El enlace contiene la pregunta de la familia y la respuesta sin cortes.",
             "pregunta": "Sigue la explicación hasta su registro completo, además de una frase que la resume."},
            {"titulo": "Fecha y contexto · La misma pregunta, después del debate",
             "texto": "La carpeta reúne el acta educativa del principio de la campaña y la nueva entrevista. Ambos documentos plantean mantener las clases durante las obras; ninguno ordena cerrar el colegio como afirmaba el rumor inicial.",
             "pregunta": "Compara las piezas independientes y conserva el orden en que aparecieron."},
            {"titulo": "Testimonio · El ciudadano vuelve a llamar a su hermana",
             "texto": "«Me preguntó por qué le hablé tan seguro el primer día. Le prometí que esta vez iba a enviarle la explicación entera. Que exista un enlace no me ahorra hablar con ella».",
             "pregunta": "Distingue reparar una relación de acumular documentos en una carpeta."},
        ],
        "cierre": "La carpeta del colegio se cierra con una conversación que ningún archivo podía reemplazar.",
    },
    120: {
        "acto": ACTOS_NUEVOS[7], "titulo": "El camino hasta la urna",
        "lugar": "Plaza de Ciudad Nova · La mañana electoral",
        "objetivo": "Ayudar a llegar al puesto de votación manteniendo la fuente, los horarios y los accesos del aviso.",
        "fondo": _FONDO + "urnas.jpg",
        "pistas": [
            {"titulo": "Fuente original · El mapa de la organización electoral",
             "texto": "El mapa público identifica puestos, horarios y entradas accesibles. La publicación de Laura Ríos enlaza a ese archivo; el emisor del mapa es la organización electoral, no una candidatura.",
             "pregunta": "Conserva la diferencia entre quien publica la información y quien es responsable de ella."},
            {"titulo": "Fecha y contexto · La versión de esta jornada",
             "texto": "El mapa indica la jornada actual y conserva el acceso lateral para personas con movilidad reducida. No cambia el puesto asignado a cada votante ni permite deducirlo a partir del lugar donde vive una amistad.",
             "pregunta": "Relaciona fecha, puesto asignado y acceso sin extender instrucciones de una persona a toda la ciudad."},
            {"titulo": "Testimonio · El abuelo prepara la salida",
             "texto": "«No necesito que me digan a quién votar. Necesito saber por qué entrada puedo pasar con el bastón. Después de tanto ruido, esa diferencia me importa».",
             "pregunta": "Escucha una necesidad de acceso sin convertir la ayuda en una instrucción de voto."},
        ],
        "cierre": "Entre tantos mensajes, una indicación conservada con cuidado puede abrir el camino de otra persona.",
    },
    35: {
        "acto": ACTOS_NUEVOS[7], "titulo": "Ningún comentario es una urna",
        "lugar": "Plaza de Ciudad Nova · Antes del cierre electoral",
        "objetivo": "Tomar la última decisión sin permitir que una interfaz social suplante la participación electoral.",
        "fondo": _FONDO + "urnas.jpg",
        "pistas": [
            {"titulo": "Fuente original · La aclaración de la organización electoral",
             "texto": "El aviso oficial de la jornada explica que las interacciones de Civitas no se contabilizan como votos. Los comentarios no sustituyen el procedimiento electoral descrito en ese aviso.",
             "pregunta": "Compara el procedimiento oficial con lo que promete el mensaje de la red social."},
            {"titulo": "Fecha y contexto · Una captura atribuida a Adrián",
             "texto": "El perfil de campaña de Adrián conserva el mensaje completo: «Comentar no sustituye el voto». La captura reenviada elimina la palabra «no» y mantiene la foto del candidato. El aspecto del perfil no conserva por sí solo el sentido original.",
             "pregunta": "Recupera la frase completa y distingue una atribución de una publicación auténtica."},
            {"titulo": "Testimonio · Valeria prepara el cierre de su directo",
             "texto": "«Me pidieron que pusiera una encuesta para no salir de casa. Puedo preguntar qué piensa la gente. No puedo convertir mi pantalla en una mesa de votación».",
             "pregunta": "Distingue una interacción con una audiencia del procedimiento que decide la elección."},
        ],
        "cierre": "El teléfono cabe en un bolsillo. La ciudad necesita que sus decisiones también encuentren lugar fuera de él.",
    },
}

PERFILES_NUEVOS = [
    {"nombre": "INFLUENCER", "rol": "Valeria Cruz · La voz que amplifica",
     "deseo": "Hacer que su comunidad sea escuchada sin perder el vínculo con quienes la siguen.",
     "conflicto": "Las personas esperan una reacción inmediata y el patrocinio premia un directo que no se detiene.",
     "recurso": _PERSONAJE + "influencer_neutral.png"},
    {"nombre": "JUAN", "rol": "Juan Torres · Educación y espacios seguros",
     "deseo": "Que el colegio deje de representar miedo y se convierta en un compromiso concreto.",
     "conflicto": "Se impacienta con los rumores y debe explicar etapas y límites sin prometer una reparación instantánea.",
     "recurso": _PERSONAJE + "juan_neutral.png"},
    {"nombre": "ADRIAN", "rol": "Adrián Morales · Bibliotecas y cultura",
     "deseo": "Que la cultura sea una necesidad cotidiana, además de una promesa vistosa en el escenario.",
     "conflicto": "Sus frases entusiasman con facilidad; los vecinos le piden presupuestos y plazos que un eslogan no contiene.",
     "recurso": _PERSONAJE + "adrian_neutral.png"},
    {"nombre": "LAURA", "rol": "Laura Ríos · Parques y convivencia",
     "deseo": "Hacer que los espacios y servicios puedan usarse con seguridad por personas distintas.",
     "conflicto": "Los avisos prácticos pierden sus matices al circular y ella debe escuchar a quienes una entrada cerrada deja fuera.",
     "recurso": _PERSONAJE + "laura_neutral.png"},
    {"nombre": "CAMILA", "rol": "Camila Vega · Participación y bienestar digital",
     "deseo": "Que la gente pueda participar y corregir sin entregar toda su vida a la red.",
     "conflicto": "Debe demostrar que una herramienta digital puede acompañar a las personas sin sustituir su criterio ni sus derechos.",
     "recurso": _PERSONAJE + "camila_neutral.png"},
]

DIALOGOS_NUEVOS = {
    90: (
        ("NARRADOR", "El aro de luz enmarca el teléfono de Valeria. Fuera del encuadre, una llamada insiste por tercera vez."),
        ("INFLUENCER", "Soy Valeria. Normalmente preparo una entrada mejor, pero hoy mi entrada tiene treinta mensajes sin responder."),
        ("CIUDADANO", "Yo tenía uno sobre mi hermana y casi no pude pensar. Treinta deben sonar como una sirena."),
        ("INFLUENCER", "Este video del parque se está compartiendo. Si corto el directo para buscar el original, parece que me escondo."),
        ("PERIODISTA", "¿Podemos ver el archivo que te enviaron, antes del recorte que cabe en la pantalla?"),
        ("INFLUENCER", "El recorte lo hice yo. Dejé fuera el sendero porque se veía feo. Ahora el titular dice que no queda ninguna entrada."),
        ("LAURA", "Esa cinta marca los juegos que están en mantenimiento. Si alguien no encuentra el acceso abierto, quiero saberlo."),
        ("CIUDADANO", "Entonces el borde que no salía era justo por donde teníamos que pasar."),
        ("INFLUENCER", "Qué maravilla: mi mejor encuadre se ha comido una puerta. Ayúdenme a decidir qué hago antes de volver al directo."),
    ),
    40: (
        ("NARRADOR", "Valeria apoya el teléfono junto al aro de luz. El silencio entre dos notificaciones dura menos que una respiración."),
        ("INFLUENCER", "Mi representante dice que una aclaración tiene menos visitas. Le dije que mi hermana tampoco era una métrica."),
        ("CIUDADANO", "La mía me pregunta si ahora todos los videos vienen con una puerta escondida."),
        ("CAMILA", "Presenté un canal para enlazar correcciones con el mensaje original. El cambio debe quedar a la vista, también cuando incomode."),
        ("PERIODISTA", "¿Con fuentes accesibles y registro de lo que se cambió? Necesito poder revisar las dos versiones."),
        ("CAMILA", "Esa es la propuesta. Y no voy a prometer que el enlace llegará solo a cada persona que recibió el error."),
        ("INFLUENCER", "Yo pensaba fijar una disculpa y cerrar el tema. Ahora tengo una lista de grupos a los que volver."),
        ("CIUDADANO", "Podemos empezar por uno. Mi abuelo cree que fijar algo es clavar el teléfono en la pared."),
        ("INFLUENCER", "Por favor, que no lo pruebe. Primero decidamos qué hacemos con esta propuesta; después lo llamo."),
    ),
    100: (
        ("NARRADOR", "Los focos del foro encienden cuatro atriles. En la primera fila, el ciudadano sostiene una pregunta escrita por su hermana."),
        ("INFLUENCER", "Me han prestado el micrófono para preguntas del barrio. Es la primera vez que me tiembla algo sin batería."),
        ("CIUDADANO", "Ella escribió: quiero un techo sin goteras y seguir viendo a mis amigas. No sabía qué parte cabía en una pregunta."),
        ("JUAN", "Caben las dos. Propongo reparar por etapas y usar aulas alternas para mantener las clases. Aquí está el plan completo."),
        ("PERIODISTA", "Queda registrada la propuesta. También queremos saber quién publicará los avances y los retrasos."),
        ("JUAN", "Mi equipo tendrá que responder por cada etapa. No voy a decir que un documento ha arreglado una cubierta."),
        ("ADRIAN", "Y esos espacios alternos necesitarán libros y estudio, además de paredes."),
        ("LAURA", "Y un acceso que pueda usar una familia con coche o una persona con bastón. Lo provisional también debe funcionar."),
        ("CAMILA", "El calendario debe poder consultarse sin tener que seguir a una candidatura en Civitas."),
        ("CIUDADANO", "Ahora sí tengo algo que contarle a mi hermana. Quiero conservar lo que dijeron, incluso las preguntas que aún faltan."),
    ),
    10: (
        ("NARRADOR", "La moderación recoge el reloj de la mesa. Nadie en los cuatro atriles parece dispuesto a devolver el último minuto."),
        ("ADRIAN", "Para mí, la cultura debe ser la primera prioridad de la próxima alcaldía. Una ciudad también necesita lugares donde imaginarse."),
        ("JUAN", "Yo empiezo por el colegio. Pero admito que sería triste reparar el techo y dejar vacíos los estantes."),
        ("LAURA", "Yo empiezo por que podamos usar los espacios comunes. Imaginar la ciudad desde una puerta cerrada deja a gente fuera."),
        ("CAMILA", "Yo quiero que se escuche a quienes no pueden venir a este foro. Tampoco todo se resuelve encendiendo una cámara."),
        ("INFLUENCER", "Agradezco que lo digas delante de la mía. Me acaba de entrar un comentario que pide reportar a quien no ponga cultura primero."),
        ("PERIODISTA", "Podemos discutir esa prioridad. No es una noticia falsa solo porque alguien prefiera otra."),
        ("ADRIAN", "Mi abuelo diría que una biblioteca necesita también un parque donde leer. El presupuesto nos va a obligar a conversar."),
        ("CIUDADANO", "El mío ya está discutiendo con la vecina y han compartido el termo. Creo que llevan ventaja al foro."),
        ("INFLUENCER", "Voy a dejar la frase con su autor y su contexto. Ustedes deciden qué hacer con la publicación, no qué voz debe desaparecer."),
    ),
    110: (
        ("NARRADOR", "La lluvia golpea la ventana de la redacción. Un audio termina demasiado pronto y deja a todos mirando el teléfono."),
        ("CIUDADANO", "Mi abuelo oyó que le van a cobrar por votar. Ya estaba sacando dinero del cajón."),
        ("INFLUENCER", "Reconozco la voz de Camila. Me piden que reaccione en directo. Esta vez no quiero adivinar los segundos que faltan."),
        ("CAMILA", "Era una advertencia sobre un engaño. La frase completa empezaba antes de lo que se está reenviando."),
        ("PERIODISTA", "Tu explicación importa, pero necesito la grabación de la mesa. No basta con que el recorte te perjudique."),
        ("CAMILA", "La técnica conserva el archivo. Pueden escuchar la pregunta y mi respuesta sin que yo escoja el fragmento."),
        ("INFLUENCER", "Y si el directo se queda en silencio mientras lo buscamos, se queda. Puedo sobrevivir a una pausa."),
        ("CIUDADANO", "Yo voy a decirle al abuelo que no entregue dinero por una cadena. Después quiero enseñarle la fuente, no otra promesa mía."),
        ("PERIODISTA", "Tenemos el recorte, la respuesta y una ruta al original. La decisión siguiente debe hacerse cargo de las tres cosas."),
    ),
    25: (
        ("NARRADOR", "En la redacción queda una carpeta abierta con el nombre del colegio. La periodista deja el archivo completo junto al primer mensaje de la campaña."),
        ("JUAN", "Conservé la pregunta de aquella familia. No quería que mi respuesta empezara cuando ya no se oyera lo que me estaban pidiendo."),
        ("CIUDADANO", "La familia era la mía. Mi hermana dice que si tanta gente habla de su colegio, alguien debería ir a verla estudiar."),
        ("JUAN", "Tiene razón en pedir algo más que una grabación. El plan sigue siendo un compromiso del que tendrán que pedirnos cuentas."),
        ("PERIODISTA", "El acta del primer día y esta entrevista conservan la misma idea: mantener las clases durante las obras. Guardaremos ambos enlaces."),
        ("INFLUENCER", "Yo guardé también el recorte del parque. Borrar lo que me avergüenza haría muy cómoda la galería y muy mala la memoria."),
        ("CIUDADANO", "Me toca llamar a mi hermana. No puedo mandarle una carpeta y fingir que la conversación ocurrió."),
        ("JUAN", "Si pregunta por las aulas alternas, todavía faltan detalles. Prefiero que esa parte quede escrita antes de que alguien invente una fecha."),
        ("PERIODISTA", "Aún podemos decidir cómo circulará este archivo. Que una pieza sea útil no garantiza que llegue entera."),
    ),
    120: (
        ("NARRADOR", "La mañana electoral abre la plaza. El abuelo espera junto al ciudadano mientras un mapa pasa de mano en mano."),
        ("CIUDADANO", "El abuelo ya eligió zapatos, bastón y tema de conversación. Solo nos falta una entrada por la que pueda pasar."),
        ("LAURA", "Compartí el mapa de la organización electoral. La entrada accesible está señalada; conserven el enlace por si hay una actualización."),
        ("PERIODISTA", "Vamos a comprobar la versión de hoy y el puesto asignado. Una dirección útil para nosotros podría no ser la de otra familia."),
        ("INFLUENCER", "Hoy mi directo tendrá una regla: ninguna cara de votantes sin permiso y ninguna cámara dentro de su decisión."),
        ("CAMILA", "Y nadie debería necesitar una cuenta en Civitas para encontrar la entrada. Hay copias del mapa en el punto de información."),
        ("LAURA", "Si algún acceso no coincide con el plano, la organización tiene que saberlo. Un mapa no sube un escalón por nadie."),
        ("CIUDADANO", "El abuelo pregunta si pueden dejar de llamarlo abuelo en la transmisión. Tiene nombre y opiniones para todos los atriles."),
        ("INFLUENCER", "Aceptado. Fuera del directo, me encantaría oír esas opiniones. Primero decidamos cómo ayudamos con el aviso."),
    ),
    35: (
        ("NARRADOR", "La plaza se llena de pasos y conversaciones. Antes del cierre electoral, un último mensaje intenta convertir los comentarios de Civitas en votos."),
        ("INFLUENCER", "Me piden abrir una encuesta para que la gente vote desde el sofá. Mi teléfono hace muchas cosas, pero no es una urna."),
        ("ADRIAN", "Han usado mi foto y han quitado una palabra. Yo escribí que comentar no sustituye el voto. Ese no hace bastante trabajo."),
        ("PERIODISTA", "Tenemos tu mensaje completo y el aviso de la organización. Conservaremos ambos para que la aclaración se pueda revisar."),
        ("JUAN", "Sea cual sea el resultado, no quiero una victoria construida sobre personas que creyeron que ya habían votado."),
        ("LAURA", "Algunas aún están buscando cómo llegar. No les cambiemos el camino con otra captura."),
        ("CAMILA", "La participación no cabe entera en un contador. Detrás de cada cifra hay alguien que debe poder decidir."),
        ("CIUDADANO", "Mi abuelo guardó el teléfono. Dice que volverá a discutir después. Creo que acaba de darme el mejor plan del día."),
        ("INFLUENCER", "Yo también voy a salir de la pantalla un rato. Antes nos queda esta decisión y la responsabilidad de cómo llegará a los demás."),
        ("PERIODISTA", "Después vendrá el resultado. Ningún titular lo conoce todavía, y ninguna candidatura recibe una victoria por adelantado."),
    ),
}

# Solo se consulta en el modo extendido. El texto clásico queda intacto.
DIALOGOS_OVERRIDE = {
    80: (
        ("NARRADOR", "La plaza empieza a vaciarse. En el teléfono, un titular promete saber el resultado antes de las urnas."),
        ("CIUDADANO", "Mi abuelo dice que para qué salir a votar si esta encuesta ya decidió por todos."),
        ("PERIODISTA", "Un porcentaje sin fecha, muestra ni método no explica cómo se obtuvo. Necesitamos esas piezas."),
        ("CIUDADANO", "Creí que la campaña cabía en estos mensajes. Ahora una influencer nos pide ayuda con un video que está llegando más lejos."),
    ),
}

_MEMORIAS = {
    "compartir": ("PERIODISTA", "Lo que reenviamos ya tiene su recorrido. La siguiente decisión no borra las personas a las que llegó la anterior."),
    "compartir_cero": ("CIUDADANO", "Mi mensaje no llegó a otros vecinos. La próxima vez quiero mirar también a quién puedo alcanzar."),
    "conversar": ("CIUDADANO", "Escuchar dejó una conversación abierta. No quiero que la siguiente notificación se la lleve por delante."),
    "convocar": ("CIUDADANO", "Después de convocar al barrio, hay personas esperando una explicación. No quiero dejarlas solo con el titular."),
    "convocar_cero": ("CIUDADANO", "Intenté convocar al barrio y no hubo receptores. Una invitación no se convierte en reunión porque yo la imagine."),
    "contrastar": ("PERIODISTA", "La revisión anterior dejó sus fuentes guardadas. Si volvemos a dudar, podemos regresar a ellas."),
    "entrevistar": ("PERIODISTA", "La fuente que escuchamos sigue teniendo voz propia. Quiero conservar sus dudas, además de la frase que me sirvió."),
    "desmentir": ("PERIODISTA", "La corrección quedó junto al error en el historial. Reparar empieza por recordar los dos."),
    "desmentir_rechazado": ("PERIODISTA", "El reporte fue rechazado. Me toca reconocerlo antes de pedir que otros confíen en mi siguiente decisión."),
    "reservar": ("PERIODISTA", "Dejé una publicación en reserva. El silencio me dio tiempo, pero todavía debo volver con una respuesta."),
    "ignorar": ("CIUDADANO", "Decidí no reenviar. La pantalla quedó en silencio, aunque la conversación del barrio siguió sin mí."),
}
_TENSION = ("INFLUENCER", "En el chat ya están discutiendo antes de escucharnos. Voy a bajar la voz; no quiero competir con el ruido.")


def _oficio(registro):
    clave = registro.get("accion_rol", registro.get("accion", "ignorar"))
    return {"verificar": "contrastar", "reportar": "desmentir"}.get(clave, clave)


def _memoria(registro):
    clave = _oficio(registro)
    if clave in ("compartir", "convocar") and not registro.get("alcance"):
        clave += "_cero"
    if clave == "desmentir" and not registro.get("eliminada"):
        clave += "_rechazado"
    return _MEMORIAS.get(clave)


def dialogos_extendidos(juego):
    """Conversación del caso actual, con memoria finita del registro previo.

    Consultar un diálogo no consume azar, inserta publicaciones ni cambia
    indicadores. None permite que el llamador recurra al guion clásico.
    """
    publicacion = juego.obtener_publicacion_actual()
    identificador = getattr(publicacion, "id", None)
    base = DIALOGOS_NUEVOS.get(identificador, DIALOGOS_OVERRIDE.get(identificador))
    if base is None:
        return None
    lineas = list(base)
    if identificador in DIALOGOS_NUEVOS:
        anterior = getattr(juego, "ultimo_registro", None)
        recuerdo = _memoria(anterior) if isinstance(anterior, dict) else None
        if recuerdo:
            lineas.insert(1, recuerdo)
        if getattr(getattr(juego, "estado", None), "conflictos", 0) >= 35:
            lineas.append(_TENSION)
    return lineas


# Ocho respuestas humanas por caso. Los desenlaces de alcance, retirada y
# vínculo se añaden después a partir del registro, sin inventar receptores.
_REACCIONES = {
    90: {
        "compartir": "Reenvié el recorte antes de recuperar sus bordes. Ahora debo explicar por qué mi mensaje cerraba más puertas que la imagen completa.",
        "conversar": "Escuché a una vecina que usa el parque. Su preocupación merece atención, aunque no pruebe lo que dice el video.",
        "convocar": "Elegí llamar al barrio a partir de este video. Me toca responder también por la parte del encuadre que no conservé.",
        "ignorar": "Aparté el teléfono. No añadí otra copia del video, pero Valeria sigue esperando qué haremos con la puerta que quedó fuera.",
        "contrastar": "El video completo conserva un paso abierto y un mantenimiento por sectores. El recorte no respaldaba el cierre de todos los parques.",
        "entrevistar": "Pregunté a la persona que grabó el video. Su relato me devuelve al lugar de la cámara; todavía debo conservar el archivo completo.",
        "desmentir": "Me hice cargo del recorte y de su contexto. La aclaración necesita mostrar el paso que el titular había hecho desaparecer.",
        "reservar": "Dejé el video en reserva. Antes de publicarlo necesito los bordes del encuadre y el calendario que no entraban en el titular.",
    },
    40: {
        "compartir": "Compartí la presentación del canal. Quiero que se entienda como una propuesta, sin prometer que una herramienta hará por nosotros el trabajo de volver a hablar.",
        "conversar": "Pregunté a una vecina qué correcciones había podido encontrar. Escuchar su experiencia no demuestra que toda la red funcione igual.",
        "convocar": "Elegí convocar al barrio alrededor de esta propuesta. Podemos pedir que sus cambios y sus fuentes queden a la vista.",
        "ignorar": "No reenvié la propuesta. El problema de llegar a quienes escucharon primero sigue esperando una respuesta.",
        "contrastar": "La presentación y sus condiciones están en el programa. Eso respalda el anuncio, sin demostrar todavía una cobertura universal.",
        "entrevistar": "Registré lo que Valeria necesita para volver a su audiencia. Su experiencia puede orientar preguntas, no certificar el futuro del canal.",
        "desmentir": "Intenté denunciar la presentación como si fuera falsa. Una propuesta que merece preguntas no merece desaparecer por mi impaciencia.",
        "reservar": "La presentación queda en reserva editorial. Tengo que distinguir lo que ya está anunciado de las pruebas que pediré si comienza a funcionar.",
    },
    100: {
        "compartir": "Envié la propuesta de Juan conservando que es un plan por etapas. Mi hermana merece saber lo que se ha dicho y lo que aún no ha ocurrido.",
        "conversar": "Escuché cómo organizaría una familia las aulas alternas. La propuesta sigue necesitando detalles que caben mejor en una conversación que en un eslogan.",
        "convocar": "Elegí convocar al barrio alrededor del plan del colegio. Ahora toca pedir etapas y responsables, además de aplaudir una frase.",
        "ignorar": "No reenvié el plan. Guardé la pregunta de mi hermana; alguien todavía debe responderle fuera de los micrófonos.",
        "contrastar": "El programa conserva las aulas alternas y la continuidad de las clases. Respalda la propuesta que escuchamos, sin convertirla en una reparación terminada.",
        "entrevistar": "Le pedí a una fuente que explicara las etapas del colegio. Conservo sus respuestas y las preguntas que el documento aún no resuelve.",
        "desmentir": "Denuncié una propuesta respaldada como si fuera falsa. Mi desacuerdo con una campaña no sustituye una razón para retirarla.",
        "reservar": "Dejé el plan en reserva para revisarlo entero. No quiero que el siguiente titular dé por arreglado un techo que todavía espera obras.",
    },
    10: {
        "compartir": "Compartí una preferencia de Adrián con su nombre. No quiero vestir mi acuerdo con él como si fuese una prueba contra las otras voces.",
        "conversar": "Escuché otra prioridad y no se cayó el mundo. A veces la convivencia empieza por conservar un lugar en la mesa para quien ordena distinto sus necesidades.",
        "convocar": "Elegí convocar una conversación sobre prioridades. No necesitamos votar una opinión como verdadera para poder discutirla.",
        "ignorar": "No reenvié la frase. Puedo dejar pasar una opinión sin pedir que desaparezca del foro.",
        "contrastar": "La frase está atribuida y expresa una preferencia. No se transforma en un hecho comprobado por pasar por mi libreta.",
        "entrevistar": "Pregunté qué significa poner la cultura primero. La respuesta amplía una opinión política; no demuestra que las demás prioridades sean falsas.",
        "desmentir": "Intenté retirar una opinión legítima. Me toca reconocer que discrepar de su prioridad no me daba motivos para censurarla.",
        "reservar": "Reservé la frase hasta poder explicar su contexto. Una opinión necesita atribución, además de un espacio donde no se la confunda con un dato.",
    },
    110: {
        "compartir": "Reenvié un audio sin recuperar los segundos que faltaban. Reconocer la voz no me autorizaba a inventar el sentido de la frase.",
        "conversar": "Escuché el miedo que provocó el audio. Acompañar esa preocupación no significa confirmar que alguien haya anunciado un cobro.",
        "convocar": "Elegí convocar al barrio a partir de un audio recortado. La urgencia no me quita la responsabilidad de explicar el contexto que faltaba.",
        "ignorar": "No reenvié el audio. Mi abuelo aún necesita una explicación que no lo deje a solas con el miedo del mensaje.",
        "contrastar": "La toma completa conserva una advertencia contra un engaño. El recorte hacía parecer una promesa lo que se estaba desmintiendo.",
        "entrevistar": "Pedí el archivo a la técnica de sonido. Su testimonio importa, pero la grabación íntegra tiene que poder revisarse por separado.",
        "desmentir": "Preparé la aclaración con la pregunta y la respuesta completas. No bastaba con asegurar que la voz conocida estaba diciendo otra cosa.",
        "reservar": "Guardé el audio hasta recuperar su continuidad. Prefiero una pausa incómoda a fabricar una certeza con los segundos que no escuché.",
    },
    25: {
        "compartir": "Compartí el archivo íntegro del colegio. Después llamaré a mi hermana; enviar un enlace no completa por sí solo una conversación pendiente.",
        "conversar": "Volví a escuchar qué necesita una familia para continuar las clases. El plan importa de otra manera cuando alguien tiene que organizar su mañana.",
        "convocar": "Elegí reunir al barrio alrededor del archivo completo. Quiero que las preguntas sobrevivan al entusiasmo por haber encontrado una respuesta.",
        "ignorar": "No reenvié la entrevista. Mi hermana sigue mereciendo una llamada, incluso si yo dejo descansar la pantalla.",
        "contrastar": "La entrevista y el acta conservan la continuidad de las clases durante las obras. Podemos mostrar ambas piezas sin fingir que los detalles pendientes ya están resueltos.",
        "entrevistar": "Registré preguntas sobre las aulas alternas y sus responsables. La fuente ayuda a seguir el plan, sin convertir una promesa en una obra terminada.",
        "desmentir": "Intenté retirar un archivo respaldado. Volver a un error conocido exige revisar mi decisión, además de revisar los mensajes ajenos.",
        "reservar": "La entrevista queda en reserva con su enlace completo. Todavía debo volver a las preguntas de las familias; la carpeta no puede hablar por mí.",
    },
    120: {
        "compartir": "Compartí el mapa con su fuente y su jornada. Quiero ayudar a encontrar una entrada, sin mandar a todas las familias a un mismo puesto.",
        "conversar": "Escuché qué acceso necesitaba un vecino. Ayudar empieza por saber por dónde puede pasar, además de señalar un punto en la pantalla.",
        "convocar": "Elegí convocar al barrio con el aviso de accesos. La ayuda debe respetar el puesto de cada persona y su libertad para decidir.",
        "ignorar": "No reenvié el mapa. Buscaré nuestra entrada sin dar por hecho que todas las personas ya encontraron la suya.",
        "contrastar": "El mapa corresponde a esta jornada y enlaza a la organización electoral. La candidatura que lo comparte no es quien asigna los puestos.",
        "entrevistar": "Pregunté cómo encontrar un acceso utilizable. Conservo el testimonio y remito las instrucciones al mapa de la organización.",
        "desmentir": "Intenté retirar un aviso útil y respaldado. Mi desconfianza hacia quien lo compartía no justificaba esconder la fuente original.",
        "reservar": "Reservé el mapa hasta conservar su versión y su fuente. La verificación debe volver a tiempo para que la ayuda todavía sirva.",
    },
    35: {
        "compartir": "Reenvié una captura que confundía comentar con votar. La última prisa de la campaña también deja una responsabilidad que explicar.",
        "conversar": "Escuché a una persona que creyó haber votado en Civitas. Su confusión merece una conversación, sin burlas ni otra captura sin contexto.",
        "convocar": "Elegí convocar al barrio a partir de este mensaje. Una pantalla llena de respuestas no convierte una instrucción engañosa en participación real.",
        "ignorar": "No reenvié la captura. Antes de guardar el teléfono quiero asegurarme de que mi abuelo conoce el camino y decide por sí mismo.",
        "contrastar": "El mensaje íntegro y el aviso oficial aclaran el procedimiento. Los comentarios de Civitas no sustituyen la participación electoral.",
        "entrevistar": "Pregunté de dónde había salido la captura. La entrevista abre una ruta a la fuente; el procedimiento debe seguir consultándose en el aviso oficial.",
        "desmentir": "Preparé una aclaración con la frase que conservaba el no y el aviso de la jornada. La foto de un candidato no puede convertir una captura alterada en una urna.",
        "reservar": "Dejé la captura en reserva. La última pausa debe servirme para volver con una fuente, no para abandonar a quienes aún creen que ya votaron.",
    },
}

_VOZ_ACCION = {
    "compartir": "CIUDADANO", "conversar": "CIUDADANO", "convocar": "CIUDADANO", "ignorar": "CIUDADANO",
    "contrastar": "PERIODISTA", "entrevistar": "PERIODISTA", "desmentir": "PERIODISTA", "reservar": "PERIODISTA",
}
_REACCION_SIN_RECEPTORES = {
    "compartir": ("CIUDADANO", "Pulsé Compartir, pero el mensaje no alcanzó a otros vecinos. Mi intención no crea receptores donde la red no los tiene."),
    "convocar": ("CIUDADANO", "Intenté convocar al barrio y ninguna persona recibió la invitación. Todavía no hay una reunión que pueda dar por hecha."),
}
_EFECTOS = {
    "difusion": "La publicación viajó por las conexiones que conserva el historial. Su alcance depende de la red, sin contar dos veces a quien la recibe por varias rutas.",
    "sin_receptores": "La decisión no alcanzó a otros ciudadanos. El observatorio conserva el intento y permite revisar las conexiones sin inventar una audiencia.",
    "conversar_nuevo": "Escuchar abrió un vínculo recíproco en el grafo. La conversación no difundió el titular ni resolvió su veracidad.",
    "conversar_existente": "La conversación usó vínculos que ya existían. No se difundió el titular ni se volvió verdadero por escucharlo entre vecinos.",
    "entrevistar_nuevo": "La entrevista abrió un contacto directo con una fuente. Su testimonio queda separado de la comprobación documental.",
    "entrevistar_existente": "La entrevista usó un contacto que ya estaba en la red. El testimonio sigue siendo una pista y no una verificación.",
    "contrastar_cierto": "Los documentos respaldan el contenido del anuncio. Esta revisión no equivale a que una propuesta ya se haya ejecutado.",
    "contrastar_falso": "La revisión desmiente el mensaje y prepara una corrección. Su recepción queda en el historial y puede seguirse en el observatorio.",
    "contrastar_falso_cero": "La revisión desmiente el mensaje, pero la corrección no alcanzó a otros vecinos. Conservar una fuente y hacerla llegar son trabajos distintos.",
    "contrastar_opinion": "La publicación expresa una opinión atribuida. No recibe un sello de verdad ni se retira por expresar una prioridad diferente.",
    "desmentir": "El contenido fue retirado del árbol después de enviar la rectificación. El historial permanece y ninguna persona fue eliminada del grafo.",
    "desmentir_cero": "El contenido fue retirado del árbol, pero la corrección no alcanzó a otros vecinos. Retirar la publicación no borra lo que alguien pudo leer antes.",
    "rechazado": "El reporte fue rechazado. La publicación permanece en el árbol; una opinión legítima o un anuncio respaldado no se retira por desacuerdo.",
    "reservar": "La publicación queda en reserva editorial. No se difundió ni se eliminó, y la redacción todavía debe una respuesta al barrio.",
    "ignorar": "No se reenvió el mensaje. Permanece en Civitas y esta decisión no resolvió su veracidad ni inició una difusión.",
}


def reaccion_extendida(juego, tipo):
    """Reacción finita al registro real; no presenta números en el diálogo."""
    registro = getattr(juego, "ultimo_registro", None)
    if not isinstance(registro, dict):
        return None
    publicacion = registro.get("publicacion", {})
    identificador = publicacion.get("id")
    if identificador not in _REACCIONES:
        return None
    accion = _oficio(registro)
    if accion not in _VOZ_ACCION:
        return None
    if tipo == 1:
        if accion in _REACCION_SIN_RECEPTORES and not registro.get("alcance"):
            nombre, texto = _REACCION_SIN_RECEPTORES[accion]
            return texto, nombre
        return _REACCIONES[identificador][accion], _VOZ_ACCION[accion]
    if tipo != 2:
        return None
    if accion in ("conversar", "entrevistar"):
        nueva = bool(registro.get("efectos_red", {}).get("conexiones_creadas"))
        clave = accion + ("_nuevo" if nueva else "_existente")
    elif accion == "contrastar":
        verdadera = publicacion.get("verdadera")
        clave = ("contrastar_opinion" if verdadera is None else "contrastar_cierto" if verdadera
                 else "contrastar_falso" if registro.get("alcance") else "contrastar_falso_cero")
    elif accion == "desmentir":
        clave = ("rechazado" if not registro.get("eliminada") else
                 "desmentir" if registro.get("alcance") else "desmentir_cero")
    elif accion in ("compartir", "convocar"):
        clave = "difusion" if registro.get("alcance") else "sin_receptores"
    else:
        clave = accion
    return _EFECTOS[clave], "NARRADOR"


_GANADOR = {
    "juan": ("JUAN", "Recibo el encargo de gobernar. La pregunta de aquella familia sigue conmigo: el techo, las clases y la obligación de explicar cada etapa."),
    "adrian": ("ADRIAN", "Recibo el encargo de gobernar. La biblioteca que imaginamos tendrá que sostenerse con plazos y cuentas abiertas, además de palabras que entusiasman."),
    "laura": ("LAURA", "Recibo el encargo de gobernar. Quiero empezar por las puertas que alguien no pudo cruzar. Necesitaré que sigan señalándolas cuando termine el aplauso."),
    "camila": ("CAMILA", "Recibo el encargo de gobernar. La participación no termina en una pantalla ni en esta elección. Debe poder pedirnos explicaciones también mañana."),
    "empate": ("NARRADOR", "Ninguna candidatura tiene una victoria única. Ciudad Nova espera un recuento público; no habrá una proclamación inventada para cerrar antes la historia."),
}
_SOCIAL = {
    "informada": ("NARRADOR", "La plaza conserva voces distintas y una mesa donde todavía caben preguntas. El desacuerdo no desapareció; la ciudad encontró formas de escucharlo."),
    "reconstruccion": ("NARRADOR", "En la plaza algunas conversaciones vuelven a empezar y otras esperan una disculpa. La elección termina con trabajo pendiente para recuperar la confianza."),
    "fracturada": ("NARRADOR", "En la plaza hay grupos que ya no se hablan. El resultado no repara lo que hicieron los mensajes; la ciudad tendrá que reconstruir sus vínculos después de las urnas."),
}
_VALERIA = {
    "responsable": ("INFLUENCER", "Hoy voy a dejar el directo con sus pausas y sus correcciones. Quien vuelva a verlo merece conocer también dónde tuvimos que cambiar de idea."),
    "crisis": ("INFLUENCER", "Mi pantalla sigue llena y algunas personas ya no quieren escucharme. Voy a volver a los mensajes que ayudé a extender. Una despedida bonita no basta para repararlos."),
    "silencio": ("INFLUENCER", "Dejé varias preguntas fuera del directo. Quiero volver a esas conversaciones sin exigir que todos sigan esperando delante de mi pantalla."),
}
_CIERRE_CANDIDATURAS = {
    "juan": ("JUAN", "Seguiré pidiendo cuentas por las clases y las cubiertas, también desde fuera del despacho. El colegio no termina cuando acaba mi campaña."),
    "adrian": ("ADRIAN", "Mi prioridad seguirá siendo la cultura. Tendré que defenderla conversando con quienes eligieron otro comienzo para la ciudad."),
    "laura": ("LAURA", "El parque y los accesos seguirán aquí mañana. Quiero volver a recorrerlos con quienes tuvieron que buscar otra entrada."),
    "camila": ("CAMILA", "Conservaré el registro de las correcciones. La ciudad debe poder consultarlo sin tener que estar de acuerdo conmigo."),
}
_CIERRE_PERSONAL = {
    "reparacion": ("CIUDADANO", "Llamé a mi hermana para explicar las decisiones que tomamos. El mensaje del principio sigue en nuestra memoria; ahora también está la conversación que tuvimos después."),
    "pendiente": ("CIUDADANO", "Mi hermana todavía espera que le explique lo del colegio. Cuando termine esto voy a llamarla. Esa parte no puede hacerla el teléfono por mí."),
    "periodista": ("PERIODISTA", "Guardaré las fuentes, los errores y lo que aún no sabemos. Si alguien abre esta carpeta mañana, quiero que pueda seguir nuestras preguntas."),
    "salida": ("NARRADOR", "El ciudadano guarda el teléfono y acerca una silla. Por primera vez en mucho rato, la próxima conversación no empieza con una notificación."),
}


def estado_narrativo(juego, eleccion=None):
    """Claves de desenlace derivadas de evidencias; consultar no altera el juego.

    Los quince cierres principales son cuatro candidaturas o empate por tres
    estados cívicos. Cada uno incorpora uno de tres arcos de Valeria. Las voces
    son módulos finitos, no cuarenta y cinco grabaciones con datos variables.
    """
    eleccion = juego.resultado_electoral() if eleccion is None else eleccion
    calidad = float(eleccion.get("calidad", 0))
    social = "informada" if calidad >= 50 else "reconstruccion" if calidad >= 20 else "fracturada"
    ganador = "empate"
    ganadores = eleccion.get("ganadores", [])
    if not eleccion.get("empate", len(ganadores) != 1) and len(ganadores) == 1:
        for candidato in getattr(juego, "candidatos", ()):
            if candidato.nombre == ganadores[0] and candidato.id in _GANADOR:
                ganador = candidato.id
                break
    nuevos = [r for r in getattr(juego, "historial", ()) if r.get("publicacion", {}).get("id") in CASOS_NUEVOS]
    reparaciones = sum(_oficio(r) == "contrastar" or (_oficio(r) == "desmentir" and r.get("eliminada"))
                       for r in nuevos)
    dano = sum(_oficio(r) in ("compartir", "convocar") and r.get("alcance", 0) > 0
               and (r.get("publicacion", {}).get("verdadera") is False or r.get("publicacion", {}).get("danina"))
               for r in nuevos)
    if reparaciones > dano and reparaciones:
        valeria = "responsable"
    elif dano:
        valeria = "crisis"
    else:
        valeria = "silencio"
    colegio = next((r for r in nuevos if r.get("publicacion", {}).get("id") == 25), None)
    reparado = bool(colegio and (_oficio(colegio) in ("contrastar", "conversar", "entrevistar")
                                or (_oficio(colegio) in ("compartir", "convocar") and colegio.get("alcance"))))
    return {"ganador": ganador, "ciudad": social, "valeria": valeria,
            "colegio": "reparacion" if reparado else "pendiente"}


def epilogo_extendido(juego, eleccion=None):
    """Devuelve un desenlace modular completo para lectura, voz y escena."""
    estado = estado_narrativo(juego, eleccion)
    lineas = [_GANADOR[estado["ganador"]], _SOCIAL[estado["ciudad"]], _VALERIA[estado["valeria"]]]
    for clave, linea in _CIERRE_CANDIDATURAS.items():
        if clave != estado["ganador"]:
            lineas.append(linea)
    lineas.extend((_CIERRE_PERSONAL[estado["colegio"]], _CIERRE_PERSONAL["periodista"], _CIERRE_PERSONAL["salida"]))
    return lineas


def texto_epilogo_extendido(juego, eleccion=None):
    """Versión del mismo desenlace para paneles de texto sin lector secuencial."""
    return "\n\n".join(texto for _, texto in epilogo_extendido(juego, eleccion))


def _frases_posibles():
    frases = []
    for dialogos in (*DIALOGOS_NUEVOS.values(), *DIALOGOS_OVERRIDE.values()):
        frases.extend(dialogos)
    frases.extend(_MEMORIAS.values())
    frases.append(_TENSION)
    for reacciones in _REACCIONES.values():
        frases.extend((_VOZ_ACCION[clave], texto) for clave, texto in reacciones.items())
    frases.extend(_REACCION_SIN_RECEPTORES.values())
    frases.extend(("NARRADOR", texto) for texto in _EFECTOS.values())
    for bloque in (_GANADOR, _SOCIAL, _VALERIA, _CIERRE_CANDIDATURAS, _CIERRE_PERSONAL):
        frases.extend(bloque.values())
    return tuple(dict.fromkeys(frases))


FRASES_POSIBLES = _frases_posibles()
