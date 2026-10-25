"""Captura las tarjetas reales de los ocho casos nuevos, sin iniciar el audio."""
import json
import os
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QImage, QPainter
from PyQt6.QtWidgets import QApplication

from arte import FUENTE_UI, cargar_tipografias
from juego.partida import Juego
from publicaciones_ui import TarjetaPublicacion


def main():
    app = QApplication.instance() or QApplication([])
    cargar_tipografias()
    casos = Juego(eventos=False, campana="extendida").publicaciones_planificadas[6:]
    destino = RAIZ / "docs/vistas/publicaciones_ocho_casos.jpg"
    destino.parent.mkdir(parents=True, exist_ok=True)
    lienzo = QImage(1920, 1080, QImage.Format.Format_RGB32)
    lienzo.fill(QColor("#182a2d"))
    p = QPainter(lienzo)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    fuente = QFont(FUENTE_UI)
    fuente.setPixelSize(21)
    p.setFont(fuente)
    datos = []
    for i, caso in enumerate(casos):
        tarjeta = TarjetaPublicacion()
        tarjeta.resize(458, 482)
        tarjeta.mostrar(caso)
        captura = tarjeta.grab()
        x, y = 12+(i % 4)*480, 14+(i//4)*535
        p.setPen(QColor("#f2d2a0"))
        p.drawText(QRectF(x, y, 458, 31), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                   f"Caso {7+i} · Publicación #{caso.id}")
        p.drawPixmap(x, y+36, captura)
        datos.append({"id": caso.id, "tarjeta": [458, 482],
                      "medio": [round(tarjeta.area_medio.width()), round(tarjeta.area_medio.height())]})
        tarjeta.deleteLater()
    p.end()
    if not lienzo.save(str(destino), "JPG", 87):
        raise OSError(f"No se pudo guardar {destino}")
    reporte = {"tipo": "Montaje de ocho TarjetaPublicacion Qt reales, no captura de una partida completa",
               "tamano": [1920, 1080], "ids": [c.id for c in casos], "tarjetas": datos,
               "procedencia": "Ilustraciones locales existentes + objetos de interfaz pintados en Qt; sin veredictos en las miniaturas"}
    (RAIZ / "docs/verificacion_publicaciones_visibles.json").write_text(
        json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8")
    app.processEvents()
    print(destino)


if __name__ == "__main__":
    main()
