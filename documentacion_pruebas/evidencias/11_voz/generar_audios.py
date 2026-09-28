import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frases import FRASES, VOCES
EDGE = "/home/yura/Proyecto Yura /cerebro_yura/.venv/bin/edge-tts"
os.makedirs("audios", exist_ok=True)
for v in VOCES:
    for i, (texto, _, _) in enumerate(FRASES):
        wav = f"audios/{v}_{i:02d}.wav"
        if os.path.exists(wav):
            continue
        mp3 = wav.replace(".wav", ".mp3")
        subprocess.run([EDGE, "--voice", v, "--text", texto, "--write-media", mp3], check=True, capture_output=True)
        # Igual que Yura: WAV 16 kHz mono, con 0,25 s de silencio al final.
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", mp3, "-ar", "16000", "-ac", "1", "-af", "apad=pad_dur=0.25", wav], check=True)
        os.remove(mp3)
print("audios:", len(os.listdir("audios")))
