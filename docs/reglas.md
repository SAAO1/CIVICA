# Reglas implementadas

## ABB y grafo

El ABB original conserva sus firmas y ordena publicaciones por ID. Los ID no se modifican durante la partida. Los duplicados no sustituyen el objeto existente. Inserción y búsqueda son iterativas; eliminación usa el sucesor inorden para dos hijos. Coste O(h), peor caso O(n), y recorridos O(n). No es un árbol balanceado.

El grafo es dirigido, no ponderado, sin bucles y sin aristas paralelas. A → B significa que información de A puede llegar a B. Una relación de seguimiento inversa debe expresarse con otra arista. Cada adyacencia usa claves de un diccionario para conservar orden y evitar duplicados; esto no sustituye el ABB.

Agregar duplicados o retirar una arista ausente devuelve False. Los ID inexistentes en operaciones que los necesitan producen KeyError. Conectar un vértice consigo mismo produce ValueError. Se validan ambos extremos antes de cambiar conexiones. Eliminar un vértice retira enlaces entrantes y salientes.

BFS usa deque, marca al encolar y devuelve orden, padres, distancias mínimas, niveles y aristas de descubrimiento. DFS usa una pila y no promete caminos mínimos. Ambos recorren O(V+E); el camino mínimo se reconstruye desde BFS. Las componentes débiles ignoran la dirección, y no se presentan como componentes fuertemente conexas.

## Difusión

El servicio consulta `arbol.buscar(id)` antes de cada simulación. La lista de receptores excluye al emisor y no repite ciudadanos aunque existan ciclos o rutas alternativas. Cada arista de descubrimiento registra una primera recepción: no equivale a toda conexión inspeccionada ni a una nueva acción de compartir. No se modelan exposiciones reiteradas en esta versión.

Los únicos personajes seleccionables son Ciudadano y Periodista. Ambos alcanzan hasta dos conexiones. Periodista usa intervalos de 0,8 minutos simulados y Ciudadano 1 minuto por nivel. Los perfiles históricos Influencer/Candidato se conservan para compatibilidad con datos anteriores, sin ofrecerse en nuevas partidas. El tiempo real de animación es independiente. El alcance se calcula antes de dibujar; reproducir una animación no otorga puntos.

La red inicial contiene nueve ciudadanos, un ciclo, rutas alternativas, una conexión entre grupos y un vértice aislado. Los eventos pueden conectar a Inés. El editor individual permite modificar relaciones y ciudadanos; protege los emisores de jugadores y los vértices necesarios para eventos.

## Indicadores y puntuación

Los indicadores se limitan a 0..100. Información verificada, desinformación, conflictos y participación parten de 0; confianza, convivencia y bienestar parten de 50. Sea s = min(5, receptores alcanzados).

| Acción | Ciudad | Puntos individuales |
|---|---|---|
| Compartir falsa/dañina | Desinformación +3s, confianza −s, conflictos +s, convivencia −s, bienestar −s | −2s |
| Compartir verdadera | Información +2s, participación +s, confianza +s, convivencia +s, bienestar +s | +2s |
| Compartir opinión | Participación +s, confianza +s, convivencia +s, bienestar +s; sin información verificada | +2s |
| Verificar hecho | Información +5, confianza +(3+b), desinformación −(3+s), conflictos −2, convivencia +2, bienestar +2 | +(6+b) |
| Verificar opinión | Participación +1; no se afirma su veracidad | +1 |
| Reportar falsa/dañina | Confianza +2, desinformación −3, convivencia +3, bienestar +2, conflictos −2 | +5 |
| Reporte infundado | Confianza −2, convivencia −1; la publicación permanece | −3 |
| Ignorar | No inicia difusión ni cambia indicadores | 0 |

b = 3 para Periodista, 2 para Ciudadano y 0 para los otros roles. Una verificación falsa difunde una corrección con BFS; su alcance no se suma al contador de personas expuestas al rumor original. Reputación cambia con puntos y confianza individual con el cambio de confianza global, ambas limitadas a 0..100. Los puntos pueden ser negativos.

Primera verificación, detección de rumor y difusión responsable se conceden una sola vez por persona. El perfil histórico Candidato mantiene su bonificación de apoyo solo por compatibilidad con partidas anteriores; no es seleccionable. Estas cifras son reglas del videojuego, no valores prescritos por el PDF.

Cada decisión guarda publicación, participante, acción, alcance, puntos, antes/después y propagación. Reportar contenido dañino lo elimina físicamente del ABB y conserva ese registro sin retirar relaciones ni personas. Un reporte infundado no lo elimina.

## Eventos y tiempo

Al presentar cada publicación se elige uno de cinco eventos con `random.Random(semilla)`: normal, viral, convivencia, discusión o conexión. Convivencia añade +2 convivencia/+1 bienestar; discusión añade +1 conflictos/−1 confianza. Conexión añade Pedro → Inés si todavía no existe. El evento viral da 15 segundos; agotarlos ejecuta ignorar. La guardia de decisión única evita efectos duplicados. La secuencia y el estado aleatorio se conservan en JSON.

## Elecciones

Los cuatro candidatos parten con apoyo 25. Para la publicación relacionada con un candidato: compartir verdadera añade 2+alcance; compartir falsa resta 2+alcance; verificar verdadera añade 4; verificar falsa añade 2; retirar contenido dañino añade 2. Las opiniones no cambian apoyo. Cada apoyo tiene mínimo 1. El bonus del perfil Candidato se conserva únicamente para datos de partidas anteriores. Los porcentajes se calculan sobre la suma de apoyos; el máximo gana y los empates se muestran explícitamente.

El final social usa (confianza + convivencia + bienestar + información verificada − desinformación − conflictos) / 4. Con al menos 50 se muestra «Comunidad informada»; de lo contrario, un cierre de reconstrucción de confianza. El resultado depende del historial real, sin partidos ni referentes políticos reales.

## Red y persistencia

Mensajes JSON UTF-8 con salto de línea y máximo 65.536 bytes. El servidor valida rol, turno, publicación, fase y revisión. Mantiene el estado y serializa acciones con RLock. No recibe estados ni puntuaciones calculadas por clientes. Todas las personas deben confirmar lectura antes del siguiente turno. Un timeout se inicia cuando el participante activo presenta sus opciones. La preferencia temporal del anfitrión gobierna toda la sala. Las salas admiten de dos a cuatro participantes con ciudadano o periodista; se permite repetir personaje y cada persona conserva identidad, turno y puntuación propios.

La desconexión conserva el participante, historial y turno, y pausa la fase y el plazo restante. Una reconexión con el token privado de esa sesión recupera al participante; la fase se reanuda al estar todos conectados. El token solo se entrega a su cliente y permanece en memoria. No se recupera una sala cuyo servidor se haya cerrado. La cuenta regresiva de la ventana representa el plazo del servidor; llegar a cero espera el resultado autoritativo.

La versión 1 del guardado conserva publicaciones activas en preorden (para reconstruir la forma del ABB), red, jugadores, turno, eventos, historial y estado del generador aleatorio. No serializa objetos Qt. Guardar/cargar está habilitado para modo individual; el servidor conserva el estado de la campaña en red.
