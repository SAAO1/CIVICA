# Verificación de la implementación

Comprobación realizada el 14 de octubre de 2026 en la rama `desarrollo/segunda-entrega-grafos`. No se hicieron commits, pushes, cambios de autoría ni operaciones destructivas de Git. No se instalaron paquetes.

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
