"""Mide cuánto de lo que Yura dice SIN internet sale con la voz de Sofía.

Recorre las frases que Yura dice sin internet (menú, juego, práctica y las
respuestas del diccionario a "¿cómo se dice...?" / "¿qué significa...?") y
cuenta cuántas están guardadas enteras o se pueden armar con oraciones
guardadas. Lo que falte se dice con una voz robótica.

Uso:  python basedatos/medir_voz_offline.py
"""
import os
import sys

CARPETA = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(CARPETA)
sys.path.insert(0, RAIZ)
sys.path.insert(0, CARPETA)

import pregenerar_voces_sofia as pre  # noqa: E402
import pronunciaciones  # noqa: E402
import voz_sofia  # noqa: E402


def guardada(frase):
    texto_voz = pre.formatear_texto_voz(pronunciaciones.texto_para_hablar(frase))
    ruta = pre.ruta_cache(texto_voz)
    if ruta and os.path.exists(ruta):
        return "entera"
    partes = voz_sofia.oraciones(texto_voz)
    if len(partes) > 1 and all(os.path.exists(pre.ruta_cache(p) or "") for p in partes):
        return "por oraciones"
    return None


if __name__ == "__main__":
    frases = pre.recolectar_frases_del_sistema()
    conteo = {"entera": 0, "por oraciones": 0, None: 0}
    faltan = []
    for frase in frases:
        estado = guardada(frase)
        conteo[estado] += 1
        if estado is None:
            faltan.append(frase)
    total = len(frases)
    con_sofia = conteo["entera"] + conteo["por oraciones"]
    print(f"Frases que Yura dice sin internet: {total}")
    print(f"  con la voz de Sofía: {con_sofia} ({100 * con_sofia / total:.0f} %)"
          f"  [enteras {conteo['entera']}, armadas por oraciones {conteo['por oraciones']}]")
    print(f"  todavía con voz robótica: {conteo[None]}")
    for frase in faltan[:10]:
        print(f"    - {frase[:80]}")
