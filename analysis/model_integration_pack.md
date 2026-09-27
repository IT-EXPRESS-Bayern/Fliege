# Integrationspaket für die virtuelle Fruchtfliege

Stand 27. September 2026. Die maschinenlesbaren Regeln stehen in [model_integration_pack.json](model_integration_pack.json); der idempotente Aktualisierungslauf ist [update_model_integration_pack.py](update_model_integration_pack.py). Quellen, Prüfsummen und Abrufversionen liegen in den jeweiligen `provenance.json`-Dateien, auch unter `data/codex_fafb_v783/`, `data/malecns_v1_reference/` und `data/research_sources/other/banc_2026/`. Die Prüfung des ursprünglichen FAFB-Graphen steht in [research_data_audit.json](research_data_audit.json).

Ein vollständiger [Kantenvergleich](model_original_edge_comparison.json) hat alle 15.091.983 gerichteten Shiu-v783-Paare gegen den aus den originalen FlyWire-Dateien gebauten Graphen geprüft: gleiche Paarmenge und null Abweichungen bei der Synapsenzahl. Vorzeichen und neuronale Dynamik sind weiterhin Modellannahmen.

Der zusätzliche [Vollhirn-Vergleich](whole_brain_detector_comparison/METHODEN_UND_ERGEBNISSE.md) erfasst sämtliche Paare des Original- und Princeton-Detektors: 13.447.535 gemeinsame Paare, 6.326.198 nur bei Princeton und 1.644.448 nur im Original. Die vollständigen Delta-Parquets, alle neuen Paare zwischen zuvor bereits verbundenen Roots und 50.000 priorisierte Prüfkandidaten stehen jetzt als eigene Eingaben im Manifest. Zählungen bleiben nach Detektor getrennt.

Die [Körperschnittstelle](body_neural_interface/README.md) ergänzt 391 proofread BANC-Bein-Motorneuronen sowie ihre vollständigen Eingangs-Paare in v2 und v3. Der neue gegliederte Browserkörper liefert Gelenkwinkel, Winkelgeschwindigkeiten und Bodenkontakte. Die belegte Bein-/Seitenzuordnung und die vorgeschlagenen Gelenkkanäle sind maschinenlesbar, aber es gibt noch keine kalibrierten Aktuatorkräfte oder eine direkte FAFB-Ansteuerung.

Der neue [Motoratlas](motor_output_atlas/README.md), die [strukturellen Motorpfade](motor_pathways/README.md) und der [direkte Gelenkaudit](../app/data/motor_joint_audit.json) sind als eigenständige Eingaben und Regeln registriert. Das Manifest enthält jetzt **160 Inputs und 46 Joins**. 805 BANC-Motor-IDs bleiben im BANC-Namensraum; 391 davon versorgen Beine. Für 92 ausgewählte DNs liegen 1.618 direkte und 448.942 Zwei-Kanten-Wege vor. Die zusätzliche Drei-Kanten-Auswertung betrifft ausschließlich vier DNa02/DNg13-Zellen; die Browserauswahl von 1.739 Beispielen ist keine vollständige Wegemenge.

