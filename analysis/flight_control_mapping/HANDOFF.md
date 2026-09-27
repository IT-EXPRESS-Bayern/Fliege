# Checkpoint für weitere Arbeit in der Cloud

Stand 27.09.2026. Diese Dateien liegen im lokalen Arbeitsordner; dieser Checkpoint bestätigt keine Cloud-Übertragung.

## Fertig und überprüft

- `app/data/flight_control_mapping.json`: 3.880.543 Bytes, SHA256 `847727439ddb7afe9723c9c099f4fcc681888d0f695f96c864c43e5d289812fd`. Zwei Builderläufe ergaben exakt dieselben Bytes.
- `analysis/flight_control_mapping/build.py`: erzeugt Inventare, vollständige begrenzte Pfad-Parquets, Browserdaten, Quell-/Kanten-Audit und FlyBody-Auszug. Alle Browserkontakte wurden erneut am jeweiligen v2/v3-Graphen geprüft.
- `analysis/flight_control_mapping/{README.md,sources.json,gaps.json,audit.json,flybody_mechanics.json}`: wissenschaftliche Bedeutung, Quellen, Grenzen und tatsächliche Hashes.
- `analysis/flight_control_mapping/{motor_inventory.csv,sensory_inventory.csv,dn_candidates.csv,visual_candidates.csv,annotation_conflicts.csv,source_side_vs_effector_side.csv}`: exakte IDs als Dezimaltext. 91 Motorzeilen; sechs Konflikte; 85 anatomische Poolkandidaten; 244 proofread Propriozeptoren. 24 Wing-Power-Motoren und 24 Steering-Motoren; keine individuelle Kraft-/Drehmomentkalibrierung.
- `analysis/flight_control_mapping/{paths_v2.parquet,paths_v3.parquet,edges_v2_at5.parquet,edges_v3_at5.parquet,visual_two_edge_paths_v2.parquet,visual_two_edge_paths_v3.parquet}`: alle Pfade dieses definierten Ausschnitts; keine Mischung alternativer Detektoren. Browser-Motorpfadbeispiele sind gekürzt.
- `analysis/sensorimotor_mapping/` und `app/data/sensorimotor_mapping.json`: FeCO-LF-Anatomie; eigener kontinuierlicher Sensor-Motor-Kreis in `app/sensorimotor_model.mjs`. Audit `app/data/sensorimotor_audit.json`: 194 Versuche, 24 Transferproben, technische Prüfungen bestanden; keine biologische Kalibrierung.
- `analysis/cpg_reproduction/run33241778_replicate0/`: acht abgeschlossene CPU-Kontrollbedingungen mit unveränderten archivierten Originalparametern von Replikat 0. `analysis/cpg_reproduction/result_verification.json`: 57 Ergebnisprüfungen bestanden. Original-Quellgraph ist ein 4.963-Zell-Beinteilnetz; seine ~15-Hz-Rhythmik ist keine Wingbeat-Frequenz.
- `analysis/update_model_integration_pack.py`, `analysis/model_integration_pack.json/.md` und `analysis/research_session_status.json`: registrieren Anatomie, Quellen und Nachrechnung mit getrennten Evidenzschichten. Der Updater prüft lokal vorhandene Quell-/Ergebnishashes.
- `app/flight_model.mjs`, `app/flight_audit.mjs`, `app/tests/flight_model.test.mjs`, `app/FLIGHT_METHODS.md`, `app/data/flight_audit.json`: 26 Versuche und 432.000 Integrationsschritte eines reduzierten Rollprüfstands; 24 Power-Motor-IDs und zwei b1-Referenzen. 9 Kernprüfungen bestanden. Mechanische Selbstschwingung und technisches Rollfeedback; keine BANC-Sensorpfad-Dynamik oder freie Translation.
- `app/cpg.html/.js/.css`, `app/data/cpg_replay.json`, `app/data/cpg_viewer_audit.json`: acht Bedingungen, 135 Serien, 1.001 Werte je Serie, 1.081.080 Werte exakt aus den berechneten CPG-Läufen übernommen. Browser-Interaktionsprüfung bleibt ein gesonderter Hauptteam-Schritt.

## Zur Reproduktion mitzunehmen

1. Die genannten erzeugten Dateien, Scripts und gegebenenfalls den gesamten `app/`-Ordner für Browser-Tests.
2. Die originalen BANC-Quellen `data/research_sources/other/banc_2026/{banc_888_meta.feather,banc_888_edgelist_simple_v2.feather,banc_888_edgelist_simple_v3.feather,supplemental_data_9.txt}` samt Provenienz. Für reine Browseransicht genügen die exportierten JSONs; für unabhängige Neuberechnung nicht.
3. `data/research_sources/other/pugliese_cpg_2026/` mit sieben gepinnten Repository-Dateien, drei run33241778-YAMLs und dem gezielt extrahierten Parameter-NPZ samt Provenienzen. `analysis/cpg_reproduction/requirements-lock.txt` beschreibt die separate Laufzeit. Windows-`.venv` nicht als portable Cloud-Umgebung behandeln.
4. Die originalen FlyBody-Dateien, die `flybody_mechanics.json` mit Pfad und Hash aufführt. Sie ersetzen weder alle Modellassets noch eine eingerichtete MuJoCo-Laufzeit.

## Noch offen

- Der getrennte Flügel-Rollprüfstand ist technisch geprüft, bildet aber keinen freien Flug ab. Eine Browser-Oberfläche und vollständige Flugphysik gehören zu weiteren getrennten Schritten.
- Individuelle Sensorphase/-richtung, chemische Rezeptorwirkungen, elektrische Kopplung, Muskelkräfte, Thoraxresonanz, Aerodynamik und visuelle Pixel→Neuron-Abbildung sind nicht validiert.
- DLM5-Effektorseite folgt dem peripheren Nerv und ist gegenüber `sourceSide` gekreuzt; diese Trennung beim Laden bewahren.
- Original-CPG-Konfiguration und Replikat-0-Parameter sind vorhanden. Die ursprünglichen gespeicherten Trajektorien und alle 1.024 Originalreplikate wurden nicht nachgerechnet/verglichen. Die CRC des gesamten Parameter-HDF5 und die MD5 des gesamten ZIP sind nicht geprüft, weil nur Bereiche geladen wurden.
- Ein lokaler LF-Regelkreis und eine Bein-Teilnetz-Nachrechnung ergeben noch keine vollständige autonome Fliege. Gang, Start/Landung, Energie, Hunger/Fütterung, Schlaf und integrierte Umgebungssinne fehlen als validierter Gesamtregelkreis.
