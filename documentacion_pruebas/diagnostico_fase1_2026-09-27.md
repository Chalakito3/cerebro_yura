# Diagnóstico inicial — Fase 1 (descubrimiento)

**Proyecto:** CEREBRO YURA · **Fecha:** 27/09/2026 · **Estado general:** 🔵 EN ANÁLISIS
**Cambios realizados en esta fase:** ninguno (solo lectura).

## 1. Documentos analizados

| Documento | Ubicación | Estado |
|---|---|---|
| Tesis *Robot interactivo… U. E. Boliviano Holandés* (17/08/2026, 63 págs.) | `~/Downloads/` | [VERIFICADO] leída; requisitos extraídos en el informe 001 (95 requisitos) |
| Informe de auditoría 001 y 6 informes de subagentes | `documentacion_pruebas/` | [VERIFICADO] base de este diagnóstico; se revalidó lo que cambió después |
| Vocabulario quechua boliviano, versiones 1 y 2 | `documentacion_quechua/` | [VERIFICADO] |
| Fuentes lingüísticas: Laime Ajacopa 2007, DDE Chuquisaca (RM 599/2011), PROEIB-UMSS 2014 | `documentacion_quechua/fuentes/` | [VERIFICADO] |
| Plataforma web Laravel `yura-platform` (repositorio público del autor) | No está en esta computadora | [INFORMACIÓN FALTANTE] la copia de solo lectura se borró; no hay PHP ni MySQL para ejecutarla |
| Código de app Android, firmware ESP32, Faster-Whisper | No existen en el disco | [INFORMACIÓN FALTANTE] |

## 2. Mapa general del sistema (verificado en el código actual)

```
 Micrófono USB ──► audio_manager.py (grabación por detección de voz)
                        │
                        ▼
 main_robot.py  BrainYura ── estados: MENU · CONVERSAR · JUEGO · TRADUCIR · SILENCIO · SALIR
   │  escuchar_voz ──► gemini_transcriber.py (nube, 20 usos/día) ─► respaldo: Whisper local (GPU)
   │  texto.py (normalización, órdenes, evaluación quechua, "apágate")
   │  ├─ conversacion.py ── práctica · consultas al diccionario · Groq (nube)
   │  ├─ traductor.py ───── diccionario.db (SQLite, 15 tablas, 187 palabras)
   │  ├─ juego.py ───────── 6 palabras fijas en el código
   │  └─ resultados.py ──── resultados.db (SQLite, tabla intentos)
   │  hablar ──► Edge TTS (nube) ► ffmpeg ► pw-play ► TV (HDMI)
   ▼
 web/app.py (Flask 0.0.0.0:5000, sin autenticación)
   ├─ /                 pantalla del robot (index.html + app.js, sin botones)
   ├─ /api/status       estado cada 5 s
   ├─ /api/card         tarjetas de ejemplo fijas
   ├─ /resultados       página de resultados (NUEVA)
   ├─ /api/resultados   datos en JSON (NUEVA)
   └─ /resultados.csv   descarga para Excel (NUEVA)
 scripts/ ── yura.service (systemd de usuario, arranque automático) + Firefox a pantalla completa

 ✗ Sin conexión con la plataforma Laravel (MySQL)   ✗ Sin hardware (ESP32, motores, pantalla táctil)
```

## 3. Matriz inicial de módulos

