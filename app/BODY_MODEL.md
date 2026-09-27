# Beweglicher Fliegenkörper · Modellstand 27. September 2026

Die Arena verwendet einen gegliederten, geometrisch berechneten Körper. Sechs Beine besitzen jeweils Coxa, Femur, Tibia und einen zusammengefassten Tarsus. Die Beine wechseln zwischen Stand und Schwung: Ein Standfuß bleibt in Weltkoordinaten an derselben Stelle, während sich der Körper darüber bewegt. Eine glatte Schwungkurve hebt ihn an und führt ihn zum nächsten Aufsetzpunkt. Die Gelenkstellungen werden aus der gewünschten Fußposition mit inverser Kinematik berechnet. Das verhindert das vorherige Gleiten und Schwenken starrer Beinpaare.

## Was sich beobachten lässt

- Zwei versetzte Dreiergruppen koordinieren die Schritte, mit überlappender Standphase. Langsameres Laufen erzeugt kleinere, langsamere Schritte. Drehungen verändern die vorausberechneten Aufsetzpunkte.
- Jeder Schritt enthält eine abgerundete Hubbewegung; die Schrittfrequenz hängt von der tatsächlich bewegten Körperposition und Drehung ab.
- Die Körperlage enthält kleine Schrittbewegungen und eine gedämpfte Neigung beim Wenden. Der Kopf gleicht einen Teil der Körperneigung aus.
- Beim Putzen lösen sich die Vorderfüße vom Boden und bewegen sich vor dem Kopf; die vier anderen Beine bleiben stehen. Auslaufende Schritte landen auch nach einem Stopp.
- Ein starkes Putzsignal (`groom > 0.55`) hemmt am Körper die noch gleichzeitig eintreffenden abstrakten Lauf- und Drehbefehle. Die Geschwindigkeit läuft gedämpft aus, bevor die Vorderbeine angehoben werden. Diese Konfliktauflösung ist eine eigene Modellannahme; das Eigenaktivitätsmodell bleibt unverändert.
- Segmentierter Hinterleib, Facettenaugen, Fühler mit Arista, Halteren, Borsten und gefaltete Flügel mit Adern machen die Geometrie besser als Fliege erkennbar.
- Die Nahansicht folgt dem Körper. Der Knopf darüber wechselt zur Arenaübersicht. Die optionalen Bodenmarkierungen und die sechs Statusfelder zeigen Stand beziehungsweise Schwung/Putzen.

## Gemessene Körperzustände für spätere Rückkopplung

`window.FlyDemo.getBodyObservation()` liefert einen unabhängigen Schnappschuss. Derselbe Zustand steht als `body` in `window.FlyDemo.getObservation()` zur Verfügung und erreicht damit einen später ausdrücklich eingerichteten Sensoradapter. Die momentanen Gelenkwinkel stammen aus der dargestellten Modellgeometrie. Sie sind keine Messungen an einem Tier.

```js
{
  schema: 'fly.body-observation.v1',
  model: 'kinematic-articulated-v1',
  units: { length: 'model-unit', angle: 'radian', time: 'second' },
  timeSeconds: 12.5,
  pose: { x, z, yaw, height, pitch, roll },
  velocity: { x, z, yaw },
  gaitFrequencyHz,
  contacts,                 // Zahl geometrisch aufgesetzter Füße
  contactForces: null,       // kein Kraftsolver vorhanden
  biologicalCalibration: false,
  legs: [{
    id: 'LF',               // LF, LM, LH, RF, RM, RH
    phase: 'stance',         // stance, swing oder groom
    contact: true,
    footWorld: [x, y, z],
    footTargetWorld: [x, y, z],
    jointAngles: { coxaAzimuth, femurElevation, femurTibia, tibiaTarsus },
    jointVelocity: { coxaAzimuth, femurElevation, femurTibia, tibiaTarsus },
    reachError,             // Abstand zwischen Ziel und erreichbarem Fußpunkt
    pointsLocal: [hip, coxaEnd, knee, ankle, foot]
  }]
}
```

Koordinaten: Y zeigt nach oben, Z im körperfesten System nach vorn, X zur rechten Körperseite. Die Rotation des Körpers folgt Yaw → Pitch → Roll in der Three.js-Eulerkonvention `YXZ`. L/R bezeichnet linke/rechte Seite, F/M/H Vorder-/Mittel-/Hinterbein. Die Längen sind Modellwerte ohne behauptete Millimeterkalibrierung. Winkelgeschwindigkeiten sind Änderungen pro Sekunde. Zeit bezieht sich auf simulierte, nicht pausierte Zeit.

