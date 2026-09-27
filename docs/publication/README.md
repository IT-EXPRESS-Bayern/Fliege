# Forschungsstand: Fliege

**Stand: 27. September 2026 · laufendes Rekonstruktionsprojekt · wissenschaftlicher Prototyp**

Wir verbinden veröffentlichte Drosophila-Konnektome, überprüfbare Zellzuordnungen und ausdrücklich vereinfachte Körpermodelle. Das Ziel ist ein geschlossenes, biologisch begründetes Sensor-Motor-Modell. Eine vollständig rekonstruierte, selbstständig lebende oder frei fliegende Fliege liegt noch nicht vor.

**GPT-6 SOL und GPT-6 ASTRA sind wesentliche Forschungstreiber dieses Projekts:** Sie unterstützen Quellenrecherche, Datenaufbereitung, Hypothesenbildung, Programmierung und Auswertung. Die biologischen Ausgangsdaten stammen von den jeweils genannten Forschungsteams. Die KI-Unterstützung ersetzt weder biologische Experimente noch unabhängige Begutachtung; Verantwortung für Veröffentlichung und Interpretation tragen die menschlichen Projektverantwortlichen.

[English summary](RESEARCH_STATUS_EN.md) · [Quellen und Zitieren](PROVENANCE_AND_CITATION.md) · [Lizenzen](REUSE_AND_LICENSES.md) · [Roadmap](ROADMAP.md) · [vollständiges Eingaberegister](source_registry.json)

## Was tatsächlich vorliegt

| Bereich | Geprüftes Ergebnis | Wissenschaftliche Grenze |
|---|---|---|
| FAFB/FlyWire v783 | Katalog aller **139.255** ursprünglichen Root-IDs; **138.765** besitzen einen Anzeigenamen. | Namen, Zelltypen und Funktionen sind verschiedene Angaben. **116.943** Zellen haben im zusammengeführten Katalog keine kuratierte Funktionsannotation. |
| Anatomischer Graph | **15.091.983** gerichtete Shiu-v783-Zellpaare stimmen einschließlich Synapsenzahl mit dem aggregierten Original überein. | LIF-Dynamik und Vorzeichen sind Modellentscheidungen. Der Originalgraph wurde nicht verändert. |
| Neuronale Versuche | **42** Hauptversuche und **4** zusätzliche JO-Diagnosen; **7.048** Zellen feuern in mindestens einem der sechs Referenzläufe. | Das sind Antworten eines festgelegten Rechenmodells, keine neu gemessenen biologischen Funktionen. |
| BANC-Motorik | **805** anatomisch annotierte Motoneuronen, darunter **391** Bein-Motoneuronen; Pfade werden je Detektor getrennt behandelt. | BANC und FAFB stammen aus unterschiedlichen Tieren. Typähnlichkeit erlaubt keinen direkten Austausch ihrer Zell-IDs oder Synapsen. |
| Lokale Rückkopplung | Linkes Vorderbein: Gelenkzustand → FeCO-Sensoren → Interneuronen → 19 Motoneuronen → Gelenkmodell. **194** Versuche und **24** gesonderte Transferproben. | Normierte Ratenzustände, unkalibrierte Kräfte und unbekannte zellspezifische Sensortunings. Keine vollständige Hirn-Körper-Kopplung. |
| CPG-Nachrechnung | Originalkonfiguration und archivierter Parametersatz eines Replikats; **8** Bedingungen. DNg100-Anregung erzeugt bei sechs konservativ klassifizierten Motoneuronen einen Rhythmus um **15,15 Hz**. | CPU-Port des veröffentlichten Modells; Vergleich mit gespeicherten Originaltrajektorien und Nachrechnung aller 1.024 Replikate stehen aus. Die Frequenz ist keine gemessene Schrittfrequenz. |
| Flugprüfstand | **24** Power-Motoneuronen und **2** b1-Zellen als anatomische Referenzen; **26** Versuche einer reduzierten Rollmechanik. | Direkt vorgegebene Aktivierung und technische Rückkopplung; keine simulierte neuronale Flugbahn, keine freie Translation, kein autonomer Flug. |

Die Zahlen stammen aus bestehenden Audits; für diese Veröffentlichung wurden keine neuen Simulationen gestartet. [Prüfbare Momentaufnahme](evidence_snapshot.json).

## Negative Ergebnisse gehören zum Befund

- **JO-Selektivität nicht erreicht:** Das eingefrorene Hirnmodell trennt JO-C/E und JO-F nicht wie in der biologischen Literatur erwartet, auch nach Kontrolle von Zellzahl und Reizphase. Eine aBN1-Abschaltung zeigt eine Abhängigkeit im Modell, aber keine neue biologische Funktionsbestätigung.
- **Neuronale Gelenkstabilisierung nicht belegt:** Bei Standardverstärkung reicht die relative Änderung der maximalen Auslenkung von etwa **−0,60 % bis +0,33 %**. Die passive Mechanik erklärt den Großteil der Rückkehr. Alle vier geprüften claw/hook-Polaritätshypothesen bleiben offen.
- **CPG-Interventionen sind selektiv:** E1- oder E2-Entfernung beseitigt den geprüften Rhythmus; I2-Entfernung lässt Rhythmik bestehen. Das DNb08-Paar erzeugt unter derselben eingefrorenen Konfiguration keinen Rhythmus. Diese Aussagen gelten für dieses Modell und diesen Parametersatz.
- **Flugfeedback ist ein technischer Demonstrator:** Eine Rollraten-Rückkopplung verbessert den Prüfstand bei gewähltem Vorzeichen. Das umgekehrte Vorzeichen verschlechtert ihn. Daraus folgt kein Nachweis eines rekonstruierten Halteren-Regelkreises.

## Wie wir Evidenz behandeln

1. **Quellbefund:** rekonstruierte Anatomie, veröffentlichte Annotation oder dokumentiertes biologisches Experiment.
2. **Übertragene Hypothese:** Zuordnung zwischen Zelltypen, Releases oder verschiedenen Tieren; niemals als neue exakte Synapse ausgegeben.
3. **Modellannahme:** Rezeptorwirkung, Zeitkonstante, Kraft, Sensortuning oder Körperadapter, die nicht für die konkrete Zelle gemessen wurden.
4. **Modellergebnis:** reproduzierbare Antwort auf einen beschriebenen Reiz oder Eingriff unter diesen Annahmen.

64-Bit-Zell-IDs bleiben im Browser Dezimalzeichenketten. Neurotransmitter-Vorhersage und kuratierte Bestätigung bleiben getrennt. Detektorversionen werden nicht zu einem vermeintlich vollständigeren Graphen addiert. Ein bestandener Softwaretest bestätigt die geprüfte Implementierung, keine biologische Vollständigkeit.

Die nächste Forschungsphase benötigt belastbare Sensorantworten, Rezeptor- und Muskelparameter, Körperkontaktmechanik sowie unabhängig überprüfte Verhaltensvorhersagen. Weitere wissenschaftliche Rechenläufe sind für eine Cloud-Umgebung vorgesehen; diese Dokumentation behauptet keine bereits laufende Cloud-Ausführung.
