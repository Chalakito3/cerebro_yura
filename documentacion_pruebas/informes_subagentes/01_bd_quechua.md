# Informe 01 — Base de datos y contenido quechua (Fases 2, 3 y 4)

**Proyecto:** YURA (cerebro Python) · **Fecha:** 2026-09-27 · **Auditor:** Subagente 1
**Modo:** solo lectura. La BD se abrió siempre con `sqlite3.connect('file:diccionario.db?mode=ro', uri=True)`. No se modificó ningún archivo del proyecto. No se hicieron llamadas a servicios en línea (0 de 25).
**Evidencias:** `documentacion_pruebas/evidencias/01_volcado_bd.txt`, `01_integridad_bd.txt`, `01_diff_respaldo.txt`, `01_pruebas_funciones_bd.txt`, `01_pruebas_modo_traducir.txt`, `01_alcanzabilidad_y_estados.txt`.

---

## 1. Resumen ejecutivo

El diccionario que YURA usa para enseñar quechua a niños de 11-12 años **no es fiable tal como está**. De 187 filas, solo 103 (55 %) quedan como correctas o coherentes. **26 son un posible error de significado**: la palabra quechua significa otra cosa. Ejemplos: agua = *Uma*, que es aimara (en quechua *uma* es "cabeza"); escuela = *T'anta wasi*, literalmente "casa del pan"; mano = *Mak'a*, cuando la misma tabla usa *maki*; nariz = *Sunkha*, que es "barba"; caliente = *Q'uychi*, que es "arcoíris"; abeja = *Wanak'u*, que es "guanaco". Otras 14 filas tienen una grafía fuera de la norma boliviana (*Q'ello, Q'omer, Allqo, Sonqo, Soqta*…). 32 necesitan revisión de un hablante y 9 no se pudieron verificar.

La aplicación **enseña esos errores en voz alta**. Se comprobó ejecutando las funciones reales: "¿cómo se dice agua?" responde "Uma", y el juego pregunta "agua" y da "Uma" como respuesta correcta.

En lo técnico, la BD es un SQLite sin índices, sin claves foráneas y sin restricciones UNIQUE. Tiene 5 palabras quechua repetidas entre tablas y 45 filas sin `significado`. La columna `pronunciacion` apunta a 187 rutas de Windows que no existen y que ningún código usa.

Hay además dos fallos de código que dejan contenido fuera de alcance:
- El modo TRADUCIR no encuentra ninguna palabra española con "ñ" (niño, montaña, pequeño, olla pequeña).
- "¿Qué significa…?" no encuentra ninguna palabra quechua con apóstrofo o ñ (42 filas).

No existe sincronización entre la BD del robot y la plataforma web. La tabla `phonetic_evaluations` que exige el RF-05 de la tesis no existe en ningún repositorio.

**Veredicto: 🔴 ERROR CRÍTICO en contenido lingüístico. 🟠 REQUIERE CORRECCIÓN en estructura y trazabilidad.**

---

## 2. Estructura de la base de datos (`diccionario.db`)

Verificado con `sqlite_master`, `PRAGMA table_info`, `PRAGMA index_list`, `PRAGMA integrity_check` y `PRAGMA encoding` (evidencia `01_volcado_bd.txt`).

| Tabla | Filas | Columnas | PK | `significado` | sqlite_sequence |
|---|---|---|---|---|---|
| nivel1_alimentos | 10 | id, palabra_frase, pronunciacion, traduccion, significado | id INTEGER AUTOINCREMENT | sí | 10 |
| nivel1_colores | 14 | id, palabra_frase, pronunciacion, traduccion | id AUTOINCREMENT | **NO** | 20 |
| nivel1_elementos_casa | 4 | 5 columnas | id AUTOINCREMENT | sí | 4 |
| nivel1_elementos_naturales | 15 | 5 columnas | id AUTOINCREMENT | sí | 15 |
| nivel1_familia | 7 | 4 columnas | id AUTOINCREMENT | **NO** | 7 (respaldo: 6) |
| nivel1_herramientas | 5 | 5 columnas | id AUTOINCREMENT | sí | 5 |
| nivel1_lugares | 8 | 5 columnas | id AUTOINCREMENT | sí | 8 |
| nivel1_numeros | 37 | 5 columnas | **id INTEGER PRIMARY KEY sin AUTOINCREMENT; `palabra_frase` admite NULL** | sí | (no figura) |
| nivel1_objetos_escolares | 10 | 5 columnas | id AUTOINCREMENT | sí | 10 |
| nivel1_partes_del_cuerpo | 20 | 4 columnas | id AUTOINCREMENT | **NO** | 20 |
| nivel1_saludos | 4 | 4 columnas | id AUTOINCREMENT | **NO** | 4 |
| nivel1_utensilios_cocina | 9 | 5 columnas | id AUTOINCREMENT | sí | 9 |
| nivel2_adjetivos_calificativos | 12 | 5 columnas | id AUTOINCREMENT | sí | 12 |
| nivel2_adjetivos_determinativos | 6 | 5 columnas | id AUTOINCREMENT | sí | 6 |
| nivel2_animales | 26 | 5 columnas | id AUTOINCREMENT | sí | 26 |
| **Total** | **187** | | | | |

Tipos: todas las columnas de texto son `TEXT`. `palabra_frase` es `NOT NULL` en 14 tablas; en `nivel1_numeros` admite NULL. `pronunciacion`, `traduccion` y `significado` admiten NULL en todas.

Hallazgos de estructura:
- **Sin índices** (`PRAGMA index_list` vacío), sin FK (`PRAGMA foreign_keys = 0`, no hay relaciones que declarar), sin `UNIQUE`, sin `CHECK` y sin `DEFAULT`.
- **Diseño "una tabla por categoría"**: el nivel y la categoría se codifican en el nombre de la tabla (`nivelN_categoria`). El código los obtiene con una expresión regular (`traductor.py:10`, `:79`). Añadir una categoría obliga a crear otra tabla. No hay una tabla de categorías, ni de niveles, ni un identificador global de palabra.
- **Esquema heterogéneo**: 4 tablas no tienen `significado`. El código lo resuelve con `try/except` (`traductor.py:106-116`).
- `nivel1_numeros` usa `id` = valor numérico (1…20, 30…100, 200…1000). Es una convención útil, pero distinta del resto.
- `traductor._tablas_de_vocabulario` (`traductor.py:87`) exige la columna `pronunciacion`. Una tabla nueva sin esa columna quedaría **excluida sin aviso**, aunque la columna no se use.
- Integridad física: `integrity_check = ok`, codificación UTF-8 y todo el texto en NFC.
- Rendimiento (medido): `buscar_vocabulario` tarda ≈1,1 ms por llamada, porque lee las 15 tablas completas cada vez. `_obtener_vocabulario_para_practica` tarda ≈7,4 ms (5 búsquedas × 15 tablas). No es un problema con 187 filas, pero no escala.
- El archivo está excluido de Git (`.gitignore:5: *.db`). La BD **no está versionada** ni tiene un script de creación o semilla: si se pierde, no hay forma de reconstruirla desde el repositorio.
- Ambos consumidores abren la BD en **lectura/escritura** aunque nunca escriben: `main_robot.py:577` y `conversacion.py:182`. No existe ningún `INSERT` ni `UPDATE` en el código (verificado con `grep`).

---

## 3. Integridad de datos

Evidencia: `01_integridad_bd.txt`.

### 3.1 Duplicados

| Tipo | Filas afectadas |
|---|---|
| Mismo quechua en varias filas | `Uma`: elementos_naturales 2 (Agua) y partes_del_cuerpo 1 (Cabeza) · `K'anchay`: elementos_naturales 3 (Luz) y adjetivos_calificativos 11 (Brillante) · `Tata`: familia 1 (Padre) y familia 7 (Papá) · `Huk`: numeros 1 (Uno) y adjetivos_determinativos 3 (Uno) · `K'uchu`: objetos_escolares 7 (Mesa) y partes_del_cuerpo 8 (Espalda) |
| Colisión al quitar el apóstrofo (como hacen `_normalizar_texto` y la evaluación de pronunciación) | `Sach'a` (Árbol, naturales 4) ↔ `Sacha` (Venado, animales 14) · `Kuchi` (Cerdo, animales 6) ↔ `K'uchi` (Mono, animales 26) |
| Mismo español en varias filas | `papa`: alimentos 3 (Papa) y familia 7 (Papá, sin tilde) · `uno`: numeros 1 y determinativos 3 (misma respuesta *Huk* repetida) |
| Español igual al quechua (la fila no traduce nada) | alimentos 3 Papa, 5 Api, 6 Ají · lugares 1 Plaza, 3 Iglesia, 5 Puente, 6 Hospital · utensilios 5 Jarra · animales 10 Llama |
| Misma ruta de audio | `C:/audios/nivel1/familia/tata.mp3` (familia 1 y 7) |

### 3.2 IDs
- `nivel1_colores`: **faltan los id 3, 5, 6, 7, 9 y 11** (sqlite_sequence = 20 con 14 filas). Hubo filas borradas sin documentar.
- `nivel1_numeros`: 963 ids "faltantes" por diseño (id = valor).
- No hay IDs repetidos (lo impide la PK).

### 3.3 Nulos, vacíos, espacios, mayúsculas y caracteres
- NULL: 45 filas sin `significado`, porque la columna no existe (colores 14, cuerpo 20, familia 7, saludos 4). No hay otros NULL ni cadenas vacías.
- Espacios sobrantes o dobles: **ninguno**.
- Mayúsculas: todas las entradas quechuas empiezan con mayúscula. Es consistente.
- Apóstrofo: solo se usa `'` (U+0027), 40 veces. No aparece `’`, `´` ni `ʼ`. Es consistente.
- No ASCII: `Ají` (í), `Ñan`, `Ch'aki ñan`, `Ch'askañawi`, `Ñawi`. Dos rutas de audio contienen ñ (`ñawi.mp3`, `chaskañawi.mp3`); `ñan` se guardó como `nan.mp3`, así que la convención de nombres de audio es incoherente.
- Letras fuera del alfabeto quechua normalizado: vocales e/o en 14 filas (ver §7), y b/d/g/j/v/z/tildes en `Ají`, `Windu`, `Plaza`, `Iglesia`, `Lapiz qillqana`, `Vasu`, `Jarra`.

### 3.4 Columna `pronunciacion`
- Contiene **rutas de archivo de Windows**, no la pronunciación: `C:/audios/...mp3`. De 187 rutas, **0 existen en disco** (verificado con `os.path.exists`).
- Coherencia de rutas con la categoría:
  - `nivel1_colores` mezcla dos prefijos: `C:/audios/nivel1/colores/` (3 filas) y `C:/audios/colores/` (11 filas).
  - 7 categorías distintas (alimentos, casa, naturales, herramientas, lugares, escolares, utensilios) comparten `C:/audios/nivel1/objetos/`.
  - `K'uchi` usa `kuchi_mono.mp3`, que se desvía del patrón.
- **Uso en el código:** se lee en `traductor.py:103` y `:124`, pero **ninguna función la usa** (grep de `pronunciacion` en todos los .py, .js y .html). El único efecto real es negativo: es obligatoria para que la tabla se cargue (`traductor.py:87`). No llega ni a la pantalla ni a la voz. La tarjeta web muestra una "Pronunciación" escrita a mano en `web/app.py`, sin relación con esta columna.

