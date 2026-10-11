# Avance en la Raspberry Pi 5 — 03/10/2026 al 08/10/2026

Continúa `correcciones_informe_2026-09-30.md`. Periodo: traslado de Yura de la computadora de escritorio (Ubuntu, GPU NVIDIA) a la Raspberry Pi 5 (8 GB, Raspberry Pi OS sobre Debian 13, Python 3.13) y entrenamiento de escucha, conversación y voz en ese equipo. Todas las cifras se midieron en la Raspberry; las evidencias están en `documentacion_pruebas/evidencias/20_` a `24_`.

## 0. Cambio de equipo: de computadora de escritorio a Raspberry Pi 5

| | Antes (hasta 03/10/2026) | Ahora |
|---|---|---|
| Equipo | Computadora de escritorio | Raspberry Pi 5 |
| Procesador | Intel Core de 10.ª generación (las evidencias registran «Intel(R) Core(TM) i3-10100»; por confirmar con el equipo, que lo recuerda como i5) | ARM Cortex-A76, 4 núcleos, 2,4 GHz |
| Memoria | 16 GB | 8 GB |
| Tarjeta gráfica | NVIDIA GTX 1650 (CUDA) | Ninguna utilizable para IA |
| Sistema | Ubuntu 24.04, Python 3.12, GNOME | Raspberry Pi OS (Debian 13), Python 3.13, labwc |
| Reconocedor en clase | Whisper small en la GPU | Vosk en la CPU |
| Audio | Audífonos USB C-Media + televisor por HDMI | Tarjeta de sonido USB C-Media (micrófono y parlante) |
| Pantalla | Televisor por HDMI | Televisor 4K o pantalla de 1024x600, ajuste automático |

Consecuencia principal: sin GPU, Whisper deja de ser viable para escuchar en tiempo real, y el reconocimiento pasa a Vosk. Todo el aprendizaje de la sección 2 sirve para que Vosk recupere lo que daba Whisper small con la GPU.

## 1. Instalación en la Raspberry Pi 5

- Se recreó el entorno `.venv` (el copiado era de Python 3.12 para x86 y no servía). `torch` se instaló en su versión solo CPU (`torch==2.14.0+cpu`); la versión por defecto de PyPI para ARM64 descargaba varios GB de bibliotecas CUDA inútiles sin GPU. Se instalaron `portaudio19-dev` y `espeak-ng`.
- Arranque automático (servicio de usuario y pantalla en Firefox) verificado con el escritorio labwc de la Pi.
- Audio: tarjeta de sonido USB C-Media (micrófono y parlante). Un primer puerto USB fallaba con error -71 junto con avisos de bajo voltaje de la fuente; en otro puerto funcionó.
- Pantalla: nuevo script `scripts/yura-ajustar-pantalla.py`, que al iniciar sesión elige la resolución según la pantalla conectada (1920x1080 en un televisor 4K; resolución nativa en pantallas menores; probado con 3840x2160 y 1024x600).
- Guía y lista de verificación en `RASPBERRY_PI5.md`.

## 2. Reconocimiento de voz (escuchar)

**Elección del reconocedor.** Con las 121 grabaciones reales de la docente:

| Reconocedor | Palabras entendidas | Tiempo por audio |
|---|---|---|
| Vosk (modelo pequeño en castellano) | 89-90 % | 0,6 s |
| Whisper tiny | 52 % | 3,6 s |

Se mantiene Vosk (`YURA_ASR=vosk`). Whisper small solo se usa como verificador en el afinado de pronunciación, no para escuchar en clase.

**Aprendizaje de Vosk.**
- Las grabaciones de la docente se volvieron a escuchar con Vosk (`aprender_de_audios.py --vosk`); lo aprendido antes era de Whisper y Vosk escribe distinto.
- Se agregaron 7 variaciones por grabación para imitar otras voces (aguda, muy aguda, grave, rápida, lenta, con ruido, aguda con ruido): 1.331 escuchas aprendidas en total. Medido con variaciones distintas a las del entrenamiento (`medir_escucha_vosk.py`), el promedio pasó de 38 % a 47 %; voz grave 37→50 %, rápida y aguda 22→36 %, aula ruidosa 34→41 %. La voz de niño solo subió de 6 % a 14 %.
- «Apágate» no existe en el vocabulario de Vosk (lo escribe «gate», «para date», «apaga te»). Se mapearon esas formas y se probó con 5 voces sintéticas y con la voz del equipo; la orden pide confirmación con «sí» antes de apagar. Se agregó un entrenamiento de órdenes con la voz de quien usa a Yura (`entrenar_ordenes.py`), que solo guarda una forma cuando Vosk la escribió igual al menos 2 veces.
- Preguntas: `aprender_preguntas_vosk.py` dijo con 4 voces «¿Qué significa ___?» y «¿Cómo se dice ___ en quechua?» para cada palabra del diccionario y aprendió 431 formas. Preguntas bien respondidas, de 10/16 a 25/30.

## 3. Modo castellano / quechua y diccionario

