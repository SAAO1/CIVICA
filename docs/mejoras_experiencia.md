# Ajustes de experiencia · 14 de octubre de 2026

- Fuente portátil Atkinson Hyperlegible, con cuatro estilos y licencia en `assets/fuentes/`. Texto de diálogo de 24–28 px, nombre de 22–25 px y panel que calcula el espacio necesario según el contenido.
- Escritura a un carácter cada 34 ms, con pausas en comas y finales de frase. Se conserva la acción de revelar primero y continuar después.
- Entrada desde negro de 1,5 segundos al comenzar la historia y transiciones de 700 ms entre escenas. Movimiento reducido desactiva estos fundidos y las repeticiones del observatorio.
- Configuración a la derecha, con el Manual de usuario dentro. El menú Partida y los indicadores se muestran desde el comienzo de la historia hasta el final; la portada tiene botones para cargar y multijugador.
- Paletas para deuteranopia, protanopia y tritanopia en grafo, ABB e indicadores. Las etiquetas, los símbolos y los trazos mantienen el significado sin depender únicamente del color.
- Publicaciones de Civitas reutilizadas en el teléfono y en la escena de decisión: autor, avatar, navegación del feed, contenido, imagen y métricas reales. El contenido no revela el veredicto antes de decidir.
- El observatorio conserva BFS, DFS y Comparar alcance; retira los controles de velocidad, pausa, completar y edición manual de comunidad de la interfaz. Avanza cada 700 ms y espera dos segundos antes de repetir. Cambiar de recorrido o salir cancela los temporizadores anteriores.
- La red real crece de nueve a diecinueve ciudadanos, dos por publicación posterior a la primera. Nuevos nombres y conexiones son reproducibles, persisten en guardados y se sincronizan desde el servidor en multijugador.
- Voz sintética local en español: Pablo, Laura y Helena en el equipo de prueba. Hay volumen independiente y desactivación de voces. La música y el ambiente se atenúan durante la lectura. Las voces instaladas pueden variar en otros equipos; Configuración informa del catálogo disponible.

Las seis publicaciones originales y sus diálogos actuales son la base de esta revisión. Los personajes futuros pueden usar perfiles estables de voz sin ampliar todavía la historia.

Comprobación final: 74 pruebas correctas en 45,342 segundos con Python 3.14.5, PyQt6 6.11.0 y Qt 6.11.0. Incluye campañas con ambos roles y multijugador de dos a cuatro participantes. Los 41 textos actuales caben en 1100×700, 1366×768 y 1920×1080. Se revisó además la publicación del teléfono en los dos primeros tamaños.

La segunda revisión usa las capturas Full HD aportadas para corregir las proporciones. El marco conserva sus esquinas mediante nueve segmentos; el diálogo corto ocupa 176 px en lugar de un tercio de la pantalla. El árbol y el observatorio tienen áreas máximas centradas, nodos mayores y controles con altura suficiente. Se ampliaron selección de rol e indicadores y se corrigió el salto inicial de altura del HUD. Evidencia reproducible: 27 PNG y `geometrias.json` en `.tmp/capturas_escalado/`.

La comprobación de voces verificó el estado Speaking y el retorno a Ready para las tres voces; no equivale a una evaluación artística humana del doblaje. La revisión visual utiliza capturas de widgets Qt. La herramienta de automatización de ventanas Windows no logró inicializarse en esta sesión (`failed to write kernel assets`, error de ruta), por lo que no se atribuye aquí una interacción nativa automatizada.
