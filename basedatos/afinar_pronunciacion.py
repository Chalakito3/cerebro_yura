"""Afina la pronunciación de Yura CON SU MISMA VOZ (sin cambiar el timbre).

Pedido del equipo (29/09/2026): Yura debe mantener su voz natural y aprender a
pronunciar cada palabra lo más parecido posible al audio de la docente. La
única herramienta que no cambia la voz es CÓMO se le escribe la palabra a la
voz sintética. Este programa busca, palabra por palabra, la escritura cuyo
sonido se parece más al audio de la docente:

1. parte de las escrituras ya medidas (aprender_pronunciacion.py);
2. prueba cambios pequeños (vocales i/e y u/o, acento, k/c/qu/j/g, w/gu/u,
   h de las aspiradas, sílabas separadas con guion...);
3. genera cada una con la voz de Yura, la compara con el audio de la docente
   (DTW sobre espectro mel) y comprueba que se entienda como la palabra;
4. se queda con la mejor y repite hasta que no mejora.

La mejor escritura queda en pronunciaciones_voz (texto_para_voz) y Yura la
usa al hablar (pronunciaciones.texto_para_hablar). Límite honesto: la voz
castellana no puede producir k', q', ch' eyectivas; se acerca, no las copia.

Uso:
    python basedatos/afinar_pronunciacion.py [--rondas 5] [--procesos 2] [--palabra "Q'umir"]
"""
import argparse
import csv
import itertools
import os
import re
import sys
import time
from datetime import datetime
from multiprocessing import Pool

CARPETA = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(CARPETA))
sys.path.insert(0, CARPETA)

import aprender_pronunciacion as pron  # noqa: E402
import pronunciaciones  # noqa: E402

VOCALES = "aeiouáéíóú"
TILDE = {"a": "á", "e": "é", "i": "í", "o": "ó", "u": "ú"}
SIN_TILDE = {v: k for k, v in TILDE.items()}
PRUEBAS_POR_RONDA = 16
# Mejora mínima para cambiar la escritura normal (3 %).
MEJORA_MINIMA = 0.03
RESULTADOS = os.path.join(pron.CARPETA_EVIDENCIAS, "afinado.csv")


def _quitar_tildes(texto):
    return "".join(SIN_TILDE.get(c, c) for c in texto)


def mutaciones(escritura):
    """Cambios pequeños de una escritura (en minúsculas)."""
    base = escritura.lower()
    salida = set()
    # Vocales: el quechua tiene 3; cerca de q/j suenan más abiertas (e, o).
    for i, c in enumerate(base):
        simple = SIN_TILDE.get(c, c)
        for otra in {"i": "e", "e": "i", "u": "o", "o": "u"}.get(simple, ""):
            nueva = otra if c == simple else TILDE[otra]
            salida.add(base[:i] + nueva + base[i + 1:])
    # Acento en cada vocal, o sin acento.
    plano = _quitar_tildes(base)
    salida.add(plano)
    for i, c in enumerate(plano):
        if c in TILDE:
            salida.add(plano[:i] + TILDE[c] + plano[i + 1:])
    # Consonantes que la voz castellana puede acercar al quechua.
    cambios = [("k", "c"), ("k", "j"), ("k", "g"), ("c", "k"), ("qu", "k"), ("j", "k"), ("j", "g"),
               ("w", "gu"), ("w", "u"), ("w", "hu"), ("gu", "w"), ("y", "ll"), ("ll", "y"), ("ll", "l"),
               ("ch", "sh"), ("s", "z"), ("p", "b"), ("t", "d"), ("kh", "k"), ("ph", "p"), ("th", "t")]
    for viejo, nuevo in cambios:
        for coincidencia in re.finditer(re.escape(viejo), base):
            i = coincidencia.start()
            salida.add(base[:i] + nuevo + base[i + len(viejo):])
    # Aspiración: "k" -> "kh"; sílabas separadas (pausa corta, como el golpe
    # de las eyectivas: k'acha -> "k-acha").
    for i, c in enumerate(base):
        if c in "kptc" and i + 1 < len(base) and base[i + 1] in VOCALES:
            salida.add(base[:i + 1] + "h" + base[i + 1:])
            if i > 0:
                salida.add(base[:i] + "-" + base[i:])
    salida.discard(base)
    return [s[:1].upper() + s[1:] for s in salida if s and len(s) <= 40]


