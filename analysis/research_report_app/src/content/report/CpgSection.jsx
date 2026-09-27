import React from 'react';
import { DataComponent, DataTable, ReportSection, RichNarrative, useDataApp } from '../../data-app-public.jsx';

export function CpgSection() {
  const { snapshot } = useDataApp();
  const rows = snapshot.queries?.cpg_original_parameter_controls?.rows ?? [];
  if (!rows.length) return null;
  return <section className="fly-section">
    <ReportSection id="cpg-progress" title="Originalparameter: ein Rhythmus entsteht im Nervennetz" queryId="cpg_original_parameter_controls" sourceRows={rows} showHeading={false}>
      <RichNarrative id="fly:cpg-progress" label="CPG-Nachrechnung erläutern" value={
        '## Originalparameter: ein Rhythmus entsteht im Nervennetz\n\n' +
        'Das veröffentlichte BANC-Ratenmodell von Pugliese und Kollegen wurde mit **4963 Zellen, der Originalmatrix und dem archivierten Parametersatz 0** nachgerechnet. Die Originalkonfiguration verwendet einen externen konstanten Eingang von 400 willkürlichen Einheiten an DNg100. Es wurde keine periodische Reizfolge vorgegeben.\n\n' +
        '**Sechs anatomische Motorzellen zeigen rhythmische Aktivität; deren Medianfrequenz beträgt etwa 15,15 Hz.** Entfernen wir E1 oder E2, verschwindet diese Rhythmik. Nach Entfernung von I2 bleibt sie erhalten. Das DNb08-Paar erzeugt in dieser Konfiguration Aktivität, aber keinen Rhythmus. Diese Eingriffe stützen eine Funktionshypothese innerhalb dieses Modells.\n\n' +
        'Die acht Bedingungen sind im [CPG-Betrachter](http://127.0.0.1:4173/cpg.html) einzeln einsehbar. Identische Wiederholung und engere numerische Toleranz wurden geprüft. Der CPU-Solver und die Rechengenauigkeit unterscheiden sich vom ursprünglichen Programm; die Gleichheit mit der archivierten Originalzeitreihe wurde nicht geprüft.\n\n' +
        '**Der Rhythmus betrifft ein Vorderbein-Teilnetz.** Er ist noch keine Schrittfolge des Körpers und kein selbst erzeugter Handlungswunsch. Muskelkräfte, Sensorik, sechsbeinige Koordination und hirneigene Zustände müssen gesondert angeschlossen werden. Ein einzelner Parametersatz zeigt noch keine Robustheit über Tiere oder Parameterschwankungen.\n\n' +
        'Aus dem 807-MB-Archiv wurden die benötigten Originalkonfigurationen und HDF5-Parameter gezielt gelesen. Das Gesamtarchiv wurde nicht vollständig heruntergeladen oder per MD5 geprüft. Die Originalmaske mit 156 Modulzeilen enthält außerdem 27 Nichtmotoren oder unklare Zellen; die hervorgehobene konservative Maske umfasst 129 Motoren.'
      } />
    </ReportSection>
    <DataComponent id="cpg-controls-table" title="Alle acht CPG-Bedingungen mit demselben Parametersatz" queryId="cpg_original_parameter_controls" kind="table" sourceRows={rows} displayRows={rows} description="Eigene Nachrechnung eines veröffentlichten Ratenmodells. Die Frequenz beschreibt die neuronale Modellaktivität, keine gemessene Schrittfrequenz.">
      <DataTable rows={rows} columns={[{field:'condition',label:'Bedingung'},{field:'active',label:'Aktive Motoren / 129'},{field:'rhythmic',label:'Rhythmische Motoren'},{field:'score',label:'Mittlerer Rhythmik-Score'},{field:'frequency',label:'Medianfrequenz (Hz)'}]} caption="129 konservativ klassifizierte Motoren; fehlende Frequenz bedeutet keine als rhythmisch gewertete Motorzelle" compactNumbers={false} searchable={false}/>
    </DataComponent>
  </section>;
}
