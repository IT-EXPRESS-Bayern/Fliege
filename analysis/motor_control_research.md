# Belegte Motorsteuerung für das Fliegenmodell

> Aktualisierung 27.09.2026: Original-CPG-Eingaben und archivierter Parametersatz0 sind inzwischen vorhanden; acht Nachrechnungen sind abgeschlossen. Aktueller Stand: [CPG-Ergebnisse](cpg_reproduction/results.md) und [Cloudübergabe](../docs/publication/README.md). Frühere offene Download-/Replikationspunkte in diesem Zwischenbericht sind dadurch teilweise überholt. Das Gesamtarchiv und seine gespeicherten Trajektorien bleiben ungeprüft.

Stand der Primärrecherche: **27. September 2026**. Dieses Dokument beschreibt Anschlussentscheidungen und prüfbare Vorhersagen. Die zugehörige [Quellen- und ID-Datei](motor_control_sources.json) enthält Veröffentlichungsstatus, genaue Fundstellen, lokale Prüfsummen und unveränderte Metadaten. Simulationsergebnisse unserer Fliege werden hier nicht als biologische Befunde ausgegeben.

## Was sich sinnvoll anschließen lässt

Die aussichtsreichste Erweiterung ist ein **durchgehender BANC-Schaltkreis innerhalb desselben Tiers**, mit expliziter Motor- und Sensorebene. BANC verbindet Gehirn und Bauchmark (VNC); seine Anatomie unterstützt lokale Rückkopplung zwischen Sensoren und Effektoren. FAFB bleibt ein anderes Individuum: Eine Typübereinstimmung erlaubt einen Vergleich, aber keine neue, tatsächlich beobachtete Verbindung zwischen den beiden Tieren. [Bates et al., Nature 2026](https://doi.org/10.1038/s41586-026-10735-w)

Für das Projekt ergeben sich vier priorisierte Aufgaben:

1. **DNa02/DNg13:** unilateral stimulieren, reale BANC-Pfade verfolgen und bein- sowie phasenspezifische Wirkung vergleichen.
2. **DNg100:** eine veröffentlichte VNC-Oszillatorsimulation reproduzieren, bevor ein neuer Laufgenerator frei angepasst wird.
3. **MDN→LBL40:** Rückwärtslaufen über Hinterbein-Standphase und Tibiaflexion prüfen; den ergänzenden LUL130-Zweig erst nach geklärter Zellzuordnung anschließen.
4. **Ein Gelenk mit Rückmeldung:** Femur–Tibia mit getrennten Beuge-/Streckmotoren und messbarer Kraft beziehungsweise validierter Gelenkdynamik aufbauen. Danach auf sechs Beine erweitern.

Das sind eigene Arbeitsentscheidungen aus der folgenden Evidenz, keine bereits erledigte biologische Rekonstruktion.

## Von absteigenden Neuronen zur Beinbewegung

| Neuron / Schaltung | Experimentell beobachtet | Konsequenz für Modell und Test |
|---|---|---|
| **DNa02** | Einseitige Aktivierung verkürzt den Schritt der gleichseitigen Beine. | Innenbein-Schrittlänge prüfen; ein pauschaler Yaw-Befehl reicht nicht als Reproduktion. |
| **DNg13** | Einzellige Strominjektion verändert die Schrittlänge der gegenüberliegenden Beine; Aktivierung unterstützt längere Außenschritte. | Getrennte Wirkungen in Stand- und Schwungphase messen. |
| **MDN** | Rückwärtsgang rekrutiert mehrere VNC-Zweige. **LBL40** beugt die Hinterbeintibia in der Standphase; **LUL130** hebt das Bein zum Schwungbeginn. | Rückwärtsgang benötigt einen eigenen phasengerechten Ablauf. Eine negative Rumpfgeschwindigkeit prüft diese Schaltung nicht. |
| **DNp09 / P9** | Vorwärtsstart und ipsilaterales Lenken; in anderen Versuchen geschwindigkeitsabhängiges Laufen/Erstarren. | Kontext, Stimulus und Treiberlinie dokumentieren. Kein universeller Geschwindigkeitsregler. |
| **BRK / AN19A018** | Aktives Anhalten und Gelenkwiderstand während des Putzens. | Stabile Haltung trotz hoher Motoraktivität zulassen; Nullgeschwindigkeit ist nicht gleich Nullaktivität. |

Die ersten beiden Zeilen stammen aus Verhalten, Elektrophysiologie und Connectomics von [Yang et al., Cell 2024](https://doi.org/10.1016/j.cell.2024.08.033). Beide Neuronen lenken ipsiversiv **relativ zur Soma-/Dendritenseite**; DNg13 kreuzt mit seinem Axon ins andere VNC-Halbfeld. Axonseite, Somaseite, Zielbeinseite und geometrisches Drehvorzeichen müssen getrennte Felder sein. Anatomische Pfade legen phasenabhängige Muskelrekrutierung nahe; nicht jede einzelne synaptische Wirkung wurde physiologisch gemessen.

Für DNa02 stützen Aktivitätsmessungen die Bedeutung der Links-rechts-Differenz. Ein berichteter fehlender signifikanter Hemmungseffekt auf Lenken begrenzt die Aussage, DNa02 sei allein notwendig. [Rayshubskiy et al., eLife 2025](https://doi.org/10.7554/eLife.102230)

Die MDN-Zweige sind funktionell untersucht; der LBL40-Zweig betrifft insbesondere T3. Die Details rechtfertigen eine Hinterbein- und Phasenprüfung, aber keine identischen Gains für alle Beine. [Feng et al., Nature Communications 2020](https://doi.org/10.1038/s41467-020-19936-x)

Bei P9 zeigte eine unabhängige Treiberlinie den Laufbeginn; Erstarren trat in dieser Studie nur in einer von vier geprüften Genotypkombinationen auf. [Bidaye et al., Neuron 2020](https://doi.org/10.1016/j.neuron.2020.07.032) Die frühere Arbeit berichtet ausdrücklich eine Abhängigkeit vom Zustand vor dem Stimulus. [Zacarias et al., Nature Communications 2018](https://doi.org/10.1038/s41467-018-05875-1) Zusätzlich benötigt DNp09 für Vorwärtslauf ein breiteres nachgeschaltetes DN-Netzwerk; MDN-Rekrutierung funktioniert anders. [Braun et al., Nature 2024](https://doi.org/10.1038/s41586-024-07523-9) Die BANC-Quellenannotation `halting` wird deshalb erhalten und durch diese Kontextinformationen ergänzt.

BRK-Neuronen sind **aufsteigende** Neuronen, keine DNs. Optogenetik, 3D-Kinematik und Schaltkreisanalyse unterscheiden ihren aktiven Bremsmechanismus von der Hemmung absteigender Laufkommandos durch „walk-OFF“-Neuronen. Wirkung und Übergang hängen von der Schrittphase ab. [Sapkal et al., Nature 2024](https://doi.org/10.1038/s41586-024-07854-7)

## Konkrete lokale IDs und Grenzen der Zuordnung

Alle folgenden Schlüssel sind **BANC v888**, als Zeichenketten zu lesen. Die Tabelle verwendet die aktuelle Metadaten-**Somaseite**, soweit für DNs anwendbar.

| Typ | Links | Rechts |
|---|---|---|
| DNa02 | `720575941510475536` | `720575941456897005` |
| DNg13 | `720575941445859754` | `720575941535086424` |
| DNp09 | `720575941566493282` | `720575941433155799` |
| DNg100 | `720575941626500746` | `720575941500851362` |
| LBL40, T3 | `720575941669107187` | `720575941669069043` |
| E1 / IN17A001, T1 | `720575941504247575` | `720575941554038555` |
| E2 / INXXX466, T1 | `720575941469024064` | `720575941519468654` |
| I1 / IN16B036, T1 | `720575941544954556` | `720575941441065919` |
| I2 / IN19A007, T1 | `720575941569601650` | `720575941461249747` |

Quelle: lokale `banc_888_meta.feather`; E1/E2/I2 sind zusätzlich mit der veröffentlichten CPG-Tabelle und dem Figure-3-Notebook abgeglichen. Die JSON-Datei enthält alle ausgewählten MDN-, DNb08- und seriellen Interneuronen-Zeilen sowie die FAFB-Matches. **`banc_888_id` ist der Graphschlüssel**: Das danebenliegende `root_id` bezeichnet teilweise eine spätere Materialisierung und ist nicht austauschbar. Beispielsweise hat DNp09 rechts später `720575941495160240`.

Mehrere BANC-Zellen können denselben `fafb_match` tragen, unter anderem MDN und DNb08. Das ist keine Eins-zu-eins-Zellidentität. Automatische Crosswalk-Texte mit `auto:` bleiben unbestätigte Zuordnungen. Insbesondere liefern Substrings wie `IN19A003` in automatischen Fremdtypfeldern auch sachlich andere Zelltypen. Für die Kandidatenauswahl wurde deshalb der exakte lokale `cell_type` benutzt.

Für **LUL130** und **CxHP8** wurde kein eindeutiger exakter lokaler Typ gefunden. Die Physiologie ist nutzbar; ein exakter BANC-Anschluss bleibt offen. Auch BRK-Aliase in automatischen Fremdtypfeldern sind keine ausreichende Freigabe einzelner Root-IDs.

Die historische Links-rechts-Inversion der FAFB-Bilder und spätere Korrektur der Annotationen ist in der [offiziellen Codex-FAQ](https://codex.flywire.ai/faq) beschrieben. Der lokale [Seitenabgleich](neuron_pathways/side_convention_audit.json) bewahrt abweichende Quellenkonventionen. Keine globale automatische Seitenumkehr.

## DNg100 und ein konkreter Kandidat für den Schrittrhythmus

Der **Preprint v2 vom 30.04.2026**, noch ohne Journalbegutachtung, verbindet wiederkehrende VNC-Simulationen mit Optogenetik: Stärkere DNg100-Aktivierung erhöht in kopflosen Fliegen Schrittfrequenz und Vorwärtsgeschwindigkeit. E1/E2 mit einem hemmenden Partner bilden einen **rechnerischen** CPG-Kandidaten; dessen biologische Notwendigkeit ist damit nicht bewiesen. DNb08 löst experimentell rhythmische Suchbewegungen aus. Seine Simulation war in BANC negativ, obwohl andere Datensätze Rhythmus zeigten. [Pugliese et al., v2](https://pmc.ncbi.nlm.nih.gov/articles/PMC13142387/)

Der Originalcode ist unter [Pugliese_2026](https://github.com/smpuglie/Pugliese_2026) geprüft, Commit `10e7661bf414ba7b4c2edf795cd36d0f878c17c0` vom 15.09.2026. Die BANC-Tabelle `wTable_20260217_fullData_consistentColumns.csv` enthält **4.963 Zeilen**. Die Indizes `1689`, `910`, `3334` sind im Figure-3-Notebook als E1, E2, I2 der BANC-Hemmversuche benannt und stimmen mit den IDs oben überein. Indizes gelten nur in exakt dieser Zeilenordnung.

Wichtige Reproduktionsdetails:

- „Left DNg100“ bedeutet im Paper **linkes Zielneuropil**, obwohl das Soma rechts liegt.
- Das Modell ist zunächst ein Ratenmodell; als Hz dargestellte Raten sind keine gemessenen Spikes. Die Autoren prüfen ergänzend ein LIF-Modell.
- Repository-Defaults: `tauMean=0.02 s`, `tauStdv=0.002 s`, Schwelle `7.5±0.6`, Gain `1±0.1`, Ratenobergrenze `200±10`, E/I-Multiplikator jeweils `0.03`. Schwelle/Input sind Modellgrößen; keine injizierten pA daraus machen.
- Defaultsimulation: 2 s, Ausgabeintervall 1 ms, Puls 0.02–1.999 s, `rtol=2e-6`, `atol=5e-9`. Das Beispiel-DNg100-YAML adressiert **MANC** und darf nicht als BANC-Konfiguration ausgegeben werden.
- Figure 2 lädt BANC-Lauf `33241778`, Figure 3 BANC-Silencing `34106247`. Das Figure-2-Notebook hat einen älteren Tabellen-Fallback von Dezember 2025. Verbindlich ist die gespeicherte `logs/run_config.yaml` des jeweiligen Laufs; dieser wurde hier noch nicht heruntergeladen.

Die [Originalresultate auf Zenodo](https://doi.org/10.5281/zenodo.22260924) umfassen 169,9 GB. Für einen nachvollziehbaren ersten Vergleich genügen zunächst die kleine BANC-Tabelle, passende Matrix und Run-Konfiguration. Die JSON-Datei enthält feste URLs/Größen; der Bericht behauptet keine bereits ausgeführte Replikation.

## Motorpool, Muskeln und Rückmeldung

**Gleiche Spikezahl bedeutet nicht gleiche Kraft.** An Vorderbein-Tibiaflexoren wurden mit Elektrophysiologie, optogenetischer Aktivierung und kalibrierter Kraftsonde etwa <0,1 µN pro Spike bei langsamen, ~1 µN bei intermediären und ~10 µN bei schnellen Motorneuronen gemessen. Langsame Einheiten werden typischerweise zuerst rekrutiert; sensorische Eingänge unterscheiden sich. Diese Werte sind versuchs- und geometrieabhängige Vergleichsgrößen, keine fertigen Gains für alle 391 Beinmotorneuronen. [Azevedo et al., eLife 2020](https://doi.org/10.7554/eLife.56754)

Die FANC-Rekonstruktion gruppiert Motorneuronen nach Muskelmodulen; bei Beinen skalieren viele prämotorische Eingangsgewichte mit der Motorneurongröße. Das erlaubt einen begründeten Test von Rekrutierungsreihenfolgen, ersetzt aber keine Kraftmessung. Supplementary Tables 1–3 und der [Originalcode](https://github.com/tuthill-lab/Lesser_Azevedo_2023) enthalten Zuordnung und Matrizen. [Lesser, Azevedo et al., Nature 2024](https://doi.org/10.1038/s41586-024-07600-z)

| Rückmeldung | Primärbefund | Umsetzbare Prüfung |
|---|---|---|
| FeCO claw / hook / club | Unterschiedliche Populationen kodieren Gelenkstellung, richtungsabhängige Bewegung und Vibration. | Winkel und Winkelgeschwindigkeit separat einspeisen; die aktuelle Kontakt-Boolean ist keine Vibrationsmessung. [Mamiya et al. 2018](https://doi.org/10.1016/j.neuron.2018.09.009) |
| Hook während Eigenbewegung | Selektive präsynaptische Hemmung durch GABAerge 9A-Interneurone reduziert vorhersehbare Bewegungsrückmeldung. | Aktive und passive Bewegung bei gleichem Gelenkverlauf vergleichen; Sensor-Gain darf zustandsabhängig sein. [Dallmann et al. 2025](https://doi.org/10.1038/s41586-025-09554-2) |
| CxHP8 | Kalziumsignal bei anteriorer Grenzstellung; Aktivierung verursacht posterioren Reflex; Hemmung verändert den Übergang von Schwung zu Stand. | Sensorantwort und Bewegungsumkehr an vorderer Reichweitengrenze testen. Andere Hair-plate-Funktionen sind überwiegend anatomische Vorhersagen. [Pratt et al. 2026](https://doi.org/10.1038/s41467-026-69333-z) |

**Transmitter und mechanische Wirkung getrennt behandeln.** Ein Feeding-Motorneuron kann mit Glutamat seinen Muskel erregen und zentral eine Disinhibitionssequenz ermöglichen; dies wurde mit vier simultanen Elektroden untersucht. Aus einer zentralen `-p_Glu`-Konvention folgt daher kein negatives Muskelkommando. Die Quelle belegt diesen Mechanismus beim Fressen, nicht pauschal für jedes Beinmotorneuron. [Sui et al., Nature Neuroscience 2026](https://doi.org/10.1038/s41593-026-02412-y)

Ein **begutachteter Preprint** zeigt außerdem entwicklungs- und muskelspezifische Glutamatrezeptoren sowie extrasynaptisches GluClα in adulten Bein-/Flugmuskeln. Die vorgeschlagene Tonusregulation bleibt dort eine Hypothese. Larvenparameter oder ein einziges Glutamatvorzeichen genügen nicht. [Sustar et al., eLife v1, 15.06.2026](https://doi.org/10.7554/eLife.111371.1)

BANC führt `neurotransmitter_predicted` und `neurotransmitter_verified` getrennt. Die [Originalpipeline](https://github.com/htem/synister_banc) klassifiziert acht Transmitterklassen an detektierten Synapsen mit `size>5`. Eine Vorhersage ist keine Rezeptor- oder NMJ-Messung; eine muskelspezifische Genauigkeit wurde hier nicht verifiziert. Kuratierte Aussagen müssen bis zu Studie und Typ-Match rückverfolgbar bleiben. [Ground-truth-Projekt](https://github.com/flyconnectome/drosophila_neurotransmitters)

**Konkreter Versionskonflikt:** Die CPG-Originaltabelle führt 151 Motorzeilen, davon 43 mit `neurotransmitter_verified=glutamate`. 42 dieser IDs sind im lokalen BANC-Metadatenschnappschuss exakt wiederzufinden: sieben Halsmotorneuronen mit ebenfalls verifiziertem Glutamat und **35 Vorderbeinmotorneuronen, deren lokales Verified-Feld leer ist**. Die 43. ID ist dort nicht exakt enthalten. Die Quellenfelder werden nebeneinander erhalten; die CPG-Angabe ist eine kuratierte Quellenannotation, deren zugrunde liegende experimentelle Evidenz hier noch nicht neu geprüft wurde. Kein stilles Überschreiben und keine ungeprüfte Übertragung auf alle 391 Beinmotorneuronen.

## Welche vorhandenen Datensätze welche Lücke schließen

| Ressource | Konkreter Nutzen | Grenze |
|---|---|---|
| **BANC v888** | Zusammenhängende sensorisch–prämotorisch–motorische Wege in einem weiblichen Tier; lokal 391 identifizierte Beinmotorneuronen samt Eingangskanten. | Anatomie, keine vollständige Physiologie. v2/v3-Kantendetektoren sind alternative Exporte. |
| **MANC** | DN→IN→MN-Pfade und Muskelgruppen; Supplementary file 1 verbindet anatomische Typen mit Literatur. | Anderes männliches Tier und VNC; direkte DN-Eingänge machen bei den meisten MNs nur einen kleinen Anteil aus. [Cheong et al., eLife Version of Record, 20.07.2026](https://doi.org/10.7554/eLife.96084.3) |
| **MaleCNS** | Zweiter vollständiger Gehirn–VNC-Graph zur Prüfung von Typen/Pfadmotiven und Geschlechtsunterschieden. | Homologie ist kein beliebig austauschbarer ID-Schlüssel. [Berg et al., Cell 2026](https://doi.org/10.1016/j.cell.2026.08.015) |
| **FANC-Motorstudien** | Detaillierte Vorderbein-Motor-/Prämotorzuordnung und Physiologiebezug. | Die besonders gründliche T1L-Rekonstruktion darf nicht still auf alle Beine übertragen werden. |
| **NeuroMechFly v2 / FlyGym** | Körperphysik, Kontakt, Sinne und Regelkreis als Vergleichsrahmen. | Die veröffentlichten CPG-/Hybridcontroller sind zusätzliche Steuerungsmodelle. [Wang-Chen et al. 2024](https://doi.org/10.1038/s41592-024-02497-y) |
| **FlyBody** | MuJoCo-Körper mit Gelenkmomenten, Trägheit, Kontakten und Adhäsion; lokale Körperdateien vorhanden. | Gelernte Steuerungen und Drehmomentaktoren ergeben keine direkte MN→Muskel-Karte. [Vaxenburg et al. 2025](https://doi.org/10.1038/s41586-025-09029-4) |

Die [lokale Motorschnittstelle](body_neural_interface/README.md) enthält 113 Femur–Tibia-, 30 Tibia–Tarsus-, 110 Coxa–Trochanter-, 56 Coxarichtungs-, 48 Langsehnen- und 34 unbestimmt wirkende Motorneuronen. Das sind Zuordnungskandidaten. Zu diesem Recherchezeitpunkt sind Vorzeichen/Gain offen und alle 391 Anschlüsse deaktiviert.

## Anforderungen an den 3D-Anschluss und die wissenschaftlichen Tests

Das [vorhandene Körpermodell](../app/BODY_MODEL.md) liefert Gelenkwinkel und Winkelgeschwindigkeit, aber noch keine Kräfte. Femur–Tibia und Tibia–Tarsus haben **Beugung = positiver Winkel ab gerader Stellung**. Coxa–Trochanter ist vereinfacht; reale Coxaachsen und Langsehnen fehlen. Die Rumpfbewegung folgt Geschwindigkeitskommandos. Diese Geometrie eignet sich jetzt für Seiten-, Achsen-, Reichweiten- und Gelenkprüfungen.

**Eigener Modellvorschlag:** Nichtnegative Aktivierung pro Muskel-/Motoreinheit getrennt führen. Antagonisten erst über ihre kalibrierten Momentarme und Gelenkdynamik zusammenführen; ihre Summe als Koaktivierung erhalten. Damit kann eine kleine Nettobewegung hohe Aktivierung und Steifigkeit begleiten. Für echte Krafttests werden Trägheit, Schwerkraft, Kontaktkraft, Adhäsion, Aktivierungsdynamik und Muskel-/Sehnenparameter benötigt. Kontakt-Boolean oder Winkelgeschwindigkeit dürfen nicht als gemessene Belastung ausgegeben werden.

| Test | Vorher festzulegende Messgröße | Mindestkontrolle / Interpretation |
|---|---|---|
| Unilaterales DNa02/DNg13 | Schrittweite jedes Beins, Stand-/Schwungdauer, Winkelverlauf, Drehrichtung | L/R spiegeln; Sham; gleiche Ausgangsgeschwindigkeit; Wirkung nicht erst im Adapter fest hineinprogrammieren. |
| DNg100 | Spektrum/Autokorrelation der MN-Aktivität, Gelenkfrequenz, Reihenfolge, Interbeinphase | Reproduktion fester Originalparameter; E1/E2/I2 getrennt hemmen; negatives DNb08-BANC-Ergebnis erhalten. Rhythmus allein bestätigt keinen stabilen Gang. |
| MDN/LBL40 | T3-Tibiaflexion während Rückwärts-Standphase; Schwungbeginn | LBL40-Hemmung, Ziel-MN-Hemmung, gleich starke Kontrollstimulation. LUL130-Zweig erst nach eindeutigem Match. |
| Antagonisten / BRK | Aktivität beider Pools, Nettomoment, Gelenkwiderstand unter äußerer Störung | Koaktivierung gegenüber gleich großem Einzelpoolreiz; reine Kinematik kann Widerstand nicht messen. |
| Motorrekrutierung | Schwelle und Kraftfolge langsam→intermediär→schnell | Gleiche Geometrie/Last; Messwerte aus Fit und unabhängiger Prüfung trennen. Noch unbekannte Poolzuordnung bleibt unbekannt. |
| Propriozeption | Gelenkwinkel-/Geschwindigkeitsantwort, Latenz, Grenzreflex | Sensor offen/geschlossen; aktive/passive Bewegung; Ausfall der ausgewählten Sensoren. Belastungsreflex erst mit Kraftsensorik. |

Erst Parametersätze einfrieren, dann vorab benannte Perturbationen auswerten. Strukturprüfung, eigenes Simulationsergebnis, Übereinstimmung mit einem veröffentlichten Verhalten und biologische Kausalität sind getrennte Evidenzstufen. Neue fehlende Kanten müssen als Hypothese mit Quelle und Sensitivitätstest sichtbar bleiben. Keine dieser Arbeiten liefert schon alle Zeitkonstanten, Rezeptoren, Muskelkräfte und Sinnestransformationen einer individuellen Fliege; gezielte Validierung bleibt nötig.
