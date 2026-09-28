# Informe 05: pruebas de casos extremos (subagente 5)

Fecha: 2026-09-27 · Proyecto: `/home/yura/Proyecto Yura /cerebro_yura` · Estado del código: árbol de trabajo sin commit (incluye los cambios de hoy descritos en `00_contexto_comun.md`).

## 1. Resumen ejecutivo

- **Pruebas ejecutadas: 322** (IDs YURA-EXT-001 … YURA-EXT-953, no consecutivos). Todas se ejecutaron de verdad y tienen su salida guardada.
- **Resultado: 211 🟢 APROBADO · 36 🟡 OBSERVACIÓN · 72 🟠 REQUIERE CORRECCIÓN · 3 🔴 ERROR CRÍTICO** (75 fallos).
- En 158 de las pruebas del grupo 1 no hubo excepciones. **Aun así, 21 dan un comportamiento incorrecto** porque las órdenes se detectan buscando un trozo de texto dentro de la frase (subcadena).
- Llamadas a servicios en línea: **4 a Groq** (dentro del límite de 25). Ninguna a Gemini y ninguna síntesis de voz con Edge TTS: la prueba EXT-750 usa el binario local y se detiene al leer los argumentos, antes de conectarse a la red.
- No se modificó ningún archivo del proyecto: `git status` es igual al del inicio y `diccionario.db` sigue con mtime 2026-09-26 23:40:33. Todas las BD de prueba son copias en el scratchpad.

**Hallazgos críticos y altos, todos VERIFICADOS con ejecución:**

| Prioridad | Hallazgo | IDs |
|---|---|---|
| 🔴 CRÍTICO | Si en el MENÚ se oye cualquier frase que contenga «apagar», el robot se apaga, y en modo web termina el proceso completo (`os._exit(0)`). Ejemplos: «no quiero apagar», «no te vayas a apagar», «cómo se dice apagar la luz». Después hay que reiniciarlo a mano, porque por voz ya no se puede. | 151, 152, 153 |
| ALTO | El evaluador del juego y de la práctica da por correctas palabras quechuas **distintas**: acepta 141 pares de palabras de la propia BD (Tawa=Wawa, Asnu=Vasu, Akcha=Aycha…). El estudiante recibe «¡Excelente!» aunque haya dicho otra palabra. | 215, 314 |
| ALTO | Si la BD está dañada o bloqueada, se lanza una excepción que nadie captura. `loop_principal` termina, el hilo del robot muere y la pantalla sigue mostrando «MODO TRADUCTOR ACTIVO» con `running=True`. | 509–513, 520, 522 |
| ALTO | Las palabras de orden chocan con el contenido que se enseña. En el traductor no se puede traducir «adiós», «volver», «terminar» ni «menú», porque salen al menú. «¿Cómo se dice adiós en quechua?» despide al usuario. «menudo» sale, «conjugar» abre el juego y «guarda silencio» despierta al robot. | 019, 021, 043, 067, 091, 093, 115, 117, 154–157, 160–164 |

## 2. Metodología

1. Leí el código completo de `conversacion.py`, `traductor.py`, `juego.py`, `main_robot.py`, `audio_manager.py`, `gemini_transcriber.py`, `web/app.py` y de `web/static/js/app.js` (la parte que dibuja la pantalla).
2. Scripts propios reproducibles en `documentacion_pruebas/evidencias/05_scripts/` (utilidades en `comun.py`). Se ejecutan con `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python <script>` desde esa carpeta.
3. Dobles de prueba usados:
   - **Groq falso** (`GroqFalso`): lanza timeout, 429, 401 o error de conexión; o devuelve respuesta vacía, `None`, `choices=[]`, Markdown, HTML, 20.000/45.000 caracteres o `finish_reason='length'`. Guarda los mensajes enviados para medir cuánto se manda.
   - **BrainYura** creado con `object.__new__` y atributos falsos (`hw=Mock()`, `escuchar_voz=Mock(...)`), como en `tests/`.
   - **sounddevice simulado** (`g08_audio.py`): nunca se abre un dispositivo real.
   - **`subprocess.run` y `shutil.which` simulados** en `hablar()`: no sale ningún sonido por el televisor.
   - **Web** con `web.app.app.test_client()` y `web.app.robot` apuntando a objetos falsos o a `None`. No se usaron los puertos 5000 ni 5051.
   - **BD**: copias hechas con `sqlite3.backup` desde `file:diccionario.db?mode=ro`. Para simular una BD ausente, vacía, de texto o con esquema raro, se redirigió la ruta cambiando `conversacion.__file__` y `BrainYura.db_path`.
   - **Claves**: se cambió `main_robot.__file__` para que apunte a una carpeta temporal con un `.env.local` de prueba. El `.env.local` real solo se leyó en `g04b` a través de la función del proyecto; su valor nunca se imprimió (`grep gsk_|AIza` sobre las evidencias da 0).
4. Criterio de estado: 🟢 cuando el comportamiento es correcto y no hay excepción; 🟡 cuando es aceptable pero mejorable o discutible; 🟠 cuando el comportamiento es incorrecto o hay una excepción no controlada; 🔴 cuando deja al robot inutilizable sin intervención manual.
5. Los bucles infinitos se detectaron con contadores (hasta 200 vueltas) para que las pruebas no se quedaran colgadas.

## 3. Resultados por grupo

| Grupo | Tema | Pruebas | 🟢 | 🟡 | 🟠/🔴 | Script / salida |
|---|---|---|---|---|---|---|
| 1 | Entradas extremas (24 entradas × 6 funciones + 14 colisiones) | 158 | 122 | 15 | 21 (3 🔴) | `g01_entradas.py` / `05_g01_entradas.txt` |
| 2 | Juego | 12 | 5 | 1 | 6 | `g02_03_juego_practica.py` / `05_g02_03_juego_practica.txt` |
| 3 | Práctica educativa | 16 | 9 | 0 | 7 | ídem |
| 4 | Traductor y Groq (falso y real) | 32 | 17 | 1 | 14 | `g04_traductor_groq.py`, `g04b_groq_real.py` |
| 5 | Base de datos | 22 | 7 | 4 | 11 | `g05_bd.py` / `05_g05_bd.txt` |
| 6 | Web | 15 | 10 | 3 | 2 | `g06_web.py` / `05_g06_web.txt` |
| 7 | Voz (TTS) | 26 | 12 | 3 | 11 | `g07_tts.py` / `05_g07_tts.txt` |
| 8 | Audio | 18 | 14 | 4 | 0 | `g08_audio.py` / `05_g08_audio.txt` |
| 9 | Claves | 19 | 14 | 4 | 1 | `g09_10_claves_concurrencia.py` |
| 10 | Concurrencia | 4 | 1 | 1 | 2 | ídem |
| **Total** | | **322** | **211** | **36** | **75** | |

### 3.1 Grupo 1: entradas extremas
- **Robustez básica (🟢).** Ninguna de estas entradas produjo excepciones en `procesar_entrada`, `ejecutar_traducir`, `Juego.ejecutar_turno`, `ejecutar_menu`, `ejecutar_conversar` ni `ejecutar_silencio`: `""`, espacios, `None`, 5.000 y 100.000 caracteres, emojis, `' " ; -- DROP TABLE`, `%`, `_`, `\x00`, saltos de línea.
  - La inyección SQL no tiene efecto: la búsqueda no construye SQL con el texto del usuario y los nombres de tabla se validan con una expresión regular y se citan (`traductor.py:13-15, 79`).
  - 100.000 caracteres tardan unos 0,5 s en `procesar_entrada`.
- **Colisiones por subcadena (🟠/🔴).** Se ven en la tabla de la sección 1:
  - `ejecutar_menu`: `"apagar" in opcion` (`main_robot.py:958`) está **antes** que traducir y conversar, así que «traducir apagar» y «cómo se dice apagar la luz» apagan el robot.
  - En el menú: «salir», «terminar» o «adios» → SILENCIO (`main_robot.py:971-975`), aunque la frase sea una pregunta de traducción.
  - En el traductor: `salir, apagar, terminar, adios, volver, menu, regresar` (`traductor.py:394-405`).
  - En conversación: `salir, terminar, adios, hasta luego, nos vemos, me voy, menu` (`conversacion.py:112-116`).
  - En el juego: `"salir" in … or "menu" in …` (`juego.py:146`).
  - En el menú: `"jugar" in opcion` (`main_robot.py:1029`).
  - En conversación, `_coincide_clave_intencion` concatena los tokens y busca subcadenas (`conversacion.py:89-94`), por eso «conjugar» cuenta como «jugar».
- **🟡 Mensaje confuso para temas válidos.** «noche», «123», «-5» y «nomás» en conversación reciben «Soy Yura… no vendo autos ni converso en inglés» (`conversacion.py:736-744`). En el traductor, «noche» sí se traduce (Allin tuta).
- **🟡 Respuesta distinta según la entrada vacía.** `ejecutar_conversar` responde «No logré escucharte» ante «   », pero calla ante «».
- **🟡 Traductor y Groq.** Un texto de 5.000 caracteres se envía completo a Groq (EXT-028). Uno de 100.000 también se envía completo (EXT-029, ver grupo 4).

### 3.2 Grupo 2: juego
- **EXT-201 🟠** Aunque se fallen las 4 preguntas, dice «¡Felicidades! Completaste todas las palabras». No lleva puntaje (`juego.py:91-97`).
- **EXT-203 🟠** Con 50 respuestas vacías seguidas, el índice sigue en 0 y la misma pregunta se repite 50 veces. Nunca avanza ni sale (`juego.py:136-144` devuelve «continuar» sin avanzar).
- **EXT-204 🟠** Si una palabra de la lista no está en la BD ni en el mapeo de emergencia, dice «No pude cargar la respuesta correcta…» y devuelve «continuar» **antes de escuchar** (`juego.py:116-121`). Es un **bucle infinito del que no se sale por voz**. Con los datos actuales no se alcanza, porque las 6 palabras existen (ver `06_palabras_juego_en_bd.txt`).
- **EXT-205/206 🟠/🟡** Sin BD, «agua» se evalúa con «yaku» (mapeo de emergencia, `juego.py:103-110`). Con BD se evalúa con «Uma». La misma respuesta es correcta o incorrecta según haya o no BD.
- **EXT-210–213 🟢** Frase de varias palabras (Buenas noches = Allin tuta): «allin tuta» y «alin tuta» se aceptan; «allin» o «tuta» solas, no.
- **EXT-214 🟠** Con la lista de palabras vacía, felicita de inmediato.
- **EXT-215 🟠 ALTO** Se compararon todos los pares de las 182 palabras quechuas de la BD con `_respuesta_es_correcta`: acepta **141 pares de palabras distintas** (umbral de similitud 0,75 tras quitar la «h» y cambiar q→k y ll→y; `juego.py:36-85`). Ejemplos: Akcha/Aycha (cabello/carne), Anqas/Manka (azul/olla), Asnu/Vasu (burro/vaso), Aswa/Tawa.

### 3.3 Grupo 3: práctica educativa
- **EXT-301–303 🟠** «repite», «otra vez» o «siguiente» sin práctica activa se detectan como intención «repetir», pero no hay nada que las atienda y caen en el mensaje de «fuera de tema».
- **EXT-304 🟢** Con la BD vacía responde «No pude cargar una palabra del vocabulario local».
- **EXT-305 🟠** Dentro de una práctica, «repite» cambia de palabra en 19 de 20 intentos: `_continuar_practica` elige otra palabra al azar (`conversacion.py:324-328, 291-307`) en lugar de repetir la actual.
- **EXT-310–318.** Respuesta casi correcta («alin punchai») → 🟢 correcta. Muy distinta («wasi») → 🟢 incorrecta. Pero **«wawa» se acepta cuando la palabra era «Tawa»** (🟠, EXT-314).
- **EXT-316 🟠** Si se practica «Allin tuta» y el estudiante lo dice bien, no se evalúa. `_responder_frase_local` se ejecuta **antes** de la sesión (`conversacion.py:655-664`, `531-534`) y contesta «Allin tuta significa Buenas noches.».
- **EXT-320 🟠** Si durante la práctica se pregunta «¿cómo se dice perro?», se toma como respuesta equivocada («Todavía no. La forma correcta es Wasi»).
- **EXT-321 🟢** «salir» termina la práctica.

### 3.4 Grupo 4: traductor y Groq
- **🟢 Casos que funcionan.**
  - Palabra ambigua «papa»: dice ambas opciones (EXT-401).
  - Palabra inexistente sin Groq, o con Groq fallando por timeout, 429, 401 o error de conexión: mensaje de respaldo y ninguna excepción (EXT-402–406).
  - Respuesta vacía, `None` o `choices=[]`: respaldo (EXT-414, 415, 420). En conversación, lo mismo (EXT-430–432).
- **🟠 Salida de Groq sin validar** (`traductor.py:333-353`, `conversacion.py:618-637`):
  - «NO ENCONTRADO» (con espacio) y «Lo siento, NO_ENCONTRADO» se dicen como si fueran la traducción: «En quechua se puede decir: NO ENCONTRADO.» (EXT-412, 413).
  - El Markdown `**Wasi** _(casa)_` y el HTML `<b>Wasi</b><script>…` pasan a la voz y a la pantalla (EXT-416, 417).
  - Una respuesta de 20.000 caracteres se habla completa (EXT-418); en conversación, una de 45.000 también (EXT-435).
  - Una respuesta cortada (`finish_reason='length'`) se acepta. En el traductor ni siquiera se comprueba (EXT-419). En conversación se registra el aviso, pero se dice igualmente la frase incompleta «…para familia es» (EXT-436).
