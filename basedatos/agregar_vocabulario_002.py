"""Agrega al diccionario las palabras del documento 002 que todavía no existen
(documentacion_quechua/vocabulario_quechua_boliviano_002_2026-09-27.pdf).

Aprobado por el equipo el 27/09/2026. Solo palabras 🟢 (confirmadas por
Laime 2007, DDE Chuquisaca o PROEIB) y ⚠️ con la forma elegida (común / DDE).
Las 🟡 (sin fuente) no se agregan.

Uso:
    python basedatos/agregar_vocabulario_002.py           # agrega (idempotente)
    python basedatos/agregar_vocabulario_002.py --probar  # solo muestra qué agregaría

No agrega una palabra si ya existe la misma forma quechua con el mismo
significado, ni si el significado en castellano ya está en el diccionario
(para no crear dos traducciones distintas de la misma palabra).
"""
import os
import sqlite3
import sys
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_DB = os.path.join(RAIZ, "diccionario.db")

TABLAS_NUEVAS = ["nivel2_pronombres", "nivel2_preguntas", "nivel2_verbos"]

# tabla: [(quechua, castellano, significado o None, fuente)]
PALABRAS = {
    "nivel1_saludos": [
        ("Napaykuy", "Saludo", "Fórmula de cortesía, respeto o afecto", "Laime"),
        ("Aywa", "Adiós", "Despedida", "Laime"),
        ("Ari", "Sí", "Afirmación", "Laime"),
        ("Mana", "No", "Negación", "Laime"),
    ],
    "nivel1_familia": [
        ("Wawa", "Bebé", "Niño pequeño", "Laime"),
        ("Churi", "Hijo (del hombre)", None, "Laime"),
        ("Qhari wawa", "Hijo (de la mujer)", None, "Laime, DDE"),
        ("Wawqi", "Hermano (del hombre)", None, "Laime, DDE"),
        ("Tura", "Hermano (de la mujer)", None, "Laime"),
        ("Ñaña", "Hermana (de la mujer)", None, "Laime, DDE"),
        ("Pana", "Hermana (del hombre)", None, "Laime"),
        ("Jatun tata", "Abuelo", None, "Laime"),
        ("Jatun mama", "Abuela", None, "Laime, DDE"),
        ("Imilla", "Muchacha", None, "Laime, DDE"),
        ("Yachachiq", "Profesor", "Persona que enseña", "Laime, DDE"),
        ("Yachakuq", "Estudiante", "Persona que aprende", "Laime, DDE"),
    ],
    "nivel1_partes_del_cuerpo": [
        ("Uya", "Cara", None, "Laime, DDE"),
        ("Kunka", "Cuello", None, "Laime, DDE"),
        ("Wiksa", "Estómago", None, "Laime, DDE"),
    ],
    "nivel2_animales": [
        ("Uwija", "Oveja", None, "Laime, DDE"),
        ("K'anka", "Gallo", None, "Laime, DDE"),
        ("Kututu", "Cuy macho", None, "Laime, DDE"),
        ("Wallata", "Ganso andino", None, "Laime"),
        ("Q'alachu", "Loro", None, "DDE"),
        ("Juku", "Búho", None, "Laime, DDE"),
        ("Yuthu", "Perdiz", None, "Laime, DDE"),
        ("Anka", "Águila", None, "Laime, DDE"),
        ("Qaraywa", "Lagartija", None, "Laime"),
        ("Ch'uspi", "Mosca", None, "Laime, DDE"),
        ("Khuru", "Gusano", None, "Laime, DDE"),
    ],
    "nivel1_alimentos": [
        ("Runtu", "Huevo", None, "Laime, DDE"),
        ("Misk'i", "Dulce", "También: miel", "Laime, DDE"),
        ("Unu", "Líquido", None, "DDE (Laime: también agua)"),
    ],
    "nivel1_elementos_naturales": [
        ("Quyllur", "Estrella", None, "Laime"),
        ("Ch'aska", "Lucero", "Estrella muy brillante", "Laime"),
        ("Para", "Lluvia", None, "Laime, DDE"),
        ("Wayra", "Viento", None, "Laime, DDE"),
        ("Nina", "Fuego", None, "Laime, DDE"),
        ("Jallp'a", "Tierra", None, "Laime"),
        ("Pampa", "Campo", "Llanura", "Laime, DDE"),
        ("T'ika", "Flor", None, "Laime, DDE"),
        ("K'aspi", "Palo", None, "Laime, DDE"),
    ],
    "nivel1_elementos_casa": [
        ("Q'uncha", "Fogón", "Lugar de la cocina para hacer fuego", "Laime, DDE"),
        ("P'acha", "Ropa", None, "Laime, DDE"),
    ],
    "nivel1_colores": [
        ("Llimp'i", "Color", None, "Laime, DDE"),
        ("Quri", "Oro", None, "Laime"),
    ],
    "nivel2_adjetivos_calificativos": [
        ("K'acha", "Lindo", "Bueno, hermoso", "Laime, DDE"),
        ("Wira", "Gordo", None, "Laime, DDE"),
        ("Tullu", "Flaco", None, "Laime, DDE"),
        ("Kusisqa", "Alegre", None, "Laime, DDE"),
    ],
    "nivel2_adjetivos_determinativos": [
        ("Jaqay", "Aquel / Aquella", "Indica algo lejano", "Laime, DDE"),
        ("Wakin", "Algunos", None, "DDE"),
        ("Tukuy", "Todos", None, "Laime, DDE"),
    ],
    "nivel2_pronombres": [
        ("Ñuqa", "Yo", None, "DDE"),
        ("Qam", "Tú", None, "DDE"),
        ("Pay", "Él / Ella", None, "DDE"),
        ("Ñuqanchik", "Nosotros (incluye a quien escucha)", None, "DDE"),
        ("Ñuqayku", "Nosotros (sin quien escucha)", None, "DDE"),
        ("Qamkuna", "Ustedes", None, "DDE"),
        ("Paykuna", "Ellos / Ellas", None, "DDE"),
    ],
    "nivel2_preguntas": [
        ("Pi", "¿Quién?", None, "DDE"),
        ("Ima", "¿Qué?", None, "DDE"),
        ("May", "¿Dónde?", None, "DDE"),
        ("Jayk'aq", "¿Cuándo?", None, "DDE"),
        ("Machkha", "¿Cuánto?", None, "DDE"),
    ],
    "nivel2_verbos": [
        ("Mikhuy", "Comer", None, "Laime, DDE"),
        ("Upyay", "Beber", None, "Laime, DDE"),
        ("Puñuy", "Dormir", None, "DDE"),
        ("Asiy", "Reír", None, "DDE"),
        ("Puriy", "Caminar", None, "DDE"),
        ("Takiy", "Cantar", None, "DDE"),
        ("Parlay", "Hablar", None, "DDE"),
        ("Kichay", "Abrir", None, "DDE"),
        ("Uyariy", "Escuchar", None, "DDE"),
        ("Phinkiy", "Saltar", None, "DDE"),
        ("Wayk'uy", "Cocinar", None, "DDE"),
        ("Samay", "Descansar", "También: respirar", "DDE"),
        ("Riqsiy", "Conocer", None, "DDE"),
        ("Yachay", "Saber", None, "DDE"),
        ("Yupay", "Contar", None, "DDE"),
        ("Waqay", "Llorar", None, "DDE"),
        ("Llamk'ay", "Trabajar", None, "DDE"),
        ("Tarpuy", "Sembrar", None, "DDE"),
        ("Pukllay", "Jugar", None, "DDE"),
        ("Munay", "Querer", None, "DDE"),
    ],
}


