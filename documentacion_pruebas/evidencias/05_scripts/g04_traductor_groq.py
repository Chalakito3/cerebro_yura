"""Grupo 4: traductor y fallos de Groq (clientes falsos). Sin llamadas reales."""
from comun import *  # noqa
import conversacion
import traductor

conn = conexion_copia("g04.db")
conversacion._conexion_vocabulario = conn


def traducir_una(frase, groq, vueltas=1):
    habla, estados = [], []
    v = [0]

    def activo():
        v[0] += 1
        return v[0] <= vueltas
    ret = traductor.ejecutar_traducir(lambda: frase, habla.append, conn, groq, activo,
                                      on_status=lambda *a, **k: estados.append(k))
    return ret, habla, estados


caso("YURA-EXT-401", "traductor", "Palabra ambigua", "papa", "decir ambas opciones",
     lambda: traducir_una("papa", None),
     lambda x: ("OK" if "varios significados" in x[1][0] else "FALLA", f"{x[1]} pantalla={x[2]}"))
caso("YURA-EXT-402", "traductor", "Palabra inexistente sin Groq", "helicóptero, groq=None",
     "mensaje de no encontrado", lambda: traducir_una("helicóptero", None),
     lambda x: ("OK", f"{x[1]}"))

FALLOS = [
    ("timeout", TimeoutError("Request timed out.")),
    ("429", RuntimeError("Error code: 429 - rate_limit_exceeded")),
    ("401", RuntimeError("Error code: 401 - invalid_api_key")),
    ("conexion", ConnectionError("Connection error.")),
]
for i, (nom, exc) in enumerate(FALLOS):
    g = groq_que_lanza(exc)
    caso(f"YURA-EXT-4{3 + i:02d}", "traductor", f"Groq falla ({nom})", "helicóptero",
         "mensaje de no encontrado, sin excepción", lambda g=g: traducir_una("helicóptero", g),
         lambda x: ("OK" if x[0] == "continuar" else "FALLA", f"{x[1]}"))

RESPUESTAS = [
    ("NO_ENCONTRADO", "NO_ENCONTRADO", "no decir nada inventado"),
    ("NO_ENCONTRADO.", "NO_ENCONTRADO.", "no decir nada inventado"),
    ("NO ENCONTRADO (espacio)", "NO ENCONTRADO", "no decir nada inventado"),
    ("Lo siento, NO_ENCONTRADO", "Lo siento, NO_ENCONTRADO", "no decir nada inventado"),
    ("vacía", "", "mensaje de no encontrado"),
    ("None", None, "mensaje de no encontrado"),
    ("Markdown", "**Wasi** _(casa)_", "texto limpio en pantalla y voz"),
    ("HTML", "<b>Wasi</b><script>alert(1)</script>", "sin etiquetas"),
    ("gigante 20k", "wasi " * 4000, "limitar lo que se habla"),
    ("cortada length", "Chay wasi", "avisar/descartar respuesta cortada"),
]
for i, (nom, cont, esp) in enumerate(RESPUESTAS):
    fin = "length" if nom == "cortada length" else "stop"
    g = groq_que_devuelve(cont, fin)

    def ev(x, nom=nom):
        dicho = x[1][0] if x[1] else ""
        pantalla = x[2][0].get("content") if x[2] else None
        malo = False
        if nom.startswith(("NO ENC", "Lo siento")) and "se puede decir" in dicho:
            malo = True
        if nom in ("Markdown", "HTML") and ("<" in dicho or "**" in dicho or (pantalla and ("<" in pantalla or "*" in pantalla))):
            malo = True
        if nom == "gigante 20k" and len(dicho) > 1000:
            malo = True
        if nom == "cortada length" and "se puede decir" in dicho:
            malo = True
        return ("FALLA" if malo else "OK"), f"voz({len(dicho)} car)={dicho[:90]!r} pantalla={str(pantalla)[:60]!r}"
    caso(f"YURA-EXT-4{10 + i:02d}", "traductor", f"Groq devuelve {nom}", "helicóptero", esp,
         lambda g=g: traducir_una("helicóptero", g), ev)

