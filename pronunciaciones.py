"""Pronunciaciones que enseña la docente (modo docente).

La docente dice una palabra del diccionario; Yura la graba y anota cómo la
escribió su reconocedor de voz. Si la docente confirma que la pronunciación
es correcta, se guarda en diccionario.db (tabla pronunciaciones_docente) y el
audio en basedatos/pronunciaciones/. Con eso Yura:

- acepta en el juego y la práctica lo que el reconocedor escribe cuando la
  palabra se dice bien (por ejemplo "Ayku" por allqu), y
- hace escuchar a los estudiantes la voz de la docente después de la suya.
"""
import os
import shutil
import sqlite3
import wave
from datetime import datetime

import numpy as np

import texto as texto_util

RAIZ = os.path.dirname(os.path.abspath(__file__))
RUTA_DB = os.path.join(RAIZ, "diccionario.db")
CARPETA_AUDIOS = os.path.join(RAIZ, "basedatos", "pronunciaciones")
NOMBRE_PENDIENTE = "pendiente.wav"
TABLA = "pronunciaciones_docente"
# Lo que Yura aprendió al volver a escuchar los audios de la docente en
# distintas situaciones (menú, juego, sin pistas): basedatos/aprender_de_audios.py.
TABLA_APRENDIDAS = "pronunciaciones_aprendidas"

# Nunca se aceptan como respuesta, aunque el reconocedor las escriba al oír a
# la docente. "ullu" es vulgar (Laime 2007: "ullu. s. Pene"); con "phuyu" y
# "usqullu" el reconocedor escribió "ullu" (27/09/2026).
PALABRAS_NO_ACEPTADAS = {"ullu"}


def _conectar():
    conexion = sqlite3.connect(RUTA_DB, timeout=10)
    conexion.row_factory = sqlite3.Row
    conexion.execute(
        f"""CREATE TABLE IF NOT EXISTS {TABLA} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tabla TEXT NOT NULL,
            id_palabra INTEGER NOT NULL,
            palabra_frase TEXT NOT NULL,
            archivo TEXT NOT NULL,
            transcripcion TEXT,
            sirve_para_calificar INTEGER NOT NULL DEFAULT 1,
            fecha TEXT NOT NULL
        )"""
    )
    conexion.execute(
        f"""CREATE TABLE IF NOT EXISTS {TABLA_APRENDIDAS} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_grabacion INTEGER NOT NULL,
            palabra_frase TEXT NOT NULL,
            contexto TEXT NOT NULL,
            transcripcion TEXT,
            fecha TEXT NOT NULL,
            UNIQUE (id_grabacion, contexto)
        )"""
    )
    return conexion


def ruta_pendiente():
    return os.path.join(CARPETA_AUDIOS, NOMBRE_PENDIENTE)


def guardar_wav(ruta, audio_bytes, frecuencia=16000):
    """Guarda audio de 16 bits mono, con el volumen igualado para que todas
    las grabaciones se escuchen parecido."""
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    muestras = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
    pico = float(np.max(np.abs(muestras))) if muestras.size else 0.0
    if pico > 0:
        muestras = muestras * min(8.0, 29000.0 / pico)
    with wave.open(ruta, "wb") as archivo:
        archivo.setnchannels(1)
        archivo.setsampwidth(2)
        archivo.setframerate(frecuencia)
        archivo.writeframes(np.clip(muestras, -32768, 32767).astype(np.int16).tobytes())


def palabra_del_diccionario(tabla, id_palabra):
    """Devuelve {"tabla", "id", "quechua", "espanol"} o None."""
    import traductor
    with _conectar() as conexion:
        for registro in traductor._leer_registros_vocabulario(conexion):
            if registro["tabla_origen"] == tabla and int(registro["id"]) == int(id_palabra):
                return {
                    "tabla": tabla,
                    "id": int(registro["id"]),
                    "quechua": registro["quechua"],
                    "espanol": registro["espanol"],
                }
    return None


def otra_palabra_igual(transcripcion, quechua):
    """Si lo que escribió el reconocedor es otra palabra del diccionario
    (p. ej. "wawa" al decir tawa), devuelve esa palabra: esa transcripción no
    sirve para calificar, porque aceptaría una respuesta equivocada."""
    buscada = texto_util.simplificar_quechua(transcripcion)
    propia = texto_util.simplificar_quechua(quechua)
    if not buscada or buscada == propia:
        return None
    return _formas_del_diccionario().get(buscada)


