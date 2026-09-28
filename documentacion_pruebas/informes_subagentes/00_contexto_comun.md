# Contexto común de la auditoría YURA (2026-09-27)

## Rutas
- Proyecto auditado (cerebro del robot, Python): `/home/yura/Proyecto Yura /cerebro_yura`  (OJO: la carpeta "Proyecto Yura " termina en espacio; usar comillas)
- Entorno Python del proyecto: `.venv/bin/python` (todas las librerías instaladas; `pytest` disponible)
- Plataforma web (Laravel/PHP, repo público MENARWIL/yura-platform, copia SOLO LECTURA): `/tmp/claude-1000/-home-yura-Proyecto-Yura--cerebro-yura/e3f2d4b6-69bd-45d2-b317-15177a7e8d72/scratchpad/yura-platform`
  - En esta computadora NO hay PHP, Composer ni MySQL: la plataforma NO se puede ejecutar → sus funciones en ejecución son NO VERIFICADO.
- Documento de requisitos (tesis, PDF 60+ páginas): `/home/yura/Downloads/YURA ROBOT INTERACTIVO PARA LA PRÁCTICA Y SEGUIMIENTO DEL APRENDIZAJE DEL QUECHUA EN ESTUDIANTES DE SEXTO DE PRIMARIA DE LA UNIDAD EDUCATIVA BOLIVIANO HOLANDES 17_08_2026.pdf`
  - Página impresa N del documento = página N+10 del PDF (leer con la herramienta Read y el parámetro `pages`).
  - Secciones clave: 5.2 Objetivos específicos (pdf 46), 5.3 Alcances (pdf 46-48), 5.4 Límites (pdf 48-49), 6.3 Recursos (pdf 50), 7.1 Actividades ejecutadas (pdf 51), 7.3 RF-01..RF-05 y RNF-01..RNF-03 (pdf 52), 7.4 UML/BD/casos de uso/despliegue (pdf 53-58), 7.6 y 8 Resultados (pdf 59), 9 Conclusiones (pdf 60). Anexos desde pdf ~63.
- Carpeta de salida: `/home/yura/Proyecto Yura /cerebro_yura/documentacion_pruebas/`
  - Informes de subagentes: `informes_subagentes/NN_nombre.md`
  - Evidencias (capturas, salidas de comandos): `evidencias/`

## Reglas obligatorias para todos los subagentes
1. SOLO LECTURA sobre el proyecto: NO modificar, crear ni borrar archivos del proyecto (código, base de datos, configuración, pruebas). Única excepción: escribir tu informe y tus evidencias en `documentacion_pruebas/`.
2. La base de datos se abre SIEMPRE en solo lectura: `sqlite3.connect('file:diccionario.db?mode=ro', uri=True)`.
3. NO mostrar ni copiar el contenido de `.env.local` (tiene claves reales). Se puede comprobar que existe y qué variables define, nunca sus valores.
4. "NO DAR POR BUENO LO QUE NO HA SIDO VERIFICADO". Prohibido: "parece funcionar", "debería funcionar", "probablemente". Usar VERIFICADO / NO VERIFICADO con evidencia (comando + salida, archivo:línea).
5. Clasificación: 🟢 APROBADO · 🟡 OBSERVACIÓN · 🟠 REQUIERE CORRECCIÓN · 🔴 ERROR CRÍTICO · ⚫ NO VERIFICADO. Prioridad: CRÍTICO / ALTO / MEDIO / BAJO.
6. Identificadores de prueba: YURA-BD-###, YURA-QCH-###, YURA-FR-###, YURA-BE-###, YURA-INT-###, YURA-EXT-###, YURA-SEC-###, YURA-TRZ-###.
7. NO corregir nada. Solo detectar, probar y documentar con propuesta de solución.
8. Contenido quechua: NO inventar traducciones. Variante declarada por el equipo: **quechua boliviano de Cochabamba**. Si no hay certeza → NO VERIFICADO / "requiere revisión de un hablante". Documentar variaciones dialectales.
9. Llamadas a servicios en línea (Groq, Gemini, Edge TTS) tienen cuota gratuita: máximo 25 llamadas por subagente.
10. Escribir todo en español claro.

