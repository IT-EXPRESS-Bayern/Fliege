# Sensor–Nervennetz–Gelenk: erster geschlossener Modellversuch

Stand: 27.09.2026. [Browserlabor](./sensorimotor.html), [Kern](./sensorimotor_model.mjs), [Audit](./data/sensorimotor_audit.json), [Quelldaten](./data/sensorimotor_mapping.json).

## Aussage und Reichweite

Die tatsächliche Winkeländerung des **linken Vorderbeingelenks (LF, Femur–Tibia)** erzeugt sensorische Eingänge. Diese verändern Zustände exakt benannter BANC-Neuronen entlang rekonstruierter Kanten. Getrennte Beuger- und Streckmotorneuronen wirken auf dasselbe Gelenk zurück. Damit besteht ein kausaler geschlossener Modellkreis.

Eine biologisch validierte Rekonstruktion ist dies noch nicht. Die Polarität der einzelnen Sensorzelle, Rezeptorwirkung, Membrandynamik und Muskelkraft sind unbekannt. Es handelt sich um kontinuierliche Modellaktivität von 0 bis 1, **keine gemessenen Feuerraten oder Spikezeiten**. Der Körper ist aufgehängt, die anderen fünf Beine bleiben in Ruhe; Bodenkontakt, Balance, Gang, Flug und Motivation sind nicht modelliert. Eine gewünschte Laufroute wird nicht eingespeist.

## Anatomischer Ausschnitt

Alle IDs gehören zum selben BANC-v888-Tier. Es werden keine FAFB-IDs angehängt. Detektor v2 und v3 sind getrennte Replikate; ihre Kontakte werden nie addiert.

| Standardfilter | v2 | v3 |
|---|---:|---:|
| LF-claw-Sensoren | 27 | 27 |
| LF-hook-Sensoren | 27 | 27 |
| VNC-Zwischenzellen | 45 | 55 |
| Motorneuronen: Beuger / Strecker | 17 / 2 | 17 / 2 |
| Unterschiedliche Kanten | 321 | 461 |
| Kanten mit im Standard unbekannter Wirkung, daher dynamisch neutral | 57 | 72 |

Nur `proofread === true`, mindestens fünf Kontakte **pro Kante**, direkte Sensor→MN- oder Sensor→VNC-Zwischenzelle→MN-Verbindungen. Alle auf diese Weise erreichbaren Muskeln beider Pools bleiben erhalten; die Pools werden nicht nach erfolgreichem Verhalten ausgewählt. Nicht ausgewählte interne oder rekurrente Wege fehlen im Modell. Die club-Sensoren bleiben im Quelldatensatz, haben hier keinen dynamischen Kanal.

Jede Kante behält ihre Original-IDs und Kontaktzahl. Ihr positives Gewicht ist `count / fullPostsynapticInputCount` derselben Detektorversion. Der Nenner kommt aus dem gesamten ursprünglichen Graphen ohne Autapsen. Diese Normierung ist eine Modellannahme, keine gemessene Leitfähigkeit. Weggelassene Eingänge liefern keine Abweichung von der gesetzten Grundaktivität.

## Was aus Literatur stammt

Claw und hook haben unterschiedliche propriozeptive Rollen: Position beziehungsweise gerichtete Gelenkbewegung. Einzelne Zellen besitzen unterschiedliche Winkelbereiche; die vereinfachten linearen Kennlinien unten sind deshalb keine publizierte Messkurve. [Mamiya et al., 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC6481666/)

