from types import SimpleNamespace

from main_robot import HardwareInterface


def test_texto_visible_guarda_texto_cuando_no_viene_con_patron() -> None:
    robot = HardwareInterface.__new__(HardwareInterface)

    texto = "Yusulpayki significa gracias. Como te llamas?"

    assert robot._texto_visible(texto) == "Yusulpayki significa gracias"


def test_hablar_genera_el_audio_antes_de_convertirlo(monkeypatch, tmp_path):
    robot = HardwareInterface.__new__(HardwareInterface)
    robot.audio_temp = str(tmp_path / "respuesta.mp3")
    robot.voz_mujer = "es-MX-DaliaNeural"
    robot.audio_manager = None
    robot.on_status = None
    llamadas = []

    def ejecutar(comando, **_kwargs):
        llamadas.append(comando[0])
        if comando[0].endswith("edge-tts"):
            with open(robot.audio_temp, "wb") as audio:
                audio.write(b"mp3 actual")
        elif comando[0] == "wpctl":
            return SimpleNamespace(
                returncode=0,
                stdout='  * object.serial = "56"\n'
            )
        elif comando[0] == "ffmpeg":
            assert (tmp_path / "respuesta.mp3").exists()
            with open(comando[-1], "wb") as audio:
                audio.write(b"wav actual")
        elif comando[0] == "pw-play":
            assert comando[1:3] == ["--target", "56"]
            assert (tmp_path / "respuesta.mp3.wav").exists()
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("main_robot.subprocess.run", ejecutar)
    monkeypatch.setattr(
        "main_robot.shutil.which",
        lambda programa: {
            "ffmpeg": "ffmpeg",
            "pw-play": "pw-play",
            "wpctl": "wpctl",
            "ffplay": None,
            "mpg123": None,
        }.get(programa)
    )

    robot.hablar("Rimaykullayki")

    assert llamadas[-3:] == ["ffmpeg", "wpctl", "pw-play"]


def test_voz_en_vivo_suena_mientras_llega_y_la_guarda_en_cache(monkeypatch, tmp_path):
    import sys
    import types
    import wave

    monkeypatch.setenv("YURA_VOZ_EN_VIVO", "1")
    robot = HardwareInterface.__new__(HardwareInterface)
    robot.voz_mujer = "es-BO-SofiaNeural"
    robot.audio_manager = None
    monkeypatch.setattr(robot, "_destino_pipewire_predeterminado", lambda: "56", raising=False)
    pcm = b"\x01\x00" * 2400
    lanzados = {}

    class Entrada:
        def __init__(self):
            self.datos = bytearray()

        def write(self, datos):
            self.datos.extend(datos)

        def flush(self):
            pass

        def close(self):
            pass

    class Proceso:
        def __init__(self, comando, **_kwargs):
            self.comando = comando
            self.stdin = Entrada()
            self.returncode = 0
            salida = [pcm, b""]
            self.stdout = types.SimpleNamespace(read=lambda _n: salida.pop(0) if salida else b"")
            lanzados[comando[0]] = self

        def wait(self, timeout=None):
            return 0

        def poll(self):
            return 0

        def kill(self):
            pass

    class Comunicar:
        def __init__(self, texto, voz, rate, pitch):
            lanzados["edge"] = (texto, voz)

        async def stream(self):
            yield {"type": "audio", "data": b"mp3"}

    monkeypatch.setitem(sys.modules, "edge_tts", types.SimpleNamespace(Communicate=Comunicar))
    monkeypatch.setattr("main_robot.subprocess.Popen", Proceso)
    monkeypatch.setattr("main_robot.shutil.which", lambda programa: programa if programa in ("ffmpeg", "pw-play") else None)
    cache = tmp_path / "frase.wav"

    assert robot._hablar_edge_en_vivo("Allillanmi", str(cache), espera=5)

    assert lanzados["edge"] == ("Allillanmi", "es-BO-SofiaNeural")
    assert bytes(lanzados["ffmpeg"].stdin.datos) == b"mp3"
    assert lanzados["pw-play"].comando[1:4] == ["--target", "56", "--raw"]
    assert bytes(lanzados["pw-play"].stdin.datos) == pcm
    with wave.open(str(cache), "rb") as archivo:
        assert archivo.readframes(archivo.getnframes()) == pcm


def test_voz_en_vivo_se_puede_desactivar(monkeypatch):
    monkeypatch.setenv("YURA_VOZ_EN_VIVO", "0")
    robot = HardwareInterface.__new__(HardwareInterface)
    assert robot._hablar_edge_en_vivo("Allillanmi", None, espera=5) is False
