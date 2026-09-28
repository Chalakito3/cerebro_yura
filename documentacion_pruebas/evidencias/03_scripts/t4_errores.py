import io
import os
import sqlite3
import sys
import threading
import contextlib
import tempfile
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch

from harness import make_brain, fake_groq, paso, S, conversacion, traductor, RO, main_robot, PROJ

print("## A) Llamadas subprocess en HardwareInterface.hablar: ¿llevan timeout?")
hw = main_robot.HardwareInterface.__new__(main_robot.HardwareInterface)
hw.audio_temp = os.path.join(tempfile.mkdtemp(), "x.mp3")
hw.voz_mujer = "v"; hw.audio_manager = None; hw.on_status = None
llamadas = []

def fake_run(cmd, **kw):
    llamadas.append((os.path.basename(str(cmd[0])), "timeout" in kw))
    if str(cmd[0]).endswith("edge-tts"):
        open(hw.audio_temp, "wb").write(b"x")
    if str(cmd[0]) == "ffmpeg":
        open(cmd[-1], "wb").write(b"x")
    return NS(returncode=0, stdout="")

with patch("main_robot.subprocess.run", fake_run), \
     patch("main_robot.shutil.which", lambda p: {"ffmpeg": "ffmpeg", "pw-play": "pw-play", "wpctl": "wpctl"}.get(p)), \
     contextlib.redirect_stdout(io.StringIO()):
    hw.hablar("Hola")
for prog, t in llamadas:
    print(f"  {prog}: timeout={'SÍ' if t else 'NO'}")

print("\n## B) Excepción no controlada dentro de un modo (BD bloqueada) -> ¿qué hace loop_principal?")
db_rota = Mock()
db_rota.cursor.side_effect = sqlite3.OperationalError("database is locked")
conversacion_backup = conversacion._conexion_vocabulario
conversacion._conexion_vocabulario = db_rota
b = make_brain(S.MENU, ["como se dice perro"], db=db_rota)
try:
    with contextlib.redirect_stdout(io.StringIO()):
        b.loop_principal()
    print("  loop_principal terminó sin excepción; running =", b.running)
except Exception as exc:
    print(f"  loop_principal PROPAGA {type(exc).__name__}: {exc}; running sigue = {b.running}; state = {b.state}")
conversacion._conexion_vocabulario = conversacion_backup

print("\n## C) web/app.py: hilo del robot muere por excepción -> ¿se cierra el proceso? ¿qué muestra /api/status?")
sys.path.insert(0, PROJ)
with contextlib.redirect_stdout(io.StringIO()):
    import web.app as webapp


class BrainFalso:
    def __init__(self):
        self.state = S.CONVERSAR
        self.running = True

    def get_web_status(self):
        return {"phase": "PENSANDO", "content": "x", "translation": "", "result": None, "updated_at": None}

    def loop_principal(self):
        raise sqlite3.OperationalError("database is locked")


salidas = []
webapp.robot = None
with patch.object(webapp, "BrainYura", BrainFalso), patch.object(webapp.os, "_exit", lambda c: salidas.append(c)):
    err = io.StringIO()
    old_hook = threading.excepthook
    threading.excepthook = lambda args: err.write(f"{args.exc_type.__name__}: {args.exc_value}")
    r = webapp.start_robot()
    for t in threading.enumerate():
        if t.name == "yura-backend":
            t.join(2)
    threading.excepthook = old_hook
    cli = webapp.app.test_client()
    st = cli.get("/api/status").get_json()
print("  excepción en hilo:", err.getvalue())
print("  os._exit llamado:", bool(salidas))
print("  /api/status tras la muerte del hilo:", {k: st[k] for k in ("state", "running", "activity", "phase")})
webapp.robot = None

print("\n## D) Historial de conversación: ¿se borra al volver al menú (otro estudiante)?")
g, capt = fake_groq("Respuesta")
b = make_brain(S.CONVERSAR, ["hablemos en quechua de mi familia", "salir"], groq=g)
paso(b); paso(b)
print("  estado:", b.state, "| mensajes en historial:", len(b.historial_conversacion))
b.state = S.CONVERSAR
b.escuchar_voz.side_effect = None
b.escuchar_voz.return_value = "hablemos en quechua de colores"
paso(b)
print("  2ª sesión: mensajes enviados a Groq en la última llamada:",
      [m["role"] + ':' + m["content"][:40] for m in capt[-1]["messages"][1:]])

print("\n## E) Archivo temporal yura_temp.wav: ruta")
print("  ruta usada:", os.path.join(PROJ, "yura_temp.wav"), "| existe ahora:", os.path.exists(os.path.join(PROJ, "yura_temp.wav")))

print("\n## F) Conexiones SQLite abiertas por el cerebro")
import re
src = open(os.path.join(PROJ, "main_robot.py")).read() + open(os.path.join(PROJ, "conversacion.py")).read()
for m in re.finditer(r"sqlite3\.connect\(([^)]*)\)", src, re.S):
    print("  connect(", " ".join(m.group(1).split()), ")")
print("  conversacion._conexion_vocabulario nunca se cierra:", "_conexion_vocabulario.close" not in src)

print("\n## G) __main__ de main_robot llama loop_principal dos veces")
lines = open(os.path.join(PROJ, "main_robot.py")).read().splitlines()
print("  ", [ (i+1, l.strip()) for i, l in enumerate(lines) if "loop_principal()" in l])

print("\n## H) Juego: mensaje final con todas las respuestas incorrectas")
import random
random.seed(3)
b = make_brain(S.JUEGO, ["no se"] * 4)
b.juego.reiniciar()
for _ in range(5):
    paso(b)
print("  último mensaje:", b.hw.hablar.call_args_list[-1].args[0])
print("  ¿se guarda algún puntaje/resultado persistente?: atributos del juego =", sorted(vars(b.juego).keys()))
