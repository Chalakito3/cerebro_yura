"""Grupo 5: base de datos ausente, vacía, corrupta, con esquema raro, NULL, bloqueada, grande.
Todo sobre COPIAS / archivos nuevos en el scratchpad."""
from comun import *  # noqa
import os
import sqlite3
import threading
from unittest.mock import Mock
import conversacion
import traductor
from juego import Juego
from main_robot import BrainYura, RobotStates

D = os.path.join(SCRATCH, "g05")
os.makedirs(D, exist_ok=True)


def preparar(nombre, contenido=None, sql=None):
    carpeta = os.path.join(D, nombre)
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, "diccionario.db")
    if os.path.exists(ruta):
        os.remove(ruta)
    if contenido is not None:
        with open(ruta, "wb") as fh:
            fh.write(contenido)
    if sql is not None:
        c = sqlite3.connect(ruta)
        c.executescript(sql)
        c.commit()
        c.close()
    return carpeta, ruta


def conversacion_con(carpeta):
    conversacion.__file__ = os.path.join(carpeta, "conversacion.py")  # redirige la ruta de la BD
    conversacion._conexion_vocabulario = None
    conversacion.cancelar_sesion_educativa()


def iniciar_robot(ruta):
    r = object.__new__(BrainYura)
    r.db_path = ruta
    r.inicializar_sistemas_locales()
    return r


def traducir(conn, frase="casa"):
    habla = []
    v = [0]
    ret = traductor.ejecutar_traducir(lambda: frase, habla.append, conn, None,
                                      lambda: (v.__setitem__(0, v[0] + 1) or v[0] <= 1))
    return ret, habla


def err(x):
    return "FALLA", f"EXCEPCIÓN NO CONTROLADA {type(x).__name__}: {x}"


ESQUEMA_OK = """CREATE TABLE nivel1_prueba (id INTEGER PRIMARY KEY, palabra_frase TEXT,
pronunciacion TEXT, traduccion TEXT, significado TEXT);"""

# ------------------------------------------------ 1. ausente
carpeta, ruta = preparar("ausente")
conversacion_con(carpeta)
caso("YURA-EXT-501", "conversacion", "BD ausente: iniciar práctica", "enséñame quechua",
     "aviso claro sin excepción", lambda: conversacion.procesar_entrada("enséñame quechua", None),
     lambda x: ("OK", repr(x["respuesta"])))
caso("YURA-EXT-502", "main_robot", "BD ausente: inicializar_sistemas_locales", ruta,
     "db_conn=None y alerta", lambda: iniciar_robot(ruta).db_conn,
     lambda x: ("OK" if x is None else "FALLA", f"db_conn={x}"))
caso("YURA-EXT-503", "traductor", "BD ausente: ejecutar_traducir", "casa", "aviso y volver al menú",
     lambda: traducir(None), lambda x: ("OK", repr(x)))
caso("YURA-EXT-504", "main_robot", "BD ausente: arranque de BrainYura crea la BD?", ruta,
     "no crear archivo vacío", lambda: os.path.exists(ruta),
     lambda x: ("FALLA" if x else "OK", f"archivo creado={x}"))

# ------------------------------------------------ 2. vacía (0 bytes)
carpeta, ruta = preparar("vacia", b"")
r = iniciar_robot(ruta)
caso("YURA-EXT-505", "main_robot", "BD de 0 bytes: inicializar", "archivo 0 bytes",
     "alerta: BD sin vocabulario", lambda: r.db_conn,
     lambda x: ("FALLA" if x is not None else "OK", f"db_conn={type(x).__name__}; imprime '[OK] enlazada' sin avisar que no hay tablas"))
caso("YURA-EXT-506", "traductor", "BD de 0 bytes: traducir 'casa'", "casa", "aviso de BD vacía",
     lambda: traducir(r.db_conn), lambda x: ("OBSERVACION", repr(x)))
conversacion_con(carpeta)
caso("YURA-EXT-507", "conversacion", "BD de 0 bytes: práctica", "enséñame quechua", "aviso",
     lambda: conversacion.procesar_entrada("enséñame quechua", None), lambda x: ("OK", repr(x["respuesta"])))

# ------------------------------------------------ 3. no es SQLite
carpeta, ruta = preparar("texto", b"esto no es una base de datos\n" * 200)
r = iniciar_robot(ruta)
caso("YURA-EXT-508", "main_robot", "Archivo de texto como BD: inicializar", "texto plano",
     "detectar y alertar", lambda: r.db_conn,
     lambda x: ("FALLA" if x is not None else "OK", f"db_conn={type(x).__name__} (lo da por bueno)"))
