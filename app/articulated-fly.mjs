import * as THREE from './vendor/three.module.js';
import { LEG_SPECS } from './body-kinematics.mjs';

/** Procedural anatomy; dimensions and decorative details are model assumptions. */
export function createArticulatedFly(scene) {
  const root = new THREE.Group();
  root.rotation.order = 'YXZ';
  scene.add(root);
  const shell = new THREE.MeshStandardMaterial({ color: '#ac7947', roughness: 0.68 });
  const amber = new THREE.MeshStandardMaterial({ color: '#d4a66c', roughness: 0.65 });
  const dark = new THREE.MeshStandardMaterial({ color: '#40302b', roughness: 0.76 });
  const legMat = new THREE.MeshStandardMaterial({ color: '#916b43', roughness: 0.72 });
  const eyeMat = new THREE.MeshPhysicalMaterial({ color: '#a02e22', roughness: 0.36, clearcoat: 0.22, flatShading: true });
  const wingMat = new THREE.MeshPhysicalMaterial({ color: '#d9e5dc', transparent: true,
    opacity: 0.30, side: THREE.DoubleSide, roughness: 0.3, depthWrite: false });
  const hairMat = new THREE.LineBasicMaterial({ color: '#352b26', transparent: true, opacity: 0.82 });
  const veinMat = new THREE.LineBasicMaterial({ color: '#7e8d7d', transparent: true, opacity: 0.63 });
  const sphere = new THREE.SphereGeometry(1, 24, 16);
  const cylinder = new THREE.CylinderGeometry(0.65, 1, 1, 7);
  const axis = new THREE.Vector3(0, 1, 0);
  const from = new THREE.Vector3();
  const to = new THREE.Vector3();
  const direction = new THREE.Vector3();

  function ellipsoid(parent, material, position, scale, geometry = sphere) {
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(...position); mesh.scale.set(...scale); mesh.castShadow = true;
    parent.add(mesh); return mesh;
  }
  function line(parent, points, material = hairMat) {
    const object = new THREE.Line(new THREE.BufferGeometry().setFromPoints(points.map((p) => new THREE.Vector3(...p))), material);
    parent.add(object); return object;
  }
  function placeBone(mesh, a, b, radius) {
    from.set(...a); to.set(...b); direction.subVectors(to, from);
    mesh.position.copy(from).add(to).multiplyScalar(0.5);
    mesh.scale.set(radius, direction.length(), radius);
    mesh.quaternion.setFromUnitVectors(axis, direction.normalize());
  }
  function bone(parent, a, b, radius, material = legMat) {
    const mesh = new THREE.Mesh(cylinder, material); mesh.castShadow = true;
    parent.add(mesh); placeBone(mesh, a, b, radius); return mesh;
  }

  ellipsoid(root, shell, [0, 0, 0.0], [0.33, 0.275, 0.43]);
  ellipsoid(root, dark, [0, 0.215, -0.05], [0.12, 0.065, 0.31]);
  ellipsoid(root, amber, [0, 0.1, -0.35], [0.25, 0.15, 0.18]);
  const abdomen = new THREE.Group(); abdomen.position.set(0, -0.025, -0.38); root.add(abdomen);
  for (let i = 0; i < 6; i++) {
    const size = [0.25, 0.315, 0.33, 0.295, 0.23, 0.135][i];
    ellipsoid(abdomen, i < 4 ? amber : shell, [0, -i * 0.022, -i * 0.135], [size, size * 0.70, 0.155]);
    ellipsoid(abdomen, dark, [0, 0.008 - i * 0.022, -i * 0.135 - 0.06], [size * 1.007, size * 0.706, 0.045]);
  }

  const head = new THREE.Group(); head.position.set(0, 0.02, 0.48); root.add(head);
  ellipsoid(head, amber, [0, 0.01, 0.065], [0.30, 0.255, 0.235]);
  ellipsoid(head, shell, [0, -0.14, 0.22], [0.125, 0.14, 0.10]);
  const antennae = [];
  const halteres = [];
  for (const side of [-1, 1]) {
    ellipsoid(head, eyeMat, [side * 0.226, 0.065, 0.10], [0.155, 0.212, 0.187], new THREE.IcosahedronGeometry(1, 3));
    const antenna = new THREE.Group(); antenna.position.set(side * 0.105, 0.065, 0.275); head.add(antenna);
    ellipsoid(antenna, shell, [side * 0.02, -0.012, 0.035], [0.045, 0.065, 0.050]);
    line(antenna, [[side * 0.035, 0.02, 0.06], [side * 0.12, 0.15, 0.13], [side * 0.20, 0.28, 0.12]]);
    for (let j = 0; j < 5; j++) {
      const h = j * 0.036;
      line(antenna, [[side * (0.07 + h * 0.65), 0.07 + h, 0.10],
        [side * (0.01 + h * 0.65), 0.105 + h, 0.13]]);
    }
    antennae.push({ group: antenna, side });
    // Halteres behind the wing hinge, reduced balancing organs of flies.
    const halterePivot = new THREE.Group(); halterePivot.position.set(side * 0.26, 0.04, -0.34); root.add(halterePivot);
    bone(halterePivot, [0, 0, 0], [side * 0.17, 0.05, -0.07], 0.012, amber);
    ellipsoid(halterePivot, amber, [side * 0.17, 0.05, -0.07], [0.041, 0.028, 0.040]);
    halteres.push({ pivot: halterePivot, side });
  }
  for (let i = 0; i < 3; i++) ellipsoid(head, dark, [(i - 1) * 0.04, 0.23, 0.035 + (i % 2) * 0.04], [0.018, 0.013, 0.018]);
  for (let i = 0; i < 34; i++) {
    const phi = i * 2.39996;
    const z = -0.33 + i / 33 * 0.64;
    const x = Math.sin(phi) * 0.25;
    const y = Math.sqrt(Math.max(0, 1 - (x / 0.34) ** 2 - (z / 0.49) ** 2)) * 0.275;
    line(root, [[x, y, z], [x * 1.17, y + 0.06 + (i % 3) * 0.025, z - 0.038]]);
  }

  const shape = new THREE.Shape();
  shape.moveTo(0, 0);
  shape.bezierCurveTo(0.24, -0.10, 0.53, -0.64, 0.48, -1.24);
  shape.bezierCurveTo(0.44, -1.68, 0.16, -1.68, 0.045, -1.29);
  shape.bezierCurveTo(-0.025, -0.92, -0.04, -0.3, 0, 0);
  const wingGeometry = new THREE.ShapeGeometry(shape, 18);
  const wings = [-1, 1].map((side) => {
    const pivot = new THREE.Group(); pivot.position.set(side * 0.20, 0.24, -0.08); root.add(pivot);
    const plane = new THREE.Group(); plane.rotation.x = Math.PI / 2; plane.scale.x = side; pivot.add(plane);
    plane.add(new THREE.Mesh(wingGeometry, wingMat));
    for (const points of [
      [[0, 0, 0.001], [0.10, -0.39, 0.001], [0.28, -1.51, 0.001]],
      [[0, 0, 0.001], [0.28, -0.58, 0.001], [0.44, -1.32, 0.001]],
      [[0, 0, 0.001], [0.04, -0.58, 0.001], [0.10, -1.39, 0.001]],
      [[0.05, -0.67, 0.001], [0.30, -0.70, 0.001]],
      [[0.16, -1.13, 0.001], [0.41, -1.03, 0.001]],
    ]) line(plane, points, veinMat);
    return { pivot, plane, side };
  });
  const legs = LEG_SPECS.map((spec) => {
    const radii = [0.040, 0.032, 0.022, 0.012];
    const segments = radii.map((radius) => bone(root, [0, 0, 0], [0, 0.1, 0], radius));
    const joints = Array.from({ length: 4 }, (_, i) => ellipsoid(root, i === 0 ? shell : legMat, [0, 0, 0], [0.037 - i * 0.006, 0.037 - i * 0.006, 0.037 - i * 0.006]));
    // Short bristles follow the femur/tibia cylinder transform.
    for (const n of [1, 2]) for (let j = 0; j < 5; j++) {
      const phi = j * 2.1;
      line(segments[n], [[Math.cos(phi) * 0.8, j / 6 - 0.35, Math.sin(phi) * 0.8],
        [Math.cos(phi) * 2.9, j / 6 - 0.39, Math.sin(phi) * 2.9]]);
    }
    const pad = ellipsoid(root, dark, [0, 0, 0], [0.027, 0.013, 0.048]);
    const marker = new THREE.Mesh(new THREE.RingGeometry(0.037, 0.050, 18),
      new THREE.MeshBasicMaterial({ color: '#b4daa5', transparent: true, opacity: 0.75, side: THREE.DoubleSide, depthWrite: false }));
    marker.rotation.x = -Math.PI / 2; scene.add(marker);
    return { id: spec.id, segments, radii, joints, pad, marker };
  });
  let contactsVisible = false;
  return { root,
    setContactsVisible(value) {
      contactsVisible = Boolean(value);
      for (const leg of legs) leg.marker.visible = contactsVisible;
    },
    update(body, control = {}) {
      root.position.set(body.pose.x, body.pose.height, body.pose.z);
      root.rotation.set(body.pose.pitch, body.pose.yaw, body.pose.roll, 'YXZ');
      const mechanicalFlight = Boolean(control.flightKinematics);
      const decorativeTime = mechanicalFlight ? 0 : body.timeSeconds;
      head.rotation.z = mechanicalFlight ? 0 : -body.pose.roll * 0.72;
      head.rotation.x = mechanicalFlight ? 0 : -body.pose.pitch * 0.68 + Math.sin(decorativeTime * 2.1) * 0.015;
      head.rotation.y = Math.sin(decorativeTime * 1.4) * 0.035;
      abdomen.rotation.x = Math.sin(decorativeTime * 3.6) * 0.016;
      for (let i = 0; i < legs.length; i++) {
        const renderLeg = legs[i]; const state = body.legs[i];
        for (let j = 0; j < 4; j++) {
          placeBone(renderLeg.segments[j], state.pointsLocal[j], state.pointsLocal[j + 1], renderLeg.radii[j]);
          renderLeg.joints[j].position.set(...state.pointsLocal[j]);
        }
        renderLeg.pad.position.set(...state.pointsLocal[4]);
        renderLeg.marker.position.set(state.footWorld[0], 0.023, state.footWorld[2]);
        renderLeg.marker.material.color.set(state.contact ? '#b4daa5' : '#dda568');
        renderLeg.marker.visible = contactsVisible;
      }
      for (const { group, side } of antennae) {
        group.rotation.x = mechanicalFlight ? 0 : Math.sin(decorativeTime * 6.3 + side) * 0.12;
        group.rotation.y = side * (0.06 + Math.sin(decorativeTime * 3.9) * 0.08);
      }
      for (const { pivot, plane, side } of wings) {
        const flight = control.flightKinematics?.wings?.[side < 0 ? 'left' : 'right'];
        if (flight) {
          // Rendering convention only: stroke=0 is spread laterally; positive stroke sweeps forward.
          // Physics and any time scaling belong to the caller, never to a decorative animation clock.
          const { stroke = 0, elevation = 0, pitch = 0 } = flight;
          if (![stroke, elevation, pitch].every(Number.isFinite)) throw new Error('Non-finite wing kinematics');
          pivot.rotation.set(elevation, -side * (Math.PI / 2 + stroke), 0, 'YXZ');
          plane.rotation.set(Math.PI / 2, side * pitch, 0, 'XYZ');
        } else {
          const flutter = (control.wing || 0) * 0.11 * Math.sin(body.timeSeconds * 31);
          pivot.rotation.set(0, side * (0.19 + Math.max(0, flutter)), side * (0.02 + flutter), 'XYZ');
          plane.rotation.set(Math.PI / 2, 0, 0, 'XYZ');
        }
      }
      for (const { pivot, side } of halteres) {
        const angle = control.flightKinematics?.halteres?.[side < 0 ? 'left' : 'right'] ?? 0;
        if (!Number.isFinite(angle)) throw new Error('Non-finite haltere kinematics');
        pivot.rotation.x = angle;
      }
    },
  };
}
