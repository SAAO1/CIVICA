"""Cuaderno de la novela: fuentes, personajes, memoria y escenas desbloqueadas."""
from html import escape

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QTabWidget, QTextBrowser, QVBoxLayout, QWidget,
)

from arte import FUENTE_UI, aplicar_estilo, pixmap_arte
from efectos_narrativos import CapaEfectos
from juego.cuaderno import CASOS, GLOSARIO, PERFILES, caso_actual, recuerdos
from recursos import pixmap_recurso


def _texto(texto, tamano=17, color="#f6e8cd"):
    etiqueta = QLabel(texto)
    etiqueta.setWordWrap(True)
    etiqueta.setTextFormat(Qt.TextFormat.PlainText)
    etiqueta.setStyleSheet(f"color:{color}; font:{tamano}px '{FUENTE_UI}'; background:transparent;")
    return etiqueta


def _pagina_desplazable():
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    area.viewport().setAutoFillBackground(False)
    contenido = QWidget()
    contenido.setStyleSheet("background:#142b3b;")
    layout = QVBoxLayout(contenido)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(16)
    area.setWidget(contenido)
    return area, layout


class _SubrayadoFuente(CapaEfectos):
    """La consulta tiene un destello transitorio, no una animación permanente."""
    def configurar(self, reducir_movimiento=None, activo=None):
        super().configurar(reducir_movimiento=reducir_movimiento, activo=activo)
        if self._reducir_movimiento or not self._activo:
            self.detener()


