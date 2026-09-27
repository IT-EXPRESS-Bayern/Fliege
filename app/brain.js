import * as THREE from './vendor/three.module.js';

const mount = document.querySelector('#brain-scene');
const ui = {
  pointCount: document.querySelector('#point-count'),
  shownCount: document.querySelector('#shown-count'),
  sampleDetail: document.querySelector('#sample-detail'),
  legend: document.querySelector('#brain-legend'),
  selectedId: document.querySelector('#selected-id'),
  selectedDetail: document.querySelector('#selected-detail'),
  toggleAll: document.querySelector('#toggle-all'),
  loadNote: document.querySelector('#load-note'),
  error: document.querySelector('#brain-error'),
};
const palette = {
  optic: '#82c6d6', central: '#c4dca0', sensory: '#f0bd78',
  visual_projection: '#aaa4e7', ascending: '#eaa182', descending: '#e98798',
  visual_centrifugal: '#85b4ed', motor: '#f0d289', endocrine: '#c39bd8',
};
const format = new Intl.NumberFormat('de-DE');

const scene = new THREE.Scene();
scene.background = new THREE.Color('#091b25');
const camera = new THREE.PerspectiveCamera(43, 1, 0.1, 5000);
const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
mount.appendChild(renderer.domElement);

let azimuth = 0.72;
let elevation = 0.52;
let distance = 1350;
let center = [0, 0, 0];
const clouds = [];
const coordinateAxes = [];
let data = null;
let sampleData = null;
let fullData = null;
let showingAll = false;
let selectedMarker = null;

function positionCamera() {
  camera.position.set(
    Math.sin(azimuth) * Math.cos(elevation) * distance,
    Math.sin(elevation) * distance,
    Math.cos(azimuth) * Math.cos(elevation) * distance,
  );
  camera.lookAt(0, 0, 0);
}
positionCamera();

function resize() {
  const width = mount.clientWidth;
  const height = mount.clientHeight;
  if (!width || !height) return;
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe(mount);
resize();

function showSelected(record, color) {
  ui.selectedId.textContent = record[0]; // exact decimal string, never Number
  ui.selectedDetail.textContent = `${data.classes[record[4]]} · X ${record[1].toFixed(3)} · Y ${record[2].toFixed(3)} · Z ${record[3].toFixed(3)} µm`;
  if (!selectedMarker) {
    selectedMarker = new THREE.Mesh(
      new THREE.SphereGeometry(3.8, 10, 8),
      new THREE.MeshBasicMaterial({ color: '#ffffff', transparent: true, opacity: 0.9 }),
    );
    scene.add(selectedMarker);
  }
  selectedMarker.position.set(record[1] - center[0], record[2] - center[1], record[3] - center[2]);
  selectedMarker.material.color.set(color);
}

function updateShownCount() {
  const count = clouds.reduce((sum, cloud) => sum + (cloud.mesh.visible ? cloud.records.length : 0), 0);
  ui.shownCount.textContent = format.format(count);
}

function addCoordinateAxes(dataBounds) {
  const origin = new THREE.Vector3(
    dataBounds.min[0] - center[0],
    dataBounds.min[1] - center[1],
    dataBounds.min[2] - center[2],
  );
  const axes = [
    [new THREE.Vector3(80, 0, 0), '#e88484'],
    [new THREE.Vector3(0, 80, 0), '#a8d5a0'],
    [new THREE.Vector3(0, 0, 80), '#7ca8e4'],
  ];
  for (const [vector, color] of axes) {
    const geometry = new THREE.BufferGeometry().setFromPoints([origin, origin.clone().add(vector)]);
    const axis = new THREE.Line(geometry, new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.68 }));
    scene.add(axis);
    coordinateAxes.push(axis);
  }
}

function clearClouds() {
  for (const { mesh } of clouds) {
    scene.remove(mesh);
    mesh.geometry.dispose();
    mesh.material.dispose();
  }
  clouds.length = 0;
  for (const axis of coordinateAxes) {
    scene.remove(axis);
    axis.geometry.dispose();
    axis.material.dispose();
  }
  coordinateAxes.length = 0;
  if (selectedMarker) {
    scene.remove(selectedMarker);
    selectedMarker.geometry.dispose();
    selectedMarker.material.dispose();
    selectedMarker = null;
  }
  ui.selectedId.textContent = 'Keiner';
  ui.selectedDetail.textContent = 'Klicke einen Punkt in der 3D-Ansicht.';
}

