# Verificación de la implementación

## Campaña completa de siete actos · 24 de octubre de 2026

La revisión actual aprobó **304 pruebas**, sin fallas, errores ni omisiones. Se ejecutó con `python -B herramientas/verificar_proyecto.py --log .tmp/verificacion_siete_actos_final.txt`; el resumen permanente está en [verificacion_suite_siete_actos.json](verificacion_suite_siete_actos.json). Las cifras de las secciones anteriores a esta ampliación se conservan como historial.

La campaña abre catorce casos en siete actos; una partida clásica anterior sigue teniendo seis. La prueba TCP con dos, tres y cuatro participantes recorre los catorce turnos. Cuatro ventanas Qt completaron catorce decisiones y catorce balances por cliente, esperaron la barrera de lectura y presentaron nueve líneas de epílogo antes del panel final. [Evidencia multijugador](verificacion_red_ui_siete_actos.json). La auditoría conserva rutas reales de victoria para cada candidatura y un empate, con ambos oficios, además de 768 campañas muestreadas; no pretende enumerar todas las secuencias de catorce decisiones.

Los 88 montajes de decisiones y ocho cortes narrativos nuevos se decodificaron completos. Los **96 transportes Qt reales** comprobaron cubierta preparada, primer plano, pausa y reanudación. Tras corregir tipografía y rótulos se repitieron los recursos afectados, y los hashes finales corresponden a los archivos entregados. [Comprobación de videos](verificacion_inicios_siete_actos.json). Los ocho botones de los nuevos casos se ejecutaron con voz y video reales: **800 pulsaciones anticipadas bloqueadas** y avance únicamente después del final de cada MP4. [Evidencia de acciones](verificacion_acciones_ui_siete_actos.json).

El doblaje cuenta con ocho identidades y 1.587 MP3; las 967 entradas de la ampliación, incluyendo fragmentos e indicadores, tienen texto, intérprete, duración y señal comprobados. [Voces](verificacion_voces_siete_actos.json). Los 25 sprites, cuatro fondos, cuatro ilustraciones y ocho pistas nuevas de ambiente/foley tienen verificaciones propias. Se revisaron diez capturas de reparto en 1366×768 y 1100×700 con tres actores, encuadre de busto y texto legible. [Arte](verificacion_arte_siete_actos.json), [encuadre](verificacion_reparto_siete_actos.json).

La muestra [muestra_siete_actos.mp4](vistas/muestra_siete_actos.mp4) usa widgets y compositores del proyecto por reloj, voces neuronales completas y ambientes locales. Es una exportación de composición; las pruebas independientes anteriores verifican la reproducción del decodificador. Las voces son sintéticas y los videos son montajes ilustrados con cámara y objetos animados. La valoración humana de interpretación, ritmo y comodidad sigue siendo una tarea de escucha y juego con personas.

## Continuidad, decisiones y contadores obligatorios · 24 de octubre de 2026

La suite completa aprobó **272 pruebas**, sin fallas, errores ni omisiones, en **159,703 s**. Comando: `python -B herramientas/verificar_proyecto.py --log .tmp/verificacion_continuidad_acciones.txt`. Registro completo en `.tmp/verificacion_continuidad_acciones.txt`; [resumen persistido](verificacion_suite_continuidad_acciones.json). Incluye campañas por ambos oficios y cuatro ventanas sincronizadas, guardados, ABB, grafos, red, voces, finales y regresiones audiovisuales.

La pantalla de balance presenta un indicador central cada vez y conserva el último al terminar; ya no muestra una cuadrícula. Clic, Espacio, Enter, Auto y «Saltar leído» no omiten contadores ni dejan un avance pendiente. La terminación anticipada o cancelación de la voz deja que la cola visual complete cada cambio. La pausa y el movimiento reducido conservan la secuencia.

La interfaz prepara el primer fotograma exacto antes de las esperas de entrada y arranca el video al comenzar la voz. Pausar conserva el plano actual; los callbacks de una fuente anterior no pueden reemplazar el video nuevo. Las ocho decisiones tienen etiquetas breves de una línea, con explicación accesible y al pasar el cursor. Su escena de acción normal debe alcanzar el final real del MP4 antes de continuar; la imagen estática por movimiento reducido y los errores de reproducción permiten seguir jugando.

Se normaliza la geometría del marco al terminar la entrada: un cambio de altura del HUD o de la ventana no separa nombre, texto y pista de su panel. Manual, Guardar, Cargar y sala multijugador pausan la presentación; una partida nueva no recupera una locución de la anterior. Hay regresiones de resize durante la entrada y de contadores congelados detrás de estos diálogos.

