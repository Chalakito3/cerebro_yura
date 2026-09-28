"""Pruebas del modo docente: la docente enseña pronunciaciones a Yura."""

import os
import queue
import sqlite3
import threading
from unittest.mock import Mock

import numpy as np
import pytest

import conversacion
import pronunciaciones
import texto
from juego import Juego
from main_robot import BrainYura, ModoDocentePedido, RobotStates

OTRO_EQUIPO = {"REMOTE_ADDR": "192.168.1.50"}
VOZ = (np.sin(np.linspace(0, 400, 8000)) * 3000).astype(np.int16).tobytes()


@pytest.fixture
def diccionario():
    """Diccionario pequeño en el archivo temporal que usa pronunciaciones."""
    with sqlite3.connect(pronunciaciones.RUTA_DB) as conexion:
        conexion.execute(
            "CREATE TABLE nivel1_numeros (id INTEGER PRIMARY KEY, palabra_frase TEXT, "
            "pronunciacion TEXT, traduccion TEXT, significado TEXT)"
        )
        conexion.executemany(
            "INSERT INTO nivel1_numeros VALUES (?, ?, NULL, ?, NULL)",
            [(1, "Tawa", "Cuatro"), (2, "Pichqa", "Cinco")],
        )
        conexion.execute(
            "CREATE TABLE nivel1_familia (id INTEGER PRIMARY KEY, palabra_frase TEXT, "
            "pronunciacion TEXT, traduccion TEXT, significado TEXT)"
        )
        conexion.execute("INSERT INTO nivel1_familia VALUES (1, 'Wawa', NULL, 'Bebé', NULL)")
    return pronunciaciones.RUTA_DB


def _grabar_pendiente():
    pronunciaciones.guardar_wav(pronunciaciones.ruta_pendiente(), VOZ)


# --- Evaluador -----------------------------------------------------------

def test_el_evaluador_acepta_lo_que_aprendio_de_la_docente():
    assert not texto.respuesta_quechua_correcta("pancho", "puka")
    assert texto.respuesta_quechua_correcta("pancho", "puka", ["Pancho"])
    assert texto.respuesta_quechua_correcta("se dice pancho", "puka", ["pancho"])
    # Sin tolerancia: una palabra parecida a la variante no se acepta.
    assert not texto.respuesta_quechua_correcta("panchito", "puka", ["pancho"])


# --- Base de datos -------------------------------------------------------

def test_guardar_una_pronunciacion_la_usa_para_calificar_y_escuchar(diccionario):
    _grabar_pendiente()
    id_grabacion = pronunciaciones.guardar("nivel1_numeros", 2, "pishka")

    assert pronunciaciones.variantes("Pichqa") == ["pishka"]
    ruta = pronunciaciones.audio_de("pichqa")
    assert ruta and os.path.exists(ruta)
    assert not os.path.exists(pronunciaciones.ruta_pendiente())
    conteo = {p["quechua"]: p["grabaciones"] for p in pronunciaciones.palabras_con_conteo()}
    assert conteo == {"Tawa": 0, "Pichqa": 1, "Wawa": 0}

    assert pronunciaciones.borrar(id_grabacion)
    assert pronunciaciones.variantes("Pichqa") == []
    assert not os.path.exists(ruta)


def test_una_transcripcion_que_es_otra_palabra_no_sirve_para_calificar(diccionario):
    # Si al decir "tawa" el reconocedor escribió "wawa", aceptar "wawa"
    # como respuesta de "cuatro" sería un error.
    _grabar_pendiente()
    pronunciaciones.guardar("nivel1_numeros", 1, "wawa")
    assert pronunciaciones.otra_palabra_igual("wawa", "Tawa") == "Wawa"
    assert pronunciaciones.variantes("Tawa") == []
    assert pronunciaciones.audio_de("Tawa") is not None


def test_no_se_guarda_sin_grabacion(diccionario):
    with pytest.raises(ValueError):
        pronunciaciones.guardar("nivel1_numeros", 1, "tawa")


def test_la_semilla_no_incluye_las_grabaciones(diccionario, tmp_path):
    from basedatos import crear_diccionario
    _grabar_pendiente()
    pronunciaciones.guardar("nivel1_numeros", 1, "tawa")
    semilla = tmp_path / "semilla.sql"
    crear_diccionario.exportar(diccionario, str(semilla))
    contenido = semilla.read_text(encoding="utf-8")
    assert "Pichqa" in contenido
    assert "pronunciaciones_docente" not in contenido


# --- Uso en el juego y la práctica --------------------------------------

def test_el_juego_hace_escuchar_la_voz_de_la_docente_al_equivocarse():
    reproducir = Mock()
    juego = Juego(
        ["cinco"], lambda palabra: "Pichqa", Mock(return_value="tawa"), Mock(),
        Mock(), texto.normalizar, reproducir_pronunciacion=reproducir,
    )
    juego.reiniciar()
    juego.ejecutar_turno()
    reproducir.assert_called_once_with("Pichqa")


