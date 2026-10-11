# Informe 09: limpieza de código (solo lectura)

- Fecha: 28/09/2026
- Alcance: todo el proyecto, sin contar `.venv/`, `.git/`, `__pycache__/` ni `.pytest_cache/`. En la búsqueda de usos del código se dejaron fuera `documentacion_pruebas/` y `documentacion_quechua/`, porque solo contienen informes y evidencias. Las menciones en esas carpetas se anotan aparte cuando importan.
- Método: para cada elemento se siguió la cadena elemento → ¿quién lo usa? (`grep -rn` sobre `.py`, `.js`, `.html`, `.css`, `.sh`, `.service`, `.desktop`, `.txt`, `.example` y las pruebas) → ¿tiene dependencias? → ¿afecta el aprendizaje o la base de datos? → ¿afecta al orquestador? → decisión.
- `pyflakes` no está instalado en `.venv` y no se instaló nada. En su lugar se usaron dos programas con el módulo `ast`, guardados en el espacio temporal:
  - `analisis.py` busca importaciones sin uso.
  - `defs.py` busca funciones y clases que no se usan en el código de producción.
- No se cambió, movió ni borró ningún archivo. No se abrieron las bases de datos ni `.env.local`. No se tocó el servicio `yura`.

## 1. Tabla de elementos revisados