Die FANC-Rekonstruktion beschreibt unterschiedliche flexions- und extensionsbezogene Sensorgruppen und Wege zu motorischen Netzwerken. Solche funktionellen Gruppen dürfen ohne geprüften Abgleich nicht auf beliebige BANC-Root-IDs übertragen werden. Auch anatomische Einflussmaße ersetzen keine dynamische Validierung. [Lee et al., 2025](https://www.nature.com/articles/s41467-025-59302-3)

Motorneuronen unterscheiden sich stark in ihrer mechanischen Wirkung. Gleiche Modellaktivität und Poolmittelwert sind hier ausdrücklich ungeprüfte Vereinfachungen. [Azevedo et al., 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7347388/)

## Offen gelegte Kennlinien und Gleichungen

`q` bezeichnet den geometrischen Beugewinkel: gerade = 0, zunehmender Winkel = mehr Flexion. Dies ist **nicht** der anatomische Innenwinkel. `q0` ist die ruhende Startstellung des vorhandenen Körpers, keine optimierte Solltrajektorie. `v` ist die Winkelgeschwindigkeit.

Alle claw-Zellen erhalten dieselbe populationsweite Testkennlinie; alle hook-Zellen ebenso:

```text
claw_target = clip(0.5 + polarity_claw * 1.0 * (q_delayed − q0), 0, 1)
hook_target = clip(0.5 + polarity_hook * 0.1 * v_delayed, 0, 1)
```

Die vier Kombinationen `(+,+)`, `(+,−)`, `(−,+)`, `(−,−)` werden gleichberechtigt untersucht. `tuningPolarity` bleibt im Quellkatalog für jede Zelle `null`. Es gibt keine zufällige oder zeilenweise Aufteilung unbekannter Zellen in physiologische Richtungsklassen. Die erste Kombination ist allein die Anzeigevoreinstellung.

Für jede Zwischenzelle und jedes MN wird ein eigener Zustand `r_i` geführt:

```text
I_i = sum_j [ assumedSign_j * count_ji / totalInput_i * (r_j − 0.5) ]
target_i = clip(0.5 + graphGain * I_i, 0, 1)
r_i(new) = r_i(old) + (target_i − r_i(old)) * (1 − exp(−dt/tau_i))
```

Die Zustände werden synchron aktualisiert. Dadurch erzeugt die Sensoraktualisierung keine sofortige Antwort über beliebig viele Zwischenzellen. Die Subtraktion von 0,5 ist eine deklarierte Zentrierung mit ausgeglichener Grundaktivität. Sie ist keine aus den Kontakten rekonstruierte Homöostase oder intrinsische Zellspannung.

Standardmäßig zählt nur verifizierte Transmitteridentität. Deren **Rezeptoreffekt bleibt angenommen**: ACh +1, GABA −1, zentrales Glutamat −1. Unbekannte, gemischte oder hier nicht modellierte modulatorische Transmitter tragen 0 bei. Der Sensitivitätstest `verified_then_predicted` verwendet zusätzlich Vorhersagen; deren Herkunft bleibt an jeder Zelle sichtbar. `biologicalSign` ist weiterhin `null`.

Die MN-Muskelansteuerung lautet:

```text
command_MN = clip(0.12 + motorGain * (r_MN − 0.5), 0, 1)
flexor_target = mean(commands of the 17 annotated flexor MNs)
extensor_target = mean(commands of the 2 annotated extensor MNs)
```

Die unterschiedliche Zellzahl wird jeweils durch den eigenen ursprünglichen Poolumfang normiert. Ein einzelnes Beuger-MN und ein einzelnes Strecker-MN sind damit mechanisch nicht gleich gewichtet. Diese Normierung, der gleiche Gain innerhalb eines Pools und die Grundaktivierung 0,12 sind ungeprüfte Demonstrationsannahmen. Die Muskelrichtung folgt ausschließlich der publizierten Muskelaktion. Eine beispielsweise vorhergesagte GABA-Klasse eines MN kehrt seine Beugeaktion **nicht** um.

Anschließend integriert unverändert `JointMotorBody` die getrennten Aktivierungen, Gegenspieler-Koaktivierung und Winkelgeschwindigkeit. Es werden dieselben Vorwärtskinematik, Längengrenzen und Gelenkgrenzen wie im [Motorlabor](./MOTOR_METHODS.md) verwendet. Koaktivierung bleibt bei Nettomoment null sichtbar und erhöht in diesem Modell Steifigkeit und Dämpfung.

| Parameter | Standard | Herkunft |
|---|---:|---|
| Integrationsschritt | 2 ms | Numerische Wahl |
| Sensor-/Neuron-Zeitkonstante | 10 / 20 ms | Unkalibrierte Wahl |
| Beobachtungsverzögerung | 8 ms | Unkalibrierte Wahl; 0 und 40 ms separat geprüft |
| Graph-Gain | 4 | Vor Auswertung festgelegt; 0 und 16 ebenfalls geprüft |
| Muskel-Gain | 1 | Unkalibrierte Wahl |
| Tonische MN-Ansteuerung | 0,12 | Gemeinsame Grundaktivierung in allen Bedingungen |
| Winkelkennlinie / Geschwindigkeitskennlinie | 1 rad⁻¹ / 0,1 s·rad⁻¹ | Unkalibrierte Wahl |
| Gelenkgrenzen | 10° bis 165° | Grenzen des vorhandenen Demonstrationskörpers |

## Kontrollen und reproduzierbare Störungen

Alle Bedingungen erhalten dieselben vorher erzeugten äußeren Momentimpulse: Beginn 1,0 s, Dauer 0,10 s; Beginn 2,2 s, Dauer 0,12 s, entgegengesetztes Vorzeichen. Der Seed 260927 bestimmt die kleinen Amplitudenvariationen. Diese Signale sind eine äußere Störung, kein gewünschter Bewegungsverlauf. Alle übrigen Parameter, die tonische Grundaktivierung und die mechanische Rückfederung bleiben gleich.

| Bedingung | Tatsächlicher Eingriff |
|---|---|
| `closed` | Aktuelle Gelenkbeobachtung wirkt über Sensoren und Kanten auf MNs zurück. |
| `sensory_open` | Sensoreingänge bleiben konstant 0,5; die Mechanik bleibt aktiv. |
| `sensory_edge_ablation` | Sensoren reagieren auf das Gelenk, aber alle ausgehenden Sensorkanten tragen null bei. |
| `frozen` | Bis 1,12 s geschlossener Kreis; danach exakt festgehaltene damalige Sensor-Zielwerte. Die eingefrorene Aktivität muss nicht null sein. |
| `replay` | Vollständige Sensor-Zielwerte eines früheren `closed`-Laufs; die aktuelle Körperbeobachtung beeinflusst den Eingang nicht. |

Ein Replay unter identischer Störung muss den Ursprungslauf exakt reproduzieren. Das allein beweist keine Rückkopplung. Deshalb erhält ein weiteres Paar bei 2,8 s einen zusätzlichen, im Spenderlauf fehlenden Momentimpuls. Die Replay-Motorbefehle bleiben exakt die alten; der geschlossene Kreis kann seine Motorantwort ändern. Eine kleinere Auslenkung ist dabei kein vorgeschriebenes Bestehenskriterium: Auch verstärkende oder praktisch wirkungslose Rückkopplung bleibt Ergebnis.

## Ergebnis des Audits

**194 Viersekundenversuche**, 388.000 Integrationsschritte, zusätzlich 24 Kleinsignal-Transferproben. Alle numerischen, Herkunfts- und Gegenkontrollprüfungen bestehen. Bei Standard-Gain 4 verändert sich die maximale Auslenkung gegenüber offener Rückmeldung über beide Detektoren und alle vier Polaritätsannahmen nur um **−0,60 % bis +0,33 % Reduktion**. Negative Reduktion bedeutet eine größere Auslenkung. Die RMS-Reduktion reicht von −1,83 % bis +1,14 %.

Der technische Kreis reagiert kausal. Die Rückkehr des Gelenks wird in diesem Versuch überwiegend durch die gesetzte Mechanik bestimmt. **Die Ergebnisse rechtfertigen weder eine Auswahl der echten Sensorpolarität noch die Behauptung eines rekonstruierten biologischen Stabilisierungsreflexes.** Kein erfolgreicher Parameterlauf wird als biologische Entdeckung umetikettiert.

Die 24 Transferproben legen von außen einen kleinen sinusförmigen Beobachtungswinkel von 0,005 rad bei 0,5 / 2 / 8 Hz an. Sie bestimmen Gain und Phase des aktiven Muskelmoments, inklusive Aktivierungsfilter. Das ist ein ausdrücklich erzwungener Systemidentifikationstest und kein Gangmuster oder autonomer Motorantrieb. Die reale Körperbeobachtung wird **nur in dieser Diagnose** ersetzt. Ein eigener Test prüft die zusätzliche Phasenverschiebung durch 20 ms Verzögerung.

## Reproduktion und API

```text
node --test app/tests/sensorimotor_model.test.mjs
node app/sensorimotor_audit.mjs
```

Zwölf Tests prüfen Herkunft der Kanten und Nenner, Proofread-Filter, fehlende Polaritätsangaben, Neuron→MN-Latenz, offene Rückmeldung, Kantenablation, Null-Gain, deterministische Störungen, Frozen- und Replay-Kontrollen, Gain/Phase sowie die echte begrenzte Körpergeometrie.

```js
const circuit = buildSensorimotorCircuit(mapping, {
  detector: 'v2', leg: 'LF', minContacts: 5, signPolicy: 'verified_only'
});
const trial = runSensorimotorTrial({
  circuit, polarity: { claw: 1, hook: 1 }, condition: 'closed',
  seed: 260927, duration: 4, includeBody: true, recordEvery: 5
});
```

`recordEvery` ändert allein die gespeicherten Ansichtsframes. Jeder neuronale und mechanische Integrationsschritt bleibt 2 ms. `sensorRecording` enthält jeden Sensor-Zielwert für die vollständige Replay-Kontrolle. Jeder Frame enthält Winkel, Geschwindigkeit, Beobachtung, benannte Sensor-/Neuron-/MN-Werte, getrennte Muskelaktivität, Koaktivierung und auf Wunsch den vorhandenen 3D-Körpersnapshot.

Der Audit speichert SHA256 des Sensor-Mappings, des Kerns, des unveränderten Gelenkmodells und der Tests. Strukturquelle: `sensorimotor_mapping.json`, SHA256 `dbf0449d7fa2951f887b62fa0a3d79b1349222d279c924499d0e6ec28aaf4ff3`. Die Originalgraphen werden nicht verändert.
