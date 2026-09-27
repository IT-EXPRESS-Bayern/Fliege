# Anatomische Wege zwischen benannten Sinnes- und Ausgangsneuronen

Der vollständige Originalgraph mit **139.255 Neuronen und 15.091.983 gerichteten Paaren** wurde für diese Analyse geladen. Alle fünf binären Grapharrays wurden gegen die SHA-256-Werte im Originalmanifest geprüft. `trace.py` sucht rückwärts vom Ausgangsneuron aus nach kürzesten gerichteten Wegen mit höchstens vier Synapsenschritten. Der Lauf wurde mit mindestens einer sowie mindestens fünf Synapsen pro Kante ausgeführt. Er ist unabhängig von den dynamischen Aktivierungstests und dem Körperadapter.

Eingänge sind exakt vorhandene v783-IDs aus dem [Shiu-Supplement](https://doi.org/10.1038/s41586-024-07763-9): 69 JO-C/E-, 60 JO-F-, 20 Zucker-, 18 Wasser- und 20 Bitter-Kandidaten. Drei nicht vorhandene Quell-IDs sind ausdrücklich ausgeschlossen. Ausgänge sind aBN1, aDN1, aDN2 sowie beide MN9-Zellen. Die aktuelle linke MN9-ID `720575940618238523` stammt unabhängig aus [Tastekin et al.](https://doi.org/10.1016/j.cell.2026.08.016), Table S1, Blatt `MNs`, Excel-Zeile 69. Sie ersetzt nicht stillschweigend die fehlende ältere Shiu-ID. Rechte MN9-ID und beide Quellenzeilen sind ebenfalls geprüft.

## Konkrete Resultate bei mindestens fünf Synapsen je Kante

| Eingang | Ausgang | Erreichbar in höchstens vier Schritten | Kürzeste Wege |
|---|---|---:|---|
| JO-C/E | aBN1 | 57 von 69 | 5 direkt, 32 mit zwei, 20 mit drei Schritten |
| JO-F | aBN1 | 37 von 60 | 5 direkt, 14 mit zwei, 18 mit drei Schritten |
| JO-C/E | aDN1 | 57 von 69 | 6 mit zwei, 41 mit drei, 10 mit vier Schritten |
| JO-F | aDN1 | 37 von 60 | 21 mit zwei, 15 mit drei, 1 mit vier Schritten |
| Zucker | MN9 rechts | 20 von 20 | Alle mit drei Schritten |
| Zucker | MN9 links | 20 von 20 | 8 mit zwei, 12 mit drei Schritten |
| Wasser | MN9 rechts | 18 von 18 | 17 mit drei, 1 mit vier Schritten |
| Bitter | MN9 rechts | 19 von 20 | Alle erreichbaren mit drei Schritten |

Die breite Erreichbarkeit zeigt, warum die Verdrahtung allein keine eindeutige Funktion festlegt: Auch Bitter-Zellen und Antennensensoren haben kurze anatomische Wege zu MN9. Ob dort Anregung, Hemmung oder keine überschwellige Antwort entsteht, hängt von der Dynamik, vorhergesagten Transmittern und unbekannten Rezeptoren ab. Ein vorhandener Weg ist kein Verhaltenstest. Die unterschiedliche Zahl verfügbarer Eingangsneuronen muss bei Reizvergleichen berücksichtigt werden.

## Ausgaben und Grenzen

- [reachability.csv](reachability.csv): 50 Kombinationen aus fünf Eingangsgruppen, fünf Ausgängen und zwei Kantenschwellen; alle Gruppen als Nenner enthalten.
- [example_shortest_paths.json](example_shortest_paths.json): 1.870 Eingangs-/Ausgangs-/Schwellenfälle, davon 1.690 innerhalb der Vier-Schritt-Grenze erreichbar. Enthält exakte IDs, Quellannotation, Synapsenzahlen und vorhergesagte Transmitterwerte für jeweils einen kürzesten Weg.
- [audit.json](audit.json): Quellenfingerabdrücke, IDs, ausgeschlossene Zellen, Methode und Grenzen.
- [trace.py](trace.py): Reproduzierbarer Lauf mit `analysis/.venv/Scripts/python.exe analysis/neuron_pathways/trace.py`.

Bei mehreren gleich kurzen Wegen wird deterministisch der erste CSR-Pfad gewählt. Das ist weder der stärkste noch ein nachgewiesener biologisch genutzter Weg. Nicht innerhalb von vier Schritten erreichbar bedeutet nicht global unverbunden. Die Transmitterwerte sind Vorhersagen und für den Browser auf 8 Bit gerundet. Die aDN-Quellnamen tragen links, während die aktuelle Annotation rechts nennt; diese Konflikte sind im Ausgangsnamen markiert und rechtfertigen keine seitenspezifische Körpersteuerung.

## Seitenkonvention unabhängig geprüft

`audit_sides.py` vergleicht die gepinnte Originalannotation, die neueren harmonisierten FAFB-Metadaten des BANC-Projekts und die Stürner-DN-Tabelle über exakte Root-IDs. Unter den 139.249 gemeinsamen FAFB-IDs stimmen 139.208 bekannte Seiten überein, 30 sind in beiden Tabellen unbekannt, 11 weichen ab. Von 1.316 Stürner-DN-Zeilen nennen 1.301 die Gegenrichtung zu beiden neueren Tabellen; 14 stimmen überein, eine braucht Einzelprüfung.

Die [offizielle FlyWire-Codex-FAQ](https://codex.flywire.ai/faq) beschreibt eine historische Links-rechts-Inversion bei der FAFB-Bildaufnahme und später korrigierte Seitenannotationen bei unverändert gespiegelten Bildern. Das systematische Muster ist damit vereinbar; die Korrekturhistorie jeder Quellenzeile ist hier nicht bewiesen. Deshalb bleiben Rohlabels und Ausnahmen erhalten. Auch eine geklärte Somaseite legt noch nicht fest, welche Körperseite ein Neuron steuert.

- `side_convention_audit.json`: Quellenfingerabdrücke, Gesamtabgleich und konkrete aDN-/DNa02-/DNg13-Zellen.
- `global_side_discrepancies.csv`: alle 11 globalen Abweichungen.
- `stuerner_dn_side_comparison.csv`: alle 1.316 DN-Zeilen mit Originalseiten und Vergleichsklasse.
