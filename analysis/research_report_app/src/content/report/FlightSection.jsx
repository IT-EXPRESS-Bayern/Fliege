import React from 'react';
import {DataComponent,DataTable,ReportSection,RichNarrative,useDataApp} from '../../data-app-public.jsx';
export function FlightSection(){
  const {snapshot}=useDataApp();const rows=snapshot.queries?.flight_roll_controls?.rows??[];if(!rows.length)return null;
  return <section className="fly-section">
    <ReportSection id="flight-progress" title="Flügelsteuerung und ihre sensorischen Lücken" queryId="flight_roll_controls" sourceRows={rows} showHeading={false}>
      <RichNarrative id="fly:flight-progress" label="Flugrekonstruktion erläutern" value={
        '## Flügelsteuerung und ihre sensorischen Lücken\n\n'+
        '**62 anatomische Flügelmotoren sind zugeordnet:** 24 für Leistung, 24 für Steuerung, 12 für Spannung und zwei mit ungeklärter Funktion. Halterenmotoren, Sensoren und Konflikte stehen getrennt im Katalog. Die Effektor-Seite wird aus dem peripheren Nerv bestimmt; besonders beim gekreuzten DLM5 wäre die Quellseite allein irreführend.\n\n'+
        'Ein neuer [mechanischer Rollprüfstand](http://127.0.0.1:4173/flight.html) verbindet 24 DLM/DVM-IDs und zwei b1-IDs mit einem vereinfachten Körpermodell. Tonischer Leistungsantrieb erhält die integrierte Flügelschwingung; Abschalten lässt sie abklingen. Die Flügelwinkel werden aus Bewegungsgleichungen berechnet. **Neun Kerntests und 26 Auditversuche sind bestanden.**\n\n'+
        '**Die Flug-Sensorik ist noch nicht biologisch wiederhergestellt.** Im Prüfstand beeinflusst ein abstraktes Signal der tatsächlichen Körperdrehung direkt die Steuerkommandos. Diese technische Regelung dämpft die Störung bei einem angenommenen Wirkvorzeichen; beim umgekehrten Vorzeichen verstärkt sie sie. Beide Ergebnisse werden gezeigt.\n\n'+
        'Anatomisch wurden zusätzlich 244 proofread propriozeptive Eingänge und ausgewählte visuelle LPTC-Wege zu priorisierten absteigenden Neuronen erfasst. Ihre zellspezifischen Kennlinien, Rezeptorwirkungen und zeitlichen Antworten sind offen. Der Flugkern simuliert diese zentralen Verbindungen noch nicht.\n\n'+
        '**Freier Flug ist noch offen.** Der Körper bleibt aufgehängt. Kräfte und Trägheit sind Modelleinheiten; das vorhandene FlyBody-XML liefert eine dokumentierte Referenz, aber noch keine Kalibrierung dieses vereinfachten Kerns. Es fehlen Gewichtstragfähigkeit, freie Translation, Start/Landung und die vollständige Kopplung an das Gehirn. Die abschließende visuelle Prüfung der neuen Flugoberfläche wird bei der angeforderten Cloudübergabe ausdrücklich als offen mitgegeben.'
      }/>
    </ReportSection>
    <DataComponent id="flight-controls-table" title="Rollprüfstand: beide ungesicherten Steuerpolaritäten" queryId="flight_roll_controls" kind="table" sourceRows={rows} displayRows={rows} description="Direkte Motorinterventionen und technische Rückmeldung; keine biologisch validierte Flugregelung.">
      <DataTable rows={rows} columns={[{field:'condition',label:'Bedingung'},{field:'hypothesis',label:'Steuerhypothese'},{field:'peak_roll_deg',label:'Max. Rollwinkel (°)'},{field:'roll_rate_rms',label:'Rollrate RMS (rad/s)'},{field:'stroke_rms_deg',label:'Späte Schlag-RMS (°)'}]} caption="Alle Referenzbedingungen beider Vorzeichen; zusätzliche numerische Kontrollen im Audit" compactNumbers={false} searchable={false}/>
    </DataComponent>
  </section>;
}
