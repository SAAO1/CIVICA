"""Planos de la novela vinculados al texto exacto y al caso real."""
from infraestructura.recursos import RAIZ

FUENTES={50:"aviso_cafe",90:"parque_contexto",110:"audio_contexto",
         40:"correccion_contexto",120:"urnas_contexto",35:"voto_contexto"}
CATALOGO_PULIDO={}
for identificador,fuente in list(FUENTES.items())+[("foro","foro_cuatro")]:
    nombre="foro" if identificador=="foro" else "caso_"+str(identificador)
    CATALOGO_PULIDO["pulido_"+nombre]={
        "video":f"assets/novela/pulido/videos/{nombre}.mp4",
        "poster":f"assets/novela/pulido/cg/{fuente}.png",
        "inicio":f"assets/novela/pulido/videos/{nombre}_inicio.png",
        "titulo":"Cuatro propuestas para Ciudad Nova" if nombre=="foro" else "Cada mensaje tiene un contexto",
        "bucle":True,"duracion":6.0,"recorte_inferior":.155,
    }

for actor in ("juan", "adrian", "laura", "camila"):
    CATALOGO_PULIDO["pulido_foro_"+actor] = {
        "video": f"assets/novela/prologo/videos/{actor}.mp4",
        "poster": f"assets/novela/prologo/cg/{actor}.png",
        "inicio": f"assets/novela/prologo/videos/{actor}_inicio.png",
        "titulo": "Cuatro propuestas para Ciudad Nova",
        "bucle": True, "duracion": 6.0, "anclaje_y": 0.0,
    }

def campana_visual(juego):
    return getattr(juego,"campana",None)=="feria"

def _caso(juego):
    publicacion=juego.obtener_publicacion_actual()
    return getattr(publicacion,"id",None) or getattr(juego,"ultima_publicacion_id",None) or 50

def es_foro(juego,texto,nombre):
    from interfaz.novela.guion import contexto_candidaturas
    return (nombre,texto) in contexto_candidaturas(juego)

def elegir_plano(juego,texto,nombre,tipo_resultado=None):
    if not campana_visual(juego) or tipo_resultado == 3:
        return None
    actor = str(nombre).upper().strip()
    if es_foro(juego,texto,nombre):
        if actor == "NARRADOR":
            return "pulido_foro"
        if actor in ("JUAN", "ADRIAN", "LAURA", "CAMILA"):
            return "pulido_foro_"+actor.lower()
    narrador=actor=="NARRADOR"
    if narrador and str(texto).startswith("Faltan cuarenta y ocho horas"):
        return "pulido_foro"
    id=_caso(juego)
    if narrador and id in FUENTES:
        return "pulido_caso_"+str(id)
    registro = getattr(juego, "ultimo_registro", None) or {}
    oficio = (registro.get("accion_rol") or getattr(juego, "ultima_accion_rol", None)
              or getattr(juego, "ultima_accion", None))
    if tipo_resultado == 1 and oficio and oficio not in ("ignorar", "reservar"):
        return "pulido_caso_"+str(id) if id in FUENTES else None
    # La voz de cada personaje deja ver el sprite con su expresion real.
    return None

def fondo_intervencion(juego,texto,nombre):
    if not campana_visual(juego):
        return None
    if es_foro(juego,texto,nombre):
        return "assets/expansion/siete_actos/fondos/debate.jpg"
    from juego.puesta_escena import escenario_actual
    return escenario_actual(juego)["fondo"]


def expresion_actor(juego, nombre, texto=""):
    """Los presentes reaccionan al efecto real del caso, además de sus palabras."""
    from juego.puesta_escena import expresion_dialogo
    nombre = str(nombre).upper().strip()
    base = expresion_dialogo(juego, nombre, texto)
    if not campana_visual(juego):
        return base
    registro = getattr(juego, "ultimo_registro", None)
    if (isinstance(registro, dict)
            and registro.get("publicacion", {}).get("id") == _caso(juego)):
        cambios = registro.get("cambios_reales", {})
        if not cambios:
            antes, despues = registro.get("antes", {}), registro.get("despues", {})
            cambios = {k: despues.get(k, v)-v for k, v in antes.items()}
        if cambios.get("desinformacion", 0) > 0:
            senalado = str(registro.get("publicacion", {}).get("candidato_id", "")).upper()
            if nombre == senalado:
                return "sorprendido"
            if nombre == "PERIODISTA":
                return "enojado"
            return "triste" if nombre == "INFLUENCER" else "preocupado"
        if cambios.get("confianza", 0) < 0:
            return "enojado" if nombre == "PERIODISTA" else "triste"
        correccion = (registro.get("propagacion") or {}).get("correccion", False)
        prueba = (registro.get("editor") or {}).get("evidencia_pertinente", False)
        reparacion = (correccion or registro.get("eliminada", False)
                      or cambios.get("info_verificada", 0) > 0)
        if reparacion and prueba:
            return "sonrisa"
        if cambios.get("conflictos", 0) > 0:
            return "enojado" if nombre in ("LAURA", "PERIODISTA") else "preocupado"
        if cambios.get("confianza", 0) > 0 or cambios.get("participacion", 0) > 0:
            return "sonrisa"
    # Una candidatura que escucha conserva atención; no queda inexpresiva
    # simplemente porque la frase de otra persona no contenga una palabra clave.
    if base == "neutral" and nombre in ("JUAN", "ADRIAN", "LAURA", "CAMILA", "INFLUENCER"):
        return "pensativo" if not texto else "decidido"
    return base
