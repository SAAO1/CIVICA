def consecuencias(accion, publicacion, alcance, rol):
    """Cambios de 0..100; difusión proporcional, limitada a cinco unidades."""
    escala = min(5, alcance)
    falsa = publicacion.verdadera is False or publicacion.danina
    if accion == "compartir":
        if falsa:
            return ({"desinformacion": escala * 3, "confianza": -escala,
                     "conflictos": escala, "convivencia": -escala,
                     "bienestar_digital": -escala}, -2 * escala,
                    "El rumor ganó alcance y perjudicó la confianza.")
        return ({"info_verificada": escala * 2 if publicacion.verdadera else 0,
                 "participacion": escala, "confianza": escala,
                 "convivencia": escala, "bienestar_digital": escala}, escala * 2,
                "La información útil llegó a tus conexiones.")
    if accion == "verificar":
        if publicacion.verdadera is None:
            return ({"participacion": 1}, 1, "Es una opinión: no equivale a una noticia comprobada.")
        bonus = 3 if rol == "periodista" else 2 if rol == "ciudadano" else 0
        return ({"info_verificada": 5, "confianza": 3 + bonus,
                 "desinformacion": -(3 + escala), "conflictos": -2,
                 "convivencia": 2, "bienestar_digital": 2},
                6 + bonus, "Las fuentes confirman la noticia." if not falsa else "Las fuentes desmienten el rumor; difundiste una corrección.")
    if accion == "reportar":
        if falsa:
            return ({"confianza": 2, "desinformacion": -3, "convivencia": 3,
                     "bienestar_digital": 2, "conflictos": -2}, 5,
                    "El contenido dañino fue retirado; no iniciará nuevas difusiones.")
        return ({"confianza": -2, "convivencia": -1}, -3,
                "El reporte carece de fundamento: la publicación se conserva.")
    return ({}, 0, "No difundiste la publicación. Permanece disponible en Civitas.")
