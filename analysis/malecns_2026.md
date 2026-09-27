# MaleCNS v1.0: zusammenhängendes männliches Gehirn und Bauchmark

Stand: 26. September 2026. **Für ein verkörpertes Fliegenmodell ist MaleCNS
v1.0 eine wichtige Ergänzung zu FAFB/FlyWire v783:** Hier stammen Gehirn,
beide Optiklappen, Halsverbindung und ventrales Nervensystem (VNC) aus
**demselben männlichen Tier**. Die Daten ersetzen FAFB v783 nicht: FAFB bildet
das Gehirn eines *anderen, weiblichen* Tiers ab. IDs dürfen zwischen den
Datensätzen nicht gleichgesetzt oder deren Synapsen einfach addiert werden.
Auch BANC ist ein eigenes weibliches Gehirn-plus-Bauchmark-Präparat.
Die Autorinnen und Autoren verbinden diese Atlanten über Zelltypen,
Morphologie und registrierte Räume, nicht über identische Einzelneuronen.
[Cell-Publikation](https://doi.org/10.1016/j.cell.2026.08.015),
[offizielles Projekt](https://male-cns.janelia.org/),
[Download-Seite](https://male-cns.janelia.org/download/),
[BANC-Publikation](https://doi.org/10.1038/s41586-026-10735-w).

## Versionen und Zählweisen

MaleCNS v1.0 wurde am **8. Juni 2026** freigegeben; die endgültige
Cell-Arbeit erschien am **3. September 2026**. Das finale Abstract nennt
**166.700 annotierte Neuronen und 11.710 Zelltypen**. Die bioRxiv-Vorversion
nennt 166.691 Neuronen und 11.691 Typen; diese älteren Zahlen dürfen nicht als
v1.0 ausgegeben werden. Das im Autoren-Repository noch vorhandene Notebook
`quantify-neuron-connections.ipynb` setzt sogar ausdrücklich `VERSION = 'v0.9'`.
Seine exakten Graphzahlen (25.563.426 Paare, 166.391 beteiligte Neuronen;
6.237.402 Paare mit ≥5 Kontakten) sind **v0.9**, nicht der hier neu berechnete
v1.0-Stand. [Freigaben](https://male-cns.janelia.org/release/),
[finales PubMed-Abstract](https://pubmed.ncbi.nlm.nih.gov/42691995/),
[Autoren-Notebook](https://github.com/flyconnectome/2025malecns/blob/main/supplemental_data/quantify-neuron-connections.ipynb).

Die vollständig heruntergeladene und per offizieller GCS-MD5 bestätigte
v1.0-Datei `connectome-weights-...-traced-only.feather` liefert bei
`minconf=0.5` folgende **direkt berechnete** Werte
([Audit-JSON](malecns_v1_reference_audit.json),
[Provenienz](../data/malecns_v1_reference/provenance.json)):

| Auswahl | Gerichtete Segment-/Neuronpaare | Eindeutige beteiligte IDs | Summe synaptischer Kontakte |
| --- | ---: | ---: | ---: |
| Sämtliche Zeilen der offiziellen `traced-only`-Tabelle | 25.563.197 | 164.587 | 124.025.046 |
| Beide Enden als Neuron (`superclass` belegt) annotiert | 25.558.671 | 164.403 | 124.009.893 |
| Sämtliche Zeilen, Gewicht ≥5 | 6.235.682 | 163.903 | 89.731.551 |
| Beide Enden Neuronen, Gewicht ≥5 | 6.234.901 | 163.803 | 89.722.750 |

Die Annotationstabelle hat 211.577 Körper-/Segment-IDs, davon **166.700 mit
`superclass`**. In der `traced-only`-Gewichtstabelle erscheinen 184 IDs ohne
Neuron-`superclass`; deshalb darf die erste Tabellenzeile nicht pauschal
„Neuron-zu-Neuron-Graph“ heißen. 2.297 der annotierten Neuronen haben in der
streng gefilterten Tabelle keine Paarzeile. Die offizielle ungekürzte
`connectome-weights-...feather` ist ein *anderes* Artefakt mit allen Segmenten;
ihre vollständigen Zahlen wurden hier noch nicht berechnet. Die Cell-Arbeit
nennt gerundet 25,6 Millionen Graphkanten. Eine Kante ist ein gerichtetes Paar
zweier IDs mit einem Gewicht aus mehreren Synapsen, keine einzelne Synapse.
[Offizielle Dateibeschreibung](https://male-cns.janelia.org/download/),
[Cell](https://doi.org/10.1016/j.cell.2026.08.015).

Die Autoren meldeten bereits in der Vorveröffentlichung ungefähr **46 Millionen
präsynaptische Stellen und 312 Millionen postsynaptische Dichten** im gesamten
Detektionsraum. Eine präsynaptische Stelle kann mehrere postsynaptische Partner
haben. Diese Gesamtzahl zählt auch Kontakte zu nicht rückverfolgten Segmenten;
sie ist daher nicht mit den **124.025.046** gewichteten Kontakten in der
`traced-only`-Tabelle gleichzusetzen. Die offiziell veröffentlichten
v1.0-ROI-Tabellen für Synapsenpräzision/-erfassung liegen lokal vor und erlauben
separate Unsicherheitsanalysen, etwa für zentrale Gehirnregionen, Optiklappen
und VNC. [Autorenvorversion, Methoden/Resultate](https://pmc.ncbi.nlm.nih.gov/articles/PMC12636603/),
[offizielle Supplemente](https://github.com/flyconnectome/2025malecns).

## Lokal geladene Dateien und ihre Funktion

Alle Originaldateien und die [GCS-/GitHub-Prüfsummen samt Version](../data/malecns_v1_reference/provenance.json)
liegen in `data/malecns_v1_reference/`. Der [Downloader](fetch_malecns_reference.py)
prüft sie beim erneuten Ausführen; das [Analyseprogramm](audit_malecns_reference.py)
erstellt die [reproduzierbaren Zahlen](malecns_v1_reference_audit.json).
Der abgeleitete [Neuronrollen-Index](../data/malecns_v1_reference/model_neuron_roles_v1.csv)
enthält **166.700** eindeutige neuronale IDs samt Typ, anatomischer Klasse,
Ein-/Austrittsnerv, Sensorrezeptor, Geschlechtsvergleich, FAFB-/MANC-Typname
und geschätztem Konsens-Transmitter. Er ist aus den Originaltabellen erzeugt,
kein neuer empirischer Befund.

| Datei | Größe, Rolle |
| --- | --- |
| `body-annotations-male-cns-v1.0-minconf-0.5.feather` | 14.483.314 Byte; Zellidentitäten, 166.700 neuronale `superclass`-Zeilen, Sensor-/Motor- und Typannotationen. |
| `body-neurotransmitters-male-cns-v1.0.feather` | 43.282.834 Byte; vorhergesagte bzw. kuratierte Transmitter pro Segment; Konsenswerte sind keine Messung der postsynaptischen Wirkung. |
| `connectome-weights-male-cns-v1.0-minconf-0.5-traced-only.feather` | 508.025.642 Byte; gerichtete Segmentpaare und Zahl der Kontakte, Modellgraph nach zusätzlichem Neuronenfilter. |
| `dnan_cluster_function_20260509.csv` | Autoren-Supplement zu ab- und aufsteigenden Neuronen: 3.201 Zeilen, 3.160 eindeutige IDs; nur 320 Zeilen haben ein nichtleeres Funktionsfeld. Für direkte ID-Joins zuerst Duplikate prüfen. |
| `mcns_fw_edge_comp_mappings.json` | Autoren-Zelltypzuordnung MaleCNS↔FlyWire für Vergleiche; sie ist **keine** Einzelneuron-ID-Identität. 562 von 616 FAFB-Neuronen ohne aggregierte Kanten im bestehenden Modell haben darin ein Typetikett, überwiegend R1–6. |
| `male-cns-v1.0-*-precision-recall-by-roi.csv`, `male-cns-v1.0-traced-synapse-capture-by-roi.csv` | 81 ROI-Werte für Detektorpräzision/-Recall je Synapsenart und 108 ROI-/Kompartimentwerte zur Proofreading-Abdeckung; Grundlage für regionalspezifische Unsicherheit. |
| `optic-column-type-assignments-v1.0.xlsx`, `sensory_network_traversal_model_layers.feather`, `mcns_lvl_6_hsbm_communities.feather` | Spalten der Sehbahn, Autoren-Traversierungs-Layer und Community-Zuordnung. Diese Modell-/Analyseprodukte sind keine gemessenen Aktivitätsverläufe. |
| `quantify-neuron-connections.ipynb` | Reproduktionsreferenz der Autoren, **aber auf v0.9 voreingestellt**. |

## Noch verfügbare offizielle Rohdaten ohne EM-Bilder

Der [v1.0-GCS-Katalog](https://male-cns.janelia.org/download/) bietet außerdem:

| Objekt | Offizielle Größe | Nutzen |
| --- | ---: | --- |
| Vollständige `connectome-weights-...feather` | 1.051.241.946 Byte | Alle Segmentpaare, besonders für Fehler-/Lückenanalyse; stärkere Filter nötig. |
| `body-stats-...feather` | 778.062.826 Byte | Ein-/Ausgangssummen und Segmentstatistik. |
| `syn-partners-...feather` | 6.777.179.098 Byte | Einzelne Prä-/Post-Partner samt Koordinaten; nötig für gezielte Rekonstruktionsprüfung. |
| `syn-points-...feather` | 13.061.489.098 Byte | Alle eindeutig gelisteten Prä-/Post-Orte; eine Prä-Stelle kann mehrere Partner haben. |
| `tbar-neurotransmitters-...feather` | 2.651.680.218 Byte | Wahrscheinlichkeiten pro präsynaptischer Stelle. |
| SWC-Skelettverzeichnis | Größe je Zelle | Räumliche Neuriten und Modellvisualisierung in MaleCNS-, gespiegeltem oder JRC2018-Raum. |

Die großen Dateien in dieser Tabelle sind **noch nicht lokal heruntergeladen**.
Das EM-Bildvolumen wird für die erste Körperkopplung nicht benötigt. Für
zusätzliche Synapsenprüfung können Partner- und Punktdatei später gezielt
verarbeitet werden. Für die MaleCNS-Daten weist das Projekt CC-BY aus;
Nutzungsrechte einzelner Codeartefakte aus dem Supplement-Repository sind
separat zu prüfen.

## Konsequenz für eine selbstständig handelnde 3D-Fliege

MaleCNS beseitigt einen großen anatomischen Bruch: Gehirn→absteigende Neuronen
→VNC→motorische Neuronen liegen in **einem** Datensatz. Im Rollenindex stehen
1.314 `descending_neuron`, 1.846 `ascending_neuron`, 708 `vnc_motor` und 107
`cb_motor`. Sensoren sind über `superclass`, `receptorType`, `entryNerve` sowie
Sinnesklassen auswählbar; Motoren über `exitNerve`, Typ, Neuromer und Anatomie.
Die Typebenen `flywireType`/`mancType` und der Autorenvergleich ermöglichen
Cross-Dataset-Vergleiche, aber keine verlustfreie Zellverschmelzung. Auch die
Autorinnen und Autoren weisen darauf hin, dass kleine Teile der Sinnes- und
Motorperipherie wegen Bild-/Segmentierungsgrenzen fehlen können.
[Cell/Autorenmanuskript](https://pmc.ncbi.nlm.nih.gov/articles/PMC12636603/),
[finales Abstract](https://pubmed.ncbi.nlm.nih.gov/42691995/).

**Ohne von uns gesetztes Verhaltensziel** kann ein Modell spontane Aktivität,
Körpersensorik, Eigenbewegung, innere Zustände und Rückkopplung nutzen, sodass
Handlungen aus dem laufenden System entstehen. Das veröffentlichte Konnektom
liefert dafür strukturelle Kontakte und teils Transmittervorhersagen; es liefert
keine gemessenen Zellzeitkonstanten, alle Synapsenvorzeichen/-stärken,
neuromodulatorischen Zustände, Muskelphysik oder vollständige Sinneswelt.
Diese Dynamik und die Körperkopplung müssen als **explizite Modellannahmen**
implementiert und gegen Verhalten/Physiologie getestet werden. Ein bewegter
Körper mit MaleCNS-Gewichten allein wäre noch keine nachgewiesene Reanimation
einer Fruchtfliege. Die Cell-Autorinnen und -Autoren betonen ebenfalls, dass
funktionelle Experimente zur Bestätigung vorhergesagter Informationsflüsse
nötig sind. [Methodische Einschränkung der Autoren](https://pmc.ncbi.nlm.nih.gov/articles/PMC12636603/).

## Vergleich der 616 FAFB-Zellen ohne publizierte Aggregatkante

Der [reproduzierbare Projektionscode](project_malecns_type_partners.py) nutzt
das [veröffentlichte MaleCNS↔FlyWire-Typmapping](https://github.com/flyconnectome/2025malecns)
und die geprüfte v1.0-Verbindungstabelle. Er nimmt für jede FAFB-v783-ID
das **Zelltyp-Etikett** aus dem Autorenmapping, sucht **gleichseitige**
MaleCNS-Neuronen mit demselben Etikett und zählt deren **beobachtete
MaleCNS-Partner-Typen** getrennt nach Eingangs-/Ausgangsrichtung und
Partnerseite. Für sensorische MaleCNS-Axone gilt `rootSide`, sonst die
bekannte `somaSide`. Die
[vollständige Gruppentabelle](../data/research_sources/derived/malecns_observed_partner_type_groups.csv)
enthält 5.078 beobachtete Typ×Seite×Richtung-Gruppen. Die
[priorisierte CSV für FAFB-IDs](../data/research_sources/derived/malecns_type_partner_hypotheses_for_616.csv)
enthält je Typ-/Seitenkohorte höchstens zehn Partnertypen pro Richtung,
geordnet nach dem Anteil männlicher Exemplare mit diesem Partner und danach
nach Kontaktzahl. Die
[Abdeckungstabelle](../data/research_sources/derived/malecns_type_mapping_coverage_for_616.csv)
enthält **alle 616** FAFB-IDs, auch die nicht zuordenbaren. Im
[Audit](malecns_type_partner_hypotheses_audit.json) stehen Eingabe- und
Ausgabeprüfsummen, Zählweisen und Grenzen.

| FAFB-v783-Gruppe | IDs ohne Aggregatkante | Gleichseitiger MaleCNS-Typmatch | FAFB-Homologhypothese | Mindestens eine **exakte Typnamen**-Übereinstimmung unter MaleCNS-Topkandidaten | IDs mit FAFB-Rohpunkten |
| --- | ---: | ---: | ---: | ---: | ---: |
| R1–6-Photorezeptoren | 520 | 520 | 520 | 520 | 293 |
| Alle übrigen Typen | 96 | 42 | 32 | 27 | 43 |
| Gesamt | 616 | 562 | 552 | 547 | 336 |

Die hohe Gesamtquote ist fast ganz durch **R1–6** bedingt. Unter den übrigen
96 fehlen für 54 Zellen Autoren-Typmatches; 48 davon besitzen schon in der
FAFB-Ausgangsliste keinen Zelltyp. Das Modell verwendet 7.282 männliche
Neuronen in 21 Typ×Seite-Kohorten. Viele FAFB-IDs teilen dieselbe männliche
Kohorte: 553 der 562 gematchten IDs haben weitere FAFB-IDs mit gleichem Typ
und gleicher Seite. Ihre priorisierten Zeilen sind daher **keine
individualisierten Kantenprognosen**. Bei 16 IDs (R7/R8) umfasst das gemeinsame
Cross-Typ-Etikett mehrere männliche Untertypen. Partnertypen mit mehrdeutigem
Komma-Etikett oder reinem MaleCNS-Typnamen werden nicht als exakte
FAFB-Typ-Übereinstimmung gezählt.

Beispiel: Für die fehlende linke R1–6-Zelle `720575940605634220` stehen im
MaleCNS bei gleichseitigen R1–6-Neuronen L2, L1 und L3 oben; diese Typen
waren auch in den bereits bestehenden FAFB-Homologhypothesen enthalten. Das
ist eine **Querprüfung auf Zelltyp-Ebene** über andere Exemplare. Wegen
retinaler Spaltenlage, Photorezeptor-Untertypen und individueller Variabilität
wird daraus kein konkreter FAFB-Ziel-Root bestimmt. Die Prävalenz ist ein
Anteil beobachteter männlicher Exemplare, keine kalibrierte
Wahrscheinlichkeit einer fehlenden FAFB-Synapse.

### R7: beobachtete FAFB-Rohkontakte und MaleCNS-Typmuster getrennt

Die FAFB-R7-Zelle `720575940623940963` ist der einzige der 616 Fälle mit
publizierten Rohkontakten, bei denen **beide** FAFB-Partner offiziell
geprüfte Roots sind und die in
der aggregierten FAFB-v783-Verbindungstabelle fehlen: **48 automatische
Kontaktaufrufe in 21 gerichteten Paaren**. Die exakten FAFB-IDs, Synapsen-IDs,
Region `ME_R` und Scores bleiben ausschließlich in der
[FAFB-Roh-Ausnahmeliste](../data/research_sources/derived/observed_raw_proofread_edge_exceptions_for_616.csv).
Die davon getrennten, beobachteten MaleCNS-Typkanten bleiben in der
[MaleCNS-Gruppentabelle](../data/research_sources/derived/malecns_observed_partner_type_groups.csv).
Der [R7-Typvergleich](../data/research_sources/derived/malecns_r7_raw_type_crosscheck.csv)
zeigt nur Bezeichnungsübereinstimmungen zwischen beiden Listen:

| FAFB-R7-Rohaufrufe | FAFB-Kontakte | MaleCNS-R7-rechts-Typmuster | Interpretation |
| --- | ---: | --- | --- |
| Dm9 → R7 | 14 | Dm9 Eingang, Rang 1 | Gleicher Typname, anderes Tier. |
| R7 → Dm9 | 7 | Dm9 Ausgang, Rang 1 | Gleicher Typname, anderes Tier. |
| R7 → Dm8 | 8 | `pDm8` und `yDm8`, Ränge 7/4 | Nur Dm8-Familie; FAFB-Rohpartner ohne p/y-Untertyp. |
| R7 → Tm20 | 4 | Tm20 Ausgang, Rang 16 | Typname in vollständiger MaleCNS-Liste; außerhalb Top 10. |
| R7 → L3 / Dm2 | 2 / 1 | L3 / Dm2 Ausgang, Ränge 2 / 5 | Gleiche Typnamen. |

Die R7-Tabelle lässt weitere Rohpartnertypen sichtbar, auch wenn im
MaleCNS-Typgraph kein passender Name steht. **Weder diese Typ-Querprüfung noch
die 7.385 veröffentlichten FAFB-Rohpunkte für die 616 Zellen ändern den
offiziellen FAFB-Verbindungsgraphen.** Die 7.337 Punkte zu ungeprüften
Segmenten ergeben insbesondere keine gesicherten Zielneuronen. Für eine
Rekonstruktion einzelner FAFB-Verbindungen braucht es zusätzliche
Bild-/Segmentprüfung und unabhängige Validierung.
