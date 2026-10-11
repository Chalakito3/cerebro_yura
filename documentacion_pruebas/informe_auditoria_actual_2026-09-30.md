**Informe de evaluación de YURA — 30 de septiembre de 2026**

**Dictamen: 7/10 como prototipo académico de asistente educativo.** Existe una implementación sustancial: interacción por voz, actividades, diccionario, enseñanza de pronunciaciones, pantalla web y seguimiento de intentos. La base permite continuar el proyecto. Todavía faltan evidencias para considerarlo un evaluador fiable de pronunciación infantil o una aplicación lista para un despliegue escolar generalizado.

La nota es un juicio técnico orientativo sobre esta revisión, no una certificación, una calificación del tribunal ni una medición del aprendizaje de los estudiantes.

**Alcance y método**

Se revisaron los módulos principales de Python, las rutas Flask, partes de las plantillas y JavaScript, pruebas automatizadas, scripts de arranque, configuración de ejemplo, reconstrucción del diccionario y documentación previa. También se inspeccionaron los procedimientos de adaptación de voz y medición. No se auditó exhaustivamente cada archivo de terceros, cada audio ni cada fuente lingüística.

Se creó una copia temporal de los módulos, pruebas, recursos web, scripts de base de datos y una copia consistente del diccionario mediante SQLite Backup. Las pruebas se ejecutaron allí con el intérprete del entorno virtual existente, sin copiar `.env.local`. Las reproducciones HTTP usaron el cliente de pruebas de Flask y datos inventados. No se inició el robot ni se hizo una prueba con el micrófono, altavoces, motores o servicios de IA reales. No se modificó el código funcional ni se instalaron herramientas.

No se abrió el archivo de claves ni se inspeccionaron nombres o respuestas reales de estudiantes. Los conteos son agregados. La evaluación corresponde al contenido actual de la carpeta, que contiene modificaciones y archivos todavía no registrados en Git; no corresponde exclusivamente al último commit.

**Evidencias actuales**

| Comprobación | Resultado | Interpretación |
|---|---|---|
| Suite `pytest tests -q --tb=short` en copia temporal | **235 aprobadas, 1 omitida; 9,31 s** | Buena protección de los escenarios cubiertos; no demuestra ausencia de defectos |
| Prueba omitida | Correcciones sobre un respaldo histórico no copiado | Omisión por condición del entorno aislado; no equivale a fallo |
| `PRAGMA integrity_check` del diccionario original, en lectura | `ok` | Integridad estructural; no certifica traducciones |
| Tablas de vocabulario | **19 tablas, 292 filas** | Son registros, no necesariamente 292 palabras distintas |
| Grabaciones docentes registradas | **115** | Conteo de filas; no comprobación individual de cada archivo de audio |
| Variantes aprendidas | **345** | No son 345 hablantes independientes |
| Entradas de pronunciación de salida | **288** | No implican 288 pronunciaciones validadas por una persona |
| Mapa Vosk | **278 claves** | No permite afirmar por sí solo una cobertura o precisión del 100 % |
| Dependencias instaladas | `pip check` sin incompatibilidades declaradas | No es un análisis de vulnerabilidades ni una instalación limpia |
| Versiones de `requirements.txt` | Coinciden con las instaladas | Es una fortaleza, aunque el listado está incompleto |
| Vosk | Instalado, versión 0.3.45; ausente del listado | Riesgo de instalación en otro equipo |

La salida de pytest quedó en `/tmp/yura-auditoria-8s0wpw7t/pytest.txt`. Es un artefacto temporal y puede desaparecer al limpiar `/tmp`.

**Desglose de la calificación**

