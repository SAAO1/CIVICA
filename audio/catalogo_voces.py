"""Identidades y claves del doblaje neuronal preproducido de CIVICA.

El juego sólo lee estos archivos locales. El servicio de síntesis se utiliza
de forma explícita desde herramientas/producir_voces.py, nunca al jugar.
"""
import hashlib
import json
import re
from pathlib import Path

from recursos import RAIZ

CARPETA_VOCES = RAIZ / "assets/audio/voces"
PERFILES = {
    "CIUDADANO": {"voz": "es-CO-GonzaloNeural", "nombre": "Gonzalo", "idioma": "es-CO",
                  "genero": "Male", "ritmo": "-3%", "tono": "+0Hz"},
    "PERIODISTA": {"voz": "es-CO-SalomeNeural", "nombre": "Salomé", "idioma": "es-CO",
                   "genero": "Female", "ritmo": "-4%", "tono": "+0Hz"},
    "NARRADOR": {"voz": "es-MX-JorgeNeural", "nombre": "Jorge", "idioma": "es-MX",
                 "genero": "Male", "ritmo": "-6%", "tono": "-2Hz"},
    "INFLUENCER": {"voz": "es-MX-DaliaNeural", "nombre": "Dalia · Valeria Cruz", "idioma": "es-MX",
                   "genero": "Female", "ritmo": "+1%", "tono": "+0Hz"},
    "JUAN": {"voz": "es-ES-AlvaroNeural", "nombre": "Álvaro · Juan Torres", "idioma": "es-ES",
             "genero": "Male", "ritmo": "-4%", "tono": "-1Hz"},
    "ADRIAN": {"voz": "es-AR-TomasNeural", "nombre": "Tomás · Adrián Morales", "idioma": "es-AR",
               "genero": "Male", "ritmo": "-5%", "tono": "-2Hz"},
    "LAURA": {"voz": "es-ES-ElviraNeural", "nombre": "Elvira · Laura Ríos", "idioma": "es-ES",
              "genero": "Female", "ritmo": "-4%", "tono": "-1Hz"},
    "CAMILA": {"voz": "es-CL-CatalinaNeural", "nombre": "Catalina · Camila Vega", "idioma": "es-CL",
               "genero": "Female", "ritmo": "-3%", "tono": "+0Hz"},
}

ETIQUETAS_INDICADORES = {
    "info_verificada": "Información verificada", "confianza": "Confianza",
    "desinformacion": "Desinformación", "convivencia": "Convivencia",
    "bienestar_digital": "Bienestar digital", "conflictos": "Conflictos",
    "participacion": "Participación",
}


def segmentos_indicadores(registro, incluir_puntos=True):
    """Variaciones efectivas, en el mismo orden de las tarjetas de impacto.

    La clave identifica una tarjeta; el texto sólo sirve al doblaje. No se
    concatena con los subtítulos del diálogo ni se confunden deltas solicitados
    con cambios que quedaron recortados al límite 0–100.
    """
    antes, despues = registro.get("antes", {}), registro.get("despues", {})
    segmentos = []
    for clave, etiqueta in ETIQUETAS_INDICADORES.items():
        if clave not in antes or clave not in despues:
            continue
        delta = despues[clave] - antes[clave]
        if delta:
            segmentos.append({"clave": clave, "texto": f"{etiqueta} {delta:+g}."})
    if incluir_puntos:
        segmentos.append({"clave": "puntos", "texto": f"Puntuación de la acción: {registro.get('puntos', 0):+g}."})
    return segmentos


def normalizar_texto(texto):
    return " ".join(str(texto or "").split())


def clave_clip(hablante, texto):
    nombre = str(hablante or "NARRADOR").strip().upper()
    identidad = PERFILES.get(nombre, PERFILES["NARRADOR"])["voz"]
    contenido = identidad + "\n" + normalizar_texto(texto)
    return hashlib.sha256(contenido.encode("utf-8")).hexdigest()[:24]


def frases_texto(texto):
    """Respeta las pausas de frases, sin partir decimales ni abreviaturas."""
    return [f.strip() for f in re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÜÑ¿¡])", normalizar_texto(texto)) if f.strip()]


def texto_grupo(texto):
    """Evita fijar un nombre personal en las consecuencias multijugador."""
    return re.sub(r"^Ciudad Nova refleja la decisión de [^:]+:",
                  "Ciudad Nova refleja la decisión del grupo:", texto)


def partes_resultado(texto):
    """Bloques fieles a las cifras para nombres y combinaciones nuevos."""
    resultado = re.fullmatch(
        r"Ciudad Nova refleja la decisión de [^:]+: (.+)\. Puntuación de la acción: ([+-]\d+)\.", texto)
    if not resultado:
        return []
    cambios, puntos = resultado.groups()
    return (["Ciudad Nova refleja la decisión del grupo."]
            + [cambio[0].upper() + cambio[1:] + "." for cambio in cambios.split(", ")]
            + [f"Puntuación de la acción: {puntos}."])


def cargar_manifest(carpeta=CARPETA_VOCES):
    try:
        with (Path(carpeta) / "manifest.json").open(encoding="utf-8") as archivo:
            datos = json.load(archivo)
        if datos.get("version") != 1 or not isinstance(datos.get("clips"), dict):
            return {}
        datos["clips"] = {clave: entrada for clave, entrada in datos["clips"].items()
                          if isinstance(entrada, dict) and isinstance(entrada.get("archivo"), str)}
        return datos
    except (OSError, ValueError, TypeError):
        return {}


def ruta_clip(entrada, carpeta=CARPETA_VOCES):
    """Un manifest no puede abrir archivos fuera del paquete de voces."""
    if not isinstance(entrada, dict):
        return None
    base = Path(carpeta).resolve()
    ruta = (base / str(entrada.get("archivo", ""))).resolve()
    return ruta if ruta.is_relative_to(base) and ruta.is_file() else None


def pronunciacion(texto):
    texto = re.sub(r"\bABB\b", "árbol binario de búsqueda", texto)
    texto = texto.replace("Civitas", "Cívitas")
    # Los signos aislados se leen como variaciones, sin alterar los subtítulos.
    texto = re.sub(r"(?<=\s)\+(\d+)", r"más \1", texto)
    texto = re.sub(r"(?<=\s)-(\d+)", r"menos \1", texto)
    return texto
