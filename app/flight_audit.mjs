import { readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { buildFlightMotorPools, runFlightTrial, FLIGHT_CONDITIONS, FLIGHT_PARAMETERS, FLIGHT_PARAMETER_PROVENANCE } from './flight_model.mjs';
const sha = (b) => createHash('sha256').update(b).digest('hex');
const mappingBytes = await readFile(new URL('./data/flight_control_mapping.json', import.meta.url));
const mapping = JSON.parse(mappingBytes); const pools = buildFlightMotorPools(mapping); const results = [];
function execute(condition, parameters = {}, probe = 'reference', seed = 260927) {
  const trial = runFlightTrial({ mapping, condition, parameters, seed, recordEvery: 5 });
  const finite = trial.frames.every((f) => [f.mechanics.rollAngle, f.mechanics.rollRate, f.forces.left, f.forces.right,
    ...Object.values(f.flightKinematics.wings).flatMap((w) => [w.stroke, w.elevation, w.pitch]),
    ...Object.values(f.flightKinematics.halteres)].every(Number.isFinite));
  const item = { id: `${condition}:${trial.parameters.steeringPolarity}:${probe}:${seed}`, condition, probe, seed,
    parameters: trial.parameters, summary: trial.summary, integrationSteps: trial.integrationSteps,
    recordingSampleRateHz: trial.recordingSampleRateHz,
    externalPerturbationSha256: sha(JSON.stringify(trial.frames.map((f) => f.forces.externalRollTorque))),
    checks: { finite, boundedRoll: trial.frames.every((f) => Math.abs(f.mechanics.rollAngle) <= trial.parameters.rollLimit),
      fixedTranslation: trial.frames.every((f) => f.world.position.x === 0 && f.world.position.z === 0 && f.world.translationEnabled === false),
      noPeriodicInput: trial.provenance.prescribedPeriodicInput === false,
      noClaimedNeuralPropagation: trial.provenance.neuralPropagationSimulated === false,
      noFreeFlightClaim: trial.provenance.freeFlight === false } };
  results.push(item); return item;
}
for (const steeringPolarity of [1, -1]) for (const test of FLIGHT_CONDITIONS) execute(test.id, { steeringPolarity });
for (const steeringPolarity of [1, -1]) for (const tonicPower of [.1, .4, .9]) execute('power', { steeringPolarity, tonicPower }, `power_gain_${tonicPower}`);
const finer = execute('power', { dt: .000025 }, 'half_timestep');
const zero = execute('power', { initialPerturbation: 0 }, 'exact_zero_equilibrium');
const repeat = execute('power', {}, 'repeat');
execute('power', {}, 'different_seed', 17);
const get = (condition, sign = 1) => results.find((r) => r.condition === condition && r.parameters.steeringPolarity === sign && r.probe === 'reference');
const comparisons = {
  passiveDecays: get('passive').summary.finalStrokeRms < 1e-10,
  constantPowerSustains: get('power').summary.finalStrokeRms > .4,
  removingDvmPreventsSustainedOscillation: get('power_pool_ablation').summary.finalStrokeRms < 1e-10,
  removingPowerCausesDecay: get('power_off').summary.finalStrokeRms < .001,
  exactZeroHasNoArtificialKick: zero.summary.finalStrokeRms === 0,
  repeatIdentical: JSON.stringify(repeat.summary) === JSON.stringify(get('power').summary),
  symmetricPowerNoRoll: get('power').summary.peakRollRadians === 0,
  steeringIsMirrorSymmetric: get('left_steering').summary.finalRollRadians === -get('right_steering').summary.finalRollRadians,
  unknownSteeringSignReversesRoll: get('left_steering').summary.finalRollRadians < 0 && get('left_steering', -1).summary.finalRollRadians > 0,
  feedbackReceivesSamePerturbation: get('roll_open').externalPerturbationSha256 === get('roll_feedback').externalPerturbationSha256,
  feedbackReducesRollForDeclaredPositiveSign: get('roll_feedback').summary.rmsRollRate < get('roll_open').summary.rmsRollRate,
  invertedSignWorsensRollAndRemainsReported: get('roll_feedback', -1).summary.rmsRollRate > get('roll_open').summary.rmsRollRate,
  halfTimestepAmplitudeAgreement: Math.abs(finer.summary.finalStrokeRms / get('power').summary.finalStrokeRms - 1) < .01,
  halfTimestepFrequencyAgreement: Math.abs(finer.summary.wingFrequencyHz.left / get('power').summary.wingFrequencyHz.left - 1) < .005,
};
const audit = { schema: 'fly.flight-roll-audit.v1', generatedAt: new Date().toISOString(),
  source: { file: 'app/data/flight_control_mapping.json', sha256: sha(mappingBytes) },
  modelSourceSha256: sha(await readFile(new URL('./flight_model.mjs', import.meta.url))),
  testSourceSha256: sha(await readFile(new URL('./tests/flight_model.test.mjs', import.meta.url))),
  sourceNamespace: mapping.namespace, mappedPowerMotors: pools.selected.filter((m) => m.modelPool !== 'b1').length,
  mappedSteeringMotors: pools.selected.filter((m) => m.modelPool === 'b1').length,
  pools, parameters: FLIGHT_PARAMETERS, parameterProvenance: FLIGHT_PARAMETER_PROVENANCE,
  protocol: { conditions: FLIGHT_CONDITIONS, duration: .8, seed: 260927, steeringPolarities: [1, -1],
    powerSensitivity: [.1, .4, .7, .9], timestepSensitivity: [.00005, .000025],
    allConditionsRetained: true, sourceSignsAndGainsStillNull: true },
  trialCount: results.length, integratedSteps: results.reduce((sum, r) => sum + r.integrationSteps, 0),
  checksPass: results.every((r) => Object.values(r.checks).every(Boolean)) && Object.values(comparisons).every(Boolean),
  biologicalCalibration: false, neuralPropagationSimulated: false, sensorToMotorEdgesSimulated: false,
  autonomousFlight: false, freeTranslation: false, originalGraphModified: false,
  findings: { sustainedModelFrequencyHz: get('power').summary.wingFrequencyHz,
    positiveAssumptionRollPeakReductionFraction: 1 - get('roll_feedback').summary.peakRollRadians / get('roll_open').summary.peakRollRadians,
    positiveAssumptionRollRateRmsReductionFraction: 1 - get('roll_feedback').summary.rmsRollRate / get('roll_open').summary.rmsRollRate,
    invertedAssumptionRollPeakRadians: get('roll_feedback', -1).summary.peakRollRadians,
    invertedAssumptionLimitContacts: get('roll_feedback', -1).summary.limitContacts,
    interpretation: 'Mechanical self-oscillation and an engineering roll-rate feedback loop work under declared assumptions. The measured quantities are simulation output, not biological calibration or neural proof of autonomous flight.' },
  comparisons, results };
await writeFile(new URL('./data/flight_audit.json', import.meta.url), JSON.stringify(audit, null, 2) + '\n');
console.log(JSON.stringify({ trialCount: audit.trialCount, checksPass: audit.checksPass, findings: audit.findings,
  source: audit.source, comparisons }, null, 2));
if (!audit.checksPass) process.exitCode = 1;
