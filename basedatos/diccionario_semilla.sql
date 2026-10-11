-- Diccionario de Yura (quechua boliviano). Generado por basedatos/crear_diccionario.py
BEGIN TRANSACTION;
CREATE TABLE nivel1_alimentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    palabra_frase TEXT NOT NULL,
    pronunciacion TEXT,
    traduccion TEXT,
    significado TEXT
);
INSERT INTO "nivel1_alimentos" VALUES(1,'Mikhuna','C:/audios/nivel1/objetos/mikhuna.mp3','Comida','Alimento en general');
INSERT INTO "nivel1_alimentos" VALUES(2,'Aqha','C:/audios/nivel1/objetos/chicha.mp3','Chicha','Bebida tradicional de maíz fermentado');
INSERT INTO "nivel1_alimentos" VALUES(3,'Papa','C:/audios/nivel1/objetos/papa.mp3','Papa','Tubérculo andino');
INSERT INTO "nivel1_alimentos" VALUES(4,'Sara','C:/audios/nivel1/objetos/sara.mp3','Maíz','Cereal básico');
INSERT INTO "nivel1_alimentos" VALUES(5,'Api','C:/audios/nivel1/objetos/api.mp3','Api','Bebida de maíz morado');
INSERT INTO "nivel1_alimentos" VALUES(6,'Uchu','C:/audios/nivel1/objetos/aji.mp3','Ají','Condimento picante');
INSERT INTO "nivel1_alimentos" VALUES(7,'Kanka','C:/audios/nivel1/objetos/kanka.mp3','Carne asada','Alimento preparado');
INSERT INTO "nivel1_alimentos" VALUES(8,'Aswa','C:/audios/nivel1/objetos/aswa.mp3','Chicha dulce','Bebida tradicional');
INSERT INTO "nivel1_alimentos" VALUES(9,'Jamk''a','C:/audios/nivel1/objetos/mullu.mp3','Maíz tostado','Alimento típico');
INSERT INTO "nivel1_alimentos" VALUES(10,'P''ukuru','C:/audios/nivel1/objetos/tanta_manka.mp3','Horno de barro','Cavidad de barro donde se cuece el pan');
INSERT INTO "nivel1_alimentos" VALUES(11,'T''anta','C:/audios/nivel1/objetos/tanta.mp3','Pan','Alimento básico');
INSERT INTO "nivel1_alimentos" VALUES(12,'Runtu',NULL,'Huevo',NULL);
INSERT INTO "nivel1_alimentos" VALUES(13,'Misk''i',NULL,'Dulce','También: miel');
INSERT INTO "nivel1_alimentos" VALUES(14,'Unu',NULL,'Líquido',NULL);
CREATE TABLE nivel1_colores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    palabra_frase TEXT NOT NULL,
    pronunciacion TEXT,
    traduccion TEXT
, significado TEXT);
INSERT INTO "nivel1_colores" VALUES(1,'Puka','C:/audios/nivel1/colores/puka.mp3','Rojo',NULL);
INSERT INTO "nivel1_colores" VALUES(2,'Anqas','C:/audios/nivel1/colores/anqas.mp3','Azul',NULL);
INSERT INTO "nivel1_colores" VALUES(4,'Yuraq','C:/audios/nivel1/colores/yuraq.mp3','Blanco',NULL);
INSERT INTO "nivel1_colores" VALUES(8,'Q''illu','C:/audios/colores/qello.mp3','Amarillo',NULL);
INSERT INTO "nivel1_colores" VALUES(10,'Q''umir','C:/audios/colores/qomer.mp3','Verde',NULL);
INSERT INTO "nivel1_colores" VALUES(12,'Yana','C:/audios/colores/yana.mp3','Negro',NULL);
INSERT INTO "nivel1_colores" VALUES(13,'Uqi','C:/audios/colores/uqi.mp3','Gris',NULL);
INSERT INTO "nivel1_colores" VALUES(14,'Ch''umpi','C:/audios/colores/chumpi.mp3','Marrón / Café',NULL);
INSERT INTO "nivel1_colores" VALUES(15,'Kulli','C:/audios/colores/kulli.mp3','Morado / Violeta',NULL);
INSERT INTO "nivel1_colores" VALUES(16,'Willapi','C:/audios/colores/qello_puka.mp3','Naranja',NULL);
INSERT INTO "nivel1_colores" VALUES(17,'Qamya puka','C:/audios/colores/qamya_puka.mp3','Rosado',NULL);
INSERT INTO "nivel1_colores" VALUES(18,'Yuraq anqas','C:/audios/colores/yuraq_anqas.mp3','Celeste',NULL);
INSERT INTO "nivel1_colores" VALUES(19,'Qurichasqa','C:/audios/colores/quri.mp3','Dorado',NULL);
INSERT INTO "nivel1_colores" VALUES(20,'Qullqi','C:/audios/colores/qullqi.mp3','Plateado',NULL);
INSERT INTO "nivel1_colores" VALUES(21,'Llimp''i',NULL,'Color',NULL);
INSERT INTO "nivel1_colores" VALUES(22,'Quri',NULL,'Oro',NULL);
CREATE TABLE nivel1_dialogo_infantil (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                palabra_frase TEXT NOT NULL UNIQUE,
                pronunciacion TEXT,
                traduccion TEXT NOT NULL,
                significado TEXT
            );