- **🟠 Tamaño de lo enviado.** 100.000 caracteres se envían completos, unos 25.000 tokens (EXT-421). **En la llamada REAL (EXT-452), Groq devolvió 413 «Request too large… TPM Limit 8000, Requested 13214».** El robot responde «No estoy seguro…». En el uso real por voz, la grabación dura como mucho 15 s y Gemini devuelve como máximo 120 tokens, así que el riesgo real es bajo.
- **🟠 EXT-422.** Con la escucha siempre vacía, el traductor dijo «Necesito que repitas la palabra o frase.» 200 veces; solo paró por el contador de la prueba. En el robot real sería una vez cada ~10 s (la espera máxima de escucha), para siempre, sin volver al menú ni callarse.
- **🟠 EXT-441.** El cliente Groq que crea `main_robot.py:680` usa `timeout read=60 s` y `max_retries=2`, así que puede quedar bloqueado unos 3 minutos si la red se cuelga. Esto es un cálculo a partir de la configuración; **el cuelgue real NO se verificó.**
- **Groq REAL (4 llamadas).**
  - «helicóptero» y «xqzv blorf» → `NO_ENCONTRADO` (🟢 EXT-450, 451).
  - Petición de viñetas y negritas → respondió en texto plano con colores que sí están en la BD: Puka, Anqas, Yuraq, Q'ello, Q'omer (🟢 EXT-453).
  - 100.000 caracteres → 413 (EXT-452).
- **🟡 EXT-440.** El historial de conversación crece sin límite (1.000 mensajes tras 500 turnos), aunque a Groq solo se envían los últimos 8.

### 3.5 Grupo 5: base de datos
- **Ausente (🟢).** Avisa y no crea el archivo (EXT-501–504).
- **0 bytes (🟠 EXT-505).** `sqlite3.connect` la acepta, se imprime «[OK]: Base de datos enlazada» y el traductor responde «No estoy seguro…» a todo. No avisa de que la BD está vacía.
- **Texto plano (🟠 EXT-508–513).** La conexión se da por buena. Al primer uso salta `sqlite3.DatabaseError: file is not a database` sin que nadie la capture, en el traductor, la conversación y el juego. En `loop_principal` solo se captura `KeyboardInterrupt` (`main_robot.py:1200`), así que el bucle termina. En `web/app.py:144-149`, `os._exit(0)` no se ejecuta: el servidor sigue vivo y `/api/status` informa `running=True`, «MODO TRADUCTOR ACTIVO» (EXT-522).
- **Esquema raro (🟡 EXT-514/515).** Se ignoran sin ningún aviso las tablas sin columnas, con mayúsculas (`nivel1_Frutas` con datos), con comillas o SQL en el nombre o con espacios. Ninguna inyección se ejecuta (la tabla `t` sigue existiendo) y `nivel007_ok` se acepta.
- **NULL y vacío (🟠 EXT-518/519).**
  - El traductor no dice «None» (EXT-516/517 🟢).
  - Pero se envía a Groq como «vocabulario verificado» `- Casa = None` y `- None = Wasi` (EXT-518).
  - La práctica dice «En quechua se dice None» (11 de 20 semillas) o «se dice .» (9 de 20) (EXT-519).
- **Bloqueada (🟠 EXT-520).** Con otra conexión en `BEGIN EXCLUSIVE`, espera 5,0 s y lanza `OperationalError: database is locked` sin capturar.
- **50.187 filas (🟡 EXT-521).** Una búsqueda tarda 0,22 s e iniciar una práctica 1,67 s, porque cada consulta lee todas las filas de todas las tablas (`traductor.py:149`) y la práctica lo hace 5 veces (`conversacion.py:194`). Con las 187 filas actuales no hay problema.

### 3.6 Grupo 6: web
- **🟢 Casos que funcionan.**
  - Con robot `None` → 200 `BACKEND_NOT_STARTED`.
  - Estado desconocido → 200 con valores por defecto.
  - `<script>` en `content`: el JSON lo devuelve tal cual y **`app.js` lo pinta con `textContent`** (líneas 150-212), así que no se ejecuta.
  - 404 y 405 correctos, sin trazas.
  - 1.000 peticiones seguidas en 0,22 s. 1.000 peticiones en 10 hilos con un escritor concurrente: 0 errores.
- **🟠 EXT-602/604.** Si `get_web_status` lanza una excepción o al robot le falta el atributo `running`, la respuesta es **500 en HTML** en lugar de JSON.
- **🟡 Otros.**
  - `content` de 1 MB → 6,3 MB de respuesta sin ningún límite (EXT-606).
  - Faltan las cabeceras `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options` y `Referrer-Policy` (EXT-630).
  - `/api/status` no envía `Cache-Control`; el `fetch` usa `cache:'no-store'`, así que en la práctica no afecta (EXT-631).

### 3.7 Grupo 7: voz (TTS)
- **🟠 `_limpiar_texto_tts` deja pasar cosas que no debería leerse en voz alta** (EXT-701–704):
  - `[ver](http://x.y)`, URLs, HTML (`<p>`, `&nbsp;`), tablas con `|` y listas numeradas «1.».
  - `_formatear_texto_voz` cambia «?» por «.» incluso dentro de una URL.
- **🟠 EXT-711.** Para la frase estándar del traductor, «En quechua se dice: Tata. Significa padre.», `_texto_visible` devuelve **«: Tata»**: en pantalla aparecen los dos puntos. La causa es la expresión regular `:??` (perezosa) en `main_robot.py:189`. Coincide con la captura `02_contenido_C06_dos_puntos_tata.png` del subagente 2. Además, «Sr. Pérez…» se muestra como «Sr» (EXT-710, 🟡 menor).
- **🟠 EXT-705/706/741/742.** Si el texto son solo espacios o solo signos, se sintetiza «.» o «..»: se llama a Edge TTS, ffmpeg y pw-play para no decir nada.
- **🟡 EXT-720–723.** 10.000 caracteres se limpian en unos 1 ms (rendimiento correcto), pero no hay ningún límite de longitud ni para la voz ni para la pantalla.
- **🟢 EXT-730–734.**
  - Si Edge TTS falla, reintenta una vez y pasa a spd-say o espeak. Si no hay ninguno, lo registra en el log y **no se bloquea**.
  - Sin ffmpeg ni reproductores: solo aviso en el log y silencio; el estudiante no oye nada, pero el texto sí se muestra.
  - Si fallan todos los reproductores, los prueba todos.
- **🟠 EXT-740.** Ninguna llamada a `subprocess.run` para Edge TTS o los reproductores tiene `timeout` (`main_robot.py:240, 270, 327, 355, 365`). Un cuelgue simulado de 1,5 s por intento bloqueó `hablar()` 3,0 s. Un cuelgue real de la red bloquearía al robot indefinidamente (esto último es una inferencia a partir del código; el cuelgue real NO se verificó).
- **🟠 EXT-750** (binario real, sin red). Si el texto empieza por «--», Edge TTS termina con «error: argument -t/--text: expected one argument» (código 2), porque el comando pasa `"--text", texto` como dos argumentos separados. Se evitaría con `--text=<texto>`.

### 3.8 Grupo 8: audio
- **🟢 Casos que funcionan.**
  - Sin dispositivos, con `query_devices` lanzando una excepción o con un dispositivo que falla al abrir: devuelve `None` sin excepción.
  - Silencio absoluto: devuelve `None` tras 130 bloques (10 s de espera).
  - Clipping ±1,8: int16 válido (máximo 32768 en valor absoluto, que es -32768).
  - NaN: `None`.
  - `bloque_ms=0`: el `ZeroDivisionError` lo captura el `except` general.
  - `_calcular_umbral_ruido(0, -1, NaN, 1.0, inf, None)` siempre queda en [0,006; 0,104].
- **🟡 Ruido constante (EXT-805/806).** La grabación **sí termina** en `duracion_maxima` (15 s = 191 bloques), así que no hay grabación infinita. Pero si el ruido empieza después de la calibración de 0,2 s (televisor, ventilador), se envían 14,8 s de ruido a Gemini o Whisper.
- **🟡 EXT-807.** `duracion_maxima` cuenta desde que empieza la escucha, no desde que empieza la voz. Si el estudiante empieza a hablar a los 9,6 s, solo se graban 5,2 s.
- **🟡 EXT-826.** `_calcular_umbral_ruido("abc")` lanza `ValueError`; en el flujo real solo recibe números.
- ⚫ **NO VERIFICADO:** un `stream.read` que se bloquee en el driver real (no se puede simular sin hardware).

### 3.9 Grupo 9: claves (carpeta temporal)
- **🟢 Formatos que se leen bien.** Líneas sin «=», comillas dobles o simples, espacios alrededor, `export`, `export` con varios espacios, valor vacío, valor con «=», CRLF, `""`, líneas comentadas. Un `.env.local` sin permisos, que sea una carpeta o que sea binario no provoca excepción (se avisa).
- **🟠 EXT-901.** Si el archivo tiene **BOM UTF-8**, la primera clave se guarda como `﻿YT_BOM`, así que la variable esperada no existe (se abre con `encoding="utf-8"`, no con `utf-8-sig`; `main_robot.py:65`). Un `.env.local` guardado con el Bloc de notas de Windows pierde en silencio su primera clave.
- **🟡 Diferencias con otros cargadores de `.env`.**
  - Un comentario al final de la línea queda dentro del valor (EXT-909).
  - Con claves duplicadas gana la **primera** (EXT-912).
  - Las comillas desbalanceadas se aceptan (EXT-905).
  - Se aceptan claves con espacios (EXT-915).

### 3.10 Grupo 10: concurrencia
- **🟢 EXT-950.** `_set_web_status`/`get_web_status` con 8 escritores y 8 lectores (80.000 operaciones): 0 errores y 0 estados incoherentes.
- **🟠 EXT-951.** La conexión de `conversacion` se crea sin `check_same_thread=False` (`conversacion.py:182`). Si se usa desde otro hilo da `ProgrammingError`. Hoy es un problema latente: el robot la usa desde un solo hilo.
- **🟠 EXT-952.** Si 8 hilos comparten la misma conexión con `check_same_thread=False` (como `BrainYura.db_conn`), aparecen 6 `IndexError: tuple index out of range` en `traductor.py:86`. También latente: hoy solo la usa el hilo del robot.
- **🟡 EXT-953.** `_sesion_educativa` es global del módulo: cualquier `cancelar_sesion_educativa()` borra la práctica en curso.

## 4. Errores encontrados (reproducción exacta y traza)

**E1. Apagado por subcadena «apagar» (🔴, EXT-151/152/153).**
```
robot = object.__new__(BrainYura); robot.state="MENU"; robot.running=True; robot.saludo_inicial_done=True
robot.hw=Mock(); robot.escuchar_voz=Mock(return_value="como se dice apagar la luz"); robot._set_web_status=Mock()
robot.ejecutar_menu()  ->  state=SALIR, running=False, habló "Hasta luego. Me voy a apagar."
```
Causa: `main_robot.py:958` `if "apagar" in opcion:`. En web, `web/app.py:147-149` ejecuta `os._exit(0)`.

**E2. Excepción no capturada con BD dañada (🟠 ALTO, EXT-509).** BD = archivo de texto; `traductor.ejecutar_traducir(lambda:"casa", …, conn, None, activo)`:
```
  File ".../traductor.py", line 415, in ejecutar_traducir
    resultado_local = buscar_vocabulario(entrada_norm, "espanol", conexion_db)
  File ".../traductor.py", line 149, in buscar_vocabulario
    registros = _leer_registros_vocabulario(conexion_db)
  File ".../traductor.py", line 100, in _leer_registros_vocabulario
    for nombre_tabla, nivel, categoria in _tablas_de_vocabulario(conexion_db):
  File ".../traductor.py", line 67, in _tablas_de_vocabulario
    cursor.execute(
sqlite3.DatabaseError: file is not a database
```
Con la BD bloqueada (EXT-520) la traza es la misma, terminando en `sqlite3.OperationalError: database is locked`, tras 5,0 s. En `loop_principal` (EXT-513) la excepción sale del bucle; `/api/status` sigue devolviendo `running=True` (EXT-522).

**E3. Evaluador demasiado permisivo (🟠 ALTO, EXT-215/314).** `Juego._respuesta_es_correcta("wawa","tawa")` → True. `conversacion.procesar_entrada("wawa")` con la práctica «Tawa» → «Muy bien. Dijiste Tawa correctamente». Lista completa de pares en `05_g02_03_juego_practica.txt`.

**E4. Comandos que se comen el contenido (🟠 ALTO).** `traductor.ejecutar_traducir(lambda:"adios", …)` → «Regresando al menú principal.» (EXT-160). `ejecutar_conversar` con «como se dice adios en quechua» → MENU + «Hasta luego. Tupananchiskama.» (EXT-155). `ejecutar_silencio` con «guarda silencio» → MENU + «Ya estoy de vuelta» (EXT-157). `ejecutar_menu` con «conjugar» → JUEGO (EXT-093).

