# Expansión audiovisual de CIVICA

La campaña completa presenta siete actos y catorce decisiones. A los seis casos anteriores se añaden ocho casos con Valeria Cruz, Juan Torres, Adrián Morales, Laura Ríos y Camila Vega. La ampliación incorpora cuatro fondos, cuatro escenas ilustradas, 25 variantes de personajes, 88 montajes de acción, ocho cortes del narrador y ocho mezclas de ambiente y foley. El doblaje reúne 1.587 MP3 locales y ocho identidades neuronales. [Guion y desenlaces](guion_siete_actos.md), [muestra de los siete actos](vistas/muestra_siete_actos.mp4), [cobertura de voces](verificacion_voces_siete_actos.json).

Se conservan los **contadores individuales obligatorios sincronizados con voz**, los botones de una línea y los 66 montajes de los casos originales. La carga de video usa el primer fotograma real y la pausa conserva el último plano. La campaña clásica mantiene sus seis publicaciones; la campaña completa amplía el relato y conserva las operaciones del ABB y del grafo. [Continuidad y acciones de la etapa anterior](continuidad_y_acciones.md).

## Escenarios y movimiento

| Caso | Escena | Ambiente sonoro |
| --- | --- | --- |
| Colegio #50 | Café exterior, brisa, vapor y luz | Calle peatonal y aves |
| Propuesta #30 | Café interior, polvo iluminado y vapor | Murmullo lejano y vajilla |
| Parque #70 | Parque de tarde, hojas y fuente | Plaza y actividad urbana |
| Biblioteca #20 | Investigación, luz y papeles | Oficina, ventilación y escritura |
| Acusación #60 | Café bajo la lluvia, gotas sólo en los cristales | Lluvia amortiguada desde dentro |
| Encuesta #80 | Plaza al anochecer, reflejos, faroles y fuente | Insectos y viento nocturno |

Los cuatro actos nuevos añaden sus propios lugares:

| Acto y casos | Escena y objetos | Ambiente y efectos |
| --- | --- | --- |
| IV · #90 y #40 | Estudio de Valeria: aro de luz, teléfono y revisión de un recorte | Estudio, teclado y señal de directo |
| V · #100 y #10 | Foro con cuatro atriles, programa educativo y prioridades en discusión | Sala de debate y micrófono |
| VI · #110 y #25 | Redacción nocturna, archivo de audio y carpeta del colegio | Redacción, lluvia amortiguada y revisión de archivo |
| VII · #120 y #35 | Plaza electoral, mapa de accesos y última captura | Actividad de la plaza y papeleta |

Los fondos se animan por capas a resolución de pantalla con `FondoVivo`, también en portada, decisiones, resultados, ABB, observatorio y final. Los edificios mantienen su geometría. Los temporizadores se detienen al ocultar; Reducir movimiento deja un fotograma quieto. La pestaña Escenas permite activar fondos y personajes por separado. Los GIF y MP4 son exportaciones del mismo motor, útiles para revisar o presentar; no se usa un servicio de video durante el juego. [Motor y exportador](AMBIENTES_ANIMADOS.md).

La etapa original incorpora nueve MP4 narrativos y catorce efectos contextuales, con pinturas para colegio, libreta, mapa, libro, lluvia y urna. Los ocho cortes nuevos se enlazan a la primera frase exacta del narrador en cada caso. Los montajes de las decisiones utilizan el caso, el método y el resultado real, con variantes que evitan inventar una reunión sin receptores o retirar un contenido cuyo reporte fue rechazado. Los cortes comparten composición con subtítulos y controles, se pausan con el cuaderno y respetan movimiento reducido. [Producción narrativa anterior](cinematicas_narrativas.md).

## Personajes

Cuatro atlas transparentes, dos por protagonista, contienen 48 fotogramas. El recorte de celdas se realiza en memoria. El repertorio muestra calma, sonrisa, preocupación, sorpresa, enfado, tristeza y pensamiento. Hay variantes de boca y párpados; la voz aporta su energía cada 50 ms. La respiración y el balanceo son discretos. La sombra del personaje que escucha usa el mismo fotograma y reloj, evitando desdoblar la silueta.

