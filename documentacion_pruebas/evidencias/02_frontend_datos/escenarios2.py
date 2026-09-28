import sys; sys.path.insert(0,'.')
from capturar import *
s=S()
base=dict(none=False, running=True, content="", translation="", result=None, fail_status=False, fail_card=False)
def F(**k): d=dict(base); d.update(k); return d
LARGO=("Rimaykullayki significa hola en quechua y se usa para saludar con respeto a una persona mayor; "
       "también puedes decir allin p'unchay por la mañana, allin sukhay por la tarde y allin tuta por la noche, "
       "así practicamos juntos cada día en la escuela.")
try:
    for (w,h) in [(1920,1080),(1024,600),(800,480),(390,844)]:
        tag=f"{w}x{h}"
        run(s, f"tam_{tag}_ESPERANDO", size=(w,h), fake=F(state="MENU", phase="ESPERANDO"))
        run(s, f"tam_{tag}_SIN_CONEXION", size=(w,h), fake=F(none=True))
        run(s, f"tam_{tag}_texto_largo", size=(w,h), fake=F(state="CONVERSAR", phase="HABLANDO", content="Ñuqaqa Yura kani, "+LARGO[:280], translation=""))
    run(s, "tam_390x844_ESPERANDO_pagina_completa", size=(390,844), fake=F(state="MENU", phase="ESPERANDO"), full=True)
    run(s, "tam_800x480_ESPERANDO_pagina_completa", size=(800,480), fake=F(state="MENU", phase="ESPERANDO"), full=True)
    run(s, "tam_1024x600_ESPERANDO_pagina_completa", size=(1024,600), fake=F(state="MENU", phase="ESPERANDO"), full=True)
finally:
    s.quit()
