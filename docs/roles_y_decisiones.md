# Oficios y decisiones compartidas

La campaña conserva seis publicaciones y una decisión por publicación. El turno
rota entre dos, tres o cuatro participantes. El ciudadano mueve la conversación
vecinal; la periodista trabaja con fuentes y responsabilidad editorial. Los
indicadores, el ABB y el grafo se comparten: una relación creada por alguien
puede ampliar una difusión de otra persona en el siguiente turno.

| Oficio | Decisión | Cambio real |
| --- | --- | --- |
| Ciudadano | Compartir con mi grupo | BFS a dos saltos; el alcance determina beneficios o daño. |
| Ciudadano | Escuchar al vecindario | Crea contacto recíproco con un vecino de su entorno; mejora convivencia y participación sin difundir el titular. |
| Ciudadano | Convocar al barrio | BFS a tres saltos; mayor participación y un daño mayor si moviliza a partir de un rumor. |
| Ciudadano | Seguir sin reenviar | No cambia conexiones ni indicadores; deja la duda pendiente. |
| Periodista | Contrastar las fuentes | Comprueba documentos; una publicación falsa genera una corrección por la red. |
| Periodista | Entrevistar a una fuente | Contacta al emisor o a un testigo si ella misma era emisora; crea las conexiones que faltan. Un testimonio no verifica automáticamente un hecho. |
| Periodista | Desmentir y denunciar | Envía corrección y retira del ABB el contenido falso o dañino. Una denuncia injustificada conserva el contenido y resta credibilidad. |
| Periodista | Mantener en reserva | Estado RESERVADA; prudencia editorial (+1 confianza, +2 bienestar), con demora de participación (-1). No difunde ni verifica. |

Los cambios se limitan al rango 0–100. El historial registra valores anteriores,
posteriores y diferencias efectivas, por lo que una bajada desde cero no se
presenta como un cambio que no ocurrió. Las conexiones se identifican por los
ciudadanos que realmente existen en el grafo; no se crean receptores inventados.

Si vence el plazo, el ciudadano no reenvía y la periodista mantiene el contenido
en reserva. El servidor valida el turno, la publicación y el oficio antes de
aceptar una decisión, y transmite el mismo estado a todos los clientes.

Para conservar guardados y clientes anteriores, siguen admitiéndose las claves
internas `compartir`, `verificar`, `reportar` e `ignorar`. Las opciones actuales
se obtienen de `acciones_para_rol`: nunca presentan al usuario las opciones del
otro oficio. El historial conserva la clave compatible en `accion` y el método
real en `accion_rol`, junto al rol y a las conexiones creadas en `efectos_red`.

Validación: `python -B -m unittest tests.test_acciones_roles tests.test_partida tests.test_red`.
