# Wiederverwendung und Lizenzgrenzen

Geprüft am **27. September 2026**. Die Projektlizenz für eigenen Code und die Dokumentationslizenz gelten nur für die jeweils eigenen Beiträge. Originaldaten, übernommener Code, Modelle, Gewichte, Abbildungen und daraus abgeleitete Datentabellen behalten ihre jeweiligen Rechte und Namensnennungen. Eine öffentliche Downloadadresse ist keine eigenständige Lizenz.

**Eigener Code:** [MIT](../../LICENSE). **Eigene Dokumentation:** [CC BY 4.0](../LICENSE-CC-BY-4.0.txt). Maßgeblicher Geltungsbereich: [Lizenzzuordnung](../../LICENSES.md). Dies umfasst keine Umdeklaration fremder Originaldaten.

Das [vollständige Eingaberegister](source_registry.json) enthält alle 160 registrierten Dateien bzw. Datenprodukte und 46 Verknüpfungsregeln des Forschungsstands. `license_note` ist der historische Quellhinweis aus dem Integrationspaket, **keine pauschale Freigabe**. Die neu geprüfte Einordnung steht in `publication_license_assessment` und der folgenden Tabelle. Ein Registereintrag bedeutet nicht, dass seine Originaldatei im Git-Repository mitgeliefert wird.

## Quellenbezogene Lizenzprüfung

