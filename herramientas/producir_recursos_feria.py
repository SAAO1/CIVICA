"""Produce documentos, clips y voz local para la campaña de investigación.

python -B herramientas/producir_recursos_feria.py
Las pinturas se conservan intactas. QPainter compone documentos y movimiento;
FFmpeg codifica y verifica cada película. La voz es síntesis de Windows.
"""
from __future__ import annotations

import argparse
import array
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import wave

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QFontMetricsF, QImage, QLinearGradient, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QApplication
from interfaz.componentes.arte import cargar_tipografias
from juego.casos_feria import IDS_FERIA, crear_caso
from herramientas.exportar_ambientes import localizar_ffmpeg

SALIDA = RAIZ / "assets/feria"
APERTURAS = {
    50: "En el grupo del barrio circula una captura sobre el colegio. Busca el documento que falta antes de publicar.",
    90: "Un video del parque parece mostrar una ciudad cerrada. Recupera lo que quedó fuera del encuadre.",
    110: "Reconocer una voz no basta para comprenderla. Busca los segundos que desaparecieron de este audio.",
    40: "Una corrección necesita algo más que otro titular. Investiga cómo se conservarán las fuentes y los cambios.",
    120: "El abuelo quiere llegar por una entrada accesible y decidir por sí mismo. Encuentra el mapa de esta jornada.",
    35: "Una sola palabra puede cambiar un mensaje completo. Recupera el original antes de anunciar lo que dice.",
}
CABECERAS = {
    50: ("Acta de reunión educativa", "Secretaría educativa · Archivo municipal"),
    90: ("Mantenimiento por sectores", "Servicios urbanos · Registro de accesos"),
    110: ("Archivo de la intervención", "Foro de Ciudad Nova · Transcripción"),
    40: ("Canal público de correcciones", "Equipo de Camila Vega · Propuesta"),
    120: ("Accesos de la jornada", "Organización electoral · Mapa oficial"),
    35: ("Publicación íntegra del perfil", "Adrián Morales · Archivo de Civitas"),
}


def sha256(ruta):
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def relativa(ruta):
    return Path(ruta).relative_to(RAIZ).as_posix()


def fuente(tamano, negrita=False):
    f = QFont("Atkinson Hyperlegible")
    f.setPixelSize(tamano)
    f.setBold(negrita)
    return f


def texto(p, cadena, caja, tamano=32, color="#193746", negrita=False, minimo=24):
    caja = QRectF(*caja) if isinstance(caja, (tuple, list)) else QRectF(caja)
    minimo = min(tamano, minimo)
    flags = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap
    while tamano >= minimo:
        f = fuente(tamano, negrita)
        alto = QFontMetricsF(f).boundingRect(caja, int(flags), cadena).height()
        if alto <= caja.height():
            p.setFont(f)
            p.setPen(QColor(color))
            p.drawText(caja, int(flags), cadena)
            return tamano
        tamano -= 1
    raise ValueError("El texto no cabe completo en el documento: " + cadena[:50])


