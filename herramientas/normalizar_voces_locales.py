"""Da cuerpo a las voces locales sin cambiar texto, intérprete ni velocidad.

Sin argumentos prepara y mide dieciséis muestras sin reemplazar los originales.
Con --aplicar procesa el catálogo y puede reanudarse después de una interrupción.
Cada MP3 lleva una marca ID3; un corte entre el reemplazo y el guardado del
manifest no provoca una segunda compresión. Solo existe un MP3 temporal a la vez.
"""
from __future__ import annotations

import argparse
import array
import base64
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import sys
import time
import unicodedata

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / ".tmp/deps"))
from audio.catalogo_voces import CARPETA_VOCES, PERFILES, cargar_manifest, clave_clip, ruta_clip
from herramientas.producir_voces import medir_audio

VERSION_MEZCLA = 2
FILTRO = ("acompressor=threshold=0.20:ratio=2:attack=5:release=120:makeup=2.5,"
          "alimiter=limit=0.95:level=false:latency=true,volume=0.8")
MARCA = b"ALCALDE_DIGITAL_MEZCLA_V2:"
REPORTE = RAIZ / "docs/verificacion_volumen_voces.json"


def sha256(ruta):
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def codificar_marca(datos):
    contenido = json.dumps(datos, separators=(",", ":"), sort_keys=True).encode("ascii")
    return MARCA.decode("ascii") + base64.urlsafe_b64encode(contenido).decode("ascii").rstrip("=")


def leer_marca(ruta):
    """Lee el comentario UTF-8 de ID3v2.4, sin decodificar el audio."""
    with Path(ruta).open("rb") as archivo:
        cabecera = archivo.read(65536)
    encontrada = re.search(re.escape(MARCA) + rb"([A-Za-z0-9_-]+)", cabecera)
    if not encontrada:
        return None
    contenido = encontrada.group(1)
    try:
        datos = json.loads(base64.urlsafe_b64decode(contenido + b"="*((-len(contenido)) % 4)))
        if (datos.get("version") != VERSION_MEZCLA or not re.fullmatch(r"[a-f0-9]{64}", datos.get("sha_original", ""))
                or datos.get("rms_original", 0) <= 0 or datos.get("duracion_original_ms", 0) <= 0):
            raise ValueError("Marca de mezcla incompleta")
        return datos
    except (ValueError, TypeError) as error:
        raise ValueError(f"Marca ID3 inválida: {Path(ruta).name}") from error


def medir_nivel(ruta, ffmpeg):
    """RMS y pico real decodificado a 24 kHz; el PCM solo vive en memoria."""
    resultado = subprocess.run([ffmpeg, "-v", "error", "-i", str(ruta), "-f", "f32le",
                                "-ac", "1", "-ar", "24000", "pipe:1"],
                               capture_output=True, check=True, timeout=40)
    muestras = array.array("f", resultado.stdout)
    if not muestras:
        raise ValueError(f"Audio sin muestras: {Path(ruta).name}")
    rms = math.sqrt(sum(m*m for m in muestras)/len(muestras))
    return {"rms": round(rms, 7), "pico_real": round(max(abs(m) for m in muestras), 7),
            "duracion_ms": round(len(muestras)/24)}


def validar_niveles(antes, despues):
    if antes["rms"] <= 0:
        raise ValueError("La toma original es silenciosa")
    ganancia = 20*math.log10(despues["rms"]/antes["rms"])
    if abs(despues["duracion_ms"]-antes["duracion_ms"]) > 60:
        raise ValueError("La mezcla cambió la duración más de 60 ms")
    if despues["pico_real"] >= .98:
        raise ValueError(f"La mezcla supera el margen de pico: {despues['pico_real']}")
    if not .5 <= ganancia <= 9:
        raise ValueError(f"Ganancia inesperada: {ganancia:.2f} dB")
    return round(ganancia, 3)


