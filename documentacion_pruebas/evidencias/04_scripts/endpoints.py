import time, json, statistics, urllib.request, urllib.error
B="http://127.0.0.1:5000"
def req(path, method="GET"):
    r=urllib.request.Request(B+path, method=method, data=(b"" if method=="POST" else None))
    t=time.perf_counter()
    try:
        resp=urllib.request.urlopen(r,timeout=5); code=resp.status; body=resp.read(); ct=resp.headers.get("Content-Type")
    except urllib.error.HTTPError as e:
        code=e.code; body=e.read(); ct=e.headers.get("Content-Type")
    return code, (time.perf_counter()-t)*1000, body, ct
for path in ["/","/api/status","/api/card"]:
    ts=[]
    for i in range(10):
        c,ms,b,ct=req(path); ts.append(ms)
    print(f"{path}: codigo={c} tipo={ct} bytes={len(b)} ms min={min(ts):.1f} media={statistics.mean(ts):.1f} mediana={statistics.median(ts):.1f} max={max(ts):.1f}")
# esquema
c,ms,b,ct=req("/api/status"); d=json.loads(b)
esperado={"robot":str,"state":str,"running":bool,"activity":str,"message":str,"phase":str,"content":str,"translation":str,"result":(type(None),str),"updated_at":str}
print("status claves:",sorted(d)); 
print("status esquema OK:", set(d)==set(esperado) and all(isinstance(d[k],esperado[k]) for k in esperado))
print("status ejemplo:", json.dumps(d,ensure_ascii=False))
c,ms,b,ct=req("/api/card"); d=json.loads(b)
ok=isinstance(d.get("examples"),list) and all(set(e)=={"key","title","written","pronunciation","meaning","example"} and all(isinstance(v,str) for v in e.values()) for e in d["examples"])
print("card n=",len(d["examples"]),"esquema OK:",ok)
print("card meaning==written en:",sum(e["meaning"]==e["written"] for e in d["examples"]),"de",len(d["examples"]))
c,ms,b,ct=req("/"); html=b.decode()
print("/ contiene <title>:", html[html.find("<title>"):html.find("</title>")+8])
import re
for src in re.findall(r'(?:src|href)="([^"]+)"',html):
    if src.startswith("http"): print("  recurso externo:",src); continue
    cc,_,bb,_=req("/"+src.lstrip("/")); print("  recurso",src,cc,len(bb))
for path,m in [("/no-existe","GET"),("/api/status","POST"),("/api/card","POST"),("/api/status","PUT"),("/static/../../.env.local","GET"),("/static/..%2f..%2f.env.local","GET")]:
    c,ms,b,ct=req(path,m); print(f"{m} {path}: {c} ({ms:.1f} ms) cuerpo={b[:60]!r}")
c,ms,b,ct=req("/api/status"); print("cabeceras CORS/seguridad: se muestran abajo")
r=urllib.request.urlopen(B+"/api/status"); print(dict(r.headers))
