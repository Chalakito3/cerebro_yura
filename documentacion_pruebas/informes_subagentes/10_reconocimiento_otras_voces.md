# 10 — Reconocimiento con otras voces: ¿lo aprendido de la docente generaliza?

Fecha: 28/09/2026. Subagente de pruebas de reconocimiento.
Evidencias: `documentacion_pruebas/evidencias/15_otras_voces/`.

## Qué se midió

Yura aprendió (tabla `pronunciaciones_aprendidas`) cómo escribe Whisper small las
palabras cuando las dice la docente. Con los **mismos** audios de la docente eso subió
el reconocimiento (menú 56 % → 85 %, juego 77 % → 92 %, sin pistas 49 % → 80 %).
Aquí se comprueba si esas formas aprendidas también ayudan con **otras voces**.

- 99 palabras distintas con grabación de la docente (`pronunciaciones.grabaciones()`).
- 3 voces sintéticas de edge-tts, distintas a la de Yura (`es-BO-SofiaNeural`):
  `es-BO-MarceloNeural` (hombre, Bolivia), `es-PE-AlexNeural` (hombre, Perú),
  `es-EC-AndreaNeural` (mujer, Ecuador). Las tres existían y generaron los 297 audios
  sin fallos. WAV 16 kHz mono con 0,25 s de silencio al final, como Yura.
- Whisper `small` en el procesador, con los mismos parámetros que
  `basedatos/aprender_de_audios.py` (`language="es"`, `fp16=False`, `temperature=0`,
  `beam_size=5`, `best_of=1`, `without_timestamps=True`, `condition_on_previous_text=False`)
  y el mismo filtro `es_alucinacion_whisper`.
- Dos situaciones por audio (594 transcripciones):
  - **juego**: la palabra mezclada con otras 6 (`aprender_de_audios.instruccion`, azar con semilla 2026);
  - **menu**: pistas generales (`texto.instruccion_reconocedor(None)`).
- Para cada transcripción:
  - (a) evaluador del juego **sin** lo aprendido: `respuesta_quechua_correcta(t, palabra)`;
  - (b) **con** lo aprendido: `respuesta_quechua_correcta(t, palabra, variantes(palabra))`;
  - (c) en menú, `traductor.buscar_vocabulario(t, "quechua", conexion)` encuentra la palabra correcta sin ambigüedad. "Sin aprendido" se obtuvo anulando en memoria `pronunciaciones.palabra_por_variante` (sin tocar el código).
- Falsos positivos: por audio, 5 palabras distintas al azar (semilla 7); además se hizo una
  revisión completa, sin Whisper, de cada transcripción contra las 98 palabras restantes
  (`falsos_exhaustivo.py`).
- Bases de datos solo leídas (`mode=ro` o funciones de lectura). No se modificó código.

Tiempo: 3 procesos en paralelo (2 hilos cada uno), 11–12 s por transcripción y proceso;
**39 minutos** en total (2 335 s). No hizo falta reducir a 2 voces. La generación de audios
tardó 9 minutos más.

## Tabla resumen (3 voces, 297 audios por situación)

| Situación | Sin aprendido | Con aprendido | Diferencia | Falsos positivos (5 al azar, sin → con) | Falsos positivos (revisión completa, sin → con) |
|---|---|---|---|---|---|
| Juego (evaluador) | 263/297 = **89 %** | 263/297 = **89 %** | 0 | 9/1 485 → 9/1 485 | 85/29 100 → 85/29 100 |
| Menú (evaluador) | 202/297 = **68 %** | 208/297 = **70 %** | +6 (+2 puntos) | 7/1 485 → 7/1 485 | 61/29 100 → 61/29 100 |
| Menú (búsqueda en consultas) | 150/297 = **51 %** | 159/297 = **54 %** | +9 (+3 puntos) | encuentra otra palabra: 0 → 0 | — |

Lo aprendido **no quitó ningún acierto** y **no añadió ningún falso positivo**.
En la búsqueda con lo aprendido hubo 2 resultados ambiguos (no cuentan como acierto).

Comparación con la voz de la docente (medición anterior):

| Situación | Docente sin → con | Otras voces sin → con |
|---|---|---|
| Juego | 77 % → 92 % (+15) | 89 % → 89 % (0) |
| Menú | 56 % → 85 % (+29) | 68 % → 70 % (+2) |

## Tabla por voz

| Voz | Juego sin | Juego con | Menú sin | Menú con | Búsqueda sin | Búsqueda con | Falsos positivos juego/menú (5 al azar) |
|---|---|---|---|---|---|---|---|
| es-BO-MarceloNeural | 86 % | 86 % | 68 % | 70 % | 49 % | 52 % | 3 / 3 (iguales sin y con) |
| es-PE-AlexNeural | 86 % | 86 % | 66 % | 69 % | 47 % | 52 % | 3 / 2 (iguales sin y con) |
| es-EC-AndreaNeural | 94 % | 94 % | 71 % | 72 % | 55 % | 58 % | 3 / 2 (iguales sin y con) |

Tiempo medio por transcripción (con 3 procesos a la vez): juego 11,3 s, menú 12,2 s.

### Qué se ganó gracias a lo aprendido

Evaluador (solo en menú, 6 casos): «chai» → Chay (3 voces), «hukucha» → Juk'ucha (2),
«mina» → Nina (1). Búsqueda en consultas (9 casos): los mismos más «iskai» → Iskay,
«guaira» → Wayra, «azno» → Asnu.

Ojo con «mina» → Nina: "mina" es una palabra del castellano; con lo aprendido, si un
estudiante dice "mina", el juego lo acepta como Nina. No apareció como falso positivo
contra otra palabra quechua, pero conviene revisarlo.

