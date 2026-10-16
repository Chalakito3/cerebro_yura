#!/usr/bin/env python3
"""Prepara con la voz de Sofía sin internet (voz_sofia_local.py) las oraciones
que Yura dice y que no tienen todavía el audio real de Sofía guardado
(basedatos/voces_sofia/), más las anotadas en faltantes.txt. Así suenan al
instante aunque no haya internet o Microsoft no responda.

Uso (en la Pi, ≈ 8 s por oración):
    python basedatos/pregenerar_voz_sofia_local.py
"""
import os
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "basedatos"))

import pregenerar_voces_sofia as sofia  # noqa: E402
import pronunciaciones  # noqa: E402
import voz_sofia  # noqa: E402
import voz_sofia_local  # noqa: E402


def oraciones_que_faltan():
    frases = set(sofia.recolectar_frases_del_sistema("todo"))
    faltantes = voz_sofia.ruta_faltantes(sofia.CARPETA_VOCES)
    if os.path.exists(faltantes):
        with open(faltantes, encoding="utf-8") as archivo:
            frases.update(linea.strip() for linea in archivo if linea.strip())
    falta = set()
    for frase in frases:
        texto_voz = sofia.formatear_texto_voz(pronunciaciones.texto_para_hablar(frase))
        if os.path.exists(sofia.ruta_cache(texto_voz)):
            continue
        for oracion in voz_sofia.oraciones(texto_voz) or [texto_voz]:
            if os.path.exists(sofia.ruta_cache(oracion)):
                continue
            if not os.path.exists(voz_sofia_local.ruta_local(oracion)):
                falta.add(oracion)
    return sorted(falta)


def main():
    if not voz_sofia_local.activa():
        print("Faltan los modelos de la voz sin internet (ver voz_sofia_local.py).")
        return 1
    falta = oraciones_que_faltan()
    print(f"Oraciones por preparar: {len(falta)}", flush=True)
    inicio = time.time()
    voz_sofia_local.cargar_modelos()
    print(f"Modelos cargados en {time.time() - inicio:.0f} s", flush=True)
    hechas = 0
    for numero, oracion in enumerate(falta, 1):
        t = time.time()
        try:
            voz_sofia_local.convertir(oracion, voz_sofia_local.ruta_local(oracion))
            hechas += 1
            print(f"[{numero}/{len(falta)}] {time.time() - t:.1f} s  {oracion[:70]}", flush=True)
        except Exception as exc:
            print(f"[{numero}/{len(falta)}] FALLÓ ({exc}): {oracion[:70]}", flush=True)
    print(f"Listo: {hechas}/{len(falta)} en {(time.time() - inicio) / 60:.1f} min", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
