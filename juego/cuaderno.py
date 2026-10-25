"""Documentos ficticios y recuerdos de la campaña de CIVICA.

El cuaderno acompaña las publicaciones de las campañas clásica y extendida sin modificar sus reglas,
el ABB, el grafo ni el guardado. Las pistas invitan a observar fuentes y contexto;
no son cuestionarios ni muestran una etiqueta de veracidad antes de decidir.
Todas las rutas son relativas al paquete artístico existente ``assets/rediseno``.
"""


CASOS = {
    50: {
        "acto": "ACTO I · Una ciudad que escucha",
        "titulo": "La puerta del colegio",
        "lugar": "Café Central · Una mañana de campaña",
        "objetivo": "Acompañar la preocupación de las familias sin apresurar una publicación.",
        "fondo": "fondos/cafe_exterior.png",
        "pistas": [
            {
                "titulo": "Fuente original · Acta de la reunión educativa",
                "texto": "Archivo municipal: «Juan Torres solicita revisar las cubiertas del colegio y mantener las clases durante las obras». La foto compartida solo muestra el encabezado «Revisión del colegio».",
                "pregunta": "Compara lo que propone el acta con lo que afirma el mensaje que circula.",
            },
            {
                "titulo": "Fecha y contexto · Dos avisos diferentes",
                "texto": "El cartel junto a la entrada dice «Acceso lateral durante el mantenimiento». Es de la semana pasada. La captura que llegó hoy no conserva esa fecha ni muestra el acceso alternativo.",
                "pregunta": "Observa qué cambia al recuperar la fecha y el aviso completo.",
            },
            {
                "titulo": "Testimonio · Una madre a la salida",
                "texto": "«Cuando vi “cerrar” pensé en cambiar a mi hija de colegio. La profesora nos indicó otra puerta para mañana, pero en el grupo nadie ha compartido ese aviso».",
                "pregunta": "Distingue la preocupación de la familia de la evidencia sobre el funcionamiento del colegio.",
            },
        ],
        "cierre": "La puerta del colegio recuerda cuánto pesa una palabra en una conversación familiar.",
    },
    30: {
        "acto": "ACTO I · Una ciudad que escucha",
        "titulo": "Una propuesta sobre la mesa",
        "lugar": "Café Central · El programa abierto",
        "objetivo": "Leer una propuesta completa antes de hacerla circular por el barrio.",
        "fondo": "fondos/cafe_interior.png",
        "pistas": [
            {
                "titulo": "Fuente original · Programa de Adrián Morales",
                "texto": "La página de campaña presenta «Red de lectura para los barrios»: bibliotecas, talleres culturales y espacios de estudio. El documento identifica a Adrián Morales como responsable de la propuesta.",
                "pregunta": "Observa quién firma el programa y qué compromisos concretos contiene.",
            },
            {
                "titulo": "Fecha y contexto · Presentación pública",
                "texto": "La invitación del día señala «Presentación de una nueva propuesta». El programa habla de etapas futuras; no afirma que todos sus servicios ya estén disponibles.",
                "pregunta": "Separa el anuncio de una propuesta de la ejecución de sus etapas.",
            },
            {
                "titulo": "Testimonio · Un vecino con el folleto",
                "texto": "«Asistí a la presentación y guardé este folleto. Me interesa el espacio de estudio, aunque todavía quiero saber cómo se financiará. Que me guste la idea no responde todo».",
                "pregunta": "Distingue la existencia del anuncio de la opinión del vecino sobre su viabilidad.",
            },
        ],
        "cierre": "El folleto conserva una propuesta y también las dudas que una comunidad puede plantearle.",
    },
    70: {
        "acto": "ACTO II · Lo que compartimos",
        "titulo": "El parque de todos",
        "lugar": "Ciudad Nova · El aviso del parque",
        "objetivo": "Ayudar a los vecinos a organizarse con información útil y completa.",
        "fondo": "fondos/ciudad.png",
        "pistas": [
            {
                "titulo": "Fuente original · Aviso de servicios de la ciudad",
                "texto": "El boletín municipal anuncia mantenimiento del parque central: revisión de juegos, poda y reparación de senderos. El equipo de Laura Ríos ha compartido el enlace al boletín.",
                "pregunta": "Sigue el aviso hasta su emisor original, además de quien lo compartió.",
            },
            {
                "titulo": "Fecha y contexto · Trabajo por sectores",
                "texto": "El calendario del boletín programa las labores para esta semana y aclara «Intervenciones por sectores». La imagen del feed recorta el cuadro con los horarios de cada acceso.",
                "pregunta": "Observa qué horarios y zonas necesitaría conocer una persona que visite el parque.",
            },
            {
                "titulo": "Testimonio · Un vecino que cruza el parque",
                "texto": "«Hoy vi señalizado el sendero de los juegos. Rodeé por el camino lateral para llegar al trabajo. Mi madre necesita saber por dónde puede pasar mañana».",
                "pregunta": "Relaciona el testimonio con el calendario sin extenderlo a todas las entradas.",
            },
        ],
        "cierre": "El recorrido del parque conecta una noticia pequeña con la vida cotidiana del barrio.",
    },
    20: {
        "acto": "ACTO II · Lo que compartimos",
        "titulo": "Una biblioteca por construir",
        "lugar": "Mesa de investigación · Los planos de la biblioteca",
        "objetivo": "Reconocer el respaldo de un proyecto sin convertir sus planes en resultados terminados.",
        "fondo": "fondos/investigacion.png",
        "pistas": [
            {
                "titulo": "Fuente original · Expediente de la biblioteca",
                "texto": "El archivo público incluye el acuerdo de construcción de una nueva biblioteca y una partida asignada. La iniciativa cultural aparece también en el programa de Adrián Morales.",
                "pregunta": "Diferencia el respaldo del proyecto de las declaraciones de campaña que lo mencionan.",
            },
            {
                "titulo": "Fecha y contexto · Un cronograma de obra",
                "texto": "El expediente sitúa el inicio después de la preparación del terreno. El plano está rotulado «Proyecto de construcción» y no incluye una fecha de inauguración confirmada.",
                "pregunta": "Observa qué parte del proceso está anunciada y qué fecha aún no puede darse por segura.",
            },
            {
                "titulo": "Testimonio · Una lectora del barrio",
                "texto": "«Consulté el expediente porque mi grupo necesita una sala. Me alegra que exista el proyecto. Hasta que termine la obra seguiremos reuniéndonos en el café».",
                "pregunta": "Conserva tanto la ilusión de la lectora como el estado actual de la construcción.",
            },
        ],
        "cierre": "Los planos guardan la ilusión de una biblioteca y la distancia entre anunciar y terminar una obra.",
    },
    60: {
        "acto": "ACTO III · La confianza en juego",
        "titulo": "El mensaje sin firma",
        "lugar": "Observatorio de Civitas · Una cadena que crece",
        "objetivo": "Cuidar a las personas cuando una acusación circula más rápido que sus fuentes.",
        "fondo": "fondos/observatorio.png",
        "pistas": [
            {
                "titulo": "Fuente original · El inicio de la cadena",
                "texto": "La captura más antigua recuperada dice «Me lo contó alguien cercano a Camila; pásalo antes de que lo borren». No identifica autor, hecho concreto ni documento que respalde la insinuación.",
                "pregunta": "Observa si cada reenvío aporta una fuente nueva o solo repite la misma frase.",
            },
            {
                "titulo": "Fecha y contexto · Un recorte que viaja",
                "texto": "La imagen adjunta tiene el encabezado cortado. Al compararla con el archivo completo, aparece una conversación vecinal de otra jornada que no menciona la acusación contra Camila Vega.",
                "pregunta": "Compara el recorte con la conversación de la que salió antes de unir ambos mensajes.",
            },
            {
                "titulo": "Testimonio · Una vecina en la conversación",
                "texto": "«Lo reenvié porque me asustó. Ahora tres personas dicen que lo saben de buena fuente y las tres me enviaron mi propia captura. No había notado que volvíamos al mismo sitio».",
                "pregunta": "Sigue el recorrido de los mensajes para distinguir varias voces de varias fuentes independientes.",
            },
        ],
        "cierre": "La cadena sin firma deja una huella de cómo una repetición puede parecer una confirmación.",
    },
    80: {
        "acto": "ACTO III · La confianza en juego",
        "titulo": "La última captura",
        "lugar": "Mesa de investigación · Antes de la elección",
        "objetivo": "Decidir qué hacer con una cifra llamativa sin entregar a un titular la voz de toda la ciudad.",
        "fondo": "fondos/investigacion.png",
        "pistas": [
            {
                "titulo": "Fuente original · El formulario de la encuesta",
                "texto": "El enlace lleva a una votación abierta en un grupo favorable a Juan Torres. La pregunta era «¿A quién prefieres?». El titular reenviado la presenta como si ya conociera al próximo alcalde.",
                "pregunta": "Compara a quiénes podía llegar el formulario con la población que el titular dice representar.",
            },
            {
                "titulo": "Fecha y contexto · Datos fuera del encuadre",
                "texto": "La captura no muestra fecha, número de respuestas ni método de selección. En el formulario original consta que se abrió antes de los últimos anuncios de campaña.",
                "pregunta": "Observa qué límites desaparecen cuando una cifra se separa de su fecha y su método.",
            },
            {
                "titulo": "Testimonio · La persona que abrió el formulario",
                "texto": "«Quería conocer a mi grupo. Cualquiera podía pasar el enlace y responder. Nunca lo planteé como un recuento de votos de Ciudad Nova».",
                "pregunta": "Distingue una preferencia recogida en un grupo del resultado de una elección completa.",
            },
        ],
        "cierre": "La última captura recuerda que una cifra necesita contexto antes de hablar por una ciudad.",
    },
}


