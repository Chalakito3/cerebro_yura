"""Pruebas de los arreglos de la auditoría del 27/09/2026 (informe 001)."""

import sqlite3
import subprocess
import threading
from pathlib import Path
from unittest.mock import Mock

import pytest

import conversacion
import texto
import traductor
from juego import Juego
from main_robot import ApagadoConfirmado, BrainYura, HardwareInterface, RobotStates


@pytest.fixture(autouse=True)
def _sin_practica_pendiente():
    # La sesión de práctica es global en conversacion: cada prueba empieza limpia.
    conversacion.cancelar_sesion_educativa()
    yield
    conversacion.cancelar_sesion_educativa()


def _robot(respuestas_voz):
    robot = object.__new__(BrainYura)
    robot.state = RobotStates.MENU
    robot.running = True
    robot.saludo_inicial_done = True
    robot.hw = Mock()
    robot.escuchar_voz = Mock(side_effect=list(respuestas_voz))
    robot.groq_client = None
    robot.historial_conversacion = []
    robot.juego = Mock()
    robot.web_status = {"phase": "ESPERANDO", "content": "", "translation": "", "result": None}
    robot.web_status_lock = threading.Lock()
    robot.db_conn = None
    return robot


def _dichos(robot):
    return [llamada.args[0] for llamada in robot.hw.hablar.call_args_list]


# --- Arreglo 1: apagar -------------------------------------------------

@pytest.mark.parametrize("frase", [
    "no quiero apagar",
    "¿cómo se dice apagar la luz?",
    "apagar la luz es importante",
])
def test_frases_con_apagar_no_apagan_el_robot(frase):
    robot = _robot([frase])
    robot.ejecutar_menu()
    assert robot.running is True
    assert robot.state != RobotStates.SALIR


def test_apagar_pide_confirmacion_y_se_apaga_con_si(monkeypatch):
    monkeypatch.delenv("YURA_APAGAR_EQUIPO", raising=False)
    robot = _robot(["Yura apágate", "sí"])
    with pytest.raises(ApagadoConfirmado):
        robot.ejecutar_menu()
    assert "¿Seguro que quieres que me apague?" in _dichos(robot)[0]
    assert robot.running is False
    assert robot.state == RobotStates.SALIR
    # Por defecto solo se cierra la aplicación, no la computadora.
    assert robot.apagar_equipo is False


@pytest.mark.parametrize("modo, metodo", [
    (RobotStates.CONVERSAR, "ejecutar_conversar"),
    (RobotStates.SILENCIO, "ejecutar_silencio"),
])
def test_apagate_funciona_fuera_del_menu(modo, metodo):
    robot = _robot(["¿puedes apagarte?", "sí"])
    robot.state = modo
    with pytest.raises(ApagadoConfirmado):
        getattr(robot, metodo)()
    assert robot.running is False


def test_apagate_en_el_traductor_y_en_el_juego():
    robot = _robot(["apágate", "sí"])
    with pytest.raises(ApagadoConfirmado):
        traductor.ejecutar_traducir(
            robot._escuchar_con_ordenes, robot.hw.hablar,
            conversacion._obtener_conexion_vocabulario(), None, lambda: robot.running,
        )
    robot = _robot(["apaga el robot", "sí"])
    juego = Juego(["perro"], lambda p: "Allqo", robot._escuchar_con_ordenes,
                  robot.hw.hablar, Mock(), texto.normalizar)
    with pytest.raises(ApagadoConfirmado):
        juego.ejecutar_turno()


@pytest.mark.parametrize("frase, esperado", [
    ("apágate", True), ("¿puedes apagarte?", True), ("apaga el robot", True),
    ("quiero que te apagues", True), ("no te apagues", False),
    ("¿cómo se dice apagar?", False), ("apaga la luz", False),
])
def test_reconocimiento_de_la_orden_de_apagar(frase, esperado):
    assert texto.es_orden_apagar(texto.normalizar(frase)) is esperado


def test_confirmar_apagado_termina_el_ciclo_sin_errores(monkeypatch):
    robot = _robot(["apágate", "sí"])
    robot.loop_principal()
    assert robot.running is False
    assert robot.fallo_fatal is False


def test_apagar_equipo_llama_a_systemctl_solo_si_se_confirmo(monkeypatch):
    llamadas = []
    monkeypatch.setattr("main_robot.subprocess.run", lambda comando, **kw: llamadas.append(comando))
    robot = _robot([])
    robot.apagar_equipo_si_corresponde()
    assert llamadas == []
    robot.apagar_equipo = True
    robot.apagar_equipo_si_corresponde()
    assert llamadas == [["systemctl", "poweroff"]]


