# Matriz de cumplimiento

**Estado actual:** la interfaz abre la campaña completa de siete actos y catorce casos. Los actos IV a VII incorporan a Valeria Cruz y a las cuatro candidaturas con diálogo, expresiones, escenas propias y ocho identidades de voz. El desenlace dialogado usa el resultado real de la elección y permite 45 combinaciones modulares de ganador o empate, estado cívico y arco de Valeria. El paquete de voces reúne 1.587 MP3 locales; la comprobación estricta cubre 967 entradas de la ampliación, incluidas las 191 líneas únicas del guion, sus fragmentos, los contadores y el alcance. Las ocho pruebas específicas de guion y voz pasaron. [Guion](guion_siete_actos.md), [modelo y compatibilidad](modelo_siete_actos.md), [auditoría de campañas](auditoria_campana_siete_actos.json), [cobertura de voces](verificacion_voces_siete_actos.json).

Se mantienen los contadores individuales obligatorios, los botones breves y la preparación del primer fotograma real de los videos. Los ocho casos nuevos añaden 88 montajes de acción y ocho cortes del narrador, además de cuatro ambientes y cuatro efectos de objetos. La campaña clásica conserva sus seis casos, su modo de guardado y sus 66 montajes anteriores. Las cuatro candidaturas pueden ganar según el historial; un empate conserva el recuento pendiente. [Recursos audiovisuales](expansion_audiovisual.md), [muestra de los siete actos](vistas/muestra_siete_actos.mp4).

La etapa anterior registró 272 pruebas aprobadas, sin fallas ni errores, con seis casos, 1.017 clips y 95 MP4. Esa comprobación corrigió destellos, pausas, alineación del diálogo y dos fallos de cierre de Qt/audio. [Detalle de esa etapa](continuidad_y_acciones.md), [suite anterior](verificacion_suite_continuidad_acciones.json), [reproducción real anterior](verificacion_continuidad_acciones.json).

Etapa anterior del 24 de octubre de 2026: novela visual y expansión audiovisual integradas, con **177 pruebas correctas** en la suite completa. La campaña presenta tres actos, seis conversaciones propias, consecuencias y epílogos del historial, dieciocho pistas, perfiles, glosario e historial de lectura. La expansión añade 595 clips neuronales, 48 fotogramas de protagonistas, tres fondos, capas animadas, once GIF, tres MP4 de ambientes y 27 WAV. La ampliación narrativa incorpora seis pinturas nuevas, nueve MP4 contextuales que se reproducen con el narrador y catorce efectos. Configuración permite probar voces y controlar movimiento. Se conservan reglas, guardados y sincronización. Diseño: [novela_visual.md](novela_visual.md), [expansion_audiovisual.md](expansion_audiovisual.md), [cinematicas_narrativas.md](cinematicas_narrativas.md). Evidencia: [verificacion.md](verificacion.md).

La matriz reúne las comprobaciones del modelo, la interfaz y sus ampliaciones. «Completado y verificado» identifica comportamiento observado mediante pruebas; no implica una evaluación artística humana. La matriz específica de grafos y los pasos de demostración están en [segunda_entrega.md](segunda_entrega.md).

