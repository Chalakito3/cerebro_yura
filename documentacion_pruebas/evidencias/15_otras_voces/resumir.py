"""Resume los resultados_*.jsonl en resumen.txt."""
import glob, json, os
from collections import defaultdict
AQUI = os.path.dirname(os.path.abspath(__file__))
filas = []
for ruta in sorted(glob.glob(os.path.join(AQUI, "resultados_*.jsonl"))):
    with open(ruta) as f:
        filas += [json.loads(l) for l in f]
voces = sorted({d["voz"] for d in filas})
lineas = []
def p(a, b):
    return f"{a}/{b} = {100 * a / b:.0f} %" if b else "-"
def bloque(titulo, sub):
    lineas.append(titulo)
    for sit in ("juego", "menu"):
        s = [d for d in sub if d["situacion"] == sit]
        n = len(s)
        if not n:
            continue
        sin = sum(d["sin_aprendido"] for d in s); con = sum(d["con_aprendido"] for d in s)
        solo_ap = sum(d["con_aprendido"] and not d["sin_aprendido"] for d in s)
        fs = sum(bool(d["falsos_sin"]) for d in s); fc = sum(bool(d["falsos_con"]) for d in s)
        pares = sum(len(d["otras_revisadas"]) for d in s)
        fpc = sum(len(d["falsos_con"]) for d in s); fps = sum(len(d["falsos_sin"]) for d in s)
        seg = sum(d["segundos"] for d in s)
        lineas.append(f"  {sit:5} evaluador sin aprendido {p(sin, n)} | con aprendido {p(con, n)} | ganados solo por lo aprendido {solo_ap}"
                      f" | falsos positivos: pares sin {fps}/{pares}, con {fpc}/{pares} (audios afectados sin {fs}, con {fc})"
                      f" | tiempo {seg:.0f} s, {seg / n:.1f} s por audio")
        if sit == "menu":
            bs = sum(d["busqueda_sin"]["correcta"] for d in s); bc = sum(d["busqueda_con"]["correcta"] for d in s)
            os_ = sum(d["busqueda_sin"]["otra_palabra"] for d in s); oc = sum(d["busqueda_con"]["otra_palabra"] for d in s)
            am = sum(d["busqueda_con"]["ambiguo"] for d in s)
            lineas.append(f"        búsqueda en consultas: correcta sin aprendido {p(bs, n)} | con aprendido {p(bc, n)}"
                          f" | encuentra OTRA palabra: sin {os_}, con {oc} | ambigua (con) {am}")
bloque("TOTAL (todas las voces)", filas)
for v in voces:
    bloque(f"VOZ {v}", [d for d in filas if d["voz"] == v])
lineas.append("\nFALSOS POSITIVOS CON LO APRENDIDO (audio de X aceptado como Y):")
for d in filas:
    extra = [o for o in d["falsos_con"] if o not in d["falsos_sin"]]
    if d["falsos_con"]:
        lineas.append(f"  {d['voz']} {d['situacion']}: «{d['transcripcion']}» ({d['palabra']}) aceptado como {d['falsos_con']}"
                      f"{' — nuevos por lo aprendido: ' + str(extra) if extra else ''}")
for sit in ("menu",):
    for d in filas:
        if d["situacion"] == sit and d["busqueda_con"]["otra_palabra"]:
            lineas.append(f"  búsqueda {d['voz']}: «{d['transcripcion']}» ({d['palabra']}) -> {d['busqueda_con']['quechua']}")
lineas.append("\nPALABRAS POR NÚMERO DE RECONOCIMIENTOS CON APRENDIDO (de voces x situaciones):")
por = defaultdict(list)
for d in filas:
    por[d["palabra"]].append(d)
total_c = len(voces) * 2
nunca, pocas = [], []
for palabra, ds in sorted(por.items()):
    c = sum(d["con_aprendido"] for d in ds)
    detalle = "; ".join(f"{d['voz'].split('-')[1]}/{d['situacion']}: «{d['transcripcion']}»" for d in ds)
    nv = ds[0]["n_variantes"]
    if c == 0:
        nunca.append(f"  {palabra} (variantes aprendidas: {nv}): {detalle}")
    elif c <= total_c // 2:
        pocas.append(f"  {palabra} {c}/{len(ds)} (variantes: {nv}): {detalle}")
lineas.append(f"Nunca reconocidas ({len(nunca)}):"); lineas += nunca
lineas.append(f"Reconocidas en la mitad o menos ({len(pocas)}):"); lineas += pocas
texto = "\n".join(lineas)
open(os.path.join(AQUI, "resumen.txt"), "w").write(texto + "\n")
print(texto)