- El afinado de Vosk convertía palabras castellanas en quechuas dentro de frases («traduce agua» → «Aywa»; «desde que» → «desde Wawqi»). Ahora separa la parte castellana («¿cómo se dice **agua**?», no se toca) de la quechua («¿qué significa **allqu**?», se busca en el diccionario). Corrige además «en que hecho» → «en quechua», «vive los» → «dime los».
- Listas por tema desde el diccionario de la base de datos: «los números del uno al nueve», colores, animales, familia, partes del cuerpo, etc., con continuación al decir «sí» o «más». Antes Yura respondía que no tenía esa información.
- Búsqueda por familia de palabras: «plata» → plateado (Qullqi), «perrito» → perro.
- «Quiero que me digas…» y «puedes decirme…» se entienden como «¿cómo se dice…?».

## 4. Conversación

- «Háblame en español» deja a Yura en modo bilingüe hasta «háblame en quechua» (antes valía solo una respuesta).
- Modo docente: «soy la profesora…», «para mi clase» (y la forma «estoy el docente» que escribe Vosk) dan ideas de actividades en español y se mantienen 5 minutos. Probado con Groq: propuso «caza de colores», «el cajón mágico» y «palabras escondidas».
- Groq (modelo `openai/gpt-oss-120b`) recibe siempre la base conversacional del diccionario (saludos, diálogo infantil, pronombres, preguntas) y debe armar sus frases con ella. Palabras quechuas de sus respuestas presentes en el diccionario: de 26 % a 61 % (10 frases de prueba; el resto son mayormente conjugaciones válidas no escritas en la base). Adivinanzas en español con respuesta del diccionario, para no inventar quechua.
- Respuestas del diccionario variadas por palabra, con invitación a seguir («¿Me la repites?», un reto con otra palabra del mismo tema). Cuando Yura enseña una palabra, durante 30 s compara lo que diga el estudiante con ella y lo felicita o lo anima a repetir.
- Práctica: solo empieza con un pedido («quiero practicar»), no al mencionar «jugar»; una frase normal en medio de la práctica la termina. Se corrigió que 10 de las 303 palabras no podían acertarse nunca («Sulpayki», «Ari», «Para», «Tupananchiskama», etc.).
- Las correcciones de las secciones 3 y 4 salieron de dos sesiones observadas en vivo con el equipo (transcripciones visibles solo con `YURA_DEBUG=1`, desactivado al terminar).

## 5. Voz de Sofía (hablar)

- Pronunciación: el afinado (`afinar_pronunciacion.py`) ahora parte de lo ya guardado y solo lo reemplaza si queda al menos 3 % más parecido a la docente. La primera corrida en la Pi había reemplazado una escritura oficial de Laime; se detuvo y se restauró. Resultado: 6 escrituras nuevas aceptadas; una segunda corrida de 10 rondas no encontró mejoras.
- Expresión (`voz_sofia.py`): se conservan «?» y «!» (antes se cambiaban por puntos) y la velocidad y el tono varían al celebrar, consolar y preguntar.
- Sin internet: la caché de frases pasó de 499 (21 %) a las 2.986 frases que Yura dice sin internet (100 %). Sin internet Yura ya no espera hasta 40 s a Edge TTS; arma frases con oraciones guardadas y anota las que faltan para generarlas cuando vuelva la conexión (`medir_voz_offline.py`).

## 6. Tiempo de respuesta

Desde que el niño deja de hablar hasta que Yura empieza a sonar:

| Caso | Con internet | Sin internet |
|---|---|---|
| Diccionario, frase guardada | ≈ 1,7 s | ≈ 1,7 s |
| Diccionario, frase nueva | ≈ 3,7 s | ≈ 1,9 s (voz robótica) |
| Conversación con Groq | ≈ 4,6 s | no disponible |

Partes: 1,0 s de silencio, Vosk 0,56 s, decisión 0,005 s, Groq 0,9 s, voz nueva 2,0 s. La meta propuesta de 2,5 s como máximo no se cumple todavía en los casos con frase nueva.

## 7. Cuerpo (ESP32)

Se integró un ESP32 DevKit V1 por USB: programa con los pines del equipo y órdenes de voz para avanzar, girar, retroceder y detenerse, con un límite de 3 s por movimiento y freno ante obstáculos a menos de 20 cm. Se encontraron tres problemas de hardware: el chip USB CP2102 reiniciaba el ESP32 al abrir el puerto (resuelto abriéndolo sin DTR/RTS); los pines D16 y D17 cuelgan esta placa; y los servos de los brazos, cableados en D34/D35, no podían funcionar porque esos pines solo son de entrada.

A pedido del equipo, el cuerpo se borró y el ESP32 se formateó. Luego, también a su pedido (07/10/2026, en otra sesión de trabajo), se volvió a integrar con el programa v5 y los brazos pasados a D15 y D33. Pines vigentes: sensores Trig/Echo adelante 23/22, izquierda 21/19, derecha 18/5, atrás 4/2; L298N ENA 13, IN1 12, IN2 14, IN3 27, IN4 26, ENB 25; servos D15, D33 y cuello D32. No se probó con motores ni sensores alimentados por la batería.