`coxaAzimuth` ist hier der seitennormierte Azimut des Femurs am proximalen Beinkomplex, `femurElevation` seine Höhe gegenüber der horizontalen Ebene. `femurTibia` und `tibiaTarsus` sind geometrische Beugungswinkel; eine gerade Fortsetzung entspricht null. Coxa–Trochanter und die einzelnen Tarsomere sind zusammengefasst. Diese vier Winkel pro Bein sind **keine** direkte Übernahme von FlyGym-Gelenkkoordinaten und keine vollständige Menge biologischer Freiheitsgrade.

Die bestehende Eigenaktivitätssteuerung liefert weiterhin die abstrakten Befehle Vorwärts, Drehung, Flügel und Putzen. Es gibt weiterhin keine validierte FlyWire-Muskelzuordnung. Der Graph-Inspektionsmodus lädt den Originalgraphen; die neue Anatomie fügt diesem Graphen keine automatischen motorischen oder sensorischen Kanten hinzu. Ein ausdrücklich eingerichteter Sensoradapter kann nun die zusätzliche Körperbeobachtung auswerten, muss die Verbindung zu bestimmten Root-IDs und deren Skalierung aber begründen.

## Herkunft und offene Arbeit

Die Architektur berücksichtigt das Prinzip von Gelenkrückmeldung und Bodenkontakten aus [NeuroMechFly v2 / FlyGym](https://doi.org/10.1038/s41592-024-02497-y); dessen [Dokumentation zur Kopfstabilisierung](https://flygym.readthedocs.io/latest/tutorials/head_stabilization.html) verwendet Gelenkstellungen und Kontakte als Eingänge. [FlyBody](https://doi.org/10.1038/s41586-025-09029-4) zeigt, welche zusätzlichen Komponenten ein vollständiges physikalisches Fliegenmodell braucht: Körperdynamik, Gelenkmomente, Kontaktphysik und trainierte Bewegungssteuerung. Unsere Browsergeometrie, Segmentlängen, Schrittkurven, Frequenzen und die Kopfkompensation sind eigene, noch unkalibrierte Modellannahmen. Die lokalen Referenzpakete enthalten die Originalarbeiten und Quelltexte; daraus wurden hier keine trainierten Steuerungen oder Körpermeshes übernommen.

Dieser Stand ist für sichtbare Gelenkbewegung, Koordinatenprüfungen und den Entwurf einer Körperschnittstelle geeignet. Noch offen sind Massenträgheit, Muskelkräfte, elastische Sehnen, Haftkräfte, echte Kontaktkräfte, Hinderniskollisionen, eine validierte Flugmechanik und der Abgleich mit gemessenen Gangsequenzen. Der Rumpf folgt weiterhin den Geschwindigkeitsbefehlen; Bodenreaktionskräfte treiben ihn noch nicht an. Die Flügelbewegung im Stand ist dekorative Bewegung, keine aerodynamische Simulation.

Ein nächster begründeter Anschluss kann BANC-Motorneuronen nach Bein, Seite und Muskelaktion mit einem physikalischen Gelenkmodell vergleichen. Für die Übertragung auf das FAFB-Gehirn werden zusätzlich nachvollziehbare Zellzuordnungen, Bauchmarksschaltkreise, Sensorskalierung und Perturbationstests gebraucht. Anatomisch ähnliche Namen allein rechtfertigen keine Kopplung.

Die lokale [BANC-Referenztabelle](./data/banc_leg_motor_reference.json) enthält bereits 391 annotierte Beinmotorneuronen mit exakten BANC-v888-IDs, Körperseite, Beinpaar und publizierter Funktionsbezeichnung. Vorgeschlagene Beobachtungskanäle dienen dem Vergleich mit diesem Modell. Alle Einträge tragen `enabled_for_control: false`; Vorzeichen und Kraftverstärkung sind offen. BANC stammt von einem anderen Tier als FAFB. Die dokumentierte Aufbereitung liegt in `analysis/body_neural_interface/README.md`; die Originalquelle ist der [BANC-Datensatz](https://doi.org/10.7910/DVN/7WTH1N).

## Prüfung

`node --test app/tests/*.test.mjs` prüft zusätzlich zur bestehenden Steuerung und Graphanbindung: Umkehrbarkeit der Koordinatentransformation, konstante Segmentlängen, gleitfreie Standfüße, Fußhöhen über dem Boden, erreichbare Laufstellungen, endliche Gelenkwinkel und -geschwindigkeiten, Landen nach dem Stopp, Vorderbein-Putzen und Rücksetzen. Diese Prüfungen bestätigen Konsistenz der Kinematik; biologische Übereinstimmung erfordert einen separaten Datenvergleich.
