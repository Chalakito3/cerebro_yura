"""Registro y consulta de resultados (resultados.db) y su página web."""

import sqlite3
from unittest.mock import Mock

import conversacion
import resultados
import texto
from juego import Juego


def _intentos():
    return resultados.todos_los_intentos()


def test_registrar_y_resumir_intentos():
    resultados.registrar_intento("juego", "perro", "Allqo", "allqo", True, "p1")
    resultados.registrar_intento("juego", "gato", "Misi", "michi", False, "p1")
    resultados.registrar_intento("practica", "gato", "Misi", "wawa", False, "s1")

    datos = resultados.resumen()
    assert (datos["total"], datos["aciertos"], datos["porcentaje"]) == (3, 1, 33)
    assert {a["actividad"]: a["sesiones"] for a in datos["por_actividad"]} == {"juego": 1, "practica": 1}
    assert datos["palabras_dificiles"][0]["quechua"] == "Misi"
    assert datos["palabras_dificiles"][0]["fallos"] == 2
    assert datos["ultimos"][0]["actividad"] == "practica"


def test_la_base_impide_datos_invalidos():
    assert resultados.registrar_intento("examen", "a", "b", "c", True, "x") is False
    with sqlite3.connect(resultados.RUTA_DB) as conexion:
        conexion.executescript(resultados._ESQUEMA)
        try:
            conexion.execute(
                "INSERT INTO intentos (fecha, actividad, sesion, palabra_espanol,"
                " palabra_quechua, respuesta, correcto) VALUES ('f','juego','s','a','b','c',5)"
            )
            assert False, "correcto=5 debía rechazarse"
        except sqlite3.IntegrityError:
            pass


def test_un_error_al_guardar_no_detiene_a_yura(monkeypatch):
    monkeypatch.setattr(resultados, "RUTA_DB", "/ruta/que/no/existe/resultados.db")
    assert resultados.registrar_intento("juego", "perro", "Allqo", "x", False, "p") is False


def test_el_juego_guarda_cada_respuesta_con_su_partida():
    # La misma palabra dos veces: el juego mezcla el orden al azar.
    juego = Juego(
        ["perro", "perro"],
        lambda palabra: "Allqo",
        Mock(side_effect=["allqo", "wawa"]),
        Mock(),
        Mock(),
        texto.normalizar,
    )
    juego.reiniciar()
    juego.ejecutar_turno()
    juego.ejecutar_turno()

    intentos = _intentos()
    assert len(intentos) == 2
    assert {i["sesion"] for i in intentos} == {juego.partida}
    assert sorted(i["correcto"] for i in intentos) == [0, 1]
    assert {i["respuesta"] for i in intentos} == {"allqo", "wawa"}


def test_una_partida_nueva_tiene_otro_identificador():
    juego = Juego(["perro"], lambda p: "Allqo", Mock(), Mock(), Mock(), texto.normalizar)
    juego.reiniciar()
    primera = juego.partida
    juego.reiniciar()
    assert juego.partida != primera


def test_la_practica_guarda_cada_intento():
    conversacion.cancelar_sesion_educativa()
    conversacion.procesar_entrada("enséñame quechua", None)
    palabra = conversacion._sesion_educativa["registro"]["quechua"]
    conversacion.procesar_entrada(palabra, None)
    conversacion.procesar_entrada("siguiente", None)
    conversacion.procesar_entrada("xyz", None)
    conversacion.cancelar_sesion_educativa()

    intentos = _intentos()
    assert len(intentos) == 2
    assert intentos[0]["correcto"] == 1
    assert intentos[1]["correcto"] == 0
    assert intentos[0]["sesion"] == intentos[1]["sesion"]


def _cliente():
    from web.app import app
    return app.test_client()


def test_pagina_de_resultados_vacia():
    respuesta = _cliente().get("/resultados")
    assert respuesta.status_code == 200
    assert "Todavía no hay resultados" in respuesta.get_data(as_text=True)


def test_pagina_de_resultados_muestra_los_intentos_sin_ejecutar_html():
    resultados.registrar_intento("juego", "perro", "Allqo", "<script>alert(1)</script>", False, "p")
    html = _cliente().get("/resultados").get_data(as_text=True)
    assert "Allqo" in html
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_api_y_csv_de_resultados():
    resultados.registrar_intento("practica", "niño", "Wawa", "wawa", True, "s")
    cliente = _cliente()
    assert cliente.get("/api/resultados").get_json()["total"] == 1

    csv = cliente.get("/resultados.csv")
    assert csv.status_code == 200
    texto_csv = csv.get_data(as_text=True)
    assert texto_csv.startswith("﻿id,fecha,actividad")
    assert "niño,Wawa,wawa,sí" in texto_csv


# --- Protección de resultados en la red ------------------------------

import base64

OTRO_EQUIPO = {"REMOTE_ADDR": "192.168.40.50"}