def _leer_medidas_previas(palabra):
    """Escrituras ya medidas por aprender_pronunciacion.py (sin repetirlas)."""
    ruta = os.path.join(pron.CARPETA_EVIDENCIAS, "resultados.csv")
    if not os.path.exists(ruta):
        return {}, {}
    with open(ruta, encoding="utf-8") as entrada:
        for fila in csv.reader(entrada):
            if fila and fila[0] == palabra and len(fila) > 7:
                puntajes, entendidas = {}, {}
                for parte in fila[7].split(" | "):
                    opcion, _, valor = parte.rpartition("=")
                    try:
                        puntajes[opcion] = float(valor.rstrip("*"))
                        entendidas[opcion] = not valor.endswith("*")
                    except ValueError:
                        continue
                return puntajes, entendidas
    return {}, {}


def afinar_palabra(argumentos):
    palabra, rondas = argumentos
    audio = pronunciaciones.audio_de(palabra)
    if not audio:
        return None
    rasgos_docente = pron.rasgos(audio)
    todas = [g["palabra_frase"] for g in pronunciaciones.grabaciones()]
    otras = sorted({p for p in todas if p != palabra})
    trabajo = os.path.join(pron.CARPETA_EVIDENCIAS, f"afinado_{os.getpid()}")
    os.makedirs(trabajo, exist_ok=True)
    puntajes, entendidas = _leer_medidas_previas(palabra)

    def ruta_de(opcion):
        return os.path.join(trabajo, pron._nombre_archivo(opcion) + ".wav")

    def medir(opcion, forzar=False):
        # En la búsqueda solo se compara el sonido con el audio de la docente
        # (rápido); el reconocedor confirma solo las mejores al final.
        if opcion in puntajes or not (forzar or pron.candidata_permitida(opcion, palabra)):
            return
        try:
            pron.voz_de_yura(opcion, ruta_de(opcion))
            puntajes[opcion] = pron.distancia_dtw(pron.rasgos(ruta_de(opcion)), rasgos_docente)
        except Exception:
            pass

    def se_entiende(opcion):
        if opcion not in entendidas:
            if not os.path.exists(ruta_de(opcion)):
                pron.voz_de_yura(opcion, ruta_de(opcion))
            entendidas[opcion] = pron.se_entiende(ruta_de(opcion), palabra, otras)[0]
        return entendidas[opcion]

    # Se sigue desde la mejor escritura ya guardada (entrenamientos anteriores),
    # no solo desde la normal: así cada entrenamiento avanza sobre el anterior.
    # La guardada se mide aunque no cumpla las reglas de búsqueda (p. ej. la
    # escritura oficial de Laime "jari" por Qhari): es con la que se compara.
    guardada = pronunciaciones.voz_de(palabra)[0]
    medir(guardada, forzar=True)
    for opcion in dict.fromkeys([palabra] + pron.candidatas(palabra, [])):
        medir(opcion)
    if palabra not in puntajes:
        return None
    original = puntajes[palabra]

    def puntaje(opcion):
        return puntajes[opcion]

    for _ in range(rondas):
        mejores = sorted((o for o in puntajes if pron.candidata_permitida(o, palabra)), key=puntaje)[:3]
        nuevas = [m for m in itertools.chain.from_iterable(mutaciones(o) for o in mejores)
                  if m not in puntajes and pron.candidata_permitida(m, palabra)]
        antes = puntaje(mejores[0])
        for opcion in nuevas[:PRUEBAS_POR_RONDA]:
            medir(opcion)
        if min(puntaje(o) for o in puntajes if pron.candidata_permitida(o, palabra)) >= antes - 1e-6:
            break  # esta ronda no mejoró: se detiene
    # La más parecida que el reconocedor entienda como la palabra correcta.
    se_entiende(palabra)
    mejor = palabra
    for opcion in sorted((o for o in puntajes if pron.candidata_permitida(o, palabra)), key=puntaje)[:5]:
        if opcion == palabra or se_entiende(opcion):
            mejor = opcion
            break
    if mejor != palabra and puntajes[mejor] > original * (1 - MEJORA_MINIMA):
        mejor = palabra
    # Lo ya guardado (afinado antes, u oficial de Laime) solo se reemplaza si
    # lo nuevo es claramente más parecido que eso, no solo que la normal.
    # Se protege aunque el reconocedor no la entienda en esta corrida (le
    # pasaba a "Jukú": el cambio empeoraba el parecido).
    if guardada in puntajes and guardada != mejor:
        if puntajes[mejor] > puntajes[guardada] * (1 - MEJORA_MINIMA):
            mejor = guardada
    # Audio "después" para escuchar.
    base = os.path.join(pron.CARPETA_EVIDENCIAS, pron._nombre_archivo(palabra))
    try:
        pron.voz_de_yura(mejor, base + "_3_yura_ahora.wav")
    except Exception:
        pass
    for archivo in os.listdir(trabajo):
        os.remove(os.path.join(trabajo, archivo))
    os.rmdir(trabajo)
    return {
        "palabra": palabra, "escritura": mejor, "original": original, "ahora": puntajes[mejor],
        "entendia": entendidas.get(palabra, False), "entiende": entendidas.get(mejor, False),
        "probadas": len(puntajes),
    }