INSERT INTO "nivel1_dialogo_infantil" VALUES(1,'Allillanmi','Allillanmi','Bien nomás','Respuesta afirmativa cortés a cómo estás (allillanchu)');
INSERT INTO "nivel1_dialogo_infantil" VALUES(2,'Kusisqam kani','Kusisqam kani','Estoy contento','Expresión de alegría del niño');
INSERT INTO "nivel1_dialogo_infantil" VALUES(3,'Imataq sutiyki','Imataq sutíyki','¿Cómo te llamas?','Pregunta básica para conocer el nombre');
INSERT INTO "nivel1_dialogo_infantil" VALUES(4,'Sutiymi','Sutíymi','Mi nombre es','Frase para presentarse');
INSERT INTO "nivel1_dialogo_infantil" VALUES(5,'Maymantataq kanki','Maymantataq kanki','¿De dónde eres?','Pregunta sobre procedencia o lugar de origen');
INSERT INTO "nivel1_dialogo_infantil" VALUES(6,'Mashkha watayuqtaq kanki','Mashkha watayoqtaq kanki','¿Cuántos años tienes?','Pregunta de edad escolar');
INSERT INTO "nivel1_dialogo_infantil" VALUES(7,'Munani','Munani','Quiero o me gusta','Expresión afirmativa de preferencia o deseo');
INSERT INTO "nivel1_dialogo_infantil" VALUES(8,'Mana munanichu','Mana munanichu','No quiero o no me gusta','Expresión negativa cortés');
INSERT INTO "nivel1_dialogo_infantil" VALUES(9,'Ama llakikuychu','Ama llakikúychu','No te preocupes','Frase de apoyo y consuelo afectuoso');
INSERT INTO "nivel1_dialogo_infantil" VALUES(10,'Kuska yachakusun','Kuska yachakusun','Juntos aprenderemos','Lema pedagógico de colaboración');
INSERT INTO "nivel1_dialogo_infantil" VALUES(11,'Allquchaymi kashan','Allqochaymi kashan','Tengo un perrito','Mascota cotidiana del estudiante');
INSERT INTO "nivel1_dialogo_infantil" VALUES(12,'Misichaymi kashan','Misichaymi kashan','Tengo un gatito','Mascota cotidiana del estudiante');
INSERT INTO "nivel1_dialogo_infantil" VALUES(13,'Chiri kashan','Chiri kashan','Hace frío','Expresión del clima andino');
INSERT INTO "nivel1_dialogo_infantil" VALUES(14,'Rupay kashan','Rupay kashan','Hace calor o sol','Expresión del clima soleado');
INSERT INTO "nivel1_dialogo_infantil" VALUES(15,'Yachaywasipi kani','Yachaywasipi kani','Estoy en la escuela','Espacio escolar de aprendizaje');
INSERT INTO "nivel1_dialogo_infantil" VALUES(16,'Mikhuyta munani','Mikhuyta munani','Quiero comer','Expresión infantil de necesidad');
INSERT INTO "nivel1_dialogo_infantil" VALUES(17,'Puñuyta munani','Puñuyta munani','Quiero dormir o descansar','Expresión infantil cotidiana');
INSERT INTO "nivel1_dialogo_infantil" VALUES(18,'Pukllayta munani','Pukllayta munani','Quiero jugar','Invitación lúdica al juego didáctico');
INSERT INTO "nivel1_dialogo_infantil" VALUES(19,'Sulpayki','Sulpayki','Gracias','Agradecimiento tradicional en quechua boliviano');
INSERT INTO "nivel1_dialogo_infantil" VALUES(20,'Tupananchiskama','Tupananchiskama','Hasta volver a encontrarnos','Despedida respetuosa y afectuosa');
INSERT INTO "nivel1_dialogo_infantil" VALUES(21,'Yurata wañuchikuy',NULL,'Yura, apágate','Orden por voz para apagar al robot Yura');
INSERT INTO "nivel1_dialogo_infantil" VALUES(22,'Parlapashanki',NULL,'Vas a estar hablando','Del verbo parlay (hablar) con sufijos de acción continuada (-pa-) y progresivo (-sha-), 2da persona (-nki)');
INSERT INTO "nivel1_dialogo_infantil" VALUES(23,'Llakisqam kani',NULL,'Estoy triste','Para decir cómo se siente.');
INSERT INTO "nivel1_dialogo_infantil" VALUES(24,'Sayk''usqam kani',NULL,'Estoy cansado','Para decir cómo se siente.');
INSERT INTO "nivel1_dialogo_infantil" VALUES(25,'Yarqhasqam kani',NULL,'Tengo hambre','Para pedir comida.');
INSERT INTO "nivel1_dialogo_infantil" VALUES(26,'Ch''akisqam kani',NULL,'Tengo sed','Para pedir agua.');
INSERT INTO "nivel1_dialogo_infantil" VALUES(27,'Unqusqam kani',NULL,'Estoy enfermo','Para avisar que se siente mal.');
INSERT INTO "nivel1_dialogo_infantil" VALUES(28,'Manchakuni',NULL,'Tengo miedo','Para decir que tiene miedo.');
INSERT INTO "nivel1_dialogo_infantil" VALUES(29,'Allillanmi, qamrí',NULL,'Bien nomás, ¿y tú?','Respuesta a cómo estás, devolviendo la pregunta.');
INSERT INTO "nivel1_dialogo_infantil" VALUES(30,'Yanapaway',NULL,'Ayúdame','Para pedir ayuda.');
INSERT INTO "nivel1_dialogo_infantil" VALUES(31,'Jamuy',NULL,'Ven','Invitación a acercarse.');
INSERT INTO "nivel1_dialogo_infantil" VALUES(32,'Tiyakuy',NULL,'Siéntate','Indicación en el aula.');
INSERT INTO "nivel1_dialogo_infantil" VALUES(33,'Uyariy',NULL,'Escucha','Indicación para prestar atención.');
INSERT INTO "nivel1_dialogo_infantil" VALUES(34,'Qhawariy',NULL,'Mira','Indicación para mirar algo.');
INSERT INTO "nivel1_dialogo_infantil" VALUES(35,'Pukllasun',NULL,'Juguemos','Invitación a jugar.');
INSERT INTO "nivel1_dialogo_infantil" VALUES(36,'Pukllasunchu',NULL,'¿Jugamos?','Pregunta para invitar a jugar.');
INSERT INTO "nivel1_dialogo_infantil" VALUES(37,'Takisun',NULL,'Cantemos','Invitación a cantar.');
INSERT INTO "nivel1_dialogo_infantil" VALUES(38,'Yupasun',NULL,'Contemos','Invitación a contar números.');
INSERT INTO "nivel1_dialogo_infantil" VALUES(39,'Qillqasun',NULL,'Escribamos','Invitación a escribir.');
INSERT INTO "nivel1_dialogo_infantil" VALUES(40,'Ancha allin',NULL,'Muy bien','Felicitación.');
INSERT INTO "nivel1_dialogo_infantil" VALUES(41,'Sumaqta ruwanki',NULL,'Lo haces muy bien','Felicitación por un trabajo.');
INSERT INTO "nivel1_dialogo_infantil" VALUES(42,'Kusa',NULL,'¡Qué bien!','Exclamación de alegría.');
INSERT INTO "nivel1_dialogo_infantil" VALUES(43,'Imatataq ruwashanki',NULL,'¿Qué estás haciendo?','Pregunta para conversar.');
INSERT INTO "nivel1_dialogo_infantil" VALUES(44,'Maypitaq tiyanki',NULL,'¿Dónde vives?','Pregunta para conocerse.');
INSERT INTO "nivel1_dialogo_infantil" VALUES(45,'Imatataq munanki',NULL,'¿Qué quieres?','Pregunta sobre deseos.');
INSERT INTO "nivel1_dialogo_infantil" VALUES(46,'Pitaq kay',NULL,'¿Quién es este?','Pregunta sobre una persona.');
INSERT INTO "nivel1_dialogo_infantil" VALUES(47,'Mamay',NULL,'Mamá, madre','Familia.');
INSERT INTO "nivel1_dialogo_infantil" VALUES(48,'Tatay',NULL,'Papá, padre','Familia.');
INSERT INTO "nivel1_dialogo_infantil" VALUES(49,'Wawqiy',NULL,'Hermano (de un varón)','Familia (hermano de un varón).');
INSERT INTO "nivel1_dialogo_infantil" VALUES(50,'Ñañay',NULL,'Hermana (de una mujer)','Familia (hermana de una mujer).');
INSERT INTO "nivel1_dialogo_infantil" VALUES(51,'Q''ayakama',NULL,'Hasta mañana','Despedida.');
INSERT INTO "nivel1_dialogo_infantil" VALUES(52,'Kunankama',NULL,'Hasta luego','Despedida.');
CREATE TABLE nivel1_elementos_casa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    palabra_frase TEXT NOT NULL,
    pronunciacion TEXT,
    traduccion TEXT,
    significado TEXT
);
INSERT INTO "nivel1_elementos_casa" VALUES(1,'Wasi','C:/audios/nivel1/objetos/wasi.mp3','Casa','Lugar de vivienda');
INSERT INTO "nivel1_elementos_casa" VALUES(2,'Punku','C:/audios/nivel1/objetos/punku.mp3','Puerta','Entrada de la casa');
INSERT INTO "nivel1_elementos_casa" VALUES(3,'Wayrana','C:/audios/nivel1/objetos/windu.mp3','Ventana','Abertura para luz y aire');
INSERT INTO "nivel1_elementos_casa" VALUES(4,'Manka','C:/audios/nivel1/objetos/manka.mp3','Olla','Recipiente para cocinar');
INSERT INTO "nivel1_elementos_casa" VALUES(5,'Q''uncha',NULL,'Fogón','Lugar de la cocina para hacer fuego');
INSERT INTO "nivel1_elementos_casa" VALUES(6,'P''acha',NULL,'Ropa',NULL);
CREATE TABLE nivel1_elementos_naturales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    palabra_frase TEXT NOT NULL,
    pronunciacion TEXT,
    traduccion TEXT,
    significado TEXT
);
INSERT INTO "nivel1_elementos_naturales" VALUES(2,'Yaku','C:/audios/nivel1/objetos/yaku.mp3','Agua','Elemento vital');
INSERT INTO "nivel1_elementos_naturales" VALUES(3,'K''anchay','C:/audios/nivel1/objetos/kanchay.mp3','Luz','Claridad del día o lámpara');
INSERT INTO "nivel1_elementos_naturales" VALUES(4,'Sach''a','C:/audios/nivel1/objetos/sacha.mp3','Árbol','Planta grande con tronco');
INSERT INTO "nivel1_elementos_naturales" VALUES(5,'Rumi','C:/audios/nivel1/objetos/rumi.mp3','Piedra','Elemento natural sólido');
INSERT INTO "nivel1_elementos_naturales" VALUES(6,'Inti','C:/audios/nivel1/objetos/inti.mp3','Sol','Astro que da luz');
INSERT INTO "nivel1_elementos_naturales" VALUES(7,'Killa','C:/audios/nivel1/objetos/killa.mp3','Luna','Astro nocturno');
INSERT INTO "nivel1_elementos_naturales" VALUES(8,'Phuyu','C:/audios/nivel1/objetos/puyu.mp3','Nube','Condensación de agua en el cielo');
INSERT INTO "nivel1_elementos_naturales" VALUES(9,'Janaqpacha','C:/audios/nivel1/objetos/hanaq_pacha.mp3','Cielo','Espacio sobre la tierra');
INSERT INTO "nivel1_elementos_naturales" VALUES(10,'Qucha','C:/audios/nivel1/objetos/qocha.mp3','Lago','Cuerpo de agua');
INSERT INTO "nivel1_elementos_naturales" VALUES(11,'Mayu','C:/audios/nivel1/objetos/mayu.mp3','Río','Corriente de agua');
INSERT INTO "nivel1_elementos_naturales" VALUES(12,'Urqu','C:/audios/nivel1/objetos/urqu.mp3','Montaña','Elevación natural');
INSERT INTO "nivel1_elementos_naturales" VALUES(13,'Ñan','C:/audios/nivel1/objetos/nan.mp3','Camino','Sendero o vía');
INSERT INTO "nivel1_elementos_naturales" VALUES(14,'Ch''aki ñan','C:/audios/nivel1/objetos/chaki_nan.mp3','Sendero','Camino pequeño');
INSERT INTO "nivel1_elementos_naturales" VALUES(15,'Muya','C:/audios/nivel1/objetos/tikari_wasi.mp3','Jardín','Lugar con plantas');
INSERT INTO "nivel1_elementos_naturales" VALUES(16,'Quyllur',NULL,'Estrella',NULL);
INSERT INTO "nivel1_elementos_naturales" VALUES(17,'Ch''aska',NULL,'Lucero','Estrella muy brillante');
INSERT INTO "nivel1_elementos_naturales" VALUES(18,'Para',NULL,'Lluvia',NULL);
INSERT INTO "nivel1_elementos_naturales" VALUES(19,'Wayra',NULL,'Viento',NULL);
INSERT INTO "nivel1_elementos_naturales" VALUES(20,'Nina',NULL,'Fuego',NULL);
INSERT INTO "nivel1_elementos_naturales" VALUES(21,'Jallp''a',NULL,'Tierra',NULL);
INSERT INTO "nivel1_elementos_naturales" VALUES(22,'Pampa',NULL,'Campo','Llanura');
INSERT INTO "nivel1_elementos_naturales" VALUES(23,'T''ika',NULL,'Flor',NULL);
INSERT INTO "nivel1_elementos_naturales" VALUES(24,'K''aspi',NULL,'Palo',NULL);
CREATE TABLE nivel1_familia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    palabra_frase TEXT NOT NULL,
    pronunciacion TEXT,
    traduccion TEXT
