const stateNode = document.querySelector('#state');
const activityNode = document.querySelector('#activity');
const messageNode = document.querySelector('#message');
const updatedNode = document.querySelector('#updated');
const secondaryStatusNode = document.querySelector('#secondary-status');
const systemReadoutNode = document.querySelector('#system-readout');
const stateLabelNode = document.querySelector('#state-label');
const contentMainNode = document.querySelector('#content-main');
const contentTranslationNode = document.querySelector('#content-translation');
const wordTitleNode = document.querySelector('#word-title');
const wordWrittenNode = document.querySelector('#word-written');
const wordPronunciationNode = document.querySelector('#word-pronunciation');
const wordMeaningNode = document.querySelector('#word-meaning');
const wordExampleNode = document.querySelector('#word-example');
const contentResultNode = document.querySelector('#content-result');
const wordTagNode = document.querySelector('.word-card-tag');
// Cada 2 s (antes 5 s): la pantalla iba hasta 5 s atrasada respecto de la voz.
const INTERVALO_ESTADO_MS = 2000;
const FALLBACK_CONTENT = 'Rimaykullayki';
const FALLBACK_CARD = {
  title: 'Rimaykullayki',
  written: 'Rimaykullayki',
  pronunciation: 'Ri-ma-y-ku-llay-ki',
  meaning: 'Hola',
  example: 'Rimaykullayki, imaynalla kachkanki?'
};
let wordExamples = {};
const phaseCopy = {
  ESPERANDO: { label: '🌟 ESPERANDO', message: '🌟 Yura está listo para escuchar.' },
  ESCUCHANDO: { label: '🎧 ESCUCHANDO', message: '🎧 Escuchando con atención...' },
  PENSANDO: { label: '🧠 PENSANDO', message: '🧠 Estoy pensando qué significa.' },
  HABLANDO: { label: '🗣️ YURA HABLA', message: '🗣️ Yura está respondiendo con alegría.' },
  CELEBRANDO: { label: '🎉 CELEBRANDO', message: '🎉 ¡Qué alegría! Vamos a aprender más.' },
  TRISTE: { label: '😟 TRISTE', message: '😟 Necesito un poco de calma.' },
  SILENCIOSA: { label: '🤫 SILENCIOSA', message: '🤫 Estoy en silencio y listo para volver.' },
  SIN_CONEXION: { label: '⚠️ SIN CONEXIÓN', message: '⚠️ La conexión con Yura está caída.' },
};

// Modo actual de Yura, visible en la pantalla (antes solo se veía la fase).
const modeCopy = {
  MENU: { label: '🏠 MENÚ PRINCIPAL' },
  JUEGO: { label: '🎮 JUEGO' },
  CONVERSAR: { label: '💬 CONVERSACIÓN' },
  TRADUCIR: { label: '🔤 TRADUCTOR' },
  SILENCIO: { label: '🤫 EN SILENCIO' },
  ENSENAR: { label: '🎙️ MODO DOCENTE' },
  SALIR: { label: '👋 APAGANDO' },
  BACKEND_NOT_STARTED: { label: '⚠️ SIN CONEXIÓN' },
};

