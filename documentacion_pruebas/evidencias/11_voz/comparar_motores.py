"""Compara motores de reconocimiento de voz con los audios de prueba.
Uso: python comparar_motores.py whisper-base whisper-small groq-turbo gemini"""
import json, os, sys, time
RAIZ = "/home/yura/Proyecto Yura /cerebro_yura"
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from frases import FRASES, VOCES
import texto
from main_robot import cargar_archivo_claves
cargar_archivo_claves()

PROMPT = ("Español boliviano con algunas palabras en quechua. Conversación entre un estudiante y un robot educativo. "
          "Comandos posibles: preséntate, conversar, jugar, traducir, enséñame quechua, practicar, silencio y salir. "
          "Vocabulario quechua: rimaykullayki, imaynalla kachkanki, allin p'unchay, yusulpayki, anchata munakuyki, ari, mana, "
          "ñuqa, ñawi, sach'a, yaku, wasi y puka. Transcribe solo lo que escuchas.")

def correcto(tipo, esperado, oido):
    n = texto.normalizar(oido)
    if tipo == "orden": return texto.pide_orden(n, (esperado,))
    if tipo == "contiene": return texto.contiene_frase(n, esperado) or esperado in n.replace("ñ", "n") if esperado == "enseñame" else texto.contiene_frase(n, esperado)
    if tipo == "apagar": return texto.es_orden_apagar(n)
    if tipo == "afirmacion": return texto.es_afirmacion(n)
    if tipo == "quechua": return texto.respuesta_quechua_correcta(n, esperado)

def motor(nombre):
    if nombre.startswith("whisper-"):
        import whisper
        m = whisper.load_model(nombre.split("-", 1)[1])
        return lambda ruta: m.transcribe(ruta, language="es", initial_prompt=PROMPT, fp16=False, temperature=0,
                                         beam_size=5, best_of=1, without_timestamps=True, condition_on_previous_text=False)["text"]
    if nombre == "groq-turbo":
        from groq import Groq
        c = Groq(api_key=os.environ["GROQ_API_KEY"], timeout=15, max_retries=1)
        def t(ruta):
            with open(ruta, "rb") as f:
                return c.audio.transcriptions.create(file=(os.path.basename(ruta), f.read()), model="whisper-large-v3-turbo",
                                                    language="es", prompt=PROMPT[:890], temperature=0).text
        return t
    if nombre == "gemini":
        from gemini_transcriber import GeminiTranscriber
        g = GeminiTranscriber()
        return lambda ruta: g.transcribir(ruta) or ""

resultados = {}
for nombre in sys.argv[1:]:
    transcribir = motor(nombre)
    filas, bien, tiempos = [], 0, []
    for v in VOCES:
        for i, (dicho, tipo, esperado) in enumerate(FRASES):
            ruta = f"audios/{v}_{i:02d}.wav"
            inicio = time.perf_counter()
            try:
                oido = transcribir(ruta)
            except Exception as e:
                oido = f"<ERROR {type(e).__name__}: {str(e)[:80]}>"
            tiempos.append(time.perf_counter() - inicio)
            ok = correcto(tipo, esperado, oido)
            bien += ok
            filas.append({"voz": v, "dicho": dicho, "oido": oido.strip(), "ok": bool(ok)})
            if nombre == "gemini" and oido.startswith("<ERROR") or (nombre == "gemini" and not oido):
                break
        if nombre == "gemini" and filas and not filas[-1]["oido"]:
            break
    total = len(filas)
    tiempos.sort()
    resumen = {"aciertos": bien, "total": total, "porcentaje": round(100 * bien / total) if total else 0,
               "mediana_s": round(tiempos[len(tiempos)//2], 2) if tiempos else None}
    resultados[nombre] = {"resumen": resumen, "filas": filas}
    print(nombre, resumen, flush=True)
    json.dump(resultados, open(f"resultados_{'_'.join(sys.argv[1:])}.json", "w"), ensure_ascii=False, indent=1)
