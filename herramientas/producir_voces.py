"""Preproduce el doblaje español y su envolvente labial, sin red al jugar.

Preparación: pip install --target .tmp/deps -r herramientas/requirements_voces.txt
Inventario: python herramientas/producir_voces.py --inventario
Producción: python herramientas/producir_voces.py --concurrencia 3
Reanuda por hash, conserva cada frase terminada y limita solicitudes paralelas.
"""
import argparse
import ast
import asyncio
import array
from datetime import datetime, timezone
import itertools
from importlib.metadata import version
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".tmp/deps"))
from audio.catalogo_voces import (CARPETA_VOCES, PERFILES, clave_clip,
                                 cargar_manifest, frases_texto, normalizar_texto,
                                 partes_resultado, pronunciacion, texto_grupo)


def inventario():
    from juego.historia import dialogos_publicacion, contenido_resultado
    from juego.partida import Juego
    textos = {}
    def agregar(nombre, texto):
        texto = normalizar_texto(texto)
        if texto:
            textos[clave_clip(nombre, texto)] = {"hablante": nombre, "texto": texto}
    def recoger(juego):
        for tipo in (1, 2, 3):
            texto, nombre = contenido_resultado(juego, tipo)
            agregar(nombre, texto)
            if tipo == 3:
                agregar(nombre, texto_grupo(texto))
                for parte in partes_resultado(texto):
                    agregar(nombre, parte)
    # Se leen las introducciones del código para detectar cambios de guion.
    arbol = ast.parse((ROOT / "interfaz.py").read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name)
                and nodo.func.id == "EscenaNarracion" and len(nodo.args) > 1
                and isinstance(nodo.args[1], ast.Constant)):
            agregar("NARRADOR", nodo.args[1].value)
    # Las 4096 historias de cada rol cubren recuerdos, alcance, límites de
    # indicadores y las consecuencias reales, sin adivinar cifras.
    acciones = ("verificar", "compartir", "reportar", "ignorar")
    for rol in ("ciudadano", "periodista"):
        for camino in itertools.product(acciones, repeat=6):
            juego = Juego(4, eventos=False)
            juego.seleccionar_rol(rol)
            juego.iniciar_primera_publicacion()
            for accion in camino:
                for nombre, texto in dialogos_publicacion(juego):
                    agregar(nombre, texto)
                juego.ejecutar_accion(accion)
                recoger(juego)
                juego.avanzar_publicacion()
    # La conexión Pedro–Inés y el emisor de cada participante alteran alcance,
    # tiempo y receptor. Son variantes reales del grafo, sin inventar números.
    base = Juego(4, eventos=False)
    from juego.red_social import ampliar_comunidad
    ampliar_comunidad(base.grafo, 6)
    for rol, emisor, conexion, accion, conflicto in itertools.product(
            ("ciudadano", "periodista"), tuple(base.grafo.nodos),
            (False, True), acciones, (0, 1)):
        juego = Juego(4, eventos=False)
        juego.seleccionar_rol(rol)
        juego.jugador.ciudadano_id = emisor
        if conexion:
            juego.grafo.agregar_arista("pedro", "ines")
        juego.iniciar_primera_publicacion()
        for _ in range(6):
            if not juego.grafo.existe_vertice(emisor):
                juego.ejecutar_accion("ignorar")
            else:
                juego.estado.conflictos = conflicto
                juego.ejecutar_accion(accion)
                recoger(juego)
            juego.avanzar_publicacion()
    for nombre, texto in (
        ("CIUDADANO", "Hola, soy un vecino de Ciudad Nova."),
        ("PERIODISTA", "Revisemos las fuentes antes de compartir."),
        ("NARRADOR", "Cada decisión transforma nuestra ciudad."),
        ("NARRADOR", "Esta frase debe detenerse al silenciar el juego."),
        ("NARRADOR", "La campaña ya no tiene publicaciones pendientes."),
        ("NARRADOR", "Todavía no se ha tomado una decisión."),
        ("NARRADOR", "Una nueva publicación interrumpe la conversación."),
        ("CIUDADANO", "Este mensaje puede cambiar lo que piensan nuestros vecinos."),
        ("PERIODISTA", "Revisemos su autor, su fecha y el contexto antes de actuar."),
    ):
        agregar(nombre, texto)
    # Los indicadores se limitan a 0..100: al llegar a cero una resta puede
    # quedar entre cero y su delta máximo. Se graban estos bloques legales para
    # combinaciones de eventos y emisores que no ocurren en la misma ruta fija.
    deltas = {
        "Info verificada": tuple(range(1, 11)),
        "Confianza": tuple(range(-5, 0)) + tuple(range(1, 7)),
        "Desinformacion": tuple(range(-8, 0)) + tuple(range(1, 16)),
        "Convivencia": tuple(range(-5, 0)) + tuple(range(1, 6)),
        "Bienestar digital": tuple(range(-5, 0)) + tuple(range(1, 6)),
        "Conflictos": (-2, -1, 1, 2, 3, 4, 5),
        "Participacion": (1, 2, 3, 4, 5),
    }
    for indicador, valores in deltas.items():
        for valor in valores:
            agregar("NARRADOR", f"{indicador} {valor:+d}.")
    # Frases de resultados permiten unir variantes sin volver a sintetizar una
    # conversación durante el juego. Las líneas completas conservan su toma.
    for dialogo in list(textos.values()):
        for frase in frases_texto(dialogo["texto"]):
            agregar(dialogo["hablante"], frase)
    textos.update(inventario_roles())
    return textos


