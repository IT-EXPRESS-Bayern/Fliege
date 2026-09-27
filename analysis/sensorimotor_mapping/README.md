# Ein echter anatomischer Sensor–Motor-Ausschnitt

Stand: 27.09.2026. Reproduktion: `analysis/.venv/Scripts/python.exe analysis/sensorimotor_mapping/build.py`.

Der Export verbindet **genau identifizierte BANC-v888-Neuronen desselben Tiers**. Er erfindet keine Sinnesfunktion aus einer Bewegung der Browserfliege. Sensorinventar, Pfade und Modellannahmen bleiben unterscheidbar.

## Enthaltene Originaldaten

- [625 Sensor-IDs](sensor_inventory.csv): alle mit exakter Unterklasse `front|middle|hind_leg_claw|hook|club_chordotonal_organ_neuron` annotierten Zellen. 616 sind als proofread markiert, neun nicht.
- Linkes Vorderbein (LF): **27 claw, 27 hook, 56 club**, insgesamt 110 Zellen; 109 proofread, eine nicht.
- [19 LF-Femur–Tibia-Motorneuronen](lf_motor_inventory.csv): 17 Beuge- und zwei Streckmotorneuronen, jeweils mit publizierter Muskelaktion und exakter ID.
- [Browserdatei](../../app/data/sensorimotor_mapping.json): vollständige Kanten des ausgewählten Ausschnitts, 477 Knoten, Sensoren/Motoren, getrennte Transmitterfelder und begrenzte Pfadbeispiele. `proofread` ist ein Boolean. Quellen-Hashes und Download-URLs sind eingebettet.

| Quelle | Direkte Sensor→MN-Pfade | Sensor→Zwischenzelle→MN-Pfade | Unterschiedliche exportierte Kanten |
|---|---:|---:|---:|
| BANC Detektor v2 | 48 | 7.244 | 2.720 |
| BANC Detektor v3 | 68 | 8.900 | 3.232 |

Vollständige Listen: [v2-Pfade](lf_paths_v2.parquet), [v3-Pfade](lf_paths_v3.parquet), [v2-Kanten](lf_edges_v2.parquet), [v3-Kanten](lf_edges_v3.parquet). Beide Pfadschritte stammen stets aus demselben Detektor. Die Versionen werden weder addiert noch zu erfundenen Wegen kombiniert. Sensorische und motorische Zellen wurden als prämotorische Zwischenzellen ausgeschlossen; andere Klassen bleiben mit ihrer Originalannotation sichtbar. Die Mengen sind strukturelle Erreichbarkeit bis zwei Kanten, keine neuronale Simulation und keine Liste ausschließlich funktionierender Reflexe.

`inputCountV2` und `inputCountV3` sind für jeden Knoten die Summe aller eingehenden `count`-Werte im jeweiligen **vollständigen** Graphen, ohne Autapsen. Damit ist eine transparente Normierung möglich. Sie liefert noch keine physiologisch gemessene Leitfähigkeit.

## Zwei konkret verfolgbare LF-Anschlüsse

| Strecke, alle IDs BANC v888 | Kantenwerte v2 | Kantenwerte v3 |
|---|---:|---:|
| claw/SNpp50 `720575941544751877` → IN19A030 `720575941573415945` → accessory_tibia_flexor_B `720575941479472258` | 50, 53 | 65, 50 |
| claw/SNpp51 `720575941478502209` → IN13A006 `720575941604082361` → tibia_extensor_SETi `720575941478577231` | 11, 52 | 23, 51 |

Beide Zwischenzellen besitzen `ntVerified=gaba`. Die Motorklassen sagen, welchen Muskel die Ausgangsneuronen ansteuern; sie beweisen keine erregende Nettowirkung des vorgelagerten Wegs. Bei einem GABA-basierten Modellvorzeichen würde die erste Route den Beugepool hemmen, die zweite den Streckpool. Das ist eine ausdrücklich zu testende physiologische Modellannahme. Rezeptorspezifische Vorzeichen sind nicht gemessen und deshalb `biologicalSign=null`.

Die zwei Sensoren werden **nicht** als bewiesenes Flexions-/Extensionspaar bezeichnet. `SNpp50` und `SNpp51` kodieren in diesen Metadaten keine geprüfte Richtungspräferenz. Ein Reflex kann mit beiden Polaritätsannahmen untersucht werden; ein daraus passendes Modell ist noch kein Nachweis der echten Zelltunings.

