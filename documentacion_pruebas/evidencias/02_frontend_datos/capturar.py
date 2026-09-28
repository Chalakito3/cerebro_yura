import sys, json, time; sys.path.insert(0,'.')
from wd import *
EV="/home/yura/Proyecto Yura /cerebro_yura/documentacion_pruebas/evidencias/"
INFO = r"""
const q=s=>document.querySelector(s);
const t=s=>q(s)?q(s).textContent:null;
const r=s=>{const e=q(s); if(!e) return null; const b=e.getBoundingClientRect(); return [Math.round(b.left),Math.round(b.top),Math.round(b.right),Math.round(b.bottom)];};
const inter=(a,b)=>a&&b&&!(a[2]<=b[0]||b[2]<=a[0]||a[3]<=b[1]||b[3]<=a[1]);
const vw=innerWidth, vh=innerHeight;
const fuera=[...document.querySelectorAll('.stage *')].filter(e=>{const b=e.getBoundingClientRect(); const cs=getComputedStyle(e); return b.width>0 && cs.visibility!=='hidden' && (b.right>vw+1||b.left<-1) && !e.closest('.orbit,.listening-waves,.energy-points') }).map(e=>e.className||e.id||e.tagName).slice(0,15);
const textoCortado=['#content-main','#word-title','#word-meaning','#word-example','#state','#message'].filter(s=>{const e=q(s);const b=e.getBoundingClientRect(); return b.right>vw||b.bottom>document.documentElement.scrollHeight;});
return {vp:[vw,vh], doc:[document.documentElement.scrollWidth, document.documentElement.scrollHeight], bodyOverflow:getComputedStyle(document.body).overflow,
 visual:document.body.dataset.visualState, phase:document.body.dataset.phase, cls:document.body.className,
 state:t('#state'), label:t('#state-label'), activity:t('#activity'), message:t('#message'), secondary:t('#secondary-status'),
 content:t('#content-main'), translation:t('#content-translation'), title:t('#word-title'), meaning:t('#word-meaning'), example:t('#word-example'), updated:t('#updated'),
 offline:q('#system-readout').classList.contains('system-offline'),
 rect:{robot:r('.robot-wrap'),status:r('.status-panel'),content:r('#content-main'),word:r('.word-card'),h1:r('#state'),footer:r('.footer'),topbar:r('.topbar')},
 solapes:{robot_status:inter(r('.robot-wrap'),r('.status-panel')), status_word:inter(r('.status-panel'),r('.word-card')), content_word:inter(r('#content-main'),r('.word-card')), robot_word:inter(r('.robot-wrap'),r('.word-card')), footer_word:inter(r('.footer'),r('.word-card')), center_brand:inter(r('.topbar-center'),r('.brand-mark'))||inter(r('.topbar-center'),r('#system-readout'))},
 fueraViewportX:fuera, textoCortado, h1font:getComputedStyle(q('#state')).fontSize, contentFont:getComputedStyle(q('#content-main')).fontSize, smallest:Math.min(...[...document.querySelectorAll('.stage *')].filter(e=>e.childNodes.length&&[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim())).map(e=>parseFloat(getComputedStyle(e).fontSize)))};
"""
def run(s, name, size=(1920,1080), fake=None, query="", wait=2.5, full=False):
    if fake is not None: setfake(**fake)
    s.size(*size)
    s.go(APP+"/"+query)
    time.sleep(wait)
    info = s.js(INFO)
    path = EV+f"02_{name}.png"
    s.shot(path, full=full)
    print(json.dumps({"captura":f"02_{name}.png","fake":fake,"query":query,**info}, ensure_ascii=False))
    return info
