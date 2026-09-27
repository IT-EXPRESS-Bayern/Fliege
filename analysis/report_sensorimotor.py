"""Reviewed partial closed-loop result; never a whole-fly autonomy score."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def extend_sensorimotor_snapshot(snapshot):
    audit = json.loads((ROOT / "app/data/sensorimotor_audit.json").read_text(encoding="utf-8"))
    assert audit["checksPass"] and audit["trialCount"] == 194
    assert hashlib.sha256((ROOT / audit["source"]["file"]).read_bytes()).hexdigest() == audit["source"]["sha256"]
    assert hashlib.sha256((ROOT / "app/sensorimotor_model.mjs").read_bytes()).hexdigest() == audit["modelSourceSha256"]
    labels = {"claw_plus_hook_plus": "Position + / Bewegung +", "claw_plus_hook_minus": "Position + / Bewegung −",
              "claw_minus_hook_plus": "Position − / Bewegung +", "claw_minus_hook_minus": "Position − / Bewegung −"}
    rows = [{"detector": r["detector"], "polarity": labels[r["polarity"]],
             "peak_reduction_pct": round(100 * r["closedVersusOpenPeakReductionFraction"], 4),
             "rms_reduction_pct": round(100 * r["closedVersusOpenRmsReductionFraction"], 4)}
            for r in audit["pairedChecks"] if r["graphGain"] == 4]
    assert len(rows) == 8
    snapshot["report"]["sensorimotor"] = {"trials": audit["trialCount"], "transferProbes": audit["transferProbeCount"],
        "neuralFeedbackComputed": True, "locomotionSimulated": False, "biologicalValidation": False}
    snapshot["queries"]["sensorimotor_polarity_controls"] = {"rows": rows, "source": {
        "label": "LF-Regelkreis: alle vier Sensorpolaritäts-Hypothesen bei vorab festgelegtem Graphgain 4",
        "executedAt": audit["generatedAt"],
        "tables": [{"name": "Vollständiger lokaler Audit", "href": "http://127.0.0.1:4173/data/sensorimotor_audit.json"},
                   {"name": "Anatomische Originaldaten BANC", "href": "https://doi.org/10.7910/DVN/7WTH1N"},
                   {"name": "Sensor-Motor-Primärstudie", "href": "https://doi.org/10.1038/s41467-025-59302-3"}],
        "evidenceFlow": [{"title": "Quellenbindung", "detail": "Die Modell- und Mapping-SHA256 stimmen mit dem finalen Audit überein. Kanten und komplette Eingangssummen wurden getrennt gegen v2/v3-Originalgraphen geprüft. Für die Dynamik nur proofread-Zellen, claw/hook und ≥5 Kontakte je Kante."},
                         {"title": "Protokoll", "detail": "194 viersekündige Versuche: vier Polaritätskombinationen, v2/v3 getrennt, Gains 0/4/16 und passende Rückkopplungs-, Replay- und Eingriffskontrollen. Hier alle acht Bedingungen bei Gain 4, ohne Auswahl günstiger Resultate. Zusätzlich 24 gesonderte Transferproben."},
                         {"title": "Mechanik und Rückkopplung unterscheiden", "detail": "Identische Störungen und Ausgangsbedingungen. Sensorabschaltung und Kantenablation ergeben dieselbe mechanische Antwort; passives Zurückfedern beweist keine neuronale Stabilisierung. Aufgezeichnete Sensoren reagieren nicht auf eine zusätzliche Störung, der geschlossene Modellkreis schon."},
                         {"title": "Erkenntnisgrenze", "detail": "Der kleine Netzwerkeffekt beweist keine biologisch korrekte Sensorpolarität, Rezeptorwirkung, Muskelkraft, Fortbewegung oder gesamte Hirnautonomie. Ein negativer Wert bleibt als Verschlechterung der Modellantwort erhalten."}],
        "metricDefinitions": [{"label": "Reduktion der Auslenkung", "definition": "100 × (offene − geschlossene Rückmeldung) / offene Rückmeldung, mit identischer mechanischer Störung. Positiv = geringere, negativ = größere Auslenkung im Modell.", "componentIds": ["sensorimotor-polarity-table"]}]
    }}