def test_se_puede_activar_el_apagado_del_equipo(monkeypatch):
    monkeypatch.setenv("YURA_APAGAR_EQUIPO", "1")
    robot = _robot(["apágate", "sí"])
    with pytest.raises(ApagadoConfirmado):
        robot.ejecutar_menu()
    assert robot.apagar_equipo is True


def test_apagar_sin_confirmar_sigue_encendida():
    robot = _robot(["apagar", "no"])
    robot.ejecutar_menu()
    assert robot.running is True
    assert robot.state == RobotStates.MENU


# --- Arreglo 2 y 7: pantalla -------------------------------------------

def test_texto_visible_del_traductor_no_empieza_con_dos_puntos():
    hw = HardwareInterface.__new__(HardwareInterface)
    assert hw._texto_visible("En quechua se dice: Tata.") == "Tata"


def test_contenido_fijado_no_se_reemplaza_mientras_yura_habla():
    robot = _robot([])
    robot._set_web_status("PENSANDO", content="Tata", translation="Papá", fijar=True)
    robot._set_web_status("HABLANDO", content="En quechua se dice", translation="x")
    estado = robot.get_web_status()
    assert (estado["content"], estado["translation"]) == ("Tata", "Papá")
    assert "fijo" not in estado

    robot._set_web_status("ESCUCHANDO")
    robot._set_web_status("HABLANDO", content="Otra frase")
    assert robot.get_web_status()["content"] == "Otra frase"


