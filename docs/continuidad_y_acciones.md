# Acciones visibles, contadores obligatorios y continuidad de video

Revisión del 24 de octubre de 2026. Los resultados muestran un indicador cada vez en el centro. Las decisiones usan botones con una sola línea; cada método del ciudadano o de la periodista tiene un montaje relacionado con el caso y el resultado registrado.

[Muestra actual de acciones y contadores obligatorios](vistas/muestra_acciones_obligatorias.mp4).

## El cambio se ve completo

La tercera consecuencia elimina la cuadrícula y el resumen de seis tarjetas. Los indicadores aparecen sucesivamente cuando cambian: nombre, valor que sube o baja y diferencia efectiva. El último contador permanece centrado al terminar; no se transforma en una tabla.

Espacio, Enter, clic, Auto y Saltar leído esperan a que todos los contadores completen su presentación. Una pulsación anticipada no los revela de golpe ni los omite. La voz solicita cada indicador cuando comienza su toma real y el reloj visual termina el anterior antes del siguiente. Si la voz se cancela, está desactivada o falta una toma, la secuencia visual termina todos los cambios pendientes.

Se usan los valores anteriores y posteriores del registro, incluidos los límites 0–100 y los puntos acumulados. Reducir desinformación o conflictos se reconoce como mejora. Movimiento reducido conserva los números sin interpolación, con tiempo de lectura por indicador. Cuaderno, Configuración y minimización conservan el progreso.

## Una acción en su propio contexto

Los seis casos siguen siendo colegio, propuesta cultural, parque, biblioteca, acusación y pronóstico electoral. Cada uno dispone de los ocho métodos de oficio, seleccionados desde la decisión aplicada:

| Ciudadano | Lo que se representa | Periodista | Lo que se representa |
| --- | --- | --- | --- |
| Compartir | Usa el teléfono para reenviar el mensaje del caso | Contrastar | Coteja el contenido con documentos y anotaciones |
| Escuchar | Conversa con dos personas del vecindario | Entrevistar | Escucha una fuente y registra sus palabras |
| Convocar | Invita al vecindario y conversa con quienes se suman | Desmentir | Prepara la corrección y el reporte correspondiente |
| No reenviar | Aparta el teléfono y continúa | Reservar | Cierra una carpeta pendiente de pruebas |

Los botones muestran una sola línea. La explicación detallada queda en la ayuda del control, sin una segunda consigna dentro del botón. El servidor conserva la validación del oficio y del turno; los videos no aplican decisiones ni alteran las aristas, puntos o apoyos electorales.

Hay **66 montajes de acción**: 48 combinaciones de caso y método, seis reportes rechazados, seis convocatorias sin receptores y seis de alcance limitado. Los dos últimos grupos no muestran una multitud reunida; un reporte rechazado no presenta el contenido como retirado. Una entrevista no convierte un testimonio en prueba. La escuela sigue funcionando, el proyecto de biblioteca no se muestra inaugurado y una encuesta no proclama ganador.

Cada montaje tiene tres planos: lugar, objeto del caso y personaje ejerciendo el método. Dura nueve segundos, a 1280×720 y 24 fps. Son 14.256 fotogramas y 594 segundos de variantes; una campaña sólo reproduce las correspondientes a sus decisiones. El paquete completo reúne **95 MP4**: tres ambientes exportados, 21 cortes de narrador/personajes, cinco desenlaces y 66 montajes de acción.

Los recursos están en `assets/expansion/acciones_video/`. El [manifiesto](../assets/expansion/acciones_video/manifest.json) registra caso, acción, variante, descripción de lo representado, planos, fuentes, dimensiones, duración y SHA-256. Las pinturas de las ocho actividades se generaron con `image_gen` incorporada; los [prompts exactos](../assets/expansion/acciones_video/ilustraciones/prompts.json) se conservan junto a ellas. El movimiento usa cámara, disoluciones y objetos animados con QPainter: montajes cinematográficos de ilustraciones, con voz y mezcla locales.

## Inicio y pausa sin mostrar otro plano

Cada video tiene dos imágenes. `_inicio.png` contiene el **primer fotograma decodificado del MP4 terminado**. Esa cubierta se instala antes de la entrada del panel y coincide con el plano del reproductor. El JPG conserva una vista legible para movimiento reducido o respaldo. Ese cartel, tomado a mitad del montaje, no cubre la carga.

