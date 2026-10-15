# Matriz de cumplimiento

Estado comprobado el 14 de octubre de 2026. «Completado y verificado» identifica comportamiento observado mediante las pruebas indicadas; no implica una evaluación artística humana. La ejecución integral anterior registró **74 pruebas correctas**, con Python 3.14.5, PyQt6 6.11.0 y Qt 6.11.0. El resultado integral más reciente se mantiene en [verificacion.md](verificacion.md). La matriz específica de los cinco criterios de grafos y los pasos de demostración están en [segunda_entrega.md](segunda_entrega.md).

| Elemento | Estado | Evidencia |
|---|---|---|
| ABB y operaciones originales | Completado y verificado | Inserción, búsqueda, duplicados, tres recorridos y eliminación de raíz con dos hijos; implementación original conservada |
| Grafo propio y operaciones | Completado y verificado | Vértices, aristas dirigidas, vecinos, grados, rutas, componentes débiles y validación de errores |
| BFS y DFS | Completado y verificado | Orden determinista, ciclos, aislados, niveles y camino mínimo con BFS; sin NetworkX |
| Integración ABB-grafo | Completado y verificado | Consulta del ABB antes de propagar; retirar contenido impide nueva difusión; cambio de relación modifica alcance |
| Propagación y consecuencias | Completado y verificado | Receptores únicos, profundidad/tiempo por rol, veracidad, correcciones, indicadores limitados y puntuación |
| Publicaciones, decisiones e historial | Completado y verificado | Seis ID originales sin saltos ni doble decisión; reportes fundados/infundados; archivo de retiradas |
| Roles y habilidades | Completado y verificado | Campaña completa por las escenas con Ciudadano y Periodista; son los únicos seleccionables |
| Eventos y tiempo limitado | Completado y verificado | Semilla reproducible, cambios controlados y timeout local/autoritativo |
| Elección y finales | Completado y verificado | Apoyo dependiente de decisiones, empate explícito, propuesta del ganador y epílogo desde el historial |
| Guardado y restauración individual | Completado y verificado | JSON conserva forma del ABB, grafo, turno, historial, jugadores y estado aleatorio |
| Portada, escenarios, personajes y diálogos | Completado y verificado | Campañas Qt completas y capturas; interacción de decisión/consecuencia inspeccionada en Windows; arte original conservado |
| Transiciones y escritura progresiva | Completado y verificado | Revelar antes de avanzar, repetición bloqueada, timers cancelados al salir, resize y F11 |
| Panel Civitas y visualizador ABB | Completado y verificado | Decisiones y recorridos desde el estado real; capturas en tres resoluciones |
| Observatorio del grafo | Completado y verificado | Flechas, emisor, consulta de ciudadanos, crecimiento automático, comparación y BFS/DFS; distinción de rumor/verdad/corrección. No muestra edición manual de topología |
| Animación del grafo | Completado y verificado | Niveles precalculados, ritmo fijo y repetición tras dos segundos; movimiento reducido muestra resultado completo; no reutiliza propagaciones antiguas tras ignorar |
| Indicadores, puntos, reputación y logros | Completado y verificado | Valores reales y logros sin duplicación; resumen desplazable para cuatro jugadores |
| Ayuda, configuración y selección de rol | Completado y verificado | Integración en ventana; opciones de audio, contraste, movimiento y límite temporal |
| Accesibilidad implementada | Completado y verificado | Teclado, contraste configurable, movimiento reducido, tiempo opcional y leyendas que no dependen solo del color |
| Gestor de audio | Completado y verificado | Reproducción Qt, volumen, silencio, fundidos, cambio rápido de pista y ausencia de recursos opcionales |
| Música, efectos y ambientación | Completado y verificado | Once efectos, tres músicas y tres ambientes originales; validez PCM y reproducción comprobadas |
| Servidor y clientes locales, 2–4 participantes | Completado y verificado | Campañas TCP completas con dos, tres y cuatro clientes; autoridad del servidor |
| Sincronización con ventanas Qt | Completado y verificado | Cuatro ventanas completan la campaña con personajes repetidos y estados finales idénticos |
| Turnos, roles y validación de red | Completado y verificado | Acciones fuera de turno/repetidas rechazadas; barrera de lectura y revisión obsoleta |
| Desconexión y reconexión | Completado y verificado | Pausa y recuperación por token, manteniendo participante, turno e historial mientras vive el servidor |
| Recursos y rutas portables | Completado y verificado | Arranque desde otro directorio, caché de imágenes y archivos originales conservados |
| Pruebas y documentación | Completado y verificado | Suite unittest y guías de ejecución, reglas, recursos, arquitectura y sustentación |
| Valoración humana integral | Pendiente | Escucha, ritmo, equilibrio y accesibilidad con personas; no se presenta como una prueba ya realizada |
| Rediseño visual e ilustraciones | Completado y verificado | Recursos instalados, manifiesto con medidas/huellas, capturas de pantallas y controles con teclado; inventario en recursos.md |

## Alcance y límites

La campaña utiliza las seis publicaciones originales y sus escenarios. El modelo permite opiniones; la campaña incluida contiene noticias y rumores. El grafo social resuelve la difusión; no se añadió un segundo grafo de lugares decorativo. La comunidad pasa de nueve a diecinueve personas mediante crecimiento automático. La estructura implementa altas y bajas de vértices y aristas, verificadas con pruebas, pero la interfaz actual no expone edición manual. En multijugador la estructura y el estado pertenecen al servidor.

«Reconectar» requiere la misma ventana del cliente, que conserva el token en memoria, y un servidor abierto. No hay migración de anfitrión ni restauración de salas tras reiniciar el servidor. El modo multijugador comprobado es local.

El paquete visual está instalado y la campaña utiliza los nuevos fondos, personajes y controles. La aprobación estética por el usuario y la evaluación humana del audio son valoraciones adicionales. Se conservan las ilustraciones y el ABB originales, el historial Git, autores y fechas de commits. No se hicieron commits ni pushes.
