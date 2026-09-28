import sys, json, time, urllib.parse, base64; sys.path.insert(0,'.')
from capturar import *
s=S()
L=("Hoy vamos a practicar los colores del arco iris, los números del uno al diez y los nombres de los animales de la granja; "
   "después repasaremos las partes del cuerpo y las frutas del mercado, para que al final de la semana puedas presentarte "
   "con tu nombre, tu edad y tu comida favorita delante de toda la clase.")
d=dict(none=False, running=True, state="CONVERSAR", phase="HABLANDO", content=L, translation="", result=None, fail_status=False, fail_card=False)
for w,h in [(1024,600),(800,480)]:
    i=run(s, f"tam_{w}x{h}_texto_largo_300", size=(w,h), fake=d)
    i=run(s, f"tam_{w}x{h}_texto_largo_300_pagina_completa", size=(w,h), fake=d, full=True)
setfake(**d); s.size(700,1000)
html=f'<html><body style="margin:0;background:#000"><iframe id="f" src="{APP}/" style="border:0;width:390px;height:844px"></iframe></body></html>'
s.go("data:text/html;charset=utf-8,"+urllib.parse.quote(html)); time.sleep(2.5)
el=call("POST",f"/session/{s.id}/element",{"using":"css selector","value":"#f"}); eid=list(el.values())[0]
call("POST",f"/session/{s.id}/frame",{"id":el}); info=s.js(INFO)
sc=s.js("const h=document.querySelector('.hero'); return {heroScrollH:h.scrollHeight, heroClientH:h.clientHeight, heroOverflow:getComputedStyle(h).overflowY}")
call("POST",f"/session/{s.id}/frame/parent",{})
open(EV+"02_tam_390x844_iframe_texto_largo_300.png","wb").write(base64.b64decode(call("GET",f"/session/{s.id}/element/{eid}/screenshot")))
print(json.dumps({"captura":"02_tam_390x844_iframe_texto_largo_300.png","vp":info["vp"],"doc":info["doc"],"bodyOverflow":info["bodyOverflow"],"rect":info["rect"],"textoCortado":info["textoCortado"],**sc}, ensure_ascii=False))
s.quit()
