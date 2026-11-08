# Guía de CIVICA · La última hora

Esta versión ofrece una campaña de investigación de seis casos agrupados en tres capítulos. El objetivo es llegar a la elección con una ciudad que conserve confianza, información contrastada y vínculos capaces de hacer llegar las correcciones. Las decisiones individuales cambian esos indicadores y el apoyo de las candidaturas.

## Comenzar

Ejecutar `python -B main.py` desde la carpeta del proyecto. La portada ofrece una historia individual y **Dos voces · Cooperativo en LAN**, además de continuar el guardado disponible, ayuda y ajustes.

En individual se elige Ciudadano o Periodista y se recorre toda la campaña con ese personaje. El acceso a fuentes se amplía para poder completar la investigación sin compañero. En cooperación participan exactamente dos personas: una con cada rol.

| Capítulo | Casos | Trabajo principal |
|---|---|---|
| 1 | La puerta del colegio; El parque fuera de cuadro | Recuperar lo que una captura o un encuadre dejaron fuera |
| 2 | Los segundos que faltan; Un canal que recuerda | Escuchar una intervención y seguir el registro de una corrección |
| 3 | Una entrada para el abuelo; La palabra que borraron | Conservar accesos, contexto y sentido de una publicación electoral |

Los nombres y situaciones pertenecen al mundo ficticio del juego.

## La mesa de investigación

La pantalla tiene cuatro espacios. Se puede cambiar de uno a otro sin atravesar una secuencia obligatoria de películas o contadores.

**Mapa.** Presenta el mensaje recibido y los lugares que se pueden visitar: Archivo público, vecindario y Redacción. Cada participante tiene dos acciones por caso. Visitar una fuente, recuperar un medio o entrevistar consume una oportunidad cuando se obtiene un hallazgo. No es obligatorio gastar las dos para decidir. En cooperación algunas fuentes corresponden a un rol: el Archivo es la perspectiva de la Periodista y el testimonio del barrio, la del Ciudadano.

**Expediente.** Reúne las pistas propias y compartidas. Seleccionar una permite leerla y, en cooperación, enviarla al compañero. Las pistas ajenas aún privadas muestran su existencia y título, pero no su contenido: el botón **Pedir pista** solicita que su propietario la comparta.

El visor permite comparar piezas, recorrer el mapa o situarse en un tramo del audio. Mover el control inspecciona el material; **Examinar este punto** registra el contexto recuperado. Si el tramo no contiene la pieza necesaria, el juego lo indica y no gasta una acción. Una prueba recuperada pasa al expediente y puede adjuntarse.

En el caso de audio se puede escuchar, pausar, buscar una posición y consultar la transcripción. El fragmento recibido y el archivo completo son audios diferentes. **Ver el momento** reproduce una apertura ilustrada opcional; no es necesario terminarla para seguir investigando.

La entrevista permite escoger una pregunta y presentar una prueba disponible. Presionar y escuchar tienen respuestas distintas. Una fuente distante puede pedir evidencia pertinente antes de volver a conversar. La entrevista recoge un testimonio; no lo convierte automáticamente en comprobación documental.

**Redacción.** Se eligen una acción del rol, un titular de hasta 160 caracteres, el grado de certeza y una evidencia. **Compartir borrador** permite proponer la decisión antes de aplicarla. **Tomar esta decisión** la registra y cambia la partida.

**Audiencia.** Se seleccionan como máximo dos contactos directos. **Ver a quién podría llegar** calcula una previsión por el grafo, sin publicar ni conceder puntos. Una ruta puede llevar a personas que no eran contactos directos. La selección inicial y las conexiones reales determinan el alcance final.

## Decidir con un rol

El Ciudadano puede compartir, escuchar al vecindario, convocar, seguir sin reenviar o rectificar con una prueba. La Periodista puede contrastar, entrevistar, desmentir o reservar.

Contrastar, desmentir y rectificar requieren una prueba pertinente, como el documento, el contexto recuperado o la pieza completa del caso. Una prueba de otro caso no demuestra el titular actual. Marcar **Confirmada** sin respaldo puede reducir confianza y puntos; el estado de certeza tiene consecuencias mecánicas.

La decisión también cambia la relación con las personas afectadas. Difundir un rumor puede hacer que una fuente tome distancia y retire conexiones. Escuchar o presentar una corrección fundamentada puede recuperar confianza y abrir vínculos. Esas conexiones pertenecen al grafo y afectan difusiones posteriores.

