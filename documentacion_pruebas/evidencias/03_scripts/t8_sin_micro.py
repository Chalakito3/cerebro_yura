import io, time, contextlib, threading
from unittest.mock import Mock
from harness import make_brain, S, main_robot
b = make_brain(S.TRADUCIR, [])
del b.escuchar_voz  # usar el escuchar_voz real
b.audio_manager = Mock(input_device=None)
b.audio_manager.grabar_hasta_silencio.return_value = None  # micrófono desconectado
b.dispositivo_index = None
b.gemini_transcriber = Mock(); b.whisper_model = None
t_fin = time.time() + 3
b.running = True
def parar():
    time.sleep(3); b.running = False
threading.Thread(target=parar).start()
with contextlib.redirect_stdout(io.StringIO()) as out:
    b.ejecutar_traducir()
print("En 3 s sin micrófono (modo TRADUCIR): intentos de escucha =", b.audio_manager.grabar_hasta_silencio.call_count,
      "| frases habladas =", b.hw.hablar.call_count, "| ejemplo:", b.hw.hablar.call_args_list[0].args[0])
print("líneas de log generadas:", len(out.getvalue().splitlines()))
