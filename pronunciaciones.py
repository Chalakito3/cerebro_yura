"""Pronunciaciones que enseña la docente (modo docente).

La docente dice una palabra del diccionario; Yura la graba y anota cómo la
escribió su reconocedor de voz. Si la docente confirma que la pronunciación
es correcta, se guarda en diccionario.db (tabla pronunciaciones_docente) y el
audio en basedatos/pronunciaciones/. Con eso Yura:

- acepta en el juego y la práctica lo que el reconocedor escribe cuando la
  palabra se dice bien (por ejemplo "Ayku" por allqu), y
- puede hacer escuchar a los estudiantes la voz de la docente después de la
  suya (desactivado por defecto; YURA_VOZ_DOCENTE=1 lo activa).
"""
import os
import re
import shutil
import sqlite3
import threading
import wave
from datetime import datetime

import numpy as np

import texto as texto_util

RAIZ = os.path.dirname(os.path.abspath(__file__))
RUTA_DB = os.path.join(RAIZ, "diccionario.db")
CARPETA_AUDIOS = os.path.join(RAIZ, "basedatos", "pronunciaciones")
# La voz de Yura entrenada con los audios de la docente (basedatos/entrenar_voz_yura.py).
CARPETA_VOZ_YURA = os.path.join(RAIZ, "basedatos", "pronunciaciones_yura")
NOMBRE_PENDIENTE = "pendiente.wav"
TABLA = "pronunciaciones_docente"
# Dos "Guardar" seguidos no deben mover dos veces la misma grabación.
_candado_guardar = threading.Lock()
# Lo que Yura aprendió al volver a escuchar los audios de la docente en
# distintas situaciones (menú, juego, sin pistas): basedatos/aprender_de_audios.py.
TABLA_APRENDIDAS = "pronunciaciones_aprendidas"

# Cómo debe escribirse cada palabra para que la voz de Yura (castellana) la
# pronuncie como en el audio de la docente: basedatos/aprender_pronunciacion.py.
TABLA_VOZ = "pronunciaciones_voz"

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
    conexion.execute(
        f"""CREATE TABLE IF NOT EXISTS {TABLA_VOZ} (
            palabra_frase TEXT PRIMARY KEY,
            texto_para_voz TEXT NOT NULL,
            parecido REAL,
            parecido_original REAL,
            fecha TEXT NOT NULL
        )"""
    )
    columnas = {fila[1] for fila in conexion.execute(f"PRAGMA table_info({TABLA_VOZ})")}
    for columna, tipo in (("se_entiende", "INTEGER"), ("se_entendia_original", "INTEGER"),
                          ("audio_yura", "TEXT"), ("metodo_audio", "TEXT"),
                          ("audio_se_entiende", "INTEGER"), ("audio_parecido", "REAL"),
                          ("fijada", "INTEGER")):
        if columna not in columnas:
            conexion.execute(f"ALTER TABLE {TABLA_VOZ} ADD COLUMN {columna} {tipo}")
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
    with _candado_guardar:
        return _guardar(tabla, id_palabra, transcripcion)


def _guardar(tabla, id_palabra, transcripcion):
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
        os.remove(os.path.join(CARPETA_AUDIOS, os.path.basename(fila["archivo"])))
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


# Palabras quechuas que también son palabras castellanas comunes: dentro de
# una frase en castellano ("para practicar") no se deben cambiar.
_TAMBIEN_CASTELLANAS = {"para", "papa", "pampa", "mama", "sara", "mina", "api"}

_memoria_voz = {"clave": None, "patrones": []}


def _patrones_voz():
    try:
        clave = (RUTA_DB, os.path.getmtime(RUTA_DB))
    except OSError:
        return []
    if clave != _memoria_voz["clave"]:
        patrones = []
        try:
            with _conectar() as conexion:
                filas = conexion.execute(
                    f"SELECT palabra_frase, texto_para_voz FROM {TABLA_VOZ}"
                ).fetchall()
        except sqlite3.Error:
            filas = []
        for palabra, para_voz in sorted(filas, key=lambda f: -len(f[0])):
            if not para_voz or para_voz == palabra or palabra.lower() in _TAMBIEN_CASTELLANAS:
                continue
            escrita = re.escape(palabra.replace("’", "'")).replace("'", "['’]?")
            patrones.append((re.compile(r"(?<![\wñÑ'’])" + escrita + r"(?![\wñÑ'’])", re.IGNORECASE), para_voz))
        _memoria_voz.update(clave=clave, patrones=patrones)
    return _memoria_voz["patrones"]


