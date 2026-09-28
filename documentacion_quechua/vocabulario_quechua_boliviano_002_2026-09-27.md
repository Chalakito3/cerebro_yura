# 1. Para qué sirve este documento

La tesis del proyecto (sección 5.4, *Límites del sistema*) dice que YURA trabajará **solo con ejercicios de vocabulario, pronunciación y comprensión básica del quechua**. Este documento reúne ese vocabulario básico **según la norma oficial boliviana** y lo compara con el diccionario que usa YURA (`diccionario.db`).

**Esta es la versión 2.** Revisa la versión 1 con el **Diccionario Bilingüe de Teófilo Laime Ajacopa** (La Paz, 2007), hecho para maestros de Educación Intercultural Bilingüe según las convenciones oficiales de Bolivia. Con él se confirmaron casi todas las palabras que en la versión 1 estaban pendientes, y se corrigieron algunos errores de esa versión (ver sección 13).

**Variante elegida por el equipo:** quechua boliviano (norma nacional).

**Cómo leer el estado de cada palabra:**

- 🟢 **Confirmada:** la palabra aparece con ese significado en al menos una fuente boliviana. Entre corchetes va la fuente: [LAIME], [DDE] o [PROEIB].
- ⚠️ **Las fuentes difieren:** dos fuentes bolivianas escriben la palabra distinto. El equipo debe elegir una.
- 🟡 **Sin fuente:** no se encontró en ninguna de las tres fuentes. Debe confirmarla un docente.

**Regla de este documento:** no se inventó ninguna palabra.

**Fuentes (sección 14):**

- **[LAIME]** T. Laime Ajacopa, *Diccionario Bilingüe Iskay simipi yuyayk'ancha, Quechua–Castellano / Castellano–Quechua*, 2.ª ed., La Paz, 2007.
- **[DDE]** Dirección Departamental de Educación de Chuquisaca, *El idioma quechua desde la sociolingüística y sus normas de escritura*. Aplica el alfabeto oficial (DS 20227 de 1984) y la **RM 599/2011** del Ministerio de Educación, obligatoria en todo el sistema educativo.
- **[PROEIB]** PROEIB Andes – Universidad Mayor de San Simón (Cochabamba, 2014), *Pautas para escribir el quechua normalizado*.

Las tres fuentes están en `documentacion_quechua/fuentes/`. Las búsquedas en el diccionario de Laime se pueden repetir con `documentacion_quechua/herramientas/buscar_laime.py`.

<<<PAGINA>>>

# 2. Normas oficiales de escritura

