import * as THREE from './vendor/three.module.js';
import { createArticulatedFly } from './articulated-fly.mjs';
import { makeMotorPools, motorTrial, MOTOR_TESTS } from './joint_motor_model.mjs';
const $ = (id) => document.getElementById(id);
const n = (value, digits = 1) => Number(value || 0).toLocaleString('de-DE', { minimumFractionDigits: digits, maximumFractionDigits: digits });
const deg = (value) => value * 180 / Math.PI;
const el = (tag, content, className) => { const e = document.createElement(tag); e.textContent = content; if (className) e.className = className; return e; };
const opt = (label, value) => { const e = el('option', label); e.value = value; return e; };
const legNames = { LF: 'Linkes Vorderbein', RF: 'Rechtes Vorderbein', LM: 'Linkes Mittelbein', RM: 'Rechtes Mittelbein', LH: 'Linkes Hinterbein', RH: 'Rechtes Hinterbein' };
let dataset, motors, pools, trial, selectedPath; let playing = false; let timeMs = 0; let last = 0; let comparisons = new Map();

const scene = new THREE.Scene(); scene.background = new THREE.Color('#0b1e28');
const camera = new THREE.PerspectiveCamera(40, 1, .05, 100); let orbit = { angle: -.65, elevation: .32, radius: 4.8 }; let drag;
function aim() { camera.position.set(Math.sin(orbit.angle) * Math.cos(orbit.elevation) * orbit.radius,
  1 + Math.sin(orbit.elevation) * orbit.radius, Math.cos(orbit.angle) * Math.cos(orbit.elevation) * orbit.radius); camera.lookAt(0, 1, -.1); }
aim(); let renderer, rig, selectedLine;
try {
  renderer = new THREE.WebGLRenderer({ antialias: true }); renderer.setPixelRatio(Math.min(devicePixelRatio, 2)); renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFShadowMap;
  $('motor-scene').append(renderer.domElement); scene.add(new THREE.HemisphereLight('#e2f1ef', '#76624a', 2.3));
  const key = new THREE.DirectionalLight('#fff2d9', 3.2); key.position.set(3, 6, 4); key.castShadow = true; key.shadow.mapSize.set(1024, 1024); scene.add(key);
  const floor = new THREE.Mesh(new THREE.CircleGeometry(4, 90), new THREE.MeshStandardMaterial({ color: '#173441', roughness: .9 })); floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);
  const grid = new THREE.GridHelper(8, 16, '#376071', '#24434f'); grid.position.y = .004; scene.add(grid);
  const holder = new THREE.Mesh(new THREE.CylinderGeometry(.055, .10, 1.07, 12), new THREE.MeshStandardMaterial({ color: '#71848b', metalness: .6, roughness: .4 })); holder.position.set(0, .535, -.1); scene.add(holder);
  const cradle = new THREE.Mesh(new THREE.SphereGeometry(.13, 16, 12), new THREE.MeshStandardMaterial({ color: '#71848b', metalness: .6, roughness: .4 })); cradle.scale.set(1, .5, 1.5); cradle.position.set(0, 1.11, -.1); scene.add(cradle);
  rig = createArticulatedFly(scene); rig.setContactsVisible(false);
  selectedLine = new THREE.Line(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: '#78caca', transparent: true, opacity: .9, depthTest: false })); selectedLine.renderOrder = 5; scene.add(selectedLine);
  new ResizeObserver(() => { const w = $('motor-scene').clientWidth; const h = $('motor-scene').clientHeight; camera.aspect = w / h; camera.updateProjectionMatrix(); renderer.setSize(w, h); }).observe($('motor-scene'));
  $('motor-scene').addEventListener('pointerdown', (e) => { drag = { x: e.clientX, y: e.clientY, ...orbit }; $('motor-scene').setPointerCapture(e.pointerId); });
  $('motor-scene').addEventListener('pointermove', (e) => { if (!drag) return; orbit.angle = drag.angle - (e.clientX - drag.x) * .009; orbit.elevation = Math.max(.08, Math.min(1.3, drag.elevation + (e.clientY - drag.y) * .008)); aim(); });
  $('motor-scene').addEventListener('pointerup', () => { drag = null; }); $('motor-scene').addEventListener('pointercancel', () => { drag = null; });
  $('motor-scene').addEventListener('wheel', (e) => { e.preventDefault(); orbit.radius = Math.max(2.5, Math.min(10, orbit.radius * Math.exp(e.deltaY * .001))); aim(); }, { passive: false });
} catch (error) { $('motor-scene-error').hidden = false; $('motor-scene-error').textContent = `3D-Ansicht nicht verfügbar: ${error.message}`; }

