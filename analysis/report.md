# FlyWire FAFB v783: Datenanalyse

Erstellt: 2026-09-26T22:09:47.390458+00:00

Quelle: [FlyWire-Zenodo-Release 783.0](https://zenodo.org/records/10676866); [Neuronannotationen v2.1.0](https://github.com/flyconnectome/flywire_annotations/releases/tag/v2.1.0).

## Integrität und Umfang

| Datei | Größe (Bytes) | MD5 | Zeilen | Status |
|---|---:|---|---:|---|
| `flywire_synapses_783.feather` | 9492998242 | `f8f1b97c9d4b0ea9b4c8b287f6b99091` | 130054535 | OK |
| `per_neuron_neuropil_count_post_783.feather` | 233843050 | `bb5999f10920ade803d9f37097a43a56` | 43439994 | OK |
| `per_neuron_neuropil_count_pre_783.feather` | 16853770 | `90fcdb42c1ba05ed92820840fa1e6ba0` | 2781037 | OK |
| `proofread_connections_783.feather` | 852022274 | `f48f972d262323a102aed49af1396b8a` | 16847997 | OK |
| `proofread_root_ids_783.npy` | 1114168 | `e0e6c19732fd8c7a4e39a2d170105421` | 139255 | OK |

## Kernergebnisse

- Gegengelesene Neuronen: **139255** (Duplikate: 0).
- Einzel-Synapsen-Zeilen: **130054535**; davon beide Partner gegengelesen: **54492970**.
- Aggregierte Kanten pro Neuronenpaar und Region: **16847997**; Synapsenzahl: **54492922**.
- Prä-Synapsen-Region-Summary: **2781037** Zeilen; gewichtete Synapsensumme **130054535** (erst mit kompletter Einzel-Synapsentabelle querprüfbar).
- Annotationen: **139255** Zeilen, **139255** eindeutige Root-IDs; mit Soma-Koordinaten: **118107**.

### Für Sensorik und Motorik relevante Klassen

- sensory: **16903**
- ascending: **2362**
- descending: **1303**
- motor: **106**

## Querprüfungen

- pre_summary_equals_synapse_rows: **True**
- post_summary_equals_synapse_rows: **True**
- pre_summary_equals_synapses_by_region: **True**
- post_summary_equals_synapses_by_region: **True**
- proofread_edge_synapses_do_not_exceed_all_synapses: **True**
- proofread_edge_row_partners_all_in_root_array: **True**

## Regionen mit den meisten Einzel-Synapsen

- ME_R: 16718114
- ME_L: 15374870
- LO_R: 7610820
- LO_L: 7478622
- GNG: 7307494
- AVLP_R: 5392827
- AVLP_L: 4487005
- SMP_R: 3330544
- LOP_R: 3166111
- SMP_L: 3140353
- SLP_R: 3021395
- SLP_L: 2722685
- LOP_L: 2555529
- PLP_L: 2164385
- LH_L: 2144877

## Neurotransmitter-Prognosen der Einzel-Synapsen

- gaba: Mittelwert 0.2169; fehlend 5347; außerhalb [0,1] 0
- ach: Mittelwert 0.4868; fehlend 5347; außerhalb [0,1] 0
- glut: Mittelwert 0.2004; fehlend 5347; außerhalb [0,1] 0
- oct: Mittelwert 0.0232; fehlend 5347; außerhalb [0,1] 0
- ser: Mittelwert 0.0230; fehlend 5347; außerhalb [0,1] 0
- da: Mittelwert 0.0498; fehlend 5347; außerhalb [0,1] 0

## Grenzen

- Die Analyse betrifft ausschließlich FAFB v783, also das Gehirn einer adulten weiblichen Fruchtfliege. BANC ist ein separater Datensatz.
- `proofread_connections` enthält ab einer Synapse eine Zeile pro gerichtetem Neuronenpaar **und Region**. Die Zeilenzahl ist nicht die Anzahl eindeutiger Neuronenpaare.
- `flywire_synapses` enthält auch Synapsen mit nicht gegengelesenen Partnern. Der Anteil beidseitig gegengelesener Synapsen wird separat ausgewiesen.
- Neurotransmitterwerte sind Modellprognosen, keine gemessenen neuronalen Dynamikparameter. Anatomische Soma-Punkte liefern allein keine Axon- oder Dendritenverläufe.
- Die v2.1.0-Annotationen entsprechen der 2024 veröffentlichten Klassifikation; spätere Codex-Annotationen können abweichen.

## Morphologie (Zenodo 10877326)

- Dateiintegrität per Größe und MD5: **vollständig geprüft**.
- Schema und Zeilenzahl: **für alle Dateien geprüft**.
- Numerische Inhalte: **erkannte Werte vollständig gelesen**.

| Datei | Größe (Bytes) | MD5 | Zeilen | Datenprüfung |
|---|---:|---|---:|---|
| `nblast_flywire_all_right_aba_comp.feather` | 809046036 | `a8b3d2589b382bdb1ca19a060249a2dc` | 139249 | MD5 OK; numerischer Vollscan |
| `nblast_flywire_hemibrain_min_comp.feather` | 212095362 | `3ca6d79615e1cd30b37f32a8ae845f32` | 97900 | MD5 OK; numerischer Vollscan |
| `nblast_flywire_mirrored_hemibrain_min_comp.feather` | 223176394 | `a0e2089764911fc5fd2d2d14c6aaa6a0` | 97900 | MD5 OK; numerischer Vollscan |
| `sk_lod1_783_healed_ds2.parquet` | 5355543468 | `a4c104776f33ec539ef859064c4de3df` | 268281651 | MD5 OK; numerischer Vollscan |

Die Skelette liegen als SWC-Knoten in einer Parquet-Datei vor: Eine Tabellenzeile beschreibt einen Knoten, `neuron` ist die FlyWire-Root-ID. Ihre Koordinaten sind in nm.
Die NBLAST-Scores wurden von den Herausgebern auf vier Dezimalstellen gerundet und negative Werte bei 0 abgeschnitten.
Dateiintegrität, Schema, ID-Abdeckung und numerische Inhaltsprüfung sind getrennt im JSON-Bericht ausgewiesen.
Ein numerischer Vollscan umfasst alle erkannten numerischen Spalten und Skelettzeilen. Nicht erkannte verschachtelte oder textuelle SWC-Inhalte werden ausdrücklich als ungeprüft markiert.

## Separater Codex-v783-Graph

- Status: **vorhanden**; Integritätsprüfungen: **bestanden**.
- Neuronen: **139255**; gerichtete Paarkanten: **3732460**; darin enthaltene Synapsen: **50666648**.
- Quelle: `connections_princeton.csv.gz` mit **5342446** Paar×Neuropil-Zeilen vor der Aggregation.
- Die Codex-Quelle ist bereits auf Paare mit mindestens fünf Synapsen über alle Regionen gefiltert. Der Graph-Parameter `min_synapses_per_edge=1` stellt ausgelassene Paare nicht wieder her.
- Die sechs Transmitterkanäle im Graphen kodieren gewichtete Anteile kategorischer `nt_type`-Labels. Sie sind **keine** ursprünglichen Wahrscheinlichkeiten wie in der Zenodo-Feather-Tabelle.
- Der Codex-Graph und die Original-Zenodo-Verbindungstabelle sind verschiedene Datenprodukte; ihre Kantenzahlen und Synapsensummen dürfen nicht gleichgesetzt werden.

Häufigste Neuropile im Codex-Export (Paar×Neuropil-Zeilen):

- ME_R: 660198
- ME_L: 616856
- LO_R: 316692
- LO_L: 306759
- GNG: 226326
- AVLP_R: 164156
- LOP_R: 164071
- AVLP_L: 128730
- LOP_L: 115527
- PVLP_L: 109322

Synapsen nach kategorischem Codex-`nt_type`:

- ACH: 30101369
- GABA: 11902450
- GLUT: 7627650
- SER: 502056
- DA: 378682
- OCT: 154441
