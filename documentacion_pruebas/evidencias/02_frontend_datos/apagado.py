import sys, json, time, subprocess; sys.path.insert(0,'.')
from capturar import *
s=S(); s.size(1920,1080)
setfake(none=False, running=True, state="CONVERSAR", phase="HABLANDO", content="Allin tuta", translation="Buenas noches", result=None, fail_status=False, fail_card=False)
s.go(APP+"/"); time.sleep(2.5)
antes=s.js(INFO)
s.shot(EV+"02_antes_de_apagar_servidor.png")
print("antes", json.dumps({k:antes[k] for k in ("label","content","translation","title","meaning","updated")}, ensure_ascii=False))
import os, signal; os.kill(int(open("server.pid").read()), signal.SIGTERM)
t0=time.time(); seq=[]
while time.time()-t0<8:
    seq.append((round(time.time()-t0,1), s.js("return document.querySelector('#state').textContent+' | '+document.querySelector('#content-main').textContent+' | '+document.querySelector('#word-title').textContent+' | '+document.querySelector('#updated').textContent"))); time.sleep(1)
print("secuencia", json.dumps(seq, ensure_ascii=False))
d=s.js(INFO); s.shot(EV+"02_servidor_apagado.png")
print("despues", json.dumps({k:d[k] for k in ("state","label","activity","message","content","translation","title","meaning","example","updated","offline","visual")}, ensure_ascii=False))
s.quit()
