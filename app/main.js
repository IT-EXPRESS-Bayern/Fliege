import * as THREE from './vendor/three.module.js';
import { CONTROL_KIND } from './control.mjs';
import { ArticulatedBody } from './body-kinematics.mjs';
import { createArticulatedFly } from './articulated-fly.mjs';
import { AutonomousController } from './autonomy.mjs';
import { BrainWorkerBridge, matchesLoadedOriginalGraph,
  ORIGINAL_GRAPH_DATASET } from './brain-bridge.mjs';
import { encodeSensoryInput, validateSensorAdapterSpec } from './sensor-map.mjs';

const mount = document.querySelector('#scene');
const readout = {
  activity: document.querySelector('#activity'),
  contacts: document.querySelector('#body-contacts'),
  gait: document.querySelector('#body-gait'),
  source: document.querySelector('#source'),
  forward: document.querySelector('#forward'),
  turn: document.querySelector('#turn'),
  arousal: document.querySelector('#arousal'),
  fatigue: document.querySelector('#fatigue'),
  groomNeed: document.querySelector('#groom-need'),
  wallSignal: document.querySelector('#wall-signal'),
  modelInspector: document.querySelector('#model-inspector'),
  coords: document.querySelector('#coords'),
  toggle: document.querySelector('#toggle'),
  reset: document.querySelector('#reset'),
  modeDemo: document.querySelector('#mode-demo'),
  modeInspect: document.querySelector('#mode-inspect'),
  modeBrain: document.querySelector('#mode-brain'),
  modeHint: document.querySelector('#mode-hint'),
  panelNote: document.querySelector('#panel-note'),
  couplingCard: document.querySelector('#coupling-card'),
  couplingTitle: document.querySelector('#coupling-title'),
  couplingDetail: document.querySelector('#coupling-detail'),
  downloadState: document.querySelector('#download-state'),
  downloadDetail: document.querySelector('#download-detail'),
  downloadProgress: document.querySelector('#download-progress'),
  graphState: document.querySelector('#graph-state'),
  graphDetail: document.querySelector('#graph-detail'),
  adapterState: document.querySelector('#adapter-state'),
  adapterDetail: document.querySelector('#adapter-detail'),
  inspectPanel: document.querySelector('#inspect-panel'),
  inspectDataset: document.querySelector('#inspect-dataset'),
  inspectNodes: document.querySelector('#inspect-nodes'),
  inspectEdges: document.querySelector('#inspect-edges'),
  inspectMotor: document.querySelector('#inspect-motor'),
  candidateList: document.querySelector('#candidate-list'),
};

const ARENA_RADIUS = 5.65;
const scene = new THREE.Scene();
scene.background = new THREE.Color('#091d27');
scene.fog = new THREE.FogExp2('#091d27', 0.025);

const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.5;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowMap;
mount.appendChild(renderer.domElement);

const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
let cameraAzimuth = 0.62;
let cameraElevation = 0.76;
let cameraDistance = 6.8;
let followFly = true;
const cameraTarget = new THREE.Vector3(0, 0.3, 0);
function positionCamera() {
  camera.position.set(
    cameraTarget.x + Math.sin(cameraAzimuth) * Math.cos(cameraElevation) * cameraDistance,
    cameraTarget.y + Math.sin(cameraElevation) * cameraDistance,
    cameraTarget.z + Math.cos(cameraAzimuth) * Math.cos(cameraElevation) * cameraDistance,
  );
  camera.lookAt(cameraTarget);
}
positionCamera();

const ambient = new THREE.HemisphereLight('#c6ecdf', '#163138', 2.2);
scene.add(ambient);
const sun = new THREE.DirectionalLight('#d6eed4', 3.0);
sun.position.set(-4, 10, 5);
sun.castShadow = true;
sun.shadow.mapSize.set(1024, 1024);
sun.shadow.camera.left = -9;
sun.shadow.camera.right = 9;
sun.shadow.camera.top = 9;
sun.shadow.camera.bottom = -9;
sun.shadow.bias = -0.0003;
scene.add(sun);
const coolLight = new THREE.PointLight('#68b4bd', 70, 18);
coolLight.position.set(6, 4, -5);
scene.add(coolLight);