| Área | Peso | Nota / 10 | Fundamentación |
|---|---:|---:|---|
| Funcionalidad implementada | 20 % | 8,5 | Flujos educativos, voz, resultados y modo docente conectados |
| Arquitectura y mantenimiento | 15 % | 6,5 | Separación parcial, con concentración excesiva en el orquestador |
| Pruebas y control de calidad | 15 % | 7,5 | Suite amplia y aprobada, pero faltan pruebas importantes de integración y navegador |
| Evidencia lingüística y pedagógica | 20 % | 6 | Adaptación útil, sin validación independiente suficiente para generalizar |
| Seguridad y privacidad | 10 % | 6 | Controles existentes, con exposición de participante reproducida |
| Instalación y operación | 10 % | 6 | Servicio y caché útiles; dependencias y recuperación incompletas |
| Documentación y trazabilidad | 10 % | 7 | Mucha evidencia, con afirmaciones y cifras que necesitan reconciliación |

Resultado ponderado: **6,9/10**, redondeado a **7/10**. La prioridad no es añadir más funciones: es consolidar lo construido y demostrar con precisión qué logra.

**Qué está bien construido**

1. **El problema educativo es concreto.** La práctica de vocabulario quechua, el acompañamiento por voz y la intervención de la docente forman un propósito coherente.
2. **El sistema tiene varios flujos implementados.** `BrainYura` coordina menú, juego, conversación, traducción, silencio, enseñanza y salida. El juego obtiene vocabulario de la base y registra intentos.
3. **La docente puede corregir el sistema.** Las grabaciones y variantes aceptadas permiten adaptar errores sistemáticos del reconocedor. Es una solución práctica para un contexto lingüístico que los modelos generales no cubren necesariamente bien.
4. **Hay defensas frente a errores reales.** Se limita la espera de varios subprocesos, Gemini se pausa tras fallos, se filtran algunas transcripciones espurias y el juego termina después de silencios repetidos.
5. **Se protege parte de la información.** Los resultados y el modo docente exigen clave fuera del equipo local; hay comprobación de origen en POST, comparación segura de contraseña y cabeceras contra inserción en marcos y detección incorrecta de contenido.
6. **El código evita algunas clases habituales de problemas.** Se usan parámetros SQL para valores en operaciones revisadas y `textContent` para contenido dinámico en la interfaz. Esto no demuestra que toda la aplicación esté libre de inyecciones, pero son decisiones correctas.
7. **Existen pruebas y evidencia de evolución.** La normalización, las ambigüedades, la pronunciación, el audio, los resultados y el modo docente tienen cobertura por escenarios. Las fixtures separan bases temporales de datos personales.
8. **La persistencia es razonable para una estación.** SQLite es adecuado para esta escala. Separar resultados y diccionario ayuda a mantener responsabilidades claras; no hay evidencia que justifique migrar ahora a una infraestructura más compleja.

**Hallazgos prioritarios y soluciones**

**1. Privacidad: el estado público revela al participante — prioridad alta, confirmado.**

`web/app.py:88` incorpora `participante_actual()` a `/api/status`. La protección de `web/app.py:234` se aplica a resultados y enseñanza, pero no a esta ruta. El servidor se configura para escuchar en `0.0.0.0` (`web/app.py:517`).

Reproducción aislada: una petición con dirección remota `192.168.1.50`, sin autenticación, recibió HTTP 200 y `participante: Alumno Prueba`. La misma dirección recibió HTTP 403 en `/api/resultados`. La exposición existe por ruta, aunque la accesibilidad real desde la red depende del firewall y del despliegue.

**Solución:** separar el estado público del estado docente. El público debe omitir identidad y cualquier contenido sensible; el privado debe exigir autenticación. Si el monitor solo se usa en esta máquina, escuchar por defecto en localhost. **Aceptación:** pruebas de todos los endpoints desde origen local, remoto sin clave y remoto con clave; ningún dato identificable en respuestas públicas.

**2. Evaluación del habla: se califica principalmente una transcripción — prioridad alta, confirmado por diseño.**

`pronunciaciones.py:493` y `texto.py:211` comparan texto normalizado, variantes y formas simplificadas. Se igualan determinados sonidos y grafías para tolerar errores del reconocedor. El juego anuncia que la respuesta fue correcta a partir de ese resultado.

