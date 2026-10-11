"""La voz de Sofía con y sin internet (voz_sofia.py)."""
import os

import voz_sofia
from main_robot import HardwareInterface


def test_divide_en_oraciones():
    assert voz_sofia.oraciones("Muy bien! Allqu significa Perro. ¿Otra?") == ["Muy bien!", "Allqu significa Perro.", "¿Otra?"]


def test_expresion_y_clave_de_cache(tmp_path):
    assert voz_sofia.prosodia("Muy bien! Lo lograste.") == voz_sofia.CELEBRAR
    assert voz_sofia.prosodia("Quieres jugar?") == voz_sofia.PREGUNTAR
    assert voz_sofia.prosodia("No te preocupes, intentemos otra vez.") == voz_sofia.CONSOLAR
    # La expresión normal conserva la clave de siempre (audios ya guardados).
    import hashlib
    clave = hashlib.sha256("v:hola.".encode()).hexdigest()[:24]
    assert voz_sofia.ruta_cache(str(tmp_path), "v", "Hola.") == str(tmp_path / f"{clave}.wav")


def test_anota_lo_que_falta_una_sola_vez(tmp_path):
    voz_sofia.anotar_faltante(str(tmp_path), "Hola, amigo.")
    voz_sofia.anotar_faltante(str(tmp_path), "Hola, amigo.")
    with open(voz_sofia.ruta_faltantes(str(tmp_path)), encoding="utf-8") as archivo:
        assert archivo.read().splitlines() == ["Hola, amigo."]


def test_arma_la_frase_con_oraciones_guardadas(tmp_path):
    hw = HardwareInterface.__new__(HardwareInterface)
    hw.carpeta_cache_voz = str(tmp_path)
    hw.voz_mujer = "es-BO-SofiaNeural"
    tocadas = []
    hw._reproducir_archivo_audio = lambda ruta, espera=30: tocadas.append(ruta) or True
    frase = "Muy bien! Allqu significa Perro."
    assert not hw._hablar_con_oraciones_guardadas(frase, 5)  # todavía no hay nada guardado
    for parte in voz_sofia.oraciones(frase):
        with open(hw._ruta_cache_voz(parte), "wb") as archivo:
            archivo.write(b"x")
    assert hw._hablar_con_oraciones_guardadas(frase, 5)
    assert len(tocadas) == 2 and all(os.path.exists(r) for r in tocadas)
