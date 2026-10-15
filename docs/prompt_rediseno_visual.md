# Prompt para ChatGPT: rediseño visual completo de CIVICA

> Encargo previo conservado como referencia. El paquete visual ya se generó e integró; consulta [rediseno_visual.md](rediseno_visual.md) para el estado actual.

Copia desde «Actúa…» hasta el final. Este documento describe el estado funcional del proyecto y los recursos que se deben producir; no afirma que el nuevo arte exista. Fecha de referencia: 14 de octubre de 2026.

---

Actúa como director de arte, ilustrador y diseñador de interfaz de CIVICA — Alcalde Digital, una novela visual educativa de la Universidad del Norte, desarrollada en Python y PyQt6. Ya conoces el estilo creativo aprobado en esta conversación: úsalo como referencia principal y conserva la identidad de los personajes y de Ciudad Nova. No sustituyas ese estilo por un panel administrativo genérico.

Necesito un paquete visual completo y coherente para renovar cómo se ve el videojuego. La lógica funciona; quiero mejorar composición, fondos, personajes, interfaz, iconos, botones, legibilidad y animaciones. Después entregaré tus archivos a Codex para integrarlos. No tienes acceso al repositorio por recibir este texto: no afirmes haberlo abierto ni modificado.

## 1. Decisiones ya tomadas

- Los únicos personajes seleccionables son EL CIUDADANO y LA PERIODISTA. Conserva su diseño aprobado y su identidad visual entre escenas, retratos y expresiones.
- El influencer y los candidatos son personajes de la historia, NO opciones de selección. El influencer no tiene actualmente una escena o un sprite propio integrado: cualquier aparición nueva debe indicarse como propuesta.
- Existen cuatro candidatos ficticios: Juan Torres, Adrián Morales, Laura Ríos y Camila Vega. Son personajes narrativos de la elección, no cuatro protagonistas jugables.
- Los habitantes que aparecen como nodos del grafo no son personajes seleccionables.
- Se conserva el multijugador local de 2–4 participantes. Pueden repetirse ciudadano o periodista; cada participante mantiene nombre, turno y puntuación independientes. Dos personajes seleccionables no significa un máximo de dos jugadores.
- El audio actual me gusta. NO pido reemplazarlo ni volver a producirlo. Diseña señales visuales compatibles con sus notificaciones, decisiones, recompensas y cuenta regresiva.
- No necesito cambiar las reglas, eliminar botones, reducir funcionalidades ni añadir nuevas mecánicas para justificar una ilustración.

## 2. Estado funcional que el diseño debe respetar

Actualmente funcionan:

1. Portada, selección de personaje, tres introducciones, conversaciones y decisiones.
2. Escritura progresiva; una interacción revela el texto y la siguiente continúa. Entradas repetidas protegidas, transiciones, animaciones de personajes y opción de movimiento reducido.
3. Civitas, una red social ficticia: publicaciones, avatar, notificaciones y cuatro acciones: COMPARTIR, VERIFICAR, IGNORAR y REPORTAR.
4. Árbol Binario de Búsqueda (ABB) propio: inserción, búsqueda, eliminación y recorridos inorden, preorden y postorden. Las publicaciones se indexan por ID.
5. Grafo social dirigido propio: vértices, aristas, vecinos, grados, BFS, DFS, alcanzabilidad, caminos mínimos y componentes débiles.
6. Propagación que primero consulta el ABB y después calcula con BFS los receptores únicos, niveles, alcance y tiempo simulado. Una publicación retirada del ABB no puede volver a difundirse.
7. Observatorio con nodos, flechas, selección de ciudadano, consulta de conexiones, animación, pausa/reanudación, velocidad, completar recorrido y comparación de alcance.
8. En individual se pueden agregar/retirar ciudadanos y conectar/desconectar relaciones reales del grafo. Hay participantes y emisores protegidos. Comparar no vuelve a conceder puntos. La edición está deshabilitada en multijugador.
9. Consecuencias sobre confianza, convivencia, bienestar digital, información verificada, desinformación, conflictos y participación; puntos, reputación y logros por participante.
10. Eventos normal, viral, convivencia, discusión y nueva conexión, reproducibles con semilla. Las alertas virales pueden dar 15 segundos para decidir. Se puede desactivar el límite.
11. Reportes fundados que retiran publicaciones y conservan historial; reportes infundados rechazados; verificaciones de rumores que pueden difundir correcciones.
12. Elección entre cuatro candidatos, apoyos dependientes de decisiones, posibilidad de empate, finales variables y epílogo desde el historial real.
13. Guardado/carga individual en JSON y preferencias persistentes.
14. Multijugador local cliente-servidor por sockets, autoridad del servidor, turnos, espera de confirmaciones, pausa por desconexión y reconexión mientras siguen abiertos cliente y servidor.
15. Ayuda, configuración, teclado, F11, contraste configurable, señales visuales y movimiento reducido.
16. Audio integrado con volúmenes general/música/efectos/ambiente, silencio y fundidos. Hay 17 WAV originales: tres músicas, tres ambientes y once efectos. Se conservan.

