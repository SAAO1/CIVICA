"""Biblioteca personal: lectura y escenas vistas, independiente de la partida."""
import hashlib
import json
import os
from pathlib import Path

from recursos import RAIZ

ESCENAS_CONOCIDAS = ("50", "30", "70", "20", "60", "80", "90", "40",
                     "100", "10", "110", "25", "120", "35", "final")


class BibliotecaLectura:
    def __init__(self, ruta=RAIZ / ".civica/biblioteca.json"):
        self.ruta = Path(ruta) if ruta is not None else None
        self.leidos = set()
        self.escenas = set()
        self._cargar()

    @staticmethod
    def clave(nombre, texto):
        return hashlib.sha256(f"{nombre.strip().upper()}\n{texto}".encode("utf-8")).hexdigest()

    def _cargar(self):
        if self.ruta is None:
            return
        try:
            datos = json.loads(self.ruta.read_text(encoding="utf-8"))
            if not isinstance(datos, dict):
                return
            leidos = datos.get("leidos", [])
            escenas = datos.get("escenas", [])
            if isinstance(leidos, list):
                self.leidos.update(v for v in leidos if isinstance(v, str) and len(v) == 64
                                   and all(c in "0123456789abcdef" for c in v))
            if isinstance(escenas, list):
                self.escenas.update(v for v in escenas if v in ESCENAS_CONOCIDAS)
        except (OSError, ValueError):
            pass

    def guardar(self):
        if self.ruta is None:
            return
        # Las ventanas de una sala comparten biblioteca, pero nunca el estado oficial.
        self._cargar()
        temporal = self.ruta.with_suffix(f".{os.getpid()}.tmp")
        try:
            self.ruta.parent.mkdir(parents=True, exist_ok=True)
            temporal.write_text(json.dumps({"leidos": sorted(self.leidos),
                                           "escenas": sorted(self.escenas)}, indent=2), encoding="utf-8")
            temporal.replace(self.ruta)
        except OSError:
            # La lectura y la campaña funcionan también en una carpeta sin escritura.
            try:
                temporal.unlink(missing_ok=True)
            except OSError:
                pass

    def ya_leido(self, nombre, texto):
        return self.clave(nombre, texto) in self.leidos

    def marcar(self, nombre, texto):
        clave = self.clave(nombre, texto)
        if clave not in self.leidos:
            self.leidos.add(clave)
            self.guardar()

    def desbloquear(self, identificador):
        clave = str(identificador)
        if clave not in self.escenas:
            self.escenas.add(clave)
            self.guardar()
