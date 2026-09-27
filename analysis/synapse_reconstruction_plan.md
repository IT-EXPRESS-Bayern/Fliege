# Prüfbarkeit zusätzlicher FAFB-v783-Verbindungen

Stand 26.09.2026. Ziel ist, veröffentlichte Kontaktpunkte auszuschöpfen und weitere Verbindungen als überprüfbare Kandidaten zu kennzeichnen. Der gemessene Originalgraph bleibt unverändert.

## Bereits quantitativ geprüft

- Die verifizierte FlyWire-Einzelpunkttabelle enthält **130.054.535** freigegebene Kontakte. Der veröffentlichte aggregierte Paargraph enthält **54.492.922** davon. [Der Vollscan](synapse_point_audit.json) findet zusätzlich **48 Kontakte mit zwei geprüften Partnern**, die im aggregierten Paargraphen fehlen.
- Die vier im Rohmaterial direkt klassifizierten Gruppen sind **54.492.970** Kontakte mit zwei geprüften Partnern, **67.421.243** nur mit geprüftem Sender, **3.608.754** nur mit geprüftem Empfänger und **4.531.568** ohne geprüften Partner. Sie summieren exakt auf 130.054.535. Die vorläufigen Differenzen aus den Summendateien waren um 48 verschoben, weil die Aggregattabelle diese Kontakte auslässt.
- Alle **48** Rohpunkt-Ausnahmen liegen im **ME_R** und betreffen das offiziell als proofread gelistete **R7-Neuron 720575940623940963**; sie bilden **21 gerichtete Neuronenpaare**. Im aggregierten Verbindungstableau gibt es null Zeilen mit dieser ID. Dies sind exakt beobachtete, zusätzliche Rohpunkt-Verbindungen, deren Ausschlussursache noch ungeklärt ist. Sie bleiben als separate Ausnahmeebene und werden nicht stillschweigend in den Originalgraphen geschrieben.
- Von **616** offiziellen Root-IDs ohne Kante im aggregierten Paargraphen haben **336** Kontakte in den Alle-Partner-Summendateien; **280** dort keine. Das ist in [synapse_coverage_audit.json](synapse_coverage_audit.json) und der [Neuronenliste](../data/research_sources/derived/proofread_synapse_coverage_by_neuron.csv) nachprüfbar.
- Für **552** dieser 616 IDs wurden bislang **nur Zielzelltypen** aus gleichartigen verbundenen Neuronen abgeleitet. Für visuelle Zellen wurde zusätzlich die publizierte v783-Typmatrix verlangt. Regeln und alle 2.821 Kandidatenzeilen: [missing_neuron_type_link_audit.json](missing_neuron_type_link_audit.json) und [Kandidaten-CSV](../data/research_sources/derived/missing_neuron_type_link_hypotheses.csv). Die Kohortenhäufigkeit ist keine kalibrierte Wahrscheinlichkeit für eine Einzelkante.

## Vollscan der 9,49-GB-Datei

[audit_synapse_points.py](audit_synapse_points.py) hat die vollständig geladene und vom Downloader per MD5 geprüfte Datei gelesen. Es kontrolliert die exakten vier Kontaktgruppen, die Cleft-Schwelle und die Koordinatenfelder. Für die 616 IDs exportiert es **7.385** vorhandene Kontakte samt Synapsen-ID, beiden Segment-IDs, Cleft-/Verbindungsscore, Neuropil sowie prä- und postsynaptischem Punkt in Nanometern. Die Ergebnisse liegen in [synapse_point_audit.json](synapse_point_audit.json) und der [Einzelpunkt-CSV](../data/research_sources/derived/points_for_616_ids_without_proofread_edges.csv). Davon haben **7.337** einen ungeprüften Partner und **48** zwei geprüfte Partner.

