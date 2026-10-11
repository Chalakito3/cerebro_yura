"""Mide cuánto aprendió Yura de los audios de la docente (meta: 80 %).

1. ENTENDER: de cada grabación de la docente, el reconocedor produjo una
   transcripción en 3 situaciones (menú, juego, sin pistas). Para cada una se
   pregunta si el juego la acepta como la palabra correcta usando SOLO lo
   aprendido de las otras situaciones y grabaciones (no de sí misma), para no
   medir de forma tramposa.
2. PRONUNCIAR: de cada palabra, si la voz de Yura se entiende como la palabra
   correcta (antes: con la escritura normal; ahora: con la forma aprendida).
   Viene de basedatos/aprender_pronunciacion.py.

Uso:  python basedatos/medir_aprendizaje.py
"""
import os
import sqlite3
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pronunciaciones  # noqa: E402
import texto as texto_util  # noqa: E402

META = 80


def medir():
    conexion = sqlite3.connect(f"file:{pronunciaciones.RUTA_DB}?mode=ro", uri=True)
    grabadas = conexion.execute(
        f"SELECT id, palabra_frase, transcripcion, sirve_para_calificar FROM {pronunciaciones.TABLA}"
    ).fetchall()
    aprendidas = conexion.execute(
        f"SELECT id_grabacion, palabra_frase, contexto, transcripcion FROM {pronunciaciones.TABLA_APRENDIDAS}"
    ).fetchall()
    voz = conexion.execute(
        f"SELECT palabra_frase, texto_para_voz, se_entiende, se_entendia_original FROM {pronunciaciones.TABLA_VOZ}"
    ).fetchall()
    conexion.close()

    # Todo lo escuchado de la docente: (id_grabacion, contexto, palabra, texto).
    fuentes = [(g[0], "guardada", g[1], g[2] or "") for g in grabadas if g[3]]
    fuentes += [(a[0], a[2], a[1], a[3] or "") for a in aprendidas]

    entender = {}
    fallas = []
    for id_grabacion, contexto, palabra, escuchado in [(a[0], a[2], a[1], a[3] or "") for a in aprendidas]:
        otras = [
            t for (i, c, p, t) in fuentes
            if p == palabra and not (i == id_grabacion and c == contexto)
            and t and pronunciaciones.variante_segura(t, palabra)
        ]
        antes = texto_util.respuesta_quechua_correcta(escuchado, palabra)
        ahora = pronunciaciones.respuesta_aceptada(escuchado, palabra, otras)
        cuenta = entender.setdefault(contexto, [0, 0, 0])
        cuenta[0] += antes
        cuenta[1] += ahora
        cuenta[2] += 1
        if not ahora:
            fallas.append((contexto, palabra, escuchado))

    lineas = ["ENTENDER (audios de la docente; lo aprendido de otras situaciones)"]
    total_ahora = total = 0
    for contexto in ("menu", "juego", "sin_pistas"):
        if contexto in entender:
            antes, ahora, n = entender[contexto]
            total_ahora += ahora
            total += n
            lineas.append(f"  {contexto:10}: antes {100 * antes / n:3.0f} %  ahora {100 * ahora / n:3.0f} %  ({ahora}/{n})")
    if total:
        lineas.append(f"  TOTAL     : ahora {100 * total_ahora / total:.0f} %  (meta {META} %)"
                      f" -> {'CUMPLE' if 100 * total_ahora / total >= META else 'NO CUMPLE'}")
    lineas.append("")
    lineas.append("PRONUNCIAR (la voz de Yura se entiende como la palabra correcta)")
    if voz:
        antes = sum(bool(v[3]) for v in voz if v[3] is not None)
        ahora = sum(bool(v[2]) for v in voz if v[2] is not None)
        n = sum(v[2] is not None for v in voz)
        if n:
            lineas.append(f"  antes {100 * antes / n:.0f} %  ahora {100 * ahora / n:.0f} %  ({ahora}/{n} palabras)"
                          f" (meta {META} %) -> {'CUMPLE' if 100 * ahora / n >= META else 'NO CUMPLE'}")
            lineas.append("  Palabras que la voz de Yura todavía no logra: "
                          + ", ".join(v[0] for v in voz if v[2] == 0))
    else:
        lineas.append("  (todavía no se entrenó: basedatos/aprender_pronunciacion.py)")
    lineas.append("")
    lineas.append("No entendidas (situación, palabra, lo que escribió el reconocedor):")
    lineas += [f"  {c:10} {p:22} «{t}»" for c, p, t in sorted(fallas)]
    return "\n".join(lineas)


if __name__ == "__main__":
    print(medir())
