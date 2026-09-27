export const CONDITIONS = {
  zero: ['Ruhe · kein Eingang', 'Alle 4.963 Zellen starten in Ruhe. Ohne externen Eingang bleibt die Aktivität im Modell null.'],
  dng100: ['DNg100 · tonischer Eingang', 'Eine DNg100-Zelle erhält konstant 400 willkürliche Einheiten. Eine periodische Reizfolge wird nicht vorgegeben.'],
  e1_removed: ['DNg100 · E1 ausgeschaltet', 'Identischer DNg100-Eingang. Eingehende und ausgehende Verbindungen von E1 sind in dieser Arbeitskopie entfernt.'],
  e2_removed: ['DNg100 · E2 ausgeschaltet', 'Identischer DNg100-Eingang. Eingehende und ausgehende Verbindungen von E2 sind in dieser Arbeitskopie entfernt.'],
  i2_removed: ['DNg100 · I2 ausgeschaltet', 'Identischer DNg100-Eingang. I2 ist entfernt; weitere hemmende Zellen bleiben im Netz.'],
  dnb08_pair: ['DNb08-Paar · Kontrollantrieb', 'Zwei DNb08-Zellen erhalten je konstant 400 Einheiten. Die Summe des externen Eingangs ist dadurch doppelt so groß.'],
  dng100_repeat: ['DNg100 · identische Wiederholung', 'Der gleiche vollständige Lauf wurde erneut ausgeführt. Sämtliche gespeicherten Zeitreihen stimmen exakt überein.'],
  dng100_tighter: ['DNg100 · engere Solvertoleranz', 'Identische biologische Modellparameter; nur die numerische Fehlertoleranz ist zehnmal enger. Die kleinen Kurvenunterschiede bleiben sichtbar.'],
};

export function validateReplay(data) {
  const errors = [];
  if (data.schema !== 'fly.cpg-rate-replay.v1') errors.push('Unbekanntes Replay-Schema');
  if (data.conditions?.length !== 8) errors.push('Acht Bedingungen erwartet');
  if (data.motorMetadata?.length !== 129) errors.push('129 konservative Motorzellen erwartet');
  if (new Set((data.conditions || []).map(c => c.id)).size !== 8) errors.push('Bedingungsnamen müssen eindeutig sein');
  if (new Set((data.motorMetadata || []).map(c => c.rootId)).size !== 129) errors.push('Motor-IDs müssen eindeutig sein');
  if (!/^[0-9a-f]{64}$/.test(data.provenance?.sourceReplaySha256 || '')) errors.push('Quell-Hash fehlt');
  const needed = [...Object.values(data.readouts || {}).map(x => x.rootId), ...(data.motorMetadata || []).map(x => x.rootId)];
  for (const c of data.conditions || []) {
    if (!CONDITIONS[c.id]) errors.push(`Unbekannte Bedingung ${c.id}`);
    if (c.timeSeconds.length !== 1001 || c.timeSeconds[0] !== 0 || c.timeSeconds.at(-1) !== 2) errors.push(`${c.id}: Zeitraster`);
    for (let i = 1; i < c.timeSeconds.length; i++) if (Math.abs(c.timeSeconds[i] - c.timeSeconds[i-1] - .002) > 1e-9) errors.push(`${c.id}: Zeitabstand`);
    for (const id of needed) {
      const values = c.ratesByRootId[id];
      if (!/^\d{18}$/.test(id) || !values || values.length !== c.timeSeconds.length || values.some(v => !Number.isFinite(v))) errors.push(`${c.id}: ungültige Reihe ${id}`);
    }
  }
  if (errors.length) throw new Error(errors.slice(0, 5).join('; '));
  return {conditions: data.conditions.length, motorCells: data.motorMetadata.length, samplesPerSeries: 1001, requiredSeriesPerCondition: needed.length};
}

const fmt = (value, digits = 2) => value == null ? '—' : Number(value).toLocaleString('de-DE', {minimumFractionDigits: digits, maximumFractionDigits: digits});
const roleColors = {DNg100_target_left: '#78caca', E1: '#c4e4b0', E2: '#e4ac78', I2: '#bea5e0', motor: '#c4e4b0'};
const NS = 'http://www.w3.org/2000/svg';

