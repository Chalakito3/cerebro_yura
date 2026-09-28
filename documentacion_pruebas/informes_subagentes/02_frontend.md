# Informe 02: Frontend / visual (pantalla del robot YURA)

- Fecha: 2026-09-27
- Subagente 2: tester frontend / visual
- Qué se auditó: `web/templates/index.html`, `web/static/js/app.js`, `web/static/css/style.css`, `web/static/css/style-draft.css`, servidos por `web/app.py`.
- Cómo se probó: servidor Flask propio en el puerto 5051 (`evidencias/02_frontend_datos/servidor_falso.py`). Importa `web.app`, sustituye `web.app.robot` por un objeto falso (o lo deja en `None`) y añade en memoria una ruta de control `/__test/set`. No se modificó ningún archivo del proyecto. El navegador fue Firefox 147 en modo headless, manejado por WebDriver (geckodriver, puerto 4445, cliente propio `wd.py`). Así se pudo esperar a la primera consulta a `/api/status`, leer el DOM, fijar el tamaño de la ventana y hacer capturas de la ventana y de la página completa.
- Evidencias: 68 capturas `evidencias/02_*.png` y datos crudos en `evidencias/02_frontend_datos/` (`res1.jsonl`, `res2.jsonl`, `contenido.json`, `res_largo.jsonl`, `pipeline_in.json`, `pipeline_out.txt` y los scripts usados).
- Limitaciones:
  - Firefox headless no deja bajar de 500 px de ancho. Por eso las capturas `02_tam_500x844_*` muestran en realidad 500 px. El ancho real de 390x844 se probó con un iframe de 390x844 (`02_tam_390x844_iframe_*`).
  - No se pudo leer la consola JS, porque WebDriver no expone esos registros en Firefox. La ausencia de errores se verificó de forma indirecta (ver §8, FR-044).
- Al terminar se detuvieron el servidor y geckodriver. Los puertos 5051 y 4445 quedaron libres (verificado con `ss -ltn`: sin resultados).

---

## 1. Resumen ejecutivo

1. 🔴 **CRÍTICO: la pantalla muestra al estudiante texto equivocado o cortado.** La función `pickVisibleContent` / `extractQuechuaPhrase` (`app.js:44-121`) usa la expresión `[A-Za-z0-9'\s]+`, que se corta en la primera letra con tilde o ñ. Resultados verificados con respuestas reales del backend:
   - "Tata significa papá" se muestra como **"pap"**.
   - "Wawa significa niño, …" se muestra como **"ni"**.
   - "Ñaña significa hermana" se muestra como "hermana": sale la palabra en español y desaparece la quechua.
   - Una ambigüedad ("papa… Papa; papá… Tata") se muestra solo como "Papa".

   Este es el formato habitual de `conversacion.py:418` ("X significa Y").
2. 🟠 **ALTO: todas las traducciones del modo traductor salen con ": " delante** (": Tata", ": Wasi"). El error está en el backend, `main_robot.py:188` (regex `\s*:??\s*`, cuantificador perezoso), y se ve en la pantalla. Evidencia: `02_contenido_C06_dos_puntos_tata.png`.
3. 🟠 **ALTO: en pantallas de 7" (1024x600 y 800x480) el contenido principal ("YURA DICE") queda fuera de la vista.** Aparece en y≈775-791 px y el documento mide 862-875 px, así que hay que desplazarse. Con un texto largo el documento llega a 1092-1207 px. En 390x844 el `body` tiene `overflow:hidden`: el contenido y la tarjeta quedan cortados y el pie se superpone a la tarjeta. La tesis promete una "pantalla LCD 7" Touch" (§5.3.1 y §6.3).
4. 🟠 **ALTO: no hay ningún botón, enlace, formulario ni manejador táctil.** `grep` de `<button|<a |<form|<input|onclick|addEventListener|touch|click` en HTML/JS/CSS: 0 coincidencias. RF-01 pide capturar comandos "mediante botón/pantalla" y la tesis habla de "robot físico con pantalla táctil". La pantalla solo informa; todo se maneja por voz.
5. 🟠 **ALTO: la tarjeta "Significado" repite la palabra quechua** ("Significado: Rimaykullayki") en los 6 ejemplos. La tarjeta es fija (6 frases escritas en `web/app.py`) y no sale de `diccionario.db`: 4 de esas 6 frases no están en la BD. Casi siempre muestra "Rimaykullayki", sea cual sea la conversación. Cuando `/api/status` falla, muestra otra cosa: los textos por defecto del HTML ("Hola", "Hola, ¿cómo estás?").
6. 🟡 **MEDIO: la lista de bloqueo oculta contenido válido y lo cambia por "Rimaykullayki" (hola).** Ejemplos: al despedirse ("Hasta luego"), en la pregunta de juego "¿Cómo se dice, hasta luego…?" con respuesta "Tupananchiskama", o en "Estoy pensando en la palabra Allqu".
7. 🟡 **MEDIO: los estados SIN CONEXIÓN no son coherentes.**
   - Con el robot en `None`, "YURA DICE: Rimaykullayki" sigue visible.
   - Al apagar el servidor, el contenido vuelve a "Rimaykullayki" mientras la tarjeta se queda con la palabra anterior.
   - A 1920x1080 el título "SIN CONEXIÓN" se sale 12 px por la izquierda y la "C" queda cortada.
8. 🟡 **MEDIO: el modo del robot (MENU/JUEGO/CONVERSAR/TRADUCIR/SILENCIO/SALIR) casi no se ve.**
   - Solo aparece en una línea de 9,9 px marcada con `aria-hidden`.
   - El título grande dice siempre "YURA", salvo en SILENCIO.
   - `modeCopy` no se usa realmente.
   - SALIR ("APAGANDO") se ve igual que MENU.
9. 🟢 **APROBADO: no hay XSS.** Todo se escribe con `textContent`; `<script>`, `<img onerror>` y `<svg onload>` se muestran como texto y no se ejecutan (verificado).
10. 🟡 **MEDIO: el tema `?theme=soft` (`style-draft.css`) está inacabado y es ilegible.** El título "YURA" queda con contraste 1,01:1, el color amarillo con 1,24:1 y el gris con 2,22:1. Además, `style-draft.css` se descarga siempre (está enlazado sin condición en `index.html:9`), aunque solo tiene efecto con `?theme=soft`.