g = groq_sin_choices()
caso("YURA-EXT-420", "traductor", "Groq devuelve choices=[]", "helicóptero", "sin excepción",
     lambda: traducir_una("helicóptero", g), lambda x: ("OK", f"{x[1]}"))

# texto enorme
g = groq_que_devuelve("NO_ENCONTRADO")
traducir_una("palabra " * 12500, g)
kw = g.llamadas[-1]
caso("YURA-EXT-421", "traductor", "Texto enorme a Groq", "'palabra '*12500 (100.000 car)",
     "recortar o rechazar antes de enviar",
     lambda: (len(kw["messages"][1]["content"]), len(kw["messages"][0]["content"]), kw["max_completion_tokens"]),
     lambda x: ("FALLA", f"se envían user={x[0]} car (~{x[0]//4} tokens), system={x[1]} car, max_completion_tokens={x[2]}"))

# bucle con escucha vacía
habla = []
v = [0]
t0 = time.perf_counter()
traductor.ejecutar_traducir(lambda: "", habla.append, conn, None,
                            lambda: (v.__setitem__(0, v[0] + 1) or v[0] <= 200))
caso("YURA-EXT-422", "traductor", "Bucle modo_activo con escucha siempre vacía", "'' x200 (límite del contador)",
     "tras N silencios, volver al menú o callar", lambda: (len(habla), set(habla)),
     lambda x: ("FALLA" if x[0] >= 200 else "OK",
                f"habló {x[0]} veces {x[1]}; solo se detuvo por el contador de la prueba"))

# Conversación: Groq defectuoso
CONV = [
    ("timeout", groq_que_lanza(TimeoutError("timed out"))),
    ("vacía", groq_que_devuelve("")),
    ("choices=[]", groq_sin_choices()),
    ("Markdown", groq_que_devuelve("## Colores\n- **Puka**: rojo\n- *Q'illu*: amarillo\n1. [ver](http://x.y)")),
    ("HTML", groq_que_devuelve("<p>Rimaykullayki</p><br>")),
    ("gigante", groq_que_devuelve("Rimaykullayki. " * 3000)),
    ("cortada", groq_que_devuelve("La palabra en quechua para familia es", "length")),
]
for i, (nom, g) in enumerate(CONV):
    conversacion.cancelar_sesion_educativa()

    def ev(x, nom=nom):
        r = x["respuesta"]
        malo = (nom in ("Markdown", "HTML") and any(s in r for s in ("<", "**", "##", "http"))) or \
               (nom == "gigante" and len(r) > 1000) or (nom == "cortada" and r.endswith(" es"))
        return ("FALLA" if malo else "OK"), f"({len(r)} car) {r[:100]!r}"
    caso(f"YURA-EXT-4{30 + i:02d}", "conversacion", f"Groq en conversación: {nom}", "hablemos del idioma quechua",
         "respuesta de respaldo o texto limpio y corto",
         lambda g=g: conversacion.procesar_entrada("hablemos del idioma quechua", g, []), ev)

# historial: ¿crece sin límite?
hist = []
g = groq_que_devuelve("Ari, rimasunchik.")
for _ in range(500):
    conversacion.procesar_entrada("hablemos del idioma quechua", g, hist)
caso("YURA-EXT-440", "conversacion", "Historial tras 500 turnos", "500 turnos", "historial acotado",
     lambda: (len(hist), len(g.llamadas[-1]["messages"])),
     lambda x: ("OBSERVACION" if x[0] > 100 else "OK",
                f"historial en memoria={x[0]} mensajes (crece sin límite); enviados a Groq={x[1]} (recortado a 8+2)"))

import groq as _groq
c = _groq.Groq(api_key="x")
caso("YURA-EXT-441", "traductor", "Tiempo máximo de espera del cliente Groq (configuración por defecto)",
     "Groq(api_key) como lo crea main_robot", "timeout corto (<15 s) para un robot interactivo",
     lambda: (c.timeout, c.max_retries),
     lambda x: ("FALLA", f"timeout={x[0]} max_retries={x[1]} -> hasta ~3 min bloqueado si la red cuelga (cálculo, NO medido)"))

resumen()
volcar_matriz("../05_g04_matriz.md")
