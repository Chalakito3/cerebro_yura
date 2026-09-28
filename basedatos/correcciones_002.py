"""Aplica al diccionario las correcciones aprobadas del documento 002
(documentacion_quechua/vocabulario_quechua_boliviano_002_2026-09-27.pdf).

Aprobado por el equipo el 27/09/2026:
- las 70 correcciones de la sección 14.2 (fuentes: Laime 2007, DDE, PROEIB);
- en los casos donde las fuentes difieren, la forma común / DDE
  (Allin p'unchay, Phichqa, Chawlla, Pilli); rosado queda sin cambio;
- las palabras sin fuente (sección 14.4) se dejan como están.

Uso:
    python basedatos/correcciones_002.py           # aplica (idempotente)
    python basedatos/correcciones_002.py --probar  # solo muestra qué cambiaría

Cada cambio verifica la palabra actual antes de modificarla; si alguna no
coincide, no se aplica ninguno (una sola transacción).
"""
import os
import sqlite3
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_DB = os.path.join(RAIZ, "diccionario.db")

# (tabla, id, quechua actual, quechua nuevo, traducción nueva o None, significado nuevo o None)
CORRECCIONES = [
    # Partes del cuerpo
    ("nivel1_partes_del_cuerpo", 11, "Mak'a", "Maki", None, None),
    ("nivel1_partes_del_cuerpo", 17, "K'ullu", "Tullu", None, None),
    ("nivel1_partes_del_cuerpo", 9, "Sonqo", "Sunqu", None, None),
    ("nivel1_partes_del_cuerpo", 19, "Akcha", "Chukcha", None, None),
    ("nivel1_partes_del_cuerpo", 8, "K'uchu", "Wasa", None, None),
    ("nivel1_partes_del_cuerpo", 12, "Ruku maki", "Ruk'ana", "Dedo", None),
    ("nivel1_partes_del_cuerpo", 15, "K'uchu chaki", "Takillpa", None, None),
    ("nivel1_partes_del_cuerpo", 16, "Waqta chaki", "T'usu", None, None),
    # Animales
    ("nivel2_animales", 1, "Allqo", "Allqu", None, None),
    ("nivel2_animales", 6, "Kuchi", "Khuchi", None, None),
    ("nivel2_animales", 26, "K'uchi", "K'usillu", None, None),
    ("nivel2_animales", 14, "Sacha", "Taruka", None, None),
    ("nivel2_animales", 8, "Wallata", "Pilli", None, "Ave acuática"),
    ("nivel2_animales", 19, "K'anchisapa", "Ninanina", None, None),
    ("nivel2_animales", 20, "Wanak'u", "Wara", None, None),
    ("nivel2_animales", 21, "Ch'iwchi", "Lachiwana", None, None),
    ("nivel2_animales", 16, "Ch'ita", "Usqullu", None, None),
    ("nivel2_animales", 24, "K'achi", "Araranka", None, None),
    ("nivel2_animales", 25, "Ukucha", "Juk'ucha", None, None),
    ("nivel2_animales", 17, "Hamp'atu", "Jamp'atu", None, None),
    ("nivel2_animales", 22, "Challwa", "Chawlla", None, None),
    ("nivel2_animales", 9, "Kuy", "Quwi", None, None),
    # Colores
    ("nivel1_colores", 8, "Q'ello", "Q'illu", None, None),
    ("nivel1_colores", 10, "Q'omer", "Q'umir", None, None),
    ("nivel1_colores", 16, "Q'ello-puka", "Willapi", None, None),
    ("nivel1_colores", 19, "Quri", "Qurichasqa", None, None),
    # Elementos naturales
    ("nivel1_elementos_naturales", 10, "Qocha", "Qucha", None, None),
    ("nivel1_elementos_naturales", 8, "Puyu", "Phuyu", None, None),
    ("nivel1_elementos_naturales", 9, "Hanaq pacha", "Janaqpacha", None, None),
    ("nivel1_elementos_naturales", 15, "T'ikari wasi", "Muya", None, None),
    # Alimentos
    ("nivel1_alimentos", 7, "K'anka", "Kanka", None, None),
    ("nivel1_alimentos", 9, "Mullu", "Jamk'a", None, None),
    ("nivel1_alimentos", 10, "T'anta manka", "P'ukuru", None, "Cavidad de barro donde se cuece el pan"),
    ("nivel1_alimentos", 6, "Ají", "Uchu", None, None),
    ("nivel1_alimentos", 2, "Chicha", "Aqha", "Chicha", "Bebida tradicional de maíz fermentado"),
    # Herramientas
    ("nivel1_herramientas", 1, "Llamk'ana", "Ruwalla", None, None),
    ("nivel1_herramientas", 2, "Rumi maqana", "Takana", "Martillo", "Herramienta para golpear"),
    ("nivel1_herramientas", 3, "Wachikuy", "Yawrilla", None, None),
    ("nivel1_herramientas", 4, "T'uksu", "Lampa", None, None),
    ("nivel1_herramientas", 5, "Ch'aki maqana", "Ayri", None, None),
    # Lugares
    ("nivel1_lugares", 1, "Plaza", "Kancha", None, None),
    ("nivel1_lugares", 2, "Marka", "Llaqta", None, None),
    ("nivel1_lugares", 5, "Puente", "Chaka", None, None),
    ("nivel1_lugares", 6, "Hospital", "Jampina wasi", None, None),
    ("nivel1_lugares", 7, "Ch'askañawi", "Qhawana", None, None),
    # Objetos escolares
    ("nivel1_objetos_escolares", 2, "T'anta wasi", "Yachay wasi", None, None),
    ("nivel1_objetos_escolares", 1, "Yachay wasi", "Yachaqana wasi", None, None),
    ("nivel1_objetos_escolares", 7, "K'uchu", "Jamp'ara", None, None),
    ("nivel1_objetos_escolares", 4, "Qillqa", "P'anqa", None, None),
    ("nivel1_objetos_escolares", 10, "Lapiz qillqana", "Tinta qillqana", None, None),
    ("nivel1_objetos_escolares", 9, "K'anchay rikhuy", "Maru", None, None),
    # Utensilios de cocina y casa
    ("nivel1_utensilios_cocina", 1, "Platu", "Chuwa", None, None),
    ("nivel1_utensilios_cocina", 2, "Vasu", "Qiru", None, None),
    ("nivel1_utensilios_cocina", 7, "Q'ipina", "Wayaqa", None, None),
    ("nivel1_elementos_casa", 3, "Windu", "Wayrana", None, None),
    # Adjetivos
    ("nivel2_adjetivos_calificativos", 3, "Hatun", "Jatun", None, None),
    ("nivel2_adjetivos_calificativos", 4, "Huchuy", "Juch'uy", None, None),
    ("nivel2_adjetivos_calificativos", 2, "Mana allin", "Saqra", None, None),
    ("nivel2_adjetivos_calificativos", 8, "Q'uychi", "Q'uñi", None, None),
    ("nivel2_adjetivos_calificativos", 11, "K'anchay", "K'anchaq", None, None),
    ("nivel2_adjetivos_calificativos", 12, "Ch'upi", "Ayphu", None, None),
    ("nivel2_adjetivos_determinativos", 1, "Kay", "Kay", "Este / Esta / Esto", "Indica algo cercano a quien habla"),
    ("nivel2_adjetivos_determinativos", 2, "Chay", "Chay", "Ese / Esa / Eso", "Indica algo cercano a quien escucha"),
    ("nivel2_adjetivos_determinativos", 3, "Huk", "Juk", None, None),
    # Familia y saludos
    ("nivel1_familia", 3, "Wawa", "Irqi", None, None),
    ("nivel1_saludos", 1, "Allin punchay", "Allin p'unchay", None, None),
    ("nivel1_saludos", 2, "Imaynalla", "Imaynalla kachkanki", None, None),
    ("nivel1_saludos", 3, "Allin sukay", "Allin sukha", None, None),
    # Números
    ("nivel1_numeros", 1, "Huk", "Juk", None, None),
    ("nivel1_numeros", 11, "Chunka hukniyuq", "Chunka jukniyuq", None, None),
    ("nivel1_numeros", 5, "Pisqa", "Phichqa", None, None),
    ("nivel1_numeros", 15, "Chunka pisqayuq", "Chunka phichqayuq", None, None),
    ("nivel1_numeros", 50, "Pisqa chunka", "Phichqa chunka", None, None),
    ("nivel1_numeros", 500, "Pisqa pachak", "Phichqa pachak", None, None),
    ("nivel1_numeros", 6, "Soqta", "Suqta", None, None),
    ("nivel1_numeros", 16, "Chunka soqtayuq", "Chunka suqtayuq", None, None),
    ("nivel1_numeros", 60, "Soqta chunka", "Suqta chunka", None, None),
    ("nivel1_numeros", 600, "Soqta pachak", "Suqta pachak", None, None),
    ("nivel1_numeros", 9, "Isqun", "Jisq'un", None, None),
    ("nivel1_numeros", 19, "Chunka isqonniyuq", "Chunka jisq'unniyuq", None, None),
    ("nivel1_numeros", 90, "Isqun chunka", "Jisq'un chunka", None, None),
    ("nivel1_numeros", 900, "Isqun pachak", "Jisq'un pachak", None, None),
    ("nivel1_numeros", 18, "Chunka pusqayuq", "Chunka pusaqniyuq", None, None),
    ("nivel1_numeros", 1000, "Waranka", "Waranqa", None, None),
]

