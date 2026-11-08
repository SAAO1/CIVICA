"""Dos invitaciones breves sobre la apertura; la historia y sus voces continúan."""
from PyQt6.QtCore import QEvent, QObject, QPropertyAnimation, QTimer
from PyQt6.QtWidgets import (QApplication, QGraphicsOpacityEffect, QLineEdit,
                            QPlainTextEdit, QTextEdit)

from interfaz.novela.componentes import BotonNovela


class EngancheInicial(QObject):
    def __init__(self, ventana):
        super().__init__(ventana)
        self.ventana = ventana
        self.botones = {}
        self._pulsos = {}
        self._atajos = {}
        self._vigilancia = QTimer(self)
        self._vigilancia.setInterval(250)
        self._vigilancia.timeout.connect(self.actualizar)
        for indice, texto, atajo, accion in (
            (ventana.ESCENA_NARRACION_2, "Abrir el mensaje · M", "M", self._abrir_mensaje),
            (ventana.ESCENA_NARRACION_3, "Examinar esta prueba · P", "P", self._examinar),
        ):
            escena = ventana.escenas.widget(indice)
            boton = BotonNovela(texto, escena)
            boton.setAccessibleName(texto.replace(" · ", "; tecla "))
            boton.setToolTip("Abrir no gasta investigaciones. También puedes seguir leyendo con Espacio."
                             if indice == ventana.ESCENA_NARRACION_3 else
                             "Abre la notificación del barrio. También puedes seguir leyendo con Espacio.")
            boton.setShortcut(atajo)
            boton.clicked.connect(accion)
            boton.hide()
            efecto = QGraphicsOpacityEffect(boton)
            boton.setGraphicsEffect(efecto)
            pulso = QPropertyAnimation(efecto, b"opacity", self)
            pulso.setDuration(1600)
            pulso.setStartValue(.86)
            pulso.setKeyValueAt(.5, 1.0)
            pulso.setEndValue(.86)
            pulso.setLoopCount(-1)
            self.botones[indice] = boton
            self._atajos[indice] = atajo
            self._pulsos[indice] = pulso
            escena.installEventFilter(self)
            # La preparación asíncrona vuelve a elevar estas capas después
            # de mostrar la escena. La invitación debe seguir siendo pulsable.
            for nombre in ("fondo_label", "cine_narrativo", "publicacion_telefono"):
                capa = getattr(escena, nombre, None)
                if capa is not None:
                    capa.installEventFilter(self)
        ventana.installEventFilter(self)
        ventana.escenas.currentChanged.connect(self.actualizar)
        QApplication.instance().focusChanged.connect(self.actualizar)
        QTimer.singleShot(0, self.actualizar)

    def _activa(self):
        vista = self.ventana.vista_novela
        return (vista.get("caso", {}).get("numero") == 1
                and vista.get("fase") in ("investigacion", "decision")
                and vista.get("mi_id") not in vista.get("decididos", [])
                and self.ventana.overlay_investigacion is None
                and getattr(self.ventana, "cuaderno", None) is None
                and QApplication.activeModalWidget() is None
                and QApplication.activeWindow() in (None, self.ventana)
                and not isinstance(QApplication.focusWidget(), (QLineEdit, QPlainTextEdit, QTextEdit)))

    def actualizar(self, *_):
        ventana = self.ventana
        activa = self._activa() and ventana.isVisible()
        alguno = False
        for indice, boton in self.botones.items():
            escena = ventana.escenas.widget(indice)
            mostrar = activa and ventana.escenas.currentIndex() == indice
            alguno = alguno or mostrar
            ancho = min(326, max(250, escena.width()-32))
            alto = 66
            limite = getattr(escena, "franja_inferior", escena).y()-alto-16
            y = max(84, min(round(escena.height()*.43), limite))
            x = min(escena.width()-ancho-20, round(escena.width()*.62))
            boton.setGeometry(max(16, x), y, ancho, alto)
            boton.setVisible(mostrar)
            boton.setEnabled(mostrar)
            boton.setShortcut(self._atajos[indice] if mostrar else "")
            pulso = self._pulsos[indice]
            if mostrar:
                boton.raise_()
            if mostrar and not ventana.reducir_movimiento:
                if pulso.state() != QPropertyAnimation.State.Running:
                    pulso.start()
            else:
                pulso.stop()
                boton.graphicsEffect().setOpacity(1.0)
        if alguno:
            self._vigilancia.start()
        else:
            self._vigilancia.stop()

    def _abrir_mensaje(self):
        v = self.ventana
        if not self._activa() or v.escenas.currentIndex() != v.ESCENA_NARRACION_2:
            return
        v.audio.reproducir_efecto("pulido_paso")
        v.mostrar_escena(v.ESCENA_NARRACION_3)

    def _examinar(self):
        v = self.ventana
        if not self._activa() or v.escenas.currentIndex() != v.ESCENA_NARRACION_3:
            return
        v.audio.reproducir_efecto("pulido_transicion")
        v.abrir_fuentes("material")

    def eventFilter(self, objeto, evento):
        if evento.type() in (QEvent.Type.Resize, QEvent.Type.Show, QEvent.Type.Hide,
                             QEvent.Type.ZOrderChange, QEvent.Type.WindowActivate):
            QTimer.singleShot(0, self.actualizar)
        return False


def instalar_enganche(ventana):
    """Conserva el controlador y evita instalar invitaciones duplicadas."""
    if not hasattr(ventana, "enganche_inicial"):
        ventana.enganche_inicial = EngancheInicial(ventana)
    return ventana.enganche_inicial
