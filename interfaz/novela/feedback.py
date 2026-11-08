"""Señales de acciones confirmadas, independientes de revisiones y del reloj."""


def efectos_de_cambio(anterior, actual):
    if (not anterior or anterior.get("caso", {}).get("id") != actual.get("caso", {}).get("id")
            or actual.get("fase") in ("pausa", "sala")):
        return ()
    mi_id = actual.get("mi_id")
    previos = {h["id"]: h for h in anterior.get("hallazgos", [])}
    hallazgos = actual.get("hallazgos", [])
    nuevos = [h for h in hallazgos if h["id"] not in previos]
    efectos = []
    propios = [h for h in nuevos if h.get("propietario") == mi_id]
    compartidos = [h for h in hallazgos if h.get("compartido")
                   and (h["id"] not in previos or not previos[h["id"]].get("compartido"))]
    if propios:
        efectos.append(("taza",) if any(h.get("tipo") == "testimonio" for h in propios)
                       else ("pulido_hallazgo", "hallazgo"))
    elif compartidos:
        efectos.append(("papeles",))
    propuesta = next((p for p in actual.get("propuestas", []) if p.get("jugador_id") == mi_id), None)
    previa = next((p for p in anterior.get("propuestas", []) if p.get("jugador_id") == mi_id), None)
    if (propuesta is not None and propuesta != previa and mi_id not in actual.get("decididos", [])
            and not propios):
        efectos.append(("lapiz",))
    antes_red = {tuple(a) for a in anterior.get("red", {}).get("aristas", [])}
    despues_red = {tuple(a) for a in actual.get("red", {}).get("aristas", [])}
    if antes_red != despues_red:
        efectos.append(("pulido_red", "nodo"))
    return tuple(efectos)


def reproducir_cambios(audio, anterior, actual):
    for alternativas in efectos_de_cambio(anterior, actual):
        for nombre in alternativas:
            if audio.reproducir_efecto(nombre):
                break