Las regresiones comprueban los ocho botones, el primer plano preparado, clics repetidos, Auto, final de transporte, error, movimiento reducido y casos importados. El balance volvió a reproducirse con voz real: seis segmentos completos, 180 pulsaciones anticipadas ignoradas, confianza **50 → 56** y desinformación **9 → 1**, sin texto estadístico en el panel, cambios de partida ni escritura en los archivos personales. [Evidencia de voz y UI actual](verificacion_balance_audio.json).

Se corrigieron dos fallos de cierre detectados por la suite: filtros de ventana que recibían eventos durante la recolección de objetos parcialmente liberados y transportes de audio que conservaban sus fuentes. Las tres capas retiran sus filtros al detenerse; el cierre total descarga voz, música y ambiente. El caso que bloqueaba `gc.collect()` terminó con 27 pruebas correctas tras la corrección, y la limpieza problemática tardó 113 ms. [Comparación antes/después](verificacion_cierre_audio.json).

Los **66 MP4 nuevos** se decodificaron completos. Las **92 cubiertas** de escenas y finales coinciden exactamente con el primer fotograma; los **92 transportes Qt** fueron comprobados. Ocho decisiones con voces y videos reales ignoraron 800 pulsaciones y sólo permitieron avanzar después de EndOfMedia a 9000 ms. [Informe real](verificacion_continuidad_acciones.json), [diseño y recursos](continuidad_y_acciones.md). La [muestra actual de 118,375 s](vistas/muestra_acciones_obligatorias.mp4) contiene las ocho acciones y dos balances íntegros, exportados con widgets y compositor instalados; imagen y audio se decodificaron completos, con pico −5,3 dB. Las muestras de etapas anteriores conservan el aspecto que tenían al producirse.

## Roles, balance y desenlaces · etapa anterior

La suite completa aprobó **239 pruebas**, sin fallas, errores ni omisiones, en **164,046 s**. Registro: `.tmp/verificacion_roles_impacto_finales.txt`; [resumen verificable](verificacion_roles_impacto_finales.json). Se corrigieron la pérdida de escenas al minimizar, el reloj detenido del balance sin voz al cerrar el cuaderno, la narración iniciada por timeout minimizado y la lectura que continuaba durante una interrupción de sala. Hay regresiones específicas para los cuatro casos.

Se reprodujo el balance completo con GestorAudio real: seis segmentos, cada cifra en PlayingState activa su tarjeta correcta, el contador de confianza recorre 50 → 55 → 56 y los subtítulos estadísticos permanecen ocultos. El juego y los archivos personales no cambian durante la presentación. [Evidencia de voz y UI](verificacion_balance_audio.json).

La auditoría electoral cubre **49.152 campañas**, con cuatro ganadores alcanzables también en multijugador mixto, y guardado/recarga deterministas. Las 16 combinaciones de participante/turno muestran sus propias opciones; sólo se habilita el turno activo. El grafo conserva las conexiones reales de conversaciones y entrevistas. Los 21 cortes y cinco videos finales se comprobaron con decodificador real. [Elecciones](verificacion_elecciones.json), [cierres de finales](verificacion_cierres_finales.json), [muestra de 68,25 s](vistas/muestra_impacto_roles_finales.mp4), [diseño y recursos](impacto_roles_y_finales.md).

Las secciones siguientes conservan la evidencia de las etapas previas.

## Cortos narrativos · verificación final del 24 de octubre de 2026

La ejecución final completa aprobó **177 pruebas en 111,761 segundos**, con cero fallas, errores u omisiones. Comando reproducible: `python -B herramientas/verificar_proyecto.py --log .tmp/verificacion_proyecto.txt`. El ejecutor mantiene el progreso de lectura en memoria y procesa las destrucciones diferidas de Qt entre pruebas.

Los nueve MP4 contextuales se decodificaron completos: 108 segundos, 2.592 fotogramas, 1280×720/24 fps. Dentro de VentanaPrincipal se verificaron fotogramas de video a los cinco segundos, cambio efectivo de imagen, composición con subtítulos, pausa/reanudación, liberación de fuentes, cartel con movimiento reducido y regreso de actores. El contraste medio RGB entre la captura integrada y el fotograma esperado fue inferior a 1,77/255 en el área comprobada. También pasaron 24 cierres reales: doce durante la carga y doce durante reproducción.