const floorMat = new THREE.MeshStandardMaterial({ color: '#234853', roughness: 0.93, metalness: 0.05 });
const floor = new THREE.Mesh(new THREE.CircleGeometry(ARENA_RADIUS + 0.55, 96), floorMat);
floor.rotation.x = -Math.PI / 2;
floor.receiveShadow = true;
scene.add(floor);

const platform = new THREE.Mesh(
  new THREE.CylinderGeometry(ARENA_RADIUS + 0.55, ARENA_RADIUS + 0.67, 0.23, 96),
  new THREE.MeshStandardMaterial({ color: '#14313c', roughness: 0.7, metalness: 0.18 }),
);
platform.position.y = -0.16;
platform.receiveShadow = true;
scene.add(platform);

function addCircle(radius, color, opacity, tube = 0.012, y = 0.014) {
  const ring = new THREE.Mesh(
    new THREE.TorusGeometry(radius, tube, 8, 96),
    new THREE.MeshBasicMaterial({ color, transparent: true, opacity }),
  );
  ring.rotation.x = -Math.PI / 2;
  ring.position.y = y;
  scene.add(ring);
}
addCircle(ARENA_RADIUS + 0.38, '#aed8bf', 0.72, 0.025, 0.012);
addCircle(ARENA_RADIUS, '#71a4a7', 0.43, 0.016, 0.018);
addCircle(3.25, '#79a9a7', 0.15, 0.008, 0.018);

const grid = new THREE.GridHelper(11, 22, '#5e9395', '#5e9395');
grid.position.y = 0.019;
grid.material.transparent = true;
grid.material.opacity = 0.12;
scene.add(grid);

for (let i = 0; i < 24; i++) {
  const angle = (i / 24) * Math.PI * 2;
  const marker = new THREE.Mesh(
    new THREE.BoxGeometry(i % 6 === 0 ? 0.10 : 0.055, 0.025, i % 6 === 0 ? 0.42 : 0.21),
    new THREE.MeshBasicMaterial({ color: i % 6 === 0 ? '#c0dbad' : '#80aaab', transparent: true, opacity: 0.57 }),
  );
  marker.position.set(Math.sin(angle) * (ARENA_RADIUS - 0.26), 0.026, Math.cos(angle) * (ARENA_RADIUS - 0.26));
  marker.rotation.y = angle;
  scene.add(marker);
}

const articulatedFly = createArticulatedFly(scene);

const trailMaterial = new THREE.LineBasicMaterial({ color: '#c8df9e', transparent: true, opacity: 0.68 });
let trailGeometry = new THREE.BufferGeometry();
const trail = new THREE.Line(trailGeometry, trailMaterial);
scene.add(trail);
let trailPoints = [];
let trailElapsed = 0;

let controller = new AutonomousController();
const state = { x: 0, z: 0, yaw: 0.5, speed: 0, yawRate: 0, elapsed: 0 };
const body = new ArticulatedBody(state);
let bodyFrame = body.snapshot();
articulatedFly.update(bodyFrame, { wing: 0 });
let paused = false;
let previousTime = performance.now();
let hudElapsed = 0;
let mode = 'demo';
let graphStatus = { state: 'missing', reason: 'Graph noch nicht erstellt' };
const bridge = new BrainWorkerBridge(updateConnectionUi);
const neutralControl = { forward: 0, turn: 0, wing: 0, groom: 0 };
let automaticWorker = null;
let automaticStartAttempted = false;
let candidatesLoaded = false;
let candidatesLoading = false;
let sensorAdapter = null;

function observation() {
  return { x: state.x, z: state.z, yaw: state.yaw, arenaRadius: ARENA_RADIUS, body: body.snapshot() };
}

function graphLoaded() {
  return bridge.status === 'ready' && matchesLoadedOriginalGraph(graphStatus, bridge.metadata);
}

function brainAvailable() {
  return graphLoaded() && bridge.motorConfigured &&
    sensorAdapter?.dataset === graphStatus.dataset;
}

