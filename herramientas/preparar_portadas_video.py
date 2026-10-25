"""Portadas de carga tomadas del primer fotograma real, sin adelantar planos.

python -B herramientas/preparar_portadas_video.py
python -B herramientas/preparar_portadas_video.py --verificar

Los carteles JPG siguen siendo las imágenes de movimiento reducido. Estos
PNG son exclusivamente la cubierta de carga de cada MP4 y no alteran su arte.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtGui import QImage
from herramientas.exportar_ambientes import localizar_ffmpeg
from herramientas.producir_cinematicas import guardar_portada_inicio


def comprobar(video, portada, ffmpeg):
    imagen = QImage(str(portada)).convertToFormat(QImage.Format.Format_RGB888)
    if imagen.isNull():
        raise RuntimeError(f"Portada ausente o ilegible: {portada}")
    decodificar = subprocess.run(
        [ffmpeg, "-v", "error", "-i", str(video), "-frames:v", "1",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"], capture_output=True)
    if decodificar.returncode:
        raise RuntimeError(decodificar.stderr.decode("utf-8", "replace"))
    ancho, alto = imagen.width(), imagen.height()
    datos = imagen.constBits().asstring(imagen.sizeInBytes())
    if imagen.bytesPerLine() != ancho*3:
        datos = b"".join(datos[y*imagen.bytesPerLine():y*imagen.bytesPerLine()+ancho*3]
                          for y in range(alto))
    iguales = datos == decodificar.stdout
    if not iguales:
        raise RuntimeError(f"La cubierta de {video.name} no coincide con su primer frame decodificado")
    return dict(video=video.relative_to(RAIZ).as_posix(),
                inicio=portada.relative_to(RAIZ).as_posix(),
                ancho=ancho, alto=alto, bytes=portada.stat().st_size,
                inicio_sha256=hashlib.sha256(portada.read_bytes()).hexdigest(),
                diferencia_maxima_rgb=0, pixeles_distintos=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verificar", action="store_true", help="Comprueba sin reescribir portadas")
    parser.add_argument("--carpeta", type=Path, action="append")
    parser.add_argument("--cantidad-esperada", type=int, help="Falla si falta cualquier video del lote esperado")
    args = parser.parse_args()
    carpetas = args.carpeta or [RAIZ / "assets/expansion" / nombre
                                for nombre in ("cinematica", "finales", "acciones_video")]
    ffmpeg = localizar_ffmpeg()
    registros = []
    for carpeta in carpetas:
        if not carpeta.is_absolute():
            carpeta = RAIZ / carpeta
        if not carpeta.is_dir():
            continue
        manifest = carpeta / "manifest.json"
        documento = json.loads(manifest.read_text(encoding="utf-8")) if manifest.is_file() else None
        for video in sorted(carpeta.glob("*.mp4")):
            if video.name.startswith("."):
                continue
            portada = video.with_name(f"{video.stem}_inicio.png")
            if not args.verificar:
                guardar_portada_inicio(video, portada, ffmpeg)
            registro = comprobar(video, portada, ffmpeg)
            registros.append(registro)
            if documento is not None and not args.verificar:
                for clip in documento.get("clips", []):
                    if clip.get("video") == video.name:
                        clip["inicio"] = portada.name
                        clip["inicio_sha256"] = registro["inicio_sha256"]
            print(f"{video.stem}: cubierta = frame 0 exacto ({registro['bytes']} bytes)", flush=True)
        if documento is not None and not args.verificar:
            manifest.write_text(json.dumps(documento, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    salida = RAIZ / ".tmp/inicios_video_verificados.json"
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(dict(cantidad=len(registros), clips=registros), ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    if args.cantidad_esperada is not None and len(registros) != args.cantidad_esperada:
        raise RuntimeError(f"Se esperaban {args.cantidad_esperada} videos y sólo hay {len(registros)} completos")
    print(f"Verificados {len(registros)} primeros fotogramas.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
