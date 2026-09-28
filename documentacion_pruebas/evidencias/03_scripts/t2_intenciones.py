import random
from harness import make_brain, fake_groq, paso, S, conversacion, traductor, RO, norm_brain

print("## A) Menú principal (ejecutar_menu): frase -> estado resultante")
casos_menu = [
    ("¿cómo se dice apagar en quechua?", "CONVERSAR (traducción)"),
    ("no quiero jugar", "no JUEGO"),
    ("quiero conjugar verbos en quechua", "no JUEGO"),
    ("¿cómo se dice silencio en quechua?", "CONVERSAR (traducción)"),
    ("¿cómo se dice adiós en quechua?", "CONVERSAR (traducción)"),
    ("no quiero salir", "no SILENCIO"),
    ("¿qué significa terminar?", "CONVERSAR"),
    ("juguemos", "JUEGO"),
    ("vamos a jugar", "JUEGO"),
    ("quiero platicar", "CONVERSAR"),
    ("traduce perro", "TRADUCIR o traducción"),
    ("espera un momento yura", "SILENCIO (esperado por diseño)"),
    ("yura apágate", "SALIR"),
    ("apaga", "SALIR"),
]
for frase, esperado in casos_menu:
    random.seed(1)
    conversacion.cancelar_sesion_educativa()
    g, _ = fake_groq()
    b = make_brain(S.MENU, [frase], groq=g)
    paso(b)
    d = [c.args[0] for c in b.hw.hablar.call_args_list]
    print(f"| \"{frase}\" | esperado: {esperado} | obtenido: {b.state} running={b.running} | {(d[0] if d else '(nada)')[:60]} |")

print()
print("## B) _detectar_intencion (conversacion): frase -> intención")
casos_int = [
    ("buenas noches", "conversar"),
    ("como se dice adios en quechua", "traducir"),
    ("que significa tupananchiskama", "significado"),
    ("me voy a portar bien", "conversar"),
    ("el menudo de mi abuela", "conversar"),
    ("siguiente pregunta", "conversar/repetir"),
    ("quiero conjugar verbos", "conversar"),
    ("tengo una pregunta", "conversar"),
    ("mi profesor ensena quechua", "conversar"),
    ("como se dice jugar en quechua", "traducir"),
    ("como se dice aprender en quechua", "traducir"),
    ("como se dice prueba en quechua", "traducir"),
    ("como se dice ensenar en quechua", "traducir"),
    ("como se dice practicar", "traducir"),
    ("que significa yachay", "significado"),
    ("comprueba si esta bien", "conversar"),
    ("es practicamente igual", "conversar"),
    ("nos vemos manana", "salir (aceptable)"),
    ("como se dice nos vemos", "traducir"),
    ("repite la palabra", "repetir"),
    ("hablemos de mi familia", "conversar"),
    ("el ejercito", "conversar"),
    ("dejame aprender", "aprender"),
]
for frase, esperado in casos_int:
    obt = conversacion._detectar_intencion(frase)
    ok = "OK" if obt in esperado else "FALLA"
    print(f"| \"{frase}\" | {esperado} | {obt} | {ok} |")

print()
print("## C) Modo TRADUCIR: frases que el niño quiere traducir")
for frase in ["adiós", "volver", "regresar", "menú", "salir", "terminar", "apagar la luz",
              "¿cómo se dice perro?", "perro", "no", "sí", "sol", "hola", "casa", "el perro"]:
    g, capt = fake_groq("GROQ")
    dichos = []
    entradas = [norm_brain(frase)]

    def esc():
        if not entradas:
            raise StopIteration
        return entradas.pop(0)
    try:
        r = traductor.ejecutar_traducir(esc, dichos.append, RO, g, lambda: True)
    except (StopIteration, RuntimeError):
        r = "sigue en TRADUCIR"
    print(f"| \"{frase}\" | resultado={r} | {dichos[0][:110] if dichos else ''} | groq_llamado={bool(capt)} |")

print()
print("## D) Modo SILENCIO: frases de aula que despiertan a Yura")
for frase in ["niños, silencio por favor", "vamos a volver a clase", "vuelve a tu asiento",
              "despierta a tu compañero", "¿puedes hablar más fuerte?", "apagar", "yura apagar"]:
    b = make_brain(S.SILENCIO, [frase])
    paso(b)
    print(f"| \"{frase}\" | estado={b.state} running={b.running} |")
