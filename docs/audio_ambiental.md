# Ambientación de CIVICA

La expansión incorpora ocho paisajes sonoros de 45 segundos, dieciséis efectos de escena y tres pistas musicales instrumentales de aproximadamente un minuto. Se entregan como WAV estéreo PCM de 16 bits a 32 kHz, listos para Qt Multimedia y sin necesitar conexión durante la partida. Los ambientes y foley proceden de páginas individuales de BigSoundBank con licencia CC0 explícita; su autor, URL, fecha de verificación y hash se conservan en `assets/audio/expansion/licencias.json`. La música tiene un manifiesto independiente, `licencias_musica.json`.

## Paisajes sonoros

| Archivo en `assets/audio/expansion/ambientes/` | Contenido y perspectiva |
| --- | --- |
| `cafe.wav` | Café de fondo, murmullo distante, cucharilla y vajilla con posiciones diferentes. |
| `plaza.wav` | Actividad de una plaza peatonal, aire y aves. |
| `calle.wav` | Calle peatonal con actividad urbana y aves lejanas. |
| `oficina.wav` | Ventilación de ordenador, escritura con pausas y movimiento de documentos. |
| `lluvia.wav` | Grabación de lluvia regular sobre una superficie de tela en exterior. |
| `noche.wav` | Insectos nocturnos, viento entre vegetación y tráfico muy lejano. |
| `viento.wav` | Viento real en hojas y copas de árboles. |
| `interior_lluvia.wav` | Lluvia amortiguada como tras una ventana y ventilación interior tenue. |

Se utilizan grabaciones ambientales reales y montajes de objetos grabados. La perspectiva de lluvia interior se construye filtrando la grabación exterior: no se presenta como una toma independiente. Las grabaciones de origen fueron realizadas en Francia; sirven para el pueblo ficticio del juego y no se identifican como grabaciones de Colombia. El ambiente de oficina es un montaje de ventilación, teclado y papeles, con pausas, en lugar de una grabación continua de una oficina ocupada.

Los murmullos de café, plaza y calle se filtran y mezclan con otras posiciones temporales de la misma toma para mantenerlos en un plano lejano. No se emplean como diálogo ni como voces de personajes. Para primer plano narrativo se mantienen separados los canales de voces, música y ambiente.

Cada bucle tiene un empalme de dos segundos que solapa el final con el principio. Así no necesita detenerse ni bajar a silencio en cada repetición. Los archivos ya tienen nivel equilibrado y margen de pico; el gestor puede atenuarlos durante el diálogo y aplicar fundidos al cambiar de escena.

## Efectos

Los archivos están en `assets/audio/expansion/efectos/`:

| Uso | Nombres disponibles |
| --- | --- |
| Interfaz física y evidencia | `clic_real`, `pagina`, `papeles`, `lapiz`, `teclado` |
| Entrada y desplazamiento | `pasos_madera`, `pasos_calle`, `puerta_abrir`, `puerta_cerrar`, `llamada_puerta` |
| Café | `taza`, `cucharilla`, `cafetera` |
| Reacción y descubrimiento | `suspiro`, `hallazgo`, `notificacion_suave` |

`taza` es un detalle de cucharilla apoyándose en un plato, no una taza golpeada sintéticamente. `hallazgo` procede de una nota de metalófono grabada. `suspiro` es una respiración humana sin palabras. `notificacion_suave` es la única fuente de este paquete descrita por su autor como diseño sonoro electrónico (Prologue de Cubase); se conserva esa distinción en el manifiesto. Los demás efectos proceden de objetos y acciones grabados.

Para mantener la escena legible, los foley deben seguir acciones visibles: página al abrir el cuaderno, teclado al consultar información, vajilla en el café, pasos y puerta al entrar. Los efectos largos no necesitan dispararse al pasar cada línea de diálogo. El ambiente continuo ya contiene pequeños acontecimientos a distintas distancias.

## Música instrumental

Las tres composiciones fueron publicadas por **The Cynic Project / cynicmusic** en OpenGameArt con licencia CC0 en la ficha individual. Son obras musicales completas con piano, guitarra, cuerdas y capas ambientales; no se afirma que procedan de una sesión acústica grabada en vivo.

| Archivo en `assets/audio/expansion/musica/` | Composición original y uso |
| --- | --- |
| `ciudad.wav` | [Calm Piano 1 (Vaporware)](https://opengameart.org/content/calm-piano-1-vaporware): piano cálido para ciudad y conversaciones tranquilas. |
| `investigacion.wav` | [Dark Forest Theme](https://opengameart.org/content/dark-forest-theme): guitarra acústica y cuerdas para investigación y misterio. |
| `eleccion.wav` | [Sirens in Darkness](https://opengameart.org/content/sirens-in-darkness): piano y capas ambientales para decisiones y reflexión nocturna. |

Los originales MP3 se conservan completos en `.tmp/audio_fuentes/musica_*.mp3`. Para la partida se seleccionan extractos de 56–66 segundos; la herramienta busca coincidencias de armonía y nivel en el retorno y aplica un empalme circular de dos segundos. El manifiesto musical registra el segundo de inicio de cada recorte y la duración exacta. No se añaden voces ni se modifica la melodía.

El compositor solicita el crédito **The Cynic Project / cynicmusic.com / pixelsphere.org**. Se incluye en `CREDITOS.md` aunque las fichas identifican su licencia como CC0. Sólo se utilizan los tres archivos específicos publicados en esas páginas, sin extender esa licencia a otras obras de su sitio web.

## Reproducción y regeneración

El juego utiliza los WAV entregados sin instalar bibliotecas nuevas. Las dependencias siguientes son sólo para la herramienta de producción:

```powershell
python -m pip install --target .tmp/audio_deps numpy imageio-ffmpeg
python -B herramientas/preparar_ambientes.py --descargar
python -B herramientas/preparar_ambientes.py --musica --descargar
```

La primera ejecución descarga los MP3 oficiales, comprueba el texto de licencia y registra al autor real de cada ficha. Los originales y sus metadatos se guardan en `.tmp/audio_fuentes/`, excluida de Git. Para volver a mezclar desde esa caché basta con:

```powershell
python -B herramientas/preparar_ambientes.py
python -B herramientas/preparar_ambientes.py --musica
```

Para verificar los archivos entregados sin red ni regenerarlos:

```powershell
python -B herramientas/preparar_ambientes.py --verificar
```

La comprobación valida formato, duración, hashes, nivel no silencioso, ausencia de saturación, continuidad del empalme y tamaño total inferior a 100 MiB. El manifiesto enumera también las operaciones aplicadas a cada recurso.

## Licencias y crédito

Consultar [el crédito del paquete](../assets/audio/expansion/CREDITOS.md) y el [manifiesto por fuente y archivo](../assets/audio/expansion/licencias.json). Las páginas individuales confirman CC0; la [licencia del proveedor](https://bigsoundbank.com/licenses.html) permite editar, mezclar, distribuir y usar comercialmente esos materiales. La [dedicación CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) no exige atribución; el proyecto conserva los créditos como parte de la documentación de sus assets.
