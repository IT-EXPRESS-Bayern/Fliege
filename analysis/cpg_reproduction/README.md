# Kontrollierte Nachrechnung des CPG-Ratenmodells

## Zweck und Reichweite

Dieser Ordner prüft, ob **konstanter** Eingang in das originale BANC-Teilnetz von Pugliese und Kollegen zeitlich veränderliche Motorantworten erzeugt. Der Eingang enthält keine vorgegebene Schrittfolge. Ruhe, DNg100-Antrieb sowie die Entfernung von E1, E2 und I2 werden mit denselben Zellparametern verglichen. DNb08 wird als gesonderte Zellidentitätskontrolle untersucht.

Dies ist eine **Nachrechnung der Modellgleichungen mit dokumentierter CPU-Portierung**, keine Replikation eines bestimmten publizierten Laufs und kein Nachweis einer biologisch autonomen Fliege. Das Teilnetz enthält 4.963 Zellen aus BANC und insbesondere vordere Beinregionen. Es ist weder das FAFB-Gehirn noch ein vollständig geschlossenes Gehirn-Körper-Sinnes-System.

## Quellen

- [Originalcode, festgehaltener Commit](https://github.com/smpuglie/Pugliese_2026/tree/10e7661bf414ba7b4c2edf795cd36d0f878c17c0): Modellgleichung, Zufallssampling, Größenkorrektur und Rhythmisierungsmaß.
- [Originaler Präprint, Version 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13142387/): biologisches DNg100-Experiment und rechnerische CPG-Hypothese. Noch kein experimenteller Nachweis der vorausgesagten E1/E2-Notwendigkeit.
- [Archiv der Simulationen](https://doi.org/10.5281/zenodo.22260924): die tatsächliche Konfiguration von Lauf **33241778** und die gespeicherten Zellparameter von **Replikat 0** liegen lokal vor. Sie wurden per Range ohne das vollständige Archiv geladen. Die gespeicherten Referenztrajektorien wurden noch nicht verglichen.

Wissenschaftliche Quelldateien liegen unter `data/research_sources/other/pugliese_cpg_2026/`. Matrix, Tabelle und Code wurden über den sichtbaren Browser beschafft; nach Freigabe direkter Downloads wurden die archivierten Laufkonfigurationen per HTTP-Range geladen. Dieser Runner lädt keine Daten aus dem Netz. Die gesonderte Python-Umgebung verwendet gewöhnliche PyPI-Bibliotheken.

## Gleichung und Provenienz

Für eine Zelle gilt `dR/dt = (max(r_cap*tanh((a/r_cap)*(I + W_eff@R - threshold)),0)-R)/tau`.

- Die gelieferte Matrix hat **Präzelle in der Zeile**, Postzelle in der Spalte. Die Dynamik verwendet ihre Transponierte.
- Bereits gespeicherte Vorzeichen bleiben erhalten. Bei ACh, GABA und Glutamat stimmen sie mit `neurotransmitter_verified`, ersatzweise `neurotransmitter_predicted`, überein.
- Originaldefaults skalieren positive und negative Gewichte jeweils mit 0,03. Dies sind Modellparameter, keine gemessenen Muskelkräfte.
- Gain und Schwelle werden wie im Original durch median-normalisierte Zelloberfläche geteilt beziehungsweise damit multipliziert; fehlende/Null-Flächen erhalten den Quellmedian.
- Der originale JAX-Rhythmisierungs-Score wird aus der lokal unveränderten Quelldatei importiert. Die Hauptserie verwendet die **gespeicherten Parameter von Originalreplikat 0**, ohne neue Zufallsziehung oder erneute Größenkorrektur. Als explizite Alternative kann der Runner eine eigene Ziehung aus dem originalen JAX-Sampler erzeugen; diese ist nicht identisch zur gespeicherten Serie mit 1.024 Wiederholungen.
- Die CPU-Portierung verwendet SciPy RK45, einen Dormand-Prince-Solver mit eigener adaptiver Schrittsteuerung, und float64-Zustände. Der originale Runner verwendet Diffrax Dopri5 und float32. Ein direkter Ableitungsvergleich mit den originalen Funktionen und eine engere Toleranznachrechnung prüfen die Portierung.
- Es werden keine fehlenden Synapsen ergänzt, keine Gewichte an eine gewünschte Bewegung angepasst und keine fehlgeschlagenen Kontrollbedingungen unterdrückt.

## Wichtiger Fehler in der originalen Auswertetabelle

156 Zeilen haben einen Eintrag in `motor module`. **27 davon sind laut derselben Tabelle keine bestätigten Motorzellen**: sämtliche Zeilen mit `tarsus control`, darunter aufsteigende, absteigende, intrinsische, Glia- und unklassifizierte Zellen. Die originale Notebook-Auswertung wählt über `motor module.notna()` aus und würde diese mit erfassen.

Deshalb werden beide Masken separat ausgewertet:

1. **Originalmaske:** alle 156 Modulzeilen, um die Methode nachvollziehbar zu halten.
2. **Konservative Motormaske:** 129 Modulzeilen mit `super_class=motor`. Nur diese werden für mögliche Körperadapter exportiert.

Die Quelldatei bleibt unverändert. Die 27 Konflikte werden als CSV exportiert. Auch die konservative Maske bestätigt noch keine Kraftkennlinie oder Muskelwirkung im Körpermodell.

Die 129 konservativen Motorzellen passen zu 128 von 391 IDs im vorhandenen BANC-Beinatlas. Die Quell-ID `720575941651501585` fehlt dort und wird nicht automatisch durch eine vermeintliche Nachfolge-ID ersetzt. Die ursprüngliche `fullData.csv` wurde mit `consistentColumns.csv` über sämtliche 4.963 Zeilen verglichen: alle 32 gemeinsamen Spalten sind identisch; letztere ergänzt nur `predictedNt` und `class`.

## Exakte Zellidentitäten

| Rolle | Matrixindex | BANC-ID | Typ |
|---|---:|---|---|
| DNg100 mit Ziel links, Soma rechts | 1605 | 720575941500851362 | DNg100 |
| E1 vorne links | 1689 | 720575941504247575 | IN17A001 |
| E2 vorne links | 910 | 720575941469024064 | INXXX466 |
| I2 vorne links | 3334 | 720575941569601650 | IN19A007 |
| I1 vorne links | 2708 | 720575941544954556 | IN16B036 |

`removeNeurons` entfernt im Original Zeile und Spalte der betreffenden Zelle. Die Portierung führt dieselbe Intervention nur an einer Arbeitskopie aus. Sie ist keine Aussage darüber, wie biologische optogenetische Hemmung jede Synapse beeinflusst.

## Ausführung

Im Projektordner mit PowerShell:

```powershell
& analysis/cpg_reproduction/.venv/Scripts/python.exe analysis/cpg_reproduction/run.py --input-amplitude 400 --seed 129 --label run33241778_replicate0 --run-config data/research_sources/other/pugliese_cpg_2026/run33241778/logs/run_config.yaml --parameter-file data/research_sources/other/pugliese_cpg_2026/run33241778/original_parameters_replicate0.npz
```

Die tatsächliche BANC-Konfiguration verwendet **400 willkürliche Einheiten**, Seed **129**, Matrix **W_20260217.npz** und 1.024 Replikate. Die früher erwogene Eingangsgröße 250 stammt aus einem MANC-Beispiel und wird hier nicht als BANC-Originalparameter ausgegeben. Die lokale Hauptserie benutzt die gespeicherten Parameter des ersten Replikats; das Programm kennzeichnet den Solverunterschied weiterhin ausdrücklich.

Der extrahierte Parameterdatensatz hat SHA256 `4658a080dd5e9313056f4a60c82f5937e836b59f4523875829689e86231560a9`. Nur 3.082.270 Bytes wurden für die abschließende Extraktion übertragen. Einzelne Datenbereiche und die extrahierten Werte sind gehasht; der Gesamt-CRC der nicht vollständig geladenen HDF5-Datei und die MD5 des vollständigen ZIP wurden nicht geprüft. Die detaillierte Herkunft steht bei den Quelldateien in `run33241778/original_parameter_extract_provenance.json`.

Die Bedingungsfolge ist vor der ersten Simulation eingefroren: `zero`, `dng100`, `e1_removed`, `e2_removed`, `i2_removed`, `dnb08_pair`, `dng100_repeat`, `dng100_tighter`. Alle verwenden denselben Parametersatz. DNb08 erhält pro Zelle dieselbe Stromgröße; da zwei Zellen angeregt werden, ist der gesamte externe Eingang doppelt so groß und kein mengenabgeglichener Test.

## Dateien nach erfolgreichem Lauf

- `protocol.json`: tatsächlich benutzte Parameter, Quelle, Abweichungen und Interventionen.
- `input_audit.json` / `audit.json`: Hashes, exakte Identitäten, Vorzeichenprüfung, Laufumgebung und Ausgaben.
- `sampled_parameters.npz`: unveränderte Zellparameter für sämtliche Gegenproben.
- `*_rates.npz`: vollständige kontinuierliche Zeitreihe sämtlicher 4.963 Zellen im 1-ms-Raster; `root_ids` sind Strings.
- `summary.json`: Resultate jeder Bedingung einschließlich numerischer Diagnose.
- `motor_readout_statistics.csv`: beide Masken, Zelltypen, Aktivität und originaler Rhythmisierungs-Score.
- `original_module_annotation_conflicts.csv`: die 27 problematischen Quellzeilen.
- `replay.json`: 2-ms-Replay der sechs fest benannten Readouts und 129 konservativen Motorzellen, in abstrakten Raten-Hz.

Rhythmische Raten sind keine Spikes. Ein Körperadapter benötigt eine gesonderte, transparent deklarierte Kalibrierung. Der 2-s-Lauf enthält keine Sinnesrückkopplung, kein Gleichgewicht, keine Motivation und keinen Lernmechanismus. In Ruhe bei Nullinitialisierung und ohne Eingang ist Nullaktivität die analytisch erwartete Lösung dieses Modells.
