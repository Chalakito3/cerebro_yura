"""Pruebas de la pronunciación que Yura aprende de los audios de la docente."""

import os
import sqlite3
import sys

import pronunciaciones

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "basedatos"))
import aprender_pronunciacion as aprender  # noqa: E402


def _guardar_voz(palabra, para_voz):
    with pronunciaciones._conectar() as conexion:
        conexion.execute(
            f"INSERT OR REPLACE INTO {pronunciaciones.TABLA_VOZ} "
            "(palabra_frase, texto_para_voz, parecido, parecido_original, fecha) VALUES (?, ?, 1, 2, 'hoy')",
            (palabra, para_voz),
        )


def test_la_voz_usa_la_forma_aprendida_y_la_pantalla_no_cambia(monkeypatch):
    monkeypatch.delenv("YURA_PRONUNCIACION_APRENDIDA", raising=False)
    _guardar_voz("Q'umir", "Kúmir")
    _guardar_voz("Allin p'unchay", "Allin púnchay")
    frase = "Verde se dice Q'umir. Allin p'unchay, wawakuna. q’umir"
    assert pronunciaciones.texto_para_hablar(frase) == "Verde se dice Kúmir. Allin púnchay, wawakuna. Kúmir"


def test_no_cambia_palabras_dentro_de_otras_ni_castellanas():
    _guardar_voz("Uj", "Uuj")
    _guardar_voz("Para", "Pára")
    frase = "Sujeta la uja para practicar"
    assert pronunciaciones.texto_para_hablar(frase) == frase


def test_se_puede_desactivar(monkeypatch):
    _guardar_voz("Q'umir", "Kúmir")
    monkeypatch.setenv("YURA_PRONUNCIACION_APRENDIDA", "0")
    assert pronunciaciones.texto_para_hablar("Q'umir") == "Q'umir"


def test_sin_aprendizaje_el_texto_queda_igual():
    assert pronunciaciones.texto_para_hablar("Allqu significa perro") == "Allqu significa perro"


def test_adaptacion_al_castellano():
    assert aprender.adaptar_al_castellano("Q'umir") == "Kúmir"
    assert aprender.adaptar_al_castellano("Atuq") == "Átuk"
    assert aprender.adaptar_al_castellano("Atuq", q_final="j") == "Átuj"
    assert aprender.adaptar_al_castellano("Qhari") == "Jari"
    assert aprender.adaptar_al_castellano("Wasi") == "Wasi"


def test_candidatas_descartan_lo_que_no_se_parece():
    opciones = aprender.candidatas("Q'umir", ["omer", "adios", "subtitulos de amara org"])
    assert "omer" in opciones and "Kúmir" in opciones
    assert "adios" not in opciones


def test_dtw_prefiere_el_sonido_igual():
    import numpy as np
    azar = np.random.default_rng(0)
    a = azar.normal(size=(40, 80))
    parecido = a + azar.normal(scale=0.1, size=a.shape)
    distinto = azar.normal(size=(40, 80))
    assert aprender.distancia_dtw(a, parecido) < aprender.distancia_dtw(a, distinto)


def test_reglas_de_sentido_comun():
    assert not aprender.candidata_permitida("ucha", "Qucha")        # pierde el primer sonido
    assert not aprender.candidata_permitida("omer", "Q'umir")
    assert not aprender.candidata_permitida("cagual lo", "Kawallu")  # parte la palabra
    assert not aprender.candidata_permitida("walking", "Wakin")      # suena a inglés
    assert not aprender.candidata_permitida("hóchuy", "Juch'uy")     # la h no suena
    assert aprender.candidata_permitida("Kúmir", "Q'umir")
    assert aprender.candidata_permitida("taua", "Tawa")


def _voz_entrenada(palabra, archivo="x.wav"):
    import numpy as np
    os.makedirs(pronunciaciones.CARPETA_VOZ_YURA, exist_ok=True)
    pronunciaciones.guardar_wav(os.path.join(pronunciaciones.CARPETA_VOZ_YURA, archivo),
                                (np.ones(800) * 1000).astype(np.int16).tobytes())
    with pronunciaciones._conectar() as conexion:
        conexion.execute(
            f"INSERT OR REPLACE INTO {pronunciaciones.TABLA_VOZ} (palabra_frase, texto_para_voz, fecha, audio_yura) "
            "VALUES (?, ?, 'hoy', ?)", (palabra, palabra, archivo))


def test_la_frase_se_divide_en_voz_y_audio_entrenado(monkeypatch, tmp_path):
    monkeypatch.setattr(pronunciaciones, "CARPETA_VOZ_YURA", str(tmp_path / "voz"))
    monkeypatch.setenv("YURA_VOZ_AUDIO_APRENDIDO", "1")
    _voz_entrenada("Q'umir", "qumir.wav")
    _voz_entrenada("Para", "para.wav")  # también castellana: no se reemplaza
    partes = pronunciaciones.partes_para_hablar("Verde se dice Q'umir, para practicar.")
    assert [t for t, _ in partes] == ["texto", "audio", "texto"]
    assert partes[0][1] == "Verde se dice "
    assert partes[1][1].endswith("qumir.wav")
    assert partes[2][1] == ", para practicar."


