import sys, time
sys.path.insert(0, "/home/yura/Proyecto Yura /cerebro_yura/documentacion_pruebas/evidencias/02_frontend_datos")
from wd import S, setfake, APP
s = S()
try:
    s.size(1920, 1080)
    s.go(APP + "/")
    time.sleep(2)
    casos = [
        ("Tata", "Papá"), ("Wawa", "Niño"), ("Tata / Papa", "Papá / Papa"),
        ("Ñawi", "Ojo"), ("Allin p'unchay", "Buenos días"),
    ]
    for contenido, traduccion in casos:
        setfake(state="TRADUCIR", phase="HABLANDO", content=contenido, translation=traduccion)
        s.js("refreshStatus();")
        time.sleep(1)
        vis = s.js("return [document.querySelector('#content-main').textContent, document.querySelector('#content-translation').textContent, document.querySelector('#word-title').textContent, document.querySelector('#word-meaning').textContent]")
        print(f"enviado=({contenido!r}, {traduccion!r}) -> pantalla={vis}")
    setfake(state="TRADUCIR", phase="HABLANDO", content="Wawa", translation="Niño")
    s.js("refreshStatus();"); time.sleep(1)
    s.shot("/home/yura/Proyecto Yura /cerebro_yura/documentacion_pruebas/evidencias/08_despues_arreglo_wawa_ninio.png")
    setfake(state="MENU", phase="ESPERANDO", content="Allin p'unchay", translation="Buenos días")
    s.js("refreshStatus();"); time.sleep(1)
    print("tarjeta:", s.js("return [document.querySelector('#word-title').textContent, document.querySelector('#word-meaning').textContent]"))
finally:
    s.quit()
