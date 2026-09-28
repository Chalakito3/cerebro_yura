"""Grupos 2 (juego) y 3 (práctica educativa)."""
from comun import *  # noqa
import random
import sqlite3
import conversacion
import traductor
from juego import Juego
from main_robot import BrainYura

conn = conexion_copia("g02.db")
conversacion._conexion_vocabulario = conn
norm = BrainYura._normalizar_texto.__get__(object.__new__(BrainYura))
PALABRAS = ["gato", "perro", "sol", "agua", "casa", "arbol"]


def juego(respuestas, palabras=PALABRAS, consultar=None):
    habla = []
    it = iter(respuestas)
    j = Juego(palabras,
              consultar or (lambda p: traductor.consultar_diccionario_local(p, conn)),
              lambda: next(it), habla.append, lambda c: None, norm)
    return j, habla


# ---------------------------------------------------------------- Grupo 2
print("\n########## GRUPO 2: JUEGO ##########")
random.seed(1)
j, h = juego(["respuesta equivocada"] * 10)
r = [j.ejecutar_turno() for _ in range(5)]
caso("YURA-EXT-201", "juego", "Responder mal todas", "4x 'respuesta equivocada'",
     "al final informar puntaje/aciertos; no felicitar con 0 aciertos",
     lambda: (r, h[-1]),
     lambda x: ("FALLA" if "Felicidades" in x[1] else "OK", f"retornos={x[0]} último mensaje={x[1]!r}"))

random.seed(2)
j, h = juego(["mal", "salir"])
r = [j.ejecutar_turno() for _ in range(2)]
caso("YURA-EXT-202", "juego", "Responder 'salir' a mitad", "turno1 'mal', turno2 'salir'",
     "volver al menú", lambda: (r, h[-1]),
     lambda x: ("OK" if x[0][-1] == "menu" else "FALLA", f"retornos={x[0]} último={x[1]!r}"))

random.seed(3)
j, h = juego([""] * 60)
r = [j.ejecutar_turno() for _ in range(50)]
preguntas = [x for x in h if x.startswith("¿Cómo se dice")]
caso("YURA-EXT-203", "juego", "50 respuestas vacías seguidas", "'' x50",
     "tras N intentos sin respuesta, avanzar o salir al menú / silencio",
     lambda: (set(r), j.indice_juego, len(preguntas), len(set(preguntas))),
     lambda x: ("FALLA" if x[1] == 0 and x[3] == 1 else "OK",
                f"retornos={x[0]} indice={x[1]} preguntas={x[2]} (distintas={x[3]}); nunca sale"))

j, h = juego(["wasi"] * 30, palabras=["xyz", "helicoptero"], consultar=lambda p: None)
r = [j.ejecutar_turno() for _ in range(20)]
caso("YURA-EXT-204", "juego", "Lista con palabras que la BD no tiene", "palabras=['xyz','helicoptero'], BD sin ellas",
     "saltar la palabra o avisar y volver al menú",
     lambda: (set(r), j.indice_juego, len(h), h[0]),
     lambda x: ("FALLA" if x[1] == 0 else "OK",
                f"retornos={x[0]} indice={x[1]} mensajes={x[2]} ej={x[3]!r} -> bucle infinito"))

random.seed(4)
j, h = juego(["yaku"] * 10, palabras=["agua"], consultar=lambda p: traductor.consultar_diccionario_local(p, None))
j.ejecutar_turno()
caso("YURA-EXT-205", "juego", "Sin BD (conexión None): 'agua' usa mapeo de emergencia", "respuesta 'yaku'",
     "misma respuesta que la BD (Uma) o avisar que no hay BD",
     lambda: h, lambda x: ("FALLA" if "Excelente" in x[-1] else "OK", f"habló={x}"))
j, h = juego(["yaku"] * 10, palabras=["agua"])
j.ejecutar_turno()
caso("YURA-EXT-206", "juego", "Con BD: 'agua' respondiendo 'yaku'", "respuesta 'yaku'",
     "coherente con el caso sin BD", lambda: h,
     lambda x: ("OBSERVACION", f"habló={x} (con BD 'yaku' es incorrecto y sin BD es correcto)"))

for resp in ("allin tuta", "allin", "tuta", "alin tuta"):
    j, h = juego([resp], palabras=["buenas noches"])
    j.ejecutar_turno()
    caso(f"YURA-EXT-2{10 + ['allin tuta', 'allin', 'tuta', 'alin tuta'].index(resp):02d}", "juego",
         "Traducción de varias palabras (Buenas noches = Allin tuta)", repr(resp),
         "correcto solo con la frase completa (o variante fonética)", lambda h=h: h[-1],
         lambda x, resp=resp: (("OK" if ("Excelente" in x) == (resp in ("allin tuta", "alin tuta")) else "FALLA"),
                               repr(x[:60])))

j, h = juego(["x"] * 3, palabras=[])
r = j.ejecutar_turno()
caso("YURA-EXT-214", "juego", "Lista de palabras vacía", "palabras=[]", "avisar que no hay palabras",
     lambda: (r, h), lambda x: ("FALLA" if "Felicidades" in x[1][0] else "OK", f"ret={x[0]} habló={x[1]}"))

