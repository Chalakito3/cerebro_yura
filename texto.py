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


_FORMAS_APAGATE_ESCRITAS = (
    "apagate", "apagarte", "apagues", "apagarse", "apaguese",
    # "wañuchikuy" (quechua): apágate. "Yurata wañuchikuy" es "Yura, apágate".
    "wañuchikuy",
)

_OBJETOS_DE_APAGAR = {
    "yura", "a", "el", "la", "robot", "equipo", "computadora", "maquina",
    "por", "favor", "ya", "todo", "ahora",
    # El reconocedor a veces separa "apágate" en "apaga" + "te".
    "te",
}


def es_orden_apagar(texto_normalizado):
    """Reconoce la orden de apagar dirigida a Yura en cualquier forma común
    ("apágate", "¿puedes apagarte?", "apaga el robot", "wañuchikuy",
    "Yurata wañuchikuy"), pero no frases que solo mencionan la palabra
    ("no te apagues", "apagar la luz", "¿cómo se dice apagar?")."""
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


# Movimiento del cuerpo (ESP32). Vosk sí tiene todas estas palabras.
_DIRECCIONES_MOVIMIENTO = {
    "adelante": "ADELANTE", "delante": "ADELANTE", "enfrente": "ADELANTE",
    "atras": "ATRAS", "detras": "ATRAS",
    "izquierda": "IZQUIERDA",
    "derecha": "DERECHA",
}
_VERBOS_MOVIMIENTO = {
    "camina", "caminar", "camine", "avanza", "avanzar", "avance", "anda", "andar",
    "ve", "vete", "vaya", "ir", "muevete", "mueve", "moverte", "muevase",
    "retrocede", "retroceder", "regresa", "gira", "girar", "gire", "voltea",
    "voltear", "dobla", "doblar", "vamos", "hacia",
}
# Verbos que ya dicen la dirección sin nombrarla.
_VERBOS_CON_DIRECCION = {
    "camina": "ADELANTE", "avanza": "ADELANTE", "avanzar": "ADELANTE",
    "retrocede": "ATRAS", "retroceder": "ATRAS",
}
# "Para" o "alto" son palabras comunes ("para mi mamá", "habla más alto"):
# solo cuentan dichas solas. "Detente" o "no te muevas" valen en cualquier frase.
_ALTO_SOLO = {
    "para", "parate", "alto", "quieta", "quieto", "frena", "stop", "basta",
    "detenerse", "para ya", "alto ahi", "ya para", "quedate quieta", "quedate ahi",
}
_ALTO_EN_FRASE = ("detente", "deten", "detenerte", "no te muevas", "frena", "frenate", "parate")
# "Yura" no está en Vosk: la escribe "jura" o "llora", y el afinado vuelve "llora" en "Yuraq".
_RELLENO_MOVIMIENTO = {"yura", "yuraq", "jura", "llora", "por", "favor", "ya", "ahora", "un", "poco", "mas", "la", "a", "el", "al"}


def orden_movimiento(texto_normalizado):
    """La orden de movimiento dicha a Yura: "ADELANTE", "ATRAS", "IZQUIERDA",
    "DERECHA", "ALTO", o None.

    "camina hacia adelante", "gira a la derecha", "retrocede", "para",
    "Yura, detente". No cuenta "no camines", "¿cómo se dice derecha?" ni
    frases donde "para" no es la orden ("para mi mamá")."""
    if not texto_normalizado or es_pregunta_de_idioma(texto_normalizado):
        return None
    palabras_texto = texto_normalizado.split()
    nucleo = [p for p in palabras_texto if p not in _RELLENO_MOVIMIENTO]
    if " ".join(nucleo) in _ALTO_SOLO or texto_normalizado in _ALTO_SOLO:
        return "ALTO"
    if any(contiene_frase(texto_normalizado, frase) for frase in _ALTO_EN_FRASE):
        return "ALTO"
    if {"no", "nunca"} & set(palabras_texto):
        return None
    direcciones = [_DIRECCIONES_MOVIMIENTO[p] for p in palabras_texto if p in _DIRECCIONES_MOVIMIENTO]
    verbos = [p for p in palabras_texto if p in _VERBOS_MOVIMIENTO]
    if len(set(direcciones)) == 1 and (verbos or len(nucleo) <= 2):
        return direcciones[0]
    if not direcciones and len(nucleo) == 1 and nucleo[0] in _VERBOS_CON_DIRECCION:
        return _VERBOS_CON_DIRECCION[nucleo[0]]
    return None


_ALUCINACIONES_WHISPER = (
    "subtitulos", "subtitulado", "amara org", "gracias por ver",
    "suscribete", "suscribanse", "no olvides suscribirte",
    "gracias por su atencion", "musica",
)


# Con muy poca voz, Whisper copia partes de las instrucciones que se le dan
# (instruccion_reconocedor): "ordenes" al grabar juk (27/09/2026).
_ECOS_DE_INSTRUCCION = ("ordenes", "palabras en quechua", "espanol boliviano")