# Pronunciación de Cochabamba (pedido de la docente, 29/09/2026): la "chk" se
# dice "sh" (kachkanki -> kashanki). Ninguna palabra castellana tiene "chk".
_CHK = re.compile(r"chk", re.IGNORECASE)


def texto_para_hablar(texto):
    """Cambia las palabras quechuas por la forma aprendida de los audios de la
    docente, solo para la voz (la pantalla muestra la escritura correcta).
    YURA_PRONUNCIACION_APRENDIDA=0 lo desactiva."""
    if not texto or os.environ.get("YURA_PRONUNCIACION_APRENDIDA", "1").strip() == "0":
        return texto
    for patron, para_voz in _patrones_voz():
        texto = patron.sub(para_voz, texto)
    return _CHK.sub(lambda m: "sh" if m.group(0).islower() else "Sh", texto)


def voz_de(palabra):
    """(escritura para la voz, fijada por la docente) de una palabra."""
    with _conectar() as conexion:
        fila = conexion.execute(
            f"SELECT texto_para_voz, fijada FROM {TABLA_VOZ} WHERE palabra_frase = ?", (palabra,)
        ).fetchone()
    return (fila[0], bool(fila[1])) if fila else (palabra, False)


def fijar_voz(palabra, texto):
    """La docente dicta cómo debe sonar la palabra con la voz de Yura. Queda
    fija: los entrenamientos automáticos ya no la cambian. Texto vacío la
    devuelve a la forma automática."""
    texto = re.sub(r"\s+", " ", str(texto or "")).strip()[:80]
    with _conectar() as conexion:
        conexion.execute(
            f"INSERT OR IGNORE INTO {TABLA_VOZ} (palabra_frase, texto_para_voz, fecha) VALUES (?, ?, ?)",
            (palabra, palabra, datetime.now().isoformat(timespec="seconds")),
        )
        if texto:
            conexion.execute(
                f"UPDATE {TABLA_VOZ} SET texto_para_voz = ?, fijada = 1, fecha = ? WHERE palabra_frase = ?",
                (texto, datetime.now().isoformat(timespec="seconds"), palabra),
            )
        else:
            conexion.execute(
                f"UPDATE {TABLA_VOZ} SET texto_para_voz = ?, fijada = 0, fecha = ? WHERE palabra_frase = ?",
                (palabra, datetime.now().isoformat(timespec="seconds"), palabra),
            )


# ------------------------------------------------------------------
# Evaluación con lo aprendido de cómo escribe el reconocedor el quechua
# ------------------------------------------------------------------

# Sonidos fuertes del inicio que el reconocedor suele no escribir: «umpi» por
# ch'umpi, «anchai» por k'anchay, «hatung» por jatun (audios de la docente).
_INICIO_QUE_SE_PIERDE = re.compile(r"^(ch'|[kqpt]'|[kqpt]h|j)")


_memoria_todas = {"clave": None, "formas": {}}


def _todas_las_formas_del_diccionario():
    """{forma simplificada (ll como l y como y): palabras}, en memoria hasta
    que cambia el archivo de la base."""
    import traductor
    try:
        clave = (RUTA_DB, os.path.getmtime(RUTA_DB))
    except OSError:
        clave = None
    if clave is not None and clave == _memoria_todas["clave"]:
        return _memoria_todas["formas"]
    formas = {}
    with _conectar() as conexion:
        for registro in traductor._leer_registros_vocabulario(conexion):
            palabra = str(registro["quechua"] or "")
            for ll in ("l", "y"):
                formas.setdefault(texto_util.simplificar_quechua(palabra, ll).replace(" ", ""), set()).add(palabra)
    _memoria_todas.update(clave=clave, formas=formas)
    return formas