| # | Elemento | Archivo:línea | Tamaño | Quién lo usa (evidencia) | Decisión | Riesgo |
|---|---|---|---|---|---|---|
| 1 | Hoja de estilos del tema "soft" | `web/static/css/style-draft.css` | 3593 B | `grep -rn "style-draft\|theme-soft"` en `web/`, `scripts/`, pruebas y `.py` → **0 usos**. Solo se nombra en informes antiguos (`informe_001`, `02_frontend.md`, `cambios_ciclo1`). En el ciclo 1 se quitó el enlace desde `index.html`. Flask la sigue sirviendo como archivo estático, pero ninguna página la carga. | Eliminar | Bajo. Está en git (`git ls-files` la lista), así que se puede recuperar. |
| 2 | Carpeta `model/` (modelo pequeño de Vosk en español, según `model/README`: "Small Spanish model for Vosk") | `model/` | 58 MB | `grep -rni vosk` → solo `.gitignore:8` (`vosk-model-es/`, otra ruta), `main_robot.py:597` (un comentario vacío) y `model/README`. No hay `import vosk` ni ninguna ruta `model/` en el código. `requirements.txt` ya no incluye vosk. El último uso real aparece en la evidencia `04_arranque_log.txt:32`, de antes del ciclo 1. | Conservar con nota. Se puede eliminar si el equipo lo aprueba. | Bajo en lo técnico, porque nada lo carga. Hay dos matices: (a) está en git, así que borrarlo del disco no achica `.git` (98 MB); (b) en `cambios_ciclo1` quedó pendiente por si sirve para detectar la palabra de activación sin internet. |
| 3 | `entrada.txt` (contiene "Buenas tardes.") | `entrada.txt` | 15 B | `grep -rn "entrada.txt"` → **0 usos** en código, pruebas y scripts. Las coincidencias con "entrada" en `traductor.py` son nombres de variables (`idioma_entrada`, `entrada`), no este archivo. | Eliminar | Muy bajo. Está en git. |
| 4 | Respaldo `diccionario.respaldo.db` | raíz | 68 KB | Código y pruebas → **0 usos**. `informe_001:730` lo describe como "único respaldo antes del cambio Tayta → Tata". El `.gitignore` excluye `*.db`, así que **no está en git**. | Conservar con nota | Medio: es una copia de datos que no se puede recuperar. El diccionario puede rehacerse con `basedatos/diccionario_semilla.sql`, pero esta copia es la única prueba del estado anterior. |
| 5 | Respaldo `diccionario.respaldo_antes_correcciones.db` | raíz | 68 KB | Código y pruebas → **0 usos**. **No está en git** (`*.db`). | Conservar con nota. Se puede mover a una carpeta de respaldos si el equipo lo aprueba. | Medio: es una copia única, no recuperable. |
| 6 | `basedatos/diccionario_antes_correcciones_002_20260927_1450.db` | `basedatos/` | 68 KB | **Lo usa una prueba:** `tests/test_basedatos_y_juego.py:58` hace `glob("basedatos/diccionario_antes_correcciones_002_*.db")` en `test_las_correcciones_se_aplican_una_sola_vez`. Si falta el archivo, esa prueba se salta (`pytest.skip`). | **No tocar** | Alto: se pierde la prueba de que las correcciones 002 no se aplican dos veces, y además es una copia única de la base de datos. |
| 7 | `basedatos/diccionario_antes_agregar_002_20260927_1904.db` | `basedatos/` | 68 KB | Código y pruebas → **0 usos**. **No está en git** (`.gitignore:5 *.db`). | Conservar con nota | Medio: es la única copia del estado previo a `agregar_vocabulario_002.py`. |
| 8 | `import tempfile` | `main_robot.py:19` | — | **Se usa** en `main_robot.py:115` (`tempfile.mkstemp(...)`) para el audio temporal. | **No tocar** | Alto: el orquestador falla al arrancar. |
| 9 | `import sqlite3` | `main_robot.py:7` | — | **Se usa** en `main_robot.py:627` (`sqlite3.connect(...)`), que abre `diccionario.db`. | **No tocar** | Alto: afecta a la base de datos y al orquestador. |
| 10 | `from difflib import SequenceMatcher` | `juego.py:6` | — | **Se usa** en `juego.py:146`, donde compara la respuesta del alumno. | **No tocar** | Alto: afecta a la evaluación del aprendizaje. |
| 11 | `from difflib import SequenceMatcher` | `conversacion.py:5` | — | **Se usa** en `conversacion.py:84` (detección de palabras clave) y en `conversacion.py:484`. | **No tocar** | Alto: afecta a la conversación. |
| 12 | `import re` | `juego.py:4` | — | Con `ast`, el nombre `re` no aparece en ninguna otra parte de `juego.py`. `grep -rn "juego\.re\b"` → 0 usos, así que ninguna prueba lo sustituye. Es la **única importación sin uso** de todo el proyecto. | Eliminar | Muy bajo. |
| 13 | Comentario de sección "CARGAR MODELO VOSK" | `main_robot.py:596-598` | — | Es un encabezado de sección sin código debajo; lo que sigue es `_buscar_headset_usb`. Solo queda de cuando se quitó `_cargar_modelo_vosk` en el ciclo 1. | Eliminar el comentario, o cambiarlo por "BUSCAR MICRÓFONO" | Nulo: es un comentario. |
| 14 | `CARD_EXAMPLES` | `web/app.py:24` | — | **Se usa** en `web/app.py:197` (`/api/card`) y en `tests/test_arreglos_auditoria.py:167-168`. | **No tocar** | Alto: rompe la tarjeta de palabras de la pantalla y dos pruebas. |
| 15 | Ruta `/api/card` (`card_examples`) | `web/app.py:195-197` | — | **Se usa** en `web/static/js/app.js:81` (`fetch('/api/card')`) y en `tests/test_frontend_display.py:11` y `:20`. | **No tocar** | Alto: la pantalla pierde los ejemplos. |
| 16 | `traductor.buscar_traduccion_local` | `traductor.py:215-221` | — | `grep -rn "buscar_traduccion_local"` → **solo su propia definición**. Ningún módulo, prueba, plantilla ni script la llama, y `defs.py` lo confirma (0 usos en producción y 0 en pruebas). Depende de `buscar_vocabulario`, que sí se usa, pero nadie depende de ella. | Eliminar | Bajo. Es una función de 7 líneas y no toca la base de datos por sí misma. |
| 17 | `traductor.consultar_diccionario_local` | `traductor.py:274` | — | **Se usa** en `main_robot.py:524` y en las pruebas `test_vocabulario_groq.py:68` y `test_basedatos_y_juego.py:35` y `:39`. | **No tocar** | Alto: afecta a la traducción y al orquestador. |
| 18 | `traductor.formatear_vocabulario` | `traductor.py:355` | — | **Se usa** en `traductor.py:402` y en `conversacion.py:623`. | **No tocar** | Alto: afecta a las respuestas con Groq. |
| 19 | Variables de entorno de `.env.example` | `.env.example` | 674 B | Todas se leen en el código: `GROQ_API_KEY` (`main_robot.py:650`), `GEMINI_API_KEY` (`gemini_transcriber.py:40`), `YURA_RESULTADOS_CLAVE` (`web/app.py:231`), `YURA_VOZ` (`main_robot.py:122`), `YURA_GEMINI_ENABLED` (`gemini_transcriber.py:35`) y `YURA_VOZ_DOCENTE` (`main_robot.py:1016`). **Ninguna está obsoleta.** | **No tocar** | — |
| 20 | Variables que se leen pero no están en `.env.example` | varios | — | `YURA_DEBUG` (`depuracion.py:14`), `YURA_GROQ_MODEL` (`traductor.py:369`), `YURA_INPUT_DEVICE` (`audio_manager.py:283`), `YURA_OUTPUT_DEVICE` (`audio_manager.py:345`), `YURA_WHISPER_MODEL` (`main_robot.py:487` y `basedatos/aprender_de_audios.py:81`), `YURA_APAGAR_EQUIPO` (`main_robot.py:1157`, comentada en `scripts/yura.service:20`), `YURA_GEMINI_TRANSCRIBE_MODEL` (`gemini_transcriber.py:28`) y `GOOGLE_API_KEY` (`gemini_transcriber.py:41`). | Conservar. Solo falta documentarlas en `.env.example`. | Bajo. No se borra nada. |
| 21 | `.env.local` | raíz | 139 B | No se abrió, por norma. No se puede comprobar si tiene variables que ya no se leen. | **No tocar** | Tiene claves de API. |
| 22 | Líneas `vosk-model-es/` y `old/` del `.gitignore` | `.gitignore:8` y `:9` | — | Ninguna de las dos carpetas existe en el disco y no hay referencias en el código. Solo evitan que se suban si alguien las vuelve a crear. | Eliminar (opcional) | Nulo: sin esas líneas, git simplemente dejaría de ignorar esas carpetas. |
| 23 | 9 clases CSS sin uso: `detail-copy`, `detail-kicker`, `detail-stats`, `mode-active`, `mode-detail`, `mode-index`, `mode-label`, `mode-strip`, `progress-stat` | `web/static/css/style.css`, líneas 60 y 209-228 | — | `grep` en `web/*.html`, `web/*.js`, `.py` y pruebas → **0 usos** de cada una. Ojo: `.mode-strip` comparte regla con `.topbar` y `.footer` en la línea 60, así que solo hay que quitar ese selector y no la regla entera. | Eliminar con cuidado | Bajo. Es solo aspecto visual; conviene revisar la pantalla después. |
| 24 | `comandospara ejecutaryura.txt` | raíz | 3,3 KB | Son notas de operación para el usuario (está en git). No lo usa el código. | **No tocar** | Es documentación del usuario. |
| 25 | Dependencias de `requirements.txt` | `requirements.txt` | 371 B | Todas se usan: `flask`, `groq`, `whisper` (necesita `torch`), `sounddevice`, `numpy` y `google-genai` se importan. `edge-tts` se ejecuta como programa (`main_robot.py:233-239`). `pytest` es para las pruebas. `reportlab` y `pypdf` los usa `documentacion_pruebas/herramientas/generar_pdf.py`. No queda `vosk`. | **No tocar** | — |
| 26 | Funciones de rutas de Flask (`api_*_docente`, `audio_pendiente`, `proteger_resultados`, etc.) | `web/app.py:223-435` | — | `ast` las marca como "sin llamada", pero **no están muertas**: Flask las registra con sus decoradores y el JS o las pruebas las llaman por su dirección. | **No tocar** | Falso positivo del análisis. |