La última suite ejecutada tiene 36 pruebas correctas. Esto valida lógica e integración; no significa que el rediseño artístico ya esté producido o aprobado.

No diseñes estados visuales que prometan funciones inexistentes, como chat, tienda, inventario, combate, mapa navegable o un editor electoral. Las ilustraciones de lugares no añaden esas mecánicas.

## 3. Dirección visual y legibilidad

Mantén el estilo ilustrado aprobado, la personalidad de Ciudad Nova, la arquitectura, el vestuario y la iluminación coherentes. Quiero una novela visual cuidada, con personajes expresivos e interfaz que pertenezca a ese mundo.

La referencia es el estilo creativo ya trabajado contigo; la interfaz actual sirve para identificar funciones, no como estética que debas imitar. Evita rectángulos enormes que oculten la ilustración, filas interminables de controles, tipografía de títulos usada en párrafos y colores que compitan con el fondo. Organiza la información mediante jerarquía, espaciado y paneles discretos. El observatorio puede usar controles agrupados o plegables, siempre conservando su acceso.

Propón una paleta consistente y entrega sus valores HEX/RGBA, tipografías, tamaños relativos, márgenes, radios, sombras y estados de foco. Los títulos pueden conservar Anton si encaja; el cuerpo necesita una tipografía legible. No inventes licencias ni adjuntes fuentes sin conocer su permiso de uso.

Diseña sobre un lienzo de referencia 1920×1080, 16:9, considerando también 1600×900 y 1366×768. Reserva una zona inferior tranquila para el diálogo, aproximadamente 22–28% de la altura cuando aparezca, sin hornear una franja negra dentro del fondo. Los puntos de atención de la ilustración deben sobrevivir al escalado. Especifica zonas seguras y anclajes; no prometas una resolución que el archivo exportado no tenga.

Mantén contraste suficiente. Los estados del grafo y las alertas deben distinguirse por símbolos/texto/forma además del color. El movimiento debe ser suave y tener alternativa estática. No reveles visualmente que una publicación es falsa antes de que la mecánica lo determine.

## 4. Dos entregables diferentes por pantalla

Necesito AMBAS cosas:

A. Una vista de referencia de la pantalla terminada, mostrando cómo se combinan ilustración, personajes, paneles, textos de ejemplo y controles. Sirve para aprobar composición.

B. Los recursos de producción separados: fondo limpio, sprites, marcos, iconos, capas y estados. Estos son los archivos que se integrarán en PyQt6.

Una captura completa con botones y texto dibujados no reemplaza los recursos separados. Los textos, nombres, cifras, publicaciones, nodos y resultados reales se dibujarán mediante el programa. No conviertas toda la interfaz en una imagen fija.

## 5. Inventario de escenas y fondos

Cada fila necesita una vista de referencia. Puede reutilizarse un fondo cuando la continuidad lo justifique; indícalo en el inventario. Los nombres siguientes son propuestas para la nueva entrega, no archivos ya existentes.

