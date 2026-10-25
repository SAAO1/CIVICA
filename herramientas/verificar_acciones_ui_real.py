"""Ocho decisiones por botones reales: vídeo obligatorio y continuidad Qt.

Usa QMediaPlayer, MP4 y voces locales reales. Las preferencias y biblioteca
están aisladas; las pulsaciones automatizadas no representan juego humano.
Se deja reproducir cada montaje hasta EndOfMedia, sin simular ese estado.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_LOGGING_RULES", "qt.multimedia.*=false")

from PyQt6.QtCore import QPoint, QCoreApplication, QEvent, QRectF, Qt
from PyQt6.QtGui import QFontMetrics, QImage
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication
from audio.gestor_audio import GestorAudio
from arte import geometria_dialogo
from interfaz import VentanaPrincipal
from juego.acciones import accion_por_defecto
from juego.cinematica_acciones import CINEMATICAS_ACCIONES, clave_accion
from juego.lectura import BibliotecaLectura
from juego.partida import Juego

CASOS = ((50, "ciudadano", "compartir"), (30, "ciudadano", "conversar"),
         (70, "ciudadano", "convocar"), (20, "ciudadano", "ignorar"),
         (60, "periodista", "contrastar"), (80, "periodista", "entrevistar"),
         (30, "periodista", "desmentir"), (20, "periodista", "reservar"))


def esperar(condicion, descripcion, limite=12):
    fin = time.monotonic()+limite
    while not condicion():
        if time.monotonic() > fin:
            raise AssertionError(f"Tiempo agotado: {descripcion}")
        QTest.qWait(10)


def serializar(juego):
    return json.dumps(juego.datos(), ensure_ascii=False, sort_keys=True)


def huella(ruta):
    return hashlib.sha256(ruta.read_bytes()).hexdigest() if ruta.is_file() else None


def diferencia(a, b):
    a, b = a.scaled(64, 36), b.scaled(64, 36)
    total = 0
    for y in range(36):
        for x in range(64):
            ca, cb = a.pixelColor(x, y), b.pixelColor(x, y)
            total += abs(ca.red()-cb.red())+abs(ca.green()-cb.green())+abs(ca.blue()-cb.blue())
    return total/(64*36*3)


def preparar_juego(identificador, rol, campana="clasica"):
    juego = Juego(4, eventos=False, campana=campana)
    juego.seleccionar_rol(rol)
    juego.iniciar_primera_publicacion()
    while juego.obtener_publicacion_actual().id != identificador:
        assert juego.ejecutar_accion(accion_por_defecto(rol))
        assert juego.avanzar_publicacion()
    return juego


def comprobar_encuadre(escena):
    """El panel animado debe acabar donde están nombre, cuerpo y pista."""
    panel = escena.franja_inferior.geometry()
    assert panel.bottom() == escena.height()-1, (panel.getRect(), escena.height())
    cuerpo, nombre, pista = geometria_dialogo(QRectF(panel))
    for widget, esperado in ((escena.texto_label, cuerpo), (escena.nombre_label, nombre),
                             (escena.pista_continuar, pista)):
        assert widget.geometry() == esperado.toAlignedRect(), (widget.geometry().getRect(), esperado.getRect())
    return dict(panel=panel.getRect(), nombre=escena.nombre_label.geometry().getRect(),
                cuerpo=escena.texto_label.geometry().getRect(),
                pista=escena.pista_continuar.geometry().getRect())


def comprobar_etiqueta(boton, accion):
    """El texto debe caber completo, incluidos los dos títulos del barrio."""
    texto = boton.text()
    assert "\n" not in texto and 0 < len(texto) <= 20, texto
    esperado = {"conversar": "Escuchar al barrio", "convocar": "Convocar al barrio"}.get(accion)
    if esperado is not None:
        assert texto == esperado, (accion, texto)
    ancho_texto = QFontMetrics(boton.font()).horizontalAdvance(texto)
    espacio_icono = boton.iconSize().width()+12 if not boton.icon().isNull() else 0
    assert ancho_texto + espacio_icono + 28 <= boton.width(), (texto, ancho_texto, boton.width())
    return dict(texto=texto, ancho_texto=ancho_texto, ancho_boton=boton.width(),
                ancho_icono_y_separacion=espacio_icono, sin_recorte=True)


def main():
    global CINEMATICAS_ACCIONES, clave_accion
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extendida", action="store_true", help="Los ocho casos de los actos IV a VII.")
    parser.add_argument("--accion", action="append", choices=[caso[2] for caso in CASOS],
                        help="Comprueba sólo este botón; se puede repetir")
    parser.add_argument("--acumular", action="store_true", help="Conserva casos ya comprobados cuyos medios no cambiaron")
    args = parser.parse_args()
    campana = "extendida" if args.extendida else "clasica"
    casos_base = CASOS
    if args.extendida:
        from juego.cinematica_acciones_extendida import CINEMATICAS_ACCIONES_EXTENDIDAS, clave_accion_extendida
        CINEMATICAS_ACCIONES = CINEMATICAS_ACCIONES_EXTENDIDAS
        clave_accion = clave_accion_extendida
        casos_base = ((90, "ciudadano", "compartir"), (40, "ciudadano", "conversar"),
                      (100, "ciudadano", "convocar"), (10, "ciudadano", "ignorar"),
                      (110, "periodista", "contrastar"), (25, "periodista", "entrevistar"),
                      (120, "periodista", "desmentir"), (35, "periodista", "reservar"))
    casos = tuple(caso for caso in casos_base if not args.accion or caso[2] in args.accion)
    destino = RAIZ / (".tmp/acciones_ui_siete_actos" if args.extendida else ".tmp/acciones_ui_real")
    destino.mkdir(parents=True, exist_ok=True)
    previos = []
    ruta_resultado = destino / "resultado.json"
    if args.acumular and ruta_resultado.is_file():
        anterior = json.loads(ruta_resultado.read_text(encoding="utf-8"))
        if not anterior.get("correcto"):
            raise RuntimeError("No se acumula una ejecución anterior fallida")
        for caso in anterior.get("casos", []):
            if caso["accion"] in {c[2] for c in casos}:
                continue
            entrada = CINEMATICAS_ACCIONES[caso["clave"]]
            if any(huella(RAIZ/entrada[tipo]) != caso[f"sha256_{tipo}"] for tipo in ("video", "inicio")):
                raise RuntimeError(f"Cambió el recurso comprobado: {caso['clave']}; repite ese caso")
            previos.append(caso)
    preferencias = {nombre: huella(RAIZ / ".civica" / nombre)
                    for nombre in ("config.json", "biblioteca.json")}
    for identificador, rol, accion in casos:
        juego = preparar_juego(identificador, rol, campana)
        assert juego.ejecutar_accion(accion)
        clave = clave_accion(juego)
        for tipo in ("video", "poster", "inicio"):
            if not (RAIZ / CINEMATICAS_ACCIONES[clave][tipo]).is_file():
                raise FileNotFoundError(f"Aún no está listo {clave}: {tipo}")
    app = QApplication.instance() or QApplication([])
    evidencia = dict(correcto=False, completo_ocho_botones=False, casos=previos, errores=[],
                     transporte="QMediaPlayer real y MP4 locales; EndOfMedia no simulado",
                     audio="GestorAudio real; voces locales a volumen reducido",
                     valoracion_humana=False)
    with (patch("configuracion.cargar", return_value={}),
          patch("configuracion.guardar") as guardar,
          patch("interfaz.BibliotecaLectura", lambda: BibliotecaLectura(None))):
        ventana = VentanaPrincipal()
        ventana.sin_limite = True
        ventana.reducir_movimiento = False
        ventana.animar_fondos = True
        ventana.animar_personajes = True
        ventana.velocidad_texto = 0
        ventana.resize(1366, 768)
        assert isinstance(ventana.audio, GestorAudio)
        for categoria in ventana.audio.volumenes:
            ventana.audio.configurar(categoria, .08 if categoria == "general" else 1 if categoria == "voces" else 0)
        ventana.audio.configurar_voces(True)
        ventana.audio.silenciar(False)
        ventana.show()
        app.processEvents()
        try:
            for indice, (identificador, rol, accion) in enumerate(casos):
                juego = preparar_juego(identificador, rol, campana)
                ventana.establecer_juego(juego)
                ventana.mostrar_escena(ventana.ESCENA_ACCION)
                ventana.animacion_transicion.stop()
                ventana.velo_transicion.hide()
                opciones = ventana.escena_accion
                opciones.animacion_panel.stop()
                opciones.efecto_panel.setOpacity(1.)
                boton = opciones.botones_por_accion[accion]
                assert boton.isEnabled() and boton.isVisible()
                etiqueta = comprobar_etiqueta(boton, accion)
                if indice in (0, 4):
                    assert ventana.grab().save(str(destino / f"botones_{rol}.jpg"), "JPG", 87)
                QTest.mouseClick(boton, Qt.MouseButton.LeftButton)
                assert ventana.escenas.currentIndex() == ventana.ESCENA_RESULTADO_1
                escena = ventana.escena_resultado_1
                cine = escena.cine_narrativo
                clave = clave_accion(juego)
                assert cine.clave_actual == clave
                assert cine._pausada and cine._poster.isVisible()
                assert cine._reproductor is None or cine._reproductor.source().isEmpty()
                assert diferencia(cine._poster.imagen.toImage(), QImage(str(RAIZ / CINEMATICAS_ACCIONES[clave]["inicio"]))) == 0
                assert all(not actor.isVisible() for actor in escena.personajes.values())
                assert CINEMATICAS_ACCIONES[clave]["nombre"] == escena.nombre_inicial.upper()
                antes = serializar(juego)
                if accion == "convocar":
                    alcance = juego.ultimo_registro["alcance"]
                    variante = "sin_receptores" if alcance == 0 else "alcance_limitado" if alcance < 8 else ""
                    assert CINEMATICAS_ACCIONES[clave]["variante"] == variante
                if accion == "desmentir":
                    assert not juego.ultimo_registro["eliminada"]
                    assert CINEMATICAS_ACCIONES[clave]["variante"] == "rechazado"
                esperar(lambda: cine.estado == "reproduciendo", f"primer plano de {clave}")
                comprobar_encuadre(escena)
                inicio = time.monotonic()
                reproductor = cine._reproductor
                eventos = []
                def fin_media(estado):
                    if estado == QMediaPlayer.MediaStatus.EndOfMedia:
                        eventos.append(reproductor.position())
                reproductor.mediaStatusChanged.connect(fin_media)
                for pulso in range(100):
                    if pulso % 3 == 0:
                        QTest.keyClick(escena, Qt.Key.Key_Space)
                    elif pulso % 3 == 1:
                        QTest.keyClick(escena, Qt.Key.Key_Return)
                    else:
                        QTest.mouseClick(escena, Qt.MouseButton.LeftButton,
                                         pos=QPoint(escena.width()//2, escena.height()//3))
                    assert ventana.escenas.currentIndex() == ventana.ESCENA_RESULTADO_1, (clave, pulso)
                assert escena.corte_accion_pendiente()
                esperar(lambda: reproductor.position() >= 2500, f"avance antes de pausa {clave}")
                posicion_antes = reproductor.position()
                reanudar = ventana.pausar_lectura_modal()
                congelada = cine._poster.imagen.toImage()
                assert escena.lectura_pausada and reproductor.source().isEmpty()
                QTest.qWait(120)
                assert abs(cine._posicion-posicion_antes) < 125
                assert diferencia(cine._poster.imagen.toImage(), congelada) == 0
                reanudar()
                esperar(lambda: cine.estado == "reproduciendo", f"reanudar {clave}")
                assert reproductor.position() >= posicion_antes-125
                esperar(lambda: cine._video.videoSink().videoFrame().startTime() >= 5_450_000,
                        f"captura a 5.5 s {clave}")
                fotograma_ms = cine._video.videoSink().videoFrame().startTime()/1000
                encuadre = comprobar_encuadre(escena)
                captura = destino / f"{clave}_5500.jpg"
                assert ventana.grab().save(str(captura), "JPG", 88)
                assert ventana.escenas.currentIndex() == ventana.ESCENA_RESULTADO_1
                assert escena.corte_accion_pendiente()
                esperar(lambda: cine.estado == "finalizada", f"EndOfMedia real de {clave}")
                assert eventos and eventos[-1] >= 8900
                assert not escena.corte_accion_pendiente()
                assert serializar(juego) == antes
                if escena.escribiendo:
                    QTest.keyClick(escena, Qt.Key.Key_Space)
                QTest.keyClick(escena, Qt.Key.Key_Space)
                assert ventana.escenas.currentIndex() == ventana.ESCENA_RESULTADO_2
                assert reproductor.source().isEmpty() and not cine.activa
                reproductor.mediaStatusChanged.disconnect(fin_media)
                evidencia["casos"].append(dict(clave=clave, publicacion=identificador, rol=rol,
                    accion=accion, texto_boton=boton.text(), alcance=juego.ultimo_registro["alcance"],
                    etiqueta_verificada=etiqueta,
                    sha256_video=huella(RAIZ/CINEMATICAS_ACCIONES[clave]["video"]),
                    sha256_inicio=huella(RAIZ/CINEMATICAS_ACCIONES[clave]["inicio"]),
                    video_real=True, cubierta_antes_de_panel=True, pulsaciones_bloqueadas=100,
                    pausa_reanuda_ms=posicion_antes, captura=captura.relative_to(RAIZ).as_posix(),
                    fotograma_capturado_ms=fotograma_ms, fin_real_ms=eventos[-1],
                    encuadre_verificado=encuadre,
                    segundos_transcurridos=round(time.monotonic()-inicio, 3),
                    avance_solo_despues_del_video=True, partida_sin_cambios_durante_presentacion=True))
                print(f"OK {clave}: 100 pulsaciones bloqueadas, pausa, captura {fotograma_ms:g} ms y fin real {eventos[-1]} ms", flush=True)
            evidencia["correcto"] = True
            evidencia["completo_ocho_botones"] = {c["accion"] for c in evidencia["casos"]} == {c[2] for c in casos_base}
        except BaseException as error:
            evidencia["errores"].append(str(error))
            raise
        finally:
            ventana.close()
            ventana.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            evidencia["preferencias_sin_cambios"] = all(huella(RAIZ / ".civica" / nombre) == h
                                                       for nombre, h in preferencias.items())
            evidencia["guardado_config_no_invocado"] = not guardar.called
            ruta_resultado.write_text(json.dumps(evidencia, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    assert evidencia["preferencias_sin_cambios"] and evidencia["guardado_config_no_invocado"]
    print(json.dumps(dict(correcto=evidencia["correcto"], casos=len(evidencia["casos"]),
                          completo_ocho_botones=evidencia["completo_ocho_botones"]), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
