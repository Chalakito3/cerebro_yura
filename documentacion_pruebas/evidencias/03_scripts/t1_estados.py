import random
from harness import make_brain, fake_groq, paso, S, conversacion

COMANDOS = ["", "hola", "preséntate", "silencio", "cállate", "espera", "apagar",
            "salir", "adiós", "terminar", "menú", "volver", "despierta",
            "traducir", "conversar", "jugar", "enséñame quechua", "otra vez",
            "¿cómo se dice perro?"]
ESTADOS = [S.MENU, S.CONVERSAR, S.JUEGO, S.TRADUCIR, S.SILENCIO]

print("| Estado inicial | Comando dicho | Estado final | running | Primera frase de Yura (recortada) |")
print("|---|---|---|---|---|")
for est in ESTADOS:
    for cmd in COMANDOS:
        random.seed(1)
        conversacion.cancelar_sesion_educativa()
        groq, _ = fake_groq()
        b = make_brain(est, [cmd], groq=groq)
        if est == S.JUEGO:
            b.juego.reiniciar()
        r = paso(b)
        dichos = [c.args[0] for c in b.hw.hablar.call_args_list]
        # En JUEGO la primera frase es la pregunta; mostramos la reacción (2ª)
        if est == S.JUEGO and len(dichos) > 1:
            frase = dichos[1]
        else:
            frase = dichos[0] if dichos else "(nada)"
        extra = " [bucle traductor sigue esperando]" if r == "sin_mas_entradas" else ""
        print(f"| {est} | \"{cmd}\" | {b.state}{extra} | {b.running} | {frase[:70]} |")