| ID | Pantalla/escena y recursos necesarios | Fondo de producción propuesto |
|---|---|---|
| 01 | Portada: Ciudad Nova, identidad CIVICA, composición para comenzar y accesos principales. Logo separado. | `bg_portada.png` |
| 02 | Selección: SOLO tarjetas del ciudadano y la periodista; retratos, descripción de habilidad y selección/foco visibles. | `bg_seleccion.png` o reutilización declarada |
| 03 | Introducción 1: panorama de Ciudad Nova durante la campaña electoral, alcaldía/plaza, ambiente de ciudad viva. | `bg_ciudad_elecciones.png` |
| 04 | Introducción 2: calle y exterior del Café Central, circulación de información entre vecinos; figurantes discretos, sin duplicar protagonistas. | `bg_cafe_exterior.png` |
| 05 | Introducción 3: se recibe el rumor del colegio en el teléfono. Fondo, mano/teléfono y pantalla separables; pantalla de producción sin el titular fijo. | `bg_calle_telefono.png`, `overlay_telefono_mano.png` |
| 06 | Conversación: interior del Café Central para el ciudadano y la periodista. Espacios de personaje y diálogo coherentes. | `bg_cafe_interior.png` |
| 07 | Decisión Civitas: publicación protagonista, autor/avatar, aviso, tiempo y cuatro botones. Priorizar lectura. | `bg_decisiones.png` o variante del café |
| 08 | Consecuencia 1: reacción inmediata y explicación de la acción. Admite resultados positivos, negativos y neutros. | `bg_consecuencia.png` o reutilización del café |
| 09 | Consecuencia 2: investigación/contraste de fuentes, verificación o explicación del alcance. Escritorio/redacción de la periodista sin ella incrustada. | `bg_investigacion.png` |
| 10 | Consecuencia 3: balance de cambios de ciudad y puntos; continuidad con el café. | `bg_balance.png` o reutilización declarada |
| 11 | Archivo ABB: espacio narrativo para consultar publicaciones, visualizar árbol y tres recorridos; área central despejada. | `bg_archivo_abb.png` |
| 12 | Observatorio de difusión Civitas: espacio visual atractivo para el grafo y sus controles; puede ser un monitor/panel de investigación integrado en el mundo. | `bg_observatorio.png` |
| 13 | Elección/final favorable: comunidad informada, candidato ganador, apoyos y resumen. | `bg_final_comunidad.png` |
| 14 | Elección/final de reconstrucción de confianza: tono reflexivo y empático, sin tratamiento de terror o castigo exagerado. | `bg_final_reconstruccion.png` |
| 15 | Empate electoral: resultado neutral/transparente. Puede reutilizar uno de los fondos finales con un panel distinto. | reutilización declarada o `bg_final_empate.png` |
| 16 | Ayuda: objetivos, reglas, acciones, personajes, indicadores y controles. Diseño legible con desplazamiento. | superficie/modal reutilizable |
| 17 | Configuración/accesibilidad: cuatro volúmenes, silencio, límite temporal, movimiento reducido, contraste y opción existente de superposición de sprites. | superficie/modal reutilizable |
| 18 | Sala multijugador: nombre, dirección, puerto, dos personajes seleccionables, participantes, crear/unirse/iniciar y mensajes de conexión. | `bg_sala.png` o reutilización declarada |
| 19 | Guardar/cargar, confirmaciones y errores: proponer marcos, entradas y estados coherentes con el resto. Actualmente guardar/cargar usa diálogos de archivo. | superficie/modal reutilizable |
| 20 | Estados de espera, reconexión, desconexión y tiempo agotado: overlays claros que no parezcan un cierre del programa. | overlays separados |

Correspondencia con el arte anterior: portada; `Escena 1` ciudad electoral; `Escena 2` exterior/calle del café; `Escena 3` teléfono; `Escena 4/5/8` composición del café reutilizada; `Escena 6/7` investigación reutilizada; `Escena Arbol` fondo compartido por ABB, observatorio y final. Actualmente hay fondos con personajes ya dibujados: necesito fondos limpios para poder colocar sprites sin duplicarlos. Las composiciones especiales con personajes pueden entregarse además como ilustraciones narrativas, claramente diferenciadas.

No hace falta una imagen nueva por cada línea de diálogo ni por cada combinación de puntos. Diseña familias reutilizables y variantes realmente útiles.

## 6. Personajes, retratos y expresiones

Para el ciudadano y la periodista:

- Sprite individual de cuerpo completo, PNG RGBA con alfa real; lienzo objetivo común 1024×2048, mismo encuadre y escala por personaje, sin cortes en cabello/manos/pies.
- Poses orientadas para conversar entre sí; conserva anclaje de pies y posición corporal entre expresiones. Si espejar cambia detalles asimétricos, prepara la variante expresamente.
- Expresiones: neutral, hablando, pensativo/investigando, preocupado, sorprendido, satisfecho y decepcionado/reflexivo.
- Si el vestuario lo permite, poses de uso del teléfono para ciudadano y de libreta/investigación para periodista. Son recursos visuales, no habilidades nuevas.
- Retrato de selección objetivo 768×1024, retrato de diálogo 512×512 y avatar 256×256.
- Una hoja de referencia por personaje para verificar rostro, colores, proporciones y ropa; no usarla como sustituto de PNG individuales.
- Para gestos de habla, ojos/boca alternativos solo si pueden mantenerse alineados y consistentes. No necesito GIFs con cambio de rostro o vibración del cuerpo.

