import React from "react";
import { MotorControlSection } from './MotorControlSection.jsx';
import { SensorimotorSection } from './SensorimotorSection.jsx';
import { CpgSection } from './CpgSection.jsx';
import { FlightSection } from './FlightSection.jsx';
import { DataComponent, DataTable, ReportSection, RichNarrative, useDataApp } from "../../data-app-public.jsx";

const graphColumns = [
  { field: "name", label: "Datenprodukt" },
  { field: "neurons", label: "Neuronen" },
  { field: "connectionRows", label: "Verbindungszeilen" },
  { field: "grain", label: "Eine Zeile bedeutet" },
  { field: "synapses", label: "Synapsen" },
];
const pathwayColumns = [
  { field: "sense_or_output", label: "Funktion" },
  { field: "source", label: "Fachquelle" },
  { field: "matched_ids", label: "ID-Abgleich" },
  { field: "model_use", label: "Für unser Modell" },
  { field: "constraint", label: "Noch offen" },
];
const literatureColumns = [
  { field: "year", label: "Jahr" },
  { field: "work", label: "Arbeit", renderCell: (value, row) =>
    <a href={row.url} target="_blank" rel="noopener noreferrer">{value}</a> },
  { field: "finding", label: "Erkenntnis" },
  { field: "asset", label: "Nutzbare Daten" },
  { field: "fit", label: "Rolle" },
];
const integrationColumns = [
  { field: "id", label: "Eingabe" },
  { field: "role", label: "Rolle im Modell" },
  { field: "state", label: "Nutzungsstand" },
  { field: "path", label: "Lokale Datei" },
  { field: "url", label: "Quelle", renderCell: (value) => value ?
    <a href={value} target="_blank" rel="noopener noreferrer">Original</a> : "—" },
];

