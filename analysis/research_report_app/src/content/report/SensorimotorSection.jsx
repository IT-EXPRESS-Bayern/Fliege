import React from 'react';
import { DataComponent, DataTable, ReportSection, RichNarrative, useDataApp } from '../../data-app-public.jsx';

export function SensorimotorSection() {
  const { snapshot } = useDataApp();
  const rows = snapshot.queries?.sensorimotor_polarity_controls?.rows ?? [];
  if (!rows.length) return null;
  return <section className="fly-section">
    <ReportSection id="sensorimotor-progress" title="Erster berechneter Sensor-Motor-Regelkreis" queryId="sensorimotor_polarity_controls" sourceRows={rows} showHeading={false}>
      <RichNarrative id="fly:sensorimotor-progress" label="Sensorische Rückkopplung erläutern" value={
        '## Erster berechneter Sensor-Motor-Regelkreis\n\n' +
        'Im [neuen 3D-Regelkreis](http://127.0.0.1:4173/sensorimotor.html) beeinflusst der tatsächliche Gelenkzustand die Sensoraktivität. Diese läuft durch einen rekonstruierten BANC-Ausschnitt, verändert die Motoransteuerung und damit die nächste Gelenkbewegung. Es werden weder eine Schrittfolge noch eine Laufroute eingegeben. Der Versuch betrifft das fixierte linke Vorderbein; Fortbewegung und vollständige Hirnautonomie sind noch offen.\n\n' +
        '**54 Gelenksensoren und 19 Motorneuronen** sind dynamisch angeschlossen. Je nach Detektor vermitteln 45 beziehungsweise 55 Zwischenzellen über 321 beziehungsweise 461 Kanten die Antwort. Der größere anatomische Export enthält 625 Sensor-IDs. Zellindividuelle Richtungskennlinien fehlen; deshalb bleiben alle vier Polaritätskombinationen gleichberechtigte Modellhypothesen.\n\n' +
        '**12 Kerntests, 194 Kontrollversuche und 24 Transferproben** sind ausgeführt. Die geschlossene Rückmeldung reagiert auf eine zusätzliche Störung; eine zuvor aufgezeichnete Sensorfolge kann das nicht. Die passive Rückfederung funktioniert auch bei ausgeschalteter Rückmeldung.\n\n' +
        '**Die Mechanik dominiert bisher.** Bei der vorab festgelegten Verstärkung 4 reicht die Reduktion der maximalen Auslenkung von −0,60 % bis +0,33 %. Das ist ein kleiner, je nach Hypothese auch nachteiliger Modelleffekt. Es belegt keine biologisch richtige Stabilisierung. Kennlinien, Rezeptorwirkungen, Zeitkonstanten und Kräfte müssen gegen unabhängige Daten geprüft werden.\n\n' +
        'Die offenen Aufgaben sind in `analysis/sensorimotor_mapping/autonomy_gaps.md` dokumentiert: Neuronendynamik, Muskelphysiologie, Kontakt und Last, Interbein-Koordination, innere Zustände, Lernen, Fressen und weitere Sinne. Dieser Arbeitsstand wird nicht als vollständige Rekonstruktion ausgegeben.'
      } />
    </ReportSection>
    <DataComponent id="sensorimotor-polarity-table" title="Alle Sensorhypothesen: Einfluss auf die Auslenkung" queryId="sensorimotor_polarity_controls" kind="table" sourceRows={rows} displayRows={rows}
      description="Gleiche Störung bei offener und geschlossener Rückmeldung. Prozentwerte sind eigene unkalibrierte Simulationsergebnisse; negative Werte bedeuten stärkere Auslenkung.">
      <DataTable rows={rows} columns={[
        { field: 'detector', label: 'Detektor' }, { field: 'polarity', label: 'Gesetzte Sensorhypothese' },
        { field: 'peak_reduction_pct', label: 'Reduktion maximal (%)' },
        { field: 'rms_reduction_pct', label: 'Reduktion RMS (%)' }
      ]} caption="Alle acht Varianten bei Graphverstärkung 4; keine Auswahl einer vermeintlich erfolgreichen Biologie" compactNumbers={false} searchable={false} />
    </DataComponent>
  </section>;
}
