# CIVICA — Alcalde Digital

Una **novela visual de seis actos** en Ciudad Nova. Conserva personajes, diálogo progresivo, voces neuronales locales y consecuencias narradas. La investigación ocurre sobre las escenas: recuperar un recorte, escuchar una fuente y decidir cómo responder.

## Iniciar

Desde esta carpeta, con Python 3.10 o superior:

    python -m pip install -r requirements.txt
    python -B main.py

También funcionan iniciar.py y python -m interfaz. Para una demostración individual:

    python -B main.py --rol ciudadano --semilla 4 --sin-eventos --sin-limite

Las opciones --sin-audio y --sin-limite permiten ajustar la demostración. La configuración conserva subtítulos, lectura automática, historial, tamaño de texto, contraste y movimiento reducido. --clasica y --legado abren las campañas originales completas.

## Dentro de la novela

El expediente sigue tres pasos: **buscar una fuente → elegir entre tres respuestas → confirmar**. Cada personaje dispone de dos investigaciones por acto. No hay formularios de titular, certeza ni destinatarios: la respuesta adjunta automáticamente una prueba documental del caso actual que el personaje pueda leer. Los hallazgos antiguos permanecen en el historial y las fuentes privadas requieren que el compañero las comparta.

Los testimonios muestran a su fuente real: la madre, el abuelo o Valeria tienen una atribución y un retrato propios. La persona que aparece en la ficha no se confunde con el contacto que mantiene la relación en el grafo.

La escena queda libre de HUD inferior y de llamadas flotantes a investigar o decidir. Después de responder, los siete indicadores y la puntuación aparecen centrados, con letras grandes, en un panel ilustrado opaco sobre el fondo de ciudad. Los valores se animan en 1,2 segundos y la explicación se narra automáticamente. **Espacio, Enter o un clic permiten continuar inmediatamente.**

El narrador presenta planos de contexto y los cuatro candidatos tienen primeros planos animados en el foro. Los clips duran seis segundos, a 1280×720 y 24 fotogramas por segundo. Las transiciones suaves se pueden interrumpir; el movimiento reducido evita esas animaciones.

Después de las consecuencias aparecen **el ABB y el grafo**, con recorridos y comparación de alcance, antes de pasar al siguiente acto. Ambos pertenecen al motor real de la partida y también pueden consultarse desde Partida.

La [guía vigente de inmersión](docs/inmersion_narrativa.md) detalla este recorrido. La [guía de pulido visual](docs/pulido_visual.md) describe el arte, las fuentes y los controles.

## Dos personajes, dos dispositivos

En la portada, abrir **Multijugador**. Una persona crea una sala y comparte su IP LAN y puerto; la otra se une. La sala admite exactamente dos participantes, con los roles exclusivos **Ciudadano** y **Periodista**. El rol ocupado queda desactivado en el otro cliente y las reservas se actualizan en tiempo real.

Los dos investigan el mismo acto y sus hallazgos empiezan privados. Pueden compartir fuentes. Primero decide Ciudadano y después Periodista; ambas decisiones cambian la misma ciudad. Cada persona revisa el árbol y el grafo, y el acto avanza cuando ambas confirman. En solitario actúa el personaje elegido.

El servidor principal escucha en **0.0.0.0** para admitir conexiones LAN. El anfitrión se conecta localmente y comparte su IP LAN; 127.0.0.1 solo comunica instancias del mismo equipo. Si se interrumpe una conexión, la partida se pausa y Partida → Reconectar sala recupera el lugar mientras el servidor siga abierto.

## Organización y entrega

    estructuras/                ABB y grafo propios
    models/                     Publicaciones, ciudadanos, jugadores y ciudad
    juego/                      Reglas, investigación, consecuencias y elección
    interfaz/escenas/            Escenas originales de la novela visual
    interfaz/componentes/       Actores, teléfono, archivo, red y arte
    interfaz/novela/             Investigación, sala, dirección y controles ilustrados
    red/                        Servidor y cliente cooperativos
    audio/                      Reproducción del doblaje neuronal original
    audiovisual/                Renderizadores de los videos originales
    assets/novela/               Arte, controles, planos y manifiestos
    herramientas/               Producción y verificación reproducibles
    tests/                      Pruebas de dominio, interfaz, red y recursos
    docs/                       Arquitectura y sustentación

La ruta de llamadas de las estructuras se explica en [entrega final](docs/entrega_final.md) y [arquitectura](docs/arquitectura.md). El laboratorio original está en docs/laboratorio.

El arte nuevo se generó con la herramienta integrada ImageGen; [prompts y procedencia](assets/novela/origen_arte.json). Los videos animan ese arte mediante cámara, luz y partículas, codificados con FFmpeg. El recorrido principal reproduce el doblaje neuronal original. El prototipo de tablero y sus medios experimentales se conservan fuera del inicio principal en interfaz/feria y assets/feria.

## Verificar

    python -m pip install -r requirements-dev.txt
    python -B herramientas/verificar_proyecto.py --log .tmp/verificacion_ajustes_visuales.txt
    python -B -m ejemplos.demo_integracion

El [informe de verificación vigente](docs/verificacion_ajustes_visuales.md) registra el resultado y alcance de las pruebas de esta versión. Los informes anteriores se conservan como historial. Las comprobaciones locales con dos clientes no sustituyen la prueba física en dos equipos. Esta copia descargada no contiene .git; el equipo debe conservar su repositorio e historial reales.
