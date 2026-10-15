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
from juego.eventos import Evento, generar_evento
from juego.elecciones import calcular_eleccion
from recursos import RAIZ


class Juego:
    def __init__(self, semilla=None, eventos=True):
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
        self.ultima_publicacion_id = None
        self.ultima_publicacion_texto = ""
        self.ultima_publicacion_verdadera = None
        self.ultimo_resultado = "El árbol comenzará vacío."
        self.ultimo_registro = None
        self.publicaciones_planificadas = self.crear_publicaciones()

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
        self.ciudadanos_nuevos = ampliar_comunidad(self.grafo, self.indice_proxima_publicacion)
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

    def ejecutar_accion(self, accion, jugador_id=None):
        if accion not in ("compartir", "verificar", "ignorar", "reportar") or self.decision_aplicada:
            return False
        if jugador_id is not None and jugador_id != self.jugador.id:
            return False
        publicacion = self.obtener_publicacion_actual()
        if publicacion is None:
            return False
        antes = self.estado.datos()
        resultado = None
        habilidad = ROLES[self.jugador.rol]
        if accion == "compartir" or (accion == "verificar" and publicacion.verdadera is False):
            resultado = self.propagacion.simular(publicacion.id, self.jugador.ciudadano_id,
                                                habilidad["saltos"], habilidad["intervalo"], accion == "verificar")
        alcance = resultado.alcance if resultado is not None else 0
        cambios, puntos, explicacion = consecuencias(accion, publicacion, alcance, self.jugador.rol)
        self.estado.aplicar(cambios)
        self.jugador.puntos += puntos
        self.jugador.reputacion = max(0, min(100, self.jugador.reputacion + puntos))
        self.jugador.confianza = max(0, min(100, self.jugador.confianza + cambios.get("confianza", 0)))
        if accion == "compartir":
            publicacion.compartidos += 1
            publicacion.impacto += 1
            publicacion.estado = "COMPARTIDA"
            recibidos = self.receptores_por_publicacion.setdefault(publicacion.id, set())
            recibidos.update(resultado.receptores)
            publicacion.alcance = len(recibidos)
        elif accion == "verificar":
            publicacion.verificaciones += 1
            publicacion.estado = "VERIFICADA" if publicacion.verdadera else "FALSA VERIFICADA"
            if publicacion.verdadera is None:
                publicacion.estado = "OPINIÓN"
        elif accion == "ignorar":
            publicacion.estado = "IGNORADA"
        else:
            publicacion.reportes += 1
            publicacion.estado = "REPORTADA" if publicacion.verdadera is False or publicacion.danina else "REPORTE RECHAZADO"
        eliminada = publicacion.estado == "REPORTADA"
        registro = {"publicacion": publicacion.datos(), "accion": accion,
                    "jugador_id": self.jugador.id, "alcance": alcance, "eliminada": eliminada,
                    "antes": antes, "despues": self.estado.datos(), "puntos": puntos,
                    "explicacion": explicacion,
                    "propagacion": resultado.datos() if resultado else None}
        self.historial.append(registro)
        self.ultimo_registro = registro
        self.ultima_propagacion = resultado
        if resultado:
            self.historial_propagacion.append(resultado.datos())
        self.ultima_accion = accion
        self.ultima_publicacion_id = publicacion.id
        self.ultima_publicacion_texto = publicacion.texto
        self.ultima_publicacion_verdadera = publicacion.verdadera
        self.ultimo_resultado = f"{accion.upper()} · #{publicacion.id} · {explicacion}"
        if resultado:
            self.ultimo_resultado += f" Alcance: {alcance} ciudadanos; {resultado.tiempo_simulado:g} unidades simuladas."
        if eliminada:
            self.arbol.eliminar(publicacion.id)
            self.publicaciones_eliminadas.append(publicacion.id)
            self.publicacion_actual_id = None
        self.decision_aplicada = True
        if accion == "verificar" and "Primera verificación" not in self.jugador.logros:
            self.jugador.logros.append("Primera verificación")
        if accion == "reportar" and eliminada and "Detección de rumor" not in self.jugador.logros:
            self.jugador.logros.append("Detección de rumor")
        if accion == "compartir" and publicacion.verdadera and "Difusión responsable" not in self.jugador.logros:
            self.jugador.logros.append("Difusión responsable")
        if self.jugador.rol == "candidato" and accion == "compartir" and publicacion.verdadera:
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
        return calcular_eleccion(self.candidatos, self.estado, self.historial)

    def datos(self):
        return {"version": 1, "semilla": self.semilla, "eventos_activos": self.eventos_activos,
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
        juego = cls(datos["semilla"], datos["eventos_activos"])
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