| Regla | Qué dice la norma | Ejemplo |
|---|---|---|
| Alfabeto | 28 letras: 25 consonantes y 3 vocales (DS 20227 de 1984) | a, i, u |
| Solo 3 vocales | Se escriben **a, i, u**. Junto a q, qh, q' se **pronuncian** e y o, pero **no se escriben** | se escribe **allqu**, se dice [alqo] |
| Aspiradas (con h) | chh, kh, ph, qh, th: se pronuncian soplando | **khuchi** (cerdo), **phuyu** (nube) |
| Glotales (con ') | ch', k', p', q', t': se pronuncian como una explosión | **t'ika** (flor), **p'acha** (ropa) |
| J al inicio | Se escribe la J aunque en algunas regiones no se pronuncie | **juk** (uno), **jisq'un** (nueve), **jatun** (grande) |
| LL antes de Q | Se escribe ll aunque suene l | **allqu** (perro), **qullqi** (plata, dinero) |
| M antes de P | En palabras raíz se escribe m | **pampa**, **jampi** (medicina) |
| Sufijo -chka- | Siempre se escribe -chka-, aunque se diga -sha-, -sa- o -ja- | **kachkanki** (se dice "kashanki") |
| Sufijo -chik | Siempre con k | **ñuqanchik**, **tupananchikkama** |
| Sin diptongos | u se escribe w; i se escribe y | **wawqi** (hermano), **raymi** (fiesta) |
| Pronunciación | Cada región pronuncia a su modo; **la escritura es una sola** | sinqa: [senqa] o [sinqa], se escribe **sinqa** |

**Palabras que cambian de significado por una letra** (importante para YURA):

| Palabra | Significado | Palabra parecida | Significado |
|---|---|---|---|
| kanka | asado | k'anka | gallo |
| chaki | pie | ch'aki | seco |
| sach'a | árbol | sacha | (no es venado) |
| k'uchu | rincón | kuchi / khuchi | cerdo |
| uma | cabeza | yaku, unu | agua |

<<<PAGINA>>>

# 3. Saludos y expresiones

| Quechua | Castellano | Estado |
|---|---|---|
| Imaynalla kachkanki? | ¿Cómo estás? | 🟢 [LAIME] |
| Allin p'unchaw / Allin p'unchay | Buenos días | ⚠️ Laime escribe "día" como **p'unchaw**; el proyecto y el uso común usan **p'unchay** |
| Allin sukha | Buenas tardes | 🟢 [LAIME] (sukha = tarde; allin = bueno) |
| Allin tuta | Buenas noches | 🟢 [LAIME] (tuta = noche) |
| Allinlla kachkani | Estoy bien | 🟡 |
| Napaykuy | Saludo, saludar | 🟢 [LAIME] |
| Rimaykullayki | Te saludo (saludo respetuoso) | 🟡 (no está en Laime) |
| Yusulpayki | Gracias | 🟡 (no está en Laime) |
| Aywa, aywariku | Adiós | 🟢 [LAIME] |
| Tupananchikkama | Hasta vernos | 🟡 (escritura -chik 🟢 [DDE]) |
| Arí | Sí | 🟢 [LAIME] |
| Mana | No | 🟢 [LAIME] |

# 4. Pronombres y palabras para preguntar

| Quechua | Castellano | Estado |
|---|---|---|
| Ñuqa | Yo | 🟢 [DDE] |
| Qam | Tú | 🟢 [DDE] |
| Pay | Él, ella | 🟢 [DDE] |
| Ñuqanchik | Nosotros (incluye a quien escucha) | 🟢 [DDE] |
| Ñuqayku | Nosotros (sin quien escucha) | 🟢 [DDE] |
| Qamkuna | Ustedes | 🟢 [DDE] |
| Paykuna | Ellos, ellas | 🟢 [DDE] |
| Kay | Este, esta, esto | 🟢 [LAIME] [DDE] |
| Chay | Ese, esa, eso | 🟢 [LAIME] [DDE] |
| Jaqay | Aquel, aquella | 🟢 [LAIME] [DDE] |
| Llapa, tukuy | Todo, todos | 🟢 [LAIME] |
| Wakin | Algunos | 🟢 [DDE] |
| Pi? | ¿Quién? | 🟢 [DDE] |
| Ima? | ¿Qué? | 🟢 [DDE] |
| May? | ¿Dónde? | 🟢 [DDE] |
| Mayqin? | ¿Cuál? | 🟢 [LAIME] [DDE] |
| Imayna? | ¿Cómo? | 🟢 [LAIME] |
| Jayk'aq? | ¿Cuándo? | 🟢 [DDE] |
| Machkha? | ¿Cuánto? | 🟢 [DDE] |

# 5. Números

| Quechua | Castellano | Estado |
|---|---|---|
| Juk | Uno | 🟢 [LAIME] [DDE] |
| Iskay | Dos | 🟢 [LAIME] [DDE] |
| Kimsa | Tres | 🟢 [LAIME] [DDE] |
| Tawa | Cuatro | 🟢 [LAIME] [DDE] |
| Phichqa / Pichqa | Cinco | ⚠️ Laime trae las dos (castellano→quechua: **phichqa**; quechua→castellano: **pichqa**); [DDE]: **phichqa** |
| Suqta | Seis | 🟢 [LAIME] |
| Qanchis | Siete | 🟢 [LAIME] |
| Pusaq | Ocho | 🟢 [LAIME] |
| Jisq'un | Nueve | 🟢 [LAIME] [DDE] |
| Chunka | Diez | 🟢 [LAIME] [DDE] |
| Chunka jukniyuq | Once | 🟢 [LAIME] |
| Chunka pusaqniyuq | Dieciocho | 🟢 [LAIME] |
| Iskay chunka | Veinte | 🟡 (se forma igual que los demás) |
| Pachak | Cien | 🟢 [LAIME] |
| Waranqa | Mil | 🟢 [LAIME] |

**Regla:** después de chunka va el número con **-yuq** si termina en vocal (chunka kimsayuq = 13) o **-niyuq** si termina en consonante (chunka qanchisniyuq = 17, chunka pusaqniyuq = 18).

# 6. Colores

| Quechua | Castellano | Estado |
|---|---|---|
| Puka | Rojo | 🟢 [LAIME] [PROEIB] |
| Q'illu | Amarillo | 🟢 [LAIME] |
| Q'umir | Verde | 🟢 [LAIME] |
| Anqas | Azul | 🟢 [LAIME] |
| Yuraq anqas | Celeste | 🟢 [LAIME] |
| Yuraq | Blanco | 🟢 [LAIME] [DDE] |
| Yana | Negro | 🟢 [LAIME] [DDE] |
| Ch'iqchi | Gris | 🟢 [LAIME] [PROEIB] |
| Uqi | Color plomo, gris | 🟢 [LAIME] |
| Ch'umpi | Marrón, castaño | 🟢 [LAIME] |
| Kulli | Morado | 🟢 [LAIME] |
| Willapi | Anaranjado | 🟢 [LAIME] |
| Quri | Oro | 🟢 [LAIME] |
| Qurichasqa | Dorado | 🟢 [LAIME] |
| Qullqi | Plata, dinero | 🟢 [LAIME] [DDE] |
| Llamkha | Rosado | ⚠️ Laime lo da para "rosado", pero en otra entrada dice que llamkha es "tacto" |

<<<PAGINA>>>

# 7. Familia y personas

| Quechua | Castellano | Estado |
|---|---|---|
| Tata, tayta | Padre, papá | 🟢 [LAIME] [DDE] |
| Mama | Madre, mamá | 🟢 [LAIME] [DDE] |
| Wawa | Bebé, niño pequeño | 🟢 [LAIME] |
| Irqi | Niño | 🟢 [LAIME] |
| Qhari wawa | Niño; hijo (de la mujer) | 🟢 [LAIME] [DDE] |
| Churi | Hijo (del hombre) | 🟢 [LAIME] |
| Wawqi | Hermano (del hombre) | 🟢 [LAIME] |
| Tura | Hermano (de la mujer) | 🟢 [LAIME] |
| Ñaña | Hermana (de la mujer) | 🟢 [LAIME] |
| Pana | Hermana (del hombre) | 🟢 [LAIME] |
| Jatun tata | Abuelo | 🟢 [LAIME] |
| Jatun mama | Abuela | 🟢 [LAIME] [DDE] |
| Qhari | Hombre, varón | 🟢 [LAIME] [DDE] |
| Warmi | Mujer | 🟢 [LAIME] [DDE] |
| Runa | Persona | 🟢 [LAIME] [DDE] |
| Imilla | Muchacha | 🟢 [LAIME] [DDE] |
| Yachachiq | Profesor, profesora | 🟢 [LAIME] [DDE] |
| Yachakuq | Estudiante | 🟢 [LAIME] [DDE] |

# 8. Partes del cuerpo

| Quechua | Castellano | Estado |
|---|---|---|
| Uma | Cabeza | 🟢 [LAIME] [DDE] |
| Uya | Cara | 🟢 [LAIME] [DDE] |
| Ñawi | Ojo | 🟢 [LAIME] [DDE] |
| Sinqa | Nariz | 🟢 [LAIME] [DDE] [PROEIB] |
| Simi | Boca | 🟢 [LAIME] [DDE] |
| Rinri, ninri | Oreja | 🟢 [LAIME] [DDE] |
| Kiru | Diente | 🟢 [LAIME] [DDE] [PROEIB] |
| Qallu | Lengua | 🟢 [LAIME] |
| Chukcha | Cabello | 🟢 [LAIME] [DDE] |
| Kunka | Cuello | 🟢 [LAIME] [DDE] |
| Wiksa | Estómago, barriga | 🟢 [LAIME] [DDE] |
| Sunqu | Corazón | 🟢 [LAIME] |
| Wasa | Espalda | 🟢 [LAIME] |
| Maki | Mano | 🟢 [LAIME] [DDE] |
| Ruk'ana | Dedo | 🟢 [LAIME] |
| Chaki | Pie | 🟢 [LAIME] |
| Takillpa | Talón | 🟢 [LAIME] |
| T'usu | Pantorrilla | 🟢 [LAIME] |
| Tullu | Hueso | 🟢 [LAIME] [DDE] |
| Aycha | Carne | 🟢 [LAIME] [DDE] |

# 9. Animales

| Quechua | Castellano | Estado |
|---|---|---|
| Allqu | Perro | 🟢 [LAIME] [DDE] |
| Misi, michi | Gato | 🟢 [LAIME] [DDE] |
| Usqullu | Gato montés | 🟢 [LAIME] |
| Waka | Vaca | 🟢 [LAIME] [DDE] |
| Khuchi | Cerdo, chancho | 🟢 [LAIME] [DDE] |
| Uwija | Oveja | 🟢 [LAIME] [DDE] |
| Wallpa | Gallina | 🟢 [LAIME] [DDE] |
| K'anka | Gallo | 🟢 [LAIME] [DDE] |
| Pili / Pilli | Pato | ⚠️ [LAIME]: **pili**; [DDE]: **pilli** |
| Wallata | Ganso andino | 🟢 [LAIME] |
| Quwi | Cuy / conejo | ⚠️ [LAIME]: "conejo"; [DDE]: "coneja". En Bolivia se usa para el cuy |
| Kututu | Cuy macho | 🟢 [LAIME] [DDE] |
| K'usillu | Mono | 🟢 [LAIME] [DDE] |
| K'alla / Q'alachu | Loro | ⚠️ [LAIME]: **k'alla**, q'ichichi, uritu; [DDE]: **q'alachu** |
| Juku | Búho | 🟢 [LAIME] [DDE] |
| Yuthu | Perdiz | 🟢 [LAIME] [DDE] |
| Anka | Águila | 🟢 [LAIME] [DDE] |
| Kuntur | Cóndor | 🟢 [LAIME] |
| Atuq | Zorro | 🟢 [LAIME] |
| Taruka | Venado | 🟢 [LAIME] |
| Ukuku | Oso | 🟢 [LAIME] |
| Juk'ucha | Ratón | 🟢 [LAIME] |
| Challwa / Chawlla | Pez | ⚠️ [LAIME]: **challwa**; [DDE]: **chawlla** |
| Jamp'atu | Sapo | 🟢 [LAIME] |
| Amaru | Serpiente | 🟢 [LAIME] |
| Araranka | Lagarto | 🟢 [LAIME] |
| Qaraywa | Lagartija | 🟢 [LAIME] |
| Pillpintu | Mariposa | 🟢 [LAIME] |
| Wara | Abeja | 🟢 [LAIME] |
| Lachiwana | Avispa | 🟢 [LAIME] |
| Ninanina | Luciérnaga | 🟢 [LAIME] |
| Ch'uspi | Mosca | 🟢 [LAIME] [DDE] |
| Khuru | Gusano | 🟢 [LAIME] [DDE] |
| Llama | Llama | 🟡 (no se encontró la entrada) |

<<<PAGINA>>>

# 10. Comida y naturaleza

**Comida y bebida**

| Quechua | Castellano | Estado |
|---|---|---|
| Mikhuna | Comida | 🟢 [LAIME] |
| Mikhuy | Comer | 🟢 [LAIME] [DDE] |
| Upyay | Beber | 🟢 [LAIME] [DDE] |
| T'anta | Pan | 🟢 [LAIME] [DDE] |
| Sara | Maíz | 🟢 [LAIME] [DDE] |
| Jamk'a | Maíz tostado | 🟢 [LAIME] |
| Papa | Papa | 🟢 [LAIME] [DDE] |
| Runtu | Huevo | 🟢 [LAIME] [DDE] |
| Kanka | Asado, carne asada | 🟢 [LAIME] [DDE] |
| Misk'i | Dulce; miel | 🟢 [LAIME] [DDE] |
| Uchu | Ají | 🟢 [LAIME] |
| Api | Mazamorra de maíz | 🟢 [LAIME] |
| Aqha | Chicha | 🟢 [LAIME] |
| Yaku, unu | Agua | 🟢 [LAIME] (las dos palabras); [DDE] da unu como "líquido" |

**Naturaleza**

| Quechua | Castellano | Estado |
|---|---|---|
| Inti | Sol | 🟢 [LAIME] [DDE] |
| Killa | Luna; mes | 🟢 [LAIME] |
| Quyllur | Estrella | 🟢 [LAIME] |
| Ch'aska | Lucero | 🟢 [LAIME] |
| Janaqpacha | Cielo | 🟢 [LAIME] |
| Phuyu | Nube | 🟢 [LAIME] [DDE] |
| Para | Lluvia | 🟢 [LAIME] [DDE] |
| Wayra | Viento | 🟢 [LAIME] [DDE] |
| Nina | Fuego | 🟢 [LAIME] [DDE] |
| K'anchay | Luz | 🟢 [LAIME] |
| Jallp'a | Tierra | 🟢 [LAIME] |
| Rumi | Piedra | 🟢 [LAIME] [DDE] |
| Qucha | Lago, laguna | 🟢 [LAIME] [DDE] |
| Mayu | Río | 🟢 [LAIME] |
| Urqu | Cerro | 🟢 [LAIME] |
| Pampa | Campo, llanura | 🟢 [LAIME] [DDE] |
| Ñan | Camino | 🟢 [LAIME] [PROEIB] |
| Sach'a | Árbol | 🟢 [LAIME] |
| T'ika | Flor | 🟢 [LAIME] [DDE] |
| Muya, inkill | Jardín | 🟢 [LAIME] |
| K'aspi | Palo | 🟢 [LAIME] [DDE] |

# 11. Casa, escuela y lugares

| Quechua | Castellano | Estado |
|---|---|---|
| Wasi | Casa | 🟢 [LAIME] [DDE] |
| Punku | Puerta | 🟢 [LAIME] |
| Wayrana / Qhawana | Ventana | 🟢 [LAIME] (qhawana también es "mirador") |
| Manka | Olla | 🟢 [LAIME] |
| Chuwa | Plato | 🟢 [LAIME] [DDE] |
| Qiru | Vaso (de cerámica) | 🟢 [LAIME] |
| Q'uncha | Fogón | 🟢 [LAIME] [DDE] |
| P'ukuru | Horno | 🟢 [LAIME] |
| Wayaqa | Bolsa | 🟢 [LAIME] |
| P'acha | Ropa | 🟢 [LAIME] [DDE] |
| Yachay wasi / Yachaywasi | Escuela | ⚠️ [LAIME]: dos palabras; [DDE]: una palabra |
| Yachaqana wasi | Aula | 🟢 [DDE] |
| Jamp'ara | Mesa | 🟢 [LAIME] [DDE] |
| Tiyana | Silla | 🟢 [LAIME] [DDE] |
| P'anqa | Libro | 🟢 [LAIME] [DDE] |
| Qillqana | Lápiz; lugar para escribir | 🟢 [DDE] lápiz; [LAIME] escritorio |
| Tinta qillqana | Bolígrafo | 🟢 [DDE] |
| Maru | Pizarra | 🟢 [LAIME] |
| Llaqta | Pueblo, ciudad | 🟢 [LAIME] [DDE] |
| Kancha | Plaza, espacio cercado | 🟢 [LAIME] |
| Qhatu | Mercado | 🟢 [LAIME] [DDE] |
| Chaka | Puente | 🟢 [LAIME] |
| Jampina wasi | Hospital | 🟢 [LAIME] |
| Qhawana | Mirador | 🟢 [LAIME] |
| Ruwalla | Herramienta | 🟢 [LAIME] |
| Takana | Martillo | 🟢 [LAIME] |
| Ayri | Hacha | 🟢 [LAIME] |
| Lampa | Pala | 🟢 [LAIME] |
| Yawrilla | Aguja | 🟢 [LAIME] (yawri = aguja grande para costales) |

# 12. Adjetivos y verbos básicos

| Quechua | Castellano | Estado |
|---|---|---|
| Allin | Bueno; bien | 🟢 [LAIME] |
| Saqra | Malo | 🟢 [LAIME] [DDE] |
| Jatun | Grande | 🟢 [LAIME] [DDE] |
| Juch'uy | Pequeño | 🟢 [LAIME] [DDE] |
| Sumaq, k'acha | Bonito, hermoso | 🟢 [LAIME] [DDE] |
| Millay | Feo | 🟢 [LAIME] [DDE] |
| Wira | Gordo | 🟢 [LAIME] [DDE] |
| Tullu | Flaco | 🟢 [LAIME] [DDE] |
| Kusisqa | Alegre | 🟢 [LAIME] [DDE] |
| Q'uñi | Caliente | 🟢 [LAIME] |
| Chiri | Frío | 🟢 [LAIME] |
| Musuq | Nuevo | 🟢 [LAIME] |
| Machu | Viejo | 🟢 [LAIME] |
| K'anchaq | Brillante | 🟢 [LAIME] |
| Ayphu | Opaco | 🟢 [LAIME] |

| Quechua | Castellano | Quechua | Castellano |
|---|---|---|---|
| Puñuy | Dormir | Asiy | Reír |
| Puriy | Caminar | Takiy | Cantar |
| Parlay | Hablar | Kichay | Abrir |
| Uyariy | Escuchar | Phinkiy | Saltar |
| Wayk'uy | Cocinar | Samay | Descansar |
| Riqsiy | Conocer | Yachay | Saber |
| Yupay | Contar | Waqay | Llorar |
| Llamk'ay | Trabajar | Tarpuy | Sembrar |
| Pukllay | Jugar | Munay | Querer |

Verbos: 🟢 [DDE].

<<<PAGINA>>>

# 13. Qué cambió respecto de la versión 1

La versión 1 tenía errores que el diccionario de Laime corrige:

| Palabra | Versión 1 decía | Versión 2 (según Laime) |
|---|---|---|
| Luciérnaga | ninakuru 🟡 | **ninanina** 🟢 |
| Pez | proponía cambiar a chawlla | **challwa** es correcta según Laime ⚠️; no hace falta cambiarla |
| Tierra | allpa 🟡 | **jallp'a** 🟢 |
| Ratón | ukucha 🟡 | **juk'ucha** 🟢 |
| Aguja | yawri | **yawrilla**; yawri es la aguja grande para costales |
| Día | p'unchay | Laime escribe **p'unchaw** ⚠️ |
| Agua | "unu = líquido" (DDE) | Laime: **yaku y unu** significan los dos "agua" |
| Niño | qhari wawa | Laime: **irqi**; qhari wawa = hijo de la mujer |

Además, casi todas las palabras que la versión 1 marcaba 🟡 ahora están **confirmadas** por Laime.

# 14. Comparación con el diccionario de YURA

## 14.1 Ya corregidas (confirmadas)

| Castellano | Antes | Ahora | Fuente |
|---|---|---|---|
| Agua | Uma | **Yaku** ✅ | 🟢 [LAIME] [DDE]; uma = cabeza |
| Nariz | Sunkha | **Sinqa** ✅ | 🟢 [LAIME] [DDE] [PROEIB] |
| Diente | K'aki | **Kiru** ✅ | 🟢 [LAIME] [DDE] [PROEIB] |
| Padre / Papá | Tayta | **Tata** ✅ | 🟢 [LAIME] [DDE] (Laime acepta tata y tayta) |

## 14.2 Correcciones confirmadas por las fuentes (pendientes de tu aprobación)

| # | Castellano | Hoy dice | Propuesta | Fuente |
|---|---|---|---|---|
| 1 | Mano | Mak'a | **Maki** | 🟢 [LAIME] [DDE] |
| 2 | Hueso | K'ullu | **Tullu** | 🟢 [LAIME] [DDE]; k'ullu = madera |
| 3 | Corazón | Sonqo | **Sunqu** | 🟢 [LAIME] |
| 4 | Cabello | Akcha | **Chukcha** | 🟢 [LAIME] [DDE] |
| 5 | Espalda | K'uchu | **Wasa** | 🟢 [LAIME]; k'uchu = rincón |
| 6 | Dedos | Ruku maki | **Ruk'ana** | 🟢 [LAIME] |
| 7 | Talón | K'uchu chaki | **Takillpa** | 🟢 [LAIME] |
| 8 | Pantorrilla | Waqta chaki | **T'usu** | 🟢 [LAIME] |
| 9 | Perro | Allqo | **Allqu** | 🟢 [LAIME] [DDE] |
| 10 | Cerdo | Kuchi | **Khuchi** | 🟢 [LAIME] [DDE] |
| 11 | Mono | K'uchi | **K'usillu** | 🟢 [LAIME] [DDE] |
| 12 | Venado | Sacha | **Taruka** | 🟢 [LAIME] |
| 13 | Pato | Wallata | **Pili** | 🟢 [LAIME] (DDE: pilli); wallata = ganso andino |
| 14 | Luciérnaga | K'anchisapa | **Ninanina** | 🟢 [LAIME] |
| 15 | Abeja | Wanak'u | **Wara** | 🟢 [LAIME] |
| 16 | Avispa | Ch'iwchi | **Lachiwana** | 🟢 [LAIME] |
| 17 | Gato montés | Ch'ita | **Usqullu** | 🟢 [LAIME] |
| 18 | Lagarto | K'achi | **Araranka** | 🟢 [LAIME] |
| 19 | Ratón | Ukucha | **Juk'ucha** | 🟢 [LAIME] |
| 20 | Sapo | Hamp'atu | **Jamp'atu** | 🟢 [LAIME] |
| 21 | Amarillo | Q'ello | **Q'illu** | 🟢 [LAIME] |
| 22 | Verde | Q'omer | **Q'umir** | 🟢 [LAIME] |
| 23 | Naranja | Q'ello-puka | **Willapi** | 🟢 [LAIME] |
| 24 | Dorado | Quri | **Qurichasqa** (quri = oro) | 🟢 [LAIME] |
| 25 | Lago | Qocha | **Qucha** | 🟢 [LAIME] [DDE] |
| 26 | Nube | Puyu | **Phuyu** | 🟢 [LAIME] [DDE] |
| 27 | Cielo | Hanaq pacha | **Janaqpacha** | 🟢 [LAIME] |
| 28 | Jardín | T'ikari wasi | **Muya** | 🟢 [LAIME] |
| 29 | Carne asada | K'anka | **Kanka** | 🟢 [LAIME] [DDE]; k'anka = gallo |
| 30 | Maíz tostado | Mullu | **Jamk'a** | 🟢 [LAIME]; mullu = concha |
| 31 | Horno de barro | T'anta manka | **P'ukuru** | 🟢 [LAIME] |
| 32 | Ají | Ají | **Uchu** | 🟢 [LAIME] |
| 33 | Chicha | Chicha | **Aqha** | 🟢 [LAIME] |
| 34 | Herramienta | Llamk'ana | **Ruwalla** | 🟢 [LAIME] |
| 35 | Martillo de piedra | Rumi maqana | **Takana** (martillo) | 🟢 [LAIME] |
| 36 | Aguja | Wachikuy | **Yawrilla** | 🟢 [LAIME] |
| 37 | Pala | T'uksu | **Lampa** | 🟢 [LAIME] |
| 38 | Hacha | Ch'aki maqana | **Ayri** | 🟢 [LAIME] |
| 39 | Plaza | Plaza | **Kancha** | 🟢 [LAIME] |
| 40 | Pueblo | Marka | **Llaqta** | 🟢 [LAIME] [DDE]; marka es aymara |
| 41 | Puente | Puente | **Chaka** | 🟢 [LAIME] |
| 42 | Hospital | Hospital | **Jampina wasi** | 🟢 [LAIME] |
| 43 | Mirador | Ch'askañawi | **Qhawana** | 🟢 [LAIME] |
| 44 | Escuela | T'anta wasi | **Yachay wasi** | 🟢 [LAIME]; t'anta wasi = casa del pan |
| 45 | Aula | Yachay wasi | **Yachaqana wasi** | 🟢 [DDE] |
| 46 | Mesa | K'uchu | **Jamp'ara** | 🟢 [LAIME] [DDE] |
| 47 | Libro | Qillqa | **P'anqa** | 🟢 [LAIME] [DDE] |
| 48 | Bolígrafo | Lapiz qillqana | **Tinta qillqana** | 🟢 [DDE] |
| 49 | Pizarra | K'anchay rikhuy | **Maru** | 🟢 [LAIME] |
| 50 | Plato | Platu | **Chuwa** | 🟢 [LAIME] [DDE] |
| 51 | Vaso | Vasu | **Qiru** | 🟢 [LAIME] |
| 52 | Bolsa | Q'ipina | **Wayaqa** | 🟢 [LAIME] |
| 53 | Ventana | Windu | **Wayrana** | 🟢 [LAIME] |
| 54 | Grande | Hatun | **Jatun** | 🟢 [LAIME] [DDE] |
| 55 | Pequeño | Huchuy | **Juch'uy** | 🟢 [LAIME] [DDE] |
| 56 | Malo | Mana allin | **Saqra** | 🟢 [LAIME] [DDE] |
| 57 | Caliente | Q'uychi | **Q'uñi** | 🟢 [LAIME]; k'uychi = arcoíris |
| 58 | Brillante | K'anchay | **K'anchaq** | 🟢 [LAIME]; k'anchay = luz |
| 59 | Opaco | Ch'upi | **Ayphu** | 🟢 [LAIME] |
| 60 | Kay | significado "Aquí / Ahora" | **Este, esta, esto** | 🟢 [LAIME] [DDE] |
| 61 | Chay | significado "Ese / Aquel" | **Ese, esa, eso** | 🟢 [LAIME] [DDE] |
| 62 | Uno (determinativo) | Huk | **Juk** | 🟢 [LAIME] [DDE] |
| 63 | Niño | Wawa | **Irqi** (wawa = bebé) | 🟢 [LAIME] |
| 64 | Buenas tardes | Allin sukay | **Allin sukha** | 🟢 [LAIME] (sukha) |
| 65 | ¿Cómo estás? | Imaynalla | **Imaynalla kachkanki?** | 🟢 [LAIME] |
| 66 | Números con "Huk" (1, 11) | Huk, Chunka hukniyuq | **Juk, Chunka jukniyuq** | 🟢 [LAIME] |
| 67 | Números con "Soqta" (6, 16, 60, 600) | Soqta… | **Suqta…** | 🟢 [LAIME] |
| 68 | Números con "Isqun" (9, 19, 90, 900) | Isqun, Chunka isqonniyuq… | **Jisq'un, Chunka jisq'unniyuq…** | 🟢 [LAIME] [DDE] |
| 69 | Dieciocho | Chunka pusqayuq | **Chunka pusaqniyuq** | 🟢 [LAIME] |
| 70 | Mil | Waranka | **Waranqa** | 🟢 [LAIME] |

## 14.3 Decisiones que debe tomar el equipo (las fuentes difieren)

| # | Castellano | Hoy dice | Opción A | Opción B |
|---|---|---|---|---|
| 71 | Buenos días | Allin punchay | **Allin p'unchaw** (así escribe Laime "día") | **Allin p'unchay** (uso común; el resto del proyecto ya lo usa) |
| 72 | Cinco (y 15, 50, 500) | Pisqa… | **Phichqa…** ([DDE] y Laime castellano→quechua) | **Pichqa…** (Laime quechua→castellano) |
| 73 | Rosado | Qamya puka | **Llamkha** (Laime, con la contradicción de la sección 6) | Quitar la palabra |
| 74 | Pez | Challwa | Dejar **Challwa** ([LAIME]) | **Chawlla** ([DDE]) |

## 14.4 Palabras sin forma quechua encontrada (recomendación: quitarlas)

Iglesia, Jarra, K'uchara (cuchara), K'uchillu (cuchillo), T'ikari manka (sartén), K'uchuna (tijera), Waqta (espalda baja), Ruku chaki (dedos del pie), P'anka (cuaderno), K'ipi (mochila), Aswa (chicha dulce), Manka michi (olla pequeña).

No aparecen en ninguna de las tres fuentes y **no son vocabulario básico**. Lo más seguro para un robot que enseña es **quitarlas** hasta que un docente las confirme.

**Otro detalle:** *T'anta* (pan) está en la tabla de elementos naturales, y *Taqlla* (arado) en la de lugares. Las palabras son correctas, pero están en la **categoría equivocada**. Conviene moverlas a alimentos y herramientas.

<<<PAGINA>>>

# 15. Fuentes

1. Laime Ajacopa, Teófilo y otros (2007). *Diccionario Bilingüe Iskay simipi yuyayk'ancha, Quechua–Castellano / Castellano–Quechua*. 2.ª edición, La Paz, Bolivia. Presentación de Xavier Albó. Licencia Creative Commons. Copia en `documentacion_quechua/fuentes/`.
2. Dirección Departamental de Educación de Chuquisaca (2022). *El idioma quechua desde la sociolingüística y sus normas de escritura*. Basado en el DS 20227 (1984) y la RM 599/2011. https://web.ddechuquisaca.gob.bo/wp-content/uploads/2022/12/LENGUA-QUECHUA-rev-3-corregido-julio-27.pdf — copia en `documentacion_quechua/fuentes/`.
3. PROEIB Andes – Universidad Mayor de San Simón (2014). *Pautas para escribir el quechua normalizado*. Cochabamba. https://www.proeibandes.org/wp-content/uploads/2019/04/2Pautas-E-Q.pdf — copia en `documentacion_quechua/fuentes/`.

**Cómo se verificó:** las búsquedas en el diccionario de Laime se hicieron con `documentacion_quechua/herramientas/buscar_laime.py` y los resultados completos están en `laime_verificacion.txt` y `laime_verificacion_2.txt`, en la misma carpeta. Algunas entradas no se pudieron leer porque el texto del PDF viene cortado en ciertas páginas; en esos casos se buscó la palabra desde el lado castellano→quechua.

**Nota final:** este documento lo preparó un asistente de programación a partir de las fuentes indicadas. No reemplaza la revisión de un docente de quechua. Ninguna palabra del diccionario de YURA se cambia sin la aprobación del equipo.
