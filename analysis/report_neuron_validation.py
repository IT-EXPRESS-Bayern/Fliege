"""Add reviewed neuron naming and intervention evidence to the existing report."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def extend_snapshot(snapshot):
    def load(path):
        return json.loads((ROOT / path).read_text(encoding="utf-8"))
    catalog = load("analysis/neuron_catalog/audit.json")
    assays = load("analysis/neuron_assays/summary.json")
    checks = load("analysis/neuron_assays/audit.json")
    sides = load("analysis/neuron_pathways/side_convention_audit.json")
    assert catalog["exact_root_join_complete"] and catalog["duplicate_root_ids"] == 0
    assert checks["all_passed"] and assays["validation"]["allTrialsComplete"]
    findings = {x["id"]: x for x in assays["findings"]}
    counts = [
        {"measure": "Offizielle v783-IDs im Katalog", "count": catalog["root_count"], "scope": "Exakte IDs; keine Duplikate"},
        {"measure": "Originales Feld cell_type belegt", "count": catalog["official_cell_type_present"], "scope": "Gepinnte Annotation v2.1.0"},
        {"measure": "Veröffentlichter Typ oder Zellname verfügbar", "count": catalog["display_name_present"], "scope": "Mehrere Quellen; Name belegt keine vollständige Funktion"},
        {"measure": "Ohne benannten Typ oder Alias", "count": catalog["unbenannt_roots"], "scope": "Bleiben ausdrücklich unbenannt"},
        {"measure": "Mit kuratierter Funktionsannotation", "count": catalog["harmonized_function_annotated_roots"], "scope": "BANC-Projekt: harmonisierte FAFB-Metadaten, gleiche v783-IDs"},
        {"measure": "Neuronen mit aufgezeichnetem Modellantwortprofil", "count": checks["reference_responsive_unique_neurons"], "scope": "Sechs Referenzbedingungen; keine neue biologische Benennung"},
    ]
    result_rows = []
    for name, label in [("sugar", "Zucker"), ("water", "Wasser"), ("bitter", "Bitter")]:
        values = findings["taste_order"]["evidence"][name]
        result_rows.append({"stimulus": label, "readout": "MN9 rechts / links", "first_hz": values["MN9_R_hz"], "second_hz": values["MN9_L_hz"], "interpretation": "Modellrate; qualitativ unterschiedlicher Geschmackseingang"})
    for name, label in [("jo_ce", "Antennengruppe JO-C/E"), ("jo_f", "Antennengruppe JO-F")]:
        values = findings["jo_selectivity"]["evidence"][name]
        result_rows.append({"stimulus": label, "readout": "aDN1 / aDN2", "first_hz": values["aDN1_hz"], "second_hz": values["aDN2_hz"], "interpretation": "Literaturmuster verfehlt: JO-F sollte die schwächere absteigende Antwort geben"})
    lesion_rows = []
    for key, conditions in findings["abn1_dependency"]["evidence"].items():
        for condition, values in conditions.items():
            lesion_rows.append({"input": key, "condition": {"reference": "Referenz 150 Hz", "upstream_ablated": "aBN1 stillgelegt", "upstream_sham": "Kontrollzelle stillgelegt"}[condition], "adn1_hz": values["aDN1_hz"], "adn2_hz": values["aDN2_hz"]})
    snapshot["report"]["neuronValidation"] = {
        "roots": catalog["root_count"], "named": catalog["display_name_present"], "unnamed": catalog["unbenannt_roots"], "functionAnnotated": catalog["harmonized_function_annotated_roots"],
        "trials": checks["trials"], "responsive": checks["reference_responsive_unique_neurons"], "technicalChecks": checks["check_count"], "sideOpposite": sides["stuerner_comparison"]["source_opposite_both_current"],
        "literatureSelectivityStatus": findings["jo_selectivity"]["status"],
    }
    snapshot["queries"]["neuron_catalog_coverage"] = {"rows": counts, "source": {
        "label": "Exakter Neuronenkatalog mit getrennten Original- und Zusatzannotationen",
        "executedAt": catalog["built_utc"],
        "tables": [{"name": "Gepinnte FlyWire-Annotation", "href": "https://github.com/flyconnectome/flywire_annotations/releases/tag/v2.1.0"}, {"name": "BANC-Projekt und harmonisierte FAFB-Metadaten", "href": "https://doi.org/10.7910/DVN/7WTH1N"}],
        "evidenceFlow": [{"title": "ID-Join", "detail": "analysis/neuron_catalog/audit.json: Alle offiziellen Root-IDs exakt und eindeutig; Originalfelder bleiben unverändert. Mehrere Quellen und ihre Rollen werden getrennt gespeichert."}, {"title": "Benennung und Funktion", "detail": "Ein Veröffentlichungsname, eine Funktionsannotation und eine simulierte Antwort sind verschiedene Größen. Keine Funktionsnamen werden aus beobachteter Modellbewegung erzeugt."}, {"title": "Modellprofile", "detail": "analysis/neuron_assays/model_response_profiles.csv: tatsächlich reagierende Neuronen unter sechs Referenzreizen, keine unabhängige physiologische Klassifikation."}],
        "metricDefinitions": [{"label": "Neuronen", "definition": "Einzigartige offizielle FAFB-v783-Root-IDs je benannter Teilmenge; Teilmengen sind nicht disjunkt und werden nicht addiert.", "componentIds": ["neuron-catalog-coverage-table"]}],
    }}
    for query, rows, component in [("neuron_function_trials", result_rows, "neuron-function-trials-table"), ("neuron_ablation_trials", lesion_rows, "neuron-ablation-trials-table")]:
        snapshot["queries"][query] = {"rows": rows, "source": {
            "label": "Ausgeführte Interventionen im explorativen Originalgraph-Modell",
            "executedAt": assays["generatedAt"],
            "tables": [{"name": "Shiu et al., unabhängige publizierte Vergleichsmuster", "href": "https://doi.org/10.1038/s41586-024-07763-9"}, {"name": "Tastekin et al., aktuelle MN9-Identitäten", "href": "https://doi.org/10.1016/j.cell.2026.08.016"}],
            "evidenceFlow": [{"title": "Reproduzierbarer Lauf", "detail": "analysis/neuron_assays/protocol.json, run.mjs, summary.json und audit.json. Vollständiger Originalgraph, eingefrorene 1-ms-Dynamik, 600-ms-Trials, Reizfenster 100–500 ms; keine Parameteranpassung an die Ausgaben."}, {"title": "Messgröße", "detail": "Die Tabelle enthält neu berechnete Modellraten, nicht Zahlen aus den Fachartikeln. Spikes im 400-ms-Reizfenster geteilt durch 0,4 s; 2,5 Hz Zählauflösung. Sensoren werden angeregt, getrennte Ausgangsneuronen ausgelesen."}, {"title": "Kontrollen und Grenze", "detail": "Ruhe, Dosis, Vergleichseingang, gezielte Stilllegung und gradangepasste Kontroll-Stilllegung; ein deterministischer Lauf pro Bedingung. Technische Prüfungen sind keine biologischen Validierungstests. Das JO-C/E-versus-JO-F-Muster scheitert ausdrücklich."}],
            "metricDefinitions": [{"label": "Hz", "definition": "Im angegebenen Simulationsfenster berechnete Spike-Rate pro Ausgangsneuron; keine gemessene Tieraktivität.", "componentIds": [component]}],
        }}
        snapshot["queries"][query]["source"]["evidenceFlow"].extend([
            {"title": "JO-Diagnose", "detail": "analysis/neuron_assays/jo_diagnostic.json: Zwei identische Wiederholungen und zwei Tests mit gleicher Gruppengröße (60/60) und identischen Phasen; unveränderte Dynamik. Beiträge präsynaptischer Zellen sind Modellgrößen."},
            {"title": "3D-Körperwiedergabe", "detail": "app/data/neuron_body_replay_audit.json und app/LAB_METHODS.md: Alle 42 gespeicherten Verläufe durch denselben geometrischen Körper; keine Bewegung ohne zugeordnete aDN-Spikes. Kein biologisch kalibrierter Muskelaktor und keine sensorische Rückkopplung."},
        ])
    snapshot["queries"]["neuron_catalog_coverage"]["source"]["evidenceFlow"].extend([
        {"title": "Benannte Modellprofile", "detail": "analysis/neuron_catalog/model_response_join_audit.json: Alle 7.048 Profile exakt verbunden; 6.845 Zellen mit mindestens einem nicht direkt erzwungenen Spike. 17 weiter unbenannt."},
        {"title": "Seitenkonvention", "detail": "analysis/neuron_pathways/side_convention_audit.json: 1.301 von 1.316 Stürner-DN-Zeilen haben die Gegenrichtung zu beiden neueren FAFB-Tabellen. Das ist mit der offiziellen Codex-FAQ vereinbar; kein Beweis jeder einzelnen Korrekturhistorie."},
    ])
