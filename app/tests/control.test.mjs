import assert from 'node:assert/strict';
import test from 'node:test';
import { CONTROL_KIND, DemoController, ExternalControlInbox, normalizeControlFrame } from '../control.mjs';

const frame = (timestampMs) => ({ kind: CONTROL_KIND, timestampMs, forward: 0.5, turn: -0.25, wing: 0.2, groom: 0 });

test('external control frames are validated and bounded', () => {
  assert.throws(() => normalizeControlFrame({ ...frame(100), forward: Number.NaN }), /forward/);
  assert.throws(() => normalizeControlFrame({ ...frame(100), kind: 'other' }), /fly.control.v1/);
  assert.deepEqual(normalizeControlFrame({ ...frame(100), forward: 9, turn: -9 }).forward, 1);
  assert.deepEqual(normalizeControlFrame({ ...frame(100), forward: 9, turn: -9 }).turn, -1);
});

test('stale external frames expire instead of producing motor commands', () => {
  const inbox = new ExternalControlInbox(350);
  inbox.receive(frame(1000));
  assert.equal(inbox.sample(1200).forward, 0.5);
  assert.equal(inbox.sample(1400), null);
  inbox.clear();
  assert.equal(inbox.sample(1000), null);
});

test('demo movement is reproducible, bounded, and turns away from the arena edge', () => {
  const a = new DemoController(42);
  const b = new DemoController(42);
  const center = { x: 0, z: 0, yaw: 0, arenaRadius: 5.65 };
  const first = a.next(center, 0.016, 16);
  assert.deepEqual(first, b.next(center, 0.016, 16));
  assert.ok(first.forward >= 0 && first.forward <= 1);
  assert.ok(first.turn >= -1 && first.turn <= 1);

  const edge = { x: 5.2, z: 0, yaw: Math.PI / 2, arenaRadius: 5.65 };
  const edgeControl = a.next(edge, 0.016, 32);
  assert.ok(Math.abs(edgeControl.turn) > 0.5, 'edge steering should turn back inside');
});
