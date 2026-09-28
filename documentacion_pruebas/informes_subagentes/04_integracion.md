# 04 — Pruebas de configuración e integración (Fases 7 y 11)

- Subagente: 4 (configuración e integración). Fecha: 2026-09-27.
- Proyecto: `/home/yura/Proyecto Yura /cerebro_yura` (solo lectura; no se modificó ningún archivo del proyecto).
- Evidencias: `documentacion_pruebas/evidencias/04_*.txt`, `04_cadena_voz.json` y scripts en `evidencias/04_scripts/`. No contienen claves (comprobado con `grep -E 'gsk_|AIza'`: la única coincidencia es el texto del propio comando en `04_rutas_scripts.txt:3`).
- Llamadas a servicios en línea: **16 reales** (Edge TTS 13, Gemini 2, Groq 1), más 7 transcripciones Gemini que el código ya no envió porque había desactivado el cliente. Aun contándolas, son 23, por debajo del límite de 25. Las simulaciones sin internet no hicieron ninguna petición real porque se ejecutaron en un espacio de red aislado (`unshare -rn`).
- El robot real (`web/app.py`) se arrancó una vez (PID 53270), se detuvo con SIGTERM y se comprobó que el **puerto 5000 quedó libre** (`ss -ltn` → "PUERTO 5000 LIBRE"; no queda ningún proceso `python … web/app.py`).

---

## 1. Resumen ejecutivo

1. **Arranque real VERIFICADO:** `/api/status` respondió **4,08 s** después del lanzamiento. Se cargan Whisper "base" en GPU (cuda:0), Gemini, Groq, Vosk y la BD. El micrófono elegido es el C-Media USB (hw:2,0, 48 kHz, mono). El proceso usa unos 0,96–1,5 GB de RAM (RSS) y 486 MiB de GPU.
2. **Endpoints VERIFICADOS:** `/`, `/api/status` y `/api/card` responden 200 con una mediana de 0,6–0,8 ms (10 repeticiones). El esquema JSON es correcto. Las rutas inexistentes devuelven 404 y POST/PUT devuelven 405. El servidor escucha en 0.0.0.0 y responde por la IP de la red local sin autenticación.
3. 🔴 **Gemini, el transcriptor principal, está inutilizable:** devuelve el error `429 RESOURCE_EXHAUSTED` con **límite gratuito de 20 peticiones por día y por modelo** (`gemini-3.8-flash`). Tras el primer 429 el código desactiva Gemini hasta reiniciar y toda la transcripción pasa a Whisper. La precisión de Gemini queda **NO VERIFICADA**.
4. **Cadena de voz completa (voz sintética → Whisper → decisión → respuesta) VERIFICADA con 8 frases:** Whisper acertó **8/8** (WER 0) en 0,24–0,38 s en GPU (1,12–1,74 s en CPU). Con dos palabras quechua que no están en el `initial_prompt` acertó 1/2 ("Allqo" → "Ayo"). La voz de entrada es sintética (es-MX), no la de un niño, así que estas cifras **no** sirven como precisión en el aula.
5. **RNF-01 (≤ 2,5 s):** el procesamiento (ASR + decisión + generación de voz) tarda unos **1,9–2,0 s** cuando la respuesta sale del diccionario local y unos **2,7 s** cuando usa Groq. Si se suma el segundo fijo de silencio que el robot espera antes de dar por terminada la frase (`silencio_final=1.0`), el turno percibido es de **2,9–3,7 s**. 🟠 El requisito **no se cumple** en el turno percibido.
6. **Salida de audio VERIFICADA:** edge-tts (código 0, 1,7 s) → ffmpeg (0,04 s) → `pw-play --target 242` (código 0) hacia el sink por defecto "HDA NVidia Digital Stereo (HDMI)", que es el televisor. El log dice "Salida seleccionada: USB Audio Device", pero ese valor no se usa para reproducir.
7. **Sin internet:** Gemini pasa a Whisper en 0,04 s; Groq devuelve un mensaje genérico; Edge TTS falla y el código usa `spd-say` (espeak-ng, código 0). La traducción con el diccionario local sigue funcionando. 🔴 **Si la red se queda "colgada"** (hay conexión pero no llegan respuestas), cada turno pierde 12 s en Gemini y **Groq bloquea el robot más de 100 s** (el SDK usa 60 s de espera × 3 intentos).
8. 🔴 **No hay integración entre el cerebro y la plataforma Laravel.** El cerebro no tiene ningún cliente HTTP. Laravel ofrece `POST /api/v1/robot/activity`, pero nadie la llama. La tabla `phonetic_evaluations` (RF-05) **no existe** en las migraciones. La conexión "WiFi / REST" del diagrama de despliegue de la tesis (pdf 58) no está implementada.
9. 🔴 **El hardware prometido no existe:** no hay ESP32 ni dispositivos `/dev/ttyUSB*` o `/dev/ttyACM*`, `pyserial` no está instalado y no hay pantalla táctil. Tampoco están instalados Faster-Whisper ni SciPy (la tesis, pdf 59, afirma haber usado "Faster-Whisper int8" y un "filtro paso banda SciPy"). El sistema operativo real es Ubuntu 24.04 en un i3-10100 con 16 GB de RAM y GPU GTX 1650, no el "Debian 13 / i3 3ra gen / 8 GB" de la tesis.
10. 🟠 **Los scripts de despliegue no sirven en esta máquina.** `yura.service` y `yura.desktop` apuntan a `/home/yura/Documents/YURAQUECHUA/Proyecto_Quechua`, que no existe. El servicio correría como root y declara un micrófono Logitech. `yura-open-browser.sh` necesita Chrome o Chromium (no están instalados; solo hay Firefox) y abre `yura.local`, que **no resuelve** (`gaierror -2`). Ni el servicio ni el arranque automático están instalados.

---

## 2. Configuración y dependencias

Evidencia: `04_configuracion.txt` y `04_variables_gitignore.txt`.

