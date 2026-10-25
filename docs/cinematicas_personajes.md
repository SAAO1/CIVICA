# Videos de las conversaciones

Doce insertos acompañan las intervenciones principales del ciudadano y de la periodista en los seis casos. Se añaden a los nueve cortes del narrador. Cada video dura 12 segundos, a 1280×720 y 24 fps: 144 segundos y 3456 fotogramas nuevos.

| Caso | Ciudadano | Periodista |
| --- | --- | --- |
| Colegio | Su hermana camino del colegio, la fachada en funcionamiento y la preocupación familiar | Escuchar a una vecina, abrir la libreta y buscar el comunicado completo |
| Cultura | Conversación con el abuelo y el libro que los conecta | Preguntas sobre contenido, plazo y recursos de la propuesta |
| Parque | Su hermana, el recorrido sobre el mapa y el sendero del parque | Ruta animada y preguntas sobre fechas y zonas afectadas |
| Biblioteca | El libro del abuelo, una página que gira y el lugar de investigación | Comparación entre anuncio, proyecto aprobado y obra terminada |
| Acusación | Teléfono, conexiones entre mensajes y lluvia; el contenido sigue sin verificar | Escuchar, pedir una fuente y contrastar antes de publicar |
| Encuesta | Conversación con el abuelo, urna preparada y plaza nocturna | Preguntas sobre fecha, muestra y método de la encuesta |

Cada inserto tiene tres planos con cambio de pintura, cámara, disolución y objetos animados. Las tres ilustraciones nuevas muestran al ciudadano con su abuelo, al ciudadano con su hermana y a la periodista entrevistando a una vecina. Las voces neuronales existentes corresponden exactamente a las doce frases: no se cambian por una voz del sistema. [Contacto de las nuevas situaciones](vistas/cinematicas_personajes.jpg).

El disparador compara **rol y frase completa**, normalizando espacios y acentos Unicode. Una cita dicha por otro personaje, una frase incompleta o una consecuencia con cifras variables no dispara estos videos. Se ocultan los sprites durante el inserto para evitar duplicar a los protagonistas. Al terminar, el último plano queda visible hasta continuar; no se repite el montaje. El siguiente diálogo restaura el escenario y los actores cuando corresponde.

El colegio no aparece clausurado, una propuesta no se presenta como inauguración y la encuesta no determina al ganador. La urna del diálogo del ciudadano permanece preparada: su voto todavía no ha sucedido.

`assets/expansion/cinematica/manifest.json` registra los 21 MP4, sus carteles, cubiertas `_inicio.png`, fotogramas, dimensiones, huellas SHA-256 y fuentes. La cubierta es el primer fotograma extraído del MP4 terminado; el cartel JPG sólo sirve para movimiento reducido o respaldo. Pausar congela el plano que se estaba viendo y reanudar conserva esa cubierta hasta completar la búsqueda. La exportación comprueba la decodificación completa antes de reemplazar cada video final. La reproducción es local, sin audio incrustado; voz, música y ambientes siguen mezclándose en el juego. [Continuidad y los 66 montajes de decisiones](continuidad_y_acciones.md).

```powershell
python -B herramientas/producir_cinematicas.py --personajes
python -B herramientas/producir_cinematicas.py --personajes --rol periodista
python -B herramientas/verificar_cinematicas.py
python -B herramientas/capturar_cinematicas.py --clave person_colegio_c --destino .tmp/colegio_con_voz.mp4
```

La revisión real de los 21 cortes comprobó video visible en la ventana, cambio de fotograma, pausa/reanudación, cartel con movimiento reducido, descarga de la fuente y regreso de los actores. Las pruebas del catálogo también verifican que una intervención del ciudadano no active el corte de la periodista, y que los cambios de rol actualicen la política de repetición al reutilizar el reproductor.
