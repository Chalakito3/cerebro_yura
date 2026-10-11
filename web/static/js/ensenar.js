// Modo docente: la docente graba pronunciaciones y Yura las guarda.
const $ = (selector) => document.querySelector(selector);
const estadoModo = $('#estado-modo');
const botonModo = $('#boton-modo');
const panelGrabacion = $('#panel-grabacion');
const aviso = $('#aviso-grabacion');
const botonGrabar = $('#boton-grabar');
const botonGuardar = $('#boton-guardar');
const botonDescartar = $('#boton-descartar');
const escuchado = $('#escuchado');
const audioPendiente = $('#audio-pendiente');
const lista = $('#lista-palabras');

let palabras = [];
let elegida = null;
let modo = 'inactivo';
let ultimoEstado = '';

async function enviar(ruta, datos) {
  const respuesta = await fetch(ruta, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(datos || {}),
  });
  const cuerpo = await respuesta.json().catch(() => ({}));
  if (!respuesta.ok) throw new Error(cuerpo.error || 'No se pudo completar la acción.');
  return cuerpo;
}

function texto(nodo, valor) { nodo.textContent = valor; }

// ---------- Lista de palabras ----------

async function cargarPalabras() {
  const respuesta = await fetch('/api/ensenar/palabras');
  palabras = (await respuesta.json()).palabras || [];
  const categorias = [...new Set(palabras.map((p) => p.categoria))].sort();
  const select = $('#categoria');
  const actual = select.value;
  select.innerHTML = '<option value="">Todas</option>';
  categorias.forEach((c) => select.add(new Option(c, c)));
  select.value = actual;
  pintarLista();
}

