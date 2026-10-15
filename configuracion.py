import json
from recursos import RAIZ

RUTA = RAIZ / ".civica/config.json"


def cargar():
    if not RUTA.exists():
        return {}
    try:
        datos = json.loads(RUTA.read_text(encoding="utf-8"))
        return datos if isinstance(datos, dict) else {}
    except (OSError, ValueError):
        return {}


def guardar(datos):
    RUTA.parent.mkdir(parents=True, exist_ok=True)
    RUTA.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