# Palabras correctas en la categoría equivocada (sección 14.4).
MOVIMIENTOS = [
    ("nivel1_elementos_naturales", "T'anta", "nivel1_alimentos"),
    ("nivel1_lugares", "Taqlla", "nivel1_herramientas"),
]

# Tablas sin la columna "significado".
SIN_SIGNIFICADO = ["nivel1_colores", "nivel1_familia", "nivel1_partes_del_cuerpo", "nivel1_saludos"]


def _columnas(conexion, tabla):
    return [fila[1] for fila in conexion.execute(f'PRAGMA table_info("{tabla}")')]


def aplicar(conexion, probar=False):
    cambios = []
    pendientes = 0
    for tabla, id_, actual, nuevo, traduccion, significado in CORRECCIONES:
        fila = conexion.execute(
            f'SELECT palabra_frase, traduccion FROM "{tabla}" WHERE id = ?', (id_,)
        ).fetchone()
        if fila is None:
            raise SystemExit(f"No existe {tabla} id {id_}")
        ya_aplicada = fila[0] == nuevo and (traduccion is None or fila[1] == traduccion)
        if ya_aplicada:
            continue
        if fila[0] not in (actual, nuevo):
            raise SystemExit(f"{tabla} id {id_}: se esperaba '{actual}' y hay '{fila[0]}'. No se aplicó nada.")
        pendientes += 1
        cambios.append(f"{tabla} id {id_}: {actual} → {nuevo}" + (f" ({traduccion})" if traduccion else ""))
        if probar:
            continue
        conexion.execute(f'UPDATE "{tabla}" SET palabra_frase = ? WHERE id = ?', (nuevo, id_))
        if traduccion:
            conexion.execute(f'UPDATE "{tabla}" SET traduccion = ? WHERE id = ?', (traduccion, id_))
        if significado and "significado" in _columnas(conexion, tabla):
            conexion.execute(f'UPDATE "{tabla}" SET significado = ? WHERE id = ?', (significado, id_))

    for tabla in SIN_SIGNIFICADO:
        if "significado" not in _columnas(conexion, tabla):
            cambios.append(f"{tabla}: nueva columna 'significado'")
            if not probar:
                conexion.execute(f'ALTER TABLE "{tabla}" ADD COLUMN significado TEXT')

    for origen, palabra, destino in MOVIMIENTOS:
        fila = conexion.execute(
            f'SELECT palabra_frase, pronunciacion, traduccion, significado FROM "{origen}" WHERE palabra_frase = ?',
            (palabra,),
        ).fetchone()
        if fila is None:
            continue
        cambios.append(f"{palabra}: {origen} → {destino}")
        if not probar:
            conexion.execute(
                f'INSERT INTO "{destino}" (palabra_frase, pronunciacion, traduccion, significado) VALUES (?, ?, ?, ?)',
                fila,
            )
            conexion.execute(f'DELETE FROM "{origen}" WHERE palabra_frase = ?', (palabra,))
    return cambios


if __name__ == "__main__":
    probar = "--probar" in sys.argv
    with sqlite3.connect(RUTA_DB) as conexion:
        cambios = aplicar(conexion, probar)
        if probar:
            conexion.rollback()
    print(("CAMBIARÍA" if probar else "APLICADO") + f": {len(cambios)} cambios")
    for cambio in cambios:
        print("  " + cambio)
