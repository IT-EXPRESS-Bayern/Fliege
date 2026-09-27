import test from 'node:test';
import assert from 'node:assert/strict';
import { ArticulatedBody, LEG_SPECS, localToWorld, worldToLocal } from '../body-kinematics.mjs';

const distance = (a, b) => Math.hypot(...a.map((value, i) => value - b[i]));

test('body rotations preserve the measured world/local foot positions', () => {
  const pose = { x: 3.2, z: -1.1, height: 0.65, yaw: 1.8, pitch: -0.05, roll: 0.08 };
  const point = [0.6, -0.5, -0.4];
  assert.ok(distance(point, worldToLocal(localToWorld(point, pose), pose)) < 1e-12);
});

test('walking and turning preserve segment lengths and plant stance feet in world space', () => {
  const pose = { x: 0, z: 0, yaw: 0 };
  const model = new ArticulatedBody(pose);
  let previous = model.snapshot();
  let swingSeen = false;
  let worstError = 0;
  for (let i = 0; i < 1200; i++) {
    const dt = 1 / 60;
    pose.yaw += Math.sin(i * 0.005) * 0.9 * dt;
    pose.x += Math.sin(pose.yaw) * 1.1 * dt;
    pose.z += Math.cos(pose.yaw) * 1.1 * dt;
    const current = model.update(pose, { groom: 0 }, dt);
    for (let n = 0; n < current.legs.length; n++) {
      const leg = current.legs[n];
      const before = previous.legs[n];
      for (let j = 0; j < 4; j++) {
        assert.ok(Math.abs(distance(leg.pointsLocal[j], leg.pointsLocal[j + 1]) - LEG_SPECS[n].lengths[j]) < 1e-9);
      }
      if (leg.contact && before.contact) assert.ok(distance(leg.footWorld, before.footWorld) < 1e-9, `${leg.id} stance must not skate`);
      if (leg.phase === 'swing') swingSeen = true;
      assert.ok(leg.footWorld[1] >= -1e-8, 'feet may not penetrate the ground');
      assert.ok(Object.values(leg.jointAngles).every(Number.isFinite));
      assert.ok(Object.values(leg.jointVelocity).every(Number.isFinite));
      worstError = Math.max(worstError, leg.reachError);
    }
    previous = current;
  }
  assert.ok(swingSeen);
  assert.ok(worstError < 1e-8, `all walking feet must be reachable, got ${worstError}`);
});

test('stopping settles ongoing steps and grooming releases only the two front feet', () => {
  const pose = { x: 0, z: 0, yaw: 0 };
  const model = new ArticulatedBody(pose);
  for (let i = 0; i < 120; i++) {
    pose.z += 0.6 / 60;
    model.update(pose, {}, 1 / 60);
  }
  for (let i = 0; i < 180; i++) model.update(pose, {}, 1 / 60);
  assert.equal(model.snapshot().contacts, 6);
  for (let i = 0; i < 120; i++) model.update(pose, { groom: 1 }, 1 / 60);
  const grooming = model.snapshot();
  assert.equal(grooming.contacts, 4);
  assert.deepEqual(grooming.legs.filter((leg) => leg.phase === 'groom').map((leg) => leg.id), ['LF', 'RF']);
  for (let i = 0; i < 180; i++) model.update(pose, { groom: 0 }, 1 / 60);
  assert.equal(model.snapshot().contacts, 6);
});

test('reset clears dynamics and snapshots cannot mutate body state', () => {
  const pose = { x: 2, z: -3, yaw: 0.8 };
  const model = new ArticulatedBody(pose);
  const snapshot = model.snapshot();
  snapshot.legs[0].pointsLocal[0][0] = 100;
  snapshot.legs[0].footTargetWorld[0] = 200;
  assert.notEqual(model.snapshot().legs[0].pointsLocal[0][0], 100);
  assert.notEqual(model.snapshot().legs[0].footTargetWorld[0], 200);
  model.update({ ...pose, z: -2.99 }, {}, 1 / 60);
  model.reset(pose);
  assert.equal(model.snapshot().timeSeconds, 0);
  assert.equal(model.snapshot().contacts, 6);
  assert.equal(model.snapshot().velocity.z, 0);
  assert.equal(model.snapshot().contactForces, null);
});

test('front feet return from grooming before supporting legs begin a new stride', () => {
  const pose = { x: 0, z: 0, yaw: 0 };
  const model = new ArticulatedBody(pose);
  for (let i = 0; i < 90; i++) model.update(pose, { groom: 1 }, 1 / 60);
  assert.equal(model.snapshot().contacts, 4);
  let frontLandingSeen = false;
  for (let i = 0; i < 180; i++) {
    pose.z += 0.8 / 60;
    const frame = model.update(pose, { groom: 0 }, 1 / 60);
    if (frame.legs.filter((leg) => leg.id.endsWith('F')).every((leg) => leg.contact)) frontLandingSeen = true;
    assert.ok(frame.contacts >= 3, 'groom-to-walk transition needs at least tripod support');
    assert.ok(frame.legs.every((leg) => leg.reachError < 1e-8));
  }
  assert.ok(frontLandingSeen);
});
