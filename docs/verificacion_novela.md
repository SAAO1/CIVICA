> Informe histórico previo al pulido. Consultar la [verificación actual](verificacion_pulido_visual.md).

# Verificación final de la novela visual

La versión del 7 de noviembre de 2026 conserva la novela visual original y sus voces neuronales e integra la investigación en seis actos.

Resultado final: **412 pruebas correctas**, sin fallas, errores ni omisiones, en **177,796 segundos**. El [informe JSON](verificacion_novela.json) y el [registro completo](verificacion_novela.txt) conservan el resultado de la ejecución terminada.

Se recorrieron los seis actos con Ciudadano y Periodista en solitario. Las pruebas verifican investigación, decisiones, consecuencias, guardado actual y compatibilidad con guardados anteriores. Las pruebas históricas siguen comprobando ABB, grafo, propagacion y resultado electoral.

La cooperación se comprobo con dos ventanas reales y TCP: reserva exclusiva de roles, ambas decisiones sobre el mismo acto, avance coordinado, privacidad de hallazgos, desconexión y recuperacion. Las regresiones incluyen abrir el cuaderno durante una transición y reconectar sin perder la lectura. Además pasaron treinta reconexiones consecutivas. Estas comprobaciones se realizaron en un equipo; no equivalen a una prueba en dos dispositivos físicos.

Los seis MP4 nuevos decodifican sus 96 cuadros completos, muestran movimiento y no incluyen audio. El GIF conserva 48 cuadros. Se abrieron correctamente las 33 imágenes PNG/JPG; dimensiones y hashes constan en el informe. La reproducción del plano se comprobo tambien dentro de la ventana, con cuadros visibles y botón para adelantarlo.

Capturas de revisión: [diálogo](capturas/novela_dialogo.png), [decisión](capturas/novela_decision.png), [plano animado](capturas/novela_plano.png), [fuentes](capturas/novela_fuentes.png), [entrevista](capturas/novela_entrevista.png) y [editor](capturas/novela_editor.png).

Para repetir la suite desde la carpeta interna del proyecto:

    python -B herramientas/verificar_proyecto.py --log .tmp/verificacion_novela.txt

El arte se generó mediante la herramienta integrada ImageGen; [prompts y procedencia](../assets/novela/origen_arte.json). Los planos son animaciones nativas de esas ilustraciones.
