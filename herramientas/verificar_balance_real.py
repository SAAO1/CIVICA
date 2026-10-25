"""Verifica la escena de balance con UI, transporte y MP3 reales.

No escribe preferencias ni progreso personal. La prueba usa un reloj de Qt y
termina al oír la secuencia completa; no sustituye la voz por un mock. Guarda
dos JPEG y evidencia JSON. No constituye una valoración auditiva humana.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_LOGGING_RULES", "qt.multimedia.*=false")

from PyQt6.QtCore import QRect, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QImage, QPainter
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication
from audio.catalogo_voces import segmentos_indicadores
from audio.gestor_audio import GestorAudio
from interfaz import VentanaPrincipal
from juego.lectura import BibliotecaLectura
from juego.partida import Juego


def huella(ruta):
    return hashlib.sha256(ruta.read_bytes()).hexdigest() if ruta.is_file() else None


def estado_serializado(juego):
    return json.dumps(juego.datos(), ensure_ascii=False, sort_keys=True)


def main():
    destino = ROOT / ".tmp/balance_real"
    destino.mkdir(parents=True, exist_ok=True)
    preferencias = {nombre: huella(ROOT / ".civica" / nombre)
                    for nombre in ("config.json", "biblioteca.json")}
    app = QApplication.instance() or QApplication([])
    inicio = time.monotonic()
    evidencia = {"correcto": False, "segmentos": [], "confianza_animacion": [],
                 "errores": [], "transporte": "QMediaPlayer real; clips neuronales locales",
                 "escena": "VentanaPrincipal · EscenaResultado tipo 3",
                 "valoracion_auditiva_humana": False,
                 "configuracion_prueba": {"general": .2, "voces": .6,
                                          "musica": 0, "ambiente": 0, "efectos": 0}}
    capturas = []
    terminado = False

    with (patch("configuracion.cargar", return_value={}),
          patch("configuracion.guardar") as guardar,
          patch("interfaz.BibliotecaLectura", lambda: BibliotecaLectura(None))):
        ventana = VentanaPrincipal()
        assert isinstance(ventana.audio, GestorAudio)
        audio = ventana.audio
        for categoria, volumen in evidencia["configuracion_prueba"].items():
            audio.configurar(categoria, volumen)
        audio.configurar_voces(True)
        audio.silenciar(False)
        ventana.sin_limite = True
        ventana.resize(1280, 720)
        ventana.show()
        juego = Juego(4, eventos=False)
        juego.seleccionar_rol("periodista")
        juego.jugador.ciudadano_id = "carlos"
        juego.estado.desinformacion = 9
        juego.iniciar_primera_publicacion()
        assert juego.ejecutar_accion("contrastar")
        assert juego.estado.confianza == 56
        assert juego.estado.info_verificada == 5
        assert juego.estado.desinformacion == 1
        ventana.establecer_juego(juego)
        antes = estado_serializado(juego)
        esperado = [s["clave"] for s in segmentos_indicadores(juego.ultimo_registro)]
        evidencia["indicadores_antes"] = dict(juego.ultimo_registro["antes"])
        evidencia["indicadores_despues"] = dict(juego.ultimo_registro["despues"])
        evidencia["claves_esperadas"] = esperado
        evidencia["voces_locales"] = audio.estado_voces()["clips_locales"]
        escena = ventana.escena_resultado_3

        def terminar(correcto):
            nonlocal terminado
            if terminado:
                return
            terminado = True
            evidencia["correcto"] = bool(correcto)
            evidencia["duracion_segundos"] = round(time.monotonic() - inicio, 3)
            evidencia["estado_partida_sin_cambios"] = antes == estado_serializado(juego)
            evidencia["preferencias_sin_cambios"] = all(
                huella(ROOT / ".civica" / nombre) == valor for nombre, valor in preferencias.items())
            evidencia["guardado_config_no_invocado"] = not guardar.called
            ventana.close()
            QTimer.singleShot(0, app.quit)

        def protegido(funcion):
            def ejecutar(*args):
                if terminado:
                    return
                try:
                    funcion(*args)
                except Exception:
                    evidencia["errores"].append(traceback.format_exc())
                    terminar(False)
            return ejecutar

        @protegido
        def captura_confianza(retardo_ms):
            assert escena.balance.clave_actual == "confianza"
            assert not escena.texto_label.isVisible()
            imagen = escena.balance.grab().toImage()
            caja = QRect(round(imagen.width() * .16), round(imagen.height() * .21),
                         round(imagen.width() * .68), round(imagen.height() * .53))
            recorte = imagen.copy(caja)
            datos = recorte.constBits().asstring(recorte.sizeInBytes())
            evidencia["confianza_animacion"].append({
                "retardo_programado_ms": retardo_ms,
                "reloj_animacion_ms": round(escena.balance.tiempo_actual() * 1000),
                "pixel_sha256": hashlib.sha256(datos).hexdigest(),
                "antes": 50, "despues": 56, "cambio": 6})
            capturas.append((retardo_ms, recorte))

        @protegido
        def segmento(clave):
            # El slot de VentanaPrincipal se conectó en su constructor y debe
            # haber actualizado el centro antes de llegar a este observador.
            assert ventana.escenas.currentWidget() is escena
            assert escena.balance.clave_actual == clave
            assert audio._reproductor_voz.playbackState().name == "PlayingState"
            assert not escena.texto_label.isVisible()
            assert "Confianza +6" not in escena.texto_label.text()
            assert not escena.balance._automatico
            for _ in range(10):
                QTest.keyClick(escena, Qt.Key.Key_Space)
                QTest.keyClick(escena, Qt.Key.Key_Return)
                QTest.mouseClick(escena, Qt.MouseButton.LeftButton)
            assert ventana.escenas.currentWidget() is escena
            assert escena.balance.clave_actual == clave
            assert not escena.balance_listo()
            tarjeta = next(t for t in escena.balance.tarjetas if t["clave"] == clave)
            evidencia["segmentos"].append({
                "clave": clave, "tarjeta_actual": escena.balance.clave_actual,
                "estado_transporte": audio._reproductor_voz.playbackState().name,
                "archivo": Path(audio._reproductor_voz.source().toLocalFile()).name,
                "posicion_ms": audio._reproductor_voz.position(),
                "duracion_ms": audio._reproductor_voz.duration(),
                "antes": tarjeta["antes"], "despues": tarjeta["despues"],
                "delta": tarjeta["delta"], "subtitulo_oculto": True,
                "pulsaciones_anticipadas_ignoradas": 30,
                "transcurrido_ms": round((time.monotonic() - inicio) * 1000)})
            if clave == "confianza":
                assert (tarjeta["antes"], tarjeta["despues"], tarjeta["delta"]) == (50, 56, 6)
                for retardo in (0, 500, 1000):
                    QTimer.singleShot(retardo, lambda ms=retardo: captura_confianza(ms))

        @protegido
        def guardar_capturas_y_cerrar():
            assert escena.balance.completo
            assert [s["clave"] for s in evidencia["segmentos"]] == esperado
            assert len(capturas) == 3
            assert len({c["pixel_sha256"] for c in evidencia["confianza_animacion"]}) == 3
            assert antes == estado_serializado(juego)
            assert not escena.texto_label.isVisible()
            tira = QImage(1200, 245, QImage.Format.Format_RGB32)
            tira.fill(QColor("#0c1f2a"))
            pintor = QPainter(tira)
            pintor.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            fuente = QFont("Segoe UI")
            fuente.setPixelSize(17)
            pintor.setFont(fuente)
            pintor.setPen(QColor("#f4e8d0"))
            for i, (retardo, imagen) in enumerate(capturas):
                pintor.drawText(QRect(i * 400, 3, 400, 30), Qt.AlignmentFlag.AlignCenter,
                                f"Confianza · {retardo / 1000:g} s")
                pintor.drawImage(QRect(i * 400, 37, 400, 196), imagen)
            pintor.end()
            assert tira.save(str(destino / "confianza_animacion.jpg"), "JPG", 86)
            resumen = ventana.grab().scaledToWidth(1100, Qt.TransformationMode.SmoothTransformation)
            assert resumen.save(str(destino / "balance_final.jpg"), "JPG", 85)
            evidencia["contadores_completos"] = True
            evidencia["cuadricula_de_resumen"] = False
            evidencia["capturas"] = [".tmp/balance_real/confianza_animacion.jpg",
                                      ".tmp/balance_real/balance_final.jpg"]
            terminar(True)

        @protegido
        def fin(completada):
            assert completada, "La secuencia se canceló o falló antes del último clip."
            QTimer.singleShot(120, guardar_capturas_y_cerrar)

        @protegido
        def timeout():
            raise TimeoutError("No terminó la secuencia real antes de 60 segundos.")

        audio.segmento_iniciado.connect(segmento)
        audio.secuencia_finalizada.connect(fin)
        QTimer.singleShot(60000, timeout)
        ventana.mostrar_escena(ventana.ESCENA_RESULTADO_3)
        app.exec()
        evidencia["estado_partida_sin_cambios"] = antes == estado_serializado(juego)
        evidencia["preferencias_sin_cambios"] = all(
            huella(ROOT / ".civica" / nombre) == valor for nombre, valor in preferencias.items())
        evidencia["correcto"] = bool(evidencia["correcto"] and evidencia["estado_partida_sin_cambios"]
                                     and evidencia["preferencias_sin_cambios"] and not guardar.called)
    contenido = json.dumps(evidencia, ensure_ascii=False, indent=2)
    (destino / "evidencia.json").write_text(contenido, encoding="utf-8")
    (ROOT / "docs/verificacion_balance_audio.json").write_text(contenido, encoding="utf-8")
    print(json.dumps(evidencia, ensure_ascii=False), flush=True)
    return 0 if evidencia["correcto"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