def _clave(texto):
    texto = unicodedata.normalize("NFD", str(texto or "").lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.replace("¿", "").replace("?", "").split())


def _todas(conexion):
    filas = []
    for (tabla,) in conexion.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'nivel%'"):
        filas += [(tabla, q, e) for q, e in conexion.execute(f'SELECT palabra_frase, traduccion FROM "{tabla}"')]
    return filas


def aplicar(conexion, probar=False):
    agregadas, omitidas = [], []
    for tabla in TABLAS_NUEVAS:
        existe = conexion.execute("SELECT 1 FROM sqlite_master WHERE name = ?", (tabla,)).fetchone()
        if not existe:
            agregadas.append(f"tabla nueva {tabla}")
            if not probar:
                conexion.execute(
                    f'CREATE TABLE "{tabla}" (id INTEGER PRIMARY KEY AUTOINCREMENT, '
                    "palabra_frase TEXT NOT NULL, pronunciacion TEXT, traduccion TEXT, significado TEXT)"
                )

    existentes = _todas(conexion)
    castellano_existente = {_clave(e) for _, _, e in existentes}
    pares_existentes = {(_clave(q), _clave(e)) for _, q, e in existentes}

    for tabla, palabras in PALABRAS.items():
        for quechua, castellano, significado, fuente in palabras:
            if (_clave(quechua), _clave(castellano)) in pares_existentes:
                continue
            if _clave(castellano) in castellano_existente:
                omitidas.append(f"{quechua} = {castellano} (ese significado ya está en el diccionario)")
                continue
            agregadas.append(f"{tabla}: {quechua} = {castellano}  [{fuente}]")
            castellano_existente.add(_clave(castellano))
            if not probar:
                conexion.execute(
                    f'INSERT INTO "{tabla}" (palabra_frase, pronunciacion, traduccion, significado) VALUES (?, NULL, ?, ?)',
                    (quechua, castellano, significado),
                )
    return agregadas, omitidas


if __name__ == "__main__":
    probar = "--probar" in sys.argv
    with sqlite3.connect(RUTA_DB) as conexion:
        agregadas, omitidas = aplicar(conexion, probar)
        if probar:
            conexion.rollback()
    print(("AGREGARÍA" if probar else "AGREGADO") + f": {len(agregadas)}")
    for linea in agregadas:
        print("  + " + linea)
    if omitidas:
        print(f"NO AGREGADAS: {len(omitidas)}")
        for linea in omitidas:
            print("  - " + linea)
