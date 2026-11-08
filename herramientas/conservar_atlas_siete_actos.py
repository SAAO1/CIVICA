"""Conserva las diez hojas originales para poder repetir su extracción."""
import hashlib
import json
from pathlib import Path
import shutil

RAIZ=Path(__file__).resolve().parents[1]
CARPETA=RAIZ/'assets/expansion/siete_actos/personajes'
ATLAS=RAIZ/'assets/expansion/siete_actos/atlas'


def main():
    ATLAS.mkdir(parents=True,exist_ok=True);registros=[]
    for archivo,tipo,lista in [('prompts.json','expresiones','personajes'),('prompts_animacion.json','animacion','assets')]:
        ruta=CARPETA/archivo;datos=json.loads(ruta.read_text(encoding='utf-8'))
        for asset in datos[lista]:
            origen=Path(asset['fuente']);destino=ATLAS/f"{asset['id']}_{tipo}.png"
            if not destino.exists():shutil.copyfile(origen,destino)
            assert hashlib.sha256(origen.read_bytes()).digest()==hashlib.sha256(destino.read_bytes()).digest()
            asset['atlas']=destino.relative_to(RAIZ).as_posix()
            registros.append({'archivo':asset['atlas'],'sha256':hashlib.sha256(destino.read_bytes()).hexdigest(),'tipo':tipo,'alpha_original':True})
        ruta.write_text(json.dumps(datos,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ATLAS/'manifest.json').write_text(json.dumps({'version':1,'origen':'ImageGen integrado. Copia binaria íntegra de las hojas originales; no se descartó ni alteró el alpha.','hojas':registros},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(len(registros),'hojas originales conservadas')


if __name__=='__main__':main()
