# Flügelmechanik und Rollprüfstand

[Kern](./flight_model.mjs) · [Originalzuordnungen](./data/flight_control_mapping.json) · [Audit](./data/flight_audit.json).

## Was dieser Versuch nachweist

Ein tonischer, zeitlich konstanter Modellantrieb kann selbstständige mechanische Flügelschwingungen erhalten. Die Winkel entstehen durch integrierte Bewegungsgleichungen. Im Antrieb steckt keine Sinusfunktion, Schlagfolge, Laufroute oder vorgegebene Flugbahn.

Der Körper ist an einem gedachten Prüfstand befestigt und darf rollen. Translation, Abheben, Gewichtstragfähigkeit und freier Flug werden nicht berechnet. Das Nervennetz ist in diesem Prüfstand ebenfalls nicht simuliert: Die Eingänge sind ausdrücklich **direkte Motorinterventionen** mit normierter Aktivität 0–1. Ein technischer Rückkopplungsversuch verwendet eine idealisierte Rollgeschwindigkeitsmessung. Er ist keine rekonstruierte Halteren-Synapsenschaltung.

## Belegte Identitäten und unbekannte Wirkungen

Die BANC-v888-Quelldatei liefert je Körperseite fünf DLM-, sieben DVM- und ein b1-Motorneuron. Der Adapter verwendet diese 26 exakten IDs. Alle sind proofread und für den anatomischen Pool zugelassen. Die Körperseite stammt aus dem peripheren Nerv: Bei den beiden DLM5-Zellen unterscheidet sie sich von der Quellseite der Zelle. Eine ungeprüfte Übernahme der Soma-/Quellseite würde diese beiden Motoren falsch zuordnen.

DLM/DVM werden als asynchrone Leistungsmuskeln behandelt; b1 ist ein direkter Steuermuskel. Die Annotation belegt **keinen** einzelnen positiven oder negativen Rollmoment-Gain. `kinematicSign`, `forceGain` und `wingbeatRatePerSpike` bleiben in den Originaldaten unbekannt. Die demonstrierte b1-Wirkung wird deshalb in beiden Vorzeichen gerechnet und nicht als gemessene Physiologie benannt. Zentrale Transmittervorhersagen bestimmen kein Muskelvorzeichen.

