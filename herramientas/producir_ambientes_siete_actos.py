"""Monta cuatro ambientes y cuatro gestos sonoros usando el paquete CC0 local.

Producción determinista y sin descargas. Conserva las fuentes, sus licencias y
los hashes del resultado. No sintetiza voces ni añade mensajes comprensibles.
"""
import hashlib
import json
import array
from pathlib import Path
import wave

RAIZ = Path(__file__).resolve().parents[1]

BASE = RAIZ / "assets/audio/expansion"
SALIDA = RAIZ / "assets/audio/siete_actos"
HZ = 32000


def leer(ruta):
    with wave.open(str(ruta), "rb") as archivo:
        assert archivo.getsampwidth() == 2 and archivo.getframerate() == HZ
        muestras = array.array("h", archivo.readframes(archivo.getnframes()))
        canales = archivo.getnchannels()
        return [sum(muestras[i:i+canales]) / (32768 * canales)
                for i in range(0, len(muestras), canales)]


def producir():
    SALIDA.mkdir(parents=True, exist_ok=True)
    recursos = {}
    recetas = {
        "estudio": (30, (("ambientes/oficina", .4, 0, None),
                          ("efectos/teclado", .19, 3, 8), ("efectos/clic_real", .14, 6, 7))),
        "debate": (30, (("ambientes/cafe", .3, 0, None),
                         ("ambientes/oficina", .18, 0, None), ("efectos/papeles", .13, 7, 11))),
        "redaccion": (30, (("ambientes/interior_lluvia", .42, 0, None),
                            ("ambientes/oficina", .24, 0, None), ("efectos/teclado", .22, 2, 10))),
        "urnas": (30, (("ambientes/calle", .32, 0, None),
                        ("efectos/pasos_madera", .13, 4, 12), ("efectos/pagina", .17, 8, 10))),
        "directo": (1.6, (("efectos/clic_real", .38, .08, None),
                           ("efectos/notificacion_suave", .27, .35, None))),
        "microfono": (1.8, (("efectos/papeles", .25, .05, None),
                             ("efectos/clic_real", .32, .9, None))),
        "archivo_audio": (2.4, (("efectos/teclado", .3, .05, None),
                                 ("efectos/clic_real", .37, 1.55, None))),
        "papeleta": (2.4, (("efectos/pagina", .3, .05, None),
                            ("efectos/papeles", .25, .85, None))),
    }
    for nombre, (duracion, capas) in recetas.items():
        mezcla = [0.0] * round(HZ * duracion)
        fuentes = []
        for recurso, volumen, inicio, intervalo in capas:
            ruta = BASE / (recurso + ".wav")
            audio = leer(ruta)
            fuentes.append({"archivo": str(ruta.relative_to(RAIZ)),
                             "sha256": hashlib.sha256(ruta.read_bytes()).hexdigest(),
                             "ganancia": volumen})
            if recurso.startswith("ambientes/"):
                for i in range(len(mezcla)):
                    mezcla[i] += audio[i % len(audio)] * volumen
                continue
            segundo = inicio
            while segundo < duracion:
                desde = round(segundo * HZ)
                largo = min(len(audio), len(mezcla)-desde)
                for i in range(largo):
                    mezcla[desde+i] += audio[i] * volumen
                segundo += intervalo or duracion + 1
        # Los dos extremos llegan a cero; el bucle no introduce un chasquido.
        fundido = min(round(HZ * .35), len(mezcla)//4)
        for i in range(fundido):
            mezcla[i] *= i / (fundido-1)
            mezcla[-1-i] *= i / (fundido-1)
        pico = max(abs(x) for x in mezcla)
        ganancia = min(1, .72 / pico) if pico else 1
        ruta = SALIDA / (nombre + ".wav")
        with wave.open(str(ruta), "wb") as destino:
            destino.setparams((1, 2, HZ, 0, "NONE", "not compressed"))
            destino.writeframes(array.array("h", (round(x*ganancia*32767) for x in mezcla)).tobytes())
        recursos[nombre] = {"duracion_s": duracion, "hz": HZ,
                            "pico": round(pico * ganancia, 4),
                            "sha256": hashlib.sha256(ruta.read_bytes()).hexdigest(), "capas": fuentes}
    manifest = {"version": 1, "licencia": "CC0-1.0", "tipo": "montajes de fuentes locales",
                "procedencia": "assets/audio/expansion/licencias.json",
                "descripcion": "Grabaciones ambientales y foley; notificación electrónica indicada en la fuente. Sin voces nuevas ni victoria electoral implícita.",
                "recursos": recursos}
    (SALIDA / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ambientes": 4, "efectos": 4, "segundos": sum(x[0] for x in recetas.values())}))


if __name__ == "__main__":
    producir()