_memoria_formas = {"clave": None, "formas": {}}


def _formas_del_diccionario():
    """{forma simplificada: palabra quechua} de todo el diccionario. Se
    guarda en memoria hasta que cambia el archivo de la base."""
    import traductor
    try:
        clave = (RUTA_DB, os.path.getmtime(RUTA_DB))
    except OSError:
        clave = None
    if clave is None or clave != _memoria_formas["clave"]:
        formas = {}
        with _conectar() as conexion:
            for registro in traductor._leer_registros_vocabulario(conexion):
                otra = str(registro["quechua"] or "")
                if otra:
                    formas.setdefault(texto_util.simplificar_quechua(otra), otra)
        _memoria_formas.update(clave=clave, formas=formas)
    return _memoria_formas["formas"]


def guardar(tabla, id_palabra, transcripcion):
    """Pasa la grabación pendiente a la lista de pronunciaciones correctas."""
    palabra = palabra_del_diccionario(tabla, id_palabra)
    if palabra is None:
        raise ValueError("La palabra ya no está en el diccionario.")
    pendiente = ruta_pendiente()
    if not os.path.exists(pendiente):
        raise ValueError("No hay una grabación para guardar.")

    fecha = datetime.now()
    nombre = f"{tabla}_{int(id_palabra)}_{fecha:%Y%m%d_%H%M%S}.wav"
    shutil.move(pendiente, os.path.join(CARPETA_AUDIOS, nombre))
    transcripcion = str(transcripcion or "").strip()
    sirve = bool(transcripcion) and otra_palabra_igual(transcripcion, palabra["quechua"]) is None
    with _conectar() as conexion:
        cursor = conexion.execute(
            f"INSERT INTO {TABLA} (tabla, id_palabra, palabra_frase, archivo, transcripcion, "
            "sirve_para_calificar, fecha) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (tabla, int(id_palabra), palabra["quechua"], nombre, transcripcion,
             int(sirve), fecha.isoformat(timespec="seconds")),
        )
        return cursor.lastrowid


def descartar_pendiente():
    try:
        os.remove(ruta_pendiente())
    except OSError:
        pass


def borrar(id_grabacion):
    with _conectar() as conexion:
        fila = conexion.execute(f"SELECT archivo FROM {TABLA} WHERE id = ?", (int(id_grabacion),)).fetchone()
        if fila is None:
            return False
        conexion.execute(f"DELETE FROM {TABLA} WHERE id = ?", (int(id_grabacion),))
        conexion.execute(f"DELETE FROM {TABLA_APRENDIDAS} WHERE id_grabacion = ?", (int(id_grabacion),))
    try:
        os.remove(os.path.join(CARPETA_AUDIOS, fila["archivo"]))
    except OSError:
        pass
    return True


def ruta_archivo(id_grabacion):
    with _conectar() as conexion:
        fila = conexion.execute(f"SELECT archivo FROM {TABLA} WHERE id = ?", (int(id_grabacion),)).fetchone()
    if fila is None:
        return None
    ruta = os.path.join(CARPETA_AUDIOS, os.path.basename(fila["archivo"]))
    return ruta if os.path.exists(ruta) else None


def grabaciones(tabla=None, id_palabra=None):
    consulta = f"SELECT * FROM {TABLA}"
    parametros = ()
    if tabla is not None:
        consulta += " WHERE tabla = ? AND id_palabra = ?"
        parametros = (tabla, int(id_palabra))
    with _conectar() as conexion:
        return [dict(fila) for fila in conexion.execute(consulta + " ORDER BY id DESC", parametros)]


def _misma_palabra(a, b):
    return texto_util.normalizar(a).replace("'", "") == texto_util.normalizar(b).replace("'", "")


