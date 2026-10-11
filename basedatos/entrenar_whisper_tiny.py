"""Entrena Whisper tiny con la voz de la docente y lo compara con Vosk.

Comparación justa pedida por el equipo (07/10/2026): Whisper tiny aprende de
lo mismo que Vosk (las 121 grabaciones de la docente y sus variaciones:
aguda, muy aguda, grave, rápida, lenta, con ruido) y los dos se miden con la
misma prueba, con variaciones DISTINTAS a las del entrenamiento
(medir_escucha_vosk.PRUEBAS). También se mide si Whisper sigue entendiendo
frases en castellano, porque entrenarlo solo con palabras sueltas puede
hacerle olvidar el idioma, y cuánto tarda por frase en la Raspberry.

Se entrena solo el decodificador (la parte que escribe); el oído (encoder)
queda igual. El modelo entrenado se guarda en basedatos/whisper_tiny_yura.pt
y NO reemplaza a Vosk: Yura sigue usando Vosk salvo que se decida otra cosa.

Uso:  python basedatos/entrenar_whisper_tiny.py [--epocas 3]
"""
import argparse
import asyncio
import os
import random
import subprocess
import sys
import tempfile
import time

CARPETA = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(CARPETA)
sys.path.insert(0, RAIZ)
sys.path.insert(0, CARPETA)

import numpy as np  # noqa: E402
import torch  # noqa: E402
import whisper  # noqa: E402

import pronunciaciones  # noqa: E402
import texto as texto_util  # noqa: E402
from aprender_de_audios import VARIACIONES_VOSK, audio_para_vosk, escuchar_vosk  # noqa: E402
from medir_escucha_vosk import PRUEBAS  # noqa: E402

RUTA_MODELO = os.path.join(CARPETA, "whisper_tiny_yura.pt")
RUTA_RESULTADOS = os.path.join(RAIZ, "documentacion_pruebas", "evidencias", "24_whisper_tiny_vs_vosk.json")
FRASES_CASTELLANO = {
    "¿Cómo se dice perro en quechua?": "perro", "¿Cómo se dice agua en quechua?": "agua",
    "¿Cómo se dice azul en quechua?": "azul", "Quiero jugar contigo.": "jugar",
    "Hoy fui a la escuela con mi mamá.": "escuela", "¿Qué significa allqu?": "significa",
    "Dime los números en quechua.": "numeros", "Me gusta mucho comer fruta.": "fruta",
}
VOCES_CASTELLANO = ("es-BO-SofiaNeural", "es-PE-AlexNeural", "es-MX-DaliaNeural")


def _a_float(audio_s16):
    return np.frombuffer(audio_s16, np.int16).astype(np.float32) / 32768.0


def _grabaciones():
    return [g for g in pronunciaciones.grabaciones()
            if os.path.exists(os.path.join(pronunciaciones.CARPETA_AUDIOS, os.path.basename(g["archivo"])))]


def _ruta(grabacion):
    return os.path.join(pronunciaciones.CARPETA_AUDIOS, os.path.basename(grabacion["archivo"]))


def datos_entrenamiento():
    """(audio, texto) de cada grabación tal cual y con cada variación de aprendizaje."""
    datos = []
    for grabacion in _grabaciones():
        ruta = _ruta(grabacion)
        datos.append((_a_float(audio_para_vosk(ruta)), grabacion["palabra_frase"]))
        for nombre, filtro in VARIACIONES_VOSK.items():
            datos.append((_a_float(audio_para_vosk(ruta, filtro, 0.02 if "ruido" in nombre else 0.0)),
                          grabacion["palabra_frase"]))
    return datos