| Quelle / genaues Produkt | Festgestellte Regel und Nachweis | Umgang in diesem Projekt |
|---|---|---|
| FlyWire-Originalgraph v783.0, Zenodo 10676866 | Record-Metadaten: **CC BY 4.0**. [Originalrecord](https://zenodo.org/records/10676866), [Metadaten-API](https://zenodo.org/api/records/10676866). | Versionsgebundene Attribution erhalten. Zugleich den nachstehenden Konflikt mit den allgemeinen FlyWire-Richtlinien beachten. |
| Schlegel-Supplemente / Skeletons, Zenodo 10877326 | Record-Metadaten: **CC BY 4.0**. [Record](https://zenodo.org/records/10877326), [API](https://zenodo.org/api/records/10877326). | Diese konkrete Archivlizenz nicht automatisch auf spätere GitHub-Annotationen übertragen. |
| Princeton-Detektor und weitere Codex-/FlyWire-Downloads | Allgemeine offizielle [FlyWire-Richtlinie](https://flywire.ai/guidelines): **CC BY-NC 4.0**. | Konservativ als nichtkommerziell gebunden behandeln; nicht unter eigener MIT-/CC-BY-Lizenz umdeklarieren. |
| `flywire_annotations` v2.1.0 | In der geprüften [Release-/Repository-Ansicht](https://github.com/flyconnectome/flywire_annotations/releases/tag/v2.1.0) kein eigenständiger Lizenztext festgestellt. | Genaue Rechte der TSV und möglicher Fremdanteile offen. Veröffentlichungsfreigabe eines Mischkatalogs nicht aus einer anderen Archivversion ableiten. |
| BANC, Dataverse v3.0, CAVE v888 | **CC BY 4.0**, ausdrücklich im Dataverse-Datensatz, nicht nur im Fachartikel. [Datensatz](https://doi.org/10.7910/DVN/7WTH1N), [Metadaten](https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId=doi:10.7910/DVN/7WTH1N). | BANC-Teilgraphen und Tabellen mit Urheber-/Quellenangabe, Version, Lizenzlink und Änderungsvermerk veröffentlichen. v2/v3-Detektoren getrennt kennzeichnen. |
| MaleCNS v1.0, offizielle Flat-Connectome-Dateien | Offizielle [Downloadseite](https://male-cns.janelia.org/download/) verlinkt **CC BY 4.0**. | Berg et al. / FlyEM / beteiligte Institute, Version und Transformation nennen. Die Lizenz separater GitHub-Zusatzanalysen nicht ungeprüft gleichsetzen. |
| Shiu-Modellcode, Commit `91bdd1e7dcf193f3e7ca5a8933497fcef63b7960` | **MIT**, Copyright Philip Shiu und Nico Spiller; [Original-Lizenz](https://github.com/philshiu/Drosophila_brain_model/blob/91bdd1e7dcf193f3e7ca5a8933497fcef63b7960/LICENSE). | Übernommenen Code mit vollständigem Lizenztext behalten. Eingebettete Konnektomdaten und Verlagssupplemente separat zuordnen. |
| Eon `fly-brain`, Commit `a3db62f9436074e485c0278290c2164ed6150808` | README ausdrücklich **GPL-2.0-or-later**, mit Ausnahmen für unveränderten Shiu-Code unter MIT. [Repository](https://github.com/eonsystemspbc/fly-brain/tree/a3db62f9436074e485c0278290c2164ed6150808). | Kein pauschales MIT für Eon-Code. In der ersten Veröffentlichung als externe Referenz behandeln; bei späterem Einbau kompatible Lizenz- und Quelltextpflichten erfüllen. |
| Pugliese-CPG-Code, Commit `10e7661bf414ba7b4c2edf795cd36d0f878c17c0` | Upstream-[README](https://github.com/smpuglie/Pugliese_2026) erklärt **MIT**; in unserem kleinen Originaldatei-Export fehlt ein vollständiger eigenständiger Lizenztext. | Eigene Nachrechnung und Originalcode unterscheiden. Vor Weiterverteilung des Originalcodes die vollständigen MIT-/Copyright-Hinweise sichern. Keine Behauptung, der Code sei „ohne Lizenz“. |
| Pugliese-Originaldaten, Zenodo 22260924 | **CC BY 4.0**, [Metadaten-API](https://zenodo.org/api/records/22260924), [Record](https://zenodo.org/records/22260924). | Selektierte Originalparameter und abgeleitete Replays mit Attribution, Run-/Replikatbezug und Extraktionsbeschreibung kennzeichnen. Code-Lizenz separat. |
| FlyBody-Code / GitHub-Modell | **Apache-2.0**, [Original-Lizenz](https://github.com/TuragaLab/flybody/blob/main/LICENSE); lokal gepinnter Commit im Quellenregister. | Bei Übernahme Lizenz, vorhandene NOTICE-Hinweise und Änderungsvermerke mitführen. |
| FlyBody-Figshare-Daten/Policies, Version 4 | **GPL 3.0+**, ausdrücklich im [Figshare-Paket](https://doi.org/10.25378/janelia.25309105.v4), [API](https://api.figshare.com/v2/articles/25309105). | Nicht mit der Apache-Lizenz des GitHub-Codes verwechseln. Policies/Assets zunächst nicht mitliefern. |
| FlyGym / NeuroMechFly-Code | **Apache-2.0**, [Original-Lizenz](https://github.com/NeLy-EPFL/flygym/blob/main/LICENSE). | Externe Körper-/Sensorreferenz. Dataverse-Kinematik ist ein eigenes Datenprodukt mit separat zu prüfenden Bedingungen. |
| DoOR.data | **CC BY-SA 4.0**, explizit in der gepinnten [DESCRIPTION](https://github.com/ropensci/DoOR.data/blob/db323a496577c4b4a72b5c2fcd1859e07521ffb5/DESCRIPTION). | Geruchsantworttabellen und übernommene Adaptationen samt ShareAlike-Bedingung führen; nicht pauschal unter CC BY 4.0 stellen. |
| Visual-system-parts-list | **Apache-2.0**, [gepinntes LICENSE](https://github.com/murthylab/visual-system-parts-list/blob/0d8574d46627ce7fadd968a3c5d602e837325373/LICENSE). | Hinweise auf zugrundeliegende FlyWire-Daten zusätzlich erhalten. |
| `drosophila_neuropeptides` | **CC BY 4.0**, [gepinntes LICENSE](https://github.com/flyconnectome/drosophila_neuropeptides/blob/8df0b4506d28646ce6e77947515ba03246f5275d/LICENSE). | Typbasierte Übertragungen als solche und mit Attribution kennzeichnen. |
| Stürner-Neck-connective-Tabellen | Beim gepinnten Repository keine eigenständige Freigabe belegt. [Original](https://github.com/flyconnectome/2023neckconnective/tree/94637d7d82920234ef0bfdbf383c000e74a8b45a). | Quellenlink/Analysen zitieren; rohe Tabellen und Mischprodukte bis zur Klärung nicht pauschal weiterlizenzieren. |
| Tastekin- und Shiu-Verlagssupplemente; Benton; Calle/Schüler | Unterschiedliche Artikel-/Supplementrechte. Historische Rechtehinweise sind pro Eingabe im Register erhalten; vollständige Einzeldatei-Freigabe wurde hier nicht für alle abgeschlossen. | Keine pauschale Übernahme aus der Lizenz eines Code-Repositories. Belegte Quellenbefunde referenzieren; Original-Supplemente gesondert prüfen. |
| Gattuso, Rayshubskiy, WebGPU-Fly | Lokale Original-Lizenzdateien: **BSD-2-Clause**, **MIT**, **MIT**; vorgelagerte FlyBody-Anteile behalten Apache-Hinweise. Quellen-/Commitangaben im Register. | Vergleichs- und Methodenreferenzen; Rohdatenpakete haben eigene Bedingungen. |

### Tatsächlicher FlyWire-Konflikt

Die spezifischen Zenodo-Metadaten für 10676866/10877326 deklarieren CC BY 4.0; die allgemeine FlyWire-Richtlinie nennt CC BY-NC 4.0. Diese Dokumentation bewahrt beide Aussagen und entscheidet den Widerspruch nicht stillschweigend zugunsten einer kommerziellen Freigabe. Der Downloadkanal, die genaue Version und gegebenenfalls eine Klärung mit den Rechteinhabern sind maßgeblich. Für neuere Codex-/Princeton-Dateien gilt keine aus dem älteren Zenodo-Record abgeleitete pauschale Freigabe.

**CC BY-NC 4.0 erlaubt öffentliches Teilen und Bearbeiten für nichtkommerzielle Zwecke** unter anderem mit korrekter Namensnennung, Lizenzlink und Kennzeichnung von Änderungen. Eine nichtkommerzielle Forschungsfreigabe ist daher für Material möglich, das tatsächlich von dieser Freigabe erfasst wird. „Öffentlich auf GitHub“ allein entscheidet nicht, ob eine Verwendung nichtkommerziell ist. Die Plattformfreigabe klärt außerdem nicht automatisch zusätzliche Tabellen anderer Urheber in einem gemischten Export. Entsprechende Beiträge behalten ihre eigenen Bedingungen; die Projekt-MIT-Lizenz gibt sie nicht zur kommerziellen Nutzung frei. [Offizieller CC-BY-NC-Lizenzüberblick](https://creativecommons.org/licenses/by-nc/4.0/).

## Exakte Empfehlung für die erste Veröffentlichung

Diese Liste ist eine Auswahlhilfe; sie behauptet nicht, dass alle genannten Dateien bereits im veröffentlichten Git-Stand enthalten sind.

| Pfad / Menge | Empfehlung |
|---|---|
| `app/vendor/three.module.js`, `app/vendor/three.core.js`, `app/vendor/THREE-LICENSE.txt` | **Zusammen einschließen.** Three.js r186, MIT, vorhandene Copyright-/SPDX-Header und vollständigen Lizenztext bewahren. [Upstream](https://github.com/mrdoob/three.js/blob/r186/LICENSE). |
| Eigener Programmcode, Tests, Methoden, Berichte und Audit-Zusammenfassungen | Einschließen, soweit keine fremden Tabellen, personenbezogenen Betriebsinformationen oder fremden Codeblöcke ohne deren Hinweise eingebettet sind. |
| `app/data/banc_leg_motor_reference.json`, `motor_pathways.json`, `sensorimotor_mapping.json`, `flight_control_mapping.json` | BANC-Datenattribution und **CC BY 4.0** ausdrücklich beilegen. Auswahl, Umbenennung von Feldern, Pfadsuche und Modellzuordnung sind Projekttransformationen. Typ-Literaturrollen bleiben quellengebundene Hypothesen. |
| `app/data/cpg_replay.json` und CPG-Audits | Eigene CPU-Port-Ergebnisse, abgeleitet aus Pugliese/BANC; Quelle und Originaldaten-Lizenz beibehalten. Kein unbearbeiteter biologischer Datensatz und keine Originaltrajektorie. |
| `app/data/neuron_catalog.json`, `neuron_catalog_claims.json`, `neuron_catalog_assay_sets.json`, `brain-anchor-points*.json` | Enthalten Annotationen bzw. Mischquellen. Eine nichtkommerzielle Forschungsfreigabe ist für nachweislich von FlyWire-BY-NC erfasste Beiträge mit Namensnennung möglich. Zusätzliche Fremdtabellen getrennt prüfen; keine pauschale MIT-/kommerzielle Freigabe des Gesamtexports. Erforderlichenfalls nur erlaubte Teile mit dokumentierter Filterung exportieren. |
| `data/`, Original-EM, große Graph-/Punkt-/Skeletonarchive, fremde Policies/Meshes | Für ein schlankes Code-/Dokumentationsrelease **nicht mitliefern**; gepinnte Bezugsquellen und Hashes nennen. |
| `references/shiu-source/` | Falls mitgeliefert, unveränderte Originaldateien einschließlich `LICENSE` und Herkunftsangaben zusammen behalten. |
| `app/preview.png`, `download-live.png`, `graph-inspection.png`, `brain-points.png`, `brain-all-points.png` | Zunächst **ausschließen**; Bildschirmaufnahmen sind für die Laufzeit unnötig und benötigen eine eigene Sicht-/Quellenprüfung. |
| Private Cloud-Übergaben, Sitzungsdaten, Logs, `.venv`, Zugangsdaten | Ausschließen. Öffentliche Methoden und relative Reproduktionspfade gesondert bereitstellen. |

Bei der Inspektion von `app/` wurden keine importierten GLB/GLTF/STL/OBJ/FBX-Modelle oder Schriftdateien gefunden. Dies ist keine Lizenzprüfung sämtlicher außerhalb dieses Ordners gespeicherter Forschungsassets.

## Attribution für BANC-Ableitungen

> Anatomische Daten: Bates et al., *Distributed control circuits across a brain-and-cord connectome* (Nature, 2026), und zugehöriger Datensatz DOI 10.7910/DVN/7WTH1N, Dataverse v3.0 / BANC CAVE v888, CC BY 4.0. Dieses Projekt hat Teilmengen ausgewählt, Metadaten normalisiert, detektorspezifische Pfade berechnet und ungeprüfte Modelladapter ergänzt. Diese Transformationen und Modellresultate sind keine Bestätigung durch die ursprünglichen Datenersteller.

[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) · [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) · [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