def preparar_clip(origen, ffmpeg):
    """Produce y valida un temporal; el llamador decide si lo aplica."""
    origen = Path(origen)
    temporal = origen.parent / ".mezcla_dialogos_v2.mp3"
    antes = medir_nivel(origen, ffmpeg)
    marca = {"version": VERSION_MEZCLA, "sha_original": sha256(origen),
             "rms_original": antes["rms"], "pico_original": antes["pico_real"],
             "duracion_original_ms": antes["duracion_ms"]}
    try:
        volumen = .8
        # Algunos fonemas generan sobrepicos al recodificar MP3. Se vuelve a
        # partir del original con más margen, nunca del MP3 ya comprimido.
        for intento in range(3):
            filtro = FILTRO.rsplit("volume=", 1)[0]+f"volume={volumen:.6f}"
            marca["filtro"] = filtro
            subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(origen),
                            "-map", "0:a:0", "-map_metadata", "-1", "-af", filtro,
                            "-ac", "1", "-ar", "24000", "-c:a", "libmp3lame", "-b:a", "48k",
                            "-id3v2_version", "4", "-write_xing", "1", "-metadata",
                            "comment="+codificar_marca(marca), str(temporal)],
                           capture_output=True, check=True, timeout=45)
            if temporal.stat().st_size < 1000:
                raise ValueError("MP3 mezclado incompleto")
            despues = medir_nivel(temporal, ffmpeg)
            if despues["pico_real"] < .98:
                break
            volumen *= .94/despues["pico_real"]
        ganancia = validar_niveles(antes, despues)
        if leer_marca(temporal) != marca:
            raise ValueError("No se conservó la marca ID3 de reanudación")
        medicion = medir_audio(temporal, ffmpeg)
        return temporal, marca, medicion, despues, ganancia
    except BaseException:
        temporal.unlink(missing_ok=True)
        raise


def actualizar_entrada(entrada, marca, medicion, nivel, ruta):
    ganancia = round(20*math.log10(nivel["rms"]/marca["rms_original"]), 3)
    entrada.update(medicion)
    entrada.update({"mezcla_dialogos": VERSION_MEZCLA, "sha256_mezclado": sha256(ruta),
                    "mezcla_original": marca, "rms": nivel["rms"], "pico_real": nivel["pico_real"],
                    "ganancia_rms_db": ganancia})
    return ganancia


def guardar_manifest(manifest, carpeta):
    destino = Path(carpeta) / "manifest.json"
    temporal = destino.with_suffix(".mezcla.tmp")
    manifest["actualizado_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    temporal.write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    temporal.replace(destino)


def procesar_entrada(entrada, carpeta, ffmpeg):
    """Reanuda la transacción de un clip usando su marca, no el orden del lote."""
    origen = ruta_clip(entrada, carpeta)
    if origen is None:
        raise FileNotFoundError(entrada["archivo"])
    marca = leer_marca(origen)
    if marca:
        if entrada.get("mezcla_dialogos") == VERSION_MEZCLA and entrada.get("sha256_mezclado") == sha256(origen):
            return "omitido"
        nivel = medir_nivel(origen, ffmpeg)
        validar_niveles({"rms": marca["rms_original"], "duracion_ms": marca["duracion_original_ms"]}, nivel)
        actualizar_entrada(entrada, marca, medir_audio(origen, ffmpeg), nivel, origen)
        return "recuperado"
    if entrada.get("mezcla_dialogos") == VERSION_MEZCLA:
        raise ValueError(f"El MP3 cambió después de la mezcla: {origen.name}")
    temporal, marca, medicion, nivel, _ = preparar_clip(origen, ffmpeg)
    temporal.replace(origen)
    actualizar_entrada(entrada, marca, medicion, nivel, origen)
    return "producido"


def muestras_representativas(manifest):
    clips = manifest["clips"]
    elegidos = []
    for hablante in PERFILES:
        clave = next((k for k, c in clips.items() if c["hablante"] == hablante and len(c["texto"]) > 65), None)
        if clave:
            elegidos.append(clave)
    etiquetas = ("Informacion verificada", "Confianza", "Convivencia", "Bienestar digital",
                 "Desinformacion", "Conflictos", "Participacion", "Puntuacion de la accion")
    def simple(texto):
        return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)).casefold()
    for etiqueta in etiquetas:
        clave = next((k for k, c in clips.items() if c["hablante"] == "NARRADOR"
                      and simple(c["texto"]).startswith(simple(etiqueta)) and len(c["texto"]) < 110), None)
        if clave and clave not in elegidos:
            elegidos.append(clave)
    if len(elegidos) != 16:
        raise ValueError(f"Se esperaban dieciséis muestras; se encontraron {len(elegidos)}")
    return elegidos


def preflight(manifest, carpeta, ffmpeg):
    resultados = []
    for clave in muestras_representativas(manifest):
        entrada = manifest["clips"][clave]
        origen = ruta_clip(entrada, carpeta)
        if origen is None:
            raise FileNotFoundError(entrada["archivo"])
        marca_previa = leer_marca(origen)
        if marca_previa:
            nivel = medir_nivel(origen, ffmpeg)
            ganancia = 20*math.log10(nivel["rms"]/marca_previa["rms_original"])
            antes = marca_previa["rms_original"]
            despues = nivel
        else:
            temporal, marca, _, despues, ganancia = preparar_clip(origen, ffmpeg)
            antes = marca["rms_original"]
            temporal.unlink()
        resultados.append({"clave": clave, "hablante": entrada["hablante"],
                           "texto": entrada["texto"], "rms_antes": antes,
                           "rms_despues": despues["rms"], "pico_real": despues["pico_real"],
                           "ganancia_rms_db": round(ganancia, 3),
                           "duracion_ms": despues["duracion_ms"]})
    mediana = statistics.median(m["ganancia_rms_db"] for m in resultados)
    if not 4 <= mediana <= 6.5:
        raise ValueError(f"La muestra no cumple la ganancia media prevista: {mediana:.3f} dB")
    return {"clips": resultados, "mediana_ganancia_rms_db": round(mediana, 3),
            "pico_maximo": max(c["pico_real"] for c in resultados)}