| Elemento | Resultado | Estado |
|---|---|---|
| Python | `.venv` usa 3.12.3 (el del sistema también es 3.12.3) | 🟢 |
| `requirements.txt` (9 paquetes) | Todos instalados: flask 3.1.3, groq 1.7.0, vosk 0.3.45, openai-whisper 20250625, sounddevice 0.5.6, numpy 2.5.3, google-genai 2.25.0, edge-tts 7.2.8, pytest 9.1.1. `pip check`: "No broken requirements found". El venv tiene 85 paquetes | 🟡 sin versiones fijas: la instalación no es reproducible |
| Paquetes del sistema | ffmpeg 6.1.1, pw-play (libpipewire 1.0.5), wpctl, libportaudio2 19.6.0, wireplumber 0.4.17 y spd-say (espeak-ng) presentes. **No están** mpg123, espeak ni pactl. `edge-tts` no está en el PATH (el código usa `.venv/bin/edge-tts`) | 🟢 / 🟡 los respaldos mpg123 y espeak del código no pueden ejecutarse |
| `.env.local` | Existe, permisos `-rw------- 600` y propietario yura. Define `GROQ_API_KEY` (1 línea no vacía) y `GEMINI_API_KEY` (1). No se leyeron los valores | 🟢 |
| `.gitignore` | `git check-ignore` confirma que se ignoran `.env.local` (regla `.env*`), `diccionario.db` y `diccionario.respaldo.db` (`*.db`), `yura_temp.wav` y `clave api.txt`. `.env.example` queda permitido. `model/` (Vosk, 58 MB, sin uso) **sí** está en Git | 🟢 / 🟡 |
| Claves en el historial de Git | 0 commits tocan `.env*` o `clave api.txt`; 0 coincidencias `gsk_`/`AIza` en todo el historial y en el árbol de trabajo | 🟢 |

**Variables de entorno que lee el código:**

| Variable | Archivo:línea | Valor por defecto | Observación |
|---|---|---|---|
| `GROQ_API_KEY` | main_robot.py:598 | — | Si falta, además busca en .env, ~/.env, .bashrc, .profile y .zshrc, y ejecuta `bash -lc`/`zsh -lc` con `shell=True` (main_robot.py:644-662) |
| `GEMINI_API_KEY` / `GOOGLE_API_KEY` | gemini_transcriber.py:27-28 | — | |
| `YURA_GEMINI_ENABLED` | gemini_transcriber.py:22 | `1` | No aparece en `.env.example` |
| `YURA_GEMINI_TRANSCRIBE_MODEL` | gemini_transcriber.py:17 | `gemini-3.8-flash` | Cuota gratuita de 20 peticiones al día (ver §5) |
| `YURA_GROQ_MODEL` | traductor.py:281 | `openai/gpt-oss-120b` | 🟡 `scripts/yura.service` fija `openai/gpt-oss-20b`: el modelo cambia según cómo se arranque el robot |
| `YURA_WHISPER_MODEL` | main_robot.py:417 | `base` | |
| `YURA_INPUT_DEVICE` / `YURA_OUTPUT_DEVICE` | audio_manager.py:297 / 359 | vacío (automático) | Con el valor del servicio ("Logitech USB Headset") o un índice inexistente (99), el robot sigue eligiendo el C-Media: **VERIFICADO** (`04_microfono.txt`) |

El shell actual no tiene definida ninguna variable `YURA_*` ni de claves. `.bashrc` y `.profile` tienen 0 menciones a `GROQ_API_KEY`.

## 3. Rutas y scripts

Evidencia: `04_rutas_scripts.txt`.

- **Código Python:** las rutas se construyen de forma relativa a `__file__` (diccionario.db, model/, .env.local, `.venv/bin/edge-tts`), así que funcionan sin importar el directorio de trabajo. 🟢 Solo hay rutas de `~` en los comandos de shell de `_obtener_api_key_groq` (main_robot.py:645-647).
- **Archivo temporal dentro del proyecto:** `escuchar_voz` escribe `yura_temp.wav` en la carpeta del proyecto (main_robot.py:800-811) y lo borra en `finally`. 🟡 Con un servicio que corre como root, el directorio tendría que ser escribible.
- **`scripts/yura.service`:**
  - `WorkingDirectory`, `EnvironmentFile` y `ExecStart` apuntan a `/home/yura/Documents/YURAQUECHUA/Proyecto_Quechua`, que **NO EXISTE**.
  - `EnvironmentFile` no lleva el prefijo `-`, así que systemd no arrancaría el servicio si falta ese archivo (análisis de configuración; no se instaló el servicio).
  - No tiene `User=` y `comandospara ejecutaryura.txt` usa `sudo systemctl` → correría como **root**. PipeWire es una sesión del usuario, así que root no podría usar `pw-play`/`wpctl` del usuario (NO VERIFICADO por ejecución).
  - Declara el micrófono "Logitech USB Headset", pero el conectado es un C-Media.
  - `systemctl status yura.service` → "Unit yura.service could not be found": **el servicio no está instalado**.
- **`scripts/yura.desktop`:** `Exec=` apunta a la misma ruta inexistente. No existe en `~/.config/autostart/`.
- **`scripts/yura-open-browser.sh`:**
  - Busca solo google-chrome o chromium en 5 rutas y **ninguna existe** (solo `/usr/bin/firefox` y `/snap/bin/firefox`), así que termina con "No se encontró Chrome/Chromium" y `exit 1`.
  - Usa `http://yura.local:5000/`, pero `socket.gethostbyname('yura.local')` da `gaierror [Errno -2] Name or service not known`. El nombre del equipo es `yura-System-Product-Name`; avahi está activo, pero publicaría `yura-System-Product-Name.local`.
- **`comandospara ejecutaryura.txt`:** empieza con "Buenas tardes." y contiene comandos `sudo systemctl … yura.service` para un servicio que no está instalado.

## 4. Arranque real y endpoints

Evidencia: `04_arranque_log.txt` y `04_endpoints.txt`.

