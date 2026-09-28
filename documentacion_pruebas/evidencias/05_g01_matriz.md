| ID | Módulo | Prueba | Entrada | Esperado | Obtenido | Estado |
|---|---|---|---|---|---|---|
| YURA-EXT-001 | conversacion | procesar_entrada | vacio | sin excepción, respuesta razonable | accion=responder resp='No logré escucharte.' (0 ms) | OK |
| YURA-EXT-002 | conversacion | procesar_entrada | espacios | sin excepción, respuesta razonable | accion=responder resp='No logré escucharte.' (0 ms) | OK |
| YURA-EXT-003 | conversacion | procesar_entrada | None | sin excepción, respuesta razonable | accion=responder resp='No logré escucharte.' (0 ms) | OK |
| YURA-EXT-004 | conversacion | procesar_entrada | 5000c | sin excepción, respuesta razonable | accion=responder resp='Rimaykullayki significa hola.' (0 ms) | OK |
| YURA-EXT-005 | conversacion | procesar_entrada | 100000c | sin excepción, respuesta razonable | accion=responder resp='Soy Yura, un robot educativo que ayuda a practicar quechua. Puedo enseñarte vocabulario, t' (592 ms) | OK |
| YURA-EXT-006 | conversacion | procesar_entrada | emojis | sin excepción, respuesta razonable | accion=responder resp='No logré escucharte.' (0 ms) | OK |
| YURA-EXT-007 | conversacion | procesar_entrada | sql | sin excepción, respuesta razonable | accion=responder resp='Soy Yura, un robot educativo que ayuda a practicar quechua. Puedo enseñarte vocabulario, t' (1 ms) | OK |
| YURA-EXT-008 | conversacion | procesar_entrada | porcentaje | sin excepción, respuesta razonable | accion=responder resp='No logré escucharte.' (0 ms) | OK |
| YURA-EXT-009 | conversacion | procesar_entrada | guion_bajo | sin excepción, respuesta razonable | accion=responder resp='No logré escucharte.' (0 ms) | OK |
| YURA-EXT-010 | conversacion | procesar_entrada | nulo | sin excepción, respuesta razonable | accion=responder resp='No logré escucharte.' (0 ms) | OK |
| YURA-EXT-011 | conversacion | procesar_entrada | saltos | sin excepción, respuesta razonable | accion=responder resp='RESPUESTA_GROQ_FALSA' ¦ Groq llamado: user=15 car, system=974 car (5 ms) | OK |
| YURA-EXT-012 | conversacion | procesar_entrada | ingles | sin excepción, respuesta razonable | accion=responder resp='RESPUESTA_GROQ_FALSA' ¦ Groq llamado: user=31 car, system=974 car (6 ms) | OK |
| YURA-EXT-013 | conversacion | procesar_entrada | num_123 | sin excepción, respuesta razonable | accion=responder resp='Soy Yura, un robot educativo que ayuda a practicar quechua. Puedo enseñarte vocabulario, t' (0 ms) | OK |
| YURA-EXT-014 | conversacion | procesar_entrada | num_-5 | sin excepción, respuesta razonable | accion=responder resp='Soy Yura, un robot educativo que ayuda a practicar quechua. Puedo enseñarte vocabulario, t' (0 ms) | OK |
| YURA-EXT-015 | conversacion | procesar_entrada | mezcla | sin excepción, respuesta razonable | accion=responder resp='Rimaykullayki significa hola. Es un saludo en quechua.' (0 ms) | OK |
| YURA-EXT-016 | conversacion | procesar_entrada | repetidas | sin excepción, respuesta razonable | accion=responder resp='Practiquemos una palabra. En quechua se dice Ukuku. Significa Oso andino: Mamífero de mont' (9 ms) | OK |
| YURA-EXT-017 | conversacion | procesar_entrada | jugar_y_salir | sin excepción, respuesta razonable | accion=menu resp='Hasta luego. Tupananchiskama.' (0 ms) | OK |
| YURA-EXT-018 | conversacion | procesar_entrada | traducir_apagar | sin excepción, respuesta razonable | accion=responder resp="No tengo una traducción segura de 'traducir apagar' en mi vocabulario local todavía. Puedo" (2 ms) | OK |
| YURA-EXT-019 | conversacion | procesar_entrada | menudo | sin excepción, respuesta razonable | accion=menu resp='Hasta luego. Tupananchiskama.' (0 ms) | FALLA |
| YURA-EXT-020 | conversacion | procesar_entrada | salirse | sin excepción, respuesta razonable | accion=menu resp='Hasta luego. Tupananchiskama.' (0 ms) | OBSERVACION |
| YURA-EXT-021 | conversacion | procesar_entrada | conjugar | sin excepción, respuesta razonable | accion=responder resp='Practiquemos una palabra. En quechua se dice Qallu. Significa Lengua: una palabra de uso c' (10 ms) | FALLA |
| YURA-EXT-022 | conversacion | procesar_entrada | nomas | sin excepción, respuesta razonable | accion=responder resp='Soy Yura, un robot educativo que ayuda a practicar quechua. Puedo enseñarte vocabulario, t' (0 ms) | OBSERVACION |
| YURA-EXT-023 | conversacion | procesar_entrada | apagarlo | sin excepción, respuesta razonable | accion=responder resp='Soy Yura, un robot educativo que ayuda a practicar quechua. Puedo enseñarte vocabulario, t' (0 ms) | OK |
| YURA-EXT-024 | conversacion | procesar_entrada | noche | sin excepción, respuesta razonable | accion=responder resp='Soy Yura, un robot educativo que ayuda a practicar quechua. Puedo enseñarte vocabulario, t' (0 ms) | OBSERVACION |
| YURA-EXT-025 | traductor | ejecutar_traducir | vacio | sin excepción; salir solo con orden clara | ret=continuar habló=['Necesito que repitas la palabra o frase.'] (0 ms) | OK |
| YURA-EXT-026 | traductor | ejecutar_traducir | espacios | sin excepción; salir solo con orden clara | ret=continuar habló=['Necesito que repitas la palabra o frase.'] (0 ms) | OK |
| YURA-EXT-027 | traductor | ejecutar_traducir | None | sin excepción; salir solo con orden clara | ret=continuar habló=['Necesito que repitas la palabra o frase.'] (0 ms) | OK |
| YURA-EXT-028 | traductor | ejecutar_traducir | 5000c | sin excepción; salir solo con orden clara | ret=continuar habló=['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra ma'] ¦ Groq user=4999 car (7 ms) | OBSERVACION |
| YURA-EXT-029 | traductor | ejecutar_traducir | 100000c | sin excepción; salir solo con orden clara | ret=continuar habló=['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra ma'] ¦ Groq user=100000 car (29 ms) | FALLA |
| YURA-EXT-030 | traductor | ejecutar_traducir | emojis | sin excepción; salir solo con orden clara | ret=continuar habló=['Necesito que repitas la palabra o frase.'] (0 ms) | OK |
| YURA-EXT-031 | traductor | ejecutar_traducir | sql | sin excepción; salir solo con orden clara | ret=continuar habló=['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra ma'] ¦ Groq user=35 car (7 ms) | OK |
| YURA-EXT-032 | traductor | ejecutar_traducir | porcentaje | sin excepción; salir solo con orden clara | ret=continuar habló=['Necesito que repitas la palabra o frase.'] (0 ms) | OK |
| YURA-EXT-033 | traductor | ejecutar_traducir | guion_bajo | sin excepción; salir solo con orden clara | ret=continuar habló=['Necesito que repitas la palabra o frase.'] (0 ms) | OK |
| YURA-EXT-034 | traductor | ejecutar_traducir | nulo | sin excepción; salir solo con orden clara | ret=continuar habló=['Necesito que repitas la palabra o frase.'] (0 ms) | OK |
| YURA-EXT-035 | traductor | ejecutar_traducir | saltos | sin excepción; salir solo con orden clara | ret=continuar habló=['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra ma'] ¦ Groq user=18 car (5 ms) | OK |
| YURA-EXT-036 | traductor | ejecutar_traducir | ingles | sin excepción; salir solo con orden clara | ret=continuar habló=['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra ma'] ¦ Groq user=31 car (6 ms) | OK |
| YURA-EXT-037 | traductor | ejecutar_traducir | num_123 | sin excepción; salir solo con orden clara | ret=continuar habló=['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra ma'] ¦ Groq user=3 car (5 ms) | OK |
| YURA-EXT-038 | traductor | ejecutar_traducir | num_-5 | sin excepción; salir solo con orden clara | ret=continuar habló=['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra ma'] ¦ Groq user=2 car (6 ms) | OK |
| YURA-EXT-039 | traductor | ejecutar_traducir | mezcla | sin excepción; salir solo con orden clara | ret=continuar habló=['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra ma'] ¦ Groq user=29 car (6 ms) | OK |
| YURA-EXT-040 | traductor | ejecutar_traducir | repetidas | sin excepción; salir solo con orden clara | ret=continuar habló=['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra ma'] ¦ Groq user=17 car (5 ms) | OK |
| YURA-EXT-041 | traductor | ejecutar_traducir | jugar_y_salir | sin excepción; salir solo con orden clara | ret=menu habló=['Regresando al menú principal.'] (0 ms) | OK |
| YURA-EXT-042 | traductor | ejecutar_traducir | traducir_apagar | sin excepción; salir solo con orden clara | ret=menu habló=['Regresando al menú principal.'] (0 ms) | OBSERVACION |
| YURA-EXT-043 | traductor | ejecutar_traducir | menudo | sin excepción; salir solo con orden clara | ret=menu habló=['Regresando al menú principal.'] (0 ms) | FALLA |
| YURA-EXT-044 | traductor | ejecutar_traducir | salirse | sin excepción; salir solo con orden clara | ret=menu habló=['Regresando al menú principal.'] (0 ms) | OBSERVACION |
| YURA-EXT-045 | traductor | ejecutar_traducir | conjugar | sin excepción; salir solo con orden clara | ret=continuar habló=['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra ma'] ¦ Groq user=8 car (6 ms) | OK |
| YURA-EXT-046 | traductor | ejecutar_traducir | nomas | sin excepción; salir solo con orden clara | ret=continuar habló=['No estoy seguro de cómo traducir esa frase. ¿Puedes decirla de otra ma'] ¦ Groq user=5 car (5 ms) | OK |
| YURA-EXT-047 | traductor | ejecutar_traducir | apagarlo | sin excepción; salir solo con orden clara | ret=menu habló=['Regresando al menú principal.'] (0 ms) | OBSERVACION |
| YURA-EXT-048 | traductor | ejecutar_traducir | noche | sin excepción; salir solo con orden clara | ret=continuar habló=['En quechua se dice: Allin tuta.'] (3 ms) | OK |
| YURA-EXT-049 | juego | ejecutar_turno | vacio | sin excepción; salir solo con orden clara | ret=continuar indice=0 habló=['¿Cómo se dice, agua, en quechua?', 'No logré escucharte.'] (2 ms) | OBSERVACION |
| YURA-EXT-050 | juego | ejecutar_turno | espacios | sin excepción; salir solo con orden clara | ret=continuar indice=0 habló=['¿Cómo se dice, casa, en quechua?', 'No logré escucharte.'] (1 ms) | OK |
| YURA-EXT-051 | juego | ejecutar_turno | None | sin excepción; salir solo con orden clara | ret=continuar indice=0 habló=['¿Cómo se dice, casa, en quechua?', 'No logré escucharte.'] (2 ms) | OK |
| YURA-EXT-052 | juego | ejecutar_turno | 5000c | sin excepción; salir solo con orden clara | ret=continuar indice=1 habló=['¿Cómo se dice, sol, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera'] (4 ms) | OK |
| YURA-EXT-053 | juego | ejecutar_turno | 100000c | sin excepción; salir solo con orden clara | ret=continuar indice=1 habló=['¿Cómo se dice, gato, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera'] (56 ms) | OK |
| YURA-EXT-054 | juego | ejecutar_turno | emojis | sin excepción; salir solo con orden clara | ret=continuar indice=0 habló=['¿Cómo se dice, perro, en quechua?', 'No logré escucharte.'] (1 ms) | OK |
| YURA-EXT-055 | juego | ejecutar_turno | sql | sin excepción; salir solo con orden clara | ret=continuar indice=1 habló=['¿Cómo se dice, perro, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera'] (2 ms) | OK |
| YURA-EXT-056 | juego | ejecutar_turno | porcentaje | sin excepción; salir solo con orden clara | ret=continuar indice=0 habló=['¿Cómo se dice, casa, en quechua?', 'No logré escucharte.'] (2 ms) | OK |
| YURA-EXT-057 | juego | ejecutar_turno | guion_bajo | sin excepción; salir solo con orden clara | ret=continuar indice=0 habló=['¿Cómo se dice, agua, en quechua?', 'No logré escucharte.'] (2 ms) | OK |
| YURA-EXT-058 | juego | ejecutar_turno | nulo | sin excepción; salir solo con orden clara | ret=continuar indice=0 habló=['¿Cómo se dice, gato, en quechua?', 'No logré escucharte.'] (1 ms) | OK |
| YURA-EXT-059 | juego | ejecutar_turno | saltos | sin excepción; salir solo con orden clara | ret=continuar indice=1 habló=['¿Cómo se dice, agua, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera'] (1 ms) | OK |
| YURA-EXT-060 | juego | ejecutar_turno | ingles | sin excepción; salir solo con orden clara | ret=continuar indice=1 habló=['¿Cómo se dice, agua, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera'] (1 ms) | OK |
| YURA-EXT-061 | juego | ejecutar_turno | num_123 | sin excepción; salir solo con orden clara | ret=continuar indice=1 habló=['¿Cómo se dice, gato, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera'] (1 ms) | OK |
| YURA-EXT-062 | juego | ejecutar_turno | num_-5 | sin excepción; salir solo con orden clara | ret=continuar indice=1 habló=['¿Cómo se dice, casa, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera'] (1 ms) | OK |
| YURA-EXT-063 | juego | ejecutar_turno | mezcla | sin excepción; salir solo con orden clara | ret=continuar indice=1 habló=['¿Cómo se dice, perro, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera'] (2 ms) | OK |
| YURA-EXT-064 | juego | ejecutar_turno | repetidas | sin excepción; salir solo con orden clara | ret=continuar indice=1 habló=['¿Cómo se dice, sol, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera'] (1 ms) | OK |
| YURA-EXT-065 | juego | ejecutar_turno | jugar_y_salir | sin excepción; salir solo con orden clara | ret=menu indice=0 habló=['¿Cómo se dice, casa, en quechua?', 'Saliendo al menú principal.'] (1 ms) | OK |
| YURA-EXT-066 | juego | ejecutar_turno | traducir_apagar | sin excepción; salir solo con orden clara | ret=continuar indice=1 habló=['¿Cómo se dice, gato, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera'] (1 ms) | OK |
| YURA-EXT-067 | juego | ejecutar_turno | menudo | sin excepción; salir solo con orden clara | ret=menu indice=0 habló=['¿Cómo se dice, gato, en quechua?', 'Saliendo al menú principal.'] (1 ms) | FALLA |
| YURA-EXT-068 | juego | ejecutar_turno | salirse | sin excepción; salir solo con orden clara | ret=menu indice=0 habló=['¿Cómo se dice, sol, en quechua?', 'Saliendo al menú principal.'] (1 ms) | OBSERVACION |
| YURA-EXT-069 | juego | ejecutar_turno | conjugar | sin excepción; salir solo con orden clara | ret=continuar indice=1 habló=['¿Cómo se dice, casa, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera'] (1 ms) | OK |
| YURA-EXT-070 | juego | ejecutar_turno | nomas | sin excepción; salir solo con orden clara | ret=continuar indice=1 habló=['¿Cómo se dice, gato, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera'] (1 ms) | OK |
| YURA-EXT-071 | juego | ejecutar_turno | apagarlo | sin excepción; salir solo con orden clara | ret=continuar indice=1 habló=['¿Cómo se dice, casa, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera'] (1 ms) | OK |
| YURA-EXT-072 | juego | ejecutar_turno | noche | sin excepción; salir solo con orden clara | ret=continuar indice=1 habló=['¿Cómo se dice, arbol, en quechua?', 'Sigue aprendiendo, tú puedes. Se dice de la siguiente manera'] (1 ms) | OK |
| YURA-EXT-073 | main_robot | ejecutar_menu | vacio | sin excepción; estado coherente | estado=MENU running=True habló=[] (0 ms) | OK |
| YURA-EXT-074 | main_robot | ejecutar_menu | espacios | sin excepción; estado coherente | estado=MENU running=True habló=[] (0 ms) | OK |
| YURA-EXT-075 | main_robot | ejecutar_menu | None | sin excepción; estado coherente | estado=MENU running=True habló=[] (0 ms) | OK |
| YURA-EXT-076 | main_robot | ejecutar_menu | 5000c | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Rimaykullayki significa hola.'] (1 ms) | OK |
| YURA-EXT-077 | main_robot | ejecutar_menu | 100000c | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Soy Yura, un robot educativo que ayuda a practicar quechua. '] (543 ms) | OK |
| YURA-EXT-078 | main_robot | ejecutar_menu | emojis | sin excepción; estado coherente | estado=MENU running=True habló=[] (0 ms) | OK |
| YURA-EXT-079 | main_robot | ejecutar_menu | sql | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Soy Yura, un robot educativo que ayuda a practicar quechua. '] (3 ms) | OK |
| YURA-EXT-080 | main_robot | ejecutar_menu | porcentaje | sin excepción; estado coherente | estado=MENU running=True habló=[] (0 ms) | OK |
| YURA-EXT-081 | main_robot | ejecutar_menu | guion_bajo | sin excepción; estado coherente | estado=MENU running=True habló=[] (0 ms) | OK |
| YURA-EXT-082 | main_robot | ejecutar_menu | nulo | sin excepción; estado coherente | estado=MENU running=True habló=[] (0 ms) | OK |
| YURA-EXT-083 | main_robot | ejecutar_menu | saltos | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['RESPUESTA_GROQ_FALSA'] (7 ms) | OK |
| YURA-EXT-084 | main_robot | ejecutar_menu | ingles | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['RESPUESTA_GROQ_FALSA'] (9 ms) | OK |
| YURA-EXT-085 | main_robot | ejecutar_menu | num_123 | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Soy Yura, un robot educativo que ayuda a practicar quechua. '] (0 ms) | OK |
| YURA-EXT-086 | main_robot | ejecutar_menu | num_-5 | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Soy Yura, un robot educativo que ayuda a practicar quechua. '] (0 ms) | OK |
| YURA-EXT-087 | main_robot | ejecutar_menu | mezcla | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Rimaykullayki significa hola. Es un saludo en quechua.'] (0 ms) | OK |
| YURA-EXT-088 | main_robot | ejecutar_menu | repetidas | sin excepción; estado coherente | estado=JUEGO running=True habló=[] (0 ms) | OK |
| YURA-EXT-089 | main_robot | ejecutar_menu | jugar_y_salir | sin excepción; estado coherente | estado=SILENCIO running=True habló=['Hasta luego. Tupananchiskama. Dime despierta cuando quieras '] (0 ms) | OK |
| YURA-EXT-090 | main_robot | ejecutar_menu | traducir_apagar | sin excepción; estado coherente | estado=SALIR running=False habló=['Hasta luego. Me voy a apagar.'] (0 ms) | OBSERVACION |
| YURA-EXT-091 | main_robot | ejecutar_menu | menudo | sin excepción; estado coherente | estado=MENU running=True habló=['Hasta luego. Tupananchiskama.'] (0 ms) | FALLA |
| YURA-EXT-092 | main_robot | ejecutar_menu | salirse | sin excepción; estado coherente | estado=SILENCIO running=True habló=['Hasta luego. Tupananchiskama. Dime despierta cuando quieras '] (0 ms) | OBSERVACION |
| YURA-EXT-093 | main_robot | ejecutar_menu | conjugar | sin excepción; estado coherente | estado=JUEGO running=True habló=[] (0 ms) | FALLA |
| YURA-EXT-094 | main_robot | ejecutar_menu | nomas | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Soy Yura, un robot educativo que ayuda a practicar quechua. '] (1 ms) | OK |
| YURA-EXT-095 | main_robot | ejecutar_menu | apagarlo | sin excepción; estado coherente | estado=SALIR running=False habló=['Hasta luego. Me voy a apagar.'] (0 ms) | OBSERVACION |
| YURA-EXT-096 | main_robot | ejecutar_menu | noche | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Soy Yura, un robot educativo que ayuda a practicar quechua. '] (2 ms) | OBSERVACION |
| YURA-EXT-097 | main_robot | ejecutar_conversar | vacio | sin excepción; estado coherente | estado=CONVERSAR running=True habló=[] (0 ms) | OK |
| YURA-EXT-098 | main_robot | ejecutar_conversar | espacios | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['No logré escucharte.'] (0 ms) | OBSERVACION |
| YURA-EXT-099 | main_robot | ejecutar_conversar | None | sin excepción; estado coherente | estado=CONVERSAR running=True habló=[] (0 ms) | OK |
| YURA-EXT-100 | main_robot | ejecutar_conversar | 5000c | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Rimaykullayki significa hola.'] (0 ms) | OK |
| YURA-EXT-101 | main_robot | ejecutar_conversar | 100000c | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Soy Yura, un robot educativo que ayuda a practicar quechua. '] (536 ms) | OK |
| YURA-EXT-102 | main_robot | ejecutar_conversar | emojis | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['No logré escucharte.'] (0 ms) | OK |
| YURA-EXT-103 | main_robot | ejecutar_conversar | sql | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Soy Yura, un robot educativo que ayuda a practicar quechua. '] (2 ms) | OK |
| YURA-EXT-104 | main_robot | ejecutar_conversar | porcentaje | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['No logré escucharte.'] (0 ms) | OK |
| YURA-EXT-105 | main_robot | ejecutar_conversar | guion_bajo | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['No logré escucharte.'] (0 ms) | OK |
| YURA-EXT-106 | main_robot | ejecutar_conversar | nulo | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['No logré escucharte.'] (0 ms) | OK |
| YURA-EXT-107 | main_robot | ejecutar_conversar | saltos | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['RESPUESTA_GROQ_FALSA'] (4 ms) | OK |
| YURA-EXT-108 | main_robot | ejecutar_conversar | ingles | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['RESPUESTA_GROQ_FALSA'] (5 ms) | OK |
| YURA-EXT-109 | main_robot | ejecutar_conversar | num_123 | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Soy Yura, un robot educativo que ayuda a practicar quechua. '] (0 ms) | OK |
| YURA-EXT-110 | main_robot | ejecutar_conversar | num_-5 | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Soy Yura, un robot educativo que ayuda a practicar quechua. '] (0 ms) | OK |
| YURA-EXT-111 | main_robot | ejecutar_conversar | mezcla | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Rimaykullayki significa hola. Es un saludo en quechua.'] (0 ms) | OK |
| YURA-EXT-112 | main_robot | ejecutar_conversar | repetidas | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Practiquemos una palabra. En quechua se dice Qhari. Signific'] (9 ms) | OK |
| YURA-EXT-113 | main_robot | ejecutar_conversar | jugar_y_salir | sin excepción; estado coherente | estado=MENU running=True habló=['Hasta luego. Tupananchiskama.'] (0 ms) | OK |
| YURA-EXT-114 | main_robot | ejecutar_conversar | traducir_apagar | sin excepción; estado coherente | estado=CONVERSAR running=True habló=["No tengo una traducción segura de 'traducir apagar' en mi vo"] (2 ms) | OK |
| YURA-EXT-115 | main_robot | ejecutar_conversar | menudo | sin excepción; estado coherente | estado=MENU running=True habló=['Hasta luego. Tupananchiskama.'] (0 ms) | FALLA |
| YURA-EXT-116 | main_robot | ejecutar_conversar | salirse | sin excepción; estado coherente | estado=MENU running=True habló=['Hasta luego. Tupananchiskama.'] (0 ms) | OK |
| YURA-EXT-117 | main_robot | ejecutar_conversar | conjugar | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Practiquemos una palabra. En quechua se dice Iglesia. Signif'] (9 ms) | FALLA |
| YURA-EXT-118 | main_robot | ejecutar_conversar | nomas | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Soy Yura, un robot educativo que ayuda a practicar quechua. '] (0 ms) | OK |
| YURA-EXT-119 | main_robot | ejecutar_conversar | apagarlo | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Soy Yura, un robot educativo que ayuda a practicar quechua. '] (0 ms) | OK |
| YURA-EXT-120 | main_robot | ejecutar_conversar | noche | sin excepción; estado coherente | estado=CONVERSAR running=True habló=['Soy Yura, un robot educativo que ayuda a practicar quechua. '] (0 ms) | OBSERVACION |
| YURA-EXT-121 | main_robot | ejecutar_silencio | vacio | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | OK |
| YURA-EXT-122 | main_robot | ejecutar_silencio | espacios | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | OK |
| YURA-EXT-123 | main_robot | ejecutar_silencio | None | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | OK |
| YURA-EXT-124 | main_robot | ejecutar_silencio | 5000c | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | OK |
| YURA-EXT-125 | main_robot | ejecutar_silencio | 100000c | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (2 ms) | OK |
| YURA-EXT-126 | main_robot | ejecutar_silencio | emojis | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | OK |
| YURA-EXT-127 | main_robot | ejecutar_silencio | sql | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | OK |
| YURA-EXT-128 | main_robot | ejecutar_silencio | porcentaje | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | OK |
| YURA-EXT-129 | main_robot | ejecutar_silencio | guion_bajo | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | OK |
| YURA-EXT-130 | main_robot | ejecutar_silencio | nulo | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | OK |
| YURA-EXT-131 | main_robot | ejecutar_silencio | saltos | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | OK |
| YURA-EXT-132 | main_robot | ejecutar_silencio | ingles | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | OK |
| YURA-EXT-133 | main_robot | ejecutar_silencio | num_123 | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | OK |
| YURA-EXT-134 | main_robot | ejecutar_silencio | num_-5 | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | OK |
| YURA-EXT-135 | main_robot | ejecutar_silencio | mezcla | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | OK |
| YURA-EXT-136 | main_robot | ejecutar_silencio | repetidas | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | OK |
| YURA-EXT-137 | main_robot | ejecutar_silencio | jugar_y_salir | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | OK |
| YURA-EXT-138 | main_robot | ejecutar_silencio | traducir_apagar | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | OK |
| YURA-EXT-139 | main_robot | ejecutar_silencio | menudo | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | OK |
| YURA-EXT-140 | main_robot | ejecutar_silencio | salirse | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | OK |
| YURA-EXT-141 | main_robot | ejecutar_silencio | conjugar | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | OK |
| YURA-EXT-142 | main_robot | ejecutar_silencio | nomas | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | OK |
| YURA-EXT-143 | main_robot | ejecutar_silencio | apagarlo | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | OK |
| YURA-EXT-144 | main_robot | ejecutar_silencio | noche | sin excepción; estado coherente | estado=SILENCIO running=True habló=[] (0 ms) | OK |
| YURA-EXT-151 | main_robot | ejecutar_menu | 'no quiero apagar' | NO debe apagar | estado=SALIR running=False habló=['Hasta luego. Me voy a apagar.'] (0 ms) | FALLA |
| YURA-EXT-152 | main_robot | ejecutar_menu | 'no te vayas a apagar yura' | NO debe apagar | estado=SALIR running=False habló=['Hasta luego. Me voy a apagar.'] (0 ms) | FALLA |
| YURA-EXT-153 | main_robot | ejecutar_menu | 'como se dice apagar la luz' | NO debe apagar | estado=SALIR running=False habló=['Hasta luego. Me voy a apagar.'] (0 ms) | FALLA |
| YURA-EXT-154 | main_robot | ejecutar_menu | 'como se dice adios en quechua' | traducir adiós, no despedirse | estado=SILENCIO running=True habló=['Hasta luego. Tupananchiskama. Dime despierta cuando quieras volver.'] (0 ms) | FALLA |
| YURA-EXT-155 | main_robot | ejecutar_conversar | 'como se dice adios en quechua' | traducir adiós | estado=MENU running=True habló=['Hasta luego. Tupananchiskama.'] (0 ms) | FALLA |
| YURA-EXT-156 | main_robot | ejecutar_conversar | 'como se dice menu en quechua' | responder, no volver al menú | estado=MENU running=True habló=['Hasta luego. Tupananchiskama.'] (0 ms) | FALLA |
| YURA-EXT-157 | main_robot | ejecutar_silencio | 'guarda silencio' | seguir en SILENCIO | estado=MENU running=True habló=['Ya estoy de vuelta. ¿Qué te gustaría hacer?'] (0 ms) | FALLA |
| YURA-EXT-158 | main_robot | ejecutar_silencio | 'no vuelvas todavia' | seguir en SILENCIO | estado=SILENCIO running=True habló=[] (0 ms) | OK |
| YURA-EXT-159 | main_robot | ejecutar_menu | 'silencio no quiero jugar' | SILENCIO (ambiguo) | estado=SILENCIO running=True habló=['Entendido. Me quedaré en silencio hasta que me pidas volver.'] (0 ms) | OK |
| YURA-EXT-160 | traductor | ejecutar_traducir | 'adios' | traducir la palabra (no salir) | ret=menu habló=['Regresando al menú principal.'] (0 ms) | FALLA |
| YURA-EXT-161 | traductor | ejecutar_traducir | 'volver' | traducir la palabra (no salir) | ret=menu habló=['Regresando al menú principal.'] (0 ms) | FALLA |
| YURA-EXT-162 | traductor | ejecutar_traducir | 'devolver' | traducir la palabra (no salir) | ret=menu habló=['Regresando al menú principal.'] (0 ms) | FALLA |
| YURA-EXT-163 | traductor | ejecutar_traducir | 'terminar' | traducir la palabra (no salir) | ret=menu habló=['Regresando al menú principal.'] (0 ms) | FALLA |
| YURA-EXT-164 | traductor | ejecutar_traducir | 'menu del dia' | traducir la palabra (no salir) | ret=menu habló=['Regresando al menú principal.'] (0 ms) | FALLA |