, significado TEXT);
INSERT INTO "nivel1_familia" VALUES(1,'Tata','C:/audios/nivel1/familia/tata.mp3','Padre',NULL);
INSERT INTO "nivel1_familia" VALUES(2,'Mama','C:/audios/nivel1/familia/mama.mp3','Madre',NULL);
INSERT INTO "nivel1_familia" VALUES(3,'Irqi','C:/audios/nivel1/familia/wawa.mp3','Niño',NULL);
INSERT INTO "nivel1_familia" VALUES(4,'Qhari','C:/audios/nivel1/familia/qhari.mp3','Hombre',NULL);
INSERT INTO "nivel1_familia" VALUES(5,'Warmi','C:/audios/nivel1/familia/warmi.mp3','Mujer',NULL);
INSERT INTO "nivel1_familia" VALUES(6,'Runa','C:/audios/nivel1/familia/runa.mp3','Persona',NULL);
INSERT INTO "nivel1_familia" VALUES(7,'Tata','C:/audios/nivel1/familia/tata.mp3','Papá',NULL);
INSERT INTO "nivel1_familia" VALUES(8,'Wawa',NULL,'Bebé','Niño pequeño');
INSERT INTO "nivel1_familia" VALUES(9,'Churi',NULL,'Hijo (del hombre)',NULL);
INSERT INTO "nivel1_familia" VALUES(10,'Qhari wawa',NULL,'Hijo (de la mujer)',NULL);
INSERT INTO "nivel1_familia" VALUES(11,'Wawqi',NULL,'Hermano (del hombre)',NULL);
INSERT INTO "nivel1_familia" VALUES(12,'Tura',NULL,'Hermano (de la mujer)',NULL);
INSERT INTO "nivel1_familia" VALUES(13,'Ñaña',NULL,'Hermana (de la mujer)',NULL);
INSERT INTO "nivel1_familia" VALUES(14,'Pana',NULL,'Hermana (del hombre)',NULL);
INSERT INTO "nivel1_familia" VALUES(15,'Jatun tata',NULL,'Abuelo',NULL);
INSERT INTO "nivel1_familia" VALUES(16,'Jatun mama',NULL,'Abuela',NULL);
INSERT INTO "nivel1_familia" VALUES(17,'Imilla',NULL,'Muchacha',NULL);
INSERT INTO "nivel1_familia" VALUES(18,'Yachachiq',NULL,'Profesor','Persona que enseña');
INSERT INTO "nivel1_familia" VALUES(19,'Yachakuq',NULL,'Estudiante','Persona que aprende');
CREATE TABLE nivel1_frutas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    palabra_frase TEXT NOT NULL,
    pronunciacion TEXT,
    traduccion TEXT,
    significado TEXT
);
INSERT INTO "nivel1_frutas" VALUES(1,'Ruru',NULL,'Fruta','Palabra genérica para fruta o fruto. También: wayu, puquy');
INSERT INTO "nivel1_frutas" VALUES(2,'Puquchi',NULL,'Plátano','También: banana');
INSERT INTO "nivel1_frutas" VALUES(3,'Rurasnu',NULL,'Durazno','Fruto del duraznero');
INSERT INTO "nivel1_frutas" VALUES(4,'Uwas',NULL,'Uva','Fruto de la vid');
INSERT INTO "nivel1_frutas" VALUES(5,'Achupalla',NULL,'Piña','También: ananá');
INSERT INTO "nivel1_frutas" VALUES(6,'Lukma',NULL,'Lúcuma','Fruto del lúcumo');
INSERT INTO "nivel1_frutas" VALUES(7,'Tintin',NULL,'Granadilla','Planta de la familia pasifloráceas');
INSERT INTO "nivel1_frutas" VALUES(8,'Chirimuya',NULL,'Chirimoya','Árbol frutal de la familia de las anonáceas');
CREATE TABLE nivel1_herramientas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    palabra_frase TEXT NOT NULL,
    pronunciacion TEXT,
    traduccion TEXT,
    significado TEXT
);
INSERT INTO "nivel1_herramientas" VALUES(1,'Ruwalla','C:/audios/nivel1/objetos/llamkana.mp3','Herramienta','Instrumento de trabajo');
INSERT INTO "nivel1_herramientas" VALUES(2,'Takana','C:/audios/nivel1/objetos/rumi_maqana.mp3','Martillo','Herramienta para golpear');
INSERT INTO "nivel1_herramientas" VALUES(3,'Yawrilla','C:/audios/nivel1/objetos/wachikuy.mp3','Aguja','Instrumento para coser');
INSERT INTO "nivel1_herramientas" VALUES(4,'Lampa','C:/audios/nivel1/objetos/tuksu.mp3','Pala','Herramienta para cavar');
INSERT INTO "nivel1_herramientas" VALUES(5,'Ayri','C:/audios/nivel1/objetos/chaki_maqana.mp3','Hacha','Herramienta para cortar madera');
INSERT INTO "nivel1_herramientas" VALUES(6,'Taqlla','C:/audios/nivel1/objetos/taqlla.mp3','Arado','Herramienta agrícola tradicional');
CREATE TABLE nivel1_lugares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    palabra_frase TEXT NOT NULL,
    pronunciacion TEXT,
    traduccion TEXT,
    significado TEXT
);
INSERT INTO "nivel1_lugares" VALUES(1,'Kancha','C:/audios/nivel1/objetos/plaza.mp3','Plaza','Lugar central de reunión');
INSERT INTO "nivel1_lugares" VALUES(2,'Llaqta','C:/audios/nivel1/objetos/marka.mp3','Pueblo','Comunidad pequeña');
INSERT INTO "nivel1_lugares" VALUES(3,'Iglesia','C:/audios/nivel1/objetos/iglesia.mp3','Iglesia','Lugar religioso');
INSERT INTO "nivel1_lugares" VALUES(4,'Qhatu','C:/audios/nivel1/objetos/qhatu.mp3','Mercado','Lugar de comercio');
INSERT INTO "nivel1_lugares" VALUES(5,'Chaka','C:/audios/nivel1/objetos/puente.mp3','Puente','Construcción para cruzar ríos');
INSERT INTO "nivel1_lugares" VALUES(6,'Jampina wasi','C:/audios/nivel1/objetos/hospital.mp3','Hospital','Centro de salud');
INSERT INTO "nivel1_lugares" VALUES(7,'Qhawana','C:/audios/nivel1/objetos/chaskañawi.mp3','Mirador','Lugar para observar paisajes');
CREATE TABLE nivel1_numeros (
    id INTEGER PRIMARY KEY,
    palabra_frase TEXT,
    pronunciacion TEXT,
    traduccion TEXT,
    significado TEXT
);
INSERT INTO "nivel1_numeros" VALUES(1,'Uj','C:/audios/nivel1/numeros/huk.mp3','Uno','Número uno (escritura normalizada: Juk)');
INSERT INTO "nivel1_numeros" VALUES(2,'Iskay','C:/audios/nivel1/numeros/iskay.mp3','Dos','Número dos');
INSERT INTO "nivel1_numeros" VALUES(3,'Kimsa','C:/audios/nivel1/numeros/kimsa.mp3','Tres','Número tres');
INSERT INTO "nivel1_numeros" VALUES(4,'Tawa','C:/audios/nivel1/numeros/tawa.mp3','Cuatro','Número cuatro');
INSERT INTO "nivel1_numeros" VALUES(5,'Phichqa','C:/audios/nivel1/numeros/pisqa.mp3','Cinco','Número cinco');
INSERT INTO "nivel1_numeros" VALUES(6,'Suqta','C:/audios/nivel1/numeros/soqta.mp3','Seis','Número seis');
INSERT INTO "nivel1_numeros" VALUES(7,'Qanchis','C:/audios/nivel1/numeros/qanchis.mp3','Siete','Número siete');
INSERT INTO "nivel1_numeros" VALUES(8,'Pusaq','C:/audios/nivel1/numeros/pusaq.mp3','Ocho','Número ocho');
INSERT INTO "nivel1_numeros" VALUES(9,'Jisq''un','C:/audios/nivel1/numeros/isqun.mp3','Nueve','Número nueve');
INSERT INTO "nivel1_numeros" VALUES(10,'Chunka','C:/audios/nivel1/numeros/chunka.mp3','Diez','Número diez');
INSERT INTO "nivel1_numeros" VALUES(11,'Chunka jukniyuq','C:/audios/nivel1/numeros/chunka_hukniyuq.mp3','Once','Diez con uno');
INSERT INTO "nivel1_numeros" VALUES(12,'Chunka iskayniyuq','C:/audios/nivel1/numeros/chunka_iskayniyuq.mp3','Doce','Diez con dos');
INSERT INTO "nivel1_numeros" VALUES(13,'Chunka kimsayuq','C:/audios/nivel1/numeros/chunka_kimsayuq.mp3','Trece','Diez con tres');
INSERT INTO "nivel1_numeros" VALUES(14,'Chunka tawayuq','C:/audios/nivel1/numeros/chunka_tawayuq.mp3','Catorce','Diez con cuatro');
INSERT INTO "nivel1_numeros" VALUES(15,'Chunka phichqayuq','C:/audios/nivel1/numeros/chunka_pisqayuq.mp3','Quince','Diez con cinco');
INSERT INTO "nivel1_numeros" VALUES(16,'Chunka suqtayuq','C:/audios/nivel1/numeros/chunka_soqtayuq.mp3','Dieciséis','Diez con seis');
INSERT INTO "nivel1_numeros" VALUES(17,'Chunka qanchisniyuq','C:/audios/nivel1/numeros/chunka_qanchisniyuq.mp3','Diecisiete','Diez con siete');
INSERT INTO "nivel1_numeros" VALUES(18,'Chunka pusaqniyuq','C:/audios/nivel1/numeros/chunka_pusqayuq.mp3','Dieciocho','Diez con ocho');
INSERT INTO "nivel1_numeros" VALUES(19,'Chunka jisq''unniyuq','C:/audios/nivel1/numeros/chunka_isqonniyuq.mp3','Diecinueve','Diez con nueve');
INSERT INTO "nivel1_numeros" VALUES(20,'Iskay chunka','C:/audios/nivel1/numeros/iskay_chunka.mp3','Veinte','Dos diez');
INSERT INTO "nivel1_numeros" VALUES(30,'Kimsa chunka','C:/audios/nivel1/numeros/kimsa_chunka.mp3','Treinta','Tres diez');
INSERT INTO "nivel1_numeros" VALUES(40,'Tawa chunka','C:/audios/nivel1/numeros/tawa_chunka.mp3','Cuarenta','Cuatro diez');
INSERT INTO "nivel1_numeros" VALUES(50,'Phichqa chunka','C:/audios/nivel1/numeros/pisqa_chunka.mp3','Cincuenta','Cinco diez');
INSERT INTO "nivel1_numeros" VALUES(60,'Suqta chunka','C:/audios/nivel1/numeros/soqta_chunka.mp3','Sesenta','Seis diez');
INSERT INTO "nivel1_numeros" VALUES(70,'Qanchis chunka','C:/audios/nivel1/numeros/qanchis_chunka.mp3','Setenta','Siete diez');
INSERT INTO "nivel1_numeros" VALUES(80,'Pusaq chunka','C:/audios/nivel1/numeros/pusaq_chunka.mp3','Ochenta','Ocho diez');
INSERT INTO "nivel1_numeros" VALUES(90,'Jisq''un chunka','C:/audios/nivel1/numeros/isqun_chunka.mp3','Noventa','Nueve diez');
INSERT INTO "nivel1_numeros" VALUES(100,'Pachak','C:/audios/nivel1/numeros/pachak.mp3','Cien','Número cien');
INSERT INTO "nivel1_numeros" VALUES(200,'Iskay pachak','C:/audios/nivel1/numeros/iskay_pachak.mp3','Doscientos','Dos cien');
INSERT INTO "nivel1_numeros" VALUES(300,'Kimsa pachak','C:/audios/nivel1/numeros/kimsa_pachak.mp3','Trescientos','Tres cien');
INSERT INTO "nivel1_numeros" VALUES(400,'Tawa pachak','C:/audios/nivel1/numeros/tawa_pachak.mp3','Cuatrocientos','Cuatro cien');
INSERT INTO "nivel1_numeros" VALUES(500,'Phichqa pachak','C:/audios/nivel1/numeros/pisqa_pachak.mp3','Quinientos','Cinco cien');
INSERT INTO "nivel1_numeros" VALUES(600,'Suqta pachak','C:/audios/nivel1/numeros/soqta_pachak.mp3','Seiscientos','Seis cien');
INSERT INTO "nivel1_numeros" VALUES(700,'Qanchis pachak','C:/audios/nivel1/numeros/qanchis_pachak.mp3','Setecientos','Siete cien');
INSERT INTO "nivel1_numeros" VALUES(800,'Pusaq pachak','C:/audios/nivel1/numeros/pusaq_pachak.mp3','Ochocientos','Ocho cien');
INSERT INTO "nivel1_numeros" VALUES(900,'Jisq''un pachak','C:/audios/nivel1/numeros/isqun_pachak.mp3','Novecientos','Nueve cien');
INSERT INTO "nivel1_numeros" VALUES(1000,'Waranqa','C:/audios/nivel1/numeros/waranka.mp3','Mil','Número mil');
CREATE TABLE nivel1_objetos_escolares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    palabra_frase TEXT NOT NULL,
    pronunciacion TEXT,
    traduccion TEXT,
    significado TEXT
);
INSERT INTO "nivel1_objetos_escolares" VALUES(1,'Yachaqana wasi','C:/audios/nivel1/objetos/yachay_wasi.mp3','Aula','Salón de clases');
INSERT INTO "nivel1_objetos_escolares" VALUES(2,'Yachay wasi','C:/audios/nivel1/objetos/tanta_wasi.mp3','Escuela','Lugar de aprendizaje');
INSERT INTO "nivel1_objetos_escolares" VALUES(3,'Qillqana','C:/audios/nivel1/objetos/qillqana.mp3','Lápiz','Instrumento para escribir');
INSERT INTO "nivel1_objetos_escolares" VALUES(4,'P''anqa','C:/audios/nivel1/objetos/qillqa.mp3','Libro','Texto para leer o escribir');
INSERT INTO "nivel1_objetos_escolares" VALUES(5,'P''anka','C:/audios/nivel1/objetos/panka.mp3','Cuaderno','Material escolar para escribir');
INSERT INTO "nivel1_objetos_escolares" VALUES(6,'K''ipi','C:/audios/nivel1/objetos/kipi.mp3','Mochila','Bolso escolar');
INSERT INTO "nivel1_objetos_escolares" VALUES(7,'Jamp''ara','C:/audios/nivel1/objetos/kuchu.mp3','Mesa','Mueble escolar');
INSERT INTO "nivel1_objetos_escolares" VALUES(8,'Tiyana','C:/audios/nivel1/objetos/tiyana.mp3','Silla','Mueble escolar');
INSERT INTO "nivel1_objetos_escolares" VALUES(9,'Maru','C:/audios/nivel1/objetos/kanchay_rikhuy.mp3','Pizarra','Superficie para escribir');
INSERT INTO "nivel1_objetos_escolares" VALUES(10,'Tinta qillqana','C:/audios/nivel1/objetos/lapiz_qillqana.mp3','Bolígrafo','Instrumento para escribir');
CREATE TABLE nivel1_partes_del_cuerpo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    palabra_frase TEXT NOT NULL,
    pronunciacion TEXT,
    traduccion TEXT
