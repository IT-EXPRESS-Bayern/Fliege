import assert from 'node:assert/strict';
import test from 'node:test';
import { AutonomousController } from '../autonomy.mjs';

const center = { x: 0, z: 0, yaw: 0, arenaRadius: 5.65 };

test('spontaneous control is seeded, bounded, and retains internal state', () => {
  const a = new AutonomousController(27);
  const b = new AutonomousController(27);
  const initial = a.snapshot();
  let changed = false;
  for (let i = 0; i < 750; i++) {
    const x = a.next(center, 0.02, i * 20);
    const y = b.next(center, 0.02, i * 20);
    assert.deepEqual(x, y);
    assert.ok(x.forward >= 0 && x.forward <= 1);
    assert.ok(x.turn >= -1 && x.turn <= 1);
    if (x.activity !== 'Laufen') changed = true;
  }
  const after = a.snapshot();
  assert.ok(after.fatigue !== initial.fatigue || after.groomNeed !== initial.groomNeed);
  assert.ok(changed || Math.abs(after.rates.left - after.rates.right) > 0.02,
    'endogenous activity should not remain at one constant output');
});

test('body-relative wall feedback shifts steering away from a side obstacle', () => {
  const leftWall = new AutonomousController(27);
  const rightWall = new AutonomousController(27);
  const nearLeft = { x: -4.5, z: 0, yaw: 0, arenaRadius: 5.65 };
  const nearRight = { x: 4.5, z: 0, yaw: 0, arenaRadius: 5.65 };
  let leftOutput;
  let rightOutput;
  for (let i = 0; i < 70; i++) {
    leftOutput = leftWall.next(nearLeft, 0.02, i * 20);
    rightOutput = rightWall.next(nearRight, 0.02, i * 20);
  }
  assert.ok(leftWall.snapshot().wall.left > leftWall.snapshot().wall.right);
  assert.ok(rightWall.snapshot().wall.right > rightWall.snapshot().wall.left);
  assert.ok(leftOutput.turn > rightOutput.turn + 0.3);
});

test('invalid observations cannot silently advance the controller', () => {
  const controller = new AutonomousController(3);
  assert.throws(() => controller.next({ ...center, x: NaN }, 0.02, 0), /Invalid/);
  assert.equal(controller.snapshot().time, 0);
});

test('closed-loop arena run moves without a target and shows multiple spontaneous behaviors', () => {
  const controller = new AutonomousController(27);
  const body = { ...center, yaw: 0.5 };
  const seen = new Set();
  let traveled = 0;
  let nearWall = 0;
  for (let i = 0; i < 12000; i++) {
    const control = controller.next(body, 0.02, i * 20);
    seen.add(control.activity);
    const oldX = body.x;
    const oldZ = body.z;
    body.yaw += control.turn * 1.8 * 0.02;
    body.x += Math.sin(body.yaw) * control.forward * 2.15 * 0.02;
    body.z += Math.cos(body.yaw) * control.forward * 2.15 * 0.02;
    const radius = Math.hypot(body.x, body.z);
    if (radius > 5.33) {
      body.x *= 5.33 / radius;
      body.z *= 5.33 / radius;
    }
    traveled += Math.hypot(body.x - oldX, body.z - oldZ);
    if (Math.hypot(body.x, body.z) > 5.1) nearWall++;
  }
  assert.deepEqual(seen, new Set(['Laufen', 'Wenden', 'Ruhen', 'Putzen']));
  assert.ok(traveled > 60, 'the body should move substantially without target coordinates');
  assert.ok(nearWall / 12000 < 0.15, 'the fly should not remain trapped at the wall');
});
