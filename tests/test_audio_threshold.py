import numpy as np

from audio_manager import AudioManager


def test_lista_de_candidatos_prefiere_dispositivo_activo_reciente(monkeypatch):
    monkeypatch.setattr(
        AudioManager,
        "_obtener_dispositivo_entrada_activo",
        staticmethod(lambda: "USB PnP Audio Device")
    )

    candidatos = [
        {"index": 0, "name": "Built-in Audio Analog Stereo", "priority": 10},
        {"index": 1, "name": "USB PnP Audio Device", "priority": 20},
        {"index": 2, "name": "Logitech USB Headset", "priority": 25},
    ]

    orden = AudioManager._reordenar_candidatos_por_dispositivo_activo(candidatos)
    assert orden[0]["name"] == "USB PnP Audio Device"
    assert orden[-1]["name"] == "Built-in Audio Analog Stereo"


def test_calculo_umbral_se_mantiene_estable():
    umbral = AudioManager._calcular_umbral_ruido(0.002)
    assert 0.006 <= umbral <= 0.02
    assert umbral < 0.02


def test_nivel_audio_usa_media_absoluta():
    bloque = np.array([0.0, 0.2, -0.2, 0.1], dtype=np.float32)
    nivel = AudioManager._calcular_nivel_audio(bloque)
    assert abs(nivel - 0.125) < 1e-6


def test_umbral_no_se_queda_demasiado_bajo_en_ruido_ambiental_leve():
    umbral = AudioManager._calcular_umbral_ruido(0.0008)
    assert umbral >= 0.006


def test_umbral_se_ajusta_ante_ruido_ambiental_alto():
    umbral = AudioManager._calcular_umbral_ruido(0.02)
    assert umbral >= 0.01


def test_umbral_supera_el_ruido_ambiental_medido():
    nivel_ruido = 0.066
    umbral = AudioManager._calcular_umbral_ruido(nivel_ruido)
    assert umbral > nivel_ruido


def _manager_con_dispositivos(monkeypatch, estado):
    """AudioManager con PortAudio y /proc/asound/cards simulados."""
    import audio_manager as modulo

    reinicios = []
    monkeypatch.setattr(modulo.sd, "query_devices", lambda: list(estado["dispositivos"]))
    monkeypatch.setattr(modulo.sd, "_terminate", lambda: reinicios.append("terminar"))
    monkeypatch.setattr(modulo.sd, "_initialize", lambda: reinicios.append("iniciar"))
    monkeypatch.setattr(AudioManager, "_leer_tarjetas", staticmethod(lambda: estado["tarjetas"]))
    monkeypatch.setattr(AudioManager, "_obtener_dispositivo_entrada_activo", classmethod(lambda cls: None))
    monkeypatch.setattr(AudioManager, "validar_entrada", lambda self, candidato: (48000, 1))
    monkeypatch.setattr(AudioManager, "seleccionar_salida", lambda self: None)
    return AudioManager(), reinicios


def test_microfono_enchufado_despues_se_detecta_y_se_usa(monkeypatch):
    placa = {"name": "Mic de la placa (hw:3,0)", "max_input_channels": 1, "max_output_channels": 0}
    usb = {"name": "USB PnP Sound Device: Audio (hw:2,0)", "max_input_channels": 1, "max_output_channels": 2}
    estado = {"dispositivos": [placa], "tarjetas": "3 placa\n"}
    manager, reinicios = _manager_con_dispositivos(monkeypatch, estado)
    assert manager.input_name == placa["name"]
    assert reinicios == []

    estado.update(dispositivos=[placa, usb], tarjetas="2 usb\n3 placa\n")
    assert manager.tarjetas_cambiaron()
    manager.detectar_dispositivos()
    manager.seleccionar_entrada()

    assert reinicios == ["terminar", "iniciar"]
    assert manager.input_name == usb["name"]
    assert not manager.tarjetas_cambiaron()


