import sys, json, time, urllib.parse; sys.path.insert(0,'.')
from capturar import *
s=S()
base=dict(none=False, running=True, state="MENU", phase="ESPERANDO", content="", translation="", result=None, fail_status=False, fail_card=False)
def F(**k): d=dict(base); d.update(k); return d
def P(tag, x): print(tag, json.dumps(x, ensure_ascii=False))
# 1) fallo /api/card con contenido Allin tuta
i=run(s,"falla_api_card", fake=F(state="CONVERSAR", phase="HABLANDO", content="Allin tuta", fail_card=True)); P("card_falla", [i["content"], i["title"], i["meaning"], i["example"]])
i=run(s,"card_ok_allin_tuta", fake=F(state="CONVERSAR", phase="HABLANDO", content="Allin tuta", fail_card=False)); P("card_ok", [i["content"], i["title"], i["meaning"], i["example"]])
# 2) fallo /api/status (HTTP 500)
i=run(s,"falla_api_status_500", fake=F(fail_status=True)); P("status500", {k:i[k] for k in ("state","label","activity","message","content","secondary","updated","visual","phase","offline")})
# 3) recuperacion: pagina abierta, se quita la falla y se espera el siguiente ciclo
setfake(**F(fail_status=False, state="TRADUCIR", phase="PENSANDO", content="Allin p'unchay"))
t0=time.time(); cambios=[]
while time.time()-t0<12:
    st=s.js("return document.querySelector('#state-label').textContent+' | '+document.querySelector('#content-main').textContent")
    cambios.append((round(time.time()-t0,1), st)); time.sleep(1)
P("recuperacion", cambios)
s.shot(EV+"02_recuperacion_tras_falla.png")
# 4) ciclo de 5 s: cambio de fase con la pagina abierta
setfake(**F(state="JUEGO", phase="CELEBRANDO", content="¿Cómo se dice, perro, en quechua?", translation="Allqu"))
t0=time.time(); cambios=[]
while time.time()-t0<7:
    cambios.append((round(time.time()-t0,1), s.js("return document.body.dataset.phase+' | '+document.querySelector('#content-translation').textContent"))); time.sleep(0.5)
P("latencia", cambios)
# 5) theme soft
run(s,"theme_soft_ESPERANDO", fake=F(), query="?theme=soft")
run(s,"theme_soft_SIN_CONEXION", fake=F(none=True), query="?theme=soft")
# 6) 390x844 con iframe (Firefox no baja de 500 px de ancho)
for (w,h,name) in [(390,844,"ESPERANDO"),(390,844,"SIN_CONEXION")]:
    setfake(**(F(none=True) if name=="SIN_CONEXION" else F()))
    s.size(700,1000)
    html=f'<html><body style="margin:0;background:#000"><iframe id="f" src="{APP}/" style="border:0;width:{w}px;height:{h}px"></iframe></body></html>'
    s.go("data:text/html;charset=utf-8,"+urllib.parse.quote(html))
    time.sleep(2.5)
    el=call("POST",f"/session/{s.id}/element",{"using":"css selector","value":"#f"})
    eid=list(el.values())[0]
    call("POST",f"/session/{s.id}/frame",{"id":el})
    info=s.js(INFO)
    call("POST",f"/session/{s.id}/frame/parent",{})
    v=call("GET",f"/session/{s.id}/element/{eid}/screenshot")
    import base64; open(EV+f"02_tam_390x844_iframe_{name}.png","wb").write(base64.b64decode(v))
    P(f"iframe390_{name}", {k:info[k] for k in ("vp","doc","bodyOverflow","solapes","textoCortado","rect","h1font","smallest","content")})
s.quit()