def es_alucinacion_whisper(texto_normalizado):
    """Frases que Whisper inventa con ruido o silencio (vienen de subtítulos
    de videos con los que fue entrenado, o de sus propias instrucciones);
    no las dijo nadie."""
    sin_signos = texto_normalizado.replace(":", " ").strip()
    return (
        any(contiene_frase(texto_normalizado, frase) for frase in _ALUCINACIONES_WHISPER)
        or any(sin_signos == eco or sin_signos.startswith(eco + " ") for eco in _ECOS_DE_INSTRUCCION)
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
    "rimaykullayki", "imaynalla kachkanki", "allin p'unchay", "allillanmi",
    "kusisqam", "imataq sutiyki", "sutiymi", "maymantataq", "mashkha watayuq",
    "munani", "ama llakikuychu", "kuska yachakusun", "allquchaymi", "misichaymi",
    "chiri", "rupay", "yachaywasi", "pukllay", "yusulpayki", "sulpayki",
    "tupananchiskama", "ari", "mana", "ñuqa", "ñawi", "wasi", "yaku", "allqu",
    "misi", "inti", "puka", "q'illu", "qullqi", "yuraq"
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
    texto = normalizar(texto).replace("'", "")
    # Escritura castellana del reconocedor (28/09/2026): "quilla" por killa,
    # "hatung" por jatun, "uzpi" por uspi.
    texto = re.sub(r"qu(?=[ei])", "k", texto)
    texto = re.sub(r"ng\b", "n", texto)
    # La i del inicio escrita como la palabra "y": «y maynaya» por imaynalla.
    texto = re.sub(r"^y\s+(?=[a-zñ])", "i", texto)
    # La ll escrita "ly" o "li" + vocal: «tolyu» por tullu, «osilio» por k'usillu.
    texto = re.sub(r"l+y(?=[aeiou])|l+i(?=[aou])", "ll", texto)
    texto = texto.replace("z", "s").replace("ch", "\x01")
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
    # "taua" y "uira" por tawa y wira; "chai" y "kaai" por chay y kay.
    texto = re.sub(r"(?<=[aiu])u(?=[ai])", "w", texto)
    texto = re.sub(r"\bu(?=[ai])", "w", texto)
    texto = re.sub(r"(?<=[aiu])i(?![aiu])", "y", texto)
    # Letras repetidas ("pukku", "kaay") valen como una.
    texto = re.sub(r"([a-z])\1+", r"\1", texto)
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


# ------------------------------------------------------------------
# Lo que Yura nunca debe decir (pedido del equipo, 29/09/2026)
# ------------------------------------------------------------------

# Palabras muy comunes de otros idiomas. Yura habla solo castellano y quechua.
_OTROS_IDIOMAS = {
    # inglés
    "the", "we", "you", "your", "can", "if", "another", "word", "practice", "let's", "lets", "is", "are",
    "and", "what", "how", "hello", "please", "try", "again", "good", "great", "it", "this", "that", "with",
    "for", "of", "to", "do", "don't", "yes", "okay", "thanks", "thank", "say", "learn", "means", "would", "like",
    # portugués
    "você", "voce", "não", "obrigado", "obrigada", "olá", "também", "então", "muito", "bem-vindo",
    # francés
    "vous", "nous", "est", "avec", "bonjour", "merci", "oui", "très", "c'est", "je",
    # italiano y alemán
    "grazie", "ciao", "sono", "und", "nicht", "danke", "ich", "ist",
}
# Una sola de estas basta para saber que la frase no es castellano.
_OTROS_IDIOMAS_SEGURAS = {"the", "you", "your", "hello", "please", "thanks", "you're", "you'll",
                          "você", "obrigado", "bonjour", "merci", "grazie", "danke"}

# Compras, ventas, dinero y publicidad: Yura es para niños en la escuela.
_COMPRAS = re.compile(
    r"\b(compr(?!end)\w*|vend(?!r)\w*|venta\w*|precio\w*|tienda\w*|oferta\w*|descuento\w*|"
    r"pag(?:a|ar|as|an|ues|ue|ó|o|ado)\b|p[aá]gal\w*|cuesta (?:poco|mucho|solo|nada|\d)|cost[oó]\b|barat\w*|publicidad|anuncio\w*|patrocin\w*|suscrib\w*|"
    r"producto\w*|marca\w*|dinero|d[oó]lar\w*|bolivianos?|bs\.?|amazon|mercado ?libre|"
    r"descarg\w* (?:la|el) app\w*|link|enlace)\b",
    re.IGNORECASE,
)


def frase_prohibida(oracion):
    """True si la oración está en otro idioma o habla de comprar/vender."""
    palabras = {p.strip(".,;:!?¿¡\"'“”()").lower() for p in oracion.split()}
    if palabras & _OTROS_IDIOMAS_SEGURAS or len(palabras & _OTROS_IDIOMAS) >= 2:
        return True
    return bool(_COMPRAS.search(oracion))


def limpiar_respuesta_ia(texto):
    """Quita de una respuesta de la IA las oraciones en otro idioma o sobre
    compras, ventas, precios o publicidad. Devuelve "" si no queda nada."""
    texto = re.sub(r"\*[^*\n]{1,60}\*|\([^)\n]{1,60}\)|\[[^\]\n]{1,60}\]", " ", str(texto or ""))
    texto = re.sub(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F]", "", texto)
    oraciones = re.split(r"(?<=[.!?])\s+", texto.strip())
    return " ".join(o for o in oraciones if o and not frase_prohibida(o)).strip()