## 8. Comparación de reconocedores: Whisper y Vosk, antes y ahora

**8.1 Lo que ya está medido**

| Reconocedor y equipo | Palabras de la docente | Tiempo por frase | Fuente |
|---|---|---|---|
| Whisper small, computadora con GPU (antes) | 81 % con lo aprendido (menú 83 %, juego 90 %, sin pistas 71 %) | 0,7 s | `evidencias/17_medicion_aprendizaje.txt` |
| Vosk, Raspberry Pi 5 (ahora) | 89-90 % | 0,56-0,6 s | sección 2 |
| Whisper tiny, Raspberry Pi 5 | 52 % | 3,6 s | sección 2 |

Las dos primeras filas no se midieron de la misma forma: en la computadora, el 81 % se calculó sin usar lo aprendido de la misma grabación y con tres tipos de pistas; en la Pi, el 89-90 % es sobre las 121 grabaciones con el afinado de Vosk. Indican que Vosk en la Pi quedó a un nivel parecido al de Whisper small con GPU para las palabras de la docente, y con tiempo de respuesta parecido; no permiten afirmar que sea mejor.

Whisper small no se usa en la Pi para escuchar: en la CPU es varias veces más lento que tiny (3,6 s por frase) y no cumpliría la meta de 2,5 s. Su tiempo exacto en la Pi no se midió.

**8.2 Whisper tiny con el mismo proceso que Vosk (medido el 08/10/2026)**

Para que la comparación sea defendible, `entrenar_whisper_tiny.py` dio a Whisper tiny el mismo trato que a Vosk y midió a los dos con la misma prueba: las 121 grabaciones de la docente tal cual y con variaciones distintas a las del entrenamiento (voz de niño, voz grave, aula ruidosa, rápido y agudo), 605 audios. También midió 24 frases en castellano (8 frases, 3 voces) y el tiempo por frase. Lo aprendido por Whisper se guardó aparte y no modificó a Vosk ni lo que usa Yura.

| Reconocedor (Raspberry Pi 5) | Palabras (prueba) | Tiempo por frase | Frases en castellano |
|---|---|---|---|
| Vosk + su proceso (lo que usa Yura) | 50 % | 0,49 s | 100 % |
| Whisper tiny tal cual | 37 % | 1,26 s | 79 % |
| Whisper tiny + el mismo proceso que Vosk | 52 % | 1,27 s | 79 % |
| Whisper tiny reentrenado (decodificador, 968 audios, 4 épocas) | 97 % | 1,19 s | 42 % |

Lectura:

- Con el mismo proceso, Whisper tiny entiende las palabras un poco más que Vosk (52 % frente a 50 %), pero es 2,6 veces más lento y entiende menos el castellano (79 % frente a 100 %).
- Reentrenado, llega al 97 % en palabras. Ese valor no demuestra que entienda a otras personas: la prueba usa variaciones de las mismas 121 grabaciones con que se reentrenó, así que en buena parte las memorizó (la pérdida del entrenamiento bajó de 1,21 a 0,026). Además olvidó el castellano: cayó de 79 % a 42 %, por lo que no entendería preguntas como «¿cómo se dice perro en quechua?».
- Decisión: Yura sigue con Vosk como reconocedor principal. Es el único que entiende el castellano completo, responde en medio segundo y cumple la meta de tiempo. El modelo reentrenado queda guardado en `basedatos/whisper_tiny_yura.pt` (no se sube a git).
- Posibilidad a probar: usar el Whisper tiny reentrenado solo para las respuestas de una palabra del juego y la práctica, y Vosk para todo lo demás; la respuesta tomaría unos 2,3 s. Antes hay que medirlo con voces que no estén en el entrenamiento (por ejemplo, niños grabados en el modo «Enseñar»).
- El quinto caso previsto (reentrenado y con el proceso) se omitió por tiempo. Durante la medición la Raspberry llegó a 82 °C y se frenó por temperatura, con el ventilador al máximo.

Datos: `evidencias/24_whisper_tiny_vs_vosk.json` y `24_whisper_tiny_vs_vosk.txt`.

**Verificación:** 357 pruebas aprobadas, incluidas las del cuerpo. Evidencias nuevas: `20_` y `22_` (afinado de pronunciación), `21_` (preguntas Vosk), `23_` (voz sin internet), `24_` (Whisper tiny frente a Vosk).

**Límites:** la comparación de la sección 8.2 usa las grabaciones de una sola docente; las mediciones de escucha usan grabaciones de una sola docente y voces sintéticas; con niños reales pueden variar, y la voz de niño sigue siendo el punto débil (14 %). El sonido «ch'» se reconoce mal («Ch'uspi» → «spy»). Las respuestas de Groq en quechua no se validaron con hablantes. Pendiente: grabar voces de niños en el modo «Enseñar», validar con la docente, cumplir la meta de 2,5 s y probar el cuerpo con energía.
