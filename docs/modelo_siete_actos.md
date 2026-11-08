# Campaña de siete actos: progreso, red y elección

La campaña extendida conserva los seis casos originales y añade ocho, para un total de catorce decisiones en siete actos. La interfaz utiliza `Juego(campana="extendida")`; el servidor admite el mismo parámetro. Las APIs conservan `campana="clasica"` por defecto para las partidas y herramientas anteriores.

| Acto | Casos | Conflicto central |
| --- | --- | --- |
| IV · La voz que amplifica | 90, 40 | El video recortado de Valeria y el alcance real de las correcciones |
| V · Cuatro promesas bajo los focos | 100, 10 | El plan del colegio y la diferencia entre una opinión y un hecho |
| VI · La noche del audio recortado | 110, 25 | La grabación completa y el documento de continuidad de las clases |
| VII · La ciudad decide | 120, 35 | Los accesos a las urnas y el mensaje que confunde comentar con votar |

El cierre ocurre después del caso catorce. Los guardados JSON de versión 1 incluyen la campaña y el plan completo de identificadores. Un archivo anterior sin esa marca conserva los seis casos clásicos. Una campaña extendida sin su plan, con otro plan o marcada como finalizada antes del último caso se rechaza para evitar pérdida de progreso.

Valeria aparece en el grafo al comenzar el acto IV. Su alcance procede de conexiones dirigidas reales: puede recibir mensajes de la comunidad y difundirlos hacia sus vecinos. Una entrevista puede contactar su nodo emisor. Los cuatro candidatos conservan su identidad electoral y sus propuestas; sus apariciones en el foro no inventan nodos ni votantes. Los personajes jugables siguen siendo ciudadano y periodista.

La elección reparte el peso total de la agenda entre las publicaciones iniciales de cada candidatura. Ese peso se congela antes de jugar: los contadores de impacto que cambian en el ABB no pueden alterar el cálculo al guardar o recargar. Las decisiones, los contactos y los receptores conservados en el historial determinan el apoyo. Consultar el resultado no consume azar.

La [auditoría reproducible](auditoria_campana_siete_actos.json) registra 768 campañas válidas, individuales y de dos a cuatro participantes, con y sin eventos. Todas completaron catorce decisiones y conservaron su resultado al recargar. La muestra produjo victorias de las cuatro candidaturas; además contiene rutas explícitas de catorce decisiones para cada victoria y para el empate. Es un muestreo reproducible, no una enumeración de todas las combinaciones posibles. La mayor trama observada fue de 53.546 bytes, dentro del límite de 65.536.

Las pruebas también recorren por TCP los catorce turnos con dos, tres y cuatro clientes, comparando en cada transición el estado autoritativo que reciben todos. Otras pruebas guardan y recargan en cada caso, conservando ABB, grafo, historial y estado del generador aleatorio.

Los ocho casos nuevos tienen 88 montajes de acciones, de nueve segundos a 1280 × 720 y 24 fps. Cada montaje sitúa el lugar, muestra el contexto del caso y termina con el método elegido por el ciudadano o la periodista. Incluye variantes para convocatorias sin receptores, grupos limitados y reportes rechazados. Son ilustraciones con cámara, objetos y efectos animados; las acciones reutilizan las ocho pinturas de métodos existentes junto a los cuatro fondos y cuatro CG nuevos de la historia. En el acto VII los rótulos se apartaron de los rostros.

La [verificación del reproductor Qt](verificacion_inicios_siete_actos.json) cubre los 96 videos nuevos: los 88 montajes y los ocho narradores. Comprueba la portada extraída del primer fotograma de cada MP4, el cambio de fuente, la pausa cerca de 2,4 segundos y la recuperación del fotograma y su posición. El informe final conserva los hashes de los archivos definitivos; las ocho escenas narrativas y los 22 montajes con rótulos corregidos se verificaron otra vez después de sus últimas exportaciones. La mayor diferencia media entre portada y primer fotograma presentado por Qt fue de 0,9238 niveles RGB sobre una escala de 0 a 255.

Reproducir la auditoría:

```powershell
python -B herramientas/auditar_campana_extendida.py --muestras 768 --salida docs/auditoria_campana_siete_actos.json
```
