"""Whisper small con pistas de vocabulario, simulando el juego: el reconocedor
recibe la palabra esperada MEZCLADA con 5 palabras distintas (para no
favorecer la respuesta correcta)."""
import json, os, random, sys, time
RAIZ = "/home/yura/Proyecto Yura /cerebro_yura"
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from frases import FRASES, VOCES
import comparar_motores_util as _u
correcto = _u.correcto
import whisper
random.seed(7)
modelo = whisper.load_model(sys.argv[1] if len(sys.argv) > 1 else "small")
QUECHUA = [e for _, t, e in FRASES if t == "quechua"]
BASE = ("Español boliviano con palabras en quechua. Un estudiante habla con el robot educativo Yura. "
        "Órdenes: jugar, traducir, enséñame quechua, apágate, sí, despierta, volver al menú.")
bien = total = 0
for v in VOCES:
    for i, (dicho, tipo, esperado) in enumerate(FRASES):
        if tipo == "quechua":
            pistas = random.sample([w for w in QUECHUA if w != esperado], 5) + [esperado]
            random.shuffle(pistas)
            prompt = BASE + " Palabras en quechua: " + ", ".join(pistas) + "."
        else:
            prompt = BASE + " Palabras en quechua: " + ", ".join(random.sample(QUECHUA, 6)) + "."
        oido = modelo.transcribe(f"audios/{v}_{i:02d}.wav", language="es", initial_prompt=prompt, fp16=False, temperature=0,
                                 beam_size=5, best_of=1, without_timestamps=True, condition_on_previous_text=False)["text"]
        ok = correcto(tipo, esperado, oido); bien += ok; total += 1
        if not ok: print("  falla:", dicho, "->", oido.strip()[:30])
print(sys.argv[1] if len(sys.argv) > 1 else "small", "con pistas:", bien, "/", total, f"= {round(100*bien/total)} %")
