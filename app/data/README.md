# Herkunft und Nutzungsbedingungen der Browserdaten

Diese Dateien sind ausgewählte, umgeformte Daten und eigene Modellresultate. Sie sind
keine vollständige Kopie des biologischen Tieres. Die MIT-Lizenz des eigenen Codes
ist **keine** pauschale Datenlizenz.

| Dateien | Herkunft und Änderungen | Bedingungen |
|---|---|---|
| `banc_leg_motor_reference.json`, `motor_pathways.json`, `sensorimotor_mapping.json`, `flight_control_mapping.json` | Bates et al., *Distributed control circuits across a brain-and-cord connectome* (2026), BANC v888 / Dataverse v3.0; ausgewählte Zellmetadaten, normalisierte Felder und berechnete Wege; v2/v3 getrennt | [Datensatz](https://doi.org/10.7910/DVN/7WTH1N), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); Quellen-/Lizenzvermerk und Änderungen erhalten |
| `cpg_replay.json`, `cpg_viewer_audit.json` | Eigene Nachrechnung mit SciPy, Pugliese et al., Originalparametersatz Run33241778/Replikat0; keine archivierten Originaltrajektorien | Eigene Resultate CC BY 4.0; [Originaldaten](https://doi.org/10.5281/zenodo.22260924), [Modellcode](https://github.com/smpuglie/Pugliese_2026/tree/10e7661bf414ba7b4c2edf795cd36d0f878c17c0) zusätzlich nennen |
| `motor_joint_audit.json`, `sensorimotor_audit.json`, `flight_audit.json` | Eigene numerische Kontrollen mit anatomischen BANC-Identitäten; unkalibrierte Modellparameter | Eigene Resultate CC BY 4.0; BANC-Attribution erhalten |
| `brain-anchor-points*.json`, `neuron_catalog*.json` | FlyWire/FAFB-Annotationen und fachliche Quellen; Auswahl, Aggregation und Projektzuordnungen | Spezifische Quellrechte im [Register](../../docs/publication/source_registry.json); neuere FlyWire-Public-Release-Annotationen nach [FlyWire-Richtlinie](https://flywire.ai/guidelines) CC BY-NC 4.0 behandeln. Keine zusätzliche kommerzielle Freigabe oder pauschale Umlizenzierung |
| `r7_skeleton.json` | Ausgewählte Äste aus Schlegel et al., FAFB v783, plus separat gekennzeichnete Synapsenexporte | [Skeleton-Archiv](https://doi.org/10.5281/zenodo.10877326) nennt CC BY 4.0; Codex-/Princeton-Anteile unter jeweiliger FlyWire-CC-BY-NC-Bedingung erhalten |
| `neuron_assays.json`, `neuron_response_profiles.json`, `neuron_body_replay_audit.json` | Eigene Modellversuche/Replays auf FlyWire-Daten mit Shiu-Modellreferenz und Quellenannotation | Eigene Auswertung CC BY 4.0; fremde Zellmetadaten und Datengrundlage unter ihren ursprünglichen Bedingungen. [Methoden](../../analysis/neuron_assays/README.md) und [Quellen](../../docs/publication/SOURCES.md) |

Die genauen Bedingungen einzelner späterer Annotationstabellen und gemischter
Supplementbestandteile sind noch nicht vollständig geklärt. Die allgemeine
FlyWire-Richtlinie umfasst öffentlich freigegebene Klassifikationen und Community-
Labels; daraus wird hier keine Lizenz für beliebige externe Supplementtexte abgeleitet.
Eine Aussage über kommerzielle Nutzbarkeit dieser gemischten Kataloge ist damit nicht
verbunden. Details und widersprüchliche Zenodo-/Plattformangaben sind in der
[Lizenzprüfung](../../docs/publication/REUSE_AND_LICENSES.md) dokumentiert.

Originalautoren bestätigen weder die Projektauswahl noch die daraus gebauten Modelle.
Bei Weiterverwendung Originalquelle, Version, Lizenz und eigene Änderungen mitführen.
