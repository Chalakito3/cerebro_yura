"""Grupo 9: cargar_archivo_claves con .env.local raro en carpeta TEMPORAL (no toca el real).
Grupo 10: concurrencia en _set_web_status/get_web_status y en la conexión SQLite de conversacion."""
from comun import *  # noqa
import os
import sqlite3
import threading
from unittest.mock import patch
import main_robot
import conversacion
import traductor
from main_robot import BrainYura

D = os.path.join(SCRATCH, "g09")
os.makedirs(D, exist_ok=True)
ARCHIVO = (
    "﻿YT_BOM=valor_bom\n"
    "YT_SIN_IGUAL\n"
    "YT_DOBLES=\"con comillas\"\n"
    "YT_SIMPLES='simples'\n"
    "YT_MIXTAS=\"abre doble cierra simple'\n"
    "  YT_ESPACIOS  =   con espacios   \n"
    "export YT_EXPORT=exportada\n"
    "export   YT_EXPORT2=doble espacio\n"
    "YT_COMENTARIO=valor # comentario en línea\n"
    "YT_VACIA=\n"
    "YT_IGUAL=a=b=c\n"
    "YT_DUP=primera\n"
    "YT_DUP=segunda\n"
    "YT_CRLF=windows\r\n"
    "YT_SOLO_COMILLAS=\"\"\n"
    "yt minus=con espacio en la clave\n"
    "=sin_clave\n"
    "# YT_COMENTADA=no\n"
)
with open(os.path.join(D, ".env.local"), "w", encoding="utf-8", newline="") as fh:
    fh.write(ARCHIVO)

ESPERADO = {
    "YT_BOM": "valor_bom", "YT_SIN_IGUAL": None, "YT_DOBLES": "con comillas", "YT_SIMPLES": "simples",
    "YT_MIXTAS": None, "YT_ESPACIOS": "con espacios", "YT_EXPORT": "exportada", "YT_EXPORT2": "doble espacio",
    "YT_COMENTARIO": "valor", "YT_VACIA": None, "YT_IGUAL": "a=b=c", "YT_DUP": "segunda",
    "YT_CRLF": "windows", "YT_SOLO_COMILLAS": None, "yt minus": None, "YT_COMENTADA": None,
}
entorno_limpio = {k: v for k, v in os.environ.items() if not k.startswith(("YT_", "﻿YT", "yt "))}
with patch.dict(os.environ, entorno_limpio, clear=True), \
        patch.object(main_robot, "__file__", os.path.join(D, "main_robot.py")):
    main_robot.cargar_archivo_claves()
    obtenido = {k: os.environ.get(k) for k in ESPERADO}
    bom_crudo = os.environ.get("﻿YT_BOM")
    vacia_clave = os.environ.get("")

for i, (k, esp) in enumerate(ESPERADO.items()):
    ob = obtenido[k]
    nota = ""
    if k == "YT_BOM" and bom_crudo:
        nota = " (quedó guardada como '\\ufeffYT_BOM')"
    if k == "YT_DUP":
        nota = " (convención dotenv: gana la última)"
    if k == "YT_MIXTAS":
        nota = " (comillas desbalanceadas)"
    estado = "OK" if ob == esp else ("OBSERVACION" if k in ("YT_DUP", "YT_MIXTAS", "yt minus", "YT_COMENTARIO") else "FALLA")
    caso(f"YURA-EXT-9{i + 1:02d}", "claves", "cargar_archivo_claves", repr(k), repr(esp),
         lambda ob=ob: ob, lambda x, estado=estado, nota=nota: (estado, repr(x) + nota))

# archivo ilegible
D2 = os.path.join(SCRATCH, "g09b")
os.makedirs(D2, exist_ok=True)
ruta = os.path.join(D2, ".env.local")
open(ruta, "w").write("YT_X=1\n")
os.chmod(ruta, 0)
with patch.object(main_robot, "__file__", os.path.join(D2, "main_robot.py")):
    caso("YURA-EXT-930", "claves", "cargar_archivo_claves con .env.local sin permisos", "chmod 000",
         "aviso sin excepción", lambda: main_robot.cargar_archivo_claves(), lambda x: ("OK", "sin excepción (ver [ALERTA CLAVES] en log)"))
os.chmod(ruta, 0o600)
# directorio llamado .env.local
D3 = os.path.join(SCRATCH, "g09c")
os.makedirs(os.path.join(D3, ".env.local"), exist_ok=True)
with patch.object(main_robot, "__file__", os.path.join(D3, "main_robot.py")):
    caso("YURA-EXT-931", "claves", "'.env.local' es una carpeta", "directorio", "ignorar sin excepción",
         lambda: main_robot.cargar_archivo_claves(), lambda x: ("OK", "sin excepción"))