Esto ayuda a reconocer una palabra, pero no mide directamente articulación, acento ni calidad de cada fonema. Un reconocedor puede acertar una palabra mal pronunciada o equivocarse con una pronunciación correcta. La propia simplificación elimina distinciones que serían necesarias para algunas evaluaciones fonéticas.

**Solución:** describir el resultado como «respuesta reconocida/aceptada» y ofrecer repetición o revisión docente cuando haya duda. Para evaluar pronunciación, definir una rúbrica con especialistas y comparar decisiones humanas con las del sistema. **Aceptación:** medir falsos aciertos y falsos rechazos por separado con audios independientes; no llamar «precisión fonética» al porcentaje de respuestas aceptadas.

**3. Las métricas históricas no validan el comportamiento actual con niños — prioridad alta, confirmado en el método.**

La evidencia `17_medicion_aprendizaje.txt` registra 81 % global en situaciones derivadas de 115 grabaciones docentes y 97 % para la inteligibilidad de la salida según el reconocedor. Son mediciones históricas, no repetidas aquí.

En `basedatos/medir_aprendizaje.py:medir`, se excluye la combinación exacta de grabación y contexto, pero se pueden conservar otros contextos de la misma grabación. Hay correlación entre entrenamiento y evaluación; el procedimiento no equivale a reservar grabaciones y hablantes completos. La síntesis evaluada con el mismo reconocedor que guía su elección también puede favorecer sus preferencias.

**Solución:** reservar hablantes y sesiones completos que no participen en ajustes, incluir ruido y distancias del aula y hacer revisión docente independiente. Separar resultados de Whisper y Vosk: el sistema ahora selecciona Vosk automáticamente sin GPU, por lo que cifras antiguas de Whisper no se trasladan a ese motor. **Aceptación:** conjunto de evaluación versionado, particiones explícitas, denominadores, errores por palabra y límites del estudio. La mejora del aprendizaje escolar necesita además un diseño pedagógico antes/después; no se deduce del reconocimiento de voz.

**4. Instalación incompleta y arranque sin reconocedor útil — prioridad alta, confirmado por inspección.**

`main_robot.py:640` selecciona Vosk cuando no hay GPU NVIDIA. `vosk` no está declarado en `requirements.txt`; sí existe en este entorno. Si su importación o carga falla, se imprime una alerta y puede continuarse con `vosk_model` y `whisper_model` vacíos. Con Gemini desactivado, el flujo termina devolviendo texto vacío.

También se importa Whisper al cargar el módulo, incluso cuando se quiere usar Vosk. El perfil ligero sigue acoplado a dependencias pesadas.

**Solución:** declarar Vosk, documentar descarga y verificación del modelo, separar perfiles CPU/GPU e introducir una comprobación de disponibilidad antes de anunciar que Yura está lista. Permitir una alternativa explícita o detener el arranque con explicación accionable. **Aceptación:** instalación desde cero en otro entorno y pruebas reales del constructor para Vosk disponible, ausente y modelo inválido. `test_modo_asr_vosk_configurado` actualmente reproduce una selección dentro del test, sin ejecutar esa lógica del constructor.

**5. La respuesta de IA no tiene validación lingüística suficiente — prioridad alta para contenido educativo.**

`conversacion.py:626` y `traductor.py:408` incluyen restricciones en el prompt. `texto.py:349` filtra algunas oraciones en otros idiomas o relacionadas con compras, pero no verifica que una frase quechua sea correcta. En una comprobación local, el texto inventado `Zaralumpa qexori.` atravesó el filtro; no fue una llamada real a Groq.

El vocabulario inyectado ayuda, pero una instrucción no garantiza cumplimiento. Además, limitar una conversación flexiva a una lista pequeña de palabras puede entrar en tensión con pedir preguntas y sufijos naturales.

