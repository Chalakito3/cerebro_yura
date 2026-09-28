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
