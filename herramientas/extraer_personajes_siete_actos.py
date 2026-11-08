"""Extrae celdas originales ImageGen conservando la transparencia auténtica."""
import hashlib
import json
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPainter

RAIZ = Path(__file__).resolve().parents[1]
CARPETA = RAIZ / "assets/expansion/siete_actos/personajes"


def extraer():
    datos = json.loads((CARPETA / "prompts.json").read_text(encoding="utf-8"))
    salidas = []
    for personaje in datos["personajes"]:
        ruta_fuente = RAIZ / personaje["atlas"] if "atlas" in personaje else Path(personaje["fuente"])
        fuente = QImage(str(ruta_fuente)).convertToFormat(QImage.Format.Format_RGBA8888)
        if fuente.isNull() or not fuente.hasAlphaChannel():
            raise ValueError(f"Fuente inválida: {personaje['id']}")
        ancho = fuente.width() // 3
        for columna, expresion in enumerate(personaje["expresiones"]):
            celda = fuente.copy(columna * ancho, 0, ancho, fuente.height())
            memoria = celda.constBits().asstring(celda.sizeInBytes())
            xs, ys = [], []
            for y in range(celda.height()):
                inicio = y * celda.bytesPerLine()
                for x in range(celda.width()):
                    if memoria[inicio + x * 4 + 3] > 16:
                        xs.append(x)
                        ys.append(y)
            if not xs:
                raise ValueError("Celda vacía")
            margen = 3
            izq, der = max(0, min(xs) - margen), min(ancho - 1, max(xs) + margen)
            arriba, abajo = max(0, min(ys) - margen), min(celda.height() - 1, max(ys) + margen)
            cuerpo = celda.copy(izq, arriba, der - izq + 1, abajo - arriba + 1)
            cuerpo = cuerpo.scaled(700, 1460, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            imagen = QImage(768, 1536, QImage.Format.Format_ARGB32_Premultiplied)
            imagen.fill(Qt.GlobalColor.transparent)
            pintor = QPainter(imagen)
            pintor.drawImage((768 - cuerpo.width()) // 2, (1536 - cuerpo.height()) // 2, cuerpo)
            pintor.end()
            salida = CARPETA / f"{personaje['id']}_{expresion}.png"
            if not imagen.save(str(salida), "PNG", 9):
                raise ValueError(f"No se pudo guardar {salida}")
            alpha = imagen.convertToFormat(QImage.Format.Format_RGBA8888)
            muestras = alpha.constBits().asstring(alpha.sizeInBytes())[3::4]
            registro = {"archivo": salida.relative_to(RAIZ).as_posix(), "ancho": 768, "alto": 1536,
                        "sha256": hashlib.sha256(salida.read_bytes()).hexdigest(),
                        "alpha_cero": muestras.count(0), "alpha_parcial": sum(0 < a < 255 for a in muestras),
                        "alpha_opaco": muestras.count(255), "esquinas_transparentes": all(imagen.pixelColor(x, y).alpha() == 0 for x, y in ((0,0),(767,0),(0,1535),(767,1535)))}
            if not registro["esquinas_transparentes"] or registro["alpha_cero"] < 100000:
                raise ValueError(f"Transparencia insuficiente: {salida}")
            salidas.append(registro)
            print(salida.name, registro["alpha_cero"], "transparentes", flush=True)
    (CARPETA / "manifest.json").write_text(json.dumps({"version":1,"sprites":salidas}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    extraer()
