"""Vuelve a elegir la escritura para la voz con las reglas actuales
(aprender_pronunciacion.candidata_permitida), usando las mediciones ya hechas
(documentacion_pruebas/evidencias/16_pronunciacion_voz/resultados.csv), sin
repetir el entrenamiento. Regenera el audio "ahora" de las que cambian.

Uso:  python basedatos/reelegir_pronunciacion.py
"""
import csv
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import aprender_pronunciacion as aprender  # noqa: E402
import pronunciaciones  # noqa: E402


def leer_pruebas(celda):
    puntajes, entendidas = {}, {}
    for parte in celda.split(" | "):
        opcion, _, valor = parte.rpartition("=")
        entendidas[opcion] = not valor.endswith("*")
        puntajes[opcion] = float(valor.rstrip("*"))
    return puntajes, entendidas


def main():
    ruta = os.path.join(aprender.CARPETA_EVIDENCIAS, "resultados.csv")
    with open(ruta, encoding="utf-8") as entrada:
        filas = list(csv.reader(entrada))
    cabecera, filas = filas[0], filas[1:]
    cambios = []
    for fila in filas:
        palabra, anterior = fila[0], fila[1]
        puntajes, entendidas = leer_pruebas(fila[7])
        if palabra not in puntajes:
            continue
        mejor = aprender.elegir(palabra, puntajes, entendidas)
        if mejor == anterior or pronunciaciones.voz_de(palabra)[1]:
            continue
        with pronunciaciones._conectar() as conexion:
            conexion.execute(
                f"UPDATE {pronunciaciones.TABLA_VOZ} SET texto_para_voz = ?, parecido = ?, se_entiende = ?, fecha = ? "
                "WHERE palabra_frase = ?",
                (mejor, puntajes[mejor], int(entendidas[mejor]), datetime.now().isoformat(timespec="seconds"), palabra),
            )
        base = os.path.join(aprender.CARPETA_EVIDENCIAS, aprender._nombre_archivo(palabra))
        aprender.voz_de_yura(mejor, base + "_3_yura_ahora.wav")
        fila[1] = mejor
        fila[3] = f"{puntajes[mejor]:.3f}"
        fila[6] = "sí" if entendidas[mejor] else "no"
        cambios.append(f"{palabra}: «{anterior}» -> «{mejor}»")
    with open(ruta, "w", encoding="utf-8", newline="") as salida:
        csv.writer(salida).writerows([cabecera] + filas)
    print("\n".join(cambios) if cambios else "Sin cambios.")


if __name__ == "__main__":
    main()
