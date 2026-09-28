import itertools
import random
from harness import make_brain, S, conversacion, traductor, RO, norm_brain, Juego, paso

b = make_brain(S.JUEGO, [])
juego_ok = b.juego._respuesta_es_correcta
practica_ok = conversacion._evaluar_respuesta

print("## A) Casos concretos (respuesta del niño transcrita, respuesta correcta de la BD)")
casos = [
    # (dicho, correcto, esperado)
    ("allqo", "Allqo", True),
    ("allku", "Allqo", True),
    ("es allqo", "Allqo", True),
    ("se dice allqo", "Allqo", True),
    ("allqo allqo", "Allqo", True),
    ("wasi", "Wasi", True),
    ("wasa", "Wasi", False),
    ("inti", "Inti", True),
    ("anti", "Inti", False),
    ("misi", "Misi", True),
    ("mesa", "Misi", False),
    ("sacha", "Sach'a", True),
    ("uma", "Uma", True),
    ("yaku", "Uma", False),
    ("puka", "Q'ello", False),
    ("q ello", "Q'ello", True),
    ("keyo", "Q'ello", True),
    ("allin tuta", "Allin punchay", False),
    ("allin sukay", "Allin tuta", False),
    ("allin", "Allin tuta", False),
    ("allin tuta", "Allin", False),
    ("huk", "Iskay", False),
    ("nuqa", "Ñuqa", True),
    ("uqa", "Ñuqa", False),
    ("mama", "Tata", False),
    ("tata", "Mama", False),
    ("kimsa", "Kinsa", True),
    ("pichqa", "Pisqa", True),
    ("no se", "Wasi", False),
]
print("| Dicho | Correcta | Esperado | Juego (_respuesta_es_correcta) | Práctica (_evaluar_respuesta) | Estado |")
print("|---|---|---|---|---|---|")
for dicho, correcta, esp in casos:
    j = juego_ok(norm_brain(dicho), correcta)
    p = practica_ok(dicho, correcta)
    estado = "OK" if (j == esp and p == esp) else "FALLA"
    print(f"| {dicho} | {correcta} | {esp} | {j} | {p} | {estado} |")

print()
print("## B) Barrido de toda la BD: pares de palabras quechua DISTINTAS (significado español distinto) aceptadas como correctas")
regs = traductor._leer_registros_vocabulario(RO)
print("registros:", len(regs))
fp_j, fp_p = [], []
for a, c in itertools.permutations(regs, 2):
    qa, qc = a["quechua"], c["quechua"]
    if traductor._normalizar_para_comparar(qa) == traductor._normalizar_para_comparar(qc):
        continue
    if traductor._normalizar_para_comparar(a["espanol"]) == traductor._normalizar_para_comparar(c["espanol"]):
        continue
    if juego_ok(norm_brain(qa), qc):
        fp_j.append((qa, a["espanol"], qc, c["espanol"]))
    if practica_ok(qa, qc):
        fp_p.append((qa, a["espanol"], qc, c["espanol"]))
print("pares aceptados erróneamente JUEGO:", len(fp_j))
print("pares aceptados erróneamente PRACTICA:", len(fp_p))
for x in fp_j[:40]:
    print("  JUEGO acepta decir '%s' (%s) cuando la respuesta es '%s' (%s)" % x)
extra = set(fp_p) - set(fp_j)
print("  pares solo en PRACTICA:", len(extra))
for x in list(extra)[:10]:
    print("  PRACTICA acepta '%s' (%s) por '%s' (%s)" % x)

print()
print("## C) Palabras del juego: respuesta esperada según la BD")
for p in ["gato", "perro", "sol", "agua", "casa", "arbol"]:
    r = traductor.buscar_vocabulario(p, "espanol", RO)
    print(p, "->", traductor.consultar_diccionario_local(p, RO), "| ambiguo:", r["ambiguo"],
          "|", [(x["quechua"], x["espanol"]) for x in r["resultados"]][:4])

print()
print("## D) Práctica: palabras interceptadas por _responder_frase_local (no se evalúan)")
conversacion.cancelar_sesion_educativa()
for reg in regs:
    conversacion._sesion_educativa = {"registro": reg, "estado": "esperando_repeticion"}
    r = conversacion.procesar_entrada(reg["quechua"], None)
    if "Muy bien" not in r["respuesta"]:
        print(f"  Repetir correctamente '{reg['quechua']}' ({reg['espanol']}) -> {r['accion']}: {r['respuesta'][:90]}")
conversacion.cancelar_sesion_educativa()

print()
print("## E) Juego: partida completa simulada (4 preguntas) con respuestas correctas de la BD")
random.seed(3)
b = make_brain(S.JUEGO, [])
b.juego.reiniciar()
palabras = list(b.juego.palabras_partida)
resp = [traductor.consultar_diccionario_local(p, RO) for p in palabras]
b2 = make_brain(S.JUEGO, resp)
b2.juego.palabras_partida = palabras
b2.juego.indice_juego = 0
b2.juego.escuchar_voz = b2.escuchar_voz
for _ in range(5):
    paso(b2)
print("palabras:", palabras, "respuestas:", resp)
print("estado final:", b2.state, "| dichos:", [c.args[0][:40] for c in b2.hw.hablar.call_args_list])
print("web_status final:", b2.get_web_status())

print()
print("## F) Juego tras terminar: se vuelve a jugar desde MENU con 'jugar'")
b2.state = S.MENU
b2.escuchar_voz.side_effect = None
b2.escuchar_voz.return_value = "jugar"
paso(b2)
print("estado:", b2.state, "indice:", b2.juego.indice_juego, "palabras nuevas:", b2.juego.palabras_partida)
