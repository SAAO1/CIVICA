> Versión anterior al pulido visual. La guía actual está en [pulido visual](pulido_visual.md).

# Novela visual de seis actos

La entrada principal construye VentanaNovela, una subclase de la VentanaPrincipal original. Las escenas de narración, diálogo, acción, consecuencias y epílogo siguen siendo las originales. El motor SesionInvestigacion coordina los hallazgos y entrega las decisiones al mismo Juego, ABB y grafo utilizados por ellas.

## Interacción

Examinar las fuentes abre un expediente sobre la escena. Los planos nuevos son breves y se pueden adelantar. Las pruebas se inspeccionan antes de confirmar un hallazgo; mover el visor no consume por sí mismo una acción. Las entrevistas cambian la confianza de una fuente. El editor permite identificar una hipótesis, adjuntar evidencia y seleccionar la audiencia inicial.

Las decisiones tienen consecuencias narradas. El archivo y la red se consultan opcionalmente desde Partida, sin obligar a pasar por un tablero entre diálogos. El archivo muestra el ABB activo y el observatorio usa las mismas conexiones del motor.

Los seis actos conservan la progresión de rumores del colegio, parque, fragmento de audio, canal de correcciones, entrada accesible y mensaje sobre el voto. No se añaden actos nuevos.

## Cooperación

ControlCooperativaNovela conecta la ventana original con ServidorCooperativo. La sala admite dos personas y reserva atómicamente los roles Ciudadano y Periodista. El servidor envía a cada persona su vista privada de investigación y una réplica del Juego para presentar las escenas originales.

Cada persona puede investigar mientras la otra lee. Las dos decisiones se aplican al mismo estado del acto. Una revisión de red actualiza hallazgos e indicadores sin reiniciar el diálogo que se está leyendo. La confirmación de ambos permite avanzar al siguiente acto.

## Guardado y compatibilidad

Las partidas individuales nuevas guardan sesión, hallazgos, presupuesto, relaciones y escena. El autoguardado de esta versión se conserva en .civica/novela_autoguardado.json. Las campañas anteriores siguen accesibles mediante --clasica y --legado y conservan su formato de guardado.

El servidor conserva la sesión cooperativa mientras está abierto; una reconexión recupera la identidad y el rol. No se promete recuperación después de cerrar el proceso anfitrión.

## Arte y sonido

assets/novela/ui contiene botones e iconos de mapa de bits, con texto dinámico legible y nombres accesibles. Los prompts y fuentes se registran en origen_arte.json. Las nuevas escenas CG sirven para planos breves de investigación; el manifiesto de recursos registra sus hashes y la producción de videos.

Los videos son animaciones de ilustraciones, con desplazamiento de cámara, luz y partículas. Las voces del recorrido principal son el paquete neuronal original de audio; las nuevas escenas no emplean las voces de Windows del prototipo anterior.

## Verificación

tests/test_novela_integrada.py recorre los seis actos con ambos roles en solitario, comprueba las escenas originales, editor, guardado y consultas de las estructuras. Las pruebas cooperativas verifican las reservas exclusivas, estado compartido y reconexión; la revisión gráfica usa capturas de la ventana real. La suite histórica continúa comprobando ABB, grafo, propagación y audiovisuales anteriores.

El informe docs/verificacion_novela.json registra únicamente ejecuciones terminadas. Los informes anteriores describen sus respectivas versiones.
