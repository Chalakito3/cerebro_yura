#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Normalización de texto compartida por todo el cerebro de Yura.

Conserva la ñ y el apóstrofo porque en quechua cambian la palabra
(ñawi, p'unchay, sach'a); quita tildes, signos y espacios repetidos.
"""

import re
import unicodedata


_APOSTROFOS = "’‘`´ʼ"


def normalizar(texto):
    if texto is None:
        return ""

    try:
        texto = str(texto).strip().lower()
    except Exception:
        return ""

    if texto == "":
        return ""

    for apostrofo in _APOSTROFOS:
        texto = texto.replace(apostrofo, "'")

    # Proteger la ñ antes de quitar tildes (NFKD la separaría en n + ~).
    texto = texto.replace("ñ", "\x00")
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = texto.replace("\x00", "ñ")

    texto = re.sub(r"[^a-z0-9ñ'\s]", " ", texto)
    # Un apóstrofo solo vale dentro de una palabra (p'unchay), no como comilla.
    texto = re.sub(r"(?<![a-zñ])'|'(?![a-zñ])", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def palabras(texto):
    return normalizar(texto).split()


def contiene_frase(texto_normalizado, frase):
    """True si la frase aparece como palabras completas (no dentro de otra)."""
    frase = normalizar(frase)
    if not frase:
        return False
    return re.search(
        r"(?<![a-zñ'])" + re.escape(frase) + r"(?![a-zñ'])",
        texto_normalizado
    ) is not None


def pide_orden(texto_normalizado, frases):
    """True si el texto contiene alguna orden como palabras completas y sin
    negación antes ("no quiero jugar" no es una orden de jugar)."""
    for frase in frases:
        frase = normalizar(frase)
        coincidencia = re.search(
            r"(?<![a-zñ'])" + re.escape(frase) + r"(?![a-zñ'])",
            texto_normalizado
        )
        if coincidencia is None:
            continue
        antes = texto_normalizado[:coincidencia.start()].split()
        if any(negacion in antes for negacion in ("no", "nunca", "tampoco")):
            continue
        return True
    return False


_MARCADORES_PREGUNTA = (
    "como se dice",
    "como se escribe",
    "como digo",
    "como puedo decir",
    "como se pronuncia",
    "que significa",
    "que quiere decir",
    "significado de",
    "traduce",
    "traduceme",
    "traducir la palabra",
)


def es_pregunta_de_idioma(texto_normalizado):
    """Preguntas como "¿cómo se dice adiós?" tienen prioridad sobre las
    órdenes, para que la palabra consultada no se ejecute como comando."""
    return any(
        contiene_frase(texto_normalizado, marcador)
        for marcador in _MARCADORES_PREGUNTA
    )


_FORMAS_APAGATE_ESCRITAS = ("apagate", "apagarte", "apagues", "apagarse", "apaguese")

_OBJETOS_DE_APAGAR = {
    "yura", "a", "el", "la", "robot", "equipo", "computadora", "maquina",
    "por", "favor", "ya", "todo", "ahora",
}


def es_orden_apagar(texto_normalizado):
    """Reconoce la orden de apagar dirigida a Yura en cualquier forma común
    ("apágate", "¿puedes apagarte?", "apaga el robot"), pero no frases que
    solo mencionan la palabra ("no te apagues", "apagar la luz",
    "¿cómo se dice apagar?")."""
    if not texto_normalizado or es_pregunta_de_idioma(texto_normalizado):
        return False

    if pide_orden(
        texto_normalizado,
        ("apagate", "apagarte", "apagues", "apagarse", "apaguese")
    ):
        return True

    # Whisper a veces escribe "apagati" o "apágati": se comparan las formas
    # simplificadas (e = i) y sin negación antes.
    palabras_texto = texto_normalizado.split()
    for posicion, palabra in enumerate(palabras_texto):
        if simplificar_quechua(palabra) in {simplificar_quechua(f) for f in _FORMAS_APAGATE_ESCRITAS}:
            if not {"no", "nunca", "tampoco"} & set(palabras_texto[:posicion]):
                return True

    coincidencia = re.search(
        r"(?<![a-zñ'])(?:apagar|apaga)(?![a-zñ'])(.*)$",
        texto_normalizado
    )
    if coincidencia is None:
        return False
    antes = texto_normalizado[:coincidencia.start()].split()
    if any(negacion in antes for negacion in ("no", "nunca", "tampoco")):
        return False
    resto = coincidencia.group(1).split()
    return all(palabra in _OBJETOS_DE_APAGAR for palabra in resto)


_ALUCINACIONES_WHISPER = (
    "subtitulos", "subtitulado", "amara org", "gracias por ver",
    "suscribete", "suscribanse", "no olvides suscribirte",
    "gracias por su atencion", "musica",
)


def es_alucinacion_whisper(texto_normalizado):
    """Frases que Whisper inventa con ruido o silencio (vienen de subtítulos
    de videos con los que fue entrenado); no las dijo nadie."""
    return any(
        contiene_frase(texto_normalizado, frase)
        for frase in _ALUCINACIONES_WHISPER
    )


def es_afirmacion(texto_normalizado):
    """"Sí", "sí, apágate", "ari", "claro", "confirmo"... en las primeras
    palabras de la respuesta y sin un "no"."""
    palabras_texto = texto_normalizado.split()[:4]
    if "no" in palabras_texto:
        return False
    return bool(set(palabras_texto) & {
        "si", "ari", "confirmo", "claro", "dale", "apagate", "okay", "ok"
    })


def es_negacion(texto_normalizado):
    palabras_texto = texto_normalizado.split()[:4]
    return bool(set(palabras_texto) & {"no", "mana", "cancela", "cancelar", "espera"})


# Palabras quechuas frecuentes que se le dan al reconocedor como pista
# cuando no hay una actividad con palabras propias (menú, conversación).
PISTAS_GENERALES = (
    "rimaykullayki", "imaynalla kachkanki", "allin p'unchay", "yusulpayki",
    "ari", "mana", "ñuqa", "ñawi", "wasi", "yaku", "allqu", "misi", "inti", "puka",
)


def instruccion_reconocedor(pistas=None):
    """Texto de contexto para el reconocedor de voz (Whisper o Gemini).

    Con pistas de vocabulario, Whisper small pasó del 77 % al 93 % de frases
    entendidas en 96 audios de prueba (27/09/2026). Las pistas deben incluir
    varias palabras, no solo la respuesta esperada, para no favorecerla.
    """
    palabras = [str(p).strip() for p in (pistas or PISTAS_GENERALES) if str(p or "").strip()]
    return (
        "Español boliviano con palabras en quechua. Un estudiante habla con "
        "el robot educativo Yura. Órdenes: jugar, traducir, conversar, "
        "enséñame quechua, apágate, sí, no, despierta, silencio, volver al menú. "
        "Palabras en quechua: " + ", ".join(dict.fromkeys(palabras)) + "."
    )


def simplificar_quechua(texto, ll="l"):
    """Forma aproximada para comparar lo que se escuchó con lo esperado.

    El reconocimiento de voz no escribe apóstrofos ni distingue q/k o las
    vocales e/o frente a i/u (variantes de escritura), así que se igualan.
    La "ll" se oye como "l" o como "y" según el hablante: ll elige cuál.
    """
    # La "ch" se conserva aparte: si no, chay (ese) y kay (este) quedaban
    # iguales, porque la c pasa a k y la h se borra.
    texto = normalizar(texto).replace("'", "").replace("ch", "\x01")
    reemplazos = (
        # ph/th antes que "hu": si no, phuyu quedaba "pwyu" y no aceptaba "puyu".
        ("ph", "p"), ("th", "t"),
        ("qh", "k"), ("kh", "k"), ("q", "k"), ("c", "k"),
        ("hu", "w"), ("gu", "w"), ("g", "k"), ("v", "w"), ("b", "w"),
        # El reconocedor escribe con letras del castellano: "Base" por wasi,
        # "Jaku" por yaku, "Algo"/"Ayku" por allqu (medido con 96 audios, 27/09/2026).
        ("ll", ll), ("j", "y"),
        ("ñ", "n"), ("e", "i"), ("o", "u"), ("h", ""),
    )
    for original, reemplazo in reemplazos:
        texto = texto.replace(original, reemplazo)
    texto = texto.replace("\x01", "ch")
    return re.sub(r"\s+", " ", texto).strip()


def distancia_edicion(a, b):
    anterior = list(range(len(b) + 1))
    for i, letra_a in enumerate(a, 1):
        actual = [i]
        for j, letra_b in enumerate(b, 1):
            actual.append(min(
                anterior[j] + 1,
                actual[j - 1] + 1,
                anterior[j - 1] + (letra_a != letra_b)
            ))
        anterior = actual
    return anterior[-1]


def respuesta_quechua_correcta(respuesta, correcta, variantes=()):
    """Evalúa una respuesta hablada contra la palabra quechua esperada.

    Acepta la palabra exacta (con variantes de escritura), la palabra dentro
    de una frase ("se dice allqu") y, en palabras largas, un error pequeño de
    reconocimiento. Rechaza palabras distintas aunque se parezcan
    (tawa/wawa, inti/anti).

    variantes: cómo escribió el reconocedor la palabra cuando la docente la
    pronunció bien (modo docente). Se aceptan solo iguales, sin tolerancia.
    """
    if any(
        _coincide_simplificada(simplificar_quechua(respuesta, ll), simplificar_quechua(correcta, ll))
        for ll in ("l", "y")
    ):
        return True
    respuesta_simple = simplificar_quechua(respuesta)
    for variante in variantes or ():
        variante_simple = simplificar_quechua(variante)
        if variante_simple and (
            respuesta_simple == variante_simple
            or re.search(r"(?<![a-z])" + re.escape(variante_simple) + r"(?![a-z])", respuesta_simple)
        ):
            return True
    return False


def _coincide_simplificada(respuesta, correcta):
    if not respuesta or not correcta:
        return False

    if respuesta == correcta:
        return True

    if re.search(r"(?<![a-z])" + re.escape(correcta) + r"(?![a-z])", respuesta):
        return True

    sin_espacios_respuesta = respuesta.replace(" ", "")
    sin_espacios_correcta = correcta.replace(" ", "")
    if sin_espacios_respuesta == sin_espacios_correcta:
        return True

    tolerancia = 0 if len(sin_espacios_correcta) <= 4 else 1 if len(sin_espacios_correcta) <= 8 else 2
    return distancia_edicion(sin_espacios_respuesta, sin_espacios_correcta) <= tolerancia
