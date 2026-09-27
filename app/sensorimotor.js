import * as THREE from './vendor/three.module.js';
import { createArticulatedFly } from './articulated-fly.mjs';
import { POLARITY_HYPOTHESES, SENSORIMOTOR_CONDITIONS } from './sensorimotor_model.mjs';

const $ = id => document.getElementById(id);
const f = (n, digits = 2) => Number(n || 0).toLocaleString('de-DE', { minimumFractionDigits: digits, maximumFractionDigits: digits });
const degrees = n => n * 180 / Math.PI;
const element = (tag, text, className) => { const e = document.createElement(tag); e.textContent = text; if (className) e.className = className; return e; };
const option = (value, text) => { const e = element('option', text); e.value = value; return e; };
const names = { closed: 'Geschlossener Regelkreis', sensory_open: 'Sensor-Rückmeldung offen', frozen: 'Sensorwerte ab 1.120 ms eingefroren', replay: 'Aufgezeichnete Sensorwerte wiedergeben', sensory_edge_ablation: 'Ausgehende Sensorkanten ausgeschaltet' };
const notes = { closed: 'Sensoren folgen dem gerade berechneten Gelenk. Das Nervennetz beeinflusst die nächsten Gelenkzustände.', sensory_open: 'Sensoren bleiben auf ihrer gesetzten Grundaktivität. Die passive Mechanik bleibt vollständig wirksam.', frozen: 'Die letzte Sensorinformation bei 1.120 ms bleibt erhalten. Danach fehlt die aktuelle Rückmeldung.', replay: 'Sensorwerte eines passenden geschlossenen Laufs werden wiedergegeben. Bei identischer Störung ist die gleiche Antwort erwartbar; dies ist eine Reproduzierbarkeitskontrolle.', sensory_edge_ablation: 'Sensoren reagieren auf Bewegung, können ihre Antwort aber nicht mehr in das Netz weitergeben.' };
const plus = n => n > 0 ? '+' : '−';
let result, playing = false, timeMs = 0, last = 0, requestId = 0;
const worker = new Worker(new URL('./sensorimotor-worker.mjs', import.meta.url), { type: 'module' });
const scene = new THREE.Scene(); scene.background = new THREE.Color('#0b1e28');
const camera = new THREE.PerspectiveCamera(40, 1, .05, 100);
let renderer, rig, selectedLine, dragging;
let orbit = { angle: -.65, elevation: .32, radius: 5.7 };
function aim() { camera.position.set(Math.sin(orbit.angle) * Math.cos(orbit.elevation) * orbit.radius, 1 + Math.sin(orbit.elevation) * orbit.radius, Math.cos(orbit.angle) * Math.cos(orbit.elevation) * orbit.radius); camera.lookAt(0, 1, -.1); }
aim();
try {
  renderer = new THREE.WebGLRenderer({ antialias: true }); renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFShadowMap; $('sm-scene').append(renderer.domElement);
  scene.add(new THREE.HemisphereLight('#e2f1ef', '#76624a', 2.3));
  const light = new THREE.DirectionalLight('#fff2d9', 3.2); light.position.set(3, 6, 4); light.castShadow = true; scene.add(light);
  const floor = new THREE.Mesh(new THREE.CircleGeometry(4, 90), new THREE.MeshStandardMaterial({ color: '#173441', roughness: .9 })); floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);
  const grid = new THREE.GridHelper(8, 16, '#376071', '#24434f'); grid.position.y = .004; scene.add(grid);
  const holder = new THREE.Mesh(new THREE.CylinderGeometry(.055, .1, 1.07, 12), new THREE.MeshStandardMaterial({ color: '#71848b', metalness: .6, roughness: .4 })); holder.position.set(0, .535, -.1); scene.add(holder);
  rig = createArticulatedFly(scene); rig.setContactsVisible(false);
  selectedLine = new THREE.Line(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: '#78caca', depthTest: false })); selectedLine.renderOrder = 5; scene.add(selectedLine);
  new ResizeObserver(() => { const w = $('sm-scene').clientWidth, h = $('sm-scene').clientHeight; camera.aspect = w / h; camera.updateProjectionMatrix(); renderer.setSize(w, h); }).observe($('sm-scene'));
  $('sm-scene').addEventListener('pointerdown', e => { dragging = { x: e.clientX, y: e.clientY, ...orbit }; $('sm-scene').setPointerCapture(e.pointerId); });
  $('sm-scene').addEventListener('pointermove', e => { if (!dragging) return; orbit.angle = dragging.angle - (e.clientX - dragging.x) * .009; orbit.elevation = Math.max(.08, Math.min(1.3, dragging.elevation + (e.clientY - dragging.y) * .008)); aim(); });
  $('sm-scene').addEventListener('pointerup', () => { dragging = null; }); $('sm-scene').addEventListener('pointercancel', () => { dragging = null; });
  $('sm-scene').addEventListener('wheel', e => { e.preventDefault(); orbit.radius = Math.max(2.5, Math.min(10, orbit.radius * Math.exp(e.deltaY * .001))); aim(); }, { passive: false });
} catch (error) { $('sm-scene-error').hidden = false; $('sm-scene-error').textContent = `3D nicht verfügbar: ${error.message}`; }

