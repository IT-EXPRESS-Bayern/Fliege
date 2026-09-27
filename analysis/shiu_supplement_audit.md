# Audit: Shiu et al. Ergänzungstabellen 1–12

Quelle: [Nature-Zusatzmappe](https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-024-07763-9/MediaObjects/41586_2024_7763_MOESM2_ESM.xlsx); [Artikel](https://doi.org/10.1038/s41586-024-07763-9).
Lokale Datei: `data/research_sources/shiu/supplementary_tables_1-12.xlsx`; SHA-256 `6922e16825aa0c92a28e2a634b073dcad7641e9c9283c4b9d8ee1e34e6d9b8d9`.

## Umfang und Version

Die Arbeitsmappe hat 28 Blätter. Ein Blatt (`Table legends`) ist leer. Excel-Formatierung lässt viele Blätter bis Zeile 1000 reichen; die Tabelle unten zählt tatsächliche nichtleere Zeilen.
In den ersten drei Spalten stehen 1532 verschiedene 18-stellige FlyWire-Root-IDs. 1305 kommen exakt in `proofread_root_ids_783.npy` vor, 227 nicht.
Die Shiu-v783-`Completeness_783.csv` enthält 138639 IDs und ist eine Teilmenge der 139255 v783-Proofread-IDs (Differenz 616).
Die Zusatzmappe gehört zu den publizierten v630-Experimenten. Ihre Zahlen sind Referenzen für v630. Gleiche Root-ID in v783 ist ein Kandidat; fehlende ID wird **nicht** über Namen oder Zeilenindex ersetzt.

## Für unser Modell nutzbare Kandidaten

| Gruppe | Zahl | Einsatz |
|---|---:|---|
| Zucker-Sensoren (`sugar_`) | 21 | Sensorreiz Zucker → Eingang; Tabelle 1A |
| Wasser-Sensoren (`water_`) | 18 | Sensorreiz Wasser → Eingang; Tabelle 6A |
| Bitter-Sensoren (`bitter_`) | 21 | Aversiver Geschmacksreiz; Tabelle 4 |
| Ir94e-Sensoren | 18 | Modellspezifischer Geschmacksreiz; tatsächlicher Reiz bleibt unsicher; Tabelle 4 |
| Johnston-Organ (`JO_`) | 146 | Antennen-Mechanosensorik; Tabelle 7A |
| MN9 (links/rechts) | 2 | Auslese für Proboscis-Heben; Tabelle 1A |
| aBN1, aDN1, aDN2 | 3 | Antennenputz-Schaltung; Tabelle 7A |

Status der 229 ausgewählten Tabellen-IDs: absent_from_v783_exact_id=4, exact_id_broad_class_match=222, exact_id_name_unverified=1, lateralization_requires_review=2.
Die vollständige ID-Liste mit Quellblatt, Excel-Zeile, v783-Exaktmatch und aktueller Annotation steht in `data/research_sources/shiu/derived/shiu_supplement_index.json`.

## Sicherheitsrelevante Zuordnungen

- `MN9_r` (`720575940660219265`, Tabelle 1A Zeile 41) kommt exakt in v783 vor; aktuelle Annotation: efferent/motor, rechts, PhN. Als **Kandidat** für Proboscis-Auslese geeignet.
- `MN9_l` (`720575940645521262`, Tabelle 1A Zeile 90) fehlt in v783. Kein automatischer Ersatz durch einen ähnlich benannten Motorneurontyp.
- `aBN1` (`720575940630907434`, Tabelle 7A Zeile 173) existiert exakt in v783; aktuelle Annotation ist links/central, bestätigt aber den Namen nicht unabhängig.
- `aDN1_l` (`720575940616185531`) und `aDN2_l` (`720575940629806974`) existieren exakt und sind in v783 als absteigend annotiert. Aktuelles Feld `side=right` widerspricht dem `_l` im Workbook-Namen. Vor einer links/rechts-Körpersteuerung Seitenkonvention und Zellidentität manuell prüfen.
- Die meisten Sensorgruppen haben einen passenden breiten v783-Zellklasseneintrag. Das bestätigt die Rolle als Sensor-Kandidat, nicht jede konkrete Rezeptor- oder Reizpräferenz.

## Reproduzierbare Modellchecks

Die folgenden Werte sind **v630-Mittelraten** in Hz und dienen als publizierte Kontrollmuster. Nach Umstellung auf v783 erst prüfen, ob die Richtung des Effekts und die beteiligten Zelltypen erhalten bleiben.

| Check | Workbook-Zelle | v630-Mittelrate Hz |
|---|---|---:|
| `sugar_150_to_MN9_r` | `Supplemental Table 1A Sugar Fir` Zeile 41, Spalte 17 | 83.67 |
| `sugar_150_to_MN9_l` | `Supplemental Table 1A Sugar Fir` Zeile 90, Spalte 17 | 60.10 |
| `water_160_to_MN9_r` | `ST 6A Water Firing Rates` Zeile 45, Spalte 10 | 10.03 |
| `water_160_to_MN9_l` | `ST 6A Water Firing Rates` Zeile 95, Spalte 10 | 2.90 |
| `JON_140_to_aBN1` | `Supplemental Table 7A Grooming ` Zeile 173, Spalte 9 | 45.27 |
| `JON_140_to_aDN1` | `Supplemental Table 7A Grooming ` Zeile 255, Spalte 9 | 16.67 |
| `JON_140_to_aDN2` | `Supplemental Table 7A Grooming ` Zeile 254, Spalte 9 | 17.13 |
| `JO_CE_150_to_aBN1` | `Supp Table 8 JO-CE and JO-F fir` Zeile 98, Spalte 3 | 50.77 |
| `JO_F_150_to_aBN1` | `Supp Table 8 JO-CE and JO-F fir` Zeile 98, Spalte 4 | 1.23 |
| `JO_CE_150_to_aDN1` | `Supp Table 8 JO-CE and JO-F fir` Zeile 277, Spalte 3 | 13.40 |
| `JO_F_150_to_aDN1` | `Supp Table 8 JO-CE and JO-F fir` Zeile 277, Spalte 4 | 0.00 |
| `JO_CE_150_to_aDN2` | `Supp Table 8 JO-CE and JO-F fir` Zeile 258, Spalte 3 | 19.03 |
| `JO_F_150_to_aDN2` | `Supp Table 8 JO-CE and JO-F fir` Zeile 258, Spalte 4 | 0.00 |

Tabelle 10 meldet 150/164 korrekte empirisch geprüfte Vorhersagen (Zeile 12); ohne Abbildung 2 49/58 (Zeile 14). Diese Werte sind keine allgemeine Fliegen-Verhaltensgenauigkeit.
Tabelle 11A/B–F prüft geänderte Synapsengewichte, Hemmungsstärke und Glutamat-Vorzeichen. Diese Varianten sollten später als Sensitivitätstests laufen, nicht zur Auswahl des besten Ergebnisses auf denselben Validierungsdaten dienen.
Tabelle 9A/B enthält 105 auslesbare Verhaltenszählwerte nach Optogenetik bzw. Silencing, mit Zähler, Nenner und Excel-Zellen im JSON. Beispiel: Tabelle 9A, 50 mM Sucrose und Bitter-GRN-Aktivierung, Versuch `Gr66a > Chrimson`: Proboscis-Erweiterung 26/30 bei Licht aus (Zeilen 2–3, Spalte 6), 3/30 bei Licht an (Spalte 7). Diese Daten liefern keine direkten Muskelkräfte.
Tabelle 12 listet Laborressourcen, keine zusätzlichen Modellparameter.

## Blattinventar

| Blatt | Nichtleere Zeilen | Excel-Maximalzeile | Spalten |
|---|---:|---:|---:|
| `Table legends` | 0 | 1 | 1 |
| `Supplemental Table 1A Sugar Fir` | 488 | 1000 | 43 |
| `ST 1B Sugar MN9 Activation` | 201 | 1000 | 26 |
| `ST 1C MN9 sugar silencing A` | 201 | 1000 | 63 |
| `ST 1D Shuffled Connectivity` | 16 | 16 | 108 |
| `Supplemental Table 2 Sugar Pred` | 12 | 1000 | 26 |
| `Sup Table 3 Predicted MN9 vs. o` | 107 | 1000 | 45 |
| `ST 4 Interaction betw Sugar, Wa` | 615 | 1001 | 26 |
| `Supplemental Table 5 Water Pred` | 12 | 989 | 26 |
| `ST 6A Water Firing Rates` | 462 | 1000 | 29 |
| `ST 6B Water MN9 Activation` | 201 | 203 | 19 |
| `ST 6C Water silencing data` | 201 | 1001 | 35 |
| `Supplemental Table 7A Grooming ` | 856 | 1000 | 26 |
| `Supp Table 7B aDN1 Activation r` | 301 | 1000 | 25 |
| `Supp Table 7C aDN2 Activation R` | 301 | 1000 | 26 |
| `Supp Table 7D aDN1 firing upon ` | 301 | 1000 | 27 |
| `Supp Table 7E aDN2 firing upon ` | 301 | 1001 | 25 |
| `Supp Table 8 JO-CE and JO-F fir` | 467 | 1000 | 27 |
| `Supp Table 9A Behavioral Data, ` | 15 | 19 | 7 |
| `Supp Table 9B Water silencing` | 43 | 1001 | 26 |
| `Supp Table 10 Overall predictio` | 15 | 997 | 28 |
| `Supplemental Table 11 A Robustn` | 65 | 984 | 29 |
| `Supp Table 11B Decrease w_syn` | 182 | 998 | 40 |
| `Supp Table 11C Increase w_syn` | 182 | 998 | 26 |
| `Supp Table 11D Decrease inhibit` | 182 | 999 | 26 |
| `Supp Table 11E Increase Inhibit` | 183 | 183 | 7 |
| `Supp Table 11F Glut excitatory` | 182 | 188 | 21 |
| `Supplementary Table 12 Key reso` | 45 | 975 | 26 |