**Solución:** priorizar contenido docente aprobado para actividades evaluadas, distinguir conversación generada de material verificado y ofrecer una respuesta segura cuando no haya respaldo. Usar evaluación adversaria de salidas y revisión lingüística; una lista literal de palabras permitidas tampoco basta para validar la morfología quechua. **Aceptación:** casos fuera de vocabulario, instrucciones contradictorias y respuestas inapropiadas probados antes del uso escolar.

**6. Adaptación Vosk con riesgo de sustituciones ambiguas — prioridad media-alta.**

`pronunciaciones.py:567` reemplaza transcripciones españolas por palabras quechuas, incluso dentro de frases. Las pruebas aceptan, por ejemplo, `comer` como `Q'umir`. En conversación en castellano, la misma cadena puede ser una palabra legítima. La ambigüedad depende del contexto y merece pruebas negativas específicas.

`basedatos/afinar_vocabulario_completo_vosk.py` genera pares usando voz sintética; asigna `mapa_actual[res_vosk] = palabra`, por lo que una clave coincidente puede sobrescribir otra sin registrar el conflicto. No se reprodujo aquí una colisión histórica ni se volvió a generar el mapa.

**Solución:** conservar transcripción original, motor, contexto y candidatos; restringir sustituciones a actividades y vocabulario esperado. Registrar colisiones como ambigüedades y pedir repetición. **Aceptación:** corpus con castellano normal y respuestas quechuas, midiendo también conversiones indebidas.

**7. Exportación CSV sin neutralización de fórmulas — prioridad media, confirmado.**

`web/app.py:297` exporta campos directamente. Un intento ficticio con respuesta `=1+1` conservó ese contenido en el CSV. No se abrió una hoja de cálculo ni se ejecutó una fórmula; su interpretación depende del programa receptor. El campo de respuesta admite texto que no se neutraliza al exportar.

