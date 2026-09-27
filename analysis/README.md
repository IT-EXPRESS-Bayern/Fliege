# FlyWire FAFB v783: reproduzierbare Datenanalyse

Dieses Werkzeug prüft und analysiert **ausschließlich** die fünf Dateien aus dem
[FlyWire FAFB v783.0 Zenodo-Release](https://zenodo.org/records/10676866),
die vier Dateien aus dem [Morphologie-Supplement](https://zenodo.org/records/10877326)
und die [Neuronannotationen v2.1.0](https://github.com/flyconnectome/flywire_annotations/releases/tag/v2.1.0).
Es benötigt keine Anmeldung und sendet keine Daten an einen Server.

## Eingaben

Standardpfade relativ zum Projektverzeichnis:

- `data/flywire_fafb_v783/flywire_synapses_783.feather`
- `data/flywire_fafb_v783/per_neuron_neuropil_count_post_783.feather`
- `data/flywire_fafb_v783/per_neuron_neuropil_count_pre_783.feather`
- `data/flywire_fafb_v783/proofread_connections_783.feather`
- `data/flywire_fafb_v783/proofread_root_ids_783.npy`
- `data/flywire_annotations_v2.1.0/Supplemental_file1_neuron_annotations.tsv`
- `data/flywire_morphology_v783/sk_lod1_783_healed_ds2.parquet`
- `data/flywire_morphology_v783/nblast_flywire_*.feather` (drei Dateien)
- `brain/graph-v783/` sowie dessen Quelle
  `data/codex_fafb_v783/connections_princeton.csv.gz` (separate Auswertung)

Die MD5-Sollwerte aller Zenodo-Dateien und der auf `v2.1.0` festgelegten
Annotationsdatei sind im Skript hinterlegt.
Das Werkzeug vergleicht zuerst die Dateigrößen mit dem Zenodo-Manifest und der
gepinnten Annotationsdatei. Noch laufende Downloads werden übersprungen und
im Teilbericht als Größenabweichung ausgewiesen.

## Ausführen unter Windows

```powershell
& '<USER_HOME>\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m venv --system-site-packages analysis/.venv
& 'analysis\.venv\Scripts\python.exe' -m pip install -r analysis/requirements.txt
& 'analysis\.venv\Scripts\python.exe' analysis/analyze_flywire.py
```

Alternativ sind `--data-dir`, `--annotations` und `--output-dir` verfügbar.
Das Programm erzeugt `analysis/report.json` und `analysis/report.md`. Ein
Teilbericht während laufender Downloads ist mit `--allow-incomplete` möglich.
`--max-batches 1 --skip-md5 --allow-incomplete` dient nur für einen schnellen
Funktionstest; der Bericht kennzeichnet diese Stichprobe als unvollständig.
Der reguläre Lauf prüft die Morphologie numerisch spaltenweise vollständig.
`--deep-morphology` wählt diesen Standard ausdrücklich. Für einen schnellen
Zwischenbericht liest `--sample-morphology --allow-incomplete` nur fünf
NBLAST-Score-Spalten und höchstens zwei Skelett-Koordinaten-Batches.

Der vollständige Lauf liest rund 10,6 GB für die MD5-Prüfung und nochmals die
Feather-Daten. Die 9,5-GB-Synapsendatei wird in Arrow-Batches verarbeitet. Die
Speicherbelegung wächst vor allem mit der Anzahl unterschiedlicher Root-IDs,
nicht mit der Gesamtzahl der Synapsen.

## Kennzahlen und Interpretation

- Dateigrößen, MD5, Arrow-Schema und gelesene Zeilen je Datei
- Zahl gegengelesener und annotierter Neuronen, ID-Duplikate und Join-Abdeckung
- Einzel-Synapsen, regional aggregierte Verbindungskanten und deren Gewichte
- Verteilung über Neuropile, Minima/Mittelwerte/Maxima der sechs
  Neurotransmitter-Wahrscheinlichkeiten sowie fehlende oder unplausible Werte
- Konsistenz der zwei per-Neuron-Region-Summendateien mit der Einzel-Synapsenzahl
- Stärkste Eingangs- und Ausgangsgewichte pro gegengelesenem Neuron
- Für SWC-Skelette im Parquet-Container: Schema, Metadaten-Zeilenzahl,
  Root-ID-Abdeckung über die tatsächliche `neuron`-Spalte sowie im regulären
  Lauf alle numerischen Spalten und Skelettknoten. Jede Tabellenzeile ist ein
  Knoten mit `node_id`, `parent_id`, `radius`, `x`, `y`, `z` und `neuron`.
- Für die drei NBLAST-Tabellen: Schema, Zeilen, IDs in Spalten/Index und im
  regulären Lauf alle numerischen Score-Spalten, in kleinen Spaltenblöcken.
- Für den separaten Codex-Graphen: SHA-256 der sechs Dateien, CSR-Struktur,
  Knoten-/Kanten-/Synapsenzahlen, ID-Abgleich mit den Zenodo-Root-IDs,
  Quell-MD5 und zeilenweiser Summenabgleich der gzip-CSV

`proofread_connections_783.feather` enthält pro gerichtetem Neuronenpaar und
Neuropil eine Zeile ab **einer** Synapse. Ein Paar kann in mehreren Neuropilen
auftauchen. Daher ist die Zeilenzahl kein global eindeutiger Paarzähler und
unterscheidet sich von der Codex-Anzeige, die standardmäßig Paare mit mindestens
fünf Synapsen zählt. Die Transmitterwerte sind Vorhersagen. Die Koordinaten in
der Annotation sind 4×4×40-nm-Voxel; die Synapsenkoordinaten in Zenodo sind nm.

Die Summen der regionalen Ein- und Ausgangszählungen sollten der Gesamtzahl der
Einzel-Synapsen entsprechen. Der gegengelesene Kanten-Subset hat weniger Synapsen,
weil die Einzel-Synapsentabelle auch nicht gegengelesene Partner enthält.
Abweichungen werden im JSON ausdrücklich ausgewiesen; sie werden nicht
stillschweigend korrigiert.

Der Codex-Export `connections_princeton.csv.gz` ist ein **anderes Datenprodukt**
als die Original-Zenodo-Feather-Tabelle. Der Codex-Export wurde bereits auf
Neuronenpaare mit mindestens fünf Synapsen über alle Regionen gefiltert. Einzelne
Paar×Neuropil-Zeilen können dennoch nur eine Synapse enthalten. Der abgeleitete
Graph kombiniert diese Zeilen zu einer gerichteten Kante pro Paar. Seine sechs
Transmitterkanäle sind nach Synapsenzahl gewichtete Anteile kategorischer
Codex-`nt_type`-Labels, keine Original-Wahrscheinlichkeiten aus Zenodo.

Die [Morphologie-Dokumentation](https://zenodo.org/records/10877326) nennt
Nanometer als Einheit der Skelettkoordinaten. Ihre NBLAST-Scores wurden auf vier
Dezimalstellen gerundet und negative Werte bei 0 abgeschnitten. Der Analyzer
trennt MD5-Integrität, Schema, ID-Abdeckung und numerische Inhaltsprüfung.
Er scannt alle **erkannten** numerischen Spalten speicherbegrenzt, interpretiert
aber keine textuellen oder unbekannt verschachtelten SWC-Inhalte. Sind x/y/z
nicht als numerische Spalten erkennbar, bleibt der Morphologiebericht als
inhaltlich unvollständig markiert. Ein numerischer Vollscan beweist auch keine
vollständige topologische Konsistenz aller Skelette.
