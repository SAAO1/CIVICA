"""Colores semánticos; cada estado conserva también una letra o un símbolo."""

MODOS_DALTONISMO = {
    "normal": "Visión habitual",
    "deuteranopia": "Deuteranopia · verde",
    "protanopia": "Protanopia · rojo",
    "tritanopia": "Tritanopia · azul",
}

_BASE = {"fondo": "#142b3c", "texto": "#fff3dc", "neutro": "#9cabb7", "acento": "#f0cd96"}
_PALETAS = {
    "normal": {"falsa": "#f0a391", "verdadera": "#77cfb2", "correccion": "#89c9ff", "exploracion": "#dfb9ff"},
    "deuteranopia": {"falsa": "#efaa45", "verdadera": "#80c7ff", "correccion": "#e3bcfa", "exploracion": "#fff0aa"},
    "protanopia": {"falsa": "#ffd16b", "verdadera": "#75c5ff", "correccion": "#d4b3ff", "exploracion": "#fff2d0"},
    "tritanopia": {"falsa": "#ff9caa", "verdadera": "#7cdec8", "correccion": "#ffe1a0", "exploracion": "#efe8df"},
}


def paleta(modo="normal"):
    return dict(_BASE, **_PALETAS.get(modo, _PALETAS["normal"]))