PERFILES = [
    {
        "nombre": "CIUDADANO",
        "rol": "La voz del barrio",
        "deseo": "Mantener informadas a sus personas cercanas y cuidar los lugares que comparten.",
        "conflicto": "Quiere ayudar enseguida, pero teme descubrir que un mensaje suyo lastimó a otra persona.",
        "recurso": "personajes/ciudadano_retrato.png",
    },
    {
        "nombre": "PERIODISTA",
        "rol": "La compañera de investigación",
        "deseo": "Publicar información que los vecinos puedan comprobar y volver a usar.",
        "conflicto": "Necesita tiempo para contrastar mientras la ciudad le exige respuestas inmediatas.",
        "recurso": "personajes/periodista_retrato.png",
    },
]


from juego.campana_extendida import CASOS_NUEVOS, PERFILES_NUEVOS

CASOS.update(CASOS_NUEVOS)
PERFILES.extend(PERFILES_NUEVOS)


GLOSARIO = {
    "Fuente original": "El lugar donde una información apareció primero: un documento, una declaración o un registro completo. Muchos reenvíos de una misma captura siguen siendo una sola fuente.",
    "Contexto": "Los detalles que permiten entender un mensaje: cuándo ocurrió, dónde, quién habla y qué quedó fuera del recorte.",
    "Rumor": "Una afirmación que circula sin respaldo suficiente. Repetirla muchas veces no añade pruebas.",
    "Corrección": "Información que aclara un error y puede recorrer las mismas conexiones que llevaron el mensaje inicial.",
    "Alcance": "Las personas distintas a las que llega una difusión. En CIVICA no incluye al emisor ni cuenta dos veces a quien recibe por varias rutas.",
    "ABB": "El archivo de publicaciones ordenado por sus números. Buscar, insertar y retirar contenido cambia ese archivo, no las personas que viven en la ciudad.",
    "Grafo": "El mapa de personas y conexiones de Civitas. Una flecha indica hacia dónde puede viajar la información; la conexión de vuelta puede no existir.",
    "BFS y DFS": "Dos maneras de explorar el mapa. BFS avanza por niveles de cercanía; DFS sigue una rama antes de probar otras. Explorar el mapa permite observarlo sin tomar otra decisión.",
}


