#!/usr/bin/env python3
"""Adapta la resolución a la pantalla conectada (escritorio Wayland de la Pi).

Se ejecuta al iniciar sesión (scripts/yura-pantalla.desktop) y se queda
revisando cada pocos segundos, así que también se adapta si se cambia la
pantalla con la Pi encendida.

Regla: si la pantalla es más grande que Full HD (por ejemplo un televisor 4K),
se usa 1920x1080 para que Yura se vea grande y fluida; si no, se usa la
resolución nativa (la "preferida") de la pantalla. Siempre la mayor
frecuencia disponible para ese tamaño.

Para usar otro tamaño máximo: YURA_PANTALLA_MAX=1280x720
"""

import json
import os
import subprocess
import time

INTERVALO = 5


def leer_maximo():
    valor = os.environ.get("YURA_PANTALLA_MAX", "1920x1080")
    try:
        ancho, alto = (int(parte) for parte in valor.lower().split("x"))
        return ancho, alto
    except ValueError:
        return 1920, 1080


def leer_pantallas():
    try:
        salida = subprocess.run(
            ["wlr-randr", "--json"], capture_output=True, text=True, timeout=10
        )
        return json.loads(salida.stdout) if salida.returncode == 0 else []
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return []


def elegir_modo(modos, maximo):
    if not modos:
        return None
    preferido = next((m for m in modos if m.get("preferred")), modos[0])
    ancho_max, alto_max = maximo
    if preferido["width"] <= ancho_max and preferido["height"] <= alto_max:
        tamano = (preferido["width"], preferido["height"])
    else:
        candidatos = [
            (m["width"], m["height"])
            for m in modos
            if m["width"] <= ancho_max and m["height"] <= alto_max
            # misma forma que la pantalla (16:9, 16:10...), con margen
            and abs(m["width"] / m["height"] - preferido["width"] / preferido["height"]) < 0.05
        ]
        if not candidatos:
            return preferido
        tamano = max(candidatos, key=lambda t: t[0] * t[1])
    return max(
        (m for m in modos if (m["width"], m["height"]) == tamano),
        key=lambda m: m["refresh"],
    )


def ajustar(maximo):
    for pantalla in leer_pantallas():
        if not pantalla.get("enabled"):
            continue
        modos = pantalla.get("modes", [])
        modo = elegir_modo(modos, maximo)
        if modo is None:
            continue
        actual = next((m for m in modos if m.get("current")), None)
        clave = lambda m: (m["width"], m["height"], round(m["refresh"]))
        if actual is not None and clave(actual) == clave(modo):
            continue
        texto = f"{modo['width']}x{modo['height']}@{modo['refresh']:.6f}Hz"
        print(f"[YURA PANTALLA] {pantalla['name']}: {texto}", flush=True)
        subprocess.run(
            ["wlr-randr", "--output", pantalla["name"], "--mode", texto],
            timeout=10,
        )


def main():
    maximo = leer_maximo()
    while True:
        ajustar(maximo)
        time.sleep(INTERVALO)


if __name__ == "__main__":
    main()