**Comando:** `cd "/home/yura/Proyecto Yura /cerebro_yura" && .venv/bin/python web/app.py > <scratchpad>/integracion/yura.log 2>&1 &`. Antes de arrancar se comprobó que el puerto estaba libre y que no había otros procesos del robot.

- **Tiempo hasta que `/api/status` responde 200: 4,08 s.** `BrainYura()` se construye antes de `app.run`, así que ese tiempo incluye la carga de Whisper.
- **Log de inicio, en orden:**
  - carga de Vosk (modelo que no se usa);
  - `[OK]: Claves cargadas desde '.env.local'`;
  - lista de 18 dispositivos de audio;
  - `Entrada seleccionada: USB Audio Device: - (hw:2,0)`, 1 canal, 48000 Hz;
  - `Salida seleccionada: USB Audio Device`;
  - `[WHISPER]: Modelo cargado base`;
  - `[GEMINI]: Transcriptor listo (gemini-3.8-flash)`;
  - `[OK GROQ]: Cliente Groq inicializado`;
  - `[OK]: Base de datos 'diccionario.db' enlazada`;
  - saludo `[YURA HABLA]: Ñuqaqa Yura kani…`;
  - Flask en `0.0.0.0:5000` (incluida la IP de la red local 192.168.40.194) con la advertencia "development server".
- **Calibración del micrófono en marcha:** `ruido=0.0003; umbral=0.0060`, y después "No se detectó voz dentro del tiempo de espera" (el ciclo se repite cada 10 s).
- **Recursos:** RSS de 957 MB a los 17 s y 1,5 GB en `top`; VSZ de 12–13 GB; CPU de 12–26 % en los primeros segundos y de 0–2 % en reposo. En GPU, el proceso usa **486 MiB** (el total subió de 1550 a 2109 MiB y volvió a 1699 MiB al detenerlo).
- 🟡 **Log excesivo:** 171 líneas y 8,3 KB cada 10 s solo en reposo, por las líneas `[DEBUG AUDIO] antes/después…`; son unos 72 MB al día en journald/stdout. De 949 líneas, 710 eran `DEBUG AUDIO`.
- Mientras el robot estuvo encendido, algún cliente externo consultaba `/api/status` cada 5 s, probablemente una pantalla o navegador abierto.

**Endpoints (10 repeticiones cada uno):**

| Ruta | Código | Tipo | Bytes | Mín / mediana / media / máx (ms) |
|---|---|---|---|---|
| `GET /` | 200 | text/html | 4770 | 0,7 / 0,8 / 3,3 / 26,2 (la primera petición, sin caché, fue la lenta) |
| `GET /api/status` | 200 | application/json | 406 | 0,5 / 0,6 / 0,6 / 0,6 |
| `GET /api/card` | 200 | application/json | 1069 | 0,5 / 0,6 / 0,6 / 0,8 |
| `GET /no-existe` | 404 | html | — | 0,7 |
| `POST /api/status`, `POST /api/card`, `PUT /api/status` | 405 | html | — | 0,7–0,9 |
| `GET /static/../../.env.local` y la variante codificada `%2f` | 404 | — | — | Sin salto de directorio 🟢 |

- **Esquema de `/api/status`:** tiene exactamente las 10 claves esperadas (`robot, state, running, activity, message, phase, content, translation, result, updated_at`) y los tipos son correctos → **OK**.
- **Esquema de `/api/card`:** 6 ejemplos con 6 campos de texto cada uno → **OK**. 🟡 En los 6, `meaning` es igual a `written` (hallazgo ya conocido).
- **Recursos de la página:** `style.css` (21803 B), `style-draft.css` (3593 B) y `app.js` (8423 B) responden 200.
- **Cabeceras:** no hay CORS ni cabeceras de seguridad (`Server: Werkzeug/3.1.8 Python/3.12.3`). La API responde desde la red local sin autenticación. 🟡 Es de solo lectura y su contenido es de baja sensibilidad.

## 5. Cadena de voz completa (sin micrófono humano)

Evidencia: `04_cadena_voz.txt`, `04_cadena_voz.json`, `04_gemini_diagnostico.txt`, `04_groq_y_salida_audio.txt`, `04_whisper_cpu.txt`. Script: `04_scripts/cadena.py`.

**Método:**
- El robot real estaba **apagado** durante la prueba.
- Se generó cada frase con `.venv/bin/edge-tts --voice es-MX-DaliaNeural`, en 1,49–1,82 s por frase (código 0).
- Cada MP3 se convirtió con ffmpeg a WAV de 16 kHz, mono y 16 bits (se verificó el formato `(16000, 1, 2)`).
- Se siguió **el mismo camino que `escuchar_voz`**: los bytes PCM se escriben en un WAV con 0,25 s de silencio añadido; primero Gemini (`GeminiTranscriber.transcribir` real); después Whisper "base" con exactamente los mismos parámetros e `initial_prompt` que main_robot.py:823-841; y normalización con `BrainYura._normalizar_texto`.
- La decisión se tomó con el código real: se creó un `BrainYura` sin `__init__` (para no abrir el micrófono) y se llamó a `ejecutar_menu()` con `escuchar_voz` sustituido por el texto transcrito. Se capturó lo que el robot iba a decir.
- La BD se abrió **en solo lectura**, también en `conversacion._conexion_vocabulario`.

**Gemini:**
- La primera llamada devolvió `429 RESOURCE_EXHAUSTED` tras 0,89 s. El diagnóstico aparte muestra `quotaId: GenerateRequestsPerDayPerProjectPerModel-FreeTier, quotaValue: '20', model: gemini-3.8-flash`.
- El código pone `self.client = None` (gemini_transcriber.py:83-88), así que las 7 frases siguientes pasaron directamente a Whisper (0,00 s).
- 🔴 Con **20 peticiones al día**, una sola clase agota Gemini en pocos minutos. Esa cuota se había consumido hoy antes de esta prueba. **Precisión de Gemini con quechua: NO VERIFICADO.**

**Tabla por frase (tiempos en segundos):**