function normalizeExampleKey(value) {
  // Sin tildes y sin apóstrofo solo para elegir la tarjeta de ejemplo.
  const clean = (value || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/['’]/g, '')
    .replace(/\s+/g, ' ')
    .trim();

  if (clean.includes('rimaykullayki')) return 'rimaykullayki';
  if (clean.includes('allin') && clean.includes('punchay')) return 'allinpunchay';
  if (clean.includes('allin') && clean.includes('tuta')) return 'allintuta';
  if (clean.includes('yusulpayki')) return 'yusulpayki';
  if (clean.includes('anchata') && clean.includes('munakuyki')) return 'anchata';
  if (clean.includes('imaynalla') && clean.includes('kachkanki')) return 'imaynallakachkanki';

  return 'rimaykullayki';
}

function pickVisibleContent(value, fallback) {
  // El cerebro ya envía la palabra quechua y su significado separados; se
  // muestran tal cual. Antes una expresión regular cortaba el texto en la
  // primera tilde o ñ ("papá" se veía "pap", "niño" se veía "ni").
  const text = (value || '').trim();
  return text || fallback;
}

async function loadWordExamples() {
  try {
    const response = await fetch('/api/card', { cache: 'no-store' });
    if (!response.ok) {
      throw new Error('card payload unavailable');
    }
    const payload = await response.json();
    const examples = Array.isArray(payload.examples) ? payload.examples : [];
    wordExamples = Object.fromEntries(
      examples.map((entry) => [entry.key || 'rimaykullayki', entry])
    );
  } catch (error) {
    wordExamples = {
      rimaykullayki: FALLBACK_CARD
    };
  }
}

function showRow(node, visible) {
  node.closest('.word-row').hidden = !visible;
}

function renderWordExample(value) {
  const key = normalizeExampleKey(value);
  const sample = wordExamples[key] || wordExamples.rimaykullayki || FALLBACK_CARD;

  wordTitleNode.textContent = sample.title;
  wordWrittenNode.textContent = sample.written;
  wordPronunciationNode.textContent = sample.pronunciation;
  wordMeaningNode.textContent = sample.meaning;
  wordExampleNode.textContent = sample.example;
  wordTagNode.textContent = 'EJEMPLO';
  showRow(wordPronunciationNode, true);
  showRow(wordExampleNode, true);
}

// Si Yura está enseñando una palabra (quechua + significado), la tarjeta
// muestra esa palabra; si no, una de las tarjetas de ejemplo.
function renderWordCard(content, translation) {
  const isWord = content && translation && content.length <= 40;
  if (!isWord) {
    renderWordExample(content);
    return;
  }
  wordTitleNode.textContent = content;
  wordWrittenNode.textContent = content;
  wordMeaningNode.textContent = translation;
  wordTagNode.textContent = 'PALABRA';
  showRow(wordPronunciationNode, false);
  showRow(wordExampleNode, false);
}

function renderResult(status) {
  const inGame = status.state === 'JUEGO';
  if (inGame && status.result === 'CORRECTO') {
    contentResultNode.textContent = '✔ ¡Correcto!';
    contentResultNode.dataset.result = 'ok';
  } else if (inGame && status.result === 'INCORRECTO') {
    contentResultNode.textContent = '✘ Sigue intentando';
    contentResultNode.dataset.result = 'error';
  } else {
    contentResultNode.textContent = '';
    delete contentResultNode.dataset.result;
  }
}

function renderStatus(status) {
  const state = status.state || 'MENU';
  const copy = modeCopy[state] || modeCopy.MENU;
  const phase = status.phase || 'ESPERANDO';
  const phaseInfo = phaseCopy[phase] || phaseCopy.ESPERANDO;
  const activity = status.activity || copy.label;
  const visualState = state === 'BACKEND_NOT_STARTED' ? 'DISCONNECTED' : state;
  const activityText = activity.toUpperCase();
  stateNode.textContent = state === 'BACKEND_NOT_STARTED' ? 'SIN CONEXIÓN' : state === 'SILENCIO' ? 'SILENCIO' : 'YURA';
  stateLabelNode.textContent = phaseInfo.label;
  activityNode.textContent = copy.label;
  messageNode.textContent = phaseInfo.message;
  const safeFallback = FALLBACK_CONTENT;
  const nextContent = pickVisibleContent(status.content, safeFallback);
  let nextTranslation = pickVisibleContent(status.translation, '');
  if (nextTranslation && nextTranslation.toLowerCase() === nextContent.toLowerCase()) {
    nextTranslation = '';
  }
  if (contentMainNode.textContent !== nextContent) {
    contentMainNode.classList.remove('response-visible');
    contentMainNode.textContent = nextContent;
    void contentMainNode.offsetWidth;
    contentMainNode.classList.add('response-visible');
  }
  if (contentTranslationNode.textContent !== nextTranslation) {
    contentTranslationNode.textContent = nextTranslation;
  }
  renderWordCard(nextContent, nextTranslation);
  renderResult(status);
  document.body.dataset.visualState = visualState;
  document.body.dataset.phase = phase;
  secondaryStatusNode.textContent = activityText;
  systemReadoutNode.classList.toggle('system-offline', !status.running);

  if (status.updated_at) {
    const time = new Date(status.updated_at);
    const hora = time.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
    const quien = status.participante ? ` · JUEGA: ${status.participante}` : '';
    updatedNode.textContent = `CONEXIÓN LOCAL · ${hora}${quien}`;
  }
}

async function refreshStatus() {
  try {
    const response = await fetch('/api/status', { cache: 'no-store' });
    if (!response.ok) throw new Error('status unavailable');
    renderStatus(await response.json());
  } catch (error) {
    stateNode.textContent = 'SIN CONEXIÓN';
    stateLabelNode.textContent = 'SIN CONEXIÓN';
    activityNode.textContent = 'ESPERANDO AL BACKEND';
    messageNode.textContent = 'La pantalla no puede consultar el estado de Yura.';
    // Sin conexión no se deja una palabra vieja en pantalla como si fuera actual.
    contentMainNode.textContent = '…';
    contentTranslationNode.textContent = 'Esperando a Yura';
    renderResult({});
    renderWordExample('');
    secondaryStatusNode.textContent = 'SISTEMA DESCONECTADO';
    document.body.dataset.visualState = 'DISCONNECTED';
    document.body.dataset.phase = 'SIN_CONEXION';
    systemReadoutNode.classList.add('system-offline');
    updatedNode.textContent = 'CONEXIÓN LOCAL · SIN DATOS';
  }
}

async function initializeDisplay() {
  await loadWordExamples();
  refreshStatus();
  setInterval(refreshStatus, INTERVALO_ESTADO_MS);
}

initializeDisplay();