function play(value) { playing = value; $('motor-play').textContent = value ? 'Ⅱ Pausieren' : '▶ Test abspielen'; }
function selectedFrame() { return trial.frames[Math.min(trial.frames.length - 1, Math.floor(timeMs / 2))]; }
function motorById(id) { return motors.find((m) => m.banc_888_id === id); }
function motorOptions(keep = 'pool') {
  const leg = $('motor-leg').value; const dropdown = $('motor-selection'); dropdown.replaceChildren(opt('Vollständiger jeweiliger Motorpool', 'pool'));
  for (const [kind, title] of [['flexor', 'Beuger'], ['extensor', 'Strecker']]) {
    const group = document.createElement('optgroup'); group.label = `${title} · ${pools[leg][kind].length} IDs`;
    for (const id of pools[leg][kind]) { const motor = motorById(id); group.append(opt(`${motor.cell_type || title} · ${id}`, id)); } dropdown.append(group);
  }
  if ([...pools[leg].flexor, ...pools[leg].extensor].includes(keep)) dropdown.value = keep;
}
function computeTrial() {
  if (!pools) return; play(false); timeMs = 0;
  const condition = $('motor-condition').value; const amplitude = Number($('motor-amplitude').value); const selection = $('motor-selection').value;
  trial = motorTrial(pools, { leg: $('motor-leg').value, condition, amplitude, selection });
  $('amplitude-label').textContent = n(amplitude, 2); $('motor-selection').disabled = condition.startsWith('coactivation') || condition === 'baseline' || condition === 'passive_disturbance';
  $('motor-test-description').textContent = MOTOR_TESTS.find((t) => t.id === condition).description + (condition.startsWith('coactivation') ? ' Beide vollständigen Gegenpools werden gleich stark angeregt.' : '');
  $('motor-id-summary').textContent = `${trial.directlyDrivenIds.length} BANC-Motor-IDs`;
  $('motor-source-note').textContent = `Direkte Aktivierung; ${trial.ablatedIds.length} IDs ausgeschaltet. Kein simuliertes DN- oder Premotorsignal.`;
  $('motor-peak').textContent = `${n(deg(trial.peakDeviationRadians))}°`;
  const index = trial.frames[0].body.legs.findIndex((l) => l.id === trial.leg);
  $('motor-coactivation').textContent = n(Math.max(...trial.frames.map((f) => f.body.legs[index].motor.coactivation)), 2);
  $('selected-leg-label').textContent = legNames[trial.leg];
  $('motor-play').disabled = false; $('motor-reset').disabled = false; $('motor-scrubber').disabled = false;
  drawTrace(); renderComparisons(); drawFrame(); renderPaths();
}
function drawFrame() {
  if (!trial) return; const frame = selectedFrame(); const leg = frame.body.legs.find((l) => l.id === trial.leg);
  rig?.update({ ...frame.body, timeSeconds: 0 }, {});
  if (selectedLine) { const points = leg.pointsLocal.map((p) => new THREE.Vector3(p[0], p[1] + frame.body.pose.height, p[2])); selectedLine.geometry.dispose(); selectedLine.geometry = new THREE.BufferGeometry().setFromPoints(points); }
  $('motor-time').textContent = `${n(timeMs, 0)} / 3.000 ms`; $('motor-scrubber').value = timeMs;
  $('motor-angle').textContent = `${n(deg(leg.jointAngles.femurTibia))}°`;
  $('motor-activation').textContent = `${n(leg.motor.flexor, 2)} / ${n(leg.motor.extensor, 2)}`;
  $('motor-torque').textContent = n(leg.motor.driveTorque, 2); $('motor-stiffness').textContent = n(leg.motor.stiffness, 2);
  const cursor = $('motor-cursor'); if (cursor) { const x = 48 + timeMs / 3000 * 932; cursor.setAttribute('x1', x); cursor.setAttribute('x2', x); }
}
const SVG = 'http://www.w3.org/2000/svg';
function svg(tag, attrs, content) { const e = document.createElementNS(SVG, tag); for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v); if (content) e.textContent = content; return e; }
function drawTrace() {
  const chart = $('motor-trace'); chart.replaceChildren(); const x = (t) => 48 + t / 3000 * 932; const y = (v) => 140 - v * 125;
  chart.append(svg('rect', { x: x(400), y: 10, width: x(2400) - x(400), height: 130, fill: '#fff', opacity: .04 }));
  for (const value of [0, 90, 180]) { chart.append(svg('line', { x1: 48, x2: 980, y1: y(value / 180), y2: y(value / 180), stroke: '#28404b' })); chart.append(svg('text', { x: 40, y: y(value / 180) + 4, fill: '#9ab0b7', 'text-anchor': 'end', 'font-size': 11 }, `${value}°`)); }
  const index = trial.frames[0].body.legs.findIndex((l) => l.id === trial.leg);
  for (const [color, value] of [['#c4e4b0', (l) => l.jointAngles.femurTibia / Math.PI], ['#78caca', (l) => l.motor.flexor], ['#e4ac78', (l) => l.motor.extensor]]) {
    chart.append(svg('polyline', { points: trial.frames.filter((_, i) => i % 5 === 0).map((f) => `${x(f.tMs)},${y(value(f.body.legs[index]))}`).join(' '), stroke: color, 'stroke-width': 2, fill: 'none' }));
  }
  chart.append(svg('text', { x: 984, y: 15, fill: '#9ab0b7', 'text-anchor': 'end', 'font-size': 10 }, 'Aktivierung 0–1'));
  chart.append(svg('line', { id: 'motor-cursor', x1: 48, x2: 48, y1: 8, y2: 145, stroke: '#eee', 'stroke-width': 1 }));
}
function renderComparisons() {
  const key = `${trial.leg}:${trial.amplitude}`;
  if (!comparisons.has(key)) comparisons.set(key, MOTOR_TESTS.map((test) => {
    const r = motorTrial(pools, { leg: trial.leg, condition: test.id, amplitude: trial.amplitude, selection: 'pool' });
    const index = r.frames[0].body.legs.findIndex((l) => l.id === r.leg);
    return { id: test.id, label: test.label, ids: r.directlyDrivenIds.length, deviation: r.peakDeviationRadians,
      coactivation: Math.max(...r.frames.map((f) => f.body.legs[index].motor.coactivation)), stiffness: Math.max(...r.frames.map((f) => f.body.legs[index].motor.stiffness)) };
  }));
  $('motor-comparisons').replaceChildren();
  for (const result of comparisons.get(key)) {
    const row = document.createElement('tr'); row.classList.toggle('selected', trial.condition === result.id && trial.selection === 'pool'); row.tabIndex = 0;
    const choose = () => { $('motor-condition').value = result.id; $('motor-selection').value = 'pool'; computeTrial(); };
    row.addEventListener('click', choose); row.addEventListener('keydown', (event) => { if (event.key === 'Enter') choose(); });
    for (const value of [result.label, n(result.ids, 0), `${n(deg(result.deviation))}°`, n(result.coactivation, 2), n(result.stiffness, 2)]) row.append(el('td', value)); $('motor-comparisons').append(row);
  }
}
function renderPaths() {
  if (!dataset) return; const current = $('motor-path').value;
  const motorIds = new Set([...pools[trial.leg].flexor, ...pools[trial.leg].extensor]);
  const paths = dataset.paths.filter((p) => motorIds.has(p.motorId));
  $('motor-path').replaceChildren(...paths.map((path) => { const dn = dataset.dns.find((d) => d.id === path.dnId); const motor = motorById(path.motorId);
    return opt(`${dn?.type || path.dnId} ${dn?.side || ''} → ${motor.cell_type || path.motorId} · ${path.hops} Kanten`, path.id); }));
  if (!paths.length) { $('motor-path').append(opt('Kein exportiertes Pfadbeispiel für dieses Gelenk', '')); $('path-chain').replaceChildren(); $('path-details').textContent = 'Fehlende Pfadbeispiele belegen keine fehlende anatomische Verbindung. Die separat publizierte Motoraktion bleibt prüfbar.'; $('test-path-motor').disabled = true; return; }
  if (paths.some((p) => p.id === current)) $('motor-path').value = current;
  $('motor-path').disabled = false; drawPath();
}
function drawPath() {
  selectedPath = dataset.paths.find((p) => String(p.id) === $('motor-path').value); $('path-chain').replaceChildren();
  if (!selectedPath) return;
  selectedPath.nodes.forEach((node, i) => {
    if (i) { const edge = selectedPath.edges[i - 1]; const arrow = el('div', '', 'path-edge'); arrow.append(el('span', `v2: ${edge.countV2 ?? '–'}`), el('b', '→'), el('span', `v3: ${edge.countV3 ?? '–'}`)); $('path-chain').append(arrow); }
    const card = el('div', '', 'path-node'); card.append(el('span', i === 0 ? 'ABSTEIGENDES NEURON' : i === selectedPath.nodes.length - 1 ? 'MOTORNEURON' : 'VORGESCHALTETE ZELLE', 'role'), el('strong', node.type || 'Typ nicht annotiert'), el('code', node.id), el('span', node.side || '', 'small muted')); $('path-chain').append(card);
  });
  const motor = motorById(selectedPath.motorId); const action = motor.cell_function_detailed === 'flex_femur_tibia_joint' ? 'Femur–Tibia beugen' : 'Femur–Tibia strecken';
  const arrow = el('div', '', 'path-edge'); arrow.append(el('span', 'Annotation'), el('b', '→')); $('path-chain').append(arrow);
  const muscle = el('div', '', 'path-node'); muscle.append(el('span', 'PUBLIZIERTE MUSKELAKTION', 'role'), el('strong', action), el('span', motor.peripheral_target_type || 'Muskelziel nicht benannt', 'small')); $('path-chain').append(muscle);
  $('path-details').replaceChildren(el('p', `Bein: ${legNames[motor.candidate_model_leg]}. Pfad-ID: ${selectedPath.id}. Minimale Kantenzahl v2/v3: ${selectedPath.bottleneckV2 ?? '–'} / ${selectedPath.bottleneckV3 ?? '–'}.`),
    el('p', 'Diese Kette ist strukturell belegt. Synapsenzahlen bestimmen weder Aktionspotenziale noch Muskelkräfte. Der folgende Knopf aktiviert ausschließlich die genannte Motor-ID direkt.', 'path-source-note'));
  $('test-path-motor').disabled = false;
}
function animate(now) { const dt = Math.min(now - last || 0, 100); last = now; if (playing && trial) { timeMs = Math.min(trial.durationMs, timeMs + dt); drawFrame(); if (timeMs >= trial.durationMs) play(false); } renderer?.render(scene, camera); requestAnimationFrame(animate); }
requestAnimationFrame(animate);
$('motor-leg').addEventListener('change', () => { motorOptions(); computeTrial(); });
$('motor-condition').addEventListener('change', computeTrial);
$('motor-amplitude').addEventListener('change', computeTrial); $('motor-amplitude').addEventListener('input', () => { $('amplitude-label').textContent = n($('motor-amplitude').value, 2); });
$('motor-selection').addEventListener('change', () => { const motor = motorById($('motor-selection').value); if (motor) $('motor-condition').value = motor.cell_function_detailed === 'flex_femur_tibia_joint' ? 'flexor' : 'extensor'; computeTrial(); });
$('motor-play').addEventListener('click', () => { if (timeMs >= 3000) timeMs = 0; play(!playing); drawFrame(); });
$('motor-reset').addEventListener('click', () => { play(false); timeMs = 0; drawFrame(); });
$('motor-scrubber').addEventListener('input', () => { play(false); timeMs = Number($('motor-scrubber').value); drawFrame(); });
$('motor-path').addEventListener('change', drawPath);
$('test-path-motor').addEventListener('click', () => { const motor = motorById(selectedPath.motorId); $('motor-leg').value = motor.candidate_model_leg; motorOptions(motor.banc_888_id); $('motor-condition').value = motor.cell_function_detailed === 'flex_femur_tibia_joint' ? 'flexor' : 'extensor'; computeTrial(); $('motor-scene').scrollIntoView({ behavior: 'smooth', block: 'center' }); });

try {
  const response = await fetch('./data/motor_pathways.json', { cache: 'no-cache' }); if (!response.ok) throw new Error(`Pfaddaten HTTP ${response.status}`); dataset = await response.json();
  if (!Array.isArray(dataset.motors) || !Array.isArray(dataset.paths)) throw new Error('Unvollständige Motor-/Pfaddaten');
  motors = dataset.motors; pools = makeMotorPools(motors);
  $('motor-condition').replaceChildren(...MOTOR_TESTS.map((t) => opt(t.label, t.id))); $('motor-condition').value = 'flexor'; $('motor-condition').disabled = false;
  motorOptions(); computeTrial(); $('motor-load').textContent = `${motors.length} Motorneuronen · 113 Femur–Tibia-IDs · ${dataset.paths.length} strukturelle Pfadbeispiele`;
} catch (error) { $('motor-load').textContent = `Daten nicht verfügbar: ${error.message}`; $('motor-load').classList.add('error'); }