Para los secundarios:

- Retratos consistentes de Juan Torres, Adrián Morales, Laura Ríos y Camila Vega para noticias y elección. Reutiliza las referencias aprobadas de los cuatro alcaldes; no inventes otra apariencia sin señalarlo.
- El influencer, si se utiliza, necesita retrato de NPC y eventualmente sprite narrativo, nunca tarjeta seleccionable. Es ampliación propuesta, no una escena ya integrada.
- Nueve avatares distinguibles para los habitantes del grafo: Ana, Luis, Pedro, María, Carlos, Sofía, Elena, Diego e Inés; y un avatar genérico. Pueden ser retratos simplificados del mismo universo, sin necesitar nueve sprites completos.
- No confundas un participante que elige ciudadano con el nombre Ana que identifica un vértice de la simulación. La asociación de datos la realizará el código.

## 7. Identidad, diálogo, paneles y controles

Crear un sistema visual reutilizable, con recursos separados y medidas documentadas:

- Logo CIVICA y subtítulo Alcalde Digital; identificador de la red social CIVITAS. Versiones sobre fondo claro/oscuro y monograma/icono de aplicación. No inventar escudos oficiales de la universidad.
- Caja de diálogo, placa de nombre, indicador de continuar, marco de retrato y overlay de enfoque del personaje que habla.
- Panel de publicación, panel de resultado, tarjeta de personaje, tarjeta de participante, tarjeta de candidato, panel de elección, resumen y espacio de epílogo desplazable.
- Panel/toolbar de navegación y HUD de ciudad/participante, preferiblemente integrados en la escena en vez de una barra de herramientas con aspecto de aplicación de oficina.
- Marcos para ventanas/modales, mensajes, tooltip, campos de texto, desplegables, sliders, checkboxes, scrollbars y pestañas o grupos de controles si ayudan a ordenar el observatorio.
- Estados normal, al pasar el cursor, presionado, deshabilitado y foco de teclado. Para controles seleccionables, también seleccionado.

Se pueden compartir bases de botón entre funciones. No hace falta renderizar un PNG distinto para cada palabra. Entrega pieles sin texto, iconos aparte y ejemplos con texto como referencia. Los botones se seguirán dibujando como controles reales y podrán cambiar de tamaño. Si propones fondos estirables, especifica zonas de borde/centro para escalado en nueve partes.

Catálogo de funciones que deben conservarse en el diseño:

1. Comenzar historia, elegir ciudadano/periodista y continuar.
2. Compartir, verificar, ignorar, reportar.
3. Inorden, preorden, postorden y continuar desde el ABB.
4. BFS, DFS, conectar, desconectar, comparar alcance.
5. Elegir origen/destino, escribir nombre, agregar ciudadano y retirar seleccionado.
6. Pausar/reanudar, completar animación, velocidad normal/rápida y continuar la historia.
7. Ayuda, volver, configuración, guardar preferencias.
8. Guardar, cargar, portada y alternar pantalla completa.
9. Multijugador, crear sala local, unirse, iniciar campaña y reconectar.
10. Volúmenes general/música/efectos/ambiente, silenciar, movimiento reducido, alto contraste y decisiones sin límite.

El diseño debe indicar cuándo un control está bloqueado por turno, por modo de red o por publicación retirada. No elimines esas indicaciones para conseguir una captura más limpia.

## 8. Iconos, indicadores y notificaciones

Necesito iconos de lenguaje visual consistente, objetivo 128×128 RGBA con lectura clara a 24–32 px; SVG auténtico adicional solo si puedes entregarlo realmente.

Funciones: compartir, verificar, ignorar, reportar, ayuda, ajustes, guardar, cargar, portada, pantalla completa, volver, cerrar, continuar, pausa, reproducir, velocidad, volumen, silencio, conexión, desconexión, reconexión, añadir, retirar, conectar/desconectar relación, comparar, origen y destino.

