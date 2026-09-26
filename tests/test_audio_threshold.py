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
