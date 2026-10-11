"""Mide cuánto entiende Vosk las palabras de la docente dichas de otras formas.

Cada grabación de la docente se escucha tal cual y con cambios que imitan a
otras personas del aula. Son cambios DISTINTOS a los que se usan para
aprender (aprender_de_audios.py --vosk --variaciones), para no medir con lo
mismo que se aprendió. Una palabra cuenta como entendida si el juego la
aceptaría (pronunciaciones.respuesta_aceptada).

Uso:  python basedatos/medir_escucha_vosk.py
"""
import os
import sys
import time

CARPETA = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(CARPETA)
sys.path.insert(0, RAIZ)
sys.path.insert(0, CARPETA)

import pronunciaciones  # noqa: E402
import texto as texto_util  # noqa: E402
from aprender_de_audios import audio_para_vosk, escuchar_vosk  # noqa: E402

# nombre: (filtro de ffmpeg, ruido rosa)
PRUEBAS = {
    "tal cual": (None, 0.0),
    "voz de niño": ("rubberband=pitch=1.45,atempo=1.05", 0.0),
    "voz grave": ("rubberband=pitch=0.85", 0.0),
    "aula ruidosa": ("rubberband=pitch=1.15", 0.04),
    "rápido y agudo": ("atempo=1.25,rubberband=pitch=1.2", 0.0),
}


def medir(modelo, informar=print):
    grabaciones = [g for g in pronunciaciones.grabaciones()
                   if os.path.exists(os.path.join(pronunciaciones.CARPETA_AUDIOS, os.path.basename(g["archivo"])))]
    resultado = {}
    for nombre, (filtro, ruido) in PRUEBAS.items():
        bien = 0
        for grabacion in grabaciones:
            ruta = os.path.join(pronunciaciones.CARPETA_AUDIOS, os.path.basename(grabacion["archivo"]))
            escuchado = escuchar_vosk(modelo, audio_para_vosk(ruta, filtro, ruido))
            afinado = texto_util.normalizar(pronunciaciones.afinar_vosk(escuchado))
            bien += bool(pronunciaciones.respuesta_aceptada(afinado, grabacion["palabra_frase"]))
        resultado[nombre] = (bien, len(grabaciones))
        informar(f"  {nombre:15}: {bien}/{len(grabaciones)} = {100 * bien / len(grabaciones):.0f} %")
    total_bien = sum(b for b, _ in resultado.values())
    total = sum(t for _, t in resultado.values())
    informar(f"  {'PROMEDIO':15}: {100 * total_bien / total:.0f} %")
    return resultado


if __name__ == "__main__":
    from vosk import Model, SetLogLevel

    SetLogLevel(-1)
    inicio = time.time()
    medir(Model(os.path.join(RAIZ, "model")), informar=lambda t: print(t, flush=True))
    print(f"({time.time() - inicio:.0f} s)")
