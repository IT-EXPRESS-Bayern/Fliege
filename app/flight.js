import * as THREE from './vendor/three.module.js';
import {createArticulatedFly} from './articulated-fly.mjs';
import {FLIGHT_CONDITIONS} from './flight_model.mjs';
const $ = id => document.getElementById(id);
const format = (n,d=2) => n == null ? '—' : Number(n).toLocaleString('de-DE',{minimumFractionDigits:d,maximumFractionDigits:d});
const deg = n => n * 180 / Math.PI;
const make = (tag,text) => {const el=document.createElement(tag);el.textContent=text;return el;};
const option = (id,label) => {const el=make('option',label);el.value=id;return el;};
const notes = {
  passive:'Kein Leistungsantrieb: die gleiche kleine Startauslenkung klingt durch Dämpfung ab.',
  power:'Konstante Aktivierung der anatomischen DLM- und DVM-Pools. Der Schlag entsteht aus den mechanischen Gleichungen.',
  power_off:'Bei 400 ms wird der externe Leistungsantrieb ausgeschaltet. Es gibt keine vorgegebene Schlagfolge.',
  power_pool_ablation:'Der DVM-Pool erhält kein Kommando. Dass beide Leistungsgruppen benötigt werden, ist eine Annahme dieses reduzierten Modells.',
  left_steering:'Ab 240 ms wird der linke b1-Steuerkanal stärker aktiviert. Sein Effekt auf die Mechanik ist eine wählbare Vorzeichenhypothese.',
  right_steering:'Ab 240 ms wird der rechte b1-Steuerkanal stärker aktiviert. Die linke Gegenprobe ist gespiegelt.',
  roll_open:'Bei 400 ms wirkt ein 12 ms langer äußerer Rollimpuls. Das Drehsignal wird gemessen, beeinflusst aber keine Kommandos.',
  roll_feedback:'Gleicher Rollimpuls. Das verzögerte Drehsignal verändert direkt die b1-Kommandos. Dies ist ein technischer Regler; biologische Sensorkanten sind noch nicht angeschlossen.'
};
let result, timeMs=0, playing=false, lastTime=0, requestId=0;
const worker=new Worker(new URL('./flight-worker.mjs',import.meta.url),{type:'module'});
const scene=new THREE.Scene();scene.background=new THREE.Color('#0b1e28');
const camera=new THREE.PerspectiveCamera(40,1,.05,100);
let renderer,rig,dragging;const orbit={angle:.25,elevation:.52,radius:6.8};
function aim(){camera.position.set(Math.sin(orbit.angle)*Math.cos(orbit.elevation)*orbit.radius,1+Math.sin(orbit.elevation)*orbit.radius,Math.cos(orbit.angle)*Math.cos(orbit.elevation)*orbit.radius);camera.lookAt(0,1,-.05);}
aim();
try{
  renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));$('fl-scene').append(renderer.domElement);
  scene.add(new THREE.HemisphereLight('#e2f1ef','#76624a',2.3));const light=new THREE.DirectionalLight('#fff2d9',3.2);light.position.set(3,6,4);scene.add(light);
  const grid=new THREE.GridHelper(8,16,'#376071','#24434f');scene.add(grid);
  // A visible longitudinal axle makes the constrained experiment clear.
  const axle=new THREE.Mesh(new THREE.CylinderGeometry(.023,.023,3.7,12),new THREE.MeshStandardMaterial({color:'#66818b',metalness:.5,roughness:.5}));axle.rotation.x=Math.PI/2;axle.position.set(0,1.35,-.1);scene.add(axle);
  rig=createArticulatedFly(scene);rig.setContactsVisible(false);
  new ResizeObserver(()=>{const w=$('fl-scene').clientWidth,h=$('fl-scene').clientHeight;camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h);}).observe($('fl-scene'));
  $('fl-scene').addEventListener('pointerdown',e=>{dragging={x:e.clientX,y:e.clientY,...orbit};$('fl-scene').setPointerCapture(e.pointerId);});
  $('fl-scene').addEventListener('pointermove',e=>{if(!dragging)return;orbit.angle=dragging.angle-(e.clientX-dragging.x)*.009;orbit.elevation=Math.max(.08,Math.min(1.4,dragging.elevation+(e.clientY-dragging.y)*.008));aim();});
  for(const event of ['pointerup','pointercancel'])$('fl-scene').addEventListener(event,()=>dragging=null);
  $('fl-scene').addEventListener('wheel',e=>{e.preventDefault();orbit.radius=Math.max(3.5,Math.min(11,orbit.radius*Math.exp(e.deltaY*.001)));aim();},{passive:false});
}catch(error){$('fl-scene-error').hidden=false;$('fl-scene-error').textContent=`3D nicht verfügbar: ${error.message}`;}
function setPlaying(value){playing=value;$('fl-play').textContent=value?'Ⅱ Pausieren':'▶ Versuch abspielen';}
function busy(value){for(const id of ['fl-condition','fl-polarity','fl-play','fl-reset','fl-scrubber','fl-neuron'])$(id).disabled=value;}
function run(){setPlaying(false);busy(true);$('fl-status').textContent='Flügelmechanik und acht Kontrollbedingungen werden berechnet …';worker.postMessage({requestId:++requestId,condition:$('fl-condition').value,polarity:Number($('fl-polarity').value)});}
function frameAt(){const frames=result.trial.frames;const dt=frames[1].tMs-frames[0].tMs;return frames[Math.max(0,Math.min(frames.length-1,Math.round(timeMs/dt)))];}
function neuronDetail(frame){
  const node=result.motors.find(n=>n.id===$('fl-neuron').value);if(!node)return;
  const selected=result.trial.pools.selected.find(n=>n.id===node.id);const pane=$('fl-neuron-detail');pane.replaceChildren();
  pane.append(make('code',node.id),make('p',`${node.cellType} · ${node.targetMuscle||'Muskelziel ungeklärt'} · ${node.sourceFunction||'Funktion ungeklärt'}`),
    make('p',`Quellseite: ${node.sourceSide||'unbekannt'} · Effektor: ${node.effectorSide||'unbekannt'} (${node.effectorSideEvidence||'keine Seitenbelegung'}).`),
    make('p',node.annotationConflict?`Annotationskonflikt: ${node.annotationConflict}`:'Kein im Export erkannter Zuordnungskonflikt.'),
    make('p',selected?`Im Versuch angeschlossen: ${selected.modelPool}; gesetztes Kommando ${format(frame.neural.motorCommandsById[node.id]??0,3)} (0–1). Keine simulierte zentrale Neuronenaktivität.`:'Anatomisch katalogisiert, in diesem mechanischen Versuch nicht dynamisch angeschlossen.'),
    make('p','Kinematisches Vorzeichen und Kraftverstärkung sind nicht durch die Zell-ID bestimmt.'));
}
const NS='http://www.w3.org/2000/svg';
const svg=(tag,attrs,text)=>{const e=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);if(text)e.textContent=text;return e;};
function traces(){
  const chart=$('fl-trace');chart.replaceChildren();const frames=result.trial.frames;
  const start=Math.max(0,Math.min(780,timeMs-10)),end=start+20;
  const local=frames.filter(r=>r.tMs>=start&&r.tMs<=end);
  const all=result.trial.frames;
  const forceScale=Math.max(.1,...local.map(r=>Math.max(Math.abs(r.forces.left),Math.abs(r.forces.right))));
  const rollScale=Math.max(1,...all.map(r=>Math.abs(deg(r.mechanics.rollAngle))));
  const panels=[
    {label:`Schlag ° · ${format(start,1)}–${format(end,1)} ms`,top:22,height:76,range:90,rows:local,start,end,channels:[['#78caca',r=>deg(r.flightKinematics.wings.left.stroke)],['#e4ac78',r=>deg(r.flightKinematics.wings.right.stroke)]]},
    {label:'Kraft · gleiches Zeitfenster',top:131,height:76,range:forceScale,rows:local,start,end,channels:[['#78caca',r=>r.forces.left],['#e4ac78',r=>r.forces.right]]},
    {label:'Rollwinkel ° · gesamter Versuch',top:240,height:74,range:rollScale,rows:all,start:0,end:800,channels:[['#c4e4b0',r=>deg(r.mechanics.rollAngle)]]}
  ];
  for(const p of panels){const x=t=>72+(t-p.start)/(p.end-p.start)*910;const y=v=>p.top+p.height/2-v/p.range*p.height/2;
    chart.append(svg('text',{x:9,y:p.top-7,fill:'#a9b8bb','font-size':11},p.label));
    for(const v of [-p.range,0,p.range])chart.append(svg('line',{x1:72,x2:982,y1:y(v),y2:y(v),stroke:'#28404b'}),svg('text',{x:64,y:y(v)+4,'text-anchor':'end',fill:'#a9b8bb','font-size':10},format(v,1)));
    for(const[color,read]of p.channels)chart.append(svg('polyline',{points:p.rows.map(r=>`${x(r.tMs)},${y(read(r))}`).join(' '),fill:'none',stroke:color,'stroke-width':1.7}));
    chart.append(svg('line',{x1:x(timeMs),x2:x(timeMs),y1:p.top,y2:p.top+p.height,stroke:'#edf0e8','stroke-width':1}));
  }
  chart.append(svg('text',{x:980,y:15,'text-anchor':'end',fill:'#e4ac78','font-size':11},'Rechts'),svg('text',{x:921,y:15,'text-anchor':'end',fill:'#78caca','font-size':11},'Links'));
}
function drawFrame(){if(!result)return;const frame=frameAt();rig?.update(frame.body,{flightKinematics:frame.flightKinematics});
  $('fl-time').textContent=`${format(timeMs,2)} / 800 ms`;$('fl-scrubber').value=timeMs;
  $('fl-stroke').textContent=`${format(deg(frame.flightKinematics.wings.left.stroke),1)}° / ${format(deg(frame.flightKinematics.wings.right.stroke),1)}°`;
  $('fl-roll').textContent=`${format(deg(frame.mechanics.rollAngle),2)}°`;$('fl-force').textContent=`${format(frame.forces.left,3)} / ${format(frame.forces.right,3)}`;
  $('fl-power').textContent=`${format(frame.neural.effectivePower.left,3)} / ${format(frame.neural.effectivePower.right,3)}`;$('fl-steer').textContent=`${format(frame.neural.steeringActivation.left,3)} / ${format(frame.neural.steeringActivation.right,3)}`;
  $('fl-sensor').textContent=format(frame.neural.rollSensorSignal,4);neuronDetail(frame);traces();
}
function renderResults(){const t=result.trial;const wing=result.motors.filter(n=>n.cellClass==='wing_motor_neuron');
  $('fl-status').textContent=`${t.pools.selected.length} anatomische Motor-IDs im mechanischen Versuch · ${t.integrationSteps.toLocaleString('de-DE')} Integrationsschritte`;
  $('fl-mode').textContent=FLIGHT_CONDITIONS.find(c=>c.id===t.condition).label;$('fl-condition-note').textContent=notes[t.condition];
  $('fl-mapping-count').textContent=wing.length;$('fl-mapping-note').textContent=`Davon ${wing.filter(n=>n.sourceFunction==='wing_power').length} Leistung, ${wing.filter(n=>n.sourceFunction==='wing_steering').length} Steuerung und ${wing.filter(n=>n.sourceFunction==='wing_tension').length} Spannung; übrige Funktion offen. Nur DLM/DVM und b1 sind hier aktiv angeschlossen.`;
  $('fl-frequency').textContent=`${format(t.summary.wingFrequencyHz.left,1)} / ${format(t.summary.wingFrequencyHz.right,1)} Hz`;
  $('fl-comparisons').replaceChildren(...result.comparison.map(r=>{const row=make('tr','');row.classList.toggle('selected',r.id===t.condition);for(const v of [r.label,`${format(r.wingFrequencyHz.left,2)} / ${format(r.wingFrequencyHz.right,2)} Hz`,`${format(deg(r.peakRollRadians),3)}°`,`${format(deg(r.finalStrokeRms),3)}°`])row.append(make('td',v));return row;}));
  $('fl-audit-note').textContent=`Gewählte b1-Wirkhypothese: ${t.parameters.steeringPolarity>0?'+':'−'}. Späte Flügel-RMS: letzte 20 % des Versuchs, beide Seiten zusammen. Eine im Modell dämpfende Rückmeldung beweist keine reale Halterenschaltung. Anschläge im gewählten Lauf: ${t.summary.limitContacts}.`;
  $('fl-timing').textContent=`Rechenschritt ${format(t.parameters.dt*1e6,0)} µs · gespeicherte Anzeige ${format(t.recordingSampleRateHz,0)} Hz · obere Kurven zeigen 20 ms`;
  $('fl-parameters').textContent=`Modellannahmen: Eigenfrequenz ${t.parameters.naturalFrequencyHz} Hz; tonischer Leistungsbefehl ${t.parameters.tonicPower}; Sensorverzögerung ${t.parameters.sensorDelay*1000} ms; Sensorzeitkonstante ${t.parameters.sensorTau*1000} ms. Kräfte und Trägheit sind unkalibrierte Modelleinheiten. Die Halteren bewegen sich über eine vereinfachte mechanische Kopplung; daraus wird kein echtes Sensorsignal abgeleitet. Alle Parameter und Grenzen stehen in der Methodendatei.`;
  const previous=$('fl-neuron').value;$('fl-neuron').replaceChildren(...result.motors.map(n=>option(n.id,`${n.cellType} · ${n.effectorSide||'?'} · ${n.id}`)));
  $('fl-neuron').value=result.motors.some(n=>n.id===previous)?previous:t.pools.selected[0].id;drawFrame();
}
worker.onmessage=({data})=>{if(data.requestId!==requestId)return;if(data.error){$('fl-status').textContent=`Berechnung nicht verfügbar: ${data.error}`;return;}result=data;timeMs=0;renderResults();busy(false);};
worker.onerror=event=>{$('fl-status').textContent=`Modellfehler: ${event.message}`;busy(true);};
$('fl-condition').replaceChildren(...FLIGHT_CONDITIONS.map(c=>option(c.id,c.label)));$('fl-condition').value='power';
for(const id of ['fl-condition','fl-polarity'])$(id).addEventListener('change',run);
$('fl-neuron').addEventListener('change',()=>result&&neuronDetail(frameAt()));
$('fl-scrubber').addEventListener('input',()=>{setPlaying(false);timeMs=Number($('fl-scrubber').value);drawFrame();});
$('fl-play').addEventListener('click',()=>{if(timeMs>=800)timeMs=0;setPlaying(!playing);});$('fl-reset').addEventListener('click',()=>{setPlaying(false);timeMs=0;drawFrame();});
function animate(now){const elapsed=Math.min(now-lastTime||0,100);lastTime=now;if(playing&&result){timeMs=Math.min(800,timeMs+elapsed*Number($('fl-speed').value));drawFrame();if(timeMs>=800)setPlaying(false);}renderer?.render(scene,camera);requestAnimationFrame(animate);}
requestAnimationFrame(animate);run();