### 3.5 Columna `significado`
- Falta en `nivel1_colores`, `nivel1_familia`, `nivel1_partes_del_cuerpo` y `nivel1_saludos` (45 filas). El código usa `NULL AS significado` (`traductor.py:112-116`); se verificó que no falla.
- Efecto visible en la práctica: `conversacion.py:235` y `:303` usan el texto genérico "una palabra de uso cotidiano". Resultado: "Significa Cabeza: una palabra de uso cotidiano", que es pedagógicamente pobre.
- En TRADUCIR y en "qué significa" simplemente no se añade la explicación.
- Hay significados que contradicen la categoría: *T'anta manka* dice "Utensilio para cocinar pan" pero está en alimentos. Otros son glosas literales ("Dos diez") o repiten la traducción ("Número uno").

### 3.6 Diferencias con `diccionario.respaldo.db`
Evidencia: `01_diff_respaldo.txt`. El esquema es idéntico. Hay solo **2 diferencias**:

| Tabla | id | Respaldo | Actual |
|---|---|---|---|
| nivel1_familia | 1 | `Tayta`, `C:/audios/nivel1/familia/tayta.mp3`, Padre | `Tata`, `C:/audios/nivel1/familia/tata.mp3`, Padre |
| nivel1_familia | 7 | (no existía) | `Tata`, `C:/audios/nivel1/familia/tata.mp3`, Papá |

El `sqlite_sequence` de familia pasó de 6 a 7; el total pasó de 186 a 187 filas. Los SHA-256 difieren (`54df86ba…` actual, `e61b66e3…` respaldo).

El cambio cumple lo que pidió el equipo, pero crea un duplicado exacto: la fila 7 no aporta información nueva al quechua y duplica el audio. Una alternativa más limpia sería una sola fila `Tata` con traducción "Padre / Papá" (queda como propuesta).

---

## 4. Relación de las tablas con YURA (verificada ejecutando el código real)

Rutas de consumo:
1. **TRADUCIR** (español→quechua): `main_robot` → `traductor.ejecutar_traducir` → `buscar_vocabulario(texto, "espanol")` → voz "En quechua se dice: X. {significado}".
2. **CONVERSAR** (`conversacion.procesar_entrada`), que usa la BD de cuatro maneras:
   - "¿cómo se dice…?" → `_responder_consulta_local(..., "espanol")`.
   - "¿qué significa…?" → `_responder_consulta_local(..., "quechua")`.
   - "enséñame / practicar" → `_comenzar_practica` → `_obtener_vocabulario_para_practica`, que elige una palabra al azar entre las 187 sin tener en cuenta el nivel.
   - Groq → `vocabulario_relevante` + `formatear_vocabulario` inyectan en el *prompt* hasta 40 filas; los **saludos se inyectan siempre**.
3. **JUEGO**: `Juego(["gato","perro","sol","agua","casa","arbol"], traductor.consultar_diccionario_local)` (`main_robot.py:465-468`). Solo usa esas 6 palabras.
4. **Pantalla**: `_set_web_status(content=traduccion)` muestra la palabra quechua en "YURA DICE". La tarjeta "EJEMPLO" nunca muestra datos de la BD (ver §8).

| Tabla | TRADUCIR | Cómo se dice / Qué significa | Práctica | Prompt Groq | Juego | ¿Llega a la pantalla? | Datos que nunca se usan |
|---|---|---|---|---|---|---|---|
| alimentos | sí | sí / sin K'anka ni T'anta manka | sí | si se menciona | no | sí, la palabra en "YURA DICE" | pronunciacion |
| colores | sí | sí / sin 4 con apóstrofo | sí | sí ("colores") | no | sí | pronunciacion |
| elementos_casa | sí | sí | sí | si se menciona | Wasi (casa) | sí | pronunciacion |
| elementos_naturales | Urqu **no** ("montaña") | 6 no alcanzables en "qué significa" | sí | si se menciona | Uma (agua), Inti (sol), Sach'a (árbol) | sí | pronunciacion |
| familia | Wawa **no** ("niño") | sí | sí | sí ("familia") | no | sí | pronunciacion |
| herramientas | sí | 3 no alcanzables | sí | si se menciona | no | sí | pronunciacion |
| lugares | sí | Ch'askañawi no | sí | si se menciona | no | sí | pronunciacion |
| numeros | sí | sí | sí | sí ("numeros": 37 filas + 3 saludos; **"Allin tuta" queda fuera por el límite de 40**) | no | sí | pronunciacion |
| objetos_escolares | sí | 5 no alcanzables | sí | si se menciona | no | sí | pronunciacion |
| partes_del_cuerpo | sí | 6 no alcanzables | sí | si se menciona | no | sí | pronunciacion |
| saludos | sí | sí (pero "allin p'unchay" no se encuentra) | sí | **siempre** | no | sí | pronunciacion |
| utensilios_cocina | Manka michi **no** ("olla pequeña") | 5 no alcanzables | sí | si se menciona | no | sí | pronunciacion |
| adjetivos_calificativos | Huchuy **no** ("pequeño") | 3 no alcanzables | sí | si se menciona | no | sí | pronunciacion |
| adjetivos_determinativos | sí | sí | sí | si se menciona | no | sí | pronunciacion |
| animales | sí | 7 no alcanzables | sí | sí ("animales") | Misi (gato), Allqo (perro) | sí | pronunciacion |

Campos que la app no aprovecha: `pronunciacion` (en las 15 tablas) y el **nivel** (`nivel1` / `nivel2`), que se extrae en `traductor.py:125` pero no se usa en ninguna parte: no hay progresión por nivel. La categoría solo se usa para filtrar el *prompt* y para dar la frase de ejemplo en colores y saludos (`conversacion.py:400-412`).

**Causas de lo "no alcanzable"** (verificado; `01_pruebas_modo_traducir.txt` y `01_alcanzabilidad_y_estados.txt`):
- `traductor._normalizar_texto` (`traductor.py:42`) elimina la ñ: "niño" se convierte en "ni o" y **no se encuentra**. Afecta a Montaña/Urqu, Niño/Wawa, Olla pequeña/Manka michi y Pequeño/Huchuy.
- `conversacion._normalizar_texto` (`conversacion.py:80-82`) convierte ñ en n y el apóstrofo en espacio. Después `buscar_vocabulario` compara con la BD, que sí conserva ñ y apóstrofo, así que **no hay coincidencia**. "Qué significa k'anchay / ñawi / sach'a / q'ello" devuelve `None` en **42 filas**.

---

## 5. Comparación con la plataforma web (Laravel) y con la tesis

### 5.1 Plataforma web (copia de solo lectura; no ejecutable: sin PHP ni MySQL, así que su comportamiento en ejecución es ⚫ NO VERIFICADO)
- `database/migrations/2026_07_20_000002_create_robot_category_tables.php:11-27` crea 7 tablas (`robot_alimentos`, `robot_colores`, `robot_casa_items`, `robot_naturaleza_items`, `robot_familia_items`, `robot_herramientas_items`, `robot_lugares_items`) con **solo `id`, `name` y timestamps**. No tienen columna para el quechua, la pronunciación ni el significado.
- `database/seeders/RobotCategorySeeder.php:12-20` siembra 35 palabras **en español**:
  - Manzana, Pan, Leche, Arroz, Carne
  - Rojo, Azul, Amarillo, Verde, Negro
  - Silla, Mesa, Cama, Puerta, Ventana
  - Árbol, Río, Montaña, Flor, Sol
  - Madre, Padre, Hermano, Abuela, Tío
  - Martillo, Destornillador, Llave, Taladro, Alicate
  - Escuela, Parque, Mercado, Iglesia, Plaza

