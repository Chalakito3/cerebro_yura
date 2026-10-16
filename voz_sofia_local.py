"""La voz de Sofía sin Microsoft: con o sin internet (13/10/2026).

Edge TTS (Sofía) es un servicio de Microsoft. Sin internet, o cuando el
servicio no responde (el 13/10/2026 rechazaba todo con error 403), Yura
hablaba con espeak, otra voz. Ahora:

1. Piper (voz castellana es_MX "claude", corre en la Raspberry) lee la frase.
2. kNN-VC (terceros/knn_vc) cambia cada instante de esa voz por los
   instantes más parecidos de la voz de Sofía (referencia de ~16 minutos de
   Sofía, basedatos/pronunciaciones_yura/referencia_voz_yura.pt).

Se dice oración por oración: si la oración ya está guardada con la voz real
de Sofía se usa esa; si no, se convierte (≈ 8 s por oración en la Pi) y se
guarda en basedatos/voces_sofia_local/, así la próxima vez suena al instante.
Mientras suena una oración se prepara la siguiente.

Modelos (no van a git): modelos_voz/es_MX-claude-high.onnx(.json) y, en
~/.cache/torch/hub/checkpoints, WavLM-Large.pt y prematch_g_02500000.pt.
YURA_VOZ_LOCAL=0 lo desactiva (se vuelve a espeak).
"""
import json
import os
import queue
import subprocess
import sys
import threading
import wave

import voz_sofia

RAIZ = os.path.dirname(os.path.abspath(__file__))
CARPETA = os.path.join(RAIZ, "basedatos", "voces_sofia_local")
MODELO_PIPER = os.path.join(RAIZ, "modelos_voz", "es_MX-claude-high.onnx")
REFERENCIA = os.path.join(RAIZ, "basedatos", "pronunciaciones_yura", "referencia_voz_yura.pt")
PUNTOS = os.path.expanduser("~/.cache/torch/hub/checkpoints")
BASE_KNN = "https://github.com/bshall/knn-vc/releases/download/v0.1/"
FRECUENCIA = 16000
CAPA_WAVLM = 6
VECINOS = 4
CLAVE = "sofia-local"

_modelos = {}
_cargando = threading.Lock()


def activa():
    if os.environ.get("YURA_VOZ_LOCAL", "1").strip() == "0":
        return False
    return all(os.path.exists(r) for r in (
        MODELO_PIPER, MODELO_PIPER + ".json", REFERENCIA,
        os.path.join(PUNTOS, "WavLM-Large.pt"), os.path.join(PUNTOS, "prematch_g_02500000.pt"),
    ))


def cargar_modelos():
    """Tarda ~50 s y ocupa ~1,5 GB: Yura lo hace en segundo plano al arrancar."""
    with _cargando:
        if _modelos:
            return _modelos
        import torch
        sys.path.insert(0, os.path.join(RAIZ, "terceros", "knn_vc"))
        from hifigan.models import Generator
        from hifigan.utils import AttrDict
        from piper import PiperVoice
        from wavlm.WavLM import WavLM, WavLMConfig

        punto = torch.hub.load_state_dict_from_url(BASE_KNN + "WavLM-Large.pt", map_location="cpu", progress=False)
        wavlm = WavLM(WavLMConfig(punto["cfg"]))
        wavlm.load_state_dict(punto["model"])
        with open(os.path.join(RAIZ, "terceros", "knn_vc", "hifigan", "config_v1_wavlm.json")) as f:
            vocoder = Generator(AttrDict(json.load(f)))
        vocoder.load_state_dict(torch.hub.load_state_dict_from_url(
            BASE_KNN + "prematch_g_02500000.pt", map_location="cpu", progress=False)["generator"])
        vocoder.eval()
        vocoder.remove_weight_norm()
        referencia = torch.load(REFERENCIA).float()
        _modelos.update(
            piper=PiperVoice.load(MODELO_PIPER),
            wavlm=wavlm.eval(),
            vocoder=vocoder,
            referencia=referencia,
            referencia_normal=torch.nn.functional.normalize(referencia, dim=-1),
        )
        return _modelos


