"""Prepara paisajes sonoros y foley reales, con procedencia verificable.

Las dependencias sólo hacen falta para producir los WAV; el juego usa Qt.
Ejemplo: python herramientas/preparar_ambientes.py --descargar
Los originales descargados quedan en .tmp/audio_fuentes, fuera de la entrega.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
import wave

RAIZ = Path(__file__).resolve().parents[1]
CACHE = RAIZ / ".tmp/audio_fuentes"
SALIDA = RAIZ / "assets/audio/expansion"
DEPS = RAIZ / ".tmp/audio_deps"
if DEPS.is_dir():
    sys.path.insert(0, str(DEPS))
try:
    import numpy as np
except ImportError as exc:
    raise SystemExit("Para producir audio instala numpy e imageio-ffmpeg (ver docs/audio_ambiental.md).") from exc

HZ = 32000
DURACION = 45
FUENTES = {
    "cafe": ("2561", "coffee-shop-at-the-capucins", "grabacion_de_campo"),
    "plaza": ("0526", "pedestrian-place", "grabacion_de_campo"),
    "calle": ("0527", "small-pedestrian-street", "grabacion_de_campo"),
    "aves": ("0100", "forest", "grabacion_de_campo"),
    "teclado": ("0229", "computer-keyboard", "grabacion_foley"),
    "teclado_lento": ("1733", "slow-keyboard", "grabacion_foley"),
    "ventilacion": ("0126", "computer-2-ventilation", "grabacion_foley"),
    "papeles": ("0785", "paper", "grabacion_foley"),
    "pagina": ("2212", "pages-that-turn-5", "grabacion_foley"),
    "lapiz": ("0221", "pencil", "grabacion_foley"),
    "lluvia": ("2679", "rain-under-an-umbrella", "grabacion_de_campo"),
    "noche": ("1469", "campaign-at-night-3", "grabacion_de_campo"),
    "viento": ("0904", "forest-wind-in-the-trees", "grabacion_de_campo"),
    "ciudad_noche": ("0680", "paris-by-night", "grabacion_de_campo"),
    "clic": ("1735", "raspberry-mouse-single-click", "grabacion_foley"),
    "pasos_madera": ("0165", "man-footsteps-on-the-wooden-floor", "grabacion_foley"),
    "pasos_calle": ("1319", "fast-steps-on-concrete", "grabacion_foley"),
    "puerta_abrir": ("1703", "apartment-door-opening-2", "grabacion_foley"),
    "puerta_cerrar": ("1704", "apartment-door-closing-1", "grabacion_foley"),
    "llamada_puerta": ("0320", "knock-on-the-glass-door-2", "grabacion_foley"),
    "taza": ("1194", "teaspoon-placed-on-a-plate", "grabacion_foley"),
    "cucharilla": ("0410", "spoon-into-a-mug-of-coffee", "grabacion_foley"),
    "cafetera": ("0301", "senseo-service", "grabacion_foley"),
    "suspiro": ("1405", "sigh-by-the-mouth", "grabacion_foley"),
    "notificacion": ("2066", "notification-lasolisa-4", "diseno_sonoro_sintetizado_por_el_autor"),
    "hallazgo": ("1399", "idea-2", "grabacion_metallofono"),
}
MUSICA = {
    "ciudad": ("calm-piano-1-vaporware", "003_Vaporware_2.mp3", "Calm Piano 1 (Vaporware)", "Piano cálido y capas ambientales."),
    "investigacion": ("dark-forest-theme", "GameMusic_ForestTheme_24_0.mp3", "Dark Forest Theme", "Guitarra acústica y cuerdas de misterio."),
    "eleccion": ("sirens-in-darkness", "012_Sirens_in_Darkness_0.mp3", "Sirens in Darkness", "Piano y capas ambientales de reflexión nocturna."),
}


def texto_html(valor):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", " ", valor))).strip()


def sha256(ruta):
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def obtener(url):
    solicitud = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (CIVICA audio asset preparation)"})
    with urllib.request.urlopen(solicitud, timeout=60) as respuesta:
        return respuesta.read()


def descargar_fuente(nombre):
    numero, slug, tipo = FUENTES[nombre]
    pagina = f"https://bigsoundbank.com/{slug}-s{numero}.html"
    datos_ruta = CACHE / f"{numero}.json"
    sonido_ruta = CACHE / f"{numero}.mp3"
    if datos_ruta.is_file() and sonido_ruta.is_file():
        datos = json.loads(datos_ruta.read_text(encoding="utf-8"))
        if datos.get("sha256_original") == sha256(sonido_ruta):
            return nombre, datos
    contenido = obtener(pagina).decode("utf-8")
    texto = texto_html(contenido)
    # No se infiere una licencia del sitio ni de una página de resultados.
    if not re.search(r"CC0\s*\(public domain\): Free and royalty-free", texto, re.I):
        raise RuntimeError(f"La página individual ya no confirma CC0: {pagina}")
    titulo = texto_html(re.search(r"<h1[^>]*>(.*?)</h1>", contenido, re.S).group(1))
    autor = re.search(r"Author\s*:\s*(.*?)\s*Sound number\s*:", texto)
    if not autor:
        raise RuntimeError(f"No se encontró autor en {pagina}")
    audio = re.search(r'<source\s+src=[\"\']([^\"\']*/UPLOAD/mp3/[^\"\']+)', contenido)
    if not audio:
        raise RuntimeError(f"No se encontró la descarga MP3 oficial en {pagina}")
    descarga = urllib.parse.urljoin(pagina, html.unescape(audio.group(1)).split("?")[0])
    original = obtener(descarga)
    if len(original) < 300:
        raise RuntimeError(f"Descarga de audio incompleta: {descarga}")
    sonido_ruta.write_bytes(original)
    datos = {
        "id": numero, "titulo_original": titulo, "autor": autor.group(1),
        "pagina_fuente": pagina, "descarga_original": descarga,
        "licencia": "CC0-1.0", "licencia_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "evidencia_pagina": "CC0 (public domain): Free and royalty-free",
        "naturaleza": tipo, "verificado_utc": datetime.now(timezone.utc).isoformat(),
        "sha256_original": sha256(sonido_ruta),
    }
    datos_ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Fuente CC0 verificada: {numero} · {titulo} · {autor.group(1)}", flush=True)
    return nombre, datos


def ffmpeg():
    ejecutable = shutil.which("ffmpeg")
    if ejecutable:
        return ejecutable
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError as exc:
        raise SystemExit("Falta FFmpeg; instala imageio-ffmpeg o usa un FFmpeg en PATH.") from exc


def decodificar(ruta, inicio=0, segundos=60, filtros=""):
    comando = [ffmpeg(), "-v", "error", "-ss", str(inicio), "-i", str(ruta),
               "-t", str(segundos), "-ac", "2", "-ar", str(HZ)]
    if filtros:
        comando += ["-af", filtros]
    comando += ["-f", "f32le", "pipe:1"]
    datos = subprocess.run(comando, check=True, capture_output=True).stdout
    muestras = np.frombuffer(datos, dtype="<f4").reshape(-1, 2).copy()
    if len(muestras) < HZ / 20:
        raise ValueError(f"Segmento vacío de {ruta.name} en {inicio}s")
    muestras -= np.mean(muestras, axis=0, keepdims=True)
    return muestras


def leer(nombre, inicio=0, segundos=60, filtros=""):
    return decodificar(CACHE / f"{FUENTES[nombre][0]}.mp3", inicio, segundos, filtros)


def descargar_musica(nombre):
    slug, nombre_original, titulo_esperado, _ = MUSICA[nombre]
    pagina = f"https://opengameart.org/content/{slug}"
    metadatos_ruta = CACHE / f"musica_{nombre}.json"
    original_ruta = CACHE / f"musica_{nombre}.mp3"
    if metadatos_ruta.is_file() and original_ruta.is_file():
        datos = json.loads(metadatos_ruta.read_text(encoding="utf-8"))
        if datos.get("sha256_original") == sha256(original_ruta):
            return nombre, datos
    contenido = obtener(pagina).decode("utf-8")
    bloque = re.search(r'field-name-field-art-licenses(.*?)field-name-collect', contenido, re.S)
    licencias = re.findall(r"class=['\"]license-name['\"]>(.*?)<", bloque.group(1) if bloque else "")
    if licencias != ["CC0"]:
        raise RuntimeError(f"La publicación musical no confirma únicamente CC0: {pagina}: {licencias}")
    autor = re.search(r'<meta name="dcterms.creator" content="([^"]+)"', contenido)
    titulo = re.search(r'<meta property="og:title" content="([^"]+)"', contenido)
    if not autor or autor.group(1) != "cynicmusic":
        raise RuntimeError(f"Autor inesperado en {pagina}")
    descarga = f"https://opengameart.org/sites/default/files/{nombre_original}"
    if descarga not in contenido:
        raise RuntimeError(f"La publicación ya no contiene el archivo esperado: {descarga}")
    original_ruta.write_bytes(obtener(descarga))
    datos = {
        "titulo_original": html.unescape(titulo.group(1)).removesuffix(" | OpenGameArt.org") if titulo else titulo_esperado,
        "autor": "The Cynic Project / cynicmusic", "perfil_autor": "https://opengameart.org/users/cynicmusic",
        "pagina_fuente": pagina, "descarga_original": descarga, "archivo_original": nombre_original,
        "licencia": "CC0-1.0", "licencia_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "evidencia_pagina": "License(s): CC0 (campo de licencia de la publicación individual)",
        "credito_solicitado": "The Cynic Project / cynicmusic.com / pixelsphere.org",
        "naturaleza": "composicion_instrumental_publicada_por_el_autor; no se afirma interpretación acústica en vivo",
        "verificado_utc": datetime.now(timezone.utc).isoformat(), "sha256_original": sha256(original_ruta),
    }
    metadatos_ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Música CC0 verificada: {nombre}: {datos['titulo_original']}", flush=True)
    return nombre, datos


def seleccionar_bucle_musical(muestras):
    """Busca un retorno de armonía y nivel cercano a un minuto, sin cortar a ciegas.

    Cada marco resume un segundo de audio en doce clases de altura y cinco
    bandas de energía. La búsqueda evita las colas silenciosas del original.
    El empalme posterior elimina discontinuidades a nivel de muestra.
    """
    mono = muestras.mean(axis=1)[::4]
    hz = HZ // 4
    marco = hz
    paso = hz // 2
    frecuencias = np.fft.rfftfreq(marco, 1 / hz)
    utiles = (frecuencias >= 55) & (frecuencias < 3600)
    midi = np.rint(69 + 12 * np.log2(np.maximum(frecuencias[utiles], 1) / 440)).astype(int)
    clases = midi % 12
    ventana = np.hanning(marco)
    descriptores, niveles = [], []
    for inicio in range(0, len(mono) - marco, paso):
        segmento = mono[inicio:inicio + marco]
        espectro = np.abs(np.fft.rfft(segmento * ventana)) ** 1.2
        chroma = np.bincount(clases, weights=espectro[utiles], minlength=12)
        chroma /= max(float(np.linalg.norm(chroma)), 1e-12)
        bandas = np.array([espectro[(frecuencias >= a) & (frecuencias < b)].sum()
                           for a, b in ((40, 180), (180, 500), (500, 1200), (1200, 2500), (2500, 4000))])
        bandas /= max(float(np.linalg.norm(bandas)), 1e-12)
        descriptores.append(np.concatenate((chroma, bandas * 0.35)))
        niveles.append(float(np.sqrt(np.mean(segmento ** 2))))
    descriptores, niveles = np.asarray(descriptores), np.asarray(niveles)
    mejor = None
    # Entre 56 y 66 s de bucle, más los dos segundos usados en el empalme.
    for comienzo in range(12, min(100, len(descriptores) - 120)):
        for largo in range(116, 137):
            fin = comienzo + largo - 4
            if fin + 4 >= len(descriptores):
                continue
            if min(niveles[comienzo:comienzo + 4].mean(), niveles[fin:fin + 4].mean()) < niveles.mean() * 0.25:
                continue
            diferencia = float(np.mean((descriptores[comienzo:comienzo + 4] - descriptores[fin:fin + 4]) ** 2))
            diferencia += abs(np.log(max(niveles[comienzo], 1e-8) / max(niveles[fin], 1e-8))) * 0.003
            diferencia += abs(largo / 2 - 62) * 0.00006
            if mejor is None or diferencia < mejor[0]:
                mejor = (diferencia, comienzo / 2, largo / 2)
    if mejor is None:
        return 8.0, 62.0
    return mejor[1], mejor[2]


def producir_musica(datos):
    recursos = []
    for nombre, (_, _, _, descripcion) in MUSICA.items():
        muestras = decodificar(CACHE / f"musica_{nombre}.mp3", 0, 240, "highpass=f=35")
        comienzo, largo = seleccionar_bucle_musical(muestras)
        recorte = muestras[int(comienzo * HZ):int((comienzo + largo) * HZ)]
        duracion = largo - 2
        bucle = nivel(circular(recorte, duracion, 2), -23, -4)
        recurso = guardar(nombre, bucle, "musica", [nombre], descripcion,
                          ["recorte con retorno armónico y nivel semejantes", "empalme circular de 2 s", "normalización RMS y pico", "PCM 16 bits estéreo 32 kHz"])
        recurso["inicio_original_segundos"] = comienzo
        recursos.append(recurso)
    manifiesto = {
        "version": 1, "proyecto": "CIVICA / Alcalde Digital", "licencia_recursos": "CC0-1.0",
        "descripcion": "Extractos instrumentales de obras publicadas por The Cynic Project / cynicmusic en OpenGameArt. Se conserva el crédito solicitado por el compositor.",
        "fuentes": datos, "recursos": recursos, "total_bytes_wav": sum(r["bytes"] for r in recursos),
    }
    (SALIDA / "licencias_musica.json").write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifiesto


def nivel(muestras, rms_db=-24, pico_db=-4):
    rms = float(np.sqrt(np.mean(np.square(muestras, dtype=np.float64))))
    if rms < 1e-8:
        raise ValueError("No se acepta audio silencioso")
    ganancia = 10 ** (rms_db / 20) / rms
    pico = float(np.max(np.abs(muestras)))
    ganancia = min(ganancia, 10 ** (pico_db / 20) / max(pico, 1e-8))
    return (muestras * ganancia).astype(np.float32)


def fundir(muestras, segundos=0.025):
    muestras = muestras.copy()
    n = min(int(HZ * segundos), len(muestras) // 3)
    rampa = np.linspace(0, 1, n, dtype=np.float32)[:, None]
    muestras[:n] *= rampa
    muestras[-n:] *= rampa[::-1]
    return muestras


def repetir(muestras, segundos):
    """Extiende grabaciones cortas con solapamientos de 0,8 s."""
    requerido = int(segundos * HZ)
    muestras = muestras.copy()
    n = min(int(HZ * 0.8), len(muestras) // 4)
    rampa = np.linspace(0, 1, n, dtype=np.float32)[:, None]
    original = muestras.copy()
    while len(muestras) < requerido:
        union = muestras[-n:] * (1 - rampa) + original[:n] * rampa
        muestras = np.concatenate((muestras[:-n], union, original[n:]))
    return muestras[:requerido].copy()


def circular(muestras, segundos=DURACION, solape=2):
    """Empalma final e inicio sin huecos ni fundidos a silencio por vuelta."""
    muestras = repetir(muestras, segundos + solape)
    n = int(HZ * solape)
    rampa = np.linspace(0, 1, n, dtype=np.float32)[:, None]
    union = muestras[-n:] * (1 - rampa) + muestras[:n] * rampa
    return np.concatenate((muestras[n:-n], union))


def difundir(muestras):
    """Aleja el murmullo: cuatro tomas desfasadas evitan un interlocutor al frente."""
    mezcla = muestras * 0.5
    for demora, ganancia in ((3.13, 0.22), (8.41, 0.18), (14.73, 0.16)):
        mezcla += np.roll(muestras[:, ::-1], int(demora * HZ), axis=0) * ganancia
    return mezcla


def colocar(base, efecto, segundo, ganancia=1.0, paneo=0.0):
    primero = int(segundo * HZ)
    n = min(len(efecto), len(base) - primero)
    if n <= 0:
        return
    izquierda = min(1.0, 1.0 - paneo)
    derecha = min(1.0, 1.0 + paneo)
    base[primero:primero + n] += efecto[:n] * ganancia * np.array([izquierda, derecha], dtype=np.float32)


def guardar(nombre, muestras, categoria, fuentes, descripcion, procesos):
    ruta = SALIDA / categoria / f"{nombre}.wav"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if not np.isfinite(muestras).all() or np.max(np.abs(muestras)) >= 1:
        raise ValueError(f"Audio inválido o saturado en {nombre}")
    pcm = np.rint(muestras * 32767).astype("<i2")
    with wave.open(str(ruta), "wb") as archivo:
        archivo.setnchannels(2)
        archivo.setsampwidth(2)
        archivo.setframerate(HZ)
        archivo.writeframes(pcm.tobytes())
    estadisticas = {
        "archivo": ruta.relative_to(RAIZ).as_posix(), "nombre": nombre, "categoria": categoria,
        "descripcion": descripcion, "fuentes": fuentes, "procesos": procesos,
        "duracion_segundos": round(len(muestras) / HZ, 3), "hz": HZ, "canales": 2,
        "pico_dbfs": round(20 * np.log10(max(float(np.max(np.abs(muestras))), 1e-10)), 2),
        "rms_dbfs": round(20 * np.log10(max(float(np.sqrt(np.mean(muestras ** 2))), 1e-10)), 2),
        "bytes": ruta.stat().st_size, "sha256": sha256(ruta),
    }
    print(f"{categoria}/{nombre}: {estadisticas['duracion_segundos']}s", flush=True)
    return estadisticas


def producir(datos):
    recursos = []
    # Los fondos se mezclan a un nivel común; Qt aplica además el volumen ambiental.
    def ambiente(nombre, mezcla, fuentes, descripcion, proceso):
        recursos.append(guardar(nombre, nivel(circular(mezcla), -23, -5), "ambientes", fuentes,
                                descripcion, proceso + ["empalme circular de 2 s", "nivel RMS y pico", "PCM 16 bits estéreo 32 kHz"]))

    cafe = difundir(nivel(leer("cafe", 32, 47, "highpass=f=100,lowpass=f=1250"), -24))
    cucharilla = nivel(fundir(leer("cucharilla", 9, 2.6)), -24)
    taza = nivel(fundir(leer("taza", 3, 1.8)), -23)
    colocar(cafe, cucharilla, 6.7, 0.5, -0.4)
    colocar(cafe, taza, 19.6, 0.5, 0.45)
    colocar(cafe, cucharilla, 33.1, 0.32, 0.25)
    ambiente("cafe", cafe, ["cafe", "cucharilla", "taza"], "Café con murmullo distante y vajilla cercana.",
             ["recorte de grabaciones reales", "filtro de distancia del murmullo", "capas y paneo de vajilla"])

    plaza = difundir(nivel(leer("plaza", 19, 47, "highpass=f=85,lowpass=f=1300"), -26))
    aves = nivel(leer("aves", 3, 47, "highpass=f=700,lowpass=f=9000"), -32)
    ambiente("plaza", plaza + aves, ["plaza", "aves"], "Plaza peatonal: multitud distante, aire y aves.",
             ["mezcla de dos grabaciones", "filtro de distancia para la multitud"])

    calle = difundir(nivel(leer("calle", 8, 47, "highpass=f=75,lowpass=f=1600"), -24))
    ambiente("calle", calle + aves * 0.28, ["calle", "aves"], "Calle peatonal con actividad urbana y aves lejanas.",
             ["recorte y mezcla", "filtrado y difusión de actividad distante"])

    oficina = repetir(nivel(leer("ventilacion", 1, 8, "highpass=f=75,lowpass=f=1400"), -35), 47)
    for segundo, inicio, duracion, paneo in ((3, 3, 4.5, -0.3), (13, 15, 3.7, 0.35), (25, 27, 5.4, -0.25), (38, 6, 3, 0.25)):
        teclas = nivel(fundir(leer("teclado_lento", inicio, duracion, "highpass=f=220,lowpass=f=4500"), 0.15), -27)
        colocar(oficina, teclas, segundo, 1, paneo)
    for segundo, inicio in ((10.8, 3), (22.6, 11), (34.5, 19)):
        colocar(oficina, nivel(fundir(leer("papeles", inicio, 2.1), 0.08), -28), segundo, 0.65, 0.4)
    ambiente("oficina", oficina, ["ventilacion", "teclado_lento", "papeles"],
             "Oficina con ventilación tenue, pausas de escritura y documentos.", ["montaje de grabaciones de objetos", "pausas naturales", "paneo espacial"])

    lluvia = repetir(leer("lluvia", 2, 28, "highpass=f=80,lowpass=f=10000"), 47)
    ambiente("lluvia", lluvia, ["lluvia"], "Lluvia regular sobre una superficie de tela, en exterior.",
             ["recorte de grabación real", "extensión mediante solapamientos"])

    noche = nivel(leer("noche", 28, 47, "highpass=f=90,lowpass=f=8500"), -25)
    ciudad = nivel(leer("ciudad_noche", 15, 47, "highpass=f=60,lowpass=f=1100"), -33)
    ambiente("noche", noche + ciudad, ["noche", "ciudad_noche"], "Noche con insectos, aire entre árboles y tráfico muy distante.",
             ["dos grabaciones de campo", "tráfico filtrado en segundo plano"])

    viento = leer("viento", 43, 47, "highpass=f=100,lowpass=f=9000")
    ambiente("viento", viento, ["viento"], "Viento real moviendo hojas de árboles.", ["recorte y filtrado de subgraves"])

    # La lluvia interior es una perspectiva de la misma grabación, filtrada como tras una ventana.
    lluvia_dentro = repetir(nivel(leer("lluvia", 2, 28, "highpass=f=90,lowpass=f=1700"), -26), 47)
    vent = repetir(nivel(leer("ventilacion", 1, 8, "highpass=f=80,lowpass=f=900"), -39), 47)
    ambiente("interior_lluvia", lluvia_dentro + vent, ["lluvia", "ventilacion"],
             "Lluvia amortiguada desde un interior silencioso.", ["perspectiva interior mediante filtro", "ventilación tenue"])

    especificaciones = [
        ("clic_real", "clic", 0, 1.0, "Clic físico de un ratón."),
        ("pagina", "pagina", 0, 2.0, "Paso de página de un libro."),
        ("papeles", "papeles", 7, 2.7, "Manipulación de documentos."),
        ("lapiz", "lapiz", 5, 2.5, "Anotación con lápiz sobre papel."),
        ("teclado", "teclado", 4, 1.8, "Varias teclas de un teclado físico."),
        ("pasos_madera", "pasos_madera", 1.0, 4.4, "Pasos humanos sobre piso de madera."),
        ("pasos_calle", "pasos_calle", 5.0, 4.3, "Pasos rápidos sobre concreto."),
        ("puerta_abrir", "puerta_abrir", 0, 5.0, "Apertura de puerta de madera."),
        ("puerta_cerrar", "puerta_cerrar", 0, 4.0, "Cierre de puerta de madera."),
        ("llamada_puerta", "llamada_puerta", 0, 2.0, "Golpes en una puerta de vidrio."),
        ("taza", "taza", 3, 1.8, "Cucharilla depositada sobre un plato: detalle de vajilla."),
        ("cucharilla", "cucharilla", 9, 2.6, "Cucharilla removiendo una taza de café."),
        ("cafetera", "cafetera", 3, 5.3, "Cafetera sirviendo café."),
        ("suspiro", "suspiro", 0, 6.0, "Suspiro humano sin palabras."),
        ("notificacion_suave", "notificacion", 0, 1.4, "Aviso breve de diseño sonoro electrónico del autor; no es una grabación real."),
        ("hallazgo", "hallazgo", 0, 4.0, "Nota real de metalófono como descubrimiento."),
    ]
    for nombre, fuente, inicio, duracion, descripcion in especificaciones:
        muestras = leer(fuente, inicio, duracion, "highpass=f=65")
        # Elimina silencio excesivo del encabezado/cola conservando margen de aire.
        envolvente = np.max(np.abs(muestras), axis=1)
        umbral = max(float(envolvente.max()) * 0.012, 0.00008)
        actividad = np.flatnonzero(envolvente > umbral)
        if len(actividad):
            muestras = muestras[max(0, actividad[0] - int(0.035 * HZ)):min(len(muestras), actividad[-1] + int(0.14 * HZ))]
        muestras = nivel(fundir(muestras), -22, -3)
        recursos.append(guardar(nombre, muestras, "efectos", [fuente], descripcion,
                                ["recorte", "retiro de silencio excedente", "fundidos de 25 ms", "normalización de pico y RMS", "PCM 16 bits estéreo 32 kHz"]))

    manifiesto = {
        "version": 1, "proyecto": "CIVICA / Alcalde Digital", "licencia_recursos": "CC0-1.0",
        "proveedor": "BigSoundBank / LaSonothèque", "licencia_proveedor": "https://bigsoundbank.com/licenses.html",
        "descripcion": "Montajes de grabaciones reales, salvo la notificación electrónica indicada en su ficha. Los autores y las páginas individuales se registran por fuente.",
        "fuentes": datos, "recursos": recursos,
        "total_bytes_wav": sum(r["bytes"] for r in recursos),
    }
    (SALIDA / "licencias.json").write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifiesto


def verificar():
    manifiesto = json.loads((SALIDA / "licencias.json").read_text(encoding="utf-8"))
    musica_ruta = SALIDA / "licencias_musica.json"
    if musica_ruta.is_file():
        musica = json.loads(musica_ruta.read_text(encoding="utf-8"))
        manifiesto["fuentes"].update({"musica_" + k: v for k, v in musica["fuentes"].items()})
        for recurso in musica["recursos"]:
            recurso["fuentes"] = ["musica_" + k for k in recurso["fuentes"]]
        manifiesto["recursos"].extend(musica["recursos"])
        manifiesto["total_bytes_wav"] += musica["total_bytes_wav"]
    for recurso in manifiesto["recursos"]:
        ruta = RAIZ / recurso["archivo"]
        assert sha256(ruta) == recurso["sha256"], f"SHA alterado: {ruta}"
        with wave.open(str(ruta)) as archivo:
            assert archivo.getnchannels() == 2 and archivo.getsampwidth() == 2
            assert archivo.getframerate() == HZ
            muestras = np.frombuffer(archivo.readframes(archivo.getnframes()), dtype="<i2").reshape(-1, 2)
        assert np.max(np.abs(muestras.astype(np.int32))) < 32767, f"Saturación en {ruta}"
        assert np.sqrt(np.mean(muestras.astype(float) ** 2)) > 10, f"Silencio en {ruta}"
        for fuente in recurso["fuentes"]:
            assert manifiesto["fuentes"][fuente]["licencia"] == "CC0-1.0"
        if recurso["categoria"] == "ambientes":
            assert abs(len(muestras) / HZ - DURACION) < 0.01
        if recurso["categoria"] == "musica":
            assert 50 <= len(muestras) / HZ <= 70
        if recurso["categoria"] in ("ambientes", "musica"):
            # Detecta un salto artificial en el punto de repetición respecto al ruido real.
            salto = float(np.max(np.abs(muestras[0].astype(int) - muestras[-1].astype(int))))
            diferencias = np.abs(np.diff(muestras.astype(np.int32), axis=0))
            assert salto <= max(128, np.percentile(diferencias, 99.9) * 2), f"Empalme brusco en {ruta}: {salto}"
    assert manifiesto["total_bytes_wav"] < 100 * 1024 ** 2
    print(f"Verificados {len(manifiesto['recursos'])} WAV, {manifiesto['total_bytes_wav'] / 1024**2:.1f} MiB; formato, hashes, audio no saturado y empalmes correctos.")


def main():
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument("--descargar", action="store_true", help="Descarga y verifica originales CC0 desde páginas oficiales.")
    argumentos.add_argument("--verificar", action="store_true", help="Comprueba los WAV finales sin descargarlos ni regenerarlos.")
    argumentos.add_argument("--musica", action="store_true", help="Prepara sólo las tres pistas musicales instrumentales CC0.")
    args = argumentos.parse_args()
    if args.verificar:
        verificar()
        return
    CACHE.mkdir(parents=True, exist_ok=True)
    SALIDA.mkdir(parents=True, exist_ok=True)
    if args.musica:
        if args.descargar:
            with ThreadPoolExecutor(max_workers=3) as grupo:
                datos = dict(grupo.map(descargar_musica, MUSICA))
        else:
            datos = {nombre: json.loads((CACHE / f"musica_{nombre}.json").read_text(encoding="utf-8")) for nombre in MUSICA}
        producir_musica(datos)
        verificar()
        return
    if args.descargar:
        with ThreadPoolExecutor(max_workers=3) as grupo:
            datos = dict(grupo.map(descargar_fuente, FUENTES))
    else:
        datos = {}
        for nombre, (numero, _, _) in FUENTES.items():
            ruta = CACHE / f"{numero}.json"
            if not ruta.is_file() or not (CACHE / f"{numero}.mp3").is_file():
                raise SystemExit("Faltan originales. Ejecuta con --descargar (consulta las fuentes y licencias en la documentación).")
            datos[nombre] = json.loads(ruta.read_text(encoding="utf-8"))
    producir(datos)
    verificar()


if __name__ == "__main__":
    main()