def test_la_practica_pide_la_voz_de_la_docente_solo_si_hay_error():
    conversacion._sesion_educativa = {
        "registro": {"quechua": "Pichqa", "espanol": "Cinco", "significado": None},
        "estado": "esperando_repeticion",
        "id": "prueba",
    }
    try:
        mal = conversacion._procesar_sesion_educativa("tawa")
        assert mal["pronunciar"] == "Pichqa"
        bien = conversacion._procesar_sesion_educativa("pichqa")
        assert bien["pronunciar"] is None
    finally:
        conversacion.cancelar_sesion_educativa()


# --- Robot ---------------------------------------------------------------

def _robot():
    robot = object.__new__(BrainYura)
    robot.state = RobotStates.MENU
    robot.running = True
    robot.hw = Mock()
    robot.audio_manager = Mock()
    robot.audio_manager.cancelar = threading.Event()
    robot.pedido_docente = threading.Event()
    robot.ordenes_docente = queue.Queue()
    robot.ensenanza = {"estado": "inactivo"}
    robot.ultima_actividad_docente = 0.0
    robot.web_status = {"phase": "ESPERANDO", "content": "", "translation": "", "result": None}
    robot.web_status_lock = threading.Lock()
    return robot


def test_el_boton_corta_la_escucha_y_entra_al_modo_docente():
    robot = _robot()
    robot.activar_modo_docente()
    assert robot.audio_manager.cancelar.is_set()
    with pytest.raises(ModoDocentePedido):
        robot._revisar_pedido_docente()

    robot._entrar_modo_docente()
    assert robot.state == RobotStates.ENSENAR
    assert not robot.audio_manager.cancelar.is_set()

    robot.terminar_modo_docente()
    robot._ejecutar_estado_actual()
    assert robot.state == RobotStates.MENU


def test_grabar_para_la_docente_guarda_audio_y_lo_que_escucho(diccionario):
    robot = _robot()
    robot.state = RobotStates.ENSENAR

    def escuchar(solo_local, pistas, guardar_audio_en):
        assert solo_local is True and "Pichqa" in pistas
        pronunciaciones.guardar_wav(guardar_audio_en, VOZ)
        return "pishka"

    robot.escuchar_voz = escuchar
    palabra = pronunciaciones.palabra_del_diccionario("nivel1_numeros", 2)
    robot._grabar_para_docente(palabra)

    assert robot.ensenanza["estado"] == "grabado"
    assert robot.ensenanza["transcripcion"] == "pishka"
    assert os.path.exists(pronunciaciones.ruta_pendiente())


def test_sin_voz_no_queda_grabacion(diccionario):
    robot = _robot()
    robot.state = RobotStates.ENSENAR
    robot.escuchar_voz = lambda **_: ""
    robot._grabar_para_docente(pronunciaciones.palabra_del_diccionario("nivel1_numeros", 1))
    assert robot.ensenanza["estado"] == "sin_voz"


# --- Página web ----------------------------------------------------------

def _cliente():
    from web.app import app
    return app.test_client()


def test_pagina_docente_protegida_en_la_red(monkeypatch, diccionario):
    monkeypatch.delenv("YURA_RESULTADOS_CLAVE", raising=False)
    cliente = _cliente()
    assert cliente.get("/ensenar").status_code == 200
    assert cliente.get("/api/ensenar/palabras").status_code == 200
    for ruta in ("/ensenar", "/api/ensenar/palabras", "/ensenar/audio/1"):
        assert cliente.get(ruta, environ_base=OTRO_EQUIPO).status_code == 403


def test_otra_pagina_no_puede_borrar_grabaciones(diccionario):
    _grabar_pendiente()
    id_grabacion = pronunciaciones.guardar("nivel1_numeros", 1, "tawa")
    respuesta = _cliente().post(
        f"/api/ensenar/borrar/{id_grabacion}", headers={"Origin": "http://malicioso.example"}
    )
    assert respuesta.status_code == 403
    assert pronunciaciones.ruta_archivo(id_grabacion) is not None


def test_flujo_web_grabar_y_guardar(monkeypatch, diccionario):
    import web.app as web_app
    robot = _robot()
    robot.state = RobotStates.ENSENAR
    monkeypatch.setattr(web_app, "robot", robot)
    cliente = _cliente()

    assert cliente.post("/api/ensenar/grabar", json={"tabla": "nivel1_numeros", "id": 2}).status_code == 200
    assert robot.ordenes_docente.get_nowait()[0] == "grabar"

    # Lo que hace el hilo del robot al terminar de grabar.
    _grabar_pendiente()
    robot.ensenanza = {"estado": "grabado", "palabra": robot.ensenanza["palabra"], "transcripcion": "pishka"}
    assert cliente.get("/ensenar/audio/pendiente").status_code == 200
    assert cliente.post("/api/ensenar/guardar").status_code == 200
    assert pronunciaciones.variantes("Pichqa") == ["pishka"]
    # Guardar dos veces la misma grabación no se permite.
    assert cliente.post("/api/ensenar/guardar").status_code == 409
