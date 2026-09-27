# Öffentliche Forschungsfassung

`publish.py` erstellt eine explizite Liste veröffentlichbarer Dateien samt getrennten SHA256 für Original und öffentliche Kopie. Das Programm lädt nichts herunter, führt weder Git-Befehle noch Simulationen aus und verändert keine wissenschaftliche Quelldatei.

```sh
python analysis/github_publication/publish.py --plan
python analysis/github_publication/publish.py --stage /path/to/publication-checkout
```

Unter Windows genügt die vorhandene Python-Umgebung `analysis/.venv/Scripts/python.exe`. Python 3.10 oder neuer und seine Standardbibliothek reichen. `--stage` schreibt nur in das ausdrücklich angegebene Ziel; vorhandene gleichnamige Dateien werden dort aktualisiert, andere Dateien nicht gelöscht. Der Veröffentlichende prüft danach den Git-Diff und entscheidet selbst über Commit und Push.

## Auswahl

- Eigener App-/Gehirn-/Analysecode, Dokumentation, negative Befunde, Prüfprotokolle und Ergebnisdateien bis 10 MB.
- App-JSONs auch bis 40 MB, damit Assay-, Motor-, CPG- und Sensorimotor-Replays vollständig bleiben; Three.js samt mitgeliefertem MIT-Lizenzhinweis.
- Kleine ursprüngliche CPG-Matrix, Tabellen, Konfigurationen und unveränderter Parameterextrakt; Quell- und Lizenzhinweise in `PUBLICATION_NOTES.md` und `license_review.json`.
- Wissenschaftliche Quellen-/Provenienz-JSONs; feste Downloadadressen und wissenschaftliche Prüfsummen bleiben erhalten.
- Vom Data-Bericht nur selbst geschriebene Inhalte. Geschützte Laufzeit, Hosting-Konfiguration und gebaute Distribution werden ausgeschlossen.

Vollständige Graph-Binärdateien, große Tabellen/Parquet-Dateien, andere fremde Originale, PDFs, Browser-Screenshots, Umgebungen, Caches, Logs und die persönliche Cloudübergabe sind ausgeschlossen. Der alte CPG-Downloadstatus und seine lokale Statusseite sind ebenfalls kein wissenschaftliches Ergebnis.

## Datenschutz und Prüfbarkeit

In der öffentlichen Kopie werden persönliche Home-Verzeichnisse durch `<USER_HOME>` und private Sitzungslinks durch einen neutralen Platzhalter ersetzt. Jede betroffene Datei erhält einen Eintrag mit Änderungstyp und Anzahl. Geheime Schlüssel werden nicht bereinigt, sondern blockieren den Export. Wissenschaftliche IDs, Gewichte, Raten, Resultate und referenzierte SHA256 werden nicht umgeschrieben.

`manifest.json` enthält alle explizit ausgewählten Pfade und beide Prüfsummen. Ausgeschlossene wissenschaftliche Dateien sind einzeln, große Laufzeit-/Cache-Bäume als Verzeichniseinträge erfasst. `SHA256SUMS` prüft die veröffentlichten Nutzdateien; das Manifest besitzt keinen zirkulären Selbsthash.

In der Veröffentlichungskopie ersetzt der Export lokale Berichtslinks auf Port 4180 und 8765 durch die öffentlichen Forschungs- und Quellenübersichten. Einige Ansichten laden externe vollständige Graphen; ohne diese bleiben die gespeicherten Replays benutzbar, die vollständige Gehirnsimulation benötigt zusätzliche Daten. Ein GitHub-Repository stellt allein keinen Rechenserver bereit.