def entrenar(modelo, datos, epocas, informar=print):
    tokenizador = whisper.tokenizer.get_tokenizer(True, language="es", task="transcribe")
    inicio = list(tokenizador.sot_sequence_including_notimestamps)
    for parametro in modelo.encoder.parameters():
        parametro.requires_grad = False
    optimizador = torch.optim.AdamW([p for p in modelo.decoder.parameters()], lr=2e-5)
    # El oído no se entrena: lo que oye de cada audio se calcula UNA vez (en
    # float16 para que entre en memoria) y se reutiliza en cada época.
    informar(f"  escuchando {len(datos)} audios una vez...")
    oidos = []
    with torch.no_grad():
        for i in range(0, len(datos), 8):
            mels = torch.stack([whisper.log_mel_spectrogram(whisper.pad_or_trim(torch.from_numpy(a)))
                                for a, _ in datos[i:i + 8]])
            oidos.extend(modelo.encoder(mels).half())
    ejemplos = [(oido, texto) for oido, (_, texto) in zip(oidos, datos)]
    modelo.train()
    azar = random.Random(2026)
    for epoca in range(1, epocas + 1):
        azar.shuffle(ejemplos)
        perdidas = []
        for i in range(0, len(ejemplos), 8):
            lote = ejemplos[i:i + 8]
            audio = torch.stack([oido.float() for oido, _ in lote])
            secuencias = [inicio + tokenizador.encode(" " + texto) + [tokenizador.eot] for _, texto in lote]
            largo = max(len(s) for s in secuencias)
            entrada = torch.full((len(lote), largo - 1), tokenizador.eot, dtype=torch.long)
            objetivo = torch.full((len(lote), largo - 1), -100, dtype=torch.long)
            for j, s in enumerate(secuencias):
                entrada[j, :len(s) - 1] = torch.tensor(s[:-1])
                objetivo[j, :len(s) - 1] = torch.tensor(s[1:])
                objetivo[j, :len(inicio) - 1] = -100  # no se aprende la cabecera
            logits = modelo.decoder(entrada, audio)
            perdida = torch.nn.functional.cross_entropy(logits.reshape(-1, logits.shape[-1]), objetivo.reshape(-1))
            optimizador.zero_grad()
            perdida.backward()
            optimizador.step()
            perdidas.append(perdida.item())
        informar(f"  época {epoca}/{epocas}: pérdida {np.mean(perdidas):.3f}")
    modelo.eval()


def transcribir_whisper(modelo, audio):
    resultado = modelo.transcribe(audio, language="es", fp16=False, temperature=0, beam_size=1,
                                  without_timestamps=True, condition_on_previous_text=False)
    return texto_util.normalizar(resultado.get("text", ""))


def aprender_variantes(transcribir, informar=print):
    """El mismo proceso que tuvo Vosk (aprender_de_audios --vosk --variaciones):
    cómo escribe cada palabra al oír la grabación y sus variaciones de
    aprendizaje. Se guarda en memoria, sin tocar lo aprendido por Vosk."""
    variantes = {}
    grabaciones = _grabaciones()
    for numero, grabacion in enumerate(grabaciones, 1):
        ruta = _ruta(grabacion)
        palabra = grabacion["palabra_frase"]
        audios = [audio_para_vosk(ruta)] + [
            audio_para_vosk(ruta, filtro, 0.02 if "ruido" in nombre else 0.0)
            for nombre, filtro in VARIACIONES_VOSK.items()
        ]
        for audio in audios:
            escrito = transcribir(audio)
            if escrito and pronunciaciones.variante_segura(escrito, palabra):
                variantes.setdefault(palabra, set()).add(escrito)
        if numero % 30 == 0:
            informar(f"  aprendidas {numero}/{len(grabaciones)} palabras")
    return variantes


def medir_palabras(transcribir, variantes=None):
    """% de palabras aceptadas por el juego con las variaciones de PRUEBA, y ms por frase.
    variantes: lo aprendido por este reconocedor (como el afinado de Vosk)."""
    grabaciones = _grabaciones()
    bien, total, tiempos = 0, 0, []
    for filtro, ruido in PRUEBAS.values():
        for grabacion in grabaciones:
            audio = audio_para_vosk(_ruta(grabacion), filtro, ruido)
            inicio = time.perf_counter()
            escuchado = transcribir(audio)
            tiempos.append(time.perf_counter() - inicio)
            palabra = grabacion["palabra_frase"]
            afinado = texto_util.normalizar(pronunciaciones.afinar_vosk(escuchado))
            aprendidas = pronunciaciones.variantes(palabra) + sorted((variantes or {}).get(palabra, ()))
            bien += bool(pronunciaciones.respuesta_aceptada(afinado, palabra, aprendidas)
                         or pronunciaciones.respuesta_aceptada(escuchado, palabra, aprendidas))
            total += 1
    return 100 * bien / total, 1000 * float(np.median(tiempos))


