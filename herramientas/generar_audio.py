"""Recursos originales sintetizados; sin muestras ni contenido de terceros."""
import math
import struct
import wave
import random
from pathlib import Path


def escribir(ruta, duracion, senal):
    frecuencia = 22050
    ruta.parent.mkdir(parents=True, exist_ok=True)
    muestras = bytearray()
    for i in range(int(duracion * frecuencia)):
        t = i / frecuencia
        borde = min(1.0, t / .04, (duracion-t) / .1)
        valor = max(-1.0, min(1.0, senal(t) * borde))
        muestras.extend(struct.pack("<h", int(valor * 24000)))
    with wave.open(str(ruta), "wb") as archivo:
        archivo.setnchannels(1)
        archivo.setsampwidth(2)
        archivo.setframerate(frecuencia)
        archivo.writeframes(muestras)


def generar():
    base = Path(__file__).resolve().parents[1] / "assets/audio"
    for nombre, notas in {"clic": [660], "notificacion": [523, 784], "compartir": [440, 660],
                          "verificar": [523, 659, 784], "ignorar": [330], "reportar": [440, 330],
                          "nodo": [880], "resultado": [392, 523, 659], "error": [220, 196],
                          "recompensa": [523, 659, 784, 1046], "cuenta_regresiva": [660]}.items():
        escribir(base / "efectos" / f"{nombre}.wav", .30,
                 lambda t, notas=notas: .16 * sum(math.sin(2*math.pi*f*t) for f in notas) / len(notas) * math.exp(-6*t))
    for nombre, bpm, acordes, melodia in (
        ("ciudad", 82, ((60,64,67), (57,60,64), (53,57,60), (55,59,62)), (72,76,79,76,74,72,69,67)),
        ("investigacion", 72, ((57,60,64), (53,57,60), (50,53,57), (52,56,59)), (69,72,71,67,69,64,67,64)),
        ("eleccion", 92, ((62,66,69), (59,62,66), (55,59,62), (57,61,64)), (74,78,81,78,76,74,73,69)),
    ):
        pulso = 60/bpm
        duracion = 32*pulso
        def frecuencia(nota):
            return 440*2**((nota-69)/12)
        def musica(t, pulso=pulso, acordes=acordes, melodia=melodia):
            compas = int(t/(4*pulso))
            acorde = acordes[compas % len(acordes)]
            fase = (t % (4*pulso))/(4*pulso)
            colchón = math.sin(math.pi*fase)**.5 * sum(math.sin(2*math.pi*frecuencia(n)*t) for n in acorde)/3
            tiempo_nota = t % pulso
            nota = melodia[int(t/pulso) % len(melodia)]
            campana = math.exp(-tiempo_nota*5) * (math.sin(2*math.pi*frecuencia(nota)*tiempo_nota)
                        + .18*math.sin(2*math.pi*frecuencia(nota)*2*tiempo_nota))
            bajo = math.sin(2*math.pi*frecuencia(acorde[0]-24)*t) * math.exp(-(t%(2*pulso))*1.5)
            return .085*colchón + .055*campana + .035*bajo
        escribir(base / "musica" / f"{nombre}.wav", duracion, musica)
    for nombre, semilla, intensidad in (("plaza", 1, .012), ("cafe", 2, .018), ("oficina", 3, .007)):
        azar = random.Random(semilla)
        filtrado = [0.0]
        def ambiente(t, azar=azar, nombre=nombre, intensidad=intensidad, filtrado=filtrado):
            filtrado[0] = .97*filtrado[0] + .03*azar.uniform(-1, 1)
            sonido = intensidad*filtrado[0] + .003*math.sin(2*math.pi*90*t)
            momento = t % (7 if nombre == "cafe" else 9)
            if nombre == "cafe" and momento < .3:
                sonido += .012*math.exp(-momento*14)*math.sin(2*math.pi*1800*momento)
            elif nombre == "plaza" and momento < .6:
                sonido += .008*math.sin(math.pi*momento/.6)**2*math.sin(2*math.pi*(1600+350*math.sin(momento*12))*momento)
            return sonido
        escribir(base / "ambientes" / f"{nombre}.wav", 18, ambiente)


if __name__ == "__main__":
    generar()
