# Rekonstruktionsforschung mit Synapsenpunkten und 3D-Skeletten

Stand: 27. September 2026. Alle ausgewählten FlyWire-Originaldateien, einschließlich der 9,49-GB-Punktdatei, des 5,36-GB-Skeletts und der drei NBLAST-Matrizen, sind heruntergeladen und mit den veröffentlichten Prüfsummen abgeglichen. Die [grundlegende Dateianalyse](report.md) ist vollständig abgeschlossen: Schemata, IDs und erkannte numerische Inhalte wurden vollständig gelesen. Die folgenden gezielten Rekonstruktionsprüfungen sind ebenfalls abgeschlossen. Die [3D-Skelettansicht](http://127.0.0.1:4173/skeleton.html) und der [interaktive Forschungsbericht](http://127.0.0.1:4180/?view=1) machen die Befunde zugänglich.

Das ursprüngliche FAFB-v783-Paargraph-Archiv enthält 139.255 offizielle Neuron-IDs, von denen 616 keine aggregierte Kante haben. Der neuere Princeton-Detektor liefert für **477 dieser 616 IDs** insgesamt **3.171 gerichtete Neuronenpaare**, unterteilt in **3.233 Paar×Hirnregion-Zeilen mit 20.914 Punktaufrufen**. Jeder dieser Zählwerte wurde gegen exakte Quellzeilen der Princeton-Einzelpunktdatei geprüft. Das ist eine zusätzliche, veröffentlichte automatische Detektion am selben Präparat; daraus folgt noch keine physiologisch bestätigte Verbindung.

## Vergleich des gesamten Gehirns

Der [Vollvergleich beider Detektoren](whole_brain_detector_comparison/METHODEN_UND_ERGEBNISSE.md) umfasst sämtliche offiziellen v783-IDs und alle 79 Regionsbezeichnungen. Die vollständigen Eingaben wurden nach gerichteten Neuronenpaaren sowie separat nach Paar und Region verglichen. Alle Endpunkt-IDs gehören zur offiziellen Menge; Zählsummen sind gegen die Quelldateien geprüft.

| Paarmenge | Gerichtete Paare |
|---|---:|
| Original insgesamt | 15.091.983 |
| Princeton insgesamt | 19.773.733 |
| In beiden vorhanden | 13.447.535 |
| Nur im Princeton-Export | 6.326.198 |
| Nur im Original-Export | 1.644.448 |

Von den Princeton-only-Paaren verbinden **6.323.027** zwei Neuronen, die beide schon im Originalgraphen mindestens eine Kante haben. Nur die übrigen 3.171 berühren die zuvor untersuchten 616 kantenlosen IDs. Damit erweitert die Untersuchung die bisherige Lückenliste auf das ganze Gehirn.

Die meisten zusätzlichen Paare sind schwach: 5.207.559 der 6.323.027 Paare haben einen Punktaufruf; **63.854 haben mindestens fünf**, 14.842 mindestens zehn und 4.799 mindestens zwanzig. Die [50.000 stärksten Prüfkandidaten](whole_brain_detector_comparison/top_50000_new_pairs_with_type_recurrence.csv) enthalten Zelltypen, Regionen und den Vergleich mit bereits bekannten Zelltyp-Paarmustern. Diese Rangfolge erleichtert die nächste Prüfung, ist aber keine gemessene Zuverlässigkeit. Auch die Gegenrichtung wird geprüft: 437 Original-only-Paare haben mindestens fünf Aufrufe.

Die [vollständigen Paar-Deltas](whole_brain_detector_comparison/full_directed_pair_delta.parquet), [Paar/Region-Deltas](whole_brain_detector_comparison/full_pair_region_delta.parquet) und [Audits](whole_brain_detector_comparison/audit.json) ermöglichen weitere Analysen ohne erneutes Einlesen aller CSV-Archive. Detektoren unterscheiden sich in Fehlalarmen, Erkennungsrate und Verarbeitung; ihre Zählungen werden nicht addiert. Der Originalgraph bleibt als Referenz erhalten.

## Aufschlüsselung der 616 ursprünglich kantenlosen Neuronen

Die 616 IDs sind in der [integrierten Prüfliste](reconstruction_candidates_v783/integrated_root_review_queue_616.csv) in sechs **disjunkte** Arbeitsgruppen eingeordnet. Eine ID erscheint hier genau einmal; die Reihenfolge ist eine Arbeitspriorität, keine geschätzte Wahrscheinlichkeit.

| Arbeitsgruppe | IDs | Was bereits vorliegt | Nächste belastbare Prüfung |
|---|---:|---|---|
| Auffälliges R7 mit zwei Detektorpunktsätzen | 1 | 48 ältere und 213 neuere nicht-selbstbezogene Punktaufrufe; 18 gemeinsame Paar/Region-Schlüssel | Ursache des Ausschlusses aus beiden Paargraphen klären; räumliche Fälle einzeln prüfen |
| Princeton-Paarbefund, auch im Export mit mindestens fünf Punkten pro Paar | 203 | Veröffentlichte Neuronenpaare mit einzelnen Punktnachweisen | Morphologie und Partneridentität an priorisierten Orten prüfen |
| Princeton-Paarbefund ausschließlich mit ein bis vier Punkten pro Paar | 274 | Schwächere veröffentlichte Neuronenpaare mit Punktnachweisen | Schwellenabhängigkeit und Detektorfehler besonders beachten |
| Ausschließlich ältere Kontakte zu ungeprüften Segmenten | 53 | Beobachtete Segment-IDs und Orte | Segmentzugehörigkeit zu vollständigen Neuronen prüfen |
| Nur Princeton-Selbstkontakte, ohne vorherige Klasse | 22 | Automatische Aufrufe innerhalb derselben Root-ID | Eigenkontakt oder Segmentierungs-/Detektorartefakt unterscheiden |
| Nur Typmuster oder kein direkter Punktbefund | 63 | Unterschiedlich starke indirekte Zelltypinformationen | Morphologische Homologie prüfen; genaue neue Kanten bleiben offen |
| **Gesamt** | **616** | | |

Die vollständige Princeton-Punktdatei hat 80.215.790 Zeilen. Davon berühren 26.941 Zeilen insgesamt 550 der 616 IDs. Die Differenz zu den 477 IDs im Paar-Export ist vollständig aufgeklärt: 72 weitere IDs tragen ausschließlich Selbstkontakte, hinzu kommt das R7-Neuron. Die Punktzählung zerfällt exakt in **20.914 Paargraph-Punkte + 5.814 Selbstkontakte + 213 R7-Ausnahmepunkte**. Nach dieser empirischen Trennung und Leerregion→`UNASGD` gibt es null Abweichungen bei den 3.233 übrigen Paar/Region-Zählwerten. Die Ursache der R7-Auslassung ist nicht bekannt. [Abgleich mit Quellzeilen](reconstruction_candidates_v783/princeton_exact_pair_candidates_3233.csv), [Audit](reconstruction_candidates_v783/princeton_point_exclusion_audit.json).

Das 3D-Skelett wurde über alle 268.281.651 Zeilen geprüft. **Alle 616 Ziel-IDs haben Skelettknoten**, insgesamt 151.369; auch sämtliche 195 IDs, die nur im neueren Princeton-Paar-Export einen Befund haben, sind enthalten. Der Median liegt bei 238,5 Knoten pro Zielneuron. Die Metadaten nennen Nanometer als Einheit. Die [Morphologietabelle](morphology_616/coverage_616.csv) enthält je ID Knotenzahl, räumliche Ausdehnung, Zelltyp und Evidenzklasse; die [Formausreißer](morphology_616/geometry_extremes.csv) kennzeichnen 21 Fälle für nähere Betrachtung. Eine ungewöhnliche Form ist für sich kein Fehlernachweis. [Methoden und Koordinatenprüfung](morphology_616/README.md).

Die [R7-Fallstudie](r7_case_study/README.md) nutzt 311 echte R7-Skelettknoten und fünf benannte Partnerbäume für die Browseransicht. Von 45 alten R7-Punkten mit passendem neuem Paar liegen 36 innerhalb von 250 nm zum nächstgelegenen Princeton-Aufruf, nach dem dokumentierten Prä/Post-Abstandsmaß. Die Zuordnung ist nicht zwingend eins zu eins. Die räumliche Nähe und die wiederholten Partnerpaare machen R7 zu einem konkreten Prüffall; sie begründen allein keine Korrektur des veröffentlichten Graphen.

| Vergleichsquelle | Bereits ausgewertet | Nutzen für die Rekonstruktion | Grenze |
|---|---|---|---|
| Original-FAFB und Princeton | Dasselbe Tier und dieselben v783-Root-IDs; Punkte und Paare exakt abgeglichen | Direkte alternative Beobachtungen konkreter Partner und Orte | Automatische Detektion, verschiedene Exportstufen |
| BANC v888 | 17 geprüfte Dateien; 34 der 616 IDs mit geprüften Homologien, 7.293 Partner-Typmuster | Durchgehendes Gehirn–Bauchmark und morphologische Vergleichspartner | Anderes weibliches Tier, eigene IDs |
| MaleCNS v1.0 | 166.700 Neuronrollen; 562 der 616 mit Typ-/Seitenvergleich, davon 520 R1–6 und 42 weitere | Zweiter vollständiger ZNS-Vergleich und motorische Rollen | Anderes männliches Tier; Typvergleich ersetzt keine FAFB-Einzelkante |
| NBLAST und Skelette | Alle Originaldateien lokal; räumliche Prüfung der 616 IDs abgeschlossen | Zellformen, Seiten und Homologiekandidaten prüfen | Ähnlichkeit oder Astnähe allein identifiziert keine Synapse |

Die [73 Eingaben und 22 Verknüpfungsregeln](model_integration_pack.json) halten die Tier- und Versionszuordnungen maschinenlesbar fest. Der [BANC-Bericht](banc_2026_integration.md), der [MaleCNS-Bericht](malecns_2026.md) und der [Rekonstruktionsbericht](reconstruction_candidates_v783/METHODEN_UND_ERGEBNISSE.md) enthalten die vollständigen Methoden und Dateien.

## Körper und motorischer Anschluss

Die [neue Browserfliege](http://127.0.0.1:4173/) besitzt sechs gegliederte Beine mit Coxa, Femur, Tibia und zusammengefasstem Tarsus, feste Standpunkte, weiche Schwungphasen, Körperneigung und Kopfkompensation. Gelenkwinkel, Winkelgeschwindigkeiten und Bodenkontakte sind als `fly.body-observation.v1` auslesbar. Das [Körpermodell](../app/BODY_MODEL.md) dokumentiert Koordinaten, Annahmen und Tests.

Als anatomische Grundlage wurden **391 proofread BANC-Bein-Motorneuronen** mit Seite, Nerv, Muskelziel und Funktionsbeschreibung aufgeschlüsselt. Ihre vollständigen nicht-selbstbezogenen Eingänge umfassen 112.809 Paare in v2 und 117.988 in v3; 101.637 sind gemeinsam, 35.725 haben in beiden Versionen mindestens fünf Aufrufe. Die [Motortabellen](body_neural_interface/README.md) enthalten auch 11.308 vorgeschaltete Neuronen. Eine Beinzuordnung ist belegt; die Übersetzung in Gelenkwinkel, Muskelkräfte und sensorische Aktivität bleibt unkalibriert. Das sichtbare Laufen wird weiterhin vom abstrakten Eigenaktivitätsmodell erzeugt.

Für das spätere Fliegenmodell liefern diese Schritte anatomische Eingaben und begründete Kandidaten. Die verbleibenden Aufgaben sind die Bestätigung ungeprüfter Segmentidentitäten, die Klärung widersprüchlicher Detektorfälle sowie Parameter für neuronale Aktivität, Rezeptoren, innere Zustände und Körperbewegung. Diese Größen lassen sich aus Synapsenzahl und Skelettgeometrie nicht eindeutig berechnen. Das Modell braucht daher dokumentierte Annahmen und Vergleichstests mit veröffentlichten Funktions- und Verhaltensdaten.

Primärquellen: [FlyWire Originaldaten](https://zenodo.org/records/10676866), [Skelette und NBLAST](https://zenodo.org/records/10877326), [Princeton-Detektor, Yu et al.](https://doi.org/10.1101/2025.07.11.664377), [BANC, Bates et al.](https://doi.org/10.1038/s41586-026-10735-w), [MaleCNS, Berg et al.](https://doi.org/10.1016/j.cell.2026.08.015).
