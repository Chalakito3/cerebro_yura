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
const FALLBACK_CONTENT = 'Rimaykullayki';
const FALLBACK_CARD = {
  title: 'Rimaykullayki',
  written: 'Rimaykullayki',
  pronunciation: 'Ri-ma-y-ku-llay-ki',
  meaning: 'Rimaykullayki',
  example: 'Rimaykullayki, imaynalla kashanki?'
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

const modeCopy = {
  MENU: { label: '🌟 ESPERANDO', message: '🌟 Esperando a que me saludes.', content: 'Rimaykullayki', translation: '' },
  JUEGO: { label: '🧠 PENSANDO', message: '🧠 ¡A jugar y aprender!', content: 'Rimaykullayki', translation: '' },
  CONVERSAR: { label: '🎧 ESCUCHANDO', message: '🎧 Estoy escuchando tus palabras.', content: 'Rimaykullayki', translation: '' },
  TRADUCIR: { label: '✨ TRADUCIENDO', message: '✨ Estoy traduciendo lo que dices.', content: 'Rimaykullayki', translation: '' },
  SILENCIO: { label: '🤫 SILENCIOSA', message: '🤫 Estoy en silencio.', content: 'Rimaykullayki', translation: '' },
};

function extractQuechuaPhrase(value) {
  const text = (value || '').trim();
  if (!text) return '';

  const patterns = [
    /rimaykullayki/i,
    /allin\s+p[' ]?unchay/i,
    /allin\s+tuta/i,
    /yusulpayki/i,
    /anchata\s+munakuyki/i,
    /imaynalla\s+kachkanki/i
  ];

  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) {
      return match[0].trim();
    }
  }

  const directMatch = text.match(/(?:en\s+quechua\s+se\s+dice|se\s+dice|significa)\s+([A-Za-z0-9'\s]+)/i);
  if (directMatch && directMatch[1]) {
    return directMatch[1].trim().replace(/[.,;!?]+$/, '');
  }

  return '';
}

function normalizeExampleKey(value) {
  const phrase = extractQuechuaPhrase(value);
  if (!phrase) return 'rimaykullayki';

  const clean = phrase
    .toLowerCase()
    .replace(/[^a-z0-9\s']/g, ' ')
    .replace(/[\'’]/g, '')
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
  const text = (value || '').trim();
  if (!text) return fallback;

  const normalized = text.toLowerCase();
  const blocked = [
    'no entendí',
    'no entendi',
    'prueba con una palabra',
    'yura está',
    'esperando',
    'escuchando',
    'pensando',
    'hablando',
    'sin conexión',
    'sistema desconectado',
    'hasta luego',
    'tupananchiskama',
    'adios',
    'terminamos por ahora',
    'nos vemos',
    'me voy'
  ];

  if (blocked.some(part => normalized.includes(part))) {
    return fallback;
  }

  const extracted = extractQuechuaPhrase(text);
  if (extracted) {
    return extracted;
  }

  return text;
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

function renderWordExample(value) {
  const key = normalizeExampleKey(value);
  const sample = wordExamples[key] || wordExamples.rimaykullayki || FALLBACK_CARD;

  wordTitleNode.textContent = sample.title;
  wordWrittenNode.textContent = sample.written;
  wordPronunciationNode.textContent = sample.pronunciation;
  wordMeaningNode.textContent = sample.meaning;
  wordExampleNode.textContent = sample.example;
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
  activityNode.textContent = phaseInfo.label;
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
  renderWordExample(nextContent);
  document.body.dataset.visualState = visualState;
  document.body.dataset.phase = phase;
  secondaryStatusNode.textContent = activityText;
  systemReadoutNode.classList.toggle('system-offline', !status.running);

  if (status.updated_at) {
    const time = new Date(status.updated_at);
    updatedNode.textContent = `CONEXIÓN LOCAL · ${time.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}`;
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
    contentMainNode.textContent = FALLBACK_CONTENT;
    contentTranslationNode.textContent = '';
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
  setInterval(refreshStatus, 5000);
}

initializeDisplay();
