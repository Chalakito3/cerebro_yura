"""Arnés común: importa el cerebro sin arrancarlo, BD en solo lectura, sin red."""
import io
import os
import sqlite3
import sys
import threading
import contextlib
from unittest.mock import Mock

sys.dont_write_bytecode = True
PROJ = "/home/yura/Proyecto Yura /cerebro_yura"
sys.path.insert(0, PROJ)

with contextlib.redirect_stdout(io.StringIO()):
    import main_robot  # noqa: E402
    import conversacion  # noqa: E402
    import traductor  # noqa: E402
    from juego import Juego  # noqa: E402

RO = sqlite3.connect(
    f"file:{PROJ}/diccionario.db?mode=ro", uri=True, check_same_thread=False
)
conversacion._conexion_vocabulario = RO  # evita que conversacion abra la BD en escritura

S = main_robot.RobotStates


class FinEntradas(Exception):
    pass


def norm_brain(texto):
    return main_robot.BrainYura._normalizar_texto(None, texto)


def make_brain(state, entradas, groq=None, db=RO, silencioso=True):
    b = object.__new__(main_robot.BrainYura)
    b.state = state
    b.running = True
    b.historial_conversacion = []
    b.web_status = {"phase": "ESPERANDO", "content": "", "translation": "",
                    "result": None, "updated_at": None}
    b.web_status_lock = threading.Lock()
    b.hw = Mock()
    b.db_conn = db
    b.groq_client = groq
    b.saludo_inicial_done = True
    cola = [norm_brain(e) for e in entradas]  # escuchar_voz real devuelve texto normalizado

    def escuchar():
        if not cola:
            raise FinEntradas()
        return cola.pop(0)

    b.escuchar_voz = Mock(side_effect=escuchar)
    b.juego = Juego(
        ["gato", "perro", "sol", "agua", "casa", "arbol"],
        lambda p: traductor.consultar_diccionario_local(p, db),
        b.escuchar_voz, b.hw.hablar, b._mover_actuador,
        b._normalizar_texto, b._set_game_event,
    )
    return b


def fake_groq(texto="RESPUESTA_GROQ_FALSA"):
    capt = []

    class _C:
        def create(self, **kw):
            capt.append(kw)
            from types import SimpleNamespace as NS
            return NS(choices=[NS(finish_reason="stop", message=NS(content=texto))])

    from types import SimpleNamespace as NS
    return NS(chat=NS(completions=_C())), capt


def paso(b):
    """Ejecuta un ciclo del loop principal para el estado actual."""
    st = b.state
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            if st == S.MENU:
                b.ejecutar_menu()
            elif st == S.CONVERSAR:
                b.ejecutar_conversar()
            elif st == S.JUEGO:
                b.ejecutar_juego()
            elif st == S.TRADUCIR:
                b.ejecutar_traducir()
            elif st == S.SILENCIO:
                b.ejecutar_silencio()
        except FinEntradas:
            return "sin_mas_entradas"
    return "ok"
