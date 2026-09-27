"""Attach the completed original-parameter CPG recomputation to the existing report."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def extend_cpg_snapshot(snapshot):
    folder = ROOT / 'analysis/cpg_reproduction/run33241778_replicate0'
    audit = json.loads((folder / 'audit.json').read_text(encoding='utf-8'))
    assert all(c['pass'] for c in audit['checks'])
    assert audit['original_rhs_comparison']['status'] == 'passed'
    assert hashlib.sha256((folder / 'summary.json').read_bytes()).hexdigest() == audit['outputs']['summary.json']
    summary = json.loads((folder / 'summary.json').read_text(encoding='utf-8'))
    labels = {'zero': 'Kein Eingang', 'dng100': 'DNg100: konstant 400', 'e1_removed': 'DNg100, E1 entfernt',
              'e2_removed': 'DNg100, E2 entfernt', 'i2_removed': 'DNg100, I2 entfernt',
              'dnb08_pair': 'DNb08-Paar: je 400', 'dng100_repeat': 'Identische Wiederholung', 'dng100_tighter': 'Engere Integratortoleranz'}
    rows = []
    for key, item in summary['conditions'].items():
        motor = item['conservative_motor_mask']
        frequency = motor['median_autocorrelation_frequency_hz_for_rhythmic_cells']
        rows.append({'condition': labels[key], 'active': motor['active_post_transient'],
                     'rhythmic': motor['rhythmic_cells_score_above_0_5'],
                     'score': round(motor['mean_rhythmicity'], 6),
                     'frequency': round(frequency, 3) if frequency is not None else None})
    assert len(rows) == 8
    snapshot['report']['cpg'] = {'conditions': 8, 'neurons': audit['n_neurons'], 'originalParameterReplicate': 0,
                                'archivedTrajectoryEqualityTested': False, 'biologicalValidation': False}
    snapshot['queries']['cpg_original_parameter_controls'] = {'rows': rows, 'source': {
        'label': 'Nachrechnung des 4963-Zellen-BANC-Ratenmodells mit originalem Parametersatz 0',
        'executedAt': datetime.fromtimestamp((folder / 'summary.json').stat().st_mtime, timezone.utc).isoformat(),
        'tables': [{'name': 'Originalpublikation (Preprint)', 'href': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC13142387/'},
                   {'name': 'Originalarchiv', 'href': 'https://zenodo.org/records/22260924'},
                   {'name': 'Gepinnter Originalcode', 'href': 'https://github.com/smpuglie/Pugliese_2026/tree/10e7661bf414ba7b4c2edf795cd36d0f878c17c0'},
                   {'name': 'Lokale Versuchskurven', 'href': 'http://127.0.0.1:4173/cpg.html'}],
        'evidenceFlow': [{'title': 'Originale Eingaben', 'detail': 'Originale signierte Matrix und 4963-IDs, exakte run33241778-Konfiguration sowie archivierte tau/a/threshold/fr_cap des Replikats 0. Keine neue Zufallsziehung und keine zweite Flächennormierung. Parameterauszug-SHA256: ' + audit['archived_parameters']['sha256']},
                         {'title': 'Gezielter Archivzugriff', 'detail': 'Die benötigten YAML-Dateien wurden mit ZIP-CRC geprüft; HDF5-Arrays wurden per HTTPS-Range ausgelesen. Weder das gesamte 807-MB-Archiv noch seine vollständige MD5-Prüfung sind abgeschlossen. Die kompletten archivierten Raten wurden nicht heruntergeladen.'},
                         {'title': 'Nachrechnung', 'detail': 'SciPy RK45 mit float64-Zuständen statt Diffrax Dopri5/float32. Originale rechte Gleichungsseite numerisch verglichen; Wiederholung identisch, engere Toleranz geprüft. Keine Gleichheit mit den original gespeicherten Zeitreihen behauptet.'},
                         {'title': 'Kontrollen und Auswertung', 'detail': 'Acht Bedingungen, ein Parametersatz. Extern angelegter konstanter Eingang 400 je stimulierter Zelle. DNb08-Paar hat insgesamt den doppelten Eingang. Konservative Motormaske 129, originale Modulmaske 156 einschließlich 27 Nichtmotoren/unklaren Zellen. Keine ungünstigen Bedingungen ausgeblendet.'},
                         {'title': 'Grenze', 'detail': 'Rhythmus in sechs Frontbein-Motorzellen unter DNg100-Anregung. E1/E2-Entfernung beseitigt ihn in dieser Modellbedingung. Keine biologische Notwendigkeit, Muskelkraft, Schrittfrequenz, sechsbeinige Koordination oder autonome Motivation bewiesen.'}],
        'metricDefinitions': [{'label': 'Aktive Motoren', 'definition': 'Nach Einschwingphase aktive Zellen aus der konservativen Maske von 129 original als Motoren annotierten Modulzellen.', 'componentIds': ['cpg-controls-table']},
                              {'label': 'Rhythmik-Score', 'definition': 'Originale Autokorrelationsauswertung; Mittel über aktive konservative Motorzellen, bei keiner Aktivität auf 0 gesetzt. Keine Prozentangabe für biologische Funktion.', 'componentIds': ['cpg-controls-table']},
                              {'label': 'Medianfrequenz', 'definition': 'Autokorrelationsfrequenz ausschließlich der konservativen Motoren mit Rhythmik-Score >0,5; keine rhythmische Zelle ergibt einen fehlenden Wert.', 'componentIds': ['cpg-controls-table']}]
    }}
