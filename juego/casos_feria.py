"""Seis investigaciones de la campaña de feria, basadas en el guion existente."""
from copy import deepcopy

from juego.cuaderno import CASOS

IDS_FERIA = (50, 90, 110, 40, 120, 35)
ROLES_FERIA = ("ciudadano", "periodista")
CERTEZAS = ("pendiente", "probable", "confirmada")
TIPOS_DOCUMENTALES = frozenset(("documento", "contexto", "medio"))
ACCIONES_CON_PRUEBA = frozenset(("contrastar", "desmentir", "rectificar"))

# La persona de un testimonio no es necesariamente el contacto del grafo
# que acompaña la entrevista. Esta atribución visual no cambia relaciones.
_FUENTES_TESTIMONIO = {
    50: {"fuente_id": "madre_colegio", "fuente_nombre": "Madre de una estudiante",
         "fuente_retrato": "avatar:maria"},
    90: {"fuente_id": "valeria", "fuente_nombre": "Valeria Cruz",
         "fuente_retrato": "assets/expansion/siete_actos/personajes/influencer_neutral.png"},
    110: {"fuente_id": "maria", "fuente_nombre": "María · Técnica de sonido",
          "fuente_retrato": "avatar:maria"},
    40: {"fuente_id": "valeria", "fuente_nombre": "Valeria Cruz",
         "fuente_retrato": "assets/expansion/siete_actos/personajes/influencer_neutral.png"},
    120: {"fuente_id": "abuelo", "fuente_nombre": "El abuelo del ciudadano",
          "fuente_retrato": "assets/novela/pulido/cg/urnas_contexto.png",
          "fuente_recorte": {"x": .03, "y": .10, "ancho": .23, "alto": .72}},
    35: {"fuente_id": "valeria", "fuente_nombre": "Valeria Cruz",
         "fuente_retrato": "assets/expansion/siete_actos/personajes/influencer_neutral.png"},
}

_FICHAS = {
    50: ("La puerta del colegio", "captura", "luis", "Luis", 72, 100,
         "Amplía el recorte hasta recuperar el encabezado y la fecha del acta.",
         "«Juan quiere cerrar el colegio». Una captura oculta la fecha y el párrafo siguiente.",
         "El acta pide revisar las cubiertas y mantener las clases con acceso lateral.",
         "assets/rediseno/fondos/cafe_exterior.png"),
    90: ("El parque fuera de cuadro", "captura", "valeria", "Valeria", 75, 100,
         "Mueve el encuadre para encontrar la entrada que quedó fuera del video.",
         "El encuadre muestra una valla. Valeria anuncia que todos los parques cerrarán.",
         "Fuera del recorte sigue abierto el acceso lateral: hay mantenimiento por sectores.",
         "assets/expansion/siete_actos/fondos/estudio.jpg"),
    110: ("Los segundos que faltan", "audio", "maria", "María", 55, 75,
          "Desplaza el cursor y escucha el tramo que precede a la frase recortada.",
          "«...cobrar por votar...» La cadena omite el comienzo de la intervención.",
          "«Si alguien pretende cobrar por votar, denuncia ese engaño». Camila advierte contra el cobro.",
          "assets/expansion/siete_actos/fondos/redaccion.jpg"),
    40: ("Un canal que recuerda", "captura", "valeria", "Valeria", 65, 100,
         "Abre el registro completo y busca a qué mensaje y fuente apunta la corrección.",
         "Una tarjeta promete un canal público de correcciones. ¿Conservará los errores?",
         "La propuesta enlaza mensaje original, fuentes y registro de cambios; no garantiza alcance universal.",
         "assets/expansion/siete_actos/fondos/estudio.jpg"),
    120: ("Una entrada para el abuelo", "mapa", "ines", "Inés", 70, 90,
          "Recorre el mapa hasta localizar el acceso lateral de la jornada actual.",
          "El mapa recortado no muestra la rampa ni conserva la fecha de la jornada.",
          "El mapa oficial de hoy conserva la entrada lateral accesible. No cambia el puesto asignado.",
          "assets/expansion/siete_actos/fondos/urnas.jpg"),
    35: ("La palabra que borraron", "captura", "luis", "Luis", 75, 100,
         "Recupera el margen izquierdo del mensaje atribuido a Adrián.",
         "«Comentar sustituye el voto». La captura conserva el avatar del candidato.",
         "El mensaje completo dice: «Comentar NO sustituye el voto». Las interacciones no cuentan como votos.",
         "assets/expansion/siete_actos/fondos/urnas.jpg"),
}

LUGARES = (
    {"id": "archivo", "nombre": "Archivo público", "descripcion": "Expediente original y documentos firmados.", "coste": 1},
    {"id": "barrio", "nombre": "Café y vecindario", "descripcion": "Hablar con la persona afectada y conocer su contexto.", "coste": 1},
    {"id": "redaccion", "nombre": "Mesa de redacción", "descripcion": "Revisar fechas, versiones y contexto del mensaje.", "coste": 1},
)


def crear_caso(identificador):
    base = deepcopy(CASOS[identificador])
    titulo, tipo, npc_id, npc_nombre, minimo, maximo, consigna, recorte, completo, fondo = _FICHAS[identificador]
    numero = IDS_FERIA.index(identificador) + 1
    pistas = base["pistas"]
    fuente_testimonio = deepcopy(_FUENTES_TESTIMONIO[identificador])
    evidencias = []
    for indice, (sufijo, rol, lugar, clase) in enumerate((
        ("documento", "periodista", "archivo", "documento"),
        ("contexto", "ambos", "redaccion", "contexto"),
        ("testimonio", "ciudadano", "barrio", "testimonio"),
    )):
        evidencias.append({
            "id": f"{identificador}:{sufijo}", "caso_id": identificador,
            "titulo": pistas[indice]["titulo"], "texto": pistas[indice]["texto"],
            "origen": lugar, "tipo": clase, "rol": rol,
            **(fuente_testimonio if clase == "testimonio" else {
                "fuente_id": "archivo_publico" if clase == "documento" else "registro_contexto",
                "fuente_nombre": "Archivo público" if clase == "documento" else "Registro de fecha y contexto",
                "fuente_retrato": "",
            }),
        })
    evidencias.append({
        "id": f"{identificador}:medio", "caso_id": identificador,
        "titulo": "La pieza completa", "texto": completo, "origen": "visor",
        "tipo": "medio", "rol": "ambos",
        "fuente_id": "pieza_original", "fuente_nombre": "La pieza completa",
        "fuente_retrato": "",
    })
    return {
        "id": identificador, "numero": numero, "total": 6,
        "capitulo": (numero - 1) // 2 + 1, "titulo": titulo,
        "objetivo": base["objetivo"], "lugar": base["lugar"], "fondo": fondo,
        "npc_id": npc_id, "npc_nombre": npc_nombre, "evidencias": evidencias,
        **fuente_testimonio,
        "medio": {"tipo": tipo, "minimo": 0, "maximo": 100, "consigna": consigna,
                  "texto_inicial": recorte, "texto_completo": completo,
                  "solucion_min": minimo, "solucion_max": maximo},
        "preguntas": [
            {"id": "contexto", "texto": "¿Qué ocurrió antes de este mensaje?"},
            {"id": "origen", "texto": "¿Puedes mostrarme de dónde salió?"},
            {"id": "presionar", "texto": "Necesito una respuesta ahora"},
        ],
    }