def _caso_campana(juego, identificador):
    caso = CASOS[identificador]
    if identificador == 80 and getattr(juego, "campana", "clasica") == "extendida":
        return dict(caso, titulo="La cifra sin método",
                    cierre="La cifra sin método recuerda que una encuesta necesita contexto antes de hablar por una ciudad.")
    return caso


def caso_actual(juego):
    """Devuelve el caso visible, el último decidido o el inicio de la campaña."""
    publicacion = juego.obtener_publicacion_actual()
    identificador = getattr(publicacion, "id", None)
    if identificador in CASOS:
        return _caso_campana(juego, identificador)
    anterior = getattr(juego, "ultima_publicacion_id", None)
    return _caso_campana(juego, anterior if anterior in CASOS else 50)


def recuerdos(juego):
    """Construye la galería desde decisiones registradas, sin modificar la partida.

    Cada caso aparece una sola vez y en el orden de su primera decisión. Los
    recursos reutilizan fondos existentes: no se presentan como CGs nuevas. El
    cierre de campaña solo se añade una vez que ``juego.finalizada`` es verdadero.
    """
    galeria = []
    incluidos = set()
    acciones = {
        "compartir": "compartir el mensaje",
        "verificar": "verificar la publicación",
        "ignorar": "dejar pasar el mensaje",
        "reportar": "reportar la publicación",
        "conversar": "escuchar al vecindario y cuidar sus vínculos",
        "convocar": "convocar al barrio",
        "contrastar": "contrastar las fuentes",
        "entrevistar": "entrevistar a una fuente",
        "desmentir": "desmentir y denunciar el contenido",
        "reservar": "mantener el contenido en reserva editorial",
    }
    for registro in juego.historial:
        identificador = registro.get("publicacion", {}).get("id")
        if identificador not in CASOS or identificador in incluidos:
            continue
        incluidos.add(identificador)
        caso = _caso_campana(juego, identificador)
        accion = acciones.get(registro.get("accion_rol", registro.get("accion")), "actuar sobre la publicación")
        explicacion = registro.get("explicacion", "La decisión quedó guardada en la historia de Civitas.")
        galeria.append({
            "id": identificador,
            "titulo": caso["titulo"],
            "recurso": caso["fondo"],
            "texto": f'{caso["cierre"]} Elegiste {accion}. {explicacion}',
        })
    if juego.finalizada:
        galeria.append({
            "id": "final",
            "titulo": "La ciudad que queda",
            "recurso": "fondos/cafe_exterior.png",
            "texto": f"La campaña termina con {len(galeria)} recuerdos de tus decisiones. En el Café Central queda una conversación abierta sobre la ciudad que construyeron sus mensajes.",
        })
    return galeria