Datos/estados: confianza, convivencia, bienestar, información verificada, desinformación, conflictos, participación, reputación, puntos, logros, tiempo, turno activo, espera, éxito, error, alerta y publicación retirada. También encabezados/pictogramas de ABB, BFS y DFS si aportan claridad.

Preparar banners/toasts reutilizables para nueva publicación, viralidad, verificación, corrección, reporte aceptado/rechazado, cambio de relaciones, subida/bajada de indicadores, logro, guardado/carga y estados de conexión. Sus textos y valores serán dinámicos.

Logros actuales: Primera verificación, Detección de rumor y Difusión responsable. Entrega tres insignias separadas y sus versiones bloqueadas/desbloqueadas; no inventes logros que el juego no concede.

## 9. Civitas y las seis publicaciones

Diseña la interfaz de teléfono/red social como componentes: marco de teléfono con interior transparente, superficie de pantalla, encabezado, tarjeta de publicación, avatar, espacio para autor/titular, metadatos, aviso y cuatro acciones. Evita una pantalla inclinada que obligue a rasterizar el texto real; si el teléfono inclinado se usa en una ilustración, entrega además una solución frontal para la pantalla interactiva.

Las seis publicaciones actuales son:

- #50: «El candidato Juan quiere cerrar el colegio.»
- #30: «Adrián Morales presentó una nueva propuesta.»
- #70: «El parque central tendrá mantenimiento.»
- #20: «La ciudad construirá una nueva biblioteca.»
- #60: «Circula un rumor sobre uno de los candidatos.»
- #80: «Una encuesta afirma conocer al próximo alcalde.»

Puedes producir seis miniaturas editoriales separadas de referencia, objetivo 960×540: colegio, propuesta, parque, biblioteca, conversación/rumor electoral y encuesta. NO dibujes los titulares, porcentajes ni respuestas dentro de ellas. No marques de antemano una noticia como falsa, verdadera o reportada; esos estados se aplicarán después mediante la interfaz. Estas miniaturas son una ampliación artística para las publicaciones, no una función gráfica actualmente integrada.

## 10. ABB y observatorio: estética con datos reales

Necesito una vista de referencia específica para cada visualizador, además de los recursos separados.

ABB: marco/área de lectura, estados de nodo normal/seleccionado/visitado, espacio para ID de publicación y superficie para mostrar el resultado de los tres recorridos. Las relaciones padre-hijo y los ID se dibujarán en tiempo real. No generes un árbol decorativo fijo como sustituto del ABB.

Observatorio: diseñar área central amplia y legible, marco de ficha de ciudadano, leyenda y controles agrupados. La red inicial tiene estos enlaces dirigidos: Ana→Luis, Ana→Pedro, Luis→María, Pedro→María, María→Carlos, Carlos→Ana, Carlos→Sofía, Sofía→Elena y Elena→Diego. Inés comienza aislada; un evento puede conectar Pedro→Inés.

Preparar estados de nodo: pendiente/no alcanzado, emisor, visitado de exploración, receptor de información falsa, receptor de información verdadera, receptor de corrección y seleccionado para consulta. El emisor debe distinguirse también por forma/borde. Las flechas muestran dirección. Rumor, información verdadera y corrección deben tener símbolos además de colores, con su leyenda.

La escena puede usar avatares en los nodos, pero debe dejar espacio para nombres y conservar clic/selección. Entrega anillos, halos o marcos por separado; las posiciones, conexiones, etiquetas, cantidades y animación del recorrido serán responsabilidad de Qt. El tamaño del grafo puede cambiar cuando se agregan ciudadanos.

IMPORTANTE: no necesito un GIF de un grafo fijo propagándose siempre igual. BFS, DFS y alcance dependen de datos reales. Puedes mostrar una animación de referencia, pero las conexiones y el orden se animarán mediante el programa.

## 11. Elección, resumen y finales

El diseño debe admitir cuatro candidatos, porcentajes variables, ganador o empate y de dos a cuatro participantes con puntos, reputación y logros. Debe incluir indicadores, número de decisiones y epílogo largo sin amontonar texto. El resumen puede tener desplazamiento.

Entrega marcos de candidato, estado ganador/empate, tarjetas de puntuación, separadores, iconos y capas de ambiente del final. No hornees el nombre del alcalde, porcentajes, ganador ni puntuaciones en el fondo. El final favorable y el de reconstrucción deben sentirse parte del mismo mundo.

## 12. Animaciones y formatos

