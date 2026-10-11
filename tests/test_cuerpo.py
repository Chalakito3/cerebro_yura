"""Pruebas del cuerpo de Yura (ESP32 por USB) con un ESP32 simulado."""
import os
import threading
import time

import pytest

import cuerpo


class ESP32Simulado:
    """Un puerto serie falso (pty) que responde como el programa del ESP32."""

    def __init__(self):
        self.maestro, esclavo = os.openpty()
        self.puerto = os.ttyname(esclavo)
        self.recibidas = []
        threading.Thread(target=self._leer, daemon=True).start()

    def _leer(self):
        pendiente = b""
        while True:
            try:
                datos = os.read(self.maestro, 256)
            except OSError:
                return
            pendiente += datos
            while b"\n" in pendiente:
                linea, pendiente = pendiente.split(b"\n", 1)
                texto = linea.decode().strip()
                self.recibidas.append(texto)
                if texto == "PING":
                    os.write(self.maestro, b"YURA_CUERPO v5\n")


def esperar(condicion, limite=5.0):
    fin = time.time() + limite
    while time.time() < fin:
        if condicion():
            return True
        time.sleep(0.05)
    return False


@pytest.fixture(autouse=True)
def sin_espera(monkeypatch):
    monkeypatch.setattr(cuerpo, "ESPERA_ARRANQUE", 0.0)


def test_envia_estados_movimientos_y_alto():
    esp32 = ESP32Simulado()
    yura = cuerpo.CuerpoESP32(puerto=esp32.puerto)
    assert esperar(lambda: yura.conectado)
    yura.estado("HABLANDO")
    yura.estado("HABLANDO")  # repetido: no se reenvía
    yura.mover("adelante", 1500)
    yura.mover("volar", 100)  # dirección inválida: no se manda
    yura.alto()
    assert esperar(lambda: "ALTO" in esp32.recibidas)
    assert esp32.recibidas == ["PING", "ESTADO:HABLANDO", "MOVER:ADELANTE:1500", "ALTO"]


def test_sin_esp32_yura_sigue_igual(monkeypatch):
    monkeypatch.setattr(cuerpo, "buscar_puerto", lambda: None)
    yura = cuerpo.CuerpoESP32()
    for _ in range(100):
        yura.estado("HABLANDO")
        yura.estado("ESPERANDO")
        yura.mover("ADELANTE")
    assert not yura.conectado


def test_se_puede_desactivar(monkeypatch):
    monkeypatch.setenv("YURA_CUERPO", "0")
    yura = cuerpo.CuerpoESP32()
    yura.alto()
    assert yura._hilo is None and yura._cola.empty()