def documento(identificador, original):
    caso = crear_caso(identificador)
    imagen = QImage(1400, 900, QImage.Format.Format_ARGB32)
    imagen.fill(QColor("#e9e3d5"))
    p = QPainter(imagen)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#fffdf5"))
    p.drawRoundedRect(QRectF(38, 30, 1324, 840), 18, 18)
    p.setBrush(QColor("#123c4c" if original else "#263c4f"))
    p.drawRoundedRect(QRectF(38, 30, 1324, 126), 18, 18)
    texto(p, "CIUDAD NOVA  /  " + ("ARCHIVO" if original else "CIVITAS"),
          (76, 46, 1080, 57), 37, "#f7e4b8", True)
    texto(p, f"CASO {identificador} · " + ("VERSIÓN COMPLETA" if original else "MENSAJE RECIBIDO"),
          (76, 103, 1200, 36), 25, "#bed5d6")
    cabecera, origen = CABECERAS[identificador]
    titulo = cabecera if original else caso["titulo"]
    texto(p, titulo, (80, 176, 1210, 95), 48, "#173f50", True, 34)
    texto(p, origen if original else "Reenviado en un grupo del barrio",
          (82, 273, 1170, 45), 27, "#647477")
    p.setPen(QPen(QColor("#cbb98e"), 2))
    p.drawLine(80, 329, 1320, 329)
    cuerpo = caso["medio"]["texto_completo"] if original else caso["medio"]["texto_inicial"]
    cuerpo_tamano = texto(p, cuerpo, (85, 350, 1225, 198), 38, minimo=30)
    # Un diagrama distinto por instrumento conserva el contenido de cada caso.
    if identificador == 110:
        p.setPen(QPen(QColor("#b08342" if original else "#527f8c"), 3))
        for x in range(110, 1285, 5):
            u = (x - 110) / 1175
            envolvente = (.25 + .75*abs(math.sin(u*math.pi*5))) * (1 if original or .38 < u < .62 else .09)
            alto = 38 * envolvente * abs(math.sin(x * .21))
            p.drawLine(QPointF(x, 640-alto), QPointF(x, 640+alto))
        texto(p, "Intervención completa" if original else "Fragmento reenviado",
              (95, 698, 1200, 45), 28, "#52717a")
    elif identificador in (90, 120):
        p.setPen(Qt.PenStyle.NoPen)
        for x, y in ((135, 590), (470, 600), (1030, 585)):
            p.setBrush(QColor("#dbe6d0"))
            p.drawRoundedRect(QRectF(x, y, 200, 95), 15, 15)
        recorrido = QPainterPath(QPointF(135, 718))
        recorrido.lineTo(440, 718)
        recorrido.lineTo(790, 627)
        recorrido.lineTo(1230, 627)
        p.setPen(QPen(QColor("#17826f" if original else "#71899a"), 11))
        p.drawPath(recorrido)
        texto(p, ("Acceso lateral accesible" if identificador == 120 else "Entrada lateral abierta")
              if original else "El encuadre no conserva todos los accesos",
              (100, 735, 1200, 50), 30, "#225b59", True)
    elif identificador == 40:
        for i, palabra in enumerate(("MENSAJE", "FUENTES", "CAMBIOS") if original else ("ANUNCIO", "¿FUENTES?", "¿CAMBIOS?")):
            x = 108 + i*422
            p.setPen(QPen(QColor("#b7c9c1"), 2))
            p.setBrush(QColor("#e4eee6"))
            p.drawRoundedRect(QRectF(x, 595, 350, 125), 16, 16)
            texto(p, palabra, (x+28, 621, 300, 65), 32, "#245b58", True)
            if i < 2:
                p.setPen(QPen(QColor("#b18b4b"), 5))
                p.drawLine(QPointF(x+360, 657), QPointF(x+407, 657))
    else:
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#e6eee6" if original else "#edf0f2"))
        p.drawRoundedRect(QRectF(85, 584, 1228, 153), 16, 16)
        frase = ("MANTENER LAS CLASES" if identificador == 50 else "Comentar NO sustituye el voto") if original else "La versión recibida deja una pregunta abierta"
        texto(p, frase, (120, 605, 1160, 110), 41, "#285b51", True)
    texto(p, "07 NOV 2026  ·  Ciudad Nova  ·  Documento del mundo ficticio de CIVICA",
          (83, 809, 1240, 36), 24, "#74847f")
    p.end()
    return imagen, cuerpo_tamano


