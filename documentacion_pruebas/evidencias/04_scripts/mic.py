import sys,time,os
sys.path.insert(0,os.getcwd())
import numpy as np, sounddevice as sd
from audio_manager import AudioManager
t=time.perf_counter(); am=AudioManager(); print(f"AudioManager init: {time.perf_counter()-t:.2f} s")
info=sd.query_devices(am.input_device); print("input_device",am.input_device,info["name"],"sr",am.input_sample_rate,"ch",am.input_channels,"output_device",am.output_device,"output_alsa",am.output_alsa_device)
fr=am.input_sample_rate; blk=int(fr*0.08)
with sd.InputStream(device=am.input_device,channels=am.input_channels,dtype="float32",samplerate=fr,blocksize=blk) as st:
    for _ in range(3): st.read(blk)
    datos=[st.read(blk)[0].mean(axis=1) for _ in range(int(3/0.08))]
a=np.concatenate(datos)
niv=[AudioManager._calcular_nivel_audio(d) for d in datos]
ruido=AudioManager._calcular_nivel_audio(a)
print(f"grabados {len(a)/fr:.2f} s; nivel medio |x| = {ruido:.5f}; bloque min={min(niv):.5f} max={max(niv):.5f}; pico={np.max(np.abs(a)):.4f}; RMS dBFS={20*np.log10(np.sqrt(np.mean(a**2))+1e-12):.1f}")
print(f"umbral calculado = {AudioManager._calcular_umbral_ruido(ruido):.4f} (mínimo forzado 0.0060); bloques mínimos inicio voz (80 ms) = {AudioManager._bloques_minimos_inicio_voz(80)}")
print("bloques de ruido que superarían el umbral:",sum(n>=AudioManager._calcular_umbral_ruido(ruido) for n in niv))