| Módulo | Archivo | Responsabilidad | Pruebas | Estado |
|---|---|---|---|---|
| Cerebro / estados | `main_robot.py` (1.317 líneas) | Ciclo principal, menú, voz, pantalla | Sí (parcial) | 🟠 funciona; archivo muy grande, código muerto |
| Audio | `audio_manager.py` | Micrófono, calibración, grabación | Sí (parcial) | 🟠 3 funciones sin uso; re-detecta dispositivos en cada escucha |
| Transcripción | `gemini_transcriber.py` | Voz → texto en la nube | Sí | 🟡 cuota agotada 2 veces hoy [VERIFICADO en el registro] |
| Normalización | `texto.py` (nuevo) | ñ, apóstrofo, órdenes, evaluación, apagado | Sí | 🟢 VERIFICADO |
| Conversación | `conversacion.py` | Intenciones, práctica, Groq | Sí | 🟠 conversación libre contradice la tesis (5.4) |
| Traductor | `traductor.py` | Diccionario y Groq | Sí | 🟢 VERIFICADO |
| Juego | `juego.py` | Preguntas y evaluación | Sí | 🟠 palabras fijas en el código, no desde la BD |
| Resultados | `resultados.py` (nuevo) | Guardar y resumir intentos | Sí | 🟢 VERIFICADO; 0 intentos reales todavía |
| Web | `web/app.py` + plantillas + JS + CSS | Pantalla y resultados | Sí | 🟠 sin autenticación; CSS sin uso |
| Arranque | `scripts/*` | Servicio y pantalla automáticos | Manual | 🟢 VERIFICADO (arrancó sola al encender, 10:14) |
| Vocabulario | `diccionario.db` | 187 palabras | Sí | 🔴 70 correcciones pendientes de aprobación |
| Reconocedor Vosk | `model/` (58 MB) | — | — | ⚫ se carga y no se usa |

## 4. Matriz inicial de requisitos (resumen; detalle en `informes_subagentes/06_trazabilidad.md`)

| Requisito de la tesis | Estado hoy | Cambio desde el informe 001 |
|---|---|---|
| Objetivo general: robot educativo interactivo | 🟠 asistente de voz sin cuerpo robótico | — |
| OE1 interacción con actividades | 🟠 menú por voz: juego, práctica, traductor | Más estable (órdenes, apagado, bucles) |
| OE2 IA de pronunciación y retroalimentación | 🟠 evalúa texto transcrito, no pronunciación | Evaluación más estricta |
| OE3 gestión académica | ⚫ solo en la plataforma Laravel (no ejecutable aquí) | — |
| OE4 seguimiento y reportes | 🟡 **nuevo:** página y CSV de resultados locales; no llega a la plataforma | **Avance** |
| OE5 app móvil para padres | 🔴 no existe | — |
| OE6 actividades grupales | 🔴 no existe | — |
| OE7 hardware | 🔴 no existe | — |
| OE8 implementación y validación | 🟡 arranque automático; sin piloto documentado | **Avance** |
| RF-01 voz mediante botón/pantalla | 🔴 captura continua, sin botones | — |
| RF-02 % de precisión fonética | 🔴 no existe | — |
| RF-03 docente crea contenidos | 🔴 no en el cerebro | — |
| RF-04 app con notificaciones | 🔴 no existe | — |
| RF-05 registrar cada intento | 🟠 **nuevo:** se guarda cada intento en `resultados.db`; falta estudiante y envío a la plataforma | **Avance** |
| RNF-01 latencia ≤ 2,5 s | [NO VERIFICADO] medido 2,9–3,7 s en el informe 001; no re-medido | — |
| RNF-02 MySQL con integridad | [CONFLICTO DETECTADO] el cerebro usa SQLite sin relación con MySQL | — |
| RNF-03 Android 8.0+ | 🔴 no existe | — |
| Límite 5.4 "sin conversación libre con IA" | [CONFLICTO DETECTADO] el cerebro conversa con Groq | — |
| Límite 5.4 "no integrarse con asistentes comerciales" | [CONFLICTO DETECTADO] usa Google Gemini, Groq y Microsoft Edge TTS | — |
| Alcance: solo vocabulario básico | 🟡 documento de vocabulario boliviano listo; faltan las correcciones | **Avance** |

## 5. Matriz inicial de riesgos