# Pares de palabras quechuas DISTINTAS de la BD que el evaluador acepta como iguales
regs = traductor._leer_registros_vocabulario(conn)
qs = sorted({r["quechua"] for r in regs if r["quechua"]})
j, _ = juego([])
pares = []
for a in qs:
    for b in qs:
        if a < b and norm(a) != norm(b) and j._respuesta_es_correcta(a, b):
            pares.append((a, b))
caso("YURA-EXT-215", "juego", "Evaluador: palabras distintas aceptadas como correctas",
     f"{len(qs)} palabras quechuas de la BD, todos los pares",
     "0 pares de palabras distintas aceptados", lambda: pares,
     lambda x: ("FALLA" if x else "OK", f"{len(x)} pares aceptados, ej: {x[:12]}"))

# ---------------------------------------------------------------- Grupo 3
print("\n########## GRUPO 3: PRÁCTICA ##########")
for i, frase in enumerate(("repite", "otra vez", "siguiente")):
    conversacion.cancelar_sesion_educativa()
    caso(f"YURA-EXT-3{i + 1:02d}", "conversacion", f"'{frase}' sin sesión activa", frase,
         "explicar que no hay práctica activa o empezar una",
         lambda f=frase: conversacion.procesar_entrada(f, None),
         lambda x: ("FALLA" if "no vendo autos" in x["respuesta"] else "OK", repr(x["respuesta"][:110])))

# BD vacía (copia con tablas vaciadas)
ruta_vacia = copia_bd("g03_vacia.db")
cv = sqlite3.connect(ruta_vacia)
for (t,) in cv.execute("select name from sqlite_master where type='table'").fetchall():
    cv.execute(f'DELETE FROM "{t}"')
cv.commit()
conversacion._conexion_vocabulario = cv
conversacion.cancelar_sesion_educativa()
caso("YURA-EXT-304", "conversacion", "Iniciar práctica con BD vacía", "enséñame quechua",
     "mensaje claro sin excepción", lambda: conversacion.procesar_entrada("enséñame quechua", None),
     lambda x: ("OK", repr(x["respuesta"])))
conversacion._conexion_vocabulario = conn

# "repite" dentro de la sesión: ¿repite la misma palabra?
random.seed(5)
distintas = 0
for _ in range(20):
    conversacion.cancelar_sesion_educativa()
    conversacion.procesar_entrada("quiero practicar", None)
    antes = conversacion._sesion_educativa["registro"]["quechua"]
    conversacion.procesar_entrada("repite", None)
    despues = conversacion._sesion_educativa["registro"]["quechua"]
    distintas += antes != despues
caso("YURA-EXT-305", "conversacion", "'repite' en sesión activa (20 intentos)", "repite",
     "repetir la MISMA palabra", lambda: distintas,
     lambda x: ("FALLA" if x else "OK", f"en {x}/20 intentos cambió a otra palabra"))


def forzar(quechua, espanol="X", categoria="saludos"):
    conversacion._sesion_educativa = {"registro": {"quechua": quechua, "espanol": espanol,
                                                   "significado": None, "categoria": categoria,
                                                   "tabla_origen": "t", "id": 1},
                                      "estado": "esperando_repeticion"}


PRUEBAS_EVAL = [
    ("Allin punchay", "allin punchay", True),
    ("Allin punchay", "alin punchai", True),     # casi correcta
    ("Allin punchay", "allin", False),           # incompleta
    ("Allin punchay", "wasi", False),            # muy distinta
    ("Tawa", "wawa", False),                     # palabra distinta (niño)
    ("Misi", "mesa", False),
    ("Allin tuta", "allin tuta", True),          # también es frase local
    ("Imaynalla", "imaynalla", True),
    ("Uma", "uma", True),
]
for k, (q, resp, esperado) in enumerate(PRUEBAS_EVAL):
    forzar(q)

    def fn(resp=resp):
        return conversacion.procesar_entrada(resp, None)

    def ev(x, esperado=esperado):
        dijo_bien = x["respuesta"].startswith("Muy bien")
        evaluo = x["respuesta"].startswith(("Muy bien", "Todavía no"))
        if not evaluo:
            return "FALLA", f"NO evaluó la respuesta: {x['respuesta'][:90]!r}"
        return ("OK" if dijo_bien == esperado else "FALLA"), repr(x["respuesta"][:80])
    caso(f"YURA-EXT-3{10 + k:02d}", "conversacion", f"Evaluar práctica de '{q}'", repr(resp),
         "Correcta" if esperado else "Incorrecta", fn, ev)

forzar("Wasi", "Casa", "elementos_casa")
caso("YURA-EXT-320", "conversacion", "Pregunta de traducción durante la práctica",
     "¿cómo se dice perro?", "responder la pregunta o aclarar que hay una práctica pendiente",
     lambda: conversacion.procesar_entrada("¿cómo se dice perro?", None),
     lambda x: ("FALLA" if x["respuesta"].startswith("Todavía no") else "OK", repr(x["respuesta"][:90])))
forzar("Wasi", "Casa", "elementos_casa")
caso("YURA-EXT-321", "conversacion", "'salir' durante la práctica", "salir", "acción menú",
     lambda: conversacion.procesar_entrada("salir", None),
     lambda x: ("OK" if x["accion"] == "menu" and conversacion._sesion_educativa is None else "FALLA", repr(x)))

resumen()
volcar_matriz("../05_g02_03_matriz.md")