caso("YURA-EXT-509", "traductor", "Archivo de texto como BD: traducir", "casa",
     "mensaje de error, sin excepción", lambda: traducir(r.db_conn), evalua=lambda x: err(x) if isinstance(x, BaseException) else ("OK", repr(x)))
conversacion_con(carpeta)
caso("YURA-EXT-510", "conversacion", "Archivo de texto como BD: práctica", "enséñame quechua",
     "mensaje, sin excepción", lambda: conversacion.procesar_entrada("enséñame quechua", None),
     lambda x: err(x) if isinstance(x, BaseException) else ("OK", repr(x)))
conversacion_con(carpeta)
caso("YURA-EXT-511", "conversacion", "Archivo de texto como BD: '¿cómo se dice casa?'", "como se dice casa",
     "mensaje, sin excepción", lambda: conversacion.procesar_entrada("como se dice casa", None),
     lambda x: err(x) if isinstance(x, BaseException) else ("OK", repr(x)))
j = Juego(["casa"], lambda p: traductor.consultar_diccionario_local(p, r.db_conn), lambda: "wasi",
          lambda t: None, lambda c: None, BrainYura._normalizar_texto.__get__(object.__new__(BrainYura)))
caso("YURA-EXT-512", "juego", "Archivo de texto como BD: turno de juego", "wasi", "sin excepción",
     lambda: j.ejecutar_turno(), lambda x: err(x) if isinstance(x, BaseException) else ("OK", repr(x)))

# ¿Qué le pasa al bucle principal?
rb = object.__new__(BrainYura)
rb.state = RobotStates.TRADUCIR
rb.running = True
rb.db_conn = r.db_conn
rb.groq_client = None
rb.hw = Mock()
rb.escuchar_voz = Mock(return_value="casa")
rb._set_web_status = Mock()
caso("YURA-EXT-513", "main_robot", "Archivo de texto como BD: loop_principal en modo traductor", "casa",
     "el robot sigue vivo (captura el error)", lambda: rb.loop_principal(),
     lambda x: ("FALLA", f"loop_principal TERMINA con {type(x).__name__}: {x}; en web/app.py el hilo muere y NO se llama os._exit -> la pantalla sigue mostrando el último estado")
     if isinstance(x, BaseException) else ("OK", repr(x)))

# tras la caída, ¿qué ve la pantalla? (hilo muerto, servidor vivo)
import threading as _th
import web.app as webapp
rb.web_status = {"phase": "PENSANDO", "content": "casa", "translation": "", "result": None, "updated_at": None}
rb.web_status_lock = _th.Lock()
del rb._set_web_status
webapp.robot = rb
caso("YURA-EXT-522", "web", "Pantalla después de que el hilo del robot muere por la BD", "GET /api/status",
     "indicar que el robot no está funcionando", lambda: webapp.app.test_client().get("/api/status").json,
     lambda x: ("FALLA" if x["running"] else "OK",
                f"running={x['running']} state={x['state']} activity={x['activity']!r} (la pantalla dice que todo va bien)"))
webapp.robot = None

# ------------------------------------------------ 4. tablas sin columnas esperadas / nombres raros
carpeta, ruta = preparar("esquema", sql="""
CREATE TABLE nivel1_sin_traduccion (id INTEGER, palabra_frase TEXT);
CREATE TABLE "nivel1_Frutas" (id INTEGER, palabra_frase TEXT, pronunciacion TEXT, traduccion TEXT);
INSERT INTO "nivel1_Frutas" VALUES (1,'Lurasnu',NULL,'Durazno');
CREATE TABLE "nivel1_x""; DROP TABLE t;--" (id INTEGER, palabra_frase TEXT, pronunciacion TEXT, traduccion TEXT);
INSERT INTO "nivel1_x""; DROP TABLE t;--" VALUES (1,'Wasi',NULL,'Casa');
CREATE TABLE "nivel2_con espacio" (id INTEGER, palabra_frase TEXT, pronunciacion TEXT, traduccion TEXT);
CREATE TABLE nivel007_ok (id INTEGER, palabra_frase TEXT, pronunciacion TEXT, traduccion TEXT);
INSERT INTO nivel007_ok VALUES (1,'Inti',NULL,'Sol');
CREATE TABLE t (x);
""")
c = sqlite3.connect(ruta)


def existe_t(con):
    return bool(con.execute("select 1 from sqlite_master where name='t'").fetchone())


caso("YURA-EXT-514", "traductor", "Esquema raro: tablas detectadas", "sin columnas, mayúsculas, comillas/SQL, espacio, nivel007",
     "ignorar las inválidas sin error; avisar de tablas ignoradas",
     lambda: traductor._tablas_de_vocabulario(c),
     lambda x: ("OBSERVACION", f"detectadas={x}; 'nivel1_Frutas' (con datos) se ignora EN SILENCIO; tabla t sigue existiendo={existe_t(c)}"))