Los gestos se eligen a partir del caso y del texto. No añaden decisiones ni modifican indicadores. Los personajes conservan rostro, vestuario y objetos: teléfono del ciudadano; libreta, lápiz y acreditación de la periodista.

Valeria y las cuatro candidaturas añaden cinco estados por persona: neutral, preocupación, decisión, habla y parpadeo. Se conservan las identidades del atlas de candidatos anterior. El cuerpo tiene fondo transparente y permite componer la escena con quien habla y quienes escuchan. La animación de voz selecciona su variante de habla; las preferencias de movimiento siguen aplicándose a estos personajes.

## Doblaje y mezcla

Se incluyen 1.587 clips neuronales locales. Gonzalo, Salomé y Jorge mantienen al ciudadano, la periodista y el narrador. Dalia interpreta a Valeria, Álvaro a Juan, Tomás a Adrián, Elvira a Laura y Catalina a Camila. Las ocho identidades son distintas. Son voces sintéticas, no actores humanos grabados. Las tomas completas mantienen sus pausas; frases y bloques de indicadores permiten recomponer resultados sin síntesis en red. La duración sumada del paquete incluye alternativas: no representa la duración de una campaña. [Producción y fuentes](../assets/audio/voces/LEEME.md).

Cuaderno y Configuración detienen la escritura y el avance automático. Al volver, sólo recuperan la línea y la voz si siguen vigentes; no restauran una escena vieja tras una actualización de red. Auto espera el fin del doblaje. Cambiar de línea, desactivar las voces o silenciar cancela la reproducción. Configuración permite probar las ocho identidades.

La expansión sonora suma ocho ambientes de 45 s, dieciséis efectos y tres piezas musicales de aproximadamente un minuto. Los recursos tienen licencia CC0, con fichas y autores registrados. La música y el ambiente bajan mientras habla el reparto. Efectos de papel, libreta, taza, pasos y puerta acompañan acciones del guion. [Grabaciones, mezclas y créditos](audio_ambiental.md).

Los actos IV a VII agregan cuatro ambientes de 30 segundos y cuatro efectos de directo, micrófono, archivo de audio y papeleta. Se mezclan a partir de las fuentes CC0 locales de la expansión, con ganancias y huellas registradas en [su manifiesto](../assets/audio/siete_actos/manifest.json).

## Epílogo de la campaña completa

Después de la última decisión aparece un cierre de nueve o diez intervenciones con voces de los personajes. La elección determina quién recibe el encargo de gobernar o si queda un recuento pendiente. Los módulos añaden el estado de convivencia de la ciudad, el arco de Valeria, las respuestas de las otras candidaturas y la conversación del colegio.

Los cinco videos de desenlace existentes muestran cuatro investiduras de alcaldía y un recuento para empates. Las 45 combinaciones narrativas son módulos de diálogo, sin atribuirles 45 películas independientes. La reproducción del ganador se selecciona desde el resultado real y precede al panel de cifras del final.

## Recursos y prompts

Las imágenes nuevas se produjeron con la herramienta `image_gen` incorporada, usando los protagonistas y fondos existentes como referencias. Se copiaron al proyecto; no se depende de la carpeta de generación de Codex. No se sustituyeron los originales.

