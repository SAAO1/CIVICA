"""Motor de investigación de CIVICA; comparte el Juego, ABB y grafo reales.

La sesión coordina presupuesto, evidencias privadas, decisiones editoriales y
la barrera cooperativa. No importa Qt, sockets ni objetos de presentación.
"""
from copy import deepcopy
from dataclasses import asdict

from juego.acciones import acciones_para_rol
from juego.casos_feria import (
    ACCIONES_CON_PRUEBA, CERTEZAS, IDS_FERIA, LUGARES, ROLES_FERIA,
    TIPOS_DOCUMENTALES, crear_caso,
)
from juego.partida import Juego
from models.jugador import Jugador


class SesionInvestigacion:
    VERSION = 1

    def __init__(self, semilla=4, cooperativa=False):
        self.semilla = semilla
        self.cooperativa = bool(cooperativa)
        self.juego = Juego(semilla, eventos=True, campana="feria")
        self.juego.jugadores = []
        self.fase = "sala"
        self.revision = 0
        self.presupuestos = {}
        self.hallazgos = []
        self.propuestas = {}
        self.solicitudes = []
        self.decisiones = {}
        self.confirmados = []
        self.audiencias = {}
        self.visitas = {}
        self.relaciones = {id: {"id": id, "nombre": nombre, "confianza": 50,
                               "respuesta": "Todavía no hemos hablado de este mensaje."}
                           for id, nombre in (("luis", "Luis"), ("valeria", "Valeria"),
                                              ("maria", "María"), ("ines", "Inés"))}
        self.mensaje = "Elige tu rol para abrir la investigación."

    @property
    def caso_id(self):
        indice = max(0, min(5, self.juego.indice_proxima_publicacion - 1))
        return IDS_FERIA[indice]

    @property
    def caso(self):
        return crear_caso(self.caso_id)

    def _jugador(self, id):
        jugador = next((j for j in self.juego.jugadores if j.id == id), None)
        if jugador is None:
            raise ValueError("Este participante no pertenece a la sesión")
        return jugador

    def _cambiar(self, mensaje):
        self.revision += 1
        self.mensaje = mensaje

    def registrar_jugador(self, nombre, rol, id=None):
        if self.fase != "sala":
            raise ValueError("La campaña ya comenzó")
        if not isinstance(nombre, str) or not nombre.strip() or len(nombre.strip()) > 24:
            raise ValueError("Escribe un nombre de entre 1 y 24 caracteres")
        if rol not in ROLES_FERIA:
            raise ValueError("Elige Ciudadano o Periodista")
        limite = 2 if self.cooperativa else 1
        if len(self.juego.jugadores) >= limite:
            raise ValueError("La sesión ya tiene todos sus participantes")
        if any(j.rol == rol for j in self.juego.jugadores):
            raise ValueError("Ese rol ya está reservado por otro participante")
        id = id or f"jugador{len(self.juego.jugadores) + 1}"
        if not isinstance(id, str) or not id or any(j.id == id for j in self.juego.jugadores):
            raise ValueError("El identificador del participante debe ser único")
        nodo = "ana" if rol == "ciudadano" else "maria"
        self.juego.jugadores.append(Jugador(id=id, nombre=nombre.strip(), rol=rol, ciudadano_id=nodo))
        self._cambiar(f"{nombre.strip()} se prepara como {rol}.")
        return id

    def cambiar_rol(self, id, rol):
        if self.fase != "sala":
            raise ValueError("El rol se elige antes de empezar")
        jugador = self._jugador(id)
        if rol not in ROLES_FERIA:
            raise ValueError("Solo están disponibles Ciudadano y Periodista")
        if any(j.id != id and j.rol == rol for j in self.juego.jugadores):
            raise ValueError("Ese rol ya está reservado")
        jugador.rol = rol
        jugador.ciudadano_id = "ana" if rol == "ciudadano" else "maria"
        self._cambiar("Rol actualizado.")
        return self.vista(id)

    def comenzar(self):
        if self.fase != "sala":
            raise ValueError("La investigación ya comenzó")
        esperados = 2 if self.cooperativa else 1
        if len(self.juego.jugadores) != esperados:
            raise ValueError("La cooperación requiere exactamente dos participantes, uno por rol"
                             if self.cooperativa else "Selecciona un participante")
        self.juego.jugadores.sort(key=lambda j: ROLES_FERIA.index(j.rol))
        self.juego.turno = 0
        self.juego.iniciar_primera_publicacion()
        self._preparar_caso()
        self._cambiar("Una captura sobre el colegio acaba de llegar. Elige qué investigar.")
        return self.vista()

    def _preparar_caso(self):
        self.fase = "investigacion"
        self.decisiones = {}
        self.confirmados = []
        self.propuestas = {}
        self.presupuestos = {j.id: 2 for j in self.juego.jugadores}
        self.visitas = {j.id: [] for j in self.juego.jugadores}
        self.audiencias = {j.id: self.juego.grafo.vecinos(j.ciudadano_id)[:2]
                           for j in self.juego.jugadores}

    def _investigador(self, id):
        jugador = self._jugador(id)
        if self.fase not in ("investigacion", "decision"):
            raise ValueError("No hay una investigación abierta en este momento")
        if id in self.decisiones:
            raise ValueError("Tu decisión de este caso ya quedó publicada")
        return jugador

    def _presupuesto(self, id):
        if self.presupuestos.get(id, 0) <= 0:
            raise ValueError("Ya utilizaste tus dos acciones de investigación")

    def _evidencia(self, id):
        for caso_id in IDS_FERIA:
            for evidencia in crear_caso(caso_id)["evidencias"]:
                if evidencia["id"] == id:
                    return evidencia
        raise ValueError("No existe esa evidencia")

    def _presentar_hallazgo(self, hallazgo):
        # Los guardados anteriores reciben la atribución actual del catálogo;
        # consultar una vista no reescribe su texto ni sus permisos persistidos.
        ficha = self._evidencia(hallazgo["id"])
        return dict(ficha, propietario=hallazgo["propietario"],
                    compartido=hallazgo["compartido"])

    def _visible(self, jugador_id, evidencia_id):
        hallazgo = next((h for h in self.hallazgos if h["id"] == evidencia_id
                         and (h["propietario"] == jugador_id or h["compartido"])), None)
        return self._presentar_hallazgo(hallazgo) if hallazgo is not None else None

    def _prueba_pertinente(self, prueba):
        return bool(prueba and prueba.get("caso_id") == self.caso_id
                    and prueba.get("tipo") in TIPOS_DOCUMENTALES)

    def _hallazgo(self, id, evidencia):
        encontrado = next((h for h in self.hallazgos if h["id"] == evidencia["id"]
                           and h["propietario"] == id), None)
        if encontrado is not None:
            raise ValueError("Ya encontraste esta fuente")
        hallazgo = deepcopy(evidencia)
        hallazgo.update(propietario=id, compartido=not self.cooperativa)
        self.hallazgos.append(hallazgo)
        self.presupuestos[id] -= 1
        return hallazgo

    def _estado_relacion(self, relacion):
        return ("abierto" if relacion["confianza"] >= 65 else
                "distante" if relacion["confianza"] < 35 else "duda")

    def _relacion(self, id, cambio, respuesta):
        jugador = self._jugador(id)
        relacion = self.relaciones[self.caso["npc_id"]]
        relacion["confianza"] = max(0, min(100, relacion["confianza"] + cambio))
        relacion["respuesta"] = respuesta
        origen, destino = jugador.ciudadano_id, relacion["id"]
        efecto = {"creadas": [], "eliminadas": []}
        if origen != destino and self.juego.grafo.existe_vertice(destino):
            if self._estado_relacion(relacion) == "distante":
                for a, b in ((origen, destino), (destino, origen)):
                    if self.juego.grafo.eliminar_arista(a, b):
                        efecto["eliminadas"].append([a, b])
            elif self._estado_relacion(relacion) == "abierto":
                for a, b in ((origen, destino), (destino, origen)):
                    if self.juego.grafo.agregar_arista(a, b):
                        efecto["creadas"].append([a, b])
        return efecto

    def investigar(self, id, lugar, interaccion=None):
        jugador = self._investigador(id)
        if lugar not in {l["id"] for l in LUGARES}:
            raise ValueError("Elige Archivo, Barrio o Redacción")
        evidencia = next(e for e in self.caso["evidencias"] if e["origen"] == lugar)
        if self.cooperativa and evidencia["rol"] not in ("ambos", jugador.rol):
            raise ValueError("Tu compañero tiene acceso a esa fuente; pídele que la comparta")
        if lugar == "barrio" and self._estado_relacion(self.relaciones[self.caso["npc_id"]]) == "distante":
            raise ValueError("La fuente está distante: presenta un documento para recuperar su confianza")
        if lugar in self.visitas[id]:
            raise ValueError("Ya visitaste este lugar en el caso actual")
        self._presupuesto(id)
        self._hallazgo(id, evidencia)
        self.visitas[id].append(lugar)
        self._cambiar(f"Encontraste «{evidencia['titulo']}». Puedes adjuntarla o compartirla.")
        return self.vista(id)

    def examinar(self, id, tipo, valor):
        self._investigador(id)
        medio = self.caso["medio"]
        if tipo != medio["tipo"]:
            raise ValueError("Ese instrumento no corresponde al medio de este caso")
        if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not 0 <= valor <= 100:
            raise ValueError("Mueve el control entre 0 y 100")
        if not medio["solucion_min"] <= valor <= medio["solucion_max"]:
            raise ValueError("Este tramo aún oculta el contexto. Sigue el encuadre o busca el segmento anterior.")
        self._presupuesto(id)
        evidencia = next(e for e in self.caso["evidencias"] if e["tipo"] == "medio")
        self._hallazgo(id, evidencia)
        self.visitas[id].append("visor")
        self._cambiar("Recuperaste la pieza completa: ahora puedes contrastarla con el mensaje.")
        return self.vista(id)

    def entrevistar(self, id, pregunta, evidencia=None):
        self._investigador(id)
        if pregunta not in {p["id"] for p in self.caso["preguntas"]}:
            raise ValueError("Elige una de las preguntas del expediente")
        prueba = None
        if evidencia:
            prueba = self._visible(id, evidencia)
            if prueba is None:
                raise ValueError("Primero obtén esa evidencia o pídele a tu compañero que la comparta")
        pertinente = self._prueba_pertinente(prueba)
        if self._estado_relacion(self.relaciones[self.caso["npc_id"]]) == "distante" and not pertinente:
            raise ValueError("La fuente pide una prueba pertinente antes de retomar la conversación")
        self._presupuesto(id)
        testimonio = next(e for e in self.caso["evidencias"] if e["tipo"] == "testimonio")
        self._hallazgo(id, testimonio)
        if pregunta == "presionar":
            cambio, respuesta = -15, "La prisa no me ayuda a recordar. Necesito que me escuches."
        elif evidencia and not pertinente:
            cambio, respuesta = -5, "Ese documento habla de otro caso. Volvamos a lo que ocurrió aquí."
        elif pertinente:
            cambio, respuesta = 15, "Con este documento puedo precisar lo que vi. Volvamos a hablar."
        else:
            cambio, respuesta = 5, "Te cuento lo que recuerdo, aunque mi testimonio necesita contexto."
        self._relacion(id, cambio, respuesta)
        self.visitas[id].append("entrevista")
        self._cambiar(f"{self.caso['npc_nombre']}: {respuesta}")
        return self.vista(id)

    def compartir_hallazgo(self, id, evidencia_id):
        self._jugador(id)
        hallazgo = next((h for h in self.hallazgos if h["id"] == evidencia_id
                        and h["propietario"] == id), None)
        if hallazgo is None:
            raise ValueError("Solo puedes compartir un hallazgo que hayas obtenido")
        if not hallazgo["compartido"]:
            hallazgo["compartido"] = True
            for solicitud in self.solicitudes:
                if solicitud["evidencia_id"] == evidencia_id:
                    solicitud["atendida"] = True
            self._cambiar("La evidencia ya está disponible para tu compañero.")
        return self.vista(id)

    def solicitar_hallazgo(self, id, evidencia_id):
        self._jugador(id)
        hallazgo = next((h for h in self.hallazgos if h["id"] == evidencia_id
                        and h["propietario"] != id), None)
        if hallazgo is None:
            raise ValueError("Tu compañero todavía no tiene ese hallazgo")
        if self._visible(id, evidencia_id):
            raise ValueError("La evidencia ya está disponible en tu expediente")
        if not any(s["solicitante"] == id and s["evidencia_id"] == evidencia_id
                   and not s["atendida"] for s in self.solicitudes):
            self.solicitudes.append({"id": len(self.solicitudes) + 1, "solicitante": id,
                                     "evidencia_id": evidencia_id, "atendida": False})
            self._cambiar("Tu compañero recibió la solicitud de evidencia.")
        return self.vista(id)

    def _contactos(self, id, contactos):
        jugador = self._jugador(id)
        if contactos is None:
            disponibles = self.juego.grafo.vecinos(jugador.ciudadano_id)
            contactos = [c for c in self.audiencias.get(id, disponibles[:2]) if c in disponibles]
        if not isinstance(contactos, (list, tuple)) or any(not isinstance(c, str) for c in contactos):
            raise ValueError("Selecciona hasta dos contactos de tu red")
        if len(contactos) > 2 or len(contactos) != len(set(contactos)):
            raise ValueError("Selecciona como máximo dos contactos diferentes")
        if any(c not in self.juego.grafo.vecinos(jugador.ciudadano_id) for c in contactos):
            raise ValueError("La audiencia inicial debe estar conectada contigo")
        return list(contactos)

    def prever_alcance(self, id, contactos):
        self._jugador(id)
        seleccionados = self._contactos(id, contactos)
        self.audiencias[id] = seleccionados
        self._cambiar("La previsión recorre conexiones reales; no publica ni concede puntos.")
        return self.vista(id)

    def _preparar_editor(self, id, accion, titular, certeza, evidencia_id, contactos):
        jugador = self._investigador(id)
        permitidas = {a["clave"] for a in acciones_para_rol(jugador.rol)}
        if jugador.rol == "ciudadano":
            permitidas.add("rectificar")
        if accion not in permitidas:
            raise ValueError("Esa acción no corresponde a tu rol")
        if certeza not in CERTEZAS:
            raise ValueError("Indica si la información está pendiente, es probable o está confirmada")
        if not isinstance(titular, str) or len(titular.strip()) > 160:
            raise ValueError("El titular debe tener como máximo 160 caracteres")
        prueba = None
        if evidencia_id:
            prueba = self._visible(id, evidencia_id)
            if prueba is None:
                raise ValueError("No puedes adjuntar evidencia privada que no te compartieron")
        pertinente = self._prueba_pertinente(prueba)
        if accion in ACCIONES_CON_PRUEBA and prueba is not None and prueba["caso_id"] != self.caso_id:
            numero_anterior = IDS_FERIA.index(prueba["caso_id"])+1
            numero_actual = IDS_FERIA.index(self.caso_id)+1
            raise ValueError(
                f"La prueba adjunta pertenece al acto {numero_anterior} (#{prueba['caso_id']}). "
                f"Usa una fuente del acto {numero_actual} (#{self.caso_id}).")
        if accion in ACCIONES_CON_PRUEBA and not pertinente:
            raise ValueError("Esta respuesta necesita un documento, contexto o pieza completa del caso actual; un testimonio por sí solo no basta.")
        if accion == "rectificar":
            publicacion = self.juego.obtener_publicacion_actual()
            if publicacion and publicacion.verdadera is not False:
                raise ValueError("La evidencia de este caso no respalda retirar una afirmación verdadera")
        publicacion = self.juego.obtener_publicacion_actual()
        texto = titular.strip() or (publicacion.texto if publicacion else self.caso["titulo"])
        return {"jugador_id": id, "accion": accion, "titular": texto, "certeza": certeza,
                "evidencia_id": evidencia_id, "contactos": self._contactos(id, contactos),
                "evidencia_pertinente": pertinente}

    def proponer(self, id, accion, titular="", certeza="pendiente", evidencia_id=None, contactos=None):
        propuesta = self._preparar_editor(id, accion, titular, certeza, evidencia_id, contactos)
        self.propuestas[id] = propuesta
        self._cambiar("Propuesta guardada: revisa el titular y conversa antes de publicar.")
        return self.vista(id)

    def decidir(self, id, accion, titular="", certeza="pendiente", evidencia_id=None, contactos=None):
        propuesta = self._preparar_editor(id, accion, titular, certeza, evidencia_id, contactos)
        pendientes = [j for j in self.juego.jugadores if j.id not in self.decisiones]
        if not pendientes or pendientes[0].id != id:
            raise ValueError("Primero publica la decisión del Ciudadano")
        jugador = self._jugador(id)
        publicacion = self.juego.obtener_publicacion_actual()
        if publicacion is None:
            raise ValueError("La publicación ya fue retirada del árbol")
        puntos_antes = jugador.puntos
        estado_antes = self.juego.estado.datos()
        self.juego.turno = self.juego.jugadores.index(jugador)
        self.juego.decision_aplicada = False
        accion_motor = "verificar" if accion == "rectificar" else accion
        if not self.juego.ejecutar_accion(accion_motor, jugador_id=id, contactos=propuesta["contactos"]):
            raise ValueError("No fue posible aplicar esta decisión")
        registro = self.juego.ultimo_registro
        if accion == "rectificar":
            # La categoría de cálculo sigue siendo verificar; el historial
            # conserva la intención que eligió realmente el Ciudadano.
            registro["accion_rol"] = "rectificar"
            registro["titulo_accion"] = "Rectificar con una prueba"
            self.juego.ultima_accion_rol = "rectificar"
        editorial = ""
        delta_puntos = 0
        cambios = {}
        difunde = accion in ("compartir", "convocar")
        if difunde and certeza != "confirmada":
            ganancia = self.juego.info_verificada - estado_antes["info_verificada"]
            if ganancia > 0:
                cambios["info_verificada"] = -ganancia
        if difunde and certeza == "confirmada" and not propuesta["evidencia_pertinente"]:
            cambios["confianza"] = -4
            delta_puntos = -3
            editorial = "Presentaste una certeza sin respaldo: la confianza y la reputación bajan."
        elif difunde and evidencia_id and not propuesta["evidencia_pertinente"]:
            cambios["confianza"] = -3
            delta_puntos = -2
            editorial = "La evidencia adjunta pertenece a otro caso y no respalda el titular."
        elif propuesta["evidencia_pertinente"] and certeza == "confirmada":
            cambios["confianza"] = 2
            delta_puntos = 2
            editorial = "El grado de certeza conserva una fuente pertinente y consultable."
        elif certeza == "probable":
            editorial = "La publicación distingue una hipótesis de un hecho confirmado."
        else:
            editorial = "La información pendiente queda identificada sin fingir una comprobación."
        self.juego.estado.aplicar(cambios)
        jugador.puntos += delta_puntos
        jugador.reputacion = max(0, min(100, jugador.reputacion + delta_puntos))
        jugador.confianza = max(0, min(100, jugador.confianza + cambios.get("confianza", 0)))
        falsa = publicacion.verdadera is False or publicacion.danina
        if difunde and falsa:
            cambio_relacion = -20
            respuesta = "Compartieron algo que me afecta sin recuperar su contexto. Necesito distancia."
        elif accion in ("rectificar", "contrastar", "desmentir") and propuesta["evidencia_pertinente"]:
            cambio_relacion = 15
            respuesta = "Mostraron la fuente y reconocieron el contexto. Puedo volver a conversar."
        elif accion in ("conversar", "entrevistar"):
            cambio_relacion = 10
            respuesta = "Gracias por escuchar antes de reaccionar."
        else:
            cambio_relacion = 0
            respuesta = "La decisión queda registrada; veremos a quién alcanza."
        red = self._relacion(id, cambio_relacion, respuesta)
        registro["efectos_red"].setdefault("conexiones_eliminadas", []).extend(red["eliminadas"])
        registro["efectos_red"]["conexiones_creadas"].extend(red["creadas"])
        registro.update(editor=deepcopy(propuesta), investigacion_caso=self.caso_id,
                        editorial=editorial, puntos_antes=puntos_antes, puntos_despues=jugador.puntos,
                        puntos=jugador.puntos-puntos_antes, antes=estado_antes,
                        despues=self.juego.estado.datos(),
                        cambios_reales={k: getattr(self.juego.estado, k)-v for k, v in estado_antes.items()
                                        if getattr(self.juego.estado, k) != v})
        self.decisiones[id] = deepcopy(registro)
        self.propuestas[id] = propuesta
        self.audiencias[id] = propuesta["contactos"]
        self.fase = "resultado" if len(self.decisiones) == len(self.juego.jugadores) else "decision"
        self._cambiar(editorial + " " + respuesta)
        return self.vista(id)

    def expirar_turno(self, id):
        self._investigador(id)
        pendientes = [j.id for j in self.juego.jugadores if j.id not in self.decisiones]
        if not pendientes or pendientes[0] != id:
            raise ValueError("Solo puede expirar la decisión del participante activo")
        if not self.juego.evento_actual.urgente:
            raise ValueError("Este caso no tiene una alerta con plazo")
        jugador = self._jugador(id)
        accion = "ignorar" if jugador.rol == "ciudadano" else "reservar"
        self.decidir(id, accion, certeza="pendiente")
        self.juego.ultimo_registro["por_plazo"] = True
        self.decisiones[id]["por_plazo"] = True
        self.mensaje = "Terminó el plazo: se conservó la publicación sin reenviarla."
        return self.vista(id)

    def continuar(self, id):
        self._jugador(id)
        if self.fase != "resultado":
            raise ValueError("Primero deben quedar registradas las decisiones del caso")
        if id not in self.confirmados:
            self.confirmados.append(id)
            self._cambiar("Esperando que cada participante confirme el resultado.")
        if len(self.confirmados) == len(self.juego.jugadores):
            self.juego.turno = 0
            if self.juego.agregar_siguiente_publicacion():
                self._preparar_caso()
                self._cambiar("Nueva investigación: elige tus próximas dos acciones.")
            else:
                self.fase = "final"
                self._cambiar("La ciudad votó. El resultado conserva sus decisiones y sus relaciones.")
        return self.vista(id)

    def _reparacion_caso(self):
        afectados, corregidos = set(), set()
        for registro in self.juego.historial:
            if registro["publicacion"]["id"] != self.caso_id:
                continue
            propagacion = registro.get("propagacion")
            if not propagacion:
                continue
            if propagacion["correccion"]:
                corregidos.update(propagacion["receptores"])
                corregidos.add(propagacion["emisor"])
            elif registro["publicacion"]["verdadera"] is False:
                afectados.update(propagacion["receptores"])
        return {"afectados": sorted(afectados), "corregidos": sorted(afectados & corregidos),
                "pendientes": sorted(afectados - corregidos)}

    def vista(self, id=None):
        if id is None and not self.cooperativa and len(self.juego.jugadores) == 1:
            id = self.juego.jugadores[0].id
        jugador = self._jugador(id) if id is not None else None
        caso = self.caso
        hallazgos = [self._presentar_hallazgo(h) for h in self.hallazgos]
        visibles = [h for h in hallazgos if h["compartido"] or h["propietario"] == id]
        for hallazgo in visibles:
            hallazgo["del_caso_actual"] = hallazgo["caso_id"] == self.caso_id
            hallazgo["pertinente"] = self._prueba_pertinente(hallazgo)
        pruebas = sorted((h for h in visibles if h["pertinente"]),
                         key=lambda h: {"documento": 0, "medio": 1, "contexto": 2}[h["tipo"]])
        medio = {k: v for k, v in caso["medio"].items() if not k.startswith("solucion")}
        medio["revelado"] = any(h["id"] == f"{self.caso_id}:medio" for h in visibles)
        if not medio["revelado"]:
            medio["texto_completo"] = ""
        medio["marcas"] = [{"valor": 0, "texto": "Inicio del recorte"},
                          {"valor": 65, "texto": "Recuperar contexto"},
                          {"valor": 100, "texto": "Pieza completa"}]
        publicacion = self.juego.obtener_publicacion_actual()
        if publicacion is None:
            publicacion = next(p for p in self.juego.publicaciones_planificadas if p.id == self.caso_id)
        caso_visible = {k: v for k, v in caso.items() if k not in ("evidencias", "medio")}
        caso_visible["medio"] = medio
        caso_visible["publicacion"] = {k: publicacion.datos()[k] for k in ("id", "texto", "estado", "emisor_id")}
        lugares = []
        for lugar in LUGARES:
            evidencia = next(e for e in caso["evidencias"] if e["origen"] == lugar["id"])
            disponible = bool(jugador and self.fase in ("investigacion", "decision")
                              and id not in self.decisiones and self.presupuestos.get(id, 0) > 0
                              and lugar["id"] not in self.visitas.get(id, [])
                              and (not self.cooperativa or evidencia["rol"] in ("ambos", jugador.rol)))
            if lugar["id"] == "barrio" and self._estado_relacion(self.relaciones[caso["npc_id"]]) == "distante":
                disponible = False
            lugares.append(dict(lugar, disponible=disponible))
        seleccionados = self._contactos(id, None) if jugador and self.fase != "sala" else []
        if jugador:
            recorrido = self.juego.grafo.bfs(jugador.ciudadano_id, 2, contactos=seleccionados)
            alcance = asdict(recorrido)
            alcance.update(receptores=recorrido.orden[1:], alcance=max(0, len(recorrido.orden)-1))
        else:
            alcance = {"orden": [], "receptores": [], "niveles": [], "distancias": {}, "alcance": 0}
        pendientes = [j.id for j in self.juego.jugadores if j.id not in self.decisiones]
        acciones = list(acciones_para_rol(jugador.rol)) if jugador else []
        if jugador and jugador.rol == "ciudadano":
            acciones.append({"clave": "rectificar", "titulo": "Rectificar con una prueba",
                             "descripcion": "Recupera el contexto y haz llegar una corrección a tu audiencia."})
        for accion in acciones:
            requiere = accion["clave"] in ACCIONES_CON_PRUEBA
            motivo = ""
            if self.fase not in ("investigacion", "decision"):
                motivo = "Este caso ya no admite respuestas."
            elif id in self.decisiones:
                motivo = "Tu respuesta de este caso ya está registrada."
            elif requiere and not pruebas:
                motivo = "Recupera un documento, contexto o pieza completa de este caso."
            elif accion["clave"] == "rectificar" and publicacion.verdadera is not False:
                motivo = "La fuente de este caso no respalda retirar esta publicación."
            elif pendientes and pendientes[0] != id:
                motivo = "Primero confirma la respuesta del Ciudadano."
            accion.update(requiere_prueba=requiere, disponible=not motivo,
                          motivo_no_disponible=motivo,
                          evidencia_sugerida=pruebas[0]["id"] if pruebas else None)
        return deepcopy({
            "version": self.VERSION, "cooperativa": self.cooperativa, "fase": self.fase,
            "revision": self.revision, "mi_id": id, "mi_rol": jugador.rol if jugador else None,
            "jugadores": [asdict(j) for j in self.juego.jugadores], "caso": caso_visible,
            "lugares": lugares, "acciones_restantes": self.presupuestos.get(id, 0),
            "hallazgos": visibles, "evidencias_pertinentes": pruebas,
            "hallazgos_disponibles": [{k: h[k]
                                       for k in ("id", "titulo", "propietario", "compartido",
                                                 "caso_id", "tipo", "fuente_id", "fuente_nombre")}
                                      for h in hallazgos if h["propietario"] != id],
            "propuestas": list(self.propuestas.values()), "solicitudes": self.solicitudes,
            "turno_id": pendientes[0] if pendientes else None,
            "decididos": list(self.decisiones), "confirmados": self.confirmados,
            "acciones": acciones, "certezas": CERTEZAS,
            "certezas_disponibles": CERTEZAS if pruebas else CERTEZAS[:2],
            "estado": self.juego.estado.datos(),
            "relaciones": [dict(r, estado=self._estado_relacion(r)) for r in self.relaciones.values()],
            "evento": self.juego.evento_actual.datos(), "mensaje": self.mensaje,
            "segundos_decision": self.juego.evento_actual.segundos
                if self.juego.evento_actual.urgente and self.fase in ("investigacion", "decision") else None,
            "mision_reparacion": self._reparacion_caso(),
            "archivo_preorden": [{k: p.datos()[k] for k in ("id", "texto", "estado")}
                                  for p in self.juego.arbol.preorden()],
            "historial": [{"jugador_id": r["jugador_id"],
                           "nombre": next((j.nombre for j in self.juego.jugadores if j.id == r["jugador_id"]), "Participante"),
                           "accion": r.get("accion_rol", r["accion"]),
                           "titulo": r.get("titulo_accion", r["accion"]),
                           "puntos": r["puntos"], "alcance": r["alcance"],
                           "publicacion_id": r["publicacion"]["id"],
                           "explicacion": r["explicacion"],
                           "cambios": r.get("cambios_reales", {})}
                          for r in self.juego.historial],
            "archivo": [{k: p.datos()[k] for k in ("id", "texto", "estado")}
                        for p in self.juego.arbol.inorden()],
            "red": {"nodos": [asdict(n) for n in self.juego.grafo.nodos.values()],
                    "aristas": self.juego.grafo.aristas(),
                    "vecinos": self.juego.grafo.vecinos(jugador.ciudadano_id) if jugador else [],
                    "seleccionados": seleccionados, "alcance": alcance},
            "resultado": {"registros": list(self.decisiones.values()), "resumen": self.mensaje}
                         if self.fase in ("resultado", "final") else None,
            "resultado_electoral": self.juego.resultado_electoral() if self.fase == "final" else None,
        })

    def datos(self):
        return deepcopy({"version": self.VERSION, "semilla": self.semilla,
                         "cooperativa": self.cooperativa, "juego": self.juego.datos(),
                         "fase": self.fase, "revision": self.revision, "presupuestos": self.presupuestos,
                         "hallazgos": self.hallazgos, "propuestas": self.propuestas,
                         "solicitudes": self.solicitudes, "decisiones": self.decisiones,
                         "confirmados": self.confirmados, "audiencias": self.audiencias,
                         "visitas": self.visitas, "relaciones": self.relaciones, "mensaje": self.mensaje})

    @classmethod
    def desde_datos(cls, datos):
        try:
            return cls._cargar_datos(datos)
        except (KeyError, TypeError, IndexError, AttributeError) as error:
            raise ValueError("El guardado de investigación está incompleto o contiene datos inválidos") from error

    @classmethod
    def _cargar_datos(cls, datos):
        if not isinstance(datos, dict) or datos.get("version") != cls.VERSION:
            raise ValueError("Formato de investigación incompatible")
        sesion = cls(datos["semilla"], datos["cooperativa"])
        sesion.juego = Juego.desde_datos(datos["juego"])
        if sesion.juego.campana != "feria":
            raise ValueError("El guardado no pertenece a la investigación de feria")
        jugadores = sesion.juego.jugadores
        if len(jugadores) > (2 if sesion.cooperativa else 1):
            raise ValueError("Cantidad de participantes incompatible")
        if any(j.rol not in ROLES_FERIA for j in jugadores) or len({j.rol for j in jugadores}) != len(jugadores):
            raise ValueError("Los roles de investigación deben ser distintos y válidos")
        if len({j.id for j in jugadores}) != len(jugadores):
            raise ValueError("Los identificadores de jugadores deben ser únicos")
        for campo in ("fase", "revision", "presupuestos", "hallazgos", "propuestas",
                      "solicitudes", "decisiones", "confirmados", "audiencias",
                      "visitas", "relaciones", "mensaje"):
            setattr(sesion, campo, deepcopy(datos[campo]))
        if sesion.fase not in ("sala", "investigacion", "decision", "resultado", "final"):
            raise ValueError("La fase guardada no es válida")
        if sesion.fase != "sala" and len(jugadores) != (2 if sesion.cooperativa else 1):
            raise ValueError("La partida iniciada no tiene sus participantes completos")
        return sesion
