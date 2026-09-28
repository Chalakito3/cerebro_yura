import os
import time
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


# Tras un fallo (red lenta, servicio caído) Gemini se deja de usar un rato:
# antes cada frase esperaba 12 s a que fallara antes de pasar a Whisper.
PAUSA_TRAS_FALLO_S = 600


class GeminiTranscriber:
    """Transcribe audio con Gemini cuando está activado y hay una clave.

    Desactivado por defecto (27/09/2026): Whisper small local entendió
    91-93 % de las frases de prueba con pistas de vocabulario, no envía la
    voz de los niños a internet y no tiene el límite gratuito de 20 usos
    diarios de Gemini. Para activarlo: YURA_GEMINI_ENABLED=1 en .env.local.
    """

    def __init__(self):
        self.model = os.environ.get(
            "YURA_GEMINI_TRANSCRIBE_MODEL",
            "gemini-3.8-flash"
        ).strip()
        self.client = None
        self.pausado_hasta = 0.0

        if os.environ.get("YURA_GEMINI_ENABLED", "0").strip() != "1":
            print("[GEMINI]: Desactivado; se usa Whisper local (YURA_GEMINI_ENABLED=1 para activarlo).")
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
                http_options=types.HttpOptions(timeout=6000)
            )
            print(f"[GEMINI]: Transcriptor listo ({self.model}).")
        except Exception as exc:
            print(f"[GEMINI]: No se pudo inicializar: {exc}")

    @property
    def disponible(self):
        return self.client is not None and time.monotonic() >= getattr(self, "pausado_hasta", 0.0)

    def transcribir(self, audio_path, instruccion=None):
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
                        "Conserva las palabras quechuas, sus apóstrofes y la letra ñ. "
                        + (instruccion or "")
                        + " No traduzcas, no expliques, no corrijas y no inventes. "
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
                self.pausado_hasta = time.monotonic() + PAUSA_TRAS_FALLO_S
                print(f"[GEMINI]: Falló ({type(exc).__name__}); se usa Whisper los próximos 10 minutos.")
            return None