function setPlaying(value) { playing = value; $('sm-play').textContent = value ? 'Ⅱ Pausieren' : '▶ Versuch abspielen'; }
function busy(value) { for (const id of ['sm-detector', 'sm-polarity', 'sm-condition', 'sm-play', 'sm-reset', 'sm-scrubber', 'sm-neuron']) $(id).disabled = value; }
function run() {
  setPlaying(false); busy(true); $('sm-status').textContent = 'Regelkreis und identische Kontrollversuche werden berechnet …';
  worker.postMessage({ requestId: ++requestId, detector: $('sm-detector').value, polarity: $('sm-polarity').value, condition: $('sm-condition').value });
}
function currentFrame() {
  const frames = result.frames; if (timeMs <= frames[0].tMs) return frames[0];
  const interval = frames.length > 1 ? frames[1].tMs - frames[0].tMs : 10;
  return frames[Math.min(frames.length - 1, Math.max(0, Math.round((timeMs - frames[0].tMs) / interval)))];
}
function neuronDetail(frame) {
  const node = result.circuit.nodes.find(n => n.id === $('sm-neuron').value); if (!node) return;
  const sign = node.signAssumption; const content = $('sm-neuron-detail'); content.replaceChildren();
  content.append(element('code', node.id), element('p', `${node.cellType || 'Typ nicht annotiert'} · ${node.role} · ${node.side || 'Seite nicht annotiert'}`),
    element('p', `Aktivität: ${f(frame.neuralRates?.[node.id], 5)} · Grundaktivität: ${f(result.parameters.baselineRate)}`),
    element('p', `Transmitter: ${sign?.transmitter || 'unbekannt'} (${sign?.transmitterEvidence === 'verified_identity' ? 'verifizierte Quellenannotation' : 'keine verifizierte Identität'}). Modellwirkung: ${sign?.sign === 1 ? 'erregend' : sign?.sign === -1 ? 'hemmend' : 'kein signierter Beitrag'}.`),
    element('p', node.role === 'sensor' ? 'Richtung und Kennlinie dieser einzelnen Sensor-ID sind unbekannt. Die gewählte Populationshypothese ist gesetzt.' : 'Die dynamische Antwort ist ein Modellergebnis, keine neue biologische Funktionsannotation.'));
}
function drawFrame() {
  if (!result) return; const frame = currentFrame();
  rig?.update({ ...frame.body, timeSeconds: 0 }, {});
  if (selectedLine) { const leg = frame.body.legs.find(l => l.id === 'LF'); selectedLine.geometry.dispose(); selectedLine.geometry = new THREE.BufferGeometry().setFromPoints(leg.pointsLocal.map(p => new THREE.Vector3(p[0], p[1] + frame.body.pose.height, p[2]))); }
  $('sm-time').textContent = `${f(timeMs, 0)} / 4.000 ms`; $('sm-scrubber').value = timeMs;
  $('sm-angle').textContent = `${f(degrees(frame.angle), 1)}°`; $('sm-deviation').textContent = `${f(degrees(frame.deviation), 2)}°`;
  $('sm-sensors').textContent = `${f(frame.clawRate, 3)} / ${f(frame.hookRate, 3)}`;
  $('sm-motors').textContent = `${f(frame.flexor, 3)} / ${f(frame.extensor, 3)}`;
  $('sm-torque').textContent = `${f(frame.externalTorque)} / ${f(frame.activeTorque)}`;
  const cursor = $('sm-cursor'); if (cursor) { const x = 72 + timeMs / 4000 * 910; cursor.setAttribute('x1', x); cursor.setAttribute('x2', x); }
  neuronDetail(frame);
}
const SVG = 'http://www.w3.org/2000/svg';
function svg(tag, attributes, text) { const e = document.createElementNS(SVG, tag); for (const [k, v] of Object.entries(attributes)) e.setAttribute(k, v); if (text) e.textContent = text; return e; }
function traces() {
  const chart = $('sm-trace'); chart.replaceChildren(); const x = t => 72 + t / 4000 * 910;
  const extent = Math.max(1, Math.ceil(Math.max(...result.frames.map(r => Math.abs(degrees(r.deviation))))));
  const panels = [{ label: 'Winkel Δ°', top: 20, height: 78, min: -extent, max: extent, channels: [['#c4e4b0', r => degrees(r.deviation)]], labels: ['Gelenk'] },
    { label: 'Sensor 0–1', top: 130, height: 70, min: 0, max: 1, channels: [['#78caca', r => r.clawRate], ['#b899dd', r => r.hookRate]], labels: ['Claw', 'Hook'] },
    { label: 'Muskel 0–1', top: 240, height: 70, min: 0, max: 1, channels: [['#78caca', r => r.flexor], ['#e4ac78', r => r.extensor]], labels: ['Beuger', 'Strecker'] }];
  for (const panel of panels) {
    const y = value => panel.top + panel.height - (value - panel.min) / (panel.max - panel.min) * panel.height;
    chart.append(svg('text', { x: 9, y: panel.top - 5, fill: '#a9b8bb', 'font-size': 11 }, panel.label));
    for (const value of [panel.min, (panel.max + panel.min) / 2, panel.max]) { chart.append(svg('line', { x1: 72, x2: 982, y1: y(value), y2: y(value), stroke: '#28404b' }), svg('text', { x: 64, y: y(value) + 4, 'text-anchor': 'end', fill: '#a9b8bb', 'font-size': 10 }, f(value, 1))); }
    for (const [at, width] of [[1000, 100], [2200, 120]]) chart.append(svg('rect', { x: x(at), y: panel.top, width: x(at + width) - x(at), height: panel.height, fill: '#e4ac78', opacity: .13 }));
    panel.channels.forEach(([color, value], index) => { chart.append(svg('polyline', { points: result.frames.map(r => `${x(r.tMs)},${y(value(r))}`).join(' '), fill: 'none', stroke: color, 'stroke-width': 2 }), svg('text', { x: 980 - index * 75, y: panel.top - 6, 'text-anchor': 'end', fill: color, 'font-size': 11 }, panel.labels[index])); });
  }
  chart.append(svg('line', { id: 'sm-cursor', x1: 72, x2: 72, y1: 12, y2: 318, stroke: '#edf0e8', 'stroke-width': 1 }));
}
function renderResults() {
  const s = result.circuit.statistics; const c = result.config;
  $('sm-status').textContent = `${s.sensors} Sensoren · ${s.interneurons} Zwischenzellen · ${s.motors} Motorneuronen · ${s.edges} Kanten (${c.detector})`;
  $('sm-mode').textContent = names[c.condition]; $('sm-condition-note').textContent = notes[c.condition];
  $('sm-network').textContent = `${s.sensors} → ${s.interneurons} → ${s.motors}`;
  $('sm-network-note').textContent = `${s.edges} strukturelle Kanten; ${s.zeroSignedEdges} ohne Beitrag wegen fehlender verwendbarer Transmitteridentität. Zentrale Vorzeichen bleiben Rezeptorannahmen.`;
  $('sm-peak').textContent = `${f(degrees(result.summary.peakDeviationRadians))}°`;
  const open = result.comparison.find(r => r.condition === 'sensory_open');
  const delta = degrees(result.summary.peakDeviationRadians - open.peakDeviationRadians);
  $('sm-compare').textContent = `${delta >= 0 ? '+' : '−'}${f(Math.abs(delta), 4)}° gegenüber offener Sensor-Rückmeldung. Keine Bewertung der biologischen Richtigkeit.`;
  $('sm-motor-delta').textContent = f(result.summary.maxMotorCommandDifference, 5);
  $('sm-comparisons').replaceChildren();
  for (const row of result.comparison) { const tr = document.createElement('tr'); tr.classList.toggle('selected', row.condition === c.condition); for (const value of [names[row.condition], `${f(degrees(row.peakDeviationRadians), 4)}°`, `${f(degrees(row.rmsDeviationRadians), 4)}°`, f(row.maxMotorCommandDifference, 6), row.jointLimitSteps]) tr.append(element('td', value)); $('sm-comparisons').append(tr); }
  const previous = $('sm-neuron').value;
  $('sm-neuron').replaceChildren(...result.circuit.nodes.map(n => option(n.id, `${n.role} · ${n.cellType || 'unbekannter Typ'} · ${n.id}`)));
  if (result.circuit.nodes.some(n => n.id === previous)) $('sm-neuron').value = previous;
  else $('sm-neuron').value = result.circuit.nodes.find(n => n.role === 'sensor')?.id || result.circuit.nodes[0].id;
  const p = result.parameters;
  $('sm-parameters').textContent = `Modellparameter: Sensor τ ${p.sensorTau * 1000} ms; Nervenzelle τ ${p.neuronTau * 1000} ms; Beobachtungsverzögerung ${p.observationDelay * 1000} ms; Graphverstärkung ${p.graphGain}; Grundaktivität ${p.baselineRate}; tonische Muskelaktivierung ${p.tonicMotorActivation}. Integration alle ${p.dt * 1000} ms, Anzeige alle 10 ms. Winkelreferenz ist die anfängliche Ruhestellung. Die übrigen fünf Beine bleiben außerhalb des sensorischen Experiments.`;
  traces(); drawFrame();
}
worker.onmessage = ({ data }) => { if (data.requestId !== requestId) return; if (data.error) { $('sm-status').textContent = `Berechnung nicht verfügbar: ${data.error}`; $('sm-status').classList.add('error'); return; } result = data; timeMs = 0; renderResults(); busy(false); };
worker.onerror = event => { $('sm-status').textContent = `Regelkreis konnte nicht berechnet werden: ${event.message}`; $('sm-status').classList.add('error'); busy(true); };
$('sm-polarity').replaceChildren(...POLARITY_HYPOTHESES.map((p, i) => option(p.id, `Hypothese ${i + 1}: Position ${plus(p.claw)} / Bewegung ${plus(p.hook)}`)));
$('sm-condition').replaceChildren(...SENSORIMOTOR_CONDITIONS.map(c => option(c, names[c])));
for (const id of ['sm-detector', 'sm-polarity', 'sm-condition']) $(id).addEventListener('change', run);
$('sm-neuron').addEventListener('change', () => { if (result) neuronDetail(currentFrame()); });
$('sm-play').addEventListener('click', () => { if (timeMs >= 4000) timeMs = 0; setPlaying(!playing); });
$('sm-reset').addEventListener('click', () => { setPlaying(false); timeMs = 0; drawFrame(); });
$('sm-scrubber').addEventListener('input', () => { setPlaying(false); timeMs = Number($('sm-scrubber').value); drawFrame(); });
function animate(now) { const dt = Math.min(now - last || 0, 100); last = now; if (playing && result) { timeMs = Math.min(4000, timeMs + dt); drawFrame(); if (timeMs >= 4000) setPlaying(false); } renderer?.render(scene, camera); requestAnimationFrame(animate); }
requestAnimationFrame(animate); run();
