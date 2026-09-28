"""Grupo 7: limpieza de texto para voz y comportamiento de hablar() con subprocess SIMULADO.
Nunca se reproduce sonido ni se llama a Edge TTS (salvo la prueba 730, que solo valida argumentos
con el binario local y falla antes de usar la red)."""
from comun import *  # noqa
import os
import subprocess
import tempfile
import time
from unittest.mock import patch
tempfile.tempdir = SCRATCH
import main_robot
from main_robot import HardwareInterface

estados = []
hw = HardwareInterface(audio_manager=None, on_status=lambda fase, **d: estados.append((fase, d)))

TEXTOS = [
    ("markdown", "## Colores\n- **Puka**: rojo\n- *Q'illu*: amarillo\n1. [ver](http://x.y)"),
    ("html", "<p>Rimaykullayki</p><br>&nbsp;&amp;"),
    ("url", "Visita https://www.ejemplo.com/quechua?x=1&y=2 para más"),
    ("tabla", "| es | qu |\n|---|---|\n| casa | wasi |"),
    ("solo_signos", "¿¡?!...;;;"),
    ("espacios", "     "),
    ("guion_bajo", "p_unchay y NO_ENCONTRADO"),
    ("apostrofo", "Allin p'unchay, Q'ello"),
    ("pregunta", "¿Imaynalla kachkanki?"),
    ("abreviatura", "Sr. Pérez dice: En quechua se dice Tata."),
    ("traduccion", "En quechua se dice: Tata. Significa padre."),
    ("asteriscos_mat", "3 * 4 * 5 = 60"),
]
for i, (nom, t) in enumerate(TEXTOS):
    caso(f"YURA-EXT-7{i + 1:02d}", "tts", "limpiar/formatear/visible", nom,
         "sin Markdown/HTML/URL; texto pronunciable",
         lambda t=t: (hw._limpiar_texto_tts(t), hw._formatear_texto_voz(hw._limpiar_texto_tts(t)),
                      hw._texto_visible(t)),
         lambda x, nom=nom: (("FALLA" if (nom in ("markdown", "html", "url", "tabla") and
                                          any(s in x[1] for s in ("<", "http", "](", "|", "&nbsp")))
                              or (nom in ("solo_signos", "espacios") and x[1].strip(" .;") == "")
                              or (nom == "traduccion" and x[2] != "Tata")
                              else "OK"),
                             f"limpio={x[0][:70]!r} voz={x[1][:70]!r} visible={x[2][:50]!r}"))

for i, (nom, t) in enumerate([("10000_palabras", "palabra " * 1250), ("10000_asteriscos", "*" * 10000),
                              ("5000_negritas", "**a" * 5000), ("10000_sin_punto", "a" * 10000)]):
    t0 = time.perf_counter()
    l = hw._limpiar_texto_tts(t)
    v = hw._formatear_texto_voz(l)
    vis = hw._texto_visible(t)
    dt = time.perf_counter() - t0
    caso(f"YURA-EXT-7{20 + i}", "tts", "texto extremo (rendimiento y longitud)", nom,
         "< 100 ms; limitar longitud visible/hablada", lambda: (dt, len(v), len(vis)),
         lambda x: ("FALLA" if x[0] > 0.1 else ("OBSERVACION" if x[1] > 1000 else "OK"),
                    f"{x[0]*1000:.1f} ms; voz={x[1]} car; pantalla={x[2]} car"))


# ---------------------------------------------------------------- hablar() con subprocess simulado
class Sim:
    def __init__(self, edge_rc=0, edge_escribe=True, player_rc=0, sleep_edge=0.0):
        self.calls = []
        self.edge_rc, self.edge_escribe, self.player_rc, self.sleep_edge = edge_rc, edge_escribe, player_rc, sleep_edge

    def run(self, cmd, *a, **kw):
        self.calls.append((cmd, kw))
        nombre = os.path.basename(cmd[0]) if isinstance(cmd, list) else str(cmd)
        if nombre == "edge-tts":
            time.sleep(self.sleep_edge)
            if self.edge_escribe and self.edge_rc == 0:
                with open(cmd[-1], "wb") as fh:
                    fh.write(b"ID3fake")
            return subprocess.CompletedProcess(cmd, self.edge_rc)
        if nombre == "ffmpeg":
            open(cmd[-1], "wb").write(b"RIFF")
            return subprocess.CompletedProcess(cmd, 0)
        if nombre == "wpctl":
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        return subprocess.CompletedProcess(cmd, self.player_rc)


