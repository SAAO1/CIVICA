"""Prepara voces de mayor nivel conservando los MP3 originales."""
from __future__ import annotations
import array
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib,json,math,os
from pathlib import Path
import statistics,subprocess,sys,time
RAIZ=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(RAIZ))
from audio.catalogo_voces import CARPETA_VOCES,cargar_manifest,ruta_clip
from herramientas.exportar_ambientes import localizar_ffmpeg
SALIDA=CARPETA_VOCES/"refuerzo"
FILTRO="acompressor=threshold=0.22:ratio=2:attack=5:release=100:makeup=3,alimiter=limit=0.84:level=false:latency=true"
def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def medir(p,ffmpeg):
    r=subprocess.run([ffmpeg,"-v","error","-i",str(p),"-ac","1","-ar","24000","-f","f32le","-"],capture_output=True,check=True,timeout=45)
    a=array.array("f",r.stdout)
    return dict(rms=math.sqrt(sum(x*x for x in a)/len(a)),pico=max(abs(x) for x in a),duracion_ms=len(a)/24)
def producir(entrada,ffmpeg):
    origen=ruta_clip(entrada)
    if origen is None:
        raise FileNotFoundError(entrada["archivo"])
    destino=SALIDA/origen.name
    temporal=SALIDA/(origen.stem+".tmp.mp3")
    antes=medir(origen,ffmpeg)
    subprocess.run([ffmpeg,"-v","error","-y","-i",str(origen),"-map","0:a:0","-map_metadata","-1","-af",FILTRO,
        "-ac","1","-ar","24000","-c:a","libmp3lame","-b:a","96k","-threads","1",str(temporal)],
        capture_output=True,check=True,timeout=45)
    nivel=medir(temporal,ffmpeg)
    ganancia=20*math.log10(nivel["rms"]/antes["rms"])
    if nivel["pico"]>=.98 or abs(nivel["duracion_ms"]-antes["duracion_ms"])>60 or ganancia<.5:
        raise ValueError((origen.name,nivel,ganancia))
    temporal.replace(destino)
    return dict(archivo=origen.name,hablante=entrada["hablante"],sha_original=sha(origen),sha256=sha(destino),
        bytes=destino.stat().st_size,rms=round(nivel["rms"],7),pico_real=round(nivel["pico"],7),
        duracion_ms=round(nivel["duracion_ms"]),ganancia_db=round(ganancia,3))
def main():
    inicio=time.monotonic()
    ffmpeg=localizar_ffmpeg()
    entradas=list(cargar_manifest()["clips"].values())
    muestra="--muestra" in sys.argv
    if muestra:
        from herramientas.normalizar_voces_locales import muestras_representativas
        catalogo=cargar_manifest()
        entradas=[catalogo["clips"][c] for c in muestras_representativas(catalogo)]
    SALIDA.mkdir(parents=True,exist_ok=True)
    registros=[]
    with ThreadPoolExecutor(max_workers=8) as pool:
        futuros=[pool.submit(producir,e,ffmpeg) for e in entradas]
        for futuro in as_completed(futuros):
            registros.append(futuro.result())
            if len(registros)%100==0:
                print(str(len(registros))+"/"+str(len(entradas)),flush=True)
    reporte={"version":1,"filtro":FILTRO,"originales_conservados":True,"muestra":muestra,
        "clips":{r["archivo"]:r for r in registros},
        "cantidad":len(registros),"mediana_ganancia_db":statistics.median(r["ganancia_db"] for r in registros),
        "pico_maximo":max(r["pico_real"] for r in registros),"segundos":round(time.monotonic()-inicio,3)}
    archivo=SALIDA/("muestra.json" if muestra else "manifest.json")
    archivo.write_text(json.dumps(reporte,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in reporte.items() if k!="clips"},ensure_ascii=False),flush=True)
if __name__=="__main__":
    main()
