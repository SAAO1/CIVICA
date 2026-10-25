"""Produce y verifica las voces locales de la campaña de siete actos.

Usa el productor neuronal existente, conserva los clips terminados por hash y
no necesita recorrer 4**14 historias. El guion declara sus ramas finitas; los
indicadores y la propagación se enumeran dentro de los límites del modelo.

Inventario: python -B herramientas/producir_voces_siete_actos.py --inventario
Producción: python -B herramientas/producir_voces_siete_actos.py --solo-faltantes
Verificar: python -B herramientas/producir_voces_siete_actos.py --verificar
"""
import argparse
import ast
import asyncio
from collections import Counter
from datetime import datetime, timezone
import itertools
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".tmp/deps"))

from audio.catalogo_voces import (
    CARPETA_VOCES, PERFILES, cargar_manifest, clave_clip, frases_texto,
    normalizar_texto, ruta_clip,
)
from herramientas.producir_voces import (
    inventario_contadores, inventario_propagacion, producir,
)
from juego.campana_extendida import FRASES_POSIBLES


def inventario_siete_actos():
    """Líneas completas, sus fragmentos y el vocabulario finito del modelo."""
    textos = {}

    def agregar(nombre, texto):
        texto = normalizar_texto(texto)
        if texto:
            textos[clave_clip(nombre, texto)] = {"hablante": nombre, "texto": texto}

    for nombre, texto in FRASES_POSIBLES:
        agregar(nombre, texto)
    textos.update(inventario_contadores())
    textos.update(inventario_propagacion())

    # La nueva comunidad reserva «Valeria» para la influencer y llama Violeta
    # a la vecina anterior. Solo recorremos una campaña, sin bifurcar historias,
    # para obtener los nombres y el límite real de receptores del grafo final.
    from juego.partida import Juego
    juego = Juego(4, eventos=False, campana="extendida")
    juego.iniciar_primera_publicacion()
    while not juego.finalizada:
        juego.ejecutar_accion("ignorar")
        juego.avanzar_publicacion()
    for vecino in juego.grafo.nodos.values():
        agregar("NARRADOR", f"{vecino.nombre} está entre sus receptores.")
    for correccion in (False, True):
        objeto = "La corrección" if correccion else "La publicación"
        for intervalo in (1.0, .8):
            profundidad_maxima = 3 if not correccion and intervalo == 1.0 else 2
            for alcance in range(1, len(juego.grafo.nodos)):
                unidad = "ciudadano" if alcance == 1 else "ciudadanos"
                for profundidad in range(1, min(alcance, profundidad_maxima) + 1):
                    texto = (f"{objeto} llegó a {alcance} {unidad} en "
                             f"{profundidad * intervalo:g} unidades simuladas.")
                    agregar("NARRADOR", texto)
                    if correccion:
                        agregar("PERIODISTA", texto)

    # Las introducciones constantes de la interfaz también tienen voz si la
    # integración añade una entrada nueva para esta campaña.
    arbol = ast.parse((ROOT / "interfaz.py").read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name)
                and nodo.func.id == "EscenaNarracion" and len(nodo.args) > 1
                and isinstance(nodo.args[1], ast.Constant)
                and isinstance(nodo.args[1].value, str)):
            agregar("NARRADOR", nodo.args[1].value)

    # Cada línea conserva una toma completa; el lector puede además componer
    # una frase cuando muestra un bloque por partes. Se enumera una vez.
    for dialogo in list(textos.values()):
        for frase in frases_texto(dialogo["texto"]):
            agregar(dialogo["hablante"], frase)
    return textos


def pendientes(textos, manifest=None):
    manifest = cargar_manifest() if manifest is None else manifest
    existentes = manifest.get("clips", {})
    return {clave: entrada for clave, entrada in textos.items()
            if not (clave in existentes and ruta_clip(existentes[clave]) is not None
                    and existentes[clave].get("envolvente"))}


def verificar_cobertura(textos=None, manifest=None):
    textos = inventario_siete_actos() if textos is None else textos
    manifest = cargar_manifest() if manifest is None else manifest
    clips = manifest.get("clips", {})
    errores = []
    for clave, dialogo in textos.items():
        entrada = clips.get(clave)
        if not entrada:
            errores.append({"clave": clave, "tipo": "sin_toma", **dialogo})
            continue
        ruta = ruta_clip(entrada)
        if ruta is None or ruta.stat().st_size < 1000:
            errores.append({"clave": clave, "tipo": "archivo_ausente_o_vacio"})
        if entrada.get("texto") != dialogo["texto"] or entrada.get("hablante") != dialogo["hablante"]:
            errores.append({"clave": clave, "tipo": "texto_o_interprete_distinto"})
        voz = PERFILES[dialogo["hablante"]]["voz"]
        if entrada.get("voz") != voz:
            errores.append({"clave": clave, "tipo": "identidad_distinta", "esperada": voz})
        if entrada.get("duracion_ms", 0) < 100 or not any(n > .01 for n in entrada.get("envolvente", ())):
            errores.append({"clave": clave, "tipo": "audio_sin_duracion_o_senal"})
    return {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "correcto": not errores,
        "frases_guion": len(FRASES_POSIBLES), "inventario_total": len(textos),
        "clips_manifest": len(clips),
        "por_hablante": dict(Counter(e["hablante"] for e in textos.values())),
        "identidades": {nombre: perfil["voz"] for nombre, perfil in PERFILES.items()},
        "aviso": "Voces neuronales sintéticas locales, no grabaciones de actores humanos.",
        "errores": errores,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventario", action="store_true")
    parser.add_argument("--verificar", action="store_true")
    parser.add_argument("--concurrencia", type=int, default=3, choices=range(1, 5))
    parser.add_argument("--solo-faltantes", action="store_true")
    parser.add_argument("--limite", type=int, default=0)
    parser.add_argument("--forzar", action="store_true")
    parser.add_argument("--reporte", type=Path, default=ROOT / "docs/verificacion_voces_siete_actos.json")
    args = parser.parse_args()
    inventario = inventario_siete_actos()
    faltantes = pendientes(inventario)
    print(json.dumps({"frases_guion": len(FRASES_POSIBLES), "inventario": len(inventario),
                      "faltantes": len(faltantes), "ya_locales": len(inventario) - len(faltantes),
                      "por_hablante": dict(Counter(e["hablante"] for e in faltantes.values()))},
                     ensure_ascii=False), flush=True)
    if args.inventario:
        return 0
    if not args.verificar:
        textos = faltantes if args.solo_faltantes else inventario
        if args.limite:
            textos = dict(itertools.islice(textos.items(), args.limite))
        errores_produccion = asyncio.run(producir(textos, args))
        if errores_produccion:
            return 1
    informe = verificar_cobertura(inventario)
    args.reporte.parent.mkdir(parents=True, exist_ok=True)
    args.reporte.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"correcto": informe["correcto"], "inventario": informe["inventario_total"],
                      "clips_manifest": informe["clips_manifest"], "errores": len(informe["errores"]),
                      "reporte": str(args.reporte)}, ensure_ascii=False), flush=True)
    return 0 if informe["correcto"] else 1


if __name__ == "__main__":
    sys.exit(main())
