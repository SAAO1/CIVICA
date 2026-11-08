# Doblaje neuronal de CIVICA

Los MP3 son voces sintéticas neuronales preproducidas de Microsoft: Gonzalo
(Colombia) interpreta al ciudadano; Salomé (Colombia), a la periodista; Jorge
(México), al narrador. La campaña completa añade Dalia para Valeria Cruz,
Álvaro para Juan Torres, Tomás para Adrián Morales, Elvira para Laura Ríos y
Catalina para Camila Vega. Las ocho identidades son distintas. El paquete
reúne 1.587 clips. No son grabaciones de actores humanos.

El juego reproduce archivos locales con Qt Multimedia y no llama a un servicio
de síntesis. Se eliminó la selección automática de voces de Windows. La música
y el ambiente bajan mientras habla un personaje; cambiar de diálogo o silenciar
cancela la toma anterior. El manifest incluye la envolvente de energía cada
50 ms para acompañar las voces con animación labial.

Se producen líneas completas para mantener las pausas entre frases. Las frases
individuales permiten recombinar variantes de resultados. Las consecuencias
con nombres personalizados usan una toma del narrador que dice «del grupo» y
conserva las cifras. Una línea importada que no esté grabada conserva sus
subtítulos y no activa automáticamente una voz distinta.

Para ampliar el guion, ejecutar desde la raíz:

```powershell
python -m pip install --target .tmp/deps -r herramientas/requirements_voces.txt
python herramientas/producir_voces.py --inventario
python herramientas/producir_voces.py --concurrencia 3
python herramientas/comprobar_voces.py --reproducir
```

La producción necesita conexión; se reanuda por hash y no vuelve a descargar
clips terminados. El inventario recorre las 4096 secuencias de decisiones de
cada rol para recoger recuerdos, reacciones, alcance y cambios de indicadores.
También consulta los 19 emisores posibles del grafo, la conexión Pedro–Inés y
variantes del descenso de conflictos. Los bloques de indicadores permiten
recombinar cifras de partidas con eventos sin cambiar su significado.
No modifica partidas guardadas ni el generador aleatorio del juego.

Las decisiones actuales añaden un inventario rápido de las ocho acciones por
oficio: rutas constantes y parejas de decisiones, cuatro emisores y eventos.
Se actualiza sin recorrer combinaciones exhaustivas:

```powershell
python herramientas/producir_voces_roles.py --inventario --solo-faltantes
python herramientas/producir_voces_roles.py --solo-faltantes --concurrencia 3
```

Los actos IV a VII declaran 191 líneas únicas y sus ramas finitas. El inventario
de siete actos incluye sus fragmentos, los contadores y la propagación hasta
diecinueve receptores de la comunidad completa, incluidas Violeta y Valeria.
No recorre combinaciones exhaustivas de catorce decisiones. La ampliación
añadió 570 clips y conservó los anteriores; 967 entradas de su inventario
quedaron verificadas por archivo, texto, intérprete, duración y señal.

```powershell
python -B herramientas/producir_voces_siete_actos.py --inventario
python -B herramientas/producir_voces_siete_actos.py --solo-faltantes --concurrencia 3
python -B herramientas/producir_voces_siete_actos.py --verificar
```

Los resultados numéricos también tienen tomas completas cortas: por ejemplo,
«Confianza más seis». `narrar_secuencia` valida todos los archivos antes de
arrancar y avisa del comienzo real de cada clip mediante `segmento_iniciado`.
La tarjeta central puede animar su número en ese momento sin insertar la lista
de cifras en el subtítulo. Si faltan voces o se han silenciado, la interfaz
conserva su animación temporizada. Los cambios se calculan desde los valores
anteriores y posteriores del registro; nunca desde un delta que se recortó al
llegar a cero o cien. Cambiar de escena invalida también los clips pendientes.

Fuentes: [voces de Microsoft](https://learn.microsoft.com/azure/ai-services/speech-service/language-support)
y [herramienta edge-tts](https://github.com/rany2/edge-tts).
