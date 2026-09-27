# Neuronenkatalog: Namen, Rollen und Herkunft

Stand: 27. September 2026. Der Katalog enthält **genau die 139.255 ursprünglichen proofread Roots von FAFB/FlyWire v783**. Jede ID bleibt eine Dezimalzeichenkette. Eine Zeile ist ein Neuron; die zusätzliche Evidenztabelle hat eine Zeile je Quellenbehauptung.

## Was jetzt zugeordnet ist

| Befund | Anzahl | Bedeutung |
|---|---:|---|
| Ursprüngliche v783-Neuronen | 139.255 | Vollständig und ohne doppelte Root-ID enthalten |
| Name oder Typ in den Originalfeldern | 131.811 | `cell_type` oder `hemibrain_type` vorhanden |
| Mit Originalen und publizierten Ergänzungen benennbar | 138.765 | Ein Name/Typ ist keine vollständige Verhaltensbeschreibung |
| Weiterhin unbenannt | 490 | Bleiben ausdrücklich `unbenannt` |
| Mit publizierter kuratierter Funktionsannotation | 22.312 | Beispielsweise visuelle, chemische oder mechanosensorische Modalität bzw. anatomischer Motorzweck |
| Ohne solche Funktionsannotation im zusammengeführten Katalog | 116.943 | Nicht automatisch ohne biologische Funktion; die Funktion ist hier unbestimmt |
| Mit ergänzender Quellenevidenz | 61.421 | Namen, Anatomie, kuratierte Rollen und getrennte Übertragungshypothesen |
| Quellenbehauptungen | 72.040 | Davon vier Shiu-v630-IDs ohne exakten v783-Match |

Die Namen werden aus der ursprünglichen Annotation bevorzugt. Zusätzliche Namen stehen in `published_names`; die harmonisierte FAFB-Tabelle von 2026 bleibt in den separaten `harmonized_*`-Feldern erhalten. Kein Originalfeld wird überschrieben.

## Die Evidenzstufen

| Kennung | Was sie trägt | Was daraus nicht folgt |
|---|---|---|
| Originalannotation v2.1.0 | Zelltyp, Klasse, Seite, Nerv, vorhergesagter und bekannter Transmitter in getrennten Feldern | Ein Zellname allein misst kein Verhalten |
| `published_anatomical_identity` | Exakte Root-ID, publizierter Name, anatomische Richtung oder Zielstruktur | Eine DN-Verbindung liefert noch keine kalibrierte Muskelsteuerung |
| `published_curated_function_annotation` | Publizierte, kuratierte Funktionsangabe für die gleiche FAFB-Root-ID | Keine neue physiologische Messung an dieser einzelnen rekonstruierten Zelle |
| `published_experiment_type_transfer` | Experiment an einem Zelltyp in anderen Fliegen, verknüpft mit der FAFB-Typidentität | Keine Messung am FAFB-Präparat und keine Bestätigung unseres Simulators |
| `published_model_cross_release_candidate` | Shiu-v630-Tabellenrolle mit exakter ID-Verfügbarkeit in v783 | Die v630-Feuerraten gelten nicht automatisch für v783 |
| `type_level_transfer_hypothesis` | Rezeptor- oder Peptidwissen nach Typ-/Glomerulusabgleich | Keine in diesem Root gemessene Rezeptor- oder Peptidausstattung |
| `model_role = unassigned` | Der Katalog vergibt keine automatische Steuerrolle im laufenden Körpermodell | Die separat gemessenen Assay-Reaktionen sind dadurch nicht verworfen |

`top_nt` und `top_nt_conf` sind Vorhersagen aus der Originalannotation. `known_nt` ist ein anderes Quellenfeld. Ein Transmitter wird hier nicht automatisch in ein universelles erregendes oder hemmendes Wirkzeichen umgerechnet.

## Direkte Testgruppen

`assay_sets.json` enthält die vollständigen IDs und Quellen. Nur vorhandene v783-IDs werden ausgewählt:

