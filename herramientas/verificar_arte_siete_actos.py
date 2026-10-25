"""Comprueba el arte de extensión sin leer o modificar partidas personales."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

RAIZ=Path(__file__).resolve().parents[1];sys.path.insert(0,str(RAIZ))
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PyQt6.QtGui import QColor,QImage,QPainter
from PyQt6.QtWidgets import QApplication
from cinematica_extension_visual import RenderizadorExtension
from juego.cinematica_extension import CINEMATICAS_EXTENSION
from herramientas.exportar_ambientes import localizar_ffmpeg


def main():
    app=QApplication.instance() or QApplication([]);ffmpeg=localizar_ffmpeg();registros=[]
    contacto=QImage(1152,1728,QImage.Format.Format_RGB32);contacto.fill(QColor('#102532'));p=QPainter(contacto)
    for fila,(clave,entrada) in enumerate(CINEMATICAS_EXTENSION.items()):
        render=RenderizadorExtension(clave);hashes=[]
        for t in [i*.5 for i in range(20)]:
            img=render.capturar_fotograma(t,(320,180));hashes.append(hashlib.sha256(img.constBits().asstring(img.sizeInBytes())).hexdigest())
        for col,t in enumerate((0,4,8)):p.drawImage(col*384,fila*216,render.capturar_fotograma(t,(384,216)))
        video=RAIZ/entrada['video'];inicio=QImage(str(RAIZ/entrada['inicio'])).convertToFormat(QImage.Format.Format_RGB888)
        real=subprocess.run([ffmpeg,'-v','error','-i',str(video),'-frames:v','1','-pix_fmt','rgb24','-f','rawvideo','pipe:1'],capture_output=True,check=True).stdout
        png=inicio.constBits().asstring(inicio.sizeInBytes())
        registro={'clave':clave,'movimiento_20_muestras':len(set(hashes))==20,'primer_frame_igual_rgb':real==png,'bytes':video.stat().st_size}
        assert registro['movimiento_20_muestras'] and registro['primer_frame_igual_rgb'];registros.append(registro)
    p.end();vistas=RAIZ/'docs/vistas';vistas.mkdir(parents=True,exist_ok=True);contacto.save(str(vistas/'contacto_cortes_siete_actos.jpg'),'JPG',92)
    archivos=list((RAIZ/'assets/expansion/siete_actos/personajes').glob('*.png'))
    assert len(archivos)==25
    for archivo in archivos:
        im=QImage(str(archivo));assert im.width()==768 and im.height()==1536 and im.hasAlphaChannel()
    resultado={'version':1,'sprites_png':len(archivos),'videos':registros,'fotogramas_muestreados':160,'contacto':'docs/vistas/contacto_cortes_siete_actos.jpg'}
    (RAIZ/'docs/verificacion_arte_siete_actos.json').write_text(json.dumps(resultado,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(resultado,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
