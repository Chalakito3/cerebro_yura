import csv
import hmac
import io
import logging
import os
import sys
import threading
from datetime import datetime, timezone

from urllib.parse import urlparse

from flask import Flask, Response, jsonify, redirect, render_template, request, send_file, url_for

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from main_robot import BrainYura, RobotStates
import depuracion
import pronunciaciones
import resultados

# Versión del producto (archivo VERSION; historial en CHANGELOG.md).
try:
    with open(os.path.join(PROJECT_ROOT, "VERSION"), encoding="utf-8") as _archivo:
        VERSION = _archivo.read().strip()
except OSError:
    VERSION = "desconocida"


CARD_EXAMPLES = [
    {
        "key": "rimaykullayki",
        "title": "Rimaykullayki",
        "written": "Rimaykullayki",
        "pronunciation": "Ri-ma-y-ku-llay-ki",
        "meaning": "Hola",
        "example": "Rimaykullayki, imaynalla kachkanki?"
    },
    {
        "key": "allinpunchay",
        "title": "Allin p'unchay",
        "written": "Allin p'unchay",
        "pronunciation": "A-lin p'un-chay",
        "meaning": "Buenos días",
        "example": "Allin p'unchay, wawqi."
    },
    {
        "key": "allintuta",
        "title": "Allin tuta",
        "written": "Allin tuta",
        "pronunciation": "A-lin tu-ta",
        "meaning": "Buenas noches",
        "example": "Allin tuta, ñañay."
    },
    {
        "key": "yusulpayki",
        "title": "Yusulpayki",
        "written": "Yusulpayki",
        "pronunciation": "Yu-su-lpay-ki",
        "meaning": "Gracias",
        "example": "Yusulpayki, uywaq."
    },
    {
        "key": "anchata",
        "title": "Anchata munakuyki",
        "written": "Anchata munakuyki",
        "pronunciation": "An-cha-ta mu-na-kuy-ki",
        "meaning": "Te quiero mucho",
        "example": "Anchata munakuyki, wayna."
    },
    {
        "key": "imaynallakachkanki",
        "title": "Imaynalla kachkanki",
        "written": "Imaynalla kachkanki",
        "pronunciation": "I-may-na-lla kach-kan-ki",
        "meaning": "¿Cómo estás?",
        "example": "Imaynalla kachkanki, tata?"
    }
]


app = Flask(__name__)
# Solo se reciben formularios y JSON pequeños (ningún archivo).
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024

# La pantalla consulta /api/status cada 5 s: sin esto el registro anotaba
# unas 17.000 peticiones al día. Con YURA_DEBUG=1 se ven todas.
if not depuracion.activa():
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
robot = None
robot_lock = threading.Lock()


def _status_payload():
    with robot_lock:
        current_robot = robot
        if current_robot is None:
            return {
                "robot": "YURA",
                "state": "BACKEND_NOT_STARTED",
                "running": False,
                "activity": "BACKEND NO INICIADO",
                "message": "La pantalla está lista para conectar con Yura.",
                "phase": "SIN_CONEXION",
                "content": "",
                "translation": "",
                "result": None,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "participante": resultados.participante_actual(),
            }

        state = current_robot.state
        state_info = {
            RobotStates.MENU: (
                "LISTA PARA ESCUCHAR",
                "Yura está en el menú principal."
            ),
            RobotStates.JUEGO: (
                "MODO JUEGO ACTIVO",
                "Yura está ejecutando el juego."
            ),
            RobotStates.CONVERSAR: (
                "MODO CONVERSACIÓN ACTIVO",
                "Yura está conversando."
            ),
            RobotStates.TRADUCIR: (
                "MODO TRADUCTOR ACTIVO",
                "Yura está traduciendo."
            ),
            RobotStates.SILENCIO: (
                "YURA EN SILENCIO",
                "Yura está esperando una orden para volver a hablar."
            ),
            RobotStates.ENSENAR: (
                "MODO DOCENTE",
                "La docente está enseñando pronunciaciones a Yura."
            ),
            RobotStates.SALIR: (
                "APAGANDO",
                "Yura está cerrando sus servicios."
            ),
        }
        activity, message = state_info.get(
            state,
            ("ACTIVIDAD DEL ROBOT", "Yura está trabajando.")
        )
        web_status = current_robot.get_web_status()

        return {
            "robot": "YURA",
            "state": state,
            "running": bool(current_robot.running),
            "activity": activity,
            "message": message,
            "phase": web_status.get("phase", "ESPERANDO"),
            "content": web_status.get("content", ""),
            "translation": web_status.get("translation", ""),
            "result": web_status.get("result"),
            "updated_at": web_status.get("updated_at") or datetime.now(timezone.utc).isoformat(),
            "participante": resultados.participante_actual(),
        }


