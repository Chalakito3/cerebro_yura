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