| # | Riesgo | Nivel | Evidencia |
|---|---|---|---|
| R1 | YURA enseña palabras quechuas equivocadas | CRÍTICO | 70 correcciones confirmadas por fuentes bolivianas, sin aplicar |
| R2 | La tesis afirma resultados y hardware sin respaldo | CRÍTICO | Informe 001, sección 5 de trazabilidad |
| R3 | Privacidad de menores: la voz va a Google/Groq/Microsoft sin aviso, **también en modo silencio** | CRÍTICO | `ejecutar_silencio` sigue escuchando y transcribiendo [VERIFICADO] |
| R4 | `/resultados` y `/resultados.csv` visibles para cualquiera en la red WiFi, sin contraseña | ALTO | `web/app.py` escucha en 0.0.0.0 sin autenticación [VERIFICADO] |
| R5 | Cuota gratis de Gemini (20/día) se agota; Whisper entiende peor el quechua | ALTO | 2 avisos "Cuota agotada" hoy en el registro |
| R6 | El registro guarda lo que dicen los niños | MEDIO | 32 transcripciones en el registro de hoy |
| R7 | Registro inflado: 88 % de las líneas son mensajes de depuración | MEDIO | 86.881 de 98.379 líneas de hoy son "DEBUG AUDIO"; 46 MB |
| R8 | Nada está guardado en Git: 26 archivos modificados o nuevos | ALTO | `git status` [VERIFICADO] |
| R9 | `_obtener_api_key_groq` ejecuta bash/zsh con `shell=True` | MEDIO | `main_robot.py` [VERIFICADO] |
| R10 | Sin conexión robot ↔ plataforma: el seguimiento académico de la tesis no funciona | ALTO | Sin cliente HTTP en el cerebro [VERIFICADO] |

## 6. Lista de problemas encontrados (estado actual)

**Resueltos después del informe 001** (con pruebas; 99/99 pasan): apagado por subcadena, pantalla que cortaba palabras, ñ y apóstrofo, órdenes contra palabras, evaluador permisivo, bucles sin salida, ": Tata", esperas sin límite, "perro" rechazado, doble `loop_principal`, robot que moría en silencio, filtro de temas, "sí" perdido en la calibración, arranque automático, registro de resultados.

**Pendientes:**

| # | Problema | Prioridad | Estado |
|---|---|---|---|
| P1 | 70 palabras quechuas por corregir, 4 decisiones y 12 palabras por quitar | CRÍTICO | ⚫ BLOQUEADO: espera aprobación del equipo |
| P2 | Modo silencio sigue enviando audio a la nube | CRÍTICO | 🟡 PENDIENTE (requiere decisión de privacidad) |
| P3 | Resultados sin contraseña en la red | ALTO | 🟡 PENDIENTE |
| P4 | Juego con 6 palabras fijas en el código, no desde la BD | ALTO | 🟡 PENDIENTE |
| P5 | Sin identificación de estudiante ni envío a la plataforma | ALTO | ⚫ BLOQUEADO: falta la plataforma y una decisión |
| P6 | Código muerto: Vosk (58 MB), `grabar`, `_es_jack_directo`, `_es_entrada_logitech`, `_fuente_predeterminada_es_logitech`, `entrada.txt`, `style-draft.css`, 10 clases CSS | MEDIO | 🟡 PENDIENTE [PENDIENTE DE VALIDACIÓN] antes de borrar |
| P7 | `_obtener_api_key_groq` con `shell=True`, redundante con `cargar_archivo_claves` | MEDIO | 🟡 PENDIENTE |
| P8 | Mensajes de depuración que inflan el registro y guardan lo que dicen los niños | MEDIO | 🟡 PENDIENTE |
| P9 | Pantalla no adaptada a 7" (1024x600, 800x480) | MEDIO | ⚫ BLOQUEADO: falta saber la pantalla real |
| P10 | Latencia no re-medida con micrófono real | MEDIO | 🟡 PENDIENTE |
| P11 | Tarjeta de ejemplo con 6 frases fijas, no desde la BD | BAJO | 🟡 PENDIENTE |
| P12 | `requirements.txt` sin versiones fijas | BAJO | 🟡 PENDIENTE |
| P13 | 3 copias del diccionario en la raíz (`.respaldo`, `.respaldo_antes_correcciones`) | BAJO | [PENDIENTE DE VALIDACIÓN] |
| P14 | Nada en Git (sin historial ni respaldo) | ALTO | ⚫ BLOQUEADO: el usuario pidió no usar Git por ahora |