def inventario_roles():
    """Cobertura de los ocho métodos por oficio, sin expandir 8**6 rutas.

    Las rutas constantes y parejas cubren cada decisión y sus recuerdos; los
    emisores y eventos aportan variantes reales. Las cifras se componen desde
    clips completos cortos, por lo que no necesitan una toma por cada conjunto
    posible de siete indicadores.
    """
    from juego.acciones import acciones_para_rol
    from juego.historia import dialogos_publicacion, contenido_resultado
    from juego.partida import Juego
    from audio.catalogo_voces import segmentos_indicadores
    textos = {}

    def agregar(nombre, texto):
        texto = normalizar_texto(texto)
        if texto:
            textos[clave_clip(nombre, texto)] = {"hablante": nombre, "texto": texto}

    for rol in ("ciudadano", "periodista"):
        opciones = tuple(a["clave"] for a in acciones_para_rol(rol))
        for pareja, emisor, semilla in itertools.product(itertools.product(opciones, repeat=2),
                                                       ("ana", "maria", "sofia", "ines"), (4, 19)):
            juego = Juego(semilla, eventos=semilla != 4)
            juego.seleccionar_rol(rol)
            juego.jugador.ciudadano_id = emisor
            juego.iniciar_primera_publicacion()
            for turno in range(6):
                for nombre, texto in dialogos_publicacion(juego):
                    agregar(nombre, texto)
                juego.ejecutar_accion(pareja[turno % 2])
                for tipo in (1, 2, 3):
                    texto, nombre = contenido_resultado(juego, tipo)
                    agregar(nombre, texto)
                for segmento in segmentos_indicadores(juego.ultimo_registro):
                    agregar("NARRADOR", segmento["texto"])
                juego.avanzar_publicacion()
    textos.update(inventario_contadores())
    textos.update(inventario_propagacion())
    for dialogo in list(textos.values()):
        for frase in frases_texto(dialogo["texto"]):
            agregar(dialogo["hablante"], frase)
    return textos


def inventario_contadores():
    """Tomas completas que sincronizan cada tarjeta de cifras con la voz."""
    from audio.catalogo_voces import ETIQUETAS_INDICADORES
    textos = {}

    def agregar(texto):
        textos[clave_clip("NARRADOR", texto)] = {"hablante": "NARRADOR", "texto": texto}

    # Deltas legales incluso cuando un indicador queda recortado en 0 o 100.
    limites = {"info_verificada": (1, 10), "confianza": (-10, 6),
               "desinformacion": (-8, 20), "convivencia": (-5, 5),
               "bienestar_digital": (-5, 5), "conflictos": (-2, 10),
               "participacion": (-1, 10)}
    for clave, (minimo, maximo) in limites.items():
        for delta in range(minimo, maximo + 1):
            if delta:
                agregar(f"{ETIQUETAS_INDICADORES[clave]} {delta:+d}.")
    for puntos in range(-15, 16):
        agregar(f"Puntuación de la acción: {puntos:+d}.")
    return textos


