# Registro de cambios — Ciclo 2 (web y base de datos SQLite)

**Fecha:** 27/09/2026 · **Alcance:** cerebro de Yura (web + SQLite) · **Pruebas:** 109 → **137**, todas pasan.

**Decisiones del equipo en este ciclo:** aplicar las 70 correcciones confirmadas del documento 002; dejar las 12 palabras sin fuente como están; en conflictos entre fuentes, usar la forma común / DDE (Allin p'unchay, Phichqa, Chawlla; por coherencia, Pilli para "pato"). Rosado queda sin cambio.

## Base de datos del vocabulario (`diccionario.db`)

| Cambio | Archivos | Prueba | Estado |
|---|---|---|---|
| 84 filas corregidas (las 70 correcciones; los números compuestos cuentan aparte) + traducción de chicha | `basedatos/correcciones_002.py` | Verifica cada palabra antes de cambiarla; idempotente (2.ª ejecución: 0 cambios); 14 búsquedas de control | 🟢 VERIFICADO |
| *T'anta* (pan) movida a alimentos; *Taqlla* (arado) a herramientas | `basedatos/correcciones_002.py` | Prueba automática | 🟢 VERIFICADO |
| Columna `significado` agregada a colores, familia, partes del cuerpo y saludos | `basedatos/correcciones_002.py` | Prueba automática | 🟢 VERIFICADO |
| Copia versionable del diccionario (texto SQL que Git sí guarda) y script para reconstruirlo | `basedatos/diccionario_semilla.sql`, `basedatos/crear_diccionario.py` | Reconstrucción idéntica al original (prueba automática) | 🟢 VERIFICADO |
| Respaldo previo a las correcciones | `basedatos/diccionario_antes_correcciones_002_20260927_1450.db` | — | 🟢 |
| Palabras antiguas escritas en el código (*sacha*, *kashanki*, *allin sukay*) | `juego.py`, `web/app.py`, `web/static/js/app.js`, `conversacion.py` | Suite completa | 🟢 VERIFICADO |

## Juego

| Cambio | Archivos | Prueba | Estado |
|---|---|---|---|
| Usa el diccionario: 101 palabras básicas, verificadas y con una sola traducción (antes 6 fijas). Sin diccionario, vuelve a las 6 de respaldo | `traductor.py` (`palabras_para_juego`), `juego.py`, `main_robot.py` | 4 pruebas automáticas | 🟢 VERIFICADO; ⚫ sin prueba con voz real |

## Resultados (`resultados.db`) y página web

| Cambio | Archivos | Prueba | Estado |
|---|---|---|---|
| Cada intento guarda el **estudiante o grupo** indicado por el docente; las bases antiguas se actualizan solas | `resultados.py` | 2 pruebas (incluida la migración de una base antigua) | 🟢 VERIFICADO |
| Formulario "¿Quién juega ahora con Yura?" (guardar / quitar nombre), tabla por estudiante o grupo, filtro, columna en el CSV | `web/app.py`, `web/templates/resultados.html`, `web/static/css/resultados.css` | 4 pruebas + prueba en vivo (guardar, mostrar, vaciar) | 🟢 VERIFICADO |
| El formulario rechaza envíos desde otras páginas (origen distinto) y está protegido desde la red | `web/app.py` | 2 pruebas | 🟢 VERIFICADO |
| La página ya no se recarga mientras se escribe en el formulario | `web/templates/resultados.html` | Revisión en navegador | 🟢 |

## Pantalla del robot

| Cambio | Archivos | Prueba | Estado |
|---|---|---|---|
| Muestra el **modo** actual (juego, traductor, conversación…) | `app.js` | Firefox: 9 combinaciones | 🟢 VERIFICADO |
| Muestra **✔ ¡Correcto!** / **✘ Sigue intentando** en el juego | `app.js`, `index.html`, `style.css` | Firefox | 🟢 VERIFICADO |
| La tarjeta muestra la **palabra que se está enseñando** (etiqueta "PALABRA"); si no, una de ejemplo; significado de ejemplo corregido ("Hola") | `app.js`, `index.html` | Firefox | 🟢 VERIFICADO |
| Muestra quién juega en el pie de pantalla | `app.js`, `web/app.py` | Prueba + en vivo | 🟢 VERIFICADO |
| Sin conexión ya no deja una palabra vieja en pantalla | `app.js` | Firefox | 🟢 VERIFICADO |
| Se actualiza cada 2 s (antes 5 s) | `app.js` | — | 🟢 |
| **Pantallas de 7"** (1024×600 y 800×480): todo cabe, sin barras de desplazamiento ni solapamiento. Se encontró que la animación del robot anulaba su achicado (`transform`); se usa `scale` | `style.css` | Firefox: mediciones de posición en 3 tamaños + capturas `evidencias/10_*.png` | 🟢 VERIFICADO |

## Integración en vivo (servicio real)

Arranque en 5 s; `/api/status` incluye el participante; formulario guarda y vacía (303); desde la red sin clave → 403; sin errores en el registro.

## Pendientes

| # | Pendiente | Estado |
|---|---|---|
| — | Probar juego, práctica, silencio y latencia **con voz real** | 🟡 PENDIENTE |
| — | 12 palabras sin fuente siguen en el diccionario (decisión del equipo) | [PENDIENTE DE VALIDACIÓN] por un docente |
| — | Rosado (*Qamya puka*) sin fuente clara | [PENDIENTE DE VALIDACIÓN] |
| P5 | Conexión con la plataforma Laravel | ⚫ BLOQUEADO |
| P14 | Guardar en Git (32 archivos o carpetas sin respaldo, según git status) | ⚫ BLOQUEADO por pedido del usuario |
| — | Privacidad fuera del modo silencio (aviso y consentimiento) | 🟡 decisión del equipo |
| — | Borrar `model/`, `entrada.txt`, `style-draft.css`, respaldos antiguos | [PENDIENTE DE VALIDACIÓN] |

**Estado: PROYECTO NO VERIFICADO — EXISTEN PENDIENTES** (principalmente pruebas con voz real y decisiones del equipo).
