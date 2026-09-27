# Prüflogik für Neuronenbenennung und Körperzuordnung

Stand: 27. September 2026. Dieser Arbeitsstand ergänzt den vollständigen [Detektorvergleich](whole_brain_detector_comparison/METHODEN_UND_ERGEBNISSE.md) um Zellrollen, gerichtete Wege und dynamische Interventionen. Ziel ist eine nachvollziehbare Zuordnung konkreter IDs zu prüfbaren Modellfunktionen.

## Vier Aussagen mit unterschiedlicher Beweiskraft

1. **Identität:** Eine Root-ID existiert im gepinnten v783-Datensatz und hat eine veröffentlichte Zelltyp-/Seitenannotation. Nicht typisierte Zellen erhalten keine erfundenen biologischen Namen.
2. **Funktionshinweis:** Eine Fachquelle ordnet einem Zelltyp oder einer identifizierten Zelle eine sensorische oder motorische Rolle zu. Physiologische Experimente an anderen Fliegen sind keine direkte Messung der Aktivität dieses FAFB-Präparats.
3. **Wirkung im neuronalen Modell:** Ein festgelegter Reiz ändert die Aktivität eines getrennten Ausgangsneurons. Gezielt entfernte Eingänge, ausgeschaltete Zwischen-/Ausgangszellen und Vergleichszellen prüfen, welche Modellteile dafür erforderlich sind.
4. **Wirkung im Körpermodell:** Eine offen dokumentierte Übersetzung aus gemessener Modellaktivität erzeugt einen Befehl für den gegliederten Körper. Die Körperreaktion prüft diese technische Übersetzung und die Kinematik. Sie liefert keine unabhängige Bestätigung derselben eingebauten biologischen Funktionsannahme.

Eine Zelle kann viele kontextabhängige Funktionen haben. Ein einzelner erfolgreicher Versuch benennt deshalb kein exklusives „Zuständigkeitszentrum“. Ein erfolgloser Versuch widerlegt nicht automatisch die Literatur: Fehlende Verbindungen, Versionsunterschiede und unpassende Dynamik können ebenfalls eine Ursache sein.

## Untersuchungen

Die [strukturelle Pfadprüfung](neuron_pathways/README.md) verwendet den vollständigen Originalgraphen und prüft kurze Wege zwischen publizierten Sinnesgruppen und Ausgangsneuronen. Sie betrachtet Kantenschwellen von einer und fünf Synapsen getrennt und interpretiert fehlende Vier-Schritt-Wege ausdrücklich nicht als globale Unverbundenheit.

Die dynamischen Versuche verwenden dokumentierte, festgehaltene Parameter des vorhandenen explorativen Modells. Versuchszeit, Stimulationsfenster, Eingangsfrequenz, Startzustand, Eingangs-IDs, Auslese-IDs und Stilllegungen werden gespeichert. Zellen werden über exakte ID-Sets angeregt; das Ausgangsneuron wird im eigentlichen Weiterleitungstest nicht direkt erzwungen. Eine direkte Ausgangsanregung bleibt ein gesonderter technischer Positivtest.

Verglichen werden Ruhebedingungen, verschiedene Eingangsklassen und Reizstärken sowie gezieltes Stilllegen und eine nachvollziehbare Kontroll-Stilllegung. Die gleiche Reizfolge und derselbe Startzustand gelten für die jeweils gepaarten Versuche. Die Datenanalyse nutzt die vollständigen internen Spike-Indices; eine gekürzte Browserliste darf keine Zählbasis sein. Ereignisgrenzen oder abgebrochene Läufe werden als solche ausgewiesen.

JO-C/E und JO-F haben unterschiedlich viele im Graphen verfügbare Zellen. Gleiche Rate je Eingangsneuron bedeutet daher nicht dieselbe Gesamtreizmenge. Zusätzlich zur Vollgruppen-Antwort ist ein Vergleich mit angeglichener Zahl/Belastung erforderlich, bevor Zellklassen-Selektivität behauptet wird. Auch eine Kontroll-Stilllegung ist nur so gut wie die offengelegte Auswahl der Vergleichszellen.

## Körpertests und Ergebnissprache

Das 3D-Labor verwendet die tatsächlich aufgezeichneten neuronalen Zeitreihen. Eine Wiederholung zeigt diese Messung erneut und rechnet die Körperantwort; sie ist als Replay erkennbar. Zeitlupe ändert nur die Wiedergabe, nicht die ausgewertete neuronale Rate. Bleibt die Ausleseaktivität null, erzeugt der Adapter daraus keinen erfundenen Bewegungsimpuls. Gelenkwinkel, Kontakte und Bewegungen werden als Modellgrößen ausgegeben.

„Technisch bestanden“ bedeutet: Dateien und IDs sind gültig, die Intervention wurde angewandt, die Auslese stimmt mit den aufgezeichneten Ereignissen überein, und der Körper reagiert gemäß seiner angegebenen Schnittstelle. „Im Modell unterstützt“ bedeutet: Eine vorab benannte erwartete Änderung zeigt sich unter diesen Einstellungen und ist durch passende Gegenbedingungen eingegrenzt. **Biologisch bestätigt** darf daraus nicht abgeleitet werden.

Referenzen: [Shiu et al. – sensorimotorisches Gehirnmodell](https://doi.org/10.1038/s41586-024-07763-9), [Steuerung einzelner Beinschritte durch DNa02/DNg13](https://doi.org/10.1016/j.cell.2024.08.033), [Tastekin et al. – Geschmacks-/Fressschaltkreise](https://doi.org/10.1016/j.cell.2026.08.016), [Körpermodell und seine Grenzen](../app/BODY_MODEL.md).