, significado TEXT);
INSERT INTO "nivel1_partes_del_cuerpo" VALUES(1,'Uma','C:/audios/nivel1/cuerpo/uma.mp3','Cabeza',NULL);
INSERT INTO "nivel1_partes_del_cuerpo" VALUES(2,'Ñawi','C:/audios/nivel1/cuerpo/ñawi.mp3','Ojo',NULL);
INSERT INTO "nivel1_partes_del_cuerpo" VALUES(3,'Simi','C:/audios/nivel1/cuerpo/simi.mp3','Boca',NULL);
INSERT INTO "nivel1_partes_del_cuerpo" VALUES(4,'Sinqa','C:/audios/nivel1/cuerpo/sinqa.mp3','Nariz',NULL);
INSERT INTO "nivel1_partes_del_cuerpo" VALUES(5,'Rinri','C:/audios/nivel1/cuerpo/rinri.mp3','Oreja',NULL);
INSERT INTO "nivel1_partes_del_cuerpo" VALUES(6,'Kiru','C:/audios/nivel1/cuerpo/kiru.mp3','Diente',NULL);
INSERT INTO "nivel1_partes_del_cuerpo" VALUES(7,'Qallu','C:/audios/nivel1/cuerpo/qallu.mp3','Lengua',NULL);
INSERT INTO "nivel1_partes_del_cuerpo" VALUES(8,'Wasa','C:/audios/nivel1/cuerpo/kuchu.mp3','Espalda',NULL);
INSERT INTO "nivel1_partes_del_cuerpo" VALUES(9,'Sunqu','C:/audios/nivel1/cuerpo/sonqo.mp3','Corazón',NULL);
INSERT INTO "nivel1_partes_del_cuerpo" VALUES(10,'Waqta','C:/audios/nivel1/cuerpo/waqta.mp3','Espalda baja',NULL);
INSERT INTO "nivel1_partes_del_cuerpo" VALUES(11,'Maki','C:/audios/nivel1/cuerpo/maka.mp3','Mano',NULL);
INSERT INTO "nivel1_partes_del_cuerpo" VALUES(12,'Ruk''ana','C:/audios/nivel1/cuerpo/ruku_maki.mp3','Dedo',NULL);
INSERT INTO "nivel1_partes_del_cuerpo" VALUES(13,'Chaki','C:/audios/nivel1/cuerpo/chaki.mp3','Pie',NULL);
INSERT INTO "nivel1_partes_del_cuerpo" VALUES(14,'Ruku chaki','C:/audios/nivel1/cuerpo/ruku_chaki.mp3','Dedos del pie',NULL);
INSERT INTO "nivel1_partes_del_cuerpo" VALUES(15,'Takillpa','C:/audios/nivel1/cuerpo/kuchu_chaki.mp3','Talón',NULL);
INSERT INTO "nivel1_partes_del_cuerpo" VALUES(16,'T''usu','C:/audios/nivel1/cuerpo/waqta_chaki.mp3','Pantorrilla',NULL);
INSERT INTO "nivel1_partes_del_cuerpo" VALUES(17,'Tullu','C:/audios/nivel1/cuerpo/kullu.mp3','Hueso',NULL);
INSERT INTO "nivel1_partes_del_cuerpo" VALUES(18,'Aycha','C:/audios/nivel1/cuerpo/aycha.mp3','Carne',NULL);
INSERT INTO "nivel1_partes_del_cuerpo" VALUES(19,'Chukcha','C:/audios/nivel1/cuerpo/akcha.mp3','Cabello',NULL);
INSERT INTO "nivel1_partes_del_cuerpo" VALUES(20,'Wira','C:/audios/nivel1/cuerpo/wira.mp3','Grasa corporal',NULL);
INSERT INTO "nivel1_partes_del_cuerpo" VALUES(21,'Uya',NULL,'Cara',NULL);
INSERT INTO "nivel1_partes_del_cuerpo" VALUES(22,'Kunka',NULL,'Cuello',NULL);
INSERT INTO "nivel1_partes_del_cuerpo" VALUES(23,'Wiksa',NULL,'Estómago',NULL);
CREATE TABLE nivel1_saludos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    palabra_frase TEXT NOT NULL,
    pronunciacion TEXT,
    traduccion TEXT
