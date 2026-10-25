# Balance escénico, oficios y desenlaces

Ampliación integrada el 24 de octubre de 2026. La revisión actual sustituye la cuadrícula por contadores individuales obligatorios, simplifica los botones y añade 66 montajes de decisiones. [Cambios actuales y continuidad de video](continuidad_y_acciones.md). La [muestra de 68,25 s](vistas/muestra_impacto_roles_finales.mp4) documenta la etapa anterior.

## Las cifras en escena

La tercera consecuencia presenta un balance central, sin lista estadística en el diálogo inferior. Cada toma neuronal de una cifra emite su clave al entrar realmente en `PlayingState`; esa señal enfoca el indicador y anima su valor anterior hasta el posterior. No se estima el instante por la longitud del texto. El resultado usa las diferencias efectivas del registro, incluidos los límites 0–100 y la puntuación acumulada.

Las mejoras y daños tienen signos, colores y sonidos coherentes: reducir desinformación o conflictos se considera una mejora. Cada indicador completa su animación antes del siguiente; Espacio, Enter, clic, Auto y Saltar leído no pueden omitirlo. El último contador permanece centrado, sin cuadrícula final. Sin voces, con una toma ausente o al cancelarse el audio se completan todos los cambios pendientes. Reducir movimiento mantiene los valores quietos con tiempo de lectura. La información también queda en AccessibleName/Description para lectura asistida.

Cuaderno y Configuración pausan la presentación. Minimizar conserva la intervención y su reloj; restaurar respeta una pausa previa. Si el plazo de una decisión vence mientras la ventana está minimizada, se registra una sola decisión y la narración espera a la restauración. Una interrupción de sala pausa texto, voz y video; al reconectar se reconstruye la escena del estado autoritativo.

## Dos oficios distintos

| Ciudadano | Periodista |
| --- | --- |
| Compartir con su grupo: difusión a dos niveles | Contrastar fuentes: revisar y corregir si es falso |
| Escuchar al vecindario: crear vínculo recíproco sin reenviar | Entrevistar: abrir contacto con una fuente sin certificar su testimonio |
| Convocar al barrio: mayor alcance y participación, mayor riesgo con rumores | Desmentir y denunciar: rectificar y retirar contenido falso; penalización si no hay fundamento |
| Seguir sin reenviar: no propaga | Mantener en reserva: prudencia editorial y participación demorada |

Cada ventana multijugador muestra las opciones de su propio participante y sólo habilita al jugador del turno. Se conserva una decisión por publicación y la rotación del servidor. Conversaciones y entrevistas cambian las aristas del grafo compartido. El observatorio traza esas conexiones y compara el alcance actual con una copia del grafo sin ellas, sin otorgar puntos por consultar.

El historial conserva el método, oficio, conexiones creadas y cambios efectivos, de modo que conversaciones, recuerdos, galería y epílogo describen lo ocurrido. Las claves de las cuatro acciones anteriores siguen disponibles para compatibilidad con guardados y clientes previos. [Reglas y API](roles_y_decisiones.md).

## Más escenas y cuatro alcaldías posibles

Se añaden doce MP4 para frases exactas de ciudadano y periodista: tres planos por corte, objetos y trazos animados, voz local completa y último fotograma al terminar. La familia, la hermana de camino al colegio y la periodista entrevistando tienen tres pinturas nuevas, creadas con `image_gen` incorporada e instaladas en `assets/expansion/cinematica/ilustraciones/`. [Prompts exactos](../assets/expansion/cinematica/prompts_personajes.json), [catálogo de personajes](cinematicas_personajes.md).

La fórmula electoral anterior favorecía la mayor cantidad de noticias positivas de Adrián. La nueva normaliza las oportunidades por agenda y considera exposición, correcciones y contactos sociales registrados. El caso de la encuesta tiene un efecto de arrastre propio, sin tratarlo como acusación contra el candidato. No hay sorteo al consultar los resultados y una recarga conserva apoyos y ganador.

Cuatro videos muestran a Juan, Adrián, Laura o Camila en su investidura como alcalde o alcaldesa de Ciudad Nova, con acta, firma, cámara, luces y confeti. Un quinto muestra un recuento cuando hay empate. La escena se puede ampliar, repetir o cerrar para leer los resultados. Son videos compuestos de ilustraciones y objetos animados; las conversaciones conservan sus sprites expresivos. [Cálculo, auditoría y finales](elecciones_y_finales.md).

## Comprobación de la etapa previa

- 239 pruebas aprobadas, cero fallas, errores u omisiones; 164,046 s con el ejecutor oficial.
- 49.152 campañas electorales: cuatro ganadores alcanzables en ciudadano, periodista y multijugador mixto; guardado y recarga comprobados.
- 256 campañas de cobertura de doblaje: 17.636 líneas revisadas, sin voces faltantes.
- Reproducción real del balance completo: seis tomas, tarjeta correcta al comenzar cada voz, valores finales correctos, partida y archivos personales sin cambios.
- Esta etapa instaló 29 MP4: tres ambientes, veintiún cortes narrativos/de personajes y cinco desenlaces. La revisión posterior agrega 66 montajes de acción, para un total de 95.
- 1.017 clips neuronales locales, con 422 nuevos para cifras, oficios y rutas de difusión.

La muestra es una exportación de widgets reales y de los mismos compositores de los videos, con voz completa y mezcla local. No se presenta como grabación de una partida humana ni valoración auditiva humana. [Metadatos](vistas/muestra_impacto_roles_finales.json), [verificación general](verificacion_roles_impacto_finales.json), [voz y balance reales](verificacion_balance_audio.json), [auditoría electoral](verificacion_elecciones.json).

```powershell
python iniciar.py
python -B herramientas/verificar_proyecto.py --log .tmp/verificacion_roles_impacto_finales.txt
python -B herramientas/verificar_balance_real.py
python -B herramientas/muestra_impacto_roles_finales.py
```

Producir y exportar medios requiere herramientas adicionales; el paquete entregado se juega sin conexión con PyQt6 y sus recursos locales. [Inventario con huellas](../assets/expansion/audiovisual_manifest.json).
