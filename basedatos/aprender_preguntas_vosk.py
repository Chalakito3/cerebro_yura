"""Yura aprende cómo escribe Vosk las palabras DENTRO de las preguntas.

Dicha sola, "wasi" se reconoce; dentro de "¿Qué significa wasi?" Vosk la
escribe "daisy" o "veis y", y "¿Cómo se dice casa en quechua?" lo escribe
"como se dice que hacen quechua". Este programa dice con varias voces, para
cada palabra del diccionario:

    ¿Qué significa <quechua>?            (la parte quechua)
    ¿Cómo se dice <castellano> en quechua?  (la parte castellana)

y anota cómo escribió Vosk esa parte. Se guarda en
basedatos/mapa_preguntas_vosk.json; pronunciaciones.afinar_vosk lo usa en el
modo castellano / quechua. No se guarda lo ambiguo (la misma escritura para
dos palabras) ni lo que ya se entiende bien.

Necesita internet (voces de Edge TTS).  Uso:  python basedatos/aprender_preguntas_vosk.py
"""
import asyncio
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

CARPETA = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(CARPETA)
sys.path.insert(0, RAIZ)
sys.path.insert(0, CARPETA)

import pronunciaciones  # noqa: E402
import texto as texto_util  # noqa: E402
import traductor  # noqa: E402
from aprender_de_audios import escuchar_vosk  # noqa: E402

VOCES = ("es-BO-SofiaNeural", "es-PE-AlexNeural", "es-MX-DaliaNeural", "es-PE-CamilaNeural")
_HUECO_QUECHUA = re.compile(r"^que significa\s+(.+)$")
_HUECO_CASTELLANO = re.compile(r"^como se dice\s+(.+?)(?:\s+en quechua)?$")


def _audio(frase, voz):
    import edge_tts

    with tempfile.TemporaryDirectory() as carpeta:
        mp3 = os.path.join(carpeta, "f.mp3")
        for intento in range(3):
            try:
                asyncio.run(edge_tts.Communicate(frase, voz).save(mp3))
                break
            except Exception:
                time.sleep(2 * (intento + 1))
        else:
            return None
        return subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-i", mp3, "-ar", "16000", "-ac", "1", "-f", "s16le", "-"],
            capture_output=True, check=True,
        ).stdout


def _castellano_simple(espanol):
    # "Mesa / Mueble escolar" -> "mesa"; "Yura, apágate" se deja entero.
    return texto_util.normalizar(re.split(r"[/(;]", str(espanol or ""))[0])


def _trabajos():
    conexion = sqlite3.connect(pronunciaciones.RUTA_DB)
    conexion.row_factory = sqlite3.Row
    registros = traductor._leer_registros_vocabulario(conexion)
    conexion.close()
    trabajos = []
    for registro in registros:
        quechua = str(registro["quechua"] or "").strip()
        espanol = _castellano_simple(registro["espanol"])
        for voz in VOCES:
            if quechua:
                frase = f"¿Qué significa {pronunciaciones.texto_para_hablar(quechua)}?"
                trabajos.append(("quechua", quechua, frase, voz))
            if espanol:
                trabajos.append(("castellano", espanol, f"¿Cómo se dice {espanol} en quechua?", voz))
    return trabajos


def aprender(informar=print):
    from vosk import Model, SetLogLevel

    SetLogLevel(-1)
    modelo = Model(os.path.join(RAIZ, "model"))
    trabajos = _trabajos()
    vistos = {"quechua": {}, "castellano": {}}  # escritura -> {palabra: veces}
    bien = {"quechua": 0, "castellano": 0}
    total = {"quechua": 0, "castellano": 0}

    def hacer(trabajo):
        tipo, palabra, frase, voz = trabajo
        audio = _audio(frase, voz)
        if not audio:
            return trabajo, None
        return trabajo, escuchar_vosk(modelo, audio)

    with ThreadPoolExecutor(max_workers=4) as grupo:
        for numero, (trabajo, escuchado) in enumerate(grupo.map(hacer, trabajos), 1):
            tipo, palabra, _, _ = trabajo
            if escuchado is None:
                continue
            patron = _HUECO_QUECHUA if tipo == "quechua" else _HUECO_CASTELLANO
            hueco = patron.match(escuchado)
            total[tipo] += 1
            if not hueco:
                continue
            escrito = hueco.group(1).strip()
            correcto = texto_util.normalizar(palabra)
            if (tipo == "castellano" and escrito == correcto) or (
                tipo == "quechua" and pronunciaciones._palabra_quechua_parecida(escrito) == palabra
            ):
                bien[tipo] += 1
                continue  # ya se entiende
            if len(escrito.replace(" ", "")) >= 2:
                vistos[tipo].setdefault(escrito, {}).setdefault(palabra, 0)
                vistos[tipo][escrito][palabra] += 1
            if numero % 200 == 0:
                informar(f"  {numero}/{len(trabajos)} frases escuchadas")

    mapa = {"quechua": {}, "castellano": {}, "ambiguas": []}
    for tipo in ("quechua", "castellano"):
        for escrito, palabras in vistos[tipo].items():
            if len(palabras) == 1:
                mapa[tipo][escrito] = next(iter(palabras))
            else:
                mapa["ambiguas"].append(escrito)
    with open(pronunciaciones.RUTA_PREGUNTAS_VOSK, "w", encoding="utf-8") as salida:
        json.dump(mapa, salida, ensure_ascii=False, indent=1, sort_keys=True)
    for tipo in ("quechua", "castellano"):
        if total[tipo]:
            informar(f"  {tipo:10}: se entendían {bien[tipo]}/{total[tipo]} = {100 * bien[tipo] / total[tipo]:.0f} %;"
                     f" escrituras aprendidas: {len(mapa[tipo])}")
    informar(f"  ambiguas (no se usan): {len(mapa['ambiguas'])}")


if __name__ == "__main__":
    inicio = time.time()
    aprender(informar=lambda t: print(t, flush=True))
    print(f"Listo en {time.time() - inicio:.0f} s -> {pronunciaciones.RUTA_PREGUNTAS_VOSK}")
