import { readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { ADAPTER, buildBodyReplay, makeActuatorControl } from './lab-replay.mjs';

const source = new URL('./data/neuron_assays.json', import.meta.url);
const bytes = await readFile(source); const assays = JSON.parse(bytes);
const results = [];
for (const scenario of assays.scenarios) for (const trial of scenario.trials) {
  const replay = buildBodyReplay(scenario, trial);
  const countsAgree = scenario.readouts.every((r) => replay.perIdSpikes[r.id] === trial.summary.readouts[r.id].spikeCount);
  const mappedSpikes = replay.mappedIds.reduce((n, id) => n + replay.perIdSpikes[id], 0);
  const nullSignalQuiet = mappedSpikes > 0 || replay.jointMotion === 0;
  const finiteGeometry = replay.frames.every((f) => f.body.legs.every((leg) => Object.values(leg.jointAngles).every(Number.isFinite)));
  const controlBounded = replay.frames.every((f) => f.control.groom >= 0 && f.control.groom <= 1 && f.control.forward === 0 && f.control.turn === 0);
  results.push({ scenario: scenario.id, trial: trial.id, condition: trial.condition,
    durationMs: replay.durationMs, mappedIds: replay.mappedIds,
    allReadoutSpikes: replay.totalReadoutSpikes, mappedSpikes, perIdSpikes: replay.perIdSpikes,
    meanReadoutHzAllTrial: replay.meanReadoutHz, cumulativeJointMotionRadians: replay.jointMotion,
    peakGroomChannel: Math.max(...replay.frames.map((f) => f.control.groom)),
    minimumGroundContacts: Math.min(...replay.frames.map((f) => f.body.contacts)),
    maxReachError: Math.max(...replay.frames.flatMap((f) => f.body.legs.map((leg) => leg.reachError))),
    checks: { countsAgreeWithNeuralAssay: countsAgree, nullSignalQuiet, finiteGeometry, controlBounded } });
}
const positive = makeActuatorControl();
const allPass = results.every((r) => Object.values(r.checks).every(Boolean));
const audit = { schema: 'fly.neuron-body-replay-audit.v1', generatedAt: new Date().toISOString(),
  source: fileURLToPath(source), sourceSha256: createHash('sha256').update(bytes).digest('hex'),
  neuralAssayGeneratedAt: assays.generatedAt, adapter: ADAPTER,
  trialCount: results.length, checksPass: allPass,
  movingTrials: results.filter((r) => r.cumulativeJointMotionRadians > 1e-8).length,
  zeroMappedSpikeTrials: results.filter((r) => r.mappedSpikes === 0).length,
  positiveTechnicalControl: { neuralSpikes: null, durationMs: positive.durationMs,
    cumulativeJointMotionRadians: positive.jointMotion, meaning: 'Actuator demonstration, excluded from neural trial counts' },
  limitations: ['A movement confirms only the specified body adapter, not new biological function.',
    'No neural feedback from body; no calibrated muscle forces; no left/right interpretation.',
    'Joint motion metric sums angular changes; it is not measured animal kinematics.'], results };
await writeFile(new URL('./data/neuron_body_replay_audit.json', import.meta.url), JSON.stringify(audit, null, 2) + '\n');
console.log(JSON.stringify({ trialCount: audit.trialCount, movingTrials: audit.movingTrials,
  zeroMappedSpikeTrials: audit.zeroMappedSpikeTrials, checksPass: audit.checksPass,
  examples: results.filter((r) => ['jo_ce', 'jo_f', 'jo_all'].includes(r.scenario) && ['reference', 'upstream_ablated', 'upstream_sham'].includes(r.trial)) }, null, 2));
if (!allPass) process.exitCode = 1;