Se corrigieron la superficie nativa que no compartía composición con los widgets y el orden de destrucción del reproductor/sink, incluida una llamada `lower()` que alteraba ese orden. Se añadieron regresiones de composición y cierre tras el primer fotograma. El fondo por capas se suspende mientras el corte lo cubre, y los títulos propios del video evitan la duplicación de cartelas.

La [muestra narrada](vistas/cinematicas_narradas.mp4) dura 108 segundos y contiene H.264 720p/24 fps y AAC estéreo a 48 kHz. Se comprobó su decodificación completa y audio no nulo (media −24,1 dB, máximo −4,6 dB); es una exportación de revisión, sin atribuir una escucha o campaña humana. [Resultados verificables](verificacion_cinematicas.json), [diseño, recursos y prompts](cinematicas_narrativas.md).

## Expansión audiovisual · 24 de octubre de 2026

Primera ampliación audiovisual: **139 pruebas correctas en 94,949 segundos**, en el mismo Python 3.14.5/PyQt6 6.11.0/Qt 6.11.0. Registro: `.tmp/verificacion_audiovisual_2026-10-24.txt`. La biblioteca personal se sustituye por una instancia en memoria durante las campañas de prueba. Se conservaron decisiones, guardados, ABB, BFS/DFS, timeout, reconexión y campañas sincronizadas de dos a cuatro jugadores.

La ampliación incorpora pruebas de fondos vivos, atlas con 24 celdas por protagonista, bocas por nivel, parpadeo, pausas y movimiento reducido; cobertura del doblaje en guion/eventos/emisores y cifras; y regresiones de Configuración, Cuaderno y Auto durante la voz. Se verificó reproducción real de las tres identidades neuronales, cancelación, silencio y una toma compuesta sin emitir un final intermedio. La auditoría de 300 campañas con eventos comprobó cobertura de 14.106 líneas.

Se decodificaron completos los once GIF y tres MP4, y se verificaron 27 WAV de expansión. Las dieciocho capturas de los seis escenarios en 1100×700, 1366×768 y 1920×1080 están en `.tmp/capturas_audiovisual/`. Se corrigió la superposición de las barras con las cabezas y se regeneraron las capturas y la muestra. El MP4 de muestra tiene imagen H.264 1280×720 a 24 FPS y audio AAC; se comprobó sonido presente y pico inferior a 0 dBFS. La revisión es de widgets Qt y archivos reproducidos; no se atribuye a una persona una escucha artística ni una campaña completa.

Los recursos, su procedencia, prompts y límites de producción están en [expansion_audiovisual.md](expansion_audiovisual.md). La partida usa voces locales y capas animadas; no requiere Internet ni herramientas de generación al jugar.

## Ampliación de novela visual anterior · 24 de octubre de 2026

Resultado completo más reciente: **110 pruebas correctas en 88,249 segundos**, Python 3.14.5, PyQt6 6.11.0 y Qt 6.11.0. Registro UTF-8: `.tmp/verificacion_novela.txt`. La ejecución usa `unittest` con descubrimiento de `tests/`, ruta absoluta del proyecto y `BibliotecaLectura(None)` sustituida mediante `unittest.mock.patch`, para que las campañas automatizadas no desbloqueen la biblioteca personal. La prueba que cambia de directorio y las campañas sincronizadas con cuatro ventanas también terminaron correctamente. Se corrigió la presencia de los protagonistas durante las nuevas intervenciones del narrador y se repitió la suite completa.

Se añadieron 19 pruebas: diez comprueban conversaciones, reacciones, destinatarios reales, alcance cero, correcciones, opinión, epílogos y reconstrucción del relato desde guardados; nueve comprueban biblioteca persistida, archivos inválidos, lectura parcial/completa, salto detenido ante texto nuevo, avance automático detenido en decisiones, lectura instantánea, pausa del cuaderno, consulta sin cambios de puntuación y timeout con decisión única. Las pruebas de presentación existentes también verificaron el ajuste de los nuevos textos en las tres resoluciones.

`python -B herramientas/capturar_novela.py` genera quince capturas de diálogos, decisiones, fuentes, personajes y galería en 1100×700, 1366×768 y 1920×1080. Ubicación: `.tmp/capturas_novela/`. Las capturas no modifican preferencias ni biblioteca personal. Se revisaron las pantallas nuevas y se corrigieron el fondo blanco del área desplazable, las rutas del arte, los controles de lectura recortados y la superposición del turno con la publicación en la ventana pequeña. La revisión utiliza widgets Qt offscreen, sin atribuir una campaña humana o una valoración artística a la profesora.