def test_la_pantalla_ya_no_recorta_el_texto_con_expresiones_regulares():
    js = (Path(__file__).resolve().parents[1] / "web" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    assert "extractQuechuaPhrase" not in js
    assert "[A-Za-z0-9'\\s]+" not in js


def test_tarjetas_muestran_el_significado_en_espanol():
    from web.app import CARD_EXAMPLES
    for tarjeta in CARD_EXAMPLES:
        assert tarjeta["meaning"] != tarjeta["title"]


# --- Arreglo 3: ñ y apóstrofo -----------------------------------------

def test_normalizacion_conserva_enie_y_apostrofo():
    assert texto.normalizar("Ñuqaqa Yura kani") == "ñuqaqa yura kani"
    assert texto.normalizar("Allin p’unchay!") == "allin p'unchay"
    assert texto.normalizar("¿Cómo se dice NIÑO?") == "como se dice niño"


def test_el_traductor_encuentra_palabras_con_enie():
    conexion = conversacion._obtener_conexion_vocabulario()
    termino = traductor.extraer_termino(texto.normalizar("¿Cómo se dice niño?"))
    assert termino == "niño"
    assert traductor.buscar_vocabulario(termino, "espanol", conexion)["encontrado"]


def test_que_significa_funciona_con_palabras_con_apostrofo():
    respuesta = conversacion.procesar_entrada("¿Qué significa Sach'a?", None)["respuesta"]
    assert "Sach'a significa" in respuesta


# --- Arreglo 4: órdenes contra palabras --------------------------------

@pytest.mark.parametrize("frase", ["no quiero jugar", "conjugar verbos"])
def test_frases_que_no_son_la_orden_de_jugar(frase):
    robot = _robot([frase])
    robot.ejecutar_menu()
    assert robot.state != RobotStates.JUEGO


def test_quiero_jugar_si_abre_el_juego():
    robot = _robot(["quiero jugar"])
    robot.ejecutar_menu()
    assert robot.state == RobotStates.JUEGO


def test_preguntar_por_adios_no_silencia_a_yura():
    robot = _robot(["¿cómo se dice adiós en quechua?"])
    robot.ejecutar_menu()
    assert robot.state != RobotStates.SILENCIO


def test_preguntar_por_adios_en_conversacion_no_vuelve_al_menu():
    resultado = conversacion.procesar_entrada("cómo se dice adiós", None)
    assert resultado["accion"] == "responder"


def test_guarda_silencio_no_despierta_a_yura():
    robot = _robot(["guarda silencio"])
    robot.state = RobotStates.SILENCIO
    robot.ejecutar_silencio()
    assert robot.state == RobotStates.SILENCIO


def test_busqueda_parcial_solo_por_palabras_completas():
    conexion = conversacion._obtener_conexion_vocabulario()
    resultados = traductor.buscar_vocabulario("no", "espanol", conexion)["resultados"]
    assert all("horno" not in r["espanol"].lower() for r in resultados)


# --- Arreglo 5: evaluación --------------------------------------------

@pytest.mark.parametrize("respuesta, correcta, esperado", [
    ("wawa", "Tawa", False),
    ("anti", "Inti", False),
    ("sara", "Sach'a", False),
    ("yana", "Llama", False),
    ("allqu", "Allqo", True),
    ("se dice allqo", "Allqo", True),
    ("sacha", "Sach'a", True),
    ("pilpintu", "Pillpintu", True),
])
def test_evaluacion_de_respuestas_quechua(respuesta, correcta, esperado):
    assert texto.respuesta_quechua_correcta(respuesta, correcta) is esperado


def _juego(respuestas, traduccion="Allqo"):
    dichos = []
    juego = Juego(
        ["perro"],
        lambda palabra: traduccion,
        Mock(side_effect=list(respuestas)),
        dichos.append,
        Mock(),
        texto.normalizar,
    )
    juego.reiniciar()
    return juego, dichos


def test_juego_no_felicita_con_cero_aciertos():
    juego, dichos = _juego(["gato"])
    juego.ejecutar_turno()
    assert juego.ejecutar_turno() == "menu"
    assert "Acertaste 0 de 1" in dichos[-1]
    assert "Felicidades" not in dichos[-1]


def test_juego_felicita_si_acierta_todo():
    juego, dichos = _juego(["allqo"])
    juego.ejecutar_turno()
    juego.ejecutar_turno()
    assert "Felicidades" in dichos[-1]


# --- Arreglo 6: bucles sin salida -------------------------------------

def test_juego_vuelve_al_menu_tras_tres_silencios():
    juego, _ = _juego(["", "", ""])
    resultados = [juego.ejecutar_turno() for _ in range(3)]
    assert resultados == ["continuar", "continuar", "menu"]


def test_traductor_vuelve_al_menu_tras_tres_silencios():
    dichos = []
    resultado = traductor.ejecutar_traducir(
        Mock(side_effect=["", "", ""]),
        dichos.append,
        conversacion._obtener_conexion_vocabulario(),
        None,
        lambda: True,
    )
    assert resultado == "menu"
    assert len(dichos) == 3


def test_traductor_traduce_adios_y_sale_con_volver_al_menu():
    dichos = []
    resultado = traductor.ejecutar_traducir(
        Mock(side_effect=["adiós", "volver al menú"]),
        dichos.append,
        conversacion._obtener_conexion_vocabulario(),
        None,
        lambda: True,
    )
    assert resultado == "menu"
    assert "Regresando al menú" not in dichos[0]
    assert dichos[-1] == "Regresando al menú principal."


# --- Arreglo 8: tiempos máximos ---------------------------------------

def test_hablar_no_se_bloquea_si_la_voz_no_responde(monkeypatch):
    hw = HardwareInterface.__new__(HardwareInterface)
    hw.audio_temp = "/tmp/yura-prueba-inexistente.mp3"
    hw.voz_mujer = "es-MX-DaliaNeural"
    hw.audio_manager = None
    hw.on_status = None
    tiempos = []

    def ejecutar(comando, **kwargs):
        tiempos.append(kwargs.get("timeout"))
        raise subprocess.TimeoutExpired(comando, kwargs.get("timeout"))

    monkeypatch.setattr(subprocess, "run", ejecutar)
    monkeypatch.setattr("main_robot.shutil.which", lambda nombre: None)
    hw.hablar("Rimaykullayki")
    assert tiempos and all(tiempo for tiempo in tiempos)


# --- Arreglo 9: palabra suelta ----------------------------------------

def test_palabra_suelta_se_busca_en_el_diccionario():
    resultado = conversacion.procesar_entrada("perro", None)
    assert "Allqu" in resultado["respuesta"]
    assert "no vendo autos" not in resultado["respuesta"]
    assert resultado["pantalla"]["content"] == "Allqu"


# --- Arreglo 10: una sola llamada al ciclo principal ------------------

def test_main_robot_llama_una_sola_vez_al_ciclo_principal():
    fuente = (Path(__file__).resolve().parents[1] / "main_robot.py").read_text(encoding="utf-8")
    arranque = fuente.split('if __name__ == "__main__":', 1)[1]
    assert arranque.count("loop_principal()") == 1


# --- Arreglo 11: errores en el ciclo principal ------------------------

def test_un_error_en_un_modo_no_mata_al_robot(monkeypatch):
    monkeypatch.setattr("main_robot.time.sleep", lambda segundos: None)
    robot = _robot([])
    llamadas = []

    def menu():
        llamadas.append(1)
        if len(llamadas) == 1:
            raise sqlite3.OperationalError("database is locked")
        robot.running = False

    robot.ejecutar_menu = menu
    robot.loop_principal()
    assert len(llamadas) == 2
    assert robot.fallo_fatal is False


def test_errores_repetidos_detienen_al_robot_con_fallo(monkeypatch):
    monkeypatch.setattr("main_robot.time.sleep", lambda segundos: None)
    robot = _robot([])
    robot.ejecutar_menu = Mock(side_effect=sqlite3.OperationalError("database is locked"))
    robot.loop_principal()
    assert robot.ejecutar_menu.call_count == 5
    assert robot.fallo_fatal is True
    assert robot.running is False


# --- Regresión detectada en la prueba en vivo (27/09/2026) -------------

def test_la_practica_carga_una_palabra_del_diccionario():
    conversacion.cancelar_sesion_educativa()
    resultado = conversacion.procesar_entrada("enséñame quechua", None)
    assert "No pude cargar" not in resultado["respuesta"]
    assert resultado["pantalla"]["content"]
    conversacion.cancelar_sesion_educativa()


# --- Filtro de temas (prueba en vivo del 27/09/2026) ------------------

def _groq_falso(mensajes_enviados, respuesta="Allin, yusulpayki. ¿Practicamos una palabra?"):
    from types import SimpleNamespace

    def create(**kwargs):
        mensajes_enviados.append(kwargs["messages"])
        return SimpleNamespace(choices=[SimpleNamespace(
            finish_reason="stop", message=SimpleNamespace(content=respuesta))])

    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


@pytest.mark.parametrize("frase", ["¿cómo estás, Yura?", "¿qué sabes hacer?", "cuéntame algo"])
def test_frases_comunes_llegan_a_groq_en_vez_de_rechazarse(frase):
    enviados = []
    resultado = conversacion.procesar_entrada(frase, _groq_falso(enviados))
    assert enviados, "la frase debía llegar a Groq"
    assert "Soy Yura, un robot educativo" not in resultado["respuesta"]


def test_pedir_otro_idioma_se_rechaza_aunque_haya_groq():
    enviados = []
    resultado = conversacion.procesar_entrada("habla en inglés conmigo", _groq_falso(enviados))
    assert not enviados
    assert "practicar quechua" in resultado["respuesta"]


# --- Confirmación de apagado (prueba en vivo del 27/09/2026) ----------

def test_apagati_de_whisper_se_reconoce_como_orden():
    assert texto.es_orden_apagar(texto.normalizar("Apágati."))


def test_si_no_entiende_la_confirmacion_pregunta_otra_vez():
    robot = _robot(["apágate", "subtitulos en la descripcion", "sí"])
    with pytest.raises(ApagadoConfirmado):
        robot.ejecutar_menu()
    assert "No te entendí. ¿Me apago? Di sí o no." in _dichos(robot)
    assert robot.running is False


def test_decir_no_a_la_confirmacion_no_vuelve_a_preguntar():
    robot = _robot(["apágate", "no"])
    robot.ejecutar_menu()
    assert "No te entendí. ¿Me apago? Di sí o no." not in _dichos(robot)
    assert robot.running is True


def test_frases_inventadas_por_whisper_se_descartan():
    assert texto.es_alucinacion_whisper(texto.normalizar("Subtítulos en la descripción"))
    assert not texto.es_alucinacion_whisper(texto.normalizar("sí"))


def _audio_manager():
    from audio_manager import AudioManager
    manager = AudioManager.__new__(AudioManager)
    manager.ruido_referencia = None
    return manager


def test_voz_durante_la_calibracion_no_sube_el_umbral():
    manager = _audio_manager()
    assert manager._ruido_para_umbral(0.0005) == (0.0005, False)
    nivel, hay_voz = manager._ruido_para_umbral(0.1114)
    assert hay_voz is True
    assert nivel < 0.001


def test_el_ruido_normal_sigue_actualizando_la_referencia():
    manager = _audio_manager()
    manager._ruido_para_umbral(0.0005)
    nivel, hay_voz = manager._ruido_para_umbral(0.0008)
    assert hay_voz is False
    assert nivel == 0.0008


def test_respuesta_rapida_durante_la_calibracion_se_graba(monkeypatch):
    import numpy as np
    import audio_manager as modulo

    manager = _audio_manager()
    manager.ruido_referencia = 0.0005
    manager.sample_rate = 16000
    manager.input_device = 0
    manager.input_candidates = [{"index": 0}]
    manager.input_sample_rate = 16000
    manager.input_channels = 1
    monkeypatch.setattr(manager, "detectar_dispositivos", lambda: None)
    monkeypatch.setattr(manager, "seleccionar_entrada", lambda: None)

    # "sí" (0,1 de volumen) empieza justo al calibrar y dura 0,5 s; luego silencio.
    bloques = iter([0.0005] * 2 + [0.1] * 6 + [0.0005] * 40)

    class Microfono:
        def __init__(self, **kwargs):
            self.frames = kwargs["blocksize"]

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, frames):
            volumen = next(bloques)
            senal = np.full((frames, 1), volumen, dtype=np.float32)
            senal[::2] *= -1
            return senal, False

    monkeypatch.setattr(modulo.sd, "InputStream", Microfono)
    audio = manager.grabar_hasta_silencio(espera_maxima=2, duracion_maxima=5, silencio_final=1.0)

    assert audio is not None
    muestras = np.frombuffer(audio, dtype=np.int16)
    assert np.abs(muestras).max() > 3000


