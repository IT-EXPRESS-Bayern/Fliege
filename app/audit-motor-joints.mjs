import { readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { LEG_SPECS } from './body-kinematics.mjs';
import { makeMotorPools, motorTrial, MOTOR_TESTS, MOTOR_PARAMETERS } from './joint_motor_model.mjs';
const sourceUrl = new URL('./data/motor_pathways.json', import.meta.url); const bytes = await readFile(sourceUrl);
const data = JSON.parse(bytes); const pools = makeMotorPools(data.motors); const results = [];
const dist = (a, b) => Math.hypot(...a.map((v, i) => v - b[i]));
for (const spec of LEG_SPECS) for (const test of MOTOR_TESTS) {
  const replay = motorTrial(pools, { leg: spec.id, condition: test.id, amplitude: .65 });
  const index = LEG_SPECS.indexOf(spec); const initial = replay.frames[0].body.legs[index].jointAngles.femurTibia;
  let maxSegmentError = 0; let minFootY = Infinity; let maxUnselectedDeviation = 0; let maxCoactivation = 0; let maxStiffness = 0;
  let finite = true; let anglesWithinLimits = true; let fixedBody = true; let maxFlexor = 0; let maxExtensor = 0;
  for (const frame of replay.frames) {
    fixedBody &&= frame.body.pose.x === 0 && frame.body.pose.z === 0 && frame.body.contacts === 0;
    for (const [j, leg] of frame.body.legs.entries()) {
      finite &&= leg.pointsLocal.flat().every(Number.isFinite) && Number.isFinite(leg.jointAngles.femurTibia);
      anglesWithinLimits &&= leg.jointAngles.femurTibia >= MOTOR_PARAMETERS.minAngle && leg.jointAngles.femurTibia <= MOTOR_PARAMETERS.maxAngle;
      for (let bone = 0; bone < 4; bone++) maxSegmentError = Math.max(maxSegmentError, Math.abs(dist(leg.pointsLocal[bone], leg.pointsLocal[bone + 1]) - LEG_SPECS[j].lengths[bone]));
      minFootY = Math.min(minFootY, leg.footWorld[1]);
      if (j !== index) maxUnselectedDeviation = Math.max(maxUnselectedDeviation, Math.abs(leg.jointAngles.femurTibia - replay.frames[0].body.legs[j].jointAngles.femurTibia));
      else { maxCoactivation = Math.max(maxCoactivation, leg.motor.coactivation); maxStiffness = Math.max(maxStiffness, leg.motor.stiffness); maxFlexor = Math.max(maxFlexor, leg.motor.flexor); maxExtensor = Math.max(maxExtensor, leg.motor.extensor); }
    }
  }
  const angleAt1800 = replay.frames.find((f) => f.tMs >= 1800).body.legs[index].jointAngles.femurTibia;
  const directionCorrect = test.id !== 'flexor' && test.id !== 'extensor' || (test.id === 'flexor' ? angleAt1800 > initial : angleAt1800 < initial);
  const zeroChecks = !['baseline', 'ablation', 'coactivation'].includes(test.id) || replay.peakDeviationRadians < 1e-12;
  results.push({ leg: spec.id, test: test.id, durationMs: replay.durationMs, amplitude: replay.amplitude,
    directlyDrivenIds: replay.directlyDrivenIds, ablatedIds: replay.ablatedIds,
    peakDeviationRadians: replay.peakDeviationRadians, cumulativeAngleTravelRadians: replay.cumulativeAngleTravelRadians,
    angleAt1800Radians: angleAt1800, initialAngleRadians: initial, maxFlexor, maxExtensor, maxCoactivation, maxStiffness,
    maxSegmentError, minFootY, maxUnselectedDeviation,
    checks: { finite, anglesWithinLimits, fixedBody, directionCorrect, zeroChecks,
      segmentLengthsPreserved: maxSegmentError < 1e-10, feetClearOfFloor: minFootY > 0, unselectedLegsStationary: maxUnselectedDeviation === 0 } });
}
const paired = LEG_SPECS.map(({ id }) => {
  const get = (test) => results.find((r) => r.leg === id && r.test === test);
  return { leg: id, shamIdenticalToFlexor: get('sham').peakDeviationRadians === get('flexor').peakDeviationRadians,
    activePerturbationSmaller: get('coactivation_disturbance').peakDeviationRadians < get('passive_disturbance').peakDeviationRadians,
    disturbanceReductionFraction: 1 - get('coactivation_disturbance').peakDeviationRadians / get('passive_disturbance').peakDeviationRadians };
});
const audit = { schema: 'fly.motor-joint-audit.v1', generatedAt: new Date().toISOString(),
  source: { file: 'app/data/motor_pathways.json', sha256: createHash('sha256').update(bytes).digest('hex') },
  modelSourceSha256: createHash('sha256').update(await readFile(new URL('./joint_motor_model.mjs', import.meta.url))).digest('hex'),
  sourceMotorCount: data.motors.length, mappedMotorCount: Object.values(pools).reduce((n, p) => n + p.flexor.length + p.extensor.length, 0),
  pools, parameters: MOTOR_PARAMETERS, trialCount: results.length, totalIntegratedSteps: results.length * 1500,
  neuralPropagationSimulated: false, calibratedBiophysics: false,
  checksPass: results.every((r) => Object.values(r.checks).every(Boolean)) && paired.every((r) => r.shamIdenticalToFlexor && r.activePerturbationSmaller),
  pairedChecks: paired, results };
await writeFile(new URL('./data/motor_joint_audit.json', import.meta.url), JSON.stringify(audit, null, 2) + '\n');
console.log(JSON.stringify({ trialCount: audit.trialCount, checksPass: audit.checksPass, mappedMotorCount: audit.mappedMotorCount, pairedChecks: paired }, null, 2));
if (!audit.checksPass) process.exitCode = 1;
