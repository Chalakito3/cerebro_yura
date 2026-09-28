"""Grupo 4b: 4 llamadas REALES a Groq (cuota: máx. 25 por subagente).
La clave se carga con cargar_archivo_claves() del propio proyecto y NUNCA se imprime."""
from comun import *  # noqa
import os
import main_robot
import conversacion
import traductor
from groq import Groq

main_robot.cargar_archivo_claves()
assert os.environ.get("GROQ_API_KEY"), "sin clave"
cliente = Groq(api_key=os.environ["GROQ_API_KEY"])
conn = conexion_copia("g04b.db")
conversacion._conexion_vocabulario = conn
LLAMADAS = 0


def real(fn):
    global LLAMADAS
    LLAMADAS += 1
    return fn()


caso("YURA-EXT-450", "traductor", "Groq REAL: palabra que no está en la BD", "helicóptero",
     "NO_ENCONTRADO (no inventar)", lambda: real(lambda: traductor.traducir_online("helicóptero", cliente, conn)),
     lambda x: ("OK" if x is None else "OBSERVACION", f"devolvió {x!r} (None = NO_ENCONTRADO)"))
caso("YURA-EXT-451", "traductor", "Groq REAL: palabra inventada", "xqzv blorf",
     "NO_ENCONTRADO", lambda: real(lambda: traductor.traducir_online("xqzv blorf", cliente, conn)),
     lambda x: ("OK" if x is None else "FALLA", f"devolvió {x!r}"))
caso("YURA-EXT-452", "traductor", "Groq REAL: texto de 100.000 caracteres", "'palabra '*12500",
     "rechazo local antes de enviar", lambda: real(lambda: traductor.traducir_online("palabra " * 12500, cliente, conn)),
     lambda x: ("FALLA", f"devolvió {str(x)[:120]!r}; ver log [ERROR GROQ] arriba"))
conversacion.cancelar_sesion_educativa()
caso("YURA-EXT-453", "conversacion", "Groq REAL: pedir formato Markdown", "Dame una lista con viñetas y negritas de 5 colores en quechua",
     "sin Markdown (lo pide el prompt)",
     lambda: real(lambda: conversacion.procesar_entrada(
         "Dame una lista con viñetas y negritas de 5 colores en quechua", cliente, [])),
     lambda x: (("FALLA" if any(s in x["respuesta"] for s in ("**", "\n-", "\n*", "1.")) else "OK"),
                f"{x['respuesta'][:300]!r}"))
print("LLAMADAS REALES A GROQ EN ESTE SCRIPT:", LLAMADAS)
resumen()
volcar_matriz("../05_g04b_matriz.md")