function makeClouds(dataset) {
  clearClouds();
  center = dataset.boundsUm.min.map((minimum, index) =>
    (minimum + dataset.boundsUm.max[index]) / 2);
  const diagonal = Math.hypot(...dataset.boundsUm.max.map((maximum, index) =>
    maximum - dataset.boundsUm.min[index]));
  distance = Math.max(800, diagonal * 1.38 / Math.min(1, camera.aspect));
  positionCamera();
  addCoordinateAxes(dataset.boundsUm);

  const groups = dataset.classes.map(() => []);
  for (const record of dataset.points) groups[record[4]].push(record);
  const legend = document.createDocumentFragment();
  for (let classIndex = 0; classIndex < dataset.classes.length; classIndex++) {
    const category = dataset.classes[classIndex];
    const records = groups[classIndex];
    const positions = new Float32Array(records.length * 3);
    for (let index = 0; index < records.length; index++) {
      positions[index * 3] = records[index][1] - center[0];
      positions[index * 3 + 1] = records[index][2] - center[1];
      positions[index * 3 + 2] = records[index][3] - center[2];
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const color = palette[category] || '#d2d8d0';
    const mesh = new THREE.Points(geometry,
      new THREE.PointsMaterial({ color, size: 2.6, sizeAttenuation: false,
        transparent: true, opacity: 0.81, depthWrite: false }));
    scene.add(mesh);
    clouds.push({ mesh, records, category, color });

    const label = document.createElement('label');
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.checked = true;
    checkbox.addEventListener('change', () => {
      mesh.visible = checkbox.checked;
      updateShownCount();
    });
    const swatch = document.createElement('span');
    swatch.className = 'legend-swatch';
    swatch.style.background = color;
    const name = document.createElement('span');
    name.textContent = category;
    const count = document.createElement('span');
    count.className = 'legend-count';
    count.textContent = format.format(records.length);
    label.append(checkbox, swatch, name, count);
    legend.append(label);
  }
  ui.legend.replaceChildren(legend);
  updateShownCount();
}

function displayDataset(dataset, full) {
  data = dataset;
  showingAll = full;
  ui.pointCount.textContent = format.format(dataset.exportedAnchors);
  ui.sampleDetail.textContent = full
    ? `${format.format(dataset.totalAnchors)} Originalanker · vollständige lokale Punktdatei`
    : `${format.format(dataset.totalAnchors)} Originalanker · seltene Klassen vollständig, große Klassen 1/${dataset.selection.stride}`;
  ui.toggleAll.textContent = full
    ? 'Schnelle Stichprobe zeigen · 1,0 MB'
    : 'Alle 139.255 Anker laden · 6,6 MB';
  ui.toggleAll.setAttribute('aria-pressed', String(full));
  ui.loadNote.textContent = full
    ? 'Vollansicht geladen. Auf schwächeren Geräten kann Drehen und Auswählen langsamer sein.'
    : 'Die schnelle Stichprobe lädt zuerst. Die Vollansicht kann auf schwächeren Geräten langsamer sein.';
  makeClouds(dataset);
}

async function fetchDataset(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const dataset = await response.json();
  if (dataset.schema !== 'flywire-anchor-points-v1' || dataset.units !== 'µm' ||
      dataset.points.length !== dataset.exportedAnchors || !Array.isArray(dataset.classes)) {
    throw new Error('Unpassendes Punktdatenformat');
  }
  return dataset;
}

const raycaster = new THREE.Raycaster();
raycaster.params.Points.threshold = 5;
const pointer = new THREE.Vector2();
function pick(clientX, clientY) {
  const bounds = renderer.domElement.getBoundingClientRect();
  pointer.set((clientX - bounds.left) / bounds.width * 2 - 1,
    -(clientY - bounds.top) / bounds.height * 2 + 1);
  raycaster.setFromCamera(pointer, camera);
  const visible = clouds.filter((cloud) => cloud.mesh.visible);
  const hits = raycaster.intersectObjects(visible.map((cloud) => cloud.mesh), false);
  if (!hits.length) return;
  const cloud = visible.find((item) => item.mesh === hits[0].object);
  showSelected(cloud.records[hits[0].index], cloud.color);
}

let drag = null;
renderer.domElement.addEventListener('pointerdown', (event) => {
  drag = { x: event.clientX, y: event.clientY, lastX: event.clientX, lastY: event.clientY, moved: false };
  renderer.domElement.setPointerCapture(event.pointerId);
});
renderer.domElement.addEventListener('pointermove', (event) => {
  if (!drag) return;
  if (Math.hypot(event.clientX - drag.x, event.clientY - drag.y) > 4) drag.moved = true;
  azimuth -= (event.clientX - drag.lastX) * 0.006;
  elevation = THREE.MathUtils.clamp(elevation + (event.clientY - drag.lastY) * 0.006, -1.35, 1.35);
  drag.lastX = event.clientX;
  drag.lastY = event.clientY;
  positionCamera();
});
renderer.domElement.addEventListener('pointerup', (event) => {
  if (drag && !drag.moved && data) pick(event.clientX, event.clientY);
  drag = null;
});
renderer.domElement.addEventListener('pointercancel', () => { drag = null; });
renderer.domElement.addEventListener('wheel', (event) => {
  event.preventDefault();
  distance = THREE.MathUtils.clamp(distance * (event.deltaY > 0 ? 1.10 : 0.9), 250, 3000);
  positionCamera();
}, { passive: false });

function animate() {
  requestAnimationFrame(animate);
  renderer.render(scene, camera);
}
requestAnimationFrame(animate);

ui.toggleAll.addEventListener('click', async () => {
  if (showingAll) {
    displayDataset(sampleData, false);
    return;
  }
  ui.toggleAll.disabled = true;
  ui.toggleAll.textContent = 'Vollansicht wird geladen …';
  try {
    fullData ||= await fetchDataset('./data/brain-anchor-points-all.json');
    if (fullData.totalAnchors !== sampleData.totalAnchors ||
        fullData.sourceSha256 !== sampleData.sourceSha256) {
      throw new Error('Quellversionen stimmen nicht überein');
    }
    displayDataset(fullData, true);
  } catch (error) {
    ui.toggleAll.textContent = 'Alle 139.255 Anker laden · 6,6 MB';
    ui.loadNote.textContent = `Vollansicht konnte nicht geladen werden: ${error.message}`;
  } finally {
    ui.toggleAll.disabled = false;
  }
});

try {
  sampleData = await fetchDataset('./data/brain-anchor-points.json');
  displayDataset(sampleData, false);
  ui.toggleAll.disabled = false;
} catch (error) {
  ui.error.hidden = false;
  ui.error.textContent = `Die Ankerpunkte konnten nicht geladen werden: ${error.message}`;
}
