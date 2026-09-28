"""Yura aprende de los audios de la docente (modo docente).

Vuelve a escuchar cada grabación guardada en basedatos/pronunciaciones/ con
el mismo reconocedor que usa en clase (Whisper small), en tres situaciones:

- menu:       con las pistas generales (cuando un niño pregunta en el menú),
- juego:      con la palabra mezclada entre otras del diccionario,
- sin_pistas: sin ninguna ayuda.

Anota cómo escribió cada palabra bien dicha (tabla pronunciaciones_aprendidas
de diccionario.db). Con eso Yura encuentra la palabra en las consultas y la
acepta en el juego aunque el reconocedor la escriba distinto ("qumir" por
Q'umir). Lo que daría aciertos falsos ("oh", "ullu", otra palabra) se filtra
al usarlo (pronunciaciones.variante_segura), no aquí.

Uso (se puede repetir: solo procesa lo que falta):
    python basedatos/aprender_de_audios.py            # todas las grabaciones
    python basedatos/aprender_de_audios.py --rehacer  # vuelve a escuchar todo
"""
import os
import random
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pronunciaciones  # noqa: E402
import texto as texto_util  # noqa: E402

CONTEXTOS = ("menu", "juego", "sin_pistas")


def instruccion(contexto, palabra, otras, azar):
    if contexto == "menu":
        return texto_util.instruccion_reconocedor(None)
    if contexto == "juego":
        pistas = [palabra] + azar.sample(otras, min(6, len(otras)))
        azar.shuffle(pistas)
        return texto_util.instruccion_reconocedor(pistas)
    return None


def aprender(modelo, rehacer=False, informar=print):
    grabaciones = pronunciaciones.grabaciones()
    otras = sorted({g["palabra_frase"] for g in grabaciones})
    azar = random.Random(2026)
    resumen = {contexto: [0, 0] for contexto in CONTEXTOS}  # [reconocidas, total]
    for numero, grabacion in enumerate(reversed(grabaciones), 1):
        ruta = os.path.join(pronunciaciones.CARPETA_AUDIOS, os.path.basename(grabacion["archivo"]))
        if not os.path.exists(ruta):
            continue
        hechos = set() if rehacer else pronunciaciones.contextos_aprendidos(grabacion["id"])
        palabra = grabacion["palabra_frase"]
        linea = []
        for contexto in CONTEXTOS:
            if contexto in hechos:
                continue
            resultado = modelo.transcribe(
                ruta, language="es", initial_prompt=instruccion(contexto, palabra, otras, azar),
                fp16=False, temperature=0, beam_size=5, best_of=1,
                without_timestamps=True, condition_on_previous_text=False,
            )
            escuchado = texto_util.normalizar(resultado.get("text", ""))
            if texto_util.es_alucinacion_whisper(escuchado):
                escuchado = ""
            pronunciaciones.guardar_aprendida(grabacion["id"], palabra, contexto, escuchado)
            reconocida = texto_util.respuesta_quechua_correcta(escuchado, palabra)
            resumen[contexto][0] += int(reconocida)
            resumen[contexto][1] += 1
            linea.append(f"{contexto}: «{escuchado}»{'' if reconocida else ' *'}")
        if linea:
            informar(f"[{numero}/{len(grabaciones)}] {palabra}: " + " | ".join(linea))
    return resumen


if __name__ == "__main__":
    import whisper
    inicio = time.time()
    # En el procesador: la tarjeta de video la usa Yura mientras está encendida.
    modelo = whisper.load_model(os.environ.get("YURA_WHISPER_MODEL", "small"), device="cpu")
    resumen = aprender(modelo, rehacer="--rehacer" in sys.argv, informar=lambda t: print(t, flush=True))
    print(f"\nListo en {time.time() - inicio:.0f} s. Reconocidas sin lo aprendido (* = no reconocida):")
    for contexto, (bien, total) in resumen.items():
        if total:
            print(f"  {contexto:10}: {bien}/{total} = {100 * bien / total:.0f} %")
