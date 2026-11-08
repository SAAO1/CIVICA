# Campaña completa de Ciudad Nova

La ampliación continúa los tres actos del juego con cuatro actos nuevos y ocho decisiones. La campaña completa conserva el orden original `50 → 30 → 70 → 20 → 60 → 80` y añade `90 → 40 → 100 → 10 → 110 → 25 → 120 → 35`. Los seis primeros casos mantienen sus hechos y sus consecuencias. En la campaña extendida, la encuesta del caso #80 cierra la primera ola de mensajes, en lugar de anunciar la última decisión de la partida.

El laboratorio exige cuatro candidaturas y contempla los roles Ciudadano, Periodista, Influencer y Candidato. No prescribe siete actos ni un guion literal para ellos. Los siete actos son la ampliación narrativa solicitada por el usuario. Valeria Cruz es un personaje original del proyecto. Los candidatos conservan sus identidades anteriores: Juan Torres, Adrián Morales, Laura Ríos y Camila Vega.

`juego/campana_extendida.py` reúne el guion y las fuentes ficticias. Consultarlo no aplica consecuencias, consume azar, añade relaciones ni modifica el resultado electoral. Las decisiones y los receptores proceden de la partida. La campaña clásica permanece disponible para las partidas anteriores.

## Recorrido de los siete actos

| Acto | Casos | Situación y movimiento dramático |
|---|---|---|
| I · Una ciudad que escucha | #50 colegio; #30 propuesta cultural | Una preocupación por la hermana del ciudadano transforma una notificación en un asunto familiar. La periodista empieza a ganarse su confianza. |
| II · Lo que compartimos | #70 parque; #20 biblioteca | La información útil necesita fechas, etapas y accesos. La ilusión del abuelo por una biblioteca conecta los documentos con la vida del barrio. |
| III · La confianza en juego | #60 rumor; #80 encuesta | Un rumor sin firma y una cifra fuera de contexto elevan la tensión. Cuando parece que todos los mensajes ya llegaron, una voz mucho más escuchada pide ayuda. |
| IV · La voz que amplifica | #90 video del parque; #40 canal de correcciones | Valeria admite que su mejor encuadre dejó fuera una puerta abierta. Entre la presión de su representante y los mensajes del público, descubre que corregir exige volver a buscar a quienes escucharon primero. |
| V · Cuatro promesas bajo los focos | #100 plan del colegio; #10 prioridades culturales | El ciudadano lleva al foro una pregunta de su hermana. Las cuatro candidaturas discuten propuestas, límites y prioridades. El abuelo y su vecina encuentran una manera más sencilla de discutir sin dejar de compartir el termo. |
| VI · La noche del audio recortado | #110 audio de Camila; #25 archivo de Juan | Una voz reconocible parece anunciar un cobro por votar. La redacción busca los segundos eliminados y vuelve al archivo del colegio. Encontrar una fuente deja pendiente una llamada familiar que ningún enlace puede reemplazar. |
| VII · La ciudad decide | #120 accesos electorales; #35 comentario y voto | El abuelo necesita una entrada accesible y quiere decidir por sí mismo. Una captura alterada intenta hacer pasar los comentarios de Civitas por votos. La campaña termina en la plaza, con la elección y las relaciones que dejan los mensajes. |

## Los nuevos casos y sus límites

| Caso | Pieza que llega a Civitas | Naturaleza en la ficción | Qué debe conservar su escena |
|---|---|---|---|
| #90 | Un video atribuye a Laura el cierre de todos los parques. | Rumor falso: el archivo completo muestra mantenimiento por sectores y un paso abierto. | Estudio de Valeria, teléfono y encuadre recortado; no representar un cierre real de todos los parques. |
| #40 | Camila presenta un canal público de correcciones con fuentes. | Anuncio respaldado de una propuesta. | Registro de cambios y enlaces; no mostrar una herramienta que ya alcance a toda la ciudad. |
| #100 | Juan propone reparar cubiertas manteniendo las clases. | Propuesta respaldada. | Foro, pregunta familiar y programa; no mostrar el colegio ya reparado. |
| #10 | Adrián considera la cultura la primera prioridad. | Opinión atribuida. | Debate con otras prioridades legítimas; no dar a una valoración un sello de verdad ni tratarla como noticia falsa. |
| #110 | Un audio asegura que Camila cobrará por votar. | Rumor falso: se recorta una advertencia contra ese engaño. | Redacción, audio y continuidad del archivo; reconocer una voz no confirma el sentido del recorte. |
| #25 | El archivo íntegro de Juan explica la continuidad de las clases. | Información respaldada. | Carpeta, entrevista y acta; los documentos no equivalen a obras ejecutadas ni a detalles aún no resueltos. |
| #120 | Laura comparte el mapa oficial de accesos electorales. | Aviso respaldado de la organización electoral. | Plaza, mapa y accesibilidad; la candidatura comparte el aviso, no asigna los puestos. |
| #35 | Una captura atribuida a Adrián dice que comentar sustituye el voto. | Rumor falso: se elimina el «no» de su mensaje. | Plaza y mensaje completo; una encuesta o un comentario no debe mostrarse como votación electoral real. |

