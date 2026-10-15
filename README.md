# CIVICA — Alcalde Digital

Novela visual educativa en Python y PyQt6 para Estructura de Datos II, Universidad del Norte. En Ciudad Nova, las decisiones sobre publicaciones de Civitas modifican la red social, los indicadores y la elección de cuatro candidatos ficticios.

## Ejecutar en Windows

Entorno comprobado: Python 3.14.5, PyQt6 6.11.0 y Qt 6.11.0. No se instalaron dependencias durante este desarrollo; PyQt6 ya estaba disponible. Las pruebas usan `unittest`, incluido en Python.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe iniciar.py
```

También se conserva `python interfaz.py` para abrir el videojuego y `python main.py` para la demostración del ABB en consola. Importar `main` ya no ejecuta la demostración.

Si Python no está en el PATH, selecciona en VS Code el intérprete instalado y ejecuta los comandos con su ruta, o utiliza `py -3.14` cuando el administrador de Python esté disponible.

```powershell
python iniciar.py --semilla 4 --sin-eventos --sin-audio --sin-limite
python -B -m unittest discover -v
```

La semilla hace reproducibles los eventos. `--sin-eventos` desactiva los sucesos aleatorios; la comunidad sigue creciendo con la historia. La aplicación resuelve los recursos desde su ubicación, aunque el directorio de trabajo sea otro.

## Jugar

Selecciona Ciudadano o Periodista. El influencer y los candidatos pertenecen a la historia y no se pueden seleccionar. Espacio, Enter y clic revelan el texto; una interacción posterior continúa. Las repeticiones automáticas del teclado no saltan diálogos. Tab permite recorrer los controles y F11 alterna pantalla completa. F1 abre la ayuda.

Cada una de las seis publicaciones originales recibe una sola decisión. Compartir calcula receptores; verificar contrasta la noticia y puede difundir una corrección; ignorar no propaga; reportar retira contenido falso o dañino. Los reportes infundados sobre noticias verdaderas reciben una penalización y conservan la publicación.

Después de las consecuencias se conservan el ABB y sus tres recorridos. El observatorio de Civitas muestra la red, BFS/DFS y la difusión a un ritmo fijo. Repite el recorrido después de una pausa de dos segundos; «Reducir movimiento» presenta el resultado sin animación ni repetición. «Comparar alcance» simula desde el ciudadano seleccionado sin volver a otorgar puntos. Las publicaciones retiradas conservan su historial, pero no se vuelven a difundir. La comunidad incorpora dos ciudadanos y sus conexiones con cada publicación posterior a la primera: pasa de nueve a diecinueve miembros sin edición manual.

Las alertas virales tienen 15 segundos desde la presentación de las opciones. Agotar el tiempo equivale a ignorar y no duplica una acción simultánea. El engranaje de Configuración está arriba a la derecha e incluye el Manual de usuario, accesibilidad y sonido. Ofrece paletas para deuteranopia, protanopia y tritanopia, símbolos independientes del color, contraste alto, movimiento reducido y decisiones sin límite. Permite ajustar cinco volúmenes, activar voces o silenciar todo el audio. Las señales sonoras tienen indicación visual.

El final presenta apoyo electoral, resultado o empate, puntuaciones, reputación, logros e indicadores. Incluye un epílogo basado en el ganador, su propuesta y el historial real; el resumen admite desplazamiento cuando participan cuatro personas. El menú «Partida» agrupa Guardar, Cargar, Reconectar (cuando hay sala) y Portada. El menú y los indicadores aparecen durante la partida y se ocultan en la portada, que ofrece Continuar partida y Multijugador. Guardar/Cargar utiliza JSON; las preferencias se conservan en `.civica/config.json`. Los guardados predeterminados se ubican en `saves/`; ambos directorios están ignorados por Git.

## Multijugador local

Abre entre dos y cuatro instancias de CIVICA. En la primera, selecciona Multijugador, elige nombre/rol y «Crear sala local». En las otras, usa «Unirse» con `127.0.0.1` y el mismo puerto (8765 por defecto). Se pueden repetir personajes para conservar de dos a cuatro participantes. El anfitrión inicia cuando hay de dos a cuatro participantes.

También puedes abrir un servidor separado:

```powershell
python -m red.servidor --puerto 8765
```

El servidor conserva ABB, grafo, turnos, eventos, indicadores y puntuaciones. Una persona decide por publicación, rotando el turno. Todos reciben el resultado y pulsan Continuar después de revisar la red; el servidor espera a todos antes de avanzar. El timeout es autoritativo. Los widgets reciben datos mediante señales Qt y las escrituras de red se procesan fuera del hilo gráfico.

Una desconexión durante la campaña pausa la sala y su cuenta regresiva. Desde la ventana del participante desconectado, «Reconectar» recupera su identidad y estado mediante un token de sesión; la campaña continúa cuando regresan todos. La ventana conserva el token en memoria y el servidor debe seguir abierto. Cerrar el servidor o el proceso anfitrión termina esa sala; no hay migración de anfitrión ni recuperación tras reiniciar el servidor. La comunidad crece automáticamente; el observatorio permite explorar y comparar, sin editor manual de topología. La sala escucha en localhost por defecto; la publicación en Internet y la configuración LAN no se realizaron.

## Organización

- `estructuras/`: ABB original y grafo dirigido propio por adyacencias; sin NetworkX.
- `models/`: publicaciones, ciudadanos, jugadores, candidatos y ciudad.
- `juego/partida.py`: progresión y estado; conserva `Juego` importable desde `interfaz`.
- `juego/propagacion.py`: resultados de BFS sin dependencias gráficas.
- `juego/decisiones.py`, `eventos.py`, `elecciones.py`, `historia.py`: reglas, variación y relato.
- `interfaz.py`: escenas originales y ventana. `paneles.py`: observatorio, roles, ayuda y opciones.
- `audio/gestor_audio.py`: música, ambiente, efectos, mezcla y fundidos.
- `red/`: protocolo JSON delimitado, servidor y cliente.
- `recursos.py`: resolución y caché de imágenes; `data/publicaciones.json`: seis publicaciones originales.
- `tests/`: estructuras, partida, sockets y ventanas Qt en modo offscreen.
- `docs/`: reglas, cumplimiento, recursos y sustentación.

La carpeta `interfaz/` original permanece reservada sin `__init__.py`, evitando ocultar `interfaz.py`. Los módulos vacíos heredados que no tienen una responsabilidad activa no se presentan como funcionalidad terminada.

## Rediseño visual

El juego incorpora imágenes generadas para CIVICA: fondos, protagonistas con expresiones, retratos, avatares, miniaturas de publicaciones y una piel ilustrada de botones, paneles, diálogos e iconos. El observatorio presenta un selector de origen, BFS, DFS y comparación de alcance junto a la red; el HUD separa los siete indicadores. Los originales y el audio se conservan. Detalles y manifiesto: [docs/rediseno_visual.md](docs/rediseno_visual.md).

## Audio y recursos

Los diálogos actuales y el narrador usan síntesis de voz local en español mediante Qt TextToSpeech. En el Windows comprobado, Pablo interpreta al ciudadano, Laura a la periodista y Helena al narrador, con ritmos y tonos diferentes. La música baja mientras hablan; cambiar de diálogo o escena cancela la lectura anterior. Las voces disponibles dependen del equipo: si no existe una voz española, la historia y los subtítulos siguen funcionando y Configuración indica su disponibilidad. No se descargan voces durante el juego. Diagnóstico y prueba de reproducción: `python herramientas/comprobar_voces.py --reproducir`.

La fuente Atkinson Hyperlegible viene incluida en `assets/fuentes/` con su licencia SIL OFL. Los diálogos tienen texto mayor, nombre centrado en la cartela y escritura más pausada con pausas de puntuación. Las transiciones revelan la escena desde negro y respetan movimiento reducido. El teléfono y las decisiones comparten una tarjeta social con autor, avatar, imagen, navegación de Civitas y contadores de la partida.

Se conservaron las ilustraciones originales. Se añadieron once efectos WAV, tres piezas musicales y tres ambientes originales de plaza, café y oficina, sintetizados mediante `herramientas/generar_audio.py`: diecisiete archivos sin muestras de terceros. Las piezas duran entre 20 y 27 segundos e incluyen melodía, acordes y bajo; los ambientes duran 18 segundos. Qt Multimedia reprodujo la música y se comprobó avance de posición, cambios rápidos de pista, volumen y silencio. La valoración del timbre y la mezcla por una persona es una revisión artística adicional.

Los fondos nuevos del café y de investigación están limpios para superponer los protagonistas sin duplicarlos. Los sprites, candidatos y elementos de interfaz están instalados en `assets/rediseno/`; los archivos anteriores se conservan como respaldo. Inventario en [docs/recursos.md](docs/recursos.md).

## Verificación y límites

La suite verifica ABB, BFS/DFS, cambios de topología, decisiones únicas, guardados, eventos reproducibles, finales, timeout y sockets con dos/tres/cuatro clientes. Completa campañas a través de las escenas con cada rol y una campaña sincronizada con cuatro ventanas Qt. Comprueba desconexión/reconexión y reproducción de audio. Renderiza pantallas a 1920×1080, 1600×900 y 1366×768 en `.tmp/capturas/`.

Se revisaron capturas offscreen y una interacción de decisión/consecuencia en la ventana real de Windows. Las campañas completas automatizadas usan Qt offscreen; no se atribuye a una persona una sesión completa ni una escucha que no realizó. Consulta [docs/estado.md](docs/estado.md) para la matriz de cumplimiento, [docs/verificacion.md](docs/verificacion.md) para la evidencia y [docs/sustentacion.md](docs/sustentacion.md) para demostrar el proyecto.