**Solución:** exportar como texto los campos controlables por entrada, aplicando una política adecuada al consumidor, o usar un formato con tipos de celda explícitos. Añadir casos con los prefijos relevantes. Referencia: [guía de pruebas OWASP sobre CSV](https://wstg.owasp.org/latest/4-Web_Application_Security_Testing/07-Injection/21-CSV_Injection/).

**8. Validación JSON insuficiente — prioridad media, confirmado.**

Una petición local a `/api/ensenar/voz` con JSON `[1]` devuelve 500. El código asume un objeto y llama a `.get()`. Se reprodujo sin robot y sin conexión externa.

**Solución:** comprobar tipo, campos, longitudes y valores antes de procesar. **Aceptación:** listas, números, cadenas, nulos y campos incorrectos deben producir errores 400/422 comprensibles, sin excepciones internas.

**9. Despliegue web y ciclo de vida acoplados — prioridad media.**

Se usa `app.run`, el servidor de desarrollo. La documentación de [Flask](https://flask.palletsprojects.com/en/stable/deploying/) recomienda un servidor de producción para desplegar la aplicación. La autenticación Basic remota se presenta sobre HTTP en las instrucciones actuales; ese despliegue no aporta cifrado al transporte.

Cambiar simplemente a varios procesos WSGI sería problemático: `robot` es global, el micrófono debe tener un único propietario y `start_robot()` se invoca desde el bloque principal. Importar `web.app:app` no inicializa por sí solo el robot. `os._exit()` acopla el apagado del cerebro y la web.

**Solución:** definir arranque y cierre explícitos con un solo propietario del audio. Para la estación actual, un proceso bien controlado es suficiente; si se separa la web, usar un canal de comunicación con el cerebro. Proteger con HTTPS el acceso remoto o restringirlo a localhost. **Aceptación:** probar arranque, cierre, caída del cerebro y reconexión sin duplicar el micrófono.

**10. Autonomía sin internet y latencia todavía requieren demostración — prioridad media.**

Hay diccionario local, reconocimiento local, caché y alternativas de voz, lo cual es positivo. Pero conversación generada depende de Groq, Gemini envía audio si se activa y Edge TTS necesita red para contenido que no esté en caché. En `hablar()` hay dos intentos de síntesis con hasta 20 segundos cada uno antes de otras alternativas.

Por tanto, no procede prometer funcionamiento totalmente independiente ni latencia menor a 2,5 segundos para toda interacción. Las esperas máximas no son tiempos medidos, pero sí muestran rutas que pueden exceder esa meta.

**Solución:** definir un modo offline explícito, precargar las frases docentes necesarias y limitar el presupuesto total de espera. Medir captura, transcripción, decisión y voz por separado, con p50/p95 y fallos de red. **Aceptación:** sesión completa con red desconectada, caché parcial y servicios caídos, documentando qué funciones siguen disponibles.

**11. Recuperación incompleta de la personalización — prioridad media-alta.**

`basedatos/crear_diccionario.py:exportar` excluye las líneas de tablas `pronunciaciones_`. Se comprobó que reconstruir solo la semilla no crea `pronunciaciones_voz`. La exclusión de audios privados de Git es adecuada, pero una restauración completa necesita respaldo privado adicional.

**Solución:** diferenciar semilla pública de copia de seguridad operacional. Respaldar consistentemente diccionario personalizado, resultados, audios y configuración necesaria, con acceso restringido. **Aceptación:** restaurar en una carpeta limpia y verificar palabras, voces personalizadas, relaciones con archivos y resultados. No confiar únicamente en que existan archivos con nombre «respaldo».

**12. Complejidad y estado compartido — prioridad media.**

`main_robot.py` tiene 1.601 líneas; `hablar()` ocupa 216 y `escuchar_voz()` 144. `AudioManager.grabar_hasta_silencio()` ocupa 190. El problema es la cantidad de responsabilidades y rutas alternativas que hay que comprender juntas.

El historial envía solo los últimos ocho mensajes, pero se conserva y amplía la lista completa en memoria (`conversacion.py:711`). Hay estado global de sesión educativa y actualizaciones de enseñanza desde el hilo web y el del robot; no se ejecutó una prueba de estrés de concurrencia.

**Solución:** extraer adaptadores ASR/TTS, evaluación de respuestas y configuración; limitar el historial almacenado; centralizar órdenes y cambios de estado. Mantener la máquina de estados actual y refactorizar por pasos con pruebas de comportamiento. No hay razón demostrada para rehacer todo ni crear microservicios ahora.

**13. Registros y flujo de datos personales — prioridad media.**

Aunque las transcripciones directas pasan por funciones de depuración, `main_robot.py:303` y `conversacion.py:714` imprimen respuestas completas normalmente. Si una respuesta repite datos del estudiante, estos pueden terminar en el diario del servicio. No se verificaron registros reales.

**Solución:** usar eventos técnicos y tiempos sin texto personal por defecto, definir retención de resultados y audios y documentar qué contenido sale a cada proveedor. Usar códigos de participante cuando sea suficiente. Esta recomendación se refiere al diseño y operación; este informe no es una evaluación de cumplimiento jurídico.

**14. Interfaz y pruebas de usuario — prioridad media-baja.**

La interfaz incluye estados, contenido educativo, etiquetas de accesibilidad y estilos para distintos tamaños. El monitor consulta el estado cada dos segundos y el modo docente cada 800 ms; una transición corta puede no aparecer. Algunas pruebas de frontend inspeccionan cadenas de los archivos en vez de ejecutar un navegador.

**Solución:** probar flujos completos en navegador, foco, teclado, errores HTTP y tamaños usados en el aula. Considerar eventos del servidor si se demuestra que la demora del sondeo afecta la experiencia. Añadir soporte para reducción de animaciones donde corresponda. No se evaluaron visualmente las pantallas actuales ni se midió contraste en esta revisión.

**15. Documentación académica desactualizada o demasiado categórica — prioridad alta antes de presentar.**

El informe de tutoría anterior contiene afirmaciones como «motor de nivel profesional», «corpus certificado», porcentajes generales y garantía de preservación lingüística. Las pruebas aprobadas y la inclusión de fuentes no justifican por sí solas esas conclusiones. Tampoco deben confundirse medidas históricas con resultados de esta versión.

`HardwareInterface.mover_actuador()` (`main_robot.py:602`) solo imprime un mensaje. En este módulo no hay una implementación del movimiento físico. La plataforma Laravel mencionada en documentación previa no forma parte de la revisión realizada y no se certifica aquí su existencia funcional o integración.

**Solución:** usar una matriz «requisito → código → prueba → evidencia → limitación», actualizar cifras y describir expresamente qué está implementado, simulado, medido o pendiente. Mantener la aprobación lingüística y las conclusiones pedagógicas bajo revisión de personas cualificadas. No trasladar a la tesis promesas que no puedan demostrarse.

**Herramientas recomendadas, por necesidad**

| Necesidad | Herramienta o método | Uso concreto |
|---|---|---|
| Detectar errores y reducir deuda | [Ruff](https://docs.astral.sh/ruff/linter/) | Empezar por errores e importaciones; revisar cambios antes de correcciones masivas |
| Conocer código y ramas ejercitados | [pytest-cov](https://pytest-cov.readthedocs.io/en/latest/config.html) | Medir cobertura por módulo y ramas; priorizar selección ASR, errores y rutas sensibles |
| Evitar regresiones funcionales | pytest y cliente de Flask ya disponibles | Añadir los casos reproducidos en este informe y pruebas que invoquen lógica real |
| Verificar experiencia real | Navegador automatizado y revisión docente | Grabar, guardar, descartar, cambiar participante y exportar bajo errores y demoras |
| Reproducir instalación | Entorno limpio, dependencias completas y manifiesto de modelos | Repetir instalación en CPU/GPU sin depender del estado de esta PC |
| Validar reconocimiento | Corpus reservado y matriz de confusión | Separar hablantes, motores, ruido, falsos aciertos y rechazos |
| Recuperar tras pérdida de disco | SQLite Backup y ensayo de restauración | Restaurar datos y archivos asociados, no solo exportar vocabulario |
| Mantener trazabilidad | Git y una verificación automática por cambio | Revisar cambios actuales, registrar una versión y repetir los controles útiles |

Ruff y pytest-cov no están instalados en el entorno revisado. No se instalaron durante esta auditoría. No se midió cobertura, no se ejecutó un escaneo de vulnerabilidades y no debe interpretarse `pip check` como tal.

**Orden recomendado de trabajo**

1. **Cerrar fallos reproducidos:** estado público sin participante, validación JSON y CSV seguro. Mantener pruebas que demuestren la corrección.
2. **Garantizar arranque reproducible:** Vosk declarado, modelo comprobado, configuración documentada y fallo claro si no existe reconocedor. Probar desde un entorno limpio.
3. **Proteger la recuperación:** respaldo privado completo y restauración ensayada antes de ampliar las personalizaciones.
4. **Validar el núcleo educativo:** conjunto independiente de voces, revisión de pronunciaciones por docentes, mediciones separadas por motor y revisión de sustituciones Vosk.
5. **Consolidar operación:** tiempos de respuesta, modo offline, acceso remoto protegido y cierre ordenado del robot.
6. **Mejorar mantenimiento y documentación:** refactorización gradual, pruebas de navegador, límites del historial y matriz de requisitos/evidencias.

No se asignan fechas cerradas sin conocer la disponibilidad del equipo y de los docentes. El criterio de finalización de cada etapa debe ser una demostración verificable, no solo completar una lista de cambios.

**Condiciones para una evaluación más alta**

Para aspirar a 8–9/10: corregir y probar los fallos confirmados, demostrar instalación y restauración en limpio, disponer de evaluación con hablantes reservados y revisión docente, medir latencia y funcionamiento offline y alinear tesis, configuración y código. La aprobación de 235 pruebas ya es una buena base; la mejora decisiva será demostrar que el sistema funciona de forma consistente en su contexto real de uso.