| # | Frase | Gemini | Whisper (texto) | Whisper (t, GPU) | Decisión (código real) | t decisión | Groq | Voz de respuesta (edge-tts) | Procesamiento* | Turno percibido** |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | jugar | 429 (0,89) | "Jugar" ✔ | 0,24 | Estado → JUEGO (luego el juego pregunta) | 0,000 | — | ~1,6 (est.) | 1,89 (+0,89 del 429 en este primer turno) | 2,89 (3,78) |
| 2 | traducir | no enviada | "Traducir." ✔ | 0,27 | → TRADUCIR, "Modo traductor. Dime una palabra…" | 0,000 | — | ~1,6 (est.) | 1,92 | 2,92 |
| 3 | perro | no enviada | "Perro." ✔ | 0,26 | En el MENÚ → CONVERSAR y responde "Soy Yura… **no vendo autos ni converso en inglés**" 🟠 | 0,001 | — | ~1,6 (est.) | 1,91 | 2,91 |
| 3b | perro (modo TRADUCIR) | — | (mismo texto) | — | "En quechua se dice: Allqo. Animal doméstico común." | 0,003 | — | **1,70 (medido)** | 2,01 | 3,01 |
| 4 | buenas noches | no enviada | "Buenas noches." ✔ | 0,29 | "Para decir buenas noches en quechua, usa «Allin tuta»…" (BD) | 0,003 | — | ~1,6 (est.) | 1,94 | 2,94 |
| 5 | ¿cómo se dice gato en quechua? | no enviada | "¿Cómo se dice gato en quechua?." ✔ | 0,38 | "En quechua se dice Misi, que significa gato…" (BD) | 0,003 | — | ~1,6 (est.) | 2,04 | 3,04 |
| 6 | enséñame quechua | no enviada | "Enséñame quechua." ✔ (se normaliza a "ense ame quechua": la ñ se pierde, pero la intención se reconoce) | 0,32 | Empieza la práctica: "…En quechua se dice Chunka pusqayuq. Significa Dieciocho…" | 0,009 | — | ~1,6 (est.) | 1,98 | 2,98 |
| 7 | Rimaykullayki | no enviada | "Rimaykullayki." ✔ | 0,32 | "Rimaykullayki significa hola. Es un saludo en quechua." (local) | 0,000 | — | ~1,6 (est.) | 1,97 | 2,97 |
| 8 | Imaynalla kachkanki | no enviada | "Imaynalla kachkanki." ✔ | 0,34 | Con la práctica anterior activa: "Todavía no. La forma correcta es Chunka pusqayuq…" (la sesión de práctica captura cualquier frase) 🟡. Sin sesión activa → Groq: "Allinmi, gracias. ¿Imaynalla kanki?" | 0,001 / 0,60 | 0,60 | **1,69 (medido)** | 2,68 | 3,68 |

\* Procesamiento = Whisper + decisión + Groq + edge-tts + ffmpeg (0,04) + wpctl (0,01). "est." = mediana de 10 mediciones de edge-tts (rango 1,49–1,82 s); en las filas 3b y 8 se midió con la respuesta real.
\** Turno percibido = procesamiento + 1,0 s fijo de silencio que el robot espera para cerrar la frase (`silencio_final=1.0`, main_robot.py:775). No incluye el tiempo que tarda `pw-play` en emitir el primer sonido (no medido).

**Otras decisiones verificadas:**
- JUEGO: a "¿Cómo se dice, perro, en quechua?" se respondió con el texto real "perro" → `[ACTUADOR TRISTE]` y "Se dice… Allqo" (similitud 0,20). 🟢
- TRADUCIR "buenas noches" → "En quechua se dice: Allin tuta." 🟢

**Precisión:**
- Whisper con voz sintética: **8/8 frases exactas (WER 0)**, 100 %.
- Palabras quechua de la BD que no están en el `initial_prompt`: "Misi" ✔ y "Allqo" → "Ayo" ✘, es decir 1/2. En total, **9/10**.
- ⚠ La voz es-MX pronuncia el quechua como castellano, y 2 de las 8 frases ("rimaykullayki", "imaynalla kachkanki") están literalmente en el `initial_prompt`, lo que sesga a Whisper a favor de acertarlas. **Esto no mide la precisión con niños.** La tesis dice 87,4 % "de fonemas" con Faster-Whisper (pdf 59), pero Faster-Whisper no está instalado y el código no calcula ningún porcentaje fonético (RF-02) → la cifra de la tesis es **NO VERIFICABLE** con este código.
- Gemini frente a Whisper: **NO VERIFICADO** (Gemini sin cuota).

**Groq:**
- `openai/gpt-oss-120b` respondió en 0,60 s: "Allinmi, gracias. ¿Imaynalla kanki?".
- 🟡 La BD solo tiene `Imaynalla` (= "¿Cómo estás?"); **"Allinmi" e "Imaynalla kanki" no están en el diccionario**. El prompt pide usar solo palabras de la lista y el modelo no cumplió. Requiere revisión de un hablante de quechua de Cochabamba.

**Whisper solo en CPU** (referencia para un equipo sin GPU como el de la tesis): carga en 0,83 s y transcripción en **1,12–1,74 s** por frase. Con eso, el procesamiento local quedaría en unos 2,8–3,4 s → también excede RNF-01.

**RNF-01 (≤ 2,5 s, "procesamiento ASR y respuesta del robot"):**
- 🟢 Se cumple solo en el camino local contando ASR + decisión + TTS (1,9–2,0 s).
- 🟠 No se cumple con Groq (2,68 s), con el turno percibido (2,9–3,7 s), en el primer turno con Gemini sin cuota (+0,89 s) ni en CPU.
- La mayor parte del tiempo se va en edge-tts (unos 1,6 s en línea en cada respuesta) y en el segundo fijo de silencio.

## 6. Audio: entrada y salida

Evidencia: `04_microfono.txt` y `04_groq_y_salida_audio.txt`.