def inventario_propagacion():
    """Vocabulario completo del alcance de las dos profesiones jugables.

    Son bloques que sólo se seleccionan con datos del ResultadoPropagacion.
    Cubren hasta dieciocho receptores (diecinueve personas menos el emisor),
    y tiempos posibles según profundidad real e intervalo de cada oficio.
    """
    textos = {}
    from juego.red_social import crear_red_social, ampliar_comunidad
    red = crear_red_social()
    ampliar_comunidad(red, 6)
    for vecino in red.nodos.values():
        texto = f"{vecino.nombre} está entre sus receptores."
        textos[clave_clip("NARRADOR", texto)] = {"hablante": "NARRADOR", "texto": texto}
    for correccion in (False, True):
        objeto = "La corrección" if correccion else "La publicación"
        cero = f"{objeto} no alcanzó a otros ciudadanos: 0 receptores en 0 unidades simuladas."
        textos[clave_clip("NARRADOR", cero)] = {"hablante": "NARRADOR", "texto": cero}
        if correccion:
            textos[clave_clip("PERIODISTA", cero)] = {"hablante": "PERIODISTA", "texto": cero}
        for intervalo in (1.0, .8):
            # Convocar es exclusivo del ciudadano; no existe un tercer nivel
            # de una rectificación ni una convocatoria de la periodista.
            profundidad_maxima = 3 if not correccion and intervalo == 1.0 else 2
            for alcance in range(1, 19):
                for profundidad in range(1, min(alcance, profundidad_maxima) + 1):
                    unidad = "ciudadano" if alcance == 1 else "ciudadanos"
                    texto = (f"{objeto} llegó a {alcance} {unidad} en "
                             f"{profundidad * intervalo:g} unidades simuladas.")
                    textos[clave_clip("NARRADOR", texto)] = {"hablante": "NARRADOR", "texto": texto}
                    if correccion:
                        textos[clave_clip("PERIODISTA", texto)] = {"hablante": "PERIODISTA", "texto": texto}
    return textos


def medir_audio(ruta, ffmpeg):
    resultado = subprocess.run([ffmpeg, "-v", "error", "-i", str(ruta), "-f", "s16le",
                                "-ac", "1", "-ar", "8000", "pipe:1"],
                               capture_output=True, check=True)
    muestras = array.array("h", resultado.stdout)
    if not muestras:
        raise ValueError("Audio sin muestras: " + ruta.name)
    ventana = 400  # 50 ms, suficiente para acompañar sílabas sin vibración.
    niveles = []
    for inicio in range(0, len(muestras), ventana):
        tramo = muestras[inicio:inicio+ventana]
        rms = (sum(m*m for m in tramo) / len(tramo)) ** .5 / 32768
        niveles.append(round(min(1.0, rms * 9.0), 3))
    return {"duracion_ms": round(len(muestras) / 8), "paso_envolvente_ms": 50,
            "envolvente": niveles, "pico": round(max(abs(m) for m in muestras) / 32768, 4)}


