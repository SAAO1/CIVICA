"""Investigación sobre las escenas de la novela, con el estado real de la sesión."""
from pathlib import Path

from PyQt6.QtCore import QEvent, QPoint, QPointF, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QGridLayout, QHBoxLayout, QLabel, QScrollArea, QSlider, QStackedWidget, QVBoxLayout, QWidget,
)

from infraestructura.recursos import RAIZ
from audio.catalogo_voces import PERFILES, clave_clip, normalizar_texto, ruta_clip
from interfaz.componentes.arte import avatar_arte, cargar_tipografias
from interfaz.feria.expediente import ComparadorPrueba as _ComparadorPrueba
from interfaz.novela.componentes import BotonNovela, MarcoNovela, decorar_novela, imagen_novela
from interfaz.novela.guia_investigacion import ProgresoInvestigacion, viajar_prueba


class ComparadorPrueba(_ComparadorPrueba):
    """Conserva el instrumento real con la paleta de la novela."""
    def paintEvent(self, event):
        super().paintEvent(event)
        p=QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(0,0,self.width(),34,QColor("#17243d"))
        p.setPen(QColor("#f6e9ce"))
        izquierda="PRUEBA GUARDADA" if self.recuperado else "ARRASTRA PARA BUSCAR LO OMITIDO"
        p.drawText(self.rect().adjusted(12,0,-12,-self.height()+34),
                   Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignLeft,izquierda)
        p.drawText(self.rect().adjusted(12,0,-12,-self.height()+34),
                   Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignRight,"RECORTE")
        corte=self.width()*self.valor/100
        p.setPen(QPen(QColor("#b99249"),4))
        p.drawLine(QPointF(corte,34),QPointF(corte,self.height()))
        p.setBrush(QColor("#17243d"))
        p.drawEllipse(QPointF(corte,self.height()/2),19,19)
        p.setPen(QColor("#f6e9ce"))
        p.drawText(QRectF(corte-18,self.height()/2-18,36,36),Qt.AlignmentFlag.AlignCenter,"↔")
        p.end()


def _texto(texto="", titulo=False):
    etiqueta = QLabel(texto)
    etiqueta.setWordWrap(True)
    etiqueta.setTextFormat(Qt.TextFormat.PlainText)
    etiqueta.setStyleSheet("color:#17243d;background:transparent;font:" + ("bold 23px" if titulo else "17px") + " 'Atkinson Hyperlegible';")
    return etiqueta


