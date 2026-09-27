# Motorsteuerung: gefundene Verbindungen und getestete Körperzuordnung

> Aktualisierung 27.09.2026: Original-CPG-Eingaben und archivierter Parametersatz0 sind inzwischen vorhanden; acht Nachrechnungen sind abgeschlossen. Aktueller Stand: [CPG-Ergebnisse](cpg_reproduction/results.md) und [Cloudübergabe](../docs/publication/README.md). Frühere offene Download-/Replikationspunkte in diesem Zwischenbericht sind dadurch teilweise überholt. Das Gesamtarchiv und seine gespeicherten Trajektorien bleiben ungeprüft.

Stand: 27. September 2026. [3D-Motorlabor öffnen](http://127.0.0.1:4173/motor.html) · [Forschungsbericht](http://127.0.0.1:4180/?view=1)

## Ergebnis

Wir haben konkrete motorische Ausgangszellen und durchgehende kurze Verbindungswege aus dem Gehirn identifiziert. Für den ersten Körperanschluss sind einzelne Femur–Tibia-Gelenke mit exakten Motor-IDs testbar. Eine vollständig kalibrierte, selbstständig laufende Hirn-Körper-Steuerung entsteht daraus noch nicht.

**Absteigendes Hirnneuron → Bauchmarksschaltung → Motorneuron → Muskel → Gelenk → sensorische Rückmeldung** ist die relevante Kette. Die ersten Schritte lassen sich im BANC-Connectom desselben Tiers verfolgen. Unser FAFB-Gehirn ist ein anderes Individuum; alle Originalgraphen bleiben erhalten und getrennt.

| Ebene | Tatsächlich vorhanden | Bedeutung |
|---|---|---|
| Motorische Ausgänge | 805 eindeutige, als motor annotierte BANC-v888-Zellen; darunter 391 Beinmotorneuronen | Exakte IDs, Körperteil, Muskelziel und vorhandene Aktionsfelder; keine vollständige Physiologie |
| Absteigende Steuerung | 92 Neuronen aus 36 literaturannotierten Typen | Auswahl nach Bewegung, Lenken, Putzen, Anhalten, Landen und Flucht/Start |
| Durchgehende Wege | 1.618 direkte Verbindungen und 448.942 Zwei-Kanten-Wege | Jeder Weg vollständig in mindestens einem der Detektoren v2/v3; keine Mischung einzelner Kanten zwischen Versionen |
| Browserauswahl | 1.739 konkrete Pfadbeispiele | Jede Kante mindestens fünf Kontakte in beiden Detektoren; Auswahl ist keine Funktionswahrscheinlichkeit |
| Direkte Körperansteuerung | 113 Femur–Tibia-Motor-IDs: 101 Beuger und 12 Strecker | Anatomisch benannte Aktionen, getrennt nach den sechs Beinen |
| Kontrollen | 594 Datenprüfungen, neun Funktionstests und 48 vollständige Gelenkversuche | Datenintegrität und Modellimplementierung geprüft; kein neuer biologischer Kausalnachweis |

## Welche Zellen wir zuerst nutzen können

| Kandidat | Literaturgestützte Rolle | Einsatz im nächsten neuronalen Modell |
|---|---|---|
| **DNa02** | Gleichseitige Schrittlänge beim Lenken verkürzen | Einseitige Aktivierung und tatsächliche Wirkung auf die sechs Beinphasen prüfen |
| **DNg13** | Gegenüberliegende Schritte beim Lenken verlängern | Gekreuzte Zielseite korrekt erhalten; keine bloße Rotation des Rumpfs |
| **DNg100** | Schrittfrequenz und Vorwärtsbewegung in Experimenten des aktuellen CPG-Preprints | Den veröffentlichten Rhythmusgenerator und seine Hemmversuche mit festgelegten Originalparametern reproduzieren |
| **MDN / LBL40** | Rückwärtsgang und phasenspezifische Hinterbeinbeugung | Separaten Hinterbein-Zweig testen; LUL130-Zuordnung bleibt offen |
| **BRK** | Aktives Bremsen und erhöhter Gelenkwiderstand | Koaktivierung der Gegenspieler erhalten; BRK sind aufsteigende Neuronen |

Quellen und Status: [Yang et al., Cell 2024](https://doi.org/10.1016/j.cell.2024.08.033), [Pugliese et al., Preprint v2, noch nicht begutachtet](https://pmc.ncbi.nlm.nih.gov/articles/PMC13142387/), [Feng et al., 2020](https://doi.org/10.1038/s41467-020-19936-x), [Sapkal et al., 2024](https://doi.org/10.1038/s41586-024-07854-7). Weitere 24 Quellen mit Evidenzgrenzen stehen in [Motorforschung](motor_control_research.md).

DNp09 ist kontextabhängig und wird nicht pauschal als Vorwärtskanal verwendet. Soma-Seite, Axonseite und Zielbeinseite bleiben getrennte Angaben.

## Ein konkreter, im Browser geprüfter Pfad

```text
DNg100, Soma rechts            720575941500851362
  ↓ 105 Kontakte v2 / 116 v3
IN09A002, links                720575941592869928
  ↓ 93 Kontakte v2 / 91 v3
Motorneuron, linkes Hinterbein 720575941451737978
  → accessory_tibia_flexor_muscle
  → Femur–Tibia beugen
```

Dieser vollständige Weg ist im selben BANC-Tier enthalten. Im Motorlabor: **Links hinten → Pfad DNg100 right / 2 Kanten → Diese Motor-ID direkt prüfen**. Die Auswahltaste aktiviert das Motorneuron direkt; sie simuliert keine Ausbreitung durch DNg100 oder IN09A002. Genau diese ID-Auswahl wurde im Browser geprüft.

## Was die Tests zeigen

Die 48 Versuche bestehen aus sechs Beinen × acht Bedingungen: Nullsignal, Beuger, Strecker, gezielte Ausschaltung, Schein-Ausschaltung, gemeinsame Gegenspieleraktivierung sowie dasselbe äußere Störmoment mit und ohne Koaktivierung. Nullsignal und ausgeschalteter Eingang bleiben ohne Bewegung; Beuger und Strecker ändern den Winkel entgegengesetzt. Bei gleicher Aktivität können beide Gegenspieler aktiv sein, obwohl ihr Nettomoment null ist. Unter derselben Störung sinkt die Auslenkung im implementierten Modell von ungefähr 9,90° auf 4,61°.

Die Parameter sind offengelegte, unkalibrierte Modellgrößen. Der Körper ist fixiert, die Beinsegmente behalten ihre Länge. Es gibt hier weder gemessene Muskelkräfte noch Bodenreaktionskräfte oder ein vorgegebenes Gehprogramm. Die Kontrollen bestätigen unsere Implementierung der gesetzten Gleichungen; sie entdecken keine zusätzliche biologische Funktion.

Separat wurden Zwischenzellen aus den anatomischen Pfaden entfernt: Für DNa02 links sinkt die Zahl in höchstens zwei Kanten erreichbarer Motorziele beispielsweise von 151 auf 139. Das ist eine strukturelle Auswertung. Längere Wege können weiterhin bestehen; ein tatsächlicher Verhaltensausfall folgt daraus nicht.

## Noch zu schließen

1. **Neuronale Dynamik:** Wiederkehrende prämotorische Schaltungen mit passenden Vorzeichen, Zeitkonstanten und Originalparametern simulieren. E1/E2/I2 sind konkrete CPG-Kandidaten; das veröffentlichte negative DNb08-Ergebnis in BANC muss erhalten bleiben.
2. **Motor- und Muskelphysiologie:** Unterschiedliche Rekrutierung und Kraft von Motoreinheiten, Momentarme, Trägheit und Last kalibrieren. Ein gleiches Poolmittel ist keine gleiche biologische Muskelkraft.
3. **Sensorischer Regelkreis:** Gelenkwinkel und Bewegung über FeCO-Zellen zurückführen; Reflexe, Zustand und Eigenbewegungshemmung prüfen. Kontaktkräfte erst bei vorhandener Kraftphysik verwenden.
4. **Datenzuordnung:** Reviewed-Homologien und Metadaten-Matches widersprechen sich teilweise. Die Quellen werden nicht still vereinheitlicht und BANC-Kanten nicht als gemessene FAFB-Kanten ausgegeben.

Ein Transmitterlabel allein bestimmt weder das Vorzeichen am Muskel noch dessen Kraft. In der lokalen BANC-Metadatei weichen 28 von 30 Motor-Vorhersagen von einem zusätzlichen verifizierten Quellenfeld ab; diese selektive Gruppe betrifft Hals/Halteren. Die Beinmotorfelder sind dort leer. Eine spätere CPG-Tabelle enthält zusätzliche Glutamat-Annotationen für 35 exakt übereinstimmende Vorderbeinmotoren; sie werden separat dokumentiert und noch nicht ungeprüft als physiologische Kalibrierung übernommen.

## Dateien direkt weiterverwenden

- [Motoratlas](motor_output_atlas/README.md): sämtliche 805 Motoridentitäten als CSV und Parquet sowie Quellenprüfung.
- [Schaltkreiswege](motor_pathways/README.md): vollständige Ein-/Zwei-Kanten-Wege, fokussierte Drei-Kanten-Auswertung, Beispiele und strukturelle Eingriffe.
- [Browserexport](../app/data/motor_pathways.json): exakte String-IDs, Motorreferenzen und nachvollziehbare Pfade.
- [Gelenkaudit](../app/data/motor_joint_audit.json): 48 Versuche, Quellen-/Modellhashes und Kontrollresultate.
- [Modellgleichungen](../app/MOTOR_METHODS.md): Aktivierung, Antagonisten, Gelenkdynamik und offene Parameter.
- [Forschungsquellen](motor_control_sources.json): 24 Quellen, 72 zusätzliche Kandidaten, Originalcode-Commit und CPG-Parameter.
- [Integrationsplan](model_integration_pack.md): 99 lokale Eingaben und 36 getrennte Join-Regeln.

Die zusätzlichen kleinen CPG-Originaldateien sind mit festen Downloadadressen registriert, aber **noch nicht lokal heruntergeladen**: Der interne Browser meldete beim Download einen Timeout. Eine vollständige Reproduktion dieses veröffentlichten Modells wurde deshalb nicht behauptet. Die bereits vorhandenen BANC-Daten und alle hier beschriebenen eigenen Pfad- und Gelenktests sind lokal nutzbar.

Originaldaten: [BANC, CC BY 4.0](https://doi.org/10.7910/DVN/7WTH1N), [zugehörige Nature-Arbeit](https://doi.org/10.1038/s41586-026-10735-w).
