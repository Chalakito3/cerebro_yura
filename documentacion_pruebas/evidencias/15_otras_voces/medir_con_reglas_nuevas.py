import json, glob, collections, sys
sys.path.insert(0, "/home/yura/Proyecto Yura /cerebro_yura")
import pronunciaciones as p
datos=[json.loads(l) for f in glob.glob("documentacion_pruebas/evidencias/15_otras_voces/resultados_*.jsonl") for l in open(f,encoding="utf-8")]
ren={"Juk":"Uj"}
palabras=sorted({ren.get(d["palabra"],d["palabra"]) for d in datos})
acierto=collections.Counter(); total=collections.Counter(); fp=collections.Counter(); pares=collections.Counter()
for d in datos:
    pal=ren.get(d["palabra"],d["palabra"]); sit=d["situacion"]; t=d["transcripcion"]
    total[sit]+=1; acierto[sit]+=p.respuesta_aceptada(t,pal)
    for o in palabras:
        if o!=pal:
            pares[sit]+=1; fp[sit]+=p.respuesta_aceptada(t,o)
for sit in sorted(total):
    print(f"{sit}: acierto {100*acierto[sit]/total[sit]:.0f} % ({acierto[sit]}/{total[sit]}) | falsos positivos {fp[sit]} de {pares[sit]} pares")
