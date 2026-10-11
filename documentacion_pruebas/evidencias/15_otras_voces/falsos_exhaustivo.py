"""Revisión completa (sin Whisper): cada transcripción contra TODAS las demás
palabras, y lista de lo ganado gracias a lo aprendido. Solo lectura."""
import glob, json, os, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, RAIZ)
import pronunciaciones, texto
filas = []
for ruta in sorted(glob.glob(os.path.join(AQUI, "resultados_*.jsonl"))):
    filas += [json.loads(l) for l in open(ruta)]
lista = sorted({d["palabra"] for d in filas})
var = {p: pronunciaciones.variantes(p) for p in lista}
misma = lambda a, b: texto.normalizar(a).replace("'", "") == texto.normalizar(b).replace("'", "")
out = []
print(f"Palabras: {len(lista)}; con variantes aprendidas seguras: {sum(1 for p in lista if var[p])}; variantes en total: {sum(len(v) for v in var.values())}")
for sit in ("juego", "menu"):
    s = [d for d in filas if d["situacion"] == sit]
    pares = sin = con = 0; nuevos = []
    for d in s:
        for o in lista:
            if misma(o, d["palabra"]) or not d["transcripcion"]:
                continue
            pares += 1
            a = texto.respuesta_quechua_correcta(d["transcripcion"], o)
            b = texto.respuesta_quechua_correcta(d["transcripcion"], o, var[o])
            sin += a; con += b
            if b and not a:
                nuevos.append(f"«{d['transcripcion']}» ({d['palabra']}, {d['voz']}) aceptado como {o} por la variante aprendida")
    print(f"\n{sit}: pares revisados {pares}; aceptados como otra palabra sin aprendido {sin}, con aprendido {con}")
    for n in nuevos:
        print("   NUEVO:", n)
print("\nGanados gracias a lo aprendido (evaluador):")
for d in filas:
    if d["con_aprendido"] and not d["sin_aprendido"]:
        print(f"   {d['situacion']} {d['voz']}: «{d['transcripcion']}» -> {d['palabra']}  (variantes {var[d['palabra']]})")
print("\nGanados gracias a lo aprendido (búsqueda en consultas del menú):")
for d in filas:
    if d["situacion"] == "menu" and d["busqueda_con"]["correcta"] and not d["busqueda_sin"]["correcta"]:
        print(f"   {d['voz']}: «{d['transcripcion']}» -> {d['palabra']}")
print("\nPerdidos o empeorados por lo aprendido:")
for d in filas:
    if d["sin_aprendido"] and not d["con_aprendido"]:
        print("   evaluador", d)
    if d["situacion"] == "menu" and d["busqueda_sin"]["correcta"] and not d["busqueda_con"]["correcta"]:
        print(f"   búsqueda {d['voz']}: «{d['transcripcion']}» ({d['palabra']}) -> {d['busqueda_con']}")
