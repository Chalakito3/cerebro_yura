"""Exporta o reconstruye el diccionario de Yura desde un archivo SQL de texto.

diccionario.db no se guarda en Git (.gitignore ignora *.db). Su contenido se
guarda en basedatos/diccionario_semilla.sql, que sí se puede versionar.

Uso:
    python basedatos/crear_diccionario.py --exportar   # diccionario.db -> semilla .sql
    python basedatos/crear_diccionario.py              # crea diccionario.db si no existe
    python basedatos/crear_diccionario.py --forzar     # lo recrea (guarda respaldo antes)
"""
import os
import shutil
import sqlite3
import sys
from datetime import datetime

CARPETA = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(CARPETA)
RUTA_DB = os.path.join(RAIZ, "diccionario.db")
RUTA_SEMILLA = os.path.join(CARPETA, "diccionario_semilla.sql")


def exportar(ruta_db=RUTA_DB, ruta_semilla=RUTA_SEMILLA):
    with sqlite3.connect(f"file:{ruta_db}?mode=ro", uri=True) as conexion:
        # Las grabaciones de la docente (y lo aprendido de ellas) no van en la semilla: sus audios
        # están en basedatos/pronunciaciones/, que no se versiona.
        lineas = [linea for linea in conexion.iterdump() if "pronunciaciones_" not in linea]
    with open(ruta_semilla, "w", encoding="utf-8", newline="") as salida:
        salida.write("-- Diccionario de Yura (quechua boliviano). Generado por basedatos/crear_diccionario.py\n")
        salida.write("\n".join(lineas) + "\n")
    return len(lineas)


def crear(ruta_db=RUTA_DB, ruta_semilla=RUTA_SEMILLA, forzar=False):
    if os.path.exists(ruta_db):
        if not forzar:
            return False
        respaldo = os.path.join(CARPETA, f"diccionario_respaldo_{datetime.now():%Y%m%d_%H%M%S}.db")
        shutil.copy2(ruta_db, respaldo)
        os.remove(ruta_db)
    with open(ruta_semilla, encoding="utf-8", newline="") as entrada:
        script = entrada.read()
    with sqlite3.connect(ruta_db) as conexion:
        conexion.executescript(script)
    return True


if __name__ == "__main__":
    if "--exportar" in sys.argv:
        print(f"Semilla exportada: {exportar()} sentencias -> {RUTA_SEMILLA}")
    elif crear(forzar="--forzar" in sys.argv):
        print(f"Diccionario creado desde la semilla: {RUTA_DB}")
    else:
        print("diccionario.db ya existe; use --forzar para recrearlo.")
