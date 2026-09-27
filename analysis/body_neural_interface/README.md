# Vom ZNS zum gegliederten Fliegenkörper

Stand: 27. September 2026. Reproduzierbarer Export: `analysis/.venv/Scripts/python.exe analysis/body_neural_interface/build.py`. Grundlage ist der bereits lokal geprüfte [BANC-v888-Datensatz](https://doi.org/10.7910/DVN/7WTH1N), beschrieben von [Bates, Phelps, Kim et al.](https://doi.org/10.1038/s41586-026-10735-w). Lizenz CC BY 4.0; Dateiquellen und SHA-256 stehen im [Audit](audit.json).

Aus 188.508 Metadatensätzen wurden exakt die Zeilen mit `super_class=motor` und `body_part_effector=front_leg|middle_leg|hind_leg` gewählt: **391 unterschiedliche, als proofread markierte Motorneuronen**. Die Körperseite stimmt bei allen mit dem Seitennamen ihres Nerven überein. Daraus ergeben sich LF 69, RF 70 sowie LM, RM, LH und RH mit jeweils 63 Neuronen. Die Beinzuordnung nutzt Körperteil und Seite; das Metadatenfeld `neuromere` wird dafür nicht umgedeutet.

Die [391 Einzelzeilen](banc_leg_motor_channels_391.csv) behalten BANC-ID, Zelltyp, Nerv, Zielmuskel, veröffentlichte Funktionsbeschreibung und Proofread-Status. Hinzu kommt eine explizite **Zuordnungshypothese** zur geometrischen Schnittstelle `fly.body-observation.v1` des neuen Browserkörpers:

| Quellenfunktion | Kandidat im Körpermodell | Neuronen | Noch zu klären |
|---|---|---:|---|
| Femur–Tibia beugen/strecken | `femurTibia` | 113 | Winkelreferenz, Vorzeichen, Muskelkraft und Dynamik |
| Tibia–Tarsus beugen/strecken | `tibiaTarsus` | 30 | Winkelreferenz, Vorzeichen, Muskelkraft und Dynamik |
| Coxa–Trochanter beugen/strecken | `femurElevation` | 110 | Im aktuellen Körper zusammengefasstes Gelenk; zusätzliche Freiheitsgrade fehlen |
| Coxa in verschiedene Richtungen bewegen | `coxaAzimuth` als erster Vergleich | 56 | Dreidimensionale Achsen und Muskelzüge können nicht auf einen Winkel reduziert werden |
| Lange Sehne ziehen | noch kein Kanal | 48 | Sehnen- und Mehrgelenkmodell fehlen |
| Unbekannte Beinbewegung | noch kein Kanal | 34 | Die Quelle benennt keine ausreichend bestimmte Wirkung |
| **Gesamt** | | **391** | |

Die 143 Neuronen der ersten zwei Zeilen haben einen passenden **Gelenknamen**, jedoch noch keine kalibrierte Ansteuerung. Deshalb stehen `actuator_sign` und `force_gain` auf fehlend, `enabled_for_control=false`. Keine dieser Zeilen schaltet bereits das Browsermodell auf einen biologischen Antrieb um. Die [Browser-Referenzdatei](../../app/data/banc_leg_motor_reference.json) erhält alle IDs als Zeichenketten und enthält dieselben Grenzen maschinenlesbar.

## Echte Eingangsverbindungen zu diesen Motorneuronen

Beide vollständigen BANC-Kantenexporte wurden nach postsynaptischer Motor-ID gefiltert; Selbstverbindungen sind ausgeschlossen. Jede Zeile bleibt ein beobachtetes Paar innerhalb des BANC-Tiers. Fehlende Kanten einer Version werden beim Vergleich als fehlend gespeichert, nicht mit der anderen Version addiert.

| Export | Gerichtete Eingangs-Paare | Summe `count` | Verschiedene vorgeschaltete Neuronen | Motorneuronen mit Eingang |
|---|---:|---:|---:|---:|
| [Paper-v2](banc_motor_incoming_v2.parquet) | 112.809 | 980.814 | 10.687 | 391 |
| [Detektor-v3](banc_motor_incoming_v3.parquet) | 117.988 | 1.080.876 | 10.990 | 391 |

Die [Vergleichstabelle](banc_motor_input_detector_comparison.parquet) enthält 129.160 unterschiedliche Paare über beide Versionen. **101.637** stehen in beiden Exporten; **35.725** haben in beiden mindestens fünf Punktaufrufe. Das sind sinnvolle Kandidaten für robuste Motor-Schaltkreise, keine unabhängige biologische Bestätigung. Die [Metadaten aller 11.308 vorgeschalteten Neuronen](banc_motor_upstream_metadata.parquet) enthalten Klassen, Typen und sensorische Körperteilbezüge. Damit lassen sich sensorische, lokale und weitergeleitete Eingänge nachvollziehbar auswählen.

## Was jetzt direkt nutzbar ist

Der Browserkörper liefert je Bein Stellung, Winkelgeschwindigkeit, Fußposition, Kontaktzustand und geometrischen Reichweitenfehler. Damit können wir eine Muskel-/Motorebene gegen konsistente Körperzustände entwickeln und testen. Die BANC-Tabellen liefern konkrete Ausgangsneuronen und ihre anatomischen Eingänge. Noch fehlen für eine physiologische Kopplung die neuronale Dynamik, Muskelparameter, Kräfte, Rezeptorantworten und deren Kalibrierung an veröffentlichten Bewegungsdaten.

BANC stammt von einer anderen Fliege als FAFB. Die BANC-Motor-IDs werden deshalb nicht als direkte Fortsetzung einzelner FAFB-Neuronen behandelt. Der vorhandene autonome Controller und der Original-FAFB-Graph bleiben von diesem reinen Evidenzexport unberührt. Details zum jetzigen geometrischen Körper stehen im [Körpermodell](../../app/BODY_MODEL.md).
