"""Selecciona el refuerzo local de volumen sin modificar el doblaje original."""
from functools import lru_cache
import hashlib,json
from pathlib import Path
from audio.catalogo_voces import CARPETA_VOCES
CARPETA_REFUERZO=CARPETA_VOCES/"refuerzo"

@lru_cache(maxsize=2)
def _manifest(ruta,modificado,tamano):
    try:
        datos=json.loads(Path(ruta).read_text(encoding="utf-8"))
        if not isinstance(datos,dict):
            return {}
        clips=datos.get("clips",{})
        return clips if datos.get("version")==1 and isinstance(clips,dict) else {}
    except (OSError,ValueError,TypeError):
        return {}

def ruta_reproduccion(entrada,original,carpeta=CARPETA_REFUERZO):
    """Sólo usa un refuerzo íntegro que corresponda al archivo original actual."""
    if original is None:
        return None
    nombre=entrada.get("archivo","") if isinstance(entrada,dict) else ""
    if not nombre or Path(nombre).name!=nombre or "/" in nombre or "\\" in nombre:
        return original
    base=Path(carpeta).resolve()
    try:
        manifest=base/"manifest.json"
        estado=manifest.stat()
        datos=_manifest(str(manifest),estado.st_mtime_ns,estado.st_size)
        registro=datos.get(nombre)
        if not isinstance(registro,dict):
            return original
        destino=(base/nombre).resolve()
        if not destino.is_relative_to(base) or not destino.is_file():
            return original
        if destino.stat().st_size!=registro.get("bytes"):
            return original
        if hashlib.sha256(Path(original).read_bytes()).hexdigest()!=registro.get("sha_original"):
            return original
        if hashlib.sha256(destino.read_bytes()).hexdigest()!=registro.get("sha256"):
            return original
        return destino
    except (OSError,ValueError,TypeError):
        return original