**Salida (`HardwareInterface.hablar` real, con `subprocess.run` instrumentado; 2 frases sonaron en el televisor):**

| Paso | Frase 1 | Frase 2 |
|---|---|---|
| Estado web | HABLANDO → ESPERANDO | HABLANDO → ESPERANDO |
| edge-tts (código, s) | 0, 1,70 | 0, 1,69 |
| ffmpeg mp3→wav 24 kHz (código, s) | 0, 0,04 | 0, 0,04 |
| wpctl inspect (código, s) | 0, 0,01 | 0, 0,01 |
| `pw-play --target <serial>` (código, s; bloquea mientras suena) | **0**, 4,90 | **0**, 4,49 |
| Temporales borrados | Sí | Sí |
| Total de `hablar()` | 6,64 s | 6,23 s |

- El sink por defecto es `id 50`, "HDA NVidia Digital Stereo (HDMI)", `object.serial = "242"`, que corresponde al televisor. 🟢
- 🟡 `AudioManager.seleccionar_salida` informa "Salida seleccionada: USB Audio Device (hw:2,0)", pero ese dato solo lo usaría mpg123, que no está instalado. El log confunde porque la voz sale por HDMI.
- El usuario confirmó que oye la voz por el televisor; aquí queda verificado el camino técnico.

**Entrada (robot apagado):**
- `AudioManager()` se inicializa en 0,02 s y elige el índice 7 "USB Audio Device: - (hw:2,0)". `lsusb` lo identifica como `0d8c:0012 C-Media Electronics, Inc. USB Audio Device`, a 48 kHz y 1 canal. 🟢
- **Grabación de 3 s sin voz (2,96 s):**
  - nivel medio |x| = **0,00034**;
  - bloques de 80 ms entre 0,00030 y 0,00039;
  - pico de 0,0017;
  - RMS de −67,3 dBFS.
- **Umbral calculado = 0,0060.** Es el mínimo forzado por `_calcular_umbral_ruido`: max(0,006, ruido×1,25+0,004). Hacen falta 3 bloques seguidos (0,24 s) por encima del umbral para detectar voz. Ningún bloque de ruido superó el umbral. 🟢
- En el aula el ruido será mayor; con este equipo no se puede verificar (NO VERIFICADO).
- 🟡 El micrófono se abre en ALSA "hw" directo (no a través de PipeWire). Mientras el robot graba, otra aplicación no puede usar el mismo micrófono.
- Con `YURA_INPUT_DEVICE="Logitech USB Headset"` o `=99`, el robot sigue eligiendo el C-Media. 🟢

## 7. Dependencia de internet

Evidencia: `04_sin_internet.txt`, script `04_scripts/offline.py`. No se desconectó la red real: se usó `unshare -rn`, un espacio de red sin interfaces.

| Función | Servicio | Escenario A: sin red | Escenario B: red colgada (proxy local que nunca responde) |
|---|---|---|---|
| Transcripción principal | Gemini (en línea) | Falla por DNS en **0,04 s** → pasa a Whisper; el cliente **sigue activo** | Falla por timeout a los **12,06 s**; el cliente sigue activo, así que **cada turno pierde 12 s** 🟠 |
| Transcripción de respaldo | Whisper local (GPU) | Funciona: "Perro" (2,10 s incluyendo la carga) 🟢 | — |
| Conversación libre | Groq (en línea) | "Connection error" en 1,19 s → "No alcancé a entender esa frase…" (mensaje engañoso) 🟡 | **Sigue bloqueado tras 100 s** (SDK: `DEFAULT_TIMEOUT=60`, `DEFAULT_MAX_RETRIES=2`); el robot no escucha ni habla 🔴 |
| Traducción de palabras desconocidas | Groq | Devuelve None en 1,24 s → "No estoy seguro…" | Sigue bloqueado tras 100 s 🔴 |
| Traducción con el diccionario | SQLite local | "perro" → Allqo (0,00 s) 🟢 | 0,01 s 🟢 |
| Voz | Edge TTS (en línea) | edge-tts falla 2 veces (0,31 + 0,33 s) → `spd-say` (espeak-ng) con código 0 en 1,56 s. Voz robótica; que se oiga es NO VERIFICADO 🟡 | No probado: `edge_tts` usa aiohttp sin `trust_env` y no respeta el proxy. Por análisis, sin un timeout explícito en main_robot.py:240, la espera depende de edge-tts |

**Contraste con la tesis (5.4, pdf 48-49):**
- "No garantizará conectividad permanente a Internet, pudiendo operar las funcionalidades principales…": sin internet, las funciones principales **se degradan** (transcripción con Whisper, diccionario local, voz robótica de espeak-ng). Con una red colgada **el robot queda inoperante** durante minutos. 🟠
- "El sistema no implementará conversaciones libres mediante inteligencia artificial": el código **sí** implementa conversación libre con Groq (LLM `gpt-oss-120b`, conversacion.py:596-661). 🔴 Contradice el alcance.
- "No se integrará con … asistentes virtuales comerciales": el robot depende de servicios comerciales en la nube (Google Gemini, Groq, Microsoft Edge TTS). No son "Alexa/Siri", pero sí son servicios de IA comerciales de terceros que reciben la voz de los estudiantes (menores de edad). 🟠 Riesgo de privacidad: hay que declararlo.

## 8. Integración con la plataforma web (Laravel)

Evidencia: `04_integracion_web.txt`. La copia de Laravel es de solo lectura y no se puede ejecutar (no hay PHP ni MySQL).

**Lado del cerebro:** no hay `requests`, `urllib`, `http` ni `aiohttp` importados; no hay ninguna URL `http(s)://`, ni `Bearer`/`sanctum`, ni `student_id`, `activity_id` o `api/v1`. No registra intentos, puntajes ni estudiantes (0 coincidencias fuera de `tests/` y `documentacion_pruebas/`). Los resultados del juego solo cambian el estado de la pantalla; no se guardan.

