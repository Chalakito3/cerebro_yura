#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Amplía el vocabulario de diálogo en quechua y completa las pronunciaciones
fonéticas de las palabras faltantes según las normas oficiales de Laime (2007)
y PROEIB UMSS (2014).

IMPORTANTE:
- NO modifica ninguna de las 113 pronunciaciones ya existentes y estudiadas de Yura.
- NO altera ninguna grabación de la docente ni archivos de audio previos.
- Solo añade las palabras que no tenían entrada fonética y las nuevas frases de diálogo.
"""

import os
import re
import shutil
import sqlite3
import unicodedata
from datetime import datetime

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_DB = os.path.join(RAIZ, "diccionario.db")
RESPALDO_DB = os.path.join(
    RAIZ, "basedatos", f"diccionario_antes_ampliar_dialogo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
)

VOCALES = "aeiou"


def _sin_tildes(texto):
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c))


def _acento_quechua(palabra):
    """Marca la tilde en la penúltima sílaba si la palabra termina en consonante
    (que no sea n ni s) para que la voz mantenga el acento grave del quechua."""
    p_limpia = _sin_tildes(palabra.lower())
    if len(p_limpia) < 3 or p_limpia[-1] in VOCALES + "ns":
        return palabra
    posiciones = [i for i, c in enumerate(p_limpia) if c in VOCALES]
    if len(posiciones) < 2:
        return palabra
    i = posiciones[-2]
    v = palabra[i]
    tilde = {
        "a": "á", "e": "é", "i": "í", "o": "ó", "u": "ú",
        "A": "Á", "E": "É", "I": "Í", "O": "Ó", "U": "Ú"
    }.get(v, v)
    return palabra[:i] + tilde + palabra[i + 1:]


def fonetica_quechua_oficial(palabra_frase):
    """Reglas fonológicas oficiales de Laime (2007) y PROEIB UMSS (2014)."""
    palabras = palabra_frase.strip().split()
    adaptadas = []

    for pal in palabras:
        p = pal
        # 1. -chka- suena -sha- en Cochabamba y valles bolivianos (PROEIB UMSS)
        p = re.sub(r"chka", "sha", p, flags=re.IGNORECASE)
        p = re.sub(r"chk", "sh", p, flags=re.IGNORECASE)

        # 2. Alófonos vocálicos ante uvulares (Laime 2007)
        # u -> o en contacto con q, qh, q'
        p = re.sub(r"u(?=q|qh|q\')", "o", p, flags=re.IGNORECASE)
        p = re.sub(r"(q|qh|q\')u", r"\g<1>o", p, flags=re.IGNORECASE)
        p = re.sub(r"U(?=q|qh|q\')", "O", p)
        p = re.sub(r"(q|qh|q\')U", r"\g<1>O", p, flags=re.IGNORECASE)

        # i -> e en contacto con q, qh, q'
        p = re.sub(r"i(?=q|qh|q\')", "e", p, flags=re.IGNORECASE)
        p = re.sub(r"(q|qh|q\')i", r"\g<1>e", p, flags=re.IGNORECASE)
        p = re.sub(r"I(?=q|qh|q\')", "E", p)
        p = re.sub(r"(q|qh|q\')I", r"\g<1>E", p, flags=re.IGNORECASE)

        # 3. Aspirada qh inicial -> j
        p = re.sub(r"^qh", "j", p, flags=re.IGNORECASE)

        # 4. Glotal q' -> k'
        p = re.sub(r"q\'", "k'", p, flags=re.IGNORECASE)

        # 5. q final -> k
        p = re.sub(r"q$", "k", p, flags=re.IGNORECASE)

        # 6. Acento grave
        p = _acento_quechua(p)
        adaptadas.append(p)

    return " ".join(adaptadas)


FRASES_DIALOGO_INFANTIL = [
    ("Allillanmi", "Allillanmi", "Bien nomás", "Respuesta afirmativa cortés a cómo estás (allillanchu)"),
    ("Kusisqam kani", "Kusisqam kani", "Estoy contento", "Expresión de alegría del niño"),
    ("Imataq sutiyki", "Imataq sutíyki", "¿Cómo te llamas?", "Pregunta básica para conocer el nombre"),
    ("Sutiymi", "Sutíymi", "Mi nombre es", "Frase para presentarse"),
    ("Maymantataq kanki", "Maymantataq kanki", "¿De dónde eres?", "Pregunta sobre procedencia o lugar de origen"),
    ("Mashkha watayuqtaq kanki", "Mashkha watayoqtaq kanki", "¿Cuántos años tienes?", "Pregunta de edad escolar"),
    ("Munani", "Munani", "Quiero o me gusta", "Expresión afirmativa de preferencia o deseo"),
    ("Mana munanichu", "Mana munanichu", "No quiero o no me gusta", "Expresión negativa cortés"),
    ("Ama llakikuychu", "Ama llakikúychu", "No te preocupes", "Frase de apoyo y consuelo afectuoso"),
    ("Kuska yachakusun", "Kuska yachakusun", "Juntos aprenderemos", "Lema pedagógico de colaboración"),
    ("Allquchaymi kashan", "Allqochaymi kashan", "Tengo un perrito", "Mascota cotidiana del estudiante"),
    ("Misichaymi kashan", "Misichaymi kashan", "Tengo un gatito", "Mascota cotidiana del estudiante"),
    ("Chiri kashan", "Chiri kashan", "Hace frío", "Expresión del clima andino"),
    ("Rupay kashan", "Rupay kashan", "Hace calor o sol", "Expresión del clima soleado"),
    ("Yachaywasipi kani", "Yachaywasipi kani", "Estoy en la escuela", "Espacio escolar de aprendizaje"),
    ("Mikhuyta munani", "Mikhuyta munani", "Quiero comer", "Expresión infantil de necesidad"),
    ("Puñuyta munani", "Puñuyta munani", "Quiero dormir o descansar", "Expresión infantil cotidiana"),
    ("Pukllayta munani", "Pukllayta munani", "Quiero jugar", "Invitación lúdica al juego didáctico"),
    ("Sulpayki", "Sulpayki", "Gracias", "Agradecimiento tradicional en quechua boliviano"),
    ("Tupananchiskama", "Tupananchiskama", "Hasta volver a encontrarnos", "Despedida respetuosa y afectuosa")
]


def aplicar():
    print(f"[BD]: Creando respaldo de seguridad en:\n  {RESPALDO_DB}")
    shutil.copy2(RUTA_DB, RESPALDO_DB)

    with sqlite3.connect(RUTA_DB) as con:
        con.row_factory = sqlite3.Row

        # 1. Crear tabla nivel1_dialogo_infantil si no existe
        con.execute(
            """CREATE TABLE IF NOT EXISTS nivel1_dialogo_infantil (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                palabra_frase TEXT NOT NULL UNIQUE,
                pronunciacion TEXT,
                traduccion TEXT NOT NULL,
                significado TEXT
            )"""
        )

        insertados_dialogo = 0
        for palabra, pron, trad, sig in FRASES_DIALOGO_INFANTIL:
            res = con.execute(
                """INSERT OR IGNORE INTO nivel1_dialogo_infantil
                   (palabra_frase, pronunciacion, traduccion, significado)
                   VALUES (?, ?, ?, ?)""",
                (palabra, pron, trad, sig)
            )
            if res.rowcount > 0:
                insertados_dialogo += 1

        print(f"[BD]: {insertados_dialogo} frases nuevas añadidas a 'nivel1_dialogo_infantil'.")

        # 2. Consultar las pronunciaciones que ya existen (NO TOCARLAS)
        filas_voz = con.execute("SELECT palabra_frase FROM pronunciaciones_voz").fetchall()
        existentes_voz = {r["palabra_frase"].strip() for r in filas_voz}
        print(f"[BD]: {len(existentes_voz)} pronunciaciones existentes preservadas 100% intactas.")

        # 3. Leer todas las palabras de todas las tablas de vocabulario
        tablas_vocabulario = [
            fila[0] for fila in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'nivel%'"
            ).fetchall()
        ]

        nuevas_pronunciaciones = 0
        ahora = datetime.now().isoformat(timespec="seconds")

        for tabla in tablas_vocabulario:
            filas = con.execute(f'SELECT palabra_frase FROM "{tabla}"').fetchall()
            for f in filas:
                palabra = str(f["palabra_frase"] or "").strip()
                if not palabra or palabra in existentes_voz:
                    continue

                texto_voz = fonetica_quechua_oficial(palabra)
                con.execute(
                    """INSERT OR IGNORE INTO pronunciaciones_voz
                       (palabra_frase, texto_para_voz, parecido, parecido_original,
                        fecha, se_entiende, se_entendia_original, audio_yura,
                        metodo_audio, audio_se_entiende, audio_parecido, fijada)
                       VALUES (?, ?, NULL, NULL, ?, NULL, NULL, NULL, 'oficial_laime', NULL, NULL, 0)""",
                    (palabra, texto_voz, ahora)
                )
                existentes_voz.add(palabra)
                nuevas_pronunciaciones += 1

        con.commit()
        total_voz = con.execute("SELECT count(*) FROM pronunciaciones_voz").fetchone()[0]
        print(f"[BD]: {nuevas_pronunciaciones} palabras recibieron pronunciación fonética oficial (Laime/PROEIB).")
        print(f"[BD]: Total actual en pronunciaciones_voz: {total_voz}")


if __name__ == "__main__":
    aplicar()