def _basic(clave):
    return {"Authorization": "Basic " + base64.b64encode(f"docente:{clave}".encode()).decode()}


def test_resultados_se_ven_sin_clave_desde_la_computadora_de_yura():
    assert _cliente().get("/resultados").status_code == 200


def test_resultados_bloqueados_en_la_red_si_no_hay_clave(monkeypatch):
    monkeypatch.delenv("YURA_RESULTADOS_CLAVE", raising=False)
    for ruta in ("/resultados", "/api/resultados", "/resultados.csv"):
        assert _cliente().get(ruta, environ_base=OTRO_EQUIPO).status_code == 403


def test_resultados_piden_clave_en_la_red(monkeypatch):
    monkeypatch.setenv("YURA_RESULTADOS_CLAVE", "kusisqa-2026")
    cliente = _cliente()
    sin_clave = cliente.get("/resultados", environ_base=OTRO_EQUIPO)
    assert sin_clave.status_code == 401
    assert "Basic" in sin_clave.headers["WWW-Authenticate"]
    mala = cliente.get("/resultados", environ_base=OTRO_EQUIPO, headers=_basic("otra"))
    assert mala.status_code == 401
    buena = cliente.get("/resultados.csv", environ_base=OTRO_EQUIPO, headers=_basic("kusisqa-2026"))
    assert buena.status_code == 200


def test_la_pantalla_del_robot_sigue_abierta_en_la_red(monkeypatch):
    monkeypatch.delenv("YURA_RESULTADOS_CLAVE", raising=False)
    cliente = _cliente()
    assert cliente.get("/", environ_base=OTRO_EQUIPO).status_code == 200
    assert cliente.get("/api/status", environ_base=OTRO_EQUIPO).status_code == 200


# --- Estudiante o grupo que juega ------------------------------------

def test_los_intentos_se_guardan_a_nombre_del_participante_actual():
    assert resultados.definir_participante("  Grupo   2 <b> ") == "Grupo 2 b"
    resultados.registrar_intento("juego", "perro", "Allqu", "allqu", True, "p1")
    resultados.definir_participante("")
    resultados.registrar_intento("juego", "gato", "Misi", "wawa", False, "p2")

    intentos = _intentos()
    assert [i["participante"] for i in intentos] == ["Grupo 2 b", ""]
    datos = resultados.resumen()
    assert {f["participante"] for f in datos["por_participante"]} == {"Grupo 2 b", ""}
    solo_grupo = resultados.resumen(participante="Grupo 2 b")
    assert solo_grupo["total"] == 1 and solo_grupo["aciertos"] == 1


def test_base_de_resultados_antigua_se_actualiza_sin_perder_datos():
    with sqlite3.connect(resultados.RUTA_DB) as conexion:
        conexion.executescript("""
            CREATE TABLE intentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT NOT NULL,
                actividad TEXT NOT NULL, sesion TEXT NOT NULL,
                palabra_espanol TEXT NOT NULL, palabra_quechua TEXT NOT NULL,
                respuesta TEXT NOT NULL DEFAULT '', correcto INTEGER NOT NULL);
            INSERT INTO intentos (fecha, actividad, sesion, palabra_espanol, palabra_quechua, respuesta, correcto)
            VALUES ('2026-09-27T10:00:00', 'juego', 's', 'sol', 'Inti', 'inti', 1);
        """)
    intentos = _intentos()
    assert len(intentos) == 1 and intentos[0]["participante"] == ""


def test_formulario_cambia_el_participante_desde_la_computadora():
    cliente = _cliente()
    respuesta = cliente.post("/resultados/participante", data={"participante": "N.º 14"})
    assert respuesta.status_code == 303
    assert resultados.participante_actual() == "N.º 14"
    assert "N.º 14" in cliente.get("/resultados").get_data(as_text=True)
    assert cliente.get("/api/status").get_json()["participante"] == "N.º 14"


def test_formulario_rechaza_envios_de_otras_paginas():
    respuesta = _cliente().post(
        "/resultados/participante",
        data={"participante": "intruso"},
        headers={"Origin": "http://pagina-maliciosa.com"},
    )
    assert respuesta.status_code == 403
    assert resultados.participante_actual() == ""


def test_formulario_protegido_desde_la_red(monkeypatch):
    monkeypatch.delenv("YURA_RESULTADOS_CLAVE", raising=False)
    respuesta = _cliente().post(
        "/resultados/participante", data={"participante": "x"}, environ_base=OTRO_EQUIPO,
    )
    assert respuesta.status_code == 403


def test_filtro_por_participante_en_la_pagina():
    resultados.registrar_intento("juego", "sol", "Inti", "inti", True, "a", participante="Grupo 1")
    resultados.registrar_intento("juego", "luna", "Killa", "x", False, "b", participante="Grupo 2")
    html = _cliente().get("/resultados?participante=Grupo 1").get_data(as_text=True)
    assert "Mostrando solo" in html and "Inti" in html and "Killa" not in html
