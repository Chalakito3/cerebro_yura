#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mensajes de depuración y privacidad del registro de Yura.

Por defecto el registro (journalctl) no guarda lo que dicen los estudiantes
ni los mensajes técnicos de cada bloque de audio. Para diagnosticar un
problema se activa todo con la variable YURA_DEBUG=1.
"""

import os


def activa():
    return os.environ.get("YURA_DEBUG", "0").strip() == "1"


def depurar(*partes):
    """Mensaje técnico: solo se imprime con YURA_DEBUG=1."""
    if activa():
        print(*partes, flush=True)


def voz(etiqueta, texto):
    """Lo que dijo un estudiante: completo solo con YURA_DEBUG=1; si no,
    se registra únicamente cuántas palabras dijo."""
    if activa():
        print(f"{etiqueta}: {texto}", flush=True)
    else:
        print(f"{etiqueta}: ({len(str(texto or '').split())} palabras)", flush=True)