class OverlayInvestigacion(QWidget):
    """Una pista, una respuesta y una confirmación, sobre la novela original."""
    comando = pyqtSignal(dict)
    cerrado = pyqtSignal()
    _REQUIEREN = frozenset(("contrastar", "desmentir", "rectificar"))
    _COPIAS = {
        "compartir": ("Compartir", "El mensaje llegará a tu grupo.", "redactar"),
        "conversar": ("Escuchar al barrio", "Hablar sin reenviar el mensaje.", "audio"),
        "ignorar": ("Seguir sin reenviar", "Conservar la duda y seguir.", "volver"),
        "contrastar": ("Comprobar la fuente", "Contrastar el mensaje con una prueba.", "investigar"),
        "desmentir": ("Desmentir y retirar", "Enviar una corrección y denunciar.", "redactar"),
        "reservar": ("Dejar en reserva", "Esperar sin publicar.", "volver"),
        "rectificar": ("Rectificar", "Corregir con la prueba recuperada.", "expediente"),
        "convocar": ("Convocar al barrio", "Hacer llegar el mensaje a más vecinos.", "audiencia"),
        "entrevistar": ("Escuchar a la fuente", "Conversar sin dar por cierto el mensaje.", "audio"),
    }

    def __init__(self, vista, callback=None, parent=None):
        super().__init__(parent)
        cargar_tipografias()
        self.callback = callback
        self.vista = {}
        self._caso_id = None
        self._actualizando = False
        self._cerrado = False
        self._accion = None
        self._pendiente = None
        self._hallazgo_abierto = None
        self._firma_pistas = None
        self._firma_acciones = None
        self._prueba = None
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        if parent:
            parent.installEventFilter(self)
            self.setGeometry(parent.rect())
        else:
            self.resize(1100,700)
        self.marco = MarcoNovela(self)
        principal = QVBoxLayout(self.marco)
        principal.setContentsMargins(25,16,25,16)
        principal.setSpacing(8)
        cabecera = QHBoxLayout()
        self.titulo = _texto("",True)
        self.titulo.setStyleSheet("color:#17243d;background:transparent;font:bold 20px 'Atkinson Hyperlegible';")
        self.presupuesto = _texto()
        self.presupuesto.setToolTip("Investigaciones disponibles en este acto. Una visita o un hallazgo usa una.")
        self.salir = BotonNovela("Volver")
        self.salir.setMinimumHeight(38)
        self.salir.setMaximumHeight(42)
        self.salir.clicked.connect(self.cerrar)
        cabecera.addWidget(self.titulo,1)
        cabecera.addWidget(self.presupuesto)
        cabecera.addWidget(self.salir)
        principal.addLayout(cabecera)
        navegacion = QHBoxLayout()
        self.botones_seccion = {}
        for clave,titulo in (("fuentes","1 · Buscar"),("decision","2 · Responder"),("confirmacion","3 · Confirmar")):
            boton = BotonNovela(titulo)
            boton.setCheckable(True)
            boton.setMinimumHeight(38)
            boton.setMaximumHeight(42)
            boton.clicked.connect(lambda _=False,c=clave:self._ir_confirmacion() if c=="confirmacion" else self.abrir(c))
            navegacion.addWidget(boton)
            self.botones_seccion[clave]=boton
        principal.addLayout(navegacion)
        self.indicacion = _texto()
        self.indicacion.setMinimumHeight(28)
        self.indicacion.setStyleSheet("color:#17243d;background:#eadcbf;padding:5px;font:16px 'Atkinson Hyperlegible';")
        principal.addWidget(self.indicacion)
        self.aviso = self.indicacion
        self.paginas = QStackedWidget()
        self.secciones = {}
        self._crear_fuentes()
        self._crear_material()
        self._crear_pista()
        self._crear_respuestas()
        self._crear_confirmacion()
        principal.addWidget(self.paginas,1)
        self.siguiente_paso = BotonNovela("Examinar el mensaje")
        self.siguiente_paso.setMinimumHeight(42)
        self.siguiente_paso.setMaximumHeight(46)
        self.siguiente_paso.clicked.connect(self._siguiente)
        self.confirmar = BotonNovela("Confirmar")
        self.confirmar.setMinimumHeight(42)
        self.confirmar.setMaximumHeight(46)
        self.confirmar.clicked.connect(self._confirmar)
        pie = QHBoxLayout()
        pie.addWidget(self.siguiente_paso)
        pie.addWidget(self.confirmar)
        principal.addLayout(pie)
        self.setStyleSheet("QSlider::groove:horizontal{height:6px;background:#bea77a;border-radius:3px;} QSlider::handle:horizontal{background:#bd944b;border:2px solid #e3c48c;width:20px;margin:-8px 0;border-radius:9px;}")
        self.actualiza(vista)
        self._colocar()
        self.hide()

    def _pagina(self,clave):
        pagina = QWidget()
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(4,2,4,2)
        layout.setSpacing(8)
        self.secciones[clave]=self.paginas.addWidget(pagina)
        return layout

    def _crear_fuentes(self):
        contenido = self._pagina("fuentes")
        from interfaz.novela.mapa import MapaNovela
        self.mapa = MapaNovela()
        self.mapa.setMaximumHeight(340)
        self.mapa.seleccionado.connect(lambda lugar:self._enviar("investigar",lugar=lugar))
        contenido.addWidget(self.mapa,1)
        self.botones_lugares = self.mapa.botones
        self.pistas_layout = QHBoxLayout()
        contenido.addLayout(self.pistas_layout)

    def _crear_material(self):
        contenido = self._pagina("material")
        self.fragmento = _texto()
        self.fragmento.setMaximumHeight(85)
        contenido.addWidget(self.fragmento)
        self.area_prueba = QScrollArea()
        self.area_prueba.setStyleSheet("QScrollArea{background:transparent;border:1px solid #b59b76;}")
        self.area_prueba.setWidgetResizable(True)
        self.area_prueba.setMinimumHeight(210)
        self.comparador = ComparadorPrueba()
        self.comparador.setMinimumHeight(205)
        self.area_prueba.setWidget(self.comparador)
        contenido.addWidget(self.area_prueba,1)
        fila = QHBoxLayout()
        self.botones_zona = []
        for nombre,valor in (("Inicio",15),("Recorte",50),("Contexto",85)):
            boton=BotonNovela(nombre)
            boton.setMinimumHeight(36)
            boton.setMaximumHeight(40)
            boton.clicked.connect(lambda _=False,v=valor:self.slider.setValue(65 if v==85 and self._medio().get("tipo")=="audio" else v))
            fila.addWidget(boton)
            self.botones_zona.append(boton)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0,100)
        self.slider.setAccessibleName("Punto de la prueba que quieres examinar")
        self.slider.valueChanged.connect(self.comparador.establecer_valor)
        self.comparador.valor_cambiado.connect(self.slider.setValue)
        self.slider.valueChanged.connect(self._fragmento_audio)
        fila.addWidget(self.slider,1)
        self.ampliar = BotonNovela("Leer en detalle")
        self.ampliar.setCheckable(True)
        self.ampliar.setMinimumHeight(36)
        self.ampliar.setMaximumHeight(40)
        self.ampliar.toggled.connect(self._ampliar)
        fila.addWidget(self.ampliar)
        self.escuchar = BotonNovela("Escuchar")
        self.escuchar.setMinimumHeight(36)
        self.escuchar.setMaximumHeight(40)
        self.escuchar.clicked.connect(self._escuchar)
        fila.addWidget(self.escuchar)
        contenido.addLayout(fila)
        self.disponibilidad_audio = _texto()
        self.disponibilidad_audio.setStyleSheet("color:#17243d;background:transparent;font:14px 'Atkinson Hyperlegible';")
        contenido.addWidget(self.disponibilidad_audio)
        self.examinar = BotonNovela(parent=self)
        self.examinar.hide()
        self.examinar.clicked.connect(self._examinar)

    def _crear_pista(self):
        contenido = self._pagina("pista")
        fila = QHBoxLayout()
        self.pista_imagen = QLabel()
        self.pista_imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pista_imagen.setMinimumWidth(230)
        self.pista_imagen.setMinimumHeight(200)
        self.pista_imagen.setMaximumHeight(360)
        fila.addWidget(self.pista_imagen,1)
        texto = QVBoxLayout()
        self.pista_titulo = _texto("",True)
        self.pista_texto = _texto()
        texto.addWidget(self.pista_titulo)
        texto.addWidget(self.pista_texto,1)
        self.compartir_pista = BotonNovela("Compartir esta fuente")
        self.compartir_pista.clicked.connect(lambda:self._enviar("compartir_hallazgo",evidencia_id=self._hallazgo_abierto))
        texto.addWidget(self.compartir_pista)
        fila.addLayout(texto,1)
        contenido.addLayout(fila,1)

    def _crear_respuestas(self):
        contenido = self._pagina("decision")
        fila = QHBoxLayout()
        prueba = QVBoxLayout()
        self.prueba_imagen = QLabel()
        self.prueba_imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.prueba_imagen.setFixedWidth(245)
        self.prueba_imagen.setMaximumHeight(235)
        self.prueba_nombre = _texto()
        self.prueba_nombre.setMaximumWidth(245)
        prueba.addWidget(self.prueba_imagen)
        prueba.addWidget(self.prueba_nombre)
        prueba.addStretch()
        fila.addLayout(prueba)
        self.acciones_layout = QGridLayout()
        self.botones_accion = {}
        self.motivos_accion = {}
        fila.addLayout(self.acciones_layout,1)
        contenido.addLayout(fila,1)
        self.motivo = _texto()
        self.motivo.setStyleSheet("color:#773c30;background:transparent;font:16px 'Atkinson Hyperlegible';")
        contenido.addWidget(self.motivo)

    def _crear_confirmacion(self):
        contenido = self._pagina("confirmacion")
        self.confirmacion_icono = QLabel()
        self.confirmacion_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.confirmacion_icono.setMaximumHeight(150)
        self.confirmacion_titulo = _texto("",True)
        self.confirmacion_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.confirmacion_detalle = _texto()
        self.confirmacion_detalle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        contenido.addStretch()
        contenido.addWidget(self.confirmacion_icono)
        contenido.addWidget(self.confirmacion_titulo)
        contenido.addWidget(self.confirmacion_detalle)
        contenido.addStretch()

    def _hallazgos_visibles(self):
        id=self.vista.get("mi_id")
        return [h for h in self.vista.get("hallazgos",[])
                if not self.vista.get("cooperativa") or h.get("compartido") or h.get("propietario")==id]

    def _actuales(self):
        return [h for h in self._hallazgos_visibles() if h.get("caso_id")==self._caso_id]

    def _elegir_prueba(self):
        elegibles=[h for h in self._actuales() if h.get("tipo") in ("documento","contexto","medio")]
        prioridad={"documento":0,"medio":1,"contexto":2}
        return min(elegibles,key=lambda h:prioridad[h["tipo"]],default=None)

    def _imagen_hallazgo(self,hallazgo):
        if hallazgo.get("tipo")=="testimonio":
            caso=self.vista.get("caso") or {}
            retrato=hallazgo.get("fuente_retrato") or caso.get("fuente_retrato")
            if retrato and retrato.startswith("avatar:"):
                return avatar_arte(retrato.partition(":")[2])
            if retrato:
                imagen=QPixmap(str(RAIZ/retrato))
                recorte=hallazgo.get("fuente_recorte") or caso.get("fuente_recorte")
                if recorte and not imagen.isNull():
                    ancho,alto=imagen.width(),imagen.height()
                    x=max(0,min(ancho-1,round(ancho*recorte.get("x",0))))
                    y=max(0,min(alto-1,round(alto*recorte.get("y",0))))
                    w=max(1,min(ancho-x,round(ancho*recorte.get("ancho",1))))
                    h=max(1,min(alto-y,round(alto*recorte.get("alto",1))))
                    imagen=imagen.copy(x,y,w,h)
                if not imagen.isNull():
                    return imagen
            return avatar_arte(hallazgo.get("fuente_id") or caso.get("npc_id",""))
        id=hallazgo.get("caso_id",self._caso_id)
        nueva=RAIZ/f"assets/novela/props/{id}_original.png"
        respaldo=RAIZ/f"assets/feria/pruebas/{id}_original.png"
        return QPixmap(str(nueva if nueva.is_file() else respaldo))

    @staticmethod
    def _vaciar(layout):
        while layout.count():
            item=layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                OverlayInvestigacion._vaciar(item.layout())

    def _activo(self):
        return self.vista.get("fase") in ("investigacion","decision") and self.vista.get("mi_id") not in self.vista.get("decididos",[])

    def _mi_turno(self):
        return self.vista.get("turno_id")==self.vista.get("mi_id")

    def _acciones_cortas(self):
        claves=("conversar","compartir","ignorar") if self.vista.get("mi_rol")=="ciudadano" else ("contrastar","desmentir","reservar")
        disponibles={a["clave"]:a for a in self.vista.get("acciones",[])}
        claves=list(claves)
        if self._accion in disponibles and self._accion not in claves:
            claves.append(self._accion)
        return [disponibles[c] for c in claves if c in disponibles]

    def _elegibilidad(self,accion):
        datos=next((a for a in self.vista.get("acciones",[]) if a["clave"]==accion),None)
        if datos is None:
            return False,"Elige una respuesta disponible."
        if accion in self._REQUIEREN and self._prueba is None:
            return False,"Falta un documento o el contexto de este mensaje."
        if datos.get("disponible") is False:
            return False,datos.get("motivo_no_disponible") or "Esta respuesta no está disponible."
        return True,""

    def _recrear_acciones(self):
        acciones=self._acciones_cortas()
        firma=tuple(a["clave"] for a in acciones)
        if firma!=self._firma_acciones:
            self._firma_acciones=firma
            self._vaciar(self.acciones_layout)
            self.botones_accion={}
            self.motivos_accion={}
            for i,accion in enumerate(acciones):
                clave=accion["clave"]
                titulo,detalle,icono=self._COPIAS.get(clave,(accion.get("titulo",clave),"","redactar"))
                tarjeta=QWidget()
                caja=QVBoxLayout(tarjeta)
                caja.setContentsMargins(4,4,4,4)
                boton=BotonNovela(titulo)
                boton.setIcon(QIcon(imagen_novela(f"ui/{icono}.png")))
                boton.setIconSize(QSize(35,35))
                boton.setCheckable(True)
                boton.setMinimumHeight(63)
                boton.clicked.connect(lambda _=False,c=clave:self.decision(c))
                caja.addWidget(boton)
                motivo=_texto(detalle)
                motivo.setStyleSheet("color:#17243d;background:transparent;font:14px 'Atkinson Hyperlegible';")
                caja.addWidget(motivo)
                self.acciones_layout.addWidget(tarjeta,i//2,i%2)
                self.botones_accion[clave]=boton
                self.motivos_accion[clave]=motivo
        for accion in acciones:
            clave=accion["clave"]
            valido,motivo=self._elegibilidad(clave)
            boton=self.botones_accion[clave]
            boton.setEnabled(self._activo() and valido)
            boton.setChecked(clave==self._accion)
            self.motivos_accion[clave].setText(motivo or self._COPIAS.get(clave,("","",None))[1])

    def actualiza(self,vista):
        anteriores={h["id"] for h in self._hallazgos_visibles()}
        self._actualizando=True
        self.vista=vista
        caso=vista.get("caso") or {}
        nuevo=caso.get("id")!=self._caso_id
        if nuevo:
            self._caso_id=caso.get("id")
            self._accion=None
            self._hallazgo_abierto=None
            self._firma_pistas=None
            self._firma_acciones=None
            self._pendiente=None
            self.slider.setValue(0)
            self.ampliar.setChecked(False)
        self._prueba=self._elegir_prueba()
        self.titulo.setText(caso.get("titulo","Investigar"))
        self.titulo.setToolTip(caso.get("objetivo",""))
        restantes=vista.get("acciones_restantes",0)
        self.presupuesto.setText(f"{restantes}/2 investigaciones")
        activa=self._activo()
        self.mapa.actualiza([dict(l,disponible=bool(activa and restantes>0 and l.get("disponible")))
                            for l in vista.get("lugares",[])])
        actuales=self._actuales()
        privados=[h for h in vista.get("hallazgos_disponibles",[])
                  if str(h.get("id","")).split(":")[0]==str(self._caso_id) and not h.get("compartido")]
        firma=repr((actuales,privados))
        if firma!=self._firma_pistas:
            self._firma_pistas=firma
            self._vaciar(self.pistas_layout)
            for h in actuales:
                boton=BotonNovela("Leer "+("testimonio" if h.get("tipo")=="testimonio" else "prueba"))
                boton.setIcon(QIcon(imagen_novela("ui/expediente.png")))
                boton.clicked.connect(lambda _=False,h=h:self.ver_hallazgo(h))
                self.pistas_layout.addWidget(boton)
            for h in privados:
                boton=BotonNovela("Pedir la fuente al compañero")
                boton.clicked.connect(lambda _=False,id=h["id"]:self._enviar("solicitar_hallazgo",evidencia_id=id))
                self.pistas_layout.addWidget(boton)
        medio=self._medio()
        recuperado=bool(medio.get("revelado") or medio.get("recuperado"))
        es_audio=medio.get("tipo")=="audio"
        self.comparador.actualizar(self._ruta_prueba(False),self._ruta_prueba(True),recuperado,
                                  inspeccionable=bool(medio.get("inspeccionable",activa and restantes>0)))
        self.area_prueba.setVisible(not es_audio)
        self.ampliar.setVisible(not es_audio)
        self.escuchar.setVisible(es_audio)
        self.examinar.setEnabled(activa and restantes>0 and not recuperado)
        self._fragmento_audio(self.slider.value())
        self._recrear_acciones()
        if self._prueba:
            self.prueba_nombre.setText(self._prueba.get("titulo","Prueba de este mensaje"))
            self.prueba_imagen.setPixmap(self._imagen_hallazgo(self._prueba).scaled(240,230,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
        else:
            self.prueba_nombre.setText("Aún no tienes una prueba documental de este mensaje.")
            self.prueba_imagen.setPixmap(imagen_novela("ui/expediente.png").scaled(150,150,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
        abierto=next((h for h in actuales if h["id"]==self._hallazgo_abierto),None)
        self.compartir_pista.setVisible(bool(abierto and vista.get("cooperativa") and
            abierto.get("propietario")==vista.get("mi_id") and not abierto.get("compartido")))
        self._actualizando=False
        nuevos=[h for h in actuales if h["id"] not in anteriores]
        if nuevos and self._pendiente in ("investigar","examinar","entrevistar"):
            self._pendiente=None
            self.ver_hallazgo(nuevos[-1])
        if self.paginas.currentIndex()==self.secciones["confirmacion"]:
            self._actualizar_confirmacion()
        self._refrescar_paso()

    def ver_hallazgo(self,hallazgo):
        h=next((h for h in self._actuales() if h["id"]==hallazgo.get("id")),None)
        if h is None:
            self.mostrar_mensaje("Pide al compañero la fuente de este mensaje.")
            return False
        self._hallazgo_abierto=h["id"]
        fuente=h.get("fuente_nombre") or self.vista.get("caso",{}).get("npc_nombre","La fuente")
        self.pista_titulo.setText(fuente if h.get("tipo")=="testimonio" else h.get("titulo","Prueba recuperada"))
        self.pista_texto.setText(h.get("texto",""))
        self.pista_imagen.setPixmap(self._imagen_hallazgo(h).scaled(480,350,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
        self.compartir_pista.setVisible(bool(self.vista.get("cooperativa") and h.get("propietario")==self.vista.get("mi_id") and not h.get("compartido")))
        self.abrir("pista")
        return True

    def decision(self,accion):
        self._accion=accion
        self._recrear_acciones()
        self.abrir("decision")

    def _usar_hallazgo(self):
        caso=self._caso_id
        def llegar():
            if not self._cerrado and self._caso_id==caso:
                self.abrir("decision")
        objetivo=self.botones_seccion["decision"].mapTo(self,self.botones_seccion["decision"].rect().center())
        viajar_prueba(self,self.rect().center(),objetivo,llegar)

    def _ir_confirmacion(self):
        valido,motivo=self._elegibilidad(self._accion)
        if not valido:
            self.abrir("decision")
            self.mostrar_mensaje(motivo)
            return
        self._actualizar_confirmacion()
        self.abrir("confirmacion")

    def _actualizar_confirmacion(self):
        if not self._accion:
            return
        titulo,detalle,icono=self._COPIAS.get(self._accion,(self._accion,"","redactar"))
        self.confirmacion_icono.setPixmap(imagen_novela(f"ui/{icono}.png").scaled(120,120,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
        self.confirmacion_titulo.setText(titulo)
        self.confirmacion_detalle.setText(detalle+("\nPrueba: "+self._prueba["titulo"] if self._prueba else ""))

    def _confirmar(self):
        valido,motivo=self._elegibilidad(self._accion)
        if not valido:
            self.mostrar_mensaje(motivo)
            return
        if not self._activo() or not self._mi_turno():
            self.mostrar_mensaje("Espera la respuesta de tu compañero.")
            return
        self._enviar("decidir",accion=self._accion,titular=(self.vista.get("caso") or {}).get("titulo",""),
                     certeza="confirmada" if self._prueba else "pendiente",
                     evidencia_id=self._prueba["id"] if self._prueba else None)

    def _examinar(self):
        if self.examinar.isEnabled():
            self._enviar("examinar",medio=self._medio().get("tipo","captura"),valor=self.slider.value())

    def _siguiente(self):
        indice=self.paginas.currentIndex()
        if indice==self.secciones["fuentes"]:
            self.abrir("material")
        elif indice==self.secciones["material"]:
            self._examinar() if self.examinar.isEnabled() else self.abrir("decision")
        elif indice==self.secciones["pista"]:
            self._usar_hallazgo()
        elif indice==self.secciones["decision"]:
            self._ir_confirmacion()

    def _refrescar_paso(self):
        indice=self.paginas.currentIndex()
        etapa=3 if indice==self.secciones["confirmacion"] else 2 if indice==self.secciones["decision"] else 1
        for clave,boton in self.botones_seccion.items():
            boton.setChecked(clave==("fuentes","decision","confirmacion")[etapa-1])
        valido,motivo=self._elegibilidad(self._accion)
        self.motivo.setText(motivo if self._accion else "")
        self.botones_seccion["confirmacion"].setEnabled(bool(self._accion and valido))
        self.confirmar.setVisible(etapa==3)
        self.confirmar.setEnabled(self._activo() and self._mi_turno() and valido)
        self.siguiente_paso.setVisible(etapa!=3)
        self.siguiente_paso.setEnabled(etapa!=2 or bool(self._accion and valido))
        if indice==self.secciones["fuentes"]:
            texto="Elige un lugar. Cada visita usa una investigación."
            boton="Examinar el mensaje"
        elif indice==self.secciones["material"]:
            texto=self._medio().get("consigna","Señala el detalle que falta.")
            boton="Guardar hallazgo · usa 1" if self.examinar.isEnabled() else "Elegir una respuesta"
        elif indice==self.secciones["pista"]:
            texto="Lee la fuente y elige cómo responder."
            boton="Elegir una respuesta"
        elif indice==self.secciones["decision"]:
            texto="Elige cómo responder." if self._mi_turno() else "Prepara tu respuesta mientras termina el compañero."
            boton="Continuar"
        else:
            texto="¿Quieres responder así?"
            boton=""
        self.indicacion.setText(texto)
        self.siguiente_paso.setText(boton)
        if self.vista.get("fase")=="pausa":
            self.indicacion.setText("Partida en pausa. Reconecta a tu compañero.")
            self.confirmar.setEnabled(False)
            self.siguiente_paso.setEnabled(False)

    def _enviar(self,tipo,**campos):
        if self._actualizando:
            return
        self._pendiente=tipo
        comando={"tipo":tipo,**campos}
        self.comando.emit(comando)
        if self.callback is not None and self.callback(comando) is False:
            self._pendiente=None

    def abrir(self,seccion="fuentes"):
        aliases={"prueba":"material","pistas":"fuentes","editor":"decision","contactos":"decision","audiencia":"decision","entrevista":"fuentes"}
        seccion=aliases.get(seccion,seccion)
        if seccion not in self.secciones:
            seccion="fuentes"
        self._cerrado=False
        self.paginas.setCurrentIndex(self.secciones[seccion])
        self._refrescar_paso()
        self._colocar()
        self.show()
        self.raise_()
        self.salir.setFocus(Qt.FocusReason.OtherFocusReason)

    def cerrar(self):
        if self._cerrado:
            return
        self._cerrado=True
        if self.parent() is not None:
            self.parent().removeEventFilter(self)
        self.hide()
        self.cerrado.emit()
        self.deleteLater()

    def mostrar_mensaje(self,texto):
        self.indicacion.setText(str(texto))

    def _colocar(self):
        margen=20 if self.width()<1200 else 40
        self.marco.setGeometry(margen,18,max(1,self.width()-margen*2),max(1,self.height()-36))

    def eventFilter(self,objeto,event):
        if objeto is self.parent() and event.type()==QEvent.Type.Resize:
            self.setGeometry(objeto.rect())
        return False

    def resizeEvent(self,event):
        self._colocar()
        super().resizeEvent(event)

    def keyPressEvent(self,event):
        if event.key()==Qt.Key.Key_Escape:
            self.cerrar()
            event.accept()
        else:
            super().keyPressEvent(event)

    def event(self,event):
        if event.type()==QEvent.Type.ShortcutOverride and event.key()==Qt.Key.Key_Escape and self.isVisible():
            event.accept()
            return True
        return super().event(event)

    def closeEvent(self,event):
        self.cerrar()
        event.accept()

    def paintEvent(self,event):
        p=QPainter(self)
        p.fillRect(self.rect(),QColor(4,12,22,170))

    def _medio(self):
        return (self.vista.get("caso") or {}).get("medio") or {}

    def _ruta_prueba(self, original):
        medio = self._medio()
        clave = "imagen_completa" if original else "imagen_recortada"
        if medio.get(clave):
            return medio[clave]
        id = (self.vista.get("caso") or {}).get("id", "")
        sufijo = "original" if original else "recorte"
        nueva = f"assets/novela/props/{id}_{sufijo}.png"
        return nueva if (RAIZ / nueva).is_file() else f"assets/feria/pruebas/{id}_{sufijo}.png"

    def _fragmento_audio(self, valor):
        medio = self._medio()
        recuperado = medio.get("revelado") or medio.get("recuperado")
        texto = medio.get("texto_completo") if recuperado else medio.get("texto_inicial")
        if medio.get("tipo") == "audio" and (medio.get("inspeccionable") or recuperado):
            fragmento = next((f for f in medio.get("fragmentos", [])
                              if f.get("inicio", 0) <= valor < f.get("fin", 100)
                              or valor == 100 and f.get("fin") == 100), None)
            if fragmento:
                texto = fragmento.get("texto", texto)
        self.fragmento.setText(texto or "Busca el detalle que quedó fuera de esta versión.")
        self.fragmento.setToolTip(self.fragmento.text())
        self._actualizar_audio_original()

    def _audio_original(self):
        """Solo acepta una toma completa que ya exista en el doblaje original."""
        gestor = getattr(self.window(), "audio", None)
        if gestor is None or getattr(gestor, "_sintetizador", None) is not None:
            return None
        catalogo = getattr(gestor, "_manifest_voces", {}).get("clips", {})
        medio = self._medio()
        recuperado = bool(medio.get("revelado") or medio.get("recuperado"))
        activa = (self.vista.get("fase") in ("investigacion", "decision")
                  and self.vista.get("mi_id") not in self.vista.get("decididos", [])
                  and self.vista.get("acciones_restantes", 0) > 0)
        puede_explorar = bool(medio.get("inspeccionable", activa) or recuperado)
        texto = medio.get("voz_texto") if puede_explorar else None
        texto = normalizar_texto(texto or self.fragmento.text())
        nombre = medio.get("voz_hablante") if puede_explorar else None
        nombres = [nombre] if nombre in PERFILES else list(PERFILES)
        for hablante in nombres:
            entrada = catalogo.get(clave_clip(hablante, texto))
            if entrada and ruta_clip(entrada) is not None:
                return texto, hablante
        return None

    def _actualizar_audio_original(self):
        es_audio = self._medio().get("tipo") == "audio"
        self.disponibilidad_audio.setVisible(es_audio)
        if not es_audio:
            return
        grabacion = self._audio_original()
        gestor = getattr(self.window(), "audio", None)
        if grabacion is None:
            self.escuchar.setText("Solo transcripción")
            self.escuchar.setEnabled(False)
            self.disponibilidad_audio.setText("Esta pieza se presenta mediante su transcripción: no incluye una grabación original coincidente.")
        elif (getattr(gestor, "silenciado", False) or not getattr(gestor, "voces_activadas", True)
              or not getattr(gestor, "voces_disponibles", False) or gestor.volumen("voces") <= 0):
            self.escuchar.setText("Voz desactivada")
            self.escuchar.setEnabled(False)
            self.disponibilidad_audio.setText("Existe una grabación original. Activa el sonido y las voces en Configuración para escucharla.")
        else:
            self.escuchar.setText("Escuchar voz original")
            self.escuchar.setEnabled(True)
            self.disponibilidad_audio.setText("Grabación original: " + grabacion[1].capitalize() + ". También puedes leer la transcripción.")

    def _escuchar(self):
        gestor = getattr(self.window(), "audio", None)
        grabacion = self._audio_original()
        if grabacion is not None and gestor is not None and self.escuchar.isEnabled():
            if not gestor.narrar(*grabacion):
                self.mostrar_mensaje("Esta pista conserva su transcripción. Ese fragmento no tiene una grabación neuronal local.")
                self.escuchar.setEnabled(False)
        else:
            self._actualizar_audio_original()

    def _ampliar(self, marcado):
        self.area_prueba.setWidgetResizable(not marcado)
        if marcado:
            self.comparador.setMaximumHeight(16777215)
            self.comparador.setFixedSize(1400, 900)
        else:
            self.comparador.setMinimumSize(360, 195)
            self.comparador.setMaximumSize(16777215, 380)
        self.ampliar.setText("Volver al encuadre" if marcado else "Leer en detalle")

