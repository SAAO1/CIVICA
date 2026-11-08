"""Registro técnico de variantes ImageGen; conserva el cuerpo neutral original.

Las expresiones son ilustraciones generadas, no dibujos fabricados por código.
El registro copia sólo los rasgos necesarios para que el cuerpo no salte.
"""
from pathlib import Path
import json
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QImage, QPainter

RAIZ=Path(__file__).resolve().parents[1]
CARPETA=RAIZ/'assets/expansion/siete_actos/personajes'
TRABAJO=RAIZ/'.tmp/animaciones_npc'


def preparar():
    TRABAJO.mkdir(parents=True,exist_ok=True)
    datos=json.loads((CARPETA/'prompts_animacion.json').read_text(encoding='utf-8'))
    contacto=QImage(1200,1500,QImage.Format.Format_ARGB32);contacto.fill(QColor('#303e48'));c=QPainter(contacto)
    for fila,asset in enumerate(datos['assets']):
        neutral=QImage(str(CARPETA/f"{asset['id']}_neutral.png"))
        c.drawImage(0,fila*300,neutral.copy(180,40,400,300))
        fuente=RAIZ/asset['atlas'] if 'atlas' in asset else Path(asset['fuente'])
        hoja=QImage(str(fuente));print(asset['id'],hoja.width(),hoja.height(),hoja.hasAlphaChannel())
        for columna,estado in enumerate(asset['estados']):
            im=hoja.copy(columna*(hoja.width()//2),0,hoja.width()//2,hoja.height()).convertToFormat(QImage.Format.Format_RGBA8888)
            memoria=im.constBits().asstring(im.sizeInBytes());xs=[];ys=[]
            for y in range(im.height()):
                for x in range(im.width()):
                    if memoria[y*im.bytesPerLine()+4*x+3]>16:xs.append(x);ys.append(y)
            x0,x1=min(xs),max(xs);y0,y1=min(ys),max(ys)
            cuerpo=im.copy(x0,y0,x1-x0+1,y1-y0+1).scaled(700,1460,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
            destino=QImage(768,1536,QImage.Format.Format_ARGB32_Premultiplied);destino.fill(Qt.GlobalColor.transparent)
            q=QPainter(destino);q.drawImage((768-cuerpo.width())//2,(1536-cuerpo.height())//2,cuerpo);q.end()
            destino.save(str(TRABAJO/f"{asset['id']}_{estado}_registro.png"),'PNG',9)
            c.drawImage((columna+1)*400,fila*300,destino.copy(180,40,400,300))
    c.end();contacto.save(str(TRABAJO/'contacto_rostros.png'),'PNG',9)


RASGOS={
    'juan':{'hablando':(398,210,88,47),'parpadeo':(378,143,132,65)},
    'adrian':{'hablando':(356,199,90,50),'parpadeo':(326,138,142,62)},
    'laura':{'hablando':(328,206,86,52),'parpadeo':(295,148,121,65)},
    'camila':{'hablando':(343,205,90,48),'parpadeo':(325,142,139,65)},
    'influencer':{'hablando':(317,228,88,45),'parpadeo':(292,169,137,58)},
}


def _matriz(imagen):
    im=imagen.convertToFormat(QImage.Format.Format_RGBA8888)
    return im.constBits().asstring(im.sizeInBytes())


def registrar(neutral,frame,rectangulos):
    """Alineación por color de pelo/nariz/cuello; excluye rasgos cambiantes."""
    a,b=_matriz(neutral),_matriz(frame);puntos=[];paso=768*4
    for yy in range(55,330,12):
        for xx in range(200,565,12):
            indice=yy*paso+xx*4
            excluido=any(x-8<=xx<=x+w+8 and y-8<=yy<=y+h+8 for x,y,w,h in rectangulos)
            if a[indice+3]>240 and not excluido:puntos.append((xx,yy,a[indice],a[indice+1],a[indice+2]))
    mejor=(float('inf'),1,0,0)
    for escala in (.96,.98,1.0,1.02,1.04):
        for dx in range(-18,19,3):
            for dy in range(-18,19,3):
                error=0
                for xx,yy,r,g,azul in puntos:
                    indice=round((yy-dy)/escala)*paso+round((xx-dx)/escala)*4
                    dr,dg,db=r-b[indice],g-b[indice+1],azul-b[indice+2]
                    error+=dr*dr+dg*dg+db*db
                error=error/(3*len(puntos))
                if error<mejor[0]:mejor=(error,escala,dx,dy)
    _,escala,dx,dy=mejor
    alineado=QImage(768,1536,QImage.Format.Format_ARGB32_Premultiplied);alineado.fill(Qt.GlobalColor.transparent)
    p=QPainter(alineado);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    p.drawImage(QRectF(dx,dy,768*escala,1536*escala),frame);p.end()
    return alineado,{'error':mejor[0],'escala':escala,'dx':dx,'dy':dy}


def ensamblar():
    registros=[];contacto=QImage(1200,1500,QImage.Format.Format_ARGB32);contacto.fill(QColor('#303e48'));c=QPainter(contacto)
    for fila,(id,rasgos) in enumerate(RASGOS.items()):
        neutral=QImage(str(CARPETA/f'{id}_neutral.png')).convertToFormat(QImage.Format.Format_RGBA8888)
        c.drawImage(0,fila*300,neutral.copy(180,40,400,300))
        for columna,(estado,rect) in enumerate(rasgos.items()):
            frame=QImage(str(TRABAJO/f'{id}_{estado}_registro.png'))
            alineado,registro=registrar(neutral,frame,rasgos.values())
            x,y,w,h=rect;recorte=alineado.copy(x,y,w,h).convertToFormat(QImage.Format.Format_RGBA8888)
            matriz=bytearray(_matriz(recorte))
            for py in range(h):
                for px in range(w):
                    factor=max(0,min(1,px/8,(w-1-px)/8,py/8,(h-1-py)/8))
                    indice=(py*w+px)*4+3;matriz[indice]=round(matriz[indice]*factor)
            parche=QImage(bytes(matriz),w,h,w*4,QImage.Format.Format_RGBA8888).copy()
            destino=neutral.copy();p=QPainter(destino);p.drawImage(x,y,parche);p.end()
            # La fuente ImageGen puede conservar alpha253 en piel. El injerto
            # facial no debe aumentar esa cobertura al superponer otra capa.
            original=_matriz(neutral);mezcla=bytearray(_matriz(destino));mezcla[3::4]=original[3::4]
            destino=QImage(bytes(mezcla),768,1536,768*4,QImage.Format.Format_RGBA8888).copy()
            salida=CARPETA/f'{id}_{estado}.png';assert destino.save(str(salida),'PNG',9)
            original,final=_matriz(neutral),_matriz(destino);paso=768*4;fuera_igual=True;cambios=0
            for py in range(1536):
                ini=py*paso
                if y<=py<y+h:
                    fuera_igual &= original[ini:ini+x*4]==final[ini:ini+x*4] and original[ini+(x+w)*4:ini+paso]==final[ini+(x+w)*4:ini+paso]
                    for px in range(x,x+w):
                        i=ini+px*4;cambios+=original[i:i+4]!=final[i:i+4]
                else:fuera_igual &= original[ini:ini+paso]==final[ini:ini+paso]
            registro.update(id=id,estado=estado,archivo=salida.relative_to(RAIZ).as_posix(),rasgo=list(rect),pixeles_modificados=cambios,pixeles_modificados_fuera_rasgo=0 if fuera_igual else -1,alpha_identico=original[3::4]==final[3::4])
            assert registro['pixeles_modificados_fuera_rasgo']==0 and registro['alpha_identico']
            registros.append(registro);print(id,estado,registro,flush=True)
            c.drawImage((columna+1)*400,fila*300,destino.copy(180,40,400,300))
    c.end();contacto.save(str(TRABAJO/'contacto_final.png'),'PNG',9)
    (CARPETA/'manifest_animacion.json').write_text(json.dumps({'version':1,'tecnica':'Rasgos reales ImageGen registrados y extraídos sobre cuerpo neutral intacto. Ningún píxel cambia fuera del rectángulo facial, alpha idéntico al original.','frames':registros},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    import sys
    ensamblar() if '--ensamblar' in sys.argv else preparar()
