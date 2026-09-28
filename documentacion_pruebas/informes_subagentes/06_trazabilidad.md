# Informe 06 — Auditoría de trazabilidad documento ↔ sistema (YURA)

- **Subagente:** 6 — Auditor de trazabilidad
- **Fecha:** 2026-09-27
- **Documento auditado:** tesis "ROBOT INTERACTIVO CON INTELIGENCIA ARTIFICIAL ASR PARA EL APOYO EN LA PRÁCTICA DEL IDIOMA QUECHUA…" (PDF de 17/08/2026, **63 páginas en total**). Página impresa N = página PDF N+10. En este informe se cita **p. impresa (pdf N)**.
- **Sistemas auditados:** cerebro Python (`/home/yura/Proyecto Yura /cerebro_yura`, 1 commit `aac001b` + cambios sin commit de hoy) y plataforma Laravel (copia de solo lectura `…/scratchpad/yura-platform`, commit `d419bd0` del 2026-09-15, clon superficial). La plataforma **no se pudo ejecutar** (no hay PHP, Composer ni MySQL): todo lo que depende de ejecutarla queda como "código presente, ejecución NO VERIFICADA".
- **Reglas:** solo lectura; no se ha corregido nada; no se ha mostrado ninguna clave; no se ha arrancado el robot ni usado puertos; 0 llamadas a servicios en línea.

### Evidencias generadas
| Archivo (`documentacion_pruebas/evidencias/`) | Contenido |
|---|---|
| `06_tesis_extracto_pdf45-63.txt` | Texto literal de la tesis, pdf 45-63 (objetivos → anexos), sacado con `pdftotext -layout` |
| `06_busquedas_trazabilidad.txt` | Todos los grep (cerebro y plataforma) que prueban presencia o ausencia, `api.php`, BD de pruebas de phpunit, `pytest -q` (28 pasan), búsqueda en disco de APK/firmware/datos de campo |
| `06_hardware_entorno.txt` | Hardware y sistema operativo reales (os-release, lscpu, free, lsblk, lsusb, xrandr, dispositivos táctiles, puertos serie, GPU, paquetes) |
| `06_plataforma_extractos.txt` | Extractos de código Laravel: API del robot, migraciones de grupos/interacciones, sembrado de categorías, actividades robot, control de padres |
| `06_palabras_juego_en_bd.txt` | Las 6 palabras fijas del juego buscadas en `diccionario.db` (abierta en solo lectura) |

Los diagramas de las pdf 53-58 (clases, BD, casos de uso, despliegue) son imágenes. Los leí directamente con la herramienta Read.

---

## 1. Resumen ejecutivo

