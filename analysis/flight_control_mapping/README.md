# Flügel, Halteren und ihre BANC-Verbindungen

Stand 27.09.2026. Dies ist ein überprüftes anatomisches Anschlussstück für einen Flugversuch, keine bereits fliegende oder biologisch validierte Rekonstruktion. [Audit](audit.json), [Browserdaten](../../app/data/flight_control_mapping.json), [Primärquellen](sources.json), [offene Lücken](gaps.json).

## Was tatsächlich zugeordnet ist

| Ebene | Umfang und Grenze |
|---|---|
| Motorinventar | 64 Quellzeilen mit Ziel `wing`, 27 mit `haltere`; alle genauen IDs in [motor_inventory.csv](motor_inventory.csv). |
| Echte Flügelmotor-Klasse | 62 Zellen: 24 `wing_power`, 24 `wing_steering`, 12 `wing_tension`, 2 unbekannte Flügelmotoren. Die zwei übrigen Wing-Zeilen heißen PSI und sind peripher-intrinsische Neuronen. |
| Konflikte | 6 Zeilen sind als Poolkandidaten ausgeschlossen: 2 PSI, 2 MNhl88 mit Beinklasse/-funktion trotz Halterenziel und 2 MNhl59 mit `unknown_leg_movement`. [Konfliktliste](annotation_conflicts.csv). 85 verbleibende Kandidaten sind anatomisch, nicht kraftkalibriert. |
| Sinneszellen | 1.032 Wing-/Halteren-Zeilen, darunter auch Geschmack und Tastsinn. 245 tragen Propriozeptionsannotation; 244 sind proofread. Die 46 Halteren-Campaniform-Zellen sind eine eigene Teilmenge. [Inventar](sensory_inventory.csv). |
| Absteigende Neuronen | 92 exakte Kandidaten aus publizierten Flug-/Landungs-/Starttypen; 59 proofread Zellen der priorisierten Gruppen DNg02, DNg07, DNp03, DNp07, DNp10 werden auf Motorwege geprüft. DNg02 umfasst 38 Roots mit Untertypen a,b,c,d,f,g,h. [Liste](dn_candidates.csv). |
| Visuelle Kandidaten | 38 HS-/VS-Familien-Zellen mit LPTC-Klasse; ihre genaue Reizübertragung bleibt unbekannt. [Liste](visual_candidates.csv). |

