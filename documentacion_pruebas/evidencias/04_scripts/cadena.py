# Cadena completa de voz sin micrófono humano (robot real APAGADO).
import os, sys, time, json, wave, subprocess, sqlite3, re, unicodedata
PROJ="/home/yura/Proyecto Yura /cerebro_yura"; sys.path.insert(0,PROJ); os.chdir(PROJ)
OUT=sys.argv[1]; os.makedirs(OUT,exist_ok=True)
LLAMADAS={"edge_tts":0,"gemini":0,"groq":0}
import main_robot, conversacion, traductor
from main_robot import BrainYura, RobotStates, HardwareInterface, cargar_archivo_claves
from gemini_transcriber import GeminiTranscriber
from juego import Juego
cargar_archivo_claves()
print("claves presentes:", bool(os.environ.get("GROQ_API_KEY")), bool(os.environ.get("GEMINI_API_KEY")))
FRASES=["jugar","traducir","perro","buenas noches","¿cómo se dice gato en quechua?","enséñame quechua","Rimaykullayki","Imaynalla kachkanki"]
EDGE=os.path.join(PROJ,".venv/bin/edge-tts")
def norm(t):
    t=str(t or "").lower().replace("’","'")
    t="".join(c for c in unicodedata.normalize("NFKD",t) if not unicodedata.combining(c))
    return re.sub(r"\s+"," ",re.sub(r"[^a-z0-9ñ'\s]"," ",t)).strip()
def wer(ref,hyp):
    r=ref.split(); h=hyp.split()
    d=[[0]*(len(h)+1) for _ in range(len(r)+1)]
    for i in range(len(r)+1): d[i][0]=i
    for j in range(len(h)+1): d[0][j]=j
    for i in range(1,len(r)+1):
        for j in range(1,len(h)+1):
            d[i][j]=min(d[i-1][j]+1,d[i][j-1]+1,d[i-1][j-1]+(r[i-1]!=h[j-1]))
    return d[len(r)][len(h)]/max(1,len(r))
# 1) generar audios
audios={}
for i,f in enumerate(FRASES):
    mp3=f"{OUT}/f{i}.mp3"; wav=f"{OUT}/f{i}.wav"
    t=time.perf_counter(); r=subprocess.run([EDGE,"--voice","es-MX-DaliaNeural","--text",f,"--write-media",mp3],capture_output=True); LLAMADAS["edge_tts"]+=1
    tg=time.perf_counter()-t
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",mp3,"-ar","16000","-ac","1","-acodec","pcm_s16le",wav],check=True)
    with wave.open(wav) as w: pcm=w.readframes(w.getnframes()); dur=w.getnframes()/w.getframerate(); fmt=(w.getframerate(),w.getnchannels(),w.getsampwidth())
    audios[f]=(pcm,dur,tg,r.returncode,fmt)
    print(f"[TTS entrada] {f!r}: rc={r.returncode} gen={tg:.2f}s dur={dur:.2f}s fmt={fmt}")
# 2) cerebro real con piezas reales (sin __init__ para no abrir micrófono ni BD en escritura)
import whisper
t=time.perf_counter(); wm=whisper.load_model(os.environ.get("YURA_WHISPER_MODEL","base")); t_wload=time.perf_counter()-t
print(f"Whisper base cargado en {t_wload:.2f}s dispositivo={next(wm.parameters()).device}")
gem=GeminiTranscriber()
db=sqlite3.connect("file:diccionario.db?mode=ro",uri=True,check_same_thread=False)
conversacion._conexion_vocabulario=db   # fuerza solo lectura también en conversacion
b=BrainYura.__new__(BrainYura)
import threading
b.state=RobotStates.MENU; b.running=True; b.historial_conversacion=[]
b.web_status={"phase":"","content":"","translation":"","result":None,"updated_at":None}; b.web_status_lock=threading.Lock()
b.saludo_inicial_done=True; b.db_conn=db; b.whisper_model=wm; b.gemini_transcriber=gem
b.groq_client=b._crear_cliente_groq()
# contar llamadas Groq
_orig=traductor.consultar_modelo_groq
def _cnt(*a,**k):
    LLAMADAS["groq"]+=1; t=time.perf_counter(); r=_orig(*a,**k); _cnt.last=time.perf_counter()-t; return r
_cnt.last=0; traductor.consultar_modelo_groq=_cnt
DICHO=[]
class HW:
    def hablar(self,t): DICHO.append(t)
    def mover_actuador(self,c): DICHO.append(f"[ACTUADOR {c}]")
