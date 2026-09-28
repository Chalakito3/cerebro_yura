"""Busca palabras en el Diccionario Bilingüe de T. Laime Ajacopa (La Paz, 2007).

Uso:
    python buscar_laime.py qu yaku sinqa           # quechua -> castellano
    python buscar_laime.py es agua nariz           # castellano -> quechua
El PDF se lee desde documentacion_quechua/fuentes/ (ver RUTA_PDF). Se genera un texto en caché.
"""
import os
import re
import sys
import unicodedata

RUTA_PDF = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "fuentes", "Laime_Ajacopa_2007_Diccionario_Bilingue_Quechua_Castellano.pdf"
)
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "laime_texto.txt")

_TIPOS = r"(?:s|adj|v|tr|intr|adv|interj|pron|num|prep|conj|prnl|Fon|onomat|loc|expr|suf|s,|Gram|Mat|Bot|Zool|Anat|Med|Mús|Rel)"
_INICIO = re.compile(r"^([a-zñáéíóúü'’][a-zñáéíóúü'’ \-]*?(?:, [a-zñáéíóúü'’ \-]+)*)\.\s+" + _TIPOS + r"\b")


def _texto():
    if not os.path.exists(CACHE):
        from pypdf import PdfReader
        paginas = PdfReader(RUTA_PDF).pages
        with open(CACHE, "w", encoding="utf-8") as salida:
            salida.write("\n".join((p.extract_text() or "") for p in paginas))
    return open(CACHE, encoding="utf-8").read().replace("’", "'")


def _entradas(lineas):
    actual = None
    for linea in lineas:
        linea = linea.strip()
        if _INICIO.match(linea):
            if actual:
                yield actual
            actual = linea
        elif actual is not None and linea:
            actual += " " + linea
    if actual:
        yield actual


def _sin_tildes(texto):
    texto = texto.replace("ñ", "\x00")
    texto = "".join(c for c in unicodedata.normalize("NFD", texto) if not unicodedata.combining(c))
    return texto.replace("\x00", "ñ").lower()


def secciones():
    lineas = _texto().splitlines()
    # La parte castellano-quechua empieza en la entrada "a." / "abajo." tras la mitad del libro.
    corte = next(
        i for i, l in enumerate(lineas)
        if i > len(lineas) // 2 and re.match(r"^a\.\s+(prep|s)\b", l.strip())
    )
    return list(_entradas(lineas[:corte])), list(_entradas(lineas[corte:]))


def buscar(palabra, entradas):
    clave = _sin_tildes(palabra.replace("’", "'"))
    encontradas = []
    for entrada in entradas:
        cabeza = _sin_tildes(entrada.split(". ", 1)[0])
        if clave in [c.strip() for c in cabeza.split(",")]:
            encontradas.append(re.sub(r"\s+", " ", entrada)[:260])
    return encontradas


if __name__ == "__main__":
    quechua, castellano = secciones()
    fuente = quechua if sys.argv[1] == "qu" else castellano
    for palabra in sys.argv[2:]:
        resultados = buscar(palabra, fuente)
        print(f"■ {palabra}: " + (" ‖ ".join(resultados) if resultados else "NO ENCONTRADA"))