def start_robot():
    global robot

    with robot_lock:
        if robot is not None:
            return robot
        robot = BrainYura()

        def _ejecutar_y_cerrar():
            # Si Yura se apaga por voz, se cierra todo el proceso
            # para no dejar la página funcionando sin robot.
            robot.loop_principal()
            if getattr(robot, "fallo_fatal", False):
                # Código 1 para que systemd (Restart=on-failure) la reinicie.
                print("[SISTEMA]: Yura se detuvo por errores; cerrando con código 1.")
                os._exit(1)
            print("[SISTEMA]: Yura se apagó; cerrando el servidor web.")
            robot.apagar_equipo_si_corresponde()
            os._exit(0)

        backend_thread = threading.Thread(
            target=_ejecutar_y_cerrar,
            name="yura-backend",
            daemon=True
        )
        backend_thread.start()
        return robot


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/status")
def status():
    datos = _status_payload()
    datos["version"] = VERSION
    if not _es_local() and not _credenciales_docentes_validas():
        # Las respuestas también pueden repetir datos personales.
        datos.update(participante="", content="", translation="", result=None)
    return jsonify(datos)


@app.get("/api/card")
def card_examples():
    return jsonify({"examples": CARD_EXAMPLES})


# Los resultados de los estudiantes no deben verse desde cualquier equipo de
# la red WiFi: fuera de esta computadora se pide la contraseña de docente.
RUTAS_DE_RESULTADOS = (
    "/resultados", "/api/resultados", "/resultados.csv", "/resultados/participante",
)
# El modo docente cambia el diccionario: la misma protección.
PREFIJOS_DE_DOCENTE = ("/ensenar", "/api/ensenar")
DIRECCIONES_LOCALES = ("127.0.0.1", "::1")
# Una página maliciosa abierta en esta computadora puede hacer que su propio
# dominio apunte a 127.0.0.1 (rebinding de DNS): la entrada sin contraseña
# vale solo si la dirección escrita es la de esta computadora.
NOMBRES_LOCALES = ("localhost", "127.0.0.1", "[::1]")


def _es_local():
    nombre = request.host.rsplit(":", 1)[0] if not request.host.endswith("]") else request.host
    return request.remote_addr in DIRECCIONES_LOCALES and nombre.lower() in NOMBRES_LOCALES


def _es_ruta_de_docente(ruta):
    return ruta in RUTAS_DE_RESULTADOS or any(
        ruta == prefijo or ruta.startswith(prefijo + "/") for prefijo in PREFIJOS_DE_DOCENTE
    )


def _origen_ajeno():
    """Evita que otra página envíe formularios en nombre del docente."""
    origen = request.headers.get("Origin") or request.headers.get("Referer")
    return bool(origen) and urlparse(origen).netloc != request.host


def _credenciales_docentes_validas():
    clave = os.environ.get("YURA_RESULTADOS_CLAVE", "").strip()
    credenciales = request.authorization
    return bool(
        clave and credenciales and credenciales.type.lower() == "basic"
        and hmac.compare_digest(
            (credenciales.password or "").encode("utf-8"), clave.encode("utf-8")
        )
    )


@app.before_request
def proteger_resultados():
    if not _es_ruta_de_docente(request.path):
        return None
    if request.method == "POST" and _origen_ajeno():
        return Response("Origen no permitido.", status=403, mimetype="text/plain; charset=utf-8")
    if _es_local():
        return None

    clave = os.environ.get("YURA_RESULTADOS_CLAVE", "").strip()
    if not clave:
        return Response(
            "Los resultados solo se pueden ver desde la computadora de Yura. "
            "Para verlos desde otro equipo, configure YURA_RESULTADOS_CLAVE en .env.local.",
            status=403,
            mimetype="text/plain; charset=utf-8",
        )

    if _credenciales_docentes_validas():
        return None

    return Response(
        "Se necesita la contraseña de docente para ver los resultados.",
        status=401,
        mimetype="text/plain; charset=utf-8",
        headers={"WWW-Authenticate": 'Basic realm="Resultados de Yura", charset="UTF-8"'},
    )


@app.after_request
def cabeceras_de_proteccion(respuesta):
    # Ninguna otra página puede mostrar las de Yura dentro de un marco.
    respuesta.headers.setdefault("X-Frame-Options", "DENY")
    respuesta.headers.setdefault("X-Content-Type-Options", "nosniff")
    if request.path == "/api/status" or _es_ruta_de_docente(request.path):
        respuesta.headers["Cache-Control"] = "no-store"
    return respuesta


