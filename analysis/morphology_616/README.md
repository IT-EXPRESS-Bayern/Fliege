# FlyWire-v783-Skelettprüfung für 616 bisher kantenlose FAFB-Neuronen

Stand: 27. September 2026. Diese Prüfung betrifft die **anatomische Skelettdatei**, nicht eine neue Synapsenrekonstruktion. Die 616 IDs stammen aus `data/research_sources/derived/model_missing_fafb_ids.csv`; die 195 Prioritätsfälle aus `analysis/reconstruction_candidates_v783/princeton_strata.json` sind die IDs ohne Buhmann-Rohpunkt, aber mit Princeton-2025-Punktbefund.

## Quelle und Reproduktion

- Offizielle Quelle: [Schlegel et al., Nature 2024, Zusatzdaten auf Zenodo](https://zenodo.org/records/10877326), `sk_lod1_783_healed_ds2.parquet`, 5.355.543.468 Byte, veröffentlichtes MD5 `a4c104776f33ec539ef859064c4de3df`, Lizenz CC BY 4.0. Der lokale `zenodo_record.json` enthält dieselben Dateiangaben. Das MD5 wurde in diesem Prüflauf erneut gegen die gesamte lokale Datei berechnet und stimmte überein.
- Reproduzieren aus dem Arbeitsordner: `analysis\.venv\Scripts\python.exe analysis\morphology_616\scan.py --verify-md5`. Der vollständige Scan liest 268.281.651 Parquet-Zeilen aus vier Row-Groups in Batches von standardmäßig 262.144 Zeilen. Ein zweiter Scan mit `--batch-size 65536 --verify-md5` ergab byteidentische `coverage_616.csv`- und `point_distance_exemplars.csv`-Ergebnisse. Nur drei Beispielskelette werden als vollständige Knotenlisten gehalten.
- `coverage_616.csv`: eine Zeile pro FlyWire-Root, mit Knotenanzahl, Wurzelknoten, Radiuswerten, Minima/Maxima und Bounding-Box-Ausdehnung in Nanometern bzw. Mikrometern.
- `review_priority_616.csv`: R7 zuerst, danach die 195 Princeton-only-IDs nach Zahl der Princeton-Einzelpunktzeilen, anschließend die restlichen IDs. Die Reihenfolge ist eine **Arbeitsreihenfolge**, keine Synapsenwahrscheinlichkeit.
- `geometry_extremes.csv`: 21 IDs in den unteren oder oberen 1 % der beobachteten Knotenanzahl beziehungsweise Bounding-Box-Diagonale. Diese dateninternen Verteilungsschwänze sind Prüfhinweise, keine biologischen Fehlerdiagnosen.
- `point_distance_exemplars.csv`: Koordinatenabstände der zugeordneten Einzelpunkte zum nächsten Skelettknoten und zum nächsten Skelettsegment, nur für R7 und zwei Princeton-only-IDs.
- `audit.json`: maschinenlesbare Gesamtzahlen, Einheiten, Extremwertschwellen und Beispielprüfungen.

## Befunde

| Prüfung | Ergebnis |
|---|---:|
| IDs mit Eintrag in Parquet-Metadaten | 616 / 616 |
| IDs mit mindestens einem tatsächlichen Skelettknoten | 616 / 616 |
| Princeton-only-IDs mit Skelettknoten | 195 / 195 |
| Knoten der 616 IDs insgesamt | 151.369 |
| Knoten je ID | Median 238,5; Spanne 13–1.353 |
| Bounding-Box-Diagonale je ID | Median 42,258 µm; Spanne 3,039–173,829 µm |
| Wurzelknoten mit `parent_id = -1` | genau einer je ID |
| Nicht endliche Koordinaten oder negative Radiuswerte | 0 |
| Radiuswerte 0 | 16.423 / 151.369 (10,85 %) |

Die Metadaten geben für alle 616 Skelette `1 nanometer` als Einheit an. Die 0-Radiuswerte sollten nicht als tatsächliche dünne biologische Fortsätze ausgelegt werden; für Dickenanalysen ist eine Prüfung der Erzeugungsmethode beziehungsweise des Rohvolumens nötig. Auch ein Skelett mit nur 13 Knoten (R1-6 `720575940629888515`, Diagonale 3,039 µm) ist lediglich ein Kandidat für eine Trunkierungsprüfung. Die größte Diagonale hat R8 `720575940632280338` mit 173,829 µm. Die Größen werden weder an einem zelltypspezifischen Erwartungswert noch am Roh-EM validiert.

**R7 `720575940623940963`:** 311 Knoten, ein Wurzelknoten, 310 auflösbare Eltern-Kind-Segmente, keine doppelten Knoten-IDs und keine fehlenden Elternreferenzen. Die Skelettkabellänge beträgt 188,641 µm; die Bounding-Box-Diagonale 132,856 µm. Diese Verbindungen sind Äste **innerhalb desselben Neurons** und keine Kanten zu anderen Neuronen.

## Exemplarischer Koordinatenabgleich

Zum Koordinatentest wurden für jedes zugeordnete Einzelpunktereignis die Koordinaten der jeweiligen Prä- oder Postsynapsenseite verwendet. Ein Self-Call kann deshalb zwei eigene Punktkoordinaten ergeben. Der Abstand wird zum nächsten Liniensegment des ausgedünnten Skeletts berechnet; ein Punkt entlang eines Segments ist näher als dessen Endknoten. Die drei geprüften Skelette haben eindeutige Knoten-IDs und vollständige Elternreferenzen.

| FlyWire-ID | Quelle | Eigene Punktkoordinaten | Median Segmentabstand | Bis 1 µm |
|---|---|---:|---:|---:|
| R7 `720575940623940963` | Buhmann-v783-Rohpunkte | 69 | 0,618 µm | 67 / 69 |
| R7 `720575940623940963` | Princeton-2025-Einzelpunkte | 217 aus 215 Zeilen | 0,466 µm | 205 / 217 |
| `720575940609016668` (Princeton-only) | Princeton-2025-Einzelpunkte | 219 | 0,382 µm | 219 / 219 |
| `720575940631647173` (Princeton-only) | Princeton-2025-Einzelpunkte | 242 | 0,346 µm | 242 / 242 |

Die Größenordnung unter 1–2 µm ist mit einem gemeinsamen FAFB-Nanometerkoordinatenraum **vereinbar**. Sie bestätigt nur, dass die eigenen Punktkoordinaten nahe der groben Anatomie des zugeordneten Neurons liegen. Sie ist keine unabhängige Bestätigung des Partnersegments: Die Punktdateien selbst nennen bereits die Root-ID, und ein ausgedünntes Skelett zeigt weder synaptische Kontaktflächen noch EM-Ultrastruktur. Die Abstände dürfen daher nicht als Nachweis einer Synapse, einer Richtung oder einer Verbindungsstärke benutzt werden. Princeton-2025 und Buhmann-v783 sind unterschiedliche automatisierte Detektoren; ihre Punktzahlen sind nicht direkt gleichzusetzen.

## Was dieser Datensatz für das Fliegenmodell leistet

Die Datei liefert eine kompakte Geometrie für **alle** 616 bislang im Modell kantenlosen FlyWire-v783-IDs. Damit lassen sich Zellen im Browser räumlich platzieren und die intraneuronale Verzweigung anzeigen. Kleine oder ungewöhnlich ausgedehnte Skelette können gezielt für eine zusätzliche Segmentierungsprüfung vorgemerkt werden. Die Parquet-Spalten `node_id` und `parent_id` beschreiben nur die Skelettstruktur **einer** Root-ID. Aus ihrer Nähe zu einem anderen Skelett darf keine interzelluläre Kante ergänzt werden; dafür sind überprüfte Synapsenpunkte und möglichst EM-Bildkontrolle erforderlich.

Die LOD1-/Downsampling- und `healed_ds2`-Bezeichnungen kennzeichnen eine verarbeitete, vereinfachte Morphologie. Der Scan prüft die interne Baumstruktur vollständig nur für die drei Beispielzellen; für die übrigen 613 werden Knotenanzahl, Root-Sentinel und Geometrie geprüft. Eine Aussage über vollständige Zellfortsätze, korrektes Merge/Split-Verhalten, chemische Synapsen oder elektrische Aktivität ist damit nicht möglich.