**Veredicto de tutor:** el documento describe un sistema distinto del que existe. Lo construido es un **asistente de voz de software** que corre en un PC de escritorio: escucha con Gemini en la nube y usa openai-whisper como respaldo, conversa con Groq, habla con Edge TTS y muestra el estado en un televisor por HDMI. A eso se suma una **plataforma web Laravel de gestión académica** bastante completa. Las dos piezas **no están conectadas**. El robot físico (ESP32, motores, sensores, pantalla táctil de 7"), la app Android, Faster-Whisper, la "precisión fonética", la tabla `phonetic_evaluations`, las actividades grupales y todas las cifras de resultados **no tienen ninguna evidencia en los repositorios ni en esta computadora**. Además, varias de ellas **contradicen** el código y el hardware reales.

Se extrajeron **95 requisitos o promesas verificables** (tabla completa en §3):

| Estado | Cantidad | % |
|---|---:|---:|
| 🟢 Cumplido y verificado | 3 | 3,2 % |
| 🟡 Implementado en código (plataforma), ejecución NO VERIFICADA | 18 | 18,9 % |
| 🟠 Parcial | 28 | 29,5 % |
| 🔴 No implementado / contradicho | 27 | 28,4 % |
| ⚫ No verificable (falta evidencia) | 19 | 20,0 % |

Si se agrupa en las 4 categorías pedidas (🟡 cuenta como parcial): **cumplidos 3,2 % · parciales 48,4 % · no implementados/contradichos 28,4 % · no verificables 20,0 %**.

**Núcleo formal (RF-01..RF-05, RNF-01..RNF-03, 8 requisitos): 0 cumplidos**. 1 🟡 (RNF-02), 2 🟠 (RF-01, RF-03), 3 🔴 (RF-02, RF-04, RF-05), 2 ⚫ (RNF-01, RNF-03).
**Objetivos (general + 8 específicos): 0 cumplidos**. 1 🟡, 4 🟠, 2 🔴, 2 ⚫.

Las 5 contradicciones más graves para la defensa:
1. **ASR:** la tesis dice Faster-Whisper int8 "optimizado" y "calibrado". En el código no hay Faster-Whisper: se usa **Google Gemini en la nube** (`gemini_transcriber.py:18`) y, como respaldo, **openai-whisper "base"** forzado a español (`main_robot.py:17,417-419,825`).
2. **Conversación libre:** el límite 5.4 dice que "no implementará conversaciones libres mediante IA", pero el código **conversa libremente con Groq** (`conversacion.py:579` "Conversa naturalmente…").
3. **Hardware:** la tesis afirma que "se completó la construcción e integración física del prototipo". Hoy no hay ESP32, ni puerto serie, ni pantalla táctil, ni motores. `mover_actuador` solo imprime texto (`main_robot.py:382-383`). El sistema operativo es **Ubuntu 24.04**, no Debian 13.
4. **Precisión fonética y registro:** RF-02, RF-05, la conclusión 3 y el resultado de 87,4 % dependen de medir la pronunciación y guardarla en `phonetic_evaluations`. Esa tabla **no existe en ningún repositorio, ni siquiera en el diagrama de BD de la propia tesis** (pdf 54). El cerebro **no guarda ningún intento** (no hay INSERT ni `commit()`).
5. **Integración robot ↔ plataforma:** existe el endpoint `POST /api/v1/robot/activity` (`routes/api.php:31`), pero el cerebro **no tiene ningún cliente HTTP**, ni URL o token de la plataforma (`.env.example` solo define GROQ_API_KEY y GEMINI_API_KEY), ni forma de saber qué estudiante habla. Los reportes a docentes y padres nunca pueden contener datos del robot.

---

## 2. Requisitos y promesas extraídos del documento

Formato: **ID — texto resumido (p. impresa / pdf)**. El ID coincide con la fila de la matriz.

**Objetivos (5.1-5.2)**
- TRZ-001 — OG: "Desarrollo del robot educativo interactivo para la práctica del idioma quechua…" (p.35/pdf45)
- TRZ-002 — OE1: módulo de interacción del robot con actividades y dinámicas educativas (p.36/pdf46)
- TRZ-003 — OE2: módulo de IA para ejercicios de pronunciación y retroalimentación automática (p.36/pdf46)
- TRZ-004 — OE3: módulo de gestión académica (docentes, estudiantes, registros de desempeño) (p.36/pdf46)
- TRZ-005 — OE4: módulo de seguimiento académico, reportes y consulta de progreso (p.36/pdf46)
- TRZ-006 — OE5: módulo móvil de consulta para padres (p.36/pdf46)
- TRZ-007 — OE6: módulo de actividades grupales (equipos, retos, resultados) (p.36/pdf46)
- TRZ-008 — OE7: construcción e integración del hardware del robot (p.36/pdf46)
- TRZ-009 — OE8: procedimiento de implementación y uso en el entorno educativo "para probar su efectividad" (p.36/pdf46)

**Alcances (5.3)**
- TRZ-010 — 5.3.1 Robot con pantalla táctil, micrófono, parlantes y mini PC (p.36/pdf46)
- TRZ-011 — 5.3.2 Reconocimiento básico de voz para ejercicios de pronunciación **previamente definidos** con retroalimentación inmediata (p.36/pdf46)
- TRZ-012 — 5.3.3 Plataforma web: administración de docentes, estudiantes, cursos y actividades (p.37/pdf47)
- TRZ-013 — 5.3.4 Registrar el desempeño en actividades **con YURA** y generar reportes para docentes y padres (p.37/pdf47)
- TRZ-014 — 5.3.5 App móvil para padres: progreso, reportes y seguimiento (p.37/pdf47)
- TRZ-015 — 5.3.6 Actividades grupales: asignación de equipos, visualización de puntajes y ejecución (p.37/pdf47)
- TRZ-016 — 5.3.7 Diseño e integración de la estructura física y la electrónica (p.37/pdf47)
- TRZ-017 — 5.3.8 Procedimiento de configuración y puesta en marcha, con pruebas funcionales y validación con usuarios (p.38/pdf48)

**Límites (5.4)**
- TRZ-018 — No reemplazará al docente (p.38/pdf48)
- TRZ-019 — No impartirá la currícula completa: solo ejercicios **previamente definidos** de vocabulario, pronunciación y comprensión (p.38/pdf48)
- TRZ-020 — **No implementará conversaciones libres mediante IA**: solo actividades previamente configuradas (p.38/pdf48)
- TRZ-021 — No hará evaluaciones oficiales ni pondrá calificaciones finales (p.38/pdf48)
- TRZ-022 — No enseñará otros idiomas: solo quechua (p.38/pdf48)
- TRZ-023 — Los padres no podrán modificar información académica (p.38/pdf48)
- TRZ-024 — No gestionará procesos administrativos, financieros ni de RR. HH. (p.38/pdf48)
- TRZ-025 — No se integrará con plataformas externas ni con asistentes comerciales (Alexa, Google Assistant, Siri) (p.38/pdf48)
- TRZ-026 — Sin reconocimiento facial ni biométrico (p.38/pdf48)
- TRZ-027 — Sin fabricación industrial: solo "prototipo funcional para validación académica" (p.39/pdf49)
- TRZ-028 — No garantizará conectividad permanente, "pudiendo operar las funcionalidades principales" en el entorno piloto (p.39/pdf49)
- TRZ-029 — No reemplazará la interacción social docente-estudiante (p.39/pdf49)

**Requisitos formales (7.3)**
- TRZ-030 — RF-01: capturar comandos de voz **en quechua** mediante **botón/pantalla** e iniciar la evaluación (p.42/pdf52)
- TRZ-031 — RF-02: el ASR devuelve la transcripción **con porcentaje de precisión fonética** (p.42/pdf52)
- TRZ-032 — RF-03: la web permite al docente crear **unidades temáticas, palabras clave y retos** (p.42/pdf52)
- TRZ-033 — RF-04: la app móvil muestra gráficos de avance y **notifica a los apoderados en tiempo real** (p.42/pdf52)
- TRZ-034 — RF-05: registrar **cada intento** en la tabla `phonetic_evaluations` con marca de tiempo (p.42/pdf52)
- TRZ-035 — RNF-01: latencia de ASR + respuesta del robot **≤ 2,5 s** (p.42/pdf52)
- TRZ-036 — RNF-02: MySQL con integridad referencial y ACID (p.42/pdf52)
- TRZ-037 — RNF-03: app fluida en Android 8.0 o superior (p.42/pdf52)

**Casos de uso (7.4.2, pdf 55-57)**
- Administrador (p.45/pdf55): TRZ-038 Consultar reportes · TRZ-039 Gestionar usuarios · TRZ-040 Gestionar actividades · TRZ-041 Gestionar cursos · TRZ-042 Gestionar estudiantes · TRZ-043 Gestionar padres · TRZ-044 Gestionar docentes
- Docente (p.46/pdf56): TRZ-045 Consultar seguimiento académico · TRZ-046 Generar reportes · TRZ-047 Consultar resultados · TRZ-048 Crear grupos · TRZ-049 Asignar actividades · TRZ-050 Modificar actividades · TRZ-051 Crear actividades
- "Padre de Familia / Tutor" (p.47/pdf57; **el actor dibujado es "Estudiante"**): TRZ-052 Consultar resultado · TRZ-053 Participar en actividad grupal · TRZ-054 Practicar pronunciación · TRZ-055 Realizar actividad

**Arquitectura de despliegue (1.4.7 p.24/pdf34 y 7.4.3 p.48/pdf58)**
- TRZ-056 Hardware ESP32 (C++) "Movimiento y Obstáculos", conectado al cerebro por Serial USB
- TRZ-057 Frontend web HTML/PHP/CSS
- TRZ-058 App móvil Android/Kotlin conectada por REST API
- TRZ-059 Cerebro: PC i3 3.ª gen, 8 GB, **Debian 13**, Python, **Faster-Whisper ASR**
- TRZ-060 Enlace cerebro ↔ servidor web por **WiFi/REST**
- TRZ-061 Servidor web central Laravel/PHP
- TRZ-062 BD local SQLite
- TRZ-063 BD web MySQL

**Recursos y presupuesto (6.3-6.4, p.40-41/pdf50-51)**
- TRZ-064 Unidad central: Intel i3, SSD 128 GB, 8 GB RAM, Linux Debian 13 para ASR
- TRZ-065 Microcontrolador secundario DevKit v1 (ESP32): motores DC, servomotores, sensores de proximidad
- TRZ-066 Micrófono de alta sensibilidad con supresión de ruido, altavoces amplificados y pantalla LCD 7" táctil
- TRZ-067 Entorno de software: Apache, PHP 8.2, MySQL 8.0, Android Studio, VS Code
- TRZ-068 Presupuesto de 1675 Bs (mini PC, ESP32, pantalla 7", micrófono y altavoces, batería LiFePO4, impresiones)

**Ejecución (7.1, 7.2, 7.5, 7.6, p.41-49/pdf51-59)**
- TRZ-069 "Se completó la construcción e integración física del prototipo" (p.41/pdf51)
- TRZ-070 "Puesta en marcha de la API Laravel con persistencia relacional en MySQL" (p.41/pdf51)
- TRZ-071 "Optimización del motor ASR Faster-Whisper en Python para Linux Debian" (p.41/pdf51)
- TRZ-072 "Prueba funcional de la APK móvil Android" (p.41/pdf51)
- TRZ-073 Consentimiento informado de apoderados para recoger métricas fonéticas de forma anónima (p.42/pdf52)
- TRZ-074 Seguimiento con Trello, Git/GitHub y "pruebas sintéticas de audio para validar la precisión ASR" (p.48/pdf58)
- TRZ-075 Dificultad 1: filtro digital pasa-banda en Python (**SciPy**) (p.49/pdf59)
- TRZ-076 Dificultad 1: ajuste del **umbral VAD de Faster-Whisper** (p.49/pdf59)
- TRZ-077 Dificultad 2: **Faster-Whisper int8**, inferencia de **1,2 s por palabra** (p.49/pdf59)

**Resultados (8, p.49/pdf59)**
- TRZ-078 8.1 Cualitativos: los estudiantes perdieron la timidez, se entusiasmaron por "alcanzar altos puntajes en el robot" y reforzaron el trabajo en equipo en las "dinámicas grupales"
- TRZ-079 8.2 **87,4 %** de reconocimiento correcto de **fonemas** en quechua, con un ASR "calibrado para niños"
- TRZ-080 8.2 Intentos orales por estudiante: de **2 a 9** interacciones efectivas por sesión
- TRZ-081 8.2 **78,5 % (77 apoderados)** instalaron la APK y revisaron los reportes
- TRZ-082 8.3 "Revitalizó el interés de las familias… en el Distrito 9"

**Conclusiones (9, p.50/pdf60)**
- TRZ-083 C1: "Se cumplió exitosamente el desarrollo… integrando ASR con IA, desarrollo web en Laravel y app móvil Android"
- TRZ-084 C2: "Faster-Whisper ASR demostró ser una solución precisa y eficiente… en tiempo real"
- TRZ-085 C3: "El esquema relacional en MySQL corregido… permite almacenar métricas fonéticas y sincronizarlas con apoderados"
- TRZ-086 C4: "La validación en la U.E. confirmó un impacto altamente positivo"

**Otras promesas verificables del texto**
- TRZ-087 Padres recibirán "reportes y **alertas**" en la app (4.2, p.35/pdf45)
- TRZ-088 Los docentes administran el contenido curricular en la plataforma web (3.3, p.34/pdf44), es decir, el contenido del robot se gestiona desde la web
- TRZ-089 Encuesta a 98 estudiantes de 6.º A, B y C (1.1.4, p.3-10/pdf13-20)
- TRZ-090 Del diagnóstico: el robot habla y repite palabras, pregunta, "emite sonidos y luces", "se desplaza dentro del aula" y felicita (p.10/pdf20)
- TRZ-091 Cronograma, fase 5: "Entrenamiento y calibración ASR Faster-Whisper" (6.1, p.39/pdf49)
- TRZ-092 Clase UML `Pronunciacion` (precision: double, retroalimentacion) y `Grupo` (puntaje) (7.4.1a, p.43/pdf53)
- TRZ-093 Modelo de BD de la tesis (7.4.1b, p.44/pdf54)
- TRZ-094 7.4.4 "Esquema completo de base de datos" (p.48/pdf58)
- TRZ-095 Anexos A-F: cronograma, fotografías, actas, instrumentos, capturas, respaldos (p.53/pdf63)

---

## 3. Matriz de trazabilidad

Columnas: **BD / Backend / Frontend** indican dónde hay algo implementado (C = cerebro Python, P = plataforma Laravel, — = nada). **Probado:** "pytest C" = cubierto por las 28 pruebas del cerebro (ejecutadas hoy, 28/28 pasan). "Pest P (no ejecutado)" = existe una prueba en la plataforma, pero no se pudo ejecutar aquí. "No" = no hay prueba.
Rutas de la plataforma relativas a `yura-platform/`.

| ID | Requisito / promesa (pág.) | Implementado | BD | Backend | Frontend | Probado | Evidencia | Estado |
|---|---|---|---|---|---|---|---|---|
| TRZ-001 | OG: robot educativo interactivo (p.35) | Parcial: asistente de voz de software sin cuerpo robótico | C: SQLite | C | C: pantalla de estado | pytest C (parcial) | `main_robot.py` (BrainYura), `web/app.py:160-177`; hardware real en `06_hardware_entorno.txt` | 🟠 |
| TRZ-002 | OE1: módulo de interacción con actividades (p.36) | Menú por voz: conversar, jugar, traducir, practicar, silencio, apagar | C | C | C (solo muestra estado) | pytest C (conversación y UI) | `main_robot.py:937-1128`; `juego.py`; `conversacion.py:674-677` | 🟠 |
| TRZ-003 | OE2: IA de pronunciación y retroalimentación (p.36) | Retroalimentación correcto/incorrecto por **similitud de texto** transcrito, no por pronunciación | — | C | C (CORRECTO/INCORRECTO) | No (sin pruebas de `juego.py`) | `juego.py:36-85,163-174`; `conversacion.py:255-288` | 🟠 |
| TRZ-004 | OE3: gestión académica (p.36) | CRUD de estudiantes, usuarios, docentes, tutores, cursos, paralelos, materias, notas y asistencia | P | P | P (Blade) | Pest P (no ejecutado); `resultado_yura.txt` = 5 pasadas antiguas | `routes/web.php:41-123` | 🟡 |
| TRZ-005 | OE4: seguimiento y reportes (p.36) | Exportación PDF/Excel, historial de notas, dashboards. **Sin datos del robot** (nunca los recibe) | P | P | P | Pest P (no ejecutado) | `routes/web.php:42-46,78-84`; `DashboardController.php:48-98`; cerebro sin cliente HTTP (`06_busquedas…`) | 🟠 |
| TRZ-006 | OE5: módulo móvil para padres (p.36) | No hay APK ni código Android. Existen API Sanctum y panel web de tutor | P | P: `/api/login`, `/api/tutor/my-children` | — (APK ausente) | No | `routes/api.php:12,20`; `TutorController.php:87`; búsqueda de *.apk/*.kt sin resultados | ⚫ |
| TRZ-007 | OE6: actividades grupales (p.36) | Tablas `groups` y `group_student` sin controlador, ruta ni vista. En el cerebro no hay nada | P (solo tablas) | — | — | No | migración `2026_07_02_000005…:11-26`; grep `Group::` en app/Http → ninguno; grep `grupo\|equipo\|puntaje` en C → nada | 🔴 |
| TRZ-008 | OE7: construcción e integración del hardware (p.36) | No hay ESP32, motores, sensores ni pantalla táctil | — | `mover_actuador` = print | — | No | `main_robot.py:382-383`; `lsusb`, `/dev/ttyUSB*` inexistente, 0 dispositivos táctiles (`06_hardware_entorno.txt`) | 🔴 |
| TRZ-009 | OE8: implementación y uso para "probar su efectividad" (p.36) | No hay manual, registro de piloto ni datos de uso | — | — | — | No | Anexos vacíos (pdf 63); `scripts/yura.service` apunta a una ruta inexistente (hallazgo de la Fase 1) | ⚫ |
| TRZ-010 | 5.3.1 pantalla táctil, micrófono, parlantes, mini PC (p.36) | Micrófono = audífonos USB C-Media; salida = TV HDMI 4K; PC i3-10100; **sin pantalla táctil ni botones** | — | C | C (sin controles) | pytest C (UI) | `lsusb` 0d8c:0012; `xrandr` HDMI-0; `grep <button\|onclick` → nada | 🟠 |
| TRZ-011 | 5.3.2 reconocimiento básico de voz para ejercicios predefinidos, con retroalimentación inmediata (p.36) | ASR sí (Gemini en la nube y Whisper local). El juego tiene 6 palabras fijas en el código, no configurables por el docente | C | C | C | pytest C (respaldo de transcripción) | `main_robot.py:465-475` (`["gato","perro","sol","agua","casa","arbol"]`); "árbol" no está en la BD (`06_palabras_juego_en_bd.txt`) | 🟠 |
| TRZ-012 | 5.3.3 plataforma web para docentes, estudiantes, cursos y actividades (p.37) | Docentes, estudiantes y cursos sí. "Actividades" solo como notas tipo robot | P | P | P | Pest P (no ejecutado) | `routes/web.php:49,95,99-103`; `GradeController.php:418-486` | 🟡 |
| TRZ-013 | 5.3.4 registrar desempeño de actividades con YURA (p.37) | La plataforma recibe (`POST /api/v1/robot/activity`), pero el **robot no envía nada** ni sabe qué estudiante habla | P: `grades` | P sí / C no | P | Pest P (no ejecutado) | `routes/api.php:31`; `Api/RobotActivityController.php:13-42`; `.env.example` del cerebro solo tiene GROQ/GEMINI | 🟠 |
| TRZ-014 | 5.3.5 app móvil para padres (p.37) | Ver TRZ-006 | P | P | — | No | Ídem TRZ-006 | ⚫ |
| TRZ-015 | 5.3.6 equipos, puntajes grupales, ejecución grupal (p.37) | Nada funcional | P (tablas sin uso) | — | — | No | Ídem TRZ-007 | 🔴 |
| TRZ-016 | 5.3.7 estructura física y electrónica (p.37) | No existe | — | — | — | No | Ídem TRZ-008 | 🔴 |
| TRZ-017 | 5.3.8 procedimiento, pruebas funcionales y validación con usuarios (p.38) | Hay pruebas automatizadas (28 en C) y guía de instalación de P (`README_EQUIPO.md`). La validación con usuarios no tiene evidencia | — | — | — | pytest C 28/28 | `06_busquedas…` (pytest); `README_EQUIPO.md`; `comandospara ejecutaryura.txt` | 🟠 |
| TRZ-018 | Límite: no reemplaza al docente (p.38) | Afirmación pedagógica, no verificable en código | — | — | — | — | — | ⚫ |
| TRZ-019 | Límite: solo ejercicios **previamente definidos** (p.38) | Hay práctica con vocabulario de la BD, pero también conversación abierta con LLM | C | C | — | pytest C | `conversacion.py:190-220` (práctica); `conversacion.py:579` (libre) | 🟠 |
| TRZ-020 | Límite: **sin conversación libre con IA** (p.38) | **Contradicho**: modo CONVERSAR con Groq (openai/gpt-oss-120b) | — | C | — | pytest C (`test_conversacion_envia_vocabulario_verificado_a_groq`) | `conversacion.py:578-587`; `traductor.py:281` | 🔴 |
| TRZ-021 | Límite: sin calificaciones oficiales ni finales (p.38) | La plataforma gestiona notas por materia y trimestre, promedios e historial, y el robot escribe en `grades` | P | P | P | Pest P (no ejecutado) | `DashboardController.php:72` (quarter_averages); migraciones `…add_quarter_to_grades…` | 🟠 |
| TRZ-022 | Límite: solo quechua (p.38) | Solo se siembra la materia "Quechua", pero se pueden crear otras; el robot conversa sobre todo en español | P | P, C | P | — | migración `2026_09_09_000001…:21-28`; `SubjectController` (CRUD) | 🟠 |
| TRZ-023 | Límite: padres sin permiso de modificación (p.38) | Control en código: 403 a familiares y a estudiantes en edición; escritura de familiares solo admin/academic | P | P | P | Pest P `FamilyAndStudentAuthTest` (no ejecutado) | `StudentController.php:495-513`; `routes/web.php:58-62,68-76` | 🟡 |
| TRZ-024 | Límite: sin procesos financieros ni de RR. HH. (p.38) | Ausencia verificada | — | — | — | grep | `grep -rniE "pago\|salari\|finanz\|payroll\|factura"` en P → nada | 🟢 |
| TRZ-025 | Límite: sin asistentes comerciales (p.38) | Literalmente no hay Alexa, Assistant ni Siri, pero depende de **servicios comerciales en la nube**: Google Gemini, Groq y Microsoft Edge TTS | — | C | — | pytest C (con dobles) | `gemini_transcriber.py:5-6,18`; `main_robot.py:19,107,218-235` | 🟠 |
| TRZ-026 | Límite: sin biometría (p.38) | Ausencia verificada | — | — | — | grep | grep `face\|biometr\|facial` en P y C → sin coincidencias relevantes | 🟢 |
| TRZ-027 | Límite: prototipo funcional (p.39) | Existe un prototipo de software; el físico no | C | C | C | pytest C | Ídem TRZ-001/008 | 🟠 |
| TRZ-028 | Límite: funcionar sin conectividad permanente (p.39) | Respaldos locales parciales: Whisper local, spd-say/espeak, traducción con la BD local. Conversación (Groq), transcripción principal (Gemini) y voz principal (Edge TTS) requieren internet. **No se probó sin red** | C | C | — | No (sin prueba sin conexión) | `main_robot.py:340-371,818-836`; `traductor.py:293-323` | 🟠 |
| TRZ-029 | Límite: no reemplaza la interacción social (p.39) | Pedagógico | — | — | — | — | — | ⚫ |
| TRZ-030 | RF-01: voz en quechua mediante botón/pantalla, e iniciar evaluación (p.42) | La captura es **continua por VAD propio**, sin botón ni pantalla. Los comandos son **palabras en español** | — | C | C (sin controles) | pytest C (umbral de audio) | `audio_manager.py:471-580`; `main_robot.py:937-1029`; sin `<button>` | 🟠 |
| TRZ-031 | RF-02: transcripción + **% de precisión fonética** (p.42) | Solo transcripción. La similitud `SequenceMatcher` de texto se imprime en consola en el juego; no se devuelve, no es fonética y no se guarda | — | C (solo texto) | — | No | `juego.py:163-174`; grep `phonetic\|porcentaje` en C → nada | 🔴 |
| TRZ-032 | RF-03: docente crea unidades temáticas, palabras clave y retos (p.42) | El docente elige 1 de **7 categorías fijas** y crea un "reto" pendiente por paralelo. No hay CRUD de unidades ni de palabras. Las palabras sembradas están en **español** ("Manzana", "Pan"…) y el robot no las usa | P: `robot_*`, `grades` | P | P: `robot/create.blade.php` | Pest P `test_web_robot_activity_creates_one_pending_record_per_student` (no ejecutado) | `GradeController.php:418-486`; `RobotCategorySeeder.php:13-17` | 🟠 |
| TRZ-033 | RF-04: app con gráficos y **notificaciones en tiempo real** (p.42) | No hay APK. No hay notificaciones en P (solo el trait `Notifiable`): sin `->notify()`, broadcast ni FCM. Los gráficos están solo en la web | — | — | P web (Chart.js) | No | grep `Notification::\|->notify(\|broadcast\|fcm` en P → nada; `dashboard.blade.php:372-379` | 🔴 |
| TRZ-034 | RF-05: cada intento en `phonetic_evaluations` con marca de tiempo (p.42) | La tabla **no existe** en C, en P ni en el diagrama de la tesis. C no guarda nada. P usa `grades.firstOrNew`, que **sobrescribe** los intentos de una misma actividad | — | — | — | No | grep `phonetic_evaluations` → solo en `docs/pruebas/identificacion-requisitos-verificables-yura.md:28`; `Api/RobotActivityController.php:22`; grep `INSERT\|commit(` en C → nada | 🔴 |
| TRZ-035 | RNF-01: latencia ≤ 2,5 s (p.42) | Sin medición. El diseño suma 1,0 s de silencio final + Gemini (red) + Groq (red) + Edge TTS (red) | — | C | — | No | `main_robot.py:775` (`silencio_final=1.0`); solo se cronometra Whisper (`main_robot.py:822,845`) | ⚫ |
| TRZ-036 | RNF-02: MySQL con integridad referencial y ACID (p.42) | FK `constrained()` en las migraciones. Las pruebas de P usan **SQLite :memory:**, no MySQL. El `.env.example` de P trae `DB_CONNECTION=sqlite` | P | P | — | No con MySQL | `phpunit.xml:26-27`; migraciones `…000006…:13-14,24-25`; `.env.example:23` de P | 🟡 |
| TRZ-037 | RNF-03: Android 8.0+ (p.42) | No hay APK | — | — | — | No | Búsqueda de *.apk/*.kt → nada | ⚫ |
| TRZ-038 | CU Admin: Consultar reportes (p.45) | Dashboard y exportaciones | P | P | P | Pest P (no ejecutado) | `routes/web.php:35,42-46` | 🟡 |
| TRZ-039 | CU Admin: Gestionar usuarios (p.45) | `users` resource con `rol:admin` | P | P | P | Pest P (no ejecutado) | `routes/web.php:118-123` | 🟡 |
| TRZ-040 | CU Admin: Gestionar actividades (p.45) | El admin **no tiene acceso** a actividades robot (solo `rol:profesor`). La tabla `activities` no tiene CRUD | P | P parcial | P parcial | No | `routes/web.php:68-76`; grep `Activity::` en app/Http → nada | 🟠 |
| TRZ-041 | CU Admin: Gestionar cursos (p.45) | `courses` resource | P | P | P | Pest P (no ejecutado) | `routes/web.php:94-95` | 🟡 |
| TRZ-042 | CU Admin: Gestionar estudiantes (p.45) | `students` resource con restaurar y borrado definitivo | P | P | P | Pest P (no ejecutado) | `routes/web.php:47-50` | 🟡 |
| TRZ-043 | CU Admin: Gestionar padres (p.45) | Tutores y familiares | P | P | P | Pest P (no ejecutado) | `routes/web.php:53-62,86-92` | 🟡 |
| TRZ-044 | CU Admin: Gestionar docentes (p.45) | `teachers.*` | P | P | P | Pest P (no ejecutado) | `routes/web.php:99-103` | 🟡 |
| TRZ-045 | CU Docente: Consultar seguimiento (p.46) | `grades.index/show/history` | P | P | P | Pest P (no ejecutado) | `routes/web.php:64-84` | 🟡 |
| TRZ-046 | CU Docente: Generar reportes (p.46) | Exportación PDF/Excel de estudiantes | P | P | P | Pest P (no ejecutado) | `routes/web.php:42-46` | 🟡 |
| TRZ-047 | CU Docente: Consultar resultados (p.46) | Notas, incluidas las de robot si llegaran | P | P | P | Pest P (no ejecutado) | `GradeController.php:20-98` | 🟡 |
| TRZ-048 | CU Docente: Crear grupos (p.46) | No existe | P (tabla) | — | — | No | Ídem TRZ-007 | 🔴 |
| TRZ-049 | CU Docente: Asignar actividades (p.46) | Asigna 1 categoría fija a **todo** un paralelo | P | P | P | Pest P (no ejecutado) | `GradeController.php:442-486` | 🟠 |
| TRZ-050 | CU Docente: Modificar actividades (p.46) | Se modifican **notas** (`grades.update/batch`), no la definición de la actividad | P | P | P | Pest P (no ejecutado) | `routes/web.php:69-73` | 🟠 |
| TRZ-051 | CU Docente: Crear actividades (p.46) | Ídem RF-03 | P | P | P | Pest P (no ejecutado) | Ídem TRZ-032 | 🟠 |
| TRZ-052 | CU "Padre/Tutor" (actor: Estudiante): Consultar resultado (p.47) | Dashboard de tutor con notas y "Retos Robot"; `students.show` para el estudiante | P | P | P | Pest P (no ejecutado) | `dashboard.blade.php:33-143`; `TutorDashboardController.php:35-42` | 🟡 |
| TRZ-053 | CU: Participar en actividad grupal (p.47) | No existe | — | — | — | No | Ídem TRZ-007 | 🔴 |
| TRZ-054 | CU: Practicar pronunciación (p.47) | Modo práctica y juego por voz (evaluación textual) | C | C | C | pytest C (parcial) | `conversacion.py:190-340`; `juego.py` | 🟠 |
| TRZ-055 | CU: Realizar actividad (p.47) | Juego de 4 preguntas elegidas de 6 palabras fijas. Sin identificación del estudiante ni registro | — | C | C | No (sin pruebas de juego) | `juego.py:31-34,87-200` | 🟠 |
| TRZ-056 | Despliegue: ESP32 (C++) por Serial USB (p.48) | No existe: sin pyserial, sin firmware, sin /dev/ttyUSB* | — | — | — | No | `06_hardware_entorno.txt`; `main_robot.py:382-383` | 🔴 |
| TRZ-057 | Despliegue: frontend web HTML/PHP/CSS (p.48) | Blade + AdminLTE | — | P | P | Pest P (no ejecutado) | `resources/views/**` | 🟡 |
| TRZ-058 | Despliegue: app Android/Kotlin por REST (p.48) | La API existe; la app no aparece | P | P | — | No | Ídem TRZ-006 | ⚫ |
| TRZ-059 | Despliegue: cerebro Debian 13 + Faster-Whisper (p.48) | **Ubuntu 24.04.5** + Gemini (nube) + openai-whisper | C | C | — | pytest C | `06_hardware_entorno.txt`; `requirements.txt:4`; `pip list` sin faster-whisper ni ctranslate2 | 🔴 |
| TRZ-060 | Despliegue: cerebro ↔ servidor por WiFi/REST (p.48) | El lado servidor existe; el lado cerebro **no existe** | P | P / C no | — | No | grep `requests\.\|urllib\|httpx\|/v1/robot` en C → nada | 🔴 |
| TRZ-061 | Despliegue: servidor Laravel/PHP (p.48) | Laravel 12 | P | P | P | Pest P (no ejecutado) | `composer.json`; `tests/QA/analisis-qa-yura.md` | 🟡 |
| TRZ-062 | Despliegue: BD local SQLite (p.48) | `diccionario.db`: 15 tablas `nivelN_*`, 188 filas, leída por `traductor.py` | C | C | — | pytest C (vocabulario) | Consulta en solo lectura (§ evidencias) | 🟢 |
| TRZ-063 | Despliegue: BD web MySQL (p.48) | La guía indica MySQL/XAMPP; aquí no hay MySQL | P | P | — | No | `README_EQUIPO.md` (DB_CONNECTION=mysql) | 🟡 |
| TRZ-064 | Recurso: i3 / SSD 128 / 8 GB / Debian 13 (p.40) | Real: **i3-10100 (10.ª gen), 16 GB RAM, NVMe 256 GB + HDD 1 TB, GTX 1650, Ubuntu 24.04**. El presupuesto dice "i3 3ra Gen" | — | — | — | Comando | `06_hardware_entorno.txt` | 🟠 |
| TRZ-065 | Recurso: DevKit v1 (ESP32), motores, servos, sensores (p.40) | No existe | — | — | — | Comando | `lsusb` (solo ratón, teclado, BT, audio) | 🔴 |
| TRZ-066 | Recurso: micrófono con supresión de ruido, altavoces, LCD 7" táctil (p.40) | Audífonos USB C-Media y TV HDMI (800×450 mm); sin táctil | — | — | — | Comando | `lsusb` 0d8c:0012; `xrandr`; `grep -ci touch` = 0 | 🟠 |
| TRZ-067 | Recurso: Apache, PHP 8.2, MySQL 8.0, Android Studio, VS Code (p.40) | Aquí solo está VS Code. La guía de P usa XAMPP en otra PC (Windows) | — | — | — | Comando | `which apache2 php mysql` → nada; `/snap/bin/code` | ⚫ |
| TRZ-068 | Presupuesto 1675 Bs (p.41) | Sin comprobantes. Varios ítems (ESP32, pantalla 7", batería LiFePO4) no aparecen en el hardware real | — | — | — | — | Tabla pdf 51 con "Fuente:" vacía | ⚫ |
| TRZ-069 | 7.1 "Se completó la construcción e integración física" (p.41) | Contradicho por el hardware real | — | — | — | Comando | Ídem TRZ-008 | 🔴 |
| TRZ-070 | 7.1 API Laravel con MySQL en marcha (p.41) | Código presente; ejecución no verificada | P | P | — | Pest P (no ejecutado) | `routes/api.php` | 🟡 |
| TRZ-071 | 7.1 optimización de Faster-Whisper para Debian (p.41) | No existe en código, requisitos, venv ni disco | — | — | — | grep / pip | `06_busquedas…`; `pip list` | 🔴 |
| TRZ-072 | 7.1 prueba funcional de la APK (p.41) | No hay APK ni registro de prueba | — | — | — | No | Búsqueda en disco → nada | ⚫ |
| TRZ-073 | 7.2 consentimiento informado para métricas fonéticas (p.42) | No hay formularios (Anexo C/D vacíos) y **no se registra ninguna métrica fonética** | — | — | — | No | pdf 63; TRZ-034 | ⚫ |
| TRZ-074 | 7.5 Trello, Git/GitHub, pruebas sintéticas de audio (p.48) | Git sí: C con 1 commit, P en GitHub MENARWIL/yura-platform. Trello no verificable. **No hay audios de prueba** en los repositorios | — | — | — | — | `git log` C = 1 commit; `git ls-files` sin .wav/.mp3 | 🟠 |
| TRZ-075 | 7.6 filtro pasa-banda SciPy (p.49) | No existe. SciPy no está instalado ni en `requirements.txt`. El ruido se trata con un **umbral de energía adaptativo** propio | — | C (otra solución) | — | pytest C (umbral) | `import scipy` → ModuleNotFoundError; `audio_manager.py:20` | 🔴 |
| TRZ-076 | 7.6 umbral VAD de Faster-Whisper (p.49) | No existe. El VAD es propio | — | C (otra solución) | — | pytest C | `audio_manager.py:471-580` | 🔴 |
| TRZ-077 | 7.6 Faster-Whisper int8, 1,2 s por palabra (p.49) | No existe (openai-whisper `fp16=False`) y no hay medición | — | — | — | No | grep `int8\|compute_type` → nada; `main_robot.py:835` | 🔴 |
| TRZ-078 | 8.1 resultados cualitativos: puntajes y dinámicas grupales (p.49) | Sin evidencia. El robot **no tiene puntajes** y no hay dinámicas grupales | — | — | — | No | grep `puntaje\|score\|grupo` en C → nada | ⚫ |
| TRZ-079 | 8.2 87,4 % de fonemas (p.49) | Sin datos, sin corpus y sin ASR a nivel de fonema: Gemini y Whisper devuelven palabras, y Whisper está forzado a `language="es"` | — | — | — | No | `main_robot.py:825` | ⚫ |
| TRZ-080 | 8.2 de 2 a 9 interacciones por sesión (p.49) | Sin registros persistentes ni identificación de estudiante | — | — | — | No | TRZ-034 | ⚫ |
| TRZ-081 | 8.2 78,5 % (77) instalaron la APK (p.49) | Sin APK ni analítica | — | — | — | No | TRZ-006 | ⚫ |
| TRZ-082 | 8.3 impacto en la comunidad (p.49) | Sin evidencia | — | — | — | — | — | ⚫ |
| TRZ-083 | C1: integración de ASR+IA, Laravel y Android cumplida (p.50) | ASR+IA y Laravel existen **por separado y sin conexión**. Android sin evidencia | C, P | C, P | C, P | Parcial | TRZ-060 | 🟠 |
| TRZ-084 | C2: Faster-Whisper preciso y en tiempo real (p.50) | No se usa Faster-Whisper | — | — | — | No | TRZ-071 | 🔴 |
| TRZ-085 | C3: MySQL guarda métricas fonéticas y las sincroniza con apoderados (p.50) | No hay tabla ni flujo de métricas fonéticas | — | — | — | No | TRZ-034, TRZ-060 | 🔴 |
| TRZ-086 | C4: la validación confirmó el impacto (p.50) | Sin evidencia | — | — | — | — | — | ⚫ |
| TRZ-087 | 4.2 alertas a padres (p.35) | No existen notificaciones ni alertas | — | — | — | No | Ídem TRZ-033 | 🔴 |
| TRZ-088 | 3.3 el contenido del robot se administra desde la web (p.34) | El robot lee solo `diccionario.db` local. Las tablas `robot_*` de P (palabras en español) no se sincronizan | C y P separadas | — | — | No | `traductor.py` (tablas `nivelN_*`); `RobotCategorySeeder.php:13-17` | 🔴 |
| TRZ-089 | 1.1.4 encuesta a 98 estudiantes (p.3-10) | Hay gráficos en la tesis, pero no el instrumento ni los datos crudos (Anexo D vacío) | — | — | — | — | pdf 14-20, 63 | ⚫ |
| TRZ-090 | Diagnóstico: el robot habla, pregunta, felicita, **se desplaza** y tiene **luces** (p.10) | Habla, pregunta y felicita: sí. Desplazamiento y luces: no | — | C | C (animaciones de estado) | pytest C (parcial) | `juego.py:130,185-188`; `main_robot.py:382-383` | 🟠 |
| TRZ-091 | 6.1 fase 5: entrenamiento y calibración de Faster-Whisper (p.39) | No hay datos, scripts ni modelos de entrenamiento | — | — | — | No | Búsqueda en disco | 🔴 |
| TRZ-092 | UML: clase `Pronunciacion` (precision, retroalimentacion) y `Grupo` (puntaje) (p.43) | Sin equivalente en C ni en P (en P, `groups` no tiene puntaje) | — | — | — | No | migración `…000005…:11-15` | 🔴 |
| TRZ-093 | Modelo de BD de la tesis (p.44) | Las tablas del diagrama existen en migraciones (users, students, activities, activity_sessions, groups, group_student, interactions, results, classes, class_student, courses, parallels, student_family_members). **Faltan en el diagrama** las tablas que realmente se usan: `grades`, `subjects`, `teaching_assignments`, `attendance`, `grade_history`, `robot_*`. Además, `interactions` y `results` **no se usan** en ningún controlador | P | P parcial | — | No | `06_plataforma_extractos.txt` (último bloque) | 🟠 |
| TRZ-094 | 7.4.4 "Esquema completo de base de datos" (p.48) | **Sección vacía** en el documento | — | — | — | — | pdf 58 | 🔴 |
| TRZ-095 | Anexos A-F (p.53) | **Solo títulos, sin contenido** (es la última página del PDF) | — | — | — | — | pdf 63 | 🔴 |

---

## 4. Contradicciones documento ↔ realidad (verificadas)

| # | El documento dice | La realidad verificada | Evidencia | Gravedad |
|---|---|---|---|---|
| C-01 | El ASR es **Faster-Whisper**, optimizado, cuantizado int8 y "calibrado para niños" (p.24, 39, 40, 41, 48, 49, 50) | Transcripción principal con **Google Gemini `gemini-3.8-flash` en la nube**. Respaldo con **openai-whisper "base"** en GPU, `language="es"`, `fp16=False`. Ni faster-whisper ni ctranslate2 están instalados | `gemini_transcriber.py:18,57-73`; `main_robot.py:17,417-419,818-836`; `requirements.txt`; `pip list` | CRÍTICO |
| C-02 | "No implementará conversaciones libres mediante IA" (p.38) | Modo CONVERSAR con Groq `openai/gpt-oss-120b` y prompt "Conversa naturalmente…". Hay una prueba automatizada que lo confirma | `conversacion.py:578-587`; `traductor.py:281`; `tests/test_vocabulario_groq.py:42` | CRÍTICO |
| C-03 | "No se integrará con… asistentes virtuales comerciales" (p.38) | No usa Alexa, Assistant ni Siri, pero **depende de 3 servicios comerciales en la nube** (Google Gemini, Groq, Microsoft Edge TTS) que el documento no declara en ninguna parte | `gemini_transcriber.py:5-6`; `main_robot.py:19,107,218-235` | ALTO (declaración omitida; también implica privacidad: el audio de menores se envía a Google) |
| C-04 | "No garantizará conectividad… pudiendo operar las funcionalidades principales" (p.39) | Sin internet: la transcripción cae a Whisper local, la voz a spd-say/espeak (si están instalados), la traducción funciona con la BD local, y **conversar deja de funcionar**. No hay prueba sin red | `main_robot.py:340-371`; `traductor.py:293-323` | MEDIO (⚫ hasta probarlo sin red) |
| C-05 | RF-01: captura "mediante **botón/pantalla**"; comandos "**en quechua**" (p.42) | Captura continua por detección de voz propia; la pantalla no tiene ningún control; los comandos del menú son palabras en **español** | `audio_manager.py:471-580`; `web/templates/index.html`, `web/static/js/app.js` sin `<button>`/`onclick`; `main_robot.py:937-1029` | ALTO |
| C-06 | RF-02: "porcentaje de precisión fonética" (p.42) | No existe. El juego calcula `SequenceMatcher` sobre **texto transcrito** (una similitud de cadenas, no fonética), con umbral 0,75 y reemplazos q→k, v→b, h→"", ll→y. El valor solo se imprime en consola | `juego.py:36-85,163-174` | CRÍTICO |
| C-07 | RF-05: tabla `phonetic_evaluations` (p.42) | No existe en el cerebro, en la plataforma **ni en el diagrama de BD de la propia tesis** (pdf 54). Solo aparece copiada como requisito en `docs/pruebas/identificacion-requisitos-verificables-yura.md:28` | grep en ambos repos | CRÍTICO |
| C-08 | RNF-01: latencia ≤ 2,5 s; "1,2 s por palabra" (p.42, 49) | No hay ninguna medición. La arquitectura real encadena 1,0 s de silencio de cierre + ida y vuelta a Gemini + Groq + Edge TTS + ffmpeg. Solo se cronometra Whisper (`print`) | `main_robot.py:775,822,845` | ALTO (⚫) |
| C-09 | RNF-02: MySQL con integridad referencial (p.42) | Las migraciones declaran FK, pero las pruebas usan SQLite en memoria y el `.env.example` de la plataforma trae `sqlite`. La BD del robot (SQLite) no tiene relaciones y **no está vinculada** a MySQL | `phpunit.xml:26-27`; `.env.example:23` (P) | MEDIO |
| C-10 | ESP32, motores reductores, servos, sensores de proximidad y sonido, LCD 7" táctil, batería LiFePO4 (p.24, 40, 41, 48) | Ninguno está presente. Solo hay audífonos USB y TV HDMI. `mover_actuador` imprime "[FISICO]: Motores ejecutando -> …" | `06_hardware_entorno.txt`; `main_robot.py:382-383` | CRÍTICO |
| C-11 | SO Debian 13; "i3 3ra Gen + 8 GB + SSD 128 GB" (p.24, 40, 41, 48) | Ubuntu 24.04.5; i3-10100 (10.ª gen), 16 GB, NVMe 256 GB + HDD 1 TB, GPU GTX 1650 (Whisper usa la GPU) | `06_hardware_entorno.txt` | MEDIO |
| C-12 | 1.4.13 describe una SBC ARM (BCM2837B0, Cortex-A53 a 1,4 GHz, es decir, una Raspberry Pi 3B+) como unidad principal (p.26) | Contradice la propia tesis (mini PC i3 x86) y la realidad | pdf 36 vs pdf 50 | BAJO (incoherencia interna) |
| C-13 | App móvil Android/Kotlin, APK instalada por 77 apoderados (p.28, 40, 41, 49, 50) | No hay código, APK ni referencia a un repositorio de la app en ninguno de los repos. El propio QA de la plataforma lo reconoce: "No se encontró en este repositorio el código fuente de la APK ni del software interno del robot físico" | `tests/QA/analisis-qa-yura.md:17`; búsqueda en disco | CRÍTICO (⚫) |
| C-14 | RF-04 y 4.2: notificaciones y alertas en tiempo real a apoderados (p.35, 42) | La plataforma no tiene notificaciones (solo el trait `Notifiable` por defecto; sin `notify()`, broadcast, colas ni FCM) | grep en P | ALTO |
| C-15 | 5.3.4, 7.4.3 y C3: el desempeño con YURA se registra y "sincroniza con apoderados" (p.37, 48, 50) | El endpoint del robot existe en la plataforma, pero el cerebro **no lo llama**: no tiene cliente HTTP, URL, token ni identificador de estudiante. Además, el endpoint hace `firstOrNew` por (estudiante, materia, actividad) y **sobrescribe** el intento anterior, así que no registra "cada intento" | `routes/api.php:31`; `Api/RobotActivityController.php:22-42`; `.env.example` (C) | CRÍTICO |
| C-16 | 3.3 y RF-03: el docente administra contenido (unidades, palabras clave) (p.34, 42) | La plataforma tiene 7 categorías fijas con palabras **en español** ("Manzana", "Pan", "Madre"…) y **no hay CRUD** de palabras. El robot usa otra BD (`diccionario.db`, 15 tablas en quechua) y un juego con 6 palabras escritas en el código (`"arbol"` ni siquiera está en la BD) | `RobotCategorySeeder.php:13-17`; `main_robot.py:465-475`; `06_palabras_juego_en_bd.txt` | ALTO |
| C-17 | 5.3.6, 8.1 y casos de uso: dinámicas grupales, equipos y puntajes (p.37, 46, 47, 49) | Tablas `groups`/`group_student` sin ningún controlador, ruta ni vista. El cerebro no tiene puntajes ni grupos | grep en P y C | CRÍTICO (8.1 afirma resultados de una función inexistente) |
| C-18 | 7.6: filtro pasa-banda con **SciPy** y umbral VAD de Faster-Whisper (p.49) | SciPy no está instalado. La solución real es un umbral de energía adaptativo propio (`_calcular_umbral_ruido`), que sí está probado (`tests/test_audio_threshold.py`) | `audio_manager.py:20,471-580` | ALTO |
| C-19 | 5.4: "no asignará calificaciones finales" (p.38) | La plataforma calcula promedios por trimestre y lleva notas por materia con historial ("cuaderno pedagógico") | `DashboardController.php:72`; migraciones de `grades` | MEDIO |
| C-20 | 8.2: 87,4 % de **fonemas** (p.49) | Ningún componente trabaja con fonemas. Whisper transcribe forzado a **español** (`language="es"`), lo que empeora el quechua | `main_robot.py:825` | CRÍTICO (⚫) |
| C-21 | Caso de uso "Padre de Familia / Tutor" (p.47) | El actor dibujado es **"Estudiante"**. No hay diagrama de casos de uso del padre | pdf 57 | MEDIO (error documental) |
| C-22 | 7.4.4 "Esquema completo de base de datos" y Anexos A-F (p.48, 53) | Sección vacía y anexos solo con títulos. El PDF termina en la página 63 | pdf 58, 63 | ALTO (la defensa no tiene respaldo anexado) |
| C-23 | Documento fechado 17/08/2026 con todo "completado" (p.41) | En la plataforma, las migraciones clave de la integración con el robot tienen fecha posterior: `2026_09_09_*` (materias, asignaciones docentes) y `2026_09_15_000001_add_robot_activity_id_to_grades_table`. El commit es del 2026-09-15 ("fix: remediar riesgos QA de API y actividades robot"). El cerebro tiene cambios de hoy, 2026-09-27, sin commit | nombres de migración; `git log` de P | ALTO (indica que la integración se hizo después de declararla completada; la marca de tiempo del nombre de migración es un indicio, no una prueba) |

---

## 5. Afirmaciones sin evidencia (riesgo para la defensa)

Todas se clasifican **⚫ NO VERIFICADO**. No afirmo que sean falsas; afirmo que **no existe evidencia en los repositorios ni en esta computadora**. Para cada una indico qué falta y dónde tendría que estar.

| # | Afirmación (pág.) | Evidencia que falta | Dónde se esperaría | Pregunta probable del tribunal |
|---|---|---|---|---|
| R-01 | 87,4 % de reconocimiento de fonemas (p.49) | Corpus de audios de niños con transcripción de referencia, script de evaluación (PER/WER), hoja de resultados y versión del modelo | Repo del cerebro (`eval/`, `datos/`) o Anexo F | "¿Cómo midieron fonemas si el sistema devuelve palabras y Whisper está forzado a español?" |
| R-02 | De 2 a 9 interacciones por estudiante y sesión (p.49) | Línea base (observación previa), registros por sesión con identificación del estudiante y cantidad de sesiones | BD (`interactions`/`grades` con datos reales), exportación CSV, Anexo D/F | "¿De dónde sale el conteo si el robot no guarda ni identifica a nadie?" |
| R-03 | 78,5 % (77) instalaron la APK y revisaron los reportes (p.49) | APK, código fuente, registro de instalaciones o de inicios de sesión (`personal_access_tokens`) | Repo de la app, BD de producción de la plataforma | "Muéstrenos la APK instalada y el registro de accesos." |
| R-04 | Construcción e integración física completada (p.41) | Fotografías, firmware del ESP32, esquema eléctrico, prototipo presente | Anexo B (vacío), repo del firmware | "¿Dónde está el ESP32? El código solo imprime 'Motores ejecutando'." |
| R-05 | Faster-Whisper int8 a 1,2 s por palabra (p.49) | Código con `faster_whisper`, `compute_type="int8"` y mediciones de tiempo | Cerebro (`requirements.txt`, módulo ASR) | "Abra `requirements.txt`: ¿dónde está Faster-Whisper?" |
| R-06 | Filtro SciPy pasa-banda (p.49) | Código con `scipy.signal` | `audio_manager.py` | Ídem |
| R-07 | Latencia ≤ 2,5 s (RNF-01, p.42) | Mediciones reproducibles de extremo a extremo (fin del habla → inicio del audio de respuesta), con percentiles | Informe de pruebas y logs | "¿Cuánto tarda con Gemini + Groq + Edge TTS en la red del colegio?" |
| R-08 | Pruebas piloto en aula y resultados cualitativos (p.39, 49) | Actas, lista de sesiones, fotos, instrumentos de observación | Anexos B, C, D (vacíos) | "¿Cuántas sesiones, con qué paralelos y en qué fechas?" |
| R-09 | Consentimiento informado de apoderados (p.42) | Formularios firmados (anonimizados) | Anexo C/F | Ético-legal: datos de voz de menores enviados a Google (Gemini) |
| R-10 | Encuesta a 98 estudiantes (p.3-10) | Instrumento y datos crudos | Anexo D (vacío) | "Muéstrenos el cuestionario." |
| R-11 | "Pruebas sintéticas de audio para validar la precisión ASR" (p.48) | Audios y script de prueba | Repo del cerebro (no hay .wav ni .mp3 versionados) | — |
| R-12 | Prueba funcional de la APK y RNF-03 Android 8.0+ (p.41-42) | APK y registro de pruebas en dispositivos | Repo de la app | — |
| R-13 | "Revitalizó el interés de las familias en el Distrito 9" (p.49) | Cualquier instrumento de medición | Anexos | — |
| R-14 | Uso de Trello y "entrenamiento y calibración" del ASR (p.39, 48) | Tablero exportado; datos y scripts de entrenamiento | Anexo F; repo | — |
| R-15 | Presupuesto de 1675 Bs (p.41) | Facturas o cotizaciones. La tabla tiene "Fuente:" vacía y varios ítems no existen físicamente | Anexo F | — |

**Nota de tutor:** R-01, R-02, R-03 y R-04 son **las de mayor riesgo**. Se presentan como hechos medidos, con cifras exactas, pero el software entregado **no tiene capacidad técnica para producir esos datos**: no identifica al estudiante, no persiste intentos, no hace análisis fonético y no existe la app. Si no hay un respaldo externo (hojas de observación, otra versión del software), un tribunal puede interpretarlas como datos no sustentados.

---

## 6. ¿Qué falta? (priorizado)

Hay dos caminos: **(A) construir lo que el documento promete** o **(B) ajustar el documento a lo construido**. Con la fecha de defensa cerca, recomiendo **B para todo lo físico y lo cuantitativo, y A solo para la integración mínima**.

### CRÍTICO
1. **Decidir y alinear el ASR** (C-01, TRZ-059/071/077/084). A: implementar Faster-Whisper int8 local y medirlo. B: reescribir 1.4.7, 6.1, 6.2, 7.1, 7.6, 7.4.3 y la conclusión 2 para decir "Gemini (nube) con respaldo openai-whisper local".
2. **Resolver el límite "sin conversación libre"** (C-02). A: desactivar el modo CONVERSAR o restringirlo a guiones. B: eliminar ese límite y describir la conversación acotada con vocabulario verificado y filtro de temas (`conversacion.py:489-497`), declarando Groq.
3. **Registro de intentos + identificación del estudiante + envío a la plataforma** (C-07, C-15, TRZ-013/034/060). Esto es mínimo para que 5.3.4, RF-05 y la conclusión 3 tengan sentido: un campo de "estudiante activo" (por ejemplo, el docente lo selecciona en la web), una tabla local de intentos con marca de tiempo y un cliente HTTP con token Sanctum hacia `POST /api/v1/robot/activity`, que además no debe sobrescribir intentos. Si no se construye, hay que retirar RF-05 y la conclusión 3.
4. **Retirar o respaldar las cifras de 8.2** (R-01..R-03). Sin datos crudos anexados deben eliminarse, o presentarse como metas o como resultados esperados, no como obtenidos.
5. **Hardware** (C-10, TRZ-008/016/056/065/069). B: declarar el prototipo real (PC + audífonos USB + TV HDMI) y pasar ESP32, motores y pantalla táctil a "trabajo futuro". A: solo si el hardware existe físicamente. En ese caso faltan el firmware, el protocolo serie y `pyserial` en el cerebro.
6. **App Android** (C-13). Entregar el código o la APK al tribunal, o reescribir 5.3.5, RF-04, RNF-03 y 8.2 indicando que el seguimiento de los padres se hace con el **panel web de tutor** (`dashboard.blade.php:33-143`), que sí existe.

### ALTO
7. **Precisión fonética (RF-02)**: renombrarla a "similitud de la respuesta transcrita (0-1, umbral 0,75)" y guardarla. Hoy solo se imprime (`juego.py:169-174`).
8. **RF-01**: reescribir como "activación por voz continua (VAD), comandos en español", o añadir un control en pantalla.
9. **RF-03 y contenido docente**: unificar el vocabulario. La plataforma (palabras en español, 7 categorías) y el robot (`diccionario.db`, 15 categorías en quechua) no comparten nada. El juego debería tomar las palabras de la BD en vez de las 6 escritas en el código.
10. **Actividades grupales** (5.3.6, OE6, casos de uso, 8.1): implementar un mínimo (grupos y puntaje por grupo) o retirarlas del documento, incluido el resultado cualitativo que las menciona.
11. **Notificaciones** (RF-04, 4.2): retirar "en tiempo real" y "alertas", o implementarlas.
12. **Medir la latencia (RNF-01)** con un protocolo reproducible, o cambiar la cifra por el valor medido.
13. **Declarar los servicios en la nube y la privacidad** (C-03): el audio de menores se envía a Google Gemini y el texto a Groq. El consentimiento (7.2) debe cubrirlo.
14. **Completar 7.4.4 y los Anexos A-F** con material real: fotos del prototipo real, actas, instrumentos y capturas.

### MEDIO
15. Corregir los datos de hardware y SO (C-11, C-12): Ubuntu 24.04, i3-10100, 16 GB, GTX 1650; quitar o contextualizar la SBC ARM.
16. Actualizar el diagrama de BD (C-09, TRZ-093) para incluir `grades`, `subjects`, `teaching_assignments`, `attendance`, `grade_history` y `robot_*`, y marcar como no usadas `interactions`, `results`, `groups` y `activities`, o darles uso.
17. Corregir el diagrama de casos de uso del padre (C-21).
18. Aclarar el límite "no asigna calificaciones finales" frente al módulo de notas por trimestre (C-19).
19. Permitir al administrador gestionar actividades (el caso de uso lo exige; hoy solo puede el profesor, `routes/web.php:68-76`).
20. Probar el funcionamiento sin internet (C-04) y documentar qué funciones sobreviven.
21. Ejecutar las pruebas de la plataforma contra **MySQL** (no SQLite) para respaldar RNF-02.

### BAJO
22. Unificar el título (portada, índice y nombre de archivo tienen títulos distintos) y completar la "Fuente:" de las tablas.
23. Versionar el cerebro con commits significativos (hoy hay 1 commit), para respaldar la afirmación de 7.5 sobre Git/GitHub.

---

## 7. Recomendaciones sobre el documento

1. **Reescribir 7.1, 7.6, 8 y 9 con verbos que describan solo lo que se puede demostrar en vivo.** Todo lo que no se pueda mostrar en la defensa (robot móvil, APK, 87,4 %, 77 apoderados, 2→9) debe pasar a "limitaciones" o "trabajo futuro".
2. **Hacer una sección "Arquitectura implementada" separada de la "propuesta".** El marco teórico puede describir ESP32 y Faster-Whisper como alternativas estudiadas, pero 7.3-7.4 deben describir el sistema real: Flask + Gemini/Whisper + Groq + Edge TTS + SQLite local por un lado, y Laravel + MySQL por otro, con su estado de integración declarado honestamente.
3. **Reformular los RF para que sean verificables y coherentes con el código:**
   - RF-01 "captura por voz continua con detección de actividad"
   - RF-02 "transcripción y evaluación por similitud textual con umbral 0,75"
   - RF-05 "registro de intentos en la tabla X" (una que exista: `grades` o una nueva)
   - RNF-01 con el valor medido.
4. **Revisar la sección 5.4 de límites.** Hoy dos límites (conversación libre y asistentes comerciales) contradicen el sistema entregado, y un tercero (calificaciones finales) contradice la plataforma.
5. **Declarar la dependencia de servicios en la nube y su implicancia para los datos de menores** (consentimiento, anonimización), en coherencia con 7.2.
6. **Incluir los anexos reales**: fotos del montaje actual, capturas de la pantalla de estado y de la plataforma, salida de `pytest` (28/28) y de las pruebas Pest, el cuestionario de la encuesta y las actas.
7. **Corregir errores documentales puntuales**: actor "Estudiante" en el caso de uso del padre, sección 7.4.4 vacía, SBC ARM frente a i3, "i3 3ra Gen" frente a i3-10100, Debian 13 frente a Ubuntu 24.04.

---
*Fin del informe 06. Solo lectura: no se modificó ningún archivo del proyecto; solo se escribieron este informe y las evidencias `06_*` en `documentacion_pruebas/`.*
