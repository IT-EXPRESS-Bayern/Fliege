# Quellen, Rechte und wissenschaftlicher Umfang

## Externe Bestandteile

| Bestandteil | Festgestellter Hinweis | Herkunft |
|---|---|---|
| Three.js | MIT; Lizenztext liegt unter `app/vendor/THREE-LICENSE.txt` | [Three.js](https://github.com/mrdoob/three.js) |
| Shiu-Code | MIT, Philip Shiu und Nico Spiller, 2023; Lizenztext bleibt unter `references/shiu-source/LICENSE` | [Whole-brain simulation](https://github.com/philshiu/Drosophila_brain_model) |
| FlyWire-Datensatz 10676866 | CC-BY-4.0 laut Datensatz-API | [Zenodo](https://zenodo.org/records/10676866) |
| BANC v888 | CC-BY-4.0 laut archivierter Dataverse-Provenienz | [Dataverse](https://doi.org/10.7910/DVN/7WTH1N) |
| Pugliese-Modellmaterial | Repository-README erklärt MIT; am festgehaltenen Commit ist keine separate LICENSE-Datei vorhanden | [Commit 10e7661](https://github.com/smpuglie/Pugliese_2026/tree/10e7661bf414ba7b4c2edf795cd36d0f878c17c0) |
| Pugliese-Laufarchiv / Parameterextrakt | CC-BY-4.0 laut Datensatz-API; ausgewählte Konfigurationen und unveränderter erster Parametersatz, kein vollständiges Archiv | [Zenodo 22260924](https://zenodo.org/records/22260924) |

Urheber der CPG-Quelle sind Pugliese und Kollegen; der zugehörige [Präprint](https://doi.org/10.1101/2025.09.12.675944) und die genaue Datenherkunft sind in den CPG-Provenienzdateien verlinkt. Das öffentliche Projekt vergibt keine neue pauschale Lizenz für fremde Daten. Eigene Analysen, Nachrechnungen und Darstellungen sind vom unveränderten Originalmaterial unterscheidbar. Eigener Code wird unter MIT, eigene Dokumentation unter CC BY 4.0 veröffentlicht; [LICENSES.md](../../LICENSES.md) grenzt dies von fremden Rechten ab. Die spezifischen Zenodo-Metadaten und die abweichenden allgemeinen FlyWire-BY-NC-Bedingungen werden in der [aktuellen Lizenzprüfung](../../docs/publication/REUSE_AND_LICENSES.md) getrennt dokumentiert.

Der kleine CPG-Eingabeteil enthält Matrix, Tabellen und Konfigurationen mit exakten Prüfsummen. Die zwei unveränderten fremden Python-Quelldateien werden über ihre feste URL und SHA256 in `data/research_sources/other/pugliese_cpg_2026/provenance.json` referenziert und nicht erneut mitgeliefert. Sie werden für die originale JAX-Score-/Sampling-Funktion vor einer Nachrechnung benötigt. Andere Originaldatensätze werden ebenfalls an ihrer Quelle beschafft; eine öffentlich lesbare Quelle ist nicht automatisch eine allgemeine Lizenz für alle Bestandteile.

## Aussagegrenzen und negative Ergebnisse

- FAFB- und BANC-IDs bleiben unterschiedliche Tiere und Versionen; eine Typentsprechung erzeugt keine beobachtete Synapse zwischen den Datensätzen.
- Die Neuronenassays enthalten den dokumentierten JO-F-Spezifitätsfehler. Anatomische Erreichbarkeit und Modellantwort sind keine Bestätigung biologischer Funktion.
- Die CPG-Nachrechnung nutzt gespeicherte Parameter von Originalreplikat 0 mit einem dokumentierten CPU-Solver. Sie untersucht acht Bedingungen einschließlich Ruhe, E1/E2/I2-Entfernung und Identitätskontrolle. E1/E2-Entfernung unterdrückte das verwendete Rhythmuskriterium; I2-Entfernung nicht.
- Der CPG-Eingang ist ein äußerer tonischer Strom. Das Teilnetz ist keine autonome Ganzhirnfliege und besitzt noch keine kalibrierte Gelenk- oder Flugsteuerung.
- Gelenk-, Sensorimotor- und Flugmodelle deklarieren ihre mechanischen Annahmen. Gespeicherte Replays ersetzen keine biologische Validierung und keine laufende Cloudsimulation.

## Öffentliche Vorschau und Wiederholung

Die App kann mit `node app/server.mjs` lokal bereitgestellt werden. Die CPG-, Neuronen- und Motorreplays lesen die mitgelieferten `app/data`-Dateien. Umfangreiche Originalgraphen werden separat wiederbeschafft. Wissenschaftliche Simulationen werden nach dem Cloudwechsel ausschließlich in der dafür vorgesehenen Cloudumgebung fortgesetzt; dieses Veröffentlichungsskript startet keine Berechnungen.