# --- Privacidad en modo silencio ---------------------------------------

def test_en_silencio_la_voz_no_se_envia_a_la_nube():
    robot = _robot([])
    robot.escuchar_voz = Mock(return_value="")
    robot.state = RobotStates.SILENCIO
    robot.ejecutar_silencio()
    assert robot.escuchar_voz.call_args.kwargs["solo_local"] is True


def test_fuera_del_silencio_se_puede_usar_la_nube():
    robot = _robot([])
    robot.escuchar_voz = Mock(return_value="")
    robot.state = RobotStates.CONVERSAR
    robot.ejecutar_conversar()
    assert robot.escuchar_voz.call_args.kwargs["solo_local"] is False


def test_escuchar_voz_solo_local_no_llama_a_gemini(monkeypatch):
    import main_robot
    robot = _robot([])
    del robot.escuchar_voz  # usar la función real, no la simulada de _robot
    robot.audio_manager = Mock(input_device=0)
    robot.audio_manager.grabar_hasta_silencio.return_value = b"\x00\x01" * 16000
    robot.dispositivo_index = 0
    robot.gemini_transcriber = Mock()
    robot.whisper_model = Mock()
    robot.whisper_model.transcribe.return_value = {"text": "despierta"}
    monkeypatch.setattr(main_robot.time, "sleep", lambda s: None)
    assert robot.escuchar_voz(solo_local=True) == "despierta"
    robot.gemini_transcriber.transcribir.assert_not_called()