**E5. Bucles sin salida (🟠 MEDIO).** EXT-203 (juego con respuestas vacías), EXT-204 (palabra sin traducción: ni siquiera escucha), EXT-422 (traductor con escucha vacía).

**E6. «: Tata» en pantalla (🟠 MEDIO, EXT-711).** `HardwareInterface._texto_visible("En quechua se dice: Tata. Significa padre.")` → `': Tata'`.

**E7. Salida de Groq sin validar (🟠 MEDIO).** Respuesta falsa «NO ENCONTRADO» → la voz dice «En quechua se puede decir: NO ENCONTRADO.» (EXT-412). HTML y Markdown llegan a la voz y a la pantalla (EXT-416/417, 701-704). Respuestas cortadas y gigantes se dicen enteras (EXT-418/419, 435/436).

**E8. Sin límite de tamaño hacia Groq (🟠 MEDIO, EXT-421/452).** Llamada real: `Error code: 413 … on tokens per minute (TPM): Limit 8000, Requested 13214` (identificador de organización redactado en la evidencia).

**E9. Subprocesos sin `timeout` (🟠 MEDIO, EXT-740)** y cliente Groq con 60 s × 3 intentos (EXT-441).

**E10. BOM en `.env.local` (🟠 MEDIO, EXT-901):** la primera clave se pierde en silencio.

**E11. 500 en HTML en `/api/status` (🟠 BAJO, EXT-602/604):** `RuntimeError: fallo interno simulado` → «ERROR in app: Exception on /api/status [GET]».

**E12. Conexiones SQLite y hilos (🟠 BAJO, latente, EXT-951/952):** `ProgrammingError: SQLite objects created in a thread can only be used in that same thread` e `IndexError` en `traductor.py:86`.

**E13 (lectura de código, VERIFICADO con `sed -n 1221,1226p main_robot.py`).** `__main__` llama `cerebro.loop_principal()` dos veces (líneas 1224 y 1226). La segunda vuelve de inmediato porque `running=False` y vuelve a cerrar `db_conn`. Prioridad BAJO.

## 5. Matriz de pruebas

Estados de la matriz: 🟢 comportamiento correcto; 🟡 aceptable o discutible; 🟠 incorrecto o con excepción; 🔴 deja al robot inutilizable.
Por cada script hay también una matriz sin recortar en `evidencias/05_g*_matriz.md`, y cada salida completa (incluidas las trazas) está en el archivo de la columna «Evidencia».

