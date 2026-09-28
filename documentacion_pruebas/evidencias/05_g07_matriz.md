| ID | Módulo | Prueba | Entrada | Esperado | Obtenido | Estado |
|---|---|---|---|---|---|---|
| YURA-EXT-701 | tts | limpiar/formatear/visible | markdown | sin Markdown/HTML/URL; texto pronunciable | limpio="Colores Puka: rojo Q'illu: amarillo 1. [ver](http://x.y)" voz="Colores Puka: rojo Q'illu: amarillo 1. [ver](http://x.y)." visible="Colores Puka: rojo Q'illu: amarillo 1" (0 ms) | FALLA |
| YURA-EXT-702 | tts | limpiar/formatear/visible | html | sin Markdown/HTML/URL; texto pronunciable | limpio='<p>Rimaykullayki</p><br>&nbsp;&amp;' voz='<p>Rimaykullayki</p><br>&nbsp;&amp;' visible='<p>Rimaykullayki</p><br>&nbsp;&amp;' (0 ms) | FALLA |
| YURA-EXT-703 | tts | limpiar/formatear/visible | url | sin Markdown/HTML/URL; texto pronunciable | limpio='Visita https://www.ejemplo.com/quechua?x=1&y=2 para más' voz='Visita https://www.ejemplo.com/quechua.x=1&y=2 para más.' visible='Visita https://www.ejemplo.com/quechua?x=1&y=2 par' (0 ms) | FALLA |
| YURA-EXT-704 | tts | limpiar/formatear/visible | tabla | sin Markdown/HTML/URL; texto pronunciable | limpio='¦ es ¦ qu ¦ ¦---¦---¦ ¦ casa ¦ wasi ¦' voz='¦ es ¦ qu ¦ ¦---¦---¦ ¦ casa ¦ wasi ¦.' visible='¦ es ¦ qu ¦ ¦---¦---¦ ¦ casa ¦ wasi ¦' (0 ms) | FALLA |
| YURA-EXT-705 | tts | limpiar/formatear/visible | solo_signos | sin Markdown/HTML/URL; texto pronunciable | limpio='¿¡?!...;;;' voz='.....;;;' visible='¿¡?!...;;;' (0 ms) | FALLA |
| YURA-EXT-706 | tts | limpiar/formatear/visible | espacios | sin Markdown/HTML/URL; texto pronunciable | limpio='' voz='.' visible='' (0 ms) | FALLA |
| YURA-EXT-707 | tts | limpiar/formatear/visible | guion_bajo | sin Markdown/HTML/URL; texto pronunciable | limpio='p unchay y NO ENCONTRADO' voz='p unchay, y NO ENCONTRADO.' visible='p unchay y NO ENCONTRADO' (0 ms) | OK |
| YURA-EXT-708 | tts | limpiar/formatear/visible | apostrofo | sin Markdown/HTML/URL; texto pronunciable | limpio="Allin p'unchay, Q'ello" voz="Allin p'unchay, Q'ello." visible="Allin p'unchay, Q'ello" (0 ms) | OK |
| YURA-EXT-709 | tts | limpiar/formatear/visible | pregunta | sin Markdown/HTML/URL; texto pronunciable | limpio='¿Imaynalla kachkanki?' voz='Imaynalla kachkanki.' visible='¿Imaynalla kachkanki?' (0 ms) | OK |
| YURA-EXT-710 | tts | limpiar/formatear/visible | abreviatura | sin Markdown/HTML/URL; texto pronunciable | limpio='Sr. Pérez dice: En quechua se dice Tata.' voz='Sr. Pérez dice: En quechua se dice Tata.' visible='Sr' (0 ms) | OK |
| YURA-EXT-711 | tts | limpiar/formatear/visible | traduccion | sin Markdown/HTML/URL; texto pronunciable | limpio='En quechua se dice: Tata. Significa padre.' voz='En quechua se dice: Tata. Significa padre.' visible=': Tata' (0 ms) | FALLA |
| YURA-EXT-712 | tts | limpiar/formatear/visible | asteriscos_mat | sin Markdown/HTML/URL; texto pronunciable | limpio='3 4 5 = 60' voz='3 4 5 = 60.' visible='3 4 5 = 60' (0 ms) | OK |
| YURA-EXT-720 | tts | texto extremo (rendimiento y longitud) | 10000_palabras | < 100 ms; limitar longitud visible/hablada | 1.1 ms; voz=10000 car; pantalla=9999 car (0 ms) | OBSERVACION |
| YURA-EXT-721 | tts | texto extremo (rendimiento y longitud) | 10000_asteriscos | < 100 ms; limitar longitud visible/hablada | 1.2 ms; voz=1 car; pantalla=0 car (0 ms) | OK |
| YURA-EXT-722 | tts | texto extremo (rendimiento y longitud) | 5000_negritas | < 100 ms; limitar longitud visible/hablada | 1.7 ms; voz=5001 car; pantalla=5000 car (0 ms) | OBSERVACION |
| YURA-EXT-723 | tts | texto extremo (rendimiento y longitud) | 10000_sin_punto | < 100 ms; limitar longitud visible/hablada | 0.6 ms; voz=10001 car; pantalla=10000 car (0 ms) | OBSERVACION |
| YURA-EXT-730 | tts | hablar(): Edge TTS falla (sin internet), sin motor local | Rimaykullayki | reintenta 1 vez, avisa y NO se bloquea | procesos=['edge-tts', 'edge-tts'] estados=['HABLANDO', 'ESPERANDO'] 0 ms (0 ms) | OK |
| YURA-EXT-731 | tts | hablar(): Edge TTS falla, hay spd-say | Rimaykullayki | usa spd-say | procesos=['edge-tts', 'edge-tts', 'spd-say'] estados=['HABLANDO', 'ESPERANDO'] 0 ms (0 ms) | OK |
| YURA-EXT-732 | tts | hablar(): Sin ffmpeg ni reproductores | Rimaykullayki | avisa que no hay audio | procesos=['edge-tts'] estados=['HABLANDO', 'ESPERANDO'] 0 ms (0 ms) | OK |
| YURA-EXT-733 | tts | hablar(): Todos los reproductores fallan | Rimaykullayki | prueba todos y cae a motor local | procesos=['edge-tts', 'ffmpeg', 'wpctl', 'pw-play', 'ffplay', 'mpg123'] estados=['HABLANDO', 'ESPERANDO'] 0 ms (0 ms) | OK |
| YURA-EXT-734 | tts | hablar(): Camino normal | Rimaykullayki | edge-tts -> ffmpeg -> pw-play | procesos=['edge-tts', 'ffmpeg', 'wpctl', 'pw-play'] estados=['HABLANDO', 'ESPERANDO'] 0 ms (0 ms) | OK |
| YURA-EXT-740 | tts | hablar(): Edge TTS se cuelga 1,5 s por intento (red lenta) | Rimaykullayki | timeout en subprocess.run | bloqueado 3.0 s; llamadas SIN timeout=['edge-tts', 'edge-tts'] (un cuelgue real bloquea al robot indefinidamente) (3001 ms) | FALLA |
| YURA-EXT-741 | tts | hablar('     ') solo espacios | '     ' | no llamar a Edge TTS | procesos=['edge-tts', 'ffmpeg', 'pw-play'] (sintetiza '.') (2 ms) | FALLA |
| YURA-EXT-742 | tts | hablar('¿¡?!') solo signos | '¿¡?!' | no llamar a Edge TTS | procesos=['edge-tts', 'ffmpeg', 'pw-play'] texto enviado='..' (1 ms) | FALLA |
| YURA-EXT-743 | tts | hablar(None) | None | no hacer nada | procesos=[] (0 ms) | OK |
| YURA-EXT-750 | tts | Edge TTS real con texto que empieza por '--' | '--hola.' | sintetizar el texto (usar --text=<texto>) | returncode=2 stderr=['edge-tts: error: argument -t/--text: expected one argument'] (0 ms) | FALLA |
