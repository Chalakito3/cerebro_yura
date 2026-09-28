"""Pasa los 96 audios por BrainYura.escuchar_voz (código real) con Whisper small,
pistas como en el juego y el evaluador del proyecto."""
import os, random, sys, time, wave
from unittest.mock import Mock
RAIZ = "/home/yura/Proyecto Yura /cerebro_yura"
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.environ.pop("YURA_GEMINI_ENABLED", None)
import threading, whisper, main_robot
from frases import FRASES, VOCES
from comparar_motores_util import correcto
from gemini_transcriber import GeminiTranscriber
random.seed(11)
robot = object.__new__(main_robot.BrainYura)
robot.state = main_robot.RobotStates.JUEGO
robot.web_status = {}; robot.web_status_lock = threading.Lock()
robot.dispositivo_index = 0
robot.audio_manager = Mock(input_device=0)
robot.gemini_transcriber = GeminiTranscriber()
robot.whisper_model = whisper.load_model(os.environ.get("YURA_WHISPER_MODEL", "small"))
main_robot.time.sleep = lambda s: None
QUECHUA = [e for _, t, e in FRASES if t == "quechua"]
bien = total = 0; tiempos = []
for v in VOCES:
    for i, (dicho, tipo, esperado) in enumerate(FRASES):
        with wave.open(f"audios/{v}_{i:02d}.wav") as w:
            robot.audio_manager.grabar_hasta_silencio.return_value = w.readframes(w.getnframes())
        pistas = None
        if tipo == "quechua":
            pistas = random.sample([w for w in QUECHUA if w != esperado], 5) + [esperado]
            random.shuffle(pistas)
        t0 = time.perf_counter(); oido = robot.escuchar_voz(pistas=pistas); tiempos.append(time.perf_counter() - t0)
        ok = correcto(tipo, esperado, oido); bien += ok; total += 1
        if not ok: print("  falla:", dicho, "->", oido)
tiempos.sort()
print(f"Yura real (Whisper {os.environ.get('YURA_WHISPER_MODEL','small')} + pistas + evaluador): {bien}/{total} = {round(100*bien/total)} % | mediana {tiempos[len(tiempos)//2]:.2f} s")
