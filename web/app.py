import os
import sys
import threading
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from main_robot import BrainYura, RobotStates


CARD_EXAMPLES = [
    {
        "key": "rimaykullayki",
        "title": "Rimaykullayki",
        "written": "Rimaykullayki",
        "pronunciation": "Ri-ma-y-ku-llay-ki",
        "meaning": "Rimaykullayki",
        "example": "Rimaykullayki, imaynalla kashanki?"
    },
    {
        "key": "allinpunchay",
        "title": "Allin p'unchay",
        "written": "Allin p'unchay",
        "pronunciation": "A-lin p'un-chay",
        "meaning": "Allin p'unchay",
        "example": "Allin p'unchay, wawqi."
    },
    {
        "key": "allintuta",
        "title": "Allin tuta",
        "written": "Allin tuta",
        "pronunciation": "A-lin tu-ta",
        "meaning": "Allin tuta",
        "example": "Allin tuta, ñañay."
    },
    {
        "key": "yusulpayki",
        "title": "Yusulpayki",
        "written": "Yusulpayki",
        "pronunciation": "Yu-su-lpay-ki",
        "meaning": "Yusulpayki",
        "example": "Yusulpayki, uywaq."
    },
    {
        "key": "anchata",
        "title": "Anchata munakuyki",
        "written": "Anchata munakuyki",
        "pronunciation": "An-cha-ta mu-na-kuy-ki",
        "meaning": "Anchata munakuyki",
        "example": "Anchata munakuyki, wayna."
    },
    {
        "key": "imaynallakachkanki",
        "title": "Imaynalla kachkanki",
        "written": "Imaynalla kachkanki",
        "pronunciation": "I-ma-ya-lla ka-ch-kan-ki",
        "meaning": "Imaynalla kachkanki",
        "example": "Imaynalla kachkanki, tayta?"
    }
]


app = Flask(__name__)
robot = None
robot_lock = threading.Lock()


def _status_payload():
    with robot_lock:
        current_robot = robot
        if current_robot is None:
            return {
                "robot": "YURA",
                "state": "BACKEND_NOT_STARTED",
                "running": False,
                "activity": "BACKEND NO INICIADO",
                "message": "La pantalla está lista para conectar con Yura.",
                "phase": "SIN_CONEXION",
                "content": "",
                "translation": "",
                "result": None,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

        state = current_robot.state
        state_info = {
            RobotStates.MENU: (
                "LISTA PARA ESCUCHAR",
                "Yura está en el menú principal."
            ),
            RobotStates.JUEGO: (
                "MODO JUEGO ACTIVO",
                "Yura está ejecutando el juego."
            ),
            RobotStates.CONVERSAR: (
                "MODO CONVERSACIÓN ACTIVO",
                "Yura está conversando."
            ),
            RobotStates.TRADUCIR: (
                "MODO TRADUCTOR ACTIVO",
                "Yura está traduciendo."
            ),
            RobotStates.SILENCIO: (
                "YURA EN SILENCIO",
                "Yura está esperando una orden para volver a hablar."
            ),
            RobotStates.SALIR: (
                "APAGANDO",
                "Yura está cerrando sus servicios."
            ),
        }
        activity, message = state_info.get(
            state,
            ("ACTIVIDAD DEL ROBOT", "Yura está trabajando.")
        )
        web_status = current_robot.get_web_status()

        return {
            "robot": "YURA",
            "state": state,
            "running": bool(current_robot.running),
            "activity": activity,
            "message": message,
            "phase": web_status.get("phase", "ESPERANDO"),
            "content": web_status.get("content", ""),
            "translation": web_status.get("translation", ""),
            "result": web_status.get("result"),
            "updated_at": web_status.get("updated_at") or datetime.now(timezone.utc).isoformat(),
        }


def start_robot():
    global robot

    with robot_lock:
        if robot is not None:
            return robot
        robot = BrainYura()
        backend_thread = threading.Thread(
            target=robot.loop_principal,
            name="yura-backend",
            daemon=True
        )
        backend_thread.start()
        return robot


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/status")
def status():
    return jsonify(_status_payload())


@app.get("/api/card")
def card_examples():
    return jsonify({"examples": CARD_EXAMPLES})


if __name__ == "__main__":
    start_robot()
    app.run(host="0.0.0.0", port=5000, debug=False)
