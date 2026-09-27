import { readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { buildSensorimotorCircuit, runSensorimotorTrial, makePerturbationSequence, measureClampedTransfer,
  POLARITY_HYPOTHESES, SENSORIMOTOR_PARAMETERS, sensorimotorProvenance } from './sensorimotor_model.mjs';

const sha = (bytes) => createHash('sha256').update(bytes).digest('hex');
const bytes = await readFile(new URL('./data/sensorimotor_mapping.json', import.meta.url));
const mapping = JSON.parse(bytes); const results = []; const pairedChecks = []; const transfer = []; const circuits = [];
const protocol = { seed: 260927, duration: 4, graphGains: [0, 4, 16], detectorVersions: ['v2', 'v3'],
  polarities: POLARITY_HYPOTHESES, threshold: 5, signPolicy: 'verified_only', proofreadOnly: true,
  freezeAtSeconds: 1.12, frequencyProbesHz: [.5, 2, 8], delaySensitivitySeconds: [0, .008, .04],
  defaultGraphGainChosenBeforeResults: 4, defaultPolarityIsDisplayChoiceNotInferredBiology: true,
  noSelectingSuccessfulPolarity: true };
const basePerturbations = makePerturbationSequence(protocol);
const changedPerturbations = makePerturbationSequence({ ...protocol, counterfactual: true });
const maxDifference = (a, b) => a.reduce((max, x, i) => Math.max(max, Math.abs(x - b[i])), 0);
function addResult(trial, extra = {}) {
  const allFinite = trial.frames.every((f) => ['angle', 'velocity', 'activeTorque', 'flexor', 'extensor', 'coactivation', 'stiffness', 'clawRate', 'hookRate'].every((k) => Number.isFinite(f[k])));
  const id = [trial.detector, trial.polarity.id || `${trial.polarity.claw}_${trial.polarity.hook}`, trial.parameters.graphGain,
    trial.condition, extra.probe || 'reference', trial.parameters.observationDelay].join(':');
  const record = { id, detector: trial.detector, polarity: trial.polarity, graphGain: trial.parameters.graphGain,
    observationDelay: trial.parameters.observationDelay, condition: trial.condition, ...extra,
    summary: trial.summary, checks: { allFinite, bounded: trial.frames.every((f) => f.angle >= trial.bodyParameters.minAngle && f.angle <= trial.bodyParameters.maxAngle),
      fullDuration: trial.summary.integrationSteps === 2000, noBiologicalValidationClaim: trial.biologicalReconstructionValidated === false },
    perturbationSha256: sha(JSON.stringify(trial.perturbations)), activeTorqueSha256: sha(JSON.stringify(trial.activeTorques)) };
  results.push(record); return record;
}
for (const detector of protocol.detectorVersions) {
  const circuit = buildSensorimotorCircuit(mapping, { detector });
  circuits.push({ detector, statistics: circuit.statistics, sensorIds: circuit.sensors.map((s) => s.id),
    motorPools: circuit.pools.LF, nodes: circuit.nodes.map((n) => ({ id: n.id, cellType: n.cellType, role: n.role,
      ntVerified: n.ntVerified, ntPredicted: n.ntPredicted, signAssumption: n.signAssumption })), assumptions: circuit.assumptions,
    edgeSha256: sha(JSON.stringify(circuit.edges)) });
  for (const polarity of POLARITY_HYPOTHESES) for (const graphGain of protocol.graphGains) {
    const args = { circuit, polarity, seed: protocol.seed, duration: protocol.duration, parameters: { graphGain },
      perturbations: basePerturbations, recordEvery: 10, recordNeurons: false };
    const closed = runSensorimotorTrial(args); addResult(closed);
    const open = runSensorimotorTrial({ ...args, condition: 'sensory_open' }); addResult(open);
    const frozen = runSensorimotorTrial({ ...args, condition: 'frozen' }); addResult(frozen);
    const ablated = runSensorimotorTrial({ ...args, condition: 'sensory_edge_ablation' }); addResult(ablated);
    const replay = runSensorimotorTrial({ ...args, condition: 'replay', replay: closed.sensorRecording }); addResult(replay);
    const counterClosed = runSensorimotorTrial({ ...args, perturbations: changedPerturbations }); addResult(counterClosed, { probe: 'additional_unseen_torque' });
    const counterReplay = runSensorimotorTrial({ ...args, condition: 'replay', perturbations: changedPerturbations, replay: closed.sensorRecording });
    addResult(counterReplay, { probe: 'additional_unseen_torque' });
    const angleDifference = (a, b) => maxDifference(a.frames.map((f) => f.angle), b.frames.map((f) => f.angle));
    const feedbackChangedTorque = maxDifference(counterClosed.activeTorques, closed.activeTorques);
    pairedChecks.push({ detector, polarity: polarity.id, graphGain,
      closedVersusOpenPeakReductionFraction: 1 - closed.summary.peakDeviationRadians / open.summary.peakDeviationRadians,
      closedVersusOpenRmsReductionFraction: 1 - closed.summary.rmsDeviationRadians / open.summary.rmsDeviationRadians,
      feedbackChangedTorqueUnderUnseenPerturbation: feedbackChangedTorque,
      checks: { identicalReferencePerturbations: [open, frozen, ablated, replay].every((t) => maxDifference(t.perturbations, closed.perturbations) === 0),
        edgeAblationEqualsOpen: angleDifference(ablated, open) === 0,
        matchedReplayEqualsClosed: angleDifference(replay, closed) === 0,
        replayBlindToUnseenPerturbation: maxDifference(counterReplay.activeTorques, closed.activeTorques) === 0,
        closedRespondsToUnseenPerturbationOrGainZero: graphGain === 0 ? feedbackChangedTorque === 0 : feedbackChangedTorque > 1e-8,
        gainZeroEqualsOpen: graphGain !== 0 || angleDifference(closed, open) === 0 },
      interpretation: 'A positive reduction is only a result of this uncalibrated polarity/gain hypothesis. Negative and zero results retained.' });
  }
  for (const polarity of POLARITY_HYPOTHESES) {
    for (const observationDelay of [0, .04]) addResult(runSensorimotorTrial({ circuit, polarity,
      parameters: { observationDelay }, perturbations: basePerturbations, recordEvery: 10, recordNeurons: false }), { probe: 'delay_sensitivity' });
    const predicted = buildSensorimotorCircuit(mapping, { detector, signPolicy: 'verified_then_predicted' });
    addResult(runSensorimotorTrial({ circuit: predicted, polarity, perturbations: basePerturbations,
      recordEvery: 10, recordNeurons: false }), { probe: 'predicted_transmitter_sign_sensitivity', signPolicy: 'verified_then_predicted', predictedSignEdges: predicted.statistics.predictedSignEdges });
    for (const frequencyHz of protocol.frequencyProbesHz) transfer.push({ detector, polarity: polarity.id,
      ...measureClampedTransfer({ circuit, polarity, frequencyHz }) });
  }
  addResult(runSensorimotorTrial({ circuit, polarity: POLARITY_HYPOTHESES[0], perturbations: basePerturbations.map(() => 0),
    recordEvery: 10, recordNeurons: false }), { probe: 'zero_disturbance' });
}
const primaryPairs = pairedChecks.filter((p) => p.graphGain === 4);
const range = (key) => [Math.min(...primaryPairs.map((p) => p[key])), Math.max(...primaryPairs.map((p) => p[key]))];
const audit = { schema: 'fly.sensorimotor-audit.v1', generatedAt: new Date().toISOString(),
  source: { file: 'app/data/sensorimotor_mapping.json', sha256: sha(bytes) },
  modelSourceSha256: sha(await readFile(new URL('./sensorimotor_model.mjs', import.meta.url))),
  bodyModelSourceSha256: sha(await readFile(new URL('./joint_motor_model.mjs', import.meta.url))),
  testSourceSha256: sha(await readFile(new URL('./tests/sensorimotor_model.test.mjs', import.meta.url))),
  protocol, parameters: SENSORIMOTOR_PARAMETERS, provenance: sensorimotorProvenance,
  trialCount: results.length, transferProbeCount: transfer.length, integratedTrialSteps: results.reduce((n, r) => n + r.summary.integrationSteps, 0),
  namespace: mapping.namespace, neuralPropagationSimulated: true, biologicalReconstructionValidated: false,
  tuningValidated: false, locomotionSimulated: false, originalGraphModified: false,
  checksPass: results.every((r) => Object.values(r.checks).every(Boolean)) && pairedChecks.every((r) => Object.values(r.checks).every(Boolean)),
  findings: { defaultGainPeakReductionRange: range('closedVersusOpenPeakReductionFraction'),
    defaultGainRmsReductionRange: range('closedVersusOpenRmsReductionFraction'),
    allFourPolarityHypothesesRetained: true, scientificInterpretation: 'The technical loop closes and responds causally to the actual joint. Neither root tuning, signed physiological circuit, nor force scale is calibrated. Mechanical return alone occurs in sensory_open and is not evidence of neural stabilization.' },
  circuits, pairedChecks, results, transfer };
await writeFile(new URL('./data/sensorimotor_audit.json', import.meta.url), JSON.stringify(audit, null, 2) + '\n');
console.log(JSON.stringify({ trialCount: audit.trialCount, transferProbeCount: audit.transferProbeCount,
  checksPass: audit.checksPass, findings: audit.findings, source: audit.source,
  primaryPairs: primaryPairs.map(({ detector, polarity, closedVersusOpenPeakReductionFraction, closedVersusOpenRmsReductionFraction }) =>
    ({ detector, polarity, closedVersusOpenPeakReductionFraction, closedVersusOpenRmsReductionFraction })) }, null, 2));
if (!audit.checksPass) process.exitCode = 1;
