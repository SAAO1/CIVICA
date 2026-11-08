"""Produce siete planos contextuales nativos sin voz sobre las CG de pulido.

Exportación autorizada: python -X utf8 -B herramientas/producir_pulido_visual.py
Solo escribe assets/novela/pulido/videos y su manifiesto de video independiente.
Las CG, los recursos originales y sus manifiestos permanecen intactos.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QColor, QFont, QFontDatabase, QFontMetricsF, QImage, QLinearGradient,
    QPainter, QPainterPath, QPen, QPolygonF, QRawFont, QTransform,
)
from PyQt6.QtWidgets import QApplication
from herramientas.exportar_ambientes import localizar_ffmpeg

SALIDA = RAIZ / "assets/novela/pulido"
ANCHO, ALTO, FPS, SEGUNDOS = 1280, 720, 24, 6
MARINO, ORO, CREMA = "#13213c", "#c7a15b", "#f5e8ca"
FAMILIA = "Atkinson Hyperlegible"
ORDEN_FORO = ("JUAN", "ADRIÁN", "LAURA", "CAMILA")
PLANES = (
    ("caso_50", "aviso_cafe", "Una notificación interrumpe la mañana", "Falta la fuente original."),
    ("caso_90", "parque_contexto", "El parque fuera de cuadro", "Mira qué quedó fuera del encuadre."),
    ("caso_110", "audio_contexto", "Los segundos que faltan", "Escucha el comienzo y el cierre."),
    ("caso_40", "correccion_contexto", "Un canal que recuerda", "Conserva el original, las fuentes y los cambios."),
    ("caso_120", "urnas_contexto", "Una entrada para el abuelo", "Sigue el recorrido hasta el acceso."),
    ("caso_35", "voto_contexto", "La palabra que borraron", "Comentar no sustituye el voto."),
    ("foro", "foro_cuatro", "Cuatro candidaturas, una ciudad", "Escucha las propuestas y compara sus fuentes."),
)


def huella(ruta):
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def relativa(ruta):
    return Path(ruta).resolve().relative_to(RAIZ.resolve()).as_posix()


def inventario(ruta, **campos):
    ruta = Path(ruta)
    return dict(archivo=relativa(ruta), sha256=huella(ruta), bytes=ruta.stat().st_size, **campos)


def destino(nombre):
    ruta = (SALIDA / "videos" / nombre).resolve()
    if not ruta.is_relative_to((SALIDA/"videos").resolve()):
        raise ValueError("La exportación debe permanecer en pulido/videos")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    return ruta


def cargar_fuentes():
    """Usa exclusivamente la familia portátil registrada desde los TTF del juego."""
    archivos = [RAIZ/"assets/fuentes"/("AtkinsonHyperlegible-"+variante+".ttf")
                for variante in ("Regular", "Bold")]
    for archivo in archivos:
        if not archivo.is_file():
            raise FileNotFoundError("Falta la fuente empaquetada: "+str(archivo))
        id = QFontDatabase.addApplicationFont(str(archivo))
        if id < 0 or FAMILIA not in QFontDatabase.applicationFontFamilies(id):
            raise ValueError("No se puede registrar la fuente canónica: "+archivo.name)
    muestra = " ".join(x for plan in PLANES for x in plan[2:])+" ".join(ORDEN_FORO)+"¿Dónde está el documento?"
    raw = QRawFont.fromFont(fuente(22))
    faltantes = sorted({c for c in muestra if c.isprintable() and not raw.supportsCharacter(ord(c))})
    if faltantes:
        raise ValueError("La fuente carece de estos caracteres: "+repr(faltantes))
    return [inventario(x) for x in archivos]


def fuente(tamano, negrita=False):
    f=QFont(FAMILIA)
    f.setPixelSize(tamano)
    f.setBold(negrita)
    return f


def texto(p, contenido, caja, tamano=26, negrita=False, color=CREMA, minimo=16, centrado=False):
    caja=QRectF(*caja) if isinstance(caja,(tuple,list)) else QRectF(caja)
    flags=Qt.AlignmentFlag.AlignVCenter|Qt.TextFlag.TextWordWrap
    flags |= Qt.AlignmentFlag.AlignHCenter if centrado else Qt.AlignmentFlag.AlignLeft
    for px in range(tamano,minimo-1,-1):
        f=fuente(px,negrita)
        medida=QFontMetricsF(f).boundingRect(caja,int(flags),contenido)
        if medida.height()<=caja.height()+0.5 and medida.width()<=caja.width()+1:
            p.setFont(f)
            p.setPen(QColor(color))
            p.drawText(caja,int(flags),contenido)
            return px
    raise ValueError("El texto no cabe legible: "+contenido)


def panel(p,caja,alpha=226):
    p.setPen(QPen(QColor(ORO),1.5))
    p.setBrush(QColor(19,33,60,alpha))
    p.drawRoundedRect(QRectF(*caja),14,14)


def suavizar(t):
    t=max(0.,min(1.,t))
    return t*t*(3-2*t)


def fondo(p,imagen,segundo,indice):
    # Una ida de cámara continua; cada plano da prioridad a un punto distinto.
    t=segundo/SEGUNDOS
    centro=((.64,.51),(.58,.53),(.55,.52),(.53,.54),(.62,.53),(.63,.55),(.50,.44))[indice]
    progreso=suavizar(t)
    zoom=1.025+.035*progreso
    base=min(imagen.width()/ANCHO,imagen.height()/ALTO)/zoom
    ancho,alto=ANCHO*base,ALTO*base
    margen_x,margen_y=(imagen.width()-ancho)/2,(imagen.height()-alto)/2
    cx=imagen.width()/2+margen_x*(centro[0]-.5)*2*progreso
    cy=imagen.height()/2+margen_y*(centro[1]-.5)*2*progreso
    caja=QRectF(cx-ancho/2,cy-alto/2,ancho,alto)
    p.drawImage(QRectF(0,0,ANCHO,ALTO),imagen,caja)
    return QTransform(ANCHO/ancho,0,0,ALTO/alto,-caja.x()*ANCHO/ancho,-caja.y()*ALTO/alto)


def telefono(p,imagen,camara,segundo):
    """Texto vectorial nativo sobre la pantalla vacía; sigue la cámara de la CG."""
    # Cuadrilátero normalizado de la pantalla de aviso_cafe, no del borde del móvil.
    destino_telefono=QPolygonF([QPointF(x*imagen.width(),y*imagen.height())
                               for x,y in ((.812,.343),(.931,.324),(.897,.769),(.789,.758))])
    original=QPolygonF([QPointF(0,0),QPointF(240,0),QPointF(240,450),QPointF(0,450)])
    transformacion=QTransform()
    if not QTransform.quadToQuad(original,destino_telefono,transformacion):
        raise ValueError("No se puede proyectar la pantalla del aviso")
    p.save()
    p.setTransform(transformacion*camara)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#07142d"))
    p.drawRoundedRect(QRectF(0,0,240,450),18,18)
    pulso=(1+math.sin(segundo*math.tau))/2
    p.setPen(QPen(QColor(199,161,91,int(130+80*pulso)),3))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(8,10,224,430),14,14)
    texto(p,"CIVITAS",(20,28,200,32),22,True,color=ORO)
    texto(p,"MENSAJE REENVIADO",(20,79,200,45),18,True)
    p.setPen(QPen(QColor(ORO),1))
    p.drawLine(QPointF(20,137),QPointF(220,137))
    texto(p,"Juan quiere cerrar el colegio",(20,155,200,112),28,True,minimo=24)
    texto(p,"¿Dónde está el documento?",(20,304,200,89),25,True,color=ORO,minimo=22)
    p.restore()


def vapor(p,segundo):
    for i in range(3):
        x=714+i*17
        camino=QPainterPath(QPointF(x,439))
        desplazamiento=math.sin(segundo*1.4+i)*9
        camino.cubicTo(x-19+desplazamiento,414,x+20+desplazamiento,394,x+desplazamiento,368)
        p.setPen(QPen(QColor(255,239,211,30+int(14*math.sin(segundo+i))),2))
        p.drawPath(camino)


def onda(p,segundo):
    panel(p,(135,492,1010,110))
    p.setPen(QPen(QColor(ORO),3))
    camino=QPainterPath(QPointF(160,547))
    for x in range(0,961,4):
        amplitud=9+22*(.5+.5*math.sin(x*.013))
        y=547+amplitud*math.sin(x*.075-segundo*5)*math.sin(x*.009+1)
        camino.lineTo(160+x,y)
    p.drawPath(camino)
    cursor=160+(segundo/SEGUNDOS)*960
    p.setPen(QPen(QColor(CREMA),2))
    p.drawLine(QPointF(cursor,510),QPointF(cursor,582))
    for etiqueta,x in (("COMIENZO",178),("RECORTE",573),("CIERRE",975)):
        texto(p,etiqueta,(x,499,130,24),16,True,minimo=16)


def versiones(p,segundo):
    progreso=suavizar(segundo/SEGUNDOS)
    for i,(titulo,x) in enumerate((("ORIGINAL",62),("FUENTES",315),("CAMBIOS",568))):
        alpha=int(85+160*min(1,max(0,progreso*3-i*.62)))
        panel(p,(x,488,230,83),alpha)
        texto(p,titulo,(x+15,505,200,47),25,True,centrado=True)


def recorrido(p,segundo,caso,imagen,camara):
    # Se ancla al acceso visible de la CG final, dentro del monitor en el
    # parque y a lo largo de la rampa en las urnas; acompaña la misma cámara.
    normalizados=(
        ((.77,.58),(.83,.55),(.90,.47),(.95,.38))
        if caso=="caso_120" else
        ((.82,.42),(.842,.39),(.862,.36),(.88,.33))
    )
    puntos=[QPointF(x*imagen.width(),y*imagen.height()) for x,y in normalizados]
    longitud=(len(puntos)-1)*suavizar(segundo/SEGUNDOS)
    p.save()
    p.setTransform(camara)
    p.setPen(QPen(QColor(199,161,91,210),5,Qt.PenStyle.DashLine))
    for i in range(len(puntos)-1):
        fraccion=max(0,min(1,longitud-i))
        if fraccion:
            fin=puntos[i]+(puntos[i+1]-puntos[i])*fraccion
            p.drawLine(puntos[i],fin)
    p.setBrush(QColor(ORO))
    p.setPen(QPen(QColor(MARINO),2))
    indice=min(len(puntos)-2,int(longitud))
    t=min(1,longitud-indice)
    pos=puntos[indice]+(puntos[indice+1]-puntos[indice])*t
    p.drawEllipse(pos,10,10)
    p.restore()


def enfoque_foro(p,segundo):
    activo=min(3,int(segundo/(SEGUNDOS/4)))
    for indice,nombre in enumerate(ORDEN_FORO):
        x=90+indice*292
        panel(p,(x,504,240,55),242 if indice==activo else 180)
        texto(p,nombre,(x+10,510,220,40),27,True,color=ORO if indice==activo else CREMA,centrado=True)
        if indice==activo:
            luz=QLinearGradient(x,70,x+240,500)
            luz.setColorAt(0,QColor(236,207,146,23))
            luz.setColorAt(1,QColor(236,207,146,0))
            p.fillRect(QRectF(x,70,240,420),luz)


def fotograma(imagen,segundo,indice):
    clave,cg,titulo,consigna=PLANES[indice]
    salida=QImage(ANCHO,ALTO,QImage.Format.Format_ARGB32)
    salida.fill(QColor(MARINO))
    p=QPainter(salida)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    camara=fondo(p,imagen,segundo,indice)
    if clave=="caso_50":
        telefono(p,imagen,camara,segundo)
        vapor(p,segundo)
    elif clave in ("caso_90","caso_120"):
        recorrido(p,segundo,clave,imagen,camara)
    elif clave=="caso_110":
        onda(p,segundo)
    elif clave=="caso_40":
        versiones(p,segundo)
    elif clave=="caso_35":
        panel(p,(800,482,400,95))
        texto(p,"COMENTAR NO ES VOTAR",(820,496,360,65),29,True,minimo=24)
        p.setPen(QPen(QColor(199,161,91,int(100+70*math.sin(segundo*2)**2)),3))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(790,474,420,111),18,18)
    else:
        enfoque_foro(p,segundo)
    panel(p,(35,613,1210,84),235)
    texto(p,titulo,(57,620,1166,34),25,True,minimo=23)
    texto(p,consigna,(57,658,1166,31),21,False,minimo=20)
    p.end()
    return salida


def ejecutar(comando):
    return subprocess.run(comando,capture_output=True,check=True)


def cuadro_decodificado(ffmpeg,ruta,segundo):
    datos=ejecutar([ffmpeg,"-v","error","-ss",str(segundo),"-i",str(ruta),
                    "-frames:v","1","-pix_fmt","rgb24","-f","rawvideo","-"]).stdout
    if len(datos)!=ANCHO*ALTO*3:
        raise ValueError("Fotograma incompleto en "+ruta.name)
    return datos


def exportar(ffmpeg,imagen,indice):
    clave,cg,titulo,consigna=PLANES[indice]
    ruta=destino(clave+".mp4")
    temporal=destino(clave+".temporal.mp4")
    proceso=subprocess.Popen(
        [ffmpeg,"-hide_banner","-loglevel","error","-y","-f","rawvideo","-pixel_format",
         "bgra","-video_size",f"{ANCHO}x{ALTO}","-framerate",str(FPS),"-i","pipe:0","-an",
         "-c:v","libx264","-preset","fast","-crf","23","-threads","2",
         "-pix_fmt","yuv420p","-movflags","+faststart",str(temporal)],
        stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    try:
        for i in range(FPS*SEGUNDOS):
            frame=fotograma(imagen,i/FPS,indice)
            proceso.stdin.write(frame.constBits().asstring(frame.sizeInBytes()))
        proceso.stdin.close()
        errores=proceso.stderr.read()
        if proceso.wait(timeout=120):
            raise RuntimeError(errores.decode(errors="replace"))
    except BaseException:
        if proceso.poll() is None:
            proceso.terminate()
            proceso.wait(timeout=10)
        raise
    finally:
        proceso.stderr.close()
    temporal.replace(ruta)
    lectura=ejecutar([ffmpeg,"-hide_banner","-loglevel","error","-i",str(ruta),
                     "-progress","pipe:1","-nostats","-f","null","-"]).stdout.decode()
    conteos=[int(linea.split("=",1)[1]) for linea in lectura.splitlines() if linea.startswith("frame=")]
    if not conteos or conteos[-1]!=FPS*SEGUNDOS:
        raise ValueError("El video no se decodificó por completo: "+clave)
    muestras=[cuadro_decodificado(ffmpeg,ruta,t) for t in (0,3,5)]
    if len({hashlib.sha256(d).hexdigest() for d in muestras})!=3:
        raise ValueError("El plano no tiene movimiento real: "+clave)
    png=destino(clave+"_inicio.png")
    poster=destino(clave+"_poster.jpg")
    for nombre,datos,formato,calidad in ((png,muestras[0],"PNG",-1),(poster,muestras[1],"JPG",90)):
        image=QImage(datos,ANCHO,ALTO,ANCHO*3,QImage.Format.Format_RGB888).copy()
        if not image.save(str(nombre),formato,calidad):
            raise RuntimeError("No se pudo guardar "+str(nombre))
    print(clave+": 144 cuadros decodificados y 3 muestras diferentes",flush=True)
    return inventario(ruta,clave=clave,cg=cg,ancho=ANCHO,alto=ALTO,fps=FPS,
                      duracion=float(SEGUNDOS),fotogramas=conteos[-1],audio=False,
                      decodificacion_completa=True,
                      primer_fotograma=inventario(png),poster=inventario(poster),
                      textos=[titulo,consigna]+(list(ORDEN_FORO) if clave=="foro" else []),
                      movimiento={"segundos":[0,3,5],
                                  "rgb_sha256":[hashlib.sha256(d).hexdigest() for d in muestras]})


def producir(origen=None):
    app=QApplication.instance() or QApplication([])
    fuentes=cargar_fuentes()
    origen=origen or SALIDA/"origen_arte.json"
    if not origen.is_file():
        raise FileNotFoundError("Falta la procedencia real del arte: "+str(origen))
    procedencia=json.loads(origen.read_text(encoding="utf-8"))
    cg=[]
    imagenes=[]
    for clave,nombre,_,_ in PLANES:
        ruta=SALIDA/"cg"/(nombre+".png")
        imagen=QImage(str(ruta))
        if imagen.isNull():
            raise FileNotFoundError("Falta una CG final decodificable: "+str(ruta))
        imagenes.append(imagen)
        cg.append(inventario(ruta,id=nombre,ancho=imagen.width(),alto=imagen.height()))
    ffmpeg=localizar_ffmpeg()
    videos=[exportar(ffmpeg,imagen,i) for i,imagen in enumerate(imagenes)]
    for entrada in cg:
        if huella(RAIZ/entrada["archivo"])!=entrada["sha256"]:
            raise ValueError("Una CG cambió durante la producción; vuelve a exportar con fuentes estables")
    manifest={
        "version":1,"generado_utc":datetime.now(timezone.utc).isoformat(),
        "productor":inventario(Path(__file__)),
        "metodo":"Composición nativa QPainter sobre siete CG de ImageGen: cámara, notificación, vapor, recorrido indicativo, onda, versiones y focos. H.264 por FFmpeg; no es video generativo.",
        "audio":"Ningún clip incorpora voz ni pista sonora. El doblaje neural se reproduce por separado.",
        "tipografia":{"familia":FAMILIA,"archivos":fuentes,"glifos_verificados":True},
        "origen_arte":procedencia,"archivo_procedencia":inventario(origen),
        "orden_visual_foro":list(ORDEN_FORO),
        "cg":cg,"videos":videos,
    }
    destino("manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Manifiesto independiente: assets/novela/pulido/videos/manifest.json",flush=True)
    return manifest


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origen-arte",type=Path)
    opciones=parser.parse_args()
    producir(opciones.origen_arte)