## Qué es el cerebro (arquitectura real verificada)
- `web/app.py` (Flask, 0.0.0.0:5000): crea `BrainYura` en un hilo; rutas `GET /`, `GET /api/status`, `GET /api/card`. La pantalla (`index.html` + `app.js`) NO tiene botones ni formularios: solo muestra estado cada 5 s. Todo se maneja por voz.
- `main_robot.py`: `BrainYura` con estados MENU, CONVERSAR, JUEGO, TRADUCIR, SILENCIO, SALIR. Escucha (`audio_manager.grabar_hasta_silencio`) → transcribe con Gemini (`gemini_transcriber.py`, modelo gemini-3.8-flash) y respaldo Whisper local ("base", en GPU) → decide (`conversacion.py`, `traductor.py`, `juego.py`) → habla con Edge TTS (voz es-MX-DaliaNeural) + ffmpeg + pw-play.
- `conversacion.py`: intenciones, práctica de vocabulario, Groq (modelo openai/gpt-oss-120b) con vocabulario del diccionario inyectado para no inventar.
- `traductor.py`: lee todas las tablas `nivelN_categoria` de `diccionario.db` (SQLite, 15 tablas, 187 filas; columnas id, palabra_frase=quechua, pronunciacion, traduccion=español, significado [falta en 5 tablas]).
- Hardware real hoy: micrófono = audífonos USB C-Media; voz sale por el televisor HDMI. NO hay pantalla táctil, NI ESP32, NI motores: `mover_actuador` solo imprime texto.
- Vosk (`model/`, 58 MB) se carga pero nunca se usa para transcribir.

## Cambios hechos HOY antes de la auditoría (sin commit todavía; considerar en regresión)
1. main_robot: `cargar_archivo_claves()` lee `.env.local`; "menú/salir" en conversación ya no apaga; "salir/adiós" en menú → SILENCIO; solo "apagar" apaga y cierra el proceso (web/app.py `os._exit(0)`); alerta si falta diccionario.db; `__main__` llama `loop_principal()`.
2. conversacion: no crea diccionario vacío si falta; Groq vía `traductor.consultar_modelo_groq` (reasoning_effort low, max_completion_tokens); vocabulario verificado inyectado en el prompt; ambigüedades con `describir_opciones`.
3. traductor: `vocabulario_relevante`, `formatear_vocabulario`, `describir_opciones`, `consultar_modelo_groq`; traductor dice todas las opciones si la palabra es ambigua (papa/papá).
4. gemini_transcriber: modelo por defecto gemini-3.8-flash (gemini-2.5-flash ya no está disponible para cuentas nuevas; verificado con error 404).
5. Base de datos: `nivel1_familia` id 1 Tayta→**Tata** (Padre) y nueva fila id 7 Tata = Papá (pedido explícito del equipo: en Cochabamba padre/papá = tata). Respaldo previo: `diccionario.respaldo.db`.
6. Nuevos: `requirements.txt`, `.env.example`, `tests/test_vocabulario_groq.py`. Hoy: 28 pruebas, 28 pasan.

## Hallazgos ya documentados en la Fase 1 (no repetir la búsqueda; verificar/profundizar si toca a tu área)
- `_normalizar_texto` duplicado en 3 módulos y destruye ñ y apóstrofo ("Ñuqaqa"→"uqaqa", "p'unchay"→"p unchay") en main_robot y traductor.
- Sin uso: `AudioManager.grabar`, `_es_jack_directo`, `_es_entrada_logitech`, `_fuente_predeterminada_es_logitech`; reconocedor Vosk; `import json` en main_robot; `entrada.txt`; `style-draft.css` (solo con ?theme=soft, nada lo activa); 9 clases CSS sin uso en style.css (detail-copy, detail-kicker, detail-stats, mode-active, mode-detail, mode-index, mode-label, mode-strip, progress-stat).
- `_obtener_api_key_groq` ejecuta bash/zsh con shell=True leyendo .bashrc (redundante con cargar_archivo_claves).
- Tarjetas `CARD_EXAMPLES` (web/app.py): el campo "meaning" repite la palabra quechua en vez del significado en español.
- `juego.py` mapeo de emergencia agua=yaku contradice BD (agua=Uma); `Uma` también es "cabeza" en partes_del_cuerpo.
- Columna `pronunciacion` contiene rutas de audio Windows (C:/audios/...) inexistentes.
- `tests/test_conversacion_ui.py::test_silence_command_is_recognized_without_noise` no prueba nada (tautología).
- Pruebas dependen de diccionario.db, que Git ignora.
- `scripts/yura.service` y `yura.desktop` apuntan a /home/yura/Documents/YURAQUECHUA/Proyecto_Quechua (no existe); servicio corre como root; menciona Logitech.
- `requirements.txt` sin versiones fijas.
