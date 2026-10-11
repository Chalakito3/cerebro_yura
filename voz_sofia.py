"""Cómo habla Sofía (la voz de Yura, Edge TTS): texto, expresión y caché.

Lo usan Yura al hablar (main_robot.HardwareInterface) y el pre-generador de
la caché sin internet (basedatos/pregenerar_voces_sofia.py), para que el
audio guardado suene igual que el generado en el momento.

Expresión (07/10/2026): antes los "?" y "!" se cambiaban por puntos y todo
salía con el mismo tono. Ahora se conservan (Edge TTS entona sola preguntas
y exclamaciones) y la velocidad y el tono cambian según lo que se dice:
celebrar, consolar, preguntar o hablar normal.
"""
import hashlib
import os
import re

NORMAL = ("+5%", "+0Hz")
CELEBRAR = ("+12%", "+8Hz")
CONSOLAR = ("-3%", "-3Hz")
PREGUNTAR = ("+5%", "+3Hz")

_CELEBRAR = re.compile(
    r"\b(muy bien|excelente|correcto|felicidades|genial|bien hecho|lo lograste|perfecto|"
    r"increible|fantastico|sumaq|allinmi)\b"
)
_CONSOLAR = re.compile(
    r"\b(no te preocupes|casi|intentemos|intentalo|lo siento|no pasa nada|otra vez|"
    r"no es correcto|incorrecto|ama llakikuychu)\b"
)


def _sin_tildes(texto):
    import unicodedata

    texto = unicodedata.normalize("NFKD", str(texto or "").lower())
    return "".join(c for c in texto if not unicodedata.combining(c))


def formatear_texto_voz(texto):
    """Prepara el texto para la voz: pausas naturales y signos de entonación."""
    if texto is None:
        return ""
    texto = re.sub(r"\s+", " ", str(texto).strip())
    texto = texto.replace("¿", "").replace("¡", "")
    if not texto:
        return ""
    if not re.search(r"[.,;:?!]$", texto):
        texto += "."
    # Pausas antes de "y", "pero", "entonces" (si no hay ya un signo). La de
    # "y" solo en tramos largos: en frases cortas sonaba entrecortado.
    texto = re.sub(r"([^,;:.!?]{40,}?)(?<![,;:.]) y ", r"\1, y ", texto)
    texto = re.sub(r"(?<![,;:.]) pero ", ". Pero ", texto)
    texto = re.sub(r"(?<![,;:.]) entonces ", ". Entonces ", texto)
    texto = texto.replace(" por favor ", ", por favor, ")
    return re.sub(r",\s*,", ",", texto).strip()


def prosodia(texto_voz):
    """(velocidad, tono) de Edge TTS según lo que se dice."""
    simple = _sin_tildes(texto_voz)
    if _CELEBRAR.search(simple) and "!" in texto_voz:
        return CELEBRAR
    if _CONSOLAR.search(simple):
        return CONSOLAR
    if texto_voz.rstrip().endswith("?"):
        return PREGUNTAR
    if _CELEBRAR.search(simple):
        return CELEBRAR
    return NORMAL


def argumentos_edge(voz, texto_voz):
    velocidad, tono = prosodia(texto_voz)
    return ["--voice", voz, f"--rate={velocidad}", f"--pitch={tono}", "--text", texto_voz]


def ruta_cache(carpeta, voz, texto_voz):
    """Archivo de la caché para esta frase. Con la expresión normal la clave
    es la de siempre (se conservan los audios ya guardados)."""
    if not carpeta or not texto_voz:
        return None
    texto_norm = re.sub(r"\s+", " ", str(texto_voz).strip().lower())
    if not texto_norm:
        return None
    velocidad, tono = prosodia(texto_voz)
    base = f"{voz}:{texto_norm}" if (velocidad, tono) == NORMAL else f"{voz}:{velocidad}:{tono}:{texto_norm}"
    clave = hashlib.sha256(base.encode("utf-8")).hexdigest()[:24]
    return os.path.join(carpeta, f"{clave}.wav")


# ------------------------------------------------------------ sin internet

_internet = {"hasta": 0.0, "hay": True}


def hay_internet(espera=1.5):
    """¿Responde el servicio de voz? Se revisa como mucho cada 30 s, para no
    esperar en cada frase (antes, sin internet, Yura esperaba hasta 40 s a
    Edge TTS antes de hablar con otra voz)."""
    import socket
    import time

    ahora = time.monotonic()
    if ahora < _internet["hasta"]:
        return _internet["hay"]
    try:
        with socket.create_connection(("speech.platform.bing.com", 443), timeout=espera):
            hay = True
    except OSError:
        hay = False
    _internet.update(hay=hay, hasta=ahora + 30)
    return hay


def oraciones(texto_voz):
    """Divide la frase en oraciones ("¡Muy bien!", "Allqu significa perro.")
    para decirla con trozos guardados cuando no está entera en la caché."""
    return [o.strip() for o in re.findall(r"[^.!?]+[.!?]+", texto_voz or "") if o.strip()]


def ruta_faltantes(carpeta):
    return os.path.join(carpeta, "faltantes.txt")


def anotar_faltante(carpeta, texto):
    """Frase que Yura tuvo que decir sin internet y sin la voz guardada: se
    genera con la voz de Sofía la próxima vez que haya internet."""
    if not carpeta or not texto:
        return
    try:
        ruta = ruta_faltantes(carpeta)
        existentes = set()
        if os.path.exists(ruta):
            with open(ruta, encoding="utf-8") as archivo:
                existentes = {linea.strip() for linea in archivo}
        if texto.strip() not in existentes:
            with open(ruta, "a", encoding="utf-8") as archivo:
                archivo.write(texto.strip().replace("\n", " ") + "\n")
    except OSError:
        pass