def _filtro_participante():
    # "?participante=" (vacío) filtra los intentos sin nombre; sin el
    # parámetro se muestran todos.
    if "participante" not in request.args:
        return None
    return resultados.limpiar_participante(request.args.get("participante"))


@app.get("/resultados")
def pagina_resultados():
    return render_template(
        "resultados.html",
        datos=resultados.resumen(participante=_filtro_participante()),
    )


@app.post("/resultados/participante")
def cambiar_participante():
    resultados.definir_participante(request.form.get("participante", ""))
    return redirect(url_for("pagina_resultados"), code=303)


@app.get("/api/resultados")
def api_resultados():
    return jsonify(resultados.resumen(participante=_filtro_participante()))


def _texto_csv_seguro(valor):
    if not isinstance(valor, str):
        return valor
    # Neutralizar solo la exportación; conservar el dato original en SQLite.
    if valor.lstrip().startswith(("=", "+", "-", "@")) or valor.startswith(("\t", "\r", "\n")):
        return "'" + valor
    return valor


@app.get("/resultados.csv")
def exportar_resultados():
    salida = io.StringIO()
    # BOM para que Excel abra bien las tildes y la ñ.
    salida.write("\ufeff")
    escritor = csv.writer(salida)
    escritor.writerow([
        "id", "fecha", "actividad", "sesion", "estudiante_o_grupo",
        "palabra_espanol", "palabra_quechua", "respuesta", "correcto"
    ])
    for intento in resultados.todos_los_intentos():
        escritor.writerow([_texto_csv_seguro(valor) for valor in (
            intento["id"], intento["fecha"], intento["actividad"],
            intento["sesion"], intento["participante"], intento["palabra_espanol"],
            intento["palabra_quechua"], intento["respuesta"],
            "sí" if intento["correcto"] else "no",
        )])
    return Response(
        salida.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=resultados_yura.csv"},
    )


# ============================================================
# MODO DOCENTE: enseñar pronunciaciones a Yura
# ============================================================

def _robot_o_error():
    with robot_lock:
        actual = robot
    if actual is None:
        return None, (jsonify({"error": "Yura no está encendida."}), 503)
    return actual, None


@app.get("/ensenar")
def pagina_ensenar():
    return render_template("ensenar.html")


@app.get("/api/ensenar/palabras")
def api_palabras_docente():
    return jsonify({"palabras": pronunciaciones.palabras_con_conteo()})


@app.get("/api/ensenar/estado")
def api_estado_docente():
    with robot_lock:
        actual = robot
    if actual is None:
        return jsonify({"modo": "sin_yura", "ensenanza": {"estado": "inactivo"}})
    if actual.state == RobotStates.ENSENAR:
        modo = "activo"
    elif actual.pedido_docente.is_set():
        modo = "activando"
    else:
        modo = "inactivo"
    return jsonify({"modo": modo, "ensenanza": dict(actual.ensenanza)})


@app.get("/api/ensenar/grabaciones")
def api_grabaciones_docente():
    tabla = request.args.get("tabla", "")
    try:
        id_palabra = int(request.args.get("id", ""))
    except ValueError:
        return jsonify({"error": "Palabra no válida."}), 400
    return jsonify({"grabaciones": pronunciaciones.grabaciones(tabla, id_palabra)})


@app.post("/api/ensenar/activar")
def api_activar_docente():
    actual, error = _robot_o_error()
    if error:
        return error
    actual.activar_modo_docente()
    return jsonify({"ok": True})


@app.post("/api/ensenar/terminar")
def api_terminar_docente():
    actual, error = _robot_o_error()
    if error:
        return error
    actual.terminar_modo_docente()
    return jsonify({"ok": True})


@app.post("/api/ensenar/grabar")
def api_grabar_docente():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        return jsonify({"error": "Se necesita un objeto JSON válido."}), 400
    actual, error = _robot_o_error()
    if error:
        return error
    palabra = _palabra_pedida(datos)
    if palabra is None:
        return jsonify({"error": "Esa palabra no está en el diccionario."}), 400
    if actual.ensenanza.get("estado") in ("esperando", "grabando"):
        return jsonify({"error": "Yura ya está grabando."}), 409
    if not actual.pedir_grabacion_docente(palabra):
        return jsonify({"error": "Primero active el modo docente."}), 409
    return jsonify({"ok": True})


