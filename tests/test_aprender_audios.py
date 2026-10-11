"""Pruebas de lo que Yura aprende de los audios de la docente."""

import os
import sqlite3
import sys

import numpy as np
import pytest

import pronunciaciones
import texto
import traductor

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "basedatos"))
import aprender_de_audios  # noqa: E402

VOZ = (np.sin(np.linspace(0, 400, 8000)) * 3000).astype(np.int16).tobytes()


@pytest.fixture
def diccionario():
    with sqlite3.connect(pronunciaciones.RUTA_DB) as conexion:
        conexion.execute(
            "CREATE TABLE nivel1_colores (id INTEGER PRIMARY KEY, palabra_frase TEXT, "
            "pronunciacion TEXT, traduccion TEXT, significado TEXT)"
        )
        conexion.executemany(
            "INSERT INTO nivel1_colores VALUES (?, ?, NULL, ?, NULL)",
            [(1, "Q'umir", "Verde"), (2, "Tawa", "Cuatro"), (3, "Wawa", "Bebé"),
             (4, "Juk", "Uno"), (5, "Phuyu", "Nube"), (6, "Kay", "Este"), (7, "Chay", "Ese")],
        )
    conexion = sqlite3.connect(pronunciaciones.RUTA_DB)
    conexion.row_factory = sqlite3.Row
    yield conexion
    conexion.close()


def _grabar(id_palabra, escuchado):
    pronunciaciones.guardar_wav(pronunciaciones.ruta_pendiente(), VOZ)
    return pronunciaciones.guardar("nivel1_colores", id_palabra, escuchado)


def test_chay_y_kay_ya_no_son_iguales():
    assert not texto.respuesta_quechua_correcta("chay", "Kay")
    assert not texto.respuesta_quechua_correcta("kay", "Chay")
    assert texto.respuesta_quechua_correcta("canchis", "Qanchis")


@pytest.mark.parametrize("escuchado, palabra", [
    ("oh", "Juk"),            # muy corta
    ("ullu", "Phuyu"),        # palabra vulgar (Laime 2007)
    ("ordenes", "Juk"),       # el reconocedor copió sus instrucciones
    ("wawa", "Tawa"),         # es otra palabra del diccionario
])
def test_no_se_aprenden_transcripciones_peligrosas(diccionario, escuchado, palabra):
    assert not pronunciaciones.variante_segura(escuchado, palabra)


def test_se_aprenden_transcripciones_parecidas(diccionario):
    assert pronunciaciones.variante_segura("kumir", "Q'umir")
    assert pronunciaciones.variante_segura("pukuyu", "Phuyu")


def test_ullu_nunca_da_un_acierto_aunque_este_guardado(diccionario):
    _grabar(5, "ullu")
    assert pronunciaciones.variantes("Phuyu") == []
    assert not texto.respuesta_quechua_correcta("ullu", "Phuyu", pronunciaciones.variantes("Phuyu"))


def test_consulta_encuentra_la_palabra_sin_apostrofo(diccionario):
    for escrito in ("qumir", "kumir", "q'umir"):
        resultado = traductor.buscar_vocabulario(escrito, "quechua", diccionario)
        assert [r["quechua"] for r in resultado["resultados"]] == ["Q'umir"], escrito


def test_consulta_usa_lo_aprendido_de_los_audios(diccionario):
    assert not traductor.buscar_vocabulario("kumiri", "quechua", diccionario)["encontrado"]
    id_grabacion = _grabar(1, "q'umir")
    pronunciaciones.guardar_aprendida(id_grabacion, "Q'umir", "sin_pistas", "kumiri")
    resultado = traductor.buscar_vocabulario("kumiri", "quechua", diccionario)
    assert [r["quechua"] for r in resultado["resultados"]] == ["Q'umir"]
    assert "kumiri" in pronunciaciones.variantes("Q'umir")


class _ModeloFalso:
    def __init__(self):
        self.llamadas = 0

    def transcribe(self, ruta, initial_prompt=None, **_):
        self.llamadas += 1
        return {"text": "Kumir." if initial_prompt is None else "Q'umir."}


def test_aprender_escucha_cada_audio_una_vez_por_situacion(diccionario):
    id_grabacion = _grabar(1, "q'umir")
    modelo = _ModeloFalso()
    resumen = aprender_de_audios.aprender(modelo, informar=lambda _: None)
    assert modelo.llamadas == 3
    assert resumen["sin_pistas"] == [1, 1]
    assert pronunciaciones.contextos_aprendidos(id_grabacion) == {"menu", "juego", "sin_pistas"}
    # Repetirlo no vuelve a escuchar lo que ya aprendió.
    aprender_de_audios.aprender(modelo, informar=lambda _: None)
    assert modelo.llamadas == 3
    # Al borrar la grabación se borra también lo aprendido.
    pronunciaciones.borrar(id_grabacion)
    assert pronunciaciones.contextos_aprendidos(id_grabacion) == set()


@pytest.fixture
def diccionario_amplio():
    with sqlite3.connect(pronunciaciones.RUTA_DB) as conexion:
        conexion.execute(
            "CREATE TABLE nivel1_varios (id INTEGER PRIMARY KEY, palabra_frase TEXT, "
            "pronunciacion TEXT, traduccion TEXT, significado TEXT)"
        )
        conexion.executemany(
            "INSERT INTO nivel1_varios VALUES (?, ?, NULL, ?, NULL)",
            [(1, "Ch'umpi", "Café"), (2, "Ch'uspi", "Mosca"), (3, "K'acha", "Lindo"), (4, "P'acha", "Ropa"),
             (5, "Aqha", "Chicha"), (6, "Atuq", "Zorro"), (7, "Jatun", "Grande"), (8, "Tullu", "Flaco"),
             (9, "Imaynalla kachkanki", "¿Cómo estás?"), (10, "Tawa", "Cuatro"), (11, "Killa", "Luna")],
        )


@pytest.mark.parametrize("dicho, palabra", [
    ("umpi", "Ch'umpi"),                 # se perdió el sonido fuerte del inicio
    ("atu", "Atuq"),                     # se perdió la q final
    ("hatung", "Jatun"),
    ("tolyu", "Tullu"),                  # ll escrita "ly"
    ("y mayna", "Imayna"),                # i inicial escrita "y"
    ("taua", "Tawa"),
    ("quilla", "Killa"),
])
def test_acepta_como_escribe_el_reconocedor(diccionario_amplio, dicho, palabra):
    assert pronunciaciones.respuesta_aceptada(dicho, palabra)


@pytest.mark.parametrize("dicho, palabra", [
    ("k'acha", "P'acha"),     # es otra palabra del diccionario
    ("ch'umpi", "Ch'uspi"),
    ("aca", "K'acha"),        # sin el inicio se confunde con aqha
    ("oh", "Atuq"),
    ("perro", "Tullu"),
])
def test_no_acepta_otra_palabra_por_parecido(diccionario_amplio, dicho, palabra):
    assert not pronunciaciones.respuesta_aceptada(dicho, palabra)
