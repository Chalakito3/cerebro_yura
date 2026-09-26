from types import SimpleNamespace

from audio_manager import AudioManager
from gemini_transcriber import GeminiTranscriber


def test_inicio_de_voz_acepta_respuestas_cortas():
    assert AudioManager._bloques_minimos_inicio_voz(80) == 3


def test_cuota_gemini_agotada_desactiva_reintentos_hasta_reinicio(tmp_path):
    class Models:
        llamadas = 0

        def generate_content(self, **_kwargs):
            self.llamadas += 1
            raise RuntimeError("429 RESOURCE_EXHAUSTED quota exceeded")

    models = Models()
    transcriber = GeminiTranscriber.__new__(GeminiTranscriber)
    transcriber.model = "gemini-test"
    transcriber.client = SimpleNamespace(models=models)
    archivo_audio = tmp_path / "audio.wav"
    archivo_audio.write_bytes(b"audio")

    assert transcriber.transcribir(archivo_audio) is None
    assert not transcriber.disponible
    assert transcriber.transcribir(archivo_audio) is None
    assert models.llamadas == 1