@app.post("/api/ensenar/guardar")
def api_guardar_docente():
    actual, error = _robot_o_error()
    if error:
        return error
    ensenanza = dict(actual.ensenanza)
    if ensenanza.get("estado") != "grabado":
        return jsonify({"error": "No hay una grabación nueva para guardar."}), 409
    palabra = ensenanza["palabra"]
    try:
        id_grabacion = pronunciaciones.guardar(palabra["tabla"], palabra["id"], ensenanza.get("transcripcion"))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 409
    actual.ensenanza = {**ensenanza, "estado": "guardado", "id_grabacion": id_grabacion}
    return jsonify({"ok": True, "id": id_grabacion})


@app.post("/api/ensenar/descartar")
def api_descartar_docente():
    actual, error = _robot_o_error()
    if error:
        return error
    ensenanza = dict(actual.ensenanza)
    if ensenanza.get("estado") == "grabado":
        pronunciaciones.descartar_pendiente()
        actual.ensenanza = {**ensenanza, "estado": "descartado"}
    return jsonify({"ok": True})


@app.post("/api/ensenar/borrar/<int:id_grabacion>")
def api_borrar_grabacion(id_grabacion):
    if not pronunciaciones.borrar(id_grabacion):
        return jsonify({"error": "Esa grabación no existe."}), 404
    return jsonify({"ok": True})


def _palabra_pedida(datos):
    tabla = datos.get("tabla")
    identificador = datos.get("id")
    if not isinstance(tabla, str) or isinstance(identificador, bool):
        return None
    if not isinstance(identificador, (int, str)):
        return None
    try:
        identificador = int(identificador)
        if identificador <= 0:
            return None
        return pronunciaciones.palabra_del_diccionario(tabla, identificador)
    except (TypeError, ValueError):
        return None


@app.get("/api/ensenar/voz")
def api_voz_docente():
    """Cómo dice Yura la palabra con su voz, y si la fijó la docente."""
    palabra = _palabra_pedida(request.args)
    if palabra is None:
        return jsonify({"error": "Esa palabra no está en el diccionario."}), 400
    texto, fijada = pronunciaciones.voz_de(palabra["quechua"])
    return jsonify({"texto": texto, "fijada": fijada})


@app.post("/api/ensenar/voz")
def api_fijar_voz_docente():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        return jsonify({"error": "Se necesita un objeto JSON válido."}), 400
    texto_pedido = datos.get("texto", "")
    if not isinstance(texto_pedido, str) or len(texto_pedido) > 80:
        return jsonify({"error": "La pronunciación debe ser texto de hasta 80 caracteres."}), 400
    palabra = _palabra_pedida(datos)
    if palabra is None:
        return jsonify({"error": "Esa palabra no está en el diccionario."}), 400
    pronunciaciones.fijar_voz(palabra["quechua"], texto_pedido)
    texto, fijada = pronunciaciones.voz_de(palabra["quechua"])
    return jsonify({"ok": True, "texto": texto, "fijada": fijada})


@app.get("/api/ensenar/voz/escuchar")
def api_escuchar_voz_docente():
    """Genera con la voz de Yura (la misma de siempre) el texto que escribe
    la docente, para que lo escuche antes de guardarlo."""
    import asyncio
    import edge_tts
    texto = str(request.args.get("texto", "")).strip()[:80]
    if not texto:
        return Response(status=400)
    texto = pronunciaciones._CHK.sub(lambda m: "sh" if m.group(0).islower() else "Sh", texto)
    voz = os.environ.get("YURA_VOZ", "es-BO-SofiaNeural").strip() or "es-BO-SofiaNeural"

    async def generar():
        partes = []
        async for trozo in edge_tts.Communicate(texto, voz, rate="+5%").stream():
            if trozo["type"] == "audio":
                partes.append(trozo["data"])
        return b"".join(partes)
    try:
        audio = asyncio.run(generar())
    except Exception:
        return Response("No se pudo generar la voz (¿hay internet?).", status=503,
                        mimetype="text/plain; charset=utf-8")
    return Response(audio, mimetype="audio/mpeg", headers={"Cache-Control": "no-store"})


@app.get("/ensenar/audio/pendiente")
def audio_pendiente():
    ruta = pronunciaciones.ruta_pendiente()
    if not os.path.exists(ruta):
        return Response(status=404)
    return send_file(ruta, mimetype="audio/wav", max_age=0)


@app.get("/ensenar/audio/<int:id_grabacion>")
def audio_grabacion(id_grabacion):
    ruta = pronunciaciones.ruta_archivo(id_grabacion)
    if ruta is None:
        return Response(status=404)
    return send_file(ruta, mimetype="audio/wav", max_age=0)


if __name__ == "__main__":
    print(f"[YURA] Versión {VERSION}")
    start_robot()
    app.run(host="0.0.0.0", port=5000, debug=False)
