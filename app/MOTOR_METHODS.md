# Motorlabor: anatomische Aktion → antagonistische Gelenkdynamik

`motor.html` prüft eine direkte, unkalibrierte Ansteuerung einzelner Femur–Tibia-Gelenke am bestehenden 3D-Körper. Die neue Datei `joint_motor_model.mjs` ist unabhängig vom Geh-/Putzprogramm der Arena. Körperposition, Hüfte und Femur bleiben im fixierten Versuchsaufbau unverändert; Tibia und Tarsus bewegen sich durch Vorwärtskinematik um die definierte Gelenkachse.

## Quellen und Reichweite

Der [BANC-v888-Datensatz](https://doi.org/10.7910/DVN/7WTH1N), beschrieben in [Bates, Phelps, Kim et al.](https://doi.org/10.1038/s41586-026-10735-w), enthält die lokal exportierten 391 annotierten Beinmotorneuronen. Die expliziten Quellaktionen `flex_femur_tibia_joint` und `extend_femur_tibia_joint` liefern 101 Beuger- und 12 Strecker-IDs. Die übrigen 278 IDs bleiben als Quellen im Motorpfadexport erhalten, erhalten in diesem Experiment aber keinen Ersatzaktor.

DN→vorgeschaltete Zelle→MN-Pfade werden mit den individuellen BANC-IDs und getrennten v2/v3-Synapsenzahlen gezeigt. Es gibt hier keine simulierte Ausbreitung von Aktionspotenzialen durch BANC. Ein direkter Motorversuch setzt Aktivierungen bestimmter Motor-IDs vorgegeben auf 0–1. Eine strukturelle Verbindung ist keine gemessene motorische Aktivität. BANC und FAFB stammen von verschiedenen Tieren; ihre IDs werden nicht gleichgesetzt.

Motorneuronen können sehr unterschiedliche Kräfte erzeugen. [Azevedo et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7347388/) beschreiben unterschiedlich starke, verschieden rekrutierte Tibia-Beuger. Deshalb ist unser gleich gewichtetes Poolmittel keine behauptete Muskelphysiologie. Ebenso bildet ein gleiches Signal beider Gegenspieler nicht fehlende Muskelaktivität ab. [Sapkal et al. 2024](https://www.nature.com/articles/s41586-024-07854-7) zeigen eine aktive Erhöhung des Gelenkwiderstands beim BRK-Mechanismus. Dies motiviert die getrennte Anzeige von Aktivierung, Nettomoment und Steifigkeit; unsere Parameter werden daraus nicht numerisch abgeleitet.

## Nachvollziehbare Zuordnung

- Jede ID bleibt eine Zeichenkette; die Körperseite stammt aus der Motorannotation.
- Nur die zwei exakten Quellaktionen werden zugeordnet, mit getrennten Beuger- und Streckerpools je Bein.
- Doppelte IDs im selben Pool werden entfernt. Widersprüchliche Rollen derselben ID lösen einen Fehler aus.
- Die Aktivierung ist der Mittelwert über die ursprüngliche Anzahl eindeutiger IDs. Eine ausgeschaltete ID bleibt mit Null im Nenner; Ausfälle werden nicht durch Umnormierung kompensiert.
- Die zentrale Transmittervorhersage bestimmt hier nicht das Muskelvorzeichen. Eine positive Motoraktivierung wirkt gemäß der annotierten Muskelaktion. Es gibt keine pauschale Übertragung des inhibitorischen Glutamat-Vorzeichens der Hirnengine auf den Muskel.
- Der ursprüngliche Referenzexport behält `enabled_for_control=false`. Das separate Motorlabor führt eine ausdrücklich experimentelle Zuordnung aus; es schaltet keine biologisch validierte Steuerung in der Arena frei.

## Gelenkgleichung

Aktivierungsfilter mit Zeitkonstante 0,07 s:

`a += (Poolmittel − a) × (1 − exp(−dt / 0,07))`

Für die Beuger- und Streckeraktivierung `aF`, `aE`:

```
c = min(aF, aE)
K = 7 + 45 c
D = 5 + 8 c
M_aktiv = 18 (aF − aE)
q'' = [M_aktiv + M_stör − K (q − q_ruhend) − D q'] / I
I = 1
```

Alle mechanischen Zahlen sind **unkalibrierte Modelleinheiten**. `q` ist der Beugewinkel in Radiant: gerade = 0; zunehmender Wert = stärkere Beugung. Er ergänzt den häufig publizierten inneren Gelenkwinkel zu π. Grenzen 10°–165°, Trägheit, Widerstände und Aktivierung sind Modellannahmen; keine Kräfte in µN werden behauptet. Die Integration erfolgt deterministisch in 2-ms-Schritten. Gelenkgrenzen begrenzen Winkel und nach außen gerichtete Geschwindigkeit.

## Vorwärtskinematik

Die Ausgangslage verwendet einmalig die bisherige Körpergeometrie. Danach bleibt der Femur fixiert. Die Tibia rotiert um das Kreuzprodukt der initialen Femur- und Tibiarichtung. Der Tarsus rotiert mit der Tibia; alle vier Segmentlängen bleiben konstant. Gezeigt wird ein fixierter Körper mit freien Beinen. Es gibt keine künstlichen Bodenkontakte, Fußziele oder Gangphase. Dekorative Fühler-/Kopfbewegungen sind eingefroren.

## Kontrollversuche

Jeder Versuch dauert 3 s. Die direkte Motoraktivierung liegt von 0,4 bis 2,4 s an. Das Störmoment beträgt 12 Modelleinheiten von 1,2 bis <1,3 s.

1. Nullkontrolle: kein Eingang, keine Bewegung.
2. Beuger: positive Beugung des benannten Beins.
3. Strecker: entgegengesetzte Winkeländerung.
4. Ablation: angeregte Beuger-IDs ausgeschaltet; kein Signal.
5. Sham: gleich viele nicht angeregte andere IDs ausgeschaltet; direkte Beugerantwort bleibt gleich. Dies ist ein technischer Spezifitätstest, kein Netzwerk-Kausaltest.
6. Koaktivierung: beide vollständigen Gegenpools gleich aktiv; praktisch Null Nettomoment bei erhöhter Steifigkeit.
7. Passives Störmoment und 8. dasselbe Störmoment unter Koaktivierung: prüft die implementierte Widerstandserhöhung.

## Reproduktion

`node --test app/tests/joint_motor_model.test.mjs`

`node app/audit-motor-joints.mjs`

Tests prüfen alle sechs Beine, Quell-ID-Zuordnung, Deduplizierung, feste Normalisierung nach Ablation, Null-/Sham-/Antagonistenkontrollen, Reaktion auf identische Störung, Gelenkgrenzen und unveränderte Segmentlängen. Der Audit speichert die 48 vollständigen Kontrollversuche und die Quellprüfsummen in `data/motor_joint_audit.json`.
