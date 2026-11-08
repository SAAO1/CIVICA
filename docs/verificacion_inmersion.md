# Verificación final de inmersión

**476 pruebas aprobadas**, sin fallos, errores ni omisiones, en **233,168 segundos**. Corresponden al código final de esta revisión del 7 de noviembre de 2026, incluidos el libro simplificado, las pruebas pertinentes, los videos y los encuadres.

- [Resumen y huellas de archivos](verificacion_inmersion.json).
- [Registro completo de las 476 pruebas](verificacion_inmersion.txt).
- [Guía de la versión](inmersion_narrativa.md).

## Recorridos y errores corregidos

Se completaron los seis actos con Ciudadano y con Periodista mediante clics de investigación, respuesta y confirmación. Las doce decisiones pasaron por las tres escenas de consecuencias y por ABB → grafo, sin duplicar decisiones ni alterar el número de actos.

El avance de las consecuencias se comprobó con Enter y clic; las pruebas incluyen Espacio, voz automática, silencio, voces desactivadas, pausas y reanudación. Los ocho valores corresponden al registro real y aparecen sin tarjetas ni una cubierta azul sobre toda la escena.

La reproducción del fallo del acto V conservó hallazgos de los actos anteriores. La interfaz adjuntó **120:documento** y Confirmar avanzó con cero investigaciones disponibles. Una denuncia infundada sigue teniendo su penalización: avanzar correctamente no convierte una decisión en acertada.

Se comprobaron también el tramo «Contexto» del audio 110 y la actualización del nombre de la prueba cuando un compañero comparte un documento mientras está abierta la confirmación.

- [Recorrido de las doce decisiones](qa_recorrido_inmersion.json).
- [Libro, testimonios, acto V y conservación del progreso](qa_libro_inmersion.json).

## Reproducción y revisión visual

Los cuatro videos de candidatos y el plano de consecuencias entregaron múltiples fotogramas reales diferentes a QVideoSink con el reproductor en marcha. La comprobación descarta confundir una cubierta estática con un video activo.

Las capturas finales muestran el cabello completo de los candidatos, el pie incrustado excluido y la escena visible detrás del balance. Las pruebas de encuadre comparan los píxeles del video y de su cubierta, tres proporciones de ventana, pausas y cambios de plano.

Los nuevos archivos de candidatos tienen seis segundos, 1280×720, 24 fps y 144 fotogramas decodificados. Sus imágenes, videos, cubiertas y productor tienen huellas verificadas. Las voces proceden del paquete neuronal original.

- [Reproducción real y encuadres](qa_video_inmersion.json).
- [Procedencia de las cuatro ilustraciones](../assets/novela/prologo/origen_arte.json).
- [Manifiesto de los cuatro videos](../assets/novela/prologo/videos/manifest.json).

La revisión del libro se realizó a 1100×700 y 1360×720; las capturas persistentes utilizan 1360×720. Los retratos de la madre y del abuelo corresponden a sus testimonios. El autoguardado se interceptó y la biblioteca se mantuvo en memoria durante la revisión manual; los hashes del progreso persistente permanecieron iguales.

## Capturas finales

[Inicio sin barra ni botones flotantes](capturas_inmersion/inicio_sin_barra.png) · [Consecuencias](capturas_inmersion/consecuencia.png)

[Juan](capturas_inmersion/prologo_juan.png) · [Adrián](capturas_inmersion/prologo_adrian.png) · [Laura](capturas_inmersion/prologo_laura.png) · [Camila](capturas_inmersion/prologo_camila.png)

[Madre](capturas_inmersion/libro_fuente_madre.png) · [Abuelo](capturas_inmersion/libro_fuente_abuelo.png) · [Respuestas](capturas_inmersion/libro_respuestas.png) · [Confirmación del acto V](capturas_inmersion/confirmacion_acto_v.png)

[Árbol](capturas_inmersion/arbol.png) · [Grafo](capturas_inmersion/grafo.png)

## Alcance y reproducción

La suite incluye dominio, guardados anteriores, recursos, audio, interfaz, recorridos de campaña y cooperación por TCP. Las comprobaciones con dos clientes locales no equivalen a probar dos dispositivos físicos.

Desde la carpeta interna:

    python -B herramientas/verificar_proyecto.py --log .tmp/verificacion_inmersion_final.txt

Los informes anteriores describen sus versiones respectivas y se conservan como historial. El catálogo de producción de los medios archivados de feria se preservó con sus bytes y hash originales; su manifiesto apunta a esa copia histórica, mientras el juego utiliza el catálogo vigente.
