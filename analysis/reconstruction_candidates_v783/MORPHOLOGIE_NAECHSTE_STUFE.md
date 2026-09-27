# Nachgelagerte Morphologieprüfung

`data/flywire_morphology_v783/sk_lod1_783_healed_ds2.parquet` wurde inzwischen vollständig heruntergeladen und gegen die [Zenodo-MD5](https://zenodo.org/records/10877326) geprüft. `.partial`-Dateien sind kein Eingabematerial. [Schema](morphology_schema_probe.json) und [zwei konkrete Punkt-zu-Skelett-Fälle](morphology_priority_site_check.json) liegen vor.

Die Quelle beschreibt v783-Skelette im SWC-Format, aus LOD-1-Meshes und zweifach heruntergerechnet, mit Nanometerkoordinaten. Damit lässt sich der räumliche Verlauf eines **proofread** Neurons prüfen. Ein ungeprüftes Partnersegment der B-Liste wird dadurch allein noch keinem vollständigen Neuron zugeordnet.

1. [probe_morphology_schema.py](probe_morphology_schema.py) liest nur Parquet-Metadaten und ermittelt Spalten, Zeilen und Root-ID-Felder. Eine Annahme über x/y/z oder SWC-Struktur wird nicht vorweggenommen.
2. Für die hochrangigen A-Roh-, B- und Princeton-Fälle zuerst Root-ID und Punktkoordinaten in derselben v783-Version abgleichen. Einzelpunkte im passenden Neuropil sind nur Kontaktindikatoren; sie zeigen noch keine kontinuierliche Segmentzugehörigkeit.
3. Für ein B-Segment die gesamte Geometrie und nachprüfbare Proofreading-/Root-ID-Abbildung prüfen. Eine ID-Übersetzung auf spätere Releases braucht eine dokumentierte Segment-Historie. Die reine NBLAST-Ähnlichkeit oder räumliche Nähe genügt nicht für eine exakte Kante.
4. Alle Vorschläge als eigene Versioned-Ebene mit Quellen-IDs, Datum, Koordinaten, visueller Prüfung, Alternativerklärung und offenem Status speichern. Den offiziellen v783-CSR nie überschreiben.

Ein Skelett kann zwar Kontaktstellen plausibilisieren oder widerlegen, liefert aber keine fehlenden unterhalb der Detektorschwelle liegenden Synapsenpositionen aus sich heraus. Für diese Fälle wären ein besserer Einzelpunktdetektor oder erneute Prüfung der Mikroskopdaten nötig. [FlyWire-Methoden](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446842/), [Matsliah et al.](https://www.nature.com/articles/s41586-024-07981-1).
