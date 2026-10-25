"""Produce ocho MP4 H.264 de diez segundos y sus primeros fotogramas exactos."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

RAIZ=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(RAIZ));os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from PyQt6.QtWidgets import QApplication
from cinematica_extension_visual import CARPETA,FPS,DURACION,RenderizadorExtension
from juego.cinematica_extension import CINEMATICAS_EXTENSION
from herramientas.exportar_ambientes import localizar_ffmpeg
from herramientas.producir_cinematicas import guardar_portada_inicio


def producir(clave,ffmpeg):
    render=RenderizadorExtension(clave);inicio=time.monotonic()
    video=CARPETA/f"{clave}.mp4";temporal=CARPETA/f".{clave}.produccion.mp4"
    proceso=subprocess.Popen([ffmpeg,"-hide_banner","-loglevel","error","-y","-f","rawvideo","-pixel_format","bgra","-video_size","1280x720","-framerate",str(FPS),"-i","pipe:0","-an","-c:v","libx264","-preset","fast","-crf","24","-threads","2","-pix_fmt","yuv420p","-movflags","+faststart",str(temporal)],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    try:
        for i in range(round(FPS*DURACION)):
            img=render.capturar_fotograma(i/FPS);proceso.stdin.write(img.constBits().asstring(img.sizeInBytes()))
        proceso.stdin.close();error=proceso.stderr.read().decode("utf-8","replace")
        if proceso.wait():raise RuntimeError(error)
        verificacion=subprocess.run([ffmpeg,"-v","error","-i",str(temporal),"-f","null","-"],capture_output=True,text=True)
        if verificacion.returncode:raise RuntimeError(verificacion.stderr)
        temporal.replace(video)
    except BaseException:
        proceso.kill();proceso.wait();temporal.unlink(missing_ok=True);raise
    finally:
        if not proceso.stdin.closed:proceso.stdin.close()
        proceso.stderr.close()
    poster=CARPETA/f"{clave}.jpg";render.capturar_fotograma(6.7).save(str(poster),"JPG",91)
    primero=guardar_portada_inicio(video,CARPETA/f"{clave}_inicio.png",ffmpeg)
    registro={"clave":clave,"publicacion":render.identificador,"texto":CINEMATICAS_EXTENSION[clave]["texto"],"video":video.name,"poster":poster.name,"inicio":primero.name,"duracion":DURACION,"fps":FPS,"fotogramas":round(FPS*DURACION),"ancho":1280,"alto":720,"bytes":video.stat().st_size,"sha256":hashlib.sha256(video.read_bytes()).hexdigest(),"inicio_sha256":hashlib.sha256(primero.read_bytes()).hexdigest(),"decodificacion_completa":True,"fuentes":[r.relative_to(RAIZ).as_posix() for r in render.fuentes]}
    print(f"{clave}:240frames {registro['bytes']}bytes {time.monotonic()-inicio:.1f}s",flush=True)
    return registro


def main():
    app=QApplication.instance() or QApplication([]);CARPETA.mkdir(parents=True,exist_ok=True);ffmpeg=localizar_ffmpeg();clips=[]
    for clave in CINEMATICAS_EXTENSION:
        clips.append(producir(clave,ffmpeg))
        (CARPETA/"manifest.json").write_text(json.dumps({"version":1,"tecnica":"Cuatro pinturas ImageGen originales, cámara y objetos dibujados en capas QPainter, MP4 H.264 sin pista de voz. La voz exacta la reproduce el juego. No es animación corporal generada.","coherencia":"Cada publicación nueva tiene un corte propio enlazado a su primera frase de narrador; no proclama ganadores ni certifica rumores.","clips":clips},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return 0


if __name__=="__main__":raise SystemExit(main())