def audios_castellano():
    import edge_tts

    audios = []
    with tempfile.TemporaryDirectory() as carpeta:
        for frase, clave in FRASES_CASTELLANO.items():
            for voz in VOCES_CASTELLANO:
                mp3 = os.path.join(carpeta, "f.mp3")
                asyncio.run(edge_tts.Communicate(frase, voz).save(mp3))
                crudo = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", mp3, "-ar", "16000", "-ac", "1",
                                        "-f", "s16le", "-"], capture_output=True, check=True).stdout
                audios.append((crudo, clave))
    return audios


def medir_castellano(transcribir, audios):
    bien = sum(clave in transcribir(audio).split() for audio, clave in audios)
    return 100 * bien / len(audios)


def main():
    parametros = argparse.ArgumentParser()
    parametros.add_argument("--epocas", type=int, default=3)
    opciones = parametros.parse_args()
    torch.set_num_threads(4)
    inicio = time.time()

    from vosk import Model, SetLogLevel
    SetLogLevel(-1)
    vosk = Model(os.path.join(RAIZ, "model"))
    tiny = whisper.load_model("tiny", device="cpu")
    castellano = audios_castellano()

    def con_vosk(audio):
        return escuchar_vosk(vosk, audio)

    def con_tiny(audio):
        return transcribir_whisper(tiny, _a_float(audio))

    informar = lambda t: print(t, flush=True)  # noqa: E731

    # Cada paso guarda su resultado apenas termina y, si el proceso se corta
    # (la Raspberry se apagó con la medición a medias, 08/10/2026), al volver
    # a correrlo se saltan los pasos hechos.
    import json
    resultados = {}
    if os.path.exists(RUTA_RESULTADOS):
        with open(RUTA_RESULTADOS, encoding="utf-8") as archivo:
            resultados = json.load(archivo)

    def paso(nombre, medir):
        if nombre in resultados:
            informar(f"  (ya medido: {nombre})")
        else:
            resultados[nombre] = list(medir())
            with open(RUTA_RESULTADOS, "w", encoding="utf-8") as archivo:
                json.dump(resultados, archivo, ensure_ascii=False, indent=1)
        palabras, ms, cast = resultados[nombre]
        informar(f"  -> {nombre}: palabras {palabras:.0f} %, {ms:.0f} ms por frase, castellano {cast:.0f} %")
        return resultados[nombre]

    informar("1/6 Vosk con su proceso (lo aprendido + afinado)...")
    paso("Vosk + su proceso", lambda: (*medir_palabras(con_vosk), medir_castellano(con_vosk, castellano)))
    informar("2/6 Whisper tiny tal cual...")
    _, _, castellano_base = paso("Whisper tiny tal cual",
                                 lambda: (*medir_palabras(con_tiny), medir_castellano(con_tiny, castellano)))
    informar("3/6 Whisper tiny aprende con el mismo proceso que Vosk...")
    paso("Whisper tiny + mismo proceso",
         lambda: (*medir_palabras(con_tiny, aprender_variantes(con_tiny, informar)), castellano_base))

    if os.path.exists(RUTA_MODELO):
        informar("4/6 (ya reentrenado: se carga el modelo guardado)")
        tiny.load_state_dict(torch.load(RUTA_MODELO, map_location="cpu"))
    else:
        datos = datos_entrenamiento()
        informar(f"4/6 Reentrenando Whisper tiny con {len(datos)} audios ({opciones.epocas} épocas)...")
        entrenar(tiny, datos, opciones.epocas, informar=informar)
        torch.save(tiny.state_dict(), RUTA_MODELO)
    informar("5/6 Whisper tiny reentrenado...")
    _, _, castellano_entrenado = paso("Whisper tiny reentrenado",
                                      lambda: (*medir_palabras(con_tiny), medir_castellano(con_tiny, castellano)))
    informar("6/6 Whisper tiny reentrenado + mismo proceso...")
    paso("Whisper reentrenado + proceso",
         lambda: (*medir_palabras(con_tiny, aprender_variantes(con_tiny, informar)), castellano_entrenado))
    filas = [(nombre, *valores) for nombre, valores in resultados.items()]

    print(f"\n{'':28} {'palabras (prueba)':>18} {'ms por frase':>13} {'castellano':>11}")
    for nombre, palabras, ms, cast in filas:
        print(f"{nombre:28} {palabras:17.0f}% {ms:12.0f} {cast:10.0f}%")
    print(f"\nListo en {time.time() - inicio:.0f} s. Modelo guardado en {RUTA_MODELO} (Yura sigue usando Vosk).")


if __name__ == "__main__":
    main()