| Eingangsgruppe | IDs | Geeignete Auslese |
|---|---:|---|
| Shiu Zucker-GRNs | 20 | MN9 rechts und links |
| Shiu Wasser-GRNs | 18 | MN9 rechts und links |
| Shiu Bitter-GRNs | 20 | MN9; gleicher Versuchsaufbau als Vergleich |
| Johnston-Organ C/E | 69 | aBN1, aDN1, aDN2 |
| Johnston-Organ F | 60 | Dieselben Auslesen zur Prüfung von Selektivität |
| Johnston-Organ insgesamt | 145 | Dieselben Auslesen |

**Neu unabhängig identifiziert:** Tastekin et al. Tabelle S1, Blatt `MNs`, Zeilen 68 und 69 benennt `MN9` rechts als `720575940660219265` und links als `720575940618238523`, jeweils Zielmuskel 9 / Nerv PhN. Die fehlende linke Shiu-v630-ID `720575940645521262` wurde nicht durch Namensraten ersetzt. Die aktuelle linke ID stammt aus einer eigenen v783-Quelle. [Tastekin et al. 2026](https://doi.org/10.1016/j.cell.2026.08.016)

DNa02 und DNg13 sind über Stürner exakt benannt. Ihre unterschiedlichen Beiträge zur Schrittgeometrie während des Lenkens sind experimentell auf Zelltypebene beschrieben. Die Übertragung auf unsere Modellbewegung bleibt eine getrennte Modellannahme. [Cheong et al. 2024](https://doi.org/10.1016/j.cell.2024.08.033)

## Seitenkonventionen

Bei 1.301 von 1.316 DN-Zeilen unterscheiden sich die Stürner-L/R-Beschriftungen von der ursprünglichen v2.1.0-Seite. Das betrifft auch beide DNa02 und beide DNg13. Der separate vollständige Seitenaudit bestätigt für diese vier Neuronen die Übereinstimmung zwischen v2.1.0 und der harmonisierten FAFB-Annotation von 2026.

Codex dokumentiert eine historische Links/Rechts-Inversion und eine spätere Korrektur der Annotationsbeschriftungen; die Bilddaten wurden dabei nicht entsprechend umgeschrieben. Quellenseite, aktuelle Annotationsseite, Somaseite und Projektionsseite dürfen daher nicht pauschal gleichgesetzt werden. Eine globale automatische Seitenumkehr wird hier nicht vorgenommen. [Offizielle Codex-FAQ](https://codex.flywire.ai/faq)

Die Prüfliste `side_conflicts.csv` zählt unterschiedliche Quellenbehauptungen, nicht unabhängige biologische Fehler. Sie enthält 1.325 Zeilen für 1.317 verschiedene Roots. Der vollständige systematische Abgleich liegt in `analysis/neuron_pathways/side_convention_audit.json` und `global_side_discrepancies.csv`.

## Gemessene Modellantworten

`named_model_responses.csv` / `.parquet` verbindet **7.048 Neuronen** aus sechs tatsächlich ausgeführten Referenzbedingungen exakt mit dem Katalog. Bei **6.845** wurde in mindestens einer Bedingung Aktivität gezählt, die nicht unmittelbar als Eingangsspike vorgegeben war. **17** der antwortenden Neuronen sind weiterhin unbenannt; **6.767** besitzen in diesem Katalog keine publizierte kuratierte Funktionsrolle.

Diese Datei beschreibt Antworten des festgelegten Rechenmodells. Die Spalten `*_non_forced_spikes` sind Gesamtsignale minus aufgezwungene Eingangsspikes im jeweiligen 600-ms-Fenster, keine Baseline-bereinigten biologischen Messungen. Die stärkste Testbedingung benennt ein Reaktionsprofil dieses Protokolls; sie wird nicht zum neuen biologischen Funktionsnamen. Die vollständigen Eingriffs- und Vergleichstests liegen separat unter `analysis/neuron_assays/`.

## Dateien und Wiederholung

| Datei | Einsatz |
|---|---|
| `catalog_139255.parquet` / `.csv` | Vollständiger Neuronenkatalog einschließlich aller Original- und harmonisierten Felder |
| `source_claims.parquet` / `.csv` | Jede zusätzliche Behauptung mit Quelle, Tabellenzeile, Evidenzart und Zusatzdetails |
| `unmatched_source_claims.csv` | Vier ausgeschlossene v630-IDs, ohne stillschweigende Ersetzung |
| `side_conflicts.csv` | Unterschiedliche Seitenangaben auf Ebene der Quellenbehauptungen |
| `assay_sets.json` | Exakte Sensor-/Auslesegruppen für reproduzierbare Versuche |
| `named_model_responses.*` | Getrennter Join der tatsächlich simulierten Antworten auf Namen und Quellenrollen |
| `audit.json` | Zählungen, Join-Abdeckung, Eingabedateien mit SHA-256 und Ergebnisfingerabdrücke |
| `validation.json` | Zehn unabhängige Prüfungen der exportierten Daten |
| `catalog_audit.ipynb` | Ausführbarer Einstieg in Zählungen, Quellen und Modellantworten |
| `app/data/neuron_catalog.json` | Browser-Suchindex; `columns` plus `rows`, Root-IDs als Strings |
| `app/data/neuron_catalog_claims.json` | Nachladbare Evidenzdetails, referenziert durch `claims_url` |

Aus dem Projektordner:

```powershell
& analysis/.venv/Scripts/python.exe analysis/neuron_catalog/build.py
& analysis/.venv/Scripts/python.exe analysis/neuron_catalog/validate.py
& analysis/.venv/Scripts/python.exe analysis/neuron_catalog/join_model_responses.py
```

Die Validierung verglich **3.759.885 Originalfeldwerte**, alle 139.255 Root-IDs und sämtliche **72.036 Browser-Evidenzverweise**. Originalfelder, Transmittersemantik und ID-Schreibweise blieben erhalten; alle zehn Exportprüfungen bestanden.

## Quellen und Abgrenzung

- [FlyWire-Annotation v2.1.0](https://github.com/flyconnectome/flywire_annotations/releases/tag/v2.1.0): gepinnte Ausgangsnamen und Originalfelder.
- [BANC-Publikation 2026](https://doi.org/10.1038/s41586-026-10735-w), Supplementary Data 3: harmonisierte **FAFB**-Metadaten mit Schlüssel `root_783`. 139.249 unserer Roots passen exakt; sechs fehlen dort und bleiben erhalten. 928 zusätzliche Quell-IDs liegen außerhalb unseres festgelegten Originaluniversums und werden nicht als neue Katalogneuronen angehängt. Diese Tabelle enthält keine importierten BANC-Synapsen.
- [Stürner et al.](https://doi.org/10.1038/s41586-025-08925-z): 1.316 DN- und 2.345 AN/SA-Identitäten.
- [Calle-Schuler et al.](https://doi.org/10.7554/eLife.108044.3): 705 Borsten-Mechanosensoren.
- [Shiu et al.](https://doi.org/10.1038/s41586-024-07763-9): 229 ausgewählte Tabellenrollen, davon 225 exakt verfügbar; Versuchsreferenzen stammen aus v630.
- [Benton et al.](https://doi.org/10.1038/s44319-025-00476-8) und [DoOR](https://doi.org/10.1038/srep21841): Glomerulus-/Rezeptorwissen als explizite Übertragungshypothesen, einschließlich unklarer Zuordnungen.
- [Gepinnte Neuropeptid-Kuration](https://github.com/flyconnectome/drosophila_neuropeptides/tree/8df0b4506d28646ce6e77947515ba03246f5275d): Peptid-Hypothesen nach Typgleichheit; Methoden und Quellennachweise stehen je Behauptung in `details_json`.

Die Datenerstellung änderte weder den ursprünglichen Verbindungsgrafen noch die Dynamik des Hirnmodells.
