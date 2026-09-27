import { buildSensorimotorCircuit, runSensorimotorTrial, POLARITY_HYPOTHESES, SENSORIMOTOR_PARAMETERS, SENSORIMOTOR_CONDITIONS } from './sensorimotor_model.mjs';
let mapping; const circuits = new Map(); const summaries = new Map();
self.onmessage = async ({ data }) => {
  try {
    if (!mapping) { const response = await fetch('./data/sensorimotor_mapping.json'); if (!response.ok) throw new Error(`Sensor-Motor-Daten HTTP ${response.status}`); mapping = await response.json(); }
    if (!circuits.has(data.detector)) circuits.set(data.detector, buildSensorimotorCircuit(mapping, { detector: data.detector }));
    const circuit = circuits.get(data.detector); const polarity = POLARITY_HYPOTHESES.find(p => p.id === data.polarity);
    if (!polarity || !SENSORIMOTOR_CONDITIONS.includes(data.condition)) throw new Error('Unbekannte Versuchsbedingung');
    const options = { circuit, polarity, seed: 260927, duration: 4, recordEvery: 5, recordNeurons: true };
    const key = `${data.detector}:${polarity.id}`; let selected;
    // Sensor replay is recorded from the matching closed-loop run, never invented or shuffled.
    const closed = runSensorimotorTrial({ ...options, condition: 'closed', includeBody: data.condition === 'closed' });
    const comparison = [{ condition: 'closed', ...closed.summary }];
    if (data.condition === 'closed') selected = closed;
    if (!summaries.has(key)) {
      for (const condition of SENSORIMOTOR_CONDITIONS.filter(c => c !== 'closed')) {
        const result = runSensorimotorTrial({ ...options, condition, replay: condition === 'replay' ? closed.sensorRecording : null,
          includeBody: data.condition === condition, recordNeurons: data.condition === condition });
        comparison.push({ condition, ...result.summary });
        if (data.condition === condition) selected = result;
      }
      summaries.set(key, comparison);
    } else if (!selected) selected = runSensorimotorTrial({ ...options, condition: data.condition, includeBody: true,
      replay: data.condition === 'replay' ? closed.sensorRecording : null });
    self.postMessage({ requestId: data.requestId, frames: selected.frames, summary: selected.summary,
      parameters: SENSORIMOTOR_PARAMETERS, bodyParameters: selected.bodyParameters,
      comparison: summaries.get(key), circuit: { statistics: circuit.statistics, nodes: circuit.nodes, edges: circuit.edges.length,
        assumptions: circuit.assumptions, detector: circuit.detector, signPolicy: circuit.signPolicy },
      config: { detector: data.detector, polarity, condition: data.condition, seed: 260927 } });
  } catch (error) { self.postMessage({ requestId: data.requestId, error: error.message }); }
};
