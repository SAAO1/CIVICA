"""Actualiza sólo los cuatro montajes que muestran el teléfono de Civitas."""
import os
from pathlib import Path
import subprocess
import sys

RAIZ = Path(__file__).resolve().parents[1]


def main():
    for clave in ("mensaje_barrio", "rumor_colegio", "cafe_alerta", "person_acusacion_c"):
        subprocess.run([sys.executable, "-B", str(RAIZ / "herramientas/producir_cinematicas.py"),
                        "--clave", clave], cwd=RAIZ, check=True)
    return 0


if __name__ == "__main__":
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    raise SystemExit(main())
