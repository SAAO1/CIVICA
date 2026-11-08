# Cortos narrativos y efectos de CIVICA

Ampliación del 24 de octubre de 2026. Nueve videos locales acompañan frases concretas del narrador dentro de la partida. Los diálogos conservan sus controles, subtítulos, historia y decisiones. [Muestra narrada con la interfaz](vistas/cinematicas_narradas.mp4).

## Las nueve secuencias

| Momento | Imagen y acción |
| --- | --- |
| Cuarenta y ocho horas antes | Ciudad al atardecer, reloj animado, avisos que aparecen |
| Mensaje del barrio | Teléfono, notificaciones sucesivas y conexiones entre lectores |
| Rumor del colegio | Del mensaje al colegio en funcionamiento; aviso de comunicado ausente |
| Café sin probar | Vibración del teléfono, vapor y cambio de plano hacia el contexto familiar |
| Propuesta cultural | Libreta, preguntas, trazos que se escriben y polvo iluminado |
| Camino del parque | Mapa, ruta que se dibuja y marcador que avanza |
| Libro del abuelo | Libro gastado, luz de escritorio y una hoja que gira sobre el lomo |
| Acusación bajo la lluvia | Cristal con gotas, teléfono y mensajes que se multiplican |
| Víspera electoral | Plaza nocturna, luces y urna preparada; el resultado permanece abierto |

Cada MP4 contiene 288 fotogramas: 12 segundos, 1280×720, 24 fps. En total son 108 segundos de cortes distintos y 19.164.674 bytes de video. El reproductor los repite mientras permanezca la intervención, hasta que el jugador o Auto avance. Auto conserva la espera de fin de voz. Espacio, Enter y clic mantienen el comportamiento de revelar texto y después continuar.

Las seis pinturas nuevas se generaron con `image_gen` incorporada, tomando los escenarios del juego como referencia. [Prompts exactos](../assets/expansion/cinematica/prompts.json). Están instaladas en `assets/expansion/cinematica/ilustraciones/`. El movimiento combina cámara, disoluciones y objetos dibujados y animados por QPainter. El video representa una composición cinematográfica de ilustraciones y capas; los protagonistas continúan usando sus sprites expresivos durante las conversaciones.

Los rumores conservan rótulos de incertidumbre. El colegio no aparece clausurado y la encuesta no determina al ganador. Los efectos de consecuencias consultan el historial real: sólo se dibuja difusión con receptores, el reporte rechazado no recibe un escudo de retirada y una opinión no recibe una marca de verificación factual.

## Efectos durante el juego

`CapaEfectos` incorpora catorce composiciones: notificación, rumor, investigación, verificación, reporte, silencio, lluvia, tensión, elección, recuerdo, decisión, archivo, transición y fuente. Cada una usa su propio movimiento y duración. Los diálogos, decisiones y consecuencias seleccionan la que corresponde al acontecimiento. Abrir una fuente anima un subrayado en una franja sin texto del cuaderno; el final anima luces y papeles sobre el retrato. Los empates muestran documentos de recuento.

Las capas permiten los clics y dejan libre el área de lectura. No agregan puntuación, pistas nuevas, resultados electorales ni decisiones. La comunidad, ABB, grafo, guardados y servidor mantienen sus reglas.

## Reproducción y preferencias

`juego/cinematica.py` enlaza las nueve frases completas del narrador y doce intervenciones de personajes con sus recursos. Las decisiones tienen un catálogo aparte, seleccionado por el registro aplicado; un texto importado sin coincidencia conserva su fondo habitual. `cinematica_narrativa.py` decodifica con QMediaPlayer y pinta los fotogramas de QVideoSink en el mismo lienzo de los widgets: video, partículas, texto y controles comparten composición. Los actores desaparecen durante el corte y regresan en la siguiente intervención.

Los MP4 son silenciosos. La voz neuronal, música, efectos y ambiente pertenecen al gestor de audio existente, sin duplicar la narración. Se reproducen los archivos locales; no hay descargas durante el juego.

Cuaderno y Configuración pausan la puesta en escena; sólo recuperan la intervención vigente. Cambiar de escena o diálogo cancela el corte anterior. Minimizar, ocultar o pausar descarga la fuente del reproductor, conservando la posición cuando corresponde. La cubierta `_inicio.png` es el primer fotograma decodificado del MP4 y se prepara antes de la entrada del panel. El cartel JPG se reserva para movimiento reducido o respaldo. Al pausar se congela el último plano; al reanudar no se muestra el frame cero durante la búsqueda. Cada carga tiene un canal y una generación propios para descartar callbacks antiguos. **Reducir movimiento** o desactivar **Fondos animados** conserva el contexto como imagen quieta. [Continuidad y videos de las decisiones](continuidad_y_acciones.md).

## Producción y revisión

```powershell
python -B herramientas/producir_cinematicas.py --todos
python -B herramientas/verificar_cinematicas.py
python -B herramientas/capturar_cinematicas.py
```

La producción requiere FFmpeg; jugar sólo requiere PyQt6 y el paquete de recursos entregado. El exportador escribe por pipe, sin guardar miles de imágenes intermedias. [Manifest de videos, carteles, fuentes y SHA-256](../assets/expansion/cinematica/manifest.json).

La comprobación de cada MP4 incluye decodificación completa. La revisión dentro de VentanaPrincipal contrasta el fotograma recibido con el pintado, comprueba pausa/reanudación, movimiento reducido y regreso de actores. La muestra es una exportación de los widgets reales y el compositor, con las tomas locales del narrador y las mezclas CC0 del proyecto. Las preferencias y la biblioteca de revisión están en memoria; no altera la partida personal.

Resultado final: **177 pruebas aprobadas, sin fallas ni errores**, en 111,761 segundos. Los nueve cortes pasaron la comprobación de imagen y transporte, y 24 ciclos reales de cierre terminaron correctamente. El reproductor se destruye antes que la superficie de video y su sink. El ejecutor `python -B herramientas/verificar_proyecto.py` procesa las destrucciones diferidas de Qt entre pruebas y mantiene la biblioteca personal en memoria. [Resultados registrados](verificacion_cinematicas.json).