function sinTildes(valor) {
  return (valor || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/['’]/g, '');
}

function pintarLista() {
  const buscado = sinTildes($('#buscar').value.trim());
  const categoria = $('#categoria').value;
  const soloSin = $('#sin-grabar').checked;
  const visibles = palabras.filter((p) =>
    (!categoria || p.categoria === categoria)
    && (!soloSin || p.grabaciones === 0)
    && (!buscado || sinTildes(p.quechua).includes(buscado) || sinTildes(p.espanol).includes(buscado)));

  lista.replaceChildren(...visibles.map((p) => {
    const fila = document.createElement('tr');
    if (elegida && elegida.tabla === p.tabla && elegida.id === p.id) fila.className = 'elegida';
    const celdas = [
      [p.quechua, 'quechua'], [p.espanol, ''], [p.categoria, ''],
      [p.grabaciones ? `✅ ${p.grabaciones}` : '—', p.grabaciones ? 'grabaciones si' : 'grabaciones'],
    ];
    celdas.forEach(([valor, clase]) => {
      const celda = fila.insertCell();
      celda.textContent = valor;
      if (clase) celda.className = clase;
    });
    const boton = document.createElement('button');
    boton.type = 'button';
    boton.className = 'boton chico';
    boton.textContent = 'Elegir';
    boton.addEventListener('click', () => elegir(p));
    fila.insertCell().append(boton);
    return fila;
  }));
  const grabadas = palabras.filter((p) => p.grabaciones > 0).length;
  texto($('#conteo'), `${visibles.length} ${visibles.length === 1 ? 'palabra' : 'palabras'} en la lista · ${grabadas} de ${palabras.length} ya tienen grabación de la docente`);
}

['#buscar', '#categoria', '#sin-grabar'].forEach((s) => $(s).addEventListener('input', pintarLista));

// ---------- Palabra elegida ----------

function elegir(palabra) {
  elegida = palabra;
  panelGrabacion.hidden = false;
  texto($('#palabra-quechua'), palabra.quechua);
  texto($('#palabra-espanol'), palabra.espanol);
  escuchado.hidden = true;
  botonGuardar.hidden = true;
  botonDescartar.hidden = true;
  texto(aviso, modo === 'activo' ? 'Presione Grabar y diga la palabra.' : 'Primero active el modo docente.');
  aviso.classList.remove('escuchando');
  pintarLista();
  cargarGuardadas();
  cargarVoz();
  panelGrabacion.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function cargarGuardadas() {
  const contenedor = $('#guardadas');
  if (!elegida) return;
  const respuesta = await fetch(`/api/ensenar/grabaciones?tabla=${encodeURIComponent(elegida.tabla)}&id=${elegida.id}`);
  const grabaciones = (await respuesta.json()).grabaciones || [];
  contenedor.replaceChildren();
  if (!grabaciones.length) {
    const nota = document.createElement('p');
    nota.className = 'nota';
    nota.textContent = 'Esta palabra todavía no tiene grabaciones guardadas.';
    contenedor.append(nota);
    return;
  }
  const titulo = document.createElement('p');
  titulo.className = 'etiqueta';
  titulo.textContent = 'Grabaciones guardadas (Yura aprende de ellas)';
  contenedor.append(titulo);
  grabaciones.forEach((g) => {
    const fila = document.createElement('div');
    fila.className = 'guardada';
    const audio = document.createElement('audio');
    audio.controls = true;
    audio.preload = 'none';
    audio.src = `/ensenar/audio/${g.id}`;
    const nota = document.createElement('span');
    nota.className = 'nota';
    const uso = g.sirve_para_calificar ? 'se usa para calificar' : 'no se usa para calificar';
    nota.textContent = `${g.fecha.replace('T', ' ')} · escuchó «${g.transcripcion || '—'}» · ${uso}`;
    const borrar = document.createElement('button');
    borrar.type = 'button';
    borrar.className = 'boton chico peligro';
    borrar.textContent = 'Borrar';
    borrar.addEventListener('click', async () => {
      if (!confirm('¿Borrar esta grabación?')) return;
      await enviar(`/api/ensenar/borrar/${g.id}`);
      await cargarPalabras();
      cargarGuardadas();
    });
    fila.append(audio, nota, borrar);
    contenedor.append(fila);
  });
}

// ---------- Pronunciación para la voz de Yura ----------

const vozTexto = $('#voz-texto');
const vozNota = $('#voz-nota');

async function cargarVoz() {
  if (!elegida) return;
  const respuesta = await fetch(`/api/ensenar/voz?tabla=${encodeURIComponent(elegida.tabla)}&id=${elegida.id}`);
  const datos = await respuesta.json();
  vozTexto.value = datos.texto || elegida.quechua;
  texto(vozNota, datos.fijada
    ? '✅ Pronunciación fijada por la docente: Yura la dice así.'
    : 'Pronunciación automática. Escriba la palabra como se oye, escúchela y guárdela.');
}

$('#boton-escuchar-voz').addEventListener('click', () => {
  const valor = vozTexto.value.trim();
  if (!valor) return;
  texto(vozNota, 'Generando la voz de Yura…');
  const audio = new Audio(`/api/ensenar/voz/escuchar?texto=${encodeURIComponent(valor)}`);
  audio.addEventListener('playing', () => texto(vozNota, '🔊 Así lo dice Yura. ¿Suena bien? Si no, ajuste la escritura.'));
  audio.addEventListener('error', () => texto(vozNota, 'No se pudo generar la voz (¿hay internet?).'));
  audio.play().catch(() => texto(vozNota, 'No se pudo reproducir el audio.'));
});

$('#boton-guardar-voz').addEventListener('click', async () => {
  if (!elegida) return;
  try {
    const datos = await enviar('/api/ensenar/voz', { tabla: elegida.tabla, id: elegida.id, texto: vozTexto.value });
    vozTexto.value = datos.texto;
    texto(vozNota, datos.fijada ? '✅ Guardada. Desde ahora Yura la dice así.' : 'Se volvió a la pronunciación automática.');
  } catch (error) {
    texto(vozNota, error.message);
  }
});

// ---------- Botones ----------

botonModo.addEventListener('click', async () => {
  botonModo.disabled = true;
  try {
    await enviar(modo === 'inactivo' ? '/api/ensenar/activar' : '/api/ensenar/terminar');
  } catch (error) {
    alert(error.message);
  }
  consultarEstado();
});

botonGrabar.addEventListener('click', async () => {
  if (!elegida) return;
  try {
    await enviar('/api/ensenar/grabar', { tabla: elegida.tabla, id: elegida.id });
    ultimoEstado = '';
    consultarEstado();
  } catch (error) {
    texto(aviso, error.message);
  }
});

botonGuardar.addEventListener('click', async () => {
  try {
    await enviar('/api/ensenar/guardar');
    texto(aviso, '✅ Guardada. Yura ya la usa. Puede grabar otra vez o elegir otra palabra.');
    botonGuardar.hidden = true;
    botonDescartar.hidden = true;
    escuchado.hidden = true;
    await cargarPalabras();
    cargarGuardadas();
  } catch (error) {
    texto(aviso, error.message);
  }
});

botonDescartar.addEventListener('click', async () => {
  await enviar('/api/ensenar/descartar').catch(() => {});
  texto(aviso, 'Descartada. Presione Grabar para intentar otra vez.');
  botonGuardar.hidden = true;
  botonDescartar.hidden = true;
  escuchado.hidden = true;
});

// ---------- Estado de Yura ----------

function mostrarEnsenanza(e) {
  const clave = `${e.estado}|${e.transcripcion || ''}|${e.palabra ? e.palabra.id : ''}`;
  if (clave === ultimoEstado) return;
  ultimoEstado = clave;
  const ocupado = e.estado === 'esperando' || e.estado === 'grabando';
  aviso.classList.toggle('escuchando', ocupado);

  if (e.estado === 'listo_para_grabar' && elegida) texto(aviso, 'Presione Grabar y diga la palabra.');
  if (e.estado === 'esperando') texto(aviso, 'Preparando el micrófono…');
  if (e.estado === 'grabando') texto(aviso, '🎙️ Hable ahora: diga la palabra al micrófono.');
  if (e.estado === 'sin_voz') texto(aviso, 'No escuché nada. Acérquese al micrófono y presione Grabar otra vez.');
  if (e.estado === 'grabado') {
    texto(aviso, '¿Quedó bien? Escúchela y guárdela si es correcta.');
    escuchado.hidden = false;
    texto($('#texto-escuchado'), e.transcripcion || '(no entendí palabras)');
    let nota;
    if (!e.transcripcion) nota = 'Se puede guardar, pero no servirá para calificar.';
    else if (e.confunde_con) nota = `Ojo: eso se parece a otra palabra del diccionario (${e.confunde_con}). Se guardará, pero no se usará para calificar.`;
    else if (e.reconocida) nota = '✅ Yura entiende esta palabra así: en el juego la aceptaría. Puede guardarla o descartarla (si solo estaba probando).';
    else nota = 'Yura todavía no la entiende así: al guardarla (y aprender de los audios) la aceptará cuando un estudiante la diga igual.';
    texto($('#nota-escuchado'), nota);
    audioPendiente.src = `/ensenar/audio/pendiente?v=${Date.now()}`;
    botonGuardar.hidden = false;
    botonDescartar.hidden = false;
  }
}

async function consultarEstado() {
  try {
    const datos = await (await fetch('/api/ensenar/estado')).json();
    modo = datos.modo;
    const textos = {
      activo: '🟢 Modo docente activo: Yura espera sus grabaciones.',
      activando: '⏳ Activando… Yura termina lo que estaba diciendo.',
      inactivo: 'Yura está con los estudiantes. Active el modo docente para grabar.',
      sin_yura: '⚠️ Yura no está encendida.',
    };
    texto(estadoModo, textos[modo] || modo);
    estadoModo.classList.toggle('activo', modo === 'activo');
    botonModo.disabled = modo === 'sin_yura' || modo === 'activando';
    botonModo.textContent = modo === 'inactivo' || modo === 'sin_yura' ? 'Activar modo docente' : 'Terminar modo docente';
    if (modo !== 'activo') ultimoEstado = '';
    const e = datos.ensenanza || {};
    const ocupado = e.estado === 'esperando' || e.estado === 'grabando';
    botonGrabar.disabled = modo !== 'activo' || ocupado || !elegida;
    if (modo === 'activo') mostrarEnsenanza(e);
  } catch (error) {
    texto(estadoModo, '⚠️ Sin conexión con Yura.');
  }
}

cargarPalabras();
consultarEstado();
setInterval(consultarEstado, 800);
