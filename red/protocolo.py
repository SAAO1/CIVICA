import json

MAX_MENSAJE = 65536


def codificar(mensaje):
    datos = json.dumps(mensaje, ensure_ascii=False, allow_nan=False).encode("utf-8")
    if len(datos) > MAX_MENSAJE:
        raise ValueError("Mensaje demasiado grande")
    return datos + b"\n"


def decodificar(datos):
    if len(datos) > MAX_MENSAJE:
        raise ValueError("Mensaje demasiado grande")
    try:
        mensaje = json.loads(datos)
    except (ValueError, UnicodeDecodeError) as error:
        raise ValueError("JSON inválido") from error
    if not isinstance(mensaje, dict) or not isinstance(mensaje.get("tipo"), str):
        raise ValueError("El mensaje necesita un tipo")
    return mensaje


def recibir(archivo):
    linea = archivo.readline(MAX_MENSAJE + 2)
    if not linea:
        return None
    if not linea.endswith(b"\n") or len(linea) > MAX_MENSAJE + 1:
        raise ValueError("Trama incompleta o demasiado grande")
    return decodificar(linea[:-1])
