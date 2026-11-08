def consecuencias(accion, publicacion, alcance, rol):
    """Cambios de 0..100; difusión proporcional, limitada a cinco unidades."""
    escala = min(5, alcance)
    falsa = publicacion.verdadera is False or publicacion.danina
    if accion == "conversar":
        return ({"participacion": 2, "convivencia": 3, "confianza": 1,
                 "conflictos": -1, "bienestar_digital": 1}, 2,
                "Escuchaste a un vecino y abriste una relación de ida y vuelta. No reenviaste el titular ni resolviste su veracidad.")
    if accion == "entrevistar":
        return ({"participacion": 1, "confianza": 1, "bienestar_digital": 1}, 2,
                "Registraste un testimonio y un contacto directo con la fuente. Una entrevista no sustituye la comprobación documental.")
    if accion == "reservar":
        return ({"confianza": 1, "bienestar_digital": 2, "participacion": -1}, 1,
                "La redacción dejó la publicación en reserva a la espera de pruebas. No se difundió ni se verificó; informar al barrio queda pendiente.")
    if accion == "convocar":
        if falsa:
            return ({"desinformacion": escala * 4, "confianza": -escala * 2,
                     "conflictos": escala * 2, "convivencia": -escala,
                     "bienestar_digital": -escala, "participacion": escala * 2},
                    -escala * 3,
                    "La convocatoria movilizó vecinos por información falsa o dañina: ganó participación, pero amplificó el rumor y la tensión.")
        return ({"participacion": escala * 2, "confianza": escala,
                 "info_verificada": escala * 2 if publicacion.verdadera else 0,
                 "convivencia": escala, "bienestar_digital": escala}, escala * 3,
                "La convocatoria movilizó a la comunidad a tres niveles de la red. El alcance y la participación dependen de sus conexiones reales.")
    if accion == "desmentir":
        if falsa:
            return ({"info_verificada": 3, "confianza": 4,
                     "desinformacion": -(3 + escala), "convivencia": 3,
                     "bienestar_digital": 2, "conflictos": -2}, 7,
                    "Publicaste una rectificación fundamentada y denunciaste el contenido falso o dañino. La publicación se retira, pero el historial se conserva.")
        return ({"confianza": -4, "convivencia": -2, "conflictos": 1}, -5,
                "La denuncia no tenía fundamento: una noticia cierta o una opinión legítima no puede presentarse como falsa. La publicación se conserva.")
    if accion == "contrastar":
        accion = "verificar"
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