## 7. Planificación propuesta para las fases siguientes

| Fase | Agentes | Trabajo | Requiere |
|---|---|---|---|
| 2 Auditoría | 2, 3, 4, 7, 9 | Revalidar el código nuevo (texto.py, resultados.py, arranque) y la seguridad de las rutas nuevas | Nada |
| 3 Corrección | 3, 4, 5, 7 | P3 contraseña de resultados, P4 juego desde la BD, P7, P8, P11 | Aprobación del plan |
| 3b Vocabulario | 2 | P1 aplicar correcciones aprobadas | **Tu aprobación palabra por palabra** |
| 4 Limpieza | 6 | P6, P12, P13 (con referencias y pruebas antes de borrar) | Aprobación |
| 5 Pruebas | 8 | Unitarias, integración, navegador, seguridad; latencia con micrófono real | Una persona que hable al micrófono |
| 6–7 | 0, 10 | Verificación y informe 002 en PDF | — |

**Estado general: PROYECTO NO VERIFICADO — EXISTEN PENDIENTES.**

<<<PAGINA>>>

# Actualización del diagnóstico (después del ciclo 1)

**Verificado en esta revisión (sin modificar nada):**

| Indicador | Fase 1 inicial | Ahora | Evidencia |
|---|---|---|---|
| Pruebas automáticas | 99 pasan | **109 pasan** | `pytest -q` |
| Líneas del registro | ~4.000 por hora (88 % técnicas) | **161 en la última hora** | `journalctl --user -u yura --since -1h` |
| Lo que dicen los niños en el registro | Se guardaba completo | Solo cantidad de palabras | `depuracion.py` |
| `/resultados` desde la red | Abierto | **403 sin contraseña** | Prueba en vivo desde 192.168.40.194 |
| Modo silencio | Enviaba audio a Google | Solo Whisper local | 3 pruebas automáticas |
| Código muerto | 4 funciones + Vosk + tema roto | Quitados | Búsqueda de referencias + pruebas |
| Servicio | Instalado | Activo | `systemctl --user is-active yura` |
| Intentos reales guardados | 0 | **0** (nadie ha jugado aún) | `resultados.db` |

**Siguen pendientes (sin cambios desde el ciclo 1):**

| # | Pendiente | Estado |
|---|---|---|
| P1 | Vocabulario: *K'uchu* (mesa), *T'anta wasi* (escuela), *Mak'a* (mano), *Wanak'u* (abeja) y las demás del documento 002 siguen igual | ⚫ BLOQUEADO: espera aprobación |
| P4, P11 | Juego y tarjetas desde el diccionario | ⚫ BLOQUEADO por P1 |
| P5 | Conexión con la plataforma Laravel | ⚫ BLOQUEADO: no está en esta computadora; alcance sin definir |
| P9 | Pantalla de 7" | ⚫ BLOQUEADO: falta el modelo de pantalla |
| P10 | Latencia y modo silencio con micrófono real | 🟡 PENDIENTE: requiere una persona hablando |
| P14 | 28 archivos sin respaldo en Git | ⚫ BLOQUEADO: el usuario pidió no usar Git |
| Limpieza | `model/` (58 MB), `entrada.txt`, `style-draft.css`, 2 respaldos del diccionario, 9 clases CSS sin uso | [PENDIENTE DE VALIDACIÓN] |
| Privacidad | Voz enviada a Google, Groq y Microsoft fuera del modo silencio, sin aviso | 🟡 PENDIENTE: decisión del equipo |

**Estado: PROYECTO NO VERIFICADO — EXISTEN PENDIENTES.**
