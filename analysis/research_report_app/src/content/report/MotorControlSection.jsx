import React from 'react';
import { DataComponent, DataTable, ReportSection, RichNarrative, useDataApp } from '../../data-app-public.jsx';

export function MotorControlSection() {
  const { snapshot } = useDataApp();
  const rows = snapshot.queries?.banc_motor_output_atlas?.rows ?? [];
  const paths = snapshot.queries?.banc_motor_path_reachability?.rows ?? [];
  const controls = snapshot.queries?.direct_motor_joint_controls?.rows ?? [];
  if (!rows.length) return null;
  return <section className="fly-section">
    <ReportSection id="motor-control-evidence" title="Motorsteuerung vom Gehirn zum Gelenk" queryId="banc_motor_output_atlas" sourceRows={rows} showHeading={false}>
      <RichNarrative id="fly:motor-control-evidence" label="Motorsteuerung erläutern" value={
        "## Motorsteuerung vom Gehirn zum Gelenk\n\n" +
        "Die durchgehende Kette lautet **absteigendes Hirnneuron → Bauchmarksschaltung → Motorneuron → Muskel → Gelenk**. BANC verbindet Gehirn und Bauchmark desselben Tiers und ist damit für diese Pfadsuche nutzbar. Es enthält **805 als Motorneuronen annotierte Zellen**, darunter **391 Beinmotorneuronen**. BANC und unser ursprüngliches FAFB-Gehirn stammen von unterschiedlichen Fliegen; Verbindungen bleiben in ihrem jeweiligen Datensatz.\n\n" +
        "**92 absteigende Neuronen aus 36 Typen** sind untersucht. Die getrennten v2/v3-Auswertungen enthalten zusammen 1.618 direkte Verbindungen und 448.942 vollständige Zwei-Kanten-Wege. Jeder gezählte Weg existiert vollständig in mindestens einem Detektor. Für die Browseransicht sind 1.739 Beispiele ausgewählt, die auf jeder Kante mindestens fünf Kontakte in beiden Detektoren haben. DNa02 und DNg13 sind literaturgestützte Kandidaten für Lenkbewegungen; DNg100 ist ein weiterer Kandidat für Schrittsteuerung. Seine aktuelle Rhythmusgenerator-Arbeit ist ein noch nicht begutachteter Preprint.\n\n" +
        "**113 konkrete Beinmotorneuronen** tragen eine veröffentlichte Femur–Tibia-Beuge- oder Streckaktion: 101 Beuger und 12 Strecker, verteilt auf sechs Beine. Das [Motorlabor](http://127.0.0.1:4173/motor.html) prüft diese anatomische Gelenkzuordnung mit direkter Aktivierung, Ausschaltung, Gegenprobe und gemeinsamer Gegenspieleraktivierung. Aktivierung, Trägheit, Dämpfung und Muskelverstärkung sind offengelegte Modellgrößen. Ein anatomischer DN-Pfad erzeugt dort noch keine simulierten neuronalen Spikes.\n\n" +
        "**48 Kontrollversuche** am Körpermodell und neun Funktionstests sind bestanden. Zusätzlich wurden die Pfaddaten mit 594 unabhängigen Datenprüfungen kontrolliert. Die Körperversuche bestätigen die korrekte Implementierung der gesetzten Gelenkgleichungen; sie bestätigen keine neue biologische Funktion. Strukturelles Entfernen bestimmter Zwischenzellen verringert die Zahl über höchstens zwei Kanten erreichbarer Motorziele, lässt jedoch längere Wege offen.\n\n" +
        "**Ein Transmitterlabel reicht nicht für die Muskelwirkung.** Bei 28 von 30 Motorneuronen mit zusätzlich verifiziertem Quellenfeld weicht die automatische Vorhersage ab. Diese selektive Teilmenge betrifft Hals und Halteren, nicht alle Neuronen. Für die 391 Beinmotorneuronen ist das verifizierte Feld leer. Die zentrale Modellregel `ACh − GABA − Glu` wird deshalb nicht als Muskelregel übernommen.\n\n" +
        "Die vollständigen Motoridentitäten, Zielmuskel- und Aktionsfelder stehen in `analysis/motor_output_atlas/`, die Schaltkreiswege in `analysis/motor_pathways/`. Kalibrierte Muskelkräfte, Gelenkrezeptoren und ihre Rückkopplung bleiben für eine biologisch belastbare Steuerung zu ergänzen."
      } />
    </ReportSection>
    <DataComponent id="motor-output-atlas-table" title="805 motorische Ausgangszellen nach Zielgruppe" queryId="banc_motor_output_atlas" kind="table" sourceRows={rows} displayRows={rows}
      description="Exakte BANC-v888-IDs. Nichtleere Aktionsfelder sind keine Aussage über deren mechanische Kalibrierung.">
      <DataTable rows={rows} columns={[
        { field: 'body_part', label: 'Körperteil' }, { field: 'motor_roots', label: 'Motorneuronen' },
        { field: 'detailed_action_present', label: 'Mit Aktionsangabe' }, { field: 'verified_transmitter_present', label: 'Mit verifiziertem Transmitterfeld' }
      ]} caption="Anatomische Identitäten und zusätzliche Quellenfelder getrennt gezählt" compactNumbers={false} searchable={false} />
    </DataComponent>
    <DataComponent id="motor-path-reachability-table" title="Konkrete absteigende Neuronen und ihre Beinmotorziele" queryId="banc_motor_path_reachability" kind="table" sourceRows={paths} displayRows={paths}
      description="Identischer vollständiger Weg in v2 und v3; jede Kante mindestens fünf Kontakte. Anatomische Erreichbarkeit ist keine Nettoaktivierung.">
      <DataTable rows={paths} columns={[
        { field: 'dn_type', label: 'DN-Typ' }, { field: 'soma_side', label: 'Soma-Seite' },
        { field: 'dn_id', label: 'Exakte BANC-ID' }, { field: 'direct_motor_count', label: 'Direkte Motorziele' },
        { field: 'within_two_motor_count', label: 'Motorziele bis 2 Kanten' }
      ]} caption="DN-Soma-Seite und Zielbein werden getrennt bestimmt" compactNumbers={false} searchable={false} />
    </DataComponent>
    <DataComponent id="motor-joint-controls-table" title="48 direkte Gelenkversuche am 3D-Körper" queryId="direct_motor_joint_controls" kind="table" sourceRows={controls} displayRows={controls}
      description="Je Bein acht Kontrollen. Identisches Störmoment mit passivem Gelenk und mit aktiven Gegenspielern; alle mechanischen Parameter sind unkalibriert.">
      <DataTable rows={controls} columns={[
        { field: 'leg', label: 'Bein' }, { field: 'flexor_ids', label: 'Beuger-IDs' },
        { field: 'extensor_ids', label: 'Strecker-IDs' }, { field: 'passive_degrees', label: 'Passive Störung (°)' },
        { field: 'coactivation_degrees', label: 'Mit Gegenspielern (°)' }, { field: 'status', label: '8 Kontrollen' }
      ]} caption="Maximale Winkelabweichung im Modell; keine gemessene biologische Muskelkraft" compactNumbers={false} searchable={false} />
    </DataComponent>
  </section>;
}
