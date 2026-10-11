#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pre-generador de voces locales de Sofía (es-BO-SofiaNeural).

Descarga y guarda en basedatos/voces_sofia/ todas las frases, preguntas,
saludos, números y palabras del diccionario que Yura dice en el aula.

Con esta caché, Yura habla de forma 100% autónoma y natural sin necesidad de
internet, con cero latencia y con la voz oficial de Sofía.

Uso:
    python basedatos/pregenerar_voces_sofia.py              # Genera todas las frases
    python basedatos/pregenerar_voces_sofia.py --resumen    # Muestra cuántas están guardadas
    python basedatos/pregenerar_voces_sofia.py --limite 10  # Genera solo las primeras 10
"""

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import traductor
import conversacion
import pronunciaciones
import voz_sofia

CARPETA_VOCES = os.path.join(RAIZ, "basedatos", "voces_sofia")
RUTA_INDICE = os.path.join(CARPETA_VOCES, "indice.json")
RUTA_DB = os.path.join(RAIZ, "diccionario.db")
VOZ_SOFIA = os.environ.get("YURA_VOZ", "es-BO-SofiaNeural").strip() or "es-BO-SofiaNeural"


# Igual que Yura al hablar (voz_sofia.py): mismo texto, expresión y clave.
formatear_texto_voz = voz_sofia.formatear_texto_voz


def ruta_cache(texto_voz, voz=VOZ_SOFIA):
    return voz_sofia.ruta_cache(CARPETA_VOCES, voz, texto_voz)


def recolectar_frases_del_sistema(modo="todo"):
    """Recopila frases que Yura dice durante su operación.
    
    modo="sistema": Solo saludos, menú, despedidas y control (~25 frases, descarga en <1 min).
    modo="juego":   Sistema + preguntas y retroalimentación del juego pedagógico (~300 frases).
    modo="todo":    Todo el vocabulario y explicaciones completas (2,101 frases).
    """
    frases = set()

    # 1. Saludos, menú y bienvenida
    frases.add("Ñuqaqa Yura kani. Robotmi kani, qhichwa simita rimanakuypaq yanapakuq. Qhichwa simita rimanakuyta, rimaykunata kallpachayta yanapani. Imapin yanapaykiman?")
    frases.add("Rimaykullayki")
    frases.add("Allin p'unchay")
    frases.add("Allin tuta")
    frases.add("Allin sukha")
    frases.add("Yusulpayki")
    frases.add("Tupananchiskama")
    frases.add("Hola. Soy Yura, tu robot educativo. Di jugar, traducir o conversar para comenzar.")
    frases.add("Hola. Di jugar, traducir o conversar.")
    frases.add("Volviendo al menú principal.")
    frases.add("Estoy en silencio. Di despierta cuando quieras hablar conmigo.")
    frases.add("Hola de nuevo, ya me desperté. ¿En qué te puedo ayudar?")
    frases.add("¿Quieres que me apague? Di sí para confirmar o no para continuar.")
    frases.add("Hasta luego. Tupananchiskama.")
    frases.add("Entendido, sigamos aprendiendo juntos.")
    frases.add("No te escuché con claridad. ¿Puedes repetir, por favor?")
    frases.add("No escuché ninguna respuesta.")
    frases.add("Por favor, elige una opción: jugar, traducir o conversar.")
    frases.add("No entendí esa opción. Di jugar, traducir o conversar.")

    # 1b. Diálogos en Quechua Puro
    frases.add("¡Allin p'unchay, wawacha! Ñuqaqa Yura kani. Imataq sutiyki?")
    frases.add("¡Rimaykullayki, wawacha! Kusisqam kani qamwan rimaspa. Imataq sutiyki?")
    frases.add("¡Allillanmi kashani! Qamrí, allillanchu kashanki?")
    frases.add("¡Ancha allinmi! Kusisqachu kashanki?")
    frases.add("¡Kusa! Kusisqa kaspaqa sumaqtam yachakusun. Imata ruwayta munanki?")
    frases.add("Ama llakikuychu, wawacha. Kuska yachakusun. Maymantataq kanki?")
    frases.add("¡Qammatapis sulpayki! Sumaqta qhichwata rimanki.")
    frases.add("¡Tupananchiskama, sumaq wawa! Allin p'unchay kachun.")

    if modo == "sistema":
        return sorted(frases)

    # 2. Frases del Juego
    frases.add("Vamos a jugar. Te haré cuatro preguntas sobre palabras en quechua. Di salir en cualquier momento para volver al menú.")
    frases.add("Pasemos a la siguiente pregunta.")
    frases.add("No te escuché. Repite tu respuesta, por favor.")
    frases.add("No pude cargar la respuesta correcta de esta pregunta.")
    frases.add("No pude cargar las palabras del juego.")

    # Mensajes finales del juego (0 a 4 aciertos)
    for aciertos in range(5):
        if aciertos == 4:
            frases.add("Terminamos la partida. Acertaste cuatro de cuatro preguntas. ¡Excelente trabajo! Te felicito.")
        elif aciertos >= 2:
            frases.add(f"Terminamos la partida. Acertaste {aciertos} de cuatro preguntas. ¡Muy bien! Sigue practicando.")
        elif aciertos == 1:
            frases.add("Terminamos la partida. Acertaste una de cuatro preguntas. Ánimo, cada vez lo harás mejor.")
        else:
            frases.add("Terminamos la partida. Esta vez no tuviste aciertos, pero no te rindas. ¡Volvamos a practicar!")

    # 3. Preguntas y respuestas del juego
    with sqlite3.connect(f"file:{RUTA_DB}?mode=ro", uri=True) as con:
        palabras_juego = traductor.palabras_para_juego(con)
        for palabra_es in palabras_juego:
            frases.add(f"¿Cómo se dice {palabra_es} en quechua?")
            quechua = traductor.consultar_diccionario_local(palabra_es, con)
            if quechua:
                frases.add(f"¡Muy bien! Dijiste {quechua} correctamente.")
                frases.add(f"No es correcto. La respuesta correcta es {quechua}.")
                frases.add(f"En quechua se dice: {quechua}.")

        if modo == "juego":
            return sorted(frases)

        # 4. Todas las traducciones del diccionario completo (283 términos)
        registros = traductor._leer_registros_vocabulario(con)
        for reg in registros:
            q = str(reg["quechua"] or "").strip()
            e = str(reg["espanol"] or "").strip()
            s = str(reg["significado"] or "").strip()
            if q and e:
                frases.add(f"En quechua se dice: {q}.")
                if s:
                    frases.add(f"En quechua se dice: {q}. {s}")
                    frases.add(f"{q} significa {e}: {s}")
                    frases.add(f"Practiquemos una palabra. En quechua se dice {q}. Significa {e}: {s}. Repítela, por favor.")
                    frases.add(f"Otra palabra: {q} significa {e}, {s}. Repítela, por favor.")
                else:
                    frases.add(f"{q} significa {e}.")
                    frases.add(f"Practiquemos una palabra. En quechua se dice {q}. Significa {e}. Repítela, por favor.")
                frases.add(f"Escucha otra vez: {q}, que significa {e}. Repítela, por favor.")
                # Lo que Yura responde de verdad a "¿cómo se dice...?" y "¿qué significa...?"
                for idioma in ("espanol", "quechua"):
                    try:
                        frases.add(conversacion._texto_consulta(reg, idioma))
                    except Exception:
                        pass
                frases.add(f"Muy bien. Dijiste {q} correctamente. Di siguiente para practicar otra palabra, o salir para terminar.")

        # Listas por tema ("los colores", "los números del uno al nueve") y su
        # continuación cuando dicen "sí".
        for palabra in conversacion._TEMAS:
            articulo = "la" if palabra == "familia" else ("las" if palabra in ("frutas", "comidas", "herramientas") else "los")
            pedido = f"dime {articulo} {palabra} en quechua" if palabra != "cuerpo" else "dime las partes del cuerpo"
            conversacion._ULTIMO_TEMA.update(tema=None, desde=0, hasta=0.0)
            respuesta = conversacion._responder_tema(conversacion._normalizar_texto(pedido))
            for _ in range(8):
                if not respuesta:
                    break
                frases.add(respuesta["respuesta"])
                respuesta = conversacion._responder_tema("si")
        for hasta in ("cinco", "nueve", "diez"):
            respuesta = conversacion._responder_tema(f"dime los numeros del uno al {hasta}")
            if respuesta:
                frases.add(respuesta["respuesta"])

    return sorted(frases)


def generar_audio_sofia(texto, ruta_salida, ya_preparado=False):
    """Genera audio con Edge-TTS y lo convierte a WAV 24kHz mono.
    ya_preparado: el texto ya es el que se manda a la voz (una oración)."""
    edge_tts = os.path.join(RAIZ, ".venv", "bin", "edge-tts")
    if not os.path.exists(edge_tts):
        edge_tts = "edge-tts"

    texto_voz = texto if ya_preparado else formatear_texto_voz(pronunciaciones.texto_para_hablar(texto))

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_mp3:
        ruta_mp3 = temp_mp3.name

    try:
        cmd_tts = [
            edge_tts,
            *voz_sofia.argumentos_edge(VOZ_SOFIA, texto_voz),
            "--write-media", ruta_mp3
        ]
        res = subprocess.run(cmd_tts, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=25)
        if res.returncode != 0 or not os.path.exists(ruta_mp3) or os.path.getsize(ruta_mp3) == 0:
            return False

        # Convertir a WAV 24000 Hz pcm_s16le mono
        cmd_ffmpeg = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", ruta_mp3,
            "-acodec", "pcm_s16le",
            "-ar", "24000",
            "-ac", "1",
            ruta_salida
        ]
        res_ff = subprocess.run(cmd_ffmpeg, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
        return res_ff.returncode == 0 and os.path.exists(ruta_salida) and os.path.getsize(ruta_salida) > 0
    finally:
        try:
            os.remove(ruta_mp3)
        except OSError:
            pass


def main():
    os.makedirs(CARPETA_VOCES, exist_ok=True)
    modo = "todo"
    if "--sistema" in sys.argv:
        modo = "sistema"
    elif "--juego" in sys.argv:
        modo = "juego"

    frases = recolectar_frases_del_sistema(modo=modo)
    # Lo que Yura tuvo que decir sin internet y no estaba guardado.
    faltantes = voz_sofia.ruta_faltantes(CARPETA_VOCES)
    if os.path.exists(faltantes):
        with open(faltantes, encoding="utf-8") as archivo:
            frases = sorted(set(frases) | {linea.strip() for linea in archivo if linea.strip()})

    if "--resumen" in sys.argv:
        archivos_existentes = [f for f in os.listdir(CARPETA_VOCES) if f.endswith(".wav")]
        print(f"\n[RESUMEN DE CACHÉ DE SOFÍA]")
        print(f"  • Modo:                       {modo}")
        print(f"  • Total frases identificadas: {len(frases)}")
        print(f"  • Audios locales guardados:   {len(archivos_existentes)}")
        print(f"  • Cobertura actual:           {100 * len(archivos_existentes) / max(1, len(frases)):.1f} %\n")
        return

    limite = None
    for arg in sys.argv:
        if arg.startswith("--limite="):
            limite = int(arg.split("=")[1])
        elif arg == "--limite" and sys.argv.index(arg) + 1 < len(sys.argv):
            limite = int(sys.argv[sys.argv.index(arg) + 1])

    if limite:
        frases = frases[:limite]

    print(f"\n[INICIANDO PRE-GENERACIÓN DE VOCES DE SOFÍA]")
    print(f"Modo: {modo}")
    print(f"Voz: {VOZ_SOFIA}")
    print(f"Destino: {CARPETA_VOCES}")
    print(f"Frases a procesar: {len(frases)}\n")

    exitosos = 0
    ya_existentes = 0
    fallidos = 0
    inicio = time.time()

    indice = {}
    if os.path.exists(RUTA_INDICE):
        try:
            with open(RUTA_INDICE, "r", encoding="utf-8") as f:
                indice = json.load(f)
        except Exception:
            indice = {}

    for i, frase in enumerate(frases, 1):
        texto_voz = formatear_texto_voz(pronunciaciones.texto_para_hablar(frase))
        destino = ruta_cache(texto_voz)

        if destino and os.path.exists(destino) and os.path.getsize(destino) > 0:
            ya_existentes += 1
            indice[os.path.basename(destino)] = {"texto": frase, "voz": texto_voz}
            continue

        print(f"[{i}/{len(frases)}] Generando: «{frase[:45]}...»", flush=True)
        if generar_audio_sofia(frase, destino):
            exitosos += 1
            indice[os.path.basename(destino)] = {"texto": frase, "voz": texto_voz}
        else:
            fallidos += 1
            print(f"    [AVISO] No se pudo generar (¿falta conexión a internet?)")

        time.sleep(0.1)

    # Cada oración por separado: Yura arma con ellas frases que no están
    # enteras (main_robot._hablar_con_oraciones_guardadas).
    for frase in frases:
        partes = voz_sofia.oraciones(formatear_texto_voz(pronunciaciones.texto_para_hablar(frase)))
        if len(partes) < 2:
            continue
        for parte in partes:
            destino = ruta_cache(parte)
            if not destino or (os.path.exists(destino) and os.path.getsize(destino) > 0):
                continue
            if generar_audio_sofia(parte, destino, ya_preparado=True):
                exitosos += 1
                indice[os.path.basename(destino)] = {"texto": parte, "voz": parte}
            else:
                fallidos += 1
            time.sleep(0.05)

    if os.path.exists(faltantes) and not fallidos:
        os.remove(faltantes)  # ya quedaron todas con la voz de Sofía

    with open(RUTA_INDICE, "w", encoding="utf-8") as f:
        json.dump(indice, f, ensure_ascii=False, indent=2)

    total_tiempo = time.time() - inicio
    print(f"\n[LISTO en {total_tiempo:.1f} s]")
    print(f"  • Ya estaban guardados: {ya_existentes}")
    print(f"  • Nuevos generados:     {exitosos}")
    print(f"  • Fallidos:             {fallidos}")
    print(f"  • Total en disco:       {ya_existentes + exitosos} audios WAV locales en {CARPETA_VOCES}\n")


if __name__ == "__main__":
    main()
