# CIVICA — Alcalde Digital

Novela visual educativa en Python y PyQt6 para Estructura de Datos II, Universidad del Norte. Su campaña completa recorre siete actos y catorce decisiones. En Ciudad Nova, las publicaciones de Civitas modifican la red social, los indicadores y la elección de cuatro candidatos ficticios. Valeria Cruz, la influencer, y las cuatro candidaturas participan en la historia con sus propias voces y expresiones.

La revisión de siete actos aprobó **304 pruebas**. [Muestra de escenas y finales, 3 min 23 s](docs/vistas/muestra_siete_actos.mp4) · [Verificación consolidada](docs/verificacion_siete_actos.json). Inicia una partida nueva para recorrer la campaña completa; los guardados anteriores conservan la campaña clásica. La muestra reúne escenas independientes y ejemplos de las cuatro victorias y del empate.

## Ejecutar en Windows

Entorno comprobado: Python 3.14.5, PyQt6 6.11.0 y Qt 6.11.0. PyQt6 es la dependencia del juego. Las herramientas opcionales de producción de voces y video tienen dependencias separadas, instaladas en `.tmp/`; no se necesitan para jugar con el paquete entregado. Las pruebas usan `unittest`, incluido en Python.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe iniciar.py
```

También se conserva `python interfaz.py` para abrir el videojuego y `python main.py` para la demostración del ABB en consola. Importar `main` ya no ejecuta la demostración.

Si Python no está en el PATH, selecciona en VS Code el intérprete instalado y ejecuta los comandos con su ruta, o utiliza `py -3.14` cuando el administrador de Python esté disponible.

```powershell
python iniciar.py --semilla 4 --sin-eventos --sin-audio --sin-limite
python -B herramientas/verificar_proyecto.py --log .tmp/verificacion_proyecto.txt
```

La semilla hace reproducibles los eventos. `--sin-eventos` desactiva los sucesos aleatorios; la comunidad sigue creciendo con la historia. La aplicación resuelve los recursos desde su ubicación, aunque el directorio de trabajo sea otro.

El verificador mantiene el progreso de lectura en memoria y libera los objetos Qt pendientes entre pruebas. `--patron test_cinematica*.py` permite revisar sólo los archivos que coincidan con ese patrón; `--log` guarda el detalle y un resumen JSON.

## Jugar

Selecciona Ciudadano o Periodista. El influencer y los candidatos pertenecen a la historia y no se pueden seleccionar. Espacio, Enter y clic revelan el texto; una interacción posterior continúa cuando termina la presentación obligatoria de la escena. Las repeticiones automáticas del teclado no saltan diálogos. Tab permite recorrer los controles y F11 alterna pantalla completa. F1 abre la ayuda.

Cada una de las catorce publicaciones recibe una sola decisión. El **ciudadano** puede compartir, escuchar al vecindario, convocar al barrio o seguir sin reenviar. La **periodista** puede contrastar fuentes, entrevistar, desmentir y denunciar, o mantener una publicación en reserva. Escuchar crea vínculos recíprocos; entrevistar abre contacto con una fuente sin certificar su testimonio; convocar alcanza tres niveles y amplifica también el daño de un rumor. Las rectificaciones se difunden antes de retirar contenido falso. Una denuncia infundada conserva la publicación y resta credibilidad. [Decisiones y efectos de cada oficio](docs/roles_y_decisiones.md).

Los actos I a III conservan colegio, cultura, parque, biblioteca, rumor y encuesta. El acto IV introduce a Valeria y un video recortado; el V lleva las preguntas del barrio a un debate con Juan Torres, Adrián Morales, Laura Ríos y Camila Vega; el VI recupera los segundos eliminados de un audio; el VII acompaña la jornada electoral. Cada caso tiene una conversación propia y tres fuentes ficticias opcionales. Los personajes recuerdan decisiones anteriores. El desenlace combina el resultado real de la elección, tres estados de la ciudad y tres arcos de Valeria: 45 combinaciones modulares, con voces de las candidaturas que no ganan. [Guion, personajes y finales](docs/guion_siete_actos.md).

La interfaz abre la campaña completa. La API `Juego(campana="clasica")` y los guardados anteriores conservan la campaña de seis casos; `Juego(campana="extendida")` usa los catorce. El modo se guarda y se sincroniza en la sala.

**Cuaderno** abre cinco secciones: Investigar, Personajes, Historial, Galería y Glosario. En la pantalla de decisión, **Examinar las fuentes** permite consultar tres documentos o testimonios ficticios por caso. Consultarlos es opcional y no aplica una decisión ni otorga puntos. Las alertas siguen su plazo mientras el cuaderno está abierto; en multijugador lo controla el servidor. La lectura y la voz de un diálogo se pausan al abrir el cuaderno y continúan al volver.

Los diálogos ofrecen **Auto** y **Saltar leído**. Auto espera a que termine la línea; Saltar leído se detiene ante texto nuevo. Ambos se desactivan al cambiar de escena y nunca deciden por el jugador. Configuración incluye una pestaña Lectura con velocidades Pausada, Normal, Ágil e Instantánea. Historial reúne los diálogos completados en la sesión. La biblioteca personal conserva las líneas leídas y los recuerdos de cada caso en `.civica/biblioteca.json`, por separado del guardado de campaña; permite volver a verlos desde la portada. La galería utiliza el fondo correspondiente a cada caso y conserva un recuerdo del cierre. El diseño clásico y su ampliación están en [docs/novela_visual.md](docs/novela_visual.md).

Después de las consecuencias se conservan el ABB y sus tres recorridos. El observatorio de Civitas muestra la red, BFS/DFS y la difusión a un ritmo fijo. Repite el recorrido después de una pausa de dos segundos; «Reducir movimiento» presenta el resultado sin animación ni repetición. «Comparar alcance» simula desde el ciudadano seleccionado sin volver a otorgar puntos. Las publicaciones retiradas conservan su historial, pero no se vuelven a difundir. La comunidad crece automáticamente desde nueve personas. En la campaña completa alcanza veinte: Valeria se incorpora al comenzar el acto IV con conexiones reales que modifican el alcance; la campaña clásica conserva sus diecinueve miembros.

Las alertas virales tienen 15 segundos desde la presentación de las opciones. Al agotar el plazo, el ciudadano sigue sin reenviar y la periodista mantiene el contenido en reserva; nunca se publica automáticamente ni se duplica una acción simultánea. El engranaje de Configuración está arriba a la derecha e incluye el Manual de usuario, accesibilidad y sonido. Ofrece paletas para deuteranopia, protanopia y tritanopia, símbolos independientes del color, contraste alto, movimiento reducido y decisiones sin límite. Permite ajustar cinco volúmenes, activar voces o silenciar todo el audio. Las señales sonoras tienen indicación visual.

Los cambios de indicadores aparecen uno a uno en el centro: al pronunciar la voz «Confianza +6», el contador muestra la transición entre sus valores efectivos. No hay lista estadística inferior ni cuadrícula final. Disminuir desinformación o conflictos se reconoce como mejora; se respetan los topes y la puntuación acumulada. Espacio, Enter, clic, Auto y Saltar leído esperan a que cada contador complete su animación. Sin voces, la secuencia visual termina todos los cambios; movimiento reducido conserva los valores sin interpolarlos, con tiempo de lectura por indicador.

El final presenta primero el epílogo dialogado de la campaña y el video de la candidatura ganadora, o del recuento si hay empate. Después muestra apoyo electoral, resultado, puntuaciones, reputación, logros e indicadores; el resumen admite desplazamiento cuando participan cuatro personas. Las 45 combinaciones narrativas usan módulos de diálogo y cinco películas de cierre, no 45 películas de presidencia. El menú «Partida» agrupa Guardar, Cargar, Reconectar (cuando hay sala) y Portada. El menú y los indicadores aparecen durante la partida y se ocultan en la portada, que ofrece Continuar partida y Multijugador. Guardar/Cargar utiliza JSON; las preferencias se conservan en `.civica/config.json`. Los guardados predeterminados se ubican en `saves/`; ambos directorios están ignorados por Git.

## Multijugador local

Abre entre dos y cuatro instancias de CIVICA. En la primera, selecciona Multijugador, elige nombre/rol y «Crear sala local». En las otras, usa «Unirse» con `127.0.0.1` y el mismo puerto (8765 por defecto). Se pueden repetir personajes para conservar de dos a cuatro participantes. El anfitrión inicia cuando hay de dos a cuatro participantes.

También puedes abrir un servidor separado:

```powershell
python -m red.servidor --puerto 8765 --campana extendida
```

El servidor conserva ABB, grafo, turnos, eventos, indicadores y puntuaciones. Una persona decide por publicación, rotando el turno. Cada participante ve los cuatro botones de su propio oficio; sólo se habilitan cuando le corresponde actuar. Los vínculos vecinales y entrevistas quedan en el grafo compartido y cambian las rutas futuras. Todos reciben el resultado y pulsan Continuar después de revisar la red; el servidor espera a todos antes de avanzar. El timeout es autoritativo. Los widgets reciben datos mediante señales Qt y las escrituras de red se procesan fuera del hilo gráfico.

Una desconexión durante la campaña pausa la sala y su cuenta regresiva. Desde la ventana del participante desconectado, «Reconectar» recupera su identidad y estado mediante un token de sesión; la campaña continúa cuando regresan todos. La ventana conserva el token en memoria y el servidor debe seguir abierto. Cerrar el servidor o el proceso anfitrión termina esa sala; no hay migración de anfitrión ni recuperación tras reiniciar el servidor. La comunidad crece automáticamente; el observatorio permite explorar y comparar, sin editor manual de topología. La sala escucha en localhost por defecto; la publicación en Internet y la configuración LAN no se realizaron.

## Organización

- `estructuras/`: ABB original y grafo dirigido propio por adyacencias; sin NetworkX.
- `models/`: publicaciones, ciudadanos, jugadores, candidatos y ciudad.
- `juego/partida.py`: progresión y estado; conserva `Juego` importable desde `interfaz`.
- `juego/propagacion.py`: resultados de BFS sin dependencias gráficas.
- `juego/decisiones.py`, `eventos.py`, `elecciones.py`, `historia.py`: reglas, variación y relato.
- `juego/campana_extendida.py`: ocho publicaciones nuevas, actos IV–VII, personajes, fuentes, reacciones y epílogos finitos.
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

El doblaje utiliza 1.587 MP3 y ocho identidades neuronales locales: Gonzalo para el ciudadano, Salomé para la periodista, Jorge para el narrador, Dalia para Valeria, Álvaro para Juan, Tomás para Adrián, Elvira para Laura y Catalina para Camila. Son voces sintéticas neuronales. El juego no usa las voces de Windows ni necesita Internet para reproducirlas. Las tomas cubren las conversaciones, decisiones de los dos oficios, recuerdos, reacciones y variantes de resultados, y la energía de la voz mueve la boca del personaje. Las cifras disparan su contador al comenzar la reproducción efectiva de cada toma. La música y el ambiente bajan mientras habla. Auto espera a que termine la toma; Cuaderno y Configuración pausan la lectura y recuperan la línea vigente. En Sonido y voces puedes probar a cada intérprete. Un guion importado completamente nuevo requiere producir sus clips; sus subtítulos continúan disponibles. El catálogo completo de la ampliación y su verificación se generan con `python -B herramientas/producir_voces_siete_actos.py --verificar`. Detalles: [assets/audio/voces/LEEME.md](assets/audio/voces/LEEME.md).

La fuente Atkinson Hyperlegible viene incluida en `assets/fuentes/` con su licencia SIL OFL. Los diálogos tienen texto mayor, nombre centrado en la cartela y escritura más pausada con pausas de puntuación. Las transiciones revelan la escena desde negro y respetan movimiento reducido. El teléfono y las decisiones comparten una tarjeta social con autor, avatar, imagen, navegación de Civitas y contadores de la partida.

La expansión sonora prioriza ocho ambientes de 45 segundos con grabaciones de campo, dieciséis efectos de objetos y pasos, y tres pistas musicales instrumentales de aproximadamente un minuto. Los recursos CC0 incluyen créditos, licencias y procesamiento en `assets/audio/expansion/`; los diecisiete WAV sintetizados originales quedan como respaldo. El café, la calle, la oficina, la lluvia y la noche tienen mezclas distintas. Procedencia: [docs/audio_ambiental.md](docs/audio_ambiental.md).

Los fondos tienen movimiento durante la partida: fuente, hojas, aves, vapor, luces, reflejos y lluvia sobre los cristales. Tres escenarios nuevos representan parque, café lluvioso y plaza nocturna. Los protagonistas disponen de cuatro atlas nuevos con 48 fotogramas y siete emociones, con respiración, parpadeo y boca por nivel de voz. Configuración → Escenas permite activar fondos y personajes por separado; Reducir movimiento deja la escena quieta. El motor sólo anima widgets visibles. Hay once GIF y tres MP4 exportados en `assets/expansion/movimiento/`, además del renderizado a resolución de pantalla. Diseño y recursos: [docs/expansion_audiovisual.md](docs/expansion_audiovisual.md).

El narrador activa nueve videos contextuales dentro de la partida: colegio, mensajes del barrio, libreta, mapa, libro, lluvia y víspera electoral. Son 108 segundos distintos en MP4 720p/24 fps, con cámara, documentos y objetos animados. Catorce efectos acompañan decisiones, consecuencias, fuentes y final. Los cortes se pausan con el cuaderno, descargan el decodificador al salir y conservan un cartel quieto con movimiento reducido. [Muestra con voz e interfaz](docs/vistas/cinematicas_narradas.mp4), [secuencias, recursos y producción](docs/cinematicas_narrativas.md).

Ahora también hay doce cortes para las intervenciones de ciudadano y periodista y cinco videos de desenlace: cuatro investiduras de alcaldía y un recuento para empates. Las elecciones normalizan las oportunidades de cada candidatura y consideran exposición, correcciones y contactos reales. Los cuatro candidatos pueden ganar en solitario y en multijugador; repetir o cargar la misma partida conserva su resultado. [Cinemáticas de personajes](docs/cinematicas_personajes.md), [elecciones y finales](docs/elecciones_y_finales.md), [muestra de roles, contadores y desenlaces](docs/vistas/muestra_impacto_roles_finales.mp4).

Las decisiones se muestran en botones de una sola línea. A los 66 montajes propios de los seis casos originales se añaden 88 de los ocho casos nuevos, además de ocho cortes contextuales del narrador. Convocar muestra la actividad vecinal; un alcance nulo o reducido usa su variante y un reporte rechazado conserva el contenido. La carga usa el primer fotograma real; pausar conserva el último plano, evitando el salto de una imagen adelantada al inicio del montaje. El estudio de Valeria, el foro, la redacción y la plaza electoral tienen fondos, escenas ilustradas y mezclas de ambiente propias. [Muestra de los siete actos](docs/vistas/muestra_siete_actos.mp4), [expansión y recursos](docs/expansion_audiovisual.md), [continuidad de las acciones](docs/continuidad_y_acciones.md).

Los fondos nuevos del café y de investigación están limpios para superponer los protagonistas sin duplicarlos. Los sprites, candidatos y elementos de interfaz están instalados en `assets/rediseno/`; los archivos anteriores se conservan como respaldo. Inventario en [docs/recursos.md](docs/recursos.md).

## Verificación y límites

La suite verifica ABB, BFS/DFS, cambios de topología, decisiones únicas, guardados, eventos reproducibles, finales, timeout y sockets con dos/tres/cuatro clientes. Completa campañas a través de las escenas con cada rol y una campaña sincronizada con cuatro ventanas Qt. Comprueba desconexión/reconexión y reproducción de audio. Renderiza pantallas a 1920×1080, 1600×900 y 1366×768 en `.tmp/capturas/`.

Se revisaron capturas offscreen y una interacción de decisión/consecuencia en la ventana real de Windows. Las campañas completas automatizadas usan Qt offscreen; no se atribuye a una persona una sesión completa ni una escucha que no realizó. Consulta [docs/estado.md](docs/estado.md) para la matriz de cumplimiento, [docs/verificacion.md](docs/verificacion.md) para la evidencia y [docs/sustentacion.md](docs/sustentacion.md) para demostrar el proyecto.