export function ReportContent() {
  const { snapshot, visible, appTitle, canEdit, mode, setAppTitle } = useDataApp();
  const queries = snapshot.queries ?? {};
  const neuronCoverage = queries.neuron_catalog_coverage?.rows ?? [];
  const neuronTrials = queries.neuron_function_trials?.rows ?? [];
  const neuronAblations = queries.neuron_ablation_trials?.rows ?? [];
  const sources = queries.source_inventory?.rows ?? [];
  const graphs = queries.graph_comparison?.rows ?? [];
  const literature = queries.literature?.rows ?? [];
  const pathways = queries.pathway_evidence?.rows ?? [];
  const parameters = queries.model_parameters?.rows ?? [];
  const checks = queries.validation_examples?.rows ?? [];
  const pointGroups = queries.synapse_point_groups?.rows ?? [];
  const missingStatus = queries.missing_neuron_status?.rows ?? [];
  const downloads = queries.download_pipeline?.rows ?? [];
  const pointAnalysis = queries.point_analysis?.rows ?? [];
  const rawExceptions = queries.raw_aggregate_exception?.rows ?? [];
  const rawExceptionPairs = queries.raw_exception_pairs?.rows ?? [];
  const reconciliation = queries.raw_published_reconciliation?.rows ?? [];
  const reviewBands = queries.integrated_review_bands?.rows ?? [];
  const princetonPointExclusions = queries.princeton_point_exclusion?.rows ?? [];
  const morphology616 = queries.morphology_616?.rows ?? [];
  const detectorPairs = queries.whole_brain_pair_classes?.rows ?? [];
  const detectorStrength = queries.whole_brain_new_pair_strength?.rows ?? [];
  const detectorRegions = queries.whole_brain_new_pair_regions?.rows ?? [];
  const detectorRegionCrosswalk = queries.whole_brain_region_crosswalk?.rows ?? [];
  const motorInterface = queries.banc_leg_motor_interface?.rows ?? [];
  const integrationInputs = queries.integration_inventory?.rows ?? [];
  const integrationJoinCount = snapshot.report?.integrationJoinCount ?? 0;
  const reconstruction = snapshot.report?.reconstruction ?? {};
  const wholeBrain = snapshot.report?.wholeBrainDetector ?? {};
  const synapseDownload = downloads.find(row => row.name === "flywire_synapses_783.feather");
  const pointAudit = pointAnalysis[0];
  const selectedPoints = pointAnalysis[1];
  const segmentAudit = pointAnalysis[2];
  const rawClassesReady = pointAudit?.state === "Analysiert";
  const totalReleasedPoints = pointGroups.reduce((sum, row) => sum + Number(row.synapses || 0), 0);
  const rawBothProofread = Number(pointGroups.find(row => row.class === "Beide Partner geprüft")?.synapses || 0);
  const outsideProofread = totalReleasedPoints - rawBothProofread;
  const pointDetail = segmentAudit?.state === "Analysiert"
    ? `Der Vollscan fand **${Number(selectedPoints.quantity).toLocaleString("de-DE")}** Punkte an den bisher kantenlosen IDs. **${Number(segmentAudit.points).toLocaleString("de-DE")}** davon betreffen **${Number(segmentAudit.segments).toLocaleString("de-DE")}** ungeprüfte Segment-IDs und bilden **${Number(segmentAudit.quantity).toLocaleString("de-DE")}** Kontaktgruppen nach Partner, Richtung und Hirnregion. Die übrigen 48 Rohpunkte mit zwei geprüften Partnern sind separat dokumentiert. Ein ungeprüftes Segment ist noch kein identifiziertes Neuron.`
    : pointAudit?.state === "Analysiert"
      ? `Der Einzelpunkt-Vollscan ist geprüft; **${Number(selectedPoints.quantity).toLocaleString("de-DE")}** exakte Synapsen-IDs, Segmentpartner und Nanometer-Koordinaten für die 336 betroffenen IDs liegen im lokalen Punktexport. Die gruppierte Segmentkontaktliste wird noch geprüft.`
      : synapseDownload?.state === "Prüfsumme geprüft"
        ? "Die 9,49-GB-Einzelpunkttabelle ist mit Zenodos Prüfsumme geprüft. Der noch offene Vollscan soll die 336 Fälle auf konkrete Segmentpartner und Nanometer-Koordinaten prüfen."
        : `Die 9,49-GB-Einzelpunkttabelle ist im Stand dieses Berichts **${synapseDownload?.state ?? "ausstehend"}**. Nach Prüfsumme und Vollscan können wir die 336 Fälle auf konkrete Segmentpartner und Nanometer-Koordinaten prüfen.`;
  const pointClassSummary = rawClassesReady
    ? `Der vollständige Rohscan der [offiziellen FlyWire-Einzelpunkte](https://zenodo.org/records/10676866) zählt **${totalReleasedPoints.toLocaleString("de-DE")} freigegebene Synapsen**. **${rawBothProofread.toLocaleString("de-DE")}** verbinden zwei geprüfte Root-IDs; bei den anderen **${outsideProofread.toLocaleString("de-DE")}** ist mindestens ein Partnersegment ungeprüft. Die veröffentlichte aggregierte Proofread-Tabelle zählt **54.492.922** Synapsen, also netto **48 weniger** als die Rohpunktmenge mit zwei geprüften Partnern.`
    : "Die [offiziellen FlyWire-Summendateien](https://zenodo.org/records/10676866) enthalten **130.054.535 freigegebene Synapsen**. Die vier Partnerklassen sind bis zum direkten Rohpunkt-Vollscan nur eine vorläufige Differenzrechnung; die publizierte aggregierte Proofread-Tabelle zählt **54.492.922** Kontakte.";
  const reconciliationSummary = reconciliation.length
    ? "Der globale Abgleich nach **gerichtetem Paar × Hirnregion** fand zunächst **3.214 nur im Rohfile** und **3.193 nur im Aggregat** vorhandene Schlüssel. Davon erklären **3.193 Paare mit 4.185 Kontakten** eine reine Regionsbezeichner-Differenz: `None` im Rohfile entspricht `UNASGD` im Aggregat, bei jeweils gleicher Richtung, Root-ID und Zahl. Nach dieser belegten Normalisierung bleiben **21 R7-Paare mit 48 Rohkontakten** ohne Aggregatzeile. Die 48 sind also eine Netto-Differenz; die nicht normalisierten Schlüsselabweichungen sind unten separat dokumentiert."
    : "Ein vollständiger Paar- und Hirnregionsabgleich der Roh- und Aggregatdateien ist noch offen.";
  const reconstructionSummary = reconstruction.princetonSameSpecimenRootCount
    ? `Der [Princeton-Detektor von 2025](https://doi.org/10.1101/2025.07.11.664377) untersucht **dasselbe FAFB-Präparat** mit einem neuen Verfahren. Sein ungefilterter Paar-Export meldet **${Number(reconstruction.princetonDirectedPairs).toLocaleString("de-DE")} gerichtete Paare** für **${Number(reconstruction.princetonSameSpecimenRootCount).toLocaleString("de-DE")} der 616 bislang kantenlosen IDs**. Bei **${Number(reconstruction.princetonOnlyRoots).toLocaleString("de-DE")} IDs** gab es im alten Rohpunktexport gar keinen Punkt; **${Number(reconstruction.oldRawOnlyRoots).toLocaleString("de-DE")}** haben umgekehrt nur alte Rohpunkte. Der vollständige Princeton-Einzelpunktexport enthält **${Number(reconstruction.princetonPointsTouching616).toLocaleString("de-DE")} Punkte an ${Number(reconstruction.princetonRootsWithAnyPoint).toLocaleString("de-DE")} der 616 IDs**. Die Differenz zum Paar-Export ist vollständig zerlegt: **5.814 Autapsen**, **213 nichtautaptische Punkte des R7-Roots 720575940623940963** und **20.914 Punkte**, deren Paar×Region-Zahlen nach Leerregion→\`UNASGD\` exakt mit dem ungefilterten Export stimmen. Diese Filtergleichheit erklärt nicht, warum der frühere Paar-Export den R7-Root ausließ. Beide Princeton-Exporte und der ältere Originalgraph bleiben getrennt.`
    : "Der neuere Princeton-Synapsendetektor wird am selben FAFB-Präparat getrennt geprüft.";
  const crossAnimalSummary = reconstruction.bancReviewedHomologRoots && reconstruction.maleTypeMappedRoots
    ? `Für **${Number(reconstruction.bancReviewedHomologRoots).toLocaleString("de-DE")} FAFB-IDs** liegen geprüfte morphologische [BANC-v888](https://doi.org/10.1038/s41586-026-10735-w)-Homologien vor; daraus wurden **${Number(reconstruction.bancPartnerTypeHypotheses).toLocaleString("de-DE")}** Richtung×Partner-Zelltyp-Muster geordnet. Bei **${Number(reconstruction.bancMatchedRootsWithPrinceton).toLocaleString("de-DE")} dieser 34 FAFB-IDs** findet der Princeton-Detektor eigene Kandidaten und bei **${Number(reconstruction.bancMatchedRootsWithOldRaw).toLocaleString("de-DE")}** liegen alte Rohpunkte vor. [MaleCNS v1.0](https://doi.org/10.1016/j.cell.2026.08.015) bietet Typ-/Seitenvergleich für **${Number(reconstruction.maleTypeMappedRoots).toLocaleString("de-DE")} IDs**, darunter 520 R1–6-Photorezeptoren und **${Number(reconstruction.maleOther96MappedRoots).toLocaleString("de-DE")} der übrigen 96**. Beide Connectome stammen von **anderen Tieren**. Ihre Kanten sind deshalb Hypothesen für FAFB-Zelltypen und keine nachträglich gemessenen FAFB-Verbindungen.`
    : "Vergleichsconnectome für Gehirn und Bauchmark werden als getrennte Tierdaten ausgewertet.";

  return <article className="report-content fly-report" aria-label="Forschungsbericht zur virtuellen Fruchtfliege">
    <header className="report-hero">
      <div className="fly-eyebrow">FLYWIRE · FAFB v783 · FORSCHUNGSSTAND {snapshot.report?.asOf ?? "2026-09-27"}</div>
      <h1 data-data-app-title contentEditable={canEdit && mode === "edit"} suppressContentEditableWarning
        aria-label={canEdit && mode === "edit" ? "Berichtstitel bearbeiten" : undefined}
        onBlur={canEdit && mode === "edit" ? (event) => setAppTitle(event.currentTarget.textContent.trim() || appTitle) : undefined}
        onKeyDown={canEdit && mode === "edit" ? (event) => {
          if (event.key === "Enter") { event.preventDefault(); event.currentTarget.blur(); }
        } : undefined}>{appTitle}</h1>
      <RichNarrative id="fly:deck" className="report-deck" label="Einordnung bearbeiten"
        value={"Fachartikel, Originaldaten und Zusatzmaterial für eine virtuelle Fliege. Jede Zahl und Zuordnung lässt sich auf eine Quelle oder einen lokalen ID-Abgleich zurückführen."} />
    </header>

    {visible("fly-summary") && <ReportSection id="fly-summary" title="Zusammenfassung" queryId="graph_comparison"
      queryIds={["graph_comparison", "pathway_evidence", "whole_brain_pair_classes", "whole_brain_new_pair_strength", "integrated_review_bands", "princeton_point_exclusion", "morphology_616", "missing_neuron_status"]}
      sourceRowsByQuery={{ graph_comparison: graphs, pathway_evidence: pathways,
        whole_brain_pair_classes: detectorPairs, whole_brain_new_pair_strength: detectorStrength,
        integrated_review_bands: reviewBands, princeton_point_exclusion: princetonPointExclusions,
        morphology_616: morphology616, missing_neuron_status: missingStatus }} showHeading={false}
      className="fly-summary">
      <RichNarrative id="fly:summary" label="Zusammenfassung bearbeiten" value={
        "## Was wir bereits verwenden können\n\n" +
        "- Die [3D-App](http://127.0.0.1:4173/) lädt den vollständigen Export der offiziellen aggregierten FlyWire-Verbindungen: **139.255 Neuronen**, **15.091.983 gerichtete Neuronenpaare** und **54.492.922 gezählte Synapsen**. Ihr Lade- und Aktivierungstest ist bestanden. Ein erzeugter Spike ist ein technischer Funktionstest; in der Arena bleibt die Bewegungssteuerung aus dem Hirngraphen gesperrt. Das separate Neuronenlabor prüft ausgewählte Ausgänge mit einer ausdrücklich hypothetischen Körperübersetzung.\n" +
        "- Die publizierten v783-Eingaben von Shiu und Eon sind geprüft. Ihre **138.639 Modell-IDs** stimmen exakt überein. Alle **15.091.983** gerichteten Modellpaare und Synapsenzahlen stimmen mit dem Originalexport überein; 616 offizielle IDs haben keine geprüfte Verbindung.\n" +
        `- Fachartikel geben Startpunkte für **Sehen, Geruch, Berührung, Geschmack, Fressen und Bewegung**. Das lokale Integrationspaket umfasst **${integrationInputs.length} eingeordnete Eingaben** und **${integrationJoinCount} Verknüpfungsregeln**. Exakte IDs helfen bei der Kopplung; Reizstärke, Körperdynamik und Eigenantrieb müssen wir als Modelle begründen.\n` +
        `- Der Princeton-Detektor findet im **selben FAFB-Präparat** **${Number(wholeBrain.princetonOnlyPairs ?? 0).toLocaleString("de-DE")} gerichtete Paare**, die im älteren Originalexport fehlen. Diese automatischen Kandidaten sind keine bestätigten neuen Synapsen. **${Number(wholeBrain.princetonOnlyTouching616 ?? 0).toLocaleString("de-DE")} Paare** berühren die 616 ursprünglich kantenlosen IDs; ihre **sechs disjunkten Prüfbänder** summieren sich auf 616. Alle 616 haben Skelettdaten; [R7 und fünf Partner in 3D ansehen](http://127.0.0.1:4173/skeleton.html). BANC und MaleCNS liefern getrennte tierübergreifende Vergleichsmuster.`
      } />
    </ReportSection>}

    {neuronCoverage.length > 0 && <section className="fly-section">
      <ReportSection id="fly-neuron-validation" title="Neuronen benennen und gezielt prüfen"
        queryId="neuron_catalog_coverage" queryIds={["neuron_catalog_coverage", "neuron_function_trials", "neuron_ablation_trials"]}
        sourceRowsByQuery={{ neuron_catalog_coverage: neuronCoverage, neuron_function_trials: neuronTrials, neuron_ablation_trials: neuronAblations }} showHeading={false}>
        <RichNarrative id="fly:neuron-validation" label="Neuronentests erläutern" value={
          "## Neuronen benennen und gezielt prüfen\n\n" +
          "**Alle 139.255 offiziellen Root-IDs sind katalogisiert.** Veröffentlichte Typen, Zellnamen und Aliase machen 138.765 davon benennbar; 490 bleiben unbenannt. Für 22.312 liegen kuratierte Funktionsannotationen vor. Eine solche Angabe beschreibt den Forschungsstand und ist keine vollständige Funktionsmessung jeder einzelnen Zelle. Die Originalfelder sind unverändert erhalten.\n\n" +
          "**42 Hauptversuche und vier Diagnoseversuche wurden ausgeführt.** Im vollständigen Originalgraphen wurden Sinneseingänge angeregt, getrennte Ausgänge ausgelesen und Zellen gezielt stillgelegt. 1.002 technische Prüfungen der Hauptversuche bestanden. Unter sechs Referenzreizen reagierten 7.048 Zellen; 6.845 hatten mindestens einen nicht direkt erzwungenen Spike. Diese Antwortprofile sind über exakte IDs benannt und bleiben Modellbefunde.\n\n" +
          "Die nachfolgende Tabelle zeigt 150-Hz-Anregung während 400 ms. Zucker aktiviert beide MN9-Ausgänge, Wasser schwächer, Bitter allein in diesem Modelllauf gar nicht. Die aktuelle linke MN9-Zelle `720575940618238523` wurde unabhängig in [Tastekin et al., Table S1](https://doi.org/10.1016/j.cell.2026.08.016) identifiziert; die fehlende ältere Shiu-ID wird nicht geraten.\n\n" +
          "**Der Vergleich zum Antennenputzen scheitert teilweise.** JO-F erzeugt stärkere Antworten der absteigenden aDN-Zellen als JO-C/E. Das widerspricht dem publizierten Vergleichsmuster von [Shiu et al.](https://doi.org/10.1038/s41586-024-07763-9). Bei gleicher Eingangsanzahl und gleichem Reizplan bleibt die Abweichung bestehen: JO-C/E ergibt 5 / 0 Hz, JO-F 30 / 10 Hz an aDN1 / aDN2. Die vorgeschaltete aBN1-Zelle selbst reagiert im ursprünglichen Vergleich stärker auf JO-C/E. Zusätzlich erregende Beiträge von DNg84, DNg57 und DNge011 sind überprüfbare Ursachen innerhalb unseres Modells. Ihre biologische Funktion folgt daraus nicht.\n\n" +
          "Im [3D-Neuronenlabor](http://127.0.0.1:4173/lab.html) lassen sich die aufgezeichneten Versuche samt Stilllegung und Kontrollstilllegung abspielen. Der gegliederte Körper übersetzt aDN-Aktivität in eine ausdrücklich angenommene Putzbewegung. Alle 42 Körperwiedergaben sind geprüft; 8 bewegen sich, 34 bleiben ohne aDN-Spikes still. MN9- und Steuerneuronen werden einzeln angezeigt, haben aber noch keinen kalibrierten Körperaktor. Die direkte Körperkontrolle ist separat gekennzeichnet.\n\n" +
          "**Seitenangaben brauchen Quellenkontext.** 1.301 Stürner-DN-Zeilen nennen die Gegenrichtung zu beiden neueren FAFB-Annotationen. Das passt zur [dokumentierten historischen Links-rechts-Konvention](https://codex.flywire.ai/faq); einzelne Ausnahmen bleiben offen. Wir übertragen daraus keine ungeprüften seitenspezifischen Bewegungsbefehle. Pfadsuche, Seitenvergleich und vollständige Quellenbelege liegen in `analysis/neuron_pathways/`, der Katalog in `analysis/neuron_catalog/`, Versuchsläufe in `analysis/neuron_assays/`."
        } />
      </ReportSection>
      <DataComponent id="neuron-catalog-coverage-table" title="Benennung, Funktionsannotation und Modellantwort" queryId="neuron_catalog_coverage"
        kind="table" sourceRows={neuronCoverage} displayRows={neuronCoverage} description="Überlappende Teilmengen; nicht addieren.">
        <DataTable rows={neuronCoverage} columns={[{ field: "measure", label: "Zuordnung" }, { field: "count", label: "Neuronen" }, { field: "scope", label: "Bedeutung" }]}
          caption="Die Menge benennbarer Zellen ist größer als die Menge mit einer publizierten Funktionsangabe" compactNumbers={false} searchable={false} />
      </DataComponent>
      <DataComponent id="neuron-function-trials-table" title="Tatsächlich berechnete Ausgangsantworten" queryId="neuron_function_trials"
        kind="table" sourceRows={neuronTrials} displayRows={neuronTrials} description="Modell-Hz pro Zelle im 400-ms-Reizfenster; 2,5 Hz Zählauflösung, ein deterministischer Lauf pro Bedingung.">
        <DataTable rows={neuronTrials} columns={[{ field: "stimulus", label: "Eingang" }, { field: "readout", label: "Ausgänge 1 / 2" }, { field: "first_hz", label: "1: Hz" }, { field: "second_hz", label: "2: Hz" }, { field: "interpretation", label: "Einordnung" }]}
          caption="Qualitative Geschmacksantwort und fehlgeschlagener JO-Spezifitätsvergleich" compactNumbers={false} searchable={false} />
      </DataComponent>
      <DataComponent id="neuron-ablation-trials-table" title="Gezielte Stilllegung mit Gegenprobe" queryId="neuron_ablation_trials"
        kind="table" sourceRows={neuronAblations} displayRows={neuronAblations} description="Die Kontrollzelle wurde nach vergleichbarem Verbindungsgrad ausgewählt.">
        <DataTable rows={neuronAblations} columns={[{ field: "input", label: "Eingang" }, { field: "condition", label: "Eingriff" }, { field: "adn1_hz", label: "aDN1: Hz" }, { field: "adn2_hz", label: "aDN2: Hz" }]}
          caption="aBN1-Stilllegung löscht die getrennten JO-C/E- und JO-F-Ausgangsantworten; die Kontrollstilllegung erhält sie" compactNumbers={false} searchable={false} />
      </DataComponent>
    </section>}

    {visible("fly-graph") && <section className="fly-section">
      <ReportSection id="fly-graph-explainer" title="Der Hirngraph" queryId="graph_comparison"
        sourceRows={graphs} showHeading={false}>
        <RichNarrative id="fly:graph-intro" label="Graph-Erklärung bearbeiten" value={
          "## Der Originalgraph ist jetzt direkt nutzbar\n\n" +
          "Die offizielle aggregierte Proofread-Tabelle enthält 16.847.997 Zeilen nach **Neuronenpaar × Hirnregion**. Unser vollständiger Export dieser Tabelle fasst Regionen pro gerichtetem Paar zusammen, behält alle dort gezählten 54.492.922 Synapsen und wurde ohne Stärkeschwelle gebaut. Die 3D-App lädt diesen vollständigen Export für Graph-Inspektion und Aktivität. Ein Vollvergleich zeigt: Alle 15.091.983 Shiu-Modellpaare und ihre Synapsenzahlen sind exakt gleich. Ein separater Rohpunkt-Vollvergleich zeigt eine Regionslabel-Konvention und 21 zusätzliche R7-Paare; beide Befunde stehen unten als eigene Evidenzschichten. Shius Modell ergänzt ein vorhergesagtes Vorzeichen; unser Export hält sechs Transmitterkanäle vor.\n\n" +
          "Die visuelle Datensatzsammlung verwendet für dieselben 138.639 verbundenen IDs eine **andere kompakte Indexreihenfolge** als Shiu. Die Übersetzung muss über die volle Root-ID laufen.\n\n" +
          "Quelle: [FlyWire-Archivdatensatz v783](https://zenodo.org/records/10676866). Vollvergleich: analysis/model_original_edge_comparison.json. Neuer Export: brain/graph-original-v783/."
        } />
      </ReportSection>
      <DataComponent id="graph-table" title="Vier Darstellungen desselben FAFB-Standes" queryId="graph_comparison"
        kind="table" sourceRows={graphs} displayRows={graphs}
        description="Zeilen haben je nach Produkt unterschiedliche Granularität; Synapsensummen sind separat angegeben.">
        <DataTable rows={graphs} columns={graphColumns} caption="Vergleich der lokalen und publizierten FAFB-Graphen"
          compactNumbers={false} searchable={false} />
      </DataComponent>
    </section>}

    {visible("fly-graph") && <section className="fly-section">
      <ReportSection id="fly-detector-comparison" title="Vollhirnvergleich der Synapsendetektoren" queryId="whole_brain_pair_classes"
        queryIds={["whole_brain_pair_classes", "whole_brain_new_pair_strength", "whole_brain_new_pair_regions", "whole_brain_region_crosswalk"]}
        sourceRowsByQuery={{ whole_brain_pair_classes: detectorPairs,
          whole_brain_new_pair_strength: detectorStrength, whole_brain_new_pair_regions: detectorRegions,
          whole_brain_region_crosswalk: detectorRegionCrosswalk }}
        showHeading={false}>
        <RichNarrative id="fly:detector-comparison" label="Detektorvergleich bearbeiten" value={
          "## Zwei Synapsendetektoren untersuchten dasselbe FAFB-Gehirn\n\n" +
          "Der vollständige Abgleich zählt **15.091.983 gerichtete Paare** im ursprünglichen FlyWire-v783-Export und **19.773.733** im neueren Princeton-Export. **13.447.535 Paare** stehen in beiden Tabellen. **6.326.198** stehen nur bei Princeton, **1.644.448** nur im Original. Beide Detektoren verwenden die offiziellen v783-Root-IDs; ihre Synapsenzahlen werden nicht addiert. Eine Princeton-only-Kante ist zunächst ein **automatischer Prüf-Kandidat**, keine experimentell bestätigte neu rekonstruierte Synapse.\n\n" +
          "Von den Princeton-only-Paaren betreffen **6.323.027** zwei IDs, die **jeweils andere Kanten** im ursprünglichen Graphen hatten; das konkrete Prä/Post-Paar war dort nicht verbunden. Nur **3.171** berühren die 616 zuvor kantenlosen IDs. Die große Differenz betrifft also überwiegend mögliche zusätzliche Paare *innerhalb* des alten Graphknotensatzes. Unter den 6.323.027 haben **5.207.559 (82,4 %)** genau einen Princeton-Count; **63.854** haben mindestens fünf und **14.842** mindestens zehn. Umgekehrt besitzen nur **437** Original-only-Paare mindestens fünf alte Counts. Die Größenverteilung ist eine Priorisierung für die Sichtung, keine biologische Qualitätswahrscheinlichkeit.\n\n" +
          "Die Regionstabelle zeigt Paar×Neuropil-Schlüssel und ist daher **nicht** zur Zahl eindeutiger Neuronenpaare addierbar: dasselbe gerichtete Paar kann mehrere Regionen berühren. Selbst bei in beiden Detektoren vorhandenen Paaren gibt es **755.099 nur bei Princeton** und **204.865 nur im Original** vorkommende Regionsschlüssel. Die größten Princeton-only-Häufungen liegen in ME_L und ME_R. Die vollständigen 79 Regionszeilen, die Regions-Kreuztabelle und Paar-Deltas stehen in `analysis/whole_brain_detector_comparison/`; der Originalgraph bleibt unverändert."
        } />
      </ReportSection>
      <DataComponent id="whole-brain-pair-table" title="Gerichtete Paare in Original und Princeton"
        queryId="whole_brain_pair_classes" kind="table" sourceRows={detectorPairs} displayRows={detectorPairs}
        description="Vier disjunkte Klassen über denselben FAFB-v783-Root-ID-Satz; Synapsenzahlen gehören je zum angegebenen Detektor.">
        <DataTable rows={detectorPairs} columns={[
          { field: "class", label: "Paarmenge" }, { field: "pairs", label: "Gerichtete Paare" },
          { field: "originalSynapses", label: "Original-Counts" },
          { field: "princetonSynapses", label: "Princeton-Counts" },
        ]} caption="13.447.535 gemeinsame Paare; die Detektor-Counts bleiben getrennt" compactNumbers={false} searchable={false} />
      </DataComponent>
      <DataComponent id="whole-brain-strength-table" title="Princeton-only-Paare zwischen IDs mit jeweils anderen Originalkanten"
        queryId="whole_brain_new_pair_strength" kind="table" sourceRows={detectorStrength} displayRows={detectorStrength}
        description="6.323.027 Paare in disjunkten Zählwertklassen; weitere 3.171 Princeton-only-Paare berühren die 616 ursprünglich isolierten IDs.">
        <DataTable rows={detectorStrength} columns={[
          { field: "synapsesPerPair", label: "Princeton-Counts je Paar" },
          { field: "directedPairs", label: "Gerichtete Paare" },
          { field: "princetonSynapses", label: "Summe Princeton-Counts" },
        ]} caption="5.207.559 Paare mit genau einem Princeton-Count; 63.854 mit mindestens fünf" compactNumbers={false} searchable={false} />
      </DataComponent>
      <DataComponent id="whole-brain-region-table" title="Regionen mit den meisten Princeton-only-Kandidaten"
        queryId="whole_brain_new_pair_regions" kind="table" sourceRows={detectorRegions} displayRows={detectorRegions.slice(0, 8)}
        description="Acht größte von 79 Neuropilen; ein gerichtetes Paar kann in mehreren Regionen vorkommen.">
        <DataTable rows={detectorRegions.slice(0, 8)} columns={[
          { field: "neuropil", label: "Neuropil" },
          { field: "pairRegionKeys", label: "Paar×Region-Schlüssel" },
          { field: "princetonSynapses", label: "Princeton-Counts" },
          { field: "keysGe5", label: "Schlüssel mit ≥5" },
        ]} caption="Regionale Verteilung automatischer Kandidaten, keine validierten Synapsen" compactNumbers={false} searchable={false} />
      </DataComponent>
      <DataComponent id="whole-brain-region-crosswalk-table" title="Regionsunterschiede trotz gemeinsamen Neuronpaars"
        queryId="whole_brain_region_crosswalk" kind="table" sourceRows={detectorRegionCrosswalk} displayRows={detectorRegionCrosswalk}
        description="Regionsschlüssel kommen nur in einer Detektortabelle vor, während das Prä/Post-Paar in beiden vorkommt.">
        <DataTable rows={detectorRegionCrosswalk} columns={[
          { field: "case", label: "Einseitige Region" },
          { field: "pairRegionKeys", label: "Paar×Region-Schlüssel" },
        ]} caption="Regionsunterschiede erzeugen hier keine neuen gerichteten Neuronpaare" compactNumbers={false} searchable={false} />
      </DataComponent>
    </section>}

    {visible("fly-gaps") && <section className="fly-section">
      <ReportSection id="fly-gap-intro" title="Fehlende Kontaktpunkte" queryId="synapse_point_groups"
        queryIds={["synapse_point_groups", "missing_neuron_status", "raw_aggregate_exception", "raw_exception_pairs", "raw_published_reconciliation", "integrated_review_bands", "princeton_point_exclusion", "morphology_616"]}
        sourceRowsByQuery={{ synapse_point_groups: pointGroups, missing_neuron_status: missingStatus,
          raw_aggregate_exception: rawExceptions, raw_exception_pairs: rawExceptionPairs,
          raw_published_reconciliation: reconciliation, integrated_review_bands: reviewBands,
          princeton_point_exclusion: princetonPointExclusions, morphology_616: morphology616 }}
        showHeading={false}>
        <RichNarrative id="fly:gap-intro" label="Lückenanalyse bearbeiten" value={
          "## Wo der geprüfte Hirngraph noch Kontakte verliert\n\n" +
          pointClassSummary + "\n\n" + reconciliationSummary + "\n\n" +
          "Von den **616** offiziellen IDs ohne Kante in der aggregierten Tabelle haben **336** freigegebene Punkte; **280** haben keine. " + pointDetail + " Für **552** IDs gibt es zusätzlich **2.757 nach Qualitätsregeln ausgewählte Zielzelltyp-Hypothesen** aus gleichartigen verbundenen Zellen und, im Sehsystem, aus der publizierten Typmatrix. Diese Hypothesen sind ausdrücklich keine exakten neuen Neuron-zu-Neuron-Kanten und ihre Häufigkeiten keine kalibrierten Wahrscheinlichkeiten.\n\n" + reconstructionSummary + "\n\n" + crossAnimalSummary +
          (rawExceptionPairs.length ? "\n\nEin konkreter Rohdatenfund betrifft **R7 720575940623940963**: In ME_R gibt es **14 Dm9→R7**, **6 R7→Dm9** und **4 R7→Tm20** Einzelkontakte; die 21 Paar/Region-Schlüssel fehlen alle in der publizierten Aggregattabelle. Das belegt Kontaktpunkte, noch keine physiologische Signalwirkung." : "")
        } />
      </ReportSection>
      <ReportSection id="fly-integrated-review" title="Rekonstruktions- und 3D-Sichtung" queryId="integrated_review_bands"
        queryIds={["integrated_review_bands", "princeton_point_exclusion", "morphology_616"]}
        sourceRowsByQuery={{ integrated_review_bands: reviewBands,
          princeton_point_exclusion: princetonPointExclusions, morphology_616: morphology616 }} showHeading={false}>
        <RichNarrative id="fly:integrated-review" label="Rekonstruktionsprüfung bearbeiten" value={
          "### Die 616 IDs sind jetzt in sechs getrennte Prüfbänder eingeordnet\n\n" +
          "Jede ID steht **genau einmal** in der Prüfliste; die sechs Bandzahlen summieren sich auf **616**. Das ist eine Reihenfolge für die anatomische Sichtung, keine Wahrscheinlichkeit für eine echte Verbindung. Princeton-Paare sind automatische Detektionen im selben FAFB-Präparat; alte Segmentkontakte und Zelltyp-Hypothesen bleiben eigene Belege.\n\n" +
          "Die Princeton-Punktdatei ist vollständig: **26.941 automatische Punktaufrufe** berühren die 616 IDs. Davon sind **5.814** Selbstkontakte, **213** nichtautaptische Punkte des R7-Roots 720575940623940963 und **20.914** Punkte, die nach der dokumentierten Leerregion-Zuordnung exakt den **3.233** Paar×Region-Zahlen im ungefilterten Princeton-Verbindungsexport entsprechen. Dieser rechnerische Abgleich erklärt die R7-Filterursache nicht.\n\n" +
          "Die offizielle, erneut MD5-geprüfte Skelettdatei liefert **151.369 Knoten für alle 616 IDs**, einschließlich aller **195 IDs**, für die Princeton Kandidaten und der alte Rohpunktexport keinen Punkt hat. Die [3D-Skelettansicht](http://127.0.0.1:4173/skeleton.html) zeigt derzeit R7 und fünf Partner exemplarisch für die räumliche Prüfung. Die Knoten der übrigen IDs sind im Quelldatensatz nachgewiesen und im Audit erfasst. Ein Skelett allein beweist keine Synapse."
        } />
      </ReportSection>
      <DataComponent id="integrated-review-bands-table" title="Sechs disjunkte Prüfbänder für genau 616 IDs"
        queryId="integrated_review_bands" kind="table" sourceRows={reviewBands} displayRows={reviewBands}
        description="Die Bänder beschreiben den nächsten Prüfpfad, keine kalibrierte Sicherheit oder neue Kante im Originalgraphen.">
        <DataTable rows={reviewBands} columns={[
          { field: "band", label: "Prüfband" }, { field: "ids", label: "FAFB-IDs" },
          { field: "evidence", label: "Bedeutung" },
        ]} caption="616 v783-IDs ohne ursprüngliche aggregierte Proofread-Kante" compactNumbers={false} searchable={false} />
      </DataComponent>
      <DataComponent id="princeton-point-exclusion-table" title="Princeton-Punktdatei und Verbindungsexport stimmen nach empirischen Filtern überein"
        queryId="princeton_point_exclusion" kind="table" sourceRows={princetonPointExclusions} displayRows={princetonPointExclusions}
        description="Disjunkte Zerlegung der 26.941 Princeton-Punkte für die 616 IDs; der Grund des R7-Ausschlusses ist unbekannt.">
        <DataTable rows={princetonPointExclusions} columns={[
          { field: "class", label: "Punktklasse" }, { field: "points", label: "Punkte" },
          { field: "meaning", label: "Einordnung" },
        ]} caption="26.941 = 5.814 Autapsen + 213 R7-Punkte + 20.914 Verbindungspunkte" compactNumbers={false} searchable={false} />
      </DataComponent>
      <DataComponent id="morphology-616-table" title="Alle 616 bislang kantenlosen IDs besitzen ein 3D-Skelett"
        queryId="morphology_616" kind="table" sourceRows={morphology616} displayRows={morphology616}
        description="Vollscan der offiziellen v783-LOD1-Morphologie; Geometrie ist kein Synapsennachweis.">
        <DataTable rows={morphology616} columns={[
          { field: "metric", label: "Nachweis" }, { field: "value", label: "Anzahl" },
          { field: "meaning", label: "Nutzung" },
        ]} caption="151.369 Knoten für 616 Root-IDs, darunter alle 195 Princeton-only-IDs" compactNumbers={false} searchable={false} />
      </DataComponent>
      <DataComponent id="point-group-table" title="Alle veröffentlichten Kontaktpunkte nach Partnerstatus"
        queryId="synapse_point_groups" kind="table" sourceRows={pointGroups} displayRows={pointGroups}
        description={rawClassesReady ? "Vier disjunkte Gruppen direkt aus dem Vollscan aller offiziellen Einzelpunkte." : "Vorläufige Differenzrechnung aus zwei offiziellen Alle-Partner-Zähltabellen; Rohscan ausstehend."}>
        <DataTable rows={pointGroups} columns={[
          { field: "class", label: "Partnerstatus" },
          { field: "synapses", label: "Synapsenpunkte" },
          { field: "sharePercent", label: "Anteil %" },
          { field: "meaning", label: "Bedeutung" },
        ]} caption="Freigegebene Synapsen nach Proofreading-Status der Partner"
          compactNumbers={false} searchable={false} />
      </DataComponent>
      {reconciliation.length > 0 && <DataComponent id="reconciliation-table"
        title="Globaler Vergleich von Rohpunkten und Aggregattabelle"
        queryId="raw_published_reconciliation" kind="table"
        sourceRows={reconciliation} displayRows={reconciliation}
        description="Zuerst exakte Prä/Post/Region-Schlüssel; die 3.193 None/UNASGD-Fälle wurden anschließend anhand identischer Paare und Zählwerte zugeordnet.">
        <DataTable rows={reconciliation} columns={[
          { field: "class", label: "Befund" },
          { field: "pairRegionKeys", label: "Paar×Region-Schlüssel" },
          { field: "synapses", label: "Synapsen" },
          { field: "meaning", label: "Einordnung" },
        ]} caption="Vollvergleich der publizierten FAFB-v783-Roh- und Aggregatdateien"
          compactNumbers={false} searchable={false} />
      </DataComponent>}
      {rawExceptions.length > 0 && <DataComponent id="raw-exception-table"
        title="R7-Teilbefund: 48 Rohkontakte außerhalb der Aggregattabelle"
        queryId="raw_aggregate_exception" kind="table" sourceRows={rawExceptions} displayRows={rawExceptions}
        description="Alle Punkte sind im offiziellen Rohdatensatz; der Grund für ihr Fehlen in proofread_connections ist nicht geklärt. Diese Ausnahme wird getrennt vom aggregierten Graphen geführt.">
        <DataTable rows={rawExceptions} columns={[
          { field: "rootId", label: "Proofread Root-ID" },
          { field: "cellType", label: "Zelltyp" },
          { field: "neuropil", label: "Region" },
          { field: "rawPoints", label: "Rohpunkte" },
          { field: "directedPairs", label: "Gerichtete Paare" },
          { field: "aggregatedRows", label: "Aggregierte Zeilen dieser ID" },
        ]} caption="R7-Rohkontakt-Ausnahme der veröffentlichten FAFB-v783-Dateien"
          compactNumbers={false} searchable={false} />
      </DataComponent>}
      {rawExceptionPairs.length > 0 && <DataComponent id="raw-exception-pairs-table"
        title="21 gerichtete Rohkontakt-Paare mit Zelltypen" queryId="raw_exception_pairs"
        kind="table" sourceRows={rawExceptionPairs} displayRows={rawExceptionPairs}
        description="Prä- und Postsynapsen-IDs bleiben exakte Dezimalstrings. Zelltypen stammen aus der v783-Annotation; kein Paar ist dadurch funktionell validiert.">
        <DataTable rows={rawExceptionPairs} columns={[
          { field: "preType", label: "Sender-Typ" },
          { field: "preRootId", label: "Sender-ID" },
          { field: "postType", label: "Empfänger-Typ" },
          { field: "postRootId", label: "Empfänger-ID" },
          { field: "synapseCount", label: "Rohpunkte" },
          { field: "region", label: "Region" },
        ]} caption="Beobachtete R7-Rohkontakte außerhalb der offiziellen Aggregattabelle"
          compactNumbers={false} />
      </DataComponent>}
      <DataComponent id="missing-status-table" title="616 bisher kantenlose Neuronen" queryId="missing_neuron_status"
        kind="table" sourceRows={missingStatus} displayRows={missingStatus}
        description="Die Zeilen sind überlappende Evidenzklassen aus verschiedenen Detektoren und Tieren. Ihre ID-Zahlen dürfen nicht addiert werden.">
        <DataTable rows={missingStatus} columns={[
          { field: "state", label: "Befund" }, { field: "ids", label: "IDs" },
          { field: "nextEvidence", label: "Nächster Nachweis" },
        ]} caption="Lücken und vorsichtige Rekonstruktionskandidaten"
          compactNumbers={false} searchable={false} />
      </DataComponent>
      <DataComponent id="point-analysis-table" title="Prüfschritte für exakte Punkt- und Segmentbelege"
        queryId="point_analysis" kind="table" sourceRows={pointAnalysis} displayRows={pointAnalysis}
        description="Der Vollscan liefert Punkt-IDs und Koordinaten; Segmentkontakte und die 48 Rohpunkt-Ausnahmen bleiben als getrennte Evidenzschichten erhalten.">
        <DataTable rows={pointAnalysis} columns={[
          { field: "stage", label: "Analyseschritt" },
          { field: "state", label: "Stand" },
          { field: "quantity", label: "Geprüfte Anzahl" },
          { field: "output", label: "Lokaler Nachweis" },
        ]} caption="Befundstufen der Einzelpunktanalyse" compactNumbers={false} searchable={false} />
      </DataComponent>
    </section>}

    {visible("fly-pathways") && <section className="fly-section">
      <ReportSection id="fly-pathway-intro" title="Konkrete Sinneswege" queryId="pathway_evidence"
        sourceRows={pathways} showHeading={false}>
        <RichNarrative id="fly:pathway-intro" label="Sinneswege bearbeiten" value={
          "## Fachartikel liefern konkrete Ein- und Ausgänge\n\n" +
          "Die [visuelle Zellliste](https://doi.org/10.1038/s41586-024-07981-1) enthält genau die 139.255 offiziellen v783-IDs. [DoOR](https://doi.org/10.1038/srep21841) und [Benton 2025](https://doi.org/10.1038/s44319-025-00476-8) ergeben Typ-Hypothesen für 2.281 v783-Riechsensoren; die Geruchsantworten wurden an anderen Fliegen gemessen. Die [Kopfborsten-Arbeit](https://elifesciences.org/articles/108044) nennt 705 BMN-IDs, alle im Modellgraphen. [Tastekin et al.](https://doi.org/10.1016/j.cell.2026.08.016) liefern 411 Geschmackssensoren und 66 Motorneuronen, ebenfalls mit exaktem Modell-ID-Treffer. [Stürner et al.](https://doi.org/10.1038/s41586-025-08925-z) liefern 1.316 absteigende und 2.345 aufsteigende beziehungsweise SA-Zellen für die Verbindung zum Bauchmark."
        } />
      </ReportSection>
      <DataComponent id="pathway-table" title="Was sich schon anatomisch zuordnen lässt" queryId="pathway_evidence"
        kind="table" sourceRows={pathways} displayRows={pathways}
        description="Exakte Root-ID-Treffer zeigen Graphmitgliedschaft; sie messen weder Reiztransduktion noch Muskelkraft.">
        <DataTable rows={pathways} columns={pathwayColumns}
          caption="Fachquellen mit anatomisch zuordenbaren Sinnes- und Motorwegen" searchable={false} />
      </DataComponent>
      <ReportSection id="fly-shiu-mapping" title="Shiu-Zellen" queryId="source_inventory"
        sourceRows={sources.filter(row => row.id === "shiu-tables")} showHeading={false}>
        <RichNarrative id="fly:shiu-mapping" label="Shiu-ID-Prüfung bearbeiten" value={
          "Die Shiu-Zusatzmappe enthält 28 Blätter. Ein reproduzierbarer Scan der ersten drei Spalten fand 1.532 verschiedene Root-IDs; **1.305** sind in v783 exakt vorhanden. Ausgewählt wurden 229 für Zucker, Wasser, Bittergeschmack, Ir94e, Johnstons Organ, MN9 und Antennenputzen. Vier davon fehlen als exakte v783-ID, darunter MN9_l. Zwei als links bezeichnete aDN-Zellen haben in der aktuellen v783-Annotation side=right. Deshalb ist ihre Körperseite vor einer Steuerkopplung gesperrt. Die genaue Liste mit Blatt und Zeile liegt in data/research_sources/shiu/derived/shiu_supplement_index.json."
        } />
      </ReportSection>
      <ReportSection id="fly-modality-limits" title="Sehen, Geruch und Modulation" queryId="pathway_evidence"
        sourceRows={pathways} showHeading={false}>
        <RichNarrative id="fly:modality-limits" label="Sinnesdaten einordnen" value={
          "Photorezeptor-Ausgangssynapsen sind in v783 laut der [visuellen Facharbeit](https://doi.org/10.1038/s41586-024-07981-1) deutlich untererkannt; ein Bildsensor braucht eine kalibrierte Vorderstufe. Der Geruchs-Crosswalk findet **1.324** Riechsensor-IDs mit übereinstimmender Benton-Rezeptor- und DoOR-Antworteinheit; die anderen Zuordnungen sind teils mehrdeutig oder ohne Antwortdaten. Kuratierte [Neuropeptid-Evidenz](https://github.com/flyconnectome/drosophila_neuropeptides) lässt sich auf **11.567** v783-IDs auf Zelltypebene projizieren. Das sind Kandidaten für innere Zustände, keine gemessenen Rezeptoren oder Wirksamkeiten am einzelnen FAFB-Neuron."
        } />
      </ReportSection>
    </section>}

    {visible("fly-model") && <section className="fly-section">
      <ReportSection id="fly-model-intro" title="Aktivität" queryId="model_parameters"
        sourceRows={parameters} showHeading={false}>
        <RichNarrative id="fly:model-intro" label="Modellbeschreibung bearbeiten" value={
          "## Ein Modell kann den Graphen aktivieren – mit benannten Annahmen\n\n" +
          "[Shiu et al.](https://doi.org/10.1038/s41586-024-07763-9) verwendeten ein gehirnweites Leaky-Integrate-and-Fire-Modell. Der öffentliche [Eon-Code](https://github.com/eonsystemspbc/fly-brain) setzt diese Parameter für mehrere Rechen-Backends um. Die Werte unten sind **Modellparameter**, keine Messungen für jedes einzelne Neuron. Das Vorzeichen einer Ausgangsverbindung wird vereinfacht aus dem vorhergesagten Transmitter des sendenden Neurons abgeleitet.\n\n" +
          "Die Shiu-Publikation prüfte konkrete sensorische Schaltkreise auf **v630**. Ihr Repository und Eons Tabellen enthalten **v783-Eingaben**. Die publizierten v630-Antwortwerte dienen daher als Vergleichsmuster, nicht als garantierte v783-Raten."
        } />
      </ReportSection>
      <DataComponent id="model-parameter-table" title="Öffentlich implementierte LIF-Startparameter" queryId="model_parameters"
        kind="table" sourceRows={parameters} displayRows={parameters}
        description="Abgelesen aus Eons Brian2- und PyTorch-Implementierung auf gepinnter Git-Revision.">
        <DataTable rows={parameters} columns={[
          { field: "parameter", label: "Parameter" }, { field: "value", label: "Wert" },
          { field: "use", label: "Funktion" },
        ]} caption="LIF-Modellparameter aus Eons öffentlichem Code" searchable={false} />
      </DataComponent>
      <ReportSection id="fly-validation-intro" title="Vergleichsdaten" queryId="validation_examples"
        sourceRows={checks} showHeading={false}>
        <RichNarrative id="fly:validation-intro" label="Validierung bearbeiten" value={
          "## Die Fachliteratur gibt überprüfbare Antwortmuster vor\n\n" +
          "Die [Shiu-Ergänzungstabellen](https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-024-07763-9/MediaObjects/41586_2024_7763_MOESM2_ESM.xlsx) enthalten Zellantworten, Stimulationen und Verhaltenszählungen. Beispiel: Im v630-Modell antwortete aBN1 auf JO-CE-Stimulation mit 50,77 Hz, auf JO-F mit 1,23 Hz. Table 10 zählt **150 von 164** empirisch geprüften Vorhersagen als korrekt. Das ist ein Ergebnis dieser Tests, keine allgemeine Genauigkeit einer „lebenden“ Fliege. Alle 13 ausgelesenen Zellchecks und 105 Verhaltenszählwerte sind mit Originalzellen im lokalen JSON indexiert."
        } />
      </ReportSection>
      <DataComponent id="validation-table" title="Vier publizierte v630-Kontrollmuster" queryId="validation_examples"
        kind="table" sourceRows={checks} displayRows={checks}
        description="Mittelraten in Hz; die Werte sind v630-Ergebnisse und keine v783-Vorhersagen.">
        <DataTable rows={checks} columns={[
          { field: "circuit", label: "Schaltkreis" },
          { field: "v630_comparison_hz", label: "Publizierte Mittelrate" },
          { field: "sheet_row", label: "Originalstelle" },
          { field: "v783_condition", label: "v783-Abgleich" },
        ]} caption="Nachvollziehbare Aktivitätsmuster aus Shiu et al." searchable={false} />
      </DataComponent>
    </section>}

    {visible("fly-autonomy") && <ReportSection id="fly-autonomy" title="Selbstständiges Handeln" queryId="literature"
      queryIds={["literature", "source_inventory"]}
      sourceRowsByQuery={{ literature: literature.filter(row => ["Gattuso et al.", "Rayshubskiy et al.", "Wang-Chen et al.", "Vaxenburg et al."].includes(row.work)),
        source_inventory: sources.filter(row => row.id === "autonomous-prototype") }}
      showHeading={false}>
      <RichNarrative id="fly:autonomy" label="Autonomie-Modell bearbeiten" value={
        "## Selbstständiges Verhalten ohne vorgegebene Aufgabe\n\n" +
        "Unsere [3D-Arena im Browser](http://127.0.0.1:4173/) zeigt bereits einen **zielungebundenen Prototyp**. Vier abstrakte Aktivitätsgruppen für Laufen, Links-/Rechtslenken und Putzen entwickeln sich mit internen Zuständen, eigenem Rauschen und Rückmeldung über die Wandnähe. Eine feste Zielposition oder Aktionsfolge wird nicht vorgegeben. Die App-Tests einschließlich der Körperkinematik bestanden; dazu gehört ein geschlossener Arena-Lauf mit Bewegung und wechselnden Verhaltenszuständen. Diese Gruppen sind **nicht** auf einzelne FlyWire-Neuronen abgebildet. Der volle Graph lässt sich in derselben App laden und untersuchen, steuert die Körperbewegung aber noch nicht.\n\n" +
        "Das [Gattuso-Modell](https://doi.org/10.1073/pnas.2407626122) zeigt spontanes und geruchsmoduliertes Gehen in fünf abstrakten absteigenden Einheiten. [Rayshubskiy et al.](https://doi.org/10.7554/eLife.102230) liefern Mess- und Analysebezüge für DNa01/DNa02 beim Lenken. [FlyGym](https://doi.org/10.1038/s41592-024-02497-y) liefert Körpermechanik; [FlyBody](https://doi.org/10.1038/s41586-025-09029-4) demonstriert Gang und Flug in einem physikalischen Körper mit trainierten Controllern. Diese Bausteine helfen bei der nächsten Kopplung, aber intrinsische Aktivität, Sensoren und Motoren müssen wissenschaftlich zugeordnet und an Verhalten geprüft werden. Der Arena-Prototyp belegt, dass **autonomes Modellverhalten technisch möglich** ist; er validiert noch keine biologisch korrekte Ganzhirn-Körper-Fliege."
      } />
    </ReportSection>}

    {visible("fly-autonomy") && <section className="fly-section">
      <ReportSection id="fly-motor-interface" title="Motorische Schnittstelle" queryId="banc_leg_motor_interface"
        sourceRows={motorInterface} showHeading={false}>
        <RichNarrative id="fly:motor-interface" label="Motor-Schnittstelle bearbeiten" value={
          "## Vom Bauchmark zum gegliederten Körper\n\n" +
          "Die [BANC-v888-Daten](https://doi.org/10.7910/DVN/7WTH1N) liefern **391 geprüfte Beinmotorneuronen** für alle sechs Beine. Die getrennten Eingangstabellen zählen **112.809 gerichtete Paare in v2** und **117.988 in v3**; **101.637 Paare** kommen in beiden Versionen vor, darunter **35.725 mit jeweils mindestens fünf Counts**. Der [gegliederte Körper in der 3D-Arena](http://127.0.0.1:4173/) stellt Fußkontakt und Gelenkstellungen über `getBodyObservation()` bereit. Seine Bewegung verwendet weiterhin abstrakte Antriebe: **kein Aktuatorkanal ist biologisch kalibriert**. BANC stammt von einem anderen Tier als FAFB, sodass diese Motor-IDs und Eingänge nur Vergleichs- und Zuordnungsmuster für eine spätere Kopplung sind."
        } />
      </ReportSection>
      <DataComponent id="banc-leg-motor-table" title="Geprüfte Motorreferenz und Eingangsgraphen"
        queryId="banc_leg_motor_interface" kind="table" sourceRows={motorInterface} displayRows={motorInterface}
        description="BANC v888 ist ein anderes Tier; v2 und v3 sind getrennte Kantenstände und keine zusätzliche FAFB-Messung.">
        <DataTable rows={motorInterface} columns={[
          { field: "measure", label: "Messgröße" }, { field: "value", label: "Wert" },
          { field: "scope", label: "Geltungsbereich" },
        ]} caption="Motorevidenz für den Entwurf der Körperschnittstelle" compactNumbers={false} searchable={false} />
      </DataComponent>
    </section>}

    <MotorControlSection />
    <SensorimotorSection />
    <CpgSection />
    <FlightSection />

    {visible("fly-literature") && <section className="fly-section">
      <ReportSection id="fly-literature-intro" title="Fachschriften" queryId="literature"
        sourceRows={literature} showHeading={false}>
        <RichNarrative id="fly:literature-intro" label="Literatureinordnung bearbeiten" value={
          "## Fachschriften als Arbeitsmaterial\n\n" +
          "Die Auswahl besteht aus Originalarbeiten mit Daten, Zelllisten, Modellcode oder Körperreferenzen. Der [BANC-v888-Datensatz](https://doi.org/10.1038/s41586-026-10735-w) ergänzt die fehlende Bauchmark-Perspektive, stammt aber aus einem **anderen Tier**. Seine IDs dürfen nicht direkt an FAFB v783 angehängt werden. [FlyGym/NeuroMechFly v2](https://doi.org/10.1038/s41592-024-02497-y) und [FlyBody](https://doi.org/10.1038/s41586-025-09029-4) sind Körper- und Physikvorbilder mit getrennten Steuerungen; ein eigener Browserkörper braucht weiterhin die Übertragung von Sensoren, Motoren und Zeitsteuerung."
        } />
      </ReportSection>
      <DataComponent id="literature-table" title="Primärarbeiten und Preprints" queryId="literature"
        kind="table" sourceRows={literature} displayRows={literature}
        description="Verlinkte Primärarbeiten mit nutzbaren Datensätzen und klarer Rolle im Modell.">
        <DataTable rows={literature} columns={literatureColumns}
          caption="Facharbeiten für Connectom, Aktivität, Sinne und Körper" compactNumbers={false} />
      </DataComponent>
    </section>}

    {visible("fly-implementation") && <section className="fly-section">
      <ReportSection id="fly-implementation" title="Integration" queryId="source_inventory"
        queryIds={["source_inventory", "pathway_evidence"]}
        sourceRowsByQuery={{ source_inventory: sources, pathway_evidence: pathways }} showHeading={false}>
        <RichNarrative id="fly:implementation" label="Integrationsweg bearbeiten" value={
          "## So verwenden wir die Daten im Fliegenmodell\n\n" +
          "1. **Graph:** brain/graph-original-v783/ als aus v783 abgeleiteten vollständigen CSR-Export laden. Regionen sind pro Paar zusammengefasst und Transmitterwahrscheinlichkeiten quantisiert; IDs als Dezimalstrings oder 64-Bit-Werte behandeln.\n" +
          "2. **Sensoren:** Visuelle Typen, Geruch, Kopfborsten und Geschmack an v783-Root-IDs binden. Wo nur Zelltypen oder Glomeruli vorliegen, bleibt die Übertragung eine markierte Hypothese.\n" +
          "3. **Dynamik:** Shius LIF-Ansatz mit dokumentierten Startparametern implementieren und publizierte Reizantworten als Richtungstests verwenden. Danach lokale Aktivität, Stabilität und Sensitivität prüfen.\n" +
          "4. **Körper:** DN-/MN-Ausgänge an ein 3D-Körpermodell binden; Mechanik und Muskeln kommen aus einer eigenen Körpermodellschicht.\n" +
          "5. **Eigenaktivität:** Keine festen „Geh zu X“-Ziele einbauen. Spontane Aktivität und innere Zustände benötigen trotzdem begründete Dynamik und Abgleich mit Verhaltensdaten.\n\n" +
          `Das maschinenlesbare Integrationspaket enthält **${integrationInputs.length} Eingaben** und **${integrationJoinCount} Regeln** für exakte und ausdrücklich nur angenommene Verknüpfungen. Das [webgpu-fly-Browserprojekt](https://github.com/abgnydn/webgpu-fly/tree/bb00419e874eee9e878542dcc5fce289ede2e1b9) verbindet öffentlich FlyWire, MANC, FlyBody, WebGPU und MuJoCo-WASM; seine [Grenzen](https://github.com/abgnydn/webgpu-fly/blob/bb00419e874eee9e878542dcc5fce289ede2e1b9/LIMITATIONS.md) umfassen Typnamen-Verknüpfungen über verschiedene Tiere sowie eigene Ganghilfen und Policies. Das ist eine Architektur-Referenz, keine Validierung unserer individuellen v783-Fliege. Die Tabellen liegen unter data/research_sources/, mit Prüfsummen und Original-URLs in den provenance.json-Dateien. Das Integrationspaket steht in analysis/model_integration_pack.json. Mikroskopbilder sind für diesen Datenabgleich nicht nötig.`
        } />
      </ReportSection>
      <DataComponent id="source-table" title="Lokale Daten und Quellenstand" queryId="source_inventory"
        kind="table" sourceRows={sources} displayRows={sources}
        description="Der Stand bezieht sich auf die lokal geprüften Original-, Morphologie- und ergänzenden Referenzdateien.">
        <DataTable rows={sources} columns={[
          { field: "name", label: "Quelle" }, { field: "kind", label: "Art" },
          { field: "artifact", label: "Datei / Material" }, { field: "state", label: "Lokaler Stand" },
        ]} caption="Stand der Forschungsquellen und lokalen Dateien" compactNumbers={false} />
      </DataComponent>
      <DataComponent id="download-table" title="Stand der fünf großen Originaldateien" queryId="download_pipeline"
        kind="table" sourceRows={downloads} displayRows={downloads}
        description="Momentaufnahme aus fertigen HTTP-Abschnitten. Eine volle .partial-Dateigröße zählt nicht als vollständig heruntergeladen oder geprüft.">
        <DataTable rows={downloads} columns={[
          { field: "name", label: "Datei" }, { field: "purpose", label: "Wofür" },
          { field: "state", label: "Stand" }, { field: "downloadedGB", label: "Geladen GB" },
          { field: "totalGB", label: "Gesamt GB" }, { field: "sharePercent", label: "Anteil %" },
        ]} caption="Verifizierter Downloadfortschritt beim letzten Berichtsaufbau"
          compactNumbers={false} searchable={false} />
      </DataComponent>
      <DataComponent id="integration-table" title={`${integrationInputs.length} geordnete Modelleingaben`} queryId="integration_inventory"
        kind="table" sourceRows={integrationInputs} displayRows={integrationInputs}
        description={`Lokale Dateien, Rolle, Quelladresse und Nutzungsstand; die ${integrationJoinCount} Join-Regeln stehen im maschinenlesbaren Integrationspaket.`}>
        <DataTable rows={integrationInputs} columns={integrationColumns}
          caption="Prüfbare Eingaben für Gehirn, Sensoren, Dynamik und Körper" compactNumbers={false} />
      </DataComponent>
      <ReportSection id="fly-limits" title="Offene Modellfragen" queryId="pathway_evidence"
        sourceRows={pathways} showHeading={false}>
        <RichNarrative id="fly:limits" label="Modellgrenzen bearbeiten" value={
          "### Was die Literatur derzeit nicht vollständig liefert\n\n" +
          "Aus der anatomischen Verbindungstabelle allein folgen keine individuellen Leitungs- und Synapsenparameter, keine vollständige Umrechnung von Licht, Berührung oder Geschmack in Spike-Züge, keine geschlossene Bauchmark- und Muskelmechanik und keine belastbare Theorie für eigenständige Motivation. Eon beschreibt eine verkörperte Kopplung, veröffentlicht in seinem fly-brain-Repository aber keine vollständige Tabelle aller Sensor- und Motorzuordnungen. Eine biologisch validierte Kopplung aller v783-Hirnneuronen an einen Körper liegt hier nicht vor. Für diese Lücken sind gezielte, offengelegte Modellannahmen und Tests an Verhaltensdaten nötig."
        } />
      </ReportSection>
    </section>}
  </article>;
}
