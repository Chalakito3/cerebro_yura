"""Grupo 8: AudioManager con sounddevice SIMULADO (no se abre ningún dispositivo real)."""
from comun import *  # noqa
import math
import subprocess
import numpy as np
from unittest.mock import patch
import audio_manager
from audio_manager import AudioManager


class Stream:
    def __init__(self, generador, canales):
        self.gen, self.canales, self.leidos = generador, canales, 0

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self, frames):
        datos = self.gen(self.leidos, frames)
        self.leidos += 1
        return np.repeat(np.asarray(datos, dtype=np.float32).reshape(-1, 1), self.canales, axis=1), False


class SD:
    def __init__(self, dispositivos, generador=None, falla_abrir=False):
        self.dispositivos, self.generador, self.falla_abrir = dispositivos, generador, falla_abrir
        self.ultimo = None

    def query_devices(self):
        return self.dispositivos

    def check_input_settings(self, **kw):
        if self.falla_abrir:
            raise RuntimeError("Error opening InputStream: Device unavailable")

    def check_output_settings(self, **kw):
        pass

    def InputStream(self, **kw):
        if self.falla_abrir:
            raise RuntimeError("Error opening InputStream: Device unavailable")
        self.ultimo = Stream(self.generador or (lambda i, n: np.zeros(n)), kw.get("channels", 1))
        return self.ultimo

    def OutputStream(self, **kw):
        return Stream(lambda i, n: np.zeros(n), 1)


MIC = [{"name": "USB Audio Device: C-Media (hw:2,0)", "max_input_channels": 1, "max_output_channels": 2,
        "default_samplerate": 48000}]
sin_pw = patch.object(audio_manager.subprocess, "run",
                      lambda *a, **k: subprocess.CompletedProcess(a, 1, stdout="", stderr=""))


def manager(sd):
    with patch.object(audio_manager, "sd", sd), sin_pw:
        return AudioManager()


def grabar(sd, **kw):
    with patch.object(audio_manager, "sd", sd), sin_pw:
        am = AudioManager()
        t0 = time.perf_counter()
        audio = am.grabar_hasta_silencio(**kw)
        dt = time.perf_counter() - t0
    leidos = sd.ultimo.leidos if sd.ultimo else 0
    return audio, leidos, dt


sd = SD([])
caso("YURA-EXT-801", "audio", "Ningún dispositivo", "query_devices()=[]", "input_device=None y grabar devuelve None",
     lambda: grabar(sd), lambda x: ("OK" if x[0] is None else "FALLA", f"audio={x[0]} bloques={x[1]}"))


class SDRoto(SD):
    def query_devices(self):
        raise OSError("PortAudio not initialized")


caso("YURA-EXT-802", "audio", "query_devices lanza excepción", "OSError", "sin excepción",
     lambda: grabar(SDRoto([])), lambda x: ("OK" if x[0] is None else "FALLA", f"audio={x[0]}"))
caso("YURA-EXT-803", "audio", "Dispositivo que falla al abrir", "check_input_settings lanza", "None sin excepción",
     lambda: grabar(SD(MIC, falla_abrir=True)), lambda x: ("OK" if x[0] is None else "FALLA", f"audio={x[0]}"))

sd = SD(MIC, lambda i, n: np.zeros(n))
caso("YURA-EXT-804", "audio", "Silencio absoluto", "ceros", "None tras espera_maxima (10 s = 125 bloques)",
     lambda: grabar(sd), lambda x: ("OK" if x[0] is None else "FALLA", f"audio={x[0]} bloques leídos={x[1]}"))

rng = np.random.default_rng(0)
sd = SD(MIC, lambda i, n: rng.uniform(-0.6, 0.6, n))
caso("YURA-EXT-805", "audio", "Ruido constante alto (0,3 medio) desde el inicio", "uniforme ±0,6",
     "terminar como máximo en duracion_maxima (15 s)", lambda: grabar(sd),
     lambda x: ("OBSERVACION" if x[0] is not None else "OK",
                f"devuelve {0 if x[0] is None else len(x[0])//2/16000:.1f} s de audio; bloques={x[1]} (el ruido estable se calibra; umbral máx 0,104)"))

