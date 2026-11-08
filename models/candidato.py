from dataclasses import dataclass


@dataclass
class Candidato:
    id: str
    nombre: str
    propuesta: str
    apoyo: int = 25


def candidatos_iniciales():
    return [Candidato("juan", "Juan Torres", "Educación y espacios seguros"),
            Candidato("adrian", "Adrián Morales", "Bibliotecas y cultura"),
            Candidato("laura", "Laura Ríos", "Parques y convivencia"),
            Candidato("camila", "Camila Vega", "Participación y bienestar digital")]
