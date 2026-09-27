# R7-Fallstudie: Skelett und zwei Synapsendetektoren

Stand: 27. September 2026. Untersucht wird die offizielle FAFB-v783-Root-ID **720575940623940963**, annotiert als rechtes R7-Photorezeptorneuron. Die [interaktive 3D-Ansicht](http://127.0.0.1:4173/skeleton.html) zeigt das Original-Skelett und fünf benannte Partnerzellen: Dm9, Dm8, Dm11, L3 und Tm20. Jede Ebene lässt sich einzeln schalten; ein Klick auf einen goldenen oder pinken Punkt zeigt Richtung, Partner-ID, Region und Quellkennung.

Das R7-Skelett hat **311 Knoten und 310 innere Segmente**. Es stammt aus dem MD5-verifizierten, ausgedünnten `sk_lod1_783_healed_ds2.parquet` des [offiziellen Morphologiearchivs](https://zenodo.org/records/10877326). Die [separate Morphologieprüfung](../morphology_616/README.md) findet für R7 188,641 µm aufsummierte Skelettlänge. Ein solcher Skelettbaum beschreibt Äste innerhalb eines Neurons; `parent_id` ist keine Verbindung zu einem anderen Neuron.

| Befund | Älterer Buhmann-Punktexport | Neuerer Princeton-Punktexport |
|---|---:|---:|
| Nicht-selbstbezogene R7-Punkte mit zwei geprüften Partnern | 48 | 213 |
| Gerichtete Neuronenpaare × Hirnregion | 21 | 45 |
| Zusätzliche Selbstkontakte in dieser Auswertung | 0 | 2 |
| Im jeweiligen veröffentlichten Paargraphen enthaltene R7-Kanten | 0 | 0 |

**18 der 21 älteren Paar/Region-Schlüssel** erscheinen auch im Princeton-Punktexport. Diese 18 Schlüssel enthalten 45 der 48 alten Einzelpunkte; die drei übrigen alten Schlüssel haben hier keinen neuen Gegenbefund. Die Übersicht [r7_pair_point_comparison.csv](r7_pair_point_comparison.csv) bewahrt die beiden Detektor-Zählungen separat. Die Gesamtzahlen dürfen nicht addiert werden, weil beide Verfahren dieselbe Anatomie untersuchen.

Für jeden alten Punkt wird innerhalb desselben gerichteten Neuronenpaares und derselben Region der nächstgelegene neue Punkt gesucht. Der Abstand ist die Wurzel aus dem Mittel der quadrierten 3D-Abstände des Prä- und Postsynapsenorts. Von den 45 alten Punkten mit einem passenden Paar liegen **13 innerhalb von 100 nm, 36 innerhalb von 250 nm, 41 innerhalb von 500 nm und 43 innerhalb von 1.000 nm** zu ihrem nächsten Princeton-Aufruf. Der Median beträgt 121,951 nm; der größte Abstand 2.643,775 nm. Kein Paar stimmt in allen sechs Koordinaten exakt überein. Die 45 alten Punkte wählen 43 verschiedene neue Aufrufe, weil diese Suche keine eindeutige Eins-zu-eins-Zuordnung erzwingt. Die vollständige Liste steht in [r7_old_to_new_nearest_points.csv](r7_old_to_new_nearest_points.csv), die Prüfsummen und Methodik in [audit.json](audit.json).

Die räumliche Nähe ist ein nützlicher Prüfhinweis. Sie beweist weder, dass zwei Aufrufe dieselbe biologische Synapse meinen, noch eine physiologische Signalwirkung. Das Skelett ist ausgedünnt und beschreibt eine Mittellinie; der Abstand eines Punkts dazu ist daher ebenfalls kein Synapsennachweis.

Die Princeton-Punktdatei trägt das GCS-Datum **24. Juli 2025**, ihre Verbindungstabelle **8. Juli 2025**. Für alle 616 untersuchten IDs lässt sich ihre Differenz rechnerisch vollständig erklären: 26.941 Punkte = 20.914 Paargraph-Punkte + 5.814 Selbstkontakte + 213 nicht-selbstbezogene R7-Punkte. Nach dieser empirischen Trennung und der Regionslabel-Zuordnung Leerfeld→`UNASGD` stimmen alle übrigen 3.233 Paar/Region-Schlüssel exakt überein. **Warum R7 aus den Paargraphen ausgeschlossen wurde, ist weiterhin ungeklärt.** Der [vollständige Abgleich](../reconstruction_candidates_v783/princeton_point_exclusion_audit.json) dokumentiert diesen Befund.

Die 3D-Ansicht verwendet für ältere Aufrufe den Mittelpunkt zwischen Prä- und Postsynapsenort und für Princeton die veröffentlichte `ctr_*`-Position. Diese Darstellung ist eine gemeinsame räumliche Ansicht, keine Gleichsetzung der beiden Koordinatendefinitionen. Zur Anzeige werden Nanometer in Mikrometer umgerechnet und um die R7-Bounding-Box-Mitte verschoben; Root-IDs bleiben Zeichenketten. [Export-Audit](skeleton_view_audit.json).

Reproduzierbar im Arbeitsordner:

```powershell
& analysis/.venv/Scripts/python.exe analysis/r7_case_study/compare_r7_points.py
& analysis/.venv/Scripts/python.exe analysis/r7_case_study/export_skeleton_view.py
```

Quellen: [FlyWire v783 Originalpunkte](https://zenodo.org/records/10676866), [FlyWire v783 Morphologie](https://zenodo.org/records/10877326), [Yu et al. 2025 – Princeton-Synapsendetektor](https://doi.org/10.1101/2025.07.11.664377), [Codex-Datenexport](https://codex.flywire.ai/api/download?dataset=fafb). Die Quelldateien wurden lokal gegen die veröffentlichten Prüfsummen geprüft.
