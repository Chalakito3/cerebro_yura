"""Yura aprende a escuchar las órdenes con la voz de quien la usa (Vosk).

Vosk (el reconocedor de la Raspberry Pi, sin GPU) no tiene en su vocabulario
palabras como "apágate" o "Yura", así que las escribe con otras que sí conoce
("gate", "para date", "jura"). Cada voz se deforma distinto. Este programa
le pide a la persona decir cada orden varias veces, anota cómo la escribió
Vosk y lo guarda en basedatos/ordenes_aprendidas_vosk.json. Al usarla, Yura
convierte esas escrituras en la orden (pronunciaciones.afinar_vosk).

Para que no haya órdenes falsas, solo se aprende lo que Vosk escribió igual
en al menos 2 de las veces que se dijo la orden (una grabación que captó otra
cosa no cuenta), y no se aprende lo que:
- Vosk ya escribe bien (no hace falta),
- se escuchó igual para dos órdenes distintas (sería ambiguo),
- es una palabra quechua del diccionario o es muy corto (menos de 3 letras).
"apágate" igual pide confirmar con "sí" antes de apagar.

Detener a Yura antes (usa el mismo micrófono):  systemctl --user stop yura
Uso:
    python basedatos/entrenar_ordenes.py                 # todas las órdenes, 3 veces
    python basedatos/entrenar_ordenes.py --veces 5
    python basedatos/entrenar_ordenes.py --orden apagate
    python basedatos/entrenar_ordenes.py --borrar        # olvida lo aprendido
"""
import argparse
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pronunciaciones  # noqa: E402
import texto as texto_util  # noqa: E402

# Orden (como la entiende Yura) -> cómo se le pide a la persona que la diga.
ORDENES = {
    "apagate": "Apágate",
    "si": "Sí",
    "no": "No",
    "jugar": "Jugar",
    "traducir": "Traducir",
    "conversar": "Conversar",
    "despierta": "Despierta",
    "silencio": "Silencio",
    "volver al menu": "Volver al menú",
    "repetir": "Repetir",
    # Movimiento del cuerpo (texto.orden_movimiento)
    "camina hacia adelante": "Camina hacia adelante",
    "camina hacia atras": "Camina hacia atrás",
    "gira a la izquierda": "Gira a la izquierda",
    "gira a la derecha": "Gira a la derecha",
    "para": "Para",
}


def puede_aprenderse(escuchado, orden):
    """Si esta escritura de Vosk se puede asociar a la orden sin riesgo."""
    if len(escuchado.replace(" ", "")) < 3 or escuchado == orden:
        return False
    if escuchado in ORDENES:  # Vosk escribió otra orden: sería ambiguo
        return False
    if pronunciaciones.afinar_vosk(escuchado) == orden:  # ya se entiende
        return False
    # Lo que ya se entiende como otra orden ("apaga te" es apágate).
    if pronunciaciones.afinar_vosk(escuchado) in ORDENES or texto_util.es_orden_apagar(escuchado):
        return False
    # Ya se entiende como una orden de movimiento (la misma u otra).
    if texto_util.orden_movimiento(escuchado):
        return False
    # Una palabra quechua del diccionario no puede volverse una orden.
    afinado = pronunciaciones.afinar_vosk(escuchado)
    if texto_util.normalizar(afinado) != escuchado:
        return False
    return pronunciaciones.palabra_por_variante(escuchado) is None


def agregar(aprendidas, escuchado, orden):
    """Guarda escuchado -> orden; si ya era de otra orden, la quita (ambigua)."""
    anterior = aprendidas.get(escuchado)
    if anterior is None:
        aprendidas[escuchado] = orden
        return True
    if anterior != orden:
        aprendidas[escuchado] = None  # se oyó igual para dos órdenes
    return False


