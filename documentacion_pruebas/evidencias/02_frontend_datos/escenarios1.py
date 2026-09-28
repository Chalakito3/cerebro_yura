import sys; sys.path.insert(0,'.')
from capturar import *
s=S()
base=dict(none=False, running=True, content="", translation="", result=None, fail_status=False, fail_card=False)
def F(**k): d=dict(base); d.update(k); return d
try:
    for ph in ["ESPERANDO","ESCUCHANDO","PENSANDO","HABLANDO","CELEBRANDO","TRISTE"]:
        run(s, "fase_"+ph, fake=F(state="MENU", phase=ph))
    run(s, "fase_SILENCIOSA", fake=F(state="SILENCIO", phase="SILENCIOSA"))
    run(s, "fase_SIN_CONEXION_robot_None", fake=F(none=True))
    for st in ["MENU","JUEGO","CONVERSAR","TRADUCIR","SILENCIO","SALIR"]:
        run(s, "estado_"+st, fake=F(state=st, phase="ESPERANDO", running=(st!="SALIR")))
finally:
    s.quit()
