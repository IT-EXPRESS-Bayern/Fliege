# Neuronen benennen, Modellantworten messen, Körperreaktionen prüfen

Stand: **27. September 2026**. [3D-Labor öffnen](http://127.0.0.1:4173/lab.html).

## Namen und belegte Rollen

Der [vollständige Neuronenkatalog](neuron_catalog/catalog_139255.parquet) enthält alle **139.255** originalen v783-Root-IDs ohne Duplikate. **138.765** haben einen aus Quellen übernommenen Anzeigenamen; **490** bleiben unbenannt. Ein Name ist noch keine bekannte Funktion: **22.312** Neuronen haben eine kuratierte Funktionsannotation, **116.943** weiterhin keine. Originalannotation, harmonisierte Annotation, anatomische Rolle und übertragene Typ-Hypothese sind getrennte Felder.

[72.040 Quellenclaims](neuron_catalog/source_claims.parquet) halten Herkunft, Tabellenzeile und Evidenzart fest. Einzelheiten und Validierung stehen im [Katalogbericht](neuron_catalog/README.md). Der neue linke MN9-Root `720575940618238523` wurde direkt aus Tastekin 2026, Tabelle S1, Blatt `MNs`, Zeile 69 übernommen; er ist kein anhand des Namens erratener Ersatz der fehlenden alten Shiu-ID.

## Was am gesamten Graphen getestet wurde

**42 Hauptläufe** über sechs sensorische Gruppen und **vier Diagnose-Läufe** verwenden den unveränderten Originalgraphen mit **15.091.983 gerichteten Paaren**. Pro Hauptlauf: 600 ms, Schrittweite 1 ms, Reizung von 100 bis 500 ms. Eingänge werden als Spikezüge gesetzt; Auslesespikes entstehen über den Graphen. Die vorbestehenden abstrakten Dynamikparameter wurden fixiert und nicht auf ein gewünschtes Verhalten angepasst.

Neben 50/150-Hz-Reizung gibt es Baseline, stillgelegte Eingangsneuronen, stillgelegte Auslesen, gradangepasste Sensor-Kontrollen und bei den JO-Gruppen aBN1-Stilllegung samt Kontrollstilllegung. **1.002 Arithmetik-, Provenienz- und Invariantenprüfungen** sowie drei Engine-Tests bestanden. Die Hauptdaten enthalten 25.200 Zeitschritte und 226.800 einzelne Auslesebeobachtungen. [Methoden und vollständige Befunde](neuron_assays/README.md), [Prüfprotokoll](neuron_assays/audit.json).

### Antworten bei 150 Hz Eingang

Die Tabelle zeigt Modell-Hz während des 400-ms-Reizfensters, keine Messungen am Tier.

| Reizgruppe | Eingangszellen | aBN1 | aDN1 | aDN2 | MN9 rechts | MN9 links |
|---|---:|---:|---:|---:|---:|---:|
| JO-C/E | 69 | 112,5 | 25 | 2,5 | 0 | 0 |
| JO-F | 60 | 90 | 30 | 10 | 0 | 0 |
| gesamte JO-Gruppe | 145 | 175 | 70 | 32,5 | 0 | 0 |
| Zucker | 20 | 0 | 0 | 0 | 127,5 | 122,5 |
| Wasser | 18 | 0 | 0 | 0 | 32,5 | 30 |
| Bitter | 20 | 0 | 0 | 0 | 0 | 0 |

Das Zucker-/Wasser-Muster ist qualitativ mit der publizierten Fütterungsschaltung vereinbar. Bitter allein ohne MN9-Antwort testet keine Unterdrückung einer gleichzeitigen Zuckerantwort. DNa02 und DNg13 werden ebenfalls überwacht; dort gibt es zusätzliche Antworten, weshalb keine exklusive Verhaltenszuordnung behauptet wird. [Alle Auslesen](neuron_assays/readout_summary.csv).

**Der JO-C/E-versus-JO-F-Vergleich besteht den Literaturtest nicht:** Die publizierte geringe/fehlende F-Antwort der Putz-Auslesen erscheint in unserem Modell nicht. Bei identischer Zahl von 60 Eingängen und identischem Phasenplan bleiben die Antworten CE **5/0 Hz**, F **30/10 Hz** für aDN1/aDN2. Zwei unveränderte Diagnosewiederholungen reproduzieren die gespeicherten ursprünglichen Zeitreihen exakt.

aBN1-Stilllegung reduziert die CE- und F-Antworten beider aDNs auf null. Bei der gesamten JO-Gruppe sinken sie von **70/32,5** auf **10/0 Hz**; die Kontrollstilllegung ergibt **67,5/30 Hz**. Das zeigt eine Abhängigkeit innerhalb des Modells. Die [Ereignisdiagnose](neuron_assays/jo_diagnostic.json) nennt DNg84, DNg57 und DNge011 als zusätzliche modellierte Erregungsquellen zur aDN1-Auslese und zeigt weniger modellierte Hemmung an aDN2 unter F. Diese Zellen sind Kandidaten für weitere Ursachenprüfungen, keine neu biologisch bestätigten Putzneuronen.

## Antworten einzelner Neuronen

**7.048** Neuronen feuern in mindestens einem der sechs Referenzläufe; **6.845** haben mindestens einen nicht erzwungenen Spike. Die [benannten Antwortprofile](neuron_catalog/named_model_responses.parquet) verbinden jede Root-ID exakt mit dem Katalog. Darunter bleiben **17 unbenannt** und **6.767 ohne kuratierte Funktion**. Die biologischen Katalogfelder wurden durch die Simulation nicht verändert.

Die Profilzahlen umfassen jeweils alle 600 ms. „Nicht erzwungen“ bedeutet Gesamtspikes minus gesetzte Eingangsspitzen, keine am Tier gemessene Aktivitätssteigerung. Ein offizieller v783-Root außerhalb dieser Vereinigung hat in genau diesen sechs Läufen null Spikes; seine biologische Funktion und mögliche unterschwellige Antwort bleiben dadurch offen. [Join-Prüfung](neuron_catalog/model_response_join_audit.json).

## Anatomie und Seitenkonvention

Die unabhängige [Pfadprüfung](neuron_pathways/README.md) erfasst gerichtete Wege bis vier Schritte bei mindestens einem beziehungsweise fünf Kontakten je Kante. Bei der Fünf-Kontakt-Schwelle erreichen **57/69 JO-C/E** und **37/60 JO-F** die untersuchten Putz-Auslesen innerhalb vier Schritten. Alle 20 Zucker-Eingänge erreichen MN9 rechts in drei Schritten; links erreichen acht Zellen MN9 in zwei und zwölf in drei Schritten. Anatomische Erreichbarkeit allein beweist keine funktionelle Reaktion.

**1.301 von 1.316 Stürner-DN-Seitenlabels** stehen beiden aktuellen Annotationsquellen entgegen; 14 stimmen überein, ein Fall bleibt zur Einzelprüfung. Die dokumentierte historische Bildspiegelung erklärt die systematische Abweichung plausibel, nicht automatisch jede Quellzeile. Beide untersuchten aDNs sind aktuell rechts annotiert, trotz alter `_l`-Namen. Rohangaben bleiben erhalten; daraus wurde keine Links/Rechts-Körpersteuerung abgeleitet. [Seitenprüfung](neuron_pathways/side_convention_audit.json).

## Was das 3D-Labor nachweist

Das [3D-Labor](http://127.0.0.1:4173/lab.html) spielt die aufgezeichneten aDN1/aDN2-Spikes ab. Ein offengelegter Adapter verwendet die kausale mittlere Rate der letzten 100 ms, geteilt durch 50 Hz, als Putzintensität. Neuronale Zeit und Körperzeit bleiben gleich; Zeitlupe verändert nur die Darstellung.

Der [Körperprüfbericht](../app/data/neuron_body_replay_audit.json) umfasst dieselben **42 Läufe**: **acht erzeugen Bewegung**, **34 haben keine auf den Körper übertragenen Spikes und bleiben still**. Alle Geometrie-, Zähl- und Adapterprüfungen bestehen; der Quellenhash stimmt mit der finalen Assaydatei überein. Ein separater direkter Aktuatortest bewegt das Modell, ohne neuronale Evidenz vorzutäuschen.

MN9 hat noch keinen Proboscis-Aktuator; DNa02/DNg13 steuern hier kein Drehen. Kalibrierte Muskelkräfte, vollständige VNC-Kopplung und sensorische Rückkopplung vom Körper ins Gehirn fehlen. Bewegung belegt deshalb den angegebenen Darstellungsadapter, keine neu bestätigte biologische Funktion.

## Direkt nutzbares Datenpaket

Das [Modellmanifest](model_integration_pack.json) enthält jetzt **87 Eingaben und 30 dokumentierte Verknüpfungsregeln**. Die vorherigen 73 Eingaben und 22 Regeln sind erhalten. Alle Pfade wurden geprüft; zwei aufeinanderfolgende Updaterläufe erzeugen identische Dateien. [Integrationsprüfung](neuron_assays/integration_pack_update_audit.json).

**Keine neue Synapse wurde durch diese Tests erzeugt.** Neue Detektorverbindungen, anatomische Hypothesen, Quellenfunktionen, Modellantworten und Körperadapter bleiben als unterschiedliche Evidenz sichtbar.

Primärquellen: [FlyWire-Gehirngraph](https://doi.org/10.1038/s41586-024-07558-y), [Shiu 2024](https://doi.org/10.1038/s41586-024-07763-9), [Tastekin 2026](https://doi.org/10.1016/j.cell.2026.08.016), [Stürner 2025](https://doi.org/10.1038/s41586-025-08925-z), [DNa02/DNg13-Funktionsarbeit](https://doi.org/10.1016/j.cell.2024.08.033), [Codex-Seitenkonvention](https://codex.flywire.ai/faq).

Die Einzelzell-Suche im Labor zeigt zusätzlich die sechs gespeicherten Antwortprofile, mit getrennten erzwungenen und nicht direkt erzwungenen Spikes. Browserexport: pp/data/neuron_response_profiles.json, 512 KB; 126.864 Werte gegen Quellen geprüft. [Browserprüfung](neuron_lab_browser_qa.json).