La campaña conserva las seis publicaciones y las reglas de ABB/grafo. El relato se ramifica y converge según el historial; no se añadieron rutas extensas independientes. La galería reutiliza los fondos existentes. Los documentos del cuaderno son ficción interna; orientan la investigación sin cuestionarios ni puntos por abrir fuentes. Diseño y mapa: [novela_visual.md](novela_visual.md).

## Revisión anterior · 14 de octubre de 2026

Comprobación realizada el 14 de octubre de 2026 en la rama `desarrollo/segunda-entrega-grafos`. No se hicieron commits, pushes, cambios de autoría ni operaciones destructivas de Git. No se instalaron paquetes en esa revisión.

## Entorno y resultado

- Python 3.14.5, PyQt6 6.11.0 y Qt 6.11.0.
- Comando: `python -B -m unittest discover -v`, usando la ruta del intérprete instalado cuando no estaba disponible en PATH.
- Última ejecución: **74 pruebas, todas correctas**, 45,342 segundos. Registro: `.tmp/verificacion_escalado.txt`.
- Los fuentes Python se analizaron sintácticamente sin generar nuevos pyc.
- Se comprobó arranque desde otro directorio y que importar la demostración no la ejecuta.

## Evidencia funcional

| Bloque | Verificado |
|---|---|
| ABB | Inserción, duplicados, búsquedas, recorridos, vacío y eliminaciones de hoja/un hijo/dos hijos/raíz |
| Grafo | Orden BFS/DFS, ciclo, aislado, dirección, componentes débiles, grados, rutas, edición y errores sin mutación parcial |
| Propagación | Consulta del ABB, alcance único, niveles y cambio por topología; rechazo después de retirar una publicación |
| Partida | Seis publicaciones sin saltos, decisión única, reportes fundados/infundados, opiniones y rangos; selección limitada a ciudadano/periodista en interfaz, partida y servidor |
| Estado | Historial, indicadores, logros, guardado JSON, restauración y semilla |
| Elecciones | Resultados distintos según decisiones y apoyo del rol Candidato |
| Qt | Escritura/revelado, transición protegida, cancelación de temporizadores, resize y F11; campaña completa por las escenas con cada uno de los dos personajes seleccionables |
| Red | Campañas TCP completas con 2, 3 y 4 clientes; mismos estados; acciones inválidas/repetidas rechazadas |
| Red/Qt | Cuatro ventanas Qt completan las seis publicaciones y llegan al mismo estado final; dos ventanas recuperan la sesión después de una interrupción |
| Tiempo | Timeout local y autoritativo; rechazo de confirmación con revisión obsoleta |
| Desconexión | Pausa explícita, identidad conservada y reconexión mediante token; turno e historial restaurados |
| Audio | Diecisiete WAV válidos; reproducción mediante el backend Qt, avance de posición, fuente correcta después de cambios rápidos, volumen/silencio y recursos opcionales ausentes |
| Grafo visual | Rumor, noticia verdadera y corrección con símbolos/colores distintos; ignorar borra el recorrido anterior y no permite reanudarlo |
| Final | Resumen desplazable con cuatro participantes y epílogo condicionado por elección e historial |

## Revisión visual

Las capturas aportadas de Full HD motivaron una segunda revisión de proporciones. Los marcos usan nueve segmentos reales para conservar sus adornos; el árbol limita su área y centra los nodos sin separarlos hasta los extremos. Los botones tienen alto explícito después de aplicar el estilo Qt y un ancho acotado. El observatorio centra su panel, agranda los retratos y las etiquetas al aumentar la ventana y conserva la red compacta. La selección de rol reserva margen para el título. El diálogo calcula su altura por texto, con un mínimo de 176 px, y aplica el contraste dentro del marco.

Se generaron 27 capturas reproducibles y un registro de geometrías con `herramientas/capturar_escalado.py`, en `.tmp/capturas_escalado/`. Se inspeccionaron árboles de dos y seis nodos, observatorios de trece y diecinueve ciudadanos, diálogo corto/largo/alto contraste y selección de personaje en 1100×700, 1366×768 y 1920×1080. Las seis pruebas nuevas comprueban proporción, tamaños de texto y contención real de los widgets; dos adicionales verifican el marco y la cartela. Los indicadores dejan de calcular siete filas al recibir su ancho provisional inicial de 100 px.

