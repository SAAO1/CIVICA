"""Comprueba cubiertas, cambio de fuente y reanudación con el códec real Qt."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_LOGGING_RULES", "qt.multimedia.*=false")

from PyQt6.QtCore import QCoreApplication, QEvent
from PyQt6.QtGui import QImage
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication
from cinematica_narrativa import CapaCinematica
from juego.cinematica import CINEMATICAS
from juego.cinematica_final import CINEMATICAS_FINALES


def esperar(condicion, descripcion):
    limite = time.monotonic()+8
    while not condicion():
        if time.monotonic() >= limite:
            raise AssertionError(f"Tiempo agotado: {descripcion}")
        QTest.qWait(10)


def datos(imagen):
    imagen = imagen.convertToFormat(QImage.Format.Format_RGBA8888)
    return imagen.constBits().asstring(imagen.sizeInBytes())


def diferencia(a, b):
    a, b = a.scaled(64, 36), b.scaled(64, 36)
    total = 0
    for y in range(36):
        for x in range(64):
            ca, cb = a.pixelColor(x, y), b.pixelColor(x, y)
            total += abs(ca.red()-cb.red())+abs(ca.green()-cb.green())+abs(ca.blue()-cb.blue())
    return round(total/(64*36*3), 4)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogo", choices=("todos", "acciones", "narrativos", "finales", "extension", "personajes"), default="todos")
    parser.add_argument("--accion", action="append", help="Filtra métodos del catálogo de acciones; se puede repetir")
    parser.add_argument("--clave", action="append", help="Limita la revisión a un corte concreto; se puede repetir")
    parser.add_argument("--exigir-completo", action="store_true", help="Rechaza un lote con videos o portadas pendientes")
    parser.add_argument("--destino", type=Path, default=RAIZ / ".tmp/inicios_video_qt_verificados.json")
    args = parser.parse_args()
    app = QApplication.instance() or QApplication([])
    catalogo = {}
    if args.catalogo in ("todos", "extension"):
        from juego.cinematica_extension import CINEMATICAS_EXTENSION
        from juego.cinematica_acciones_extendida import CINEMATICAS_ACCIONES_EXTENDIDAS
        catalogo.update(CINEMATICAS_EXTENSION)
        catalogo.update(CINEMATICAS_ACCIONES_EXTENDIDAS)
    if args.catalogo in ("todos", "extension", "personajes"):
        from juego.cinematica_personajes_extendida import CINEMATICAS_PERSONAJES_EXTENDIDAS
        catalogo.update(CINEMATICAS_PERSONAJES_EXTENDIDAS)
    if args.catalogo in ("todos", "narrativos"):
        catalogo.update(CINEMATICAS)
    if args.catalogo in ("todos", "finales"):
        catalogo.update({f"final_{clave}": entrada for clave, entrada in CINEMATICAS_FINALES.items()})
    if args.catalogo in ("todos", "acciones"):
        try:
            from juego.cinematica_acciones import CINEMATICAS_ACCIONES
            catalogo.update(CINEMATICAS_ACCIONES)
        except ImportError:
            if args.exigir_completo:
                raise
    if args.accion:
        catalogo = {clave: entrada for clave, entrada in catalogo.items() if entrada.get("accion") in args.accion}
        if not catalogo:
            raise ValueError("Ninguna entrada coincide con los métodos solicitados")
    if args.clave:
        desconocidas = set(args.clave)-set(catalogo)
        if desconocidas:
            raise ValueError(f"Cortes desconocidos: {sorted(desconocidas)}")
        catalogo = {clave: entrada for clave, entrada in catalogo.items() if clave in args.clave}
    if args.exigir_completo:
        faltantes = [entrada[tipo] for entrada in catalogo.values()
                     for tipo in ("video", "poster", "inicio") if not (RAIZ / entrada[tipo]).is_file()]
        if faltantes:
            raise RuntimeError(f"Lote incompleto: faltan {len(faltantes)} recursos; primero {faltantes[0]}")
    capa = CapaCinematica(catalogo=catalogo)
    capa.resize(640, 360)
    primeros = {}

    def primer_frame(clave):
        frame = capa._video.videoSink().videoFrame()
        primeros[clave] = dict(imagen=capa._video._imagen.copy(), tiempo=frame.startTime()/1000)

    capa.video_preparado.connect(primer_frame)
    registros = []
    try:
        for clave, entrada in catalogo.items():
            if not (RAIZ / entrada["video"]).is_file():
                continue
            assert capa.iniciar(clave, reproducir=False)
            assert capa.isVisible() and capa._poster.isVisible()
            assert capa._reproductor is None or capa._reproductor.source().isEmpty()
            cubierta = QImage(str(RAIZ / entrada["inicio"]))
            assert datos(capa._poster.imagen.toImage()) == datos(cubierta), clave
            capa.reanudar()
            esperar(lambda: clave in primeros, f"inicio de {clave}")
            primero = primeros[clave]
            error_inicio = diferencia(cubierta, primero["imagen"])
            assert error_inicio < 5, (clave, error_inicio, primero["tiempo"])
            reproductor = capa._reproductor
            reproductor.setPosition(2400)
            esperar(lambda: capa._video.videoSink().videoFrame().startTime() >= 2_300_000,
                    f"plano de pausa de {clave}")
            reproductor.pause()
            ultimo = capa._video._imagen.copy()
            posicion = reproductor.position()
            capa.pausar()
            assert reproductor.source().isEmpty()
            assert datos(capa._poster.imagen.toImage()) == datos(ultimo), clave
            capa.reanudar()
            assert datos(capa._poster.imagen.toImage()) == datos(ultimo), clave
            esperar(lambda: capa.estado == "reproduciendo", f"reanudación de {clave}")
            tiempo_reanudado = capa._video.videoSink().videoFrame().startTime()/1000
            assert tiempo_reanudado >= posicion-125, (clave, posicion, tiempo_reanudado)
            registros.append(dict(clave=clave, primer_frame_ms=primero["tiempo"],
                                   diferencia_inicio_rgb=error_inicio,
                                   video_sha256=hashlib.sha256((RAIZ/entrada["video"]).read_bytes()).hexdigest(),
                                   inicio_sha256=hashlib.sha256((RAIZ/entrada["inicio"]).read_bytes()).hexdigest(),
                                   cubierta_inicial_exacta=True, pausa_congela_ultimo_plano=True,
                                   posicion_guardada_ms=posicion, primer_frame_reanudado_ms=tiempo_reanudado,
                                   fuente_anterior_liberada=True))
            print(f"OK {clave}: cubierta exacta, vídeo continuo y pausa en {posicion} ms", flush=True)
    finally:
        capa.close()
        capa.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        destino = args.destino if args.destino.is_absolute() else RAIZ / args.destino
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(json.dumps(dict(cantidad=len(registros), esperados=len(catalogo),
                                          catalogo=args.catalogo,
                                          reproductor_sha256=hashlib.sha256((RAIZ/"cinematica_narrativa.py").read_bytes()).hexdigest(),
                                          clips=registros), ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"Verificados {len(registros)} reproductores reales sin plano ajeno de carga/reanudación.")


if __name__ == "__main__":
    main()
