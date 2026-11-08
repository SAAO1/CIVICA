# Entrega final: requisitos y sustentación del código

Revisión del 7 de noviembre de 2026 sobre el [PDF original](laboratorio/LABORATORIO%201%20202630.pdf). La sección 18, página 13, fija la entrega final del 16 al 20 de noviembre de 2026. Esta guía distingue implementación, evidencia automatizada y pendientes; no sustituye la calificación de la profesora.

## Estado vigente y evidencia histórica

La presentación actual se describe en la [guía de inmersión narrativa](inmersion_narrativa.md) y se comprueba en la [verificación vigente](verificacion_ajustes_visuales.md). La matriz y la cifra de **334 pruebas** conservadas más abajo corresponden a una revisión histórica; no representan el resultado de la versión actual.

El HUD inferior fue sustituido por la presentación de consecuencias: siete indicadores y puntuación centrados, con letras grandes y un panel opaco sobre el fondo de ciudad, con narración automática y avance inmediato mediante Espacio, Enter o clic. El expediente sigue fuente → tres respuestas → confirmación, sin formularios y con prueba adjunta del acto actual. Después de las consecuencias se revisan el ABB y el grafo.

El multijugador principal utiliza [ServidorCooperativo](../red/cooperativa.py) y [ClienteCooperativo](../red/cliente_cooperativo.py): exactamente dos roles exclusivos, Ciudadano y Periodista. El servidor escucha en **0.0.0.0** para la LAN; el anfitrión comparte su IP LAN y puerto. Las pruebas locales con dos clientes no acreditan por sí solas una comprobación con dos equipos físicos.

## Ruta de lectura para mostrar el código

| Qué mostrar | Implementación | Llamada durante el juego |
|---|---|---|
| Nodo del ABB con hijos | [Nodo](../estructuras/nodo.py) | `ArbolPublicaciones.insertar` construye nodos propios |
| Inserción, búsqueda, eliminación y tres recorridos | [ArbolPublicaciones](../estructuras/bst.py) | `Juego.agregar_publicacion`, `obtener_publicacion_actual`, `ejecutar_accion` y `datos` |
| Vértices y relaciones dirigidas | [Grafo](../estructuras/grafo.py), [Ciudadano](../models/ciudadano.py) | [crear_red_social y ampliar_comunidad](../juego/red_social.py) |
| BFS: orden, distancias, padres y niveles | [Grafo.bfs](../estructuras/grafo.py) | [ServicioPropagacion.simular](../juego/propagacion.py) |
| Unión ABB y grafo | [ServicioPropagacion](../juego/propagacion.py) | Busca en ABB antes de recorrer las relaciones |
| Efecto en reglas y puntuación | [Juego.ejecutar_accion](../juego/partida.py), [consecuencias](../juego/decisiones.py) | El alcance de BFS entra como parámetro de las consecuencias |
| Relaciones creadas por decisiones | [Juego._abrir_contacto](../juego/partida.py) | Conversar y entrevistar llaman `agregar_arista` |
| Efecto en la elección | [calcular_eleccion](../juego/elecciones.py) | Usa los receptores reales guardados en el historial |
| Recorridos y resultados visibles | [EscenaArbol](../interfaz/escenas/arbol.py), [EscenaRed](../interfaz/escenas/red.py) | Botones de inorden/preorden/postorden, BFS/DFS y comparación |
| Restauración de ambas estructuras | [Juego.datos y desde_datos](../juego/partida.py) | Preorden reconstruye el ABB; vértices y aristas reconstruyen el grafo |

Para responder «¿dónde los llaman?», abrir primero `juego/partida.py`, después `juego/propagacion.py` y finalmente `estructuras/bst.py` y `estructuras/grafo.py`. Las clases de interfaz representan esos objetos; el motor consulta y modifica las estructuras.

## Evidencia causal reproducible

Ejecutar desde la raíz:

```powershell
python -B -m ejemplos.demo_integracion
python -B -m unittest tests.test_bst tests.test_grafo tests.test_integracion_final -v
```

La demostración llama el mismo motor del videojuego y comprueba lo siguiente:

1. La partida comienza con ABB vacío; al llegar #50 se ejecutan inserción y búsqueda.
2. Dos partidas idénticas comparten #50. En una se quita únicamente `ana → luis`: el alcance cambia de 3 a 2, la desinformación de 9 a 6 y los puntos de −6 a −4. También cambia el apoyo electoral.
3. Avanzar la campaña construye un ABB con resultados distintos para inorden, preorden y postorden.
4. BFS, DFS y camino mínimo exploran el grafo sin volver a otorgar puntos.
5. Un paso por JSON conserva la forma exacta del ABB, las conexiones y el estado.
6. Desmentir #50 como Periodista difunde una corrección y retira el contenido del ABB. Una nueva simulación falla, incluso después de restaurar la partida; las personas y relaciones permanecen.

Estos cambios prueban que las estructuras participan en la mecánica independientemente de sus dibujos. El ejemplo de consola aporta evidencia del motor; la interfaz gráfica sigue siendo el videojuego entregado.

