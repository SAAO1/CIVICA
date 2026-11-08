"""Efectos breves de interfaz y descubrimiento, sujetos a la mezcla del juego."""
from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QSoundEffect
from infraestructura.recursos import RAIZ

def instalar_sonidos_novela(gestor):
    for clave in ("hallazgo","paso","red","transicion"):
        nombre="pulido_"+clave
        ruta=RAIZ/"assets/novela/pulido/audio"/(clave+".wav")
        if nombre in gestor.efectos or not ruta.is_file():
            continue
        efecto=QSoundEffect(gestor)
        efecto.setSource(QUrl.fromLocalFile(str(ruta)))
        efecto.setLoopCount(1)
        efecto.setVolume(gestor.volumen("efectos"))
        gestor.efectos[nombre]=efecto