def test_sin_voz_entrenada_o_desactivada_solo_texto(monkeypatch, tmp_path):
    monkeypatch.setattr(pronunciaciones, "CARPETA_VOZ_YURA", str(tmp_path / "voz"))
    monkeypatch.setenv("YURA_VOZ_AUDIO_APRENDIDO", "1")
    assert pronunciaciones.partes_para_hablar("Allqu es perro") == [("texto", "Allqu es perro")]
    _voz_entrenada("Allqu", "allqu.wav")
    monkeypatch.delenv("YURA_VOZ_AUDIO_APRENDIDO")
    # Por defecto no se usa: Yura mantiene su voz natural.
    assert pronunciaciones.partes_para_hablar("Allqu es perro") == [("texto", "Allqu es perro")]
    monkeypatch.setenv("YURA_VOZ_AUDIO_APRENDIDO", "0")
    assert pronunciaciones.partes_para_hablar("Allqu es perro") == [("texto", "Allqu es perro")]


def test_hablar_por_partes_arma_una_sola_grabacion(monkeypatch, tmp_path):
    import wave
    import numpy as np
    from main_robot import HardwareInterface
    monkeypatch.setattr(pronunciaciones, "CARPETA_VOZ_YURA", str(tmp_path / "voz"))
    monkeypatch.setenv("YURA_VOZ_AUDIO_APRENDIDO", "1")
    _voz_entrenada("Allqu", "allqu.wav")
    # La voz de Yura en 24 kHz (el entrenamiento guarda así las palabras).
    ruta = os.path.join(str(tmp_path / "voz"), "allqu.wav")
    with wave.open(ruta, "wb") as archivo:
        archivo.setnchannels(1); archivo.setsampwidth(2); archivo.setframerate(24000)
        archivo.writeframes((np.ones(2400) * 2000).astype(np.int16).tobytes())
    hw = HardwareInterface.__new__(HardwareInterface)
    hw.audio_temp = str(tmp_path / "voz_temp")
    hw._voz_a_muestras = lambda texto, i: np.full(4800, 0.1, dtype=np.float32)
    reproducido = {}

    def reproducir(ruta):
        with wave.open(ruta) as archivo:
            reproducido["muestras"] = archivo.getnframes()
        return True
    hw.reproducir_grabacion = reproducir
    assert hw._hablar_por_partes("Se dice Allqu, perro.")
    # voz (4800) + pausa + palabra (2400) + pausa + voz (4800)
    assert reproducido["muestras"] == 4800 + 1440 + 2400 + 1440 + 4800
    assert not hw._hablar_por_partes("Sin palabras entrenadas.")


def test_ruta_cache_voz_calcula_hash_consistente(tmp_path):
    from main_robot import HardwareInterface
    hw = HardwareInterface()
    hw.carpeta_cache_voz = str(tmp_path / "cache_test")
    hw.voz_mujer = "es-BO-SofiaNeural"
    ruta = hw._ruta_cache_voz("Rimaykullayki.")
    assert ruta is not None
    assert ruta.startswith(str(tmp_path / "cache_test"))
    assert ruta.endswith(".wav")
    # El mismo texto debe producir siempre la misma ruta
    assert hw._ruta_cache_voz("  rimaykullayki.  ") == ruta


def test_hablar_reproduce_desde_cache_offline_sin_llamar_edge_tts(monkeypatch, tmp_path):
    from main_robot import HardwareInterface
    cache_dir = tmp_path / "cache_sofia"
    cache_dir.mkdir()

    hw = HardwareInterface()
    hw.carpeta_cache_voz = str(cache_dir)
    hw.voz_mujer = "es-BO-SofiaNeural"

    # Pre-crear archivo simulado en caché para "Rimaykullayki."
    ruta_esperada = hw._ruta_cache_voz(hw._formatear_texto_voz(pronunciaciones.texto_para_hablar("Rimaykullayki")))
    with open(ruta_esperada, "wb") as f:
        f.write(b"RIFF....WAVEfmt ....data....")

    reproducidos = []
    monkeypatch.setattr(hw, "_reproducir_archivo_audio", lambda ruta, espera=30: reproducidos.append(ruta) or True)

    # Si intentara llamar a subprocess (edge-tts), debe fallar el test
    def no_debe_llamarse(*args, **kwargs):
        raise AssertionError("Edge-TTS no debió llamarse porque el audio ya estaba en la caché local offline.")
    monkeypatch.setattr("main_robot.subprocess.run", no_debe_llamarse)

    hw.hablar("Rimaykullayki")
    assert len(reproducidos) == 1
    assert reproducidos[0] == ruta_esperada
