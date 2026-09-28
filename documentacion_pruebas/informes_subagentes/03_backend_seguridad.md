# Informe 03: Backend (código del cerebro) y seguridad del proyecto YURA

- **Subagente:** 3, tester de backend, código y seguridad (fases 6 y 10)
- **Fecha:** 2026-09-27
- **Alcance:** `main_robot.py`, `conversacion.py`, `traductor.py`, `juego.py`, `audio_manager.py`, `gemini_transcriber.py` y `web/app.py`, más una revisión estática de la plataforma Laravel `yura-platform` (commit `d419bd0`).
- **Reglas aplicadas:**
  - No se modificó ningún archivo del proyecto.
  - La base de datos se abrió siempre en solo lectura (`mode=ro`). Los scripts también redirigen la conexión global de `conversacion` a esa conexión de solo lectura.
  - No se arrancó el robot y no se usaron los puertos 5000/5051.
  - Las herramientas de análisis se instalaron en un venv aparte dentro del scratchpad: pyflakes, vulture, bandit, radon, coverage y pip-audit.
  - Se hicieron 5 llamadas reales a Groq (límite: 25). No se hicieron llamadas a Gemini ni a Edge TTS.
  - No se muestra ninguna clave.
- **Evidencias:** `documentacion_pruebas/evidencias/03_*.txt`. Los scripts reproducibles están en `evidencias/03_scripts/`. Cada archivo lleva el comando exacto en su cabecera.

---

## 1. Resumen ejecutivo

**Qué funciona (VERIFICADO):**
- La suite de pruebas pasa entera: 28 de 28.
- La base de datos no admite inyección SQL.
- Flask corre con `debug=False`.
- `.env.local` tiene permisos 600, y no hay claves en el historial de Git.
- El flujo feliz del juego funciona. Con 4 respuestas correctas, Yura celebra las 4 y vuelve al MENÚ.
- Groq rechazó los 5 intentos reales de inyección de instrucciones.

**Problemas encontrados:**

