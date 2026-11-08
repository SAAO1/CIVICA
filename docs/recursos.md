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

El paquete original cubre los siete fondos, los dos protagonistas y sus expresiones, retratos de selección, cuatro candidatos, nueve avatares, seis noticias, 24 iconos y pieles de paneles, diálogo, botón y controles. Los atlas se recortan en memoria y los datos se dibujan con Qt.

La expansión audiovisual del 24 de octubre añade cuatro atlas transparentes de los protagonistas (48 fotogramas), tres fondos, once GIF y tres MP4, además del motor de movimiento en tiempo real. Añade 595 MP3 neuronales y 27 WAV de ambientes, efectos y música. Los originales se conservan. Rutas, prompts, autores, licencias y alcance: [expansion_audiovisual.md](expansion_audiovisual.md).

En la campaña de siete actos, Valeria Cruz interviene como influencer dentro de la historia y del grafo. Tiene sprites propios; los dos oficios jugables siguen siendo Ciudadano y Periodista.

## Cortos narrativos instalados

`assets/expansion/cinematica/` añade nueve MP4 silenciosos, nueve carteles JPG y seis pinturas JPG originales generadas con `image_gen`. Los videos suman 108 segundos en 1280×720 a 24 fps y se reproducen durante las intervenciones del narrador. El manifest registra SHA-256 y fuentes; `prompts.json` conserva los seis prompts exactos. Los catorce efectos adicionales son dibujos y animaciones del motor Qt y no requieren archivos externos. [Detalle y muestra](cinematicas_narrativas.md).

## Balance y oficios

La ampliación de oficios sumó tres pinturas ImageGen (familia, hermana y entrevista), doce MP4 de personajes y cinco MP4 de desenlace. Se añadieron 422 tomas neuronales, para un total de 1.017. Los contadores centrales y las uniones del grafo son animaciones Qt. [Rutas, prompts y evidencia](impacto_roles_y_finales.md).

La revisión de continuidad agrega 66 MP4 de acciones en `assets/expansion/acciones_video/`, sus 66 carteles y sus 66 cubiertas exactas del primer fotograma, además de ocho pinturas de los métodos de oficio. Los 21 cortes de narrador/personajes y cinco finales también tienen sus cubiertas iniciales. El inventario reúne 95 MP4 y 92 cubiertas de carga; los tres MP4 de ambientes son exportaciones sin reproductor narrativo. El balance se presenta con contadores individuales obligatorios, sin cuadrícula. [Diseño, recursos, prompts y comprobación](continuidad_y_acciones.md).

## Campaña de siete actos

`assets/expansion/siete_actos/` incorpora cinco personajes (Valeria y las cuatro candidaturas), cada uno con tres expresiones, boca al hablar y parpadeo; cuatro fondos vacíos y cuatro ilustraciones de escena. El arte se generó con ImageGen integrado; sus prompts y referencias se conservan en esta carpeta. Los protagonistas mantienen sus 48 fotogramas anteriores.

Los actos IV–VII añaden 88 montajes de decisiones y ocho cortes del narrador, con cámara y objetos animados, carteles y cubiertas del primer fotograma. Se conserva el contexto de cada caso y las variantes de alcance o reporte rechazado. La elección activa una de las cuatro investiduras existentes o el recuento, seguida por las voces del epílogo. Son 45 combinaciones de relato, no 45 películas distintas.

El doblaje reúne 1.587 MP3 locales y ocho identidades neuronales. La ampliación tiene 967 entradas verificadas, incluyendo frases completas, fragmentos, indicadores y propagación. Son voces sintéticas. `assets/audio/siete_actos/` contiene cuatro ambientes y cuatro gestos sonoros montados a partir de las fuentes CC0 locales; el manifest enlaza su procedencia y registra sus hashes. [Guion y alcance](guion_siete_actos.md), [comprobación de voces](verificacion_voces_siete_actos.json).
