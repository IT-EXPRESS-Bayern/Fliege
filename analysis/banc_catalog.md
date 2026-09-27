# BANC v888: abgeleitete Daten für eine spätere Körperkopplung

Stand: 26. September 2026. **BANC ist ein anderes adultes weibliches Tier als
FAFB v783.** Seine Root-IDs gehören zur BANC-Materialisierung 888 und dürfen
nicht mit FAFB-IDs gleichgesetzt oder als fehlendes Bauchmark derselben Fliege
angehängt werden. Die [Nature-Studie](https://doi.org/10.1038/s41586-026-10735-w)
beschreibt ein zusammenhängendes Gehirn und ventrales Nervensystem. Die statische,
zitierfähige Veröffentlichung liegt unter
[Harvard Dataverse DOI 10.7910/DVN/7WTH1N](https://doi.org/10.7910/DVN/7WTH1N)
(laut [Projektangaben](https://github.com/htem/BANC-project#license) **CC BY 4.0**).
Der [öffentliche GCS-Bucket](https://console.cloud.google.com/storage/browser/lee-lab_brain-and-nerve-cord-fly-connectome/)
erlaubt direkte Downloads, wird aber weiter aktualisiert. Alle folgenden
Bytegrößen stammen deshalb aus der öffentlichen GCS-Objektliste vom genannten
Stichtag; sie müssen nicht mit dem eingefrorenen Dataverse-Stand übereinstimmen.
Bei `banc_888_meta.feather` nennt die Papierdokumentation 51,45 MB,
der aktuelle GCS-Gegenstand dagegen 57,50 MB (laut Objektmetadaten zuletzt
am 21. August 2026 aktualisiert).
Die unveränderte, nur 31 KB große [GCS-Listing-Antwort](../data/banc_v888/gcs_compiled_data_listing.json)
für `compiled_data/banc_888/` liegt lokal; sie stammt aus der
[öffentlichen GCS-JSON-API](https://storage.googleapis.com/storage/v1/b/lee-lab_brain-and-nerve-cord-fly-connectome/o?prefix=compiled_data%2Fbanc_888%2F&delimiter=%2F&maxResults=1000).
Die Dataverse-API gab hier HTTP 403;
einzelne Dataverse-Datei-IDs und deren statische Bytegrößen sind daher nicht
verifiziert.

## Lokal geprüfter Referenzsatz

Die beiden kleinen Referenztabellen liegen unter `data/banc_v888/`:
`banc_fafb_reviewed_matches.csv` (6.581.434 Byte) und
`codex_annotations_flat_table_260520.csv` (39.303.076 Byte). Beide Dateien
wurden vollständig gegen die **offiziellen GCS-MD5-Werte** geprüft. Die
[Provenienzdatei](../data/banc_v888/reference_provenance.json) enthält außerdem
SHA-256, GCS-Objektgeneration, Abrufzeit und direkte Quell-URLs. Der
[Downloader](fetch_banc_reference.py) ist fortsetzbar und prüft vorhandene
Dateien erneut. Im Match-CSV stehen 64.372 Zeilen, davon 62.088 mit
`valid=t`; die flache Annotation enthält 158.265 Zeilen. Weitere große
BANC-Dateien wurden nicht heruntergeladen.

### DNa02 und DNg13: mehrdeutige Match-Liste

Die geprüfte Match-Liste ist **keine Eins-zu-eins-Abbildung**. Dieselbe
FAFB-ID kann in mehreren als gültig markierten Zeilen auftreten; einzelne
`query_id`-Werte kommen für beide Seiten vor oder sind im aktuellen flachen
Annotations-Export nicht mehr vorhanden. Für die vier FAFB-Kandidaten ergibt
die flache Annotation je eine BANC-Zeile mit passendem Zelltyp und passender
Seite:

| FAFB v783 ID | Typ, Seite | `valid=t`-Zeilen in Match-Liste | BANC v888 `pt_root_id` in flacher Annotation |
| --- | --- | ---: | --- |
| `720575940604737708` | DNa02, rechts | 3 | `720575941456897005` |
| `720575940629327659` | DNa02, links | 3 | `720575941510475536` |
| `720575940606112940` | DNg13, rechts | 2 | `720575941535086424` |
| `720575940616471052` | DNg13, links | 1 | `720575941445859754` |

Diese BANC-Zellen sind **Korrespondenzen in einem anderen Individuum**. Bei
diesen vier Zeilen sind `body_part_effector` und `cell_function` als `NA`
annotiert. Die Zuordnung belegt deshalb weder einen konkreten Muskel noch
eine kalibrierte Abbildung von Modell-Spikes auf Körperbewegung.

## Direkt ladbare Tabellen

Basis für die Links unten ist
`https://storage.googleapis.com/lee-lab_brain-and-nerve-cord-fly-connectome/`.
Die inhaltliche Beschreibung folgt der
[offiziellen Produktübersicht](https://github.com/htem/bancpipeline#released-data-products),
dem [Datei-Index](https://github.com/htem/BANC-project/blob/main/manuscript/print/banc_data_locations.md)
und der [Spaltendokumentation zur Metadaten-Tabelle](https://github.com/htem/BANC-project/blob/main/manuscript/print/dataverse/documentation/banc_888_meta.md).

| Datei (direkter Download) | GCS-Größe | Inhalt und Schlüssel | Nutzen |
| --- | ---: | --- | --- |
| [`banc_fafb_reviewed_matches.csv`](https://storage.googleapis.com/lee-lab_brain-and-nerve-cord-fly-connectome/nblast/banc_fafb_reviewed_matches.csv) | 6.58 MB | Manuell geprüfte BANC-`query_id` ↔ FAFB-`match_id`-Paare, `match_cell_type`, `valid`; beide IDs als Dezimalstrings behandeln. | Lokal geladen und geprüft; deckt nur geprüfte Matches ab und ist nicht zwingend eindeutig. |
| [`codex_annotations_flat_table_260520.csv`](https://storage.googleapis.com/lee-lab_brain-and-nerve-cord-fly-connectome/neuron_annotations/v888/codex_annotations_flat_table_260520.csv) | 39.30 MB | `pt_root_id`, `flow`, Zelltyp, `cell_function`, `body_part_sensory`, `body_part_effector`, `nerve`, `fafb_783_match_id` und weitere Match-IDs. | Lokal geladen und geprüft; Referenz für eine ausdrücklich hypothetische Sensor-/Motor-Zuordnung. Dateiname datiert den Export auf 2026-05-20. |
| [`banc_888_meta.feather`](https://storage.googleapis.com/lee-lab_brain-and-nerve-cord-fly-connectome/compiled_data/banc_888/banc_888_meta.feather) | 57.50 MB | Hauptmetadaten mit 79 Spalten: `banc_888_id` als String, `root_626/850/888`, `proofread`, `region`, Zelltyp, FAFB/MANC-Matches, `body_part_sensory`, `body_part_effector`, Funktion, Transmitter und Morphologiemetriken. | Bester vollständiger Index für gezielte Kopplung und Qualitätsfilter. Die [Papierdokumentation](https://github.com/htem/BANC-project/blob/main/manuscript/print/dataverse/documentation/banc_888_meta.md) nennt 188.162 **Segmente**, darunter unvollständig geprüfte und nichtneuronale Einträge; das ist keine Neuronenzahl. |
| [`banc_888_metrics.feather`](https://storage.googleapis.com/lee-lab_brain-and-nerve-cord-fly-connectome/compiled_data/banc_888/banc_888_metrics.feather) | 12.29 MB | Pro-Zelle-Kabellänge, Volumen, Synapsenzahlen, Mitochondrien und Axon/Dendriten-Trennung. | Schlanke morphologische Qualitätskontrolle; für Funktionsmapping allein nicht ausreichend. |
| [`banc_888_neurotransmitter_prediction_v2.csv`](https://storage.googleapis.com/lee-lab_brain-and-nerve-cord-fly-connectome/compiled_data/banc_888/banc_888_neurotransmitter_prediction_v2.csv) | 21.11 MB | Vorhersagen der Transmitter aus v2-Synapsen pro Neuron. | Ergänzt die Funktionszuordnung; vorhergesagte Chemie ist kein gemessener dynamischer Synapseneffekt. |
| [`codex_annotations.parquet`](https://storage.googleapis.com/lee-lab_brain-and-nerve-cord-fly-connectome/neuron_annotations/v888/codex_annotations.parquet) | 74.35 MB | Kuratierte BANC-Annotationen für FlyWire Codex. | Alternative zur flachen CSV, wenn Parquet-Werkzeuge vorliegen. |
| [`peripheral_nerves.parquet`](https://storage.googleapis.com/lee-lab_brain-and-nerve-cord-fly-connectome/neuron_annotations/v888/peripheral_nerves.parquet) | 0.63 MB | Bezeichnungen/Seed-Ebenen der peripheren Nerven. | Kleine Ergänzung, um sensorische Ein- und motorische Austritte anatomisch zu prüfen. |
| [`neck_connective_y92500.parquet`](https://storage.googleapis.com/lee-lab_brain-and-nerve-cord-fly-connectome/neuron_annotations/v888/neck_connective_y92500.parquet), [`neck_connective_y121000.parquet`](https://storage.googleapis.com/lee-lab_brain-and-nerve-cord-fly-connectome/neuron_annotations/v888/neck_connective_y121000.parquet) | 0.14 / 0.09 MB | Zwei Halskonnektiv-Seed-Ebenen. | Anatomische Kontrolle für auf- und absteigende Zellen, keine Bewegungsfunktion. |
| [`banc_888_edgelist_simple_v2.feather`](https://storage.googleapis.com/lee-lab_brain-and-nerve-cord-fly-connectome/compiled_data/banc_888/banc_888_edgelist_simple_v2.feather) | 305.25 MB | Papier-Verbindungsliste: `pre`, `post` als **Strings**, `count`, `norm`, `post_count`, `pre_count`; 11.510.975 gerichtete Zellpaare laut [Schema](https://github.com/htem/BANC-project/blob/main/manuscript/print/dataverse/documentation/banc_888_edgelist_simple_v2.md). | Späterer zusammenhängender Gehirn–Bauchmark-Graph. v2 berücksichtigt Synapsen mit detektierter Größe ≥5 Voxeln; es gibt **keine** globale Mindestzahl von Synapsen pro Zellpaar in der Datei. |
| [`banc_888_edgelist_simple_v3.feather`](https://storage.googleapis.com/lee-lab_brain-and-nerve-cord-fly-connectome/compiled_data/banc_888/banc_888_edgelist_simple_v3.feather) | 359.16 MB | Alternativer v3-Synapsendetektor (Größe ≥10 Voxel), gleiches Zellpaar-Schema. | Nicht mit v2-Zahlen mischen; die Nature-Auswertungen verwendeten v2. |
| [`banc_888_edgelist_split_v2.feather`](https://storage.googleapis.com/lee-lab_brain-and-nerve-cord-fly-connectome/compiled_data/banc_888/banc_888_edgelist_split_v2.feather) | 847.55 MB | Verbindungen nach Axon-, Dendriten- und weiteren Kompartimenten getrennt. | Später relevant für gerichtete physiologische Regeln. |

Die vollständige morphologische BANC↔FAFB-Ähnlichkeitstabelle
[`banc_fafb_783_nblast.feather`](https://storage.googleapis.com/lee-lab_brain-and-nerve-cord-fly-connectome/nblast/banc_fafb_783_nblast.feather)
ist öffentlich (578.41 MB). Sie ist für unklare Matches interessant, aber für
einen ersten Kopplungsversuch erheblich größer als die 6.58-MB-Tabelle der
geprüften Zuordnungen.

## Morphologie ohne EM-Bilder

Einzelne L2-Skelette sind im öffentlichen GCS-Verzeichnis
[`compiled_data/banc_888/banc_banc_space_swc/`](https://console.cloud.google.com/storage/browser/lee-lab_brain-and-nerve-cord-fly-connectome/compiled_data/banc_888/banc_banc_space_swc)
als `{banc_root_id}_l2.swc` oder `{banc_root_id}_skeleton.swc` erhältlich,
zum Beispiel
[`720575941263393328_l2.swc`](https://storage.googleapis.com/lee-lab_brain-and-nerve-cord-fly-connectome/compiled_data/banc_888/banc_banc_space_swc/720575941263393328_l2.swc)
(414 Byte) und
[`720575941500212603_skeleton.swc`](https://storage.googleapis.com/lee-lab_brain-and-nerve-cord-fly-connectome/compiled_data/banc_888/banc_banc_space_swc/720575941500212603_skeleton.swc)
(6,45 MB). Das Verzeichnis hat sehr viele Einzelobjekte; Größe und Qualität
variieren je Neuron. Kompartimentierte Skelette liegen unter
[`banc_banc_space_split_swc/`](https://console.cloud.google.com/storage/browser/lee-lab_brain-and-nerve-cord-fly-connectome/compiled_data/banc_888/banc_banc_space_split_swc),
etwa [`720575941330393199_split.swc`](https://storage.googleapis.com/lee-lab_brain-and-nerve-cord-fly-connectome/compiled_data/banc_888/banc_banc_space_split_swc/720575941330393199_split.swc)
(13.45 KB). Für eine Anwendung sollten nur nach Metadaten und Match
ausgewählte Skelette geladen werden. Die Projektübersicht nennt auch
Neuron-Meshes und Color-MIPs im Dataverse-Deposit; für diese Archive konnte
hier keine direkte öffentliche Datei-ID samt aktueller Größe verifiziert
werden. EM-Bildvolumen gehören ausdrücklich nicht zu diesem Katalog.

## Entscheidung für den nächsten Schritt

1. Die lokal geprüften FAFB↔BANC-Matches und die flache BANC-Annotation
   erlauben es, bekannte FAFB-DNs auf BANC-Zellen zu beziehen und
   BANC-Sensor-/Effektorgruppen über `body_part_*`, `cell_function`, `flow`
   und `nerve` bestimmen. Die Tabellen belegen Anatomie und Annotationen;
   eine Formel von Spikes zu Körperbewegung muss separat als Modellannahme
   ausgewiesen werden.
2. Für eine vollständige dynamische Gehirn–Bauchmark-Simulation anschließend
   den v2-Edgelist und die BANC-Metadaten verwenden. Die
   [Nature-Studie](https://www.nature.com/articles/s41586-026-10735-w)
   zeigt lokale Sensor-Effektor-Schleifen und auf-/absteigende Steuerwege.
3. Morphologie nur selektiv per BANC-ID nachladen. BANC enthält laut Studie
   Lamina und Ocellarganglion nicht vollständig; visuelle Eingaben brauchen
   daher zusätzlich eine ausdrücklich vereinfachte Modellgrenze.

Die spätere Anwendung muss BANC-v888-IDs (als Dezimalstrings) und
FAFB-v783-IDs getrennt führen; ein geprüfter Match ist eine
zellübergreifende Korrespondenz zwischen **zwei Tieren**, keine Identität.