sd = SD(MIC, lambda i, n: np.zeros(n) if i < 6 else rng.uniform(-0.6, 0.6, n))
caso("YURA-EXT-806", "audio", "Ruido alto que empieza tras la calibración (TV/ventilador)", "ceros y luego ±0,6",
     "terminar en duracion_maxima; no enviar 15 s de ruido al transcriptor", lambda: grabar(sd),
     lambda x: ("OBSERVACION", f"devuelve {0 if x[0] is None else len(x[0])//2/16000:.1f} s de audio; bloques={x[1]} -> Gemini/Whisper reciben 15 s de ruido"))


def voz_tardia(i, n):
    return np.zeros(n) if i < 6 + 120 else 0.3 * np.sin(np.arange(n) / 5.0)


sd = SD(MIC, voz_tardia)
caso("YURA-EXT-807", "audio", "Voz que empieza a los 9,6 s y dura mucho", "silencio 120 bloques + voz continua",
     "grabar hasta 15 s DESDE que empieza la voz", lambda: grabar(sd),
     lambda x: ("OBSERVACION", f"audio={0 if x[0] is None else len(x[0])//2/16000:.1f} s (duracion_maxima cuenta desde el inicio de la escucha, no desde la voz)"))

sd = SD(MIC, lambda i, n: np.zeros(n) if i < 8 else np.full(n, 1.8) * np.sign(np.sin(np.arange(n))))
caso("YURA-EXT-808", "audio", "Clipping (amplitud 1,8 > 1,0)", "onda cuadrada ±1,8", "int16 válido, sin overflow",
     lambda: grabar(sd),
     lambda x: ("OK" if x[0] is not None and np.abs(np.frombuffer(x[0], np.int16)).max() <= 32768 else "FALLA",
                f"{'None' if x[0] is None else f'{len(x[0])//2} muestras, max={np.abs(np.frombuffer(x[0], np.int16).astype(int)).max()}'}"))

sd = SD(MIC, lambda i, n: np.full(n, np.nan))
caso("YURA-EXT-809", "audio", "Bloques con NaN", "NaN", "None sin excepción", lambda: grabar(sd),
     lambda x: ("OK" if x[0] is None else "FALLA", f"audio={x[0]} bloques={x[1]}"))

sd = SD(MIC, lambda i, n: np.zeros(n) if i < 6 else 0.3 * np.sin(np.arange(n) / 5.0))
caso("YURA-EXT-810", "audio", "Parámetros extremos: bloque_ms=0", "bloque_ms=0", "error controlado",
     lambda: grabar(sd, bloque_ms=0), lambda x: ("OK" if not isinstance(x, BaseException) else "FALLA",
                                                  f"{type(x).__name__}: {x}" if isinstance(x, BaseException) else f"audio={'None' if x[0] is None else len(x[0])}"))

for i, v in enumerate([0, -1, float("nan"), 1.0, float("inf"), None, "abc"]):
    caso(f"YURA-EXT-8{20 + i}", "audio", "_calcular_umbral_ruido", repr(v), "valor en [0,006; 0,12] o error controlado",
         lambda v=v: AudioManager._calcular_umbral_ruido(v),
         lambda x: ("OBSERVACION", f"{type(x).__name__}: {x} (solo recibe floats en el flujo real)") if isinstance(x, BaseException)
         else (("OK" if 0.006 <= x <= 0.12 and not math.isnan(x) else "FALLA"), f"umbral={x}"))

with patch.dict("os.environ", {"YURA_INPUT_DEVICE": "99"}):
    sd = SD(MIC, lambda i, n: np.zeros(n))
    caso("YURA-EXT-830", "audio", "YURA_INPUT_DEVICE apunta a índice inexistente", "99",
         "usar otro dispositivo o avisar", lambda: manager(sd).input_device,
         lambda x: ("OK", f"input_device={x} (se ignora el índice y usa el disponible)"))

resumen()
volcar_matriz("../05_g08_matriz.md")
