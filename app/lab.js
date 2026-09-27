import * as THREE from './vendor/three.module.js';
import { createArticulatedFly } from './articulated-fly.mjs';
import { ADAPTER, buildBodyReplay, makeActuatorControl, frameAt, groomingReadouts } from './lab-replay.mjs';

const $ = (id) => document.getElementById(id);
const number = (n, digits = 1) => Number(n || 0).toLocaleString('de-DE', { maximumFractionDigits: digits, minimumFractionDigits: digits });
const text = (tag, content, className) => { const el = document.createElement(tag); el.textContent = content; if (className) el.className = className; return el; };
const paragraphs = (target, values) => { target.replaceChildren(...values.filter(Boolean).map((s) => text('p', s))); };
const safeLink = (label, href) => { const a = text('a', label); if (/^https?:\/\//.test(href || '')) { a.href = href; a.target = '_blank'; a.rel = 'noopener noreferrer'; } return a; };
const choice = (label, value) => { const el = text('option', label); el.value = value; return el; };
let dataset; let catalog; let rootIndex; let scenario; let trial; let replay;
let currentMs = 0; let playing = false; let lastFrameAt = 0; let circuitSummaries = new Map();
let responseProfilesPromise; let searchVersion = 0;
const TECHNICAL = '__actuator_control__';
const conditionNames = { baseline: 'Baseline · ohne Reiz', stimulation: 'Stimulation', stimulated: 'Stimulation',
  ablation: 'Ablation / Ausschaltung', sham: 'Schein-Eingriff', sensory_ablation: 'Sensoren ausgeschaltet',
  readout_ablation: 'Ausleseneuronen ausgeschaltet' };
const evidenceNames = { published_anatomical_identity: 'PUBLIZIERTE ANATOMISCHE IDENTITÄT',
  published_model_cross_release_candidate: 'PUBLIZIERTER MODELLKANDIDAT · RELEASE-WECHSEL',
  published_curated_function_annotation: 'PUBLIZIERTE KURATIERTE FUNKTIONSANNOTATION',
  published_type_level_function: 'PUBLIZIERTE FUNKTION AUF ZELLTYP-EBENE',
  published_experiment_type_transfer: 'EXPERIMENTELLER BEFUND · ÜBERTRAGUNG AUF ZELLTYP',
  type_level_transfer_hypothesis: 'ÜBERTRAGUNG AUF ZELLTYP · HYPOTHESE',
  model_hypothesis: 'MODELLHYPOTHESE' };

const mount = $('lab-scene');
let renderer; let rig; let scene; let camera;
let orbit = { angle: .65, elevation: .4, radius: 4.5 }; let drag;
function cameraUpdate() {
  camera.position.set(Math.sin(orbit.angle) * Math.cos(orbit.elevation) * orbit.radius,
    .45 + Math.sin(orbit.elevation) * orbit.radius, Math.cos(orbit.angle) * Math.cos(orbit.elevation) * orbit.radius);
  camera.lookAt(0, .4, -.12);
}
function initializeScene() {
  try {
    scene = new THREE.Scene(); scene.background = new THREE.Color('#0b1e28');
    camera = new THREE.PerspectiveCamera(42, 1, .05, 100); cameraUpdate();
    renderer = new THREE.WebGLRenderer({ antialias: true }); renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFShadowMap;
    renderer.setClearColor('#0b1e28'); mount.append(renderer.domElement);
    scene.add(new THREE.HemisphereLight('#e2f1ef', '#76624a', 2.3));
    const key = new THREE.DirectionalLight('#fff2d9', 3.2); key.position.set(3, 5, 4); key.castShadow = true;
    key.shadow.mapSize.set(1024, 1024); key.shadow.camera.left = -4; key.shadow.camera.right = 4;
    key.shadow.camera.top = 4; key.shadow.camera.bottom = -4; scene.add(key);
    const floor = new THREE.Mesh(new THREE.CircleGeometry(4, 90), new THREE.MeshStandardMaterial({ color: '#173441', roughness: .9 }));
    floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);
    const grid = new THREE.GridHelper(8, 16, '#376071', '#24434f'); grid.position.y = .003; scene.add(grid);
    rig = createArticulatedFly(scene); rig.setContactsVisible(true);
    new ResizeObserver(() => { const width = mount.clientWidth; const height = mount.clientHeight;
      camera.aspect = width / height; camera.updateProjectionMatrix(); renderer.setSize(width, height); renderer.render(scene, camera); }).observe(mount);
    mount.addEventListener('pointerdown', (event) => { drag = { x: event.clientX, y: event.clientY, ...orbit }; mount.setPointerCapture(event.pointerId); });
    mount.addEventListener('pointermove', (event) => { if (!drag) return; orbit.angle = drag.angle - (event.clientX - drag.x) * .009;
      orbit.elevation = Math.max(.1, Math.min(1.35, drag.elevation + (event.clientY - drag.y) * .008)); cameraUpdate(); });
    mount.addEventListener('pointerup', () => { drag = null; }); mount.addEventListener('pointercancel', () => { drag = null; });
    mount.addEventListener('wheel', (event) => { event.preventDefault(); orbit.radius = Math.max(2.3, Math.min(10, orbit.radius * Math.exp(event.deltaY * .001))); cameraUpdate(); }, { passive: false });
  } catch (error) { $('scene-error').hidden = false; $('scene-error').textContent = `3D-Ansicht nicht verfügbar: ${error.message}. Die Versuchsdaten bleiben unten einsehbar.`; }
}
initializeScene();

function selectedTrialLabel(t) { return t.label || conditionNames[t.condition] || t.condition || t.id; }
function selectedScenario() { return $('experiment-select').value === TECHNICAL ? null : dataset.scenarios.find((s) => s.id === $('experiment-select').value); }
function setPlay(value) { playing = value; $('play').textContent = value ? 'Ⅱ Pausieren' : '▶ Wiedergabe'; }

function neuronButton(id, label) {
  const button = text('button', label || id, 'neuron-chip'); button.title = id;
  button.addEventListener('click', () => { $('lookup-query').value = id; searchCatalog(); $('lookup-form').scrollIntoView({ behavior: 'smooth', block: 'center' }); });
  return button;
}
function sourceList(target, sources) {
  if (!sources) return;
  for (const entry of sources) {
    const url = typeof entry === 'string' ? entry : entry.url || entry.source_url || entry.doi;
    const label = typeof entry === 'string' ? entry : entry.label || entry.title || ({ graph: 'FlyWire · Originalgraph', shiu: 'Shiu et al. · Funktionsmodell', tastekin: 'Tastekin et al. · Motoneuronen', stuerner: 'Stürner et al. · Absteigende Neuronen' }[entry.id]) || entry.id || url;
    if (url && /^https?:/.test(url)) { const p = document.createElement('p'); p.append(safeLink(label, url)); target.append(p); }
  }
}

function describeScenario() {
  const technical = !scenario;
  $('replay-label').textContent = technical ? 'TECHNISCHER AKTUATORTEST / OHNE HIRNGRAPH' : 'AUFZEICHNUNG / NEURONALES NETZMODELL';
  if (technical) {
    paragraphs($('circuit-evidence'), ['Dieser technische Kontrollversuch enthält keine neuronale Stimulation und keine Root-IDs.']);
    paragraphs($('model-evidence'), ['Ein direkt gesetzter Putzkanal prüft, ob der gegliederte Körper die Bewegung darstellen kann. Dieser Versuch ist kein Nachweis einer Gehirnfunktion.']);
    paragraphs($('body-evidence'), ['Putzkanal = 1 von 300 bis 1.700 ms; sonst 0. Kein neuronales Signal beteiligt. Derselbe Körper und dieselben Gelenkgleichungen werden auch für alle Netzwerk-Replays verwendet.']);
    $('trial-description').textContent = 'Positive technische Kontrolle: Putzkanal direkt aktiv. Außerhalb des neuronalen Versuchs.';
    return;
  }
  const input = scenario.input || {};
  paragraphs($('circuit-evidence'), [input.role || scenario.description || 'Zellen aus den veröffentlichten FlyWire-Annotationen und den Quellen des Versuchs.',
    `Reizgruppe: ${(input.ids || []).length} exakte Root-IDs. Auslese: ${scenario.readouts.length} benannte Zellen.`]);
  for (const readout of scenario.readouts) $('circuit-evidence').append(neuronButton(readout.id, `${readout.label || readout.id} ↗`));
  sourceList($('circuit-evidence'), scenario.sources || dataset.sources);
  paragraphs($('model-evidence'), ['Stimulation, Ausschaltung und Schein-Eingriffe werden im selben veröffentlichten Graphen verglichen. Angezeigt werden gespeicherte Aktionspotenziale des gewählten rechnerischen Zellmodells.',
    'Eine Antwort zeigt die Erreichbarkeit und Dynamik unter diesen Modellannahmen. Eine fehlende Antwort widerlegt die Funktion im lebenden Tier nicht.']);
  const finding = dataset.findings?.find((f) => f.id === (scenario.id.startsWith('jo_') ? 'abn1_dependency' : 'taste_order'));
  if (finding) { $('model-evidence').append(text('p', finding.claim), text('p', finding.limitation, 'small')); }
  const mapped = groomingReadouts(scenario);
  paragraphs($('body-evidence'), mapped.length ? [
    `Nur ${mapped.map((r) => r.label).join(', ')} treiben den hypothetischen Putzkanal. Die mittlere Spikerate der ${mapped.length} Zellen wird in einem kausalen Fenster von ${ADAPTER.rateWindowMs} ms gemessen.`,
    `Putzkanal = min(1, mittlere Rate / ${ADAPTER.groomingFullScaleHz} Hz). Verstärkung und Körperübersetzung sind ungeprüfte Modellannahmen. Ohne diese Spikes bleibt die Fliege stehen.`,
    'Es gibt keine Links-/Rechtszuordnung. Die Körperkinematik koordiniert beide Vorderbeine; Muskelkräfte und sensorische Rückkopplung zum Netz sind noch offen.'
  ] : ['Für diese Ausleseneuronen ist im aktuellen Körper kein biologisch begründeter Aktuator implementiert. Daher wird auch eine gemessene neuronale Antwort nicht in Bewegung umgerechnet.',
    'Die neuronale Zeitreihe und die Gegenproben bleiben auswertbar. Der Körper bleibt in diesem Versuch unbewegt.']);
}

function classifyResult(result) {
  if (result.technicalControl) return 'Technische Bewegungsfähigkeit';
  if (!result.totalReadoutSpikes) return 'Keine Ausleseantwort im Modell';
  if (!result.mappedIds.length) return 'Auslese aktiv · Körperkanal offen';
  if (!result.movement) return 'Auslese aktiv · keine Bewegung';
  return 'Auslese aktiv · Adapter reagiert';
}

function renderComparison() {
  const tbody = $('comparison-body'); tbody.replaceChildren();
  const trials = scenario?.trials || [{ id: TECHNICAL, label: 'Direkter Aktuator' }];
  for (const t of trials) {
    if (!circuitSummaries.has(t.id)) {
      const r = scenario ? buildBodyReplay(scenario, t) : makeActuatorControl();
      circuitSummaries.set(t.id, { totalReadoutSpikes: r.totalReadoutSpikes, meanReadoutHz: r.meanReadoutHz,
        jointMotion: r.jointMotion, mappedIds: r.mappedIds, movement: r.movement, technicalControl: r.technicalControl });
    }
    const result = circuitSummaries.get(t.id); const tr = document.createElement('tr');
    tr.classList.toggle('selected', t.id === trial?.id || (!scenario && t.id === TECHNICAL));
    tr.tabIndex = 0; tr.setAttribute('aria-label', `${selectedTrialLabel(t)} auswählen`);
    const select = () => { if (scenario) { $('condition-select').value = t.id; selectTrial(); } };
    tr.addEventListener('click', select); tr.addEventListener('keydown', (e) => { if (e.key === 'Enter') select(); });
    for (const value of [selectedTrialLabel(t), result.totalReadoutSpikes === null ? '–' : number(result.totalReadoutSpikes, 0),
      result.meanReadoutHz === null ? '–' : `${number(result.meanReadoutHz)} Hz / Zelle`, `${number(result.jointMotion, 3)} rad`, classifyResult(result)]) tr.append(text('td', value));
    tbody.append(tr);
  }
}

function selectScenario() {
  scenario = selectedScenario(); circuitSummaries = new Map();
  $('condition-select').replaceChildren();
  if (scenario) for (const t of scenario.trials) $('condition-select').append(choice(selectedTrialLabel(t), t.id));
  else $('condition-select').append(choice('Direkter Putzkanal · technische Kontrolle', TECHNICAL));
  $('condition-select').disabled = !scenario;
  if (scenario) {
    const stimulation = scenario.trials.find((t) => t.id === 'reference') || scenario.trials.find((t) => t.condition === 'stimulation' || t.condition === 'stimulated');
    if (stimulation) $('condition-select').value = stimulation.id;
  }
  describeScenario(); selectTrial();
}
function selectTrial() {
  setPlay(false); currentMs = 0;
  trial = scenario?.trials.find((t) => t.id === $('condition-select').value);
  replay = scenario ? buildBodyReplay(scenario, trial) : makeActuatorControl();
  if (trial) $('trial-description').textContent = `${selectedTrialLabel(trial)} · ${trial.durationMs} ms · Eingangsreiz ${trial.doseHz ?? 0} Hz. ${trial.description || ''}`;
  $('duration-label').textContent = `${number(replay.durationMs, 0)} ms`; $('scrubber').max = replay.durationMs;
  $('scrubber').disabled = false; $('play').disabled = false; $('reset').disabled = false;
  drawTrace(); renderComparison(); renderReadouts(); drawFrame();
}

function renderReadouts() {
  const target = $('readout-body'); target.replaceChildren();
  if (!scenario) { const row = document.createElement('tr'); const cell = text('td', 'Technischer Aktuatortest: keine neuronale Auslese.'); cell.colSpan = 5; row.append(cell); target.append(row); $('specificity-note').textContent = ''; return; }
  for (const readout of scenario.readouts) {
    const data = trial.summary?.readouts?.[readout.id] || {};
    const row = document.createElement('tr'); const label = document.createElement('td'); label.append(neuronButton(readout.id, readout.label), text('span', readout.id, 'root-id'));
    const live = text('td', '0 Hz'); live.id = `rate-${readout.id}`;
    row.append(label, text('td', number(replay.perIdSpikes[readout.id], 0)), text('td', data.stimulusRateHz !== undefined ? `${number(data.stimulusRateHz)} Hz` : '–'), live,
      text('td', replay.mappedIds.includes(readout.id) ? 'Putzen · Annahme' : 'Nicht gekoppelt'));
    target.append(row);
  }
  $('specificity-note').textContent = ['jo_ce', 'jo_f', 'jo_all'].includes(scenario.id)
    ? 'Prüfbefund: Auch die JO-F-Gruppe aktiviert bei 150 Hz aDN-Auslesezellen. Die publizierte C/E-versus-F-Spezifität der absteigenden Putz-Auslese (aDN1/aDN2) wird unter diesen Modellparametern nicht reproduziert. Eine sichtbare Putzbewegung ist daher kein bestandener biologischer Spezifitätstest.'
    : 'Die anatomische Benennung bleibt gültig, wenn ein Modellversuch still bleibt. Fehlende Antwort und unpassende Selektivität werden als offene Modellprobleme ausgewiesen.';
}

const SVG = 'http://www.w3.org/2000/svg';
function svg(tag, attrs, content) { const element = document.createElementNS(SVG, tag); for (const [key, value] of Object.entries(attrs)) element.setAttribute(key, value); if (content) element.textContent = content; return element; }
function drawTrace() {
  const chart = $('trace-chart'); chart.replaceChildren();
  const traces = replay.frames.map((f) => ({ tMs: f.tMs, value: scenario ? Object.values(f.rates).reduce((s, v) => s + v, 0) / (scenario.readouts.length || 1) : f.control.groom,
    mapped: f.control.meanHz || 0 }));
  const max = Math.max(scenario ? 10 : 1, ...traces.map((f) => Math.max(f.value, f.mapped)));
  const x = (t) => 48 + t / replay.durationMs * 932; const y = (v) => 137 - v / max * 115;
  if (trial?.stimulusWindowMs) chart.append(svg('rect', { x: x(trial.stimulusWindowMs[0]), y: 15,
    width: x(trial.stimulusWindowMs[1]) - x(trial.stimulusWindowMs[0]), height: 123, fill: '#ffffff', opacity: .04 }));
  for (const value of [0, max / 2, max]) { chart.append(svg('line', { x1: 48, x2: 980, y1: y(value), y2: y(value), stroke: '#28404b', 'stroke-width': 1 }));
    chart.append(svg('text', { x: 40, y: y(value) + 4, fill: '#9ab0b7', 'text-anchor': 'end', 'font-size': 11 }, number(value, 0))); }
  chart.append(svg('polyline', { points: traces.map((f) => `${x(f.tMs)},${y(f.value)}`).join(' '), fill: 'none', stroke: '#78caca', 'stroke-width': 2 }));
  if (scenario && replay.mappedIds.length) chart.append(svg('polyline', { points: traces.map((f) => `${x(f.tMs)},${y(f.mapped)}`).join(' '), fill: 'none', stroke: '#c4e4b0', 'stroke-width': 2 }));
  chart.append(svg('line', { id: 'time-cursor', x1: 48, x2: 48, y1: 10, y2: 142, stroke: '#e4ac78', 'stroke-width': 1.5 }));
  $('trace-label').textContent = scenario ? `Türkis: alle Auslesezellen · Grün: Putz-Auslese · Hz pro Zelle (${ADAPTER.rateWindowMs} ms Fenster)` : 'Direkt gesetzter Putzkanal 0–1 · kein neuronales Signal';
}
function drawFrame() {
  if (!replay) return;
  const frame = frameAt(replay, currentMs);
  // Freeze decorative motion: every visible change must come from recorded control and joint geometry.
  rig?.update({ ...frame.body, timeSeconds: 0 }, frame.control);
  $('scrubber').value = currentMs; $('time-label').textContent = `${number(currentMs, 0)} / ${number(replay.durationMs, 0)} ms`;
  $('body-status').textContent = `${frame.body.contacts} / 6 Bodenkontakte`;
  $('readout-value').textContent = scenario ? `${number(Object.values(frame.rates).reduce((s, n) => s + n, 0) / (scenario.readouts.length || 1))} Hz / Zelle` : 'Kein Hirnsignal';
  $('body-command').textContent = !scenario ? `${number(frame.control.groom, 2)} · direkt` : replay.mappedIds.length ? `${number(frame.control.groom, 2)} · Putzen` : 'Nicht zugeordnet';
  $('joint-motion').textContent = `${number(frame.jointMotion, 3)} rad`;
  if (scenario) for (const readout of scenario.readouts) { const cell = $(`rate-${readout.id}`); if (cell) cell.textContent = `${number(frame.rates[readout.id] || 0)} Hz`; }
  const cursor = $('time-cursor'); if (cursor) { const x = 48 + currentMs / replay.durationMs * 932; cursor.setAttribute('x1', x); cursor.setAttribute('x2', x); }
}
function animate(now) {
  const dt = Math.min((now - lastFrameAt) || 0, 100); lastFrameAt = now;
  if (playing && replay) { currentMs = Math.min(replay.durationMs, currentMs + dt * Number($('replay-speed').value));
    drawFrame(); if (currentMs >= replay.durationMs) setPlay(false); }
  if (renderer) renderer.render(scene, camera);
  requestAnimationFrame(animate);
}
requestAnimationFrame(animate);

$('experiment-select').addEventListener('change', selectScenario); $('condition-select').addEventListener('change', selectTrial);
$('play').addEventListener('click', () => { if (currentMs >= replay.durationMs) currentMs = 0; setPlay(!playing); drawFrame(); });
$('reset').addEventListener('click', () => { setPlay(false); currentMs = 0; drawFrame(); });
$('scrubber').addEventListener('input', () => { setPlay(false); currentMs = Number($('scrubber').value); drawFrame(); });
$('contacts').addEventListener('change', () => rig?.setContactsVisible($('contacts').checked));

function rowObject(row) { return Object.fromEntries(catalog.columns.map((key, index) => [key, row[index]])); }
function renderNeuron(row) {
  const n = rowObject(row); const card = text('article', '', 'neuron-card');
  const heading = text('h3', n.display_name || n.cell_type || 'Unbenanntes Neuron'); heading.append(text('span', n.root_id, 'root-id')); card.append(heading);
  const fields = text('div', '', 'neuron-fields');
  for (const [label, value] of [['Zelltyp', n.cell_type || 'offen'], ['Publizierte Namen / Aliase', n.published_names?.replaceAll('|', ', ') || 'keine weiteren'], ['Hemibrain-Typ', n.hemibrain_type || 'offen'], ['Klasse', n.cell_class || n.super_class || 'offen'],
    ['Seite · Annotation', n.side || 'unbekannt'], ['Transmitter · Vorhersage', n.top_nt || 'unbekannt'], ['Transmitter · bekannt', n.known_nt || 'nicht angegeben']]) {
    const field = text('span', ''); field.append(text('b', label), document.createTextNode(value)); fields.append(field);
  }
  card.append(fields);
  const claims = String(n.evidence_ids || '').split('|').filter(Boolean).map((id) => ({ id, ...catalog.claims_by_id?.[id] }));
  for (const claim of claims) {
    const source = (catalog.sources || []).find((s) => s.id === claim.source_id) || {};
    const kind = claim.evidence_kind || source.evidence_kind;
    const claimBox = text('div', '', 'claim'); claimBox.append(text('span', evidenceNames[kind] || kind || 'Quellenbehauptung', 'kind'), text('p', claim.label || claim.id));
    if (claim.caveat || source.caveat) claimBox.append(text('p', claim.caveat || source.caveat, 'muted'));
    const sourceUrl = claim.source_url || source.source_url || source.url || source.doi;
    if (sourceUrl) claimBox.append(safeLink('Originalquelle ↗', sourceUrl));
    const file = claim.source_file || source.source_file || source.path || source.file;
    if (file || claim.source_row != null) claimBox.append(text('p', `${file || ''}${claim.source_row != null ? ` · Quellenzeile ${claim.source_row}` : ''}`, 'muted small'));
    card.append(claimBox);
  }
  card.append(text('p', `Funktion: ${n.functional_role && n.functional_role !== 'unknown' ? n.functional_role : 'in diesem Katalog nicht funktionell belegt'}. Validierte Modellrolle: ${n.model_role && n.model_role !== 'unassigned' ? n.model_role : 'nicht zugeordnet'}.`, claims.length ? 'muted small' : 'no-evidence'));
  const used = dataset?.scenarios.filter((s) => s.readouts.some((r) => r.id === n.root_id) || s.input.ids.includes(n.root_id)) || [];
  if (used.length) { const row = text('p', 'In Versuchen: ', 'small'); for (const s of used) { const b = text('button', s.label, 'neuron-chip'); b.addEventListener('click', () => { $('experiment-select').value = s.id; selectScenario(); $('lab-scene').scrollIntoView({ behavior: 'smooth' }); }); row.append(b); } card.append(row); }
  const profile = text('section', 'Aufgezeichnetes Antwortprofil wird geladen …', 'response-profile'); profile.dataset.rootId = n.root_id; card.append(profile);
  return card;
}
async function loadResponseProfiles() {
  if (!responseProfilesPromise) responseProfilesPromise = fetch('./data/neuron_response_profiles.json', { cache: 'no-cache' }).then(async (response) => {
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (data.schema !== 'fly.neuron-response-profiles.v1' || !Array.isArray(data.conditions) || data.conditions.length !== 6 || !data.profiles_by_id || !Array.isArray(data.value_order)) throw new Error('Unerwartetes Format des Antwortprofils');
    return data;
  }).catch((error) => { responseProfilesPromise = undefined; throw error; });
  return responseProfilesPromise;
}
function renderResponseProfile(target, data) {
  const row = data.profiles_by_id[target.dataset.rootId]; target.replaceChildren();
  target.append(text('h4', 'Aufgezeichnetes Antwortprofil'), text('p', 'Modellantwort, keine biologische Funktionsbenennung.', 'profile-caveat'));
  target.append(text('p', `Sechs Referenzläufe zu je ${data.window_ms} ms; Reizfrequenz ${data.input_frequency_hz} Hz von ${data.stimulus_window_ms?.[0]} bis ${data.stimulus_window_ms?.[1]} ms.`, 'muted small'));
  if (!row) {
    target.append(text('p', 'In den sechs aufgezeichneten Referenzversuchen wurden für diese Root-ID keine Spikes erfasst. Unterschwellige Spannungsänderungen sind damit nicht ausgeschlossen. Daraus folgt keine biologische Funktionslosigkeit.', 'muted'));
  } else {
    const labels = { jo_ce: 'Johnston-Organ C/E', jo_f: 'Johnston-Organ F', jo_all: 'Johnston-Organ gesamt', sugar: 'Zucker', water: 'Wasser', bitter: 'Bitter' };
    const table = document.createElement('table'); const head = document.createElement('thead'); const header = document.createElement('tr');
    for (const value of ['Referenzreiz', 'Gesamt', 'Erzwungener Eingang', 'Nicht direkt erzwungen¹']) header.append(text('th', value)); head.append(header); table.append(head);
    const body = document.createElement('tbody');
    const indices = ['total_spikes', 'forced_input_spikes', 'non_forced_spikes'].map((key) => data.value_order.indexOf(key));
    if (indices.some((index) => index < 0) || row.length !== data.conditions.length) throw new Error('Unvollständige Spike-Spalten im Antwortprofil');
    data.conditions.forEach((condition, index) => {
      const values = indices.map((column) => row[index]?.[column]);
      if (values.some((value) => !Number.isFinite(value) || value < 0) || values[0] !== values[1] + values[2]) throw new Error('Inkonsistente Spike-Zählung im Antwortprofil');
      const tr = document.createElement('tr'); tr.append(text('td', labels[condition] || condition), ...values.map((value) => text('td', number(value, 0)))); body.append(tr);
    });
    table.append(body); const wrap = text('div', '', 'table-wrap'); wrap.append(table); target.append(wrap);
    target.append(text('p', `Je ${data.window_ms || 600} ms. ¹ Nicht direkt erzwungene Spikes im Graphmodell. Erzwungene Eingangsspitzen werden gesondert ausgewiesen und zählen nicht als selbst erzeugte Netzwerkantwort.`, 'muted small'));
  }
  const source = text('p', '', 'small'); const link = text('a', 'Antwortprofildaten ↗'); link.href = './data/neuron_response_profiles.json'; link.target = '_blank'; link.rel = 'noopener noreferrer'; source.append(link);
  if (data.source?.file) source.append(document.createTextNode(` · Berechnung: ${data.source.file}`)); target.append(source);
}
async function searchCatalog() {
  if (!catalog) return;
  const version = ++searchVersion;
  const query = $('lookup-query').value.trim(); const results = $('lookup-results'); results.replaceChildren();
  if (!query) { results.append(text('p', 'Bitte eine Root-ID oder einen Namen eingeben.', 'muted')); return; }
  let matches;
  if (/^\d+$/.test(query)) { const index = rootIndex.get(query); matches = index === undefined ? [] : [catalog.rows[index]]; }
  else { const lower = query.toLocaleLowerCase(); const cols = ['display_name', 'cell_type', 'hemibrain_type', 'functional_role', 'published_names'].map((k) => catalog.columns.indexOf(k)).filter((i) => i >= 0);
    matches = catalog.rows.filter((row) => cols.some((i) => String(row[i] || '').toLocaleLowerCase().includes(lower))); }
  results.append(text('p', `${number(matches.length, 0)} Treffer${matches.length > 30 ? ' · erste 30 angezeigt; Suche genauer eingrenzen' : ''}.`, 'muted small'));
  results.append(...matches.slice(0, 30).map(renderNeuron));
  if (matches.length) {
    try { const profiles = await loadResponseProfiles(); if (version !== searchVersion) return;
      for (const target of results.querySelectorAll('.response-profile')) {
        try { renderResponseProfile(target, profiles); } catch (error) { target.replaceChildren(text('p', `Antwortprofil nicht darstellbar: ${error.message}. Die Quellenzuordnung oben bleibt verfügbar.`, 'error')); }
      }
    } catch (error) { if (version !== searchVersion) return; for (const target of results.querySelectorAll('.response-profile')) target.replaceChildren(text('p', `Antwortprofile konnten nicht geladen werden (${error.message}). Erneut suchen, um das Laden zu wiederholen. Die Neuronenannotation oben bleibt verfügbar.`, 'error')); }
  }
}
$('lookup-form').addEventListener('submit', (event) => { event.preventDefault(); searchCatalog(); });

async function loadTrials() {
  try {
    const response = await fetch('./data/neuron_assays.json', { cache: 'no-cache' }); if (!response.ok) throw new Error(`HTTP ${response.status}`);
    dataset = await response.json(); if (!Array.isArray(dataset.scenarios) || !dataset.scenarios.length) throw new Error('Keine Versuche in der Datei');
    $('experiment-select').replaceChildren(...dataset.scenarios.map((s) => choice(s.label, s.id)), choice('Technischer Kontrolltest · direktes Putzen', TECHNICAL));
    $('experiment-select').disabled = false; selectScenario();
    const count = dataset.scenarios.reduce((sum, s) => sum + s.trials.length, 0);
    $('data-status').textContent = `${count} berechnete Versuche · ${dataset.scenarios.length} Schaltkreisgruppen`;
    $('generated-at').textContent = dataset.generatedAt ? `Berechnet: ${new Date(dataset.generatedAt).toLocaleString('de-DE')}` : '';
    const dynamics = dataset.dynamics || {};
    paragraphs($('method-details'), [dynamics.description || dynamics.model || '', ...(dataset.limitations || [])]);
    const params = document.createElement('details'); params.append(text('summary', 'Parameter des neuronalen Modells')); params.append(text('pre', JSON.stringify(dynamics, null, 2))); $('method-details').append(params);
  } catch (error) { $('data-status').textContent = `Versuchsdaten nicht verfügbar: ${error.message}`; $('data-status').classList.add('error');
    $('trial-description').textContent = 'Es werden keine neuronalen Antworten erfunden. Die Aufzeichnungen müssen zuerst vollständig berechnet sein.'; }
}
async function loadCatalog() {
  try {
    const response = await fetch('./data/neuron_catalog.json', { cache: 'no-cache' }); if (!response.ok) throw new Error(`HTTP ${response.status}`);
    catalog = await response.json();
    if (catalog.claims_url) { const claimsResponse = await fetch(catalog.claims_url, { cache: 'no-cache' }); if (!claimsResponse.ok) throw new Error(`Belegkatalog HTTP ${claimsResponse.status}`);
      const claimData = await claimsResponse.json(); catalog.claims_by_id = claimData.claims_by_id; if (claimData.sources) catalog.sources = claimData.sources; }
    const idCol = catalog.columns.indexOf('root_id'); rootIndex = new Map(catalog.rows.map((r, i) => [r[idCol], i]));
    $('catalog-status').textContent = `${number(catalog.rows.length, 0)} Neuronen · Root-IDs ohne Zahlenrundung`; $('search').disabled = false;
  } catch (error) { $('catalog-status').textContent = `Katalog nicht verfügbar: ${error.message}`; $('catalog-status').classList.add('error'); }
}
await Promise.allSettled([loadTrials(), loadCatalog()]);