def _formas_relajadas(correcta):
    """Formas de la palabra sin el sonido fuerte del inicio o sin la q final,
    solo si no coinciden con otra palabra del diccionario."""
    escrita = texto_util.normalizar(correcta).replace("’", "'")
    formas = set()
    for ll in ("l", "y"):
        simple = texto_util.simplificar_quechua(correcta, ll).replace(" ", "")
        opciones = []
        if _INICIO_QUE_SE_PIERDE.match(escrita):
            opciones.append(re.sub(r"^(ch|[kpty])", "", simple))
        if escrita.endswith("q"):
            opciones += [o[:-1] for o in opciones] + [simple[:-1]]
        formas.update(opciones)
    diccionario = _todas_las_formas_del_diccionario()
    propias = {correcta}
    return {
        forma for forma in formas
        if len(forma) >= 3 and not (diccionario.get(forma, set()) - propias)
    }


def respuesta_aceptada(dicho, correcta, variantes_aprendidas=None):
    """¿La respuesta hablada (ya transcrita) es la palabra correcta?

    Usa el evaluador de siempre, lo aprendido de los audios de la docente y
    las formas en que el reconocedor suele escribir el quechua. Es la función
    que usan el juego, la práctica y el modo docente.
    """
    if variantes_aprendidas is None:
        variantes_aprendidas = variantes(correcta)
    # Si lo dicho es exactamente OTRA palabra del diccionario ("k'acha" cuando
    # se espera p'acha), no se acepta por parecido.
    diccionario = _todas_las_formas_del_diccionario()
    duenas = set()
    for ll in ("l", "y"):
        duenas |= diccionario.get(texto_util.simplificar_quechua(dicho, ll).replace(" ", ""), set())
    if duenas and correcta not in duenas and not any(
        _misma_palabra(d, correcta) for d in duenas
    ):
        return False
    if texto_util.respuesta_quechua_correcta(dicho, correcta, variantes_aprendidas):
        return True
    dicho_afinado = afinar_vosk(dicho)
    if dicho_afinado != dicho:
        if texto_util.respuesta_quechua_correcta(dicho_afinado, correcta, variantes_aprendidas):
            return True
        if _misma_palabra(dicho_afinado, correcta):
            return True
    dicho_simple = texto_util.simplificar_quechua(dicho)
    junto = dicho_simple.replace(" ", "")
    palabras = dicho_simple.split()
    for forma in _formas_relajadas(correcta):
        if junto == forma or forma in palabras:
            return True
        if len(forma) >= 6 and texto_util.distancia_edicion(junto, forma) <= 1:
            return True
    return False


_RUTA_MAPA_VOSK = os.path.join(RAIZ, "basedatos", "mapa_acustico_vosk.json")
_memoria_mapa_vosk = {"clave": None, "mapa": {}}

_COMANDOS_SISTEMA_VOSK = {
    "jugar", "traducir", "conversar", "menu", "volver al menu",
    "apagate", "despierta", "silencio", "si", "no", "ensename quechua",
    "repetir", "otra vez", "salir"
}

# "apágate" no está en el vocabulario del modelo de Vosk, así que nunca la
# escribe: la aproxima con palabras que sí conoce. Medido en la Raspberry Pi
# (voz real y voces de prueba). "Apaga te" ya se reconoce como orden; estas
# no. Siempre se pide confirmar con "sí", así que un falso positivo no apaga.
_APROXIMACIONES_APAGATE_VOSK = {
    "gate", "a gate", "pa gate", "a pa gate", "paga te", "a paga te", "date", "a date", "pa date",
    "para date", "para te", "para ti", "a para te", "a para ti", "apaga ti", "atada te", "atala te",
    "a paquete", "apaga paquete", "aparte", "a pagarte", "pagarte", "esa pagarte",
}
# "Yura" tampoco está en el vocabulario: Vosk la escribe "jura" o "llora".
_PREFIJOS_ORDEN_VOSK = ("yura", "jura", "llora", "lula", "puedes", "pues")
_SUFIJOS_ORDEN_VOSK = ("por favor", "ya", "ahora")


# Cómo escribe Vosk las órdenes dichas por quien usa a Yura, aprendido con
# basedatos/entrenar_ordenes.py ({"ordenes": {"para date": "apagate", ...}}).
RUTA_ORDENES_VOSK = os.path.join(RAIZ, "basedatos", "ordenes_aprendidas_vosk.json")
_memoria_ordenes_vosk = {"clave": None, "ordenes": {}}


