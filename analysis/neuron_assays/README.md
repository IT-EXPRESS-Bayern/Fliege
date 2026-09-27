# Funktionsprüfungen am vollständigen v783-Graphen

**Stand: 27.09.2026.** 42 vorab definierte Modellläufe über sechs sensorische Eingangsgruppen sind ausgeführt. Dazu kommen vier Diagnose-Läufe zur misslungenen JO-CE/JO-F-Vorhersage. Der originale Graph wurde unverändert verwendet: **139.255 Neuronen, 15.091.983 gerichtete Neuronenpaare, 54.492.922 gewichtete Synapsenkontakte**. Sämtliche Graphdateien wurden gegen die SHA-256-Werte im Manifest geprüft.

Die Experimente messen **Antworten dieses Rechenmodells**. Sie bestimmen weder die reale Funktion eines bislang unbekannten Neurons noch bestätigen sie eine vollständige biologische Emulation. Die Zuordnungen für die Eingangs- und Auslesezellen kommen aus überprüfbaren veröffentlichten Tabellen; die Modellantwort ist eine zusätzliche, getrennte Evidenz.

## Was tatsächlich getestet wurde

- Eingänge: 69 exakt vorhandene JO-C/E-, 60 JO-F-, 145 gesamte JO-, 20 Zucker-, 18 Wasser- und 20 Bitter-Sensor-Kandidaten. Fehlende alte Root-IDs wurden ausgeschlossen. Keine IDs wurden numerisch gerundet oder durch ähnlich benannte Zellen ersetzt.
- Neun gemeinsam überwachte Auslesen: aBN1, aDN1, aDN2, beide aktuellen MN9, beide DNa02 und beide DNg13.
- Jeder Hauptlauf: 600 ms, 1-ms-Schritte, Reizfenster `[100,500)` ms, somit 400 ms aktive Reizung. Die Datenzeile bei 101 ms folgt dem ersten Schritt des Reizfensters.
- Bedingungen: ohne Reiz, 50 Hz, 150 Hz, Eingangssilencing, Auslesesilencing und Reizung anderer gradangepasster Sensorneuronen. Die drei JO-Szenarien enthalten zusätzlich aBN1-Silencing und Stilllegung eines gradangepassten Kontrollinterneurons.
- Der gesamte Graph ist geladen. Nur aktive Ereignisse werden berechnet; das ist keine Auswahl eines kleinen Ausschnitts. Eingangs-Spikes sind experimentell vorgegeben. Auslese-Spikes werden ausschließlich durch synaptische Propagation erzeugt.
- Pro Schritt sind die tatsächlichen Auslese-Spikes, Modellspannungen und Gesamtspikezahlen gespeichert. Alle aktiven Neuronen sind außerdem pro Lauf exakt aufgelistet.

## Ergebnisse bei 150 Hz Eingang

Ausleserate im 400-ms-Reizfenster; **Modell-Hz**, nicht am Tier gemessen. Eine Rate von 2,5 Hz entspricht hier einem Spike.

| Eingang | aBN1 | aDN1 | aDN2 | MN9 rechts | MN9 links |
|---|---:|---:|---:|---:|---:|
| JO-C/E (69) | 112,5 | 25 | 2,5 | 0 | 0 |
| JO-F (60) | 90 | 30 | 10 | 0 | 0 |
| alle JO (145) | 175 | 70 | 32,5 | 0 | 0 |
| Zucker (20) | 0 | 0 | 0 | 127,5 | 122,5 |
| Wasser (18) | 0 | 0 | 0 | 32,5 | 30 |
| Bitter (20) | 0 | 0 | 0 | 0 | 0 |

Das Fütterungsmuster ist qualitativ mit Zucker-/Wasser-Aktivierung vereinbar. Das ist kein quantitatives Bestehen der Shiu-Experimente: Datenversion, Dynamik, Stimulusplan und Versuchslänge unterscheiden sich. Bitter allein ohne MN9-Spikes belegt keine Unterdrückung einer gleichzeitig gereizten Zuckerantwort; eine solche Kombination wurde hier nicht getestet.