Keine 64-bit-ID wird in eine Gleitkommazahl umgewandelt. BANC ist ein anderes Tier als FAFB oder FANC. Die Literaturrolle ist eine Zelltyp-/Familienzuordnung; ein einzelner BANC-Root wurde dadurch nicht physiologisch vermessen. Grundquelle: [BANC 2026](https://www.nature.com/articles/s41586-026-10735-w).

## Seiten und konkrete Anschlüsse

`sourceSide` bleibt das Originalfeld. `effectorSide` wird ausschließlich aus dem eindeutigen Seitenpräfix des peripheren Nervennamens abgeleitet. Das ist hier entscheidend: DLM5 `720575941596050112` hat Quellseite links, aber einen rechten Nerv; `720575941692400603` umgekehrt. Die experimentelle Anatomie beschreibt MN5 als kreuzend, während MN1–4 ipsilateral innervieren. Die chemischen Graphen enthalten die dort untersuchte elektrische Kopplung nicht. [Hürkey et al. 2023](https://www.nature.com/articles/s41586-023-06099-0).

| Muskel | Linker Effektor | Rechter Effektor | Quellrolle |
|---|---|---|---|
| b1 | `720575941521196211` | `720575941549822781` | tonic_wing_steering |
| b2 | `720575941624155644` | `720575941655597785` | phasic_wing_steering |
| hDVM | `720575941546998972` | `720575941572052381` | haltere_power |

Diese Rollen liefern keinen individuellen Roll-/Nick-/Gier-Drehmomentsinn. `kinematicSign`, `forceGain` und `wingbeatRatePerSpike` bleiben null. Insbesondere dürfen erregend/hemmend im zentralen Netz und Kraftwirkung am Muskel nicht gleichgesetzt werden.

## Vollständige Pfade innerhalb des definierten Ausschnitts

| Alternative | Direkte Pfade ≥1 | Zwei-Kanten-Pfade ≥1 | Vollständige Pfade ≥5 pro Kante | Verwendete Kanten ≥5 |
|---|---:|---:|---:|---:|
| BANC v2 | 1.145 | 152.402 | 10.625 | 5.529 |
| BANC v3 | 1.281 | 188.914 | 15.347 | 7.304 |

Startpunkte sind die 244 proofread Propriozeptoren und 59 priorisierten DNs; Ziele die 85 konfliktfreien Motor-Poolkandidaten. Zwischenzellen sind proofread und weder sensorisch noch motorisch. Jeder Pfad liegt vollständig in **einer** Detektorversion. Kanten beider Versionen werden niemals addiert. [paths_v2.parquet](paths_v2.parquet) und [paths_v3.parquet](paths_v3.parquet) enthalten alle Pfade dieses Ausschnitts. Die Browserdatei zeigt je 160 Rangbeispiele, enthält aber sämtliche 5.529/7.304 verwendeten Kanten. Fehlende Browserbeispiele belegen keine fehlende Verbindung.

Für die ausgewählten HS/VS-Kandidaten fanden sich keine direkten Kanten zu den priorisierten DNs, jedoch 1.016/1.445 vollständige Zwei-Kanten-Wege in v2/v3. Davon besitzen 18/32 auf **beiden** Kanten mindestens fünf Kontakte, mit 20/41 verschiedenen Kanten. Beispiel v2: HSS `720575941574535240` → PS080 `720575941572516873` → DNg02_f `720575941587856951`, Kontaktzahlen 13 und 21. Diese beobachtete Anatomie verbindet den visuellen Kandidatenausschnitt mit einer DN-Population; Richtungstuning, Rezeptoren und Dynamik sind dadurch nicht gemessen.

## Mechanismen für das Körpermodell

**Leistung:** DLM/DVM-Motoraktivität verändert die langsamer wirkende Calcium-/Leistungsbereitstellung. Die schnelle Dehnungsaktivierung und Thoraxmechanik erzeugen viele Kontraktionen pro Nervenimpuls. Deshalb ist „Spikefrequenz = Flügelschlagfrequenz“ falsch. Ein Modell darf einen mechanischen Schwinger mit neural moduliertem Antrieb prüfen; dessen Kräfte und Parameter bleiben Annahmen. [Gordon & Dickinson 2006](https://pmc.ncbi.nlm.nih.gov/articles/PMC1449689/).

**Steuerung:** Tonic/phasic bezeichnet unterschiedliche Aktivierungsmuster, nicht eine fertige Achsensteuerung. DNg02 wurde mit Optogenetik und Funktionsbildgebung als Populationssteuerung der Flügelschlagamplitude untersucht. Die Studie weist den hier vorhandenen einzelnen Untertyp-Roots keine kalibrierten Flugachsen zu; ihre VNC-Ausgänge können die Mittellinie kreuzen. [Namiki et al. 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9206711/).

**Sensorik:** Wing-/Hinge-Campaniform-, Chordotonal- und Haarplattenrezeptoren liefern verschiedene mechanische Signale. Der 2026 erschienene Flügelatlas ordnet periphere Rezeptoren in **FANC** zu; Tegula-Campaniform-Zellen projizieren zu b1. Der neue Halterenatlas verwendet FANC v840 und beschreibt unterschiedliche afferente Gruppen. Diese Quellen helfen beim Typabgleich, ersetzen aber keine BANC-Root-zu-Phasen-/Strain-Zuordnung. [Lesser et al. 2026](https://pubmed.ncbi.nlm.nih.gov/41805047/), [Dhawan et al. 2026](https://www.sciencedirect.com/science/article/pii/S0960982225016720).

**Halteren:** Sie liefern schnelle mechanische Rückmeldung, können ihre Bewegung aber auch aktiv verändern. Ein Regelkanal „Körperrollgeschwindigkeit → Flügelkorrektur“ ist daher eine vereinfachte technische Hypothese. Die echte Kette umfasst Halterenbewegung, mechanische Dehnung und phasenabhängige Sensorantwort. [Verbe et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11338719/). Mechanische Thoraxkopplungen tragen zur Wing-/Halterenphasenkopplung bei; daraus folgt kein root-spezifischer Zahlenwert für unser Modell. [Deora et al. 2015](https://pmc.ncbi.nlm.nih.gov/articles/PMC4321282/).

**Verhaltenszustand:** DNp07/DNp10 sind Landungskandidaten mit Flugzustandsabhängigkeit. Landung ist keine bloße negative Poweraktivität und umfasst die Beine. [Ache et al. 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC7444277/).

## Originales 3D-/Physikvorbild

[flybody_mechanics.json](flybody_mechanics.json) hält die fünf lokal gelesenen Originaldateien mit SHA256 fest. Die XML liefert drei Flügelachsen je Seite und ellipsoide Fluidelemente. Rohwerte: Zeitschritt 0,0001; Gravitation −981; Dichte 0,00128; Viskosität 0,000185. Diese Modellwerte sind **keine direkt einsetzbaren SI-Zahlen**; das vollständige Einheitensystem muss gemeinsam konvertiert werden. Yawbereich −1,5…1,5, Roll −1…1,5, Pitch −1,27…2,92 rad.

Der Originalcode `flight_imitation.py` kombiniert einen WingBeatPatternGenerator mit trainierten Restaktionen. Das publizierte Modell nutzt phänomenologische Fluidkräfte und gelerntes Verhalten; es ist keine BANC-Gehirnrekonstruktion. Seine Quellgeometrie und ein Flügelschlaggenerator beweisen noch keinen stabilen Flug unseres Browsers. [FlyBody 2025](https://www.nature.com/articles/s41586-025-09029-4).

## Reproduzieren und wissenschaftlich prüfen

`analysis/.venv/Scripts/python.exe analysis/flight_control_mapping/build.py`

Der Builder prüft sämtliche exportierten Browserkanten erneut gegen den jeweiligen Originalgraphen. IDs, unbekanntes Tuning, Quelltransmitter und angenommene mechanische Wirkung bleiben getrennte Felder. Die Flug-Dynamiktests selbst gehören in ein getrenntes Protokoll: kein Auftrieb bei stillstehenden Flügeln, Einheitensystem und Energiebilanz, symmetrischer Antrieb, einseitige Ablation, Sensoren offen/eingefroren/verzögert, echte Störung gegenüber Replay und Zeitschrittvergleich. Negative Resultate bleiben erhalten. Erst danach lässt sich sagen, welche Modellvariante fliegt; biologische Validierung und vollständige Autonomie benötigen zusätzliche Evidenz.
