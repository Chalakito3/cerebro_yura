#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Completa el mapa acústico de Vosk y la caché de voz de Sofía para las 288 palabras.

1. Para cada palabra del diccionario quechua, genera su pronunciación con Sofía (Edge-TTS)
   aplicando las reglas fonéticas de Teófilo Laime (pronunciaciones.texto_para_hablar).
2. Guarda el audio WAV en basedatos/voces_sofia/ (autonomía offline para Sofía).
3. Pasa el audio por VOSK (Kaldi) para registrar cómo decodifica el modelo acústico en español.
4. Guarda las correspondencias en basedatos/mapa_acustico_vosk.json para que Yura entienda
   las 288 palabras del diccionario con 100% de cobertura.
"""

import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)


CARPETA_VOCES = os.path.join(RAIZ, "basedatos", "voces_sofia")
RUTA_MAPA = os.path.join(RAIZ, "basedatos", "mapa_acustico_vosk.json")
RUTA_DB = os.path.join(RAIZ, "diccionario.db")
RUTA_MODELO_VOSK = os.path.join(RAIZ, "model")
VOZ_SOFIA = os.environ.get("YURA_VOZ", "es-BO-SofiaNeural")


def ruta_cache(texto_voz):
    texto_norm = re.sub(r"\s+", " ", str(texto_voz or "").strip().lower())
    if not texto_norm:
        return None
    clave = hashlib.sha256(f"{VOZ_SOFIA}:{texto_norm}".encode("utf-8")).hexdigest()[:24]
    return os.path.join(CARPETA_VOCES, f"{clave}.wav")


def sintetizar_audio(texto_para_voz, ruta_wav):
    edge_tts = os.path.join(RAIZ, ".venv", "bin", "edge-tts")
    if not os.path.exists(edge_tts):
        edge_tts = "edge-tts"

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_mp3:
        ruta_mp3 = temp_mp3.name

    try:
        cmd_tts = [
            edge_tts,
            "--voice", VOZ_SOFIA,
            "--rate=+5%",
            "--text", texto_para_voz,
            "--write-media", ruta_mp3
        ]
        res = subprocess.run(cmd_tts, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=25)
        if res.returncode != 0 or not os.path.exists(ruta_mp3) or os.path.getsize(ruta_mp3) == 0:
            return False

        cmd_ffmpeg = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", ruta_mp3,
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            ruta_wav
        ]
        res_ff = subprocess.run(cmd_ffmpeg, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
        return res_ff.returncode == 0 and os.path.exists(ruta_wav) and os.path.getsize(ruta_wav) > 0
    finally:
        try:
            os.remove(ruta_mp3)
        except OSError:
            pass


def main():
    os.makedirs(CARPETA_VOCES, exist_ok=True)
    from vosk import Model, KaldiRecognizer
    import wave

    print("[VOSK]: Cargando modelo acústico...")
    vosk_model = Model(RUTA_MODELO_VOSK)

    # Cargar mapa actual
    mapa_actual = {}
    if os.path.exists(RUTA_MAPA):
        with open(RUTA_MAPA, "r", encoding="utf-8") as f:
            mapa_actual = json.load(f)

    con = sqlite3.connect(RUTA_DB)
    con.row_factory = sqlite3.Row

    # Obtener todas las palabras y su fonética para voz
    filas = con.execute("SELECT palabra_frase, texto_para_voz FROM pronunciaciones_voz").fetchall()
    print(f"[VOCABULARIO]: {len(filas)} palabras en pronunciaciones_voz.")

    nuevas_mapeadas = 0
    nuevas_voces = 0

    for idx, f in enumerate(filas, 1):
        palabra = f["palabra_frase"].strip()
        para_voz = (f["texto_para_voz"] or palabra).strip()

        # Ruta en caché de Sofía
        wav_cache = ruta_cache(para_voz)

        # Si no existe en caché de Sofía, sintetizar
        if not os.path.exists(wav_cache):
            exito = sintetizar_audio(para_voz, wav_cache)
            if exito:
                nuevas_voces += 1
            else:
                continue

        # Si ya está mapeada en Vosk, saltar escucha
        if palabra in set(mapa_actual.values()):
            continue

        # Pasar por Vosk para capturar la acústica
        try:
            with wave.open(wav_cache, "rb") as wf:
                rec = KaldiRecognizer(vosk_model, 16000)
                rec.AcceptWaveform(wf.readframes(wf.getnframes()))
                res_vosk = json.loads(rec.FinalResult()).get("text", "").strip()

            if res_vosk and res_vosk != "[unk]":
                mapa_actual[res_vosk] = palabra
                nuevas_mapeadas += 1
                if nuevas_mapeadas % 10 == 0:
                    print(f"[{idx}/{len(filas)}] Mapeado: '{res_vosk}' -> '{palabra}'")
        except Exception as e:
            pass

    # Guardar mapa acústico actualizado
    with open(RUTA_MAPA, "w", encoding="utf-8") as f:
        json.dump(mapa_actual, f, ensure_ascii=False, indent=2)

    print("\n[RESUMEN FINAL]")
    print(f"  • Nuevas voces de Sofía guardadas en disco: {nuevas_voces}")
    print(f"  • Nuevas variantes acústicas de Vosk:       {nuevas_mapeadas}")
    print(f"  • Total pares acústicos en Vosk:            {len(mapa_actual)}")
    print(f"  • Total palabras cubiertas:                 {len(set(mapa_actual.values()))} de {len(filas)}")


if __name__ == "__main__":
    main()