Las veinticuatro pistas nuevas son documentos, contextos y testimonios ficticios del mundo de Ciudad Nova. No se usan como información sobre elecciones reales. Leerlas no otorga puntos ni responde un cuestionario. La pista conserva el lugar de una observación; la consecuencia corresponde a la acción tomada después.

## Cinco voces nuevas

Valeria quiere que su comunidad sea escuchada y teme perderla si deja de reaccionar inmediatamente. Tiene humor, reconoce errores y no se convierte en una autoridad infalible. Su conflicto no consiste en tener una audiencia grande, sino en responder por lo que hace circular dentro de ella.

Juan se impacienta con el rumor del colegio, pero debe explicar etapas y responsabilidades. Adrián entusiasma con la cultura y descubre que sus frases necesitan presupuestos y plazos. Laura devuelve la discusión a los accesos y al uso cotidiano de los espacios. Camila defiende herramientas de participación sin prometer que la pantalla sustituirá las decisiones de las personas.

Los tokens de hablante son `INFLUENCER`, `JUAN`, `ADRIAN`, `LAURA` y `CAMILA`. El ciudadano, la periodista y el narrador conservan sus identidades. Los cinco personajes nuevos intervienen en la historia; esta ampliación mantiene las dos perspectivas jugables y sus ocho métodos distintos.

## Decisiones que dejan memoria

Cada caso tiene ocho reacciones específicas: compartir, escuchar, convocar y no reenviar para el ciudadano; contrastar, entrevistar, desmentir y reservar para la periodista. La escena siguiente recuerda la acción anterior mediante frases finitas. Una convocatoria sin receptores no se narra como una reunión. Una denuncia rechazada no se presenta como retirada. Una entrevista y una conversación mantienen su diferencia respecto a la comprobación de un hecho.

El guion contiene respuestas adicionales para alcance cero, relaciones ya existentes, rectificaciones sin receptores y una ciudad con conflictos elevados. Las cifras se conservan en el observatorio y en la animación obligatoria de indicadores; no se vuelven a insertar en el subtítulo como un párrafo de puntuaciones.

## Desenlaces

La elección conserva el cálculo del modelo. El guion acepta a cualquiera de las cuatro candidaturas ganadoras y un empate exacto con recuento pendiente. Un empate no reproduce una proclamación de victoria.

Cada resultado electoral se combina con tres estados de la ciudad:

| Estado narrativo | Calidad calculada por el modelo | Escena de cierre |
|---|---|---|
| Ciudad informada | Al menos 50 | Las diferencias continúan, pero queda una mesa donde se puede conversar y contrastar. |
| Reconstrucción | Desde 20 hasta menos de 50 | Algunas conversaciones vuelven a empezar; otras esperan una explicación o una disculpa. |
| Ciudad fracturada | Menos de 20 | Algunos grupos ya no se hablan. La elección termina y la reparación de los vínculos sigue pendiente. |

Además, Valeria tiene tres arcos: reparación responsable cuando las comprobaciones y rectificaciones fundadas superan las difusiones dañinas de los actos nuevos; crisis cuando persiste la difusión dañina; y silencio cuando no hubo difusión dañina ni una reparación predominante. El desenlace recuerda también si el archivo del colegio abrió una conversación o quedó pendiente.

Esto permite representar 45 combinaciones modulares principales: cinco resultados electorales, tres estados cívicos y tres arcos de Valeria. Son combinaciones de líneas, no una afirmación de que existan 45 películas independientes o de que cada combinación de indicadores se haya alcanzado en una campaña real. Las candidaturas que no ganan mantienen una voz y una tarea posterior; el cierre no las convierte automáticamente en villanas ni las hace desaparecer.

## Voces y comprobaciones del guion

`FRASES_POSIBLES` enumera 191 parejas únicas de hablante y texto: diálogos, memorias, reacciones, efectos y módulos de cierre. El texto no interpola nombres personales ni cifras ilimitadas, por lo que todas sus líneas pueden tener un archivo de voz local. La producción usa voces neuronales sintéticas; estos archivos no representan grabaciones de intérpretes humanos.

`tests/test_guion_siete_actos.py` comprueba el recorrido de catorce casos sin mutaciones por lectura, las 64 combinaciones de caso nuevo y método, el alcance cero, los contactos existentes, la opinión que no se certifica como hecho, el cierre de la primera ola y las 45 combinaciones modulares del epílogo. `tests/test_voces_siete_actos.py` añade identidad, fragmentos y cobertura local estricta. Las ocho pruebas pasaron el 24 de octubre de 2026. El paquete completo tiene 1.587 clips y el [informe de la ampliación](verificacion_voces_siete_actos.json) cubre 967 entradas. La verificación del arte, el transporte audiovisual y la integración general pertenece a las comprobaciones del resto de la aplicación.
