"""Yura aprende a PRONUNCIAR las palabras como en los audios de la docente.

La voz de Yura (Edge TTS, es-BO-SofiaNeural) lee con reglas del castellano:
"Q'umir" suena "q umír". Para cada palabra grabada por la docente se prueban
varias formas de escribirla para la voz (la escritura normal, una adaptada al
castellano con el acento del quechua y lo que el reconocedor escribió al oír
a la docente), se genera cada una con la voz de Yura y se compara su sonido
con el audio de la docente (espectro mel + alineamiento temporal, DTW). La
forma que suena más parecida se guarda en la tabla pronunciaciones_voz y Yura
la usa al hablar (pronunciaciones.texto_para_hablar). La pantalla sigue
mostrando la escritura correcta.

Los audios de antes y después quedan en
documentacion_pruebas/evidencias/16_pronunciacion_voz/ para escucharlos.

Uso:
    python basedatos/aprender_pronunciacion.py            # palabras que faltan
    python basedatos/aprender_pronunciacion.py --rehacer  # todas otra vez
"""
import csv
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
import wave
from datetime import datetime

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pronunciaciones  # noqa: E402
import texto as texto_util  # noqa: E402

VOZ = os.environ.get("YURA_VOZ", "es-BO-SofiaNeural")
CARPETA_EVIDENCIAS = os.path.join(RAIZ, "documentacion_pruebas", "evidencias", "16_pronunciacion_voz")
TEMPORAL = os.path.join(CARPETA_EVIDENCIAS, "trabajo")
# Solo se cambia la escritura si suena claramente más parecida (5 %).
MEJORA_MINIMA = 0.05
VOCALES = "aeiou"


# ---------------------------------------------------------------- candidatas

def _sin_tildes(texto):
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c))


def _acento_quechua(palabra):
    """El quechua acentúa la penúltima sílaba. En castellano una palabra que
    termina en consonante (no n ni s) se acentúa en la última: se marca la
    tilde para que la voz diga "kúmir" y no "kumír"."""
    if len(palabra) < 3 or palabra[-1] in VOCALES + "ns":
        return palabra
    posiciones = [i for i, c in enumerate(palabra) if c in VOCALES]
    if len(posiciones) < 2:
        return palabra
    i = posiciones[-2]
    # En diptongos (ay, uy...) la vocal fuerte lleva la tilde igual.
    return palabra[:i] + {"a": "á", "e": "é", "i": "í", "o": "ó", "u": "ú"}[palabra[i]] + palabra[i + 1:]


def adaptar_al_castellano(frase, q_final="k"):
    """Escritura para que una voz castellana se acerque al quechua."""
    palabras = []
    for palabra in _sin_tildes(frase.lower()).replace("’", "'").split():
        p = palabra.replace("'", "")
        p = p.replace("qh", "j").replace("kh", "j").replace("ph", "p").replace("th", "t").replace("chh", "ch")
        if p.endswith("q"):
            p = p[:-1] + q_final
        p = p.replace("q", "k")
        palabras.append(_acento_quechua(p))
    texto = " ".join(palabras)
    return texto[:1].upper() + texto[1:]