, significado TEXT);
INSERT INTO "nivel1_saludos" VALUES(1,'Allin p''unchay','C:/audios/nivel1/saludos/allin_punchay.mp3','Buenos días',NULL);
INSERT INTO "nivel1_saludos" VALUES(2,'Imaynalla kachkanki','C:/audios/nivel1/saludos/imaynalla.mp3','¿Cómo estás?',NULL);
INSERT INTO "nivel1_saludos" VALUES(3,'Allin sukha','C:/audios/nivel1/saludos/allin_sukay.mp3','Buenas tardes',NULL);
INSERT INTO "nivel1_saludos" VALUES(4,'Allin tuta','C:/audios/nivel1/saludos/allin_tuta.mp3','Buenas noches',NULL);
INSERT INTO "nivel1_saludos" VALUES(5,'Napaykuy',NULL,'Saludo','Fórmula de cortesía, respeto o afecto');
INSERT INTO "nivel1_saludos" VALUES(6,'Aywa',NULL,'Adiós','Despedida');
INSERT INTO "nivel1_saludos" VALUES(7,'Ari',NULL,'Sí','Afirmación');
INSERT INTO "nivel1_saludos" VALUES(8,'Mana',NULL,'No','Negación');
CREATE TABLE nivel1_utensilios_cocina (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    palabra_frase TEXT NOT NULL,
    pronunciacion TEXT,
    traduccion TEXT,
    significado TEXT
);
INSERT INTO "nivel1_utensilios_cocina" VALUES(1,'Chuwa','C:/audios/nivel1/objetos/platu.mp3','Plato','Utensilio para servir comida');
INSERT INTO "nivel1_utensilios_cocina" VALUES(2,'Qiru','C:/audios/nivel1/objetos/vasu.mp3','Vaso','Recipiente para beber');
INSERT INTO "nivel1_utensilios_cocina" VALUES(3,'K''uchara','C:/audios/nivel1/objetos/kuchara.mp3','Cuchara','Utensilio para comer');
INSERT INTO "nivel1_utensilios_cocina" VALUES(4,'T''ikari manka','C:/audios/nivel1/objetos/tikari_manka.mp3','Sartén','Utensilio para freír');
INSERT INTO "nivel1_utensilios_cocina" VALUES(5,'Jarra','C:/audios/nivel1/objetos/jarra.mp3','Jarra','Recipiente para líquidos');
INSERT INTO "nivel1_utensilios_cocina" VALUES(6,'K''uchillu','C:/audios/nivel1/objetos/kuchillu.mp3','Cuchillo','Utensilio de cocina');
INSERT INTO "nivel1_utensilios_cocina" VALUES(7,'Wayaqa','C:/audios/nivel1/objetos/qipina.mp3','Bolsa','Recipiente para alimentos');
INSERT INTO "nivel1_utensilios_cocina" VALUES(8,'Manka michi','C:/audios/nivel1/objetos/manka_michi.mp3','Olla pequeña','Utensilio de cocina');
INSERT INTO "nivel1_utensilios_cocina" VALUES(9,'K''uchuna','C:/audios/nivel1/objetos/kuchuna.mp3','Tijera','Utensilio para cortar');
CREATE TABLE nivel2_adjetivos_calificativos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    palabra_frase TEXT NOT NULL,
    pronunciacion TEXT,
    traduccion TEXT,
    significado TEXT
);
INSERT INTO "nivel2_adjetivos_calificativos" VALUES(1,'Allin','C:/audios/nivel2/adjetivos/allin.mp3','Bueno','Que es positivo o correcto');
INSERT INTO "nivel2_adjetivos_calificativos" VALUES(2,'Saqra','C:/audios/nivel2/adjetivos/mana_allin.mp3','Malo','Que es negativo o incorrecto');
INSERT INTO "nivel2_adjetivos_calificativos" VALUES(3,'Jatun','C:/audios/nivel2/adjetivos/hatun.mp3','Grande','De tamaño considerable');
INSERT INTO "nivel2_adjetivos_calificativos" VALUES(4,'Juch''uy','C:/audios/nivel2/adjetivos/huchuy.mp3','Pequeño','De tamaño reducido');
INSERT INTO "nivel2_adjetivos_calificativos" VALUES(5,'Sumaq','C:/audios/nivel2/adjetivos/sumaq.mp3','Bonito','Que es agradable a la vista');
INSERT INTO "nivel2_adjetivos_calificativos" VALUES(6,'Millay','C:/audios/nivel2/adjetivos/millay.mp3','Feo','Que no es agradable a la vista');
INSERT INTO "nivel2_adjetivos_calificativos" VALUES(7,'Chiri','C:/audios/nivel2/adjetivos/chiri.mp3','Frío','De baja temperatura');
INSERT INTO "nivel2_adjetivos_calificativos" VALUES(8,'Q''uñi','C:/audios/nivel2/adjetivos/quychi.mp3','Caliente','De alta temperatura');
INSERT INTO "nivel2_adjetivos_calificativos" VALUES(9,'Machu','C:/audios/nivel2/adjetivos/machu.mp3','Viejo','Que tiene mucha edad o antigüedad');
INSERT INTO "nivel2_adjetivos_calificativos" VALUES(10,'Musuq','C:/audios/nivel2/adjetivos/musuq.mp3','Nuevo','Que es reciente o no usado');
INSERT INTO "nivel2_adjetivos_calificativos" VALUES(11,'K''anchaq','C:/audios/nivel2/adjetivos/kanchay.mp3','Brillante','Que refleja luz intensamente');
INSERT INTO "nivel2_adjetivos_calificativos" VALUES(12,'Ayphu','C:/audios/nivel2/adjetivos/chupi.mp3','Opaco','Que no refleja luz, sin brillo');
INSERT INTO "nivel2_adjetivos_calificativos" VALUES(13,'K''acha',NULL,'Lindo','Bueno, hermoso');
INSERT INTO "nivel2_adjetivos_calificativos" VALUES(14,'Wira',NULL,'Gordo',NULL);
INSERT INTO "nivel2_adjetivos_calificativos" VALUES(15,'Tullu',NULL,'Flaco',NULL);
INSERT INTO "nivel2_adjetivos_calificativos" VALUES(16,'Kusisqa',NULL,'Alegre',NULL);
CREATE TABLE nivel2_adjetivos_determinativos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    palabra_frase TEXT NOT NULL,
    pronunciacion TEXT,
    traduccion TEXT,
    significado TEXT
);
INSERT INTO "nivel2_adjetivos_determinativos" VALUES(1,'Kay','C:/audios/nivel2/adjetivos/kay.mp3','Este / Esta / Esto','Indica algo cercano a quien habla');
INSERT INTO "nivel2_adjetivos_determinativos" VALUES(2,'Chay','C:/audios/nivel2/adjetivos/chay.mp3','Ese / Esa / Eso','Indica algo cercano a quien escucha');
INSERT INTO "nivel2_adjetivos_determinativos" VALUES(3,'Uj','C:/audios/nivel2/adjetivos/huk.mp3','Uno','Indica unidad o singularidad (escritura normalizada: Juk)');
INSERT INTO "nivel2_adjetivos_determinativos" VALUES(4,'Llapa','C:/audios/nivel2/adjetivos/llapa.mp3','Todo','Indica totalidad o conjunto completo');
INSERT INTO "nivel2_adjetivos_determinativos" VALUES(5,'Mayqin','C:/audios/nivel2/adjetivos/mayqin.mp3','Cuál','Indica selección o identificación');
INSERT INTO "nivel2_adjetivos_determinativos" VALUES(6,'Imayna','C:/audios/nivel2/adjetivos/imayna.mp3','Cómo','Indica modo o manera');
INSERT INTO "nivel2_adjetivos_determinativos" VALUES(7,'Jaqay',NULL,'Aquel / Aquella','Indica algo lejano');
INSERT INTO "nivel2_adjetivos_determinativos" VALUES(8,'Wakin',NULL,'Algunos',NULL);
INSERT INTO "nivel2_adjetivos_determinativos" VALUES(9,'Tukuy',NULL,'Todos',NULL);
CREATE TABLE nivel2_animales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    palabra_frase TEXT NOT NULL,
    pronunciacion TEXT,
    traduccion TEXT,
    significado TEXT
);
INSERT INTO "nivel2_animales" VALUES(1,'Allqu','C:/audios/nivel2/animales/allqo.mp3','Perro','Animal doméstico común');
INSERT INTO "nivel2_animales" VALUES(2,'Misi','C:/audios/nivel2/animales/misi.mp3','Gato','Animal doméstico');
INSERT INTO "nivel2_animales" VALUES(3,'Kawallu','C:/audios/nivel2/animales/kawallu.mp3','Caballo','Animal de carga');
INSERT INTO "nivel2_animales" VALUES(4,'Asnu','C:/audios/nivel2/animales/asnu.mp3','Burro','Animal de carga');
INSERT INTO "nivel2_animales" VALUES(5,'Waka','C:/audios/nivel2/animales/waka.mp3','Vaca','Animal de ganado vacuno');
INSERT INTO "nivel2_animales" VALUES(6,'Khuchi','C:/audios/nivel2/animales/kuchi.mp3','Cerdo','Animal doméstico de granja');
INSERT INTO "nivel2_animales" VALUES(7,'Wallpa','C:/audios/nivel2/animales/wallpa.mp3','Gallina','Ave doméstica');
INSERT INTO "nivel2_animales" VALUES(8,'Pilli','C:/audios/nivel2/animales/wallata.mp3','Pato','Ave acuática');
INSERT INTO "nivel2_animales" VALUES(9,'Quwi','C:/audios/nivel2/animales/kuy.mp3','Cuy','Roedor doméstico andino');
INSERT INTO "nivel2_animales" VALUES(10,'Llama','C:/audios/nivel2/animales/llama.mp3','Llama','Camélido andino usado como carga');
INSERT INTO "nivel2_animales" VALUES(11,'Alpaka','C:/audios/nivel2/animales/alpaka.mp3','Alpaca','Camélido andino productor de lana');
INSERT INTO "nivel2_animales" VALUES(12,'Kuntur','C:/audios/nivel2/animales/kuntur.mp3','Cóndor','Ave rapaz de gran tamaño');
INSERT INTO "nivel2_animales" VALUES(13,'Atuq','C:/audios/nivel2/animales/atuq.mp3','Zorro','Mamífero carnívoro de los Andes');
INSERT INTO "nivel2_animales" VALUES(14,'Taruka','C:/audios/nivel2/animales/sacha.mp3','Venado','Mamífero herbívoro de los bosques');
INSERT INTO "nivel2_animales" VALUES(15,'Ukuku','C:/audios/nivel2/animales/ukuku.mp3','Oso andino','Mamífero de montaña');
INSERT INTO "nivel2_animales" VALUES(16,'Usqullu','C:/audios/nivel2/animales/chita.mp3','Gato montés','Felino silvestre de los Andes');
INSERT INTO "nivel2_animales" VALUES(17,'Jamp''atu','C:/audios/nivel2/animales/hampatu.mp3','Sapo','Anfibio común en zonas húmedas');
INSERT INTO "nivel2_animales" VALUES(18,'Pillpintu','C:/audios/nivel2/animales/pillpintu.mp3','Mariposa','Insecto volador de colores');
INSERT INTO "nivel2_animales" VALUES(19,'Ninanina','C:/audios/nivel2/animales/kanchisapa.mp3','Luciérnaga','Insecto que emite luz');
INSERT INTO "nivel2_animales" VALUES(20,'Wara','C:/audios/nivel2/animales/wanaku.mp3','Abeja','Insecto productor de miel');
INSERT INTO "nivel2_animales" VALUES(21,'Lachiwana','C:/audios/nivel2/animales/chiwchi.mp3','Avispa','Insecto volador con aguijón');
INSERT INTO "nivel2_animales" VALUES(22,'Chawlla','C:/audios/nivel2/animales/challwa.mp3','Pez','Animal acuático');
INSERT INTO "nivel2_animales" VALUES(23,'Amaru','C:/audios/nivel2/animales/amaru.mp3','Serpiente','Reptil de cuerpo alargado');
INSERT INTO "nivel2_animales" VALUES(24,'Araranka','C:/audios/nivel2/animales/kachi.mp3','Lagarto','Reptil de cuerpo pequeño');
INSERT INTO "nivel2_animales" VALUES(25,'Juk''ucha','C:/audios/nivel2/animales/ukucha.mp3','Ratón','Roedor pequeño');
INSERT INTO "nivel2_animales" VALUES(26,'K''usillu','C:/audios/nivel2/animales/kuchi_mono.mp3','Mono','Mamífero amazónico');
INSERT INTO "nivel2_animales" VALUES(27,'Uwija',NULL,'Oveja',NULL);
INSERT INTO "nivel2_animales" VALUES(28,'K''anka',NULL,'Gallo',NULL);
INSERT INTO "nivel2_animales" VALUES(29,'Kututu',NULL,'Cuy macho',NULL);
INSERT INTO "nivel2_animales" VALUES(30,'Wallata',NULL,'Ganso andino',NULL);
INSERT INTO "nivel2_animales" VALUES(31,'Q''alachu',NULL,'Loro',NULL);
INSERT INTO "nivel2_animales" VALUES(32,'Juku',NULL,'Búho',NULL);
INSERT INTO "nivel2_animales" VALUES(33,'Yuthu',NULL,'Perdiz',NULL);
INSERT INTO "nivel2_animales" VALUES(34,'Anka',NULL,'Águila',NULL);
INSERT INTO "nivel2_animales" VALUES(35,'Qaraywa',NULL,'Lagartija',NULL);
INSERT INTO "nivel2_animales" VALUES(36,'Ch''uspi',NULL,'Mosca',NULL);
INSERT INTO "nivel2_animales" VALUES(37,'Khuru',NULL,'Gusano',NULL);
CREATE TABLE "nivel2_preguntas" (id INTEGER PRIMARY KEY AUTOINCREMENT, palabra_frase TEXT NOT NULL, pronunciacion TEXT, traduccion TEXT, significado TEXT);
INSERT INTO "nivel2_preguntas" VALUES(1,'Pi',NULL,'¿Quién?',NULL);
INSERT INTO "nivel2_preguntas" VALUES(2,'Ima',NULL,'¿Qué?',NULL);
INSERT INTO "nivel2_preguntas" VALUES(3,'May',NULL,'¿Dónde?',NULL);
INSERT INTO "nivel2_preguntas" VALUES(4,'Jayk''aq',NULL,'¿Cuándo?',NULL);
INSERT INTO "nivel2_preguntas" VALUES(5,'Machkha',NULL,'¿Cuánto?',NULL);
CREATE TABLE "nivel2_pronombres" (id INTEGER PRIMARY KEY AUTOINCREMENT, palabra_frase TEXT NOT NULL, pronunciacion TEXT, traduccion TEXT, significado TEXT);
INSERT INTO "nivel2_pronombres" VALUES(1,'Ñuqa',NULL,'Yo',NULL);
INSERT INTO "nivel2_pronombres" VALUES(2,'Qam',NULL,'Tú',NULL);
INSERT INTO "nivel2_pronombres" VALUES(3,'Pay',NULL,'Él / Ella',NULL);
INSERT INTO "nivel2_pronombres" VALUES(4,'Ñuqanchik',NULL,'Nosotros (incluye a quien escucha)',NULL);
INSERT INTO "nivel2_pronombres" VALUES(5,'Ñuqayku',NULL,'Nosotros (sin quien escucha)',NULL);
INSERT INTO "nivel2_pronombres" VALUES(6,'Qamkuna',NULL,'Ustedes',NULL);
INSERT INTO "nivel2_pronombres" VALUES(7,'Paykuna',NULL,'Ellos / Ellas',NULL);
CREATE TABLE "nivel2_verbos" (id INTEGER PRIMARY KEY AUTOINCREMENT, palabra_frase TEXT NOT NULL, pronunciacion TEXT, traduccion TEXT, significado TEXT);
INSERT INTO "nivel2_verbos" VALUES(1,'Mikhuy',NULL,'Comer',NULL);
INSERT INTO "nivel2_verbos" VALUES(2,'Upyay',NULL,'Beber',NULL);
INSERT INTO "nivel2_verbos" VALUES(3,'Puñuy',NULL,'Dormir',NULL);
INSERT INTO "nivel2_verbos" VALUES(4,'Asiy',NULL,'Reír',NULL);
INSERT INTO "nivel2_verbos" VALUES(5,'Puriy',NULL,'Caminar',NULL);
INSERT INTO "nivel2_verbos" VALUES(6,'Takiy',NULL,'Cantar',NULL);
INSERT INTO "nivel2_verbos" VALUES(7,'Parlay',NULL,'Hablar',NULL);
INSERT INTO "nivel2_verbos" VALUES(8,'Kichay',NULL,'Abrir',NULL);
INSERT INTO "nivel2_verbos" VALUES(9,'Uyariy',NULL,'Escuchar',NULL);
INSERT INTO "nivel2_verbos" VALUES(10,'Phinkiy',NULL,'Saltar',NULL);
INSERT INTO "nivel2_verbos" VALUES(11,'Wayk''uy',NULL,'Cocinar',NULL);
INSERT INTO "nivel2_verbos" VALUES(12,'Samay',NULL,'Descansar','También: respirar');
INSERT INTO "nivel2_verbos" VALUES(13,'Riqsiy',NULL,'Conocer',NULL);
INSERT INTO "nivel2_verbos" VALUES(14,'Yachay',NULL,'Saber',NULL);
INSERT INTO "nivel2_verbos" VALUES(15,'Yupay',NULL,'Contar',NULL);
INSERT INTO "nivel2_verbos" VALUES(16,'Waqay',NULL,'Llorar',NULL);
INSERT INTO "nivel2_verbos" VALUES(17,'Llamk''ay',NULL,'Trabajar',NULL);
INSERT INTO "nivel2_verbos" VALUES(18,'Tarpuy',NULL,'Sembrar',NULL);
INSERT INTO "nivel2_verbos" VALUES(19,'Pukllay',NULL,'Jugar',NULL);
INSERT INTO "nivel2_verbos" VALUES(20,'Munay',NULL,'Querer',NULL);
INSERT INTO "nivel2_verbos" VALUES(21,'Wañuchikuy',NULL,'Apágate','Orden para apagar a Yura (imperativo)');
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('nivel1_alimentos',14);
INSERT INTO "sqlite_sequence" VALUES('nivel1_colores',22);
INSERT INTO "sqlite_sequence" VALUES('nivel1_elementos_casa',6);
INSERT INTO "sqlite_sequence" VALUES('nivel1_elementos_naturales',24);
INSERT INTO "sqlite_sequence" VALUES('nivel1_familia',19);
INSERT INTO "sqlite_sequence" VALUES('nivel1_herramientas',6);
INSERT INTO "sqlite_sequence" VALUES('nivel1_lugares',8);
INSERT INTO "sqlite_sequence" VALUES('nivel1_objetos_escolares',10);
INSERT INTO "sqlite_sequence" VALUES('nivel1_partes_del_cuerpo',23);
INSERT INTO "sqlite_sequence" VALUES('nivel1_saludos',8);
INSERT INTO "sqlite_sequence" VALUES('nivel1_utensilios_cocina',9);
INSERT INTO "sqlite_sequence" VALUES('nivel2_adjetivos_calificativos',16);
INSERT INTO "sqlite_sequence" VALUES('nivel2_adjetivos_determinativos',9);
INSERT INTO "sqlite_sequence" VALUES('nivel2_animales',37);
INSERT INTO "sqlite_sequence" VALUES('nivel2_pronombres',7);
INSERT INTO "sqlite_sequence" VALUES('nivel2_preguntas',5);
INSERT INTO "sqlite_sequence" VALUES('nivel2_verbos',21);
INSERT INTO "sqlite_sequence" VALUES('nivel1_dialogo_infantil',52);
INSERT INTO "sqlite_sequence" VALUES('nivel1_frutas',8);
COMMIT;