## Matriz del PDF — revisión histórica

| Requisito y página | Implementación o evidencia | Alcance y pendientes |
|---|---|---|
| Python o Java, p. 1 | Python y PyQt6; `requirements.txt` | Comprobar el entorno de la máquina de sustentación |
| 2–4 jugadores y roles, p. 3 | `red/cooperativa.py`, `models/jugador.py`, pruebas de red | Dos participantes en el recorrido principal; solo Ciudadano y Periodista seleccionables. Influencer y Candidato no están habilitados como roles jugables |
| Árbol funcional, p. 4 | ABB propio, operaciones y llamadas de la tabla anterior | Variante no autoequilibrada; justificación en [arquitectura](arquitectura.md) |
| Grafo funcional y operaciones, p. 5 | Altas/bajas, BFS, DFS, vecinos, grados, caminos y componentes | Las bajas se demuestran mediante código y pruebas; no hay editor manual en pantalla |
| Propagación, p. 6 | Receptores, cantidad, distancia, tiempo simulado, veracidad y consecuencias | El modelo simula saltos; no mide velocidad real de red |
| Eventos aleatorios, pp. 6–7 | `juego/eventos.py` y generador con semilla en `Juego` | `--sin-eventos` se usa para demostraciones reproducibles |
| Tiempo y decisiones, p. 7 | Eventos urgentes y temporizadores en escenas y servidor | Modo accesible sin límite configurable |
| Indicadores y puntuaciones, p. 8 | `models/estado_ciudad.py`, `Juego.ejecutar_accion`, HUD | Cambios al estado e historial por participante |
| Elección del alcalde, p. 9 | `juego/elecciones.py` | Apoyos derivados de decisiones y alcance; empate explícito |
| Multijugador cliente-servidor, pp. 9–10 | `red/servidor.py`, `cliente.py`, `protocolo.py` | Servidor local autoritativo; la sala gráfica escucha en `127.0.0.1`. Usar equipos distintos requiere configurar y verificar el enlace LAN |
| Interfaz gráfica, p. 10 | `interfaz/escenas`, `componentes`, `ventana.py` | Revisión humana de legibilidad y campaña completa |
| Inclusividad, pp. 10–11 | Contraste, filtros, subtítulos y movimiento reducido | Atiende dificultades visuales, de lectura y sensibilidad al movimiento |
| Ayuda, p. 11 | `interfaz.dialogos.mostrar_ayuda` | Objetivo, reglas, acciones, roles, indicadores y forma de ganar |
| Motivación, pp. 11–12 | Audio, animaciones, consecuencias y logros | Revisión humana del ritmo y de la escucha |
| Estabilidad, p. 13 | Suite en `herramientas/verificar_proyecto.py` | Consultar el informe actual; no inferir resultados de informes históricos |
| Repositorio e historial individual, p. 13 | Repositorio del equipo | Esta copia descargada no incluye `.git`; no permite comprobar aportes ni sustituye el enlace del repositorio |
| Sustentación de todo el código, pp. 13–15 | Esta guía, arquitectura y demostraciones | Todos los integrantes deben conocer estructuras, red y decisiones |

La sección de roles del PDF enumera cuatro perfiles y esta versión solo permite dos. Es un pendiente frente al alcance descrito; no se declara cumplimiento total del laboratorio.

## Demostración gráfica breve

Ejecutar `python -B main.py --clasica --semilla 4 --sin-eventos --sin-audio --sin-limite`. Elegir Ciudadano y compartir #50. Mostrar indicadores y puntos, después el árbol y el observatorio; ejecutar recorridos desde sus botones. Avanzar a otra publicación para mostrar inserción y crecimiento de la red. En otra partida elegir Periodista y desmentir el rumor para mostrar su retiro del ABB.

Para multijugador abrir dos instancias y pulsar **Multijugador** en la portada. El anfitrión usa **Crear sala**; los demás eligen **Unirse** al mismo servidor y puerto. Con los participantes conectados, el anfitrión pulsa **Iniciar campaña (anfitrión)**. Mostrar que solo actúa el participante del turno y que todos reciben el mismo resultado. El menú **Partida → Reconectar sala** recupera una sesión mientras siga abierto su servidor.

## Verificación histórica de esta matriz

```powershell
python -m pip install -r requirements-dev.txt
python -B herramientas/verificar_proyecto.py --log .tmp/verificacion_entrega_final.txt
```

Las dependencias de desarrollo permiten ejecutar también las pruebas de producción audiovisual; la instalación normal del juego usa únicamente `requirements.txt`. El archivo JSON paralelo registra la cantidad real de pruebas, fallas, errores, omisiones y duración. Los informes anteriores se conservan como historial; sus cifras no son resultados de esta reorganización.

Resultado de aquella revisión histórica: **334 pruebas correctas**, sin fallas, errores ni omisiones, en 146,764 segundos. Véanse el [resumen de la suite](verificacion_entrega_final.json) y la [explicación de los cambios y comprobaciones](verificacion.md). Esto acredita las pruebas ejecutadas; los pendientes de la matriz siguen señalados.
