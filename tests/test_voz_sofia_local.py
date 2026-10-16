"""Voz de Sofía sin Microsoft (voz_sofia_local.py), sin cargar modelos."""
import os

import voz_sofia
import voz_sofia_local


def _activar(monkeypatch, tmp_path):
    monkeypatch.setattr(voz_sofia_local, "activa", lambda: True)
    monkeypatch.setattr(voz_sofia_local, "CARPETA", str(tmp_path / "local"))
    convertidas = []

    def convertir(texto, destino):
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(destino, "wb") as archivo:
            archivo.write(b"wav")
        convertidas.append(texto)
        return destino

    monkeypatch.setattr(voz_sofia_local, "convertir", convertir)
    return convertidas


def test_usa_la_sofia_real_guardada_y_convierte_solo_lo_que_falta(monkeypatch, tmp_path):
    convertidas = _activar(monkeypatch, tmp_path)
    carpeta = tmp_path / "sofia"
    carpeta.mkdir()
    real = voz_sofia.ruta_cache(str(carpeta), "es-BO-SofiaNeural", "¡Muy bien!")
    with open(real, "wb") as archivo:
        archivo.write(b"wav")
    sonaron = []

    ok = voz_sofia_local.decir(
        "¡Muy bien! Allqu significa perro.",
        lambda ruta: sonaron.append(ruta) or True,
        str(carpeta),
        "es-BO-SofiaNeural",
    )

    assert ok
    assert sonaron[0] == real
    assert convertidas == ["Allqu significa perro."]


def test_la_segunda_vez_no_vuelve_a_convertir(monkeypatch, tmp_path):
    convertidas = _activar(monkeypatch, tmp_path)
    for _ in range(2):
        assert voz_sofia_local.decir("Hola, soy Yura.", lambda ruta: True)
    assert convertidas == ["Hola, soy Yura."]


def test_si_falla_la_conversion_avisa_para_usar_otra_voz(monkeypatch, tmp_path):
    _activar(monkeypatch, tmp_path)

    def falla(texto, destino):
        raise RuntimeError("sin modelos")

    monkeypatch.setattr(voz_sofia_local, "convertir", falla)
    assert not voz_sofia_local.decir("Hola.", lambda ruta: True)


def test_microsoft_caido_no_se_intenta_por_un_rato(monkeypatch):
    monkeypatch.setattr(voz_sofia, "hay_internet", lambda espera=1.5: True)
    assert voz_sofia.edge_disponible()
    voz_sofia.marcar_falla_edge()
    assert not voz_sofia.edge_disponible()


def test_apagada_con_variable(monkeypatch):
    monkeypatch.setenv("YURA_VOZ_LOCAL", "0")
    assert not voz_sofia_local.activa()
