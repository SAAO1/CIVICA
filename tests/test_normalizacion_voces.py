"""Mezcla local con margen, sincronización e idempotencia tras una interrupción."""
import array
import json
import math
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import wave

from herramientas import normalizar_voces_locales as mezcla


class PruebasNormalizacionVoces(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import imageio_ffmpeg
        cls.ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    def test_la_marca_id3_conserva_el_origen_y_rechaza_datos_incompletos(self):
        datos = {"version": 2, "sha_original": "a"*64, "rms_original": .055,
                 "pico_original": .64, "duracion_original_ms": 1200}
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / "toma.mp3"
            ruta.write_bytes(b"ID3"+mezcla.codificar_marca(datos).encode("ascii")+b"\0")
            self.assertEqual(mezcla.leer_marca(ruta), datos)
            ruta.write_bytes(b"ID3"+mezcla.codificar_marca({"version": 2}).encode("ascii")+b"\0")
            with self.assertRaises(ValueError):
                mezcla.leer_marca(ruta)

    def test_los_limites_rechazan_saturacion_y_cambios_de_tiempo(self):
        antes = {"rms": .05, "duracion_ms": 1200}
        despues = {"rms": .1, "duracion_ms": 1200, "pico_real": .85}
        self.assertAlmostEqual(mezcla.validar_niveles(antes, despues), 6.021, places=3)
        for cambio in ({"pico_real": .981}, {"duracion_ms": 1261}, {"rms": .05}):
            with self.subTest(cambio=cambio), self.assertRaises(ValueError):
                mezcla.validar_niveles(antes, {**despues, **cambio})

    def crear_toma(self, carpeta):
        origen = carpeta / "toma.mp3"
        wav = carpeta / "toma.wav"
        muestras = array.array("h", (round(7000*(.65+.35*math.sin(2*math.pi*4*i/24000))
                                                 *math.sin(2*math.pi*330*i/24000)) for i in range(28800)))
        with wave.open(str(wav), "wb") as salida:
            salida.setparams((1, 2, 24000, len(muestras), "NONE", "not compressed"))
            salida.writeframes(muestras.tobytes())
        subprocess.run([self.ffmpeg, "-v", "error", "-y", "-i", str(wav), "-c:a", "libmp3lame",
                        "-b:a", "48k", str(origen)], capture_output=True, check=True)
        wav.unlink()
        return origen

    def test_preparar_no_modifica_la_toma_y_actualiza_la_envolvente(self):
        with tempfile.TemporaryDirectory() as temporal:
            origen = self.crear_toma(Path(temporal))
            huella_original = mezcla.sha256(origen)
            preparado, marca, medicion, nivel, ganancia = mezcla.preparar_clip(origen, self.ffmpeg)
            self.assertEqual(mezcla.sha256(origen), huella_original)
            self.assertEqual(marca["sha_original"], huella_original)
            self.assertEqual(mezcla.leer_marca(preparado), marca)
            self.assertGreater(ganancia, 4)
            self.assertLess(nivel["pico_real"], .98)
            self.assertLessEqual(abs(nivel["duracion_ms"]-marca["duracion_original_ms"]), 60)
            self.assertTrue(medicion["envolvente"])
            self.assertEqual(medicion["paso_envolvente_ms"], 50)

    def test_reanudar_despues_del_reemplazo_no_aplica_la_ganancia_dos_veces(self):
        with tempfile.TemporaryDirectory() as temporal:
            carpeta = Path(temporal)
            origen = self.crear_toma(carpeta)
            entrada = {"archivo": origen.name, "texto": "Una frase que conserva su intérprete.",
                       "hablante": "CIUDADANO", "voz": "es-CO-GonzaloNeural"}
            original = dict(entrada)
            preparado, _, _, _, _ = mezcla.preparar_clip(origen, self.ffmpeg)
            preparado.replace(origen)  # Corte antes de actualizar el manifest.
            huella_mezclada = mezcla.sha256(origen)
            with patch.object(mezcla, "preparar_clip", side_effect=AssertionError("Doble ganancia")):
                self.assertEqual(mezcla.procesar_entrada(entrada, carpeta, self.ffmpeg), "recuperado")
                self.assertEqual(mezcla.procesar_entrada(entrada, carpeta, self.ffmpeg), "omitido")
            self.assertEqual(mezcla.sha256(origen), huella_mezclada)
            self.assertEqual({clave: entrada[clave] for clave in original}, original)
            self.assertEqual(entrada["mezcla_dialogos"], 2)
            manifest = {"version": 1, "clips": {"toma": entrada}}
            mezcla.guardar_manifest(manifest, carpeta)
            self.assertEqual(json.loads((carpeta / "manifest.json").read_text(encoding="utf-8"))["clips"]["toma"], entrada)
            self.assertFalse((carpeta / "manifest.mezcla.tmp").exists())

    def test_un_sobrepico_se_corrige_volviendo_al_original(self):
        with tempfile.TemporaryDirectory() as temporal:
            origen = Path(temporal) / "toma.mp3"
            origen.write_bytes(b"original"*200)
            codificaciones = []
            def codificar(comando, **kwargs):
                codificaciones.append(comando)
                comentario = comando[comando.index("-metadata")+1].removeprefix("comment=")
                Path(comando[-1]).write_bytes(b"ID3"+comentario.encode("ascii")+b"\0"+b"audio"*300)
            niveles = [{"rms": .05, "duracion_ms": 1200, "pico_real": .5},
                       {"rms": .1, "duracion_ms": 1200, "pico_real": 1.01},
                       {"rms": .093, "duracion_ms": 1200, "pico_real": .94}]
            with patch.object(mezcla.subprocess, "run", side_effect=codificar), \
                    patch.object(mezcla, "medir_nivel", side_effect=niveles), \
                    patch.object(mezcla, "medir_audio", return_value={"envolvente": [.5]}):
                preparado, marca, _, nivel, _ = mezcla.preparar_clip(origen, self.ffmpeg)
            self.assertEqual(len(codificaciones), 2)
            self.assertTrue(all(c[c.index("-i")+1] == str(origen) for c in codificaciones))
            self.assertLess(nivel["pico_real"], .98)
            self.assertIn("volume=0.744554", marca["filtro"])
            self.assertEqual(mezcla.leer_marca(preparado), marca)
