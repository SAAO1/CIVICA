"""Capturas offscreen reproducibles de proporciones, sin audio ni preferencias.

Ejecutar desde cualquier carpeta: python herramientas/capturar_escalado.py
Los PNG y un registro de geometrías quedan en .tmp/capturas_escalado.
"""
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from PyQt6.QtWidgets import QApplication

from interfaz import VentanaPrincipal
from juego.partida import Juego
from paneles import DialogoRol


RESOLUCIONES = ((1100, 700), (1366, 768), (1920, 1080))
TEXTO_CORTO = "En Civitas comienzan a aparecer publicaciones polémicas."
TEXTO_LARGO = (
    "Antes de compartir una publicación, revisa quién la escribió y consulta las fuentes. "
    "Tus decisiones afectan la confianza, la convivencia y el bienestar de la ciudad. "
    "Cada vecino tiene una historia y puede ayudar a construir una comunidad mejor informada."
)


def juego_arbol(ids):
    juego = Juego(4, eventos=False)
    publicaciones = {publicacion.id: publicacion for publicacion in juego.publicaciones_planificadas}
    for id in ids:
        juego.arbol.insertar(publicaciones[id])
    juego.ultimo_resultado = "VERIFICAR · #70 · Las fuentes confirman la noticia."
    return juego


def juego_comunidad(etapa):
    juego = Juego(4, eventos=False)
    juego.iniciar_primera_publicacion()
    for _ in range(etapa - 1):
        juego.ejecutar_accion("verificar")
        juego.avanzar_publicacion()
    juego.ejecutar_accion("verificar")
    return juego


def _rect(rect):
    return [rect.x(), rect.y(), rect.width(), rect.height()]


def main():
    app = QApplication.instance() or QApplication([])
    destino = RAIZ / ".tmp/capturas_escalado"
    destino.mkdir(parents=True, exist_ok=True)
    registro = []
    with patch("configuracion.cargar", return_value={}), patch("interfaz.GestorAudio") as audio:
        audio.return_value.volumenes = {
            "general": .65, "musica": .3, "efectos": .6, "ambiente": .2, "voces": 1,
        }
        ventana = VentanaPrincipal()
        ventana.reducir_movimiento = True
        ventana.sin_limite = True
        ventana.aplicar_accesibilidad()
        ventana.show()

        def guardar(nombre, widget, datos=None):
            for _ in range(3):
                app.processEvents()
            ruta = destino / f"{ancho}x{alto}_{nombre}.png"
            if not widget.grab().save(str(ruta)):
                raise RuntimeError(f"No se pudo guardar {ruta}")
            registro.append({"archivo": ruta.name, "ventana": [ancho, alto],
                             "widget": _rect(widget.rect()), **(datos or {})})
            print(ruta.name, flush=True)

        for ancho, alto in RESOLUCIONES:
            ventana.resize(ancho, alto)
            app.processEvents()
            for nombre, ids in (("abb_1", (50,)), ("abb_2", (30, 70)),
                                ("abb_6", (50, 30, 70, 20, 60, 80))):
                ventana.establecer_juego(juego_arbol(ids))
                ventana.mostrar_escena(ventana.ESCENA_ARBOL)
                app.processEvents()
                escena = ventana.escena_arbol
                visualizador = escena.visualizador
                visualizador.grab()
                guardar(nombre, ventana, {
                    "grafo": _rect(visualizador.geometry()),
                    "continuar": _rect(escena.boton_continuar.geometry()),
                    "radio_nodo": getattr(visualizador, "radio_nodo", None),
                    "centros": {id: [p.x(), p.y()] for id, p in getattr(visualizador, "posiciones", {}).items()},
                })

            for etapa, cantidad in ((3, 13), (6, 19)):
                ventana.establecer_juego(juego_comunidad(etapa))
                ventana.mostrar_escena(ventana.ESCENA_GRAFO)
                app.processEvents()
                visualizador = ventana.escena_red.visualizador
                visualizador.grab()
                guardar(f"observatorio_{cantidad}", ventana, {
                    "grafo": _rect(visualizador.geometry()),
                    "radio_nodo": getattr(visualizador, "radio_nodo", None),
                    "centros": {id: [p.x(), p.y()] for id, p in visualizador.posiciones.items()},
                })

            for nombre, texto, contraste in (("dialogo_corto", TEXTO_CORTO, False),
                                             ("dialogo_largo", TEXTO_LARGO, False),
                                             ("dialogo_contraste", TEXTO_CORTO, True)):
                ventana.alto_contraste = contraste
                ventana.mostrar_escena(ventana.ESCENA_NARRACION_1)
                escena = ventana.escena_narracion_1
                escena.finalizar_escena()
                escena.estado_escena = "esperando"
                escena.texto_completo = texto
                escena.texto_label.setText(texto)
                escena.nombre_label.setText("NARRADOR")
                escena.actualizar_geometria()
                for widget in (escena.nombre_label, escena.texto_label, escena.pista_continuar):
                    widget.show()
                    widget.raise_()
                guardar(nombre, ventana, {
                    "franja": _rect(escena.franja_inferior.geometry()),
                    "nombre": _rect(escena.nombre_label.geometry()),
                    "texto": _rect(escena.texto_label.geometry()),
                    "fuente_px": escena.texto_label.font().pixelSize(),
                    "alto_contraste": contraste,
                })
            ventana.alto_contraste = False
            dialogo = DialogoRol(ventana)
            dialogo.show()
            app.processEvents()
            guardar("seleccion_rol", dialogo)
            dialogo.close()

        ventana.close()
        app.processEvents()
    (destino / "geometrias.json").write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")
    print(destino, flush=True)


if __name__ == "__main__":
    main()
