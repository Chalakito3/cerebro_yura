import os
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


class GeminiTranscriber:
    """Transcribe audio con Gemini cuando hay una clave configurada."""

    def __init__(self):
        self.model = os.environ.get(
            "YURA_GEMINI_TRANSCRIBE_MODEL",
            "gemini-2.5-flash"
        ).strip()
        self.client = None

        if os.environ.get("YURA_GEMINI_ENABLED", "1").strip() == "0":
            print("[GEMINI]: Desactivado por configuración; se usará Whisper.")
            return

        api_key = (
            os.environ.get("GEMINI_API_KEY", "").strip()
            or os.environ.get("GOOGLE_API_KEY", "").strip()
        )
        if genai is None:
            print("[GEMINI]: SDK no disponible; se usará Whisper.")
            return
        if not api_key:
            print("[GEMINI]: No hay GEMINI_API_KEY; se usará Whisper.")
            return

        try:
            self.client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(timeout=12000)
            )
            print(f"[GEMINI]: Transcriptor listo ({self.model}).")
        except Exception as exc:
            print(f"[GEMINI]: No se pudo inicializar: {exc}")

    @property
    def disponible(self):
        return self.client is not None

    def transcribir(self, audio_path):
        if not self.disponible:
            return None

        ruta = Path(audio_path)
        try:
            audio_bytes = ruta.read_bytes()
            respuesta = self.client.models.generate_content(
                model=self.model,
                contents=[
                    types.Part.from_bytes(
                        data=audio_bytes,
                        mime_type="audio/wav"
                    ),
                    (
                        "Transcribe exactamente lo que dice el estudiante. "
                        "Puede hablar español o quechua boliviano. "
                        "Conserva las palabras quechuas y sus apóstrofes. "
                        "Ejemplos de vocabulario: rimaykullayki, "
                        "imaynalla kachkanki, allin p'unchay, yusulpayki, "
                        "anchata munakuyki, puka, yaku, wasi. "
                        "No traduzcas, no expliques, no corrijas y no inventes. "
                        "Devuelve únicamente la transcripción, sin comillas."
                    )
                ],
                config=types.GenerateContentConfig(
                    temperature=0,
                    max_output_tokens=120,
                )
            )
            texto = str(respuesta.text or "").strip()
            return texto or None
        except Exception as exc:
            error = str(exc)
            if "429" in error or "RESOURCE_EXHAUSTED" in error.upper():
                self.client = None
                print(
                    "[GEMINI]: Cuota agotada; se usará Whisper hasta "
                    "reiniciar Yura."
                )
            else:
                print(f"[GEMINI]: Falló la transcripción: {exc}")
            return None