caso("YURA-EXT-515", "traductor", "Esquema raro: buscar 'durazno' (tabla nivel1_Frutas)", "durazno",
     "encontrar o avisar", lambda: traductor.buscar_vocabulario("durazno", "espanol", c),
     lambda x: ("OBSERVACION", f"encontrado={x['encontrado']}"))

# ------------------------------------------------ 5. filas con NULL
carpeta, ruta = preparar("nulos", sql=ESQUEMA_OK + """
INSERT INTO nivel1_prueba VALUES (1, NULL, NULL, 'Casa', NULL);
INSERT INTO nivel1_prueba VALUES (2, 'Wasi', NULL, NULL, NULL);
INSERT INTO nivel1_prueba VALUES (3, '', NULL, 'Sol', '');
""")
c = sqlite3.connect(ruta)
caso("YURA-EXT-516", "traductor", "Fila con quechua NULL: traducir 'casa'", "casa",
     "no decir 'None'", lambda: traducir(c, "casa"),
     lambda x: ("FALLA" if "None" in " ".join(x[1]) else "OK", repr(x[1])))
caso("YURA-EXT-517", "traductor", "Fila con quechua vacío '': traducir 'sol'", "sol",
     "no quedar mudo / avisar", lambda: traducir(c, "sol"), lambda x: ("OK", repr(x[1])))
caso("YURA-EXT-518", "traductor", "NULL en vocabulario enviado a Groq", "casa sol wasi",
     "no enviar 'None' como vocabulario verificado",
     lambda: traductor.formatear_vocabulario(traductor.vocabulario_relevante("casa wasi", c)),
     lambda x: ("FALLA" if "None" in x else "OK", repr(x)))
conversacion_con(carpeta)


def practicas_20():
    salidas = []
    for semilla in range(20):
        conversacion.random.seed(semilla)
        conversacion.cancelar_sesion_educativa()
        salidas.append(conversacion.procesar_entrada("enséñame quechua", None)["respuesta"])
    return salidas


caso("YURA-EXT-519", "conversacion", "Práctica con filas quechua NULL / '' (20 semillas)", "enséñame quechua",
     "no decir 'None' ni una palabra vacía", practicas_20,
     lambda x: ("FALLA" if any("None" in s or "se dice ." in s for s in x) else "OK",
                f"con 'None'={sum('None' in s for s in x)}, vacías={sum('se dice .' in s for s in x)}; ej: {sorted(set(x))[:2]}"))
conversacion.cancelar_sesion_educativa()

# ------------------------------------------------ 6. BD bloqueada
ruta_b = copia_bd("g05_bloqueada.db")
bloqueo = sqlite3.connect(ruta_b, isolation_level=None)
bloqueo.execute("BEGIN EXCLUSIVE")
lectora = sqlite3.connect(ruta_b, check_same_thread=False)  # timeout por defecto = 5 s
caso("YURA-EXT-520", "traductor", "BD bloqueada (BEGIN EXCLUSIVE en otra conexión)", "casa",
     "mensaje de error, sin excepción", lambda: traducir(lectora),
     lambda x: err(x) if isinstance(x, BaseException) else ("OK", repr(x)))
bloqueo.execute("ROLLBACK")

# ------------------------------------------------ 7. BD grande (rendimiento)
ruta_g = copia_bd("g05_grande.db")
cg = sqlite3.connect(ruta_g)
cg.executemany("INSERT INTO nivel1_colores (palabra_frase, pronunciacion, traduccion) VALUES (?,?,?)",
               [(f"Palabra{i}", None, f"termino{i}") for i in range(50000)])
cg.commit()
t0 = time.perf_counter()
traductor.buscar_vocabulario("casa", "espanol", cg)
t_busq = time.perf_counter() - t0
conversacion._conexion_vocabulario = cg
conversacion.cancelar_sesion_educativa()
t0 = time.perf_counter()
conversacion.procesar_entrada("quiero practicar", None)
t_prac = time.perf_counter() - t0
caso("YURA-EXT-521", "traductor", "BD con 50.187 filas: tiempo de búsqueda y de iniciar práctica",
     "casa / quiero practicar", "< 0,5 s", lambda: (t_busq, t_prac),
     lambda x: ("OBSERVACION" if max(x) > 0.5 else "OK",
                f"búsqueda={x[0]:.2f}s práctica={x[1]:.2f}s (lee TODAS las filas en cada consulta; práctica = 5 lecturas)"))

resumen()
volcar_matriz("../05_g05_matriz.md")