async def producir(textos, args):
    import edge_tts
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    CARPETA_VOCES.mkdir(parents=True, exist_ok=True)
    manifest = cargar_manifest() or {
        "version": 1, "motor": "Microsoft Edge Neural · clips locales",
        "fuentes": ["https://github.com/rany2/edge-tts",
                    "https://learn.microsoft.com/azure/ai-services/speech-service/language-support"],
        "aviso": "Voces sintéticas neuronales, no grabaciones de actores humanos.",
        "perfiles": PERFILES, "clips": {},
    }
    manifest["perfiles"] = PERFILES
    manifest["herramientas"] = {nombre: version(nombre) for nombre in ("edge-tts", "imageio-ffmpeg")}
    semaforo = asyncio.Semaphore(args.concurrencia)
    fallos = []
    completados = 0
    inicio = time.monotonic()
    def guardar():
        manifest["actualizado_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        temporal = CARPETA_VOCES / "manifest.json.tmp"
        temporal.write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        temporal.replace(CARPETA_VOCES / "manifest.json")
    async def uno(clave, dialogo):
        nonlocal completados
        destino = CARPETA_VOCES / (clave + ".mp3")
        entrada = manifest["clips"].get(clave, {})
        if destino.is_file() and entrada.get("envolvente") and not args.forzar:
            completados += 1
            return
        async with semaforo:
            perfil = PERFILES.get(dialogo["hablante"], PERFILES["NARRADOR"])
            temporal = destino.with_suffix(".part.mp3")
            for intento in range(3):
                try:
                    voz = edge_tts.Communicate(pronunciacion(dialogo["texto"]), perfil["voz"],
                                               rate=perfil["ritmo"], pitch=perfil["tono"],
                                               connect_timeout=15, receive_timeout=45)
                    await asyncio.wait_for(voz.save(str(temporal)), timeout=65)
                    if temporal.stat().st_size < 1000:
                        raise ValueError("Clip demasiado pequeño")
                    medicion = await asyncio.to_thread(medir_audio, temporal, ffmpeg)
                    temporal.replace(destino)
                    manifest["clips"][clave] = {**dialogo, "voz": perfil["voz"],
                                                "archivo": destino.name, **medicion}
                    completados += 1
                    guardar()
                    if completados % 10 == 0 or completados == len(textos):
                        print(f"{completados}/{len(textos)} clips · {round(time.monotonic()-inicio)} s", flush=True)
                    return
                except Exception as error:
                    if intento < 2:
                        await asyncio.sleep(2 + intento * 3)
                    else:
                        fallos.append({"clave": clave, "error": str(error)})
                        print("No producido: " + clave + " " + str(error), flush=True)
    await asyncio.gather(*(uno(clave, dialogo) for clave, dialogo in textos.items()))
    guardar()
    resumen = {"clips": len(manifest["clips"]), "pendientes": len(fallos),
               "duracion_minutos": round(sum(c["duracion_ms"] for c in manifest["clips"].values())/60000, 2),
               "errores": fallos}
    print(json.dumps(resumen, ensure_ascii=False), flush=True)
    return bool(fallos)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventario", action="store_true")
    parser.add_argument("--concurrencia", type=int, default=3, choices=range(1, 5))
    parser.add_argument("--limite", type=int, default=0)
    parser.add_argument("--forzar", action="store_true")
    parser.add_argument("--solo-roles", action="store_true",
                        help="Inventario rápido de los ocho métodos actuales y sus cifras.")
    parser.add_argument("--solo-contadores", action="store_true",
                        help="Únicamente las cifras sincronizadas con las tarjetas de impacto.")
    parser.add_argument("--solo-faltantes", action="store_true",
                        help="Filtra el inventario antes del límite, conservando las tomas locales.")
    args = parser.parse_args()
    textos = (inventario_contadores() if args.solo_contadores else
              inventario_roles() if args.solo_roles else inventario())
    if args.solo_faltantes:
        existentes = cargar_manifest().get("clips", {})
        textos = {k: d for k, d in textos.items() if not (k in existentes
                  and (CARPETA_VOCES / existentes[k]["archivo"]).is_file()
                  and existentes[k].get("envolvente"))}
    print(json.dumps({"dialogos_unicos": len(textos), "caracteres": sum(len(d["texto"]) for d in textos.values()),
                      "por_hablante": {p: sum(d["hablante"] == p for d in textos.values()) for p in PERFILES}}), flush=True)
    if args.inventario:
        return 0
    if args.limite:
        textos = dict(itertools.islice(textos.items(), args.limite))
    return asyncio.run(producir(textos, args))


if __name__ == "__main__":
    sys.exit(main())