def which_fn(disponibles):
    return lambda n: f"/usr/bin/{n}" if n in disponibles else None


def hablar_con(sim, disponibles, texto="Rimaykullayki"):
    estados.clear()
    with patch.object(main_robot.subprocess, "run", sim.run), \
         patch.object(main_robot.shutil, "which", which_fn(disponibles)):
        t0 = time.perf_counter()
        hw.hablar(texto)
        dt = time.perf_counter() - t0
    usados = [os.path.basename(c[0][0]) for c in sim.calls]
    sin_timeout = [os.path.basename(c[0][0]) for c in sim.calls if "timeout" not in c[1]]
    return usados, sin_timeout, dt, [e[0] for e in estados]


ESC = [
    ("Edge TTS falla (sin internet), sin motor local", Sim(edge_rc=1), set(),
     "reintenta 1 vez, avisa y NO se bloquea"),
    ("Edge TTS falla, hay spd-say", Sim(edge_rc=1), {"spd-say"}, "usa spd-say"),
    ("Sin ffmpeg ni reproductores", Sim(), {"pw-play"}, "avisa que no hay audio"),
    ("Todos los reproductores fallan", Sim(player_rc=1), {"ffmpeg", "pw-play", "ffplay", "mpg123", "wpctl"},
     "prueba todos y cae a motor local"),
    ("Camino normal", Sim(), {"ffmpeg", "pw-play", "wpctl"}, "edge-tts -> ffmpeg -> pw-play"),
]
for i, (nom, sim, disp, esp) in enumerate(ESC):
    caso(f"YURA-EXT-7{30 + i}", "tts", f"hablar(): {nom}", "Rimaykullayki", esp,
         lambda sim=sim, disp=disp: hablar_con(sim, disp),
         lambda x: ("OK", f"procesos={x[0]} estados={x[3]} {x[2]*1000:.0f} ms"))

sim = Sim(edge_rc=0, sleep_edge=1.5, edge_escribe=False)
caso("YURA-EXT-740", "tts", "hablar(): Edge TTS se cuelga 1,5 s por intento (red lenta)", "Rimaykullayki",
     "timeout en subprocess.run", lambda: hablar_con(sim, set()),
     lambda x: ("FALLA" if x[2] >= 3 and x[1] else "OK",
                f"bloqueado {x[2]:.1f} s; llamadas SIN timeout={x[1]} (un cuelgue real bloquea al robot indefinidamente)"))

sim = Sim()
caso("YURA-EXT-741", "tts", "hablar('     ') solo espacios", "'     '", "no llamar a Edge TTS",
     lambda: hablar_con(sim, {"ffmpeg", "pw-play"}, "     "),
     lambda x: ("FALLA" if "edge-tts" in x[0] else "OK", f"procesos={x[0]} (sintetiza '.')"))
sim = Sim()
caso("YURA-EXT-742", "tts", "hablar('¿¡?!') solo signos", "'¿¡?!'", "no llamar a Edge TTS",
     lambda: hablar_con(sim, {"ffmpeg", "pw-play"}, "¿¡?!"),
     lambda x: ("FALLA" if "edge-tts" in x[0] else "OK", f"procesos={x[0]} texto enviado={sim.calls[0][0][5]!r}" if sim.calls else f"{x}"))
sim = Sim()
caso("YURA-EXT-743", "tts", "hablar(None)", "None", "no hacer nada", lambda: hablar_con(sim, set(), None),
     lambda x: ("OK" if not x[0] else "FALLA", f"procesos={x[0]}"))

# Prueba con el binario real edge-tts: texto que empieza con '--' (falla en argparse, antes de usar la red)
edge = os.path.join(PROYECTO, ".venv", "bin", "edge-tts")
salida = os.path.join(SCRATCH, "g07_argparse.mp3")
res = subprocess.run([edge, "--voice", "es-MX-DaliaNeural", "--rate=+5%", "--text", "--hola.", "--write-media", salida],
                     capture_output=True, text=True, timeout=30)
caso("YURA-EXT-750", "tts", "Edge TTS real con texto que empieza por '--'", "'--hola.'",
     "sintetizar el texto (usar --text=<texto>)", lambda: (res.returncode, res.stderr.strip().splitlines()[-1:]),
     lambda x: ("FALLA" if x[0] != 0 else "OK", f"returncode={x[0]} stderr={x[1]}"))

resumen()
volcar_matriz("../05_g07_matriz.md")
