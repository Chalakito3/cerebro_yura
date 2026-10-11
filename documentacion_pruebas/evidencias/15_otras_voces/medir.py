"""Mide si lo aprendido de los audios de la docente sirve con otras voces.

Uso: python medir.py VOZ [hilos]
Escribe resultados_<VOZ>.jsonl (una línea por audio y situación) y se puede
reanudar. Solo lee diccionario.db (funciones de lectura / modo ro).
"""
import json, os, random, sqlite3, sys, time
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "basedatos"))

import pronunciaciones
import texto
import traductor
from aprender_de_audios import instruccion
from generar_audios import palabras, nombre

voz = sys.argv[1]
hilos = int(sys.argv[2]) if len(sys.argv) > 2 else 2

import torch
torch.set_num_threads(hilos)
import whisper

LISTA = palabras()
VARIANTES = {p: pronunciaciones.variantes(p) for p in LISTA}
BD = os.path.join(RAIZ, "diccionario.db")
conexion = sqlite3.connect(f"file:{BD}?mode=ro", uri=True)
conexion.row_factory = sqlite3.Row

_original = pronunciaciones.palabra_por_variante


def buscar(t, con_aprendido):
    pronunciaciones.palabra_por_variante = _original if con_aprendido else (lambda _t: None)
    try:
        r = traductor.buscar_vocabulario(t, "quechua", conexion)
    finally:
        pronunciaciones.palabra_por_variante = _original
    quechuas = sorted({str(x["quechua"]) for x in r["resultados"]})
    return {"encontrado": r["encontrado"], "ambiguo": r["ambiguo"], "quechua": quechuas}


def misma(a, b):
    return texto.normalizar(a).replace("'", "") == texto.normalizar(b).replace("'", "")


salida = os.path.join(AQUI, f"resultados_{voz}.jsonl")
hechos = set()
if os.path.exists(salida):
    with open(salida) as f:
        for linea in f:
            d = json.loads(linea)
            hechos.add((d["palabra"], d["situacion"]))

modelo = whisper.load_model("small", device="cpu")
azar_pistas = random.Random(2026)
azar_falsos = random.Random(7)
inicio = time.time()
with open(salida, "a") as f:
    for i, palabra in enumerate(LISTA):
        ruta = nombre(voz, i)
        otras_fp = azar_falsos.sample([p for p in LISTA if not misma(p, palabra)], 5)
        for situacion in ("juego", "menu"):
            pista = instruccion(situacion, palabra, LISTA, azar_pistas)  # siempre, para el mismo azar
            if (palabra, situacion) in hechos or not os.path.exists(ruta):
                continue
            t0 = time.time()
            r = modelo.transcribe(
                ruta, language="es", initial_prompt=pista,
                fp16=False, temperature=0, beam_size=5, best_of=1,
                without_timestamps=True, condition_on_previous_text=False,
            )
            segundos = time.time() - t0
            t = texto.normalizar(r.get("text", ""))
            if texto.es_alucinacion_whisper(t):
                t = ""
            d = {
                "voz": voz, "indice": i, "palabra": palabra, "situacion": situacion,
                "transcripcion": t, "segundos": round(segundos, 2),
                "sin_aprendido": texto.respuesta_quechua_correcta(t, palabra),
                "con_aprendido": texto.respuesta_quechua_correcta(t, palabra, VARIANTES[palabra]),
                "n_variantes": len(VARIANTES[palabra]),
                "falsos_sin": [o for o in otras_fp if texto.respuesta_quechua_correcta(t, o)],
                "falsos_con": [o for o in otras_fp if texto.respuesta_quechua_correcta(t, o, VARIANTES[o])],
                "otras_revisadas": otras_fp,
            }
            if situacion == "menu":
                for clave, con in (("busqueda_sin", False), ("busqueda_con", True)):
                    b = buscar(t, con)
                    b["correcta"] = b["encontrado"] and not b["ambiguo"] and len(b["quechua"]) == 1 and misma(b["quechua"][0], palabra)
                    b["otra_palabra"] = b["encontrado"] and not b["ambiguo"] and not b["correcta"]
                    d[clave] = b
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
            f.flush()
            print(f"[{voz} {i + 1}/{len(LISTA)} {situacion}] {palabra}: «{t}» "
                  f"sin={int(d['sin_aprendido'])} con={int(d['con_aprendido'])} {segundos:.1f}s "
                  f"(total {time.time() - inicio:.0f}s)", flush=True)
print(f"{voz} terminado en {time.time() - inicio:.0f} s", flush=True)