## Palabras problemáticas

**Nunca reconocida** (0 de 6):
- **Irqi**: las 3 voces dieron «iri» en las dos situaciones. Tiene 3 variantes aprendidas, pero ninguna es «iri».

**Reconocidas en la mitad o menos** (24), con lo que escribió Whisper:

| Palabra | Aciertos | Lo que escribió Whisper (ejemplos) |
|---|---|---|
| Juk | 1/6 | «fu», «pu», «hook» |
| Juku | 1/6 | «puku» (5 veces), «fuku» |
| T'ika | 1/6 | «teika» (5 veces) |
| Wayrana | 1/6 | «way then» (4 veces), «guairan» |
| Pilli | 2/6 | «pige», «pigi», «pg» |
| Wawa | 2/6 | «baikwai», «bagua», «bacua», «ba kua» |
| Ñan | 2/6 | «yen», «yan» |
| Allin | 3/6 | «adjim», «ajin», «algin» |
| Anqas | 3/6 | «anas», «ana» |
| Jamk'a | 3/6 | «chamka», «hamka», «qanchis» (sin variantes aprendidas) |
| Jaqay | 3/6 | «fakay», «hakai» |
| Juch'uy | 3/6 | «huchuli», «huchui», «fuchui» |
| K'anchaq | 3/6 | «con check», «gancek» |
| Kulli | 3/6 | «kujy», «kuji», «cudi», «cugi» |
| Phichqa | 3/6 | «pichu», «picha», «richa» |
| Qillqana | 3/6 | «quilana», «kilana» |
| Quwi | 3/6 | «cugui», «gurwi», «kugui» |
| Runa | 3/6 | «rune», «bruna» |
| Tawa | 3/6 | «taba», «daba» |
| Tukuy | 3/6 | «tukwi» |
| Wasi | 3/6 | «base», «basie», «beisi» |
| Wira | 3/6 | «vida», «guida», «uida» |
| Yachaqana wasi | 3/6 | «ya checa en avesi», «ya te canabeis» |
| Ñuqanchik | 3/6 | «puedes verlo» (3 veces) |

Casi todos los fallos son en **menú** (sin la palabra entre las pistas); en juego las
pistas corrigen la mayoría. El detalle completo está en `resumen.txt`.

### Falsos positivos (no causados por lo aprendido)

Los 85 (juego) y 61 (menú) pares aceptados como otra palabra vienen de la tolerancia
del propio evaluador, no de las variantes aprendidas. 107 de 594 audios fueron
aceptados como al menos otra palabra en la revisión completa. Los más repetidos:
kanka ↔ Manka, misi → Misk'i, sacha → P'acha / K'acha, sara → Saqra, tata → T'anta,
qucha → Khuchi / Q'uncha, ch'umpi ↔ Ch'uspi, k'anchaq ↔ K'anchay, puku → Punku,
«kaan chay» → Chay. También se acepta una palabra dentro de otra frase: «jampina wasi» y
«yachaqana wasi» → Wasi; «ch'aki ñan» → Ñan. En el juego solo importa si el estudiante
dice una palabra parecida a la pedida. Aun así, es un riesgo que ya existía y conviene
revisarlo aparte (tolerancia de 1 letra en palabras de 5 a 8 letras).

## Limitaciones

- **Las voces sintéticas pronuncian mal el quechua**: leen con reglas del castellano
  (sin eyectivas ni aspiradas; «T'ika» sale «teika»). **No son voces de niños**, que es
  el público real de Yura. Tampoco hay ruido de aula ni micrófono real.
- Las 3 voces son del mismo motor (edge-tts). Se parecen más entre sí que dos personas
  distintas, así que sus errores coinciden mucho (Irqi → «iri» en las tres).
- Un solo audio por palabra y voz, y la palabra sola (no dentro de una frase como
  "se dice...").
- Los falsos positivos al azar son solo 5 por audio. Por eso se añadió la revisión
  completa, que no necesita Whisper.
- La búsqueda en consultas se probó con la palabra suelta, no con la frase completa
  de una consulta real ("¿qué significa ...?").
- Las variantes se leyeron una vez al empezar (97 de 99 palabras tienen variantes
  seguras, 213 en total). Si la docente graba más, el resultado puede cambiar.

## Conclusión

**Lo aprendido de la docente casi no generaliza a otras voces.** Con las voces
sintéticas:

- En el juego no ganó ni un acierto (89 % → 89 %). Con la docente había ganado 15 puntos.
- En el menú ganó 2 puntos con el evaluador (68 % → 70 %) y 3 en la búsqueda (51 % → 54 %).
  Con la docente había ganado 29.

Las formas aprendidas sirven cuando otra voz produce **exactamente** el mismo error que
la docente («chai», «hukucha»). Las demás voces se equivocan de otra manera («puku»,
«teika», «iri», «base»). En cambio, lo aprendido **no daña**: no quitó aciertos ni sumó
falsos positivos. Mantenerlo es seguro, pero las cifras de 85–92 % describen solo a
la docente y no deben presentarse como el reconocimiento esperado con estudiantes.

Lo que sí ayuda con cualquier voz son las **pistas del juego**: 89 % en juego contra
68 % en menú, con las mismas voces. Para confirmar con estudiantes hacen falta
grabaciones reales de niños.

## Archivos

En `documentacion_pruebas/evidencias/15_otras_voces/`:
- `generar_audios.py`, `audios/` (297 WAV, 22 MB);
- `medir.py` (medición), `registro.log` (avance);
- `resultados_<voz>.jsonl` (una línea por audio y situación);
- `resumir.py` → `resumen.txt`;
- `falsos_exhaustivo.py` → `falsos_exhaustivo.txt`.
