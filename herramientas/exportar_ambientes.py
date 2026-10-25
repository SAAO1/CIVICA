"""Exporta GIFs animados reales del motor Qt sin Pillow ni FFmpeg.

Ejemplo: python herramientas/exportar_ambientes.py --todos
         python herramientas/exportar_ambientes.py --escena cafe --ancho 960
         python herramientas/exportar_ambientes.py --escena plaza_noche --formato mp4 --ancho 1280 --fps 24

Los GIF son vistas portátiles. El juego renderiza estas mismas capas en tiempo
real a resolución de pantalla y no necesita decodificar archivos pesados.
La codificación GIF usa paleta de Qt, tramado y LZW estándar; ningún paquete
extra, descarga o servicio de generación es necesario.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtWidgets import QApplication
from ambiente_visual import FondoVivo

ESCENAS = {
    "ciudad": "ciudad", "portada": "portada_ciudad",
    "cafe_exterior": "cafe_exterior", "cafe": "cafe_interior",
    "telefono": "telefono", "investigacion": "investigacion",
    "observatorio": "observatorio", "lluvia": "ciudad",
    "cafe_lluvia": "assets/expansion/fondos/cafe_lluvia.png",
    "plaza_noche": "assets/expansion/fondos/plaza_noche.png",
    "parque_tarde": "assets/expansion/fondos/parque_tarde.png",
}


def _lzw(datos):
    """LZW GIF de 9 bits, con reinicios antes de ampliar el diccionario.

    Acotar el diccionario a 511 entradas simplifica el escritor y evita
    diferencias entre decodificadores al cambiar el ancho de código. Todavía
    comprime repeticiones; todas las entradas y reinicios son GIF89a estándar.
    """
    salida = bytearray()
    acumulador = bits = 0

    def emitir(codigo):
        nonlocal acumulador, bits
        acumulador |= codigo << bits
        bits += 9
        while bits >= 8:
            salida.append(acumulador & 255)
            acumulador >>= 8
            bits -= 8

    tabla = {bytes((i,)): i for i in range(256)}
    proximo = 258
    emitir(256)
    prefijo = b""
    for valor in datos:
        simbolo = bytes((valor,))
        combinado = prefijo + simbolo
        if combinado in tabla:
            prefijo = combinado
            continue
        emitir(tabla[prefijo])
        tabla[combinado] = proximo
        proximo += 1
        prefijo = simbolo
        if proximo >= 511:
            emitir(256)
            tabla = {bytes((i,)): i for i in range(256)}
            proximo = 258
    if prefijo:
        emitir(tabla[prefijo])
    emitir(257)
    if bits:
        salida.append(acumulador & 255)
    return salida


def _fotograma_gif(archivo, imagen, retraso):
    imagen = imagen.convertToFormat(QImage.Format.Format_RGB32).convertToFormat(
        QImage.Format.Format_Indexed8, Qt.ImageConversionFlag.DiffuseDither)
    ancho, alto = imagen.width(), imagen.height()
    paleta = imagen.colorTable()
    paleta.extend([0] * (256-len(paleta)))
    # Disposal 1 deja el cuadro completo mientras llega el próximo, sin flashes.
    archivo.write(b"\x21\xf9\x04\x04" + struct.pack("<H", retraso) + b"\x00\x00")
    archivo.write(b"\x2c" + struct.pack("<HHHH", 0, 0, ancho, alto) + b"\x87")
    archivo.write(bytes(canal for color in paleta[:256]
                        for canal in ((color >> 16) & 255, (color >> 8) & 255, color & 255)))
    datos = imagen.constBits().asstring(imagen.sizeInBytes())
    if imagen.bytesPerLine() != ancho:
        datos = b"".join(datos[y*imagen.bytesPerLine():y*imagen.bytesPerLine()+ancho]
                          for y in range(alto))
    comprimido = _lzw(datos)
    archivo.write(b"\x08")
    for posicion in range(0, len(comprimido), 255):
        bloque = comprimido[posicion:posicion+255]
        archivo.write(bytes((len(bloque),)) + bloque)
    archivo.write(b"\x00")


def _fotograma_bucle(fondo, indice, cantidad, fps, tamano):
    """Solapa 0.8 s de los extremos para un bucle continuo, sin corte de cámara."""
    duracion = cantidad / fps
    transicion = min(.8, duracion/3)
    t = indice / fps
    imagen = fondo.capturar_fotograma(t+transicion, tamano)
    if t > duracion-transicion:
        solape = t-(duracion-transicion)
        progreso = solape/transicion
        opacidad = progreso*progreso*(3-2*progreso)
        inicio = fondo.capturar_fotograma(solape, tamano)
        pintor = QPainter(imagen)
        pintor.setOpacity(opacidad)
        pintor.drawImage(0, 0, inicio)
        pintor.end()
    return imagen


def exportar_gif(fondo, destino, ancho=640, alto=360, segundos=6, fps=10):
    """Escribe un GIF por streaming; devuelve su número de fotogramas."""
    cantidad = max(2, round(segundos*fps))
    retraso = max(2, round(100/fps))
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("wb") as archivo:
        archivo.write(b"GIF89a" + struct.pack("<HH", ancho, alto) + b"\x70\x00\x00")
        archivo.write(b"\x21\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00")
        for indice in range(cantidad):
            imagen = _fotograma_bucle(fondo, indice, cantidad, fps, (ancho, alto))
            _fotograma_gif(archivo, imagen, retraso)
        archivo.write(b"\x3b")
    return cantidad


def localizar_ffmpeg(indicado=None):
    if indicado:
        candidato = Path(indicado)
        if candidato.is_file():
            return str(candidato)
        raise FileNotFoundError(f"FFmpeg no está en {candidato}")
    sistema = shutil.which("ffmpeg")
    if sistema:
        return sistema
    # Herramienta de desarrollo opcional: el juego no la necesita instalada.
    for candidato in (RAIZ / ".tmp/deps/imageio_ffmpeg/binaries").glob("ffmpeg*.exe"):
        return str(candidato)
    raise FileNotFoundError("Para exportar MP4, indica --ffmpeg RUTA o instala FFmpeg")


def exportar_mp4(fondo, destino, ancho=1280, alto=720, segundos=8, fps=24, ffmpeg=None):
    """Codifica fotogramas BGRA con FFmpeg; no guarda miles de PNG intermedios."""
    if ancho % 2 or alto % 2:
        raise ValueError("MP4 necesita ancho y alto pares")
    cantidad = max(2, round(segundos*fps))
    destino.parent.mkdir(parents=True, exist_ok=True)
    comando = [localizar_ffmpeg(ffmpeg), "-hide_banner", "-loglevel", "error", "-y",
               "-f", "rawvideo", "-pixel_format", "bgra", "-video_size", f"{ancho}x{alto}",
               "-framerate", str(fps), "-i", "pipe:0", "-an", "-c:v", "libx264",
               "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
               "-movflags", "+faststart", str(destino)]
    proceso = subprocess.Popen(comando, stdin=subprocess.PIPE,
                               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        for indice in range(cantidad):
            imagen = _fotograma_bucle(fondo, indice, cantidad, fps, (ancho, alto))
            imagen = imagen.convertToFormat(QImage.Format.Format_ARGB32)
            proceso.stdin.write(imagen.constBits().asstring(imagen.sizeInBytes()))
        proceso.stdin.close()
        errores = proceso.stderr.read().decode("utf-8", errors="replace")
        resultado = proceso.wait()
        if resultado != 0 or not destino.is_file() or not destino.stat().st_size:
            raise RuntimeError(f"FFmpeg no pudo crear el vídeo: {errores}")
    except BaseException:
        proceso.kill()
        proceso.wait()
        raise
    finally:
        if not proceso.stdin.closed:
            proceso.stdin.close()
        proceso.stderr.close()
    return cantidad


def main():
    opciones = argparse.ArgumentParser(description=__doc__)
    opciones.add_argument("--escena", choices=ESCENAS, default="portada")
    opciones.add_argument("--todos", action="store_true")
    opciones.add_argument("--formato", choices=("gif", "mp4", "ambos"), default="gif")
    opciones.add_argument("--ffmpeg", type=Path)
    opciones.add_argument("--ancho", type=int, default=640)
    opciones.add_argument("--segundos", type=float, default=6)
    opciones.add_argument("--fps", type=int, default=10)
    opciones.add_argument("--destino", type=Path,
                          default=RAIZ / "assets/expansion/movimiento")
    args = opciones.parse_args()
    if not 160 <= args.ancho <= 1920 or not 1 <= args.segundos <= 60 or not 2 <= args.fps <= 30:
        opciones.error("Usa ancho 160–1920, segundos 1–60 y fps 2–30")
    app = QApplication.instance() or QApplication([])
    fondo = FondoVivo()
    elegidas = list(ESCENAS) if args.todos else [args.escena]
    registros = []
    alto = round(args.ancho*9/16)
    for escena in elegidas:
        ruta = ESCENAS[escena]
        if not ruta.startswith("assets/"):
            ruta = f"assets/rediseno/fondos/{ruta}.png"
        if not (RAIZ / ruta).is_file():
            raise FileNotFoundError(f"Falta la ilustración {ruta}")
        fondo.establecer_escena(ruta, escena)
        fondo.establecer_tiempo(0)
        formatos = ("gif", "mp4") if args.formato == "ambos" else (args.formato,)
        for formato in formatos:
            archivo = args.destino / f"{escena}.{formato}"
            inicio = time.perf_counter()
            if formato == "gif":
                cantidad = exportar_gif(fondo, archivo, args.ancho, alto, args.segundos, args.fps)
            else:
                cantidad = exportar_mp4(fondo, archivo, args.ancho, alto, args.segundos,
                                        args.fps, args.ffmpeg)
            duracion = time.perf_counter()-inicio
            registro = {"archivo": archivo.name, "fotogramas": cantidad,
                        "fps": args.fps, "duracion_s": cantidad/args.fps,
                        "ancho": args.ancho, "alto": alto, "bytes": archivo.stat().st_size,
                        "sha256": hashlib.sha256(archivo.read_bytes()).hexdigest()}
            registros.append(registro)
            print(f"{archivo.name}: {cantidad} cuadros, {archivo.stat().st_size/1024/1024:.1f} MB, "
                  f"{duracion:.1f} s de exportación", flush=True)
        fondo.capturar_fotograma(2, (1366, 768)).save(str(args.destino / f"{escena}.png"))
    manifiesto = args.destino / "manifiesto.json"
    if manifiesto.is_file():
        anteriores = json.loads(manifiesto.read_text(encoding="utf-8")).get("recursos", [])
        archivos_nuevos = {item["archivo"] for item in registros}
        registros = [item for item in anteriores if item["archivo"] not in archivos_nuevos] + registros
    manifiesto.write_text(json.dumps({
        "generador": "herramientas/exportar_ambientes.py", "motor": "ambiente_visual.FondoVivo",
        "origen": "Ilustraciones locales de assets/rediseno/fondos con capas animadas Qt",
        "recursos": registros}, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    fondo.close()


if __name__ == "__main__":
    main()
