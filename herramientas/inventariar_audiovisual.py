"""Actualiza el inventario de arte y movimiento instalado en el proyecto."""
import hashlib
import json
from pathlib import Path

from PyQt6.QtGui import QImage

RAIZ = Path(__file__).resolve().parents[1]


def inventariar():
    archivos = []
    for grupo in ("fondos", "expresiones", "movimiento", "cinematica", "finales", "acciones_video"):
        for ruta in sorted((RAIZ / "assets/expansion" / grupo).rglob("*")):
            if (not ruta.is_file() or ruta.name.startswith(".")
                    or ruta.suffix.lower() not in (".png", ".jpg", ".gif", ".mp4")):
                continue
            h = hashlib.sha256()
            with ruta.open("rb") as archivo:
                for bloque in iter(lambda: archivo.read(1024*1024), b""):
                    h.update(bloque)
            entrada = {"archivo": ruta.relative_to(RAIZ).as_posix(), "bytes": ruta.stat().st_size,
                       "sha256": h.hexdigest()}
            if ruta.suffix.lower() in (".png", ".jpg"):
                imagen = QImage(str(ruta))
                entrada.update(ancho=imagen.width(), alto=imagen.height(), alfa=imagen.hasAlphaChannel())
            archivos.append(entrada)
    voces = json.loads((RAIZ / "assets/audio/voces/manifest.json").read_text(encoding="utf-8"))
    videos = [a for a in archivos if a["archivo"].endswith(".mp4")]
    resultado = {"fecha": "2026-10-24", "herramienta_imagenes": "image_gen incorporada",
                 "herramienta_animaciones": "FondoVivo, objetos QPainter y cámara; GIF y FFmpeg MP4",
                 "hojas": 4, "fotogramas_actores": 48, "fondos_nuevos": 3,
                 "gif": sum(a["archivo"].endswith(".gif") for a in archivos),
                 "mp4": len(videos),
                 "mp4_ambientes": sum("/movimiento/" in a["archivo"] for a in videos),
                 "mp4_narrativos": sum("/cinematica/" in a["archivo"] for a in videos),
                 "mp4_finales": sum("/finales/" in a["archivo"] for a in videos),
                 "mp4_acciones": sum("/acciones_video/" in a["archivo"] for a in videos),
                 "portadas_inicio_video": sum(a["archivo"].endswith("_inicio.png") for a in archivos),
                 "ilustraciones_narrativas": sum("/cinematica/ilustraciones/" in a["archivo"] for a in archivos),
                 "ilustraciones_acciones": sum("/acciones_video/ilustraciones/" in a["archivo"] for a in archivos),
                 "efectos_narrativos": 14, "balance_central_animado": True,
                 "balance_obligatorio_sin_cuadricula": True,
                 "cubierta_video_primer_fotograma": True,
                 "botones_accion_una_linea": True,
                 "acciones_por_rol": 4, "clips_neuronales": len(voces["clips"]),
                 "manifiesto_cinematicas": "assets/expansion/cinematica/manifest.json",
                 "manifiesto_acciones": "assets/expansion/acciones_video/manifest.json",
                 "prompts_cinematicas": "assets/expansion/cinematica/prompts.json",
                 "audio_creditos": ["assets/audio/expansion/licencias.json",
                                    "assets/audio/expansion/licencias_musica.json",
                                    "assets/audio/voces/LEEME.md"], "archivos": archivos}
    destino = RAIZ / "assets/expansion/audiovisual_manifest.json"
    temporal = destino.with_suffix(".tmp")
    temporal.write_text(json.dumps(resultado, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    temporal.replace(destino)
    print({k: v for k, v in resultado.items() if k not in ("archivos", "audio_creditos")})


if __name__ == "__main__":
    inventariar()
