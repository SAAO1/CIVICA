# Arquitectura de la campaña de investigación

La versión activa se abre por `main.py`, `iniciar.py` o `python -m interfaz`. El enrutador [interfaz/aplicacion.py](../../interfaz/aplicacion.py) carga [interfaz/feria/aplicacion.py](../../interfaz/feria/aplicacion.py) por defecto. La opción `--legado` conserva la novela anterior para compatibilidad; `--clasica` abre su campaña clásica.

## Dominio y presentación

| Módulo | Responsabilidad |
|---|---|
| [SesionInvestigacion](../../juego/investigacion.py) | Presupuesto, hallazgos, propuestas, turnos, editor, relaciones y confirmaciones |
| [casos_feria](../../juego/casos_feria.py) | Seis casos, tres capítulos, pruebas y medios reutilizados del guion |
| [Juego](../../juego/partida.py) | Estado real, ABB, grafo social, consecuencias, historial y elección |
| [TableroInvestigacion](../../interfaz/feria/componentes.py) | Mostrar la vista privada y emitir intenciones de interacción |
| [VentanaInvestigacion](../../interfaz/feria/ventana.py) | Coordinar portada, sala, escena, tablero, preferencias, guardado y red |
| [ServidorCooperativo](../../red/cooperativa.py) | Mantener estado oficial, identidades, roles exclusivos, plazo y sincronización TCP |
| [ClienteCooperativo](../../red/cliente_cooperativo.py) | Transportar comandos y estados; su callback llega a Qt mediante una señal |

El dominio no importa Qt ni sockets. Los widgets no calculan puntuaciones oficiales. La interfaz individual y el servidor llaman los mismos métodos de `SesionInvestigacion`, que a su vez usa el mismo `Juego` de las campañas históricas con `campana="feria"`. El plan activo es `50 → 90 → 110 → 40 → 120 → 35`.

## Árbol y grafo: llamadas que afectan al juego

La publicación entra al ABB mediante `Juego.agregar_publicacion`. Antes de actuar, `Juego.obtener_publicacion_actual` ejecuta `arbol.buscar`; `ServicioPropagacion.simular` vuelve a exigir su presencia y calcula `grafo.bfs`. Los receptores producen un alcance real que entra en `consecuencias` y después en el apoyo electoral.

El [ABB](../../estructuras/bst.py) es propio, no autoequilibrado, con llave `Publicacion.id` y enlaces izquierdo/derecho. Inserción, búsqueda y eliminación cuestan O(h); el peor caso es O(n). Los recorridos cuestan O(n). Una denuncia fundada elimina el contenido del ABB; conservar un registro histórico no lo reinserta.

El [grafo](../../estructuras/grafo.py) es dirigido y usa diccionarios de adyacencia. BFS emplea una cola FIFO, identifica cada receptor una vez y calcula distancias mínimas en saltos; DFS emplea una pila LIFO para explorar. Sin límite de profundidad ambos cuestan O(V + E). No se trata de un grafo ponderado.

El parámetro opcional `contactos` limita los primeros vecinos que reciben el mensaje. Las siguientes expansiones siguen las relaciones reales; elegir un contacto no limita la difusión a una sola persona. La campaña admite hasta dos contactos iniciales. Las firmas anteriores siguen funcionando con `contactos=None`.

Las relaciones narrativas tienen tres estados: distante por debajo de 35, duda entre 35 y 64 y abierto desde 65. Una pérdida de confianza puede eliminar aristas; recuperar una relación puede crearlas. El presupuesto y los hallazgos no sustituyen esas operaciones de la estructura.

El Observatorio recibe `archivo_preorden`, una lista pública en el orden real del ABB, y una instantánea pública del grafo. Puede reconstruir su forma y mostrar recorridos sin aplicar otra decisión ni conceder puntos. Es una inspección de los datos del motor, no una segunda implementación de las reglas.

## Investigación y editor

Cada jugador recibe dos acciones por caso. `investigar`, `examinar` y `entrevistar` validan identidad, fase, presupuesto y contexto antes de registrar un hallazgo. Un valor incorrecto en el visor no consume presupuesto. La evidencia tiene un ID estable, caso, tipo, propietario y condición de compartida.

`proponer` guarda un borrador visible para conversar; `decidir` valida rol y turno antes de llamar a `Juego.ejecutar_accion`. Adjuntar una evidencia ajena que no fue compartida se rechaza. Contrastar, desmentir y rectificar requieren prueba pertinente; declarar una certeza sin respaldo tiene un coste adicional.

La acción pública `rectificar` utiliza la categoría histórica `verificar` para mantener el cálculo electoral. El registro conserva `accion="verificar"`, mientras `accion_rol`, `titulo_accion` y `ultima_accion_rol` conservan la intención Rectificar. La persistencia reconstruye esa misma etiqueta.

La misión de reparación se deriva de receptores y emisores guardados en el historial: diferencia exposición al rumor, recepción de corrección y personas pendientes. No inventa una audiencia distinta de la calculada por el grafo.

