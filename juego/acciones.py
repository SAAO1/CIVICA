"""Decisiones públicas de cada oficio y compatibilidad con partidas anteriores.

Las claves de rol describen el método elegido; ``legacy`` sólo mantiene legible
el historial antiguo. La autorización se comprueba antes de cambiar la partida.
"""


_ACCIONES = {
    "ciudadano": (
        {"clave": "compartir", "titulo": "Compartir con mi grupo",
         "descripcion": "Difunde el titular a dos niveles de tu red. Una noticia falsa también puede llegar a tus vecinos.",
         "legacy": "compartir", "efecto": "difusion"},
        {"clave": "conversar", "titulo": "Escuchar al vecindario",
         "titulo_corto": "Escuchar al barrio",
         "descripcion": "Habla con un vecino y crea un vínculo recíproco. Mejora la convivencia sin reenviar ni dar por cierto el titular.",
         "legacy": "ignorar", "efecto": "vinculo"},
        {"clave": "convocar", "titulo": "Convocar al barrio",
         "titulo_corto": "Convocar al barrio",
         "descripcion": "Moviliza hasta tres niveles de la red. Aumenta la participación, pero convocar por un rumor multiplica el daño.",
         "legacy": "compartir", "efecto": "movilizacion"},
        {"clave": "ignorar", "titulo": "Seguir sin reenviar",
         "descripcion": "No difunde el mensaje ni cambia tus contactos. La publicación queda disponible y la duda sigue pendiente.",
         "legacy": "ignorar", "efecto": "silencio"},
    ),
    "periodista": (
        {"clave": "contrastar", "titulo": "Contrastar las fuentes",
         "descripcion": "Revisa documentos y contexto. Si es falso, publica una corrección; una opinión no se convierte en hecho.",
         "legacy": "verificar", "efecto": "verificacion"},
        {"clave": "entrevistar", "titulo": "Entrevistar a una fuente",
         "descripcion": "Abre contacto directo con el emisor o un testigo. Añade una relación a la red; el testimonio aún necesita contraste.",
         "legacy": "ignorar", "efecto": "fuente"},
        {"clave": "desmentir", "titulo": "Desmentir y denunciar",
         "descripcion": "Envía una rectificación y retira contenido falso o dañino. Denunciar un hecho cierto resta credibilidad.",
         "legacy": "reportar", "efecto": "rectificacion"},
        {"clave": "reservar", "titulo": "Mantener en reserva",
         "descripcion": "Deja el contenido pendiente de pruebas. Protege la prudencia editorial, pero demora la participación y no informa al barrio.",
         "legacy": "ignorar", "efecto": "reserva"},
    ),
}

ACCIONES_LEGACY = frozenset(("compartir", "verificar", "ignorar", "reportar"))
_POR_CLAVE = {accion["clave"]: dict(accion, rol=rol)
              for rol, acciones in _ACCIONES.items() for accion in acciones}


def acciones_para_rol(rol):
    """Cuatro opciones nuevas del oficio, sin las opciones del otro personaje."""
    return tuple(dict(accion, rol=rol) for accion in _ACCIONES.get(rol, ()))


def obtener_accion(clave):
    accion = _POR_CLAVE.get(clave) if isinstance(clave, str) else None
    return dict(accion) if accion else None


def accion_permitida(clave, rol, permitir_legacy=True):
    if not isinstance(clave, str):
        return False
    if permitir_legacy and clave in ACCIONES_LEGACY:
        return True
    accion = _POR_CLAVE.get(clave)
    return bool(accion and accion["rol"] == rol)


def accion_legacy(clave):
    accion = obtener_accion(clave)
    return accion["legacy"] if accion else clave


def accion_por_defecto(rol):
    """Al agotar el plazo nunca se publica información automáticamente."""
    return "reservar" if rol == "periodista" else "ignorar"
