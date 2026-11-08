"""Comprobación real de Qt Multimedia con su bucle de eventos completo."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PyQt6.QtCore import QCoreApplication, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QMediaDevices
from audio.gestor_audio import GestorAudio


def main():
    app = QCoreApplication([])
    audio = GestorAudio()
    resultado = {"dispositivos": len(QMediaDevices.audioOutputs())}
    audio.cambiar_pista("ciudad")
    audio.cambiar_pista("investigacion")
    audio.cambiar_pista("ciudad")
    reproductor, salida = audio.pistas["musica"]
    inicio = time.monotonic()
    def comprobar():
        listo = reproductor.position() > 0 and reproductor.duration() > 0 and reproductor.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        if not listo and reproductor.error() == QMediaPlayer.Error.NoError and time.monotonic()-inicio < 9:
            QTimer.singleShot(100, comprobar)
            return
        resultado.update(posicion=reproductor.position(), duracion=reproductor.duration(),
                         reproduciendo=reproductor.playbackState() == QMediaPlayer.PlaybackState.PlayingState,
                         error=reproductor.errorString(), fuente=Path(reproductor.source().toLocalFile()).name)
        audio.silenciar()
        QTimer.singleShot(200, silenciado)
    def silenciado():
        resultado["silencio"] = salida.volume() == 0
        audio.configurar("musica", .8)
        resultado["silencio_tras_volumen"] = salida.volume() == 0
        audio.silenciar(False)
        resultado["restaurado"] = abs(salida.volume()-audio.volumen("musica")) < .0001
        audio.detener()
        print(json.dumps(resultado), flush=True)
        app.quit()
    QTimer.singleShot(200, comprobar)
    app.exec()
    return 0 if resultado.get("posicion", 0) > 0 and resultado.get("silencio") and resultado.get("restaurado") else 1


if __name__ == "__main__":
    sys.exit(main())