def ejecutar(aplicar=False, limite=0):
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    manifest = cargar_manifest()
    if not manifest.get("clips"):
        raise ValueError("No hay catálogo local de voces")
    if shutil.disk_usage(CARPETA_VOCES).free < 8*1024*1024:
        raise OSError("Se necesitan 8 MB libres para reemplazar el manifest de forma atómica")
    ayuda = subprocess.run([ffmpeg, "-hide_banner", "-h", "filter=alimiter"], capture_output=True, text=True, check=True)
    if "auto level" not in ayuda.stdout or "compensate delay" not in ayuda.stdout:
        raise ValueError("Este FFmpeg no documenta level/latency del limitador")
    inicio = time.monotonic()
    print("Comprobando ocho voces y ocho indicadores sin reemplazar originales...", flush=True)
    piloto = preflight(manifest, CARPETA_VOCES, ffmpeg)
    print(json.dumps({"muestras": 16, "mediana_db": piloto["mediana_ganancia_rms_db"],
                      "pico_maximo": piloto["pico_maximo"]}), flush=True)
    informe = {"version": VERSION_MEZCLA, "filtro": FILTRO,
               "formato": "MP3 libmp3lame · 48 kbps · 24 kHz · mono",
               "medicion": "RMS y pico sobre PCM float32 a 24 kHz; envolvente labial con medir_audio existente",
               "muestras": piloto, "aplicado": aplicar}
    if not aplicar:
        REPORTE.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
        return informe
    completados = recuperados = omitidos = 0
    try:
        for clave, entrada in manifest["clips"].items():
            if limite and completados+recuperados >= limite:
                break
            for intento in range(5):
                try:
                    resultado = procesar_entrada(entrada, CARPETA_VOCES, ffmpeg)
                    break
                except PermissionError as error:
                    # Windows puede retener brevemente un proceso o un MP3.
                    # Las marcas permiten reintentar incluso tras el reemplazo.
                    if getattr(error, "winerror", None) not in (5, 32) or intento == 4:
                        raise
                    time.sleep(.3*(intento+1))
            if resultado == "omitido":
                omitidos += 1
                continue
            if resultado == "recuperado":
                recuperados += 1
            else:
                completados += 1
            total = completados+recuperados
            if total % 15 == 0:
                guardar_manifest(manifest, CARPETA_VOCES)
                print(f"{total+omitidos}/{len(manifest['clips'])} clips · {round(time.monotonic()-inicio)} s", flush=True)
    finally:
        guardar_manifest(manifest, CARPETA_VOCES)
        (CARPETA_VOCES / ".mezcla_dialogos_v2.mp3").unlink(missing_ok=True)
    mezclados = [c for c in manifest["clips"].values() if c.get("mezcla_dialogos") == VERSION_MEZCLA]
    informe["resumen"] = {"catalogo": len(manifest["clips"]), "mezclados": len(mezclados),
                           "producidos_ahora": completados, "recuperados": recuperados,
                           "omitidos_por_marca": omitidos, "segundos": round(time.monotonic()-inicio, 3),
                           "mediana_ganancia_rms_db": round(statistics.median(c["ganancia_rms_db"] for c in mezclados), 3),
                           "pico_maximo": max(c["pico_real"] for c in mezclados)}
    manifest["mezcla_dialogos"] = VERSION_MEZCLA if len(mezclados) == len(manifest["clips"]) else 1
    manifest["mezcla_dialogos_detalles"] = {"filtro": FILTRO, **informe["resumen"]}
    guardar_manifest(manifest, CARPETA_VOCES)
    REPORTE.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(informe["resumen"], ensure_ascii=False), flush=True)
    return informe