| # | Hallazgo | Estado | Prioridad |
|---|---|---|---|
| 1 | **Pedir la traducción de "apagar" apaga el robot.** En el MENÚ, cualquier frase que contenga "apagar" (por ejemplo, "¿cómo se dice apagar en quechua?") pone `running=False`. `web/app.py` entonces cierra el proceso con `os._exit(0)`. El servicio usa `Restart=on-failure` y el código de salida es 0, así que el robot no se reinicia solo. | 🔴 VERIFICADO | ALTO |
| 2 | **La evaluación del juego y de la práctica no es fiable.** En un barrido de toda la BD, el juego acepta **298 pares de palabras quechuas distintas** como respuesta correcta (ejemplos: Sara/maíz por Sach'a/árbol, Yana/negro por Llama, Quri/dorado por Qhari/hombre, Manka/olla por Marka/pueblo). También acepta "anti" por Inti y "wasa" por Wasi. En cambio, rechaza respuestas correctas como "se dice allqo". Al final del juego siempre dice "¡Felicidades!", aunque haya 0 de 4 aciertos, y no guarda ningún puntaje. | 🔴 VERIFICADO | ALTO |
| 3 | **Las intenciones se detectan por subcadenas y hay muchos falsos positivos.** En `_detectar_intencion` fallan 15 de 23 casos probados. En la tabla de 5 estados × 19 comandos hay transiciones incoherentes. Ejemplos: "no quiero jugar" abre el JUEGO, "¿cómo se dice adiós?" silencia a Yura, y en el TRADUCTOR no se pueden traducir adiós, volver, salir ni terminar. | 🟠 VERIFICADO | ALTO |
| 4 | **El traductor da resultados erróneos o innecesarios en línea.** "no" se traduce como horno de barro, camino o uno; "sí" como iglesia, siete o diecisiete. Además, "¿cómo se dice perro?" o "el perro" van a Groq en vez de usar Allqo, que está en la BD local. | 🟠 VERIFICADO | ALTO |
| 5 | **Robot "zombi".** Cualquier excepción no controlada dentro de un modo (por ejemplo, `database is locked`) mata el hilo del robot. `os._exit` no llega a ejecutarse y `/api/status` sigue mostrando `running=True`. | 🔴 VERIFICADO | ALTO |
| 6 | **Privacidad de menores.** La voz de los niños se envía a Google Gemini y el texto a Groq, sin ningún aviso en el sistema. El modo SILENCIO sigue grabando y transcribiendo en la nube todo lo que se dice en el aula. El historial de conversación de un estudiante se envía a Groq en la sesión del siguiente. La tesis (7.2) solo habla de consentimiento para la "recolección anónima de métricas fonéticas". | 🔴 VERIFICADO (código) | ALTO |
| 7 | **Plataforma Laravel** (revisión estática; la ejecución es ⚫ NO VERIFICADO). `POST /api/users` deja a cualquier usuario autenticado crear un administrador. `GET /api/users` lista a todos los usuarios. Las exportaciones PDF/Excel de todos los estudiantes no controlan el rol. `/api/v1/robot/activity` acepta notas de cualquier token. | 🔴 | CRÍTICO / ALTO |
| 8 | **El cerebro no se comunica con la plataforma.** No hay cliente HTTP, URL, token ni identificador de estudiante. RF-05 (registrar cada intento) no está implementado en el robot. | 🔴 VERIFICADO | ALTO |
| 9 | **Cobertura de pruebas: 38 %.** `juego.py` tiene 10 %, `audio_manager.py` 20 % y `main_robot.py` 31 %. Ninguna prueba cubre la máquina de estados. Sin `diccionario.db`, que Git ignora, fallan 9 de 28 pruebas. | 🟠 VERIFICADO | MEDIO |

---

## 2. Arquitectura del código

```
web/app.py (Flask 0.0.0.0:5000; GET /, /api/status, /api/card)
  └─ main_robot.py  (BrainYura, HardwareInterface, RobotStates)
       ├─ audio_manager.py      → sounddevice, numpy, subprocess(wpctl/pactl/pacmd)
       ├─ gemini_transcriber.py → google.genai (NUBE: audio del estudiante)
       ├─ whisper (local, GPU)   · vosk (se carga pero no se usa)
       ├─ groq.Groq              (NUBE: texto del estudiante)
       ├─ conversacion.py → traductor.py ; conexión SQLite global propia
       ├─ traductor.py    (BD SQLite + Groq)
       └─ juego.py        (sin imports del proyecto; recibe callbacks)
  Procesos externos: edge-tts (NUBE Microsoft: texto que dice Yura), ffmpeg, pw-play, wpctl,
  ffplay, mpg123, spd-say, espeak, bash/zsh (shell=True)
```

**Tamaño y calidad, según radon** (`03_estatico_pyflakes_vulture_radon.txt`):
- **Tamaño (SLOC):** 2812 líneas en total.
- **Más líneas:** `main_robot.py` (877), `conversacion.py` (634) y `audio_manager.py` (543).
- **Mantenibilidad más baja:** `conversacion.py` (C, 6.09) y `audio_manager.py` (C, 6.02).

**Hilos:**
- `BrainYura()` se crea en el hilo principal.
- `loop_principal` corre en el hilo `yura-backend` (daemon).
- Flask atiende en otros hilos y solo lee `web_status` (protegido con lock), `state` y `running`. Estos dos últimos se leen sin lock; en CPython es inocuo.
- **Conexiones SQLite:** hay dos, ambas en lectura y escritura:
  - `main_robot.db_conn`, con `check_same_thread=False`. Se crea en el hilo principal y se usa en el hilo del robot.
  - La conexión global de `conversacion`, que se crea de forma perezosa en el hilo del robot y **nunca se cierra**.
  - Hoy ningún otro hilo toca la BD, así que no se observó un problema de concurrencia real.

## 3. Máquina de estados: tabla estado × comando (VERIFICADO)

**Método:** `BrainYura` se construye sin `__init__`. `escuchar_voz` es falso y devuelve el texto ya pasado por `_normalizar_texto`, como hace el real. `hw.hablar` es un Mock, la BD es de solo lectura y Groq es falso. Se ejecuta un ciclo del modo correspondiente. Evidencia: `03_estados_x_comandos.txt`, script `t1_estados.py`.

**Leyenda:**
- **M** = MENU, **C** = CONVERSAR, **J** = JUEGO, **T** = TRADUCIR, **S** = SILENCIO, **OFF** = SALIR con `running=False`.
- "T…" significa que sigue en el bucle del traductor.
- En J, la respuesta dicha se evalúa en la pregunta "perro" (respuesta correcta: Allqo).

| Comando dicho | desde MENU | desde CONVERSAR | desde JUEGO | desde TRADUCIR | desde SILENCIO |
|---|---|---|---|---|---|
| (silencio / "") | M (callada) | C | J "No logré escucharte" (repite la misma pregunta sin fin) | T… "Necesito que repitas…" (sin fin) | S |
| hola | **C** ("Rimaykullayki significa hola") | C | J, cuenta como respuesta incorrecta | T… → Groq (hola no está en la BD) | S |
| preséntate | M (presentación) | C (presentación) | J, incorrecta | T… → Groq | S |
| silencio | S | **C, no se calla** (dice "no vendo autos…") | J, incorrecta | T… → Groq | **M (se despierta)** |
| cállate / espera | S | **C, no se calla** | J, incorrecta | T… → Groq | S |
| apagar | **OFF** | **C, no apaga** | J, incorrecta | **M, no apaga** | **S, no apaga** |
| salir / adiós / terminar | S ("Hasta luego…") | M | salir→**M**; adiós y terminar→**J, incorrecta** | M | S |
| menú | **M, pero dice "Hasta luego. Tupananchiskama."** | M | M | M | S |
| volver | C ("no vendo autos…") | C ("no vendo autos…") | J, incorrecta | M | M |
| despierta | C ("no vendo autos…") | C | J, incorrecta | T… → Groq | M |
| traducir | T | **C, no cambia de modo** ("No tengo traducción segura de 'traducir'") | J, incorrecta | T… → Groq | S |
| conversar | C | C → Groq | J, incorrecta | T… → Groq | S |
| jugar | J | **C, inicia la práctica de vocabulario, no el juego** | J, incorrecta | T… → Groq | S |
| enséñame quechua | C (práctica) | C (práctica) | J, incorrecta | T… → Groq | S |
| ¿cómo se dice perro? | C (Allqo, local) | C (Allqo, local) | J, incorrecta | **T… → Groq, no usa la BD local** | S |

**Conclusiones sobre la máquina de estados (VERIFICADO):**
- **Estados sin salida:** ninguno. Desde todos se puede volver al MENÚ.
- **Solo se puede apagar desde el MENÚ.** Desde C, J, T y S la orden "apagar" no apaga.
- **Solo se puede silenciar desde el MENÚ.** Desde CONVERSAR no hay forma de pedirle silencio.
- **No hay atajos entre modos.** Desde CONVERSAR no se puede ir al TRADUCTOR ni al JUEGO. En CONVERSAR, "jugar" inicia la práctica de vocabulario.
- **El MENÚ manda a CONVERSAR cualquier frase no reconocida** (`main_robot.py:1040-1051`). Por ejemplo, "despierta" o "volver" reciben la respuesta "no vendo autos ni converso en inglés".
- **Bucles de insistencia sin límite:**
  - En T, con silencio, Yura repite "Necesito que repitas la palabra o frase" cada ciclo de escucha, sin tiempo de salida (`traductor.py:377-392`).
  - En J repite la misma pregunta indefinidamente.
  - Sin micrófono, el bucle del traductor hizo **10 intentos de escucha y dijo 10 frases en 3 s** (TTS falso), con 140 líneas de log (`03_bucle_sin_microfono.txt`). Con TTS real, Yura hablaría sin parar.
- **Código inalcanzable:**
  - La rama `elif self.state == RobotStates.SALIR` del bucle (`main_robot.py:1196`): `ejecutar_menu` ya pone `running=False` antes.
  - `__main__` llama a `loop_principal()` **dos veces** (`main_robot.py:1224` y `1226`).

## 4. Lógica e intenciones: casos que fallan (VERIFICADO)

Evidencia: `03_intenciones_falsos_positivos.txt`.

**A. MENÚ** (`main_robot.py:925-1034`, comparación por subcadena):

| Frase | Esperado | Obtenido |
|---|---|---|
| "¿cómo se dice apagar en quechua?" | traducción | **SALIR, running=False (apagado)** |
| "no quiero jugar" / "quiero conjugar verbos en quechua" | no jugar | **JUEGO** |
| "¿cómo se dice silencio en quechua?" | traducción | **SILENCIO** |
| "¿cómo se dice adiós en quechua?" / "no quiero salir" / "¿qué significa terminar?" | traducción / seguir | **SILENCIO** |
| "juguemos" | JUEGO | CONVERSAR ("no vendo autos…") |
| "apaga" / "yura apágate" | SALIR | CONVERSAR ("no vendo autos…") |

**B. `conversacion._detectar_intencion`** (`conversacion.py:109-163`): **15 de 23 casos FALLAN**.
- **Salidas falsas:** "como se dice adios en quechua"→salir, "que significa tupananchiskama"→salir, "me voy a portar bien"→salir, "el menudo de mi abuela"→salir ("menu" dentro de "menudo") y "como se dice nos vemos"→salir. Con la intención salir, la conversación vuelve al MENÚ en vez de traducir.
- **Prácticas falsas:** "quiero conjugar verbos"→practicar ("jugar"), "tengo una pregunta"→practicar (similitud 0.89 con "preguntame"), "comprueba si esta bien"→practicar, "es practicamente igual"→practicar y "el ejercito"→practicar (similitud difusa con "ejercicio").
- **Orden incorrecto de reglas:** "como se dice jugar/aprender/enseñar/prueba/practicar" devuelve aprender o practicar, porque estas reglas se evalúan antes que traducir.
- **Coincidencias entre palabras:** `_coincide_clave_intencion` concatena todos los tokens sin espacios (`texto_compacto`), así que también encuentra coincidencias que cruzan palabras.

**C. Modo TRADUCIR** (`traductor.py:394-409`, y búsqueda por subcadena en `buscar_vocabulario:158-164`):

| Frase del niño | Resultado |
|---|---|
| adiós / volver / regresar / menú / salir / terminar / "apagar la luz" | vuelve al MENÚ, no traduce |
| "¿cómo se dice perro?" y "el perro" | no quita el prefijo ni el artículo, **va a Groq** (la BD tiene "perro" = Allqo) |
| "no" | "Tiene varios significados: Horno de barro… T'anta manka; Camino… Ñan; Uno… Huk" |
| "sí" | "Iglesia… Iglesia; Siete… Qanchis; Diecisiete…" |
| "hola" | no está en la BD, va a Groq. Sí lo resuelve `conversacion._responder_frase_local`, pero el traductor no usa esa función. |

**D. Modo SILENCIO** (`main_robot.py:1058-1068`). Frases normales del aula lo despiertan: "niños, silencio por favor", "vamos a volver a clase", "vuelve a tu asiento", "despierta a tu compañero" y "¿puedes hablar más fuerte?". Las tres primeras son órdenes típicas de la profesora.

**E. Normalización.** Se confirma lo documentado en la fase 1: el `_normalizar_texto` de `main_robot` elimina la ñ. Consecuencia en el juego: "uqa" se acepta como Ñuqa.

## 5. Juego y evaluación (VERIFICADO)

Evidencia: `03_evaluacion_juego_practica.txt`.

- **Palabras del juego y su respuesta en la BD:**
  - gato→Misi, perro→Allqo, sol→Inti, agua→Uma, casa→Wasi, árbol→Sach'a.
  - Ninguna es ambigua en la búsqueda exacta.
  - El mapeo de emergencia de `juego.py:98-105` (michi, allqu, yaku, sacha) no coincide con la BD. Solo se usa si falta la BD.
- **Barrido de las 187 filas (pares de palabras con significado distinto):**
  - El **juego** acepta 298 pares como respuesta correcta y la **práctica** acepta 294.
  - Causa: umbral 0.75 sobre palabras de 4 a 6 letras, más el reemplazo q→k y la eliminación de la h.
  - Ejemplos: Chicha por Ch'ita (gato montés), Papa por Llapa, Sara por Sach'a, K'anka por Manka o P'anka, Kulli por Quri, Qullqi, K'ullu o Kuchi, y Yana por Tiyana o Llama.
- **Falsos positivos concretos:** wasa→Wasi, anti→Inti y uqa→Ñuqa se aceptan.
- **Falsos negativos:** "se dice allqo" y "allqo allqo" se rechazan. El niño que responde con una frase completa, o al que la transcripción le duplica la palabra, recibe "Sigue aprendiendo".
- **Práctica:** si la palabra que toca es "Allin sukay" o "Allin tuta", repetirla bien **no se evalúa**. `_responder_frase_local` la intercepta antes (`conversacion.py:533-534` y `655-660`).
- **Salidas del juego:** solo "salir" y "menú" (`juego.py:607`). "adiós", "terminar", "volver", "apagar" y "silencio" se califican como respuestas incorrectas y el robot pone la cara TRISTE.
- **Final de partida:** "¡Felicidades! Completaste todas las palabras" incluso con 0 de 4. No hay contador de aciertos ni persistencia. Los atributos del juego son solo índice y lista.
- **Flujo feliz:** 4 de 4 respuestas correctas se celebran, y `web_status` pasa a CELEBRANDO/CORRECTO y vuelve a MENU. 🟢 VERIFICADO.

## 6. Errores silenciosos y recursos

| Hallazgo | Evidencia | Estado |
|---|---|---|
| `loop_principal` solo captura `KeyboardInterrupt` (`main_robot.py:1200`). Con una BD bloqueada, `OperationalError` **se propaga**. En `web/app.py:144-149`, el hilo muere, **no se llama a `os._exit`** y `/api/status` sigue devolviendo `state=CONVERSAR, running=True`. | `03_errores_recursos_hilos.txt` B y C | 🔴 VERIFICADO |
| `hablar()`: `edge-tts`, `ffmpeg` y `pw-play` se ejecutan **sin timeout**; solo `wpctl` lo tiene. Si la red o el audio se cuelgan, el robot se bloquea. | idem A | 🟠 VERIFICADO |
| Groq sin timeout propio: la librería usa por defecto 60 s de lectura y 2 reintentos. | `groq._constants` | 🟡 VERIFICADO |
| `except Exception: pass` en `main_robot.py`: 48 (ALSA), 152 (on_status), **372** (oculta cualquier fallo de spd-say/espeak), 861 y 1213; `continue` silencioso en 641 y 661 (bandit B110/B112). | `03_bandit.txt` | 🟡 VERIFICADO |
| `yura_temp.wav` con nombre fijo en la carpeta del proyecto (`main_robot.py:800-803`). Contiene la voz del niño. Se borra en `finally`, pero si el proceso muere (kill o corte de luz) entre escribirlo y borrarlo, queda en disco. Hoy no existe. | idem E | 🟡 VERIFICADO |
| El mp3 de `mkstemp` se crea en `__init__` y se borra en cada `hablar`. Luego edge-tts lo recrea con el mismo nombre (condición de carrera TOCTOU menor). | código 102-106 y 375-379 | 🟡 |
| Dos conexiones SQLite en lectura y escritura sobre el mismo archivo. La de `conversacion` nunca se cierra. Ninguna se abre en solo lectura, aunque el cerebro solo lee. | idem F | 🟡 VERIFICADO |
| `historial_conversacion` nunca se limpia al volver al MENÚ. En la sesión siguiente se reenvía a Groq lo que dijo el estudiante anterior. | idem D | 🟠 VERIFICADO |

## 7. Código muerto, duplicado y complejidad

- **pyflakes:** `import json` sin uso (`main_robot.py:6`).
- **vulture** (confirma y amplía la fase 1):
  - `AudioManager.grabar`, `_es_jack_directo`, `_es_entrada_logitech`, `output_device` (se escribe pero nunca se lee) y `vosk_recognizer` (se crea y no se usa).
- **Muerto por lógica:**
  - La segunda llamada a `_responder_frase_local` (`conversacion.py:746`) nunca devuelve nada: la primera, con la misma entrada, ya retornó (línea 655).
  - La rama SALIR del bucle principal y la doble llamada a `loop_principal`.
  - `traductor.ejecutar_traducir` solo devuelve "continuar" cuando `modo_activo()` pasa a falso desde fuera, cosa que no ocurre.
  - En Laravel, `app/Http/Controllers/RobotActivityController.php` (web) no tiene ninguna ruta: `routes/web.php` usa `GradeController`.
- **Código duplicado:**
  - `_normalizar_texto` está en tres módulos con comportamiento distinto: la de `conversacion` convierte ñ→n y las otras dos eliminan la ñ.
  - `Juego._respuesta_es_correcta` y `conversacion._evaluar_respuesta` son el mismo algoritmo copiado.
- **Complejidad ciclomática (radon C o peor):**
  - `HardwareInterface.hablar` **E (35)**.
  - `BrainYura.ejecutar_menu` D (24), `conversacion.procesar_entrada` D (22), `AudioManager._obtener_dispositivo_entrada_activo` D (21).
  - `_obtener_api_key_groq` C (20) y `_detectar_intencion` C (18).
  - Promedio: B (5.93).

## 8. Rendimiento (medido, sin micrófono)

Evidencia: `03_rendimiento.txt`.

| Operación | Mediana | Máx. |
|---|---|---|
| `_leer_registros_vocabulario` (15 tablas, 187 filas) | 0.74 ms | 1.58 ms |
| `buscar_vocabulario('perro')` | 1.22 ms | 1.88 ms |
| `vocabulario_relevante(...)` | 1.92 ms | 2.40 ms |
| `_obtener_vocabulario_para_practica` (5 lecturas completas de la BD) | 8.61 ms | 10.47 ms |
| `procesar_entrada('como se dice perro en quechua')` (local) | 3.14 ms | 3.82 ms |
| `detectar_dispositivos()+seleccionar_entrada()` (se repite en cada escucha) | 13 ms | 19 ms |
| `whisper.load_model('base')` | 1.27 s en `cuda:0`, **447 MB de GPU reservados** | |
| Importar los módulos del cerebro (torch, whisper, vosk) | 2.67 s | |

**Conclusiones:**
- **Lecturas de BD y dispositivos:** releer todas las tablas en cada llamada y volver a detectar los dispositivos en cada escucha **no es un cuello de botella hoy** (milisegundos con 187 filas). 🟢 Crece de forma lineal con el vocabulario.
- **Whisper:** ocupa 447 MB de la GPU (GTX 1650 de 4 GB) aunque Gemini sea el motor principal. 🟡
- **Latencia fija por turno** (código de `escuchar_voz` y `grabar_hasta_silencio`), antes de transcribir:
  - Partes: `sleep` de 0.3 s + 0.2 s de arranque + 0.2 s de calibración + 1.0 s de silencio final.
  - Total: **≈ 1.7 s de espera fija**.
  - A eso se suman Gemini (red), Groq (red) y Edge TTS (red).
  - RNF-01 exige una latencia de 2.5 s o menos. La medición de extremo a extremo quedó ⚫ NO VERIFICADO porque no hubo micrófono en esta prueba, pero la parte fija ya consume el 68 % del presupuesto.

## 9. Calidad y cobertura de las pruebas

Evidencia: `03_pytest_y_cobertura.txt` y `03_pytest_sin_diccionario.txt`.

- **Ejecución:** `.venv/bin/python -m pytest -q` da **28 passed en 2.40 s**. 🟢
- **Cobertura** (coverage del venv aparte): **38 % en total**.

| Módulo | Cobertura | Sin prueba |
|---|---|---|
| juego.py | **10 %** | `ejecutar_turno`, `_respuesta_es_correcta` y `reiniciar`: todo el módulo |
| audio_manager.py | 20 % | `grabar_hasta_silencio`, la selección de dispositivos y `validar_entrada` |
| main_robot.py | 31 % | `ejecutar_menu` (salvo la entrada vacía), `ejecutar_silencio`, `ejecutar_traducir`, `ejecutar_juego`, `loop_principal`, `escuchar_voz`, `cargar_archivo_claves`, `_obtener_api_key_groq` y `inicializar_sistemas_locales` |
| web/app.py | 47 % | `_status_payload` con robot y `start_robot` |
| gemini_transcriber.py | 50 % | `__init__` |
| conversacion.py | 52 % | la práctica (`_comenzar_practica`, `_evaluar_respuesta`, `_procesar_sesion_educativa`) e `interpretar_entrada_quechua` |
| traductor.py | 72 % | el bucle de `ejecutar_traducir` salvo el caso ambiguo |

**Pruebas débiles o falsas:**
- `test_silence_command_is_recognized_without_noise` es una tautología (ya documentado en la fase 1).
- `test_conversation_entry_does_not_include_intro_sentence` solo comprueba que falten dos frases.
- Las pruebas de `test_frontend_display` buscan cadenas o emojis en `app.js` y `style.css`.
- `test_reconoce_respuestas_cortas…` solo comprueba que no aparezca "no entend".

**Lo que ninguna prueba detectaría:**
- Ningún caso de las secciones 3, 4 y 5: transiciones de estado, falsos positivos ni evaluación del juego.

**Dependencia de la BD:**
- En una copia limpia (archivos versionados, sin `diccionario.db`), **fallan 9 de 28 pruebas**, porque Git ignora `*.db`.
- Varias pruebas abren `diccionario.db` en **lectura y escritura** mediante `conversacion._obtener_conexion_vocabulario`.

## 10. Seguridad (fase 10)

| ID | Hallazgo | Evidencia | Estado / prioridad |
|---|---|---|---|
| SEC-001 | Flask escucha en `0.0.0.0:5000` (`web/app.py:177`) sin autenticación. La interfaz de red es `enp3s0 192.168.40.194/24`, así que cualquiera en la LAN puede leer `/api/status` y `/api/card`. Solo hay rutas GET de lectura, y no exponen lo que dice el niño sino lo que dice Yura. Sin cabeceras de seguridad (X-Frame-Options, CSP y nosniff ausentes), con el servidor de desarrollo de Werkzeug y sin `SECRET_KEY`. Firewall `ufw`: ⚫ NO VERIFICADO, requiere root. | `03_seguridad_sql_flask.txt` | 🟡 MEDIO |
| SEC-002 | `debug=False`. POST devuelve 405 y las rutas inexistentes 404. | idem | 🟢 |
| SEC-003 | SQL: los identificadores de tabla vienen de `sqlite_master`, se filtran con `^nivel\d+_[a-z0-9_]+$` y se citan escapando `"`. El texto del usuario nunca entra en SQL, porque se filtra en Python. Prueba: una tabla con nombre malicioso se descarta, la búsqueda con `'; DROP TABLE` no altera nada y la tabla sigue existiendo. Los avisos B608 de bandit son falsos positivos. | idem | 🟢 VERIFICADO |
| SEC-004 | `_obtener_api_key_groq` usa `shell=True` (`main_robot.py:644-662`). Los comandos son constantes y no admiten inyección, pero ejecutan `.bashrc`, `.profile` y `.zshrc` con `bash -lc` / `zsh -lc` (hasta 3 × 10 s de timeout). Como el servicio corre como root (sin `User=`), ejecutaría los perfiles de root. Es redundante con `cargar_archivo_claves`. Hoy no llega a ejecutarse, porque `.env.local` ya aporta la clave. Bandit: B602 High. | `03_bandit.txt` | 🟠 MEDIO |
| SEC-005 | Claves: `.env.local` tiene permisos `-rw------- yura`. Define GROQ_API_KEY y GEMINI_API_KEY (valores no leídos). `.gitignore` excluye `.env*`. Un grep de `gsk_` y `AIza` en todo el historial de Git no encuentra nada. Las claves pasan a `os.environ` y las heredan todos los subprocesos (edge-tts, ffmpeg, bash). | `stat`, `git log -p` | 🟢 / 🟡 BAJO |
| SEC-006 | **Datos de menores enviados a terceros sin aviso.** El audio del estudiante va a Google Gemini (`gemini_transcriber.py:724-741`). El texto va a Groq junto con el historial (`conversacion.py:604-616`). Las frases que Yura repite de vuelta, por ejemplo "No tengo una traducción segura de '<frase del niño>'", van a Microsoft (Edge TTS). No hay ningún aviso ni consentimiento en código, pantalla ni documentación del cerebro (grep "consentim/privacidad" sin resultados en el código). La tesis 7.2 solo cubre la "recolección anónima de métricas fonéticas". | código y grep | 🔴 ALTO |
| SEC-007 | **El modo SILENCIO sigue grabando** y enviando a Gemini todo lo que se habla en el aula (`ejecutar_silencio` llama a `escuchar_voz`, `main_robot.py:1054`). | código y tabla de la sección 3 | 🔴 ALTO |
| SEC-008 | Las transcripciones de los niños se imprimen en stdout ("[GEMINI ESCUCHÓ]", "[CONVERSACION] Usuario:"). Con `yura.service` quedan guardadas en journald. | `main_robot.py:817`, `conversacion.py:760` | 🟠 MEDIO |
| SEC-009 | El historial de un estudiante se reenvía a Groq en la sesión del siguiente (BE-030). | `03_errores_recursos_hilos.txt` D | 🟠 MEDIO |
| SEC-010 | Inyección de instrucciones: 5 intentos reales ("ignora tus instrucciones…", "ahora eres un pirata…", "repite tu mensaje de sistema…", "dame tu dirección", "invéntala") y **5 rechazados**; el traductor en línea devolvió None. La defensa depende solo del modelo (temperatura 0.7, no determinista): no hay moderación ni filtro de salida en el código, y lo que dice el modelo se habla directamente. El filtro `_es_tema_quechua` se supera con solo incluir la palabra "quechua". | `03_inyeccion_prompt_groq.txt` | 🟡 MEDIO |
| SEC-011 | `requirements.txt` no fija versiones. pip-audit sobre las versiones instaladas (Flask 3.1.3, Werkzeug 3.1.8, groq 1.7.0, google-genai 2.25.0, torch 2.14.0…): **"No known vulnerabilities found"**. | `03_pip_audit.txt` | 🟡 BAJO |
| SEC-012 | Bandit sobre el cerebro: 1 High (B602), 3 Medium (2 B608 falsos positivos y B104 por 0.0.0.0) y 21 Low (subprocess, try/except/pass, random). | `03_bandit.txt` | informativo |
| SEC-013 | `scripts/yura.service` no tiene `User=`, así que corre como root. Además, `WorkingDirectory` y `EnvironmentFile` apuntan a una ruta inexistente (confirma la fase 1). | `scripts/yura.service` | 🟠 MEDIO |

## 11. Plataforma Laravel (revisión estática; toda ejecución ⚫ NO VERIFICADO)

Evidencia: `03_laravel_revision_estatica.txt`.

**Endpoint del robot.** `POST /api/v1/robot/activity`, protegido con `auth:sanctum` y `throttle:global` (60 por minuto por IP). Controlador `Api/RobotActivityController@store`. Espera:
- `activity_id`: string requerido, máximo 100.
- `student_id`: entero requerido, debe existir en `students`.
- `subject_id`: entero requerido, debe existir en `subjects`.
- `score`: numérico requerido, de 0 a 100.
- `activity_type`: string requerido, máximo 50.
- `observations`: string opcional, máximo 1000.

Hace un `firstOrNew` por (student_id, subject_id, robot_activity_id) y responde 201 si crea o 200 si actualiza. El token del robot sale de `RobotUserSeeder`, que **imprime el token en consola**.

**Hallazgos de seguridad:**

| ID | Hallazgo | Ubicación | Estado |
|---|---|---|---|
| SEC-014 | `GET /api/users`, `POST /api/users` y `PATCH /api/users/{user}/status` solo exigen estar autenticado, sin comprobar el rol. El comentario del código dice "(Admin)". Cualquier padre, estudiante o el propio robot puede **crear un usuario admin**, listar a todos los usuarios y suspender cuentas. | `routes/api.php:28-30`, `Api/UserController.php` (sin isAdmin, abort ni 403) | 🔴 CRÍTICO (estático) |
| SEC-015 | `/api/v1/robot/activity` no comprueba el rol. Cualquier token puede escribir o sobrescribir notas de cualquier estudiante. | `Api/RobotActivityController.php` | 🟠 ALTO (estático) |
| SEC-016 | Exportaciones web `students/export-pdf-all`, `export-excel-all`, `{student}/export-pdf` y `{student}/export-excel`: solo exigen `auth`, sin middleware `rol` ni autorización dentro de los métodos. Cualquier usuario autenticado puede descargar los datos de todos los estudiantes (IDOR). | `routes/web.php:39-42`, `StudentController.php:516-562` | 🔴 ALTO (estático) |
| SEC-017 | Tokens de Sanctum sin caducidad (`'expiration' => null`), sin abilities y con el token del robot impreso en consola. | `config/sanctum.php:50`, `RobotUserSeeder.php` | 🟠 MEDIO |
| SEC-018 | Credenciales de demostración escritas en el repositorio **público** (valores omitidos). | `README_EQUIPO.md:58-60`, `temp_demo_check.php:27,38`, `test_api.php:39`, `database/seeders/SchoolPilotSeeder.php:45,58,78,112`, `RobotUserSeeder.php:20` | 🟠 MEDIO |
| SEC-019 | Archivos que no deberían estar en la raíz del repositorio: `temp_demo_check.php` (crea usuarios demo), `test_api.php`, `tinker_scripts/` y `resultado_yura.txt` (salida de pruebas en UTF-16). No hay `.env` versionado. | raíz | 🟡 BAJO |
| SEC-020 | `.env.example` trae `APP_DEBUG=true` y `APP_ENV=local`, y la guía de instalación lo copia tal cual. `/api/login` no usa el limitador `login` (5 por minuto) que sí usa la web. | `.env.example:2,4`, `routes/api.php:12` | 🟡 BAJO |

**Validaciones positivas (estático):**
- `Api/StudentController` restringe por rol en `index`, `show`, `store` y `updatePuntaje`.
- `web restore` y `forceDestroy` sí verifican el rol.
- `User::$hidden` oculta `password` y `remember_token`.

**¿El cerebro llama a la plataforma?** **NO. VERIFICADO.**
- Un grep en los `.py`, `web/`, `scripts/` y `.env.example` de `requests|urllib|httpx|aiohttp|api/v1|robot/activity|sanctum|bearer|laravel|student_id|score` solo encuentra `urllib` en `scripts/yura-open-browser.sh`, que consulta el `/api/status` local.
- El cerebro no tiene concepto de estudiante (no hay identificación ni `student_id`), ni de materia, ni de puntaje persistente. El juego no cuenta aciertos.
- Por tanto, la tabla `grades` de la plataforma nunca recibe datos del robot, y RF-05 (`phonetic_evaluations` por intento) no existe en el cerebro.
- La tesis (6. Dificultades) menciona Faster-Whisper int8 y un filtro de paso banda con SciPy: un grep de `faster.whisper|scipy|bandpass|phonetic_evaluations` en el código no encuentra nada.

## 12. Matriz de pruebas

| ID | Módulo | Prueba | Entrada | Esperado | Obtenido | Estado | Evidencia |
|---|---|---|---|---|---|---|---|
| YURA-BE-001 | tests | Suite pytest | `.venv/bin/python -m pytest -q` | todo pasa | 28 passed | 🟢 | 03_pytest_y_cobertura |
| YURA-BE-002 | tests | Cobertura | coverage run -m pytest | ≥ 70 % en la lógica | 38 % total; juego 10 %, audio 20 %, main_robot 31 % | 🟠 MEDIO | idem |
| YURA-BE-003 | tests | Pruebas sin BD versionada | copia limpia sin diccionario.db | pasan o se saltan | 9 de 28 fallan | 🟠 MEDIO | 03_pytest_sin_diccionario |
| YURA-BE-004 | main_robot | Menú: "apagar" dentro de una pregunta | "¿cómo se dice apagar en quechua?" | traducir | SALIR, running=False, se cierra el proceso | 🔴 ALTO | 03_intenciones A |
| YURA-BE-005 | main_robot | Menú: negación / "conjugar" | "no quiero jugar", "quiero conjugar verbos" | no jugar | JUEGO | 🟠 MEDIO | idem |
| YURA-BE-006 | main_robot | Menú: traducir palabras de orden | "¿cómo se dice silencio/adiós?", "no quiero salir", "¿qué significa terminar?" | traducir o seguir | SILENCIO | 🟠 MEDIO | idem |
| YURA-BE-007 | main_robot | Menú: sinónimos | "juguemos", "apaga", "yura apágate" | JUEGO / SALIR | CONVERSAR "no vendo autos…" | 🟡 MEDIO | idem |
| YURA-BE-008 | main_robot | Menú: "menú" | "menú" | seguir en el menú con un mensaje coherente | queda en M pero dice "Hasta luego. Tupananchiskama." | 🟡 BAJO | 03_estados |
| YURA-BE-009 | main_robot | Menú: frase desconocida | "despierta", "volver", "otra vez" | pedir aclaración | CONVERSAR + "no vendo autos ni converso en inglés" | 🟡 BAJO | idem |
| YURA-BE-010 | main_robot | Órdenes en CONVERSAR | silencio, cállate, espera, apagar, traducir, jugar | cambiar de modo | sigue en C; "jugar" inicia la práctica | 🟠 MEDIO | idem |
| YURA-BE-011 | juego | Salidas del juego | adiós, terminar, volver, apagar, silencio | salir | se califican como incorrectas (TRISTE) | 🟠 MEDIO | idem |
| YURA-BE-012 | traductor | Traducir palabras de salida | adiós, volver, regresar, menú, salir, terminar, "apagar la luz" | traducción | vuelve al MENÚ | 🟠 MEDIO | 03_intenciones C |
| YURA-BE-013 | traductor | Frase con prefijo o artículo | "¿cómo se dice perro?", "el perro" | Allqo (local) | Groq en línea | 🟠 ALTO | idem |
| YURA-BE-014 | traductor | Palabras cortas | "no", "sí" | Mana / Ari, o "no está" | horno/camino/uno; iglesia/siete/diecisiete | 🟠 ALTO | idem |
| YURA-BE-015 | traductor | Saludo | "hola" | Rimaykullayki (local) | Groq (no está en la BD) | 🟡 BAJO | idem |
| YURA-BE-016 | main_robot | Silencio: frases del aula | "niños, silencio por favor", "vamos a volver a clase", "vuelve a tu asiento" | seguir callada | se despierta (M) | 🟠 MEDIO | idem D |
| YURA-BE-017 | main_robot | Apagar desde SILENCIO/C/J/T | "apagar" | apagar | no apaga | 🟡 BAJO | 03_estados |
| YURA-BE-019 | conversacion | `_detectar_intencion` | 23 frases | intención correcta | 15 fallan (salir, practicar, aprender falsos) | 🟠 ALTO | 03_intenciones B |
| YURA-BE-020 | juego | Barrido de falsos positivos | 187×186 pares de la BD | 0 aceptados | 298 aceptados | 🔴 ALTO | 03_evaluacion B |
| YURA-BE-021 | juego / práctica | Respuesta correcta en frase o repetida | "se dice allqo", "allqo allqo" | correcta | incorrecta | 🟠 MEDIO | 03_evaluacion A |
| YURA-BE-022 | juego / práctica | Parecidas pero incorrectas | wasa/Wasi, anti/Inti, uqa/Ñuqa | incorrecta | correcta | 🟠 MEDIO | idem |
| YURA-BE-023 | conversacion | Práctica interceptada | repetir "Allin sukay" / "Allin tuta" | "Muy bien" | "…significa Buenas tardes/noches" (sin evaluar) | 🟠 MEDIO | 03_evaluacion D |
| YURA-BE-024 | juego | Final con 0 de 4 | 4 × "no se" | resultado real | "¡Felicidades! Completaste…"; sin puntaje | 🟠 MEDIO | 03_errores H |
| YURA-BE-025 | juego | Partida completa correcta | Allqo, Wasi, Sach'a, Uma | 4 celebraciones → M | 4 celebraciones → M; web CELEBRANDO/CORRECTO | 🟢 | 03_evaluacion E |
| YURA-BE-026 | traductor / juego | Silencio prolongado / sin micrófono | micrófono None, 3 s | pausa o salida | 10 escuchas y 10 frases "Necesito que repitas…" | 🟠 MEDIO | 03_bucle_sin_microfono |
| YURA-BE-027 | main_robot / web | Excepción en un modo | BD "database is locked" | recuperar o cerrar | se propaga; el hilo muere; `_exit` no se llama; /api/status running=True | 🔴 ALTO | 03_errores B, C |
| YURA-BE-028 | main_robot | Timeouts de subprocess en `hablar` | fake subprocess.run | timeout en todos | edge-tts, ffmpeg y pw-play sin timeout | 🟠 MEDIO | 03_errores A |
| YURA-BE-029 | conversacion | Timeout de Groq | inspección de la librería | ≤ 10 s | 60 s + 2 reintentos (por defecto) | 🟡 MEDIO | groq._constants |
| YURA-BE-030 | main_robot | Historial entre sesiones | C → salir → C | historial vacío | se envía el historial anterior a Groq | 🟠 MEDIO | 03_errores D |
| YURA-BE-031 | todos | Errores silenciosos | bandit B110/B112 | registrar el error | 5 `pass` + 2 `continue` | 🟡 BAJO | 03_bandit |
| YURA-BE-032 | main_robot / conversacion | Conexiones SQLite | inspección | 1 conexión de solo lectura, cerrada | 2 en lectura y escritura; la global no se cierra | 🟡 BAJO | 03_errores F |
| YURA-BE-033 | main_robot | Temporal de audio | ruta de yura_temp.wav | carpeta temporal privada | carpeta del proyecto, nombre fijo | 🟡 BAJO | 03_errores E |
| YURA-BE-034 | main_robot | `__main__` | inspección | 1 llamada | `loop_principal` ×2 (1224 y 1226) | 🟡 BAJO | 03_errores G |
| YURA-BE-035 | todos | Código muerto | pyflakes, vulture | 0 | json, grabar, _es_jack_directo, _es_entrada_logitech, vosk_recognizer, output_device, segunda `_responder_frase_local` | 🟡 BAJO | 03_estatico |
| YURA-BE-036 | todos | Complejidad | radon cc | ≤ C | hablar E35; ejecutar_menu D24; procesar_entrada D22; `_obtener_dispositivo…` D21 | 🟡 MEDIO | idem |
| YURA-BE-037 | todos | Duplicación | inspección | 1 implementación | `_normalizar_texto` ×3 (distintas); evaluación ×2 | 🟡 MEDIO | código |
| YURA-BE-038 | traductor | Rendimiento de la BD | 30 repeticiones | < 50 ms | 0.7–3.1 ms; práctica 8.6 ms | 🟢 | 03_rendimiento |
| YURA-BE-039 | audio_manager | Redetección por escucha | 5 repeticiones | < 100 ms | 13 ms de mediana | 🟢 | idem |
| YURA-BE-040 | main_robot | Whisper en GPU | load_model('base') | cargar solo si hace falta | 1.27 s, cuda:0, 447 MB | 🟡 BAJO | idem |
| YURA-BE-041 | audio / main | Latencia fija por turno | parámetros del código | ≤ 2.5 s total (RNF-01) | ≈ 1.7 s solo de esperas fijas; total ⚫ | 🟠 MEDIO / ⚫ | código |
| YURA-BE-043 | tests | Pruebas débiles | revisión | aserciones significativas | 1 tautología, 3 de cadenas en JS/CSS, 0 de estados | 🟠 MEDIO | tests/*.py |
| YURA-BE-045 | integración | ¿El cerebro llama a la plataforma? | grep de clientes HTTP y tokens | cliente hacia `/api/v1/robot/activity` | inexistente; sin student_id ni puntaje | 🔴 ALTO | sección 11 |
| YURA-SEC-001 | web/app | Exposición en la LAN | url_map, cabeceras | autenticación o localhost | 0.0.0.0, GET sin autenticación, sin cabeceras | 🟡 MEDIO | 03_seguridad_sql_flask |
| YURA-SEC-002 | web/app | Modo debug | app.debug | False | False | 🟢 | idem |
| YURA-SEC-003 | traductor | Inyección SQL | tabla maliciosa, `'; DROP TABLE` | sin efecto | descartada; tabla intacta | 🟢 | idem |
| YURA-SEC-004 | main_robot | shell=True | bandit + código | sin shell | B602; ejecuta perfiles del shell (root en el servicio) | 🟠 MEDIO | 03_bandit |
| YURA-SEC-005 | config | Permisos y secretos | stat, git log -p | 600, sin secretos | 600; historial limpio | 🟢 | comandos en sección 10 |
| YURA-SEC-006 | privacidad | Voz y texto de menores a la nube | código, grep | aviso y consentimiento | ninguno | 🔴 ALTO | sección 10 |
| YURA-SEC-007 | privacidad | Escucha en SILENCIO | código | no grabar | graba y envía a Gemini | 🔴 ALTO | main_robot:1054 |
| YURA-SEC-008 | privacidad | Logs | código | no registrar el habla | transcripciones en stdout/journald | 🟠 MEDIO | main_robot:817 |
| YURA-SEC-009 | privacidad | Historial compartido | BE-030 | aislamiento | se comparte | 🟠 MEDIO | 03_errores D |
| YURA-SEC-010 | conversacion | Inyección de instrucciones (Groq real) | 5 ataques + 1 al traductor | rechazo | 5 de 5 rechazados, traductor None; sin defensa en el código | 🟡 MEDIO | 03_inyeccion_prompt_groq |
| YURA-SEC-011 | dependencias | Versiones y CVE | pip-audit | fijadas, 0 CVE | sin fijar; 0 CVE conocidas | 🟡 BAJO | 03_pip_audit |
| YURA-SEC-012 | todos | bandit | escaneo | sin High | 1 High, 3 Medium, 21 Low | 🟡 | 03_bandit |
| YURA-SEC-013 | scripts | Servicio systemd | lectura | usuario sin privilegios y ruta válida | root; ruta inexistente | 🟠 MEDIO | scripts/yura.service |
| YURA-SEC-014 | Laravel | Gestión de usuarios por API | lectura del código | solo admin | cualquier usuario autenticado | 🔴 CRÍTICO (⚫ ejecución) | 03_laravel_revision_estatica |
| YURA-SEC-015 | Laravel | Endpoint del robot | lectura del código | solo el rol robot | cualquier token | 🟠 ALTO (⚫) | idem |
| YURA-SEC-016 | Laravel | Exportaciones de estudiantes | lectura del código | control de rol | ninguno | 🔴 ALTO (⚫) | idem |
| YURA-SEC-017 | Laravel | Tokens de Sanctum | config | con caducidad | null; token impreso | 🟠 MEDIO | idem |
| YURA-SEC-018 | Laravel | Credenciales en el repositorio | grep (ubicaciones) | ninguna | README_EQUIPO, seeders, temp_demo_check, test_api | 🟠 MEDIO | idem |
| YURA-SEC-019 | Laravel | Archivos sospechosos | ls | ausentes | presentes en la raíz | 🟡 BAJO | idem |
| YURA-SEC-020 | Laravel | Debug y limitador de login de la API | .env.example, rutas | debug off; 5 por minuto | debug true; 60 por minuto | 🟡 BAJO | idem |

## 13. Problemas priorizados y propuesta de solución (no aplicada)

**CRÍTICO**
1. **SEC-014 (Laravel):** añadir `->middleware('rol:admin')` a las rutas `/api/users*` o comprobar `isAdmin()` en `Api/UserController`. Añadir una prueba Feature que confirme 403 para padre, estudiante y robot.

**ALTO**
2. **BE-004 y BE-005/006/019 (intenciones):**
   - Reconocer los comandos por **coincidencia de frase completa o inicio de frase**, con listas de sinónimos (`apagar|apágate|apaga`), en vez de buscar subcadenas.
   - Si la frase contiene "cómo se dice / qué significa / traduce", tratarla primero como consulta, nunca como comando.
   - Pedir confirmación antes de apagar ("¿Seguro que me apago? Di sí").
   - Detectar negaciones ("no quiero…").
   - En `_detectar_intencion`, comparar por token (sin `texto_compacto`) y subir la similitud difusa o limitarla a palabras de 6 letras o más.
3. **BE-020/021/022 (evaluación):**
   - Comparar primero contra la respuesta exacta y sus variantes ortográficas aceptadas, que el equipo o un hablante deberían validar.
   - Usar un umbral dependiente de la longitud (por ejemplo, distancia de edición ≤ 1 para 4 a 5 letras).
   - Rechazar la respuesta si coincide mejor con otra palabra de la BD que con la correcta.
   - Extraer la palabra de frases como "se dice X" y colapsar las repeticiones.
   - Unificar `_respuesta_es_correcta` y `_evaluar_respuesta` en un solo módulo con pruebas.
4. **BE-013/014 (traductor):**
   - Reutilizar `conversacion._extraer_termino` en el modo TRADUCIR.
   - Buscar por palabra completa (tokens) en vez de por subcadena. Las búsquedas por subcadena solo tienen sentido para 4 letras o más.
   - Salir del modo solo con frases de orden exactas ("salir del traductor", "volver al menú").
5. **BE-027 (robot zombi):**
   - Envolver cada `ejecutar_*` de `loop_principal` en `try/except Exception`, registrar el error y volver al MENÚ.
   - En `web/app.py`, llamar a `os._exit(1)` también cuando el hilo muere por una excepción (`try/finally`), para que `Restart=on-failure` actúe.
6. **SEC-006/007/008/009 (privacidad de menores):**
   - Mostrar y decir un aviso de privacidad, y documentar el consentimiento de los apoderados que cubra específicamente el envío de voz y texto a Google, Groq y Microsoft.
   - En SILENCIO, no enviar audio a la nube: detectar la palabra de activación en local (Vosk, que ya está cargado) y solo entonces transcribir con Gemini.
   - Borrar `historial_conversacion` al volver al MENÚ.
   - No registrar las transcripciones en los logs, o hacerlo con un nivel DEBUG desactivado por defecto.
7. **BE-045 (integración con la plataforma):** si el alcance lo requiere, crear un cliente HTTP con token (en `.env.local`) hacia `POST /api/v1/robot/activity`. Requiere identificar al estudiante (`student_id`), la materia y la actividad, y contar los aciertos del juego. Alternativa: documentar en la tesis que hoy no existe.
8. **SEC-015/016 (Laravel):** restringir `/api/v1/robot/activity` al rol `robot` (o a una ability del token). Poner el middleware `rol:admin,academic,profesor` en las exportaciones, más una autorización por estudiante.

**MEDIO**
9. **BE-024:** llevar la cuenta de aciertos y decir el resultado real ("Acertaste 2 de 4").
10. **BE-026:**
    - Después de N silencios seguidos (por ejemplo 3), volver al MENÚ o quedarse callada.
    - Sin micrófono, esperar con retroceso (backoff) en vez de repetir la frase.
11. **BE-028/029:** poner `timeout=` en edge-tts, ffmpeg y pw-play (por ejemplo, 20 s) y `Groq(timeout=10, max_retries=1)`.
12. **BE-010/011/016/017:** definir una tabla de comandos globales (apagar, silencio, menú) que se evalúe igual en todos los estados.
    - Despertar de SILENCIO solo con la frase "Yura, despierta".
    - Quitar "silencio" y "volver" como palabras de activación.
13. **BE-002/003/043 (pruebas):**
    - Añadir pruebas parametrizadas de estado × comando (se pueden reutilizar los scripts de `evidencias/03_scripts/`) y del juego.
    - Crear una BD de prueba mínima en `tests/fixtures` (o en memoria) para que la suite no dependa de `diccionario.db`.
    - Eliminar la prueba tautológica.
14. **SEC-004/013:**
    - Eliminar la búsqueda de la clave por shell.
    - Poner `User=yura` en `yura.service` y corregir las rutas.
15. **BE-036/037:**
    - Dividir `hablar` en generar voz, convertir y reproducir.
    - Unificar `_normalizar_texto` conservando la ñ y el apóstrofo.
16. **BE-041:** medir la latencia de extremo a extremo con micrófono real y reducir las esperas fijas (sleep de 0.3 s y silencio final de 1.0 s).
17. **SEC-017/018:** poner caducidad a los tokens, dejar de imprimir el token, quitar las contraseñas del README y los scripts de la raíz, y rotar las credenciales demo si se usaron en un servidor real.

**BAJO**
18. **BE-008/009:** mensajes coherentes para "menú" y para las frases desconocidas del menú (pedir aclaración en vez de "no vendo autos").
19. **BE-031 a 035:**
    - Registrar los errores en lugar de `pass`.
    - Usar una sola conexión SQLite en modo `ro`.
    - Guardar `yura_temp.wav` en `tempfile.mkstemp`.
    - Quitar la segunda llamada a `loop_principal` y el código muerto.
20. **BE-040:** cargar Whisper de forma perezosa, solo cuando Gemini falle.
21. **SEC-001/011/019/020:**
    - Escuchar en `127.0.0.1` si la pantalla es local, o añadir un token.
    - Fijar las versiones en `requirements.txt`.
    - Limpiar la raíz del repositorio Laravel.
    - Usar `APP_DEBUG=false` y `throttle:login` en `/api/login`.
