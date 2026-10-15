def calcular_eleccion(candidatos, estado, historial):
    apoyos = {c.id: c.apoyo for c in candidatos}
    razones = []
    for registro in historial:
        candidato = registro["publicacion"].get("candidato_id")
        if candidato not in apoyos:
            continue
        accion, verdadera = registro["accion"], registro["publicacion"]["verdadera"]
        alcance = registro.get("alcance", 0)
        cambio = 0
        if accion == "compartir":
            cambio = 2 + alcance if verdadera is True else -(2 + alcance) if verdadera is False else 0
        elif accion == "verificar":
            cambio = 4 if verdadera is True else 2 if verdadera is False else 0
        elif accion == "reportar" and registro["eliminada"]:
            cambio = 2
        apoyos[candidato] = max(1, apoyos[candidato] + cambio)
        razones.append(f"#{registro['publicacion']['id']}: {accion}, apoyo {cambio:+d}")
    total = sum(apoyos.values())
    porcentajes = {id: round(valor * 100 / total, 1) for id, valor in apoyos.items()}
    maximo = max(apoyos.values())
    ganadores = [c.nombre for c in candidatos if apoyos[c.id] == maximo]
    calidad = (estado.confianza + estado.convivencia + estado.bienestar_digital
               + estado.info_verificada - estado.desinformacion - estado.conflictos) / 4
    final = "Comunidad informada" if calidad >= 50 else "Una ciudad que necesita reconstruir confianza"
    return {"ganadores": ganadores, "empate": len(ganadores) > 1,
            "porcentajes": porcentajes, "apoyos": apoyos, "razones": razones,
            "final": final, "calidad": round(calidad, 1)}
