"""Nivel, integridad y reproducción del refuerzo local de voces."""
import hashlib,json,os
from pathlib import Path
import statistics,tempfile,unittest
from unittest.mock import Mock
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from PyQt6.QtWidgets import QApplication
from audio.catalogo_voces import CARPETA_VOCES,cargar_manifest,ruta_clip
from audio.gestor_audio import GestorAudio
from audio.voces_reforzadas import CARPETA_REFUERZO,ruta_reproduccion

class VocesReforzadas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])
        cls.manifest=json.loads((CARPETA_REFUERZO/"manifest.json").read_text(encoding="utf-8"))

    def test_todas_las_voces_tienen_refuerzo_integro_sin_modificar_los_originales(self):
        originales=cargar_manifest()["clips"]
        self.assertEqual(set(self.manifest["clips"]),{e["archivo"] for e in originales.values()})
        self.assertEqual(self.manifest["cantidad"],len(originales))
        for entrada in originales.values():
            with self.subTest(archivo=entrada["archivo"]):
                registro=self.manifest["clips"][entrada["archivo"]]
                original=ruta_clip(entrada)
                self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(),registro["sha_original"])
                reforzado=CARPETA_REFUERZO/entrada["archivo"]
                self.assertEqual(hashlib.sha256(reforzado.read_bytes()).hexdigest(),registro["sha256"])
                self.assertEqual(reforzado.stat().st_size,registro["bytes"])
                self.assertEqual(ruta_reproduccion(entrada,original),reforzado)

    def test_nivel_aumenta_sin_saturacion_ni_cambio_de_duracion_o_interprete(self):
        originales=cargar_manifest()["clips"]
        ganancias=[]
        for entrada in originales.values():
            r=self.manifest["clips"][entrada["archivo"]]
            self.assertGreater(r["ganancia_db"],.5)
            self.assertLess(r["pico_real"],.98)
            self.assertLessEqual(abs(r["duracion_ms"]-entrada["duracion_ms"]),60)
            self.assertEqual(r["hablante"],entrada["hablante"])
            ganancias.append(r["ganancia_db"])
        self.assertGreater(statistics.median(ganancias),3)
        self.assertLess(self.manifest["pico_maximo"],.98)

    def test_reproduccion_usa_refuerzo_y_silencio_sigue_cancelando_la_voz(self):
        audio=GestorAudio()
        self.addCleanup(audio.detener)
        audio.configurar("general",1)
        audio.configurar("voces",1)
        audio._reproductor_voz=Mock()
        entrada=next(e for e in cargar_manifest()["clips"].values() if e["hablante"]=="NARRADOR")
        self.assertTrue(audio.narrar(entrada["texto"],"NARRADOR"))
        archivo=audio._reproductor_voz.setSource.call_args.args[0].toLocalFile()
        self.assertEqual(Path(archivo),CARPETA_REFUERZO/entrada["archivo"])
        audio.silenciar()
        self.assertEqual(audio._salida_voz.volume(),0)
        self.assertFalse(audio.narrar(entrada["texto"],"NARRADOR"))

    def test_refuerzo_ausente_corrupto_o_de_otro_original_vuelve_a_la_voz_original(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)
            original=base/"original.mp3";original.write_bytes(b"original")
            carpeta=base/"refuerzo";carpeta.mkdir()
            entrada={"archivo":"voz.mp3"}
            self.assertEqual(ruta_reproduccion(entrada,original,carpeta),original)
            reforzado=carpeta/"voz.mp3";reforzado.write_bytes(b"reforzado")
            registro={"sha_original":hashlib.sha256(b"original").hexdigest(),
                "sha256":hashlib.sha256(b"reforzado").hexdigest(),"bytes":9}
            manifest=carpeta/"manifest.json"
            manifest.write_text(json.dumps({"version":1,"clips":{"voz.mp3":registro}}),encoding="utf-8")
            self.assertEqual(ruta_reproduccion(entrada,original,carpeta),reforzado)
            original.write_bytes(b"otra voz")
            self.assertEqual(ruta_reproduccion(entrada,original,carpeta),original)
            original.write_bytes(b"original")
            reforzado.write_bytes(b"corrupto")
            self.assertEqual(ruta_reproduccion(entrada,original,carpeta),original)
            self.assertEqual(ruta_reproduccion({"archivo":"../original.mp3"},original,carpeta),original)
            manifest.write_text("[]",encoding="utf-8")
            self.assertEqual(ruta_reproduccion(entrada,original,carpeta),original)

if __name__=="__main__":
    unittest.main()
