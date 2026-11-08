# Verificación final del pulido visual

**452 pruebas aprobadas**, sin fallos, errores ni omisiones, en **225,134 segundos**. El resultado corresponde al código final, incluidos el selector del grafo y los retratos de alta resolución.

- [Informe JSON](verificacion_pulido_visual.json).
- [Registro completo](verificacion_pulido_visual.txt).
- [Cambios y guía de juego](pulido_visual.md).

Se completaron las campañas de ambos roles, el flujo ABB → grafo y las barreras cooperativas. Las pruebas heredadas de balance se actualizaron para comprobar los ocho valores completos contra el estado real y permitir el avance inmediato; conservan los recorridos completos y la verificación de balances sin duplicados.

Los siete videos nuevos decodifican sus 144 cuadros completos, muestran movimiento y carecen de pista de audio. Las voces proceden del paquete neuronal original. Las imágenes se abrieron correctamente; dimensiones y hashes figuran en el JSON.

Se comprobaron la guía de tres pasos, confirmación visible, presupuesto, fuentes privadas y texto conservado durante revisiones. El recorrido con clics reales se revisó a 1100×700 y 1360×720.

La cooperación se verificó con dos ventanas y TCP real en un equipo; no equivale a una comprobación en dos dispositivos físicos.

## Capturas reales

[Selección](capturas_pulido/seleccion_personajes.png) · [Cuatro candidatos](capturas_pulido/foro_inicio.png) · [Juan en la historia](capturas_pulido/juan_en_historia.png)

[Explorar](capturas_pulido/guia_explorar.png) · [Hallazgo](capturas_pulido/hallazgo.png) · [Decidir](capturas_pulido/guia_decidir.png)

[Balance simultáneo](capturas_pulido/balance_simultaneo.png) · [Árbol](capturas_pulido/arbol.png) · [Grafo](capturas_pulido/grafo.png)

## Repetir las pruebas

Desde la carpeta interna del proyecto:

    python -B herramientas/verificar_proyecto.py --log .tmp/verificacion_pulido_visual.txt

Los informes anteriores describen sus versiones respectivas y se conservan como historial.