def guardar(resultado):
    if pronunciaciones.voz_de(resultado["palabra"])[1]:
        return  # la fijó la docente: no se cambia
    with pronunciaciones._conectar() as conexion:
        conexion.execute(
            f"INSERT OR IGNORE INTO {pronunciaciones.TABLA_VOZ} (palabra_frase, texto_para_voz, fecha) VALUES (?, ?, ?)",
            (resultado["palabra"], resultado["palabra"], datetime.now().isoformat(timespec="seconds")),
        )
        conexion.execute(
            f"UPDATE {pronunciaciones.TABLA_VOZ} SET texto_para_voz = ?, parecido = ?, parecido_original = ?, "
            "se_entiende = ?, se_entendia_original = ?, fecha = ? WHERE palabra_frase = ?",
            (resultado["escritura"], resultado["ahora"], resultado["original"], int(resultado["entiende"]),
             int(resultado["entendia"]), datetime.now().isoformat(timespec="seconds"), resultado["palabra"]),
        )


def main():
    parametros = argparse.ArgumentParser()
    parametros.add_argument("--rondas", type=int, default=5)
    parametros.add_argument("--procesos", type=int, default=2)
    parametros.add_argument("--palabra")
    opciones = parametros.parse_args()
    palabras = sorted({g["palabra_frase"] for g in pronunciaciones.grabaciones()})
    if opciones.palabra:
        palabras = [opciones.palabra]
    inicio = time.time()
    resultados = []
    nuevo = not os.path.exists(RESULTADOS)
    with open(RESULTADOS, "a", encoding="utf-8", newline="") as salida, Pool(opciones.procesos) as grupo:
        escritor = csv.writer(salida)
        if nuevo:
            escritor.writerow(["palabra", "escritura_para_la_voz", "distancia_original", "distancia_ahora",
                               "se_entendia", "se_entiende", "escrituras_probadas"])
        for numero, resultado in enumerate(grupo.imap_unordered(afinar_palabra, [(p, opciones.rondas) for p in palabras]), 1):
            if not resultado:
                continue
            guardar(resultado)
            resultados.append(resultado)
            mejora = 100 * (resultado["original"] - resultado["ahora"]) / resultado["original"]
            escritor.writerow([resultado["palabra"], resultado["escritura"], f"{resultado['original']:.3f}",
                               f"{resultado['ahora']:.3f}", resultado["entendia"], resultado["entiende"], resultado["probadas"]])
            salida.flush()
            print(f"[{numero}/{len(palabras)}] {resultado['palabra']} -> «{resultado['escritura']}» "
                  f"({mejora:.0f} % más parecida, {resultado['probadas']} escrituras probadas, "
                  f"se entiende: {'sí' if resultado['entiende'] else 'no'})", flush=True)
    if resultados:
        n = len(resultados)
        mejoradas = sum(r["ahora"] < r["original"] for r in resultados)
        entienden = sum(r["entiende"] for r in resultados)
        media_antes = sum(r["original"] for r in resultados) / n
        media_ahora = sum(r["ahora"] for r in resultados) / n
        print(f"\nListo en {time.time() - inicio:.0f} s. Palabras: {n}. Más parecidas a la docente que con la "
              f"escritura normal: {mejoradas} ({100 * mejoradas / n:.0f} %). Se entienden: {entienden} "
              f"({100 * entienden / n:.0f} %). Distancia media al audio: {media_antes:.2f} -> {media_ahora:.2f}.")


if __name__ == "__main__":
    main()
