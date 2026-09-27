# Quellen, Herkunft und Zitieren

## Vollständiges Register dieses Forschungsstands

Das maschinenlesbare [source_registry.json](source_registry.json) übernimmt **alle 160 Eingaben und 46 Join-Spezifikationen** des eingefrorenen Integrationspakets. Eingaben umfassen Originaldateien, Literaturtabellen und daraus entstandene Projektprodukte; die Zahl ist deshalb keine Anzahl unabhängiger Datensätze oder Publikationen. Das Register bewahrt Bezugsquelle, Release, Schlüssel, fachliche Rolle, bekannte Grenzen und ursprüngliche Lizenznotiz. Öffentliche Ergänzungen kennzeichnen verifizierte, widersprüchliche und ungeklärte Rechte.

Der [lesbare Index](SOURCE_INDEX.md) listet jede Eingabe einzeln. Fehlende `source_url` bei einem abgeleiteten Produkt bedeutet, dass die Herkunft über seine Analyse-/Auditdateien und die dokumentierte Join-Kette verfolgt werden muss. Die Registrierung ist keine Behauptung, alle Originaldateien seien im Repository enthalten. Große Originaldaten werden separat von ihren offiziellen Quellen bezogen.

[evidence_snapshot.json](evidence_snapshot.json) bindet die hier berichteten Zahlen an bestehende Auditdateien mit SHA-256. [literature_registry.json](literature_registry.json) bewahrt die ergänzenden Motorik- und Flug-Primärquellenregister. Die Registrierung und Hashprüfung führen keine Simulation aus.

## Zentrale Ausgangsarbeiten

| Verwendung | Originalquelle |
|---|---|
| FAFB-Konnektom | Dorkenwald et al., *Neuronal wiring diagram of an adult brain*, Nature (2024), [DOI](https://doi.org/10.1038/s41586-024-07558-y); [Connectivity-Release 783.0](https://doi.org/10.5281/zenodo.10676866). |
| Neuronale Annotationen und Skeletons | Schlegel et al., *Whole-brain annotation and multi-connectome cell typing of Drosophila*, Nature (2024), [DOI](https://doi.org/10.1038/s41586-024-07686-5); [Supplementarchiv](https://doi.org/10.5281/zenodo.10877326), [benutzte Annotation v2.1.0](https://github.com/flyconnectome/flywire_annotations/releases/tag/v2.1.0). |
| Ganzhirn-Rechenmodell | Shiu et al. (2024), [Fachartikel](https://doi.org/10.1038/s41586-024-07763-9), [gepinntes Originalrepository](https://github.com/philshiu/Drosophila_brain_model/tree/91bdd1e7dcf193f3e7ca5a8933497fcef63b7960). Veröffentlichte v630-Experimente und lokale v783-Tabellen sind verschiedene Evidenzebenen. |
| Eon-Vergleich | [Eon Systems fly-brain, gepinnter Commit](https://github.com/eonsystemspbc/fly-brain/tree/a3db62f9436074e485c0278290c2164ed6150808); Referenz für Implementierung und Datenvergleich, keine unabhängige biologische Bestätigung. |
| Durchgehende BANC-Anatomie | Bates et al., *Distributed control circuits across a brain-and-cord connectome*, Nature (2026), [DOI](https://doi.org/10.1038/s41586-026-10735-w); [Dataverse v3.0](https://doi.org/10.7910/DVN/7WTH1N). |
| Vergleichsconnectom MaleCNS | Berg et al., *Sexual dimorphism in the complete Drosophila male central nervous system connectome*, Cell (2026), [DOI](https://doi.org/10.1016/j.cell.2026.08.015); [offizieller v1.0-Download](https://male-cns.janelia.org/download/). |
| VNC-/CPG-Modell | Pugliese et al., *Connectome simulations identify a central pattern generator circuit for fly walking*, [Preprint](https://doi.org/10.1101/2025.09.12.675944), [gepinntes Repository](https://github.com/smpuglie/Pugliese_2026/tree/10e7661bf414ba7b4c2edf795cd36d0f878c17c0), [Originaldaten](https://doi.org/10.5281/zenodo.22260924). Der geprüfte Upstream-README bezeichnet die Arbeit als Preprint. |
| Körperphysik | [FlyBody / Whole-body physics simulation of fruit fly locomotion](https://doi.org/10.1038/s41586-025-09029-4) und [NeuroMechFly v2](https://doi.org/10.1038/s41592-024-02497-y). Diese Methodenreferenzen sind kein Beleg, dass unsere Browsermechanik gleichwertig validiert ist. |

Weitere Quellen für Geschmack, Grooming, Geruch, Neurotransmitter, Neuropeptide, Beinsteuerung und Flug stehen im vollständigen Register und den dort benannten Originaldateien. Für eine konkrete Folgeveröffentlichung sind die tatsächlich benutzten Originalarbeiten zusätzlich zu diesem Projekt zu zitieren.

## Versionen und Transformationen

- **FAFB v783:** Root-ID als exakte Dezimalzeichenkette. Zusammenfassung nach Zellpaar ist von der ursprünglichen Paar-und-Neuropil-Zeilenzahl zu unterscheiden.
- **Princeton-Detektor:** Alternative Synapsenrufe am gleichen FAFB-Tier; neue Kandidaten werden nicht als bestätigte Reparaturen bezeichnet.
- **BANC v888:** Eigenes Tier und eigener Namensraum. v2- und v3-Synapsendetektoren werden getrennt gerechnet; Kontaktzahlen werden nicht addiert.
- **MaleCNS v1.0:** Eigenes männliches Tier. Homologien, Zelltypen und direkte ID-Gleichheit sind verschiedene Beziehungen.
- **Seiten:** Quellseiten bleiben erhalten. Bekannte historische Links-/Rechtskonventionen werden dokumentiert; Somaseite ist keine gemessene Drehrichtung.
- **Transmitter:** Vorhersage, kuratierter Nachweis und angenommene Rezeptorwirkung sind getrennte Felder. Ein zentrales Vorzeichen wird nicht ungeprüft auf die neuromuskuläre Synapse übertragen.
- **CPG:** Originalarchivparameter von Replikat 0 wurden unverändert extrahiert. Die acht lokalen Bedingungen benutzen einen CPU-Solver-Port; keine gespeicherte Originaltrajektorie wurde als eigene Nachrechnung ausgegeben. Vollarchiv-MD5 und vollständige HDF5-CRC wurden bei der Teilbereichsextraktion nicht geprüft.

## Dieses Projekt zitieren

Bitte die URL des konkreten Git-Commits oder eines späteren Releases und das Zugriffsdatum angeben. Solange kein archivierter Release-DOI existiert, keinen DOI erfinden. Beispiel:

> IT-EXPRESS-Bayern. *Fliege: ongoing connectome reconstruction and embodied modelling research prototype*. Forschungsstand 2026-09-27. GitHub repository, commit **[verwendeten Commit einsetzen]**. https://github.com/IT-EXPRESS-Bayern/Fliege. KI-gestützte Forschung und Entwicklung mit GPT-6 SOL und GPT-6 ASTRA.

Die Modellnamen beschreiben eingesetzte Forschungswerkzeuge. Sie übertragen keine Verantwortung auf die Systeme und implizieren keine Beteiligung oder Zustimmung der ursprünglichen Forschungsteams.