Der [Segment-Builder](build_observed_segment_links.py) hat diese Punkte abgeglichen. Die [beobachtete Segmentliste](../data/research_sources/derived/observed_segment_links_for_616.csv) fasst **7.337 Punkte zu 4.327 gerichteten Paar/Neuropil-Zeilen** mit **3.475 verschiedenen ungeprüften Segment-IDs** zusammen. Ein solches Segment wird nicht ohne weiteren Beleg einem bekannten Neuron zugeschlagen. Die [Rohpunkt-Ausnahmeliste](../data/research_sources/derived/observed_raw_proofread_edge_exceptions_for_616.csv) enthält die 48 beidseitig geprüften Kontakte als **21 gerichtete Paar/Neuropil-Zeilen**. [Die separate Prüfung](observed_raw_proofread_edge_exceptions_audit.json) hat alle **16.847.997** Zeilen der offiziellen Aggregattabelle gelesen und keinen dieser 21 Schlüssel darin gefunden. Beide Ebenen bleiben getrennt vom veröffentlichten CSR-Graphen.

Ein [vollständiger Roh-gegen-Aggregat-Abgleich](raw_published_edge_reconciliation_audit.json) hat danach alle **54.492.970** Rohkontakte mit zwei geprüften Partnern nach exaktem Sender, Empfänger und Neuropil gegen sämtliche offiziellen Aggregatzeilen verglichen. Zunächst gab es **6.407** unterschiedliche Schlüssel: **3.193** gerichtete Paare tragen im Rohfile wörtlich die Region `None`, im Aggregat `UNASGD`, jeweils mit exakt denselben **4.185** Kontakten. Nach dieser nur für den Vergleich verwendeten, empirisch belegten Regionsangleichung bleiben **genau die 21 R7-Paare und 48 Rohkontakte**. Es gibt dann keine weiteren Paar- oder Zählunterschiede. [Der unnormalisierte Vergleich](../data/research_sources/derived/raw_published_edge_count_exceptions.csv) und [die verbleibenden Ausnahmen](../data/research_sources/derived/raw_published_edge_exceptions_after_region_alignment.csv) bleiben getrennt nachvollziehbar; die Originaldateien wurden nicht verändert.

## Evidenzstufen für eine Modellergänzung

| Stufe | Aussage | Zulässiger Einsatz |
|---|---|---|
| A | Beide Partner proofread; Einzelkontakt und aggregierte Kante veröffentlicht | Gemessener FAFB-Graph |
| A-Roh | Beide Partner proofread; Einzelkontakt veröffentlicht, aber aggregierte Kante fehlt | Separat prüfbare Rohpunkt-Ausnahme, derzeit 48 Kontakte/21 Paare |
| B | Freigegebener Einzelkontakt; ein Partner nicht proofread | Separater Segmentgraph mit Kennzeichnung |
| C | Zelltyp-Hypothese aus homologen Neuronen und Fachmatrix | Such- und Priorisierungsliste, keine exakte Einzelkante |
| D | Räumliche Nähe von Skeletten oder anderes Tier/andere Version | Weitere Prüfung; nicht als gemessene Verbindung |

Für eine hochgestufte Zuordnung eines unproofread Segments zu einem geprüften Neuron braucht es unabhängig prüfbare Belege, etwa FlyWire-Proofreading, konsistente Morphologie im 3D-Skelett, Neuropil, Lateralisierung und/oder eine dokumentierte ID-Abbildung neuerer Releases. Zwei nahe Punkte allein genügen nicht.

## Biologische Grenze

Die freigegebene Einzelpunkttabelle enthält Kontakte oberhalb der veröffentlichten Cleft-Score-Schwelle 50. Das [Zenodo-Archiv](https://zenodo.org/records/10676866) sagt ausdrücklich, dass Punkte unterhalb dieser Schwelle dort nicht enthalten sind. [Dorkenwald et al.](https://doi.org/10.1038/s41586-024-07558-y) beschreiben falsch negative Synapsen als wichtigen Fehler. [Matsliah et al.](https://doi.org/10.1038/s41586-024-07981-1) warnen speziell vor stark untererkannten Photorezeptor-Ausgängen. Ohne verbesserte Synapsendetektion oder erneute Prüfung der Mikroskopdaten können wir deren **genaue fehlende Positionen nicht wissenschaftlich bestimmen**. Für die Simulation dürfen nur als solche deklarierte funktionelle Ersatzgewichte eingesetzt und gegen Messdaten geprüft werden.
