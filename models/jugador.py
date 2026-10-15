from dataclasses import dataclass, field

ROLES = {
    "ciudadano": {"nombre": "Ciudadano", "saltos": 2, "intervalo": 1.0,
                  "habilidad": "Bonificación al verificar información."},
    "periodista": {"nombre": "Periodista", "saltos": 2, "intervalo": 0.8,
                   "habilidad": "Verificación: mayor recuperación de confianza."},
    "influencer": {"nombre": "Influencer", "saltos": 4, "intervalo": 0.5,
                   "habilidad": "Difusión: cuatro niveles en lugar de dos."},
    "candidato": {"nombre": "Candidato", "saltos": 2, "intervalo": 1.0,
                  "habilidad": "Propuestas: mayor apoyo al difundir información verdadera."},
}

# Los otros perfiles se conservan para datos y partidas anteriores.
ROLES_JUGABLES = ("ciudadano", "periodista")


@dataclass
class Jugador:
    id: str = "local"
    nombre: str = "Alex"
    rol: str = "ciudadano"
    ciudadano_id: str = "ana"
    puntos: int = 0
    reputacion: int = 50
    confianza: int = 50
    logros: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.rol not in ROLES:
            raise ValueError("Rol desconocido")