class DialogoCuaderno(QDialog):
    def __init__(self, ventana, pestana=0):
        super().__init__(ventana)
        self.ventana = ventana
        self.setWindowTitle("Cuaderno de Ciudad Nova")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setMinimumSize(680, 460)
        self.resize(min(950, ventana.width()-70), min(690, ventana.height()-65))
        self.setObjectName("cuadernoNovela")
        exterior = QVBoxLayout(self)
        exterior.setContentsMargins(24, 18, 24, 18)
        exterior.setSpacing(12)
        cabecera = QHBoxLayout()
        cabecera.addWidget(_texto("CUADERNO DE CIUDAD NOVA", 23, "#e8c78f"), 1)
        cerrar = QPushButton("Volver al juego")
        cerrar.setMinimumWidth(205)
        cerrar.setToolTip("También puedes volver con Esc")
        cerrar.clicked.connect(self.close)
        cabecera.addWidget(cerrar)
        exterior.addLayout(cabecera)
        self.aviso = _texto("Explora a tu ritmo. Las fuentes pertenecen al mundo ficticio de CIVICA.", 14, "#bbd5d1")
        if (ventana.escenas.currentWidget() is ventana.escena_accion and ventana.juego.evento_actual.urgente
                and (ventana.cliente_red is not None or not ventana.sin_limite)):
            self.aviso.setText("La alerta de la sala sigue su plazo mientras consultas el cuaderno; el servidor controla el tiempo."
                               if ventana.cliente_red is not None else
                               "La alerta sigue contando mientras consultas el cuaderno. Puedes activar decisiones sin límite en Configuración.")
        exterior.addWidget(self.aviso)
        self.pestanas = QTabWidget()
        self.pestanas.setAccessibleName("Secciones del cuaderno")
        exterior.addWidget(self.pestanas, 1)
        self._investigar()
        self._personajes()
        self._historial()
        self._galeria()
        self._glosario()
        self.pestanas.setCurrentIndex(pestana)
        self.pestanas.currentChanged.connect(self._cambiar_seccion)
        aplicar_estilo(self)
        self.setStyleSheet(self.styleSheet() + "QDialog#cuadernoNovela {background:#142b3b;} "
                           "QFrame#fichaCuaderno {background:#203e4d; border:1px solid #557c80; border-radius:12px;}")

    def _investigar(self):
        pagina, layout = _pagina_desplazable()
        caso = caso_actual(self.ventana.juego)
        publicacion = self.ventana.juego.obtener_publicacion_actual()
        identificador = publicacion.id if publicacion else self.ventana.juego.ultima_publicacion_id
        if identificador is None:
            layout.addWidget(_texto("El cuaderno se abrirá con tu primer caso. Mientras tanto, conoce a los personajes y explora el glosario.", 20))
            layout.addStretch()
            self.pestanas.addTab(pagina, "Investigar")
            return
        layout.addWidget(_texto(caso["acto"], 14, "#e8c78f"))
        layout.addWidget(_texto(caso["titulo"], 26))
        layout.addWidget(_texto(caso["objetivo"], 18, "#bbd5d1"))
        self.progreso_pistas = _texto("", 15, "#e8c78f")
        layout.addWidget(self.progreso_pistas)
        # Franja decorativa independiente: el hallazgo nunca invade una pista
        # o el botón que la abre y no cambia ninguna mecánica de investigación.
        self.efectos_pista = _SubrayadoFuente()
        self.efectos_pista.setFixedHeight(16)
        self.efectos_pista.setAccessibleName("Subrayado de la fuente consultada")
        self._configurar_efectos_pista()
        layout.addWidget(self.efectos_pista)
        self.pistas = []
        for indice, pista in enumerate(caso["pistas"]):
            tarjeta = QFrame()
            tarjeta.setObjectName("fichaCuaderno")
            contenido = QVBoxLayout(tarjeta)
            contenido.setContentsMargins(18, 15, 18, 15)
            boton = QPushButton(f"{indice+1:02d}  ·  {pista['titulo']}")
            boton.setCheckable(True)
            boton.setAccessibleName("Examinar " + pista["titulo"])
            detalle = _texto(pista["texto"], 19)
            orientacion = _texto(pista["pregunta"], 16, "#bbd5d1")
            contenido.addWidget(boton)
            contenido.addWidget(detalle)
            contenido.addWidget(orientacion)
            visto = (identificador, indice) in self.ventana.pistas_consultadas
            detalle.setVisible(visto)
            orientacion.setVisible(visto)
            boton.setChecked(visto)
            boton.toggled.connect(lambda abierto, i=indice, d=detalle, o=orientacion:
                                  self._ver_pista(identificador, i, abierto, d, o))
            self.pistas.append(boton)
            layout.addWidget(tarjeta)
        self._actualizar_pistas(identificador)
        layout.addWidget(_texto("Vuelve a la publicación para decidir qué hacer. Consultar una fuente no aplica una acción ni otorga puntos.", 15, "#bbd5d1"))
        layout.addStretch()
        self.pestanas.addTab(pagina, "Investigar")

    def _ver_pista(self, identificador, indice, abierto, detalle, orientacion):
        detalle.setVisible(abierto)
        orientacion.setVisible(abierto)
        if abierto:
            self.ventana.pistas_consultadas.add((identificador, indice))
            self._destacar_fuente()
        self._actualizar_pistas(identificador)

    def _configurar_efectos_pista(self):
        if not hasattr(self, "efectos_pista"):
            return
        reducir = bool(getattr(self.ventana, "reducir_movimiento", False))
        activo = bool(getattr(self.ventana, "animar_fondos", True))
        self.efectos_pista.configurar(reducir_movimiento=reducir, activo=activo)
        if reducir or not activo:
            self.efectos_pista.detener()

    def _destacar_fuente(self):
        self._configurar_efectos_pista()
        if (hasattr(self, "efectos_pista")
                and not getattr(self.ventana, "reducir_movimiento", False)
                and getattr(self.ventana, "animar_fondos", True)):
            self.efectos_pista.reproducir("fuente", duracion=2.1, intensidad=.85)

    def _cambiar_seccion(self, indice):
        if indice != 0 and hasattr(self, "efectos_pista"):
            self.efectos_pista.detener()

    def hideEvent(self, event):
        if hasattr(self, "efectos_pista"):
            self.efectos_pista.detener()
        super().hideEvent(event)

    def closeEvent(self, event):
        if hasattr(self, "efectos_pista"):
            self.efectos_pista.detener()
        super().closeEvent(event)

    def _actualizar_pistas(self, identificador):
        vistas = sum((identificador, i) in self.ventana.pistas_consultadas for i in range(3))
        self.progreso_pistas.setText(f"{vistas} de 3 fuentes consultadas")
        if hasattr(self.ventana.escena_accion, "actualizar_pistas"):
            self.ventana.escena_accion.actualizar_pistas()

    def _personajes(self):
        pagina, layout = _pagina_desplazable()
        for perfil in PERFILES:
            ficha = QFrame()
            ficha.setObjectName("fichaCuaderno")
            fila = QHBoxLayout(ficha)
            fila.setContentsMargins(18, 18, 18, 18)
            retrato = QLabel()
            retrato.setFixedSize(125, 164)
            retrato.setAlignment(Qt.AlignmentFlag.AlignCenter)
            imagen = pixmap_arte(perfil["recurso"])
            retrato.setPixmap(imagen.scaled(retrato.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            fila.addWidget(retrato)
            texto = QVBoxLayout()
            texto.addWidget(_texto(perfil["nombre"], 23, "#e8c78f"))
            texto.addWidget(_texto(perfil["rol"], 15, "#bbd5d1"))
            texto.addWidget(_texto(perfil["deseo"], 19))
            texto.addWidget(_texto(perfil["conflicto"], 17))
            fila.addLayout(texto, 1)
            layout.addWidget(ficha)
        layout.addStretch()
        self.pestanas.addTab(pagina, "Personajes")

    def _historial(self):
        pagina = QTextBrowser()
        pagina.setAccessibleName("Diálogos leídos en esta sesión")
        bloques = []
        for nombre, texto in self.ventana.historial_dialogos:
            bloques.append(f"<p style='color:#e8c78f'><b>{escape(nombre)}</b></p><p>{escape(texto)}</p><hr>")
        pagina.setHtml("<h2>Lo que hemos vivido</h2>" + ("".join(bloques) or "<p>Los diálogos aparecerán aquí al terminar de mostrarse.</p>"))
        self.pestanas.addTab(pagina, "Historial")
        pagina.verticalScrollBar().setValue(pagina.verticalScrollBar().maximum())

    def _galeria(self):
        pagina, layout = _pagina_desplazable()
        biblioteca = self.ventana.biblioteca
        layout.addWidget(_texto(f"ESCENAS RECORDADAS · {len(biblioteca.escenas)} / 7", 21, "#e8c78f"))
        layout.addWidget(_texto("Cada decisión guarda una escena. Vuelve a jugar para descubrir otras reacciones y desenlaces.", 17))
        actuales = {str(r["id"]): r for r in recuerdos(self.ventana.juego)}
        for identificador, caso in [*[(str(i), c) for i, c in CASOS.items()], ("final", {"titulo": "La elección de Ciudad Nova", "fondo": "assets/fondos/Escena 1.jfif", "cierre": "La campaña termina. Sus vínculos continúan."})]:
            desbloqueado = identificador in biblioteca.escenas
            tarjeta = QFrame()
            tarjeta.setObjectName("fichaCuaderno")
            fila = QHBoxLayout(tarjeta)
            fila.setContentsMargins(16, 16, 16, 16)
            datos = actuales.get(identificador, {})
            if desbloqueado:
                imagen = QLabel()
                imagen.setFixedSize(205, 120)
                imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
                recurso = datos.get("recurso", caso["fondo"])
                pixmap = pixmap_recurso(recurso) if recurso.startswith("assets/") else pixmap_arte(recurso)
                imagen.setPixmap(pixmap.scaled(imagen.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                fila.addWidget(imagen)
            relato = QVBoxLayout()
            relato.addWidget(_texto(caso["titulo"] if desbloqueado else "Escena por descubrir", 21, "#e8c78f" if desbloqueado else "#aec0c4"))
            relato.addWidget(_texto(datos.get("texto", caso["cierre"]) if desbloqueado else "Continúa la historia para desbloquear este recuerdo.", 17))
            fila.addLayout(relato, 1)
            layout.addWidget(tarjeta)
        layout.addStretch()
        self.pestanas.addTab(pagina, "Galería")

    def _glosario(self):
        pagina = QTextBrowser()
        pagina.setHtml("<h2>Para leer la ciudad</h2>" + "".join(
            f"<h3 style='color:#e8c78f'>{escape(termino)}</h3><p>{escape(texto)}</p>" for termino, texto in GLOSARIO.items()))
        self.pestanas.addTab(pagina, "Glosario")
