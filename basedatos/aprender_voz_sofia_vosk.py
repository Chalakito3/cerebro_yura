"""Vosk aprende a escuchar las palabras dichas con la voz de Sofía.

Pedido del equipo (11/10/2026): Sofía es la voz de Yura y con ella se entrena
también la escucha. Para cada palabra del diccionario (también las que no
tienen grabación de la docente), Sofía la dice con la escritura que usa al
hablar (pronunciaciones.texto_para_hablar) y Vosk la escucha tal cual y con
las mismas variaciones que la voz de la docente (aguda, grave, rápida, lenta,
con ruido). Lo que Vosk escribe se guarda en pronunciaciones_aprendidas con
los contextos "sofia" y "sofia_<variación>".

Las palabras sin grabación de la docente no tienen id de grabación: se usa
uno negativo fijo por palabra. Lo que daría aciertos falsos (muy corto, otra
palabra del diccionario, nada parecido) se filtra al usarlo
(pronunciaciones.variante_segura), igual que lo aprendido de la docente.

Detener a Yura antes:  systemctl --user stop yura
Uso (se puede repetir: solo procesa lo que falta):
    python basedatos/aprender_voz_sofia_vosk.py
    python basedatos/aprender_voz_sofia_vosk.py --rehacer
"""
import os
import sys
import tempfile
import time
import zlib

CARPETA = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(CARPETA)
sys.path.insert(0, RAIZ)
sys.path.insert(0, CARPETA)

import pronunciaciones  # noqa: E402
import texto as texto_util  # noqa: E402
import traductor  # noqa: E402
from aprender_de_audios import VARIACIONES_VOSK, audio_para_vosk, escuchar_vosk  # noqa: E402
from aprender_pronunciacion import voz_de_yura  # noqa: E402


# Palabras muy comunes del castellano que Vosk escribe al oír a Sofía («vale»
# por Kawallu, «acá» por Aqha): si se aprendieran, un niño que las dijera en
# castellano quedaría como si hubiera dicho la palabra quechua. No se guardan.
CASTELLANO_COMUN = pronunciaciones._PALABRAS_CASTELLANAS | {
    "vale", "aca", "aqui", "alla", "ahi", "asi", "ya", "si", "bueno", "okay", "ok", "listo",
    "eso", "esto", "esa", "ese", "luna", "pronto", "tanto", "nada", "todo", "bien", "mal",
    "ocho", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "nueve", "diez",
    "alto", "perro", "comer", "agua", "casa", "mama", "papa", "para", "y", "o", "a",
}


def es_castellano_comun(transcripcion):
    palabras = texto_util.normalizar(transcripcion).split()
    return bool(palabras) and all(p in CASTELLANO_COMUN for p in palabras)


def id_de_palabra(palabra, grabadas):
    """El id de la grabación de la docente o, si no hay, uno negativo fijo."""
    if palabra in grabadas:
        return grabadas[palabra]
    return -(zlib.crc32(palabra.encode("utf-8")) % 1_000_000_000) - 1


def palabras_del_diccionario():
    with pronunciaciones._conectar() as conexion:
        registros = traductor._leer_registros_vocabulario(conexion)
    return sorted({str(r["quechua"]).strip() for r in registros if str(r["quechua"] or "").strip()})


def aprender(rehacer=False, informar=print):
    from vosk import Model, SetLogLevel
    SetLogLevel(-1)
    modelo = Model(os.path.join(RAIZ, "model"))
    grabadas = {g["palabra_frase"]: g["id"] for g in reversed(pronunciaciones.grabaciones())}
    contextos = {"sofia": (None, 0.0)}
    for nombre, filtro in VARIACIONES_VOSK.items():
        contextos[f"sofia_{nombre}"] = (filtro, 0.02 if "ruido" in nombre else 0.0)
    palabras = palabras_del_diccionario()
    resumen = [0, 0]
    with tempfile.TemporaryDirectory(dir="/dev/shm" if os.path.isdir("/dev/shm") else None) as temporal:
        for numero, palabra in enumerate(palabras, 1):
            identificador = id_de_palabra(palabra, grabadas)
            hechos = set() if rehacer else pronunciaciones.contextos_aprendidos(identificador)
            pendientes = {c: v for c, v in contextos.items() if c not in hechos}
            if not pendientes:
                continue
            ruta = os.path.join(temporal, "sofia.wav")
            try:
                voz_de_yura(pronunciaciones.texto_para_hablar(palabra), ruta)
            except Exception as exc:
                informar(f"[{numero}/{len(palabras)}] {palabra}: no se pudo generar la voz ({exc})")
                continue
            linea = []
            for contexto, (filtro, ruido) in pendientes.items():
                escuchado = escuchar_vosk(modelo, audio_para_vosk(ruta, filtro, ruido))
                bien = texto_util.respuesta_quechua_correcta(
                    texto_util.normalizar(pronunciaciones.afinar_vosk(escuchado)), palabra)
                # Se guarda vacía si es castellano común: así no se repite y no se usa.
                guardada = "" if es_castellano_comun(escuchado) else escuchado
                pronunciaciones.guardar_aprendida(identificador, palabra, contexto, guardada)
                resumen[0] += int(bien)
                resumen[1] += 1
                linea.append(f"«{escuchado}»{'' if bien else ' *'}")
            informar(f"[{numero}/{len(palabras)}] {palabra}: " + " | ".join(linea))
    return resumen


if __name__ == "__main__":
    inicio = time.time()
    bien, total = aprender(rehacer="--rehacer" in sys.argv, informar=lambda t: print(t, flush=True))
    if total:
        print(f"\nListo en {time.time() - inicio:.0f} s. Vosk entendió a Sofía sin lo aprendido: "
              f"{bien}/{total} = {100 * bien / total:.0f} % (* = no entendida).")