| Carpeta | Entrega y procedencia |
| --- | --- |
| `assets/expansion/expresiones/` | `ciudadano_atlas.png`, `periodista_atlas.png`, `ciudadano_drama_atlas.png`, `periodista_drama_atlas.png`; hojas 4×3 con alfa. [Prompts base](../assets/expansion/expresiones/prompts_base.json), [prompts dramáticos](../assets/expansion/expresiones/prompts_drama.json). |
| `assets/expansion/fondos/` | `cafe_lluvia.png`, `parque_tarde.png`, `plaza_noche.png`. [Prompts exactos](../assets/expansion/fondos/prompts.json). |
| `assets/expansion/movimiento/` | Once GIF y tres MP4 de capas Qt, más PNG de revisión y manifest de hashes. |
| `assets/expansion/acciones_video/` | 66 montajes de decisión de nueve segundos, carteles JPG y cubiertas PNG del primer fotograma; ocho pinturas de actividades. [Prompts](../assets/expansion/acciones_video/ilustraciones/prompts.json), [manifiesto](../assets/expansion/acciones_video/manifest.json). |
| `assets/expansion/siete_actos/personajes/` | Valeria y cuatro candidatos con cinco estados por persona, alfa, prompts y manifiesto propios. |
| `assets/expansion/siete_actos/fondos/` | Estudio, foro, redacción y plaza electoral, sin duplicar los sprites superpuestos. |
| `assets/expansion/siete_actos/ilustraciones/` | Cuatro escenas ilustradas para los actos IV a VII. |
| `assets/expansion/siete_actos/acciones/` | 88 montajes de los ocho casos nuevos y cubiertas de inicio para cada variante. |
| `assets/expansion/siete_actos/videos/` | Ocho MP4 del narrador ligados a frases exactas, carteles y primeros fotogramas reales. |
| `assets/audio/voces/` | MP3 locales, manifest de texto/identidad/duración/envolvente, herramienta reproducible de producción. |
| `assets/audio/expansion/` | 27 WAV, `licencias.json`, `licencias_musica.json` y `CREDITOS.md`. |
| `assets/audio/siete_actos/` | Cuatro ambientes y cuatro efectos mezclados desde fuentes locales CC0, con manifiesto de procedencia. |

El nuevo manifiesto `assets/expansion/audiovisual_manifest.json` registra archivos y huellas. Las animaciones son renderizadas por el motor del proyecto. No se presentan como videos creados por Runway ni como animación corporal completa dibujada cuadro a cuadro.

## Verificación

La producción de voces de los siete actos añadió 570 clips y conservó los existentes. [El informe estricto](verificacion_voces_siete_actos.json) verifica 967 entradas del inventario: archivo presente, texto, intérprete, duración y señal. Las 191 líneas únicas declaradas en el guion y todos sus fragmentos están cubiertos. `herramientas/producir_voces_siete_actos.py` permite revisar el inventario, reanudar sólo lo que falta y repetir la comprobación sin recorrer todas las historias de catorce decisiones.

Las ocho pruebas específicas de guion y doblaje pasaron. Comprueban las 64 combinaciones de caso nuevo y método, las variantes de cero receptores y contactos existentes, la opinión que no se certifica como hecho, las 45 combinaciones modulares de cierre y la ausencia de cambios de estado al consultar escenas. La auditoría del modelo y la recarga están en [auditoria_campana_siete_actos.json](auditoria_campana_siete_actos.json).

La etapa previa registró 177 pruebas correctas, incluidas las campañas locales de dos a cuatro participantes, lectura, cancelación, labios, pausas, accesibilidad y recursos. La reproducción de las tres voces y de una frase compuesta se comprobó con Qt Multimedia. Los catorce archivos anteriores de movimiento y los nueve MP4 narrativos se decodificaron completos. Los nueve cortes se comprobaron dentro de la ventana, contrastando fotogramas reales y capturas; 24 ciclos de cierre verificaron el orden de destrucción multimedia. Los nuevos textos y escenas se revisaron en 1100×700, 1366×768 y 1920×1080.

`python -B herramientas/capturar_audiovisual.py --video` genera dieciocho capturas y una muestra de la escena con voz, música, ambiente y movimiento en `.tmp/capturas_audiovisual/`. Usa preferencias y biblioteca en memoria para no alterar el progreso personal. Se trata de renderizado de revisión, sin atribuir una campaña humana completa o una escucha humana a quien no la realizó.