Cada carga obtiene un canal QVideoSink y una generación propios. Los callbacks encolados de otra fuente se rechazan. El nuevo plano se revela después de recibir una imagen válida de la fuente vigente. Al pausar se conserva el último fotograma presentado; esa misma imagen cubre la búsqueda hasta la posición guardada. Un frame cero entregado antes de completar el seek no sustituye la imagen congelada.

`CapaCinematica.iniciar(clave, reproducir=False)` prepara el primer plano sin iniciar el transporte. `reanudar()` comienza cuando la escena inicia su intervención. Reemplazar una fuente mantiene la capa visible. El reproductor se destruye antes del widget de video y del sink; el video no tiene salida de audio y no duplica el doblaje.

## Comprobación reproducible

La suite final completa aprobó **272 pruebas**, sin fallas, errores ni omisiones, en **159,703 s**. [Resumen de la suite](verificacion_suite_continuidad_acciones.json). La [muestra actual de 1:58](vistas/muestra_acciones_obligatorias.mp4) contiene las ocho acciones y dos balances íntegros; [datos del montaje](vistas/muestra_acciones_obligatorias.json).

```powershell
python -B herramientas/producir_acciones_video.py --todos --pendientes
python -B herramientas/preparar_portadas_video.py --verificar --cantidad-esperada 92
python -B herramientas/verificar_inicio_video.py --catalogo todos --exigir-completo --destino .tmp/inicios_video_qt_todos.json
python -B herramientas/verificar_acciones_ui_real.py
python -B herramientas/inventariar_audiovisual.py
python -B herramientas/consolidar_revision_acciones.py --transporte .tmp/inicios_video_qt_todos.json
python -B herramientas/verificar_proyecto.py --log .tmp/verificacion_continuidad_acciones.txt
```

La comprobación de portadas compara los bytes RGB con el primer fotograma decodificado por FFmpeg. La revisión del transporte usa QMediaPlayer real: cubierta anterior a la reproducción, primer plano propio, cambio de fuente y pausa/reanudación desde 2400 ms. Las herramientas fallan si se exige un lote completo y falta un recurso. No modifican partida ni preferencias personales. [Inventario](../assets/expansion/audiovisual_manifest.json), [verificación](verificacion.md).

La revisión final comprobó las **92 cubiertas sin diferencias RGB**, los **92 transportes Qt** y los **ocho botones con voces y videos reales**. Se ignoraron 800 pulsaciones anticipadas; los ocho montajes emitieron EndOfMedia a 9000 ms y sólo entonces permitieron continuar. La convocatoria examinada alcanzó nueve personas y el reporte cultural rechazado conservó el contenido. Partida y preferencias quedaron intactas. [Informe verificable](verificacion_continuidad_acciones.json), [contacto de las ocho capturas](vistas/acciones_comprobadas.jpg).

La inspección detectó un marco de diálogo desplazado cuando cambiaba el área de la escena durante su entrada. Se corrigió el rectángulo final de marco y etiquetas; la convocatoria se repitió con comprobación de geometría antes y después de pausar. También se retiraron las invitaciones que tapaban los rostros durante la reunión. El [balance con audio real](verificacion_balance_audio.json) comprueba por separado sus contadores y los intentos de avance anticipado.

La campaña completa también expuso un callback de ventana recibido durante la limpieza de objetos por Python: el filtro cinematográfico consultaba un atributo ya eliminado y PyQt terminaba el proceso. Los filtros de video, balance y efectos toleran ese estado parcial y se retiran de la ventana al detenerse. Al reutilizar la capa vuelven a instalarse, conservando la pausa y restauración. Tres regresiones envían el evento nativo tras borrar el atributo, comprueban la reutilización y recorren ocho ciclos de cierre y recolección.

El cierre total también vacía las fuentes de voz, música y ambiente antes de destruir los transportes. La reproducción detenida conservaba lectores nativos y bloqueaba `gc.collect` tras la prueba de diálogo/F11. La misma secuencia audiovisual y de balance pasó después completa: **27 pruebas en 70,583 s**, sin fallas ni errores; la recolección que se bloqueaba terminó en **113 ms**. La cancelación habitual de una línea conserva su fuente para reutilizarla. [Comparación de trazas, tiempos y memoria](verificacion_cierre_audio.json).
