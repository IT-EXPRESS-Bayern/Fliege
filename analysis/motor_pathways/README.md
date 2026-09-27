# Beobachtete Wege vom absteigenden Neuron zum Beinmotor

Stand: 27.09.2026. [Motorlabor](http://127.0.0.1:4173/motor.html). Grundlage sind die lokal SHA-256-geprüften BANC-v888-Metadaten und die getrennten Detektorexporte v2/v3 derselben weiblichen Fliege. **FAFB v783 ist ein anderes Tier. Keine dieser Kanten wurde in den FAFB-Graphen ergänzt.**

## Umfang und Auswahl

Aus BANC Supplementary Data 9 wurden die Typen mit den Quellenrollen `steering`, `walking`, `grooming`, `halting`, `landing` und `escape_takeoff` gewählt. Exakter Typ- und Klassenabgleich mit `banc_888_id` ergibt **92 absteigende Neuronen aus 36 Typen**. Die Literaturrollen sind Typ-Evidenz; putative oder kontextabhängige Angaben bleiben in den Quellenfeldern erhalten. Die Zielmenge umfasst die zuvor geprüften **391 Bein-Motorneuronen**.

Es gibt **1.618 direkte** DN–Motor-Verbindungen und **448.942 vollständige Zwei-Kanten-Wege** in mindestens einem der beiden Detektoren. Eine Mischung, bei der nur die erste Kante in v2 und nur die zweite in v3 existiert, ist ausdrücklich ausgeschlossen. Für die vier DNa02/DNg13-Zellen wurden zusätzlich **5.628.994 vollständige Drei-Kanten-Wege** erfasst. Mehrere Wege zum selben Motor sind unterschiedliche Wege, keine zusätzlichen Motorneuronen und keine unabhängigen Synapsenmessungen.

Alle Ein- und Zwei-Kanten-Wege sind als Parquet gespeichert. Für Drei-Kanten-Wege werden vollständige Zählungen und je DN/Motor die drei stärksten Beispiele jedes Detektors sowie der gemeinsamen Menge gespeichert. Drei-Kanten-Erreichbarkeit für andere DN-Typen wurde nicht untersucht.

**1.739 Browserbeispiele** enthalten auf jeder Kante mindestens fünf Kontakte in **beiden** Detektoren. Die Auswahl nimmt je DN, Bein und Pfadlänge bis zu drei Wege mit dem höchsten minimalen Kantenwert; das ist eine Heuristik zur Inspektion, keine Wahrscheinlichkeit oder gemessene funktionelle Stärke.

## DNa02 und DNg13: reale Motorziele

Alle Zahlen unten verlangen mindestens fünf Kontakte **je Kante**. „Gemeinsam“ verlangt denselben vollständigen Weg in beiden Detektoren, nicht nur getrennte Erreichbarkeit derselben Endpunkte.

| DN, Soma-Seite | BANC-v888-ID | direkte Motoren gemeinsam | Motoren innerhalb 2 Kanten v2 / v3 / gemeinsam | Motoren über 3 Kanten gemeinsam |
|---|---|---:|---:|---:|
| DNa02 links | 720575941510475536 | 16 | 154 / 170 / **151** | 376 |
| DNa02 rechts | 720575941456897005 | 14 | 173 / 187 / **171** | 383 |
| DNg13 links | 720575941445859754 | 3 | 202 / 187 / **173** | 362 |
| DNg13 rechts | 720575941535086424 | 2 | 224 / 218 / **213** | 376 |

Die letzte Spalte zählt Endpunkte von Wegen mit genau drei Kanten. Alle Schwellen-1/5-Ergebnisse und beide Detektoren stehen in [reachability.csv](reachability.csv) und [three_edge_reachability.csv](three_edge_reachability.csv).

### Konkrete Pfadbeispiele

| Start → Zwischenzelle → Motor | Kontakte v2 | Kontakte v3 | anatomische Motoraktion |
|---|---:|---:|---|
| DNa02 L `720575941510475536` → IN08A006 `720575941537865165` → `720575941455787245` | 142 → 442 | 152 → 450 | LF, Coxa nach anterior |
| DNg13 L `720575941445859754` → IN19A016 R `720575941512779084` → `720575941353301552` | 60 → 136 | 61 → 128 | RF, Coxa nach posterior |
| DNg13 L `720575941445859754` → IN21A007 `720575941571487134` → `720575941573687049` | 46 → 65 | 45 → 70 | RM, Femur–Tibia beugen |
| DNg100 R `720575941500851362` → IN09A002 `720575941592869928` → `720575941451737978` | 105 → 93 | 116 → 91 | LH, Femur–Tibia beugen |
| DNb08 R `720575941545432425` → INXXX464 `720575941564525480` → `720575941432965902` | 48 → 66 | 47 → 66 | RM, Femur–Tibia strecken |

LF/RF = linkes/rechtes Vorderbein, LM/RM = Mittelbein, LH/RH = Hinterbein. Die Beinzuordnung kommt vom Motorziel, nicht von der DN-Soma-Seite. Der DNg13-Pfad zur Gegenseite macht diese Unterscheidung konkret. Eine anatomische Beuge-/Streckaktion bedeutet nicht, dass DN-Aktivierung im Tier oder im ungeprüften Modell diese Aktion netto auslöst: Zwischenzellen, Hemmung und andere parallele Wege sind relevant.

## Weitere konkrete Motor-Kandidaten

**DNg100:** Soma links `720575941626500746`, rechts `720575941500851362`; gemeinsam ≥5 ergeben sich 58/54 direkte Motorziele und 306/307 Ziele innerhalb zwei Kanten. Für die erste Zelle unterscheidet sich die spätere Metadaten-`root_id` vom erforderlichen `banc_888_id`. Es wird ausschließlich der v888-Schlüssel verwendet.

**DNb08:** Vier v888-Zellen `720575941415598737`, `720575941724184890`, `720575941534881368`, `720575941545432425` erreichen gemeinsam ≥5 jeweils 212, 252, 218 und 214 Motoren innerhalb zwei Kanten; keine hat in dieser Schwelle eine direkte Motorverbindung. Die beobachteten Wege laufen über Zwischenzellen.

Der [Pugliese-Preprint, Version 2 vom 30.04.2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13142387/) liefert zusätzliche Experimente und Modelle zu DNg100/DNb08 sowie einem vorgeschlagenen Rhythmusgenerator. Die Arbeit ist noch nicht begutachtet. Ein darin nach Zielneuropil als „links“ bezeichnetes DNg100 muss nicht Soma links sein. Die hier berechneten Pfade reproduzieren weder das veröffentlichte dynamische Modell noch seine Parameter- oder Versionswahl.

**DNp09:** Die Rohannotation `halting` bleibt erhalten. Die publizierte Wirkung hängt von Verhaltenszustand und experimenteller Treiberlinie ab; DNp09 wird nicht zu einem universellen Vorwärtskanal umgedeutet. [Zacarias 2018](https://doi.org/10.1038/s41467-018-05875-1), [Bidaye 2020](https://doi.org/10.1016/j.neuron.2020.07.032).

## Strukturelle Eingriffe: Knoten entfernen

Für jeden der vier priorisierten DNs wurde aus **allen** gemeinsamen Zwei-Kanten-Wegen ≥5 die Zwischenzelle gewählt, die die meisten dieser Wege vermittelt. Nach Entfernen wurden die verbleibenden Wege und Ziele neu gezählt; direkte Wege bleiben erhalten. Die Tests verwenden die vollständige Wegemenge, nicht die gekürzte Browserauswahl.

| DN | entfernte Zwischenzelle | Zwei-Kanten-Wege vorher → nachher | innerhalb 2 Kanten erreichbare Motoren vorher → nachher |
|---|---|---:|---:|
| DNa02 links | INXXX053 | 382 → 356 | 151 → 139 |
| DNa02 rechts | INXXX053 | 434 → 409 | 171 → 160 |
| DNg13 links | IN16B016 | 597 → 560 | 173 → 171 |
| DNg13 rechts | IN16B016 | 615 → 581 | 213 → 208 |

Gradangepasste Kontrollzwischenzellen außerhalb der jeweiligen ausgewählten DN-Wege lassen die Zahlen unverändert. Diese Kontrollen sind absichtlich außerhalb der DN-Wege gewählt; ihr Nullresultat ist daher erwartbar und kein unabhängiger Nachweis der besonderen Funktion des entfernten Knotens. Entfernen des Start-DNs beseitigt ebenfalls erwartbar alle von ihm ausgehenden Wege. [Alle IDs, Verluste und Kontrollen](structural_ablations.json).

Es handelt sich um **Knotenentfernung und anatomische Erreichbarkeit**, nicht um Silencing in einer kalibrierten Spike-Simulation oder einen Versuch am Tier. Nicht mehr innerhalb zweier Kanten erreichbar heißt nicht insgesamt unerreichbar: längere Wege können bestehen bleiben.

## FAFB-Homologien und Transmittergrenzen

[93 gültig bewertete Quellmatch-Zeilen](reviewed_dn_homologies.csv) betreffen die untersuchten DN-Zellen und wurden nach Möglichkeit über Supervoxel-Anker, direkte v888-ID oder Versions-Crosswalk aufgelöst. Alte Query-IDs bleiben gespeichert. Die Metadaten-Spalte `fafb_match` und die getrennte Reviewed-Match-Datei sind **keine identischen Zuordnungen**: Bei 46 der DN-Zellen mit Reviewed-Matches steht der Metadaten-Match nicht in ihrer Reviewed-Liste. Beispiel DNa02 links: Metadaten `720575940629327659`, Reviewed-Match `720575940604737708`. Beide Angaben bleiben sichtbar; Seiten- und Homologiefragen werden nicht durch stilles Überschreiben entschieden.

Alle Homologien liegen zwischen verschiedenen Fliegen. Ein homologiegestützter Zelltypvergleich erlaubt keine Übertragung einer individuellen BANC-Kante als gemessene FAFB-Synapse.

Die Knotendaten behalten vorhergesagten und verifizierten Neurotransmitter getrennt. Die 391 Beinmotoren haben in der Metadatei keine verifizierte Transmitterangabe; vorhergesagte Labels sind deshalb keine bestätigten Wirkungszeichen an Muskel oder Folgezelle. **Es wird keine Vorzeichenkette und kein Muskelkraft-Gewinn aus NT-Labels abgeleitet.** Zielaktionen stammen aus anatomischen Muskelannotationen. Der [separate Motoratlas](../motor_output_atlas/) prüft die Transmitterkonflikte umfassender.

## Dateien, Prüfung und Wiederholung

- [audit.json](audit.json): alle Mengenzahlen, Quellenhashes, Erreichbarkeit und strukturellen Eingriffe.
- [validation.json](validation.json): **594 unabhängige Prüfungen bestanden**. Beide vorgefilterten Motoreingangsdateien stimmen exakt mit frischen Filtern der Originalgraphen überein; jede dargestellte Kante hat die Originalzählung in v2 und v3. Vollständige Zwei-Kanten-Mengen wurden auf echte Detektorwege, Eindeutigkeit und Zählsummen geprüft.
- [path_examples.csv](path_examples.csv): kompakte Endpunkte, Zwischenschritte, Aktionen und getrennte Kontaktzahlen.
- `all_direct_paths.parquet`, `all_two_edge_paths.parquet`: vollständige Ein-/Zwei-Kanten-Mengen mit nullable getrennten Versionen.
- `top_three_edge_paths.parquet`: priorisierte Drei-Kanten-Wege; Zählübersicht enthält auch die nicht dargestellten Wege.
- [Browserdaten](../../app/data/motor_pathways.json): exakte String-IDs, 391 Motorreferenzen, 92 DNs, 1.739 Beispiele, Grenzen und Ablationsresultate.

```powershell
analysis/.venv/Scripts/python.exe analysis/motor_pathways/build.py
analysis/.venv/Scripts/python.exe analysis/motor_pathways/validate.py
```

Der Aufbau begrenzt DuckDB auf 1,5 GB Arbeitsspeicher und zwei Threads. Zeitstempel verändern sich bei Wiederholung; Auswahl und Wegzählungen sind deterministisch.

Quellen: [BANC-Datensatz und Lizenz CC BY 4.0](https://doi.org/10.7910/DVN/7WTH1N), [BANC-Studie](https://doi.org/10.1038/s41586-026-10735-w), [DNa02/DNg13-Funktionsarbeit](https://doi.org/10.1016/j.cell.2024.08.033). Tabellenzeilen, DOI-Angaben und Provenienz bleiben in den exportierten DN-Datensätzen enthalten.
