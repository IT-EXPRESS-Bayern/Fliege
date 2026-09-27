# Neuronenlabor und Körper-Replay

Die neuronalen Versuche werden vorab auf dem originalen FAFB-v783-Verbindungsgraphen gerechnet. `data/neuron_assays.json` enthält Eingangs- und Auslese-IDs, Bedingungen, Zeitschritte, Aktionspotenziale und Modellparameter. Die Browserseite `/lab.html` liest diese Aufzeichnungen. Sie simuliert den gleichen gegliederten Körper wie die Arena mit `ArticulatedBody` aus `body-kinematics.mjs`.

## Was wird tatsächlich getestet?

1. Neuronale Stimulation, Ausschaltung und Gegenproben testen Reaktionen des implementierten Netzmodells.
2. Die Zuordnung der dokumentierten Zelltypen und publizierten Rollen bleibt von diesen Simulationsergebnissen getrennt.
3. Der Körper-Replay überprüft, wie eine explizite Signalübersetzung den gegliederten Körper bewegt. Dies belegt die technische Kopplung unter dieser Annahme, keine biologisch kalibrierte Muskelsteuerung.

## Putzkanal

Nur im Manifest als Putz-Auslese markierte aDN1/aDN2-Zellen dürfen den Körperkanal treiben. aBN1-Interneuronen, sensorische Neuronen und andere absteigende Zelltypen werden nicht automatisch in Bewegung übersetzt. Es gibt keine ungesicherte Zuordnung linker und rechter aDNs zu Körperseiten.

- Rate jeder Auslesezelle: Anzahl der aufgezeichneten Spikes im kausalen Fenster `(t − 100 ms, t]`, geteilt durch 0,1 s.
- Populationsrate: arithmetisches Mittel über die zugeordneten aDN-Auslesezellen, inklusive stiller Zellen.
- Putzkanal: `min(1, max(0, mittlere_Rate_Hz / 50))`.
- Fensterlänge, Verstärkung und bilaterale Körperkinematik sind Modellannahmen. Es wird keine Übereinstimmung mit gemessenen Muskelkräften behauptet.
- Forward-, Turn- und Wing-Kanäle bleiben bei den neuronalen Versuchen null.
- Ohne aDN-Spikes sind alle Körperkanäle exakt null. Unabhängige dekorative Kopf-, Fühler- und Hinterleibbewegungen werden im Labor eingefroren.
- MN9- oder andere Ausleseantworten ohne implementierten Aktuator werden dargestellt, erzeugen aber keine Ersatzbewegung.

## Zeit und Wiedergabe

Neuronale Zeit und Körperzeit sind identisch. Jeder gespeicherte Zeitschritt wird deterministisch durch dieselbe Körperkinematik geführt. Die Anzeige spielt daraus erzeugte Körperzustände ab. Zeitlupe verändert ausschließlich die Dauer der Bildschirmwiedergabe, nicht die neuronale Antwort, Körperzeit oder Gelenkdynamik. Zurückspulen rechnet keine neue neuronale Antwort aus.

Die Zeitkurve zeigt mittlere Ausleseraten im 100-ms-Fenster. Die Tabelle zeigt Spikeanzahl und mittlere Rate über den gesamten Versuch. Beinbewegung ist die Summe absoluter Winkeländerungen aller geometrischen Gelenkkanäle (Radiant). Sie ist kein experimentell gemessener Bewegungsumfang des lebenden Tiers.

## Technische positive Kontrolle

Ein eigener, sichtbar getrennter Versuch setzt den Putzkanal direkt auf 1 von 300 bis 1.700 ms eines 2.400-ms-Versuchs. Er enthält keine neuronalen Spikes und keine Root-IDs. Er prüft lediglich die Bewegungsfähigkeit des Körpermodells.

## Grenzen

Der Körper besitzt geometrische Bodenkontakte und Gelenkwinkel, aber keine validierte Muskelphysik. Die Körperrückmeldung wird in diesen aufgezeichneten Versuchen nicht an den neuronalen Graphen zurückgegeben. Ein Sensorreiz ist eine vorgegebene Modellstimulation, keine aus den Kamera- oder Antennengeometrien errechnete Sinneswahrnehmung. Fehlende Modellantworten können auch durch unbekannte Biophysik, unpassende Reizstärke, fehlende Verbindungen oder ausgeschlossene Körpernerven entstehen.

## Antwortprofile im Neuronenkatalog

Bei der ersten Suche wird `data/neuron_response_profiles.json` nachgeladen. Die sechs Referenzbedingungen (JO C/E, JO F, gesamtes Johnston-Organ, Zucker, Wasser, Bitter) enthalten jeweils 600 ms vollständige Aufzeichnung aller 139.255 Graphknoten. Für jede ausgewählte Root-ID werden Gesamtspikes, direkt erzwungene Eingangsspitzen und die Differenz beider getrennt angezeigt. Die letzte Spalte heißt deshalb „Nicht direkt erzwungen“. Sie stellt keine neue biologische Funktionsbenennung dar.

Die kompakte Profildatei enthält die Vereinigung der 7.048 IDs mit mindestens einem Spike in diesen Referenzläufen. Fehlt eine bekannte Katalog-ID dort, wurden in genau diesen sechs Läufen keine Spikes für sie registriert. Das schließt unterschwellige Spannungsänderungen, Antworten auf andere Reize oder eine biologische Funktion nicht aus. Ladefehler werden ausdrücklich angezeigt und nicht als ausbleibende Antwort interpretiert.

## Reproduzierbare Kontrollen des Adapters

`node --test app/tests/lab-replay.test.mjs`

Geprüft werden kausale Zeitfenster, exakt ausbleibende Bewegung ohne motorische Auslese, Trennung von Interneuronen und absteigenden Auslesezellen, begrenzte Verstärkung, fehlende Aktuatoren, identische Körperkinematik, Wiederholbarkeit, Zeit-Scrubbing und separat ausgewiesene direkte Aktuatorkontrolle.

`node app/audit-lab.mjs` führt anschließend sämtliche gespeicherten neuronalen Versuche durch den Körperadapter. Die Ergebnisse, Quellprüfsumme und Kontrollen stehen in `data/neuron_body_replay_audit.json`. Der Audit gleicht jede ausgelesene Spikeanzahl mit der neuronalen Versuchszusammenfassung ab und prüft insbesondere: kein Bewegungssignal ohne zugeordnete Spikes, endliche Gelenkwinkel und begrenzte Körperbefehle.