def test_al_sacar_el_microfono_vuelve_al_que_queda(monkeypatch):
    placa = {"name": "Mic de la placa (hw:3,0)", "max_input_channels": 1, "max_output_channels": 0}
    usb = {"name": "USB PnP Sound Device: Audio (hw:2,0)", "max_input_channels": 1, "max_output_channels": 2}
    estado = {"dispositivos": [placa], "tarjetas": "3 placa\n"}
    manager, _ = _manager_con_dispositivos(monkeypatch, estado)
    estado.update(dispositivos=[placa, usb], tarjetas="2 usb\n3 placa\n")
    manager.detectar_dispositivos()
    manager.seleccionar_entrada()

    estado.update(dispositivos=[placa], tarjetas="3 placa\n")
    manager.detectar_dispositivos()
    manager.seleccionar_entrada()

    assert manager.input_name == placa["name"]
    assert manager._entrada_nueva is None


def test_microfono_desconectado_no_deja_a_yura_colgada():
    """Al sacar la tarjeta USB, PortAudio dejaba de entregar audio sin avisar
    y stream.read() esperaba para siempre (13/10/2026)."""
    import time
    import pytest

    class MicrofonoMuerto:
        read_available = 0

        def read(self, frames):
            raise AssertionError("no debe leer si no hay audio")

    inicio = time.monotonic()
    with pytest.raises(RuntimeError):
        AudioManager._leer_bloque(MicrofonoMuerto(), 1280, limite=0.1)
    assert time.monotonic() - inicio < 1


def test_reconectar_la_misma_tarjeta_cuenta_como_cambio(monkeypatch, tmp_path):
    """Vuelve con igual número y nombre: lo que cambia es el archivo /dev/snd."""
    import audio_manager as modulo

    nodo = tmp_path / "pcmC2D0c"
    nodo.write_text("")
    cartas = tmp_path / "cards"
    cartas.write_text(" 2 [Device ]: USB-Audio - USB PnP Sound Device\n")
    abrir_real = open
    monkeypatch.setattr(modulo.glob, "glob", lambda patron: [str(nodo)])
    monkeypatch.setattr("builtins.open", lambda ruta, *a, **k: abrir_real(cartas if ruta == "/proc/asound/cards" else ruta, *a, **k))

    antes = AudioManager._leer_tarjetas()
    otro = tmp_path / "otro"
    otro.write_text("")
    nodo.unlink()
    otro.rename(nodo)  # mismo nombre, archivo nuevo
    assert AudioManager._leer_tarjetas() != antes


_HDMI = (35, "alsa_output.platform-107c706400.hdmi.hdmi-stereo", "Built-in Audio Digital Stereo (HDMI)")
_TARJETA = (57, "alsa_output.usb-C-Media_Electronics_Inc._USB_PnP_Sound_Device-00.analog-stereo-output",
            "PCM2902 Audio Codec Analog Stereo")
_AUDIFONO = (91, "alsa_output.usb-Logitech_USB_Headset_Logitech_USB_Headset-00.analog-stereo",
             "H390 headset with microphone Analog Stereo")


def test_el_parlante_vuelve_a_la_tarjeta_usb_y_no_al_audifono():
    """Tras reiniciar, PipeWire dejaba el HDMI por defecto (13/10/2026)."""
    salidas = [_HDMI, _AUDIFONO, _TARJETA]
    assert AudioManager.elegir_parlante(salidas, actual=_HDMI[1]) == _TARJETA
    assert AudioManager.elegir_parlante(salidas, actual=_TARJETA[1]) is None  # ya está bien
    assert AudioManager.elegir_parlante([_HDMI, _AUDIFONO], actual=_HDMI[1]) == _AUDIFONO
    assert AudioManager.elegir_parlante([_HDMI], actual=_HDMI[1]) is None


def test_yura_parlante_elige_otro():
    salidas = [_HDMI, _AUDIFONO, _TARJETA]
    assert AudioManager.elegir_parlante(salidas, actual=_TARJETA[1], preferido="H390") == _AUDIFONO
