"""Actualiza únicamente el doblaje de las decisiones por oficio y los contadores.

Uso: python herramientas/producir_voces_roles.py --solo-faltantes --concurrencia 3
No se ejecuta desde el juego y no requiere conexión durante una partida.
"""
import sys
from producir_voces import main


if __name__ == "__main__":
    if "--solo-roles" not in sys.argv:
        sys.argv.append("--solo-roles")
    raise SystemExit(main())