def variante_segura(transcripcion, quechua):
    """Decide si una transcripción de la voz de la docente puede usarse para
    aceptar respuestas de los estudiantes.

    Se descartan las que darían aciertos falsos: muy cortas ("oh", "uf"),
    palabras no aceptadas ("ullu"), otra palabra del diccionario, o frases
    que no se parecen a la palabra ("ordenes", "hola", "adios": el
    reconocedor las inventa cuando casi no oye nada).
    """
    variante = texto_util.simplificar_quechua(transcripcion).replace(" ", "")
    if len(variante) < 3:
        return False
    palabras = set(texto_util.normalizar(transcripcion).replace("'", "").split())
    if palabras & PALABRAS_NO_ACEPTADAS:
        return False
    # La "ll" se oye como "l" o como "y" ("yachta" por llaqta).
    propias = [texto_util.simplificar_quechua(quechua, ll).replace(" ", "") for ll in ("l", "y")]
    if not propias[0] or all(
        texto_util.distancia_edicion(variante, propia) > max(2, len(propia) // 2)
        for propia in propias
    ):
        return False
    return otra_palabra_igual(transcripcion, quechua) is None


def _transcripciones():
    """(palabra_frase, transcripción) de la docente y de lo aprendido."""
    with _conectar() as conexion:
        propias = conexion.execute(
            f"SELECT palabra_frase, transcripcion FROM {TABLA} "
            "WHERE sirve_para_calificar = 1 AND transcripcion != ''"
        ).fetchall()
        aprendidas = conexion.execute(
            f"SELECT palabra_frase, transcripcion FROM {TABLA_APRENDIDAS} WHERE transcripcion != ''"
        ).fetchall()
    return [(fila[0], fila[1]) for fila in list(propias) + list(aprendidas)]


def variantes(quechua):
    """Cómo escribió el reconocedor esta palabra cuando la docente la dijo
    bien, solo las que no darían aciertos falsos."""
    try:
        filas = _transcripciones()
    except sqlite3.Error:
        return []
    candidatas = dict.fromkeys(
        transcripcion for palabra, transcripcion in filas
        if _misma_palabra(palabra, quechua)
    )
    return [t for t in candidatas if variante_segura(t, quechua)]


def palabra_por_variante(texto):
    """Palabra del diccionario que corresponde a lo que escribió el
    reconocedor, según lo aprendido de la docente ("qumir" -> "Q'umir").
    None si no hay una sola palabra posible."""
    buscado = texto_util.simplificar_quechua(texto).replace(" ", "")
    if len(buscado) < 3:
        return None
    try:
        filas = _transcripciones()
    except sqlite3.Error:
        return None
    encontradas = {
        palabra for palabra, transcripcion in filas
        if texto_util.simplificar_quechua(transcripcion).replace(" ", "") == buscado
        and variante_segura(transcripcion, palabra)
    }
    return encontradas.pop() if len(encontradas) == 1 else None


def guardar_aprendida(id_grabacion, palabra_frase, contexto, transcripcion):
    with _conectar() as conexion:
        conexion.execute(
            f"INSERT OR REPLACE INTO {TABLA_APRENDIDAS} "
            "(id_grabacion, palabra_frase, contexto, transcripcion, fecha) VALUES (?, ?, ?, ?, ?)",
            (int(id_grabacion), palabra_frase, contexto, str(transcripcion or "").strip(),
             datetime.now().isoformat(timespec="seconds")),
        )


def contextos_aprendidos(id_grabacion):
    with _conectar() as conexion:
        return {
            fila[0] for fila in conexion.execute(
                f"SELECT contexto FROM {TABLA_APRENDIDAS} WHERE id_grabacion = ?", (int(id_grabacion),)
            )
        }


def audio_de(quechua):
    """Ruta de la grabación más reciente de la docente para esta palabra, o None."""
    if not quechua:
        return None
    try:
        filas = grabaciones()
    except sqlite3.Error:
        return None
    for fila in filas:
        if _misma_palabra(fila["palabra_frase"], quechua):
            ruta = os.path.join(CARPETA_AUDIOS, os.path.basename(fila["archivo"]))
            if os.path.exists(ruta):
                return ruta
    return None


def palabras_con_conteo():
    """Todo el vocabulario con cuántas grabaciones tiene cada palabra."""
    import traductor
    with _conectar() as conexion:
        registros = traductor._leer_registros_vocabulario(conexion)
        conteo = {
            (fila["tabla"], fila["id_palabra"]): fila["cantidad"]
            for fila in conexion.execute(
                f"SELECT tabla, id_palabra, COUNT(*) AS cantidad FROM {TABLA} GROUP BY tabla, id_palabra"
            )
        }
    return [
        {
            "tabla": r["tabla_origen"],
            "id": r["id"],
            "quechua": r["quechua"],
            "espanol": r["espanol"],
            "categoria": str(r["categoria"]).replace("_", " "),
            "grabaciones": conteo.get((r["tabla_origen"], r["id"]), 0),
        }
        for r in registros if r["quechua"]
    ]