def precargar():
    """Carga los modelos sin frenar a Yura. No hace nada si falta algo."""
    if not activa():
        return
    def _cargar():
        try:
            cargar_modelos()
            print("[VOZ] Voz de Sofía sin internet lista.")
        except Exception as exc:
            print(f"[VOZ] No se pudo preparar la voz de Sofía sin internet: {exc}")
    threading.Thread(target=_cargar, name="voz-sofia-local", daemon=True).start()


def _a_16k(ruta):
    salida = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", ruta, "-ac", "1", "-ar", str(FRECUENCIA),
         "-f", "s16le", "-"], capture_output=True, check=True, timeout=60,
    ).stdout
    import numpy as np
    return np.frombuffer(salida, dtype=np.int16).astype(np.float32) / 32768.0


def _guardar(ruta, senal):
    import numpy as np
    senal = np.asarray(senal, dtype=np.float32)
    pico = float(np.max(np.abs(senal))) if senal.size else 0.0
    if pico > 0:
        senal = senal * (0.9 / pico)
    temporal = ruta + ".tmp"
    with wave.open(temporal, "wb") as archivo:
        archivo.setnchannels(1)
        archivo.setsampwidth(2)
        archivo.setframerate(FRECUENCIA)
        archivo.writeframes((np.clip(senal, -1, 1) * 32767).astype(np.int16).tobytes())
    os.replace(temporal, ruta)


def convertir(texto, destino):
    """Texto -> WAV con la voz de Sofía (Piper + kNN-VC)."""
    import torch
    modelos = cargar_modelos()
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    lectura = destino + ".piper.wav"
    try:
        with wave.open(lectura, "wb") as archivo:
            modelos["piper"].synthesize_wav(texto.replace("«", "").replace("»", ""), archivo)
        senal = _a_16k(lectura)
    finally:
        try:
            os.remove(lectura)
        except OSError:
            pass
    with torch.inference_mode():
        rasgos = modelos["wavlm"].extract_features(
            torch.from_numpy(senal)[None], output_layer=CAPA_WAVLM, ret_layer_results=False)[0].squeeze(0)
        parecidos = torch.nn.functional.normalize(rasgos, dim=-1) @ modelos["referencia_normal"].T
        mejores = parecidos.topk(k=VECINOS, dim=-1).indices
        onda = modelos["vocoder"](modelos["referencia"][mejores].mean(dim=1)[None]).squeeze().numpy()
    _guardar(destino, onda)
    return destino


def ruta_local(texto_voz):
    return voz_sofia.ruta_cache(CARPETA, CLAVE, texto_voz)


def decir(texto_voz, reproducir, carpeta_sofia=None, voz=None):
    """Dice la frase con la voz de Sofía sin usar Microsoft. reproducir(ruta)
    devuelve True si sonó. Devuelve False si no pudo decirla entera."""
    if not activa():
        return False
    partes = voz_sofia.oraciones(texto_voz) or [texto_voz.strip()]
    partes = [p for p in partes if p]
    if not partes:
        return False

    def _ruta(parte):
        if carpeta_sofia and voz:
            real = voz_sofia.ruta_cache(carpeta_sofia, voz, parte)
            if real and os.path.exists(real) and os.path.getsize(real) > 0:
                return real
        local = ruta_local(parte)
        if not (os.path.exists(local) and os.path.getsize(local) > 0):
            convertir(parte, local)
        return local

    listas = queue.Queue()

    def _preparar():
        for parte in partes:
            try:
                listas.put(_ruta(parte))
            except Exception as exc:
                print(f"[VOZ] Sofía sin internet no pudo decir «{parte[:40]}»: {exc}")
                listas.put(None)
                return

    threading.Thread(target=_preparar, name="voz-sofia-local-frase", daemon=True).start()
    for _ in partes:
        ruta = listas.get()
        if ruta is None or not reproducir(ruta):
            return False
    return True
