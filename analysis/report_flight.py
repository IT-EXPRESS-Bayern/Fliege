"""Source-linked flight mapping and explicitly uncalibrated roll-test results."""
import hashlib
import json
import math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def extend_flight_snapshot(snapshot):
    audit=json.loads((ROOT/'app/data/flight_audit.json').read_text(encoding='utf-8'))
    mapping=json.loads((ROOT/'analysis/flight_control_mapping/audit.json').read_text(encoding='utf-8'))
    assert audit['checksPass']
    assert hashlib.sha256((ROOT/audit['source']['file']).read_bytes()).hexdigest()==audit['source']['sha256']==mapping['browserSha256']
    assert hashlib.sha256((ROOT/'app/flight_model.mjs').read_bytes()).hexdigest()==audit['modelSourceSha256']
    rows=[{'condition':r['condition'],'hypothesis':r['parameters']['steeringPolarity'],
           'peak_roll_deg':round(math.degrees(r['summary']['peakRollRadians']),4),
           'roll_rate_rms':round(r['summary']['rmsRollRate'],5),
           'stroke_rms_deg':round(math.degrees(r['summary']['finalStrokeRms']),4)}
          for r in audit['results'] if r['probe']=='reference']
    snapshot['report']['flight']={'trialCount':audit['trialCount'],'wingMotorRows':62,'freeFlight':False,'neuralPropagationSimulated':False}
    snapshot['queries']['flight_roll_controls']={'rows':rows,'source':{
      'label':'Reduzierter mechanischer Rollprüfstand mit anatomischen DLM/DVM- und b1-IDs',
      'executedAt':audit['generatedAt'],
      'tables':[{'name':'Lokaler vollständiger Versuchsaudit','href':'http://127.0.0.1:4173/data/flight_audit.json'},
                {'name':'BANC-Anatomie und Pfade','href':'http://127.0.0.1:4173/data/flight_control_mapping.json'},
                {'name':'Flugmotor-Anatomie','href':'https://www.nature.com/articles/s41586-023-06099-0'},
                {'name':'FlyBody-Körperreferenz','href':'https://github.com/TuragaLab/flybody/blob/main/flybody/fruitfly/assets/fruitfly.xml'}],
      'evidenceFlow':[{'title':'Anatomische Zuordnung','detail':'62 echte Flügelmotorzeilen: 24 Leistung,24 Steuerung,12 Spannung,2 ungeklärt. Der gesamte Wing/Haltere-Export hat91Zeilen,85konfliktfreiePoolkandidaten und6ausgewieseneKonflikte. Effektor-Seiten folgen eindeutigen peripheren Nervennamen; Quellseite bleibt erhalten.'},
                      {'title':'Strukturelle Sensorik','detail':'244 proofread propriozeptive Eingänge; DNs und sensorische Pfade getrennt. Bei ≥5 Kontakten je Kante: v2 10625,v3 15347 direkte/Zweikantenpfade. Ausgewählte LPTC→Zwischenzelle→priorisierte DN:18/32 Pfade. Dies rekonstruiert noch keine vollständige optische oder Halteren-Dynamik.'},
                      {'title':'Mechanischer Test','detail':'26Versuche mit50µsIntegrationsschritt.24Leistungsmotoren und2b1-Steuerneuronen erhalten direkt gesetzte normierte Kommandos. Tonischer Antrieb wirkt als negative Dämpfung, nicht als Sinusvorgabe. Eigenfrequenz200Hz ist gesetzt; die ähnliche resultierende Frequenz ist keine unabhängige biologische Validierung.'},
                      {'title':'Rückkopplung und Grenzen','detail':'Ein abstrakter verzögerter Drehsensor greift direkt auf b1-Kommandos zu. Beide ungesicherten Steuerpolaritäten bleiben sichtbar; das invertierte Vorzeichen verschlechtert die Rollantwort. Keine zentrale neuronale Propagation, SI-Kräfte, Gewichtstragfähigkeit oder freier Flug.'}],
      'metricDefinitions':[{'label':'Maximaler Rollwinkel','definition':'Größter absoluter Rollwinkel während0,8s in Grad; identischer äußerer Impuls für roll_open/roll_feedback.', 'componentIds':['flight-controls-table']},
                           {'label':'Späte Schlag-RMS','definition':'Quadratisches Mittel der Schlagwinkel beider Flügel über die letzten20Prozent des Versuchs in Grad. Ein Modellergebnis, kein anatomisches Maß.','componentIds':['flight-controls-table']}]
    }}
