"""Genera un audio por cada palabra con grabación de la docente, con voces
sintéticas distintas a la de Yura (es-BO-SofiaNeural). WAV 16 kHz mono."""
import os, subprocess, sys, time
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, RAIZ)
import pronunciaciones

EDGE = os.path.join(RAIZ, ".venv", "bin", "edge-tts")
VOCES = ["es-BO-MarceloNeural", "es-PE-AlexNeural", "es-EC-AndreaNeural"]
CARPETA = os.path.join(AQUI, "audios")


def palabras():
    return sorted({g["palabra_frase"] for g in pronunciaciones.grabaciones()})


def nombre(voz, i):
    return os.path.join(CARPETA, f"{voz}_{i:03d}.wav")


if __name__ == "__main__":
    os.makedirs(CARPETA, exist_ok=True)
    lista = palabras()
    for voz in VOCES:
        for i, palabra in enumerate(lista):
            wav = nombre(voz, i)
            if os.path.exists(wav):
                continue
            mp3 = wav.replace(".wav", ".mp3")
            for intento in range(3):
                r = subprocess.run([EDGE, "--voice", voz, "--text", palabra, "--write-media", mp3], capture_output=True)
                if r.returncode == 0:
                    break
                time.sleep(2)
            else:
                print("FALLÓ", voz, palabra, r.stderr.decode()[-200:], flush=True)
                continue
            # Igual que Yura: WAV 16 kHz mono, con 0,25 s de silencio al final.
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", mp3, "-ar", "16000", "-ac", "1",
                            "-af", "apad=pad_dur=0.25", wav], check=True)
            os.remove(mp3)
        print(voz, "listo", flush=True)
    print("audios:", len([f for f in os.listdir(CARPETA) if f.endswith(".wav")]), "palabras:", len(lista))
