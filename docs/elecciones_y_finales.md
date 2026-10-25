# Elección y escenas de investidura

El resultado se calcula a partir de la campaña conservada. No se sortean ganadores al abrir la pantalla final: consultar, repetir un video, guardar o recuperar la partida conserva la elección. Los cuatro candidatos pueden conseguir el mayor índice de apoyo. Un empate exacto queda pendiente de recuento público; nunca se inventa una investidura para llenar la pantalla.

## Problemas corregidos

La fórmula anterior premiaba por cada publicación favorable. Adrián tenía dos propuestas verdaderas, Laura una, y Juan y Camila recibían sobre todo acusaciones falsas. Eso favorecía a Adrián incluso antes de valorar la campaña. Ahora cada candidatura dispone del mismo peso total de agenda. Cada noticia representa una fracción de ese peso, según su impacto original; el `+1` de impacto interno que recibe una publicación al compartirse no concede un segundo premio electoral.

Compartir una propuesta verdadera aumenta su visibilidad. Difundir una acusación falsa perjudica a quien señala; contrastarla devuelve apoyo y una rectificación que recorre el grafo amplifica esa recuperación. El alcance procede de los receptores reales del BFS guardado, sin crear contactos para el balance. El caso de la encuesta engañosa es diferente: una falsa expectativa de victoria genera arrastre al difundirse; revisarla deshace esa expectativa, sin tratarla como una acusación penal.

Escuchar al vecindario o entrevistar puede moderar el rechazo automático y abrir espacio al diálogo. Su efecto es pequeño y depende de contactos nuevos reales: dos aristas recíprocas cuentan como un contacto humano. No declara verdadera la publicación, no aumenta por sí mismo el número de verificaciones y no presenta un testimonio como hecho confirmado. Si no se creó un contacto, no concede un bono de apoyo. Las conexiones también cambian los recorridos posteriores de la red.

Los apoyos son índices de simulación, no votos de una población real. Los porcentajes exactos conservan los empates; la interfaz los redondea a una décima y explica ese redondeo. No se reparte una décima sobrante al primer nombre de la lista.

## Videos instalados

`assets/expansion/finales/` contiene cinco MP4 H.264 reales de 12 segundos, 1280 × 720 y 24 fps: Juan, Adrián, Laura, Camila y recuento pendiente. Se conservaron las ilustraciones originales de los candidatos con banda de investidura, en el Palacio Municipal de la ciudad ficticia. Cámara, acta, firma ilustrativa, luces y confeti se animan en capas independientes. No son grabaciones de actores ni animación corporal generada por un modelo de video.

La pantalla final inicia únicamente la escena correspondiente al ganador real. En un empate muestra urnas y revisión pública, sin proclamar a nadie. La vista mantiene candidatos, porcentajes y epílogo disponibles; «Ampliar escena final» permite ver la composición completa, repetirla o volver a los resultados en cualquier momento, incluso mientras carga. Cada escena termina en su último fotograma. Reducir movimiento o desactivar la animación conserva un cartel, sin abrir el decodificador.

El manifiesto conserva dimensiones, duración, fotogramas, fuentes y huellas SHA-256. Cada archivo se decodificó completo después de exportarlo. La música sigue a cargo del gestor de audio del juego; los videos no duplican la mezcla sonora.

## Verificación y reproducción

```powershell
python -B herramientas/auditar_elecciones.py
python -B herramientas/verificar_proyecto.py --patron test_elecciones_equilibradas.py
python -B herramientas/verificar_proyecto.py --patron test_final_videos.py
python -B herramientas/producir_finales.py
python -B herramientas/capturar_finales.py
```

La auditoría recorre 4.096 campañas por modalidad —API anterior, ciudadano, periodista y pareja con roles alternos— en tres semillas: 49.152 campañas. Sus distribuciones y secuencias de ejemplo se guardan en `docs/verificacion_elecciones.json` y `.tmp/auditoria_elecciones.json`. Para cada ruta ganadora y empate encontrado se comprueba además que serializar y restaurar conserva el resultado. Las pruebas adicionales comprueban consultas sin consumo de azar, persistencia de guardados versión 1, efecto del alcance del grafo, las cuatro candidaturas, empate, reproducción local, cierre del reproductor y salto de escena sin modificar la partida.

Las capturas `docs/vistas/final_*.jpg` proceden de seis decisiones ejecutadas realmente: contrastar las noticias de una candidatura y reservar las demás, o reservar todo para el recuento. No se modifica el ganador para preparar esas capturas.
