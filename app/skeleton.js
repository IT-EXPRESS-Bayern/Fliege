import * as THREE from './vendor/three.module.js';

const mount = document.querySelector('#viewer');
const layerList = document.querySelector('#layer-list');
const detail = document.querySelector('#point-detail');
const status = document.querySelector('#load-state');
const errorBox = document.querySelector('#viewer-error');
const R7 = '720575940623940963';

const scene = new THREE.Scene();
scene.background = new THREE.Color('#081924');
const camera = new THREE.PerspectiveCamera(52, 1, 0.05, 3000);
camera.up.set(0, 0, 1);
const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
mount.append(renderer.domElement);
const origin = new THREE.Vector3(0, 0, 0);
let azimuth = 0.72;
let elevation = 0.42;
let radius = 122;
const meshes = [];
const pointLayers = [];
let dragStart = null;

function setCamera() {
  camera.position.set(
    radius * Math.cos(elevation) * Math.cos(azimuth),
    radius * Math.cos(elevation) * Math.sin(azimuth),
    radius * Math.sin(elevation),
  );
  camera.lookAt(origin);
}

function resize() {
  const width = Math.max(1, mount.clientWidth);
  const height = Math.max(1, mount.clientHeight);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height);
  renderer.render(scene, camera);
}

function addLayer(label, color, count, object, initiallyVisible = true) {
  object.visible = initiallyVisible;
  scene.add(object);
  meshes.push(object);
  const row = document.createElement('label');
  row.className = 'layer';
  const check = document.createElement('input');
  check.type = 'checkbox';
  check.checked = initiallyVisible;
  check.addEventListener('change', () => { object.visible = check.checked; renderer.render(scene, camera); });
  const dot = document.createElement('span');
  dot.className = 'swatch';
  dot.style.background = color;
  const title = document.createElement('span');
  title.textContent = label;
  const countLabel = document.createElement('small');
  countLabel.textContent = count.toLocaleString('de-DE');
  row.append(check, dot, title, countLabel);
  layerList.append(row);
}

function skeletonObject(neuron) {
  const nodes = new Map(neuron.nodes.map(([id, parent, x, y, z]) => [id, { parent, x, y, z }]));
  const positions = [];
  for (const [id, node] of nodes) {
    const parent = nodes.get(node.parent);
    if (!parent || node.parent === id) continue;
    positions.push(node.x, node.y, node.z, parent.x, parent.y, parent.z);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  const material = new THREE.LineBasicMaterial({ color: neuron.color, transparent: true, opacity: neuron.rootId === R7 ? 1 : 0.85 });
  const group = new THREE.Group();
  group.add(new THREE.LineSegments(geometry, material));
  const nodeGeometry = new THREE.BufferGeometry();
  nodeGeometry.setAttribute('position', new THREE.Float32BufferAttribute(neuron.nodes.flatMap(row => row.slice(2)), 3));
  group.add(new THREE.Points(nodeGeometry, new THREE.PointsMaterial({
    color: neuron.color, size: neuron.rootId === R7 ? 3.5 : 2.5,
    sizeAttenuation: false, transparent: true, opacity: 0.9,
  })));
  return group;
}

function pointObject(points, color, size, label) {
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(points.flatMap(point => point.xyz), 3));
  const material = new THREE.PointsMaterial({ color, size, sizeAttenuation: false, depthTest: false, transparent: true, opacity: 0.95 });
  const object = new THREE.Points(geometry, material);
  object.renderOrder = 4;
  pointLayers.push({ object, rows: points, label });
  return object;
}

function showPoint(point, source) {
  const partner = point.pre === R7 ? point.post : point.pre;
  detail.innerHTML = '';
  const lines = [
    ['Datensatz', source],
    ['Quellzeile / ID', point.id],
    ['Richtung', `${point.pre === R7 ? 'R7 → Partner' : 'Partner → R7'}`],
    ['Partner-ID', partner],
    ['Hirnregion', point.region],
    ['Position relativ', `${point.xyz.map(value => Number(value).toFixed(2)).join(' · ')} µm`],
  ];
  for (const [title, value] of lines) {
    const row = document.createElement('div');
    const name = document.createElement('strong');
    name.textContent = `${title}: `;
    row.append(name, document.createTextNode(String(value)));
    detail.append(row);
  }
}

const raycaster = new THREE.Raycaster();
raycaster.params.Points.threshold = 0.45;
function pickPoint(clientX, clientY) {
  const box = renderer.domElement.getBoundingClientRect();
  const cursor = new THREE.Vector2(
    ((clientX - box.left) / box.width) * 2 - 1,
    -((clientY - box.top) / box.height) * 2 + 1,
  );
  raycaster.setFromCamera(cursor, camera);
  const visible = pointLayers.filter(layer => layer.object.visible);
  const hits = raycaster.intersectObjects(visible.map(layer => layer.object));
  const hit = hits[0];
  if (!hit) return;
  const layer = visible.find(item => item.object === hit.object);
  if (layer?.rows[hit.index]) showPoint(layer.rows[hit.index], layer.label);
}

mount.addEventListener('pointerdown', event => {
  dragStart = { x: event.clientX, y: event.clientY, azimuth, elevation, moved: false };
  mount.setPointerCapture(event.pointerId);
});
mount.addEventListener('pointermove', event => {
  if (!dragStart) return;
  const dx = event.clientX - dragStart.x;
  const dy = event.clientY - dragStart.y;
  if (Math.abs(dx) + Math.abs(dy) > 4) dragStart.moved = true;
  azimuth = dragStart.azimuth - dx * 0.007;
  elevation = Math.max(-1.45, Math.min(1.45, dragStart.elevation + dy * 0.007));
  setCamera();
  renderer.render(scene, camera);
});
mount.addEventListener('pointerup', event => {
  if (dragStart && !dragStart.moved) pickPoint(event.clientX, event.clientY);
  dragStart = null;
});
mount.addEventListener('pointercancel', () => { dragStart = null; });
mount.addEventListener('wheel', event => {
  event.preventDefault();
  radius = Math.max(4, Math.min(450, radius * Math.exp(event.deltaY * 0.001)));
  setCamera();
  renderer.render(scene, camera);
}, { passive: false });
document.querySelector('#reset-view').addEventListener('click', () => {
  azimuth = 0.72; elevation = 0.42; radius = 122; setCamera(); renderer.render(scene, camera);
});
new ResizeObserver(resize).observe(mount);

async function main() {
  try {
    const response = await fetch('./data/r7_skeleton.json', { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (!Array.isArray(data.skeletons) || !Array.isArray(data.oldPoints) || !Array.isArray(data.princetonPoints)) {
      throw new Error('Unerwartetes Datenformat');
    }
    for (const neuron of data.skeletons) {
      addLayer(`${neuron.label} · Skelett`, neuron.color, neuron.nodes.length,
        skeletonObject(neuron), ['R7', 'Dm9'].includes(neuron.label));
    }
    addLayer('Buhmann · Rohpunkte', '#ffc66d', data.oldPoints.length,
      pointObject(data.oldPoints, '#ffc66d', 7, 'Buhmann v783 Rohpunkt'));
    addLayer('Princeton · Punkte', '#ff6fb1', data.princetonPoints.length,
      pointObject(data.princetonPoints, '#ff6fb1', 5, 'Princeton 2025 Punkt'));
    status.textContent = `${data.skeletons.length} Skelette geladen`;
    setCamera(); resize();
  } catch (error) {
    status.textContent = 'Ladefehler';
    errorBox.hidden = false;
    errorBox.textContent = `3D-Daten konnten nicht geladen werden: ${error.message}`;
  }
}

main();