El apartado de reparación distingue a quienes recibieron el rumor, quienes recibieron una corrección y quienes siguen pendientes. Borrar la publicación del árbol no borra el recuerdo de sus receptores.

## Cómo cooperar en dos dispositivos

Ambos equipos necesitan una copia del proyecto y sus dependencias. Conectarlos a la misma Wi-Fi o LAN.

1. En la portada, abrir **Dos voces · Cooperativo en LAN**.
2. El anfitrión escribe su nombre y pulsa **Crear sala**. La sala muestra sus direcciones LAN y el puerto.
3. En el segundo dispositivo, introducir esa IP y el mismo puerto; escribir otro nombre y pulsar **Unirme a la sala**.
4. Reservar Ciudadano y Periodista. Un rol ocupado queda bloqueado para el otro participante. Se puede liberar la reserva antes de comenzar.
5. El anfitrión inicia cuando estén ambos conectados y los dos roles reservados.

La sala usa TCP y el servidor conserva ciudad, publicaciones, relaciones, puntuaciones y decisiones oficiales. El creador se conecta a su propio servidor; el otro dispositivo usa su IP LAN. `127.0.0.1` identifica al propio equipo y sirve para probar dos instancias en una sola máquina.

Cada persona investiga por su cuenta y decide qué compartir. Ambos actúan sobre la misma publicación: primero Ciudadano, después Periodista. La Periodista puede seguir investigando mientras espera su turno, siempre que conserve presupuesto. La ciudad y la puntuación de cada persona cambian con ambas decisiones.

Después del resultado, cada participante pulsa **Listo para continuar**. El siguiente caso aparece al confirmar los dos. Una desconexión pausa la sala y conserva la identidad. **Reconectar** permite recuperarla mientras sigan abiertos el servidor y la aplicación que conserva su sesión. Cerrar el anfitrión termina la sala; no hay migración a otro equipo.

El alcance actual es de dos personas con roles exclusivos, de acuerdo con la aclaración del proyecto. El PDF archivado describe un alcance más amplio de dos a cuatro jugadores; esa referencia histórica no cambia la configuración actual.

## Alertas y resultados

Algunos eventos tienen un plazo. El contador comienza al presentar las opciones de decisión de quien tiene el turno. Llegar a cero aplica una respuesta prudente: Ciudadano no reenvía y Periodista conserva el mensaje en reserva. Nunca se publica automáticamente por agotar el tiempo.

En individual puede activarse **Decidir sin límite de tiempo**. En cooperación el anfitrión configura esa preferencia para la sala antes de comenzar. Los plazos cooperativos dependen del servidor, no del reloj de cada cliente.

La pantalla de resultado resume lo ocurrido. **Ver los cambios y las decisiones** amplía los detalles; los indicadores y las puntuaciones también aparecen en la cabecera. Tras seis casos se celebra la elección calculada con el historial y el alcance real. Un empate se mantiene como tal.

## Controles y ajustes

| Control | Función |
|---|---|
| Ratón o teclado con Tab y Enter/Espacio | Seleccionar los controles de la pantalla |
| Alt+1, Alt+2, Alt+3, Alt+4 | Mapa, Expediente, Redacción y Audiencia |
| F1 | Ayuda |
| F2 | Observatorio del ABB y del grafo |
| F3 | Historial público de decisiones |
| Ctrl+S | Guardar la partida individual |
| Ctrl+O | Abrir un guardado individual |
| Escape | Abrir ajustes |
| F11 | Alternar pantalla completa |

Los ajustes permiten activar sonido y narración, cambiar volumen y tamaño de texto, usar contraste alto, reducir movimiento y decidir sin límite. Sus valores se conservan en el perfil local. La transcripción permite investigar el audio sin depender de escucharlo. La interfaz señala mensajes y resultados mediante texto y controles, además de color.

## Guardado y límites

La partida individual se guarda automáticamente en `.civica/feria_autoguardado.json` y también mediante Guardar. **Continuar mi partida** recupera ese archivo. Las preferencias están en `.civica/feria_preferencias.json`.

La sesión cooperativa vive en el servidor y se recupera mediante reconexión; Guardar/Cargar individuales no sustituyen ese mecanismo. La cooperación está diseñada para LAN. Las pruebas con conexiones locales no sustituyen la comprobación entre los equipos reales de presentación y su firewall.

Los videos acompañan la investigación con ilustraciones y movimiento nativo; las voces son sintéticas. Si falla la reproducción de un medio, el documento y la transcripción permiten conservar la información del caso.