class Plano:
    def __init__(self, identificador=None):
        self.id = identificador
        self.caso = crear_caso(identificador) if identificador else None
        fondo = ("portada.png" if identificador in (None, 50) else
                 "mesa_investigacion.png" if identificador in (40, 110) else "mapa_ciudad.png")
        self.fondo_path = SALIDA / fondo
        self.fondo = QImage(str(self.fondo_path))
        self.prueba = QImage(str(SALIDA / f"pruebas/{identificador}_recorte.png")) if identificador else None
        if self.fondo.isNull():
            raise FileNotFoundError(self.fondo_path)

    def capturar_fotograma(self, t, tamano=(1280, 720)):
        w, h = tamano
        imagen = QImage(w, h, QImage.Format.Format_ARGB32)
        imagen.fill(QColor("#0b1e2c"))
        p = QPainter(imagen)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        fase = t / 6 * math.tau
        zoom = 1.018 + .009*math.sin(fase)
        dw, dh = w*zoom, h*zoom
        x = (w-dw)/2 + w*.003*math.cos(fase)
        y = (h-dh)/2 + h*.002*math.sin(fase)
        p.drawImage(QRectF(x, y, dw, dh), self.fondo)
        if self.id is not None:
            degradado = QLinearGradient(0, 0, w, 0)
            degradado.setColorAt(0, QColor(5, 23, 35, 234))
            degradado.setColorAt(.60, QColor(7, 24, 35, 170))
            degradado.setColorAt(1, QColor(7, 24, 35, 40))
            p.fillRect(imagen.rect(), degradado)
            p.save()
            p.scale(w/1280, h/720)
            texto(p, f"CAPÍTULO {self.caso['capitulo']}  ·  EXPEDIENTE {self.id}",
                  (64, 75, 590, 45), 22, "#e9c58a", True)
            texto(p, self.caso["titulo"], (62, 145, 570, 170), 52, "#f6ead4", True, 36)
            texto(p, self.caso["objetivo"], (66, 343, 525, 145), 27, "#c0d5d5")
            texto(p, "Dos acciones. Una publicación. Sus consecuencias.",
                  (66, 555, 530, 70), 25, "#e6c48c")
            p.setBrush(QColor(0, 0, 0, 92))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(QRectF(680, 150, 550, 365), 14, 14)
            p.drawImage(QRectF(670, 135+5*math.sin(fase), 550, 354), self.prueba)
            p.restore()
        # Lluvia dibujada; las personas y las pinturas permanecen intactas.
        if self.id in (None, 50, 90):
            p.setPen(QPen(QColor(184, 221, 232, 24), max(1, w/1280)))
            for i in range(44):
                rx = ((i*.6180339887) % 1) * w
                ry = ((i*.371 + t*.21) % 1) * h
                p.drawLine(QPointF(rx, ry), QPointF(rx-2*w/1280, ry+9*h/720))
        p.end()
        return imagen


def metadatos(ruta, **extras):
    return dict(archivo=relativa(ruta), bytes=ruta.stat().st_size, sha256=sha256(ruta), **extras)


def pelicula(plano, destino, ffmpeg):
    inicio = time.monotonic()
    temporal = destino.with_name(destino.stem + ".produccion.mp4")
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
           "-f", "rawvideo", "-pixel_format", "bgra", "-video_size", "1280x720", "-framerate", "24",
           "-i", "pipe:0", "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "25",
           "-threads", "2", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(temporal)]
    proceso = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        for n in range(144):
            imagen = plano.capturar_fotograma(n/24)
            proceso.stdin.write(imagen.constBits().asstring(imagen.sizeInBytes()))
        proceso.stdin.close()
        error = proceso.stderr.read().decode("utf-8", "replace")
        if proceso.wait():
            raise RuntimeError(error)
    except BaseException:
        proceso.kill()
        proceso.wait()
        temporal.unlink(missing_ok=True)
        raise
    finally:
        if not proceso.stdin.closed:
            proceso.stdin.close()
        proceso.stderr.close()
    subprocess.run([ffmpeg, "-v", "error", "-i", str(temporal), "-f", "null", "-"],
                   capture_output=True, check=True)
    temporal.replace(destino)
    primer = destino.with_name(destino.stem + "_inicio.png")
    subprocess.run([ffmpeg, "-v", "error", "-y", "-i", str(destino), "-frames:v", "1",
                    "-update", "1", str(primer)], capture_output=True, check=True)
    poster = destino.with_suffix(".jpg")
    if not plano.capturar_fotograma(3).save(str(poster), "JPG", 89):
        raise RuntimeError("No se guardó la miniatura")
    print(f"{destino.name}: 144 fotogramas verificados en {time.monotonic()-inicio:.1f}s", flush=True)
    return metadatos(destino, caso_id=plano.id, duracion=6.0, ancho=1280, alto=720, fps=24,
                     fotogramas=144, codec="h264", audio_incrustado=False,
                     decodificacion_completa=True, primer_fotograma=metadatos(primer),
                     poster=metadatos(poster), fuente=metadatos(plano.fondo_path),
                     contenido="Apertura sin prueba completa: solo el recorte recibido y el objetivo del caso.")