Resultado global de la pantalla: **REQUIERE CORRECCIÓN.** Funciona como monitor de estado en el televisor de 1920x1080. No cumple lo prometido para la pantalla táctil de 7" ni garantiza que el texto educativo mostrado sea correcto.

---

## 2. Inventario de la pantalla

| Zona | Elemento (id/clase) | Origen del dato | Observación |
|---|---|---|---|
| Barra superior | `.brand-mark` "YURA / ROBOT EDUCATIVO" | fijo en HTML | `aria-label` en un `div` sin `role` (no tiene efecto) |
| Barra superior | `.topbar-center` (5 rombos) | fijo | decorativo, `aria-hidden` |
| Barra superior | `#system-readout` "SISTEMA LOCAL" | fijo; el punto cambia con `status.running` | el texto no cambia nunca; solo cambia el color del punto |
| Héroe | `.orbit` ×3, `.energy-points`, `.listening-waves`, `.robot-halo`, `.energy-base` | CSS | animaciones infinitas; las órbitas pasan por encima del texto de estado (capturas 1920) |
| Héroe | `.robot` (antena, cabeza, ojos, boca, cuello, cuerpo) | CSS | `.arm-left/.arm-right` están en el HTML pero sin estilo en `style.css`: son invisibles salvo con `theme-soft` |
| Panel de estado | `.institution` "CULTURA QUECHUA BOLIVIANA" | fijo | 9,9 px |
| Panel de estado | `#state-label` (insignia) | `phaseCopy[phase].label` | con emoji |
| Panel de estado | `h1#state` | "YURA" / "SILENCIO" / "SIN CONEXIÓN" | 120 px a 1920 |
| Panel de estado | `#activity` | `phaseCopy[phase].label` (repite `#state-label`) | duplicado |
| Panel de estado | `#message` | `phaseCopy[phase].message` | ignora `status.message` del API |
| Panel de estado | `#secondary-status` | `status.activity` (texto del modo, en mayúsculas) | única indicación del modo; 9,9 px; `aria-hidden="true"` |
| Tarjeta de contenido | `#content-main` "YURA DICE" | `pickVisibleContent(status.content)` | contenido principal |
| Tarjeta de contenido | `#content-translation` | `pickVisibleContent(status.translation)` | se oculta si es igual al contenido. `hablar()` envía content = translation, así que solo se ve en el juego (resultado) |
| Tarjeta de ejemplo | `#word-title/-written/-pronunciation/-meaning/-example` | `/api/card` (6 ejemplos fijos en `web/app.py:15-64`) elegidos con `normalizeExampleKey` | valores por defecto del HTML: "Hola" / "Hola, ¿cómo estás?" |
| Pie | "YURA" y `#updated` "CONEXIÓN LOCAL · hh:mm" | `status.updated_at` | 9,3 px (8 px con ancho ≤ 800) |
| Datos del API sin usar | `status.message`, `status.result` (CORRECTO/INCORRECTO), `status.robot` | — | `result` nunca se muestra |

Ciclo de actualización (VERIFICADO): al cargar se ejecuta `loadWordExamples()`, después `refreshStatus()` y luego `setInterval(5000)`. Un cambio en el backend tardó entre 0,5 y 3 s en verse en las pruebas, con un máximo teórico de 5 s. Ver `fallos.py`, salidas "latencia" y "recuperacion" más abajo.

---

## 3. Tabla de botones y acciones

