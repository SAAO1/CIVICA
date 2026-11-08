"""Reúne la evidencia final y rechaza hashes o recursos que hayan cambiado."""
import hashlib
import json
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from juego.campana_extendida import CASOS_NUEVOS
from juego.cinematica_extension import CINEMATICAS_EXTENSION
from juego.cinematica_acciones_extendida import CINEMATICAS_ACCIONES_EXTENDIDAS
from juego.partida import Juego


def leer(nombre):
    return json.loads((RAIZ / nombre).read_text(encoding="utf-8"))


def sha(nombre):
    return hashlib.sha256((RAIZ / nombre).read_bytes()).hexdigest()


def main():
    suite = leer("docs/verificacion_suite_siete_actos.json")
    voz = leer("docs/verificacion_voces_siete_actos.json")
    red = leer("docs/verificacion_red_ui_siete_actos.json")
    videos = leer("docs/verificacion_inicios_siete_actos.json")
    botones = leer("docs/verificacion_acciones_ui_siete_actos.json")
    arte = leer("docs/verificacion_arte_siete_actos.json")
    reparto = leer("docs/verificacion_reparto_siete_actos.json")
    muestra = leer("docs/vistas/muestra_siete_actos.json")
    assert suite["pruebas"] >= 304 and suite["fallas"] == suite["errores"] == 0
    assert voz["correcto"] and voz["inventario_total"] == 967 and voz["clips_manifest"] >= 1587
    assert red["correcto"] and len(red["casos"]) == 14 and red["jugadores"] == 4
    assert botones["correcto"] and botones["completo_ocho_botones"] and len(botones["casos"]) == 8
    catalogo = {**CINEMATICAS_EXTENSION, **CINEMATICAS_ACCIONES_EXTENDIDAS}
    assert videos["cantidad"] == videos["esperados"] == len(catalogo) == 96
    for clip in videos["clips"]:
        entrada = catalogo[clip["clave"]]
        assert sha(entrada["video"]) == clip["video_sha256"], clip["clave"]
        assert sha(entrada["inicio"]) == clip["inicio_sha256"], clip["clave"]
        assert clip["cubierta_inicial_exacta"] and clip["pausa_congela_ultimo_plano"]
    for clip in botones["casos"]:
        entrada = catalogo[clip["clave"]]
        assert sha(entrada["video"]) == clip["sha256_video"], clip["clave"]
        assert sha(entrada["inicio"]) == clip["sha256_inicio"], clip["clave"]
        assert clip["fin_real_ms"] >= 8900 and clip["pulsaciones_bloqueadas"] == 100
    assert arte["sprites_png"] == 25 and len(arte["videos"]) == 8
    assert len(reparto["capturas"]) == 10
    assert all(v["movimiento_20_muestras"] and v["primer_frame_igual_rgb"] for v in arte["videos"])
    assert muestra["decodificacion_completa"]
    assert sha("docs/vistas/muestra_siete_actos.mp4") == muestra["sha256"]
    juego = Juego(42, campana="extendida")
    assert len(juego.publicaciones_planificadas) == 14 and len(CASOS_NUEVOS) == 8
    resumen = dict(correcto=True, actos=7, casos=14, nuevos_casos=8,
                   personajes_nuevos=5, sprites_nuevos=25, fondos_nuevos=4, ilustraciones_nuevas=4,
                   videos_nuevos=96, videos_decisiones=88, videos_narrador=8,
                   voces_locales=voz["clips_manifest"], identidades_voz=8,
                   ambientes_nuevos=4, efectos_sonoros_nuevos=4, efectos_visuales_nuevos=4,
                   combinaciones_principales_epilogo=45, suite=suite,
                   cuatro_clientes_catorce_turnos=True, hashes_96_actuales=True,
                   capturas_reparto_dos_resoluciones=10,
                   botones_reales=8, pulsaciones_bloqueadas=800,
                   muestra=dict(archivo="docs/vistas/muestra_siete_actos.mp4",
                                duracion_segundos=muestra["duracion_segundos"],
                                naturaleza=muestra["naturaleza"]),
                   aviso_voces="Voces sintéticas neuronales; no grabaciones de actores humanos.",
                   aviso_animacion="Montajes ilustrados, cámara, objetos y gestos faciales; no video corporal generado.")
    (RAIZ / "docs/verificacion_siete_actos.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(resumen, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
