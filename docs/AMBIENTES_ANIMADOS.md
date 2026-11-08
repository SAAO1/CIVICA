# Fondos vivos

`ambiente_visual.FondoVivo` dibuja las ilustraciones con recorte centrado sin
deformarlas. Las capas se calculan en tiempo real: cámara suave, brisa y hojas
con distintas profundidades, aves lejanas, luz, agua y gotas de las fuentes,
vapor de las tazas, polvo iluminado, faroles, reflejos nocturnos y lluvia.
No utiliza Internet ni sintetiza imágenes durante la partida.

```python
from ambiente_visual import FondoVivo

fondo = FondoVivo(escena)
fondo.setGeometry(escena.rect())
fondo.establecer_escena("assets/expansion/fondos/cafe_lluvia.png")
fondo.lower()
fondo.show()
```

La ruta determina el perfil cuando se reconoce una ilustración. También se
aceptan estos nombres en el segundo argumento:

| Perfil | Elementos que se mueven |
| --- | --- |
| `ciudad`, `plaza` | Fuente, aves, hojas y nubes suaves |
| `portada`, `atardecer` | Fuente, brisa, luz de faroles y partículas cálidas |
| `cafe_exterior` | Hojas, aves, luces y vapor de las tazas |
| `cafe`, `cafe_interior` | Polvo en el haz de luz, vapor y lámparas |
| `telefono` | Brisa y ambiente del café, con el teléfono despejado |
| `investigacion`, `oficina` | Polvo, rayos de luz y lámpara de escritorio |
| `observatorio` | Luz cálida y polvo discreto |
| `lluvia` | Lluvia exterior y pequeños círculos sobre el suelo |
| `cafe_lluvia` | Lluvia sobre los cristales; vapor y lámparas dentro |
| `noche`, `plaza_noche` | Fuente, faroles, reflejos y luciérnagas |
| `parque`, `parque_tarde` | Brisa más presente, hojas, aves y fuente |

No se debe pasar `ambiente="lluvia"` al café interior: ese argumento solicita
lluvia exterior. La ruta `cafe_lluvia.png` selecciona el perfil que confina la
lluvia a los cristales.

## Reloj y accesibilidad

- `configurar(reducir_movimiento=True)` detiene las capas y conserva el arte
  quieto. No deja un vídeo ni un temporizador funcionando en segundo plano.
- `configurar(activo=False)` pausa el ambiente; `activo=True` lo reanuda.
- El temporizador corre sólo cuando el widget es visible, a un máximo de
  29.4 FPS (34 ms entre actualizaciones). Ocultar o cerrar la escena lo detiene.
- El widget deja pasar clics y no recibe foco, para mantener los controles
  accesibles por ratón y teclado.
- `intensidad` en `establecer_escena` admite valores de 0 a 2. El valor 1 es la
  ambientación normal. El valor 0 detiene el temporizador y conserva el arte.

## Capturas y exportación

```python
imagen = fondo.capturar_fotograma(segundos=3.0, tamano=(1366, 768))
imagen.save("fotograma.png")
fondo.establecer_tiempo(3.0)  # Congela un instante para inspección.
fondo.establecer_tiempo(None) # Devuelve el control al reloj.
```

`herramientas/exportar_ambientes.py` guarda GIF89a reales (paleta tramada y
compresión LZW estándar, sin Pillow), PNG de muestra y un manifiesto con
dimensiones, duración, cuadros y SHA-256. También puede exportar MP4 H.264 con
FFmpeg como herramienta de desarrollo. El juego no necesita FFmpeg instalado.
Los archivos se guardan en `assets/expansion/movimiento/`.

```powershell
python herramientas/exportar_ambientes.py --escena cafe_lluvia
python herramientas/exportar_ambientes.py --todos
python herramientas/exportar_ambientes.py --escena plaza_noche --formato mp4 --ancho 1280 --fps 24 --segundos 8
```

Las exportaciones usan un solape suave de 0.8 segundos al cerrar el bucle para
evitar el salto de cámara. Las capas del motor durante la partida avanzan de
forma continua. Los GIF son vistas portátiles con una paleta de 256 colores;
el motor conserva los colores completos y la resolución real de la ventana.
Los vídeos son grabaciones de las capas Qt sobre las ilustraciones locales.

## Verificación

`python -B -m unittest tests.test_ambiente_visual -v` comprueba el reloj visible,
la pausa, la accesibilidad, el tiempo reproducible, los perfiles, el respaldo
ante una imagen ausente y la decodificación de cuadros distintos de un GIF
exportado con `QImageReader`.

En esta máquina, el renderizado de las cuatro escenas exteriores/principales
tuvo medias de 9.8–14.5 ms por cuadro a 1366×768 y de 17.8–24.5 ms a 1920×1080.
Se midieron 30 capturas por escena y tamaño; cada captura incluye la asignación
de un QImage. Datos: `.tmp/rendimiento_ambientes.json`. No es una garantía de
rendimiento para otros equipos.