| ID | Módulo | Prueba | Entrada | Esperado | Obtenido | Estado | Evidencia |
|---|---|---|---|---|---|---|---|
| YURA-EXT-001 | conversacion | procesar_entrada | vacio | sin excepción, respuesta razonable | accion=responder resp='No logré escucharte.' (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-002 | conversacion | procesar_entrada | espacios | sin excepción, respuesta razonable | accion=responder resp='No logré escucharte.' (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-003 | conversacion | procesar_entrada | None | sin excepción, respuesta razonable | accion=responder resp='No logré escucharte.' (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-004 | conversacion | procesar_entrada | 5000c | sin excepción, respuesta razonable | accion=responder resp='Rimaykullayki significa hola.' (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-005 | conversacion | procesar_entrada | 100000c | sin excepción, respuesta razonable | accion=responder resp='Soy Yura, un robot educativo que ayuda a practicar quechua. Puedo enseñarte vocabulario, t' (592 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-006 | conversacion | procesar_entrada | emojis | sin excepción, respuesta razonable | accion=responder resp='No logré escucharte.' (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-007 | conversacion | procesar_entrada | sql | sin excepción, respuesta razonable | accion=responder resp='Soy Yura, un robot educativo que ayuda a practicar quechua. Puedo enseñarte vocabulario, t' (1 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-008 | conversacion | procesar_entrada | porcentaje | sin excepción, respuesta razonable | accion=responder resp='No logré escucharte.' (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-009 | conversacion | procesar_entrada | guion_bajo | sin excepción, respuesta razonable | accion=responder resp='No logré escucharte.' (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-010 | conversacion | procesar_entrada | nulo | sin excepción, respuesta razonable | accion=responder resp='No logré escucharte.' (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-011 | conversacion | procesar_entrada | saltos | sin excepción, respuesta razonable | accion=responder resp='RESPUESTA_GROQ_FALSA' ¦ Groq llamado: user=15 car, system=974 car (5 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-012 | conversacion | procesar_entrada | ingles | sin excepción, respuesta razonable | accion=responder resp='RESPUESTA_GROQ_FALSA' ¦ Groq llamado: user=31 car, system=974 car (6 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-013 | conversacion | procesar_entrada | num_123 | sin excepción, respuesta razonable | accion=responder resp='Soy Yura, un robot educativo que ayuda a practicar quechua. Puedo enseñarte vocabulario, t' (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-014 | conversacion | procesar_entrada | num_-5 | sin excepción, respuesta razonable | accion=responder resp='Soy Yura, un robot educativo que ayuda a practicar quechua. Puedo enseñarte vocabulario, t' (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-015 | conversacion | procesar_entrada | mezcla | sin excepción, respuesta razonable | accion=responder resp='Rimaykullayki significa hola. Es un saludo en quechua.' (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-016 | conversacion | procesar_entrada | repetidas | sin excepción, respuesta razonable | accion=responder resp='Practiquemos una palabra. En quechua se dice Ukuku. Significa Oso andino: Mamífero de mont' (9 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-017 | conversacion | procesar_entrada | jugar_y_salir | sin excepción, respuesta razonable | accion=menu resp='Hasta luego. Tupananchiskama.' (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-018 | conversacion | procesar_entrada | traducir_apagar | sin excepción, respuesta razonable | accion=responder resp="No tengo una traducción segura de 'traducir apagar' en mi vocabulario local todavía. Puedo" (2 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-019 | conversacion | procesar_entrada | menudo | sin excepción, respuesta razonable | accion=menu resp='Hasta luego. Tupananchiskama.' (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-020 | conversacion | procesar_entrada | salirse | sin excepción, respuesta razonable | accion=menu resp='Hasta luego. Tupananchiskama.' (0 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-021 | conversacion | procesar_entrada | conjugar | sin excepción, respuesta razonable | accion=responder resp='Practiquemos una palabra. En quechua se dice Qallu. Significa Lengua: una palabra de uso c' (10 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-022 | conversacion | procesar_entrada | nomas | sin excepción, respuesta razonable | accion=responder resp='Soy Yura, un robot educativo que ayuda a practicar quechua. Puedo enseñarte vocabulario, t' (0 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-023 | conversacion | procesar_entrada | apagarlo | sin excepción, respuesta razonable | accion=responder resp='Soy Yura, un robot educativo que ayuda a practicar quechua. Puedo enseñarte vocabulario, t' (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-024 | conversacion | procesar_entrada | noche | sin excepción, respuesta razonable | accion=responder resp='Soy Yura, un robot educativo que ayuda a practicar quechua. Puedo enseñarte vocabulario, t' (0 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-025 | traductor | ejecutar_traducir | vacio | sin excepción; salir solo con orden clara | ret=continuar habló=['Necesito que repitas la palabra o frase.'] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-026 | traductor | ejecutar_traducir | espacios | sin excepción; salir solo con orden clara | ret=continuar habló=['Necesito que repitas la palabra o frase.'] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-027 | traductor | ejecutar_traducir | None | sin excepción; salir solo con orden clara | ret=continuar habló=['Necesito que repitas la palabra o frase.'] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-028 | traductor | ejecutar_traducir | 5000c | sin excepción; salir solo con orden clara | ret=continuar habló=['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra ma'] ¦ Groq user=4999 car (7 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-029 | traductor | ejecutar_traducir | 100000c | sin excepción; salir solo con orden clara | ret=continuar habló=['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra ma'] ¦ Groq user=100000 car (29 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-030 | traductor | ejecutar_traducir | emojis | sin excepción; salir solo con orden clara | ret=continuar habló=['Necesito que repitas la palabra o frase.'] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-031 | traductor | ejecutar_traducir | sql | sin excepción; salir solo con orden clara | ret=continuar habló=['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra ma'] ¦ Groq user=35 car (7 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-032 | traductor | ejecutar_traducir | porcentaje | sin excepción; salir solo con orden clara | ret=continuar habló=['Necesito que repitas la palabra o frase.'] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-033 | traductor | ejecutar_traducir | guion_bajo | sin excepción; salir solo con orden clara | ret=continuar habló=['Necesito que repitas la palabra o frase.'] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-034 | traductor | ejecutar_traducir | nulo | sin excepción; salir solo con orden clara | ret=continuar habló=['Necesito que repitas la palabra o frase.'] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-035 | traductor | ejecutar_traducir | saltos | sin excepción; salir solo con orden clara | ret=continuar habló=['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra ma'] ¦ Groq user=18 car (5 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-036 | traductor | ejecutar_traducir | ingles | sin excepción; salir solo con orden clara | ret=continuar habló=['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra ma'] ¦ Groq user=31 car (6 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-037 | traductor | ejecutar_traducir | num_123 | sin excepción; salir solo con orden clara | ret=continuar habló=['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra ma'] ¦ Groq user=3 car (5 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-038 | traductor | ejecutar_traducir | num_-5 | sin excepción; salir solo con orden clara | ret=continuar habló=['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra ma'] ¦ Groq user=2 car (6 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-039 | traductor | ejecutar_traducir | mezcla | sin excepción; salir solo con orden clara | ret=continuar habló=['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra ma'] ¦ Groq user=29 car (6 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-040 | traductor | ejecutar_traducir | repetidas | sin excepción; salir solo con orden clara | ret=continuar habló=['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra ma'] ¦ Groq user=17 car (5 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-041 | traductor | ejecutar_traducir | jugar_y_salir | sin excepción; salir solo con orden clara | ret=menu habló=['Regresando al menú principal.'] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-042 | traductor | ejecutar_traducir | traducir_apagar | sin excepción; salir solo con orden clara | ret=menu habló=['Regresando al menú principal.'] (0 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-043 | traductor | ejecutar_traducir | menudo | sin excepción; salir solo con orden clara | ret=menu habló=['Regresando al menú principal.'] (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-044 | traductor | ejecutar_traducir | salirse | sin excepción; salir solo con orden clara | ret=menu habló=['Regresando al menú principal.'] (0 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-045 | traductor | ejecutar_traducir | conjugar | sin excepción; salir solo con orden clara | ret=continuar habló=['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra ma'] ¦ Groq user=8 car (6 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-046 | traductor | ejecutar_traducir | nomas | sin excepción; salir solo con orden clara | ret=continuar habló=['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra ma'] ¦ Groq user=5 car (5 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-047 | traductor | ejecutar_traducir | apagarlo | sin excepción; salir solo con orden clara | ret=menu habló=['Regresando al menú principal.'] (0 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-048 | traductor | ejecutar_traducir | noche | sin excepción; salir solo con orden clara | ret=continuar habló=['En quechua se dice: Allin tuta.'] (3 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-049 | juego | ejecutar_turno | vacio | sin excepción; salir solo con orden clara | ret=continuar indice=0 habló=['¿Cómo se dice, agua, en quechua?', 'No logré escucharte.'] (2 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-050 | juego | ejecutar_turno | espacios | sin excepción; salir solo con orden clara | ret=continuar indice=0 habló=['¿Cómo se dice, casa, en quechua?', 'No logré escucharte.'] (1 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-051 | juego | ejecutar_turno | None | sin excepción; salir solo con orden clara | ret=continuar indice=0 habló=['¿Cómo se dice, casa, en quechua?', 'No logré escucharte.'] (2 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-052 | juego | ejecutar_turno | 5000c | sin excepción; salir solo con orden clara | ret=continuar indice=1 habló=['¿Cómo se dice, sol, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera'] (4 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-053 | juego | ejecutar_turno | 100000c | sin excepción; salir solo con orden clara | ret=continuar indice=1 habló=['¿Cómo se dice, gato, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera'] (56 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-054 | juego | ejecutar_turno | emojis | sin excepción; salir solo con orden clara | ret=continuar indice=0 habló=['¿Cómo se dice, perro, en quechua?', 'No logré escucharte.'] (1 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-055 | juego | ejecutar_turno | sql | sin excepción; salir solo con orden clara | ret=continuar indice=1 habló=['¿Cómo se dice, perro, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera'] (2 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-056 | juego | ejecutar_turno | porcentaje | sin excepción; salir solo con orden clara | ret=continuar indice=0 habló=['¿Cómo se dice, casa, en quechua?', 'No logré escucharte.'] (2 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-057 | juego | ejecutar_turno | guion_bajo | sin excepción; salir solo con orden clara | ret=continuar indice=0 habló=['¿Cómo se dice, agua, en quechua?', 'No logré escucharte.'] (2 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-058 | juego | ejecutar_turno | nulo | sin excepción; salir solo con orden clara | ret=continuar indice=0 habló=['¿Cómo se dice, gato, en quechua?', 'No logré escucharte.'] (1 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-059 | juego | ejecutar_turno | saltos | sin excepción; salir solo con orden clara | ret=continuar indice=1 habló=['¿Cómo se dice, agua, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera'] (1 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-060 | juego | ejecutar_turno | ingles | sin excepción; salir solo con orden clara | ret=continuar indice=1 habló=['¿Cómo se dice, agua, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera'] (1 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-061 | juego | ejecutar_turno | num_123 | sin excepción; salir solo con orden clara | ret=continuar indice=1 habló=['¿Cómo se dice, gato, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera'] (1 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-062 | juego | ejecutar_turno | num_-5 | sin excepción; salir solo con orden clara | ret=continuar indice=1 habló=['¿Cómo se dice, casa, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera'] (1 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-063 | juego | ejecutar_turno | mezcla | sin excepción; salir solo con orden clara | ret=continuar indice=1 habló=['¿Cómo se dice, perro, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera'] (2 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-064 | juego | ejecutar_turno | repetidas | sin excepción; salir solo con orden clara | ret=continuar indice=1 habló=['¿Cómo se dice, sol, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera'] (1 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-065 | juego | ejecutar_turno | jugar_y_salir | sin excepción; salir solo con orden clara | ret=menu indice=0 habló=['¿Cómo se dice, casa, en quechua?', 'Saliendo al menú principal.'] (1 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-066 | juego | ejecutar_turno | traducir_apagar | sin excepción; salir solo con orden clara | ret=continuar indice=1 habló=['¿Cómo se dice, gato, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera'] (1 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-067 | juego | ejecutar_turno | menudo | sin excepción; salir solo con orden clara | ret=menu indice=0 habló=['¿Cómo se dice, gato, en quechua?', 'Saliendo al menú principal.'] (1 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-068 | juego | ejecutar_turno | salirse | sin excepción; salir solo con orden clara | ret=menu indice=0 habló=['¿Cómo se dice, sol, en quechua?', 'Saliendo al menú principal.'] (1 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-069 | juego | ejecutar_turno | conjugar | sin excepción; salir solo con orden clara | ret=continuar indice=1 habló=['¿Cómo se dice, casa, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera'] (1 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-070 | juego | ejecutar_turno | nomas | sin excepción; salir solo con orden clara | ret=continuar indice=1 habló=['¿Cómo se dice, gato, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera'] (1 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-071 | juego | ejecutar_turno | apagarlo | sin excepción; salir solo con orden clara | ret=continuar indice=1 habló=['¿Cómo se dice, casa, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera'] (1 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-072 | juego | ejecutar_turno | noche | sin excepción; salir solo con orden clara | ret=continuar indice=1 habló=['¿Cómo se dice, arbol, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera'] (1 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-073 | main_robot | ejecutar_menu | vacio | sin excepción; estado coherente | estado=MENU running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-074 | main_robot | ejecutar_menu | espacios | sin excepción; estado coherente | estado=MENU running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-075 | main_robot | ejecutar_menu | None | sin excepción; estado coherente | estado=MENU running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-076 | main_robot | ejecutar_menu | 5000c | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Rimaykullayki significa hola.'] (1 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-077 | main_robot | ejecutar_menu | 100000c | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Soy Yura, un robot educativo que ayuda a practicar quechua. '] (543 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-078 | main_robot | ejecutar_menu | emojis | sin excepción; estado coherente | estado=MENU running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-079 | main_robot | ejecutar_menu | sql | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Soy Yura, un robot educativo que ayuda a practicar quechua. '] (3 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-080 | main_robot | ejecutar_menu | porcentaje | sin excepción; estado coherente | estado=MENU running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-081 | main_robot | ejecutar_menu | guion_bajo | sin excepción; estado coherente | estado=MENU running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-082 | main_robot | ejecutar_menu | nulo | sin excepción; estado coherente | estado=MENU running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-083 | main_robot | ejecutar_menu | saltos | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['RESPUESTA_GROQ_FALSA'] (7 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-084 | main_robot | ejecutar_menu | ingles | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['RESPUESTA_GROQ_FALSA'] (9 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-085 | main_robot | ejecutar_menu | num_123 | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Soy Yura, un robot educativo que ayuda a practicar quechua. '] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-086 | main_robot | ejecutar_menu | num_-5 | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Soy Yura, un robot educativo que ayuda a practicar quechua. '] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-087 | main_robot | ejecutar_menu | mezcla | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Rimaykullayki significa hola. Es un saludo en quechua.'] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-088 | main_robot | ejecutar_menu | repetidas | sin excepción; estado coherente | estado=JUEGO running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-089 | main_robot | ejecutar_menu | jugar_y_salir | sin excepción; estado coherente | estado=SILENCIO running=True habló=['Hasta luego. Tupananchiskama. Dime despierta cuando quieras '] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-090 | main_robot | ejecutar_menu | traducir_apagar | sin excepción; estado coherente | estado=SALIR running=False habló=['Hasta luego. Me voy a apagar.'] (0 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-091 | main_robot | ejecutar_menu | menudo | sin excepción; estado coherente | estado=MENU running=True habló=['Hasta luego. Tupananchiskama.'] (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-092 | main_robot | ejecutar_menu | salirse | sin excepción; estado coherente | estado=SILENCIO running=True habló=['Hasta luego. Tupananchiskama. Dime despierta cuando quieras '] (0 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-093 | main_robot | ejecutar_menu | conjugar | sin excepción; estado coherente | estado=JUEGO running=True habló=[] (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-094 | main_robot | ejecutar_menu | nomas | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Soy Yura, un robot educativo que ayuda a practicar quechua. '] (1 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-095 | main_robot | ejecutar_menu | apagarlo | sin excepción; estado coherente | estado=SALIR running=False habló=['Hasta luego. Me voy a apagar.'] (0 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-096 | main_robot | ejecutar_menu | noche | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Soy Yura, un robot educativo que ayuda a practicar quechua. '] (2 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-097 | main_robot | ejecutar_conversar | vacio | sin excepción; estado coherente | estado=CONVERSAR running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-098 | main_robot | ejecutar_conversar | espacios | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['No logré escucharte.'] (0 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-099 | main_robot | ejecutar_conversar | None | sin excepción; estado coherente | estado=CONVERSAR running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-100 | main_robot | ejecutar_conversar | 5000c | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Rimaykullayki significa hola.'] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-101 | main_robot | ejecutar_conversar | 100000c | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Soy Yura, un robot educativo que ayuda a practicar quechua. '] (536 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-102 | main_robot | ejecutar_conversar | emojis | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['No logré escucharte.'] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-103 | main_robot | ejecutar_conversar | sql | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Soy Yura, un robot educativo que ayuda a practicar quechua. '] (2 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-104 | main_robot | ejecutar_conversar | porcentaje | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['No logré escucharte.'] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-105 | main_robot | ejecutar_conversar | guion_bajo | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['No logré escucharte.'] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-106 | main_robot | ejecutar_conversar | nulo | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['No logré escucharte.'] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-107 | main_robot | ejecutar_conversar | saltos | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['RESPUESTA_GROQ_FALSA'] (4 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-108 | main_robot | ejecutar_conversar | ingles | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['RESPUESTA_GROQ_FALSA'] (5 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-109 | main_robot | ejecutar_conversar | num_123 | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Soy Yura, un robot educativo que ayuda a practicar quechua. '] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-110 | main_robot | ejecutar_conversar | num_-5 | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Soy Yura, un robot educativo que ayuda a practicar quechua. '] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-111 | main_robot | ejecutar_conversar | mezcla | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Rimaykullayki significa hola. Es un saludo en quechua.'] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-112 | main_robot | ejecutar_conversar | repetidas | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Practiquemos una palabra. En quechua se dice Qhari. Signific'] (9 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-113 | main_robot | ejecutar_conversar | jugar_y_salir | sin excepción; estado coherente | estado=MENU running=True habló=['Hasta luego. Tupananchiskama.'] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-114 | main_robot | ejecutar_conversar | traducir_apagar | sin excepción; estado coherente | estado=CONVERSAR running=True habló=["No tengo una traducción segura de 'traducir apagar' en mi vo"] (2 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-115 | main_robot | ejecutar_conversar | menudo | sin excepción; estado coherente | estado=MENU running=True habló=['Hasta luego. Tupananchiskama.'] (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-116 | main_robot | ejecutar_conversar | salirse | sin excepción; estado coherente | estado=MENU running=True habló=['Hasta luego. Tupananchiskama.'] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-117 | main_robot | ejecutar_conversar | conjugar | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Practiquemos una palabra. En quechua se dice Iglesia. Signif'] (9 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-118 | main_robot | ejecutar_conversar | nomas | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Soy Yura, un robot educativo que ayuda a practicar quechua. '] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-119 | main_robot | ejecutar_conversar | apagarlo | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Soy Yura, un robot educativo que ayuda a practicar quechua. '] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-120 | main_robot | ejecutar_conversar | noche | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Soy Yura, un robot educativo que ayuda a practicar quechua. '] (0 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-121 | main_robot | ejecutar_silencio | vacio | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-122 | main_robot | ejecutar_silencio | espacios | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-123 | main_robot | ejecutar_silencio | None | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-124 | main_robot | ejecutar_silencio | 5000c | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-125 | main_robot | ejecutar_silencio | 100000c | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (2 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-126 | main_robot | ejecutar_silencio | emojis | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-127 | main_robot | ejecutar_silencio | sql | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-128 | main_robot | ejecutar_silencio | porcentaje | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-129 | main_robot | ejecutar_silencio | guion_bajo | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-130 | main_robot | ejecutar_silencio | nulo | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-131 | main_robot | ejecutar_silencio | saltos | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-132 | main_robot | ejecutar_silencio | ingles | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-133 | main_robot | ejecutar_silencio | num_123 | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-134 | main_robot | ejecutar_silencio | num_-5 | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-135 | main_robot | ejecutar_silencio | mezcla | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-136 | main_robot | ejecutar_silencio | repetidas | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-137 | main_robot | ejecutar_silencio | jugar_y_salir | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-138 | main_robot | ejecutar_silencio | traducir_apagar | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-139 | main_robot | ejecutar_silencio | menudo | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-140 | main_robot | ejecutar_silencio | salirse | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-141 | main_robot | ejecutar_silencio | conjugar | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-142 | main_robot | ejecutar_silencio | nomas | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-143 | main_robot | ejecutar_silencio | apagarlo | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-144 | main_robot | ejecutar_silencio | noche | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-151 | main_robot | ejecutar_menu | 'no quiero apagar' | NO debe apagar | estado=SALIR running=False habló=['Hasta luego. Me voy a apagar.'] (0 ms) | 🔴 ERROR CRÍTICO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-152 | main_robot | ejecutar_menu | 'no te vayas a apagar yura' | NO debe apagar | estado=SALIR running=False habló=['Hasta luego. Me voy a apagar.'] (0 ms) | 🔴 ERROR CRÍTICO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-153 | main_robot | ejecutar_menu | 'como se dice apagar la luz' | NO debe apagar | estado=SALIR running=False habló=['Hasta luego. Me voy a apagar.'] (0 ms) | 🔴 ERROR CRÍTICO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-154 | main_robot | ejecutar_menu | 'como se dice adios en quechua' | traducir adiós, no despedirse | estado=SILENCIO running=True habló=['Hasta luego. Tupananchiskama. Dime despierta cuando quieras volver.'] (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-155 | main_robot | ejecutar_conversar | 'como se dice adios en quechua' | traducir adiós | estado=MENU running=True habló=['Hasta luego. Tupananchiskama.'] (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-156 | main_robot | ejecutar_conversar | 'como se dice menu en quechua' | responder, no volver al menú | estado=MENU running=True habló=['Hasta luego. Tupananchiskama.'] (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-157 | main_robot | ejecutar_silencio | 'guarda silencio' | seguir en SILENCIO | estado=MENU running=True habló=['Ya estoy de vuelta. ¿Qué te gustaría hacer?'] (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-158 | main_robot | ejecutar_silencio | 'no vuelvas todavia' | seguir en SILENCIO | estado=SILENCIO running=True habló=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-159 | main_robot | ejecutar_menu | 'silencio no quiero jugar' | SILENCIO (ambiguo) | estado=SILENCIO running=True habló=['Entendido. Me quedaré en silencio hasta que me pidas volver.'] (0 ms) | 🟢 APROBADO | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-160 | traductor | ejecutar_traducir | 'adios' | traducir la palabra (no salir) | ret=menu habló=['Regresando al menú principal.'] (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-161 | traductor | ejecutar_traducir | 'volver' | traducir la palabra (no salir) | ret=menu habló=['Regresando al menú principal.'] (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-162 | traductor | ejecutar_traducir | 'devolver' | traducir la palabra (no salir) | ret=menu habló=['Regresando al menú principal.'] (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-163 | traductor | ejecutar_traducir | 'terminar' | traducir la palabra (no salir) | ret=menu habló=['Regresando al menú principal.'] (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-164 | traductor | ejecutar_traducir | 'menu del dia' | traducir la palabra (no salir) | ret=menu habló=['Regresando al menú principal.'] (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g01_entradas.txt` |
| YURA-EXT-201 | juego | Responder mal todas | 4x 'respuesta equivocada' | al final informar puntaje/aciertos; no felicitar con 0 aciertos | retornos=['continuar', 'continuar', 'continuar', 'continuar', 'menu'] último mensaje='¡Felicidades! Completaste todas las palabras del juego. Regresemos al menú princi… | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g02_03_juego_practica.txt` |
| YURA-EXT-202 | juego | Responder 'salir' a mitad | turno1 'mal', turno2 'salir' | volver al menú | retornos=['continuar', 'menu'] último='Saliendo al menú principal.' (0 ms) | 🟢 APROBADO | `evidencias/05_g02_03_juego_practica.txt` |
| YURA-EXT-203 | juego | 50 respuestas vacías seguidas | '' x50 | tras N intentos sin respuesta, avanzar o salir al menú / silencio | retornos={'continuar'} indice=0 preguntas=50 (distintas=1); nunca sale (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g02_03_juego_practica.txt` |
| YURA-EXT-204 | juego | Lista con palabras que la BD no tiene | palabras=['xyz','helicoptero'], BD sin ellas | saltar la palabra o avisar y volver al menú | retornos={'continuar'} indice=0 mensajes=20 ej='No pude cargar la respuesta correcta de esta pregunta.' -> bucle infinito (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g02_03_juego_practica.txt` |
| YURA-EXT-205 | juego | Sin BD (conexión None): 'agua' usa mapeo de emergencia | respuesta 'yaku' | misma respuesta que la BD (Uma) o avisar que no hay BD | habló=['¿Cómo se dice, agua, en quechua?', '¡Excelente! Lo dijiste de forma correcta. ¡Muy bien hecho!'] (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g02_03_juego_practica.txt` |
| YURA-EXT-206 | juego | Con BD: 'agua' respondiendo 'yaku' | respuesta 'yaku' | coherente con el caso sin BD | habló=['¿Cómo se dice, agua, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera: Uma.'] (con BD 'yaku' es incorrecto y sin BD es correcto) (0 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g02_03_juego_practica.txt` |
| YURA-EXT-210 | juego | Traducción de varias palabras (Buenas noches = Allin tuta) | 'allin tuta' | correcto solo con la frase completa (o variante fonética) | '¡Excelente! Lo dijiste de forma correcta. ¡Muy bien hecho!' (0 ms) | 🟢 APROBADO | `evidencias/05_g02_03_juego_practica.txt` |
| YURA-EXT-211 | juego | Traducción de varias palabras (Buenas noches = Allin tuta) | 'allin' | correcto solo con la frase completa (o variante fonética) | 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera' (0 ms) | 🟢 APROBADO | `evidencias/05_g02_03_juego_practica.txt` |
| YURA-EXT-212 | juego | Traducción de varias palabras (Buenas noches = Allin tuta) | 'tuta' | correcto solo con la frase completa (o variante fonética) | 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera' (0 ms) | 🟢 APROBADO | `evidencias/05_g02_03_juego_practica.txt` |
| YURA-EXT-213 | juego | Traducción de varias palabras (Buenas noches = Allin tuta) | 'alin tuta' | correcto solo con la frase completa (o variante fonética) | '¡Excelente! Lo dijiste de forma correcta. ¡Muy bien hecho!' (0 ms) | 🟢 APROBADO | `evidencias/05_g02_03_juego_practica.txt` |
| YURA-EXT-214 | juego | Lista de palabras vacía | palabras=[] | avisar que no hay palabras | ret=menu habló=['¡Felicidades! Completaste todas las palabras del juego. Regresemos al menú principal.'] (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g02_03_juego_practica.txt` |
| YURA-EXT-215 | juego | Evaluador: palabras distintas aceptadas como correctas | 182 palabras quechuas de la BD, todos los pares | 0 pares de palabras distintas aceptados | 141 pares aceptados, ej: [('Akcha', 'Aycha'), ('Akcha', "Mak'a"), ('Akcha', 'Qocha'), ('Akcha', "Sach'a"), ('Akcha', 'Sacha'), ('Akcha', 'Waka'), ('Allin', 'Mayqin'), … | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g02_03_juego_practica.txt` |
| YURA-EXT-301 | conversacion | 'repite' sin sesión activa | repite | explicar que no hay práctica activa o empezar una | 'Soy Yura, un robot educativo que ayuda a practicar quechua. Puedo enseñarte vocabulario, traducciones y saludo' (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g02_03_juego_practica.txt` |
| YURA-EXT-302 | conversacion | 'otra vez' sin sesión activa | otra vez | explicar que no hay práctica activa o empezar una | 'Soy Yura, un robot educativo que ayuda a practicar quechua. Puedo enseñarte vocabulario, traducciones y saludo' (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g02_03_juego_practica.txt` |
| YURA-EXT-303 | conversacion | 'siguiente' sin sesión activa | siguiente | explicar que no hay práctica activa o empezar una | 'Soy Yura, un robot educativo que ayuda a practicar quechua. Puedo enseñarte vocabulario, traducciones y saludo' (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g02_03_juego_practica.txt` |
| YURA-EXT-304 | conversacion | Iniciar práctica con BD vacía | enséñame quechua | mensaje claro sin excepción | 'No pude cargar una palabra del vocabulario local. Probemos más tarde.' (3 ms) | 🟢 APROBADO | `evidencias/05_g02_03_juego_practica.txt` |
| YURA-EXT-305 | conversacion | 'repite' en sesión activa (20 intentos) | repite | repetir la MISMA palabra | en 19/20 intentos cambió a otra palabra (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g02_03_juego_practica.txt` |
| YURA-EXT-310 | conversacion | Evaluar práctica de 'Allin punchay' | 'allin punchay' | Correcta | 'Muy bien. Dijiste Allin punchay correctamente. Di otra vez o continuar para prac' (0 ms) | 🟢 APROBADO | `evidencias/05_g02_03_juego_practica.txt` |
| YURA-EXT-311 | conversacion | Evaluar práctica de 'Allin punchay' | 'alin punchai' | Correcta | 'Muy bien. Dijiste Allin punchay correctamente. Di otra vez o continuar para prac' (0 ms) | 🟢 APROBADO | `evidencias/05_g02_03_juego_practica.txt` |
| YURA-EXT-312 | conversacion | Evaluar práctica de 'Allin punchay' | 'allin' | Incorrecta | 'Todavía no. La forma correcta es Allin punchay. Repítela y luego di otra vez par' (0 ms) | 🟢 APROBADO | `evidencias/05_g02_03_juego_practica.txt` |
| YURA-EXT-313 | conversacion | Evaluar práctica de 'Allin punchay' | 'wasi' | Incorrecta | 'Todavía no. La forma correcta es Allin punchay. Repítela y luego di otra vez par' (0 ms) | 🟢 APROBADO | `evidencias/05_g02_03_juego_practica.txt` |
| YURA-EXT-314 | conversacion | Evaluar práctica de 'Tawa' | 'wawa' | Incorrecta | 'Muy bien. Dijiste Tawa correctamente. Di otra vez o continuar para practicar otr' (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g02_03_juego_practica.txt` |
| YURA-EXT-315 | conversacion | Evaluar práctica de 'Misi' | 'mesa' | Incorrecta | 'Todavía no. La forma correcta es Misi. Repítela y luego di otra vez para continu' (0 ms) | 🟢 APROBADO | `evidencias/05_g02_03_juego_practica.txt` |
| YURA-EXT-316 | conversacion | Evaluar práctica de 'Allin tuta' | 'allin tuta' | Correcta | NO evaluó la respuesta: 'Allin tuta significa Buenas noches.' (1 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g02_03_juego_practica.txt` |
| YURA-EXT-317 | conversacion | Evaluar práctica de 'Imaynalla' | 'imaynalla' | Correcta | 'Muy bien. Dijiste Imaynalla correctamente. Di otra vez o continuar para practica' (0 ms) | 🟢 APROBADO | `evidencias/05_g02_03_juego_practica.txt` |
| YURA-EXT-318 | conversacion | Evaluar práctica de 'Uma' | 'uma' | Correcta | 'Muy bien. Dijiste Uma correctamente. Di otra vez o continuar para practicar otra' (0 ms) | 🟢 APROBADO | `evidencias/05_g02_03_juego_practica.txt` |
| YURA-EXT-320 | conversacion | Pregunta de traducción durante la práctica | ¿cómo se dice perro? | responder la pregunta o aclarar que hay una práctica pendiente | 'Todavía no. La forma correcta es Wasi. Repítela y luego di otra vez para continuar, o sali' (1 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g02_03_juego_practica.txt` |
| YURA-EXT-321 | conversacion | 'salir' durante la práctica | salir | acción menú | {'accion': 'menu', 'respuesta': 'Terminamos por ahora. Tupananchiskama.'} (0 ms) | 🟢 APROBADO | `evidencias/05_g02_03_juego_practica.txt` |
| YURA-EXT-401 | traductor | Palabra ambigua | papa | decir ambas opciones | ['Tiene varios significados: Papa, de alimentos, se dice Papa; Papá, de familia, se dice Tata.'] pantalla=[{'content': 'Papa', 'translation': 'Papa'}] (2 ms) | 🟢 APROBADO | `evidencias/05_g04_traductor_groq.txt` |
| YURA-EXT-402 | traductor | Palabra inexistente sin Groq | helicóptero, groq=None | mensaje de no encontrado | ['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra manera?'] (3 ms) | 🟢 APROBADO | `evidencias/05_g04_traductor_groq.txt` |
| YURA-EXT-403 | traductor | Groq falla (timeout) | helicóptero | mensaje de no encontrado, sin excepción | ['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra manera?'] (6 ms) | 🟢 APROBADO | `evidencias/05_g04_traductor_groq.txt` |
| YURA-EXT-404 | traductor | Groq falla (429) | helicóptero | mensaje de no encontrado, sin excepción | ['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra manera?'] (7 ms) | 🟢 APROBADO | `evidencias/05_g04_traductor_groq.txt` |
| YURA-EXT-405 | traductor | Groq falla (401) | helicóptero | mensaje de no encontrado, sin excepción | ['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra manera?'] (7 ms) | 🟢 APROBADO | `evidencias/05_g04_traductor_groq.txt` |
| YURA-EXT-406 | traductor | Groq falla (conexion) | helicóptero | mensaje de no encontrado, sin excepción | ['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra manera?'] (7 ms) | 🟢 APROBADO | `evidencias/05_g04_traductor_groq.txt` |
| YURA-EXT-410 | traductor | Groq devuelve NO_ENCONTRADO | helicóptero | no decir nada inventado | voz(75 car)='No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra manera?' pantalla='None' (5 ms) | 🟢 APROBADO | `evidencias/05_g04_traductor_groq.txt` |
| YURA-EXT-411 | traductor | Groq devuelve NO_ENCONTRADO. | helicóptero | no decir nada inventado | voz(75 car)='No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra manera?' pantalla='None' (5 ms) | 🟢 APROBADO | `evidencias/05_g04_traductor_groq.txt` |
| YURA-EXT-412 | traductor | Groq devuelve NO ENCONTRADO (espacio) | helicóptero | no decir nada inventado | voz(41 car)='En quechua se puede decir: NO ENCONTRADO.' pantalla='NO ENCONTRADO' (5 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g04_traductor_groq.txt` |
| YURA-EXT-413 | traductor | Groq devuelve Lo siento, NO_ENCONTRADO | helicóptero | no decir nada inventado | voz(52 car)='En quechua se puede decir: Lo siento, NO_ENCONTRADO.' pantalla='Lo siento, NO_ENCONTRADO' (5 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g04_traductor_groq.txt` |
| YURA-EXT-414 | traductor | Groq devuelve vacía | helicóptero | mensaje de no encontrado | voz(75 car)='No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra manera?' pantalla='None' (6 ms) | 🟢 APROBADO | `evidencias/05_g04_traductor_groq.txt` |
| YURA-EXT-415 | traductor | Groq devuelve None | helicóptero | mensaje de no encontrado | voz(75 car)='No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra manera?' pantalla='None' (8 ms) | 🟢 APROBADO | `evidencias/05_g04_traductor_groq.txt` |
| YURA-EXT-416 | traductor | Groq devuelve Markdown | helicóptero | texto limpio en pantalla y voz | voz(45 car)='En quechua se puede decir: **Wasi** _(casa)_.' pantalla='**Wasi** _(casa)_' (7 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g04_traductor_groq.txt` |
| YURA-EXT-417 | traductor | Groq devuelve HTML | helicóptero | sin etiquetas | voz(64 car)='En quechua se puede decir: <b>Wasi</b><script>alert(1)</script>.' pantalla='<b>Wasi</b><script>alert(1)</script>' (6 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g04_traductor_groq.txt` |
| YURA-EXT-418 | traductor | Groq devuelve gigante 20k | helicóptero | limitar lo que se habla | voz(20027 car)='En quechua se puede decir: wasi wasi wasi wasi wasi wasi wasi wasi wasi wasi wasi wasi was' pantalla='wasi wasi wasi wasi wasi wasi wasi wasi wasi wasi… | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g04_traductor_groq.txt` |
| YURA-EXT-419 | traductor | Groq devuelve cortada length | helicóptero | avisar/descartar respuesta cortada | voz(37 car)='En quechua se puede decir: Chay wasi.' pantalla='Chay wasi' (5 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g04_traductor_groq.txt` |
| YURA-EXT-420 | traductor | Groq devuelve choices=[] | helicóptero | sin excepción | ['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra manera?'] (5 ms) | 🟢 APROBADO | `evidencias/05_g04_traductor_groq.txt` |
| YURA-EXT-421 | traductor | Texto enorme a Groq | 'palabra '*12500 (100.000 car) | recortar o rechazar antes de enviar | se envían user=99999 car (~24999 tokens), system=631 car, max_completion_tokens=480 (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g04_traductor_groq.txt` |
| YURA-EXT-422 | traductor | Bucle modo_activo con escucha siempre vacía | '' x200 (límite del contador) | tras N silencios, volver al menú o callar | habló 200 veces {'Necesito que repitas la palabra o frase.'}; solo se detuvo por el contador de la prueba (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g04_traductor_groq.txt` |
| YURA-EXT-430 | conversacion | Groq en conversación: timeout | hablemos del idioma quechua | respuesta de respaldo o texto limpio y corto | (113 car) 'No alcancé a entender esa frase. Intenta decirla un poco más despacio o prueba: «¿cómo digo amarillo' (4 ms) | 🟢 APROBADO | `evidencias/05_g04_traductor_groq.txt` |
| YURA-EXT-431 | conversacion | Groq en conversación: vacía | hablemos del idioma quechua | respuesta de respaldo o texto limpio y corto | (113 car) 'No alcancé a entender esa frase. Intenta decirla un poco más despacio o prueba: «¿cómo digo amarillo' (4 ms) | 🟢 APROBADO | `evidencias/05_g04_traductor_groq.txt` |
| YURA-EXT-432 | conversacion | Groq en conversación: choices=[] | hablemos del idioma quechua | respuesta de respaldo o texto limpio y corto | (113 car) 'No alcancé a entender esa frase. Intenta decirla un poco más despacio o prueba: «¿cómo digo amarillo' (4 ms) | 🟢 APROBADO | `evidencias/05_g04_traductor_groq.txt` |
| YURA-EXT-433 | conversacion | Groq en conversación: Markdown | hablemos del idioma quechua | respuesta de respaldo o texto limpio y corto | (69 car) "## Colores\n- **Puka**: rojo\n- *Q'illu*: amarillo\n1. [ver](http://x.y)" (4 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g04_traductor_groq.txt` |
| YURA-EXT-434 | conversacion | Groq en conversación: HTML | hablemos del idioma quechua | respuesta de respaldo o texto limpio y corto | (24 car) '<p>Rimaykullayki</p><br>' (4 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g04_traductor_groq.txt` |
| YURA-EXT-435 | conversacion | Groq en conversación: gigante | hablemos del idioma quechua | respuesta de respaldo o texto limpio y corto | (44999 car) 'Rimaykullayki. Rimaykullayki. Rimaykullayki. Rimaykullayki. Rimaykullayki. Rimaykullayki. Rimaykulla' (4 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g04_traductor_groq.txt` |
| YURA-EXT-436 | conversacion | Groq en conversación: cortada | hablemos del idioma quechua | respuesta de respaldo o texto limpio y corto | (37 car) 'La palabra en quechua para familia es' (4 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g04_traductor_groq.txt` |
| YURA-EXT-440 | conversacion | Historial tras 500 turnos | 500 turnos | historial acotado | historial en memoria=1000 mensajes (crece sin límite); enviados a Groq=10 (recortado a 8+2) (0 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g04_traductor_groq.txt` |
| YURA-EXT-441 | traductor | Tiempo máximo de espera del cliente Groq (configuración por defecto) | Groq(api_key) como lo crea main_robot | timeout corto (<15 s) para un robot interactivo | timeout=Timeout(connect=5.0, read=60, write=60, pool=60) max_retries=2 -> hasta ~3 min bloqueado si la red cuelga (cálculo, NO medido) (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g04_traductor_groq.txt` |
| YURA-EXT-450 | traductor | Groq REAL: palabra que no está en la BD | helicóptero | NO_ENCONTRADO (no inventar) | devolvió None (None = NO_ENCONTRADO) (488 ms) | 🟢 APROBADO | `evidencias/05_g04b_groq_real.txt` |
| YURA-EXT-451 | traductor | Groq REAL: palabra inventada | xqzv blorf | NO_ENCONTRADO | devolvió None (358 ms) | 🟢 APROBADO | `evidencias/05_g04b_groq_real.txt` |
| YURA-EXT-452 | traductor | Groq REAL: texto de 100.000 caracteres | 'palabra '*12500 | rechazo local antes de enviar | devolvió 'None'; ver log [ERROR GROQ] arriba (245 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g04b_groq_real.txt` |
| YURA-EXT-453 | conversacion | Groq REAL: pedir formato Markdown | Dame una lista con viñetas y negritas de 5 colores en que… | sin Markdown (lo pide el prompt) | "Lo siento, no puedo usar viñetas ni negritas, pero aquí tienes cinco colores en quechua: Puka, Anqas, Yuraq, Q'ello, Q'omer." (476 ms) | 🟢 APROBADO | `evidencias/05_g04b_groq_real.txt` |
| YURA-EXT-501 | conversacion | BD ausente: iniciar práctica | enséñame quechua | aviso claro sin excepción | 'No pude cargar una palabra del vocabulario local. Probemos más tarde.' (0 ms) | 🟢 APROBADO | `evidencias/05_g05_bd.txt` |
| YURA-EXT-502 | main_robot | BD ausente: inicializar_sistemas_locales | /tmp/claude-1000/-home-yura-Proyecto-Yura--cerebro-yura/e… | db_conn=None y alerta | db_conn=None (0 ms) | 🟢 APROBADO | `evidencias/05_g05_bd.txt` |
| YURA-EXT-503 | traductor | BD ausente: ejecutar_traducir | casa | aviso y volver al menú | ('menu', ['No puedo acceder al diccionario local ahora.']) (0 ms) | 🟢 APROBADO | `evidencias/05_g05_bd.txt` |
| YURA-EXT-504 | main_robot | BD ausente: arranque de BrainYura crea la BD? | /tmp/claude-1000/-home-yura-Proyecto-Yura--cerebro-yura/e… | no crear archivo vacío | archivo creado=False (0 ms) | 🟢 APROBADO | `evidencias/05_g05_bd.txt` |
| YURA-EXT-505 | main_robot | BD de 0 bytes: inicializar | archivo 0 bytes | alerta: BD sin vocabulario | db_conn=Connection; imprime '[OK] enlazada' sin avisar que no hay tablas (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g05_bd.txt` |
| YURA-EXT-506 | traductor | BD de 0 bytes: traducir 'casa' | casa | aviso de BD vacía | ('continuar', ['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra manera?']) (0 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g05_bd.txt` |
| YURA-EXT-507 | conversacion | BD de 0 bytes: práctica | enséñame quechua | aviso | 'No pude cargar una palabra del vocabulario local. Probemos más tarde.' (0 ms) | 🟢 APROBADO | `evidencias/05_g05_bd.txt` |
| YURA-EXT-508 | main_robot | Archivo de texto como BD: inicializar | texto plano | detectar y alertar | db_conn=Connection (lo da por bueno) (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g05_bd.txt` |
| YURA-EXT-509 | traductor | Archivo de texto como BD: traducir | casa | mensaje de error, sin excepción | EXCEPCIÓN NO CONTROLADA DatabaseError: file is not a database (1 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g05_bd.txt` |
| YURA-EXT-510 | conversacion | Archivo de texto como BD: práctica | enséñame quechua | mensaje, sin excepción | EXCEPCIÓN NO CONTROLADA DatabaseError: file is not a database (1 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g05_bd.txt` |
| YURA-EXT-511 | conversacion | Archivo de texto como BD: '¿cómo se dice casa?' | como se dice casa | mensaje, sin excepción | EXCEPCIÓN NO CONTROLADA DatabaseError: file is not a database (2 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g05_bd.txt` |
| YURA-EXT-512 | juego | Archivo de texto como BD: turno de juego | wasi | sin excepción | EXCEPCIÓN NO CONTROLADA DatabaseError: file is not a database (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g05_bd.txt` |
| YURA-EXT-513 | main_robot | Archivo de texto como BD: loop_principal en modo traductor | casa | el robot sigue vivo (captura el error) | loop_principal TERMINA con DatabaseError: file is not a database; en web/app.py el hilo muere y NO se llama os._exit -> la pantalla sigue mostrando el último estado (0… | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g05_bd.txt` |
| YURA-EXT-522 | web | Pantalla después de que el hilo del robot muere por la BD | GET /api/status | indicar que el robot no está funcionando | running=True state=TRADUCIR activity='MODO TRADUCTOR ACTIVO' (la pantalla dice que todo va bien) (3 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g05_bd.txt` |
| YURA-EXT-514 | traductor | Esquema raro: tablas detectadas | sin columnas, mayúsculas, comillas/SQL, espacio, nivel007 | ignorar las inválidas sin error; avisar de tablas ignoradas | detectadas=[('nivel007_ok', 7, 'ok')]; 'nivel1_Frutas' (con datos) se ignora EN SILENCIO; tabla t sigue existiendo=True (0 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g05_bd.txt` |
| YURA-EXT-515 | traductor | Esquema raro: buscar 'durazno' (tabla nivel1_Frutas) | durazno | encontrar o avisar | encontrado=False (0 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g05_bd.txt` |
| YURA-EXT-516 | traductor | Fila con quechua NULL: traducir 'casa' | casa | no decir 'None' | ['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra manera?'] (1 ms) | 🟢 APROBADO | `evidencias/05_g05_bd.txt` |
| YURA-EXT-517 | traductor | Fila con quechua vacío '': traducir 'sol' | sol | no quedar mudo / avisar | ['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra manera?'] (1 ms) | 🟢 APROBADO | `evidencias/05_g05_bd.txt` |
| YURA-EXT-518 | traductor | NULL en vocabulario enviado a Groq | casa sol wasi | no enviar 'None' como vocabulario verificado | '- Casa = None\n- None = Wasi' (1 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g05_bd.txt` |
| YURA-EXT-519 | conversacion | Práctica con filas quechua NULL / '' (20 semillas) | enséñame quechua | no decir 'None' ni una palabra vacía | con 'None'=11, vacías=9; ej: ['Practiquemos una palabra. En quechua se dice . Significa Sol: una palabra de uso cotidiano. Repítela, por favor.', 'Practiquemos una pal… | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g05_bd.txt` |
| YURA-EXT-520 | traductor | BD bloqueada (BEGIN EXCLUSIVE en otra conexión) | casa | mensaje de error, sin excepción | EXCEPCIÓN NO CONTROLADA OperationalError: database is locked (5007 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g05_bd.txt` |
| YURA-EXT-521 | traductor | BD con 50.187 filas: tiempo de búsqueda y de iniciar práctica | casa / quiero practicar | < 0,5 s | búsqueda=0.18s práctica=1.48s (lee TODAS las filas en cada consulta; práctica = 5 lecturas) (0 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g05_bd.txt` |
| YURA-EXT-601 | web | /api/status con robot None | GET | 200 BACKEND_NOT_STARTED | 200 BACKEND_NOT_STARTED (1 ms) | 🟢 APROBADO | `evidencias/05_g06_web.txt` |
| YURA-EXT-602 | web | /api/status con get_web_status que lanza excepción | GET | JSON de error controlado (p. ej. 503) que app.js pueda mostrar | 500 content-type=text/html; charset=utf-8 cuerpo=b'<!doctype html>\n<html lang=en>\n<title>500 Internal Server Error</title>\n<h1>Inte' (1 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g06_web.txt` |
| YURA-EXT-603 | web | /api/status con estado desconocido y web_status vacío | GET | 200 con valores por defecto | 200 {'activity': 'ACTIVIDAD DEL ROBOT', 'content': '', 'message': 'Yura está trabajando.', 'phase': 'ESPERANDO', 'result': None, 'robot': 'YURA', 'running': True, 'sta… | 🟢 APROBADO | `evidencias/05_g06_web.txt` |
| YURA-EXT-604 | web | /api/status con robot sin atributo running | GET | 200 o error controlado | 500 (1 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g06_web.txt` |
| YURA-EXT-605 | web | /api/status con HTML/<script> en content | <script>alert('x')</script><img src=x onerror=alert(1)> | JSON válido; la página lo pinta como texto (textContent) | 200; JSON devuelve el texto tal cual; app.js usa textContent (líneas 175-182) -> no se ejecuta (0 ms) | 🟢 APROBADO | `evidencias/05_g06_web.txt` |
| YURA-EXT-606 | web | /api/status con content de 1 MB | 1.048.576 caracteres 'Ñ' | limitar tamaño | 200 respuesta=6291702 bytes en 12 ms (sin límite de tamaño) (0 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g06_web.txt` |
| YURA-EXT-610 | web | GET /no-existe | /no-existe | 404/405 sin filtrar información | 404 (0 ms) | 🟢 APROBADO | `evidencias/05_g06_web.txt` |
| YURA-EXT-611 | web | GET /api/status/../../etc/passwd | /api/status/../../etc/passwd | 404/405 sin filtrar información | 404 (0 ms) | 🟢 APROBADO | `evidencias/05_g06_web.txt` |
| YURA-EXT-612 | web | POST /api/status | /api/status | 404/405 sin filtrar información | 405 (0 ms) | 🟢 APROBADO | `evidencias/05_g06_web.txt` |
| YURA-EXT-613 | web | DELETE /api/card | /api/card | 404/405 sin filtrar información | 405 (0 ms) | 🟢 APROBADO | `evidencias/05_g06_web.txt` |
| YURA-EXT-614 | web | PUT / | / | 404/405 sin filtrar información | 405 (0 ms) | 🟢 APROBADO | `evidencias/05_g06_web.txt` |
| YURA-EXT-620 | web | 1.000 peticiones seguidas a /api/status | 1000 x GET | todas 200; sin límite de frecuencia es observación | códigos={200} total=0.21s (0.2084 ms por petición) (0 ms) | 🟢 APROBADO | `evidencias/05_g06_web.txt` |
| YURA-EXT-621 | web | 1.000 peticiones en 10 hilos + escritor concurrente | 10x100 GET + 2000 _set_web_status | sin errores | errores=0 tiempo=0.25s (0 ms) | 🟢 APROBADO | `evidencias/05_g06_web.txt` |
| YURA-EXT-630 | web | Cabeceras de seguridad en GET / | GET / | CSP, nosniff, X-Frame-Options, Referrer-Policy | 200 faltan=['content-security-policy', 'x-content-type-options', 'x-frame-options', 'referrer-policy'] (0 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g06_web.txt` |
| YURA-EXT-631 | web | Cache-Control en /api/status | GET | no-store | Cache-Control=None (0 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g06_web.txt` |
| YURA-EXT-701 | tts | limpiar/formatear/visible | markdown | sin Markdown/HTML/URL; texto pronunciable | limpio="Colores Puka: rojo Q'illu: amarillo 1. [ver](http://x.y)" voz="Colores Puka: rojo Q'illu: amarillo 1. [ver](http://x.y)." visible="Colores Puka: rojo Q'illu: a… | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g07_tts.txt` |
| YURA-EXT-702 | tts | limpiar/formatear/visible | html | sin Markdown/HTML/URL; texto pronunciable | limpio='<p>Rimaykullayki</p><br>&nbsp;&amp;' voz='<p>Rimaykullayki</p><br>&nbsp;&amp;' visible='<p>Rimaykullayki</p><br>&nbsp;&amp;' (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g07_tts.txt` |
| YURA-EXT-703 | tts | limpiar/formatear/visible | url | sin Markdown/HTML/URL; texto pronunciable | limpio='Visita https://www.ejemplo.com/quechua?x=1&y=2 para más' voz='Visita https://www.ejemplo.com/quechua.x=1&y=2 para más.' visible='Visita https://www.ejemplo.com… | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g07_tts.txt` |
| YURA-EXT-704 | tts | limpiar/formatear/visible | tabla | sin Markdown/HTML/URL; texto pronunciable | limpio='¦ es ¦ qu ¦ ¦---¦---¦ ¦ casa ¦ wasi ¦' voz='¦ es ¦ qu ¦ ¦---¦---¦ ¦ casa ¦ wasi ¦.' visible='¦ es ¦ qu ¦ ¦---¦---¦ ¦ casa ¦ wasi ¦' (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g07_tts.txt` |
| YURA-EXT-705 | tts | limpiar/formatear/visible | solo_signos | sin Markdown/HTML/URL; texto pronunciable | limpio='¿¡?!...;;;' voz='.....;;;' visible='¿¡?!...;;;' (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g07_tts.txt` |
| YURA-EXT-706 | tts | limpiar/formatear/visible | espacios | sin Markdown/HTML/URL; texto pronunciable | limpio='' voz='.' visible='' (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g07_tts.txt` |
| YURA-EXT-707 | tts | limpiar/formatear/visible | guion_bajo | sin Markdown/HTML/URL; texto pronunciable | limpio='p unchay y NO ENCONTRADO' voz='p unchay, y NO ENCONTRADO.' visible='p unchay y NO ENCONTRADO' (0 ms) | 🟢 APROBADO | `evidencias/05_g07_tts.txt` |
| YURA-EXT-708 | tts | limpiar/formatear/visible | apostrofo | sin Markdown/HTML/URL; texto pronunciable | limpio="Allin p'unchay, Q'ello" voz="Allin p'unchay, Q'ello." visible="Allin p'unchay, Q'ello" (0 ms) | 🟢 APROBADO | `evidencias/05_g07_tts.txt` |
| YURA-EXT-709 | tts | limpiar/formatear/visible | pregunta | sin Markdown/HTML/URL; texto pronunciable | limpio='¿Imaynalla kachkanki?' voz='Imaynalla kachkanki.' visible='¿Imaynalla kachkanki?' (0 ms) | 🟢 APROBADO | `evidencias/05_g07_tts.txt` |
| YURA-EXT-710 | tts | limpiar/formatear/visible | abreviatura | sin Markdown/HTML/URL; texto pronunciable | limpio='Sr. Pérez dice: En quechua se dice Tata.' voz='Sr. Pérez dice: En quechua se dice Tata.' visible='Sr' (0 ms) | 🟢 APROBADO | `evidencias/05_g07_tts.txt` |
| YURA-EXT-711 | tts | limpiar/formatear/visible | traduccion | sin Markdown/HTML/URL; texto pronunciable | limpio='En quechua se dice: Tata. Significa padre.' voz='En quechua se dice: Tata. Significa padre.' visible=': Tata' (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g07_tts.txt` |
| YURA-EXT-712 | tts | limpiar/formatear/visible | asteriscos_mat | sin Markdown/HTML/URL; texto pronunciable | limpio='3 4 5 = 60' voz='3 4 5 = 60.' visible='3 4 5 = 60' (0 ms) | 🟢 APROBADO | `evidencias/05_g07_tts.txt` |
| YURA-EXT-720 | tts | texto extremo (rendimiento y longitud) | 10000_palabras | < 100 ms; limitar longitud visible/hablada | 1.1 ms; voz=10000 car; pantalla=9999 car (0 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g07_tts.txt` |
| YURA-EXT-721 | tts | texto extremo (rendimiento y longitud) | 10000_asteriscos | < 100 ms; limitar longitud visible/hablada | 1.2 ms; voz=1 car; pantalla=0 car (0 ms) | 🟢 APROBADO | `evidencias/05_g07_tts.txt` |
| YURA-EXT-722 | tts | texto extremo (rendimiento y longitud) | 5000_negritas | < 100 ms; limitar longitud visible/hablada | 1.7 ms; voz=5001 car; pantalla=5000 car (0 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g07_tts.txt` |
| YURA-EXT-723 | tts | texto extremo (rendimiento y longitud) | 10000_sin_punto | < 100 ms; limitar longitud visible/hablada | 0.6 ms; voz=10001 car; pantalla=10000 car (0 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g07_tts.txt` |
| YURA-EXT-730 | tts | hablar(): Edge TTS falla (sin internet), sin motor local | Rimaykullayki | reintenta 1 vez, avisa y NO se bloquea | procesos=['edge-tts', 'edge-tts'] estados=['HABLANDO', 'ESPERANDO'] 0 ms (0 ms) | 🟢 APROBADO | `evidencias/05_g07_tts.txt` |
| YURA-EXT-731 | tts | hablar(): Edge TTS falla, hay spd-say | Rimaykullayki | usa spd-say | procesos=['edge-tts', 'edge-tts', 'spd-say'] estados=['HABLANDO', 'ESPERANDO'] 0 ms (0 ms) | 🟢 APROBADO | `evidencias/05_g07_tts.txt` |
| YURA-EXT-732 | tts | hablar(): Sin ffmpeg ni reproductores | Rimaykullayki | avisa que no hay audio | procesos=['edge-tts'] estados=['HABLANDO', 'ESPERANDO'] 0 ms (0 ms) | 🟢 APROBADO | `evidencias/05_g07_tts.txt` |
| YURA-EXT-733 | tts | hablar(): Todos los reproductores fallan | Rimaykullayki | prueba todos y cae a motor local | procesos=['edge-tts', 'ffmpeg', 'wpctl', 'pw-play', 'ffplay', 'mpg123'] estados=['HABLANDO', 'ESPERANDO'] 0 ms (0 ms) | 🟢 APROBADO | `evidencias/05_g07_tts.txt` |
| YURA-EXT-734 | tts | hablar(): Camino normal | Rimaykullayki | edge-tts -> ffmpeg -> pw-play | procesos=['edge-tts', 'ffmpeg', 'wpctl', 'pw-play'] estados=['HABLANDO', 'ESPERANDO'] 0 ms (0 ms) | 🟢 APROBADO | `evidencias/05_g07_tts.txt` |
| YURA-EXT-740 | tts | hablar(): Edge TTS se cuelga 1,5 s por intento (red lenta) | Rimaykullayki | timeout en subprocess.run | bloqueado 3.0 s; llamadas SIN timeout=['edge-tts', 'edge-tts'] (un cuelgue real bloquea al robot indefinidamente) (3001 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g07_tts.txt` |
| YURA-EXT-741 | tts | hablar('     ') solo espacios | '     ' | no llamar a Edge TTS | procesos=['edge-tts', 'ffmpeg', 'pw-play'] (sintetiza '.') (2 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g07_tts.txt` |
| YURA-EXT-742 | tts | hablar('¿¡?!') solo signos | '¿¡?!' | no llamar a Edge TTS | procesos=['edge-tts', 'ffmpeg', 'pw-play'] texto enviado='..' (1 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g07_tts.txt` |
| YURA-EXT-743 | tts | hablar(None) | None | no hacer nada | procesos=[] (0 ms) | 🟢 APROBADO | `evidencias/05_g07_tts.txt` |
| YURA-EXT-750 | tts | Edge TTS real con texto que empieza por '--' | '--hola.' | sintetizar el texto (usar --text=<texto>) | returncode=2 stderr=['edge-tts: error: argument -t/--text: expected one argument'] (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g07_tts.txt` |
| YURA-EXT-801 | audio | Ningún dispositivo | query_devices()=[] | input_device=None y grabar devuelve None | audio=None bloques=0 (0 ms) | 🟢 APROBADO | `evidencias/05_g08_audio.txt` |
| YURA-EXT-802 | audio | query_devices lanza excepción | OSError | sin excepción | audio=None (0 ms) | 🟢 APROBADO | `evidencias/05_g08_audio.txt` |
| YURA-EXT-803 | audio | Dispositivo que falla al abrir | check_input_settings lanza | None sin excepción | audio=None (0 ms) | 🟢 APROBADO | `evidencias/05_g08_audio.txt` |
| YURA-EXT-804 | audio | Silencio absoluto | ceros | None tras espera_maxima (10 s = 125 bloques) | audio=None bloques leídos=130 (5 ms) | 🟢 APROBADO | `evidencias/05_g08_audio.txt` |
| YURA-EXT-805 | audio | Ruido constante alto (0,3 medio) desde el inicio | uniforme ±0,6 | terminar como máximo en duracion_maxima (15 s) | devuelve 15.0 s de audio; bloques=191 (el ruido estable se calibra; umbral máx 0,104) (36 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g08_audio.txt` |
| YURA-EXT-806 | audio | Ruido alto que empieza tras la calibración (TV/ventilador) | ceros y luego ±0,6 | terminar en duracion_maxima; no enviar 15 s de ruido al transcriptor | devuelve 14.8 s de audio; bloques=191 -> Gemini/Whisper reciben 15 s de ruido (24 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g08_audio.txt` |
| YURA-EXT-807 | audio | Voz que empieza a los 9,6 s y dura mucho | silencio 120 bloques + voz continua | grabar hasta 15 s DESDE que empieza la voz | audio=5.2 s (duracion_maxima cuenta desde el inicio de la escucha, no desde la voz) (13 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g08_audio.txt` |
| YURA-EXT-808 | audio | Clipping (amplitud 1,8 > 1,0) | onda cuadrada ±1,8 | int16 válido, sin overflow | 234240 muestras, max=32768 (27 ms) | 🟢 APROBADO | `evidencias/05_g08_audio.txt` |
| YURA-EXT-809 | audio | Bloques con NaN | NaN | None sin excepción | audio=None bloques=130 (5 ms) | 🟢 APROBADO | `evidencias/05_g08_audio.txt` |
| YURA-EXT-810 | audio | Parámetros extremos: bloque_ms=0 | bloque_ms=0 | error controlado | audio=None (112 ms) | 🟢 APROBADO | `evidencias/05_g08_audio.txt` |
| YURA-EXT-820 | audio | _calcular_umbral_ruido | 0 | valor en [0,006; 0,12] o error controlado | umbral=0.006 (0 ms) | 🟢 APROBADO | `evidencias/05_g08_audio.txt` |
| YURA-EXT-821 | audio | _calcular_umbral_ruido | -1 | valor en [0,006; 0,12] o error controlado | umbral=0.006 (0 ms) | 🟢 APROBADO | `evidencias/05_g08_audio.txt` |
| YURA-EXT-822 | audio | _calcular_umbral_ruido | nan | valor en [0,006; 0,12] o error controlado | umbral=0.006 (0 ms) | 🟢 APROBADO | `evidencias/05_g08_audio.txt` |
| YURA-EXT-823 | audio | _calcular_umbral_ruido | 1.0 | valor en [0,006; 0,12] o error controlado | umbral=0.10400000000000001 (0 ms) | 🟢 APROBADO | `evidencias/05_g08_audio.txt` |
| YURA-EXT-824 | audio | _calcular_umbral_ruido | inf | valor en [0,006; 0,12] o error controlado | umbral=0.10400000000000001 (0 ms) | 🟢 APROBADO | `evidencias/05_g08_audio.txt` |
| YURA-EXT-825 | audio | _calcular_umbral_ruido | None | valor en [0,006; 0,12] o error controlado | umbral=0.006 (0 ms) | 🟢 APROBADO | `evidencias/05_g08_audio.txt` |
| YURA-EXT-826 | audio | _calcular_umbral_ruido | 'abc' | valor en [0,006; 0,12] o error controlado | ValueError: could not convert string to float: 'abc' (solo recibe floats en el flujo real) (0 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g08_audio.txt` |
| YURA-EXT-830 | audio | YURA_INPUT_DEVICE apunta a índice inexistente | 99 | usar otro dispositivo o avisar | input_device=0 (se ignora el índice y usa el disponible) (0 ms) | 🟢 APROBADO | `evidencias/05_g08_audio.txt` |
| YURA-EXT-901 | claves | cargar_archivo_claves | 'YT_BOM' | 'valor_bom' | None (quedó guardada como '\ufeffYT_BOM') (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g09_10_claves_concurrencia.txt` |
| YURA-EXT-902 | claves | cargar_archivo_claves | 'YT_SIN_IGUAL' | None | None (0 ms) | 🟢 APROBADO | `evidencias/05_g09_10_claves_concurrencia.txt` |
| YURA-EXT-903 | claves | cargar_archivo_claves | 'YT_DOBLES' | 'con comillas' | 'con comillas' (0 ms) | 🟢 APROBADO | `evidencias/05_g09_10_claves_concurrencia.txt` |
| YURA-EXT-904 | claves | cargar_archivo_claves | 'YT_SIMPLES' | 'simples' | 'simples' (0 ms) | 🟢 APROBADO | `evidencias/05_g09_10_claves_concurrencia.txt` |
| YURA-EXT-905 | claves | cargar_archivo_claves | 'YT_MIXTAS' | None | 'abre doble cierra simple' (comillas desbalanceadas) (0 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g09_10_claves_concurrencia.txt` |
| YURA-EXT-906 | claves | cargar_archivo_claves | 'YT_ESPACIOS' | 'con espacios' | 'con espacios' (0 ms) | 🟢 APROBADO | `evidencias/05_g09_10_claves_concurrencia.txt` |
| YURA-EXT-907 | claves | cargar_archivo_claves | 'YT_EXPORT' | 'exportada' | 'exportada' (0 ms) | 🟢 APROBADO | `evidencias/05_g09_10_claves_concurrencia.txt` |
| YURA-EXT-908 | claves | cargar_archivo_claves | 'YT_EXPORT2' | 'doble espacio' | 'doble espacio' (0 ms) | 🟢 APROBADO | `evidencias/05_g09_10_claves_concurrencia.txt` |
| YURA-EXT-909 | claves | cargar_archivo_claves | 'YT_COMENTARIO' | 'valor' | 'valor # comentario en línea' (0 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g09_10_claves_concurrencia.txt` |
| YURA-EXT-910 | claves | cargar_archivo_claves | 'YT_VACIA' | None | None (0 ms) | 🟢 APROBADO | `evidencias/05_g09_10_claves_concurrencia.txt` |
| YURA-EXT-911 | claves | cargar_archivo_claves | 'YT_IGUAL' | 'a=b=c' | 'a=b=c' (0 ms) | 🟢 APROBADO | `evidencias/05_g09_10_claves_concurrencia.txt` |
| YURA-EXT-912 | claves | cargar_archivo_claves | 'YT_DUP' | 'segunda' | 'primera' (convención dotenv: gana la última) (0 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g09_10_claves_concurrencia.txt` |
| YURA-EXT-913 | claves | cargar_archivo_claves | 'YT_CRLF' | 'windows' | 'windows' (0 ms) | 🟢 APROBADO | `evidencias/05_g09_10_claves_concurrencia.txt` |
| YURA-EXT-914 | claves | cargar_archivo_claves | 'YT_SOLO_COMILLAS' | None | None (0 ms) | 🟢 APROBADO | `evidencias/05_g09_10_claves_concurrencia.txt` |
| YURA-EXT-915 | claves | cargar_archivo_claves | 'yt minus' | None | 'con espacio en la clave' (0 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g09_10_claves_concurrencia.txt` |
| YURA-EXT-916 | claves | cargar_archivo_claves | 'YT_COMENTADA' | None | None (0 ms) | 🟢 APROBADO | `evidencias/05_g09_10_claves_concurrencia.txt` |
| YURA-EXT-930 | claves | cargar_archivo_claves con .env.local sin permisos | chmod 000 | aviso sin excepción | sin excepción (ver [ALERTA CLAVES] en log) (0 ms) | 🟢 APROBADO | `evidencias/05_g09_10_claves_concurrencia.txt` |
| YURA-EXT-931 | claves | '.env.local' es una carpeta | directorio | ignorar sin excepción | sin excepción (0 ms) | 🟢 APROBADO | `evidencias/05_g09_10_claves_concurrencia.txt` |
| YURA-EXT-932 | claves | '.env.local' binario | bytes 0-255 | sin excepción | sin excepción (0 ms) | 🟢 APROBADO | `evidencias/05_g09_10_claves_concurrencia.txt` |
| YURA-EXT-950 | main_robot | _set_web_status/get_web_status desde 16 hilos | 8 escritores x5000 + 8 lectores x5000 | sin errores, content y translation siempre del mismo evento | errores=0 incoherentes=0 tiempo=0.25s (0 ms) | 🟢 APROBADO | `evidencias/05_g09_10_claves_concurrencia.txt` |
| YURA-EXT-951 | conversacion | Conexión SQLite de conversacion usada desde otro hilo | procesar_entrada('quiero practicar') en hilo 2 | funciona o error controlado | ProgrammingError: SQLite objects created in a thread can only be used in that same thread. The object was created in thread id 129989975695488 and this is thread id 12… | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g09_10_claves_concurrencia.txt` |
| YURA-EXT-952 | traductor | db_conn compartida (check_same_thread=False) por 8 hilos | 8 x 200 búsquedas | sin errores | errores=6 ["IndexError('tuple index out of range')", "IndexError('tuple index out of range')"] (0 ms) | 🟠 REQUIERE CORRECCIÓN | `evidencias/05_g09_10_claves_concurrencia.txt` |
| YURA-EXT-953 | conversacion | Estado de práctica global (_sesion_educativa) compartido por módulo | otra parte del programa cancela la sesión | sesión por usuario/robot | tras cancelar, la respuesta correcta 'K'uchillu' ya no se evalúa: 'Soy Yura, un robot educativo que ayuda a practicar quechua. Puedo enseñarte voca' (1 ms) | 🟡 OBSERVACIÓN | `evidencias/05_g09_10_claves_concurrencia.txt` |

## 6. Problemas priorizados y propuesta (NO aplicada)

| # | Prioridad | Problema | IDs | Propuesta |
|---|---|---|---|---|
| 1 | CRÍTICO | «apagar» en cualquier parte de la frase apaga el robot y el proceso web | 151-153 (090, 095) | Aceptar solo órdenes completas («apágate», «yura apágate», «apagar yura») comparando la frase entera o un patrón anclado. Pedir confirmación por voz («¿Seguro que me apago? Di sí»). Nunca apagar si la frase contiene «cómo se dice», «no» o «traduce». |
| 2 | ALTO | El evaluador acepta palabras quechuas distintas | 215, 314 | Unificar `_respuesta_es_correcta` y `_evaluar_respuesta` en una sola función. Umbral más alto para palabras cortas (p. ej. igualdad fonética exacta tras normalizar si hay ≤5 letras). Rechazar si la respuesta coincide exactamente con **otra** palabra de la BD. Probarlo con los 141 pares como caso de regresión. |
| 3 | ALTO | BD dañada o bloqueada tumba el hilo del robot y la pantalla sigue diciendo «activo» | 508-513, 520, 522 | Al arrancar, validar la BD con `PRAGMA quick_check` y comprobar que haya al menos una tabla válida con filas; si no, avisar por voz. Envolver `buscar_vocabulario` y `_leer_registros_vocabulario` en `try/except sqlite3.Error` y devolver «sin resultados». En `loop_principal`, capturar `Exception` por vuelta (registrar, avisar y seguir). En `web/app.py`, poner `running=False` o fase ERROR si el hilo termina. Abrir en solo lectura (`mode=ro`) con `timeout` corto. |
| 4 | ALTO | Órdenes por subcadena que chocan con el vocabulario («adiós», «menú», «volver», «menudo», «conjugar», «guarda silencio» en SILENCIO) | 019-021, 043, 067, 091-093, 115-117, 154-157, 160-164 | Detectar órdenes por **palabra completa** (tokens, `\b…\b`) y solo si la frase no es una consulta («cómo se dice X», «traduce X» tienen prioridad). Unificar la tabla de órdenes en un solo módulo. En SILENCIO, quitar «silencio» de las palabras que despiertan. |
| 5 | MEDIO | Bucles sin límite: juego con respuestas vacías, palabra sin traducción, traductor con escucha vacía | 203, 204, 422 | Contador de intentos fallidos: tras 3, pasar a la siguiente palabra y, tras N silencios, volver al menú o a SILENCIO. Si no hay traducción, avanzar el índice. |
| 6 | MEDIO | Salida de Groq sin validar (NO ENCONTRADO con variantes, Markdown/HTML, cortada, gigante) | 412-419, 433-436, 701-704 | Normalizar la respuesta: quitar etiquetas HTML y Markdown (incluidos enlaces y URLs), detectar `NO[_ ]ENCONTRADO` en cualquier parte, descartar si `finish_reason=='length'` y recortar a 1–2 frases o unos 250 caracteres antes de `hablar`. |
| 7 | MEDIO | Texto sin límite hacia Groq | 028, 029, 421, 452 | Recortar la entrada (p. ej. 300 caracteres) antes de `traducir_online` y `_consultar_groq`. |
| 8 | MEDIO | Subprocesos de voz sin `timeout`; cliente Groq con 60 s × 3 | 740, 441 | `subprocess.run(..., timeout=20)` capturando `TimeoutExpired`. `Groq(api_key, timeout=10, max_retries=1)`. |
| 9 | MEDIO | «: Tata» en pantalla | 711 | En `main_robot.py:189`, cambiar `:??` por `:?` o hacer `lstrip(": ")` del resultado. Añadir una prueba unitaria con la frase exacta del traductor. |
| 10 | MEDIO | Práctica: «repite» cambia de palabra; órdenes sin sesión; respuesta correcta no evaluada; pregunta tomada como respuesta | 301-303, 305, 316, 320 | «repite» debe repetir el registro actual y «siguiente» cambiarlo. Procesar la sesión **antes** de las frases locales. Detectar la intención «traducir» antes de evaluar. Atender «repetir» sin sesión con «¿Quieres practicar? Di enséñame». |
| 11 | MEDIO | BD vacía, de texto o con NULL aceptada sin validar | 505, 508, 514-519 | Validar al cargar. Filtrar filas con `palabra_frase`/`traduccion` NULL o vacías en `_leer_registros_vocabulario`. Avisar en el log de las tablas ignoradas. |
| 12 | MEDIO | BOM en `.env.local` | 901 | Abrir con `encoding="utf-8-sig"` (o usar `python-dotenv`). |
| 13 | BAJO | Juego: felicita con 0 aciertos; lista vacía; mapeo de emergencia contradice la BD (agua=yaku) | 201, 205, 206, 214 | Contar aciertos y decir el puntaje. Si la lista está vacía, avisar. Eliminar el mapeo de emergencia o alinearlo con la BD (decisión de un hablante). |
| 14 | BAJO | Web: 500 en HTML, sin cabeceras de seguridad, sin límite de tamaño | 602, 604, 606, 630, 631 | `try/except` en `_status_payload` que devuelva JSON 503. `after_request` con CSP, nosniff, DENY y `no-store`. Recortar `content` a unos 500 caracteres. |
| 15 | BAJO | TTS: se sintetiza «.» con texto vacío o solo signos; texto que empieza por «--» | 705, 706, 741, 742, 750 | En `hablar`, salir si `texto_voz.strip(" .,;:")` está vacío. Pasar `--text=` + texto como un único argumento. |
| 16 | BAJO | Audio: la duración máxima incluye la espera; ruido de 15 s enviado al transcriptor | 806, 807 | Contar `duracion_maxima` desde que se detecta la voz. Descartar grabaciones con energía casi constante (ruido). |
| 17 | BAJO | Mensaje «no vendo autos ni converso en inglés» ante palabras válidas («noche», números) | 024, 096, 120 | Consultar primero el diccionario local (como hace el traductor) antes de decidir que está fuera de tema. Mensaje más neutro. |
| 18 | BAJO | Concurrencia latente (conexión de conversación ligada a un hilo, conexión compartida, sesión global, historial sin límite) | 951-953, 440 | Una conexión por hilo, o un lock alrededor de las consultas. Recortar `historial_conversacion` a los últimos 8 mensajes. |
| 19 | BAJO | `loop_principal()` se llama dos veces en `__main__` | E13 | Borrar la segunda llamada (`main_robot.py:1226`). |

---
Scripts: `documentacion_pruebas/evidencias/05_scripts/` (comun.py, g01_entradas.py, g02_03_juego_practica.py, g04_traductor_groq.py, g04b_groq_real.py, g05_bd.py, g06_web.py, g07_tts.py, g08_audio.py, g09_10_claves_concurrencia.py).
