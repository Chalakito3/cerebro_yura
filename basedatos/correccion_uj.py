"""Cambia "Juk" por "Uj" (uno) en el diccionario y en las grabaciones.

Decisión del equipo (28/09/2026): se usa la forma de Cochabamba "Uj" en la
pantalla y el juego. La escritura normalizada "Juk" (DDE, documento 002) queda
anotada en el significado. El reconocedor escribe "oh" al oír "uj"; por
decisión del equipo "oh" NO se acepta como respuesta (daría aciertos falsos).

Uso (se puede repetir sin efecto):
    python basedatos/correccion_uj.py
"""
import os
import sqlite3

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_DB = os.path.join(RAIZ, "diccionario.db")

CAMBIOS = [
    ("nivel1_numeros", 1, "Número uno (escritura normalizada: Juk)"),
    ("nivel2_adjetivos_determinativos", 3, "Indica unidad o singularidad (escritura normalizada: Juk)"),
]


def aplicar(conexion):
    hechos = []
    for tabla, id_fila, significado in CAMBIOS:
        fila = conexion.execute(f'SELECT palabra_frase FROM "{tabla}" WHERE id = ?', (id_fila,)).fetchone()
        if fila and fila[0] == "Juk":
            conexion.execute(
                f'UPDATE "{tabla}" SET palabra_frase = ?, significado = ? WHERE id = ?',
                ("Uj", significado, id_fila),
            )
            hechos.append(f"{tabla} {id_fila}: Juk -> Uj")
    for tabla_audio in ("pronunciaciones_docente", "pronunciaciones_aprendidas"):
        existe = conexion.execute("SELECT 1 FROM sqlite_master WHERE name = ?", (tabla_audio,)).fetchone()
        if existe:
            n = conexion.execute(
                f"UPDATE {tabla_audio} SET palabra_frase = 'Uj' WHERE palabra_frase = 'Juk'"
            ).rowcount
            if n:
                hechos.append(f"{tabla_audio}: {n} filas Juk -> Uj")
    return hechos


if __name__ == "__main__":
    with sqlite3.connect(RUTA_DB) as conexion:
        hechos = aplicar(conexion)
    print("\n".join(hechos) if hechos else "Nada que cambiar (ya estaba aplicado).")
