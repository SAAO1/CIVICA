from dataclasses import asdict, dataclass


@dataclass
class EstadoCiudad:
    info_verificada: int = 0
    confianza: int = 50
    desinformacion: int = 0
    convivencia: int = 50
    bienestar_digital: int = 50
    conflictos: int = 0
    participacion: int = 0

    def aplicar(self, cambios):
        for nombre, delta in cambios.items():
            if nombre not in self.__dataclass_fields__ or not isinstance(delta, (int, float)):
                raise ValueError("Cambio de indicador inválido")
        for nombre, delta in cambios.items():
            setattr(self, nombre, max(0, min(100, getattr(self, nombre) + delta)))

    def datos(self):
        return asdict(self)
