# Demostración y arquitectura

## Recorrido sugerido

1. Ejecutar `python iniciar.py --sin-eventos --sin-limite` y seleccionar Ciudadano.
2. Mostrar introducción y diálogo. Una pulsación revela texto y otra continúa; mantener Espacio no salta la conversación.
3. Compartir #50: buscar en ABB, calcular BFS y observar el deterioro por rumor falso.
4. Mostrar ABB, inorden/preorden/postorden y continuar al observatorio.
5. Observar la difusión automática: tres receptores iniciales desde Ana con profundidad dos; el recorrido se repite tras dos segundos. Movimiento reducido presenta el resultado completo.
6. Comparar desde Inés, inicialmente aislada: cero receptores frente a los tres del resultado previo; los puntos permanecen iguales. La interfaz no muestra edición manual de conexiones.
7. Ejecutar DFS y explicar por qué su orden difiere y no garantiza caminos mínimos.
8. Continuar con #30 y comprobar que la información verdadera tiene consecuencias distintas.
9. En una nueva campaña, reportar #50: desaparece del ABB y su historial permanece. No se borran ciudadanos.
10. Comparar finales de campañas que verifican frente a otras que comparten rumores.
11. Comparar Ciudadano y Periodista: la verificación de la periodista recupera más confianza. Influencer y candidato no son seleccionables.
12. Abrir ayuda y demostrar movimiento reducido, contraste y decisiones sin límite.
13. Crear una sala local con dos a cuatro instancias, ciudadano/periodista (se pueden repetir), rotación de turno y barrera de lectura.
14. Interrumpir la conexión de un cliente sin cerrar su ventana ni el servidor, pulsar «Reconectar» y comprobar que vuelve al mismo turno y resultado.

La matriz de los cinco criterios y una demostración reproducible con órdenes y cantidades están en [segunda_entrega.md](segunda_entrega.md). El crecimiento automático agrega dos ciudadanos por publicación posterior a la primera, hasta diecinueve miembros. Para sustentar altas y bajas de vértices/aristas se usa el código de `Grafo` y sus pruebas; no se presenta como un editor disponible en pantalla.

## Responsabilidades reales

`Nodo` enlaza publicaciones en el ABB. `Publicacion` mantiene datos y contadores. `ArbolPublicaciones` conserva el índice activo. `NodoGrafo`/`Ciudadano` identifican personas; las conexiones solo se almacenan en `Grafo`. `ServicioPropagacion` consulta ABB y produce un resultado de BFS. `Juego` decide, registra y avanza una sola vez. Las escenas muestran esos datos.

`EscenaCinematica` administra estados, temporizadores poseídos y animaciones. Al salir cancela callbacks y movimiento. La escritura usa QTimer; las animaciones usan QPropertyAnimation y grupos paralelos. No hay sleep en el hilo gráfico. El observatorio reproduce niveles ya calculados, sin BFS dentro de paintEvent.

`GestorAudio` mantiene una pista por canal de música/ambiente y efectos reutilizables, con fundidos que respetan silencio y volumen. Los fallos de recursos opcionales no afectan las reglas.

`Servidor` posee el estado oficial. Los lectores validan tramas delimitadas; RLock ordena decisiones y timeout. `Cliente` usa lectura/escritura en hilos; la ventana recibe señales. La revisión identifica el resultado que cada participante confirma. Una desconexión pausa la sala y su plazo; el token de sesión permite recuperar la identidad y reanudar cuando regresan todos. No hay migración de anfitrión ni persistencia de salas tras cerrar el servidor.

## Evaluación humana adicional

- Abrir `python iniciar.py` en el escritorio y completar una campaña con cada rol.
- Escuchar los tres canales, cambiar volúmenes durante un fundido y comprobar silencio persistente.
- Mantener Espacio/Enter, alternar F11, maximizar/restaurar y redimensionar durante una animación.
- Revisar diálogos largos y todos los botones en 1920×1080, 1600×900 y 1366×768.
- Guardar durante una decisión y después de un reporte; cargar y completar la campaña.
- Abrir cuatro procesos, jugar hasta la elección y comprobar puntuaciones coincidentes.
- Interrumpir una conexión, comprobar la pausa y recuperar la sesión con «Reconectar» mientras el servidor permanece abierto.

La suite ya completa campañas por las escenas con cada rol y con cuatro ventanas sincronizadas, además de probar reconexión y reproducción real mediante el backend de audio. Se inspeccionó una decisión/consecuencia en la ventana de Windows. La lista anterior sirve para valorar la experiencia con una persona; no describe funciones de juego sin implementar ni una sesión humana que se haya realizado.
