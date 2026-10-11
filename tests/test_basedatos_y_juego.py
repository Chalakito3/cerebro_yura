"""Correcciones del vocabulario (documento 002), semilla versionable del
diccionario y juego con palabras del diccionario."""

import glob
import os
import shutil
import sqlite3
import sys
from unittest.mock import Mock

import pytest

import conversacion
import texto
import traductor
from juego import PALABRAS_DE_RESPALDO, Juego

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "basedatos"))
import correcciones_002  # noqa: E402
import crear_diccionario  # noqa: E402


def _conexion():
    return conversacion._obtener_conexion_vocabulario()


@pytest.mark.parametrize("espanol, quechua", [
    ("mesa", "Jamp'ara"), ("escuela", "Yachay wasi"), ("aula", "Yachaqana wasi"),
    ("mano", "Maki"), ("abeja", "Wara"), ("cinco", "Phichqa"), ("pez", "Chawlla"),
    ("pato", "Pilli"), ("buenos días", "Allin p'unchay"), ("niño", "Irqi"),
    ("agua", "Yaku"), ("nariz", "Sinqa"), ("chicha", "Aqha"), ("dieciocho", "Chunka pusaqniyuq"),
])
def test_vocabulario_corregido_segun_fuentes_bolivianas(espanol, quechua):
    assert traductor.consultar_diccionario_local(espanol, _conexion()) == quechua


def test_palabras_sin_fuente_se_dejaron_como_estaban():
    assert traductor.consultar_diccionario_local("iglesia", _conexion()) == "Iglesia"


def test_pan_y_arado_estan_en_su_categoria():
    conexion = _conexion()
    pan = traductor.buscar_vocabulario("pan", "espanol", conexion)["resultados"][0]
    arado = traductor.buscar_vocabulario("arado", "espanol", conexion)["resultados"][0]
    assert pan["categoria"] == "alimentos"
    assert arado["categoria"] == "herramientas"


def test_todas_las_tablas_tienen_significado():
    conexion = _conexion()
    for (tabla,) in conexion.execute("SELECT name FROM sqlite_master WHERE name LIKE 'nivel%'"):
        columnas = [fila[1] for fila in conexion.execute(f'PRAGMA table_info("{tabla}")')]
        assert "significado" in columnas, tabla


def test_las_correcciones_se_aplican_una_sola_vez(tmp_path):
    respaldos = sorted(glob.glob(os.path.join(RAIZ, "basedatos", "diccionario_antes_correcciones_002_*.db")))
    if not respaldos:
        pytest.skip("No está el respaldo previo a las correcciones")
    copia = tmp_path / "copia.db"
    shutil.copy(respaldos[0], copia)
    with sqlite3.connect(copia) as conexion:
        primera = correcciones_002.aplicar(conexion)
    with sqlite3.connect(copia) as conexion:
        segunda = correcciones_002.aplicar(conexion)
    assert len(primera) >= 85
    assert segunda == []


def test_la_semilla_reconstruye_el_diccionario_identico(tmp_path):
    destino = tmp_path / "reconstruido.db"
    crear_diccionario.crear(str(destino))
    # Las grabaciones de la docente (modo docente) no forman parte de la semilla.
    contenido = lambda ruta: [
        linea for linea in sqlite3.connect(f"file:{ruta}?mode=ro", uri=True).iterdump()
        if "pronunciaciones_" not in linea
    ]
    assert contenido(destino) == contenido(crear_diccionario.RUTA_DB)


def test_palabras_del_juego_son_basicas_verificadas_y_sin_ambiguedad():
    conexion = _conexion()
    palabras = traductor.palabras_para_juego(conexion)
    assert len(palabras) >= 50
    assert not {"iglesia", "cuchara", "rosado", "papa", "bebida tradicional"} & set(palabras)
    for palabra in palabras:
        resultados = traductor.buscar_vocabulario(palabra, "espanol", conexion)["resultados"]
        assert len(resultados) == 1, palabra
        assert texto.normalizar(resultados[0]["quechua"]) != texto.normalizar(palabra)


def test_el_juego_usa_el_diccionario_en_cada_partida():
    fuente = Mock(return_value=["mesa", "mano", "pez", "sol", "agua"])
    juego = Juego(fuente, Mock(), Mock(), Mock(), Mock(), texto.normalizar)
    juego.reiniciar()
    juego.reiniciar()
    assert fuente.call_count == 2
    assert set(juego.palabras_partida) <= {"mesa", "mano", "pez", "sol", "agua"}
    assert len(juego.palabras_partida) == 4


def test_el_juego_usa_palabras_de_respaldo_sin_diccionario():
    juego = Juego(lambda: [], Mock(), Mock(), Mock(), Mock(), texto.normalizar)
    juego.reiniciar()
    assert set(juego.palabras_partida) <= set(PALABRAS_DE_RESPALDO)


def test_dialogo_infantil_en_diccionario():
    conexion = _conexion()
    filas = conexion.execute("SELECT palabra_frase, traduccion FROM nivel1_dialogo_infantil").fetchall()
    assert len(filas) >= 15
    palabras = {f[0].lower() for f in filas}
    assert "allillanmi" in palabras
    assert "kusisqam kani" in palabras
    assert "imataq sutiyki" in palabras
    # Verificar que pronunciaciones_voz tiene las 113 preservadas
    total_voz = conexion.execute("SELECT count(*) FROM pronunciaciones_voz").fetchone()[0]
    assert total_voz >= 280