**Lado de Laravel:**
- Existe `POST /api/v1/robot/activity` (routes/api.php:31, con `auth:sanctum`). Espera `activity_id`, `student_id`, `subject_id`, `score`, `activity_type` y `observations`, y guarda en `grades`.
- El usuario `robot@yura.com` se crea en `RobotUserSeeder` con la contraseña fija `robot-password-123`, y el token se imprime en consola. Se deriva a la revisión de seguridad.
- Las tablas `robot_*` (7) solo tienen `id`, `name` y `timestamps`, con palabras en español. No se sincronizan con `diccionario.db`, que tiene 15 tablas `nivelN_*`.
- Ninguna parte de Laravel consulta el puerto 5000, `/api/status` ni `/api/card`.
- **`phonetic_evaluations` no existe** en `database/` ni en `app/`; solo aparece en `docs/pruebas/*.md`.

**Conclusión:** 🔴 **No existe ninguna conexión real** (ni HTTP, ni BD compartida, ni sincronización). No se cumplen la flecha "WiFi / REST" entre el Cerebro Interno y el Servidor Web Central del diagrama de despliegue (pdf 58), ni RF-05 (registrar cada intento en `phonetic_evaluations`), ni el seguimiento del progreso por docentes y padres a partir del robot.

## 9. Hardware prometido frente a real

Evidencia: `04_hardware.txt`.

| Prometido en la tesis (6.3, 6.4 y 7.4.3) | Real (verificado) | Estado |
|---|---|---|
| ESP32 DevKit v1 por Serial USB (motores DC, servos, sensores de proximidad) | `lsusb`: ratón, teclado, dongle Bluetooth y C-Media. No hay `/dev/ttyUSB*`, `/dev/ttyACM*` ni `/dev/serial`. `pyserial` no está instalado. No hay código serial, GPIO, servo ni sensores. `mover_actuador` solo imprime `[FISICO]: Motores ejecutando -> …` (main_robot.py:382-383) | 🔴 |
| Pantalla LCD táctil de 7" | Solo HDMI-A-1 conectado (televisor). `/proc/bus/input/devices` no muestra ningún dispositivo táctil. La interfaz web no tiene botones | 🔴 |
| RF-01: "capturar comandos … mediante botón/pantalla" | La captura es solo por voz, con detección de actividad (VAD) | 🟠 |
| Micrófono de condensador con supresión de ruido y altavoces amplificados | Audífonos USB C-Media (0d8c:0012) y el televisor por HDMI | 🟡 |
| PC i3 3ra gen, 8 GB, Debian 13 | i3-10100, 15 GiB, **Ubuntu 24.04.5**, GPU GTX 1650 de 4 GB (Whisper la usa) | 🟡 La plataforma es distinta y más potente |
| Faster-Whisper int8 y filtro paso banda SciPy (7.6) | `faster-whisper`, `ctranslate2` y `scipy` **no instalados**; 0 referencias en el código. Se usa openai-whisper "base" | 🔴 La tesis describe algo que no existe |
| Batería LiFePO4 | No verificable por software | ⚫ NO VERIFICADO |

## 10. Matriz de pruebas