def guardar(aprendidas):
    limpias = {k: v for k, v in sorted(aprendidas.items()) if v}
    ambiguas = sorted(k for k, v in aprendidas.items() if not v)
    with open(pronunciaciones.RUTA_ORDENES_VOSK, "w", encoding="utf-8") as archivo:
        json.dump({"ordenes": limpias, "ambiguas": ambiguas}, archivo, ensure_ascii=False, indent=2)


def cargar():
    if not os.path.exists(pronunciaciones.RUTA_ORDENES_VOSK):
        return {}
    with open(pronunciaciones.RUTA_ORDENES_VOSK, encoding="utf-8") as archivo:
        datos = json.load(archivo)
    aprendidas = dict(datos.get("ordenes", {}))
    aprendidas.update({k: None for k in datos.get("ambiguas", [])})
    return aprendidas


MINIMO_REPETICIONES = 2


def entrenar(ordenes, veces):
    from vosk import KaldiRecognizer, Model, SetLogLevel

    from audio_manager import AudioManager
    from main_robot import HardwareInterface

    SetLogLevel(-1)
    modelo = Model(os.path.join(RAIZ, "model"))
    audio = AudioManager()
    voz = HardwareInterface(audio)
    aprendidas = cargar()
    nuevas = 0

    voz.hablar("Vamos a practicar. Repite cada orden cuando yo te diga.")
    for orden in ordenes:
        dicha = ORDENES[orden]
        escuchados = []
        for vez in range(1, veces + 1):
            voz.hablar(f"Di: {dicha}." if vez == 1 else f"Otra vez: {dicha}.")
            grabado = audio.grabar_hasta_silencio(espera_maxima=8.0, duracion_maxima=6.0, silencio_final=0.8)
            if not grabado:
                print(f"  {dicha} ({vez}/{veces}): no se escuchó nada", flush=True)
                continue
            reconocedor = KaldiRecognizer(modelo, 16000)
            reconocedor.AcceptWaveform(grabado + b"\x00" * int(16000 * 2 * 0.25))
            escuchado = texto_util.normalizar(json.loads(reconocedor.FinalResult()).get("text", ""))
            escuchados.append(escuchado)
            print(f"  {dicha} ({vez}/{veces}): «{escuchado}»", flush=True)
        for escuchado in dict.fromkeys(escuchados):
            movimiento = texto_util.orden_movimiento(escuchado)
            if (pronunciaciones.afinar_vosk(escuchado) == orden or escuchado == orden
                    or (orden == "apagate" and texto_util.es_orden_apagar(escuchado))
                    or (movimiento and movimiento == texto_util.orden_movimiento(orden))):
                nota = "ya se entiende"
            elif escuchados.count(escuchado) < MINIMO_REPETICIONES:
                nota = "se oyó una sola vez, no se aprende"
            elif puede_aprenderse(escuchado, orden) and agregar(aprendidas, escuchado, orden):
                nuevas += 1
                nota = "aprendido"
            else:
                nota = "no se aprende"
            print(f"  {dicha}: «{escuchado}» -> {nota}", flush=True)
        guardar(aprendidas)
    voz.hablar("Listo. Gracias, ya aprendí cómo dices las órdenes.")
    print(f"\nListo: {nuevas} escrituras nuevas en {pronunciaciones.RUTA_ORDENES_VOSK}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--veces", type=int, default=3)
    parser.add_argument("--orden", choices=sorted(ORDENES), action="append")
    parser.add_argument("--borrar", action="store_true")
    argumentos = parser.parse_args()
    if argumentos.borrar:
        if os.path.exists(pronunciaciones.RUTA_ORDENES_VOSK):
            os.remove(pronunciaciones.RUTA_ORDENES_VOSK)
        print("Órdenes aprendidas borradas.")
    else:
        import subprocess
        activa = subprocess.run(["systemctl", "--user", "is-active", "--quiet", "yura"], check=False)
        if activa.returncode == 0:
            sys.exit("Yura está encendida y usa el micrófono. Detenla antes: systemctl --user stop yura")
        entrenar(argumentos.orden or list(ORDENES), max(1, argumentos.veces))
