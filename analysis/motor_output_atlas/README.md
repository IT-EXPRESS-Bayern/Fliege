# Motorische Ausgänge im BANC-v888-Präparat

Stand: 27. September 2026. Der vollständige lokale Metadatenexport enthält **805 unterschiedliche, als proofread markierte Motorneuronen** (`super_class=motor`). Der SHA-256-Wert der Quelldatei wurde gegen den vorhandenen Quellen-Audit geprüft. Jede ID bleibt ein Dezimalstring. Quelle: [BANC-Datensatz](https://doi.org/10.7910/DVN/7WTH1N), [Originalarbeit](https://doi.org/10.1038/s41586-026-10735-w), CC BY 4.0.

| Wörtlicher Körperteil der Quelle | Motorneuronen |
|---|---:|
| Vorderbeine | 139 |
| Mittelbeine | 126 |
| Hinterbeine | 126 |
| Abdomen | 168 |
| Flügel | 64 |
| Hals | 49 |
| Rüssel | 35 |
| Halteren | 27 |
| Pharynx | 22 |
| Thorax/Abdomen | 18 |
| Weitere Körperteile und unbekannt | 31 |
| **Gesamt** | **805** |

Die vollständigen 17 wörtlichen Zielgruppen stehen in [body_part_summary.csv](body_part_summary.csv). Körperteil und Zellklasse sind verschiedene Annotationen; ihre Häufigkeiten müssen nicht identisch sein. `antenna, scape` ist ein einziges Quellenlabel und wird einmal gezählt. Die 805 sind die hier explizit als motorisch klassifizierten Zellen, keine Behauptung vollständiger Erfassung aller biologischen Effektoren.

## Was sich auf Gelenke beziehen lässt

Die 391 Beinmotorneuronen sind bereits mit exakten IDs, Nerven und Zielmuskeln erfasst. 113 tragen eine Femur–Tibia-Beuge-/Streckaktion, 30 eine Tibia–Tarsus-Aktion. Diese anatomischen Angaben legen eine Gelenkzuordnung nahe. Sie liefern keine individuelle Rate-zu-Kraft-Kurve, keine Trägheit, keine Sehnenlänge und kein validiertes Gangmuster. 110 weitere Beinmotorneuronen wirken am Coxa–Trochanter-Komplex, der im bisherigen Browserkörper reduziert dargestellt ist. Details: [bestehende Körperschnittstelle](../body_neural_interface/README.md).

## Transmittervorhersage ist keine Muskelsteuerung

Von 805 Motorneuronen haben **30** eine Quellenangabe im Feld `neurotransmitter_verified`: alle Glutamat, verteilt auf 15 Hals- und 15 Halterenzellen. Bei **28 dieser 30** nennt `neurotransmitter_predicted` etwas anderes. Das ist ein konkreter Konflikt zwischen zwei Quellenfeldern; hier wurde keine neue Transmittermessung durchgeführt. Die Teilmenge ist selektiv und erlaubt keine globale Fehlerquote des Klassifikators.

Bei den 391 Beinmotorneuronen gibt es keine Einträge in `neurotransmitter_verified`. Ihre automatischen Vorhersagen lauten GABA 260, Acetylcholin 81, Glutamat 11, Octopamin 12, Dopamin 1 und fehlend 26. Diese Verteilung ist **kein Beleg**, dass die betreffenden Muskeln entsprechend gehemmt oder erregt werden. Das Rezeptorsystem am Ziel gehört zur Wirkung dazu. Die [Primärarbeit zu absteigenden Netzwerken](https://doi.org/10.1038/s41586-024-07523-9) unterscheidet deshalb Glutamat ausdrücklich von einer fest vorgegebenen erregenden oder hemmenden Wirkung.

Ein `proofread`-Status bestätigt weder die automatische Transmittervorhersage noch eine Muskelkraft. Ein Motoradapter muss positive Zellaktivität, Muskelaktion, receptorabhängige Wirkung und mechanische Parameter getrennt behandeln. Die bisherige zentrale Modellregel `ACh − GABA − Glu` darf nicht ohne neue Begründung zur Muskelregel werden.

## Dateien und Wiederholung

- [banc_motor_neurons_805.csv](banc_motor_neurons_805.csv) und [Parquet](banc_motor_neurons_805.parquet): exakte Quellfelder aller 805 Motorneuronen.
- [predicted_verified_transmitter_conflicts.csv](predicted_verified_transmitter_conflicts.csv): alle 28 Konflikte, mit beiden Originalfeldern.
- [audit.json](audit.json): Fingerabdruck, Mengen, Definitionen und Grenzen.
- [build.py](build.py): reproduzierbar mit `analysis/.venv/Scripts/python.exe analysis/motor_output_atlas/build.py`.

BANC und FAFB stammen von unterschiedlichen Tieren. `fafb_match` bleibt ein Homologiehinweis; kein BANC-Ausgang wurde hier als neu rekonstruierter FAFB-Ausgang eingetragen.
