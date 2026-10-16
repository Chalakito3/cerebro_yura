import pytest

import pronunciaciones
import resultados


@pytest.fixture(autouse=True)
def _resultados_temporales(tmp_path, monkeypatch):
    # Las pruebas nunca escriben en el resultados.db real del proyecto.
    monkeypatch.setattr(resultados, "RUTA_DB", str(tmp_path / "resultados_prueba.db"))


@pytest.fixture(autouse=True)
def _pronunciaciones_temporales(tmp_path, monkeypatch):
    # Las pruebas nunca graban en diccionario.db ni en basedatos/pronunciaciones.
    monkeypatch.setattr(pronunciaciones, "RUTA_DB", str(tmp_path / "diccionario_prueba.db"))
    monkeypatch.setattr(pronunciaciones, "CARPETA_AUDIOS", str(tmp_path / "pronunciaciones"))


@pytest.fixture(autouse=True)
def _modo_idioma_quechua():
    """Cada prueba empieza en el modo de idioma por defecto (quechua)."""
    import conversacion

    def limpiar():
        conversacion.MODO_IDIOMA.update(bilingue=False, docente_hasta=0)
        conversacion._PALABRA_ESPERADA.update(palabra=None, hasta=0.0, intentos=0)
        conversacion._ULTIMO_TEMA.update(tema=None, desde=0, hasta=0.0)

    limpiar()
    yield
    limpiar()


@pytest.fixture(autouse=True)
def _sin_voz_en_vivo(monkeypatch):
    """Las pruebas nunca hacen sonar la voz en vivo (Edge TTS + pw-play)."""
    monkeypatch.setenv("YURA_VOZ_EN_VIVO", "0")


@pytest.fixture(autouse=True)
def _sin_voz_sofia_local(monkeypatch):
    """Las pruebas no cargan los modelos de la voz sin internet (~1,5 GB) y
    empiezan con Edge TTS sin marcas de falla de otra prueba."""
    import voz_sofia

    monkeypatch.setenv("YURA_VOZ_LOCAL", "0")
    monkeypatch.setitem(voz_sofia._edge, "falla_hasta", 0.0)


@pytest.fixture(autouse=True)
def _sin_cambiar_el_parlante_real(monkeypatch):
    """Las pruebas nunca cambian el parlante por defecto de la Raspberry."""
    import audio_manager

    monkeypatch.setattr(audio_manager.AudioManager, "_salidas_pipewire", staticmethod(lambda: []))