**Coincidencia con el cerebro** (verificado por script; evidencia `01_cerebro_vs_plataforma.txt`): solo 7 categorías de 15 (faltan números, partes del cuerpo, saludos, objetos escolares, utensilios y los 3 temas de nivel 2). De las 35 palabras de la plataforma, **21 tienen el mismo texto español en el cerebro, pero 5 están en otra categoría**:
- Pan → naturales (*T'anta*).
- Carne → partes del cuerpo (*Aycha*).
- Silla y Mesa → objetos escolares (*Tiyana*, *K'uchu*).
- Escuela → objetos escolares (*T'anta wasi*, errónea).

**14 no existen en el cerebro**: Manzana, Leche, Arroz, Cama, Flor, Hermano, Abuela, Tío, Martillo (el cerebro solo tiene "Martillo de piedra"), Destornillador, Llave, Taladro, Alicate y Parque. Las herramientas modernas de la plataforma (taladro, destornillador, alicate) no tienen equivalente, y las del cerebro son tradicionales.
- **Las tablas `robot_*` nunca se leen**: grep de `DB::table('robot_` sin resultados. Sus nombres solo aparecen como etiquetas en `app/Http/Controllers/RobotActivityController.php:25-33` y `GradeController.php:429-437`.
- **Tres listas de categorías distintas** para lo mismo:
  - `RobotActivityController.php:50`: `Casa, Naturaleza`.
  - `GradeController.php:458`: `Elementos de Casa, Elementos Naturales`.
  - `resources/views/grades/index.blade.php:217-224`: `<select name="activity_category">` con valores `nivel1_*`. Además, el formulario del modal envía `activity_category` a `robot-activities.store` (línea 190), que valida `category` como obligatorio. Por análisis estático, **el modal no puede pasar la validación** (⚫ no ejecutado).
- Etiquetas quechuas en la plataforma (`index.blade.php:218-224`): Mikhuna, Llimp'ikuna, Wasi, Sallqa Pacha, Ayllu, Llamk'anakuna, Marka. Son coherentes, salvo *Marka*, que es de origen aimara (ver §6).
- **No hay sincronización real.** El cerebro no contiene ninguna llamada HTTP ni referencia a la API (grep de `api/v1|requests.|http|laravel|mysql` en los .py: sin resultados). La API `POST /api/v1/robot/activity` (`routes/api.php:31`, `Api/RobotActivityController.php:13-20`) solo recibe una nota (score) y no vocabulario. El robot nunca la llama.
- La configuración por defecto de la plataforma es `DB_CONNECTION=sqlite` (`config/database.php:20`, `.env.example:23`), no MySQL como dice la tesis.
- `resources/lang/qu/messages.php` (fuera del alcance principal) tiene frases dudosas:
  - `:182` "Nota allinllachu ruwachisqa": el sufijo *-chu* la convierte en pregunta o negación.
  - `:149` "Kurso / Asignatura allinchay": *allinchay* = arreglar; "seleccionar" sería *akllay*.
  - `:119, :124-131` mezclan español: "estadon", "estadonta".

  → REQUIERE REVISIÓN DE HABLANTE.

### 5.2 Tesis (PDF págs. 52-58, leídas)
- **RF-05** (pág. impresa 42): "registrar cada intento en la tabla `phonetic_evaluations` con marca de tiempo". **No existe en ningún repositorio**: grep de `phonetic` sin resultados en la plataforma y en el cerebro. El cerebro no persiste los intentos: `_set_game_event` (`main_robot.py:506-520`) solo actualiza el estado en memoria para la pantalla. 🔴 No cumplido.
- **RNF-02**: "La base de datos MySQL debe mantener integridad referencial y aislamiento ACID". La BD del robot es SQLite **sin ninguna FK**, y la plataforma usa SQLite por defecto. Las tablas `robot_*` no tienen FK. 🟠 No cumplido en lo que toca a vocabulario.
- **7.4.1 a) Clases**: la clase `Pronunciacion` (idPronunciacion, palabra, precision, retroalimentacion) no tiene equivalente ni en SQLite ni en MySQL.
- **7.4.1 b) Esquema BD** (diagrama pág. 44): muestra solo tablas de la plataforma (users, students, activities, interactions, results…). **No incluye ninguna tabla de vocabulario ni las 15 tablas `nivelN_*` del robot**, ni las `robot_*`.
- **7.4.3 Despliegue** (pág. 48): dibuja un enlace "WiFi / REST" entre el cerebro y el servidor Laravel. **No está implementado** (ver 5.1). Además indica "Faster-Whisper ASR", pero el código usa `openai-whisper` (`main_robot.py:17`).
- **7.4.4 "Esquema completo de base de datos"**: la sección está **vacía**: solo tiene el título, sin contenido.
- **RF-03** ("el docente debe crear palabras clave"): la plataforma no tiene ningún formulario ni tabla para crear palabras quechuas; las `robot_*` solo se siembran.

---

## 6. Auditoría lingüística quechua

**Criterio:** quechua boliviano de Cochabamba, alfabeto normalizado de 3 vocales (a, i, u) con q, qh, q', k, kh, k', ch, chh, ch', etc.
**Regla aplicada:** solo se marca POSIBLE ERROR cuando la confianza es alta. Toda "forma sugerida" es **para revisar con un hablante o docente de quechua, no una corrección definitiva**.

**Recuento de las 187 filas:**

| Estado | Filas |
|---|---|
| CORRECTO/COHERENTE | 103 |
| REQUIERE REVISIÓN | 32 |
| POSIBLE ERROR | 26 |
| INCONSISTENTE | 14 |
| NO VERIFICADO | 9 |
| DUPLICADO | 3 |

Además, SIN TRADUCCIÓN real (palabra española): 9 filas, incluidas en los estados anteriores.

**Columna "Uso en YURA"** (verificada ejecutando el código):
- TRADUCIR = se alcanza diciendo la palabra española en modo traductor; "ambigua" = YURA lee varias opciones.
- "qué significa" = se alcanza en modo conversación.
- práctica = puede salir en "enséñame".
- JUEGO = está entre las 6 palabras del juego.

### 6.1 Tabla completa (187 filas)

| ID | Tabla | Texto quechua | Significado registrado (traducción / significado) | Categoría | Uso en YURA | Estado | Observación |
|---|---|---|---|---|---|---|---|
| 1 | nivel1_alimentos | Mikhuna | Comida / Alimento en general | alimentos | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE | Grafía boliviana con kh. |
| 2 | nivel1_alimentos | Chicha | Bebida tradicional / Fermentado de maíz | alimentos | TRADUCIR, "qué significa": sí, práctica | REQUIERE REVISIÓN | "Chicha" es préstamo del español; forma quechua usual: aqha (sur peruano) / aswa (Bolivia). Choca con id 8. |
| 3 | nivel1_alimentos | Papa | Papa / Tubérculo andino | alimentos | TRADUCIR: ambigua, "qué significa": sí, práctica | CORRECTO/COHERENTE | Palabra de origen quechua. Mismo texto en español que "Papá" (familia 7): la app dice ambas opciones (verificado). |
| 4 | nivel1_alimentos | Sara | Maíz / Cereal básico | alimentos | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 5 | nivel1_alimentos | Api | Api / Bebida de maíz morado | alimentos | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE | Término regional; traducción = misma palabra (no aporta significado en español). |
| 6 | nivel1_alimentos | Ají | Ají / Condimento picante | alimentos | TRADUCIR, "qué significa": sí, práctica | REQUIERE REVISIÓN | "Ají" es préstamo (taíno vía español), con tilde fuera del alfabeto quechua. Forma quechua conocida: uchu (alta confianza). Revisar con hablante. |
| 7 | nivel1_alimentos | K'anka | Carne asada / Alimento preparado | alimentos | TRADUCIR, "qué significa": NO, práctica | POSIBLE ERROR | En quechua boliviano k'anka se usa para "gallo"; "asar" es kankay (sin glotal). "Carne asada" no corresponde. Revisar con hablante. |
| 8 | nivel1_alimentos | Aswa | Chicha dulce / Bebida tradicional | alimentos | TRADUCIR, "qué significa": sí, práctica | REQUIERE REVISIÓN | aswa = chicha en general en Bolivia; "chicha dulce" no verificado. Duplica conceptualmente id 2. |
| 9 | nivel1_alimentos | Mullu | Maíz tostado / Alimento típico | alimentos | TRADUCIR, "qué significa": sí, práctica | POSIBLE ERROR | mullu = concha/cuenta (spondylus). "Maíz tostado" suele ser hank'a / jank'a. Revisar con hablante. |
| 10 | nivel1_alimentos | T'anta manka | Horno de barro / Utensilio para cocinar pan | alimentos | TRADUCIR, "qué significa": NO, práctica | POSIBLE ERROR | Literal "olla de pan". El significado dice "utensilio": no es alimento (categoría incorrecta). Forma para "horno" no verificada. |
| 1 | nivel1_colores | Puka | Rojo / (NULL) | colores | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 2 | nivel1_colores | Anqas | Azul / (NULL) | colores | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE | Variante boliviana anqas. |
| 4 | nivel1_colores | Yuraq | Blanco / (NULL) | colores | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 8 | nivel1_colores | Q'ello | Amarillo / (NULL) | colores | TRADUCIR, "qué significa": NO, práctica | INCONSISTENTE | Grafía con e/o fuera de la norma boliviana de 3 vocales: forma normalizada q'illu. |
| 10 | nivel1_colores | Q'omer | Verde / (NULL) | colores | TRADUCIR, "qué significa": NO, práctica | INCONSISTENTE | Grafía con e/o: forma normalizada q'umir. |
| 12 | nivel1_colores | Yana | Negro / (NULL) | colores | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 13 | nivel1_colores | Uqi | Gris / (NULL) | colores | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 14 | nivel1_colores | Ch'umpi | Marrón / Café / (NULL) | colores | TRADUCIR, "qué significa": NO, práctica | CORRECTO/COHERENTE |  |
| 15 | nivel1_colores | Kulli | Morado / Violeta / (NULL) | colores | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 16 | nivel1_colores | Q'ello-puka | Naranja / (NULL) | colores | TRADUCIR, "qué significa": NO, práctica | REQUIERE REVISIÓN | Compuesto con guion y grafía e/o (q'illu puka). Término para "naranja" no verificado. Además conversacion.py:427-431 dice que NO hay naranja (contradicción, código muerto). |
| 17 | nivel1_colores | Qamya puka | Rosado / (NULL) | colores | TRADUCIR, "qué significa": sí, práctica | NO VERIFICADO | "qamya" = insípido/soso; su uso para "rosado" no está verificado. |
| 18 | nivel1_colores | Yuraq anqas | Celeste / (NULL) | colores | TRADUCIR, "qué significa": sí, práctica | REQUIERE REVISIÓN | Compuesto descriptivo plausible ("azul blanco"); no verificado como término usual. |
| 19 | nivel1_colores | Quri | Dorado / (NULL) | colores | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE | quri = oro; uso como "dorado" aceptable. |
| 20 | nivel1_colores | Qullqi | Plateado / (NULL) | colores | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE | qullqi = plata; uso como "plateado" aceptable. |
| 1 | nivel1_elementos_casa | Wasi | Casa / Lugar de vivienda | elementos_casa | TRADUCIR, "qué significa": sí, práctica, JUEGO | CORRECTO/COHERENTE |  |
| 2 | nivel1_elementos_casa | Punku | Puerta / Entrada de la casa | elementos_casa | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 3 | nivel1_elementos_casa | Windu | Ventana / Abertura para luz y aire | elementos_casa | TRADUCIR, "qué significa": sí, práctica | REQUIERE REVISIÓN | Contiene "d" (fuera del alfabeto normalizado); forma no atestiguada. Revisar con hablante. |
| 4 | nivel1_elementos_casa | Manka | Olla / Recipiente para cocinar | elementos_casa | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE | "Olla" también está en utensilios (Manka michi): clasificación mezclada. |
| 1 | nivel1_elementos_naturales | T'anta | Pan / Alimento básico | elementos_naturales | TRADUCIR, "qué significa": NO, práctica | INCONSISTENTE | Palabra correcta (pan) pero NO es elemento natural: categoría incorrecta. |
| 2 | nivel1_elementos_naturales | Uma | Agua / Elemento vital | elementos_naturales | TRADUCIR, "qué significa": sí, práctica, JUEGO | POSIBLE ERROR | CRÍTICO: "uma" = agua en AIMARA; en quechua uma = cabeza (esta misma BD, cuerpo id 1). Quechua: yaku (la usan juego.py:107, gemini_transcriber.py:276 y main_robot.py:833). Revisar con hablante. |
| 3 | nivel1_elementos_naturales | K'anchay | Luz / Claridad del día o lámpara | elementos_naturales | TRADUCIR, "qué significa": NO, práctica | CORRECTO/COHERENTE | Duplicado en adjetivos_calificativos id 11 (Brillante). |
| 4 | nivel1_elementos_naturales | Sach'a | Árbol / Planta grande con tronco | elementos_naturales | TRADUCIR, "qué significa": NO, práctica, JUEGO | CORRECTO/COHERENTE | Grafía sach'a. Al quitar el apóstrofo colisiona con "Sacha" (animales 14). |
| 5 | nivel1_elementos_naturales | Rumi | Piedra / Elemento natural sólido | elementos_naturales | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 6 | nivel1_elementos_naturales | Inti | Sol / Astro que da luz | elementos_naturales | TRADUCIR, "qué significa": sí, práctica, JUEGO | CORRECTO/COHERENTE |  |
| 7 | nivel1_elementos_naturales | Killa | Luna / Astro nocturno | elementos_naturales | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 8 | nivel1_elementos_naturales | Puyu | Nube / Condensación de agua en el cielo | elementos_naturales | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 9 | nivel1_elementos_naturales | Hanaq pacha | Cielo / Espacio sobre la tierra | elementos_naturales | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE | Término cosmológico ("mundo de arriba"); para "cielo" físico es aceptable con matiz. |
| 10 | nivel1_elementos_naturales | Qocha | Lago / Cuerpo de agua | elementos_naturales | TRADUCIR, "qué significa": sí, práctica | INCONSISTENTE | Grafía con o: forma normalizada qucha. |
| 11 | nivel1_elementos_naturales | Mayu | Río / Corriente de agua | elementos_naturales | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 12 | nivel1_elementos_naturales | Urqu | Montaña / Elevación natural | elementos_naturales | TRADUCIR: NO alcanzable, "qué significa": sí, práctica | CORRECTO/COHERENTE | Usa la norma u (urqu) mientras Allqo/Sonqo/Qocha usan o: incoherencia interna. |
| 13 | nivel1_elementos_naturales | Ñan | Camino / Sendero o vía | elementos_naturales | TRADUCIR, "qué significa": NO, práctica | CORRECTO/COHERENTE | Audio nombrado nan.mp3 (sin ñ). |
| 14 | nivel1_elementos_naturales | Ch'aki ñan | Sendero / Camino pequeño | elementos_naturales | TRADUCIR, "qué significa": NO, práctica | POSIBLE ERROR | ch'aki = seco; "sendero/camino de a pie" es chaki ñan (chaki = pie). Diferencia glotal cambia el significado. |
| 15 | nivel1_elementos_naturales | T'ikari wasi | Jardín / Lugar con plantas | elementos_naturales | TRADUCIR, "qué significa": NO, práctica | NO VERIFICADO | "t'ikari" no reconocido (t'ika = flor). Término para "jardín" no verificado. |
| 1 | nivel1_familia | Tata | Padre / (NULL) | familia | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE | Variante de Cochabamba (tata) por decisión del equipo. Antes Tayta (ver respaldo). |
| 2 | nivel1_familia | Mama | Madre / (NULL) | familia | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 3 | nivel1_familia | Wawa | Niño / (NULL) | familia | TRADUCIR: NO alcanzable, "qué significa": sí, práctica | REQUIERE REVISIÓN | wawa = bebé / hijo(a); "niño" en general suele ser irqi. Uso coloquial aceptable; revisar. No se encuentra por voz en modo TRADUCIR ("niño" pierde la ñ). |
| 4 | nivel1_familia | Qhari | Hombre / (NULL) | familia | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 5 | nivel1_familia | Warmi | Mujer / (NULL) | familia | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 6 | nivel1_familia | Runa | Persona / (NULL) | familia | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 7 | nivel1_familia | Tata | Papá / (NULL) | familia | TRADUCIR: ambigua, "qué significa": sí, práctica | DUPLICADO | Misma palabra y mismo audio que id 1; padre/papá solo difieren en español. Genera ambigüedad "papa/papá" (manejada). |
| 1 | nivel1_herramientas | Llamk'ana | Herramienta / Instrumento de trabajo | herramientas | TRADUCIR, "qué significa": NO, práctica | REQUIERE REVISIÓN | Derivado de llamk'ay (trabajar); uso como "herramienta" genérica no verificado. |
| 2 | nivel1_herramientas | Rumi maqana | Martillo de piedra / Herramienta de construcción | herramientas | TRADUCIR, "qué significa": sí, práctica | REQUIERE REVISIÓN | Compuesto descriptivo (maqana = garrote/porra). No verificado como nombre usual. |
| 3 | nivel1_herramientas | Wachikuy | Aguja / Instrumento para coser | herramientas | TRADUCIR, "qué significa": sí, práctica | POSIBLE ERROR | Forma no reconocida; "aguja" se documenta como yawri. Revisar con hablante. |
| 4 | nivel1_herramientas | T'uksu | Pala / Herramienta para cavar | herramientas | TRADUCIR, "qué significa": NO, práctica | NO VERIFICADO | "t'uksu" no reconocido; en Bolivia "pala" suele decirse lampa (préstamo). |
| 5 | nivel1_herramientas | Ch'aki maqana | Hacha / Herramienta para cortar madera | herramientas | TRADUCIR, "qué significa": NO, práctica | POSIBLE ERROR | Literal "garrote seco"; no corresponde a "hacha". Forma correcta no verificada. |
| 1 | nivel1_lugares | Plaza | Plaza / Lugar central de reunión | lugares | TRADUCIR, "qué significa": sí, práctica | REQUIERE REVISIÓN | Palabra española sin traducir (quechua = español). |
| 2 | nivel1_lugares | Marka | Pueblo / Comunidad pequeña | lugares | TRADUCIR, "qué significa": sí, práctica | REQUIERE REVISIÓN | marka es de origen aimara, usada en quechua boliviano; alternativa quechua: llaqta. |
| 3 | nivel1_lugares | Iglesia | Iglesia / Lugar religioso | lugares | TRADUCIR, "qué significa": sí, práctica | REQUIERE REVISIÓN | Palabra española sin adaptar; contiene e/o y "g". |
| 4 | nivel1_lugares | Qhatu | Mercado / Lugar de comercio | lugares | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 5 | nivel1_lugares | Puente | Puente / Construcción para cruzar ríos | lugares | TRADUCIR, "qué significa": sí, práctica | POSIBLE ERROR | Palabra española; en quechua existe chaka (puente), alta confianza. |
| 6 | nivel1_lugares | Hospital | Hospital / Centro de salud | lugares | TRADUCIR, "qué significa": sí, práctica | REQUIERE REVISIÓN | Palabra española sin traducir. |
| 7 | nivel1_lugares | Ch'askañawi | Mirador / Lugar para observar paisajes | lugares | TRADUCIR, "qué significa": NO, práctica | POSIBLE ERROR | ch'aska ñawi = "ojos de estrella/ojos brillantes" (nombre propio, flor). No significa "mirador". Revisar. |
| 8 | nivel1_lugares | Taqlla | Arado / Herramienta agrícola tradicional | lugares | TRADUCIR, "qué significa": sí, práctica | INCONSISTENTE | Palabra correcta (arado de pie, chakitaqlla) pero NO es un lugar: categoría incorrecta (va en herramientas). |
| 1 | nivel1_numeros | Huk | Uno / Número uno | numeros | TRADUCIR: ambigua, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 2 | nivel1_numeros | Iskay | Dos / Número dos | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 3 | nivel1_numeros | Kimsa | Tres / Número tres | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 4 | nivel1_numeros | Tawa | Cuatro / Número cuatro | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 5 | nivel1_numeros | Pisqa | Cinco / Número cinco | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 6 | nivel1_numeros | Soqta | Seis / Número seis | numeros | TRADUCIR, "qué significa": sí, práctica | INCONSISTENTE | Grafía con o: forma normalizada suqta. |
| 7 | nivel1_numeros | Qanchis | Siete / Número siete | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 8 | nivel1_numeros | Pusaq | Ocho / Número ocho | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 9 | nivel1_numeros | Isqun | Nueve / Número nueve | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 10 | nivel1_numeros | Chunka | Diez / Número diez | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 11 | nivel1_numeros | Chunka hukniyuq | Once / Diez con uno | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 12 | nivel1_numeros | Chunka iskayniyuq | Doce / Diez con dos | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 13 | nivel1_numeros | Chunka kimsayuq | Trece / Diez con tres | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 14 | nivel1_numeros | Chunka tawayuq | Catorce / Diez con cuatro | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 15 | nivel1_numeros | Chunka pisqayuq | Quince / Diez con cinco | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 16 | nivel1_numeros | Chunka soqtayuq | Dieciséis / Diez con seis | numeros | TRADUCIR, "qué significa": sí, práctica | INCONSISTENTE | Grafía con o: suqtayuq. |
| 17 | nivel1_numeros | Chunka qanchisniyuq | Diecisiete / Diez con siete | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 18 | nivel1_numeros | Chunka pusqayuq | Dieciocho / Diez con ocho | numeros | TRADUCIR, "qué significa": sí, práctica | POSIBLE ERROR | "pusqa" no existe. Por la regla de la propia tabla (qanchis→qanchisniyuq) debe ser chunka pusaqniyuq. Alta confianza. |
| 19 | nivel1_numeros | Chunka isqonniyuq | Diecinueve / Diez con nueve | numeros | TRADUCIR, "qué significa": sí, práctica | INCONSISTENTE | "isqon" contradice id 9 "Isqun": forma coherente chunka isqunniyuq. |
| 20 | nivel1_numeros | Iskay chunka | Veinte / Dos diez | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 30 | nivel1_numeros | Kimsa chunka | Treinta / Tres diez | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 40 | nivel1_numeros | Tawa chunka | Cuarenta / Cuatro diez | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 50 | nivel1_numeros | Pisqa chunka | Cincuenta / Cinco diez | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 60 | nivel1_numeros | Soqta chunka | Sesenta / Seis diez | numeros | TRADUCIR, "qué significa": sí, práctica | INCONSISTENTE | Grafía con o (suqta chunka). |
| 70 | nivel1_numeros | Qanchis chunka | Setenta / Siete diez | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 80 | nivel1_numeros | Pusaq chunka | Ochenta / Ocho diez | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 90 | nivel1_numeros | Isqun chunka | Noventa / Nueve diez | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 100 | nivel1_numeros | Pachak | Cien / Número cien | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE | Variante boliviana pachak (sur peruano pachaq). |
| 200 | nivel1_numeros | Iskay pachak | Doscientos / Dos cien | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 300 | nivel1_numeros | Kimsa pachak | Trescientos / Tres cien | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 400 | nivel1_numeros | Tawa pachak | Cuatrocientos / Cuatro cien | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 500 | nivel1_numeros | Pisqa pachak | Quinientos / Cinco cien | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 600 | nivel1_numeros | Soqta pachak | Seiscientos / Seis cien | numeros | TRADUCIR, "qué significa": sí, práctica | INCONSISTENTE | Grafía con o (suqta pachak). |
| 700 | nivel1_numeros | Qanchis pachak | Setecientos / Siete cien | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 800 | nivel1_numeros | Pusaq pachak | Ochocientos / Ocho cien | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 900 | nivel1_numeros | Isqun pachak | Novecientos / Nueve cien | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 1000 | nivel1_numeros | Waranka | Mil / Número mil | numeros | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 1 | nivel1_objetos_escolares | Yachay wasi | Aula / Salón de clases | objetos_escolares | TRADUCIR, "qué significa": sí, práctica | INCONSISTENTE | yachay wasi = "casa del saber" = ESCUELA, no "aula". |
| 2 | nivel1_objetos_escolares | T'anta wasi | Escuela / Lugar de aprendizaje | objetos_escolares | TRADUCIR, "qué significa": NO, práctica | POSIBLE ERROR | CRÍTICO: t'anta wasi = "casa del pan" (panadería). Registrado como "Escuela": la app enseña esto al preguntar "escuela" (verificado). |
| 3 | nivel1_objetos_escolares | Qillqana | Lápiz / Instrumento para escribir | objetos_escolares | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE | qillqana = "instrumento para escribir". |
| 4 | nivel1_objetos_escolares | Qillqa | Libro / Texto para leer o escribir | objetos_escolares | TRADUCIR, "qué significa": sí, práctica | REQUIERE REVISIÓN | qillqa = escritura/letra/escrito; "libro" suele ser p'anqa. |
| 5 | nivel1_objetos_escolares | P'anka | Cuaderno / Material escolar para escribir | objetos_escolares | TRADUCIR, "qué significa": NO, práctica | REQUIERE REVISIÓN | p'anqa (con q) suele significar libro/hoja; grafía con k no normalizada. |
| 6 | nivel1_objetos_escolares | K'ipi | Mochila / Bolso escolar | objetos_escolares | TRADUCIR, "qué significa": NO, práctica | REQUIERE REVISIÓN | Forma documentada: q'ipi (bulto/carga); aquí escrito con k'. |
| 7 | nivel1_objetos_escolares | K'uchu | Mesa / Mueble escolar | objetos_escolares | TRADUCIR, "qué significa": NO, práctica | POSIBLE ERROR | k'uchu = rincón/esquina, no "mesa". Duplicado con cuerpo id 8 (Espalda). |
| 8 | nivel1_objetos_escolares | Tiyana | Silla / Mueble escolar | objetos_escolares | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE | tiyana = asiento. |
| 9 | nivel1_objetos_escolares | K'anchay rikhuy | Pizarra / Superficie para escribir | objetos_escolares | TRADUCIR, "qué significa": NO, práctica | POSIBLE ERROR | Compuesto "luz + ver" no atestiguado para "pizarra". Revisar. |
| 10 | nivel1_objetos_escolares | Lapiz qillqana | Bolígrafo / Instrumento para escribir | objetos_escolares | TRADUCIR, "qué significa": sí, práctica | REQUIERE REVISIÓN | Híbrido con palabra española "lapiz" (sin tilde). No verificado. |
| 1 | nivel1_partes_del_cuerpo | Uma | Cabeza / (NULL) | partes_del_cuerpo | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE | Correcto (cabeza); duplicado con Uma=Agua (naturales 2), que es el error. |
| 2 | nivel1_partes_del_cuerpo | Ñawi | Ojo / (NULL) | partes_del_cuerpo | TRADUCIR, "qué significa": NO, práctica | CORRECTO/COHERENTE | Audio con ñ en nombre de archivo (ñawi.mp3). "Qué significa ñawi" no funciona (verificado). |
| 3 | nivel1_partes_del_cuerpo | Simi | Boca / (NULL) | partes_del_cuerpo | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 4 | nivel1_partes_del_cuerpo | Sunkha | Nariz / (NULL) | partes_del_cuerpo | TRADUCIR, "qué significa": sí, práctica | POSIBLE ERROR | En quechua boliviano sunkha = barba; nariz = sinqa. Alta confianza. |
| 5 | nivel1_partes_del_cuerpo | Rinri | Oreja / (NULL) | partes_del_cuerpo | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 6 | nivel1_partes_del_cuerpo | K'aki | Diente / (NULL) | partes_del_cuerpo | TRADUCIR, "qué significa": NO, práctica | POSIBLE ERROR | k'aki = mentón/barbilla; diente = kiru. Alta confianza. |
| 7 | nivel1_partes_del_cuerpo | Qallu | Lengua / (NULL) | partes_del_cuerpo | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 8 | nivel1_partes_del_cuerpo | K'uchu | Espalda / (NULL) | partes_del_cuerpo | TRADUCIR, "qué significa": NO, práctica | POSIBLE ERROR | k'uchu = rincón; espalda = wasa. Alta confianza. |
| 9 | nivel1_partes_del_cuerpo | Sonqo | Corazón / (NULL) | partes_del_cuerpo | TRADUCIR, "qué significa": sí, práctica | INCONSISTENTE | Grafía con o: forma normalizada sunqu. |
| 10 | nivel1_partes_del_cuerpo | Waqta | Espalda baja / (NULL) | partes_del_cuerpo | TRADUCIR, "qué significa": sí, práctica | REQUIERE REVISIÓN | waqta = costado/lado; "espalda baja" no verificado. |
| 11 | nivel1_partes_del_cuerpo | Mak'a | Mano / (NULL) | partes_del_cuerpo | TRADUCIR, "qué significa": NO, práctica | POSIBLE ERROR | Mano = maki (la misma tabla usa "maki" en id 12). Alta confianza. |
| 12 | nivel1_partes_del_cuerpo | Ruku maki | Dedos / (NULL) | partes_del_cuerpo | TRADUCIR, "qué significa": sí, práctica | REQUIERE REVISIÓN | Dedo = ruk'ana; "ruku" no corresponde. Revisar con hablante. |
| 13 | nivel1_partes_del_cuerpo | Chaki | Pie / (NULL) | partes_del_cuerpo | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 14 | nivel1_partes_del_cuerpo | Ruku chaki | Dedos del pie / (NULL) | partes_del_cuerpo | TRADUCIR, "qué significa": sí, práctica | REQUIERE REVISIÓN | Igual que id 12 (ruk'ana). |
| 15 | nivel1_partes_del_cuerpo | K'uchu chaki | Talón / (NULL) | partes_del_cuerpo | TRADUCIR, "qué significa": NO, práctica | NO VERIFICADO | "rincón del pie" (k'uchu); término para talón no verificado. |
| 16 | nivel1_partes_del_cuerpo | Waqta chaki | Pantorrilla / (NULL) | partes_del_cuerpo | TRADUCIR, "qué significa": sí, práctica | NO VERIFICADO | Término para pantorrilla no verificado. |
| 17 | nivel1_partes_del_cuerpo | K'ullu | Hueso / (NULL) | partes_del_cuerpo | TRADUCIR, "qué significa": NO, práctica | POSIBLE ERROR | k'ullu = madera/tronco; hueso = tullu. Alta confianza. |
| 18 | nivel1_partes_del_cuerpo | Aycha | Carne / (NULL) | partes_del_cuerpo | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 19 | nivel1_partes_del_cuerpo | Akcha | Cabello / (NULL) | partes_del_cuerpo | TRADUCIR, "qué significa": sí, práctica | REQUIERE REVISIÓN | En quechua boliviano/sur: chukcha; "aqcha/akcha" es de variantes centrales. |
| 20 | nivel1_partes_del_cuerpo | Wira | Grasa corporal / (NULL) | partes_del_cuerpo | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 1 | nivel1_saludos | Allin punchay | Buenos días / (NULL) | saludos | TRADUCIR, "qué significa": sí, práctica, siempre en prompt Groq | INCONSISTENTE | Falta la glotal: allin p'unchay. El código (conversacion.py:26, gemini, whisper, web) usa "p'unchay": buscar "allin p'unchay" en la BD NO encuentra nada (verificado). |
| 2 | nivel1_saludos | Imaynalla | ¿Cómo estás? / (NULL) | saludos | TRADUCIR, "qué significa": sí, práctica, siempre en prompt Groq | CORRECTO/COHERENTE | Forma abreviada; completa "Imaynalla kachkanki" (usada en código). |
| 3 | nivel1_saludos | Allin sukay | Buenas tardes / (NULL) | saludos | TRADUCIR, "qué significa": sí, práctica, siempre en prompt Groq | REQUIERE REVISIÓN | "tarde" = sukha (Bolivia) o ch'isi; "sukay" no normalizado. |
| 4 | nivel1_saludos | Allin tuta | Buenas noches / (NULL) | saludos | TRADUCIR, "qué significa": sí, práctica, siempre en prompt Groq | CORRECTO/COHERENTE |  |
| 1 | nivel1_utensilios_cocina | Platu | Plato / Utensilio para servir comida | utensilios_cocina | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE | Préstamo adaptado habitual. |
| 2 | nivel1_utensilios_cocina | Vasu | Vaso / Recipiente para beber | utensilios_cocina | TRADUCIR, "qué significa": sí, práctica | REQUIERE REVISIÓN | Préstamo con "v" (fuera del alfabeto); adaptación usual wasu/vasu. Revisar. |
| 3 | nivel1_utensilios_cocina | K'uchara | Cuchara / Utensilio para comer | utensilios_cocina | TRADUCIR, "qué significa": NO, práctica | REQUIERE REVISIÓN | Préstamo (cuchara); la glotal k' no se justifica (kuchara). |
| 4 | nivel1_utensilios_cocina | T'ikari manka | Sartén / Utensilio para freír | utensilios_cocina | TRADUCIR, "qué significa": NO, práctica | NO VERIFICADO | "t'ikari" no reconocido; término para sartén no verificado. |
| 5 | nivel1_utensilios_cocina | Jarra | Jarra / Recipiente para líquidos | utensilios_cocina | TRADUCIR, "qué significa": sí, práctica | REQUIERE REVISIÓN | Palabra española sin traducir; "j" fuera de la norma. |
| 6 | nivel1_utensilios_cocina | K'uchillu | Cuchillo / Utensilio de cocina | utensilios_cocina | TRADUCIR, "qué significa": NO, práctica | REQUIERE REVISIÓN | Préstamo (cuchillo); glotal injustificada (kuchillu). |
| 7 | nivel1_utensilios_cocina | Q'ipina | Bolsa / Recipiente para alimentos | utensilios_cocina | TRADUCIR, "qué significa": NO, práctica | REQUIERE REVISIÓN | Derivado de q'ipi (carga); uso como "bolsa" no verificado. |
| 8 | nivel1_utensilios_cocina | Manka michi | Olla pequeña / Utensilio de cocina | utensilios_cocina | TRADUCIR: NO alcanzable, "qué significa": sí, práctica | POSIBLE ERROR | michi = gato (hispanismo); "olla pequeña" sería mankacha o huch'uy manka. "olla pequeña" no se alcanza por voz (ñ). |
| 9 | nivel1_utensilios_cocina | K'uchuna | Tijera / Utensilio para cortar | utensilios_cocina | TRADUCIR, "qué significa": NO, práctica | REQUIERE REVISIÓN | Derivado de k'uchuy (cortar); plausible, confirmar uso para "tijera". |
| 1 | nivel2_adjetivos_calificativos | Allin | Bueno / Que es positivo o correcto | adjetivos_calificativos | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 2 | nivel2_adjetivos_calificativos | Mana allin | Malo / Que es negativo o incorrecto | adjetivos_calificativos | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 3 | nivel2_adjetivos_calificativos | Hatun | Grande / De tamaño considerable | adjetivos_calificativos | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 4 | nivel2_adjetivos_calificativos | Huchuy | Pequeño / De tamaño reducido | adjetivos_calificativos | TRADUCIR: NO alcanzable, "qué significa": sí, práctica | REQUIERE REVISIÓN | En Bolivia se escribe huch'uy / juch'uy (con glotal). "pequeño" no se alcanza por voz (ñ). |
| 5 | nivel2_adjetivos_calificativos | Sumaq | Bonito / Que es agradable a la vista | adjetivos_calificativos | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 6 | nivel2_adjetivos_calificativos | Millay | Feo / Que no es agradable a la vista | adjetivos_calificativos | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 7 | nivel2_adjetivos_calificativos | Chiri | Frío / De baja temperatura | adjetivos_calificativos | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 8 | nivel2_adjetivos_calificativos | Q'uychi | Caliente / De alta temperatura | adjetivos_calificativos | TRADUCIR, "qué significa": NO, práctica | POSIBLE ERROR | k'uychi = arcoíris; caliente = q'uñi. Alta confianza. |
| 9 | nivel2_adjetivos_calificativos | Machu | Viejo / Que tiene mucha edad o antigüedad | adjetivos_calificativos | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE | machu para personas/animales; objetos viejos: mawk'a. |
| 10 | nivel2_adjetivos_calificativos | Musuq | Nuevo / Que es reciente o no usado | adjetivos_calificativos | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 11 | nivel2_adjetivos_calificativos | K'anchay | Brillante / Que refleja luz intensamente | adjetivos_calificativos | TRADUCIR, "qué significa": NO, práctica | DUPLICADO | Duplicado de naturales id 3; "brillante" sería k'anchaq. Revisar. |
| 12 | nivel2_adjetivos_calificativos | Ch'upi | Opaco / Que no refleja luz, sin brillo | adjetivos_calificativos | TRADUCIR, "qué significa": NO, práctica | NO VERIFICADO | Término para "opaco" no verificado. |
| 1 | nivel2_adjetivos_determinativos | Kay | Aquí / Ahora / Indica lugar cercano o tiempo presente | adjetivos_determinativos | TRADUCIR, "qué significa": sí, práctica | POSIBLE ERROR | kay = este/esta. "Aquí" = kaypi, "ahora" = kunan. Alta confianza. |
| 2 | nivel2_adjetivos_determinativos | Chay | Ese / Aquel / Indica lo que está más lejos del hablante | adjetivos_determinativos | TRADUCIR, "qué significa": sí, práctica | REQUIERE REVISIÓN | chay = ese; "aquel" = haqay/jaqay. |
| 3 | nivel2_adjetivos_determinativos | Huk | Uno / Indica unidad o singularidad | adjetivos_determinativos | TRADUCIR: ambigua, "qué significa": sí, práctica | DUPLICADO | Duplicado de números id 1 ("uno" da dos opciones idénticas, verificado). |
| 4 | nivel2_adjetivos_determinativos | Llapa | Todo / Indica totalidad o conjunto completo | adjetivos_determinativos | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE | llapa/llapan. |
| 5 | nivel2_adjetivos_determinativos | Mayqin | Cuál / Indica selección o identificación | adjetivos_determinativos | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE | Es interrogativo, no determinativo (clasificación). |
| 6 | nivel2_adjetivos_determinativos | Imayna | Cómo / Indica modo o manera | adjetivos_determinativos | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE | Es interrogativo, no determinativo (clasificación). |
| 1 | nivel2_animales | Allqo | Perro / Animal doméstico común | animales | TRADUCIR, "qué significa": sí, práctica, JUEGO | INCONSISTENTE | Grafía con o: allqu (juego.py:105 usa "allqu"). |
| 2 | nivel2_animales | Misi | Gato / Animal doméstico | animales | TRADUCIR, "qué significa": sí, práctica, JUEGO | CORRECTO/COHERENTE | Uso boliviano; juego.py:104 usa "michi" (contradicción interna). |
| 3 | nivel2_animales | Kawallu | Caballo / Animal de carga | animales | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE | Préstamo adaptado. |
| 4 | nivel2_animales | Asnu | Burro / Animal de carga | animales | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE | Préstamo adaptado. |
| 5 | nivel2_animales | Waka | Vaca / Animal de ganado vacuno | animales | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE | Préstamo adaptado. |
| 6 | nivel2_animales | Kuchi | Cerdo / Animal doméstico de granja | animales | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE | Préstamo adaptado. Colisiona con "K'uchi" (id 26) al quitar apóstrofo. |
| 7 | nivel2_animales | Wallpa | Gallina / Ave doméstica | animales | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 8 | nivel2_animales | Wallata | Pato / Ave acuática | animales | TRADUCIR, "qué significa": sí, práctica | REQUIERE REVISIÓN | wallata = ganso andino (huallata), no "pato" en general. |
| 9 | nivel2_animales | Kuy | Cuy / Roedor doméstico andino | animales | TRADUCIR, "qué significa": sí, práctica | REQUIERE REVISIÓN | Hispanización; forma quechua quwi. |
| 10 | nivel2_animales | Llama | Llama / Camélido andino usado como carga | animales | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 11 | nivel2_animales | Alpaka | Alpaca / Camélido andino productor de lana | animales | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE | Nombre nativo paqu; "alpaka" es aceptable. |
| 12 | nivel2_animales | Kuntur | Cóndor / Ave rapaz de gran tamaño | animales | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 13 | nivel2_animales | Atuq | Zorro / Mamífero carnívoro de los Andes | animales | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 14 | nivel2_animales | Sacha | Venado / Mamífero herbívoro de los bosques | animales | TRADUCIR, "qué significa": sí, práctica | POSIBLE ERROR | venado = taruka; sacha/sach'a = árbol/monte. Colisión con naturales 4. Alta confianza. |
| 15 | nivel2_animales | Ukuku | Oso andino / Mamífero de montaña | animales | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 16 | nivel2_animales | Ch'ita | Gato montés / Felino silvestre de los Andes | animales | TRADUCIR, "qué significa": NO, práctica | NO VERIFICADO | "ch'ita" no reconocido para gato montés (titi / usqhullu). Revisar. |
| 17 | nivel2_animales | Hamp'atu | Sapo / Anfibio común en zonas húmedas | animales | TRADUCIR, "qué significa": NO, práctica | CORRECTO/COHERENTE |  |
| 18 | nivel2_animales | Pillpintu | Mariposa / Insecto volador de colores | animales | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 19 | nivel2_animales | K'anchisapa | Luciérnaga / Insecto que emite luz | animales | TRADUCIR, "qué significa": NO, práctica | POSIBLE ERROR | luciérnaga = ninakuru. "k'anchisapa" no reconocido. |
| 20 | nivel2_animales | Wanak'u | Abeja / Insecto productor de miel | animales | TRADUCIR, "qué significa": NO, práctica | POSIBLE ERROR | wanaku = guanaco. Abeja: wanqullu / lachiwana (Bolivia). Alta confianza. |
| 21 | nivel2_animales | Ch'iwchi | Avispa / Insecto volador con aguijón | animales | TRADUCIR, "qué significa": NO, práctica | POSIBLE ERROR | chiwchi = pollito. "Avispa" no corresponde. Alta confianza. |
| 22 | nivel2_animales | Challwa | Pez / Animal acuático | animales | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 23 | nivel2_animales | Amaru | Serpiente / Reptil de cuerpo alargado | animales | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE | Serpiente (también mítica); en Bolivia común mach'aqway = víbora. |
| 24 | nivel2_animales | K'achi | Lagarto / Reptil de cuerpo pequeño | animales | TRADUCIR, "qué significa": NO, práctica | NO VERIFICADO | Lagartija = qaraywa / jararankhu (Bolivia); "k'achi" no reconocido. |
| 25 | nivel2_animales | Ukucha | Ratón / Roedor pequeño | animales | TRADUCIR, "qué significa": sí, práctica | CORRECTO/COHERENTE |  |
| 26 | nivel2_animales | K'uchi | Mono / Mamífero amazónico | animales | TRADUCIR, "qué significa": NO, práctica | POSIBLE ERROR | mono = k'usillu. "K'uchi" colisiona con Kuchi (cerdo) cuando el código quita apóstrofos. |