b.hw=HW()
class AM: input_device=7
b.audio_manager=AM(); b.dispositivo_index=7
b.juego=Juego(["gato","perro","sol","agua","casa","arbol"],lambda p: traductor.consultar_diccionario_local(p,db),lambda:"",b.hw.hablar,b._mover_actuador,b._normalizar_texto,b._set_game_event)
def transcribir(pcm, motor):
    """Mismo camino que escuchar_voz: WAV 16k mono + 0,25 s de silencio."""
    ruta=f"{OUT}/yura_temp.wav"
    with wave.open(ruta,"wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(16000); wf.writeframes(pcm+b"\x00"*int(16000*2*0.25))
    t=time.perf_counter()
    if motor=="gemini":
        LLAMADAS["gemini"]+=1; txt=gem.transcribir(ruta) or ""
    else:
        res=wm.transcribe(ruta,language="es",initial_prompt=("Español boliviano con algunas palabras en quechua. Conversación entre un estudiante y un robot educativo. Comandos posibles: preséntate, conversar, jugar, traducir, enséñame quechua, practicar, silencio y salir. Vocabulario quechua: rimaykullayki, imaynalla kachkanki, allin p'unchay, yusulpayki, anchata munakuyki, ari, mana, yaku, wasi y puka. Transcribe solo lo que escuchas."),fp16=False,temperature=0,beam_size=5,best_of=1,without_timestamps=True,condition_on_previous_text=False)
        txt=res.get("text","")
    return txt, time.perf_counter()-t
# calentamiento whisper (no cuenta)
transcribir(audios["jugar"][0],"whisper")
filas=[]
for f in FRASES:
    pcm,dur,tg,rc,fmt=audios[f]
    tg_txt,t_g=transcribir(pcm,"gemini")
    tw_txt,t_w=transcribir(pcm,"whisper")
    texto=b._normalizar_texto(tg_txt) if tg_txt else b._normalizar_texto(tw_txt)
    motor="Gemini" if tg_txt else "Whisper"
    # decisión en MENÚ con el código real
    b.state=RobotStates.MENU; DICHO.clear(); b.escuchar_voz=lambda texto=texto: texto
    _cnt.last=0; ng=LLAMADAS["groq"]
    t=time.perf_counter(); b.ejecutar_menu(); t_d=time.perf_counter()-t
    resp_menu=" | ".join(DICHO); estado_menu=b.state; uso_groq=LLAMADAS["groq"]>ng
    fila=dict(frase=f,dur_audio=round(dur,2),gemini=tg_txt,t_gemini=round(t_g,2),exacto_gemini=norm(tg_txt)==norm(f),wer_gemini=round(wer(norm(f),norm(tg_txt)),2),
              whisper=tw_txt.strip(),t_whisper=round(t_w,2),exacto_whisper=norm(tw_txt)==norm(f),wer_whisper=round(wer(norm(f),norm(tw_txt)),2),
              texto_normalizado=texto,motor=motor,estado_tras_menu=estado_menu,respuesta_menu=resp_menu,t_decision=round(t_d,3),groq=uso_groq,t_groq=round(_cnt.last,2))
    filas.append(fila); print(json.dumps(fila,ensure_ascii=False))
# decisiones en otros modos (sin nuevas transcripciones)
extra={}
def en_traductor(texto):
    DICHO.clear(); vueltas=iter([True,False]); t=time.perf_counter()
    traductor.ejecutar_traducir(lambda:texto,b.hw.hablar,db,b.groq_client,lambda:next(vueltas),on_status=b._set_web_status)
    return " | ".join(DICHO), round(time.perf_counter()-t,3)
for f in ("perro","buenas noches"):
    txt=[x for x in filas if x["frase"]==f][0]["texto_normalizado"]
    extra[f"TRADUCIR:{f}"]=en_traductor(txt)
def en_conversar(texto):
    DICHO.clear(); b.state=RobotStates.CONVERSAR; b.escuchar_voz=lambda:texto; t=time.perf_counter(); b.ejecutar_conversar(); return " | ".join(DICHO), round(time.perf_counter()-t,3)
for f in ("perro",):
    txt=[x for x in filas if x["frase"]==f][0]["texto_normalizado"]
    extra[f"CONVERSAR:{f}"]=en_conversar(txt)
conversacion.cancelar_sesion_educativa()
# JUEGO: respuesta del niño = transcripción real de "perro" (texto español, debe ser incorrecta)
b.juego.reiniciar(); b.juego.palabras_partida=["perro"]; b.juego.indice_juego=0
b.juego.escuchar_voz=lambda: [x for x in filas if x["frase"]=="perro"][0]["texto_normalizado"]
DICHO.clear(); t=time.perf_counter(); r=b.juego.ejecutar_turno(); extra["JUEGO:respuesta 'perro' a '¿cómo se dice perro?'"]=(" | ".join(DICHO)+f" -> {r}", round(time.perf_counter()-t,3))
for k,v in extra.items(): print("[EXTRA]",k,"=>",v)
json.dump({"filas":filas,"extra":extra,"llamadas":LLAMADAS,"t_whisper_carga":t_wload},open(f"{OUT}/cadena.json","w"),ensure_ascii=False,indent=1)
print("LLAMADAS EN LÍNEA:",LLAMADAS)