function updateConnectionUi() {
  const canInspect = graphLoaded();
  const canControl = brainAvailable();
  if (!canInspect && mode === 'inspect') mode = 'demo';
  if (!canControl && mode === 'brain') mode = canInspect ? 'inspect' : 'demo';
  readout.modeInspect.disabled = !canInspect;
  readout.modeBrain.disabled = !canControl;
  readout.modeDemo.setAttribute('aria-pressed', String(mode === 'demo'));
  readout.modeInspect.setAttribute('aria-pressed', String(mode === 'inspect'));
  readout.modeBrain.setAttribute('aria-pressed', String(mode === 'brain'));
  readout.couplingCard.classList.toggle('graph-active', mode !== 'demo');
  readout.couplingTitle.textContent = mode === 'brain'
    ? 'GRAPH-MODELL AKTIV' : mode === 'inspect' ? 'GRAPH-INSPEKTION' : 'EIGENAKTIVITÄTSMODELL';
  readout.couplingDetail.textContent = mode === 'brain'
    ? 'Aus FlyWire-Originaldaten · Körperkopplung hypothetisch'
    : mode === 'inspect' ? 'Vollständiger Proofread-Graph · keine Körpersteuerung'
      : 'Abstrakte Modellpopulationen · kein FlyWire-Antrieb';
  readout.panelNote.textContent = mode === 'brain'
    ? 'Bewegung kommt aus einer quellenbelegten, aber hypothetischen Motorzuordnung. Sensoren und Körper bleiben vereinfacht.'
    : mode === 'inspect' ? 'Die Fliege ruht. Der echte Connectome-Graph ist geladen, steuert diesen Körper aber nicht.'
      : 'Ohne Zielvorgabe: interne Schwankungen und Zustände erzeugen Bewegung. Körperposition und Wandnähe wirken zurück. Alle Modellparameter sind hypothetisch.';
  readout.modelInspector.hidden = mode !== 'demo';
  if (graphStatus.state !== 'ready') {
    readout.modeHint.textContent = 'Graph wird vorbereitet. Die Fliege bewegt sich mit einem separaten, abstrakten Eigenaktivitätsmodell.';
  } else if (bridge.status === 'loading') {
    readout.modeHint.textContent = 'Vollständiger Proofread-Graph wird im Worker geladen (ca. 213 MB Graphdaten). Das Eigenaktivitätsmodell bleibt aktiv.';
  } else if (bridge.status === 'ready' && !canInspect) {
    readout.modeHint.textContent = 'Graph-Worker und lokaler Originalgraph melden unterschiedliche Datenstände oder Größen.';
  } else if (!canInspect) {
    readout.modeHint.textContent = 'Der Graph-Worker ist noch nicht bereit.';
  } else if (!canControl) {
    const missing = [!bridge.motorConfigured && 'Motorzuordnung', !sensorAdapter && 'Sensorzuordnung']
      .filter(Boolean).join(' und ');
    readout.modeHint.textContent = `Graph-Inspektion möglich. FlyWire-Steuerung bleibt ohne ${missing || 'passende Sensorzuordnung'} gesperrt.`;
  } else {
    readout.modeHint.textContent = mode === 'brain'
      ? 'Echte Connectome-Daten; die Zuordnung zur Körperbewegung ist eine explizite Hypothese.'
      : 'Quellenbelegte Motorhypothese vorhanden. Das Eigenaktivitätsmodell bleibt aktiv, bis FlyWire-Steuerung gewählt wird.';
  }
  const labels = {
    disconnected: 'Nicht verbunden', loading: 'Graph wird geladen …',
    ready: 'Graph geladen', error: 'Worker-Fehler',
  };
  readout.adapterState.textContent = labels[bridge.status] || 'Unbekannt';
  readout.adapterDetail.textContent = bridge.status === 'ready'
    ? `${bridge.metadata.nodeCount.toLocaleString('de-DE')} Knoten · ${bridge.motorConfigured ? 'Motorhypothese vorhanden' : 'keine Motorzuordnung'}`
    : bridge.message;
  readout.inspectPanel.hidden = mode !== 'inspect';
  if (canInspect) {
    readout.inspectDataset.textContent = `FAFB v783 · ${graphStatus.sourceFile || bridge.metadata.dataset}`;
    readout.inspectNodes.textContent = bridge.metadata.nodeCount.toLocaleString('de-DE');
    readout.inspectEdges.textContent = bridge.metadata.edgeCount.toLocaleString('de-DE');
    readout.inspectMotor.textContent = canControl ? 'Hypothese' : 'Gesperrt';
  }
}

