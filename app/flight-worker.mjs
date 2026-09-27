import {runFlightTrial, FLIGHT_CONDITIONS, buildFlightMotorPools} from './flight_model.mjs';
let mappingPromise; const comparisons = new Map();
const mapping = () => mappingPromise ||= fetch('./data/flight_control_mapping.json').then(r => {if (!r.ok) throw new Error(`Zuordnungen: HTTP ${r.status}`); return r.json();});
self.onmessage = async ({data}) => {
  try {
    const source = await mapping(); const pools = buildFlightMotorPools(source);
    const parameters = {steeringPolarity: Number(data.polarity)};
    if (!comparisons.has(data.polarity)) {
      comparisons.set(data.polarity, FLIGHT_CONDITIONS.map(c => ({id:c.id,label:c.label,
        ...runFlightTrial({mapping:source,pools,condition:c.id,recordEvery:100,parameters}).summary})));
    }
    const trial = runFlightTrial({mapping:source,pools,condition:data.condition,recordEvery:5,parameters});
    self.postMessage({requestId:data.requestId,trial,comparison:comparisons.get(data.polarity),motors:source.motors});
  } catch(error) {self.postMessage({requestId:data.requestId,error:error.message});}
};