# --- Registro sin datos de los estudiantes ----------------------------

def test_el_registro_no_guarda_lo_que_dice_el_estudiante(monkeypatch, capsys):
    import depuracion
    monkeypatch.delenv("YURA_DEBUG", raising=False)
    depuracion.voz("[TRANSCRIPCIÓN FINAL - Whisper]", "me llamo Juan Pérez")
    depuracion.depurar("[DEBUG AUDIO] bloque=12")
    salida = capsys.readouterr().out
    assert "Juan" not in salida
    assert "(4 palabras)" in salida
    assert "DEBUG" not in salida


def test_con_yura_debug_se_ve_todo_para_diagnosticar(monkeypatch, capsys):
    import depuracion
    monkeypatch.setenv("YURA_DEBUG", "1")
    depuracion.voz("[TRANSCRIPCIÓN FINAL - Whisper]", "apágate")
    depuracion.depurar("[DEBUG AUDIO] bloque=12")
    salida = capsys.readouterr().out
    assert "apágate" in salida and "bloque=12" in salida


def test_archivo_de_claves_con_bom_de_windows(tmp_path, monkeypatch):
    import main_robot
    (tmp_path / ".env.local").write_bytes("﻿GROQ_API_KEY=clave-de-prueba\n".encode("utf-8"))
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setattr(main_robot.os.path, "abspath", lambda ruta: str(tmp_path / "main_robot.py"))
    main_robot.cargar_archivo_claves()
    assert main_robot.os.environ.get("GROQ_API_KEY") == "clave-de-prueba"
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