Asynchrone Flugmuskeln erhalten neuronalen Antrieb auf einer anderen Zeitskala als der einzelne Flügelschlag. Muskel- und Thoraxmechanik sind daher ein notwendiger eigener Teil eines Flugmodells. [Hürkey et al., 2023](https://www.nature.com/articles/s41586-023-06099-0)

Dehnungsaktivierte Muskulatur kann in Verbindung mit elastischer Mechanik selbst erhaltene Schwingungen erzeugen. Die hier verwendete negative Dämpfung ist eine **eigene reduzierte Näherung** dieses Prinzips; sie rekonstruiert nicht die gemessenen Einzelmuskelgleichungen oder Verzögerungen. [Gau et al., 2023](https://www.nature.com/articles/s41586-023-06606-3)

## Bewegungsgleichungen und Einheiten

Zeit wird in Sekunden, Winkel in Radiant geführt. Kraft, Moment, Inertie und Energie sind **Modelleinheiten**, keine Newton, Newtonmeter, Kilogramm oder Joule. Die XML-Rohwerte von Flybody werden nicht stillschweigend als SI übernommen. Aus dessen Originalmodell stammen nur die dokumentierten Winkelgrenzen. [Flybody-XML](https://github.com/TuragaLab/flybody/blob/main/flybody/fruitfly/assets/fruitfly.xml)

Für jeden Flügel wird ein gekoppelter Thorax-/Schlagwinkel `q` integriert. `v = dq/dt`; die gleich großen reduzierten Inertien werden auf eins normiert:

```text
power = min(filtered_DLM, filtered_DVM)
transmission = max(0, 1 + polarity * 0.45 * (filtered_b1 − 0.5))
drive = 350 * power * transmission

q'' = −(2π·200)² q
      + (drive − 80 − 650 q²) q'
      − 0.02 q' |q'|
      + 20000 (q_other − q) + 20 (q'_other − q')
```

Die positive Leistungszufuhr verringert die wirksame Dämpfung. Amplitudenabhängige und aerodynamische Dämpfung begrenzen die Bewegung. Das ist eine aktive, mechanisch gekoppelte Selbstschwingung und keine passive Energieerzeugung. Der anfängliche kleine Ausschlag wird einmalig aus einem angegebenen Seed gesetzt; er ist keine periodische Anregung. Ohne diesen Ausschlag bleibt die exakt symmetrische Nullstellung numerisch unverändert, auch wenn sie unter Antrieb instabil wäre.

`min(DLM,DVM)` ist eine explizite Demonstrationsannahme, um beide antagonistischen Leistungsgruppen getrennt prüfen zu können. Sie ist keine experimentell bestimmte Rekrutierungsformel. Auch der gemeinsame Poolmittelwert, die Aktivierungszeitkonstanten und die b1-Modulation des mechanischen Übertragungsgains sind unkalibriert. Standardantrieb DLM/DVM = 0,7; b1-Grundwert = 0,5.

Der Pitchwinkel besitzt eine eigene gedämpfte Dynamik. Sein Strömungsmoment wird vereinfacht durch einen von der tatsächlichen Schlaggeschwindigkeit abhängigen Gleichgewichtswinkel beschrieben:

```text
pitch_target = 0.7 tanh(q'/120)
pitch'' = (2π·600)² (pitch_target − pitch) − 2·0.6·(2π·600) pitch'
```

Es gibt keinen vorgegebenen Pitch-Zeitverlauf. Diese Näherung bildet weder vollständige Strömung noch den elastischen Flügel realistisch ab. Elevation bleibt in diesem ersten Prüfstand fest auf null. Eine gedämpfte Halterenkoordinate folgt mechanisch `−0.12 q`; ihre Phase ist eine gesetzte Kopplungsannahme, keine Messung einer einzelnen sensorischen Root-ID.

Die gerichtete vertikale Kraftnäherung pro Seite ist `10⁻⁶ q' |q'| sin(2·pitch)`. Aus der Differenz beider Kräfte entsteht ein Rollmoment mit Hebel 0,08. Der Rollwinkel folgt diesem Moment, dem gegebenen äußeren Moment und der Dämpfung. Pitch-Kopplung, Luftkraftnäherung und Schlagwiderstand sind separate reduzierte Annahmen; sie bilden keinen vollständig energiekonsistenten Fluid-Struktur-Solver. Aus einer positiven Kraftsumme folgt hier **kein nachgewiesenes Abheben**.

Alle numerischen Parameter besitzen in `FLIGHT_PARAMETER_PROVENANCE` einen Herkunftseintrag. Winkelgrenzen aus dem Flybody-Modell sind Modellreferenzen, keine Kalibrierung des BANC-Tiers. Der Frequenzmaßstab 200 Hz ist gesetzt und wird nicht als aus den neuronalen Kontakten entdeckte Frequenz ausgegeben.

## Rollfeedback und Kontrollen

Der technische Sensor misst nur die Rollgeschwindigkeit mit 3 ms Verzögerung und 2 ms Filterzeitkonstante. Daraus werden gegenläufige b1-Kommandos erzeugt. Es gibt keinen Positions- oder Flugbahn-Sollwert. Diese Engineering-Verbindung besitzt keine erfundene biologische Synapsen-ID.

Der Versuchsplan enthält:

- Passiver Ausschwingversuch und tonischen Leistungsantrieb.
- Antrieb nach halber Laufzeit ausschalten.
- DVM-Pools ausschalten, während DLM aktiv bleibt.
- Linksseitige und rechtsseitige b1-Intervention als Spiegelkontrolle.
- Gleichen äußeren Rollimpuls mit offener und technischer Rückmeldung.
- Beide unbekannten b1-Wirkungsvorzeichen, einschließlich der verschlechternden Variante.
- Drei zusätzliche Leistungsniveaus, halbierten Integrationsschritt, Wiederholung und anderen Seed.

Die Grenzen verhindern numerisches Durchschlagen. Jede Grenzberührung wird gezählt; eine begrenzte oder instabile Antwort wird nicht als erfolgreiche Flugstabilisierung bewertet.

## Darstellung und Reproduktion

Integration mit RK4 und **50 µs** Schrittweite; Standardaufzeichnung alle fünf Schritte, also 4.000 Frames pro Modellsekunde. Die Darstellung darf in echter Zeitlupe laufen: Der Körper erhält dabei unveränderte integrierte Modellwinkel. Das Verlangsamen des Flügelschlags durch Ändern der Physikfrequenz wäre ein anderer Versuch.

```text
node --test app/tests/flight_model.test.mjs
node app/flight_audit.mjs
```

Neun Tests prüfen exakte Motoridentitäten und gekreuzte Seiten, Ausschluss von Annotationskonflikten, passive Energiedissipation, Leistungszufuhr, Abschaltung, Nullgleichgewicht, Spiegelkontrollen, Feedback-Vorzeichen, Gelenkgrenzen und Übereinstimmung bei halbiertem Zeitschritt. Der Audit enthält sämtliche Ergebnisse, Parameter und Quellhashes. Er bestätigt einen transparenten mechanischen Prüfstand, keine vollständig autonome künstliche Fliege.
