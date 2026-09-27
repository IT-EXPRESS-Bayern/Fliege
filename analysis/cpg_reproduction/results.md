# Ergebnisse der CPG-Nachrechnung

Diese Übersicht wird ausschließlich aus abgeschlossenen lokalen Läufen erzeugt. Ein Rhythmus ist eine Eigenschaft des hier geprüften Ratenmodells unter konstantem Eingang. Er bestätigt weder biologische Autonomie noch das Zusammenspiel aller sechs Beine.

## run33241778_replicate0

Eingang je angeregter Zelle: **400 willkürliche Einheiten**. Seed **129**. Gleicher Parametersatz in allen Gegenproben. Keine periodische Reizfolge.

| Bedingung | aktive echte Modulmotoren | mittlerer Rhythmik-Score | E1 Maximum (Raten-Hz) | E2 Maximum (Raten-Hz) |
|---|---:|---:|---:|---:|

| zero | 0 / 129 | 0.000000 | 0.000 | 0.000 |

| dng100 | 6 / 129 | 0.999615 | 7.656 | 8.422 |

| e1_removed | 3 / 129 | 0.000000 | 0.000 | 0.000 |

| e2_removed | 12 / 129 | 0.000000 | 12.215 | 0.000 |

| i2_removed | 10 / 129 | 0.999499 | 10.609 | 18.788 |

| dnb08_pair | 16 / 129 | 0.000000 | 0.000 | 0.000 |

| dng100_repeat | 6 / 129 | 0.999615 | 7.656 | 8.422 |

| dng100_tighter | 6 / 129 | 0.999612 | 7.654 | 8.422 |


Ruhe: maximal 0 Raten-Hz. Nullaktivität ist bei Nullzustand ohne Eingang eine erwartete Eigenschaft dieser Gleichung.

Identische Wiederholung: **True** (vollständige float64-Zeitreihe).

Engere Integratortoleranz: größte absolute Ratenabweichung **0.104239 Hz**, RMS **0.00132617 Hz**.

`e1_removed`: Scoreänderung gegenüber DNg100 **-0.999615**. Dies ist eine Modellintervention, kein Nachweis einer biologischen Zellfunktion.

`e2_removed`: Scoreänderung gegenüber DNg100 **-0.999615**. Dies ist eine Modellintervention, kein Nachweis einer biologischen Zellfunktion.

`i2_removed`: Scoreänderung gegenüber DNg100 **-0.000115**. Dies ist eine Modellintervention, kein Nachweis einer biologischen Zellfunktion.

`dnb08_pair`: Scoreänderung gegenüber DNg100 **-0.999615**. Dies ist eine Modellintervention, kein Nachweis einer biologischen Zellfunktion.


Neuronale Rhythmusfrequenz: **15.152 Hz** (Median der rhythmischen Motorzellen). Dies ist eine Frequenz abstrakter Raten; eine Schrittfrequenz des 3D-Körpers ist noch nicht kalibriert.


### Konkrete aktive Motorzellen bei DNg100

| Quell-ID | Quellseite | Muskelmodul | mittlere Rate (Hz) |
|---|---|---|---:|

| 720575941498960546 | left | coxa swing | 3.3827 |

| 720575941506261538 | left | coxa swing | 0.3334 |

| 720575941547393825 | right | tibia flex | 0.0325 |

| 720575941559281679 | right | tibia flex | 0.2987 |

| 720575941590014007 | right | tibia flex | 0.2904 |

| 720575941593715569 | right | coxa stance | 2.4587 |


Alle sechs gehören zum vorderen Beinteilnetz. Ihre Kräfte, Gelenkhebel und die Koordination mit Mittel- und Hinterbeinen werden durch diese Nachrechnung nicht bestimmt.

- [protocol.json](run33241778_replicate0/protocol.json)

- [input_audit.json](run33241778_replicate0/input_audit.json)

- [audit.json](run33241778_replicate0/audit.json)

- [motor_readout_statistics.csv](run33241778_replicate0/motor_readout_statistics.csv)

- [replay.json](run33241778_replicate0/replay.json)



## Gemeinsame Grenzen

Die 156 Einträge der originalen Modulmaske enthalten 27 Nichtmotoren oder unklassifizierte Zellen. Die hier hervorgehobene Motormaske umfasst die 129 in derselben Quelle als Motorzellen annotierten Einträge. Die Originalmaske ist zusätzlich in jedem JSON/CSV erhalten.

CPU-Port: Originale Matrix, Zufallssampling, Größenkorrektur und Rhythmikfunktion; SciPy RK45 statt Diffrax Dopri5 und float64 statt float32 für die Integration. Ein einzelner Parametersatz belegt keine Robustheit über Tiere oder viele Zufallsziehungen. Werte von Muskelkraft, Sensorik, Motivation und Plastizität werden nicht daraus abgeleitet. Siehe [Methoden und Quellen](README.md).