function syncAutomaticWorker() {
  if (graphStatus.state !== 'ready') {
    if (automaticWorker) {
      bridge.detach();
      automaticWorker.terminate();
      automaticWorker = null;
    }
    automaticStartAttempted = false;
    return;
  }
  if (automaticStartAttempted || bridge.worker) return;
  automaticStartAttempted = true;
  if (typeof Worker !== 'function') {
    bridge.fail('Dieser Browser unterstützt keine Modul-Worker');
    return;
  }
  try {
    automaticWorker = new Worker('/brain/worker.mjs', { type: 'module' });
    bridge.attach(automaticWorker);
  } catch (error) {
    bridge.fail(`Graph-Worker konnte nicht gestartet werden: ${error.message}`);
  }
}

function formatBytes(value) {
  return value >= 1e9 ? `${(value / 1e9).toFixed(2)} GB`
    : value >= 1e6 ? `${(value / 1e6).toFixed(1)} MB`
      : `${(value / 1e3).toFixed(0)} kB`;
}

async function loadCandidateAnnotations() {
  if (candidatesLoaded || candidatesLoading || graphStatus.state !== 'ready') return;
  candidatesLoading = true;
  try {
    const response = await fetch('/api/brain-candidates', { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    const fragment = document.createDocumentFragment();
    for (const candidate of data.candidates || []) {
      const row = document.createElement('div');
      row.className = 'candidate-row';
      const label = document.createElement('span');
      label.className = 'candidate-name';
      label.textContent = candidate.label;
      const side = document.createElement('span');
      side.className = 'candidate-side';
      side.textContent = candidate.side === 'left' ? 'links' : candidate.side === 'right' ? 'rechts' : candidate.side;
      const title = document.createElement('div');
      title.append(label, side);
      const id = document.createElement('code');
      id.textContent = candidate.rootId;
      row.append(title, id);
      fragment.append(row);
    }
    readout.candidateList.replaceChildren(fragment);
    if (!data.candidates?.length) readout.candidateList.textContent = 'Keine passenden Annotationen gefunden.';
    candidatesLoaded = true;
  } catch {
    readout.candidateList.textContent = 'Annotationen derzeit nicht lesbar.';
  } finally {
    candidatesLoading = false;
  }
}

async function refreshStatuses() {
  const [downloadResult, graphResult] = await Promise.allSettled([
    fetch('/api/data-status', { cache: 'no-store' }).then(async (response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    }),
    fetch('/api/brain-status', { cache: 'no-store' }).then(async (response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    }),
  ]);
  if (downloadResult.status === 'fulfilled') {
    const data = downloadResult.value;
    const total = Number(data.bytes_total) || 1;
    const done = Number(data.bytes_done) || 0;
    const percent = Math.max(0, Math.min(100, done / total * 100));
    const files = data.records?.flatMap((record) => record.files || []) || [];
    const verified = files.filter((file) => file.state === 'geprüft').length;
    const present = files.filter((file) => Number(file.done) >= Number(file.size)).length;
    readout.downloadState.textContent = data.pipeline?.stage === 'complete' && percent >= 100
      ? 'Vollständig geladen' : `${percent.toFixed(1)} % geladen`;
    readout.downloadDetail.textContent = `${formatBytes(done)} / ${formatBytes(total)} · ${present}/${files.length} vorhanden · ${verified} Prüfsummen bestätigt`;
    readout.downloadProgress.style.width = `${percent}%`;
  } else {
    readout.downloadState.textContent = 'Statusdienst offline';
    readout.downloadDetail.textContent = 'Live-Downloadansicht derzeit nicht erreichbar';
    readout.downloadProgress.style.width = '0%';
  }
  graphStatus = graphResult.status === 'fulfilled'
    ? graphResult.value : { state: 'error', reason: 'Graphstatus nicht erreichbar' };
  if (graphStatus.state === 'ready' && graphStatus.dataset !== ORIGINAL_GRAPH_DATASET) {
    graphStatus = { state: 'error', reason: 'Server liefert noch den gefilterten Graphen · bitte App-Server neu starten' };
  }
  readout.graphState.textContent = graphStatus.state === 'ready'
    ? 'Vollständiger Graph bereit' : graphStatus.reason || 'Graphstatus unbekannt';
  readout.graphDetail.textContent = graphStatus.state === 'ready'
    ? `${Number(graphStatus.nodeCount).toLocaleString('de-DE')} Neuronen · ${Number(graphStatus.edgeCount).toLocaleString('de-DE')} Paare${graphStatus.synapseCount == null ? '' : ` · ${Number(graphStatus.synapseCount).toLocaleString('de-DE')} Synapsen`}`
    : 'brain/graph-original-v783';
  syncAutomaticWorker();
  loadCandidateAnnotations();
  updateConnectionUi();
}

// The actual brain/worker.mjs loads automatically once the graph is complete.
// It receives no motor map by default and therefore cannot control the body.
window.FlyDemo = Object.freeze({
  attachBrainWorker(worker) {
    if (automaticWorker) automaticWorker.terminate();
    automaticWorker = null;
    automaticStartAttempted = true;
    bridge.attach(worker);
  },
  detachBrainWorker() {
    bridge.detach();
    if (automaticWorker) automaticWorker.terminate();
    automaticWorker = null;
    automaticStartAttempted = true;
  },
  retryAutomaticWorker() {
    bridge.detach();
    if (automaticWorker) automaticWorker.terminate();
    automaticWorker = null;
    automaticStartAttempted = false;
    syncAutomaticWorker();
  },
  setMotorMap(spec) { bridge.setMotorMap(spec); },
  clearMotorMap() { bridge.clearMotorMap(); },
  setSensorAdapter(spec) {
    sensorAdapter = validateSensorAdapterSpec(spec);
    updateConnectionUi();
  },
  clearSensorAdapter() {
    sensorAdapter = null;
    updateConnectionUi();
  },
  selectDemo() { mode = 'demo'; updateConnectionUi(); },
  selectAutonomy() { mode = 'demo'; updateConnectionUi(); },
  selectInspect() {
    if (!graphLoaded()) throw new Error('Graph-Worker ist noch nicht bereit');
    mode = 'inspect';
    updateConnectionUi();
  },
  selectBrain() {
    if (!brainAvailable()) throw new Error('Graph oder quellenbelegte Motorzuordnung fehlen');
    mode = 'brain';
    updateConnectionUi();
  },
  getObservation() { return { ...observation(), timestampMs: performance.timeOrigin + performance.now() }; },
  getBodyObservation() { return body.snapshot(); },
  getStatus() { return { mode, graph: { ...graphStatus }, adapter: bridge.status,
    workerGraph: bridge.metadata ? { ...bridge.metadata } : null,
    motorMapConfigured: bridge.motorConfigured,
    sensorAdapterConfigured: Boolean(sensorAdapter),
    autonomy: controller.snapshot(), body: body.snapshot() }; },
  controlKind: CONTROL_KIND,
});
updateConnectionUi();
refreshStatuses();
setInterval(refreshStatuses, 3000);

function updateTrail(dt) {
  trailElapsed += dt;
  if (trailElapsed < 0.08) return;
  trailElapsed = 0;
  trailPoints.push(new THREE.Vector3(state.x, 0.044, state.z));
  if (trailPoints.length > 240) trailPoints.shift();
  const next = new THREE.BufferGeometry().setFromPoints(trailPoints);
  trail.geometry = next;
  trailGeometry.dispose();
  trailGeometry = next;
}

function updateFly(control, dt) {
  // Smooth velocity commands; the body's ground contacts are kinematic constraints.
  const decay = 1 - Math.exp(-dt * 7);
  // A strong grooming command occupies the front legs. Resolve conflicting
  // abstract walking commands here, before lifting those legs off the floor.
  const locomotionGain = (control.groom || 0) > 0.55 ? 0 : 1;
  state.speed += ((control.forward || 0) * 1.7 * locomotionGain - state.speed) * decay;
  state.yawRate += ((control.turn || 0) * 1.6 * locomotionGain - state.yawRate) * decay;
  state.yaw += state.yawRate * dt;
  state.x += Math.sin(state.yaw) * state.speed * dt;
  state.z += Math.cos(state.yaw) * state.speed * dt;
  const radius = Math.hypot(state.x, state.z);
  if (radius > ARENA_RADIUS - 0.55) {
    const factor = (ARENA_RADIUS - 0.55) / radius;
    state.x *= factor;
    state.z *= factor;
  }
  state.elapsed += dt;
  bodyFrame = body.update(state, control, dt);
  articulatedFly.update(bodyFrame, control);
  updateTrail(dt);
}

function updateHud(control, signalPresent, dt) {
  hudElapsed += dt;
  if (hudElapsed < 0.1) return;
  hudElapsed = 0;
  readout.activity.textContent = mode === 'brain'
    ? signalPresent ? 'Graphsteuerung' : 'Warte auf Signal'
    : mode === 'inspect' ? 'Graph-Inspektion' : control.activity;
  readout.source.textContent = mode === 'brain'
    ? signalPresent ? 'Graph-Adapter' : 'Signal fehlt'
    : mode === 'inspect' ? 'Keine Körpersteuerung' : 'Abstraktes Aktivitätsmodell';
  readout.forward.textContent = control.forward.toFixed(2);
  readout.contacts.textContent = `${bodyFrame.contacts} / 6`;
  readout.gait.textContent = bodyFrame.gaitFrequencyHz > 0 ? `${bodyFrame.gaitFrequencyHz.toFixed(1)} Hz` : 'Ruhe';
  for (const leg of bodyFrame.legs) {
    const element = document.querySelector(`#contact-${leg.id}`);
    element.dataset.phase = leg.phase;
    element.dataset.contact = String(leg.contact);
    element.title = `${leg.id}: ${leg.contact ? 'Bodenkontakt' : leg.phase === 'groom' ? 'Putzen' : 'Schwung'}; Knie ${(leg.jointAngles.femurTibia * 180 / Math.PI).toFixed(0)}°`;
  }
  readout.turn.textContent = `${control.turn >= 0 ? '+' : ''}${control.turn.toFixed(2)}`;
  readout.coords.textContent = `X ${state.x >= 0 ? '+' : ''}${state.x.toFixed(1)}   Z ${state.z >= 0 ? '+' : ''}${state.z.toFixed(1)}`;
  if (mode === 'demo') {
    const inner = controller.snapshot();
    readout.arousal.textContent = inner.arousal.toFixed(2);
    readout.fatigue.textContent = inner.fatigue.toFixed(2);
    readout.groomNeed.textContent = inner.groomNeed.toFixed(2);
    readout.wallSignal.textContent = inner.wall.ahead.toFixed(2);
  }
}

function animate(now) {
  requestAnimationFrame(animate);
  const dt = Math.max(0, Math.min((now - previousTime) / 1000, 0.05));
  previousTime = now;
  if (!paused) {
    const nowMs = performance.timeOrigin + now;
    const demo = controller.next(observation(), dt, nowMs);
    if (mode === 'brain') {
      try {
        const input = encodeSensoryInput(sensorAdapter, observation());
        bridge.step(nowMs, Math.max(1, Math.round(dt * 1000)), input);
      } catch (error) {
        sensorAdapter = null;
        updateConnectionUi();
        readout.modeHint.textContent = `Sensoradapter-Fehler: ${error.message}`;
      }
    }
    const brainFrame = mode === 'brain' ? bridge.sample(nowMs) : null;
    const control = mode === 'demo' ? demo : mode === 'brain' ? (brainFrame || neutralControl) : neutralControl;
    updateFly(control, dt);
    updateHud(control, Boolean(brainFrame), dt);
  }
  const target = followFly ? new THREE.Vector3(state.x, 0.25, state.z) : new THREE.Vector3(0, 0, 0);
  cameraTarget.lerp(target, 1 - Math.exp(-dt * 5));
  positionCamera();
  renderer.render(scene, camera);
}
requestAnimationFrame(animate);

readout.toggle.addEventListener('click', () => {
  paused = !paused;
  readout.toggle.innerHTML = paused ? '▶ &nbsp; Fortsetzen' : '⏸ &nbsp; Pausieren';
});
readout.reset.addEventListener('click', () => {
  controller = new AutonomousController();
  bridge.reset();
  Object.assign(state, { x: 0, z: 0, yaw: 0.5, speed: 0, yawRate: 0, elapsed: 0 });
  body.reset(state);
  bodyFrame = body.snapshot();
  articulatedFly.update(bodyFrame, neutralControl);
  trailPoints = [];
  trailGeometry.dispose();
  trailGeometry = new THREE.BufferGeometry();
  trail.geometry = trailGeometry;
  paused = false;
  readout.toggle.innerHTML = '⏸ &nbsp; Pausieren';
  readout.source.textContent = mode === 'brain' ? 'Signal fehlt' : mode === 'inspect' ? 'Keine Körpersteuerung' : 'Abstraktes Aktivitätsmodell';
  readout.activity.textContent = mode === 'brain' ? 'Warte auf Signal' : mode === 'inspect' ? 'Graph-Inspektion' : 'Laufen';
});
readout.modeDemo.addEventListener('click', () => {
  mode = 'demo';
  updateConnectionUi();
});
readout.modeInspect.addEventListener('click', () => {
  if (graphLoaded()) {
    mode = 'inspect';
    updateConnectionUi();
  }
});
readout.modeBrain.addEventListener('click', () => {
  if (brainAvailable()) {
    mode = 'brain';
    updateConnectionUi();
  }
});

const followButton = document.querySelector('#follow-fly');
followButton.addEventListener('click', () => {
  followFly = !followFly;
  followButton.setAttribute('aria-pressed', String(followFly));
  followButton.textContent = followFly ? 'Nahansicht · folgt der Fliege' : 'Arenaübersicht';
  cameraDistance = followFly ? 6.8 : 17;
});
document.querySelector('#show-contacts').addEventListener('change', (event) => {
  articulatedFly.setContactsVisible(event.target.checked);
});

let dragging = false;
let lastPointerX = 0;
let lastPointerY = 0;
renderer.domElement.addEventListener('pointerdown', (event) => {
  dragging = true;
  lastPointerX = event.clientX;
  lastPointerY = event.clientY;
  renderer.domElement.setPointerCapture(event.pointerId);
});
renderer.domElement.addEventListener('pointermove', (event) => {
  if (!dragging) return;
  cameraAzimuth -= (event.clientX - lastPointerX) * 0.006;
  cameraElevation = THREE.MathUtils.clamp(cameraElevation + (event.clientY - lastPointerY) * 0.006, 0.18, 1.42);
  lastPointerX = event.clientX;
  lastPointerY = event.clientY;
  positionCamera();
});
renderer.domElement.addEventListener('pointerup', () => { dragging = false; });
renderer.domElement.addEventListener('pointercancel', () => { dragging = false; });
renderer.domElement.addEventListener('wheel', (event) => {
  event.preventDefault();
  cameraDistance = THREE.MathUtils.clamp(cameraDistance + Math.sign(event.deltaY) * 0.55, 3.8, 28);
  positionCamera();
}, { passive: false });

const resize = () => {
  const width = mount.clientWidth;
  const height = mount.clientHeight;
  if (!width || !height) return;
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
};
new ResizeObserver(resize).observe(mount);
resize();