Das [Motorlabor](http://127.0.0.1:4173/motor.html) nutzt 113 anatomisch benannte Beuger-/Strecker-IDs für **48 direkte, unkalibrierte Gelenkversuche**. Der Quellhash des gesamten Pfadexports und der Hash des Gelenkcodes stehen im Audit. Anatomischer Pfad, direkt gesetzte Motoraktivierung, Gelenkdynamik und biologische Funktionsbelege bleiben getrennt. Die Modelle übernehmen weder zentrale Transmittervorzeichen als Muskelvorzeichen noch BANC-Kanten als FAFB-Synapsen. Alle Referenzmotoren behalten `enabled_for_control=false`, `actuator_sign=null` und `force_gain=null`.

Für eine durchgehende Gehirn–Bauchmark-Analyse stehen zusätzlich
[BANC v888](banc_2026_integration.md) und [MaleCNS v1.0](malecns_2026.md)
als **eigene Tiere mit eigenen Neuron-IDs** bereit. Der MaleCNS-v1.0-Graph und
seine Rollenliste sind lokal MD5-geprüft. BANC liefert geprüfte
FAFB-Zellzuordnungen, AN/DN-Module und Effektorcluster; beide BANC-v888-Edgelists
sind separat gegen Dataverse-MD5 geprüft. Keine
ihrer Kanten wird als im FAFB-v783-Tier gemessene Synapse übernommen.

Der spätere [Einzelpunkt-Vollscan](synapse_point_audit.json) fand 48 veröffentlichte Kontakte mit zwei geprüften Neuronen, die nicht in der aggregierten Proofread-Tabelle stehen. Sie bilden 21 gerichtete Paar/Region-Schlüssel eines R7-Neurons und liegen separat in der [Ausnahme-CSV](../data/research_sources/derived/observed_raw_proofread_edge_exceptions_for_616.csv). Daneben stehen [7.337 beobachtete Kontakte zu ungeprüften Segmenten](../data/research_sources/derived/observed_segment_links_for_616.csv). Beide Ebenen bleiben getrennt vom Original-CSR. Die Ursache der 48er-Differenz ist noch ungeklärt.

Der [Princeton-Detektor von 2025](https://doi.org/10.1101/2025.07.11.664377)
untersucht **dasselbe FAFB-v783-Präparat** erneut. Die lokal MD5-geprüfte
ungefilterte Verbindungstabelle enthält bei 477 der 616 bisher kantenlosen
Original-IDs 3.171 gerichtete Paare und 20.914 als Synapsen gezählte
Detektionen ([Verbindungsaudit](reconstruction_candidates_v783/princeton_audit.json)).
Die inzwischen vollständig geladene und MD5-geprüfte Princeton-Punkttabelle
enthält 80.215.790 Zeilen; davon berühren 26.941 Punktaufrufe 550 der 616 IDs
([Punktaudit](reconstruction_candidates_v783/princeton_point_audit.json)).
Die Punkt- und Verbindungssummen sind zunächst verschieden. Der [Filteraudit](reconstruction_candidates_v783/princeton_filter_reconciliation.json)
zerlegt die 6.027 zusätzlichen Punkte exakt in 5.814 Autapsen und 213 nichtautaptische
Punkte des R7-Roots `720575940623940963`. Nach Ausschluss beider Klassen und der dokumentierten
Zuordnung leerer Punkt-Regionen zu `UNASGD` stimmen alle 3.233 Paar×Region-Zahlen
mit der ungefilterten Verbindungstabelle überein. Der Punkt-Export stammt vom
24.07.2025, die Verbindungstabelle vom 08.07.2025; die Ursache des R7-Ausschlusses
ist **nicht** belegt. Die 21 älteren Buhmann-R7-Rohpaar/Region-Schlüssel fehlen im
Princeton-Verbindungsexport. Beide Detektoren und das ursprüngliche v783.0-Aggregat
bleiben getrennte Evidenzebenen.

## Namensräume, Graphversionen und sichere Joins

| Datenebene | Gleiches Tier wie FAFB v783? | Graph und Schlüssel | Regel |
|---|---|---|---|
| FAFB v783 Original, Buhmann-Detektor | Ja | `flywire_edges`: `pre_pt_root_id`/`post_pt_root_id` | Veröffentlichtes Originalaggregat; Shiu/Eon verwenden dessen 138.639 verbundenen IDs. |
| FAFB v783 Princeton 2025 | Ja | `fafb_princeton_unfiltered_edges`: `pre_root_id`/`post_root_id` und Einzelpunkte mit 9-stelligem Root-ID-Suffix `720575940` | Exakte v783-ID möglich; andere Detektion. Die ≥5-Paar-Datei ist eine gefilterte Sicht, keine zusätzliche Messung. |
| BANC v888, weiblich, Gehirn und Bauchmark | Nein | `banc_v888_edges_v2` **oder** `banc_v888_edges_v3`: `pre`/`post` → `banc_v888_meta.banc_888_id` | v2 gehört zur Paper-Auswertung, v3 ist ein neuer Synapsendetektor. Nie beide summieren. Supplement 2 `root_id`, Supplement 6/7 `id` verwenden BANC-IDs. |
| MaleCNS v1.0, männlich, Gehirn und Bauchmark | Nein | `malecns_v1_traced_edges.body_pre`/`body_post` → `malecns_v1_roles.bodyId` | Beide Enden auf annotierte Neuronen filtern. Die v1.0-Tabelle hat dann 25.558.671 gerichtete Paarzeilen und 124.009.893 gewichtete Kontakte. v0.9-Zahlen bleiben außen vor. |

Alle IDs werden als Dezimaltext gespeichert. Ein BANC-`fafb_match` oder ein MaleCNS-`flywireType`
kennzeichnet eine **Homologie bzw. Zelltyp-Korrespondenz zwischen Tieren**.
Die 64.372 BANC-Reviewed-Match-Zeilen müssen auf `valid=t` gefiltert und ihre
BANC-Quell-IDs über einen Segmentanker eindeutig auf v888 aufgelöst werden.
Für 34 der 616 FAFB-IDs sind 97 solche v888-Homologe eindeutig auflösbar;
14 zugehörige Quellzeilen bleiben für die Kantenanalyse ausgeschlossen.
Die [BANC-v2/v3-Partnerliste](../data/research_sources/other/banc_2026/banc_partner_type_hypotheses_for_34_fafb_ids.csv)
ist deshalb eine **Typmuster-Hypothese**, kein FAFB-Root-zu-Root-Graph.

Die veröffentlichte [MaleCNS↔FlyWire-Typzuordnung](../data/malecns_v1_reference/mcns_fw_edge_comp_mappings.json)
deckt bei passender Seite 562 der 616 FAFB-IDs ab, davon aber **520 R1–6**.
Unter den übrigen 96 sind es 42, und nur 27 zeigen wörtliche Übereinstimmung
mit der früheren FAFB-Zelltyp-Hypothese. Die [Abdeckungsliste](../data/research_sources/derived/malecns_type_mapping_coverage_for_616.csv)
und [MaleCNS-Partner-Typmuster](../data/research_sources/derived/malecns_type_partner_hypotheses_for_616.csv)
bewahren diese Trennung. [BANC-Provenienz](../data/research_sources/other/banc_2026/provenance.json),
[MaleCNS-Provenienz](../data/malecns_v1_reference/provenance.json) und
[Princeton-Provenienz](../data/codex_fafb_v783/princeton_provenance.json)
enthalten die geprüften Quellgrößen und Hashes.

## Was sofort zusammenpasst

| Aufgabe | Lokale Eingabe | Schlüssel und Regel |
|---|---|---|
| Originalgehirn | `data/flywire_fafb_v783/proofread_root_ids_783.npy`, `proofread_connections_783.feather` | `pre_pt_root_id` → `post_pt_root_id`, getrennt nach `neuropil`; 139.255 IDs, 16.847.997 Verbindungszeilen, 54.492.922 Synapsen. [FlyWire v783](https://zenodo.org/records/10676866) |
| Princeton-Alternativdetektor im selben FAFB-Gehirn | `data/codex_fafb_v783/connections_princeton_no_threshold.csv.gz`, `connections_princeton.csv.gz`, `fafb_v783_princeton_synapse_table.csv.gz` | Vollständige Punktdatei und beide Verbindungstabellen mit amtlicher GCS-MD5 geprüft. Punkt-Root-Suffix `720575940` korrekt zu vollständiger ID ergänzen. [616er-Punktliste](reconstruction_candidates_v783/princeton_individual_points_for_616.csv) und [Filteraudit](reconstruction_candidates_v783/princeton_filter_reconciliation.json) bleiben separat vom Originalgraph. |
| BANC v888, zusammenhängender weiblicher Gehirn-Bauchmark-Graph | `data/research_sources/other/banc_2026/banc_888_meta.feather`, `banc_888_edgelist_simple_v2.feather` oder `banc_888_edgelist_simple_v3.feather`, `supplemental_data_2.txt`, `supplemental_data_6.txt`, `supplemental_data_7.txt` | `pre`/`post` → `banc_888_id`; Paper-v2 und neuer v3 sind getrennte Varianten. 188.508 Meta-IDs; 11.752.828 v2- bzw. 13.620.865 v3-Paarzeilen. [Audit](../data/research_sources/other/banc_2026/edgelist_audit.json) |
| MaleCNS v1.0, zusammenhängender männlicher Gehirn-Bauchmark-Graph | `data/malecns_v1_reference/connectome-weights-male-cns-v1.0-minconf-0.5-traced-only.feather`, `model_neuron_roles_v1.csv` | `body_pre`/`body_post` → `bodyId`; beide Enden auf die 166.700 annotierten Neuronen filtern. [Audit](malecns_v1_reference_audit.json) |
| Zellnamen und Klassen | `data/flywire_annotations_v2.1.0/Supplemental_file1_neuron_annotations.tsv` | Exakter `root_id`-Join; 139.255 eindeutige IDs. [Annotations v2.1.0](https://github.com/flyconnectome/flywire_annotations/releases/tag/v2.1.0) |
| Spiking-Gehirnmodell | `data/research_sources/shiu/Completeness_783.csv`, `Connectivity_783.parquet` | Die `Unnamed: 0`-Root-IDs bilden ein **geordnetes** Array. `Presynaptic_Index` und `Postsynaptic_Index` sind dessen nullbasierte Positionen; ID-Spalten gegenprüfen. 138.639 Modellneuronen. [Shiu et al.](https://doi.org/10.1038/s41586-024-07763-9), [Modellcode](https://github.com/philshiu/Drosophila_brain_model) |
| Kopfberührung | `data/research_sources/other/calle_schuler_bmn/Supplementary_file_1_BMNs.csv` und Dateien 2/3/6/7 | 705 BMN-IDs `flywire_id_v783` direkt verfügbar; Ausgänge `pre_root_id_bmn` → `post_root_id_partner`, Eingänge umgekehrt. [Calle-Schuler et al.](https://doi.org/10.7554/eLife.108044.3) |
| Geschmack und Fütterung | `data/research_sources/other/tastekin/tastekin_2026_cell_table_s1.xlsx` | Nur Zeilen mit `Connectome = FAFB – Flywire`; dann `Body_ID` als Zeichenkette verknüpfen. 411 GRNs und 66 MNs, alle im lokalen v783-Modell. [Tastekin et al.](https://doi.org/10.1016/j.cell.2026.08.016) |
| Hirn–Körper-Schnittstelle | `data/research_sources/other/stuerner_neckconnective/Supplemental_file5_FAFB_DNs.tsv`, `Supplemental_file8_FAFB_ANs_SAs.tsv` | `root_id` exakt verknüpfen: 1.316 DNs und 2.345 ANs/SAs in offiziellen v783-IDs; 1.311 bzw. 2.300 im Spiking-Modell. [Stürner et al.](https://doi.org/10.1038/s41586-025-08925-z) |
| Visuelles System | `data/research_sources/other/visual_system/data/neuron_table.csv`, `type_to_type_connection_and_synapse_counts.csv` | `cell ID` entspricht exakt den 139.255 offiziellen v783-Root-IDs. `resolved type` bindet Typen an Neuronen; die 72.954 Typ-Paare sind Summen, keine einzelnen Synapsen. [Visual-system-Paper](https://doi.org/10.1038/s41586-024-07981-1) |
| Geruch, anatomische Kandidaten | `data/research_sources/other/olfaction/fafb_olfactory_root_id_crosswalk.csv` | 2.281 FAFB-v783-ORN-IDs stammen aus der Annotation; 2.279 sind im Shiu-Modell. Die Literaturzuordnung läuft über `hemibrain_type = ORN_<glomerulus>` und dann Glomerulus/Rezeptor, nicht über eine Root-ID in der Geruchsstudie. 1.324 Zeilen haben `mapping_status = exact_2025_and_door_agreement`. [Benton et al.](https://doi.org/10.1038/s44319-025-00476-8), [DoOR](https://github.com/ropensci/DoOR.data) |
| Geruch, Antwortmuster | `data/research_sources/other/olfaction/door/data/door_response_matrix.csv`, `odor.csv`, `door_mappings.csv` | Semikolon-CSV: erstes unlabeled Feld der Antwortmatrix ist der Geruchs-`InChIKey`; alle 691 Werte passen exakt zu `odor.csv:InChIKey`. Die 78 Antwortspalten sind Literatur-Response-Units, keine Neuronen-IDs. [DoOR.data](https://github.com/ropensci/DoOR.data) |
| Neuropeptide | `data/research_sources/other/neuropeptides/gt_np_data.csv`, `fafb_neuropeptide_type_candidates.csv` | Die Quelle hat Zelltypnamen, keine FAFB-Root-IDs. Exakter Typnamen-Abgleich mit v783-`cell_type` oder `hemibrain_type` erzeugt 17.150 Kandidatenzeilen für 11.567 Root-IDs (11.566 im Shiu-Modell); kein Messnachweis im FAFB-Tier. [Kuratierte Quelle](https://github.com/flyconnectome/drosophila_neuropeptides) |

Die Eon-`2025_Completeness_783.csv` enthält dieselben 138.639 IDs in derselben Reihenfolge und dieselben `Completed`-Werte wie Shiu. Die lokal verwendete Shiu-Parquet-Datei ist die identische öffentliche Connectivity-Datei, auf die Eon setzt. Eons Benchmark-Code liefert Rechenmethoden und Leistungsvergleiche, aber keine vollständige sensorische oder motorische Verkabelung für die 3D-Fliege. [Eon-Repository](https://github.com/eonsystemspbc/fly-brain).

## Bewegung und Körper als Referenz

| Quelle | Lokale Datei | Nutzbarer Befund und Grenze |
|---|---|---|
| Spontanes Gehen | `data/research_sources/other/autonomous_behavior/gattuso_2025/github/gattuso_locomotion_model.m` | Fünf abstrakte, verrauschte Bewegungseinheiten erzeugen Geschwindigkeit, Drehen und Wege; der Quellcode enthält auch ein Geruchsreiz-Signal. Das ist ein Vergleichsmodell für spontane Bewegung, kein FlyWire-Neuronennetz. [Gattuso et al.](https://doi.org/10.1073/pnas.2407626122) |
| DNa-Lenkung | `data/research_sources/other/autonomous_behavior/rayshubskiy_2025/github/A1_A2_yaw_fwd_analysis.m` | Analyse von DNa01/DNa02 und Geh-/Drehverhalten anderer Fliegen. Die lokal geladene Dataverse-`README.md` verweist auf Rohdaten; diese Rohaufnahmen sind hier nicht enthalten. Ein Zellname verbindet die Messung nicht automatisch mit einer v783-Root-ID oder Muskelkraft. [Rayshubskiy et al.](https://doi.org/10.7554/eLife.102230) |
| Gang-Kinematik | `data/research_sources/other/autonomous_behavior/flygym/dataverse/annotated_3d_walking_kinematics.csv` | 37 Frames und 108 Spalten mit Körper- und Beinpunkten, `frame_idx` und `video_id` als Zeilenbezug. Geeignet für Pose-/Gangvergleiche, nicht für einen Neuronen-Join. [FlyGym-Daten](https://doi.org/10.7910/DVN/3MCEYR) |
| Körper und Augen | `data/research_sources/other/autonomous_behavior/flygym/github/src/flygym/assets/model/neuromechfly/rigging.yaml`, `vision.yaml`, `compound_eye.npz` | Körperkonfiguration und simuliertes Facettenauge; das Eye-Asset hat ein Pixelraster 512 × 450 und eine Maske für 721 Ommatidien je Auge. Ommatidien-Indizes sind keine FlyWire-Root-IDs; eine Photorezeptor-zu-Spike-Kalibrierung fehlt. [FlyGym/NeuroMechFly v2](https://doi.org/10.1038/s41592-024-02497-y) |
| Ganzkörperphysik | `data/research_sources/other/autonomous_behavior/flybody/github/flybody/fruitfly/assets/fruitfly.xml`, `flybody/figshare/trained-fly-policies.zip` | FlyBody beschreibt einen detaillierten MuJoCo-Körper und separat trainierte Gang-/Flugcontroller. Lokal sind die XML- und kleinen Policy-Archive verfügbar, nicht die großen Mesh-Assets; es gibt keine direkte v783-Root-ID-zu-Muskel-Zuordnung. [Vaxenburg et al.](https://doi.org/10.1038/s41586-025-09029-4) |
| Browser-Vorbild | `data/research_sources/other/autonomous_behavior/webgpu_fly/README.md` | Quellengeprüfte Architektur mit FlyWire, MANC, FlyBody, WebGPU und MuJoCo-WASM. Dessen Gehirn–Bauchmark-Abgleich nutzt Zelltypnamen verschiedener Tiere und die Bewegung zusätzliche programmierte Hilfen; daher nur Architekturbeispiel. [webgpu-fly](https://github.com/abgnydn/webgpu-fly) |

Die FlyGym-[Browsernotizen](../data/research_sources/other/autonomous_behavior/flygym/github/wasm/README.md) beschreiben einen MuJoCo-WASM-/Three.js-Viewer und ein manuell gesteuertes Spiel. Die dazu generierten Modellassets und Anbieterdateien sind im Git-Quellbaum nicht enthalten. Keines dieser Referenzpakete liefert eine validierte, autonome v783-Gehirn-zu-Körper-Kopplung. Die genaue Herkunft und Prüfsummen stehen in [autonomous_behavior/provenance.json](../data/research_sources/other/autonomous_behavior/provenance.json).

## Schutz vor falschen Verknüpfungen

1. **ID als Text:** Die 18-stelligen Root-IDs dürfen im Browser nicht in JavaScript-`Number` umgewandelt werden. `supervoxel_id`, Stürners `group` und IDs aus MANC, FANC, MaleCNS oder BANC sind andere Bezeichner.
2. **Version prüfen:** Die Shiu-Zusatzmappe beschreibt publizierte **v630**-Experimente. Der [lokale Audit](shiu_supplement_audit.md) hat 229 Sensor-/Motor-Kandidaten extrahiert: vier IDs fehlen in v783, bei zwei widerspricht die Seite der aktuellen Annotation. Die Referenzraten sind keine bereits gemessenen v783-Antworten.
3. **Kanten nicht doppelt gewichten:** In Shius Parquet ist `Connectivity` die Synapsenzahl, `Excitatory` das Modellvorzeichen ±1 und `Excitatory x Connectivity` bereits das vorzeichenbehaftete Gewicht. Die Original-Feather-Kanten und die Shiu-Modellkanten getrennt halten.
4. **Nur graphfähige IDs stimulieren:** Die offizielle v783-Liste umfasst 616 weitere IDs ohne Zeile in der originalen Proofread-Verbindungstabelle. Sie fehlen folglich im Shiu/Eon-Modell. Ihr biologischer Grund ist aus diesem Audit nicht ableitbar.
5. **Anatomie ist keine Körperregelung:** Die Paper benennen Sinneszellen, absteigende Neuronen und einzelne Motorneuronen. Sie liefern keine vollständige kalibrierte Abbildung von 3D-Reizstärke auf Spikes oder von Spikes auf Muskelkräfte.
6. **Visuelle IDs anders indiziert:** `visual_system/data/synapse_table_compact_ids_map.csv.gz` enthält dieselbe 138.639er Root-ID-*Menge* wie Shiu, aber in anderer Reihenfolge. `compact cell ID` daher erst über `full cell ID (root ID)` auflösen; danach den Shiu-Index aus dessen eigener CSV-Reihenfolge bestimmen. Die visuelle Typ-Tabelle lässt sich nur über `resolved type` interpretieren und erzeugt keine individuellen Kanten.
7. **Photorezeptoren:** In v783 wurden Photorezeptor-Synapsen laut Visual-system-Studie unzureichend erkannt; ihre Verbindungen werden dort qualitativ behandelt. Von den 616 offiziellen IDs ohne Shiu-Kante sind 536 als visuell annotiert (520 R1–6, 10 R8, 6 R7). Sie fehlen im Spiking-Modell; daraus darf keine physiologische Inaktivität geschlossen werden.
8. **Geruch nur über Literatur-Labels:** Benton EV1 und DoOR tragen keine v783-Root-IDs. Der [lokale Crosswalk](../data/research_sources/other/olfaction/crosswalk_audit.json) gleicht Glomerulusnamen und Rezeptorbezeichnungen ab. Nur `exact_2025_and_door_agreement` wird automatisch einer DoOR-Antwortspalte zugeordnet. Auch diese 1.324 Zuordnungen sind keine Geruchsmessung an der FlyWire-Fliege. DoOR mittelt heterogene Studien; Konzentration und Assay müssen beim Modellieren ausdrücklich berücksichtigt werden.
9. **Neuropeptide nur als Zelltyp-Hinweis:** Der [lokale Audit](../data/research_sources/other/neuropeptides/crosswalk_audit.json) projiziert kuratierte Peptidbefunde auf exakt gleich benannte v783-Zelltypen. `root_id` im Ergebnis macht die Projektion auffindbar, weist aber weder Peptidfreisetzung noch Rezeptoren oder Modulationsstärke dieses einzelnen Neurons nach. Mehrere Befunde pro ID sind möglich.
10. **Referenzbewegung ist keine neuronale Auslese:** Gattusos Einheiten, Rayshubskiys Versuchsgrößen und FlyGyms Gelenk-/Augenbezeichner besitzen keine gemeinsame FAFB-Root-ID-Spalte. Eine Zuordnung von Shiu-Spikes zu Körperaktionen muss eigenständig begründet und gegen Verhalten geprüft werden.
11. **BANC und MaleCNS gehören zu anderen Tieren:** BANC-v888-`banc_888_id` und MaleCNS-v1.0-`bodyId` erhalten je einen eigenen Graph-Namensraum. BANC-Reviewed-Matches und MaleCNS-Typ-/Seitenlabels erzeugen prüfbare Homologie-Hypothesen, keine FAFB-Einzelsynapsen. Bei BANC mehrere Matches und 14 nicht eindeutig aufgelöste Quellzeilen erhalten; bei MaleCNS die starke Verzerrung durch 520 R1–6 gesondert ausweisen.
12. **Synapsendetektoren getrennt halten:** BANC v2/v3 und FAFB-Buhmann/Princeton sind alternative Detektorversionen. Princeton-Einzelpunkte stimmen nach dem [empirischen Filter](reconstruction_candidates_v783/princeton_filter_reconciliation.json) mit Princeton-Verbindungssummen überein; diese Übereinstimmung erklärt die R7-Filterursache nicht und verändert das ältere FlyWire-Aggregat nicht.

## Reihenfolge für das Modell

1. Original-IDs, Annotationen und Shiu-Modelltabellen laden; Integritätsprüfung aus `data/research_sources/provenance.json` und `analysis/research_data_audit.json` übernehmen.
2. Pro Sinnesmodalität die exakt passenden v783-IDs wählen: Kopfborsten aus Calle-Schuler, Geschmack aus Tastekin, visuelle Zelltypen aus der Visual-system-Tabelle, Geruchs-ORN-IDs aus dem Crosswalk, ergänzend geprüfte Kandidaten aus der Shiu-Zusatzmappe. Geruchs-Response-Units und Neuropeptide als Literatur-Hypothesen kennzeichnen.
3. Die Spiking-Simulation mit Shius `Connectivity_783.parquet` aufsetzen und Eingangsreize zunächst mit ausdrücklich als Annahmen gekennzeichneten Parametern einspeisen. Die v630-Referenzmuster dienen anschließend als Vergleich, nicht als v783-Garantie.
4. Aktivität benannter absteigender Neuronen nach Stürner und Fütterungs-Motorneuronen nach Tastekin als Ausgänge protokollieren. Eine 3D-Körpersteuerung erst an diese Ausgänge binden, wenn ihre Transformation dokumentiert und getestet ist.
5. FlyGym-Körperdaten für ein 3D-Rig und eine Augenansicht sowie Gattuso/Rayshubskiy als getrennte Verhaltensvergleiche verwenden. Daraus keine automatische neuronale Steuerregel oder vorgegebene Verhaltensziele ableiten.
6. Bei den 616 FAFB-IDs ohne Originalkante die vollständig geladenen Princeton-Punkte und die ungefilterte Princeton-Verbindungstabelle als **alternative Detektor-Ebene** prüfen; die alten 48 R7-Rohkontakte und 7.337 Segmentkontakte separat sichtbar halten. Die Punkttabelle darf erst nach der reproduzierten Autapsen-/R7-/Region-Filterung mit dem Princeton-Aggregat verglichen werden.
7. Für einen durchgehenden Gehirn-Bauchmark-Prototypen BANC v888 oder MaleCNS v1.0 als **eigenen** ZNS-Graphen wählen. BANC AN/DN-, Sinnes- und Effektorannotationen beziehungsweise MaleCNS-Rollenindex an dessen jeweilige IDs binden. Sinnesreiz→Spike, neuronale Aktivität→Aktuator und Energie-/Körperzustand bleiben explizite, gegen Verhalten zu prüfende Modellkomponenten.

**Rechte:** FlyWires Zenodo-Daten, BANCs ausgewählte Dataverse-Dateien und MaleCNS-Daten stehen unter CC BY 4.0; die Princeton-Codex-Exports mit ihrer gesonderten Quellprovenienz verwenden. Das Shiu-Code-Repository zeigt MIT, Eon GPL-2.0-or-later, das Visual-system-Repository Apache-2.0, DoOR.data CC BY-SA 4.0 und die Neuropeptid-Kuration CC BY 4.0. Gattusos Code ist BSD-2-Clause, Rayshubskiys Code MIT und FlyGym Apache-2.0. Calle-Schulers eLife-Artikel ist CC BY 4.0; Benton EV1 wird im Artikel als CC0-Datenmaterial beschrieben, sofern nicht anders vermerkt. Für Stürners GitHub-Dateien ist lokal keine Repository-Lizenz deklariert; bei Tastekins Verlagsdatei und der Annotation TSV vor Weiterverteilung die Nutzungsbedingungen prüfen. Die Einzelquellen bleiben mit ihren Prüfsummen im Arbeitsordner.

<!-- SENSORIMOTOR-INTEGRATION:START -->
## Lokaler Sensor-Motor-Kreis und Original-CPG-Dateien

Der [FeCO-Datensatz](sensorimotor_mapping/README.md) enthält **625 exakte BANC-Sensor-IDs** aller sechs Beine. Der linke Vorderbein-Ausschnitt enthält 110 Sensoren und 19 Femur–Tibia-Motorneuronen. Die vollständigen Wege und verwendeten Kanten bleiben getrennt: v2 mit 7.292 Wegen/2.720 Kanten, v3 mit 8.968 Wegen/3.232 Kanten. Der [Join-Audit](sensorimotor_mapping/validation.json) prüft jede Kante gegen denselben Detektor und die Eingangs-Normierung gegen den Gesamtgraphen. Exakte Sensorpolaritäten bleiben unbekannt.

Das [Sensor-Motor-Labor](http://127.0.0.1:4173/sensorimotor.html) schließt einen lokalen Kreis: tatsächlicher LF-Gelenkwinkel → deklarierte claw/hook-Eingänge → Zustände ausgewählter BANC-Neuronen → getrennte Beuger-/Strecker-Pools → dasselbe Gelenk. Standard v2: 54 Sensoren, 45 Zwischenzellen, 19 Motoren und 321 Kanten; v3: 54/55/19/461. Die kontinuierlichen Zustände sind Modellaktivitäten von 0 bis 1, keine gemessenen Raten oder Spikes. Originalgraphen bleiben unverändert.

Der [Audit](../app/data/sensorimotor_audit.json) umfasst **194 Viersekundenversuche**, 388,000 Integrationsschritte und 24 zusätzliche Übertragungsproben. Eingänge abschalten, einfrieren, Kanten entfernen und passende sowie unpassende Sensor-Replays prüfen den technischen Kausalweg. Alle vier Polaritätshypothesen und negative Resultate bleiben erhalten. Bei Standardverstärkung liegt die relative Spitzenauslenkungsreduktion ungefähr zwischen −0,60 % und +0,33 %; die mechanische Rückfederung dominiert. Das belegt keine biologische Stabilisierung. Quell- und Codeprüfsummen sind im Audit hinterlegt; [Methoden](../app/SENSORIMOTOR_METHODS.md) und [offene Rekonstruktionslücken](sensorimotor_mapping/autonomy_gaps.md) benennen Parameter und Grenzen.

**7 originale CPG-Dateien** liegen nun lokal unter `data/research_sources/other/pugliese_cpg_2026/`: signierte Matrix, zugehörige Zelltabellen, `sim_utils.py`, Original-Runner `vnc_sim.py` sowie zwei Standard-Konfigurationen. Commit `10e7661bf414ba7b4c2edf795cd36d0f878c17c0` und die tatsächlichen SHA256-Werte stehen in der [Download-Provenienz](../data/research_sources/other/pugliese_cpg_2026/provenance.json) und werden beim Manifest-Update erneut geprüft. Die neuere CPG-Zelltabelle bleibt eine eigene Annotationsversion; abweichende Motor-/Transmitterfelder überschreiben den älteren BANC-Export nicht.

Die **Originalkonfiguration von Lauf 33241778** liegt zusätzlich in drei archivierten YAML-Dateien vor: Reiz 400, Seed 129, 1.024 Replikate. Diese per HTTP-Range beschafften ZIP-Mitglieder sind gegen ihre CRC32 geprüft und mit eigenen SHA256-Werten dokumentiert; die MD5 des unvollständig geladenen Gesamtarchivs ist ausdrücklich nicht verifiziert ([Provenienz](../data/research_sources/other/pugliese_cpg_2026/run33241778/download_provenance.json)). Auch die unveränderten Originalparameter von Replikat 0 sind gezielt aus dem HDF5 extrahiert und gehasht; die CRC des gesamten HDF5 wurde nicht geprüft.

Die [CPU-Nachrechnung](cpg_reproduction/results.md) ist mit **acht Bedingungen und 57 bestandenen Ergebnisprüfungen** fertig. Bei konstantem DNg100-Eingang entstehen sechs rhythmische Motorantworten um 15,15 Hz; E1-/E2-Entfernung beseitigt diese Rhythmik im Modell, I2-Entfernung erhält sie bei etwa 13,33 Hz. Das ist ein Ergebnis des Bein-Teilnetzmodells, keine Flügelschlagfrequenz. Originalparameter, eigener Solver und fehlender Vergleich gegen ursprüngliche Trajektorien bleiben getrennt. Der lokale LF-Regelkreis bildet weder das vollständige Gehirn noch Gang, Balance, Motivation oder eine autonome Fliege ab.

Das [Flug-Anschlusspaket](flight_control_mapping/README.md) ergänzt 91 Wing-/Halteren-Motorquellzeilen, 85 konfliktfreie anatomische Poolkandidaten, 244 proofread Propriozeptor-Eingänge und echte separate v2/v3-Wege. Peripherer Nervenverlauf bestimmt die Effektor-Seite; DLM5-Somaseite ist gekreuzt. Muskelkräfte, Flügelphase, Aero-/Sensorparameter und eine biologische Flugvalidierung bleiben offen.

Der getrennte [Flügel-Rollprüfstand](../app/FLIGHT_METHODS.md) ist mit **26 Versuchen und 432.000 Integrationsschritten** technisch geprüft. Er verwendet 24 Power-Motor-IDs und zwei b1-Referenzen, mechanische Selbstschwingung und einen ausdrücklich technischen Rollrückmeldekanal. Die erfassten BANC-Sensor-Motor-Kanten werden dort noch nicht dynamisch simuliert; freie Translation und autonomer Flug sind nicht implementiert. Der [CPG-Viewer](http://127.0.0.1:4173/cpg.html) bewahrt sämtliche 1.081.080 geprüften Modellwerte ohne zusätzliche Raten oder Körperaktionen.
<!-- SENSORIMOTOR-INTEGRATION:END -->
