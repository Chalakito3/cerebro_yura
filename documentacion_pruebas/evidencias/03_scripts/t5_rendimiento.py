import io
import time
import contextlib
import statistics

t0 = time.perf_counter()
from harness import conversacion, traductor, RO, main_robot  # noqa
t_import = time.perf_counter() - t0


def medir(nombre, f, n=30):
    ts = []
    for _ in range(n):
        a = time.perf_counter()
        with contextlib.redirect_stdout(io.StringIO()):
            f()
        ts.append((time.perf_counter() - a) * 1000)
    print(f"| {nombre} | {n} | {statistics.median(ts):.2f} | {max(ts):.2f} |")


print(f"Importar main_robot+conversacion+traductor+juego (incluye whisper, vosk, torch): {t_import:.2f} s")
print("| Operación | repeticiones | mediana ms | máx ms |")
print("|---|---|---|---|")
medir("_leer_registros_vocabulario (15 tablas, 187 filas)", lambda: traductor._leer_registros_vocabulario(RO))
medir("buscar_vocabulario('perro')", lambda: traductor.buscar_vocabulario("perro", "espanol", RO))
medir("vocabulario_relevante('como se dice amarillo')", lambda: traductor.vocabulario_relevante("como se dice amarillo en quechua", RO))
medir("_obtener_vocabulario_para_practica (5 lecturas completas)", lambda: conversacion._obtener_vocabulario_para_practica(RO))
medir("procesar_entrada('como se dice perro en quechua')", lambda: conversacion.procesar_entrada("como se dice perro en quechua", None))

# contar lecturas completas de la BD por cada frase procesada
cont = {"n": 0}
orig = traductor._leer_registros_vocabulario


def contado(c):
    cont["n"] += 1
    return orig(c)


traductor._leer_registros_vocabulario = contado
for frase in ["como se dice perro en quechua", "ensename quechua", "hablemos en quechua de mi familia"]:
    cont["n"] = 0
    from types import SimpleNamespace as NS

    class C:
        def create(self, **kw):
            return NS(choices=[NS(finish_reason="stop", message=NS(content="ok"))])
    with contextlib.redirect_stdout(io.StringIO()):
        conversacion.cancelar_sesion_educativa()
        conversacion.procesar_entrada(frase, NS(chat=NS(completions=C())))
    print(f"Lecturas completas de las 15 tablas para '{frase}': {cont['n']}")
traductor._leer_registros_vocabulario = orig

# Detección de dispositivos de audio (lo que grabar_hasta_silencio repite en CADA escucha)
from audio_manager import AudioManager
am = AudioManager.__new__(AudioManager)
am.sample_rate = 16000; am.channels = 1; am.input_device = None; am.output_device = None
am.output_alsa_device = None; am.input_sample_rate = 16000; am.input_channels = 1; am.input_candidates = []
ts = []
for _ in range(5):
    a = time.perf_counter()
    with contextlib.redirect_stdout(io.StringIO()):
        am.detectar_dispositivos()
        am.seleccionar_entrada()
    ts.append(time.perf_counter() - a)
print(f"detectar_dispositivos()+seleccionar_entrada() (sin grabar): mediana {statistics.median(ts)*1000:.0f} ms, máx {max(ts)*1000:.0f} ms; entrada elegida={am.input_device}")

# Whisper
import torch
import whisper
print("CUDA disponible:", torch.cuda.is_available())
a = time.perf_counter()
m = whisper.load_model("base")
print(f"whisper.load_model('base'): {time.perf_counter()-a:.2f} s, dispositivo={next(m.parameters()).device}")
if torch.cuda.is_available():
    print(f"memoria GPU reservada por torch: {torch.cuda.memory_reserved()/1e6:.0f} MB")