def _ordenes_aprendidas_vosk():
    ruta = RUTA_ORDENES_VOSK
    try:
        clave = (ruta, os.path.getmtime(ruta))
    except OSError:
        return {}
    if _memoria_ordenes_vosk["clave"] != clave:
        import json

        try:
            with open(ruta, encoding="utf-8") as archivo:
                ordenes = dict(json.load(archivo).get("ordenes", {}))
        except (OSError, ValueError, AttributeError):
            ordenes = {}
        _memoria_ordenes_vosk.update(clave=clave, ordenes=ordenes)
    return _memoria_ordenes_vosk["ordenes"]


def _orden_vosk(texto_normalizado):
    """La orden que Vosk escribió deformada ("para date" -> "apagate"), o None."""
    palabras = texto_normalizado.split()
    while palabras and palabras[0] in _PREFIJOS_ORDEN_VOSK:
        palabras = palabras[1:]
    nucleo = " ".join(palabras)
    for sufijo in _SUFIJOS_ORDEN_VOSK:
        if nucleo.endswith(" " + sufijo):
            nucleo = nucleo[: -len(sufijo) - 1]
    aprendidas = _ordenes_aprendidas_vosk()
    for candidato in (texto_normalizado, nucleo):
        if candidato in aprendidas:
            return aprendidas[candidato]
    if nucleo in _APROXIMACIONES_APAGATE_VOSK:
        return "apagate"
    # "málaga gate", "la date": frase corta que termina en "gate"/"date" (apá-GATE).
    palabras = nucleo.split()
    if 1 <= len(palabras) <= 3 and palabras[-1] in ("gate", "date"):
        return "apagate"
    return None


def _cargar_mapa_vosk():
    try:
        mtime = os.path.getmtime(_RUTA_MAPA_VOSK) if os.path.exists(_RUTA_MAPA_VOSK) else 0
    except OSError:
        mtime = 0
    if _memoria_mapa_vosk["clave"] != mtime:
        import json
        import unicodedata

        mapa = {}
        if os.path.exists(_RUTA_MAPA_VOSK):
            try:
                with open(_RUTA_MAPA_VOSK, "r", encoding="utf-8") as f:
                    mapa = json.load(f)
            except Exception:
                mapa = {}

        def _norm(s):
            s = str(s or "").lower().strip()
            return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

        mapa_norm = {_norm(k): v for k, v in mapa.items()}
        _memoria_mapa_vosk.update(clave=mtime, mapa=mapa_norm)
    return _memoria_mapa_vosk["mapa"]


# Modo castellano / quechua: en una pregunta, una parte es castellano y otra
# quechua. "¿Cómo se dice AZUL en quechua?": azul es castellano (no se toca).
# "¿Qué significa ALLQU?": allqu es quechua (se busca en el diccionario).
_PREFIJO_YURA = r"^(?:(?:yura|jura|llora|yuraq)\s+)?"
_MARCO_CASTELLANO = re.compile(
    _PREFIJO_YURA + r"(como se dice|como digo|como se escribe|como se pronuncia|traduce|traduceme|traducir)\b"
)
_MARCO_QUECHUA = re.compile(
    _PREFIJO_YURA + r"(que significa|que quiere decir|significado de|que es)\s+(.+?)(?:\s+en (?:castellano|espanol))?$"
)
# Palabras castellanas comunes: si una frase tiene varias, es castellano y no
# se le cambian palabras por quechua ("traduce agua" no es "traduce Aywa").
_PALABRAS_CASTELLANAS = {
    "que", "como", "se", "dice", "digo", "en", "el", "la", "los", "las", "de", "del", "es", "un",
    "una", "quiero", "mi", "tu", "por", "para", "con", "yo", "me", "te", "no", "hola", "quechua",
    "significa", "decir", "quiere", "palabra", "traduce", "cual", "donde", "cuando", "porque",
    "esta", "este", "eso", "esto", "muy", "mas", "pero", "tengo", "hay", "puedes", "ayuda",
}