| ID | Módulo | Prueba | Entrada | Esperado | Obtenido | Estado | Evidencia |
|---|---|---|---|---|---|---|---|
| YURA-INT-001 | Configuración | Librerías frente a requirements | `pip show` de cada paquete | Las 9 instaladas y compatibles | 9/9 instaladas; `pip check` OK; sin versiones fijas | 🟡 | 04_configuracion.txt |
| YURA-INT-002 | Configuración | Paquetes del sistema | `which`, `dpkg -l` | ffmpeg, pw-play, wpctl, libportaudio2 | Presentes; faltan mpg123 y espeak (respaldos del código) | 🟡 | 04_configuracion.txt |
| YURA-INT-003 | Configuración | `.env.local` | `stat`, `grep -c` | 600 y las 2 claves definidas | 600, yura; GROQ=1, GEMINI=1 | 🟢 | 04_variables_gitignore.txt |
| YURA-INT-004 | Configuración | `.gitignore` | `git check-ignore` | Secretos y BD ignorados | Ignorados; `.env.example` permitido | 🟢 | 04_variables_gitignore.txt |
| YURA-INT-005 | Configuración | Claves en el historial | `git grep` sobre todos los commits | 0 | 0 | 🟢 | 04_rutas_scripts.txt |
| YURA-INT-006 | Configuración | Coherencia de variables | yura.service frente al código | Mismo modelo Groq | Servicio: gpt-oss-20b; código: gpt-oss-120b | 🟡 | 04_variables_gitignore.txt |
| YURA-INT-007 | Despliegue | `yura.service` | Rutas y usuario | Rutas existentes y usuario no root | Ruta inexistente, root, Logitech, no instalado | 🟠 | 04_rutas_scripts.txt |
| YURA-INT-008 | Despliegue | `yura.desktop` | `Exec=` | Script existente | Ruta inexistente; no está en autostart | 🟠 | 04_rutas_scripts.txt |
| YURA-INT-009 | Despliegue | `yura-open-browser.sh` | Navegadores y `yura.local` | Abre el modo kiosco | Sin Chrome/Chromium → exit 1; `yura.local` no resuelve | 🟠 | 04_rutas_scripts.txt |
| YURA-INT-010 | Arranque | Tiempo hasta estar listo | `web/app.py` | < 30 s | 4,08 s | 🟢 | 04_arranque_log.txt |
| YURA-INT-011 | Arranque | Componentes en el log | Log | Whisper, Gemini, Groq, BD y micrófono | Todos OK; micrófono C-Media hw:2,0 | 🟢 | 04_arranque_log.txt |
| YURA-INT-012 | Arranque | Volumen del log en reposo | 10 s | Log moderado | 171 líneas / 8,3 KB cada 10 s (unos 72 MB/día) | 🟡 | sección 4 |
| YURA-INT-013 | Arranque | RAM y GPU | ps, nvidia-smi | Dentro de 8 GB | RSS 0,96–1,5 GB; GPU 486 MiB | 🟢 | sección 4 |
| YURA-INT-014 | Web | `GET /` | 10 peticiones | 200 | 200, 4770 B, mediana 0,8 ms | 🟢 | 04_endpoints.txt |
| YURA-INT-015 | Web | `GET /api/status` y esquema | 10 peticiones | 200 y 10 claves tipadas | 200, 406 B, 0,6 ms, esquema OK | 🟢 | 04_endpoints.txt |
| YURA-INT-016 | Web | `GET /api/card` y esquema | 10 peticiones | 200 y significado en español | 200, 1069 B; `meaning` = `written` en 6/6 | 🟡 | 04_endpoints.txt |
| YURA-INT-017 | Web | Ruta inexistente | `/no-existe` | 404 | 404 | 🟢 | 04_endpoints.txt |
| YURA-INT-018 | Web | Método no permitido | POST/PUT | 405 | 405 | 🟢 | 04_endpoints.txt |
| YURA-INT-019 | Web | Salto de directorio | `/static/../../.env.local` | 404 | 404 (también con `%2f`) | 🟢 | 04_endpoints.txt |
| YURA-INT-020 | Web | Exposición en la red local | IP 192.168.40.194:5000 | Acceso controlado | 200 sin autenticación; servidor de desarrollo | 🟡 | sección 4 |
| YURA-INT-021 | Voz | Generación de voz de entrada | 8 frases con edge-tts | Código 0 | 8/8 con código 0; 1,49–1,82 s | 🟢 | 04_cadena_voz.txt |
| YURA-INT-022 | ASR | Gemini | WAV "jugar" | Transcripción | 429, cuota gratuita de 20/día agotada; cliente desactivado | 🔴 | 04_gemini_diagnostico.txt |
| YURA-INT-023 | ASR | Precisión de Gemini con quechua | 8 frases | Medir | Sin cuota | ⚫ | sección 5 |
| YURA-INT-024 | ASR | Whisper de respaldo | 8 frases | Texto exacto | 8/8 exactas; 0,24–0,38 s en GPU | 🟢 | 04_cadena_voz.json |
| YURA-INT-025 | ASR | Whisper con quechua fuera del prompt | Allqo, Misi | Exacto | Misi ✔; Allqo → "Ayo" ✘ | 🟡 | 04_whisper_cpu.txt |
| YURA-INT-026 | ASR | Whisper solo en CPU | 4 frases | ≤ 2,5 s por turno | 1,12–1,74 s (solo ASR) | 🟡 | 04_whisper_cpu.txt |
| YURA-INT-027 | Decisión | Menú "jugar" / "traducir" | Texto transcrito | JUEGO / TRADUCIR | Correcto | 🟢 | 04_cadena_voz.json |
| YURA-INT-028 | Decisión | Menú "perro" | "perro" | Traducir u orientar | "…no vendo autos ni converso en inglés" y pasa a CONVERSAR | 🟠 | 04_cadena_voz.json |
| YURA-INT-029 | Decisión | "buenas noches" / "¿cómo se dice gato…?" | Texto | Respuesta desde la BD | Allin tuta / Misi | 🟢 | 04_cadena_voz.json |
| YURA-INT-030 | Decisión | "enséñame quechua" | Texto | Inicia práctica | Inicia práctica ("Chunka pusqayuq") | 🟢 | 04_cadena_voz.json |
| YURA-INT-031 | Decisión | Frase durante una práctica | "imaynalla kachkanki" | Reconocer el saludo | Se evalúa como intento fallido | 🟡 | 04_cadena_voz.json |
| YURA-INT-032 | Decisión | TRADUCIR "perro" | Texto | Allqo | "En quechua se dice: Allqo…" | 🟢 | 04_cadena_voz.txt |
| YURA-INT-033 | Decisión | JUEGO, respuesta incorrecta | "perro" | TRISTE y dar la correcta | TRISTE y "Allqo" | 🟢 | 04_cadena_voz.txt |
| YURA-INT-034 | Groq | Conversación | "imaynalla kachkanki" | Solo palabras de la BD | "Allinmi… ¿Imaynalla kanki?" (fuera de la BD); 0,60 s | 🟡 | 04_groq_y_salida_audio.txt |
| YURA-INT-035 | Rendimiento | RNF-01 | Frases 1-8 | ≤ 2,5 s | Procesamiento de 1,9–2,7 s; turno percibido de 2,9–3,7 s | 🟠 | sección 5 |
| YURA-INT-036 | Audio | `hablar()` hasta el televisor | 2 textos | pw-play con código 0 | Código 0; target 242 (HDMI); temporales borrados | 🟢 | 04_groq_y_salida_audio.txt |
| YURA-INT-037 | Audio | Salida informada | Log | Coincide con la salida real | Dice USB; la voz sale por HDMI | 🟡 | 04_microfono.txt |
| YURA-INT-038 | Audio | Selección del micrófono | `AudioManager()` | C-Media USB | Índice 7 hw:2,0 (0d8c:0012) | 🟢 | 04_microfono.txt |
| YURA-INT-039 | Audio | Ruido y umbral | 3 s sin voz | Umbral por encima del ruido | Ruido 0,00034; umbral 0,0060; 0 falsos disparos | 🟢 | 04_microfono.txt |
| YURA-INT-040 | Audio | Variables de dispositivo inválidas | Logitech / 99 | Respaldo automático | Elige el C-Media | 🟢 | 04_microfono.txt |
| YURA-INT-041 | Sin internet | Gemini → Whisper | Sin red | Respaldo | 0,04 s; Whisper transcribe | 🟢 | 04_sin_internet.txt |
| YURA-INT-042 | Sin internet | Groq | Sin red | Mensaje claro | Error en 1,2 s y mensaje engañoso ("no alcancé a entender") | 🟡 | 04_sin_internet.txt |
| YURA-INT-043 | Sin internet | Voz | Sin red | Voz local | edge-tts falla → spd-say con código 0 | 🟡 | 04_sin_internet.txt |
| YURA-INT-044 | Red colgada | Gemini | Proxy sin respuesta | Falla rápido | 12,06 s por turno y no se desactiva | 🟠 | 04_sin_internet.txt |
| YURA-INT-045 | Red colgada | Groq | Proxy sin respuesta | Falla rápido | Más de 100 s bloqueado | 🔴 | 04_sin_internet.txt |
| YURA-INT-046 | Integración web | Cerebro → Laravel | grep en ambos proyectos | Llamada REST | No existe | 🔴 | 04_integracion_web.txt |
| YURA-INT-047 | Integración web | RF-05 `phonetic_evaluations` | Migraciones | Tabla y registros | La tabla no existe; el cerebro no registra intentos | 🔴 | 04_integracion_web.txt |
| YURA-INT-048 | Hardware | ESP32 / serial | `lsusb`, `/dev/tty*`, código | Dispositivo y protocolo | Nada | 🔴 | 04_hardware.txt |
| YURA-INT-049 | Hardware | Pantalla táctil | `/proc/bus/input` | Dispositivo táctil | Ninguno | 🔴 | 04_hardware.txt |
| YURA-INT-050 | Hardware / tesis | Faster-Whisper y SciPy | `pip show`, grep | Instalados y en uso | No existen | 🔴 | 04_hardware.txt |
| YURA-INT-051 | Parada | Detener el robot y liberar el puerto | `kill` SIGTERM | Proceso terminado y puerto libre | Terminado; "PUERTO 5000 LIBRE" | 🟢 | sección 4 |
| YURA-INT-052 | Código | Arranque directo de main_robot | main_robot.py:1224-1226 | Una sola llamada al bucle | `loop_principal()` se llama dos veces | 🟡 | main_robot.py:1226 |