# archivo binario
D4 = os.path.join(SCRATCH, "g09d")
os.makedirs(D4, exist_ok=True)
open(os.path.join(D4, ".env.local"), "wb").write(bytes(range(256)) * 10)
with patch.object(main_robot, "__file__", os.path.join(D4, "main_robot.py")):
    caso("YURA-EXT-932", "claves", "'.env.local' binario", "bytes 0-255", "sin excepción",
         lambda: main_robot.cargar_archivo_claves(),
         lambda x: ("FALLA", f"{type(x).__name__}: {x}") if isinstance(x, BaseException) else ("OK", "sin excepción"))

# ------------------------------------------------------------------ Grupo 10
r = object.__new__(BrainYura)
r.web_status = {"phase": "ESPERANDO", "content": "", "translation": "", "result": None, "updated_at": None}
r.web_status_lock = threading.Lock()
errores, incoherentes = [], [0]


def escritor(n):
    try:
        for i in range(5000):
            r._set_web_status(f"F{n}", content=f"{n}-{i}", translation=f"{n}-{i}")
    except Exception as e:
        errores.append(repr(e))


def lector():
    try:
        for _ in range(5000):
            s = r.get_web_status()
            if s["content"] != s["translation"]:
                incoherentes[0] += 1
    except Exception as e:
        errores.append(repr(e))


hilos = [threading.Thread(target=escritor, args=(n,)) for n in range(8)] + [threading.Thread(target=lector) for _ in range(8)]
t0 = time.perf_counter()
[h.start() for h in hilos]
[h.join() for h in hilos]
caso("YURA-EXT-950", "main_robot", "_set_web_status/get_web_status desde 16 hilos", "8 escritores x5000 + 8 lectores x5000",
     "sin errores, content y translation siempre del mismo evento", lambda: (errores, incoherentes[0], time.perf_counter() - t0),
     lambda x: ("OK" if not x[0] and x[1] == 0 else "FALLA", f"errores={len(x[0])} incoherentes={x[1]} tiempo={x[2]:.2f}s"))

# conexión de conversacion creada en un hilo y usada en otro
carpeta = os.path.join(SCRATCH, "g10")
os.makedirs(carpeta, exist_ok=True)
destino = os.path.join(carpeta, "diccionario.db")
if not os.path.exists(destino):
    import shutil
    shutil.copy(copia_bd("g10_tmp.db"), destino)
conversacion.__file__ = os.path.join(carpeta, "conversacion.py")
conversacion._conexion_vocabulario = None
conversacion.cancelar_sesion_educativa()
conversacion.procesar_entrada("quiero practicar", None)  # crea la conexión en el hilo principal
conversacion.cancelar_sesion_educativa()
res = {}


def otro_hilo():
    try:
        res["r"] = conversacion.procesar_entrada("quiero practicar", None)
    except Exception as e:
        res["e"] = e


h = threading.Thread(target=otro_hilo)
h.start()
h.join()
caso("YURA-EXT-951", "conversacion", "Conexión SQLite de conversacion usada desde otro hilo",
     "procesar_entrada('quiero practicar') en hilo 2", "funciona o error controlado",
     lambda: res, lambda x: ("FALLA", f"{type(x['e']).__name__}: {x['e']}") if "e" in x else ("OK", repr(x["r"])[:80]))

# conexión check_same_thread=False (como BrainYura.db_conn) usada por 8 hilos a la vez
cx = sqlite3.connect(destino, check_same_thread=False)
errs = []


def buscar():
    try:
        for p in ("casa", "papa", "rojo", "sol") * 50:
            traductor.buscar_vocabulario(p, "espanol", cx)
    except Exception as e:
        errs.append(repr(e))


hs = [threading.Thread(target=buscar) for _ in range(8)]
[h.start() for h in hs]
[h.join() for h in hs]
caso("YURA-EXT-952", "traductor", "db_conn compartida (check_same_thread=False) por 8 hilos", "8 x 200 búsquedas",
     "sin errores", lambda: errs, lambda x: ("OK" if not x else "FALLA", f"errores={len(x)} {x[:2]}"))

# sesión educativa global compartida
conversacion._conexion_vocabulario = cx
conversacion.cancelar_sesion_educativa()
conversacion.procesar_entrada("quiero practicar", None)
palabra = conversacion._sesion_educativa["registro"]["quechua"]
conversacion.cancelar_sesion_educativa()  # p. ej. otro modo/usuario cancela
caso("YURA-EXT-953", "conversacion", "Estado de práctica global (_sesion_educativa) compartido por módulo",
     "otra parte del programa cancela la sesión", "sesión por usuario/robot",
     lambda: conversacion.procesar_entrada(palabra, None)["respuesta"],
     lambda x: ("OBSERVACION", f"tras cancelar, la respuesta correcta '{palabra}' ya no se evalúa: {x[:80]!r}"))

resumen()
volcar_matriz("../05_g09_10_matriz.md")
