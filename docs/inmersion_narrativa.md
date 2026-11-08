# CIVICA: inmersión y recorrido actual

La novela conserva sus seis actos, personajes, voces y decisiones sobre la misma ciudad. La escena ocupa el espacio que antes utilizaba la barra inferior de indicadores. Las cifras aparecen al resolver cada decisión.

## Leer y decidir

Los botones flotantes «Abrir el mensaje» y «Examinar esta prueba» desaparecieron del inicio. La historia se lee con los controles habituales. El cuaderno y «Examinar las fuentes» permiten investigar cuando se desea.

El expediente presenta un recorrido breve:

1. **Buscar:** elegir un lugar o examinar el mensaje. Mover el visor no consume investigaciones; guardar un hallazgo utiliza una.
2. **Responder:** leer la fuente y elegir una de las tres respuestas principales del personaje.
3. **Confirmar:** revisar la respuesta y su prueba adjunta, y confirmar.

Se retiraron los formularios de titular, certeza y destinatarios. La prueba se elige automáticamente entre las fuentes visibles del acto actual. Una prueba de un acto anterior no sirve para respaldar el caso nuevo. Si una acción necesita un documento, la interfaz indica qué falta antes de confirmar; se puede continuar con una respuesta que no publique ni afirme el mensaje.

Cada personaje conserva dos investigaciones por acto. Las fuentes privadas se comparten explícitamente en cooperación. Una fuente recién compartida actualiza tanto el adjunto como su nombre en la confirmación, sin borrar la respuesta elegida.

En el caso del audio, el botón «Contexto» señala el tramo que permite recuperar lo omitido. También se puede explorar con el cursor y leer la transcripción.

## Consecuencias

Los siete indicadores y la puntuación aparecen centrados en dos filas, con nombres y cifras grandes. El balance reutiliza el fondo de ciudad y el panel ilustrado original, con superficie opaca para que ninguna escena lo atraviese.

La explicación comienza automáticamente con las voces neuronales locales. Narra los cambios reales y los puntos; el silencio y la configuración de voces se respetan. **Enter, Espacio o un clic permiten continuar inmediatamente**, aunque la voz siga hablando. La lectura automática espera el final de la voz cuando está activada.

Después se presentan el ABB y el grafo de la misma partida. Recorrerlos no vuelve a otorgar puntos. En cooperación, ambas personas deben terminar su revisión antes del acto siguiente.

Las decisiones ya no muestran descripciones flotantes ni una franja al pasar el mouse. La ayuda accesible conserva sus descripciones. Los fundidos capturan el plano anterior antes de cambiar actores o texto y cada captura se utiliza una sola vez.

## Videos, retratos y encuadres

La introducción, el diálogo, las reacciones y el epílogo conservan planos contextuales del narrador. La narración de las estadísticas utiliza el fondo de ciudad y el panel opaco del balance. El primer plano del desenlace conserva el video vinculado al resultado electoral.

Juan Torres, Adrián Morales, Laura Ríos y Camila Vega tienen cuatro ilustraciones nuevas y cuatro primeros planos animados propios mientras hablan en el foro. Los archivos duran seis segundos, a 1280×720 y 24 fotogramas por segundo. Se animan con cámara y luz; el doblaje se reproduce por separado.

La presentación conserva la parte superior de esos primeros planos para mostrar el cabello completo. Los planos contextuales excluyen el pie que contenía títulos incrustados, evitando que se superpongan con el diálogo o el balance. La cubierta y el video utilizan el mismo encuadre. Los archivos originales y sus huellas permanecen intactos.

El modo de movimiento reducido y la opción de desactivar fondos animados conservan una imagen de respaldo. Los fundidos entre escenas y planos respetan esas preferencias.

Los testimonios identifican a su fuente: una madre tiene un retrato femenino y el abuelo utiliza su imagen de la jornada electoral. La persona que habla se distingue del contacto utilizado por el grafo para registrar una relación. Los guardados anteriores recuperan estas atribuciones al cargarse.

## Juego individual y cooperación

En solitario sólo decide el personaje elegido. En cooperación participan dos personas con roles exclusivos: Ciudadano y Periodista. Las reservas se actualizan en tiempo real; ambas decisiones afectan a la ciudad compartida.

El avance, las pausas de conexión, la privacidad de las fuentes y la revisión ABB → grafo conservan la autoridad del servidor.

## Abrir esta versión

Desde la carpeta interna que contiene main.py:

    python -B main.py

Desde la carpeta exterior de esta descarga:

    python -B CIVICA-main/main.py

Una aplicación que ya estaba abierta debe cerrarse y abrirse de nuevo para cargar el código actualizado.

## Evidencia y procedencia

La [verificación final](verificacion_ajustes_visuales.md) contiene el resultado de las pruebas y enlaces a capturas de la ventana real.

- [Estadísticas centradas](capturas_ajustes_visuales/estadisticas_1360.png).
- [Camila en el foro](capturas_inmersion/prologo_camila.png).
- [Testimonio de la madre](capturas_inmersion/libro_fuente_madre.png).
- [Confirmación del acto V](capturas_inmersion/confirmacion_acto_v.png).
- [ABB](capturas_inmersion/arbol.png) y [grafo](capturas_inmersion/grafo.png).
- [Procedencia de las cuatro ilustraciones](../assets/novela/prologo/origen_arte.json) y [manifiesto de los nuevos videos](../assets/novela/prologo/videos/manifest.json).
- [Manifiesto de planos contextuales](../assets/novela/pulido/videos/manifest.json).

Los medios archivados del prototipo conservan su [catálogo original de producción](../assets/feria/fuentes/README.md). El recorrido principal utiliza la novela y su paquete de voces original.