## Was die Literatur tatsächlich liefert

Kontrollierte Gelenkbewegungen und Kalziumbildgebung unterscheiden eine Positionskodierung durch claw, eine richtungsabhängige Bewegungskodierung durch hook sowie Vibration/bidirektionale Bewegung durch club. Einzelne claw-Zellen haben unterschiedliche Winkelbereiche; deshalb liefert ein Populationsname noch keine lineare Kennlinie oder genaue Richtung für jede BANC-ID. [Mamiya et al. 2018](https://doi.org/10.1016/j.neuron.2018.09.009), [Mamiya et al. 2023](https://doi.org/10.1016/j.neuron.2023.07.009)

Die FANC-Primärrekonstruktion unterscheidet Flexions- und Extensionsgruppen und ihre unterschiedlichen Motorverbindungen. Ihr gewichteter „impact score“ beschreibt anatomische Einflüsse mit angenommenen Transmitterwirkungen; er berücksichtigt weder vollständige Dynamik noch jede elektrische Verbindung. Diese Gruppen sind keine automatisch übertragenen BANC-Root-Labels. [Lee et al. 2025](https://doi.org/10.1038/s41467-025-59302-3)

BANC führt teilweise FANC-Matches als kurze Quellkennungen und automatische Morphologiematches; mehrere Sensoren teilen sich solche Kennungen, teils über Unterklassengrenzen hinweg. Ohne versionierten Abgleich zur originalen FANC-Tuningtabelle rechtfertigt das keine einzelne Richtungszuweisung. Daher sind **alle 625 `tuningPolarity`-Werte und Tuningkurven unbekannt**. Das ist eine tatsächliche Datenlücke, keine Nullantwort.

Außerdem ist hook-Rückmeldung bei Eigenbewegung zustandsabhängig präsynaptisch reguliert. Ein festes Sensor-Gain ist ein vereinfachtes Modell. [Dallmann et al. 2025](https://doi.org/10.1038/s41586-025-09554-2)

## Schnittstelle für den kontrollierten Modellversuch

1. `jointAngles.femurTibia` und die entsprechende Winkelgeschwindigkeit in **explizit beschriftete Sensor-Tuninghypothesen** umrechnen. Modellwinkel: gerade Stellung = 0, zunehmender Wert = mehr Beugung.
2. Ratezustände an den exakten LF-claw/hook-IDs führen. Keine erfundenen biologischen Spikezeiten behaupten. club zunächst als getrennten Kontrollkanal behandeln.
3. Nur die Kanten einer gewählten Version verwenden; Modelle mit v2 und v3 als getrennte Replikate vergleichen. Transmitter-Verified und -Predicted bleiben separat. Unter den 625 Sensoren besitzen 592 Verified-ACh, 33 keinen Verified-Wert; 80 widersprüchliche Verified/Predicted-Paare sind vorhanden.
4. Beuge- und Streckpool getrennt lesen. Der geometrische Muskelaktions-Sign ist +1/-1 im Körperwinkel, unabhängig vom zentralen Transmitterzeichen des Motorneurons. Kraft-Gains bleiben unkalibriert.
5. Beide Tuningpolaritäten, Sensorabschaltung, Kantenabschaltung und äußere Gelenkstörung testen. Gemessen werden Modellstabilität, Rückstellrichtung, Latenz, Bewegungsumfang und Koaktivierung. Eine passende Antwort entscheidet zunächst zwischen Modellvarianten.

Der Ausschnitt enthält drei nicht als proofread markierte Knoten. Für eine vorsichtige erste Auswertung können diese ausgeschlossen werden; der Filter muss im Laufmanifest stehen. Vollständige Kanten bleiben im Datensatz erhalten. Anatomie ersetzt keine Spannungs-, Rezeptor-, Muskel- oder Verhaltenskalibrierung.

Weitere Autonomielücken stehen im [Gap-Ledger](autonomy_gaps.md) und seiner [JSON-Datei](autonomy_gaps.json). Quellenidentität und Exportprüfungen: [Audit](audit.json), [Validierung](validation.json).
