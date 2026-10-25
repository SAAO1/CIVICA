from PyQt6.QtCore import QObject, QTimer, QUrl, QVariantAnimation, pyqtSignal
from recursos import RAIZ
from audio.catalogo_voces import (PERFILES, cargar_manifest, clave_clip,
                                 frases_texto, normalizar_texto, partes_resultado,
                                 ruta_clip, texto_grupo)


class GestorAudio(QObject):
    aviso = pyqtSignal(str)
    voz_iniciada = pyqtSignal(str)
    voz_finalizada = pyqtSignal()
    nivel_voz = pyqtSignal(float)
    segmento_iniciado = pyqtSignal(str)
    segmento_finalizado = pyqtSignal(str)
    secuencia_finalizada = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.volumenes = {"general": 0.75, "musica": 0.16, "efectos": 0.40, "ambiente": 0.10, "voces": 1.0}
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
        self._manifest_voces = {}
        self._reproductor_voz = None
        self._salida_voz = None
        self._clip_actual = {}
        self._cola_voces = []
        self._generacion_voz = 0
        self._segmento_actual = ""
        self._segmento_empezado = False
        self._clip_terminado = True
        self._secuencia_activa = False
        self._faltantes_avisados = set()
        self._temporizador_labios = QTimer(self)
        self._temporizador_labios.setInterval(50)
        self._temporizador_labios.timeout.connect(self._actualizar_labios)
        self._inicializar_voces()
        try:
            from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
        except ImportError:
            self.voces_disponibles = False
            self.error_voces = "Qt Multimedia no está disponible para reproducir el doblaje."
            return
        self._reproductor_voz = QMediaPlayer(self)
        self._salida_voz = QAudioOutput(self)
        self._reproductor_voz.setAudioOutput(self._salida_voz)
        self._reproductor_voz.playbackStateChanged.connect(self._estado_reproduccion_voz)
        self._reproductor_voz.mediaStatusChanged.connect(self._estado_clip_voz)
        self._reproductor_voz.errorOccurred.connect(self._error_clip_voz)
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
        # Mezcla centrada en el diálogo, incluso con preferencias antiguas
        # que dejaban el ambiente alto. Los efectos tampoco tapan una frase.
        atenuacion = ({"musica": 0.12, "ambiente": 0.08, "efectos": 0.28}.get(categoria, 1.0)
                      if self.hablando else 1.0)
        return self.volumenes["general"] * self.volumenes[categoria] * atenuacion

    def _inicializar_voces(self):
        """Carga el doblaje neuronal incluido; no contacta servicios al jugar."""
        self._manifest_voces = cargar_manifest()
        clips = self._manifest_voces.get("clips", {})
        self.voces_disponibles = any(ruta_clip(clip) for clip in clips.values())
        self.motor_voz = "neural-offline" if self.voces_disponibles else ""
        self.perfiles_voces = {nombre: dict(perfil) for nombre, perfil in PERFILES.items()}
        self.catalogo_voces = [{"nombre": p["nombre"], "idioma": p["idioma"],
                                "genero": p["genero"], "identidad": p["voz"]}
                               for p in PERFILES.values()]
        self.error_voces = "" if self.voces_disponibles else "No se encuentra el paquete de doblaje neuronal."

    def descripcion_voces(self):
        if not self.voces_disponibles:
            return self.error_voces
        cantidad = len(self._manifest_voces.get("clips", {}))
        return (f"Doblaje neuronal en español · {cantidad} clips locales · "
                + ", ".join(v["nombre"] for v in self.catalogo_voces)
                + ". Voces sintéticas; reproducción sin conexión.")

    def estado_voces(self):
        """Diagnóstico serializable para configuración y comprobaciones."""
        return {
            "disponibles": self.voces_disponibles,
            "activadas": self.voces_activadas,
            "motor": self.motor_voz,
            "error": self.error_voces,
            "hablando": self.hablando,
            "catalogo": list(self.catalogo_voces),
            "clips_locales": len(self._manifest_voces.get("clips", {})),
            "conexion_al_jugar": False,
            "dialogos_sin_grabacion": len(self._faltantes_avisados),
            "perfiles": {nombre: {"voz": p["voz"] if isinstance(p["voz"], str) else p["voz"].name(),
                                   "genero": p.get("genero", ""),
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
        texto = normalizar_texto(texto)
        if not texto or not self.voces_activadas or not self.voces_disponibles or self.volumen("voces") <= 0:
            return False
        nombre = str(hablante or "NARRADOR").strip().upper()
        # La interfaz anterior puede inyectar un sintetizador para probar
        # cancelación y mezcla. En ejecución normal sólo hay clips neuronales.
        if self._sintetizador is None:
            clips = self._buscar_clips_voz(texto, nombre)
            if not clips or self._reproductor_voz is None:
                self.error_voces = "Este diálogo todavía no tiene un clip neuronal local."
                clave = clave_clip(nombre, texto)
                if clave not in self._faltantes_avisados:
                    self._faltantes_avisados.add(clave)
                    self.aviso.emit(self.error_voces + " Puedes continuar leyendo los subtítulos.")
                return False
            self.error_voces = ""
            self.hablante_actual = nombre
            self.ultimo_texto_voz = texto
            self._cola_voces = list(clips)
            self._reproducir_siguiente_clip()
            return True
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

    def _buscar_clips_voz(self, texto, nombre):
        catalogo = self._manifest_voces.get("clips", {})
        completo = catalogo.get(clave_clip(nombre, texto))
        if completo and ruta_clip(completo):
            return [completo]
        compartido = catalogo.get(clave_clip(nombre, texto_grupo(texto)))
        if compartido and ruta_clip(compartido):
            return [compartido]
        partes = partes_resultado(texto)
        bloques = [catalogo.get(clave_clip(nombre, parte)) for parte in partes]
        if bloques and all(c and ruta_clip(c) for c in bloques):
            return bloques
        # Las frases ya grabadas se pueden recombinar para variantes de datos.
        frases = frases_texto(texto)
        clips = [catalogo.get(clave_clip(nombre, frase)) for frase in frases]
        return clips if clips and all(c and ruta_clip(c) for c in clips) else []

    def narrar_secuencia(self, segmentos, hablante="NARRADOR"):
        """Reproduce cifras locales y notifica su comienzo audible real.

        Cada segmento debe tener una toma completa: si falta una, no se inicia
        una secuencia parcial. La interfaz puede entonces usar su animación
        temporizada. Esta API nunca llama a un sintetizador del sistema.
        """
        self.detener_voz()
        if (not self.voces_activadas or not self.voces_disponibles
                or self.volumen("voces") <= 0 or self._reproductor_voz is None):
            return False
        nombre = str(hablante or "NARRADOR").strip().upper()
        clips, textos = [], []
        catalogo = self._manifest_voces.get("clips", {})
        try:
            for segmento in segmentos:
                if isinstance(segmento, dict):
                    clave, texto = segmento.get("clave"), segmento.get("texto")
                else:
                    clave, texto = segmento
                if not isinstance(clave, str) or not clave.strip() or not isinstance(texto, str):
                    return False
                texto = normalizar_texto(texto)
                clip = catalogo.get(clave_clip(nombre, texto))
                if not texto or not clip or ruta_clip(clip) is None:
                    return False
                clips.append(dict(clip, _segmento_clave=clave))
                textos.append(texto)
        except (TypeError, ValueError):
            return False
        if not clips:
            return False
        self.error_voces = ""
        self.hablante_actual = nombre
        self.ultimo_texto_voz = " ".join(textos)
        self._secuencia_activa = True
        self._cola_voces = clips
        self._reproducir_siguiente_clip()
        return True

    def _finalizar_segmento(self):
        clave, empezado = self._segmento_actual, self._segmento_empezado
        self._segmento_actual = ""
        self._segmento_empezado = False
        if clave and empezado:
            self.segmento_finalizado.emit(clave)

    def _finalizar_secuencia(self, completada):
        if self._secuencia_activa:
            self._secuencia_activa = False
            self.secuencia_finalizada.emit(bool(completada))

    def _reproducir_siguiente_clip(self):
        if not self._cola_voces or not self.voces_activadas or self.volumen("voces") <= 0:
            self._cambiar_estado_hablando(False)
            return
        self._clip_actual = self._cola_voces.pop(0)
        self._segmento_actual = self._clip_actual.get("_segmento_clave", "")
        self._segmento_empezado = False
        self._clip_terminado = False
        ruta = ruta_clip(self._clip_actual)
        if ruta is None:
            self.detener_voz()
            return
        self._salida_voz.setVolume(self.volumen("voces"))
        self._reproductor_voz.setSource(QUrl.fromLocalFile(str(ruta)))
        self._reproductor_voz.play()

    def _estado_reproduccion_voz(self, estado):
        if estado.name == "PlayingState":
            if self._clip_terminado or not self._clip_actual:
                return
            self._cambiar_estado_hablando(True)
            if self._segmento_actual and not self._segmento_empezado:
                self._segmento_empezado = True
                self.segmento_iniciado.emit(self._segmento_actual)
        elif estado.name == "PausedState":
            self._cambiar_estado_hablando(False)

    def _estado_clip_voz(self, estado):
        if estado.name == "EndOfMedia":
            if self._clip_terminado:
                return
            self._clip_terminado = True
            self._finalizar_segmento()
            if self._cola_voces:
                generacion = self._generacion_voz
                QTimer.singleShot(0, lambda: self._reproducir_siguiente_clip()
                                  if generacion == self._generacion_voz else None)
            else:
                self._cambiar_estado_hablando(False)
                self._finalizar_secuencia(True)

    def _error_clip_voz(self, razon, mensaje):
        self.detener_voz()
        self._error_voz(razon, mensaje)

    def _actualizar_labios(self):
        if not self.hablando or self._reproductor_voz is None:
            self.nivel_voz.emit(0.0)
            return
        envolvente = self._clip_actual.get("envolvente", [])
        paso = max(1, self._clip_actual.get("paso_envolvente_ms", 50))
        indice = self._reproductor_voz.position() // paso
        nivel = envolvente[indice] if 0 <= indice < len(envolvente) else 0.0
        self.nivel_voz.emit(float(nivel))

    def _cambiar_estado_hablando(self, hablando):
        if hablando == self.hablando:
            return
        self.hablando = hablando
        self.actualizar_volumen()
        if hablando:
            self._temporizador_labios.start()
            self.voz_iniciada.emit(self.hablante_actual)
        else:
            self._temporizador_labios.stop()
            self.nivel_voz.emit(0.0)
            self.voz_finalizada.emit()

    def detener_voz(self):
        self._generacion_voz += 1
        self._cola_voces.clear()
        self._clip_terminado = True
        self._finalizar_segmento()
        self._finalizar_secuencia(False)
        self._clip_actual = {}
        if self._reproductor_voz is not None:
            self._reproductor_voz.stop()
        self._temporizador_labios.stop()
        self.nivel_voz.emit(0.0)
        if self._sintetizador is not None:
            from PyQt6.QtTextToSpeech import QTextToSpeech
            self._sintetizador.stop(QTextToSpeech.BoundaryHint.Immediate)
        self.hablante_actual = ""
        self.ultimo_texto_voz = ""
        self._cambiar_estado_hablando(False)

    def _estado_voz(self, estado):
        hablando = estado.name in ("Speaking", "Synthesizing")
        self._cambiar_estado_hablando(hablando)

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
        if self._salida_voz is not None:
            self._salida_voz.setVolume(self.volumen("voces") if self.voces_activadas else 0.0)

    def reproducir_efecto(self, nombre):
        alias = {"clic": "clic_real", "notificacion": "notificacion_suave",
                 "compartir": "notificacion_suave", "verificar": "hallazgo",
                 "ignorar": "papeles", "reportar": "clic_real",
                 "conversar": "taza", "convocar": "llamada_puerta",
                 "contrastar": "hallazgo", "entrevistar": "lapiz",
                 "desmentir": "papeles", "reservar": "pagina",
                 "resultado": "pagina", "recompensa": "hallazgo",
                 "nodo": "clic_real"}.get(nombre, nombre)
        expansion = RAIZ / "assets/audio/expansion/efectos" / (alias + ".wav")
        ruta = expansion if expansion.is_file() else RAIZ / "assets/audio/efectos" / (nombre + ".wav")
        nueva = RAIZ / "assets/audio/siete_actos" / (alias + ".wav")
        if nueva.is_file():
            ruta = nueva
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
        subcarpeta = "musica" if categoria == "musica" else "ambientes"
        expansion = RAIZ / "assets/audio/expansion" / subcarpeta / (nombre + ".wav")
        ruta = expansion if expansion.is_file() else RAIZ / "assets/audio" / subcarpeta / (nombre + ".wav")
        nueva = RAIZ / "assets/audio/siete_actos" / (nombre + ".wav")
        if categoria == "ambiente" and nueva.is_file():
            ruta = nueva
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
        """Cierra los transportes antes de destruir la ventana y sus objetos.

        ``stop`` conserva la fuente cargada. Vaciarla aquí libera sus lectores
        y decodificadores; la cancelación habitual de una línea mantiene su
        fuente y la siguiente reproducción puede reutilizar las salidas.
        """
        self.detener_voz()
        self.objetivos.clear()
        for animacion in self.fundidos.values():
            animacion.stop()
        if self._reproductor_voz is not None:
            self._reproductor_voz.setSource(QUrl())
        for reproductor, _ in self.pistas.values():
            reproductor.stop()
            reproductor.setSource(QUrl())
        for efecto in self.efectos.values():
            efecto.stop()
        self.fundidos.clear()
