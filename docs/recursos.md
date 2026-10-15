# Recursos conservados y añadidos

Las 26 imágenes originales, Anton.ttf y OFL.txt se conservan. Se añadió un paquete de 23 PNG generados y ya integrados, sin reemplazar físicamente los originales. Inventario, medidas, prompts y procedencia en [rediseno_visual.md](rediseno_visual.md) y `assets/rediseno/manifiesto.json`.

## Inventario original

| Grupo | Contenido | Observaciones |
|---|---|---|
| Fondos | Portada, Escena 1–8 y Escena Arbol | Varias resoluciones; escalado proporcional |
| Personajes | Ciudadano.png, periodista.png | 480×1080, transparencia real |
| Candidatos | Alcalde 1.jfif, Alcelde 2.jfif, Alcalde 3.jfif, Alcalde 4.jfif | JPEG sin alfa; patrones de fondo visibles |
| UI | Tres avatares, menú y componentes de teléfono | Avatares incorporados al panel de publicación; componentes originales disponibles |
| Fuente | Anton.ttf y OFL.txt | Se conserva la licencia SIL OFL |

Duplicados exactos: Escena 4/5/8, Escena 6/7, phone_background/phone_background_1. Se mantienen porque las rutas forman parte del trabajo original.

Los fondos originales de diálogo/investigación incluían personajes. Los nuevos fondos están limpios y utilizan los sprites generados como capas animadas. El respaldo conserva la opción de evitar duplicaciones cuando se usan composiciones originales.

## Audio original nuevo

`assets/audio/efectos/`: clic, notificacion, compartir, verificar, ignorar, reportar, nodo, resultado, error, recompensa y cuenta_regresiva (WAV mono PCM, 22.050 Hz).

`assets/audio/musica/`: ciudad, investigacion y eleccion; piezas originales de ocho compases con melodía, acordes y bajo, de aproximadamente 23,41, 26,67 y 20,87 segundos. `assets/audio/ambientes/`: plaza, cafe y oficina, de 18 segundos, con ruido filtrado y detalles sintetizados. Son síntesis originales. El generador reproducible está en `herramientas/generar_audio.py`.

Se comprobó la validez PCM de los diecisiete archivos y la reproducción mediante Qt Multimedia. `herramientas/comprobar_audio.py` comprueba la posición, la fuente final tras cambios rápidos, duración, silencio y volumen con el bucle real de Qt. La evaluación artística de timbre, repetición y mezcla queda para una sesión de escucha.

## Arte nuevo instalado

El paquete cubre los siete fondos, los dos protagonistas y sus expresiones, retratos de selección, cuatro candidatos, nueve avatares, seis noticias, 24 iconos y pieles de paneles, diálogo, botón y controles. Los atlas se recortan en memoria y los datos se dibujan con Qt. No se generaron videos ni GIF; se conservan las animaciones de personajes y recorridos existentes.

La ampliación opcional de expresiones o escenas posteriores puede realizarse sobre este paquete. El influencer sigue fuera de la selección y no tiene un sprite propio: no se presenta como un recurso generado.
