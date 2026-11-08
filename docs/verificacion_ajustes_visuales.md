# Verificación de estadísticas y transiciones

**481 pruebas aprobadas**, sin fallos, errores ni omisiones. La suite completa comprueba el código final de esta revisión.

## Cambios visibles

El balance reutiliza el fondo de ciudad y el panel ilustrado original. Las ocho estadísticas se presentan centradas en dos filas, con nombres y cifras más grandes, sobre una superficie opaca. Se revisaron 1100×700 y 1360×720 con tamaños de texto de 16 y 20 píxeles.

Las decisiones ya no tienen descripciones flotantes ni mensajes del mouse en la barra inferior. Las descripciones accesibles permanecen disponibles. La prueba recorre los botones de ambos personajes y comprueba que el tamaño de la escena no cambie al mover el mouse.

Los fundidos capturan el diálogo anterior antes de modificar los personajes o el texto. La entrada de una escena se prepara con las actualizaciones de pantalla suspendidas para evitar mostrar su fondo provisional. Cada captura se utiliza una sola vez, de modo que preparar de nuevo el mismo plano no reinicia una imagen anterior.

La narración automática y el avance inmediato con Enter, Espacio o clic se conservan.

## Pruebas y recorrido

- [Resumen, capturas y huellas del código](verificacion_ajustes_visuales.json).
- [Registro completo de las 481 pruebas](verificacion_ajustes_visuales.txt).
- [Recorrido de los seis actos con ambos personajes](qa_recorrido_ajustes_visuales.json).

El recorrido mediante clics completó doce decisiones, las tres escenas de consecuencias y ABB → grafo antes de cada acto siguiente. Las pruebas adicionales cubren cambios rápidos, primera entrada sin capturar un fondo provisional y preparación repetida del mismo plano.

Las comprobaciones de cooperación usan clientes locales con TCP; no sustituyen una prueba en dos dispositivos físicos. La revisión manual interceptó el autoguardado y utilizó una biblioteca de lectura en memoria.

## Capturas

[Estadísticas a 1360×720](capturas_ajustes_visuales/estadisticas_1360.png) · [Texto grande a 1100×700](capturas_ajustes_visuales/estadisticas_1100_texto_grande.png)

[Inicio](capturas_ajustes_visuales/inicio_sin_barra.png) · [ABB](capturas_ajustes_visuales/arbol.png) · [Grafo](capturas_ajustes_visuales/grafo.png)

Los recursos utilizados son assets/rediseno/fondos/ciudad.png y assets/rediseno/ui/panel.png. No se modificaron las ilustraciones ni los videos existentes.

## Repetir la verificación

Desde la carpeta interna del proyecto:

    python -B herramientas/verificar_proyecto.py --log .tmp/verificacion_ajustes_visuales.txt

Los [informes anteriores](verificacion_inmersion.md) conservan los resultados y capturas de sus versiones respectivas.
