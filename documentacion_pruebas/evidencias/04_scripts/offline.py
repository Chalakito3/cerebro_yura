import os,sys,time,sqlite3,subprocess,threading,socket
PROJ="/home/yura/Proyecto Yura /cerebro_yura"; sys.path.insert(0,PROJ); os.chdir(PROJ)
MODO=sys.argv[1]; WAV=sys.argv[2]
if MODO=="colgado":
    # proxy local que acepta conexiones y nunca responde (internet "colgado")
    srv=socket.socket(); srv.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1); srv.bind(("127.0.0.1",18999)); srv.listen(50)
    conns=[]
    threading.Thread(target=lambda:[conns.append(srv.accept()) for _ in iter(int,1)],daemon=True).start()
    os.environ["HTTPS_PROXY"]=os.environ["HTTP_PROXY"]="http://127.0.0.1:18999"
import main_robot, conversacion, traductor
main_robot.cargar_archivo_claves()
from gemini_transcriber import GeminiTranscriber
db=sqlite3.connect("file:diccionario.db?mode=ro",uri=True,check_same_thread=False); conversacion._conexion_vocabulario=db
def medir(nombre,f,limite=100):
    res={}
    def run():
        t=time.perf_counter()
        try: res["v"]=f()
        except Exception as e: res["v"]=f"EXCEPCION {type(e).__name__}: {str(e)[:120]}"
        res["t"]=time.perf_counter()-t
    th=threading.Thread(target=run,daemon=True); th.start(); th.join(limite)
    if th.is_alive(): print(f"[{MODO}] {nombre}: SIGUE BLOQUEADO tras {limite} s"); return
    print(f"[{MODO}] {nombre}: {res['v']!r} ({res['t']:.2f}s)")
g=GeminiTranscriber()
medir("Gemini transcribir",lambda:g.transcribir(WAV))
print(f"[{MODO}] Gemini disponible después del fallo: {g.disponible}")
from groq import Groq
cli=Groq(api_key=os.environ["GROQ_API_KEY"])
medir("Groq conversación ('imaynalla kachkanki')",lambda:conversacion.procesar_entrada("imaynalla kachkanki",cli,[]))
medir("Groq traductor online ('computadora')",lambda:traductor.traducir_online("computadora",cli,db))
medir("Traductor local ('perro')",lambda:traductor.buscar_traduccion_local("perro",db))
if MODO=="sin_red":
    import whisper
    medir("Whisper local",lambda:whisper.load_model("base").transcribe(WAV,language="es",fp16=False)["text"])
    real=subprocess.run; REG=[]
    def run(cmd,*a,**k):
        t=time.perf_counter(); r=real(cmd,*a,**k); REG.append((os.path.basename(cmd[0]) if isinstance(cmd,list) else cmd,r.returncode,round(time.perf_counter()-t,2))); return r
    main_robot.subprocess.run=run
    hw=main_robot.HardwareInterface(None)
    medir("hablar() sin internet",lambda:hw.hablar("Prueba sin internet."))
    for x in REG: print("    ",x)
