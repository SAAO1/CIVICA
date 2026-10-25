"""Publica evidencia de los 92 transportes y ocho botones ya comprobados.

No ejecuta ni sustituye pruebas: requiere los informes completos producidos
por verificar_inicio_video.py, preparar_portadas_video.py y la UI real.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QColor, QFont, QImage, QPainter
from PyQt6.QtWidgets import QApplication
from arte import FUENTE_UI, cargar_tipografias
from juego.cinematica import CINEMATICAS
from juego.cinematica_final import CINEMATICAS_FINALES
from juego.cinematica_acciones import ACCIONES_VIDEO, CINEMATICAS_ACCIONES


def sha256(ruta):
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def leer(ruta):
    return json.loads((RAIZ/ruta).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transporte", type=Path, action="append",
                        help="Informe Qt completo o lote; se puede repetir, las claves posteriores reemplazan las anteriores")
    parser.add_argument("--suite", type=Path, help="Resumen JSON del ejecutor oficial, una vez terminado")
    args = parser.parse_args()
    catalogo = {**CINEMATICAS, **{f"final_{k}": v for k, v in CINEMATICAS_FINALES.items()},
                **CINEMATICAS_ACCIONES}
    rutas_qt = ([str(r) for r in args.transporte] if args.transporte else
                [".tmp/inicios_video_qt_todos.json"] if (RAIZ/".tmp/inicios_video_qt_todos.json").is_file() else
                [".tmp/inicios_video_qt_narrativos.json", ".tmp/inicios_video_qt_finales.json",
                 ".tmp/inicios_video_qt_acciones_36.json", ".tmp/inicios_video_qt_acciones_30.json",
                 ".tmp/inicios_video_qt_convocar_final.json"])
    clips = {}
    for ruta in rutas_qt:
        registro = leer(ruta)
        assert registro["cantidad"] == registro["esperados"], (ruta, "lote parcial")
        clips.update({clip["clave"]: clip for clip in registro["clips"]})
    assert set(clips) == set(catalogo), f"Transportes pendientes: {set(catalogo)-set(clips)}"
    assert len(clips) == 92
    for clave, clip in clips.items():
        assert clip["cubierta_inicial_exacta"] and clip["pausa_congela_ultimo_plano"]
        assert clip["fuente_anterior_liberada"] and clip["diferencia_inicio_rgb"] < 5
        for tipo in ("video", "inicio"):
            actual = sha256(RAIZ/catalogo[clave][tipo])
            registrada = clip.get(f"{tipo}_sha256")
            assert registrada is None or registrada == actual, (clave, f"{tipo} cambió después de comprobarlo")
            clip[f"{tipo}_sha256_entregado"] = actual
    portadas = leer(".tmp/inicios_video_verificados.json")
    assert portadas["cantidad"] == 92
    assert all(c["diferencia_maxima_rgb"] == 0 and c["pixeles_distintos"] == 0 for c in portadas["clips"])
    assert {c["inicio"] for c in portadas["clips"]} == {v["inicio"] for v in catalogo.values()}
    for clip in portadas["clips"]:
        assert clip["inicio_sha256"] == sha256(RAIZ/clip["inicio"]), clip["inicio"]
    ui = leer(".tmp/acciones_ui_real/resultado.json")
    assert ui["correcto"] and ui["completo_ocho_botones"]
    assert ui["preferencias_sin_cambios"] and ui["guardado_config_no_invocado"]
    assert {c["accion"] for c in ui["casos"]} == set(ACCIONES_VIDEO)
    por_accion = {c["accion"]: c for c in ui["casos"]}
    casos = [por_accion[a] for a in ACCIONES_VIDEO]
    for caso in casos:
        assert caso["pulsaciones_bloqueadas"] == 100 and caso["fin_real_ms"] >= 8900
        assert caso["avance_solo_despues_del_video"] and caso["partida_sin_cambios_durante_presentacion"]
        for tipo in ("video", "inicio"):
            assert caso[f"sha256_{tipo}"] == sha256(RAIZ/CINEMATICAS_ACCIONES[caso["clave"]][tipo])
    inventario = leer("assets/expansion/audiovisual_manifest.json")
    assert inventario["mp4"] == 95 and inventario["mp4_acciones"] == 66
    assert inventario["portadas_inicio_video"] == 92
    app = QApplication.instance() or QApplication([])
    cargar_tipografias()
    contacto = QImage(1280, 412, QImage.Format.Format_RGB32)
    contacto.fill(QColor("#10222a"))
    pintor = QPainter(contacto)
    pintor.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    fuente = QFont(FUENTE_UI)
    fuente.setPixelSize(16)
    pintor.setFont(fuente)
    for i, caso in enumerate(casos):
        imagen = QImage(str(RAIZ/caso["captura"]))
        assert not imagen.isNull()
        x, y = i%4*320, i//4*206
        pintor.drawImage(QRect(x, y, 320, 180), imagen)
        pintor.setPen(QColor("#f6e7c7"))
        pintor.drawText(QRect(x+7, y+180, 306, 26), Qt.AlignmentFlag.AlignVCenter,
                       f"{caso['texto_boton']} · caso {caso['publicacion']}")
    pintor.end()
    captura = RAIZ / "docs/vistas/acciones_comprobadas.jpg"
    captura.parent.mkdir(parents=True, exist_ok=True)
    assert contacto.save(str(captura), "JPG", 89)
    resultado = dict(fecha="2026-10-24", correcto=True,
        verificacion="Reproducción automatizada con QMediaPlayer y GestorAudio reales; no es una campaña humana",
        mp4_instalados=95, mp4_acciones=66, transportes_qt_unicos=92,
        cubiertas_rgb_exactas=92, diferencia_maxima_cubiertas_rgb=0,
        maxima_diferencia_primer_plano_qt_rgb=max(c["diferencia_inicio_rgb"] for c in clips.values()),
        botones_comprobados=8, pulsaciones_anticipadas_bloqueadas=sum(c["pulsaciones_bloqueadas"] for c in casos),
        video_fin_real_ms=[c["fin_real_ms"] for c in casos],
        convocar_alcance_real=por_accion["convocar"]["alcance"],
        reporte_rechazado=por_accion["desmentir"]["clave"].endswith("_rechazado"),
        partida_y_preferencias_sin_cambios=True,
        contacto=captura.relative_to(RAIZ).as_posix(),
        casos_ui=casos, transporte_qt=[clips[k] for k in catalogo],
        fuentes=[dict(archivo=r, sha256=sha256(RAIZ/r)) for r in rutas_qt+
                 [".tmp/inicios_video_verificados.json", ".tmp/acciones_ui_real/resultado.json"]])
    if args.suite:
        suite = json.loads(args.suite.read_text(encoding="utf-8"))
        assert suite["fallas"] == suite["errores"] == suite["omitidas"] == 0
        resultado["suite_completa"] = suite
    destino = RAIZ / "docs/verificacion_continuidad_acciones.json"
    destino.write_text(json.dumps(resultado, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in resultado.items() if k not in
                      ("casos_ui", "transporte_qt", "fuentes")}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