| Elemento | Estado | Evidencia |
|---|---|---|
| ABB y operaciones originales | Completado y verificado | Inserción, búsqueda, duplicados, tres recorridos y eliminación de raíz con dos hijos; implementación original conservada |
| Grafo propio y operaciones | Completado y verificado | Vértices, aristas dirigidas, vecinos, grados, rutas, componentes débiles y validación de errores |
| BFS y DFS | Completado y verificado | Orden determinista, ciclos, aislados, niveles y camino mínimo con BFS; sin NetworkX |
| Integración ABB-grafo | Completado y verificado | Consulta del ABB antes de propagar; retirar contenido impide nueva difusión; cambio de relación modifica alcance |
| Propagación y consecuencias | Completado y verificado | Receptores únicos, profundidad/tiempo por rol, veracidad, correcciones, indicadores limitados y puntuación |
| Publicaciones, decisiones e historial | Completado y verificado | Catorce ID en la campaña completa y seis en la clásica, sin saltos ni doble decisión; reportes fundados/infundados; archivo de retiradas |
| Roles y habilidades | Completado y verificado | Ciudadano y Periodista mantienen métodos distintos; Valeria y cuatro candidaturas intervienen como personajes de la historia |
| Eventos y tiempo limitado | Completado y verificado | Semilla reproducible, cambios controlados y timeout local/autoritativo |
| Elección y finales | Completado y verificado | Apoyo dependiente de decisiones, agenda equilibrada de cada campaña y empate explícito; epílogo con 45 combinaciones modulares verificadas y cuatro ganadores posibles |
| Guardado y restauración individual | Completado y verificado | JSON conserva campaña, plan, forma del ABB, grafo, turno, historial, jugadores y estado aleatorio; guardados anteriores conservan la campaña clásica |
| Portada, escenarios, personajes y diálogos | Completado y verificado | Campañas Qt completas y capturas; interacción de decisión/consecuencia inspeccionada en Windows; arte original conservado |
| Transiciones y escritura progresiva | Completado y verificado | Revelar antes de avanzar, repetición bloqueada, timers cancelados al salir, resize y F11 |
| Panel Civitas y visualizador ABB | Completado y verificado | Decisiones y recorridos desde el estado real; capturas en tres resoluciones |
| Observatorio del grafo | Completado y verificado | Flechas, emisor, consulta de ciudadanos, crecimiento automático, comparación y BFS/DFS; distinción de rumor/verdad/corrección. No muestra edición manual de topología |
| Animación del grafo | Completado y verificado | Niveles precalculados, ritmo fijo y repetición tras dos segundos; movimiento reducido muestra resultado completo; no reutiliza propagaciones antiguas tras ignorar |
| Indicadores, puntos, reputación y logros | Completado y verificado | Valores reales y logros sin duplicación; resumen desplazable para cuatro jugadores |
| Ayuda, configuración y selección de rol | Completado y verificado | Integración en ventana; opciones de audio, contraste, movimiento y límite temporal |
| Accesibilidad implementada | Completado y verificado | Teclado, contraste configurable, movimiento reducido, tiempo opcional y leyendas que no dependen solo del color |
| Gestor de audio | Completado y verificado | Reproducción Qt, volumen, silencio, fundidos, cambio rápido de pista y ausencia de recursos opcionales |
| Música, efectos y ambientación | Completado y verificado | Fuentes CC0, 27 WAV de la expansión anterior y ocho montajes nuevos; música, ambientes, foley, validez PCM, volumen y reproducción comprobados |
| Guion de siete actos | Completado y verificado | Ocho casos nuevos, 24 fuentes, memorias de decisiones y 64 pares de caso/método con reacción específica; lectura sin mutar estado ni azar |
| Doblaje de la ampliación | Completado y verificado | Ocho identidades distintas; 967 entradas locales con texto, intérprete, duración y señal comprobados; voces sintéticas neuronales |
| Servidor y clientes locales, 2–4 participantes | Completado y verificado | Campañas TCP completas con dos, tres y cuatro clientes; autoridad del servidor |
| Sincronización con ventanas Qt | Completado y verificado | Cuatro ventanas completan la campaña con personajes repetidos y estados finales idénticos |
| Turnos, roles y validación de red | Completado y verificado | Acciones fuera de turno/repetidas rechazadas; barrera de lectura y revisión obsoleta |
| Desconexión y reconexión | Completado y verificado | Pausa y recuperación por token, manteniendo participante, turno e historial mientras vive el servidor |
| Recursos y rutas portables | Completado y verificado | Arranque desde otro directorio, caché de imágenes y archivos originales conservados |
| Pruebas y documentación | Completado y verificado | Suite unittest y guías de ejecución, reglas, recursos, arquitectura y sustentación |
| Valoración humana integral | Pendiente | Escucha, ritmo, equilibrio y accesibilidad con personas; no se presenta como una prueba ya realizada |
| Rediseño visual e ilustraciones | Completado y verificado | Recursos instalados, manifiesto con medidas/huellas, capturas de pantallas y controles con teclado; inventario en recursos.md |

## Alcance y límites

La campaña completa utiliza las seis publicaciones originales y ocho nuevas, incluidas noticias, rumores y una opinión atribuida que no se certifica como hecho. El grafo social resuelve la difusión; no se añadió un segundo grafo de lugares decorativo. La comunidad pasa de nueve a veinte personas en la campaña completa: la vecina Violeta y la influencer Valeria tienen identidades separadas, y Valeria entra al comenzar el acto IV. La campaña clásica conserva sus diecinueve personas. La estructura implementa altas y bajas de vértices y aristas, verificadas con pruebas, pero la interfaz actual no expone edición manual. En multijugador la estructura y el estado pertenecen al servidor.

Las 45 combinaciones de cierre usan diálogo modular y cinco videos de desenlace: cuatro investiduras y un recuento. No son 45 películas independientes ni una afirmación de que se haya explorado cada uno de los posibles caminos de catorce decisiones. La auditoría de campañas y las pruebas de ramas indican qué recorridos se ejecutaron.

«Reconectar» requiere la misma ventana del cliente, que conserva el token en memoria, y un servidor abierto. No hay migración de anfitrión ni restauración de salas tras reiniciar el servidor. El modo multijugador comprobado es local.

El paquete visual está instalado y la campaña utiliza los nuevos fondos, personajes y controles. La aprobación estética por el usuario y la evaluación humana del audio son valoraciones adicionales. Se conservan las ilustraciones y el ABB originales, el historial Git, autores y fechas de commits. No se hicieron commits ni pushes.
