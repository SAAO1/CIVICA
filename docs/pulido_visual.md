# Pulido visual de CIVICA

Esta guía describe la presentación actual de la novela de seis actos. El recorrido completo está en la [guía vigente de inmersión](inmersion_narrativa.md) y su evidencia en la [verificación vigente](verificacion_ajustes_visuales.md). Los informes anteriores de pulido se conservan como historial.

## Selección y reparto

La selección muestra Ciudadano y Periodista con sus retratos. En cooperación, cada rol es exclusivo y la disponibilidad de la sala se actualiza antes de elegir.

Juan Torres, Adrián Morales, Laura Ríos y Camila Vega participan desde el primer acto. El foro inicial y la discusión de prioridades del cuarto acto incorporan diecisiete frases que ya tenían doblaje; la campaña mantiene seis actos.

Los cuatro candidatos tienen primeros planos animados propios en el foro. Valeria y las candidaturas disponen de veinte imágenes nuevas de reflexión, sorpresa, enfado y tristeza; Ciudadano y Periodista conservan sus siete emociones. Los presentes también reaccionan a las consecuencias reales del caso actual. Estas reacciones no cambian los cálculos de la ciudad.

## Una fuente, tres respuestas y una confirmación

1. **Buscar una fuente:** elegir un lugar, leer un testimonio o recuperar el contexto del mensaje.
2. **Responder:** elegir entre tres respuestas breves. Cuando una opción necesita un documento, se indica qué falta antes de confirmar; una respuesta prudente permite seguir sin esa prueba.
3. **Confirmar:** revisar la acción elegida y confirmarla una sola vez.

Cada personaje dispone de dos investigaciones por acto. Abrir y mover el visor no consume acciones; guardar un hallazgo consume una. El expediente no presenta formularios ni selectores de titular, certeza o destinatarios.

La prueba se adjunta automáticamente entre los documentos, piezas completas o contextos visibles del acto actual. Un hallazgo de otro acto no se elige como respaldo. En cooperación, las fuentes privadas se solicitan y comparten explícitamente.

Los testimonios conservan sus autores y textos: la madre utiliza un retrato femenino; el abuelo, un recorte de la ilustración de la jornada; Valeria, su retrato propio. Esta atribución se distingue del contacto que mantiene la relación en el grafo y también se recupera al cargar guardados anteriores.

## Escenas y consecuencias

El recorrido principal deja libre la escena: se retiraron el HUD inferior y las llamadas flotantes a investigar o decidir. La investigación se abre cuando corresponde al recorrido de la novela.

Después de responder, **los siete indicadores y la puntuación** se muestran centrados y con letras grandes en un panel ilustrado opaco sobre el fondo de ciudad reutilizado. Los valores se animan en 1,2 segundos y la explicación hablada comienza automáticamente. Espacio, Enter o un clic permiten adelantar inmediatamente; la narración no obliga a esperar para continuar.

El antiguo botón opcional «Escuchar explicación» se retiró de este recorrido. La explicación forma parte de las consecuencias narradas y el jugador conserva el control del avance.

Después aparecen **el ABB y el grafo**. Sus datos pertenecen a la misma partida; se pueden recorrer y comparar sin volver a otorgar puntos. En cooperación, cada persona termina su revisión y ambas confirman antes de avanzar.

## Arte, planos y sonido

La interfaz utiliza azul marino y dorado; el expediente conserva papel crema y texto oscuro. Los planos del narrador corresponden al café, el estudio de Valeria, el audio en la redacción, las correcciones, el acceso electoral, el mensaje sobre votos y el foro.

Los planos de contexto y los cuatro primeros planos de candidatos duran seis segundos, a 1280×720 y 24 fotogramas por segundo. Son animaciones de ilustraciones de ImageGen, con cámara, luces y tipografías empaquetadas. Las voces se reproducen por separado desde el paquete neuronal original.

Los cambios entre cuadros y escenas utilizan un fundido de 520 ms con un acento dorado suave. La transición se puede interrumpir y no captura clics ni bloquea controles. El movimiento reducido la omite.

Cuatro efectos breves acompañan descubrimientos, conexiones e interacciones, respetando volumen y silencio. Los sonidos responden a acciones o cambios reales; una revisión de red o un paso del reloj no repite el efecto.

## Evidencia y procedencia

La [verificación vigente de inmersión](verificacion_ajustes_visuales.md) contiene los resultados actuales. La [verificación anterior de pulido](verificacion_pulido_visual.md) y sus [capturas](capturas_pulido/seleccion_personajes.png) documentan la etapa anterior.

Los [prompts y la procedencia](../assets/novela/pulido/origen_arte.json) registran la creación con ImageGen. El [manifiesto de planos contextuales](../assets/novela/pulido/videos/manifest.json) conserva fuentes, hashes y decodificación; los [primeros planos de candidatos](../assets/novela/prologo/videos/manifest.json) tienen su propio registro audiovisual.