## 11. Problemas priorizados y propuesta (no aplicada)

| Prioridad | Problema | Propuesta |
|---|---|---|
| CRÍTICO | No hay integración entre el cerebro y Laravel, no existe `phonetic_evaluations` y no se registran intentos (RF-05 y arquitectura de la tesis) (INT-046/047) | Crear la migración `phonetic_evaluations`. En el cerebro, añadir un cliente REST con token Sanctum que llame a `POST /api/v1/robot/activity` al terminar cada intento. Si no hay red, guardar los intentos en una cola SQLite local para sincronizarlos después. Hace falta definir cómo se identifica al estudiante (hoy el robot no lo sabe). Si no se hace, corregir la tesis |
| CRÍTICO | La tesis describe hardware y software inexistentes: ESP32, pantalla táctil, Faster-Whisper int8, SciPy y Debian 13 (INT-048/049/050) | Ajustar la tesis a la realidad verificada, o implementar esas piezas y documentar el protocolo serial |
| ALTO | Gemini con cuota gratuita de 20 peticiones al día; se desactiva sin avisar hasta reiniciar (INT-022) | Usar Whisper como motor principal (ya es local y rápido en GPU) y dejar Gemini como opcional, o contratar una cuota de pago. Registrar el cambio en `/api/status` |
| ALTO | Con la red colgada, Groq bloquea más de 100 s y Gemini cuesta 12 s por turno (INT-044/045) | Pasar `timeout=5` y `max_retries=0` al cliente Groq y bajar el timeout de Gemini a unos 4 s. Añadir un "circuit breaker" que desactive los servicios en línea durante N minutos tras un fallo. Añadir `timeout` al `subprocess.run` de edge-tts |
| ALTO | Scripts de despliegue inservibles: ruta inexistente, root, Logitech, sin Chrome y `yura.local` que no resuelve (INT-007/008/009) | Usar un servicio de usuario (`systemctl --user`) con rutas reales, `EnvironmentFile=-…`, `YURA_INPUT_DEVICE` vacío o "USB Audio Device", y un navegador que exista (Firefox `--kiosk`) apuntando a `http://localhost:5000/` |
| ALTO | RNF-01 se incumple en el turno percibido (2,9–3,7 s) (INT-035) | Reducir `silencio_final` a 0,6–0,7 s, cachear en MP3 las frases fijas (menú, saludos, respuestas de la BD) y considerar un TTS local |
| MEDIO | La conversación libre con LLM contradice el alcance 5.4, y Groq usa palabras que no están en la BD (INT-034) | Decidir si se mantiene. Si se mantiene, actualizar la tesis y filtrar la respuesta rechazando palabras quechua que no estén en la BD. Hacer revisar las respuestas por un hablante |
| MEDIO | "perro" en el menú responde "no vendo autos ni converso en inglés" (INT-028) | Si la palabra existe en la BD, ofrecer la traducción aunque se esté en el menú; cambiar el mensaje de rechazo por uno apropiado para niños |
| MEDIO | La voz de los estudiantes se envía a servicios comerciales en la nube (Google, Groq, Microsoft) | Declararlo en la tesis y en el consentimiento; preferir el modo local |
| MEDIO | Log de unos 72 MB al día en reposo (INT-012) | Poner las líneas `[DEBUG AUDIO]` detrás de una variable `YURA_DEBUG` o usar `logging` con niveles |
| MEDIO | La sesión de práctica captura cualquier frase, incluidos los saludos (INT-031) | Revisar primero las intenciones de saludo y comando y cerrar la práctica tras N intentos |
| BAJO | El log de salida dice USB, pero la voz sale por HDMI (INT-037) | Registrar el sink real de PipeWire que se usa |
| BAJO | Flask en 0.0.0.0 sin autenticación y en modo desarrollo (INT-020) | Usar 127.0.0.1 si la pantalla es local, o waitress/gunicorn |
| BAJO | `requirements.txt` sin versiones fijas y respaldos mpg123/espeak sin instalar (INT-001/002) | `pip freeze` con versiones fijas y documentar los paquetes apt |
| BAJO | `loop_principal()` duplicado (main_robot.py:1226) y `yura_temp.wav` escrito en la carpeta del proyecto | Borrar la segunda llamada y escribir el WAV en `tempfile` |