## Cooperación, privacidad y fases

La sala activa admite exactamente dos participantes y los roles Ciudadano/Periodista son exclusivos. Las reservas se hacen en el servidor. El observador de la sala no se convierte en jugador activo hasta comenzar con ambos roles presentes.

El ciclo es `sala → investigacion → decision → resultado → siguiente caso/final`. Ciudadano actúa primero; Periodista, después. Cada uno aplica una sola decisión en el mismo caso. Quien todavía no decidió puede seguir investigando dentro de su presupuesto. El siguiente caso necesita la confirmación de ambos. Así, seis casos producen doce decisiones en cooperación y seis en individual.

`vista(id)` filtra el contenido de las evidencias: incluye las propias y las compartidas. De los hallazgos ajenos aún privados solo aparecen metadatos para poder solicitarlos. `datos()` conserva el estado completo para persistencia; no es el objeto que el servidor envía indiscriminadamente a los clientes. El historial público excluye el contenido privado de las pruebas.

Los mensajes utilizan el [protocolo JSON/TCP existente](../../red/protocolo.py), con tramas delimitadas y tamaño máximo. El servidor aplica cada comando con la identidad de su conexión, comprueba caso/revisión en las decisiones y evita repeticiones de solicitudes. Las puntuaciones enviadas por un cliente no son autoridad.

La sala escucha en `0.0.0.0` y muestra direcciones LAN. Las desconexiones pausan su estado y plazo; un token privado permite recuperar la identidad mientras siga vivo el servidor. No existe migración de anfitrión ni recuperación de una sala después de cerrar ese proceso.

La implementación coordina dos conexiones de participantes, pensadas para dos dispositivos. Las pruebas automatizadas pueden usar conexiones locales en una misma máquina; no constituyen una prueba física en dos equipos diferentes. El PDF archivado menciona dos a cuatro jugadores: el alcance actual de dos personas sigue la aclaración del proyecto y no reescribe esa fuente histórica.

## Tiempo, persistencia y compatibilidad

Los sucesos aleatorios proceden de `random.Random(semilla)` dentro de `Juego`. Las alertas publican un límite de decisión; el servidor inicia y mantiene el plazo autoritativo cuando se presentan las opciones del participante activo. En individual lo coordina la ventana. `expirar_turno` valida primero al actor y aplica Ignorar o Reservar. Nunca comparte por agotar el tiempo.

Los comandos inválidos de turno se rechazan antes de modificar la ciudad, el presupuesto, las relaciones o el historial. Las pruebas comparan estados completos antes y después de estos errores y de una segunda expiración.

El JSON de `SesionInvestigacion` conserva juego, semilla y estado aleatorio, fase, revisión, presupuesto, evidencias, propuestas, solicitudes, decisiones, confirmaciones, audiencia, visitas y relaciones. `Juego.datos` utiliza preorden para conservar la forma del ABB y serializa vértices/aristas del grafo. La restauración no serializa objetos Qt o sockets. El guardado gráfico individual no equivale a guardar una sala TCP.

## Recursos y créditos

Los prompts y referencias exactos de las tres ilustraciones nuevas están en [origen_arte.json](../../assets/feria/origen_arte.json). Las imágenes se generaron con ImageGen. [producir_recursos_feria.py](../../herramientas/producir_recursos_feria.py) conserva esas pinturas y compone documentos y movimiento con QPainter; FFmpeg codifica y decodifica los MP4 y el GIF para comprobarlos. No se presentan esos clips como video generativo.

El audio de investigación usa síntesis local de Microsoft Sabina Desktop en español. Se produjeron tres segmentos con la misma voz para la intervención del caso 110; el fragmento reenviado es exactamente el segmento central del archivo completo. Los ocho WAV son PCM de 24 kHz, 16 bits y un canal. Se incluyen seis aperturas narradas. Las voces son sintéticas, no grabaciones de personas reales.

El [manifiesto de recursos](../../assets/feria/manifest.json) registra dimensiones, duración, fotogramas, hashes, técnica, tipografía y origen. La fuente Atkinson Hyperlegible conserva su licencia SIL OFL. Volver a producir las voces requiere Windows y System.Speech; jugar utiliza los archivos ya incluidos.

## Verificación

Las pruebas del dominio están en [test_investigacion_feria.py](../../tests/test_investigacion_feria.py). Cubren privacidad, presupuesto, pertinencia, ambas decisiones, barrera, audiencia, relaciones, expiración y continuación JSON. [test_recursos_feria.py](../../tests/test_recursos_feria.py) comprueba integridad, diferencias de documentos, decodificación, movimiento real, primera cubierta exacta, GIF y conservación del segmento de audio.

Las pruebas TCP y de interfaz se ejecutan junto a las de las versiones históricas. El ejecutor del proyecto conserva aislamiento de lectura y limpieza de objetos Qt. Se debe citar el informe de la ejecución final actual, sin reutilizar como resultado vigente una cantidad histórica de pruebas.