# Cómo escribe Vosk las palabras dentro de las preguntas, aprendido con
# basedatos/aprender_preguntas_vosk.py ({"quechua": {"daisy": "Wasi"},
# "castellano": {"que hacen": "casa"}}).
RUTA_PREGUNTAS_VOSK = os.path.join(RAIZ, "basedatos", "mapa_preguntas_vosk.json")
_memoria_preguntas = {"clave": None, "mapa": {}}
_HUECO_COMO_SE_DICE = re.compile(_PREFIJO_YURA + r"(como se dice)\s+(.+?)(?:\s+en quechua)?$")


def _preguntas_vosk():
    try:
        clave = (RUTA_PREGUNTAS_VOSK, os.path.getmtime(RUTA_PREGUNTAS_VOSK))
    except OSError:
        return {}
    if _memoria_preguntas["clave"] != clave:
        import json

        try:
            with open(RUTA_PREGUNTAS_VOSK, encoding="utf-8") as archivo:
                mapa = json.load(archivo)
        except (OSError, ValueError):
            mapa = {}
        _memoria_preguntas.update(clave=clave, mapa=mapa)
    return _memoria_preguntas["mapa"]


def _palabra_quechua_parecida(texto):
    """La palabra quechua del diccionario a la que más se parece lo que
    escribió Vosk ("alcohol" -> Allqu), o None si no hay una clara."""
    aprendida = _preguntas_vosk().get("quechua", {}).get(texto_util.normalizar(texto))
    if aprendida:
        return aprendida
    candidata = afinar_vosk(texto)
    if texto_util.normalizar(candidata) != texto_util.normalizar(texto):
        return candidata  # el mapa acústico o lo aprendido ya la reconocen
    formas = _todas_las_formas_del_diccionario()
    buscada = texto_util.simplificar_quechua(candidata).replace(" ", "")
    if buscada in formas and len(formas[buscada]) == 1:
        return next(iter(formas[buscada]))
    if len(buscada) < 3:
        return None
    distancias = sorted(
        (texto_util.distancia_edicion(buscada, forma), forma) for forma in formas if forma
    )
    if not distancias:
        return None
    mejor, forma = distancias[0]
    segunda = distancias[1][0] if len(distancias) > 1 else 99
    # Solo si es claramente la más parecida (no un empate entre dos palabras).
    if mejor <= max(1, len(forma) // 3) and segunda > mejor and len(formas[forma]) == 1:
        return next(iter(formas[forma]))
    return None


def afinar_vosk(texto):
    """Afina la transcripción acústica producida por Vosk (Kaldi en español).

    Convierte las aproximaciones fonéticas castellanas que Vosk escucha hacia
    las palabras quechuas exactas aprendidas de las grabaciones de la docente
    ('alcohol' -> 'Allqu', 'mi cuna' -> 'Mikhuna', 'es kai' -> 'Iskay').
    Preserva intactos los comandos de control del robot.
    """
    if not texto:
        return ""
    texto_limpio = str(texto).strip()
    if texto_limpio in ("[unk]", "unk"):
        return ""

    import unicodedata

    def _norm(s):
        s = str(s or "").lower().strip()
        return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

    t_norm = _norm(texto_limpio)
    # "quechua" no está en todas las pronunciaciones de Vosk: a veces escribe
    # "en que hecho" o "en que echo" (visto en vivo, 07/10/2026).
    corregido = re.sub(r"\ben (?:que|ke) (?:hecho|echo|chua|chuas|cha)\b", "en quechua", t_norm)
    # "dime los números..." llega como "vive los" o "me los".
    corregido = re.sub(r"^(?:vive|me|time|ime) (los|las)\b", r"dime \1", corregido)
    if corregido != t_norm:
        t_norm = texto_limpio = corregido
    if t_norm in _COMANDOS_SISTEMA_VOSK:
        return texto_limpio
    # «camina cinco pasos»: el número no se cambia por quechua («cinco» -> Sunqu).
    if texto_util.pasos_pedidos(t_norm) and texto_util.orden_movimiento(t_norm):
        return texto_limpio
    orden = _orden_vosk(t_norm)
    if orden:
        return orden

    mapa = _cargar_mapa_vosk()
    if t_norm in mapa:
        return mapa[t_norm]

    # Preguntas: la parte castellana no se toca (salvo lo aprendido de cómo
    # Vosk la deforma: "que hacen" -> "casa"); la quechua se busca.
    if _MARCO_CASTELLANO.match(t_norm):
        hueco = _HUECO_COMO_SE_DICE.match(t_norm)
        castellano = hueco and _preguntas_vosk().get("castellano", {}).get(hueco.group(2))
        return f"como se dice {castellano} en quechua" if castellano else texto_limpio
    marco = _MARCO_QUECHUA.match(t_norm)
    if marco:
        quechua = _palabra_quechua_parecida(marco.group(2))
        return f"{marco.group(1)} {quechua}" if quechua else texto_limpio

    variante_db = palabra_por_variante(texto_limpio)
    if variante_db:
        return variante_db

    # Una frase en castellano no se "quechuiza" palabra por palabra.
    if len(set(t_norm.split()) & _PALABRAS_CASTELLANAS) >= 2:
        return texto_limpio

    resultado = t_norm
    cambio = False
    varias_palabras = len(t_norm.split()) > 1
    for acustica, quechua in sorted(mapa.items(), key=lambda x: -len(x[0])):
        # Dentro de una frase, una palabra castellana corta ("que", "agua",
        # "pero") no se cambia: "desde que" no es "desde Wawqi".
        if varias_palabras and " " not in acustica and len(acustica) < 5:
            continue
        if len(acustica) >= 3 and acustica in resultado:
            resultado_nuevo = re.sub(r"\b" + re.escape(acustica) + r"\b", quechua, resultado)
            if resultado_nuevo != resultado:
                resultado = resultado_nuevo
                cambio = True

    return resultado if cambio else texto_limpio



_memoria_audios = {"clave": None, "patron": None, "rutas": {}}


def _patron_audios():
    """Una expresión con todas las palabras que tienen voz entrenada."""
    try:
        clave = (RUTA_DB, os.path.getmtime(RUTA_DB), CARPETA_VOZ_YURA)
    except OSError:
        return None, {}
    if clave != _memoria_audios["clave"]:
        rutas = {}
        try:
            with _conectar() as conexion:
                filas = conexion.execute(
                    f"SELECT palabra_frase, audio_yura FROM {TABLA_VOZ} WHERE audio_yura IS NOT NULL"
                ).fetchall()
        except sqlite3.Error:
            filas = []
        for palabra, archivo in filas:
            ruta = os.path.join(CARPETA_VOZ_YURA, os.path.basename(archivo))
            if os.path.exists(ruta) and palabra.lower() not in _TAMBIEN_CASTELLANAS:
                rutas[texto_util.normalizar(palabra).replace("'", "")] = ruta
        partes = [
            re.escape(palabra.replace("’", "'")).replace("'", "['’]?")
            for palabra, _ in sorted(filas, key=lambda f: -len(f[0]))
            if texto_util.normalizar(palabra).replace("'", "") in rutas
        ]
        patron = re.compile(r"(?<![\wñÑ'’])(" + "|".join(partes) + r")(?![\wñÑ'’])", re.IGNORECASE) if partes else None
        _memoria_audios.update(clave=clave, patron=patron, rutas=rutas)
    return _memoria_audios["patron"], _memoria_audios["rutas"]


def partes_para_hablar(texto):
    """Divide lo que Yura va a decir: [("texto", "En quechua se dice"),
    ("audio", ruta de la palabra con la voz entrenada), ("texto", ", que...")].

    Desactivado por defecto (29/09/2026, pedido del equipo): la palabra
    entrenada cambiaba el timbre y Yura debe mantener su voz natural. Se
    activa con YURA_VOZ_AUDIO_APRENDIDO=1; lo entrenado sigue guardado."""
    if not texto or os.environ.get("YURA_VOZ_AUDIO_APRENDIDO", "0").strip() != "1":
        return [("texto", texto)]
    patron, rutas = _patron_audios()
    if patron is None:
        return [("texto", texto)]
    partes, inicio = [], 0
    for coincidencia in patron.finditer(texto):
        clave = texto_util.normalizar(coincidencia.group(0)).replace("'", "")
        if clave not in rutas:
            continue
        if coincidencia.start() > inicio:
            partes.append(("texto", texto[inicio:coincidencia.start()]))
        partes.append(("audio", rutas[clave]))
        inicio = coincidencia.end()
    if inicio < len(texto):
        partes.append(("texto", texto[inicio:]))
    return partes or [("texto", texto)]