def candidatas(palabra, transcripciones):
    opciones = [palabra, adaptar_al_castellano(palabra), adaptar_al_castellano(palabra, q_final="j")]
    propia = texto_util.simplificar_quechua(palabra).replace(" ", "")
    for escrito in transcripciones:
        escrito = texto_util.normalizar(escrito).replace("'", "")
        if not escrito or texto_util.es_alucinacion_whisper(escrito):
            continue
        simple = texto_util.simplificar_quechua(escrito).replace(" ", "")
        # Lo que no se parece a la palabra ("adios", "all you") no sirve.
        if len(simple) < 2 or texto_util.distancia_edicion(simple, propia) > max(2, len(propia) // 2):
            continue
        opciones += [escrito, _acento_quechua(escrito) if " " not in escrito else escrito]
    return list(dict.fromkeys(o.strip() for o in opciones if o and o.strip()))


def candidata_permitida(opcion, palabra):
    """Reglas de sentido común (revisión del 28/09/2026): la voz no debe
    perder el primer sonido ("ucha" por qucha, "omer" por q'umir), partir la
    palabra ("cagual lo") ni sonar a inglés ("walking")."""
    if opcion == palabra:
        return True
    if len(opcion.split()) != len(palabra.split()):
        return False
    if re.search(r"ng\b", opcion.lower()):
        return False
    propia = texto_util.simplificar_quechua(palabra)
    forma = texto_util.simplificar_quechua(opcion)
    # La h castellana no suena: "hóchuy" pierde la j de juch'uy.
    if opcion.lower().startswith("h"):
        return False
    return bool(forma) and bool(propia) and forma[0] == propia[0]


def elegir(palabra, puntajes, entendidas):
    """La forma elegida debe estar permitida, entenderse como la palabra
    correcta y, entre esas, sonar lo más parecido al audio de la docente."""
    permitidas = [o for o in puntajes if candidata_permitida(o, palabra)]

    def puntaje(opcion):
        return puntajes[opcion] + (0.0 if entendidas.get(opcion) else 1.0)
    mejor = min(permitidas, key=puntaje)
    original = puntajes[palabra]
    if mejor != palabra and entendidas.get(palabra, False) == entendidas.get(mejor, False) \
            and puntajes[mejor] > original * (1 - MEJORA_MINIMA):
        mejor = palabra  # no suena claramente mejor: se deja como está
    return mejor


def candidatas_extra(palabra):
    """Segunda vuelta, si ninguna forma se entendió: variantes de vocales
    (el quechua tiene 3; la voz castellana distingue 5), de la w y del acento."""
    extra = []
    for q_final in ("k", "j"):
        base = _sin_tildes(adaptar_al_castellano(palabra, q_final)).lower()
        for cambio in (base, base.replace("u", "o"), base.replace("i", "e"),
                       base.replace("w", "gu"), base.replace("w", "u")):
            extra += [cambio, _acento_quechua(cambio)]
    return [e[:1].upper() + e[1:] for e in dict.fromkeys(extra)]


# ---------------------------------------------------------------- sonido

def _leer_wav(ruta):
    with wave.open(ruta, "rb") as archivo:
        datos = np.frombuffer(archivo.readframes(archivo.getnframes()), dtype=np.int16)
    return datos.astype(np.float32) / 32768.0


def _recortar_silencio(senal, frecuencia=16000):
    bloque = frecuencia // 100
    if len(senal) < bloque * 3:
        return senal
    energia = np.sqrt(np.convolve(senal ** 2, np.ones(bloque) / bloque, mode="same"))
    umbral = max(energia.max() * 0.08, 1e-4)
    voz = np.where(energia > umbral)[0]
    if len(voz) == 0:
        return senal
    return senal[max(0, voz[0] - bloque * 3): voz[-1] + bloque * 3]


def rasgos(ruta_wav):
    """Espectro mel logarítmico normalizado (quita diferencias de voz y volumen)."""
    import torch
    import whisper.audio
    senal = _recortar_silencio(_leer_wav(ruta_wav))
    mel = whisper.audio.log_mel_spectrogram(torch.from_numpy(senal)).numpy().T  # (tramas, 80)
    return (mel - mel.mean(axis=0)) / (mel.std(axis=0) + 1e-5)


def distancia_dtw(a, b):
    """Distancia media entre dos sonidos alineados en el tiempo (DTW)."""
    costo = np.sqrt(((a[:, None, :] - b[None, :, :]) ** 2).sum(axis=2))
    n, m = costo.shape
    acumulado = np.full((n + 1, m + 1), np.inf)
    acumulado[0, 0] = 0.0
    for i in range(1, n + 1):
        fila_anterior = acumulado[i - 1]
        fila = acumulado[i]
        for j in range(1, m + 1):
            fila[j] = costo[i - 1, j - 1] + min(fila_anterior[j], fila[j - 1], fila_anterior[j - 1])
    return float(acumulado[n, m] / (n + m))


def voz_de_yura(texto, destino_wav):
    """Genera el texto con la voz de Yura (igual que al hablar) en WAV 16 kHz."""
    edge = os.path.join(RAIZ, ".venv", "bin", "edge-tts")
    mp3 = destino_wav[:-4] + ".mp3"
    for _ in range(3):
        resultado = subprocess.run(
            [edge, "--voice", VOZ, "--rate=+5%", "--text", texto, "--write-media", mp3],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30,
        )
        if resultado.returncode == 0 and os.path.exists(mp3) and os.path.getsize(mp3) > 0:
            break
        time.sleep(1)
    else:
        raise RuntimeError(f"Edge TTS no generó «{texto}»")
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", mp3, "-ac", "1", "-ar", "16000", destino_wav],
        check=True, timeout=30,
    )
    os.remove(mp3)


_modelo = {}


def se_entiende(ruta_wav, palabra, otras):
    """¿El reconocedor de Yura entiende la palabra correcta al oír esta voz?
    Mismas pistas que en el juego (la palabra mezclada con otras)."""
    import random
    import whisper
    import aprender_de_audios
    if "whisper" not in _modelo:
        _modelo["whisper"] = whisper.load_model(os.environ.get("YURA_WHISPER_MODEL", "small"), device="cpu")
    azar = random.Random(palabra)
    resultado = _modelo["whisper"].transcribe(
        ruta_wav, language="es", initial_prompt=aprender_de_audios.instruccion("juego", palabra, otras, azar),
        fp16=False, temperature=0, beam_size=5, best_of=1,
        without_timestamps=True, condition_on_previous_text=False,
    )
    escuchado = texto_util.normalizar(resultado.get("text", ""))
    return texto_util.respuesta_quechua_correcta(escuchado, palabra), escuchado


def _nombre_archivo(texto):
    limpio = re.sub(r"[^a-z0-9]+", "_", _sin_tildes(texto.lower())).strip("_")
    return limpio or "palabra"


# ---------------------------------------------------------------- aprendizaje

