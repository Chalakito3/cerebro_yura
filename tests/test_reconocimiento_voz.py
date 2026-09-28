"""Mejoras del reconocimiento de voz (27/09/2026): Whisper small local,
pistas de vocabulario y Gemini desactivado por defecto."""

from unittest.mock import Mock

import pytest

import conversacion
import texto
from gemini_transcriber import GeminiTranscriber
from juego import Juego


def test_instruccion_incluye_las_pistas_y_las_ordenes():
    instruccion = texto.instruccion_reconocedor(["Wasi", "Yaku", "Wasi"])
    assert "Palabras en quechua: Wasi, Yaku." in instruccion
    assert "apágate" in instruccion
    assert "allqu" in texto.instruccion_reconocedor()


@pytest.mark.parametrize("oido, correcta", [
    ("Base", "Wasi"), ("Jaku", "Yaku"), ("Algo", "Allqu"), ("Ayku", "Allqu"),
])
def test_errores_tipicos_del_reconocedor_se_aceptan(oido, correcta):
    assert texto.respuesta_quechua_correcta(oido, correcta)


@pytest.mark.parametrize("oido, correcta", [
    ("wawa", "Tawa"), ("anti", "Inti"), ("yana", "Llama"), ("sara", "Sach'a"),
])
def test_palabras_distintas_se_siguen_rechazando(oido, correcta):
    assert not texto.respuesta_quechua_correcta(oido, correcta)


def test_el_juego_da_pistas_con_la_respuesta_mezclada_entre_otras():
    traducciones = {"perro": "Allqu", "gato": "Misi", "sol": "Inti", "agua": "Yaku", "casa": "Wasi", "mesa": "Jamp'ara"}
    escuchar = Mock(return_value="allqu")
    juego = Juego(list(traducciones), traducciones.get, escuchar, Mock(), Mock(), texto.normalizar)
    juego.reiniciar()
    juego.palabras_partida = ["perro", "gato", "sol", "agua"]
    juego.ejecutar_turno()
    pistas = escuchar.call_args.kwargs["pistas"]
    assert "Allqu" in pistas
    assert len(pistas) >= 4


def test_la_practica_da_como_pista_la_palabra_a_repetir():
    conversacion.cancelar_sesion_educativa()
    assert conversacion.pistas_practica() is None
    conversacion.procesar_entrada("enséñame quechua", None)
    palabra = conversacion._sesion_educativa["registro"]["quechua"]
    pistas = conversacion.pistas_practica()
    assert palabra in pistas and len(pistas) >= 4
    conversacion.cancelar_sesion_educativa()


def test_gemini_desactivado_por_defecto(monkeypatch):
    monkeypatch.delenv("YURA_GEMINI_ENABLED", raising=False)
    assert GeminiTranscriber().disponible is False


def test_gemini_se_pausa_tras_un_fallo_de_red(tmp_path):
    class Modelos:
        llamadas = 0

        def generate_content(self, **kwargs):
            self.llamadas += 1
            raise TimeoutError("The read operation timed out")

    modelos = Modelos()
    gemini = GeminiTranscriber.__new__(GeminiTranscriber)
    gemini.model = "prueba"
    gemini.client = Mock(models=modelos)
    gemini.pausado_hasta = 0.0
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"x")
    assert gemini.transcribir(audio) is None
    assert gemini.transcribir(audio) is None
    assert modelos.llamadas == 1


def test_voz_boliviana_por_defecto(monkeypatch):
    from main_robot import HardwareInterface
    monkeypatch.delenv("YURA_VOZ", raising=False)
    assert HardwareInterface().voz_mujer == "es-BO-SofiaNeural"
    monkeypatch.setenv("YURA_VOZ", "es-BO-MarceloNeural")
    assert HardwareInterface().voz_mujer == "es-BO-MarceloNeural"
