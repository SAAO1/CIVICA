# Rediseño visual integrado de CIVICA

El paquete ilustrado está instalado en `assets/rediseno/`. Se generó con la herramienta integrada `image_gen.imagegen`, usando las ilustraciones anteriores como referencias de identidad y estilo. Los archivos originales y el audio se conservan.

## Recursos reales

Hay **23 archivos PNG**, unos **47,1 MiB**, con dimensiones y SHA-256 registrados en [manifiesto.json](../assets/rediseno/manifiesto.json).

| Grupo | Archivos | Uso |
|---|---:|---|
| Fondos | 7 | Portada, panorama electoral, calle del café, café limpio, investigación, observatorio y teléfono |
| Personajes | 7 | Dos sprites neutrales, dos expresiones, dos retratos de selección y atlas de cuatro candidatos |
| Avatares | 1 atlas | Nueve ciudadanos diferentes del grafo |
| Interfaz | 7 | Logo, panel, diálogo, botón, atlas de 24 iconos, medallón de nodo y marca de verificación |
| Publicaciones | 1 atlas | Seis ilustraciones editoriales vinculadas a los ID originales |

Los fondos miden **1672×941**. Los sprites miden **1024×1536**; retratos y atlas ciudadanos/candidatos, **1254×1254**. Las dimensiones restantes son las exportadas por el generador y están registradas sin presentarlas como 1920×1080. El juego escala y recorta los fondos sin deformar su composición.

Cada grupo conserva sus prompts completos y rutas de procedencia en `generacion.json`. No se usó CLI de imagen ni se añadieron dependencias de generación.

## Integración

- **Portada:** nueva plaza al atardecer, marca separada y tarjeta de inicio ilustrada.
- **Selección:** dos tarjetas con retrato, selección por clic/teclado y habilidades; solo ciudadano y periodista.
- **Historia:** café libre de protagonistas incrustados, personajes superpuestos con sus animaciones y expresiones; la periodista adopta una pose pensativa y el ciudadano puede mostrar preocupación según urgencia/conflictos, sin revelar anticipadamente la veracidad.
- **Diálogos:** marco ilustrado continuo, placa de nombre, tipografía de lectura y recordatorio de continuar.
- **Teléfono:** ilustración con pantalla limpia y contenido de Civitas dibujado como texto real.
- **Decisiones:** personaje a la izquierda; publicación, avatar, miniatura y cuatro botones a la derecha. Avisos y tiempo mantienen su lógica.
- **ABB:** marco, nodos ilustrados, altura adaptable y controles de recorridos.
- **Observatorio:** tablero amplio, avatares en nodos, inspector lateral, herramientas por pestañas y reproducción separada. La topología sigue siendo interactiva y dinámica.
- **Elección:** cuatro retratos con resultados variables, puntos/reputación/logros y epílogo desplazable.
- **Navegación/HUD:** iconos coherentes y siete indicadores separados, en lugar de una línea de valores pegados.
- **Ayuda/configuración/sala:** superficies y botones ilustrados. Los checkboxes usan medallón/marca y los sliders un control circular del paquete.

Los marcos y pieles se pintan a partir de imágenes; los textos, el foco, el teclado, las cifras, las aristas y los estados siguen siendo interactivos. No son capturas fijas usadas como sustituto del videojuego. Los atlas se recortan en memoria; sus iconos, avatares y noticias no requieren duplicar archivos.

## Archivos de implementación

`arte.py` carga el paquete, recorta márgenes transparentes, reutiliza atlas y pinta controles. `recursos.py` enlaza nombres originales con el nuevo arte y conserva respaldo. `hud.py` muestra los indicadores. `interfaz.py` y `paneles.py` componen las pantallas sin cambiar las reglas del juego.

Se cargan Segoe UI y Georgia desde las fuentes del sistema cuando están disponibles, sin copiar ni redistribuir esos archivos. Se conservan las alternativas del sistema. Las variantes oscuras de sprites se comparten en caché para evitar duplicar imágenes grandes entre escenas y participantes.

## Revisión y reproducción

La suite prueba tanto la lógica como el teclado/estado de los controles ilustrados, selección de personajes, operaciones del observatorio, carga de PNG, dimensiones, alfa y huellas del manifiesto. Las pruebas de campaña y multijugador se mantienen.

Última ejecución: **42 pruebas correctas en 51,689 segundos**. Se abrió también la versión rediseñada como aplicación de Windows.

Vistas del juego integrado: [portada](vistas/01_portada.png), [diálogo](vistas/05_dialogo.png), [decisiones](vistas/06_decision.png), [ABB](vistas/10_abb.png), [observatorio](vistas/11_observatorio.png), [elección](vistas/12_final.png), [selección](vistas/13_seleccion.png) y [configuración](vistas/16_configuracion.png).

Para regenerar capturas de las **16 pantallas/estados principales**:

```powershell
python -B herramientas/capturar_diseno.py
```

Las capturas se guardan en `.tmp/capturas_rediseno/`. Son renderizados de las pantallas reales de Qt. Los nuevos PNG son recursos estáticos; se reutilizan con las animaciones del juego. No se presenta como creado un GIF o video que no existe.

La valoración artística final corresponde a la revisión del usuario. La mezcla, el comportamiento y los archivos del audio anterior permanecen conservados.
