"""Utilidades comunes para las pruebas de casos extremos (subagente 5).

- Nunca abre diccionario.db real en escritura: se trabaja sobre una COPIA en el scratchpad.
- Clientes Groq falsos que simulan fallos.
- Registro de resultados en formato uniforme.
Ejecutar con: PYTHONDONTWRITEBYTECODE=1 .venv/bin/python <script>
"""
import os
import shutil
import sqlite3
import sys
import time
import traceback
from types import SimpleNamespace

PROYECTO = "/home/yura/Proyecto Yura /cerebro_yura"
SCRATCH = "/tmp/claude-1000/-home-yura-Proyecto-Yura--cerebro-yura/e3f2d4b6-69bd-45d2-b317-15177a7e8d72/scratchpad/extremos"
os.makedirs(SCRATCH, exist_ok=True)
if PROYECTO not in sys.path:
    sys.path.insert(0, PROYECTO)
sys.dont_write_bytecode = True

DB_REAL = os.path.join(PROYECTO, "diccionario.db")


def copia_bd(nombre="copia.db"):
    """Copia la BD real (leída en solo lectura) al scratchpad y devuelve la ruta."""
    destino = os.path.join(SCRATCH, nombre)
    origen = sqlite3.connect(f"file:{DB_REAL}?mode=ro", uri=True)
    dest = sqlite3.connect(destino)
    origen.backup(dest)
    origen.close()
    dest.close()
    return destino


def conexion_copia(nombre="copia.db", check_same_thread=True):
    ruta = copia_bd(nombre)
    return sqlite3.connect(ruta, check_same_thread=check_same_thread)


# ---------------------------------------------------------------- Groq falsos
class _Completions:
    def __init__(self, comportamiento):
        self.comportamiento = comportamiento
        self.llamadas = []

    def create(self, **kw):
        self.llamadas.append(kw)
        return self.comportamiento(kw)


class GroqFalso:
    def __init__(self, comportamiento):
        self.chat = SimpleNamespace(completions=_Completions(comportamiento))

    @property
    def llamadas(self):
        return self.chat.completions.llamadas


def respuesta(contenido, finish="stop"):
    return SimpleNamespace(choices=[SimpleNamespace(
        finish_reason=finish,
        message=SimpleNamespace(content=contenido))])


def groq_que_lanza(exc):
    def f(kw):
        raise exc
    return GroqFalso(f)


def groq_que_devuelve(contenido, finish="stop"):
    return GroqFalso(lambda kw: respuesta(contenido, finish))


def groq_sin_choices():
    return GroqFalso(lambda kw: SimpleNamespace(choices=[]))


# ---------------------------------------------------------------- registro
RESULTADOS = []


def caso(id_, modulo, prueba, entrada, esperado, fn, evalua=None):
    """Ejecuta fn(); evalua(resultado) -> (estado, texto). Registra la traza si falla."""
    t0 = time.perf_counter()
    try:
        res = fn()
        exc = None
    except BaseException as e:  # noqa
        res = None
        exc = e
        tb = traceback.format_exc()
    dt = time.perf_counter() - t0
    if exc is not None:
        estado, obtenido = ("ERROR", f"EXCEPCIÓN {type(exc).__name__}: {str(exc)[:200]}")
        if evalua is not None:
            try:
                estado, obtenido = evalua(exc)
            except Exception:
                pass
        print(f"\n=== {id_} TRAZA ===\n{tb}")
    else:
        if evalua is None:
            estado, obtenido = "INFO", repr(res)[:300]
        else:
            estado, obtenido = evalua(res)
    obtenido = f"{obtenido} ({dt*1000:.0f} ms)"
    RESULTADOS.append((id_, modulo, prueba, entrada, esperado, obtenido, estado))
    print(f"[{estado}] {id_} | {modulo} | {prueba} | entrada={entrada} | esperado={esperado} | obtenido={obtenido}")
    return res


def resumen():
    from collections import Counter
    c = Counter(r[6] for r in RESULTADOS)
    print("\nRESUMEN:", dict(c), "total", len(RESULTADOS))


def volcar_matriz(ruta):
    """Escribe la matriz de este script en Markdown (evidencia reproducible)."""
    with open(ruta, "w", encoding="utf-8") as fh:
        fh.write("| ID | Módulo | Prueba | Entrada | Esperado | Obtenido | Estado |\n")
        fh.write("|---|---|---|---|---|---|---|\n")
        for r in RESULTADOS:
            celdas = [str(x).replace("|", "¦").replace("\n", " ") for x in r]
            fh.write("| " + " | ".join(celdas) + " |\n")
    print(f"Matriz escrita en {ruta}")