## 2. Seguro de eliminar

Ninguno de estos elementos tiene referencias en código, pruebas, plantillas, JS, scripts ni archivos `.service` o `.desktop`, y ninguno toca la base de datos ni el aprendizaje.

1. **`web/static/css/style-draft.css`**: 0 usos. El enlace se quitó en el ciclo 1. El tema estaba sin terminar y era ilegible (informe 02). Se puede recuperar desde git.
2. **`entrada.txt`**: 0 usos. Es una prueba suelta con "Buenas tardes." y está en git.
3. **`import re` en `juego.py:4`**: es la única importación sin uso del proyecto.
4. **`traductor.buscar_traduccion_local` (`traductor.py:215-221`)**: nadie la llama. Otras funciones ya hacen lo mismo (`consultar_diccionario_local` y `buscar_vocabulario`).
5. **Comentario "CARGAR MODELO VOSK" (`main_robot.py:596-598`)**: es un encabezado vacío que quedó de Vosk.
6. **Líneas `vosk-model-es/` y `old/` del `.gitignore`**: esas carpetas no existen. Quitarlas es opcional y no cambia nada.
7. **Las 9 clases CSS sin uso de `style.css`**: hay que quitar solo el selector `.mode-strip` de la línea 60, sin tocar `.topbar` ni `.footer`, y revisar la pantalla después.
8. **Carpeta `model/` (58 MB), solo si el equipo lo aprueba**: ningún código la carga. Antes de borrarla hay que confirmar que no se usará Vosk para detectar la palabra de activación sin internet (pendiente del ciclo 1). Como está en git, borrarla del disco no reduce el tamaño del repositorio.