def _ps_literal(cadena):
    return "'" + str(cadena).replace("'", "''") + "'"


def voces():
    temporal = RAIZ / ".tmp/feria_audio"
    temporal.mkdir(parents=True, exist_ok=True)
    segmentos = ("Si alguien pretende", "cobrar por votar", "denuncia ese engaño.")
    trabajos = [(temporal / f"segmento_{i}.wav", t) for i, t in enumerate(segmentos)]
    trabajos += [(SALIDA / f"audio/caso_{id}_apertura.wav", texto) for id, texto in APERTURAS.items()]
    script = [
        "Add-Type -AssemblyName System.Speech",
        "$synth = [System.Speech.Synthesis.SpeechSynthesizer]::new()",
        "$synth.SelectVoice('Microsoft Sabina Desktop')",
        "$synth.Rate = 0", "$synth.Volume = 85",
        "$formato = [System.Speech.AudioFormat.SpeechAudioFormatInfo]::new(24000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)",
        "try {",
    ]
    for ruta, texto_voz in trabajos:
        script += ["$synth.SetOutputToWaveFile(" + _ps_literal(ruta) + ", $formato)",
                   "$synth.Speak(" + _ps_literal(texto_voz) + ")"]
    script += ["} finally { $synth.Dispose() }"]
    script = "\n".join(script)
    (temporal / "generar.ps1").write_text(script, encoding="utf-8-sig")
    subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
                   capture_output=True, text=True, check=True)
    partes = []
    parametros = None
    for i in range(3):
        with wave.open(str(temporal / f"segmento_{i}.wav"), "rb") as entrada:
            actual = (entrada.getnchannels(), entrada.getsampwidth(), entrada.getframerate())
            if parametros is not None and actual != parametros:
                raise ValueError("Los segmentos no tienen el mismo formato PCM")
            parametros = actual
            partes.append(entrada.readframes(entrada.getnframes()))
    canales, ancho, frecuencia = parametros
    pausa = b"\0" * round(frecuencia*.10) * ancho * canales
    completa = pausa + partes[0] + pausa + partes[1] + pausa + partes[2] + pausa
    inicio_central = (len(pausa)*2 + len(partes[0])) // (ancho*canales)
    rutas = {}
    for nombre, datos in (("recortado", partes[1]), ("completo", completa)):
        ruta = SALIDA / f"audio/caso_110_{nombre}.wav"
        with wave.open(str(ruta), "wb") as salida:
            salida.setnchannels(canales)
            salida.setsampwidth(ancho)
            salida.setframerate(frecuencia)
            salida.writeframes(datos)
        rutas[nombre] = ruta
    registros = []
    for ruta in [rutas["recortado"], rutas["completo"]] + [SALIDA/f"audio/caso_{id}_apertura.wav" for id in IDS_FERIA]:
        with wave.open(str(ruta), "rb") as entrada:
            datos = entrada.readframes(entrada.getnframes())
            muestras = array.array("h", datos)
            pico = max(map(abs, muestras), default=0) / 32768
            if not muestras or pico <= .01 or pico >= 1:
                raise ValueError("Audio vacío o saturado: " + str(ruta))
            registros.append(metadatos(ruta, canales=entrada.getnchannels(), bits=entrada.getsampwidth()*8,
                                       frecuencia=entrada.getframerate(),
                                       fotogramas=entrada.getnframes(),
                                       duracion=round(entrada.getnframes()/entrada.getframerate(), 6),
                                       pico=round(pico, 6), voz="Microsoft Sabina Desktop", idioma="es-MX",
                                       origen="Síntesis local System.Speech; no es una grabación de una persona real."))
    return {"archivos": registros, "segmentos_originales": list(segmentos),
            "transcripcion_recortada": segmentos[1],
            "transcripcion_completa": "Si alguien pretende cobrar por votar, denuncia ese engaño.",
            "segmento_central_inicio_frame": inicio_central,
            "segmento_central_frames": len(partes[1]) // (ancho*canales),
            "recortado_es_segmento_exactamente_conservado": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sin-voz", action="store_true", help="Solo para regenerar imagen/video; conserva el inventario de voz previo.")
    args = parser.parse_args()
    app = QApplication.instance() or QApplication([])
    cargar_tipografias()
    ffmpeg = localizar_ffmpeg()
    for nombre in ("pruebas", "videos", "audio"):
        (SALIDA/nombre).mkdir(parents=True, exist_ok=True)
    pruebas = []
    for id in IDS_FERIA:
        for original in (False, True):
            imagen, tamano = documento(id, original)
            ruta = SALIDA / f"pruebas/{id}_{'original' if original else 'recorte'}.png"
            if not imagen.save(str(ruta), "PNG"):
                raise RuntimeError("No se pudo guardar " + str(ruta))
            imagen.save(str(ruta.with_suffix(".jpg")), "JPG", 88)
            pruebas.append(metadatos(ruta, caso_id=id, variante="original" if original else "recorte",
                                     ancho=1400, alto=900, tamano_texto_cuerpo_px=tamano,
                                     tecnica="Gráfico documental nativo de QPainter; texto del catálogo ficticio."))
    videos = [pelicula(Plano(id), SALIDA / f"videos/caso_{id}.mp4", ffmpeg) for id in IDS_FERIA]
    portada = pelicula(Plano(), SALIDA / "videos/portada_loop.mp4", ffmpeg)
    gif = SALIDA / "portada_animada.gif"
    filtro = "[0:v]fps=12,scale=800:450:flags=lanczos,split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle"
    subprocess.run([ffmpeg, "-v", "error", "-y", "-i", str(SALIDA/"videos/portada_loop.mp4"),
                    "-filter_complex", filtro, "-loop", "0", str(gif)], capture_output=True, check=True)
    subprocess.run([ffmpeg, "-v", "error", "-i", str(gif), "-f", "null", "-"], capture_output=True, check=True)
    manifest_previo = SALIDA/"manifest.json"
    if args.sin_voz:
        if not manifest_previo.is_file():
            raise ValueError("--sin-voz requiere un manifiesto previo con voces")
        audio = json.loads(manifest_previo.read_text(encoding="utf-8"))["audio"]
    else:
        audio = voces()
    origen = SALIDA/"origen_arte.json"
    documento_final = {
        "version": 1, "fecha": "2026-11-07", "zona_horaria": "America/Bogota",
        "productor": metadatos(Path(__file__)),
        "tecnica": "Ilustraciones ImageGen existentes; cámara, lluvia y documentos nativos QPainter; H.264 FFmpeg. No son videos generativos.",
        "ilustraciones": [metadatos(SALIDA/n) for n in ("portada.png", "mapa_ciudad.png", "mesa_investigacion.png")],
        "origen_arte": json.loads(origen.read_text(encoding="utf-8-sig")) if origen.is_file() else {"nota": "Prompts no incluidos en este productor."},
        "fuente_tipografica": {"familia": "Atkinson Hyperlegible", "licencia": "SIL OFL 1.1", "archivo": "assets/fuentes/OFL.txt"},
        "catalogo": metadatos(RAIZ/"juego/casos_feria.py"),
        "pruebas": pruebas, "videos": videos, "portada_video": portada,
        "portada_gif": metadatos(gif, ancho=800, alto=450, fps=12, duracion=6.0,
                                fotogramas=72, paleta_maxima=128, bucle=True, decodificacion_completa=True),
        "audio": audio,
    }
    temporal = SALIDA/"manifest.produccion.json"
    temporal.write_text(json.dumps(documento_final, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    temporal.replace(manifest_previo)
    print(json.dumps({"pruebas": len(pruebas), "videos": len(videos), "audios": len(audio["archivos"]),
                      "gif_bytes": gif.stat().st_size, "resultado": "Recursos producidos y decodificados"}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
