from PyQt6.QtCore import QObject, QUrl, QVariantAnimation, pyqtSignal
from recursos import RAIZ


class GestorAudio(QObject):
    aviso = pyqtSignal(str)
    voz_iniciada = pyqtSignal(str)
    voz_finalizada = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.volumenes = {"general": 0.65, "musica": 0.3, "efectos": 0.6, "ambiente": 0.2, "voces": 1.0}
        self.silenciado = False
        self.disponible = False
        self.efectos = {}
        self.pistas = {}
        self.fundidos = {}
        self.objetivos = {}
        self.voces_activadas = True
        self.voces_disponibles = False
        self.catalogo_voces = []
        self.perfiles_voces = {}
        self.motor_voz = ""
        self.error_voces = ""
        self.hablando = False
        self.hablante_actual = ""
        self.ultimo_texto_voz = ""
        self._sintetizador = None
        self._voces = []
        self._inicializar_voces()
        try:
            from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
        except ImportError:
            return
        for categoria in ("musica", "ambiente"):
            reproductor = QMediaPlayer(self)
            salida = QAudioOutput(self)
            reproductor.setAudioOutput(salida)
            reproductor.setLoops(QMediaPlayer.Loops.Infinite)
            self.pistas[categoria] = (reproductor, salida)
        self.disponible = True
        self.actualizar_volumen()

    def volumen(self, categoria):
        if self.silenciado:
            return 0.0
        atenuacion = 0.40 if self.hablando and categoria in ("musica", "ambiente") else 1.0
        return self.volumenes["general"] * self.volumenes[categoria] * atenuacion

    def _inicializar_voces(self):
        """Usa voces españolas del sistema, sin red ni dependencias adicionales.

        WinRT permite usar las voces actuales de Windows; SAPI queda como
        alternativa. Nunca se acepta el motor ficticio de pruebas de Qt.
        """
        try:
            from PyQt6.QtTextToSpeech import QTextToSpeech
        except ImportError:
            self.error_voces = "Este equipo no dispone del módulo de lectura de voz."
            return
        motores = [m for m in QTextToSpeech.availableEngines() if m != "mock"]
        motores.sort(key=lambda nombre: (nombre not in ("winrt", "sapi"), nombre != "winrt", nombre))
        for motor in motores:
            sintetizador = QTextToSpeech(motor, self)
            if sintetizador.state() == QTextToSpeech.State.Error:
                self.error_voces = sintetizador.errorString()
                sintetizador.deleteLater()
                continue
            voces = []
            # availableVoices() solo incluye el idioma/país seleccionado.
            for idioma in sintetizador.availableLocales():
                if idioma.name().split("_")[0] != "es":
                    continue
                sintetizador.setLocale(idioma)
                for voz in sintetizador.availableVoices():
                    if not any(v.name() == voz.name() and v.locale() == voz.locale() for v in voces):
                        voces.append(voz)
            if not voces:
                sintetizador.deleteLater()
                continue
            orden_idiomas = {"es_CO": 0, "es_MX": 1, "es_ES": 2}
            voces.sort(key=lambda v: (orden_idiomas.get(v.locale().name(), 3), v.name()))
            self._sintetizador = sintetizador
            self._voces = voces
            self.motor_voz = motor
            self.voces_disponibles = True
            self.error_voces = ""
            self.catalogo_voces = [{"nombre": v.name(), "idioma": v.locale().name(),
                                    "genero": v.gender().name} for v in voces]
            self._asignar_perfiles()
            sintetizador.stateChanged.connect(self._estado_voz)
            sintetizador.errorOccurred.connect(self._error_voz)
            sintetizador.setVolume(self.volumen("voces"))
            return
        self.error_voces = self.error_voces or "No hay voces españolas instaladas en este equipo."

    def _asignar_perfiles(self):
        from PyQt6.QtTextToSpeech import QVoice
        hombres = [v for v in self._voces if v.gender() == QVoice.Gender.Male]
        mujeres = [v for v in self._voces if v.gender() == QVoice.Gender.Female]
        ciudadano = hombres[0] if hombres else self._voces[0]
        periodista = next((v for v in mujeres if "laura" in v.name().lower()),
                           mujeres[0] if mujeres else self._voces[-1])
        narrador = next((v for v in self._voces if v != ciudadano and v != periodista), ciudadano)
        self.perfiles_voces = {
            "CIUDADANO": {"voz": ciudadano, "ritmo": -0.07, "tono": 0.04},
            "PERIODISTA": {"voz": periodista, "ritmo": -0.10, "tono": 0.03},
            "NARRADOR": {"voz": narrador, "ritmo": -0.16, "tono": -0.13},
        }

    def descripcion_voces(self):
        if not self.voces_disponibles:
            return self.error_voces
        return "Voces del sistema en español · " + ", ".join(v["nombre"] for v in self.catalogo_voces)

    def estado_voces(self):
        """Diagnóstico serializable para configuración y comprobaciones."""
        return {
            "disponibles": self.voces_disponibles,
            "activadas": self.voces_activadas,
            "motor": self.motor_voz,
            "error": self.error_voces,
            "hablando": self.hablando,
            "catalogo": list(self.catalogo_voces),
            "perfiles": {nombre: {"voz": p["voz"].name(), "genero": p["voz"].gender().name,
                                   "ritmo": p["ritmo"], "tono": p["tono"]}
                         for nombre, p in self.perfiles_voces.items()},
        }

    def configurar_voces(self, activadas):
        self.voces_activadas = bool(activadas)
        if not self.voces_activadas:
            self.detener_voz()
        self.actualizar_volumen()

    def narrar(self, texto, hablante="NARRADOR"):
        """Reemplaza inmediatamente la lectura anterior sin bloquear la interfaz."""
        self.detener_voz()
        texto = " ".join(str(texto or "").split())
        if not texto or not self.voces_activadas or not self.voces_disponibles or self.volumen("voces") <= 0:
            return False
        nombre = str(hablante or "NARRADOR").strip().upper()
        perfil = self.perfiles_voces.get(nombre)
        if perfil is None:
            # Los nuevos personajes reciben un perfil estable sin cambiar diálogos.
            perfil = dict(self.perfiles_voces["NARRADOR"])
            perfil["voz"] = self._voces[sum(map(ord, nombre)) % len(self._voces)]
            perfil["tono"] = ((sum(map(ord, nombre)) % 9) - 4) / 25
        sintetizador = self._sintetizador
        sintetizador.setVoice(perfil["voz"])
        sintetizador.setRate(perfil["ritmo"])
        sintetizador.setPitch(perfil["tono"])
        sintetizador.setVolume(self.volumen("voces"))
        self.hablante_actual = nombre
        self.ultimo_texto_voz = texto
        # say() sintetiza y reproduce de forma asíncrona; nunca encola diálogos.
        sintetizador.say(texto)
        return sintetizador.state().name != "Error"

    def detener_voz(self):
        if self._sintetizador is not None:
            from PyQt6.QtTextToSpeech import QTextToSpeech
            self._sintetizador.stop(QTextToSpeech.BoundaryHint.Immediate)
        self.hablante_actual = ""
        self.ultimo_texto_voz = ""
        if self.hablando:
            self.hablando = False
            self.actualizar_volumen()
            self.voz_finalizada.emit()

    def _estado_voz(self, estado):
        hablando = estado.name in ("Speaking", "Synthesizing")
        if hablando == self.hablando:
            return
        self.hablando = hablando
        self.actualizar_volumen()
        if hablando:
            self.voz_iniciada.emit(self.hablante_actual)
        else:
            self.voz_finalizada.emit()

    def _error_voz(self, razon, mensaje):
        self.error_voces = str(mensaje)
        self.aviso.emit("No se pudo reproducir la voz: " + self.error_voces)

    def configurar(self, categoria, valor):
        if categoria not in self.volumenes:
            raise ValueError("Categoría de audio desconocida")
        self.volumenes[categoria] = max(0.0, min(1.0, float(valor)))
        if categoria in ("general", "voces") and self.volumen("voces") <= 0:
            self.detener_voz()
        self.actualizar_volumen()

    def silenciar(self, valor=True):
        self.silenciado = bool(valor)
        if self.silenciado:
            self.detener_voz()
        self.actualizar_volumen()

    def actualizar_volumen(self):
        for categoria, (_, salida) in self.pistas.items():
            salida.setVolume(self.volumen(categoria))
        for efecto in self.efectos.values():
            efecto.setVolume(self.volumen("efectos"))
        if self._sintetizador is not None:
            self._sintetizador.setVolume(self.volumen("voces") if self.voces_activadas else 0.0)

    def reproducir_efecto(self, nombre):
        self.aviso.emit(nombre.replace("_", " "))
        ruta = RAIZ / "assets/audio/efectos" / (nombre + ".wav")
        if not self.disponible or not ruta.is_file():
            return False
        if nombre not in self.efectos:
            from PyQt6.QtMultimedia import QSoundEffect
            efecto = QSoundEffect(self)
            efecto.setSource(QUrl.fromLocalFile(str(ruta)))
            self.efectos[nombre] = efecto
        self.efectos[nombre].setVolume(self.volumen("efectos"))
        self.efectos[nombre].play()
        return True

    def cambiar_pista(self, nombre, categoria="musica"):
        if categoria not in self.pistas:
            return False
        ruta = RAIZ / "assets/audio" / ("musica" if categoria == "musica" else "ambientes") / (nombre + ".wav")
        reproductor, salida = self.pistas[categoria]
        fuente = QUrl.fromLocalFile(str(ruta))
        if self.objetivos.get(categoria) == fuente:
            return ruta.is_file()
        if categoria in self.fundidos:
            anterior = self.fundidos.pop(categoria)
            anterior.stop()
            anterior.deleteLater()
        self.objetivos[categoria] = fuente
        if not ruta.is_file():
            reproductor.stop()
            return False
        def comenzar():
            if self.objetivos.get(categoria) != fuente:
                return
            reproductor.setSource(fuente)
            reproductor.play()
            entrada = QVariantAnimation(self)
            entrada.setDuration(600)
            entrada.setStartValue(0.0)
            entrada.setEndValue(1.0)
            entrada.valueChanged.connect(lambda valor: salida.setVolume(float(valor) * self.volumen(categoria)))
            def terminar():
                if self.fundidos.get(categoria) is entrada:
                    self.fundidos.pop(categoria, None)
                entrada.deleteLater()
            entrada.finished.connect(terminar)
            self.fundidos[categoria] = entrada
            entrada.start()
        salida_fade = QVariantAnimation(self)
        salida_fade.setDuration(350)
        salida_fade.setStartValue(salida.volume())
        salida_fade.setEndValue(0.0)
        salida_fade.valueChanged.connect(lambda valor: salida.setVolume(min(float(valor), self.volumen(categoria))))
        salida_fade.finished.connect(comenzar)
        salida_fade.finished.connect(salida_fade.deleteLater)
        self.fundidos[categoria] = salida_fade
        salida_fade.start()
        return True

    def detener(self):
        self.detener_voz()
        self.objetivos.clear()
        for animacion in self.fundidos.values():
            animacion.stop()
        for reproductor, _ in self.pistas.values():
            reproductor.stop()
        for efecto in self.efectos.values():
            efecto.stop()
        self.fundidos.clear()