Me interesan: ambiente sutil de portada/ciudad/café, parpadeo/respiración de protagonistas, indicador de continuar, entrada de notificación, alerta viral, brillo breve de verificación/corrección, logro y transición al resultado electoral. Propón solo movimientos compatibles con las referencias y con una opción de movimiento reducido.

Para cada animación entrega: vista previa si puedes, imagen estática de respaldo y especificación de duración/fps/loop. Como objetivo, movimientos ambientales de 3–6 segundos en bucle suave; para interfaces, efectos breves que no retrasen decisiones.

- Fondos: PNG, objetivo 1920×1080, sRGB, normalmente opacos. Si tu herramienta produce otra medida, declara la medida real y conserva composición 16:9 sin estirar caras.
- Sprites, marcos y overlays: PNG RGBA con alfa real. Sin fondo blanco, patrón cuadriculado dibujado ni halos alrededor del recorte.
- Secuencias de animación: PNG RGBA numerados, todos con idéntico lienzo y anclajes; objetivo 12–24 fps según movimiento. Atlas opcional con cuadrícula y dimensiones documentadas.
- GIF: útil como vista previa si puedes producirlo; no es obligatorio ni sustituto de las capas. No lo uses como formato maestro para bordes transparentes suaves o datos del grafo.
- SVG solo si puedes generar un vector válido y editable. No renombres un PNG como SVG.
- Texto y cifras de juego: se dibujarán en Qt; entrega sus estilos y espacio reservado, no imágenes de cada frase.

Si no puedes generar un GIF, archivo por capas, ZIP o tamaño exacto, dilo y entrega los formatos que sí puedas producir. No inventes enlaces, archivos, resoluciones ni exportaciones que no se hayan creado.

## 13. Entrega técnica y nomenclatura

Organiza la entrega propuesta así, sin sobrescribir los originales:

```text
rediseno_civica/
  referencias_pantallas/
  fondos/
  personajes/ciudadano/
  personajes/periodista/
  personajes/npc/
  avatares/
  ui/logos/
  ui/botones/
  ui/paneles/
  ui/iconos/
  ui/indicadores/
  ui/notificaciones/
  ui/logros/
  ui/abb/
  ui/observatorio/
  publicaciones/
  animaciones/
  guia_visual.md
  manifiesto.csv
```

Usa nombres sin espacios ni tildes: por ejemplo `ciudadano_preocupado.png`, `periodista_pensativa.png`, `panel_dialogo.png`, `boton_primario_normal.png`, `boton_primario_foco.png`, `nodo_correccion.png` y `logro_primera_verificacion.png`.

El manifiesto debe indicar ID, nombre de archivo, pantalla/uso, dimensiones reales, formato, transparencia, anclaje o zona segura, variantes, duración/fps cuando proceda, prioridad y estado real de producción. Distingue aprobado, generado y pendiente; no marques como generado un recurso que solo describiste.

La guía debe explicar cómo combinar capas, márgenes de texto, zonas que se pueden estirar, orden de superposición, paleta y tamaños de iconos/tipografía. También qué recursos se comparten entre pantallas. Entrega solo archivos reales que puedas proporcionar.

## 14. Cómo quiero que trabajes

Primero organiza el inventario completo y una propuesta visual coherente. Utiliza como referencia mis diseños ya aprobados; si te falta una referencia imprescindible de personaje, pídemela sin inventar que la has visto.

Después trabaja por lotes pequeños, sin declarar completo el paquete en la primera imagen:

1. Guía visual y vistas de referencia de portada, diálogo, selección de los dos personajes, decisiones, ABB, observatorio y final. Cada vista debe poder inspeccionarse por separado; una lámina general adicional es bienvenida.
2. Fondos limpios de todas las escenas y variantes que se hayan aprobado.
3. Protagonistas, expresiones, retratos, NPC y avatares.
4. Kit de interfaz, botones y estados, iconos, notificaciones, indicadores y logros.
5. Animaciones opcionales, imágenes de respaldo y manifiesto final.

Al terminar cada lote indica los archivos realmente entregados y qué queda. Conserva identidad y escala entre lotes. Comienza con el inventario y la primera propuesta visual; quiero avanzar hasta tener recursos utilizables, no recibir únicamente recomendaciones generales de diseño.

El objetivo es que Codex pueda integrar después un rediseño bonito y consistente conservando ABB, grafos, decisiones, audio y toda la lógica ya comprobada.