def verificar_instalacion(carpeta=CARPETA_VOCES):
    """Audita marcas, contenido, identidad y tiempo sin volver a recodificar."""
    manifest = cargar_manifest(carpeta)
    voces = Counter()
    desviaciones = []
    ganancias = []
    picos = []
    adaptados = 0
    for clave, entrada in manifest.get("clips", {}).items():
        ruta = ruta_clip(entrada, carpeta)
        if (ruta is None or entrada.get("mezcla_dialogos") != VERSION_MEZCLA
                or entrada.get("sha256_mezclado") != sha256(ruta)):
            raise ValueError(f"Mezcla sin finalizar o archivo cambiado: {clave}")
        marca = leer_marca(ruta)
        if marca != entrada.get("mezcla_original"):
            raise ValueError(f"La marca y el catálogo difieren: {clave}")
        if (clave_clip(entrada["hablante"], entrada["texto"]) != clave or ruta.name != clave+".mp3"
                or entrada["voz"] != PERFILES[entrada["hablante"]]["voz"]):
            raise ValueError(f"Cambió la identidad del diálogo: {clave}")
        diferencia = abs(entrada["duracion_ms"]-marca["duracion_original_ms"])
        if diferencia > 60 or entrada["pico_real"] >= .98 or not entrada.get("envolvente"):
            raise ValueError(f"El nivel o el tiempo salen del margen: {clave}")
        desviaciones.append(diferencia)
        ganancias.append(entrada["ganancia_rms_db"])
        picos.append(entrada["pico_real"])
        voces[entrada["hablante"]] += 1
        volumen = float(marca.get("filtro", FILTRO).rsplit("volume=", 1)[-1])
        adaptados += volumen < .8-1e-6
    if not ganancias:
        raise ValueError("No hay clips mezclados para auditar")
    return {"clips": len(ganancias), "identidades_conservadas": dict(voces),
            "hashes_texto_voz_y_archivo_conservados": True,
            "marcas_y_sha256_mp3_comprobados": True,
            "mediana_ganancia_rms_db": round(statistics.median(ganancias), 3),
            "pico_real_maximo": max(picos), "diferencia_duracion_maxima_ms": max(desviaciones),
            "clips_con_margen_adicional_mp3": adaptados}


def documentar_instalacion():
    auditoria = verificar_instalacion()
    informe = json.loads(REPORTE.read_text(encoding="utf-8"))
    informe["auditoria_instalacion"] = auditoria
    REPORTE.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
    doc = (f"# Mezcla local de los diálogos\n\n"
           f"El catálogo conserva {auditoria['clips']} tomas y ocho identidades neuronales. "
           f"La ganancia RMS mediana es {auditoria['mediana_ganancia_rms_db']:+.3f} dB; "
           f"el pico real decodificado máximo es {auditoria['pico_real_maximo']:.4f}. "
           f"La mayor variación de duración es {auditoria['diferencia_duracion_maxima_ms']} ms.\n\n"
           "Se mantienen las frases, intérpretes, nombres de archivo y claves del doblaje. "
           "La recodificación conserva MP3 mono, 24 kHz y 48 kbps. "
           "La envolvente labial se recalcula con `medir_audio`, la misma función que produce las voces.\n\n"
           f"Filtro base, calibrado con ocho personajes y ocho indicadores:\n\n`{FILTRO}`\n\n"
           f"En {auditoria['clips_con_margen_adicional_mp3']} clips se amplió el margen individual "
           "para controlar los sobrepicos al decodificar MP3. Cada intento vuelve a la toma original.\n\n"
           "La herramienta comprueba RMS, pico y duración antes del reemplazo atómico. "
           "El comentario ID3 guarda la versión y el origen; reanudar tras un corte no vuelve a aplicar la ganancia. "
           "El catálogo se guarda cada quince clips y al terminar. Solo se utiliza un MP3 temporal, "
           "menor de 110 kB en este catálogo, sin copias del paquete ni PCM en disco.\n\n"
           "Opciones `level=false` y `latency=true` verificadas con la ayuda local de FFmpeg 7.1 "
           "(`ffmpeg -h filter=alimiter`). La primera evita la autonormalización del limitador; "
           "la segunda compensa su retardo.\n\n"
           "```powershell\npython -B herramientas/normalizar_voces_locales.py\n"
           "python -B herramientas/normalizar_voces_locales.py --aplicar\n"
           "python -B herramientas/normalizar_voces_locales.py --verificar\n```\n\n"
           "[Mediciones por voz y auditoría](verificacion_volumen_voces.json). "
           "Las cifras describen nivel digital; no son una evaluación de escucha humana.\n")
    (RAIZ / "docs/mezcla_voces.md").write_text(doc, encoding="utf-8")
    return auditoria


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aplicar", action="store_true")
    parser.add_argument("--limite", type=int, default=0)
    parser.add_argument("--verificar", action="store_true")
    args = parser.parse_args()
    if args.verificar:
        print(json.dumps(documentar_instalacion(), ensure_ascii=False), flush=True)
    else:
        ejecutar(aplicar=args.aplicar, limite=args.limite)