**Ein Literaturmuster scheitert:** Shiu Supplement-Tabelle 8 zeigt JO-C/E-Aktivierung der Putz-Auslesen und keine JO-F-Antwort der beiden aDNs. Unser Modell erzeugt stärkere aDN-Antworten für JO-F als für JO-C/E. Die Parameter wurden danach nicht auf das gewünschte Ergebnis eingestellt.

Die vollständigen neun Auslesesignale einschließlich DNa02/DNg13 stehen in `readout_summary.csv`. Off-target-Antworten treten auf; die Tests belegen keine exklusive Zuordnung einer Eingangsgruppe zu einem Verhalten.

## Gegenproben und Modellabhängigkeit

| Eingangsgruppe | aDN1/aDN2 bei 150 Hz | aBN1 stillgelegt | anderes, gradangepasstes Interneuron stillgelegt |
|---|---:|---:|---:|
| JO-C/E | 25 / 2,5 | 0 / 0 | 25 / 2,5 |
| JO-F | 30 / 10 | 0 / 0 | 30 / 10 |
| alle JO | 70 / 32,5 | 10 / 0 | 67,5 / 30 |

Damit ist eine **kausale Abhängigkeit innerhalb dieses Modells** messbar. Beim gesamten JO-Satz bleiben andere Wege aktiv. Ein einzelner anatomisch angepasster Kontrollknoten ist keine statistische Stichprobe biologischer Kontrolltiere.

Alle Baselines und alle vollständig stillgelegten Eingangsgruppen bleiben ohne Aktivität. Stillgelegte Ausleseneuronen liefern keine Spikes. Diese Prüfungen bestätigen die Implementierung der Intervention; das erwartete Nullsignal allein ist kein Beweis einer biologischen Funktionszuordnung.

Die Kontrollneuronen wurden deterministisch und ohne Kenntnis ihres Testausgangs gewählt: gleiche `super_class`, `top_nt` und rohe `side`-Annotation; minimale L1-Distanz von `log1p(Eingangsgrad)` und `log1p(Ausgangsgrad)`. Alle bekannten Eingangs- und Auslese-IDs waren als Sham-Kandidaten ausgeschlossen. Die einzelnen Matches samt Gradabweichungen stehen in der Ergebnisdatei.

## Diagnose des fehlgeschlagenen JO-Musters

Zwei unveränderte Wiederholungen reproduzierten die gespeicherten CE/F-Auslesen bitgenau. Zusätzlich wurden 60 CE- und 60 F-Neuronen mit identischen, indexbasierten Phasenplänen stimuliert. Die CE-Auswahl sind deterministisch die ersten 60 sortierten IDs, keine Auswahl nach Ergebnis. Ergebnis: CE aDN1/aDN2 **5/0 Hz**, F **30/10 Hz**. Die Gegenprobe widerlegt eine Erklärung allein durch die verschiedene Gruppengröße oder die verschiedenen ursprünglichen Phasenpläne; sie ist nur eine feste Teilgruppenauswahl.

Im ursprünglichen Versuch feuert aBN1 unter CE stärker als unter F. Die stärkere F-Antwort entsteht daher nicht einfach durch mehr aBN1-Spikes. Die Ereignisbilanz zeigt zusätzliche modellierte Erregung an aDN1, unter anderem durch **DNg84 (`720575940644473760`)**, **DNg57 (`720575940634617952`)** und **DNge011 (`720575940625306603`)**. An aDN2 trifft unter F weniger modellierte Hemmung ein. Das sind konkrete Kandidaten zur weiteren Ursachenprüfung, keine neu bestätigten biologischen Putzneuronen.

`jo_diagnostic.json` enthält pro präsynaptischer Root-ID Ereigniszahlen, Gewichte, positive/negative Summen und aufgrund der Refraktärphase verworfene Ereignisse. Die Stromsummen sind willkürliche Modellgrößen; Leck, Reset und zeitliche Reihenfolge verhindern eine direkte Interpretation als Membranspannung oder gemessene Leitfähigkeit.

## Modellparameter und Grenzen

