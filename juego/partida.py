import json
import random
from dataclasses import asdict

from estructuras.bst import ArbolPublicaciones
from models.publicacion import Publicacion
from models.jugador import Jugador, ROLES, ROLES_JUGABLES
from models.estado_ciudad import EstadoCiudad
from models.candidato import candidatos_iniciales
from juego.red_social import crear_red_social, ampliar_comunidad
from juego.propagacion import ServicioPropagacion, ResultadoPropagacion
from juego.decisiones import consecuencias
from juego.acciones import accion_permitida, accion_legacy, obtener_accion, acciones_para_rol
from juego.eventos import Evento, generar_evento
from juego.elecciones import calcular_eleccion
from recursos import RAIZ


class Juego:
    CAMPANAS = ("clasica", "extendida")

    def __init__(self, semilla=None, eventos=True, campana="clasica"):
        if campana not in self.CAMPANAS:
            raise ValueError("Campaña desconocida")
        self.campana = campana
        self.arbol = ArbolPublicaciones()
        self.grafo = crear_red_social()
        self.propagacion = ServicioPropagacion(self.arbol, self.grafo)
        self.estado = EstadoCiudad()
        self.jugadores = [Jugador()]
        self.turno = 0
        self.candidatos = candidatos_iniciales()
        self.azar = random.Random(semilla)
        self.semilla = semilla
        self.eventos_activos = eventos
        self.evento_actual = Evento("normal", "Bienvenido a Civitas.")
        self.indice_proxima_publicacion = 0
        self.publicacion_actual_id = None
        self.decision_aplicada = False
        self.finalizada = False
        self.publicaciones_eliminadas = []
        self.historial = []
        self.historial_propagacion = []
        self.historial_eventos = []
        self.ciudadanos_nuevos = []
        self.receptores_por_publicacion = {}
        self.ultima_propagacion = None
        self.ultima_accion = None
        self.ultima_accion_rol = None
        self.ultima_publicacion_id = None
        self.ultima_publicacion_texto = ""
        self.ultima_publicacion_verdadera = None
        self.ultimo_resultado = "El árbol comenzará vacío."
        self.ultimo_registro = None
        self.publicaciones_planificadas = self.crear_publicaciones()
        # El ABB conserva los mismos objetos y compartir aumenta su impacto.
        # La agenda electoral usa el guion inicial, nunca esos contadores.
        self._agenda_electoral = tuple(p.datos() for p in self.publicaciones_planificadas)

    @property
    def jugador(self):
        return self.jugadores[self.turno % len(self.jugadores)]

    def seleccionar_rol(self, rol):
        if rol not in ROLES_JUGABLES:
            raise ValueError("Solo puedes seleccionar al ciudadano o a la periodista")
        if self.indice_proxima_publicacion:
            raise ValueError("El rol se selecciona antes de comenzar")
        self.jugador.rol = rol

    def crear_publicaciones(self):
        with (RAIZ / "data/publicaciones.json").open(encoding="utf-8") as archivo:
            publicaciones = [Publicacion(**p) for p in json.load(archivo)]
        if self.campana == "extendida":
            from juego.campana_extendida import PUBLICACIONES_NUEVAS
            publicaciones.extend(Publicacion(**p) for p in PUBLICACIONES_NUEVAS)
        ids = [p.id for p in publicaciones]
        if len(ids) != len(set(ids)):
            raise ValueError("Los identificadores de publicaciones deben ser únicos")
        return publicaciones

    def agregar_publicacion(self, publicacion):
        if publicacion is None or self.arbol.buscar(publicacion.id) is not None:
            return False
        self.arbol.insertar(publicacion)
        self.publicacion_actual_id = publicacion.id
        self.decision_aplicada = False
        self.ultimo_resultado = f"INSERTAR: publicación #{publicacion.id} agregada al ABB."
        return True

    def agregar_siguiente_publicacion(self):
        if self.publicacion_actual_id is not None and not self.decision_aplicada:
            return False
        if self.indice_proxima_publicacion >= len(self.publicaciones_planificadas):
            self.publicacion_actual_id = None
            self.finalizada = True
            return False
        publicacion = self.publicaciones_planificadas[self.indice_proxima_publicacion]
        if not self.agregar_publicacion(publicacion):
            raise ValueError("La secuencia contiene una publicación duplicada")
        self.indice_proxima_publicacion += 1
        self.ciudadanos_nuevos = ampliar_comunidad(
            self.grafo, self.indice_proxima_publicacion, self.campana)
        if self.campana == "extendida" and self.indice_proxima_publicacion == 7:
            from juego.red_social import incorporar_influencer
            self.ciudadanos_nuevos += incorporar_influencer(self.grafo)
        self.evento_actual = generar_evento(self.azar, self) if self.eventos_activos else Evento("normal", "Una publicación llega a Civitas.")
        self.historial_eventos.append(dict(self.evento_actual.datos(), publicacion_id=publicacion.id))
        return True

    def iniciar_primera_publicacion(self):
        if self.indice_proxima_publicacion:
            return self.publicacion_actual_id is not None
        return self.agregar_siguiente_publicacion()

    def obtener_publicaciones_activas(self):
        return self.arbol.inorden()

    def obtener_publicacion_actual(self):
        return self.arbol.buscar(self.publicacion_actual_id) if self.publicacion_actual_id is not None else None

    def acciones_disponibles(self):
        return acciones_para_rol(self.jugador.rol)

    def _abrir_contacto(self, accion, publicacion):
        """Una conversación/entrevista añade relaciones reales, nunca personas ficticias."""
        origen = self.jugador.ciudadano_id
        grafo = self.grafo
        recorrido = grafo.bfs(origen, 2)
        if accion == "entrevistar":
            candidatos = [publicacion.emisor_id] + grafo.vecinos(origen) + recorrido.orden[1:]
            motivo = "Contacto de entrevista con el emisor o un testigo próximo a la publicación."
        else:
            candidatos = list(self.ciudadanos_nuevos) + recorrido.orden[1:]
            candidatos += [a for a, b in grafo.aristas() if b == origen]
            candidatos += [publicacion.emisor_id]
            motivo = "Conversación vecinal: ambos participantes pueden escucharse y recibir mensajes futuros."
        candidatos = list(dict.fromkeys(c for c in candidatos if c in grafo.nodos and c != origen))
        # Prefiere un contacto que aún no fuera recíproco. Si ya existía, se
        # conserva y se informa como tal, sin inventar un vínculo nuevo.
        vecino = (publicacion.emisor_id if accion == "entrevistar"
                  and publicacion.emisor_id in grafo.nodos and publicacion.emisor_id != origen else None)
        if vecino is None:
            vecino = next((c for c in candidatos if not grafo.existe_arista(origen, c)), None)
        if vecino is None:
            vecino = next((c for c in candidatos if not grafo.existe_arista(c, origen)),
                          candidatos[0] if candidatos else None)
        creadas = []
        if vecino:
            for a, b in ((origen, vecino), (vecino, origen)):
                if grafo.agregar_arista(a, b):
                    creadas.append([a, b])
        return {"conexiones_creadas": creadas, "motivo": motivo,
                "fuente_id" if accion == "entrevistar" else "vecino_id": vecino,
                "testimonio_verificado": False}

    def ejecutar_accion(self, accion, jugador_id=None):
        if self.decision_aplicada or not accion_permitida(accion, self.jugador.rol):
            return False
        if jugador_id is not None and jugador_id != self.jugador.id:
            return False
        publicacion = self.obtener_publicacion_actual()
        if publicacion is None or self.jugador.ciudadano_id not in self.grafo.nodos:
            return False
        accion_rol = accion
        base = accion_legacy(accion)
        definicion = obtener_accion(accion)
        titulo = definicion["titulo"] if definicion else accion.capitalize()
        antes = self.estado.datos()
        publicacion_antes = publicacion.datos()
        puntos_antes = self.jugador.puntos
        reputacion_antes = self.jugador.reputacion
        efectos_red = {"conexiones_creadas": [], "motivo": "La decisión conserva las relaciones existentes."}
        if accion in ("conversar", "entrevistar"):
            efectos_red = self._abrir_contacto(accion, publicacion)
        resultado = None
        habilidad = ROLES[self.jugador.rol]
        es_correccion = (accion in ("verificar", "contrastar") and publicacion.verdadera is False
                         or accion == "desmentir" and (publicacion.verdadera is False or publicacion.danina))
        if accion in ("compartir", "convocar") or es_correccion:
            resultado = self.propagacion.simular(publicacion.id, self.jugador.ciudadano_id,
                                                3 if accion == "convocar" else habilidad["saltos"],
                                                habilidad["intervalo"], es_correccion)
        alcance = resultado.alcance if resultado is not None else 0
        cambios, puntos, explicacion = consecuencias(accion, publicacion, alcance, self.jugador.rol)
        self.estado.aplicar(cambios)
        self.jugador.puntos += puntos
        self.jugador.reputacion = max(0, min(100, self.jugador.reputacion + puntos))
        self.jugador.confianza = max(0, min(100, self.jugador.confianza + cambios.get("confianza", 0)))
        if accion in ("compartir", "convocar"):
            publicacion.compartidos += 1
            publicacion.impacto += 1
            publicacion.estado = "CONVOCADA" if accion == "convocar" else "COMPARTIDA"
            recibidos = self.receptores_por_publicacion.setdefault(publicacion.id, set())
            recibidos.update(resultado.receptores)
            publicacion.alcance = len(recibidos)
        elif accion in ("verificar", "contrastar"):
            publicacion.verificaciones += 1
            publicacion.estado = "VERIFICADA" if publicacion.verdadera else "FALSA VERIFICADA"
            if publicacion.verdadera is None:
                publicacion.estado = "OPINIÓN"
        elif accion == "ignorar":
            publicacion.estado = "IGNORADA"
        elif accion in ("reportar", "desmentir"):
            publicacion.reportes += 1
            publicacion.estado = "REPORTADA" if publicacion.verdadera is False or publicacion.danina else "REPORTE RECHAZADO"
        elif accion == "reservar":
            publicacion.estado = "RESERVADA"
        elif accion == "conversar":
            publicacion.estado = "CONVERSADA"
        elif accion == "entrevistar":
            publicacion.estado = "TESTIMONIO PENDIENTE"
        eliminada = publicacion.estado == "REPORTADA"
        despues = self.estado.datos()
        registro = {"publicacion": publicacion.datos(), "accion": base,
                    "accion_rol": accion_rol, "rol": self.jugador.rol, "titulo_accion": titulo,
                    "publicacion_antes": publicacion_antes, "efectos_red": efectos_red,
                    "jugador_id": self.jugador.id, "alcance": alcance, "eliminada": eliminada,
                    "antes": antes, "despues": despues, "puntos": puntos,
                    "cambios_reales": {k: despues[k] - v for k, v in antes.items() if despues[k] != v},
                    "puntos_antes": puntos_antes, "puntos_despues": self.jugador.puntos,
                    "reputacion_antes": reputacion_antes, "reputacion_despues": self.jugador.reputacion,
                    "explicacion": explicacion,
                    "propagacion": resultado.datos() if resultado else None}
        self.historial.append(registro)
        self.ultimo_registro = registro
        self.ultima_propagacion = resultado
        if resultado:
            self.historial_propagacion.append(resultado.datos())
        self.ultima_accion = base
        self.ultima_accion_rol = accion_rol
        self.ultima_publicacion_id = publicacion.id
        self.ultima_publicacion_texto = publicacion.texto
        self.ultima_publicacion_verdadera = publicacion.verdadera
        self.ultimo_resultado = f"{titulo.upper()} · #{publicacion.id} · {explicacion}"
        if resultado:
            self.ultimo_resultado += f" Alcance: {alcance} ciudadanos; {resultado.tiempo_simulado:g} unidades simuladas."
        if efectos_red["conexiones_creadas"]:
            self.ultimo_resultado += f" {len(efectos_red['conexiones_creadas'])} conexiones nuevas en la red."
        if eliminada:
            self.arbol.eliminar(publicacion.id)
            self.publicaciones_eliminadas.append(publicacion.id)
            self.publicacion_actual_id = None
        self.decision_aplicada = True
        if base == "verificar" and "Primera verificación" not in self.jugador.logros:
            self.jugador.logros.append("Primera verificación")
        if base == "reportar" and eliminada and "Detección de rumor" not in self.jugador.logros:
            self.jugador.logros.append("Detección de rumor")
        if base == "compartir" and publicacion.verdadera and "Difusión responsable" not in self.jugador.logros:
            self.jugador.logros.append("Difusión responsable")
        if self.jugador.rol == "candidato" and base == "compartir" and publicacion.verdadera:
            for candidato in self.candidatos:
                if candidato.id == publicacion.candidato_id:
                    candidato.apoyo += 2
        return True

    def avanzar_publicacion(self):
        if not self.decision_aplicada or self.finalizada:
            return False
        self.turno += 1
        return self.agregar_siguiente_publicacion()

    def hay_publicaciones(self):
        return self.publicacion_actual_id is not None

    def resultado_electoral(self):
        return calcular_eleccion(
            self.candidatos, self.estado, self.historial, self.grafo,
            agenda=self._agenda_electoral if self.campana == "extendida" else None)

    def datos(self):
        return {"version": 1, "semilla": self.semilla, "eventos_activos": self.eventos_activos,
                "campana": self.campana,
                "plan_publicaciones": [p.id for p in self.publicaciones_planificadas],
                "estado": self.estado.datos(), "jugadores": [asdict(j) for j in self.jugadores],
                "turno": self.turno, "indice": self.indice_proxima_publicacion,
                "publicacion_actual_id": self.publicacion_actual_id, "decision_aplicada": self.decision_aplicada,
                "finalizada": self.finalizada,
                "publicaciones": [p.datos() for p in self.arbol.preorden()],
                "eliminadas": self.publicaciones_eliminadas, "historial": self.historial,
                "eventos": self.historial_eventos, "ciudadanos_nuevos": self.ciudadanos_nuevos,
                "nodos": [asdict(n) for n in self.grafo.nodos.values()], "aristas": self.grafo.aristas(),
                "candidatos": [asdict(c) for c in self.candidatos],
                "evento": self.evento_actual.datos(), "azar": self.azar.getstate()}

    @classmethod
    def desde_datos(cls, datos):
        from models.ciudadano import Ciudadano
        from models.candidato import Candidato
        from estructuras.grafo import Grafo
        if datos.get("version") != 1:
            raise ValueError("Versión de partida incompatible")
        juego = cls(datos["semilla"], datos["eventos_activos"],
                    campana=datos.get("campana", "clasica"))
        plan = datos.get("plan_publicaciones")
        if juego.campana == "extendida" and plan is None:
            raise ValueError("La campaña extendida necesita su plan de publicaciones")
        if plan is not None and plan != [p.id for p in juego.publicaciones_planificadas]:
            raise ValueError("El plan guardado no corresponde a la campaña")
        juego.estado = EstadoCiudad(**datos["estado"])
        juego.jugadores = [Jugador(**j) for j in datos["jugadores"]]
        if not juego.jugadores:
            raise ValueError("La partida debe tener jugadores")
        juego.turno = datos["turno"]
        juego.indice_proxima_publicacion = datos["indice"]
        juego.publicacion_actual_id = datos["publicacion_actual_id"]
        juego.decision_aplicada = datos["decision_aplicada"]
        juego.finalizada = datos.get("finalizada", False)
        if not 0 <= juego.indice_proxima_publicacion <= len(juego.publicaciones_planificadas):
            raise ValueError("Índice de publicación inválido")
        if (juego.campana == "extendida" and juego.finalizada
                and juego.indice_proxima_publicacion != len(juego.publicaciones_planificadas)):
            raise ValueError("La campaña extendida no puede finalizar antes de sus catorce casos")
        for registro in datos["publicaciones"]:
            iniciales = {k: registro[k] for k in ("id", "texto", "verdadera", "impacto", "tipo", "emisor_id", "candidato_id", "danina")}
            p = Publicacion(**iniciales)
            p.__dict__.update(registro)
            juego.arbol.insertar(p)
        juego.grafo = Grafo()
        for nodo in datos["nodos"]:
            juego.grafo.agregar_vertice(Ciudadano(**nodo))
        for a, b in datos["aristas"]:
            juego.grafo.agregar_arista(a, b)
        juego.propagacion = ServicioPropagacion(juego.arbol, juego.grafo)
        juego.candidatos = [Candidato(**c) for c in datos["candidatos"]]
        juego.publicaciones_eliminadas = list(datos["eliminadas"])
        juego.historial = list(datos["historial"])
        juego.historial_eventos = list(datos.get("eventos", []))
        juego.ciudadanos_nuevos = [id for id in datos.get("ciudadanos_nuevos", []) if id in juego.grafo.nodos]
        juego.evento_actual = Evento(**datos["evento"])
        def tuplas(valor):
            return tuple(tuplas(v) for v in valor) if isinstance(valor, list) else valor
        juego.azar.setstate(tuplas(datos["azar"]))
        if juego.historial:
            registro = juego.historial[-1]
            juego.ultimo_registro = registro
            juego.ultima_accion = registro["accion"]
            juego.ultima_accion_rol = registro.get("accion_rol", registro["accion"])
            p = registro["publicacion"]
            juego.ultima_publicacion_id = p["id"]
            juego.ultima_publicacion_texto = p["texto"]
            juego.ultima_publicacion_verdadera = p["verdadera"]
            juego.ultimo_resultado = registro["explicacion"]
            if registro["propagacion"]:
                juego.ultima_propagacion = ResultadoPropagacion(**registro["propagacion"])
        for registro in juego.historial:
            if registro["propagacion"]:
                juego.historial_propagacion.append(registro["propagacion"])
                if not registro["propagacion"]["correccion"]:
                    juego.receptores_por_publicacion.setdefault(registro["publicacion"]["id"], set()).update(registro["propagacion"]["receptores"])
        if juego.publicacion_actual_id is not None and juego.arbol.buscar(juego.publicacion_actual_id) is None:
            raise ValueError("La publicación actual no existe en el ABB")
        return juego

    def guardar(self, ruta):
        from pathlib import Path
        destino = Path(ruta)
        if destino.suffix.lower() != ".json":
            raise ValueError("El guardado debe ser JSON")
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(json.dumps(self.datos(), ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def cargar(cls, ruta):
        from pathlib import Path
        return cls.desde_datos(json.loads(Path(ruta).read_text(encoding="utf-8")))


def indicador(nombre):
    def leer(self):
        return getattr(self.estado, nombre)
    def escribir(self, valor):
        setattr(self.estado, nombre, max(0, min(100, valor)))
    return property(leer, escribir)


for _nombre in EstadoCiudad.__dataclass_fields__:
    setattr(Juego, _nombre, indicador(_nombre))