async function start() {
  const $ = id => document.getElementById(id);
  let data, trial, index = 0, selectedMotor, playing = false, lastTimestamp = null, accumulatedSeconds = 0, frameId = null;
  const cursors = [];
  const select = $('cpg-condition'), motorSelect = $('cpg-motor'), slider = $('cpg-time-slider');
  const chartRoles = ['DNg100_target_left', 'E1', 'E2', 'I2'];

  function element(tag, attributes = {}, text) {
    const node = document.createElementNS(NS, tag);
    for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
    if (text != null) node.textContent = text;
    return node;
  }
  function option(value, label) { const node = document.createElement('option'); node.value = value; node.textContent = label; return node; }
  function seriesStats(id) {
    const values = trial.ratesByRootId[id];
    let maximum = 0, postMaximum = 0;
    for (let i = 0; i < values.length; i++) { maximum = Math.max(maximum, values[i]); if (trial.timeSeconds[i] >= .25) postMaximum = Math.max(postMaximum, values[i]); }
    return {maximum, active: postMaximum > .01};
  }
  function drawTrace(svg, id, color) {
    svg.replaceChildren();
    const values = trial.ratesByRootId[id];
    const rawMax = seriesStats(id).maximum;
    const maxY = rawMax === 0 ? 1 : Math.ceil(rawMax * 1.12 * (rawMax < 1 ? 100 : 10)) / (rawMax < 1 ? 100 : 10);
    const left = 58, right = 584, top = 16, bottom = 122;
    const x = t => left + (right-left) * t / 2;
    const y = value => bottom - (bottom-top) * value / maxY;
    svg.dataset.rootId = id;
    svg.dataset.condition = trial.id;
    svg.dataset.samples = values.length;
    if (trial.summary.source_neurons.length) svg.append(element('rect', {x: x(.02), y: top, width: x(1.999)-x(.02), height: bottom-top, fill: '#193239', opacity: .5}));
    for (const level of [0, maxY/2, maxY]) {
      svg.append(element('line', {x1: left, x2: right, y1: y(level), y2: y(level), stroke: '#36505a', 'stroke-width': .8}));
      svg.append(element('text', {x: left-8, y: y(level)+5, 'text-anchor': 'end', class: 'plot-label'}, fmt(level, maxY < 1 ? 2 : 1)));
    }
    svg.append(element('text', {x: 4, y: 12, class: 'plot-label'}, 'Hz'));
    const path = values.map((value, i) => `${i ? 'L' : 'M'}${x(trial.timeSeconds[i]).toFixed(3)},${y(value).toFixed(3)}`).join(' ');
    svg.append(element('path', {d: path, stroke: color, class: 'plot-line'}));
    for (const seconds of [0, 1, 2]) svg.append(element('text', {x: x(seconds), y: 147, 'text-anchor': seconds === 0 ? 'start' : seconds === 2 ? 'end' : 'middle', class: 'plot-label'}, `${seconds} s`));
    const cursor = element('line', {x1: x(trial.timeSeconds[index]), x2: x(trial.timeSeconds[index]), y1: top, y2: bottom, class: 'plot-cursor'});
    svg.append(cursor);
    const old = cursors.findIndex(item => item.svg === svg);
    const item = {svg, cursor, x};
    if (old >= 0) cursors[old] = item; else cursors.push(item);
  }
  function updateCursor() {
    slider.value = index;
    $('cpg-time').textContent = `${fmt(trial.timeSeconds[index]*1000, 0)} / 2.000 ms`;
    for (const {cursor, x} of cursors) { const value = x(trial.timeSeconds[index]); cursor.setAttribute('x1', value); cursor.setAttribute('x2', value); }
    for (const role of chartRoles) document.querySelector(`[data-rate="${role}"]`).textContent = `${fmt(trial.ratesByRootId[data.readouts[role].rootId][index], 3)} Hz`;
    $('cpg-motor-rate').textContent = `${fmt(trial.ratesByRootId[selectedMotor][index], 3)} Hz`;
  }
  function setMotor(id) {
    selectedMotor = id;
    motorSelect.value = id;
    const meta = data.motorMetadata.find(m => m.rootId === id);
    $('cpg-motor-id').textContent = id;
    $('cpg-motor-type').textContent = `${meta.cellType || 'Typ unbekannt'} · ${meta.motorModule} · Quellseite ${meta.somaSide}`;
    drawTrace($('cpg-motor-trace'), id, roleColors.motor);
    updateCursor();
  }
  function pause() { playing = false; lastTimestamp = null; if (frameId != null) cancelAnimationFrame(frameId); frameId = null; $('cpg-play').textContent = '▶ Abspielen'; }
  function chooseCondition(id) {
    pause();
    trial = data.conditions.find(c => c.id === id);
    select.value = id;
    $('cpg-condition-note').textContent = CONDITIONS[id][1] + (trial.summary.source_neurons.length ? ` Eingangs-ID${trial.summary.source_neurons.length > 1 ? 's' : ''}: ${trial.summary.source_neurons.join(', ')}.` : '');
    const stats = trial.summary.conservative_motor_mask;
    $('cpg-active').textContent = `${stats.active_post_transient} / ${stats.total}`;
    $('cpg-score').textContent = fmt(stats.mean_rhythmicity, 6);
    $('cpg-frequency').textContent = stats.median_autocorrelation_frequency_hz_for_rhythmic_cells == null ? 'Keine' : `${fmt(stats.median_autocorrelation_frequency_hz_for_rhythmic_cells)} Hz`;
    $('cpg-rhythmic').textContent = stats.rhythmic_cells_score_above_0_5;
    $('cpg-input-note').textContent = id === 'zero' ? 'Kein externer Eingang' : id === 'dnb08_pair' ? 'DNb08-Paar: je 400 Einheiten · 20–1.999 ms' : 'DNg100: 400 Einheiten · 20–1.999 ms';
    for (const role of chartRoles) { const id = data.readouts[role].rootId; document.querySelector(`[data-root="${role}"]`).textContent = id; drawTrace(document.querySelector(`[data-trace="${role}"]`), id, roleColors[role]); }
    const motors = data.motorMetadata.map(m => ({...m, ...seriesStats(m.rootId)})).sort((a, b) => Number(b.active)-Number(a.active) || b.maximum-a.maximum || a.rootId.localeCompare(b.rootId));
    motorSelect.replaceChildren(...motors.map(m => option(m.rootId, `${m.active ? '● aktiv' : '○ inaktiv'} · ${m.somaSide === 'left' ? 'links' : m.somaSide === 'right' ? 'rechts' : m.somaSide} · ${m.motorModule} · ${m.rootId}`)));
    setMotor(selectedMotor && data.motorMetadata.some(m => m.rootId === selectedMotor) ? selectedMotor : motors[0].rootId);
    document.querySelectorAll('#cpg-comparisons tr').forEach(row => { row.classList.toggle('selected', row.dataset.condition === id); row.querySelector('button').setAttribute('aria-pressed', String(row.dataset.condition === id)); });
  }
  function frame(timestamp) {
    if (!playing) return;
    if (lastTimestamp != null) accumulatedSeconds += (timestamp-lastTimestamp)/1000 * Number($('cpg-speed').value);
    lastTimestamp = timestamp;
    index = Math.min(trial.timeSeconds.length-1, Math.round(accumulatedSeconds / .002));
    updateCursor();
    if (index === trial.timeSeconds.length-1) pause(); else frameId = requestAnimationFrame(frame);
  }
  try {
    const response = await fetch('./data/cpg_replay.json');
    if (!response.ok) throw new Error(`Replay HTTP ${response.status}`);
    data = await response.json();
    const verified = validateReplay(data);
    select.replaceChildren(...data.conditions.map(c => option(c.id, CONDITIONS[c.id][0])));
    const body = $('cpg-comparisons');
    for (const c of data.conditions) {
      const tr = document.createElement('tr'); tr.dataset.condition = c.id;
      const first = document.createElement('td'), button = document.createElement('button'); button.textContent = CONDITIONS[c.id][0]; button.addEventListener('click', () => chooseCondition(c.id)); first.append(button); tr.append(first);
      const stats = c.summary.conservative_motor_mask;
      for (const text of [String(stats.active_post_transient), fmt(stats.mean_rhythmicity, 6), String(stats.rhythmic_cells_score_above_0_5), stats.median_autocorrelation_frequency_hz_for_rhythmic_cells == null ? '—' : `${fmt(stats.median_autocorrelation_frequency_hz_for_rhythmic_cells)} Hz`]) { const td = document.createElement('td'); td.textContent = text; tr.append(td); }
      body.append(tr);
    }
    select.addEventListener('change', () => chooseCondition(select.value));
    motorSelect.addEventListener('change', () => setMotor(motorSelect.value));
    slider.addEventListener('input', () => { pause(); index = Number(slider.value); updateCursor(); });
    $('cpg-play').addEventListener('click', () => { if (playing) return pause(); if (index >= 1000) index = 0; accumulatedSeconds = trial.timeSeconds[index]; playing = true; lastTimestamp = null; $('cpg-play').textContent = 'Ⅱ Pause'; frameId = requestAnimationFrame(frame); });
    $('cpg-reset').addEventListener('click', () => { pause(); index = 0; updateCursor(); });
    document.addEventListener('visibilitychange', () => { if (document.hidden) pause(); });
    for (const id of ['cpg-condition', 'cpg-motor', 'cpg-time-slider', 'cpg-play', 'cpg-reset']) $(id).disabled = false;
    $('cpg-source-hash').textContent = data.provenance.sourceReplaySha256;
    $('cpg-numerics').textContent = `${data.provenance.verificationChecksPassed} Integritätsprüfungen und drei numerische Kontrollen bestanden. Die identische Wiederholung stimmt vollständig überein. Bei zehnmal engerer Toleranz bleibt die Rhythmik erhalten; maximale Abweichung der Motor-Raten: ${fmt(data.provenance.motorToleranceDifferenceHz, 5)} Hz.`;
    $('cpg-status').textContent = `${verified.conditions} Bedingungen · ${verified.samplesPerSeries} Zeitpunkte · Originalparameter erhalten`;
    chooseCondition('dng100');
    document.documentElement.dataset.cpgReady = 'true';
  } catch (error) {
    $('cpg-status').textContent = `Daten konnten nicht geprüft werden: ${error.message}`;
    $('cpg-status').classList.add('error');
    document.documentElement.dataset.cpgReady = 'error';
  }
}

if (typeof document !== 'undefined') start();