Después de cualquier eliminación, conviene correr `.venv/bin/python -m pytest -q` (se esperan 183 pruebas aprobadas) y abrir la pantalla una vez.

## 3. No tocar

- **`basedatos/diccionario_antes_correcciones_002_*.db`**: lo usa `tests/test_basedatos_y_juego.py:58`. Sin él, la prueba de las correcciones se salta, y además es una copia única que no está en git.
- **`diccionario.respaldo.db`, `diccionario.respaldo_antes_correcciones.db` y `basedatos/diccionario_antes_agregar_002_*.db`**: son copias de datos que no están en git (`*.db` está ignorado), así que no se podrían recuperar. Si se quiere ordenar, lo mejor es moverlas a una carpeta `respaldos/` con el acuerdo del equipo, no borrarlas.
- **`tempfile` y `sqlite3` en `main_robot.py`**: se usan en las líneas 115 y 627. Afectan al orquestador y a la base de datos.
- **`SequenceMatcher` en `juego.py` y `conversacion.py`**: evalúa las respuestas y detecta palabras clave.
- **`CARD_EXAMPLES` y `/api/card`**: los usan `app.js:81` y tres pruebas.
- **`consultar_diccionario_local` y `formatear_vocabulario`**: los usan `main_robot.py`, `conversacion.py` y las pruebas.
- **Todas las variables de `.env.example`**: se leen en el código. A `.env.example` le faltan 8 variables que sí se leen (fila 20); conviene agregarlas, no borrar nada.
- **`.env.local`**: tiene claves de API y no se revisó.
- **`comandospara ejecutaryura.txt` y `requirements.txt`**: todo su contenido está en uso o es documentación del usuario.
- **Las rutas de Flask en `web/app.py`**: los decoradores las registran, aunque no se vean llamadas en el código.