Die vorbestehenden Engine-Werte wurden vor den Versuchen festgehalten: 1 ms Zeitschritt, 20 ms Leckzeit, Schwelle 1, Reset 0, Synapsengewinn 0,1, zwei Refraktärschritte. Gewicht = `0.1 * log1p(synapse_count) * (p_ACh - p_GABA - p_Glu)`; Monoamine haben keinen dynamischen Beitrag. Eingangsspitzen sind regelmäßig und phasenversetzt; Hintergrundaktivität ist abgeschaltet. Das ist keine Implementierung der vollständigen publizierten Shiu-Physiologie.

Keine fehlenden Princeton-Verbindungen wurden zur Herstellung eines gewünschten Resultats eingefügt. Die 616 Knoten ohne Originalkante bleiben in diesem Graphen ohne Originalkante. Es gibt keine Kraftphysik, keine vollständige VNC-Muskelkopplung und in diesen Tests keine Rückkopplung vom Körper in die Sensorneuronen.

MN9 links `720575940618238523` stammt unabhängig aus Tastekin 2026, Tabelle S1, Blatt `MNs`, Zeile 69. Es ist keine stillschweigende Ersetzung der fehlenden alten Shiu-ID. DNa02/DNg13 und die aDNs haben Konflikte zwischen historischen Quellseiten und der Originalannotation. Deshalb erfolgt hier keine körperliche Links/Rechts-Steuerung anhand dieser rohen Labels.

## Dateien und Wiederholung

- `protocol.json`: eingefrorene Dynamik, Quellenhashes, vollständige Eingangs-/Auslese-IDs, Auswahlregeln.
- `run.mjs`: Hauptversuche; `assay-engine.mjs`: Kopie der bestehenden Engine mit zusätzlichem Nullspannungs-/Nullspike-Silencing. Produktion und Graph werden nicht geändert.
- `trajectories/*.json.gz`: 42 vollständige Einzelverläufe.
- `../../app/data/neuron_assays.json`: Browserpaket mit denselben Zeitreihen und Befunden.
- `summary.json`, `readout_summary.csv`: kompakte Ergebnisse und alle Auslesen.
- `neuron_spike_counts.csv.gz`: alle aktiv gewordenen Root-IDs pro Versuch, getrennte Zahl erzwungener Eingangsspitzen.
- `model_response_profiles.csv`: **7.048 unterschiedliche reagierende Neuronen** über die sechs 150-Hz-Referenzbedingungen; jede Zeile ausdrücklich nur als Modellantwort bezeichnet. Die Zahl enthält auch gereizte Sensorneuronen.
- `finalize.py`, `audit.json`: unabhängige Arithmetik-, Hash-, Zeitachsen- und Interventionsprüfungen; **1.002 Checks bestanden**, 25.200 Hauptschritte, 226.800 einzelne Auslesebeobachtungen.
- `diagnose_jo.mjs`, `jo_diagnostic.json`: vier zusätzliche Diagnose-Läufe.
- `test_assay_engine.mjs`: drei Tests für Gleichheit zur Original-Engine ohne Intervention und korrektes Silencing in einer kontrollierten Testschaltung.
- `../neuron_pathways/`: unabhängige anatomische Pfadprüfung. Erreichbarkeit allein benennt keine Funktion.

Aus dem Projektverzeichnis, mit Node und der vorhandenen Python-Umgebung:

```powershell
node --test analysis/neuron_assays/test_assay_engine.mjs
node analysis/neuron_assays/run.mjs
analysis/.venv/Scripts/python.exe analysis/neuron_assays/finalize.py
node analysis/neuron_assays/diagnose_jo.mjs
```

## Primärquellen

- [Dorkenwald et al. 2024, originaler FlyWire-Gehirngraph](https://doi.org/10.1038/s41586-024-07558-y).
- [Shiu et al. 2024, Sensorik–Motorik-Modell und Supplement-Tabellen](https://doi.org/10.1038/s41586-024-07763-9).
- [Tastekin et al. 2026, lokale Tabelle S1 für aktuelle MN9-Identitäten](https://doi.org/10.1016/j.cell.2026.08.016).
- [Stürner et al. 2025, DN/AN-Zellzuordnungen](https://doi.org/10.1038/s41586-025-08925-z).
- [Experimentelle DNa02/DNg13-Funktionsarbeit](https://doi.org/10.1016/j.cell.2024.08.033): Typ-Evidenz und exakte FAFB-Identität sind unterschiedliche Evidenzebenen.