La revisión de experiencia añade comprobación de los 41 textos actuales en 1100×700, 1366×768 y 1920×1080, incluidas todas las consecuencias. Valida que los nombres, el cuerpo del diálogo y la pista no se superponen, y que las publicaciones pintadas no recortan sus etiquetas. El teléfono corregido se inspeccionó a 1100×700 y 1366×768; capturas en `.tmp/capturas_presentacion/telefono_corregido_*.png`.

Se comprobaron ocultación del HUD y menú Partida en portada, fundido cancelable, escritura pausada, integración de voz por hablante, paletas persistidas, crecimiento 9→19, guardado/carga y repetición de recorridos sin cambiar puntos. La reproducción real de Pablo, Laura y Helena alcanzó Speaking y regresó a Ready; volumen y silencio cancelan la narración. Los detalles del cambio están en [mejoras_experiencia.md](mejoras_experiencia.md).

Se renderizaron decisiones, ABB, observatorio y final en 1920×1080, 1600×900 y 1366×768. Se revisaron capturas del diálogo, árbol completo, grafo y elección. Los controles visibles tienen su centro dentro de la escena según las comprobaciones automáticas.

Durante la revisión se corrigieron fondo blanco del final, contraste de la barra, marcadores de nodos y superposición de sprites sobre protagonistas ya incluidos en fondos. Las capturas quedan en `.tmp/capturas/`, ignoradas por Git.

Las pruebas de ventanas usan **Qt offscreen**. Además se abrió el juego en Windows y se inspeccionó una interacción de verificación y su consecuencia en la ventana real. No se declara realizada una campaña humana completa ni una evaluación auditiva. El ensayo de audio ejecuta un proceso con el bucle completo de Qt y comprueba reproducción, no una valoración humana del sonido. La ampliación de imágenes corresponde a la etapa artística posterior del encargo; ver recursos.md y sustentacion.md.

## Rediseño visual integrado

Se generaron y copiaron al proyecto 23 PNG (47,1 MiB) con la herramienta integrada image_gen: siete fondos, protagonistas/expresiones/retratos, atlas de candidatos y ciudadanos, seis miniaturas editoriales y siete recursos de interfaz. El manifiesto registra medidas reales y SHA-256; las pruebas validan todos los archivos y el alfa de los recursos recortados. Se revisaron 16 vistas renderizadas de las pantallas reales. La versión actual también se abrió como aplicación de Windows.

Se corrigieron compresión de marcos, costuras de escalado, tipografía de lectura, viewport blanco, controles fuera del ancho mínimo y duplicación de buffers oscuros de personajes. Los controles ilustrados conservan teclado, señales y estados deshabilitados. El audio de producción y sus WAV se conservaron; su comprobación espera reproducción real con plazo acotado en lugar de asumir un arranque fijo del backend.

El inventario y los prompts están documentados en [rediseno_visual.md](rediseno_visual.md). Las vistas para revisión se conservan en `docs/vistas/`.

## Cambios principales

- `interfaz.py`: progresión, ciclo de vida, escritura, temporización, paneles, señales de red, accesibilidad y acceso a guardados.
- `juego/`: partida extraída, propagación, red inicial, decisiones, eventos, elecciones y relato desde resultados reales.
- `estructuras/grafo.py`, `nodo_grafo.py`: implementación propia; ABB y Nodo originales conservados.
- `models/`: extensiones compatibles de publicación y modelos de ciudadano, jugador, ciudad y candidato.
- `red/`: cliente/servidor autoritativo y protocolo delimitado; envío en hilos mediante colas.
- `paneles.py`, `audio/`, `recursos.py`, `configuracion.py`, `iniciar.py`: integración visual y audiovisual.
- `data/publicaciones.json`: publicaciones originales con ID conservados.
- `assets/audio/`: diecisiete WAV originales (once efectos, tres músicas y tres ambientes); sin cambios a las ilustraciones originales.
- `main.py`: demostración conservada con protección de importación y caso real de eliminación con dos hijos.
- `tests/`, README, requirements, gitignore y documentación: reproducción, pruebas y límites explícitos.

Los pyc ya versionados se conservaron; `.gitignore` evita incorporar nuevas cachés. La aplicación y la demostración siguen teniendo sus comandos anteriores.

## Límites de la comprobación

La reconexión requiere conservar la ventana del cliente y mantener abierto el servidor; no se implementó migración de anfitrión ni restauración de salas tras reiniciar el servidor. La edición de topología es individual y no cambia por sí sola la puntuación. Las capturas y la automatización validan funcionamiento y disposición, pero no sustituyen una valoración humana de accesibilidad, equilibrio, ritmo narrativo o mezcla.