| Botón | Pantalla | Acción esperada | Acción real | Resultado | Estado |
|---|---|---|---|---|---|
| (ninguno) Botón o pantalla para "capturar comandos de voz… e iniciar evaluación" (RF-01) | `index.html` | Tocar la pantalla o un botón para empezar a hablar o evaluar | No existe: 0 `<button>`, 0 `<a>`, 0 `<form>`, 0 `<input>`, 0 `addEventListener`/`onclick`/`touch` (grep sobre HTML/JS/CSS) | La escucha la inicia el bucle de voz del backend, no la pantalla | 🟠 REQUIERE CORRECCIÓN (o corregir la tesis) |
| (ninguno) Elegir modo Juego / Conversar / Traducir | `index.html` | Selección táctil de modo (pantalla táctil 7") | Solo por voz | Hay CSS de una "tira de modos" (`.mode-strip`, `.mode`, `.mode-active`…) sin HTML: rastro de una versión con selector de modos | 🟠 REQUIERE CORRECCIÓN |
| (ninguno) Silencio / Apagar | `index.html` | Control visible de pausa o apagado | Solo por voz ("silencio", "apagar") | — | 🟡 OBSERVACIÓN |
| Enlaces a la plataforma web / app | `index.html` | Acceso a la plataforma docente | No hay enlaces | La plataforma Laravel (MENARWIL/yura-platform) es otra aplicación y no se ejecutó (⚫ NO VERIFICADO) | ⚫ NO VERIFICADO |

Conclusión: la pantalla del robot es **solo de salida**, una especie de "monitor de estado". Todo lo que la tesis asigna a la interacción táctil queda sin implementar en este frontend.

---

## 4. Pruebas visuales por estado y tamaño

### 4.1 Fases (`data-phase`), 1920x1080, robot falso en estado MENU (SILENCIOSA con SILENCIO)

| Fase | Captura | Insignia / mensaje mostrados (VERIFICADO en el DOM) | Efecto visual | Observaciones |
|---|---|---|---|---|
| ESPERANDO | `02_fase_ESPERANDO.png` | "🌟 ESPERANDO" / "🌟 Yura está listo para escuchar." | neutro | "listo" en masculino frente a "SILENCIOSA" / "LISTA PARA ESCUCHAR" en femenino |
| ESCUCHANDO | `02_fase_ESCUCHANDO.png` | "🎧 ESCUCHANDO" / "🎧 Escuchando con atención..." | ondas (`.listening-waves` opacity .45) | la línea del modo sigue diciendo "LISTA PARA ESCUCHAR" |
| PENSANDO | `02_fase_PENSANDO.png` | "🧠 PENSANDO" / "🧠 Estoy pensando qué significa." | órbitas más rápidas | — |
| HABLANDO | `02_fase_HABLANDO.png` | "🗣️ YURA HABLA" / "🗣️ Yura está respondiendo con alegría." | boca animada | — |
| CELEBRANDO | `02_fase_CELEBRANDO.png` | "🎉 CELEBRANDO" / "🎉 ¡Qué alegría! Vamos a aprender más." | halo dorado, antena amarilla | `result` "CORRECTO" no se muestra |
| TRISTE | `02_fase_TRISTE.png` | "😟 TRISTE" / "😟 Necesito un poco de calma." | boca invertida, halo rojizo | mensaje poco pedagógico tras una respuesta incorrecta; `result` "INCORRECTO" no se muestra |
| SILENCIOSA | `02_fase_SILENCIOSA.png` | "🤫 SILENCIOSA" / "🤫 Estoy en silencio y listo para volver." | órbitas lentas, antena gris | h1 = "SILENCIO" |
| SIN_CONEXION (robot `None`) | `02_fase_SIN_CONEXION_robot_None.png` | h1 "SIN CONEXIÓN", "⚠️ La conexión con Yura está caída.", línea del modo "BACKEND NO INICIADO" | robot en gris | h1 de x=-12 a 604 px: la "C" queda cortada. "YURA DICE: Rimaykullayki" sigue visible |

### 4.2 Estados del robot (`data-visual-state`), fase ESPERANDO, 1920x1080

| Estado | Captura | h1 | Línea de modo (9,9 px) | Diferencia visual | Observación |
|---|---|---|---|---|---|
| MENU | `02_estado_MENU.png` | YURA | LISTA PARA ESCUCHAR | ninguna | — |
| JUEGO | `02_estado_JUEGO.png` | YURA | MODO JUEGO ACTIVO | halo coral, insignia coral, ondas tenues | cambio sutil |
| CONVERSAR | `02_estado_CONVERSAR.png` | YURA | MODO CONVERSACIÓN ACTIVO | ondas tenues, sombra | cambio sutil |
| TRADUCIR | `02_estado_TRADUCIR.png` | YURA | MODO TRADUCTOR ACTIVO | halo e insignia dorados | cambio sutil |
| SILENCIO | `02_estado_SILENCIO.png` | SILENCIO | YURA EN SILENCIO | — | — |
| SALIR | `02_estado_SALIR.png` | YURA | APAGANDO | ninguna (no hay CSS para SALIR, `modeCopy` no tiene SALIR); solo el punto de "SISTEMA LOCAL" cambia de color por `running=false` | un apagado se ve como el menú |

### 4.3 Tamaños (estado ESPERANDO, SIN_CONEXION y texto largo)

| Tamaño | Capturas | Documento (ancho × alto) | Hallazgos (VERIFICADO con `getBoundingClientRect`) |
|---|---|---|---|
| 1920x1080 (TV) | `02_tam_1920x1080_ESPERANDO.png`, `_SIN_CONEXION.png`, `02_contenido_C14_largo300.png` | 1920×1080; con texto de 300 caracteres: 1920×1504 | Todo cabe con textos cortos. Gran zona vacía en el centro. Las órbitas cruzan el h1 y el mensaje. "SIN CONEXIÓN" se sale 12 px por la izquierda. Un texto de 300 caracteres llega a y=1457 y hay que desplazarse |
| 1024x600 (7") | `02_tam_1024x600_ESPERANDO.png`, `_pagina_completa.png`, `_SIN_CONEXION.png`, `_texto_largo_300.png`, `_texto_largo_300_pagina_completa.png` | 1024×875 (SIN_CONEXION 949; texto largo 1207) | **"YURA DICE" empieza en y=791, fuera de la vista.** En la primera pantalla solo se ven el robot, la tarjeta de ejemplo y el comienzo del h1 (cortado) |
| 800x480 (7") | `02_tam_800x480_ESPERANDO.png`, `_pagina_completa.png`, `_SIN_CONEXION.png`, `_texto_largo_300*.png` | 800×862 (SIN_CONEXION 919; texto largo 1092) | Solo se ven el robot y media tarjeta. El estado, el mensaje y el contenido quedan debajo del pliegue. `.hero` muestra una barra de desplazamiento horizontal blanca (media query `max-width:800px` con `overflow:auto`) |
| 390x844 (móvil, iframe real) | `02_tam_390x844_iframe_ESPERANDO.png`, `_SIN_CONEXION.png`, `_texto_largo_300.png` | 390×844 con `body overflow:hidden`; `.hero` con desplazamiento interno de 1508 px frente a 708 px visibles | El contenido principal queda cortado en el borde inferior, **la tarjeta de ejemplo queda fuera** (y=819-1167) y **el pie (y=794-824) se superpone a la tarjeta**. Se ven barras de desplazamiento blancas. La media query `orientation: landscape` no se aplica, así que el diseño es de una sola columna |
| 500x844 (mínimo de Firefox) | `02_tam_500x844_*.png` | igual que 390 | los mismos problemas; se conservan como referencia |

Nota: las capturas `02_tam_*_texto_largo_reducido_a_Rimaykullayki.png` no prueban desbordes. Se les envió "Ñuqaqa Yura kani, Rimaykullayki significa…" y el frontend lo redujo a "Rimaykullayki" (hallazgo FR-021). Para el desborde valen las capturas `_texto_largo_300`.

Otro hallazgo visual: `.robot { transform: scale(.78) }` en las media queries no tiene efecto, porque la animación `float` sobrescribe `transform` (`style.css:136` frente a `:371/:388`). El robot no se reduce en pantallas pequeñas (se ve a 800x480, donde ocupa 400 px de alto).

---

## 5. Contenido mostrado y seguridad (XSS)

### 5.1 Pruebas en el navegador (1920x1080, fase HABLANDO), `contenido.json`

| Caso | Entrada `content` / `translation` | `#content-main` mostrado | Tarjeta | Estado |
|---|---|---|---|---|
| C01 vacío | "" | Rimaykullayki (fallback) | Rimaykullayki | 🟡 muestra "hola" cuando no hay nada que decir |
| C02 ñ | "Ñuqaqa Yura kani" | Ñuqaqa Yura kani | Rimaykullayki | 🟢 la ñ se ve bien |
| C03 error | "No alcancé a entender esa frase" | igual, como contenido principal | Rimaykullayki | 🟡 error como contenido principal (el bloqueo solo cubre "no entendí") |
| C04 error | "No estoy seguro de cómo traducir esa frase" | igual | Rimaykullayki | 🟡 |
| C05 ambigua | "Tiene varios significados: papa… se dice Papa; papá… se dice Tata" | **Papa** | Rimaykullayki | 🔴 se pierde la segunda opción, que era el objetivo de la ambigüedad |
| C06 | ": Tata" (lo que produce el backend) | **: Tata** | Rimaykullayki | 🟠 |
| C07 | ": Allin p'unchay" | Allin p'unchay | Allin p'unchay | 🟢 (se "arregla" por coincidencia) |
| C08 | "Modo traductor" | Modo traductor | Rimaykullayki | 🟢 |
| C09 | "Hasta luego" | **Rimaykullayki** | Rimaykullayki | 🟠 al despedirse muestra el saludo |
| C10 | "No tengo una traducción segura de 'computadora'…" (82 car.) | igual, en 4 líneas | Rimaykullayki | 🟡 |
| C11 | "Wawa significa niño, y se usa así: Wawa pukllan" | **ni** | Rimaykullayki | 🔴 |
| C12 | "Hermana se dice Ñaña" | texto completo (la regex no admite Ñ) | Rimaykullayki | 🟡 |
| C13 | "Se dice Tata y significa papá" | **Tata y significa pap** | Rimaykullayki | 🔴 |
| C14 | texto de 300 caracteres | completo, 13 líneas, desborda la vista (doc 1504 px) | Rimaykullayki | 🟡 sin límite de líneas |
| C15 | "😀 Allinmi kashani 🎉🦙" | igual | Rimaykullayki | 🟢 |
| C16 | `<b>hola</b>` | `<b>hola</b>` literal (innerHTML `&lt;b&gt;…`) | — | 🟢 no se interpreta |
| C17 | `<script>window.__xss=1</script><img src=x onerror=…>` / `<svg onload=…>` | literal; `window.__xss` = null; 0 elementos hijo; 0 `<img>`; sin alerta | — | 🟢 sin XSS |
| C18 | "¿Cómo se dice, perro, en quechua?" | igual | Rimaykullayki | 🟢 |
| C19 | "¿Cómo se dice, hasta luego, en quechua?" / "Tupananchiskama" | **Rimaykullayki** y la traducción vacía | Rimaykullayki | 🟠 la pregunta de juego y su respuesta desaparecen |
| C20 | "¿Cómo se dice, agua, en quechua?" / "Uma" (CELEBRANDO) | pregunta + "Uma" | Rimaykullayki | 🟢 (el contenido de "Uma" lo revisa el informe de quechua) |
| C21 | "Allin p’unchay" (apóstrofo tipográfico) | igual | **Rimaykullayki** (no reconoce ’) | 🟡 |
| C22 | "Estoy pensando en la palabra Allqu" | **Rimaykullayki** | Rimaykullayki | 🟠 bloqueo por la subcadena "pensando" |
| C23 | "No digas rimaykullayki a tu perro, dile Allqu" | "rimaykullayki" (minúsculas, fuera de contexto) | Rimaykullayki | 🟡 |
| C24 | palabra de 79 letras sin espacios | cortada a la derecha (`overflow:hidden` de `.content-card`) | — | 🟡 BAJO |

### 5.2 Cadena completa backend → pantalla (`pipeline_out.txt`)

Se ejecutó el `_texto_visible` real del backend (`HardwareInterface._texto_visible`, sin crear `BrainYura`). Las funciones reales de `app.js` se evaluaron en Firefox sobre las frases que el backend genera de verdad.

| Frase del backend (archivo) | Tras `_texto_visible` | Pantalla | Estado |
|---|---|---|---|
| "En quechua se dice Tata, que significa papá. …" (`conversacion.py:414`) | "Tata, que significa papá" | **"pap"** | 🔴 |
| "Tata significa papá. …" (formato de `conversacion.py:418`) | "Tata significa papá" | **"pap"** | 🔴 |
| "Ñaña significa hermana." | igual | **"hermana"** (se pierde el quechua) | 🔴 |
| "En quechua, rojo se dice Puka. …" (`conversacion.py:403`) | "En quechua, rojo se dice Puka" | "Puka" | 🟢 |
| "Para decir buenos días en quechua, usa «Allin punchay». …" (`:408`) | "…usa «Allin punchay»" | "Allin punchay"; tarjeta "Allin p'unchay" (otra grafía) | 🟡 |
| "Practiquemos una palabra. En quechua se dice Allqu. …" (`conversacion.py:237`) | "Practiquemos una palabra" | "Practiquemos una palabra" (**la palabra a practicar no se muestra**) | 🟠 |
| "En quechua se dice: Tata. Padre." (`traductor.py:432`) | ": Tata" | ": Tata" | 🟠 |
| "En quechua se puede decir: Wasi." (`traductor.py:451`) | ": Wasi" | ": Wasi" | 🟠 |
| `describir_opciones` (papa/papá) | frase completa | "Papa" | 🔴 |
| `PRESENTACION_YURA` | "Ñuqaqa Yura kani" | igual | 🟢 |
| "Hasta luego. Tupananchiskama. …" | "Hasta luego" | "Rimaykullayki" | 🟠 |

### 5.3 Lógica de `app.js`

- `extractQuechuaPhrase` (`app.js:44-68`):
  - Tiene 6 patrones fijos, que son las frases de la tarjeta.
  - Después aplica `(?:en quechua se dice|se dice|significa)\s+([A-Za-z0-9'\s]+)`, que no admite á é í ó ú ñ ü ni ’, y que captura lo que va **después** de "significa", es decir, el español.
  - No distingue entre la palabra quechua y la española.
- `pickVisibleContent` (`app.js:88-121`):
  - La lista de bloqueo busca subcadenas ("esperando", "pensando", "hablando", "hasta luego", "tupananchiskama", "adios"). Oculta frases válidas y a la vez no bloquea "adiós" con tilde ni "no alcancé".
  - Cualquier texto que contenga "rimaykullayki" se reduce a esa palabra.
- `normalizeExampleKey` (`app.js:70-86`): solo reconoce las 6 frases de la tarjeta. Para cualquier otra cosa devuelve `rimaykullayki`, así que la tarjeta no acompaña a lo que se está enseñando.
- `renderStatus` (`app.js:153-195`):
  - Ignora `status.message` y `status.result`.
  - `modeCopy[...].message/.content/.translation` no se usan nunca. `.label` solo se usaría si faltara `status.activity`, algo que el backend siempre envía.
- Traducción: `hablar()` (`main_robot.py:205-210`) envía el mismo texto en `content` y `translation`. El JS oculta la traducción si es igual, así que la línea de traducción al español **solo aparece en el resultado del juego**.

### 5.4 Fallos de red

| Caso | Captura | Resultado (VERIFICADO) |
|---|---|---|
| `/api/card` → HTTP 500, contenido "Allin tuta" | `02_falla_api_card.png` | la tarjeta cae a FALLBACK_CARD (Rimaykullayki) aunque el contenido es "Allin tuta" (con `/api/card` correcto: `02_card_ok_allin_tuta.png` muestra "Allin tuta") |
| `/api/status` → HTTP 500 | `02_falla_api_status_500.png` | h1 "SIN CONEXIÓN", "ESPERANDO AL BACKEND", "CONEXIÓN LOCAL · SIN DATOS"; **la tarjeta muestra los valores por defecto del HTML: "Significado: Hola", "Ejemplo: Hola, ¿cómo estás?"**; contenido "Rimaykullayki"; h1 fuera por la izquierda (-12 px) |
| Recuperación (se quita la falla con la página abierta) | `02_recuperacion_tras_falla.png` | a los 3 s pasa a "🧠 PENSANDO | Allin p'unchay" 🟢 |
| Servidor apagado con la página abierta | `02_antes_de_apagar_servidor.png`, `02_servidor_apagado.png` | a los 3 s: "SIN CONEXIÓN | Rimaykullayki"; la tarjeta **se queda en "Allin tuta"** (incoherente); la traducción "Buenas noches" desaparece 🟡 |
| Robot `None` (backend no iniciado) | `02_fase_SIN_CONEXION_robot_None.png` | texto distinto al de la caída de red ("⚠️ La conexión con Yura está caída." frente a "La pantalla no puede consultar el estado de Yura."); no hay reintento visible ni hora del último dato 🟡 |

Salidas registradas en `fallos.py` y `apagado.py` (copiadas de la ejecución):

```
recuperacion [[0.0,"SIN CONEXIÓN | Rimaykullayki"],[1.0,…],[2.0,…],[3.0,"🧠 PENSANDO | Allin p'unchay"],…]
latencia     [[0.0,"PENSANDO | "],[0.5,"CELEBRANDO | Allqu"],…]
servidor apagado: [2.0,"YURA | Allin tuta | Allin tuta | CONEXIÓN LOCAL · 00:20"],[3.0,"SIN CONEXIÓN | Rimaykullayki | Allin tuta | CONEXIÓN LOCAL · SIN DATOS"]
```

---

## 6. Accesibilidad

| Aspecto | Evidencia | Estado |
|---|---|---|
| Idioma | `<html lang="es">`; el contenido quechua no lleva `lang="qu"` (un lector de pantalla lo pronuncia como español) | 🟡 |
| `aria-live` | `aria-live="polite"` sobre todo `<main>` (`index.html:12`). Cada 5 s se reescribe `textContent` de 6 nodos aunque el valor no cambie (`app.js:160-166`, `:181`). Esto puede provocar anuncios repetidos. ⚫ NO VERIFICADO con lector de pantalla real | 🟡 |
| Información oculta | `#secondary-status`, la única indicación del modo, está dentro de `aria-hidden="true"` (`index.html:83`) | 🟡 |
| `aria-label` | en `div` sin `role` (`.brand-mark`, `.robot`): no tiene efecto | 🟡 BAJO |
| Emojis en las etiquetas | "🌟 ESPERANDO", "⚠️ SIN CONEXIÓN": el lector lee el nombre del emoji | 🟡 BAJO |
| Imágenes | no hay `<img>`: no se necesitan textos alternativos | 🟢 |
| Contraste (tema oscuro, sobre #071419 / #162b2b) | ink 16,6/13,2; muted 7,4/5,9; aqua 11,9/9,5; coral 9,0/7,2; yellow 13,3/10,6; gold 10,3/8,2; mint 16,4/13,0; red-soft 7,1/5,7 | 🟢 todos ≥ 4,5:1 (AA) |
| Contraste (`theme-soft`, sobre #f4f0ea) | h1 #e9f4ef **1,01**; institución amarilla **1,24**; coral **1,83**; mensaje muted **2,22**; encabezado #7d8e76 3,08; #557688 4,27; contenido #3d6f7c 4,92 | 🔴 en el tema claro (no activo por defecto) |
| Tamaño de letra | mínimo 8,8 px (subtítulo de marca, 0,55rem); 9,3-9,9 px en etiquetas (INSTITUCIÓN, ESCRITURA/PRONUNCIACIÓN…, línea de modo, pie); 8 px en el pie con ancho ≤ 800. Ilegible a distancia en un televisor y para niños | 🟡 |
| Movimiento | 10+ animaciones infinitas; no hay `@media (prefers-reduced-motion)` (grep: 0) | 🟡 BAJO |
| Foco / teclado | no hay nada que se pueda enfocar (no hay controles) | ⚫ no aplica |

---

## 7. Limpieza (CSS/HTML sin uso)

- **Clases CSS sin uso en `style.css`**. Se verificó cada selector de clase contra `index.html` y `app.js` y se **confirman las 9 del contexto y aparece 1 más**: `detail-copy`, `detail-kicker`, `detail-stats`, `mode`, `mode-active`, `mode-detail`, `mode-index`, `mode-label`, `mode-strip`, `progress-stat` (10 en total). La regla de media query de `.mode-strip`/`.mode-detail` también es código muerto.
- **`style-draft.css`**:
  - Se descarga siempre (`index.html:9`, sin la versión `v=` que sí llevan `style.css` y `app.js`).
  - Todas sus reglas dependen de `body.theme-soft`, que solo se activa con `?theme=soft` y que nada del proyecto usa.
  - El selector `.orbits` no existe.
  - Resultado visual: `02_theme_soft_ESPERANDO.png` y `02_theme_soft_SIN_CONEXION.png` (h1 invisible, tarjeta oscura sobre fondo claro). Comparar con `02_fase_ESPERANDO.png`.
  - Clasificación: borrador sin terminar, 🟡.
- **Elementos del HTML sin función o invisibles**: `.arm-left` y `.arm-right` (sin estilo fuera de `theme-soft`), `.topbar-center` (5 rombos), `.hero::before/::after` (rejillas decorativas), `.energy-points`.
- **Duplicados**: `#activity` repite `#state-label`; `.message { display:none }` (`style.css:175`) se anula después con `.message { display:block }` (`:318`); `.word-panel`, `.status-panel` y `.content-card` se redefinen 2-3 veces en el mismo archivo.
- **Código JS sin uso**: `modeCopy` (`.message`, `.content`, `.translation`); `status.message` y `status.result` del API.
- **Textos por defecto del HTML que no coinciden con los datos**: `#word-meaning` "Hola" y `#word-example` "Hola, ¿cómo estás?" (`index.html:109,113`), frente a los datos del API ("Rimaykullayki" / "Rimaykullayki, imaynalla kashanki?"). Se ven al cargar y cuando falla `/api/status`. `#activity`/`#message` "ESPERANDO" y "SISTEMA EN ESPERA" se sustituyen enseguida.
- **Tarjetas fijas `CARD_EXAMPLES` (`web/app.py:15-64`)**:
  - `meaning` repite la palabra quechua en los 6 casos (confirmado).
  - Solo "Allin tuta" y "Allin p'unchay" (en la BD como "Allin punchay") están en `diccionario.db`, en `nivel1_saludos`. "Rimaykullayki", "Yusulpayki", "Anchata munakuyki" e "Imaynalla kachkanki" (en la BD solo "Imaynalla") no están (consulta de solo lectura).
  - El ejemplo "Rimaykullayki, imaynalla **kashanki**?" usa otra forma que el título "Imaynalla **kachkanki**": variación dialectal, ⚫ requiere revisión de un hablante de Cochabamba.
  - Pronunciaciones dudosas ("I-ma-ya-lla", "Yu-su-lpay-ki"): ⚫ requieren revisión de un hablante.
- **Inconsistencia de género**: "Yura está listo" frente a "SILENCIOSA" y "LISTA PARA ESCUCHAR".

---

## 8. Matriz de pruebas

| ID | Módulo | Prueba | Entrada | Esperado | Obtenido | Estado | Evidencia |
|---|---|---|---|---|---|---|---|
| YURA-FR-001 | Estados | Fase ESPERANDO | phase=ESPERANDO | insignia y mensaje de espera | "🌟 ESPERANDO" / "Yura está listo…" | 🟢 | 02_fase_ESPERANDO.png |
| YURA-FR-002 | Estados | Fase ESCUCHANDO | phase=ESCUCHANDO | indicador de escucha | "🎧 ESCUCHANDO" + ondas; la línea de modo dice "LISTA PARA ESCUCHAR" | 🟢 | 02_fase_ESCUCHANDO.png |
| YURA-FR-003 | Estados | Fase PENSANDO | phase=PENSANDO | indicador de proceso | "🧠 PENSANDO", órbitas rápidas | 🟢 | 02_fase_PENSANDO.png |
| YURA-FR-004 | Estados | Fase HABLANDO | phase=HABLANDO | boca animada | "🗣️ YURA HABLA", boca animada | 🟢 | 02_fase_HABLANDO.png |
| YURA-FR-005 | Estados | Fase CELEBRANDO | phase=CELEBRANDO, result=CORRECTO | celebración y resultado | celebración; `result` no se muestra | 🟡 | 02_fase_CELEBRANDO.png |
| YURA-FR-006 | Estados | Fase TRISTE | phase=TRISTE | retroalimentación de error | "Necesito un poco de calma"; `result` no se muestra | 🟡 | 02_fase_TRISTE.png |
| YURA-FR-007 | Estados | Fase SILENCIOSA | SILENCIO/SILENCIOSA | modo silencio | h1 "SILENCIO", insignia gris | 🟢 | 02_fase_SILENCIOSA.png |
| YURA-FR-008 | Estados | SIN_CONEXION (robot None) | robot=None | aviso claro y sin contenido engañoso | aviso correcto; "YURA DICE: Rimaykullayki" visible; h1 cortado (x=-12) | 🟠 | 02_fase_SIN_CONEXION_robot_None.png |
| YURA-FR-009 | Estados | Estado MENU | state=MENU | modo visible | solo "LISTA PARA ESCUCHAR" de 9,9 px | 🟡 | 02_estado_MENU.png |
| YURA-FR-010 | Estados | Estado JUEGO | state=JUEGO | modo visible | "MODO JUEGO ACTIVO" de 9,9 px, halo coral | 🟡 | 02_estado_JUEGO.png |
| YURA-FR-011 | Estados | Estado CONVERSAR | state=CONVERSAR | modo visible | 9,9 px, cambio sutil | 🟡 | 02_estado_CONVERSAR.png |
| YURA-FR-012 | Estados | Estado TRADUCIR | state=TRADUCIR | modo visible | 9,9 px, halo dorado | 🟡 | 02_estado_TRADUCIR.png |
| YURA-FR-013 | Estados | Estado SILENCIO | state=SILENCIO | modo silencio | h1 "SILENCIO" | 🟢 | 02_estado_SILENCIO.png |
| YURA-FR-014 | Estados | Estado SALIR | state=SALIR, running=false | aviso de apagado | igual que MENU; solo "APAGANDO" de 9,9 px | 🟡 | 02_estado_SALIR.png |
| YURA-FR-015 | Tamaños | TV 1920x1080 | ESPERANDO | todo visible, sin solapes | todo visible; órbitas sobre el texto; centro vacío | 🟢 | 02_tam_1920x1080_ESPERANDO.png |
| YURA-FR-016 | Tamaños | 7" 1024x600 | ESPERANDO | todo visible sin desplazamiento | doc 875 px; "YURA DICE" en y=791, fuera de la vista | 🟠 | 02_tam_1024x600_ESPERANDO(_pagina_completa).png |
| YURA-FR-017 | Tamaños | 7" 800x480 | ESPERANDO | todo visible | doc 862 px; estado y contenido fuera de la vista; barra de desplazamiento blanca | 🟠 | 02_tam_800x480_ESPERANDO(_pagina_completa).png |
| YURA-FR-018 | Tamaños | Móvil 390x844 | ESPERANDO (iframe) | una columna legible y con desplazamiento | `body` overflow hidden; tarjeta fuera; pie encima de la tarjeta | 🟠 | 02_tam_390x844_iframe_ESPERANDO.png |
| YURA-FR-019 | Tamaños | Texto de 300 caracteres a 7" | content=300 car. | recorte o ajuste | doc 1207 px (1024x600) y 1092 px (800x480) | 🟠 | 02_tam_1024x600_texto_largo_300*.png, 02_tam_800x480_texto_largo_300*.png |
| YURA-FR-020 | Tamaños | SIN CONEXIÓN en móvil | robot None, 390 | legible | el contenido queda cortado | 🟠 | 02_tam_390x844_iframe_SIN_CONEXION.png |
| YURA-FR-021 | Contenido | Texto que contiene "Rimaykullayki" | "Ñuqaqa Yura kani, Rimaykullayki significa…" | texto completo | se reduce a "Rimaykullayki" | 🟠 | 02_tam_1920x1080_texto_largo_reducido_a_Rimaykullayki.png |
| YURA-FR-022 | Contenido | "X significa Y" con tilde | "Tata significa papá" | "Tata" (y "papá" como traducción) | "pap" | 🔴 | pipeline_out.txt |
| YURA-FR-023 | Contenido | "significa" + ñ | "Wawa significa niño…" | Wawa / niño | "ni" | 🔴 | 02_contenido_C11_significa.png |
| YURA-FR-024 | Contenido | "se dice" + tilde | "Se dice Tata y significa papá" | Tata | "Tata y significa pap" | 🔴 | 02_contenido_C13_se_dice_tilde.png |
| YURA-FR-025 | Contenido | Ambigüedad | describir_opciones papa/papá | las dos opciones | "Papa" | 🔴 | 02_contenido_C05_ambiguo.png |
| YURA-FR-026 | Contenido | Traductor BD local | "En quechua se dice: Tata. Padre." | "Tata" | ": Tata" | 🟠 | 02_contenido_C06_dos_puntos_tata.png, pipeline_out.txt |
| YURA-FR-027 | Contenido | Práctica de vocabulario | "Practiquemos una palabra. En quechua se dice Allqu…" | "Allqu" | "Practiquemos una palabra" | 🟠 | pipeline_out.txt |
| YURA-FR-028 | Contenido | Despedida | "Hasta luego" | "Hasta luego / Tupananchiskama" | "Rimaykullayki" | 🟠 | 02_contenido_C09_hasta_luego.png |
| YURA-FR-029 | Contenido | Pregunta de juego con palabra bloqueada | "¿Cómo se dice, hasta luego…?" / "Tupananchiskama" | pregunta + respuesta | "Rimaykullayki", sin respuesta | 🟠 | 02_contenido_C19_juego_hasta_luego.png |
| YURA-FR-030 | Contenido | Falso positivo del bloqueo | "Estoy pensando en la palabra Allqu" | "Allqu" o la frase | "Rimaykullayki" | 🟠 | 02_contenido_C22_palabra_bloqueada.png |
| YURA-FR-031 | Contenido | Mensaje de error | "No alcancé a entender esa frase" | aviso secundario | contenido principal grande | 🟡 | 02_contenido_C03_error_no_alcance.png |
| YURA-FR-032 | Contenido | ñ | "Ñuqaqa Yura kani" | se ve la Ñ | correcto | 🟢 | 02_contenido_C02_presentacion.png |
| YURA-FR-033 | Contenido | Apóstrofo recto | "Allin p'unchay" | tarjeta correspondiente | correcto | 🟢 | 02_contenido_C07_dos_puntos_allin.png |
| YURA-FR-034 | Contenido | Apóstrofo tipográfico | "Allin p’unchay" | tarjeta correspondiente | tarjeta "Rimaykullayki" | 🟡 | 02_contenido_C21_apostrofo_tipografico.png |
| YURA-FR-035 | Contenido | Emojis | "😀 Allinmi kashani 🎉🦙" | se muestran | correcto | 🟢 | 02_contenido_C15_emoji.png |
| YURA-FR-036 | Contenido | Palabra muy larga | 79 letras | salto de línea | cortada a la derecha | 🟡 | 02_contenido_C24_palabra_sin_espacios.png |
| YURA-FR-037 | Seguridad | HTML en el contenido | `<b>hola</b>` | literal | literal (`&lt;b&gt;`) | 🟢 | 02_contenido_C16_html_b.png |
| YURA-FR-038 | Seguridad | XSS | `<script>`, `<img onerror>`, `<svg onload>` | no se ejecuta | `__xss`=null, 0 nodos, sin alerta | 🟢 | 02_contenido_C17_script.png |
| YURA-FR-039 | Tarjeta | Campo Significado | cualquier contenido | significado en español | repite el quechua ("Rimaykullayki") | 🟠 | 02_fase_ESPERANDO.png |
| YURA-FR-040 | Tarjeta | Tarjeta acorde al contenido | "Puka", "Allqu", "Tata"… | tarjeta de esa palabra | siempre "Rimaykullayki" (solo 6 frases fijas) | 🟠 | contenido.json, pipeline_out.txt |
| YURA-FR-041 | Red | Falla `/api/card` | HTTP 500, "Allin tuta" | tarjeta de "Allin tuta" o aviso | "Rimaykullayki" | 🟡 | 02_falla_api_card.png |
| YURA-FR-042 | Red | Falla `/api/status` | HTTP 500 | estado sin conexión coherente | aviso correcto; tarjeta "Significado: Hola"; contenido "Rimaykullayki"; h1 cortado | 🟡 | 02_falla_api_status_500.png |
| YURA-FR-043 | Red | Recuperación y latencia | se quita la falla / cambio de fase | ≤ 2,5 s (RNF-01) | 0,5-3 s medido; hasta 5 s por diseño (sondeo cada 5 s) | 🟡 | 02_recuperacion_tras_falla.png, salida de fallos.py |
| YURA-FR-044 | JS | Errores de ejecución | 68 cargas en 12 escenarios | sin excepciones | en todas las cargas el JS completó `renderStatus` (etiquetas con emoji, `data-phase` correcto). No se pudo leer la consola directamente | 🟢 (indirecto) | res1.jsonl, res2.jsonl |
| YURA-FR-045 | Red | Servidor apagado con la página abierta | kill del servidor | aviso coherente | aviso a los 3 s; la tarjeta se queda con "Allin tuta" y el contenido pasa a "Rimaykullayki" | 🟡 | 02_servidor_apagado.png |
| YURA-FR-046 | Botones | Existencia de controles | grep + DOM | botón/pantalla táctil (RF-01) | 0 controles interactivos | 🟠 | §3 |
| YURA-FR-047 | Accesibilidad | Contraste del tema oscuro | colores de `:root` | ≥ 4,5:1 | 5,67-16,61:1 | 🟢 | §6 |
| YURA-FR-048 | Accesibilidad | Contraste de `theme-soft` | `?theme=soft` | ≥ 4,5:1 | 1,01-4,92:1 | 🔴 (tema inactivo) | 02_theme_soft_ESPERANDO.png |
| YURA-FR-049 | Accesibilidad | Tamaños mínimos de letra | DOM | ≥ 12-14 px para lectura a distancia | 8-9,9 px en etiquetas, modo y pie | 🟡 | res2.jsonl ("smallest") |
| YURA-FR-050 | Accesibilidad | Modo visible para lector de pantalla | `#secondary-status` | anunciable | `aria-hidden="true"` | 🟡 | index.html:83 |
| YURA-FR-051 | Limpieza | CSS sin uso | selectores frente a HTML/JS | 0 | 10 clases en style.css + `.orbits` en style-draft | 🟡 | §7 |
| YURA-FR-052 | Limpieza | style-draft.css | carga sin `?theme` | no cargarse o estar terminado | se descarga siempre; tema inacabado | 🟡 | 02_theme_soft_*.png |
| YURA-FR-053 | Limpieza | Textos por defecto del HTML | falla o carga inicial | coherentes con el API | "Hola", "Hola, ¿cómo estás?" frente a "Rimaykullayki" | 🟡 | 02_falla_api_status_500.png |
| YURA-FR-054 | Visual | Escala del robot en pantallas pequeñas | 800x480 | robot reducido (scale .78) | la animación `float` anula el `transform`; sin reducción | 🟡 | 02_tam_800x480_ESPERANDO.png |
| YURA-FR-055 | Quechua | Frases de la tarjeta frente a la BD | CARD_EXAMPLES | frases del diccionario | 4/6 no están en la BD; mezcla kashanki/kachkanki | ⚫ requiere revisión de un hablante | §7 |

Totales (55 pruebas): 🟢 14 · 🟡 20 · 🟠 15 · 🔴 5 (4 de contenido + 1 del tema inactivo) · ⚫ 1.

---

## 9. Problemas con prioridad y propuesta (sin aplicar)

| # | Prioridad | Problema | Propuesta |
|---|---|---|---|
| P1 | CRÍTICO | `extractQuechuaPhrase`/`pickVisibleContent` corta o cambia el texto educativo ("pap", "ni", "hermana", "Papa") | Quitar la extracción heurística del frontend. Que el backend envíe campos estructurados (`quechua`, `espanol`, `texto`) en `_set_web_status` y que el JS los muestre tal cual. Si se mantiene alguna regex, usar clases Unicode (`\p{L}` con la bandera `u`) y no capturar lo que va después de "significa" |
| P2 | ALTO | ": Tata" / ": Wasi" en todas las traducciones (`main_robot.py:188`, `:??` perezoso) | Cambiar a `\s*:?\s*` o limpiar con `lstrip(": ")`; añadir una prueba unitaria de `_texto_visible` |
| P3 | ALTO | En 7" (1024x600, 800x480) y en móvil el contenido principal queda fuera de la vista o cortado | Diseño específico para 800x480 y 1024x600: contenido principal arriba o al centro, robot más pequeño (sacar `scale` de la animación `float` o usar `width`), h1 más pequeño, tarjeta opcional; quitar `overflow:hidden` del `body` en vertical; probar en la pantalla real |
| P4 | ALTO | No hay botones ni interacción táctil (RF-01, "pantalla táctil 7"") | Decidir: (a) añadir controles táctiles (hablar/escuchar, elegir modo, silencio) que llamen a nuevos endpoints POST, o (b) corregir la tesis para declarar que el control es solo por voz |
| P5 | ALTO | Tarjeta "Significado" con la palabra quechua; tarjeta fija de 6 frases, 4 fuera de la BD | Generar la tarjeta desde `diccionario.db` (palabra_frase, traduccion, significado) para la palabra que se está enseñando; hasta entonces, corregir `meaning` en `CARD_EXAMPLES` y validar con un hablante |
| P6 | MEDIO | La lista de bloqueo oculta despedidas, preguntas de juego y frases con "pensando" | Eliminar el bloqueo por subcadenas; que el backend decida qué contenido mostrar (campo `mostrar` o `tipo`: error/aviso/enseñanza) |
| P7 | MEDIO | SIN CONEXIÓN incoherente (contenido "Rimaykullayki", tarjeta obsoleta o "Hola", h1 cortado) | En desconexión, vaciar o ocultar el contenido y la tarjeta; h1 con `overflow-wrap`/tamaño menor; mostrar la hora del último dato recibido |
| P8 | MEDIO | Modo casi invisible; SALIR igual que MENU; `status.result` sin mostrar | Mostrar el modo en grande (usar `modeCopy`), estilo propio para SALIR, mostrar CORRECTO/INCORRECTO en el juego; revisar el mensaje de TRISTE para niños |
| P9 | MEDIO | Errores del sistema como contenido principal | Mostrarlos en `#message` con otro estilo, no en "YURA DICE" |
| P10 | MEDIO | Sondeo cada 5 s frente a RNF-01 (2,5 s) | Bajar el intervalo a 1 s o usar SSE/WebSocket |
| P11 | MEDIO | `style-draft.css` y `theme-soft` inacabados, con contraste de 1,01:1 | Borrar el borrador o terminarlo; como mínimo, no enlazarlo sin condición |
| P12 | BAJO | Accesibilidad: `aria-live` sobre todo `<main>`, reescrituras cada 5 s, `aria-hidden` en el modo, sin `lang="qu"`, letras de 8-10 px, sin `prefers-reduced-motion` | `aria-live` solo en `#content-main`; actualizar solo si el valor cambia; `lang="qu"` en el contenido quechua; mínimo 14 px; respetar `prefers-reduced-motion` |
| P13 | BAJO | CSS muerto (10 clases + `.orbits`), reglas duplicadas, `modeCopy` sin uso, brazos sin estilo, textos por defecto "Hola" | Limpieza en un solo commit |
| P14 | BAJO | Género inconsistente ("listo" / "SILENCIOSA" / "LISTA") | Unificar a femenino ("Yura está lista") |
