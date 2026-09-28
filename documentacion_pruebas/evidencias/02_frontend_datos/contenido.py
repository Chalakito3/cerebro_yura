import sys, json, time; sys.path.insert(0,'.')
from capturar import *
s=S(); s.size(1920,1080)
base=dict(none=False, running=True, state="CONVERSAR", phase="HABLANDO", content="", translation="", result=None, fail_status=False, fail_card=False)
LARGO300=("Hoy vamos a practicar los colores del arco iris, los números del uno al diez y los nombres de los animales de la granja; "
          "después repasaremos las partes del cuerpo y las frutas del mercado, para que al final de la semana puedas presentarte "
          "con tu nombre, tu edad y tu comida favorita delante de toda la clase.")
casos = [
 ("C01_vacio", "", ""),
 ("C02_presentacion", "Ñuqaqa Yura kani", "Ñuqaqa Yura kani"),
 ("C03_error_no_alcance", "No alcancé a entender esa frase", "No alcancé a entender esa frase"),
 ("C04_error_no_seguro", "No estoy seguro de cómo traducir esa frase", "No estoy seguro de cómo traducir esa frase"),
 ("C05_ambiguo", "Tiene varios significados: papa, de alimentos, se dice Papa; papá, de familia, se dice Tata", "Tiene varios significados: papa, de alimentos, se dice Papa; papá, de familia, se dice Tata"),
 ("C06_dos_puntos_tata", ": Tata", ": Tata"),
 ("C07_dos_puntos_allin", ": Allin p'unchay", ": Allin p'unchay"),
 ("C08_modo_traductor", "Modo traductor", "Modo traductor"),
 ("C09_hasta_luego", "Hasta luego", "Hasta luego"),
 ("C10_sin_traduccion", "No tengo una traducción segura de 'computadora' en mi vocabulario local todavía", ""),
 ("C11_significa", "Wawa significa niño, y se usa así: Wawa pukllan", ""),
 ("C12_se_dice_enie", "Hermana se dice Ñaña", ""),
 ("C13_se_dice_tilde", "Se dice Tata y significa papá", ""),
 ("C14_largo300", LARGO300, ""),
 ("C15_emoji", "😀 Allinmi kashani 🎉🦙", ""),
 ("C16_html_b", "<b>hola</b>", ""),
 ("C17_script", "<script>window.__xss=1</script><img src=x onerror=\"window.__xss=2\">", "<svg onload=\"window.__xss=3\">"),
 ("C18_juego_pregunta", "¿Cómo se dice, perro, en quechua?", ""),
 ("C19_juego_hasta_luego", "¿Cómo se dice, hasta luego, en quechua?", "Tupananchiskama"),
 ("C20_juego_resultado", "¿Cómo se dice, agua, en quechua?", "Uma"),
 ("C21_apostrofo_tipografico", "Allin p’unchay", ""),
 ("C22_palabra_bloqueada", "Estoy pensando en la palabra Allqu", ""),
 ("C23_rimay_en_frase", "No digas rimaykullayki a tu perro, dile Allqu", ""),
 ("C24_palabra_sin_espacios", "Antidesestablecimientarianamentequechuaqhichwasimirimanakuypaqyanapakuqkunawan", ""),
]
out={}
for name, content, trans in casos:
    ph = "CELEBRANDO" if name=="C20_juego_resultado" else "HABLANDO"
    d=dict(base); d.update(content=content, translation=trans, phase=ph)
    setfake(**d)
    s.go(APP+"/")
    time.sleep(2.2)
    info = s.js(INFO)
    extra = s.js("""return {html:document.querySelector('#content-main').innerHTML, thtml:document.querySelector('#content-translation').innerHTML,
       hijos:document.querySelectorAll('#content-main *, #content-translation *').length, xss:window.__xss||null,
       scripts:document.scripts.length, imgs:document.images.length}""")
    try:
        alerta = call("GET", f"/session/{s.id}/alert/text")
    except Exception as e:
        alerta = None
    s.shot(EV+f"02_contenido_{name}.png")
    out[name]={"entrada":[content,trans], "pantalla":info["content"], "traduccion":info["translation"], "tarjeta":[info["title"],info["meaning"],info["example"]], "contentRect":info["rect"]["content"], "statusRect":info["rect"]["status"], "doc":info["doc"], "fuera":info["fueraViewportX"], **extra, "alerta":alerta}
    print(name, json.dumps(out[name], ensure_ascii=False))
s.quit()
json.dump(out, open("contenido.json","w"), ensure_ascii=False, indent=1)
