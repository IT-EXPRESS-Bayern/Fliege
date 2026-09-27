# Vollhirnvergleich FAFB v783: Originalexport 783.0 und Princeton 2025

Stand: 27. September 2026. Diese Auswertung betrifft **den gesamten veröffentlichten, korrekturgelesenen FAFB-v783-Graphen**. Sie ergänzt die [Fallanalyse der 616 zuvor kantenlosen IDs](../reconstruction_candidates_v783/METHODEN_UND_ERGEBNISSE.md). Alle hier genannten Kontakte sind automatische Bildauswertungen. Der zweite Detektor liefert weitere Beobachtungen desselben Präparats; er beweist damit weder eine neue biologische Verbindung noch eine Aktivierung des Gehirns.

## Quellen und Vergleichseinheit

1. [FlyWire Whole-brain Connectome Connectivity Data, Version 783.0](https://zenodo.org/records/10676866), veröffentlicht 2024: `proofread_connections_783.feather`, je gerichtetes Neuronpaar und Neuropil eine Zeile, sofern mindestens ein Synapsenkandidat vorliegt. Die Datei enthält die geprüften FAFB-v783-Root-IDs und Synapsen des älteren Buhmann-Detektors. Die Originaldatei bleibt unverändert.
2. Offizieller [Codex-Princeton-2025-Export](https://codex.flywire.ai/faq): `connections_princeton_no_threshold.csv.gz`, gleicher FAFB-v783-Root-ID-Raum, anderer Synapsendetektor. [fafbseg](https://natverse.org/fafbseg/reference/flywire_connectome_data.html) bezeichnet den Princeton-Synapsenrelease als `783.2`. Die verwendete Codex-GCS-Datei wurde am 8. Juli 2025 aktualisiert; Download, GCS-MD5 und lokaler SHA-256 stehen in `data/codex_fafb_v783/princeton_provenance.json` und `audit.json`.
3. Offizielle `proofread_root_ids_783.npy` sowie FlyWire-Neuronenannotation v2.1.0 liefern ID-Kontrolle und Zelltypen. Die Zelltypen sind Kontext für die Priorisierung, keine zusätzliche Synapsenmessung.

Vergleichsschlüssel sind `(pre_root_id, post_root_id, neuropil)` und separat das über Neuropile summierte **gerichtete** Paar `(pre_root_id, post_root_id)`. Wir prüfen zuerst exakte numerische Root-IDs gegen die offizielle ID-Liste. Alle 79 vorkommenden Neuropil-Labels sind in beiden Verbindungstabellen gleich. Für denkbare leere/`None`-Labels sieht der Code eine rein technische Zuordnung zu `UNASGD` vor; sie veränderte in diesen beiden aggregierten Dateien keinen einzigen Quellschlüssel. Ein Synapsen- oder Kontaktwert aus zwei Detektoren wird **niemals addiert**.

Die Programme `compare_all.py`, `summarize_deltas.py` und `enrich_priority.py` verwenden Arrow-Streaming bzw. DuckDB mit 2-GB-Speichergrenze und Parquet-Zwischendateien. `audit.json` enthält Quell- und Ausgabefingerabdrücke sowie Kontrollgleichungen. Das Original, die Punktdateien und die laufende Fliegensimulation werden nicht überschrieben.

## Vollständige Zählung

| Einheit | Buhmann/Original 783.0 | Princeton 2025 |
|---|---:|---:|
| Paar × Neuropil | 16.847.997 | 22.285.323 |
| Gerichtete Neuronpaare | 15.091.983 | 19.773.733 |
| Automatisch gezählte Synapsen dieser Paar×Region-Dateien | 54.492.922 | 76.944.499 |

Alle 139.255 IDs der Annotations-/Root-Liste sind für die Prüfung verfügbar. Das Original enthält Kanten für 138.639 Roots; 616 hatten dort keine aggregierte Kante. In keiner der beiden aggregierten Paar-Dateien sind Autapsen (`pre_root_id == post_root_id`). Die größere Princeton-Kontaktzahl ist **ein Detektorunterschied**, keine gemessene biologische Zunahme.

| Klassifikation gerichteter Paare | Anzahl | Buhmann-Kontakte | Princeton-Kontakte |
|---|---:|---:|---:|
| In beiden, gleiche Kontaktzahl | 6.185.805 | 11.641.373 | 11.641.373 |
| In beiden, andere Kontaktzahl | 7.261.730 | 41.091.020 | 57.078.597 |
| Nur im Original | 1.644.448 | 1.760.529 | 0 |
| Nur im Princeton-Export | 6.326.198 | 0 | 8.224.529 |

Die Zahl gemeinsamer gerichteter Paare ist 13.447.535. Bei diesen meldet Princeton für 5.986.940 Paare mehr, für 1.274.790 weniger und für 6.185.805 die gleiche Kontaktzahl. Auch ein gemeinsames Paar kann neue oder weggefallene **Regionsschlüssel** haben: 755.099 Paar×Neuropil-Schlüssel erscheinen nur bei Princeton, obwohl das Paar selbst in beiden Dateien vorkommt; 204.865 sind umgekehrt nur im Original. Die vollständige Kreuztabelle steht in `region_pair_class_crosswalk.csv`. Ein Plus auf Paar×Neuropil-Ebene ist daher nicht automatisch ein neues Neuronpaar.

## Wissenschaftlich sinnvolle Prüfmenge

Von den 6.326.198 Princeton-exklusiven gerichteten Paaren verbinden **6.323.027** zwei Roots, die **jeweils irgendeine Verbindung im Originalgraphen** besitzen. Das bedeutet ausdrücklich **nicht**, dass diese beiden Roots dort bereits miteinander verbunden waren; dann wäre das Paar nicht Princeton-exklusiv. Die anderen 3.171 Paare berühren die 616 ursprünglichen Null-Kanten-Roots und sind in der separaten 616-Auswertung punktbasiert untersucht.

| Princeton-Kontakte pro neuem Paar zwischen zuvor anderweitig verbundenen Roots | Paare |
|---|---:|
| 1 | 5.207.559 |
| 2–4 | 1.051.614 |
| 5–9 | 49.012 |
| 10–19 | 10.043 |
| 20–49 | 4.188 |
| 50–99 | 602 |
| ≥100 | 9 |

Damit haben 82,4 % der Princeton-exklusiven Paare in diesem Teil des Graphen nur **einen** automatisch erkannten Kontakt. Die praktische Prüfreihenfolge beginnt bei den 63.854 Paaren mit mindestens fünf Princeton-Kontakten, darunter 14.842 mit mindestens zehn und 4.799 mit mindestens zwanzig. Die Grenze dient nur der Arbeitspriorisierung; schwache Paare werden im vollständigen Delta nicht gelöscht. Im Gegenzug haben nur 437 der 1.644.448 Original-exklusiven Paare mindestens fünf Originalkontakte. Das ist kein Beweis, welcher Detektor für ein Einzelpaar korrekt liegt.

Die häufigsten Neuropile für Princeton-exklusive Paare zwischen anderweitig verbundenen Roots sind `ME_L` (893.571 Paar×Region-Einträge), `ME_R` (829.908), `LO_L` (432.849), `LO_R` (418.512) und `GNG` (322.781). Nach Paaren mit mindestens zehn Gesamt-Princeton-Kontakten treten unter anderem `LA_R` (3.256 Paar×Region-Einträge), `SAD` (3.139), `ME_L` (2.425) und `ME_R` (2.322) hervor. Diese Regionenzahlen sind **Paar×Region-Einträge**, nicht eindeutige Paare, und dürfen nicht über Regionen als neuronale Paarzahl interpretiert werden.

Die annotierten `super_class`-Flüsse zeigen viele schwache `central→central` (2.289.666 Paare) und `optic→optic` (2.081.173). Bei mindestens zwanzig Princeton-Kontakten sind `sensory→optic` (3.319), `sensory→central` (733) und `optic→optic` (126) auffällig. Die Zelltyp-Übersicht nennt beispielsweise `R1-6→L2`, `R1-6→L1`, `R7→Dm8` und `R8→Mi4` als wiederholt beobachtete Princeton-exklusive Typkombinationen. Das ist besonders relevant für die zuvor bekannten Lücken in visuellen Zuflüssen, aber noch keine Prüfung jedes einzelnen synaptischen Punktes.

Die 50.000 kontaktstärksten Kandidaten sind mit Zelltyp, Klasse, Seite und Neuropil exportiert. Für 35.582 davon kommt dieselbe gerichtete **Zelltyp-Paar-Kombination** irgendwo im Originalgraphen vor. Dies stützt anatomische Plausibilität auf Typ-Ebene; sie ist keine unabhängige Bestätigung des konkreten Root-ID-Paares. 862 weitere Kandidaten haben zwei bekannte Zelltypen ohne alte Typ-Paar-Rekurrenz; bei 13.556 fehlt mindestens ein Zelltyp.

## Dateien für die Weiterarbeit

| Datei im Ordner `analysis/whole_brain_detector_comparison/` | Zweck |
|---|---|
| `audit.json`, `breakdown_audit.json`, `priority_enrichment_audit.json` | Quellfingerabdrücke, Zählungen, Prüfergebnisse, Ausgabegrößen |
| `full_pair_region_delta.parquet` | Alle 24.144.445 Paar×Neuropil-Schlüssel; getrennte Original-/Princeton-Zählung und Status |
| `full_directed_pair_delta.parquet` | Alle 21.418.181 gerichteten Paare; getrennte Zählung und Status |
| `all_new_princeton_pairs_between_old_connected_roots.parquet` | Alle 6.323.027 Princeton-exklusiven Paare, bei denen beide Roots bereits je andere alte Kanten hatten |
| `top_50000_new_pairs_with_type_recurrence.csv` | Kontaktstärkste Prüfliste mit Zelltyp, Region und Typ-Paar-Rekurrenz |
| `original_only_pairs_ge5_review.csv` | 437 stärkere Gegenbeispiele, die nur der alte Detektor meldet |
| `region_change_summary.csv`, `region_pair_class_crosswalk.csv`, `new_pairs_existing_roots_by_region.csv` | Regionale Differenzen, sauber zwischen Paar- und Regionsebene getrennt |
| `pair_strength_distribution.csv`, `shared_pair_count_direction.csv`, `new_pairs_existing_roots_strength.csv` | Kontaktstärken und Richtung von Zählabweichungen |
| `new_pairs_existing_roots_super_class_flow.csv`, `new_pairs_existing_roots_cell_class_flow.csv`, `top_1000_new_pair_cell_type_flows.csv` | Funktionelle Klassen und Zelltyp-Kombinationen zur Prüfplanung |
| `compare_all.py`, `summarize_deltas.py`, `enrich_priority.py` | Reproduzierbare Extraktion, Vollabgleich und Aufbereitung |

Für das Fliegenmodell sollten Originalgraph und Princeton-Kandidaten getrennte, umschaltbare Datenebenen bleiben. Jeder Kandidat braucht `pre_root_id`, `post_root_id`, `neuropil`, `detector_release`, detector-eigene `synapse_count` und `verification_status=automatic_candidate`. Eine mechanische Vereinigungsmenge würde widersprüchliche Punktmeldungen als gesicherte Biologie ausgeben. Vor einer dauerhaften Kantenübernahme sollten priorisierte Paare anhand der Princeton-Einzelpunkte, der alten Buhmann-Punkte, der v783-Morphologie und gegebenenfalls direkt an den EM-Bildern geprüft werden. Die Modellaktivität erfordert zusätzlich physiologische Parameter, sensorische Eingangssignale und Körper-/Umweltkopplung; eine reine Verdrahtungsliste liefert diese nicht.