### 6.2 Quechua fuera de la BD

| Ubicación | Texto | Uso | Estado | Observación |
|---|---|---|---|---|
| conversacion.py:11 | "Ñuqaqa Yura kani. Robotmi kani," | Presentación hablada | CORRECTO/COHERENTE | "Robotmi" es un préstamo con sufijo correcto. |
| conversacion.py:11-12 | "qhichwa simita rimanakuypaq yanapakuq. Qhichwa simita rimanakuyta, rimaykunata kallpachayta yanapani." | Presentación | REQUIERE REVISIÓN DE HABLANTE | La construcción con dos acusativos (*simita… rimanakuyta… kallpachayta*) es poco natural. No se propone forma. |
| conversacion.py:13 | "Imapin yanapaykiman?" | Presentación | REQUIERE REVISIÓN | *-n* evidencial tras vocal es muy propio del sur peruano; en Bolivia es frecuente *-mi/-n*. Confirmar con hablante de Cochabamba. |
| conversacion.py:18-19 | Rimaykullayki | Saludo = "hola" | CORRECTO/COHERENTE | Saludo respetuoso. "hola" nunca se encuentra en la BD (no hay fila). |
| conversacion.py:20, 22 | "rima el cowley que", "y minaya cachan que" | Alias de errores de transcripción | SIN RELACIÓN (no es quechua) | Parches del reconocimiento de voz. |
| conversacion.py:21 | Imaynalla kachkanki | ¿Cómo estás? | CORRECTO/COHERENTE | Forma boliviana (*-chka-*). Contradice web/app.py:22 y app.js:21 (*kashanki*). |
| conversacion.py:23-25 | Anchata munakuyki / Anchata kuyayki | Te quiero mucho | CORRECTO/COHERENTE | |
| conversacion.py:26-27 | Allin p'unchay | Buenos días | CORRECTO/COHERENTE | **Contradice la BD** (saludos 1 "Allin punchay"). |
| conversacion.py:28-29 | Yusulpayki | Gracias | CORRECTO/COHERENTE | Forma boliviana (de "Dios se lo pague"). **No está en la BD.** |
| conversacion.py:30-35 | Ari / Mana | Sí / No | CORRECTO/COHERENTE | No están en la BD. |
| conversacion.py:35 | Sulpayki | Gracias (abreviado) | REQUIERE REVISIÓN | Forma coloquial abreviada. |
| conversacion.py:36 | Imataq sutiyki | ¿Cómo te llamas? | CORRECTO/COHERENTE | |
| conversacion.py:37 | Sutiymi | "Mi nombre es" | REQUIERE REVISIÓN | Frase incompleta: falta el nombre (*Sutiyqa … kan / … sutiy*). |
| conversacion.py:38-39 | Maymanta kanki / Allinmi | ¿De dónde eres? / Está bien | CORRECTO/COHERENTE | |
| conversacion.py:40 | "Qamrí" | ¿Y tú? | REQUIERE REVISIÓN | La tilde "í" no pertenece a la grafía normalizada (*Qamri?*). |
| conversacion.py:41 | Kayqa | "Esto" | CORRECTO/COHERENTE | |
| conversacion.py:42-45 | "Quechua", "Hablar en quechua", "Enséñame quechua"… | Mapeados como "frases quechuas conocidas" | SIN RELACIÓN CON YURA | Son frases en español dentro del diccionario de frases quechuas. |
| conversacion.py:113, 321, 671; main_robot.py:980 | Tupananchiskama | Despedida | CORRECTO/COHERENTE | Forma boliviana. No está en la BD. |
| conversacion.py:427-431 | "Todavía no tengo el color naranja" | Respuesta local | INCONSISTENTE | La BD sí tiene naranja (*Q'ello-puka*). Código muerto: se verificó que responde la BD antes. |
| web/app.py:18-22 (CARD_EXAMPLES) | Rimaykullayki · pron. "Ri-ma-y-ku-llay-ki" · meaning "Rimaykullayki" · ej. "Rimaykullayki, imaynalla **kashanki**?" | Tarjeta de la pantalla | INCONSISTENTE | *meaning* repite el quechua (debería ser "Hola"). Silabeo erróneo (Ri-may-ku-llay-ki). *kashanki* es variante sur peruana, no boliviana. |
| web/app.py:26-30 | Allin p'unchay · pron. "A-lin p'un-chay" · ej. "Allin p'unchay, wawqi." | Tarjeta | REQUIERE REVISIÓN | "A-lin" pierde la *ll*. *meaning* no dice "Buenos días". *wawqi* = hermano (de varón): correcto como vocativo. |
| web/app.py:34-38 | Allin tuta · "A-lin tu-ta" · ej. "Allin tuta, ñañay." | Tarjeta | REQUIERE REVISIÓN | Silabeo sin *ll*. *ñañay* = mi hermana (dicho por mujer): uso restringido. |
| web/app.py:42-46 | Yusulpayki · "Yu-su-lpay-ki" · ej. "Yusulpayki, uywaq." | Tarjeta | REQUIERE REVISIÓN | Silabeo erróneo (Yu-sul-pay-ki). *uywaq* = "el que cría": vocativo poco natural para niños. |
| web/app.py:50-54 | Anchata munakuyki · ej. "…, wayna." | Tarjeta | REQUIERE REVISIÓN | *wayna* = joven/novio: vocativo poco apropiado en un aula de primaria. |
| web/app.py:58-62 | Imaynalla kachkanki · pron. "I-ma-ya-lla ka-ch-kan-ki" · ej. "…, tata?" | Tarjeta | POSIBLE ERROR (pronunciación) | La pronunciación **omite la n** (I-may-na-lla) y parte mal *kach-kan-ki*. |
| web/static/js/app.js:16-22 | FALLBACK_CARD con "imaynalla kashanki" | Tarjeta de respaldo | INCONSISTENTE | *kashanki* frente a *kachkanki*. |
| web/templates/index.html:91-106 | Rimaykullayki · Significado "Hola" · Ejemplo "Hola, ¿cómo estás?" | Tarjeta inicial | CORRECTO/COHERENTE | Es la única versión con el significado correcto, y app.js la sobrescribe con "Rimaykullayki". |
| gemini_transcriber.py:274-276 | rimaykullayki, imaynalla kachkanki, allin p'unchay, yusulpayki, anchata munakuyki, puka, **yaku**, wasi | Pista al transcriptor | INCONSISTENTE | Enseña "yaku" (agua), mientras la BD dice "Uma". Usa p'unchay, mientras la BD dice punchay. |
| main_robot.py:826-833 | Mismo vocabulario + ari, mana, yaku | initial_prompt de Whisper | INCONSISTENTE | Igual que la fila anterior. |
| juego.py:103-110 | gato=**michi**, perro=**allqu**, sol=inti, agua=**yaku**, casa=wasi, árbol=**sacha** | Mapeo de emergencia (solo si la BD no responde) | INCONSISTENTE | Contradice la BD en 4 de 6 palabras: Misi, Allqo, Uma, Sach'a. En la BD, "sacha" es **venado**. "michi" es un hispanismo. |
| main_robot.py:405; app.js:15, 36-40 | Rimaykullayki | Texto por defecto en pantalla | CORRECTO/COHERENTE | |
| plataforma index.blade.php:218-224 | Mikhuna, Llimp'ikuna, Wasi, Sallqa Pacha, Ayllu, Llamk'anakuna, Marka | Etiquetas de categorías | REQUIERE REVISIÓN | *Marka* es de origen aimara (alternativa: *llaqta*). *Sallqa pacha* = puna o naturaleza silvestre: aceptable. |

---

## 7. Inconsistencias de grafía y variante

| Concepto | BD | Código / tarjetas / prompts | Comentario |
|---|---|---|---|
| Agua | **Uma** (naturales 2) | **yaku** (juego.py:107, gemini_transcriber.py:276, main_robot.py:833) | *uma* es "agua" en aimara; en quechua es "cabeza" (BD cuerpo 1). La propia app se contradice. |
| ¿Cómo estás? | Imaynalla | *kachkanki* (conversacion.py, app.js patrones, CARD title) frente a **kashanki** (web/app.py:22, app.js:21) | *kachkanki* es boliviana y *kashanki* sur peruana. |
| Buenos días | Allin **punchay** | Allin **p'unchay** (conversacion.py:26, gemini, whisper, web/app.py:26) | La BD pierde la glotal. Buscar "allin p'unchay" en la BD falla (verificado). No se usa *p'unchaw* en ninguna parte. |
| Perro | **Allqo** | **allqu** (juego.py:105) | e/o frente a norma de 3 vocales. |
| Gato | **Misi** | **michi** (juego.py:104) | Dos variantes coloquiales. Elegir una. |
| Árbol | **Sach'a** | **sacha** (juego.py:109) | En la BD, *Sacha* = venado (error). |
| Padre | **Tata** (hoy) / Tayta (respaldo) | tata (web/app.py:62) | Decisión del equipo coherente con Cochabamba. |
| Uso de e/o | Q'ello, Q'omer, Q'ello-puka, Qocha, Soqta (×4), isqon, Sonqo, Allqo | — | Formas normalizadas para revisar: q'illu, q'umir, qucha, suqta, isqun, sunqu, allqu. La misma BD usa *Urqu*, *Isqun* y *Qhichwa* (en el código) con la norma: **mezcla de dos sistemas**. |
| Glotales dudosas | K'uchara, K'uchillu (préstamos), K'ipi (q'ipi), P'anka (p'anqa), Huchuy (huch'uy), Ch'aki ñan (chaki) | — | Una glotal cambia el significado: *ch'aki* = seco, *chaki* = pie. |
| Préstamos sin adaptar | Plaza, Iglesia, Puente, Hospital, Jarra, Ají, Lapiz | — | Política no definida: préstamo adaptado (Platu, Vasu, Kawallu) o sin adaptar. "Puente" tiene palabra quechua (*chaka*). |
| Posibles aimarismos | Uma (agua), Marka (pueblo) | Marka (plataforma) | En quechua boliviano *marka* se usa, pero es de origen aimara. |
| Numeración | Chunka pusqayuq (18), Chunka isqonniyuq (19) | — | Rompen el patrón de la propia tabla (*qanchisniyuq*). |
| Nombre del idioma | — | "qhichwa" (presentación) frente a "quechua" (resto) | Aceptable, pero conviene documentarlo. |

---

## 8. Trazabilidad: contenido → BD → backend → pantalla/voz → usuario

| ID | Contenido | BD | Backend | Salida | Función para el usuario | Estado |
|---|---|---|---|---|---|---|
| YURA-TRZ-001 | Traducción es→qu | 15 tablas `nivelN_*` | `traductor.ejecutar_traducir` → `buscar_vocabulario` | Voz "En quechua se dice: X. {significado}" + pantalla "YURA DICE" | Modo traductor | 🟠 Funciona, pero entrega errores de contenido; 4 palabras con ñ inalcanzables |
| YURA-TRZ-002 | Significado qu→es | idem | `conversacion._responder_consulta_local(...,"quechua")` | Voz | "¿Qué significa…?" | 🟠 42 filas inalcanzables (apóstrofo o ñ) |
| YURA-TRZ-003 | Práctica | idem (187 filas) | `_comenzar_practica` / `_evaluar_respuesta` | Voz | "Enséñame / practicar" | 🟡 Alcanza todo, pero sin nivel ni orden y 45 filas sin significado |
| YURA-TRZ-004 | Juego | 6 filas | `Juego` + `consultar_diccionario_local` | Voz + pantalla (pregunta y resultado) | "Jugar" | 🔴 Enseña "agua = Uma" como respuesta correcta |
| YURA-TRZ-005 | Vocabulario para Groq | ≤40 filas + saludos | `vocabulario_relevante` | Voz (texto generado) | Conversación libre | 🟠 La restricción "usa solo esta lista" propaga los errores de la BD como "verificados" |
| YURA-TRZ-006 | `pronunciacion` (rutas mp3) | 187 filas | Leída en `traductor.py:124`, nunca usada | Ninguna | Ninguna | 🟡 Dato muerto; los archivos no existen |
| YURA-TRZ-007 | Nivel (nivel1/nivel2) | Nombre de tabla | Extraído (`traductor.py:125`), nunca usado | Ninguna | Ninguna (no hay progresión) | 🟡 |
| YURA-TRZ-008 | Tarjeta "EJEMPLO" | **Ninguna** (6 frases en `web/app.py`) | `/api/card` + `app.js normalizeExampleKey` | Pantalla | Mostrar escritura/pronunciación/significado | 🟠 Nunca refleja la palabra de la BD: cualquier otra palabra cae en "rimaykullayki" (app.js:73, :89). El regex `[A-Za-z0-9'\s]` (app.js:63) excluye ñ y tildes. "Significado" = quechua repetido. |
| YURA-TRZ-009 | Intentos y resultados (RF-05) | No existe tabla | `_set_game_event` solo en memoria | Pantalla momentánea | Seguimiento docente | 🔴 No se persiste nada; no hay `phonetic_evaluations` |
| YURA-TRZ-010 | Vocabulario de la plataforma (`robot_*`) | MySQL/SQLite de Laravel | Nadie lo lee | Ninguna | Ninguna | 🔴 Tablas huérfanas, sin quechua y sin enlace al robot |

**Contenido de la BD que nunca llega al usuario:** la columna `pronunciacion` completa; el nivel; el `significado` de las 42 palabras de §4 cuando se consulta en modo "qué significa"; y 4 filas en modo TRADUCIR (Urqu, Wawa, Manka michi, Huchuy).

**Funciones que necesitan datos que no existen:**
- La tarjeta necesita significado en español y pronunciación silabeada, y la BD no los tiene en ese formato.
- La práctica necesita `significado` en 4 tablas que no tienen la columna.
- El RF-05 necesita una tabla de intentos.
- Los saludos básicos del código (Rimaykullayki, Yusulpayki, Ari, Mana, Tupananchiskama, Imaynalla kachkanki) **no están en la BD**: "hola" y "gracias" no se encuentran en el diccionario (verificado); solo responden por reglas escritas a mano.

**Registros sin utilidad o que hacen daño:** familia 7 (duplica la fila 1); determinativos 3 (repite *Huk* = Uno, lo que genera una ambigüedad sin información); las 9 filas donde español = quechua; y las 26 filas POSIBLE ERROR, que enseñan un significado equivocado.

---

## 9. Matriz de pruebas

| ID | Módulo | Prueba | Entrada | Esperado | Obtenido | Estado | Evidencia |
|---|---|---|---|---|---|---|---|
| YURA-BD-001 | diccionario.db | Integridad física | `PRAGMA integrity_check` | ok | ok | 🟢 APROBADO | 01_volcado_bd.txt |
| YURA-BD-002 | diccionario.db | Codificación | `PRAGMA encoding`, NFC | UTF-8, NFC | UTF-8, NFC en todo | 🟢 APROBADO | 01_integridad_bd.txt |
| YURA-BD-003 | diccionario.db | Recuento de filas | 15 tablas | 187 | 187 | 🟢 APROBADO | 01_volcado_bd.txt |
| YURA-BD-004 | diccionario.db | Esquema homogéneo | `PRAGMA table_info` | 5 columnas en todas | 4 tablas sin `significado`; numeros sin AUTOINCREMENT y con `palabra_frase` NULL-able | 🟠 REQUIERE CORRECCIÓN | 01_volcado_bd.txt |
| YURA-BD-005 | diccionario.db | Índices y restricciones | `PRAGMA index_list` | Índice/UNIQUE en palabra_frase y traduccion | Ninguno | 🟡 OBSERVACIÓN | 01_integridad_bd.txt |
| YURA-BD-006 | diccionario.db | Duplicados de quechua | Normalización | 0 | 5 grupos (Uma, K'anchay, Tata, Huk, K'uchu) + 2 colisiones sin apóstrofo | 🟠 REQUIERE CORRECCIÓN | 01_integridad_bd.txt |
| YURA-BD-007 | diccionario.db | Huecos de ID | colores | Continuos o documentados | Faltan 3, 5, 6, 7, 9, 11 | 🟡 OBSERVACIÓN | 01_integridad_bd.txt |
| YURA-BD-008 | diccionario.db | Espacios, vacíos y apóstrofos | Todas las filas | Limpios; un solo apóstrofo | Limpios; solo `'` | 🟢 APROBADO | 01_integridad_bd.txt |
| YURA-BD-009 | diccionario.db | Rutas de `pronunciacion` | `os.path.exists` | Archivos existentes | 0/187; prefijos mezclados en colores | 🟠 REQUIERE CORRECCIÓN | 01_integridad_bd.txt |
| YURA-BD-010 | traductor | Uso de `pronunciacion` | grep | La usa alguna función | Ninguna | 🟡 OBSERVACIÓN | grep §3.4 |
| YURA-BD-011 | traductor | Fallback de `significado` | `_leer_registros_vocabulario` | Lee 187 sin error | 187; 45 con None | 🟢 APROBADO | 01_pruebas_funciones_bd.txt |
| YURA-BD-012 | diccionario.db | Diferencias con el respaldo | Comparación fila a fila | Solo cambios declarados | familia 1 Tayta→Tata; nueva familia 7 | 🟢 APROBADO (coincide con lo declarado) | 01_diff_respaldo.txt |
| YURA-BD-013 | Git | Versionado de la BD | `git check-ignore` | Versionada o con script de semilla | Ignorada por `*.db`; sin semilla | 🟠 REQUIERE CORRECCIÓN | 01_diff_respaldo.txt |
| YURA-BD-014 | main_robot/conversacion | Apertura en solo lectura | Código | `mode=ro` | RW en main_robot.py:577 y conversacion.py:182 | 🟡 OBSERVACIÓN | código |
| YURA-BD-015 | traductor (TRADUCIR) | Palabra con ñ | "niño", "montaña" | Wawa, Urqu | "No estoy seguro…" (normalizado "ni o") | 🔴 ERROR CRÍTICO | 01_pruebas_modo_traducir.txt |
| YURA-BD-016 | conversacion | "Qué significa" con apóstrofo o ñ | "que significa k'anchay", "…ñawi" | Luz/Brillante, Ojo | None (42 filas afectadas) | 🔴 ERROR CRÍTICO | 01_pruebas_funciones_bd.txt, 01_alcanzabilidad_y_estados.txt |
| YURA-BD-017 | traductor | Ambigüedad papa/papá | "papá" | Dos opciones | "Papa… se dice Papa; Papá… se dice Tata" | 🟢 APROBADO | 01_pruebas_modo_traducir.txt |
| YURA-BD-018 | traductor | Ambigüedad sin información | "uno" | Una respuesta | Dos opciones idénticas (Huk/Huk) | 🟡 OBSERVACIÓN | 01_pruebas_modo_traducir.txt |
| YURA-BD-019 | traductor | Búsqueda por subcadena | "mar" | "no encontrado" o pedir aclaración | Amarillo, Marrón, Martillo | 🟡 OBSERVACIÓN | 01_pruebas_modo_traducir.txt |
| YURA-BD-020 | traductor | Límite del prompt | `vocabulario_relevante("numeros")` | Saludos completos | 40 filas; "Allin tuta" queda fuera | 🟡 OBSERVACIÓN | 01_pruebas_funciones_bd.txt |
| YURA-BD-021 | conversacion | Práctica: universo | `_obtener_vocabulario_para_practica` | 187 | 187 | 🟢 APROBADO | 01_pruebas_funciones_bd.txt |
| YURA-BD-022 | conversacion | Naranja | "como se dice naranja" | Coherente con la BD | BD responde Q'ello-puka; el código conversacion.py:427 dice que no existe (muerto) | 🟡 OBSERVACIÓN | 01_pruebas_funciones_bd.txt |
| YURA-BD-023 | Plataforma | Sincronización robot↔web | grep | Código de sincronización | Inexistente | 🔴 ERROR CRÍTICO (frente a la tesis 7.4.3) | §5.1 |
| YURA-BD-024 | Plataforma | Tabla `phonetic_evaluations` (RF-05) | grep | Existe | No existe | 🔴 ERROR CRÍTICO | §5.2 |
| YURA-BD-025 | Plataforma | Contenido de `robot_*` | Migración + seeder | Quechua + español | Solo `name` en español | 🟠 REQUIERE CORRECCIÓN | §5.1 |
| YURA-BD-026 | Plataforma | Formulario modal de actividad | index.blade.php:190/217 frente a GradeController:458 | Mismo campo | `activity_category` frente a `category` | ⚫ NO VERIFICADO (estático: falla) | §5.1 |
| YURA-BD-027 | Tesis | 7.4.4 Esquema completo | PDF pág. 58 | Esquema | Sección vacía | 🟠 REQUIERE CORRECCIÓN | PDF |
| YURA-QCH-001 | Contenido | Agua | "como se dice agua" | yaku (quechua) | "Uma" (aimara) | 🔴 ERROR CRÍTICO | 01_pruebas_funciones_bd.txt |
| YURA-QCH-002 | Juego | Respuesta correcta de "agua" | `consultar_diccionario_local("agua")` | yaku | Uma | 🔴 ERROR CRÍTICO | 01_pruebas_funciones_bd.txt |
| YURA-QCH-003 | Contenido | Escuela | "escuela" | yachay wasi | T'anta wasi ("casa del pan") | 🔴 ERROR CRÍTICO | 01_pruebas_funciones_bd.txt |
| YURA-QCH-004 | Contenido | Partes del cuerpo | nariz, diente, espalda, mano, hueso | sinqa, kiru, wasa, maki, tullu | Sunkha, K'aki, K'uchu, Mak'a, K'ullu | 🔴 ERROR CRÍTICO (revisión de hablante) | Tabla §6.1 |
| YURA-QCH-005 | Contenido | Animales | venado, abeja, avispa, mono, luciérnaga | taruka, wanqullu/lachiwana, —, k'usillu, ninakuru | Sacha, Wanak'u (guanaco), Ch'iwchi (pollito), K'uchi, K'anchisapa | 🔴 ERROR CRÍTICO (revisión de hablante) | Tabla §6.1 |
| YURA-QCH-006 | Contenido | Números 18 y 19 | "dieciocho" | chunka pusaqniyuq | Chunka pusqayuq / isqonniyuq | 🟠 REQUIERE CORRECCIÓN | 01_pruebas_modo_traducir.txt |
| YURA-QCH-007 | Contenido | Adjetivos | caliente; kay | q'uñi; este | Q'uychi (arcoíris); "Aquí / Ahora" | 🟠 REQUIERE CORRECCIÓN | Tabla §6.1 |
| YURA-QCH-008 | Grafía | Norma de 3 vocales | Todas las filas | 0 con e/o (salvo préstamos) | 14 filas | 🟠 REQUIERE CORRECCIÓN | 01_integridad_bd.txt |
| YURA-QCH-009 | Consistencia | Buenos días BD↔código | "allin p'unchay" (quechua) | Encontrado | No encontrado (BD: "punchay") | 🟠 REQUIERE CORRECCIÓN | 01_pruebas_funciones_bd.txt |
| YURA-QCH-010 | Consistencia | ¿Cómo estás? | web/app.py:22, app.js:21 | kachkanki | kashanki | 🟠 REQUIERE CORRECCIÓN | §7 |
| YURA-QCH-011 | Consistencia | Juego de emergencia frente a BD | juego.py:103-110 | Igual que la BD | 4 de 6 distintas | 🟠 REQUIERE CORRECCIÓN | §7 |
| YURA-QCH-012 | Tarjeta | Significado | `/api/card` | Español | Repite el quechua | 🟠 REQUIERE CORRECCIÓN | web/app.py:21-61 |
| YURA-QCH-013 | Tarjeta | Pronunciación | "Imaynalla kachkanki" | I-may-na-lla kach-kan-ki | "I-ma-ya-lla ka-ch-kan-ki" | 🟠 REQUIERE CORRECCIÓN | web/app.py:60 |
| YURA-QCH-014 | Categorías | Clasificación | T'anta (naturales), Taqlla (lugares), T'anta manka (alimentos) | Categoría correcta | Mal clasificadas | 🟡 OBSERVACIÓN | Tabla §6.1 |
| YURA-QCH-015 | Contenido | Préstamos sin traducir | lugares y utensilios | Política definida | 9 filas español = quechua | 🟡 OBSERVACIÓN | 01_integridad_bd.txt |
| YURA-QCH-016 | Contenido | 32 REQUIERE REVISIÓN + 9 NO VERIFICADO | Tabla §6.1 | Validación por hablante | Pendiente | ⚫ NO VERIFICADO | Tabla §6.1 |

---

## 10. Problemas priorizados y propuesta de solución (no aplicada)

| # | Prioridad | Problema | Propuesta |
|---|---|---|---|
| P1 | **CRÍTICO** | 26 filas con posible error de significado que YURA enseña en voz alta: Uma=agua, T'anta wasi=escuela, Sunkha=nariz, K'aki=diente, K'uchu=espalda/mesa, Mak'a=mano, K'ullu=hueso, Q'uychi=caliente, Kay=aquí/ahora, Sacha=venado, Wanak'u=abeja, Ch'iwchi=avispa, K'uchi=mono, K'anka, Mullu, Ch'aki ñan, Ch'askañawi, Puente, Manka michi, Wachikuy, Ch'aki maqana, K'anchay rikhuy, T'anta manka, K'anchisapa, Chunka pusqayuq… | Congelar el uso pedagógico de esas filas (marcarlas o excluirlas) hasta que **un hablante o docente de quechua de Cochabamba** las valide. Usar las formas sugeridas del §6.1 solo como punto de partida de esa revisión, nunca como corrección directa. |
| P2 | **CRÍTICO** | Modo TRADUCIR no encuentra palabras españolas con ñ (`traductor.py:42`) | Usar `_normalizar_para_comparar` (que conserva la ñ) en `ejecutar_traducir`, o cambiar `_normalizar_texto` para conservar la ñ. Añadir una prueba con "niño" y "montaña". |
| P3 | **CRÍTICO** | "¿Qué significa…?" falla con apóstrofo o ñ (42 filas) por `conversacion._normalizar_texto` | Extraer el término sin destruir ñ ni apóstrofo, y en la búsqueda comparar ambas versiones normalizadas (con y sin apóstrofo), con desambiguación. Unificar las 3 funciones `_normalizar_texto`. |
| P4 | **CRÍTICO** (frente a la tesis) | No hay `phonetic_evaluations` ni persistencia de intentos (RF-05); no hay sincronización robot↔plataforma (7.4.3) | Definir una tabla de intentos (estudiante, palabra, transcripción, similitud, correcto, fecha) y un envío a `POST /api/v1/robot/activity` o a un endpoint nuevo; o bien corregir la tesis para declarar el alcance real. |
| P5 | ALTO | Contradicciones de grafía entre BD, código, tarjetas y prompts (Uma/yaku, punchay/p'unchay, kachkanki/kashanki, Allqo/allqu, Misi/michi, Sach'a/sacha) | Adoptar una sola fuente de verdad: generar prompts, mapeo del juego y tarjetas **desde la BD**. Eliminar el mapeo de emergencia o hacerlo idéntico a la BD. |
| P6 | ALTO | Grafía mixta e/o frente a a/i/u (14 filas) | Decidir la norma oficial boliviana de 3 vocales y documentarla. Normalizar las 14 filas tras la revisión del hablante. |
| P7 | ALTO | La BD no está versionada ni tiene semilla (`*.db` ignorado) | Versionar un `schema.sql` + `seed.sql` o CSV revisado, con un script para regenerar `diccionario.db`. |
| P8 | ALTO | Las tablas `robot_*` de la plataforma no tienen quechua, no se leen y no coinciden con las 15 categorías del robot; hay 3 listas de categorías distintas | Unificar un catálogo de categorías y palabras (tabla `vocabulary` con category_id, quechua, español, significado, audio, nivel) compartido o sincronizado. Arreglar el nombre de campo del modal (`activity_category` frente a `category`). |
| P9 | MEDIO | 5 duplicados de quechua y 2 colisiones sin apóstrofo; familia 7 duplica la 1 | Una fila por palabra con traducciones múltiples ("Padre / Papá"); restricción UNIQUE (categoría, palabra_frase). |
| P10 | MEDIO | 45 filas sin `significado` y esquema heterogéneo | Añadir `significado` a las 4 tablas (redactado por el docente) o migrar a una sola tabla `vocabulario` con columnas `nivel` y `categoria`. |
| P11 | MEDIO | `pronunciacion` = rutas de Windows inexistentes, nunca usadas, pero obligatorias en `traductor.py:87` | Renombrar a `audio_path`, poner rutas relativas reales o NULL, y no exigir la columna para cargar la tabla. |
| P12 | MEDIO | La tarjeta web no muestra palabras de la BD, "meaning" repite el quechua y los silabeos están mal | Servir la tarjeta desde la palabra actual de la BD (español + significado). Corregir el regex de app.js:63 para aceptar ñ y tildes. Revisar los silabeos con un hablante. |
| P13 | MEDIO | Categorías mal asignadas (T'anta, Taqlla, T'anta manka, Manka) y 9 filas sin traducir | Reclasificar y definir una política de préstamos (adaptado o sin adaptar). "Puente" → revisar *chaka*. |
| P14 | BAJO | El nivel (nivel1/nivel2) no se usa; la práctica es aleatoria sobre 187 palabras | Filtrar la práctica por nivel y categoría, y ofrecer progresión. |
| P15 | BAJO | Búsqueda por subcadena ("mar" → amarillo, marrón, martillo); el límite de 40 deja fuera saludos | Limitar la subcadena a palabras completas o a un prefijo mínimo; reservar espacio para los saludos. |
| P16 | BAJO | Conexiones RW innecesarias; huecos de ID en colores; convención de nombres de audio con/sin ñ | Abrir con `mode=ro`; documentar los borrados; unificar la convención de nombres. |
| P17 | BAJO | Código muerto "naranja no existe" (conversacion.py:427-431) | Eliminarlo o alinearlo con la BD. |
| P18 | BAJO | Frases de la plataforma en `lang/qu/messages.php` dudosas (`allinllachu`, `allinchay`, "estadon") | Revisión de hablante. |

> Nota final del auditor: nada de esta sección se ha aplicado. Todas las "formas sugeridas" deben pasar por un hablante o docente de quechua de Cochabamba antes de tocar la base de datos.