def aprender(rehacer=False, informar=print):
    os.makedirs(TEMPORAL, exist_ok=True)
    with pronunciaciones._conectar() as conexion:
        hechas = {f[0] for f in conexion.execute(f"SELECT palabra_frase FROM {pronunciaciones.TABLA_VOZ}")}
        aprendidas = conexion.execute(
            f"SELECT palabra_frase, transcripcion FROM {pronunciaciones.TABLA_APRENDIDAS}"
        ).fetchall()
    por_palabra = {}
    for grabacion in pronunciaciones.grabaciones():  # la más reciente primero
        por_palabra.setdefault(grabacion["palabra_frase"], grabacion)
    filas_informe = []
    for numero, (palabra, grabacion) in enumerate(sorted(por_palabra.items()), 1):
        if palabra in hechas and not rehacer:
            continue
        audio_docente = pronunciaciones.audio_de(palabra)
        if not audio_docente:
            continue
        escritas = [grabacion["transcripcion"] or ""] + [t for p, t in aprendidas if p == palabra]
        rasgos_docente = rasgos(audio_docente)
        otras = [p for p in por_palabra if p != palabra]
        puntajes, entendidas = {}, {}

        def probar(opciones):
            for opcion in opciones:
                if opcion in puntajes:
                    continue
                ruta = os.path.join(TEMPORAL, _nombre_archivo(opcion) + ".wav")
                try:
                    voz_de_yura(opcion, ruta)
                    puntajes[opcion] = distancia_dtw(rasgos(ruta), rasgos_docente)
                    entendidas[opcion] = se_entiende(ruta, palabra, otras)[0]
                except Exception as exc:
                    informar(f"  (no se pudo probar «{opcion}»: {exc})")

        probar(candidatas(palabra, escritas))
        if not any(entendidas.values()):
            probar(candidatas_extra(palabra))
        if palabra not in puntajes:
            continue
        mejor = elegir(palabra, puntajes, entendidas)
        original = puntajes[palabra]
        with pronunciaciones._conectar() as conexion:
            conexion.execute(
                f"INSERT OR REPLACE INTO {pronunciaciones.TABLA_VOZ} "
                "(palabra_frase, texto_para_voz, parecido, parecido_original, fecha, se_entiende, se_entendia_original) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (palabra, mejor, puntajes[mejor], original, datetime.now().isoformat(timespec="seconds"),
                 int(entendidas.get(mejor, False)), int(entendidas.get(palabra, False))),
            )
        # Para escuchar: docente, voz de Yura antes y después.
        base = os.path.join(CARPETA_EVIDENCIAS, _nombre_archivo(palabra))
        shutil.copyfile(audio_docente, base + "_1_docente.wav")
        shutil.copyfile(os.path.join(TEMPORAL, _nombre_archivo(palabra) + ".wav"), base + "_2_yura_antes.wav")
        shutil.copyfile(os.path.join(TEMPORAL, _nombre_archivo(mejor) + ".wav"), base + "_3_yura_ahora.wav")
        mejora = 100 * (original - puntajes[mejor]) / original if original else 0
        filas_informe.append([palabra, mejor, f"{original:.3f}", f"{puntajes[mejor]:.3f}", f"{mejora:.0f}",
                              "sí" if entendidas.get(palabra, False) else "no", "sí" if entendidas.get(mejor, False) else "no",
                              " | ".join(f"{o}={d:.3f}{'' if entendidas.get(o) else '*'}"
                                         for o, d in sorted(puntajes.items(), key=lambda x: x[1]))])
        informar(f"[{numero}/{len(por_palabra)}] {palabra} -> «{mejor}» (distancia {original:.3f} -> {puntajes[mejor]:.3f}; "
                 f"se entiende: {'sí' if entendidas.get(palabra, False) else 'no'} -> {'sí' if entendidas.get(mejor, False) else 'no'})")
    shutil.rmtree(TEMPORAL, ignore_errors=True)
    if filas_informe:
        ruta_csv = os.path.join(CARPETA_EVIDENCIAS, "resultados.csv")
        nuevo = not os.path.exists(ruta_csv)
        with open(ruta_csv, "a", encoding="utf-8", newline="") as salida:
            escritor = csv.writer(salida)
            if nuevo:
                escritor.writerow(["palabra", "texto_para_voz", "distancia_antes", "distancia_ahora", "mejora_%",
                                   "se_entendia_antes", "se_entiende_ahora", "todas_las_pruebas (*=no se entiende)"])
            escritor.writerows(filas_informe)
    return filas_informe


if __name__ == "__main__":
    inicio = time.time()
    filas = aprender(rehacer="--rehacer" in sys.argv, informar=lambda t: print(t, flush=True))
    cambiadas = [f for f in filas if f[0] != f[1]]
    antes = sum(f[5] == "sí" for f in filas)
    ahora = sum(f[6] == "sí" for f in filas)
    print(f"\nListo en {time.time() - inicio:.0f} s: {len(filas)} palabras probadas, "
          f"{len(cambiadas)} con una escritura nueva para la voz.")
    if filas:
        print(f"La voz de Yura se entiende: antes {antes}/{len(filas)} = {100 * antes / len(filas):.0f} %, "
              f"ahora {ahora}/{len(filas)} = {100 * ahora / len(filas):.0f} %")
