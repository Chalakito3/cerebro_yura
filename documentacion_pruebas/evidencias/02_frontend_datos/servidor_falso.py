"""Servidor de prueba: importa web.app sin crear BrainYura y usa un robot falso."""
import sys, threading
from datetime import datetime, timezone
ROOT = "/home/yura/Proyecto Yura /cerebro_yura"
sys.path.insert(0, ROOT)
import web.app as webapp
from flask import request, jsonify, abort

class RobotFalso:
    def __init__(self):
        self.state = "MENU"
        self.running = True
        self.ws = {"phase": "ESPERANDO", "content": "", "translation": "", "result": None, "updated_at": None}
        # Modo docente (página /ensenar): inactivo en el robot falso.
        self.pedido_docente = threading.Event()
        self.ensenanza = {"estado": "inactivo"}
    def get_web_status(self):
        d = dict(self.ws); d["updated_at"] = datetime.now(timezone.utc).isoformat(); return d

FALSO = RobotFalso()
webapp.robot = FALSO
FALLA = {"status": False, "card": False}

@webapp.app.before_request
def _fallas():
    if FALLA["status"] and request.path == "/api/status":
        abort(500)
    if FALLA["card"] and request.path == "/api/card":
        abort(500)

@webapp.app.post("/__test/set")
def _set():
    d = request.get_json(force=True)
    if d.get("none"):
        webapp.robot = None
    else:
        webapp.robot = FALSO
    for k in ("state", "running"):
        if k in d: setattr(FALSO, k, d[k])
    for k in ("phase", "content", "translation", "result"):
        if k in d: FALSO.ws[k] = d[k]
    for k in ("fail_status", "fail_card"):
        if k in d: FALLA[k[5:]] = d[k]
    return jsonify(ok=True)

if __name__ == "__main__":
    webapp.app.run(host="127.0.0.1", port=5051, debug=False)
