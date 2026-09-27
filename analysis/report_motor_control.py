"""Reviewed BANC motor-output inventory for the existing research report."""
import json
import math
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def extend_motor_snapshot(snapshot):
    audit = json.loads((ROOT / "analysis/motor_output_atlas/audit.json").read_text(encoding="utf-8"))
    assert audit["all_unique_exact_ids"] and audit["all_proofread"]
    labels = {"front_leg": "Vorderbeine", "middle_leg": "Mittelbeine", "hind_leg": "Hinterbeine", "abdomen": "Abdomen",
              "wing": "Flügel", "neck": "Hals", "proboscis": "Rüssel", "haltere": "Halteren", "pharynx": "Pharynx",
              "thoracic_abdominal": "Thorax/Abdomen", "antenna, scape": "Antenne / Scapus", "crop": "Kropf",
              "uterus": "Uterus", "eye": "Auge", "salivary_gland": "Speicheldrüse", "unknown": "Unbekannt", "antenna": "Antenne"}
    rows = [{**row, "body_part": labels.get(row["body_part_effector"], row["body_part_effector"])} for row in audit["body_part_groups"]]
    assert sum(row["motor_roots"] for row in rows) == 805
    snapshot["report"]["motorControl"] = {"motorRoots": 805, "legMotorRoots": 391,
                                         "verifiedTransmitter": 30, "transmitterDisagreements": 28}
    snapshot["queries"]["banc_motor_output_atlas"] = {"rows": rows, "source": {
        "label": "BANC v888: exakte motorische Ausgangszellen und wörtliche Körperteilgruppen",
        "executedAt": audit["created_utc"],
        "tables": [{"name": "BANC-Originaldaten", "href": audit["source_url"]},
                   {"name": "BANC-Originalarbeit", "href": "https://doi.org/10.1038/s41586-026-10735-w"}],
        "evidenceFlow": [
            {"title": "Exakte Identitäten", "detail": "analysis/motor_output_atlas/build.py: SHA-256 gegen vorhandene Provenienz geprüft; Filter super_class=motor, 805 eindeutige BANC-v888-IDs. Alle proofread; keine Vermischung mit FAFB."},
            {"title": "Zielgruppen", "detail": "17 vollständige wörtliche body_part_effector-Labels, disjunkt gezählt. Körperteil ist nicht gleich Zellklasse. Anatomische Zielangabe ist keine gemessene Rate-zu-Kraft-Kurve."},
            {"title": "Transmitterkonflikte", "detail": "30 Motorneuronen mit Quellenfeld neurotransmitter_verified (15 Hals, 15 Haltere); davon 28 abweichende Vorhersagen. Keine globale Klassifikatorfehlerquote. Für die 391 Beinmotorneuronen ist dieses verifizierte Feld leer."}
        ],
        "metricDefinitions": [{"label": "Motorneuronen", "definition": "Eindeutige als motor klassifizierte BANC-v888-Root-IDs pro wörtlicher Zielgruppe; keine vollständige Zählung sämtlicher biologischer Effektoren.", "componentIds": ["motor-output-atlas-table"]}]
    }}
    pathways = json.loads((ROOT / "analysis/motor_pathways/audit.json").read_text(encoding="utf-8"))
    joints = json.loads((ROOT / "app/data/motor_joint_audit.json").read_text(encoding="utf-8"))
    assert joints["checksPass"] and joints["trialCount"] == 48
    assert joints["source"]["sha256"] == hashlib.sha256((ROOT / joints["source"]["file"]).read_bytes()).hexdigest()
    reach = [dict(row, soma_side="links" if row["dn_side"] == "left" else "rechts")
             for row in pathways["reachability"]
             if row["dn_type"] in ("DNa02", "DNg13", "DNg100") and row["detector"] == "common" and row["threshold"] == 5]
    assert len(reach) == 6
    snapshot["report"]["motorControl"].update({"descendingNeurons": pathways["dn_count"],
        "directPaths": pathways["direct_paths_union"], "twoEdgePaths": pathways["two_edge_paths_union"],
        "examples": pathways["common5_display_examples"], "jointTrials": joints["trialCount"]})
    snapshot["queries"]["banc_motor_path_reachability"] = {"rows": reach, "source": {
        "label": "Beobachtete vollständige BANC-Wege: identischer Pfad in v2 und v3, jede Kante ≥5 Kontakte",
        "executedAt": joints["generatedAt"],
        "tables": [{"name": "BANC-Daten", "href": "https://doi.org/10.7910/DVN/7WTH1N"},
                   {"name": "DNa02/DNg13-Funktionsarbeit", "href": "https://doi.org/10.1016/j.cell.2024.08.033"},
                   {"name": "DNg100/CPG-Preprint, nicht begutachtet", "href": "https://pmc.ncbi.nlm.nih.gov/articles/PMC13142387/"}],
        "evidenceFlow": [{"title": "Identitäten und vollständige Pfade", "detail": "analysis/motor_pathways/build.py und validate.py: 92 DNs aus 36 Literaturtypen; 391 Motorziele. v2/v3 getrennt, keine über die Detektoren gemischten Wege; 594 unabhängige Prüfungen bestanden."},
                         {"title": "Tabellenauswahl", "detail": "audit.json reachability: DNa02, DNg13, DNg100; detector=common, threshold=5. Soma-Seite beschreibt die DN-Zelle; Ziele können auf der Gegenseite liegen. Endpunkte innerhalb maximal zweier Kanten werden eindeutig gezählt."},
                         {"title": "Bedeutung", "detail": "Strukturelle Erreichbarkeit. Kein Nachweis der Nettoaktivierung oder Verhaltensspezifität. Die beiden Detektoren bearbeiten dasselbe Tier und sind keine unabhängigen biologischen Replikate. FAFB bleibt unverändert; Homologien können widersprüchlich sein."}],
        "metricDefinitions": [{"label": "Erreichbare Beinmotoren", "definition": "Eindeutige Motor-IDs mit mindestens einem identischen vollständigen Weg von höchstens zwei Kanten in beiden Detektoren; jede Kante jeweils mindestens fünf Kontakte.", "componentIds": ["motor-path-reachability-table"]}]
    }}
    leg_labels = {"LF": "Links vorn", "RF": "Rechts vorn", "LM": "Links Mitte", "RM": "Rechts Mitte", "LH": "Links hinten", "RH": "Rechts hinten"}
    joint_rows = []
    for leg, label in leg_labels.items():
        trials = {row["test"]: row for row in joints["results"] if row["leg"] == leg}
        assert len(trials) == 8 and all(all(row["checks"].values()) for row in trials.values())
        passive = math.degrees(trials["passive_disturbance"]["peakDeviationRadians"])
        active = math.degrees(trials["coactivation_disturbance"]["peakDeviationRadians"])
        joint_rows.append({"leg": label, "flexor_ids": len(joints["pools"][leg]["flexor"]),
            "extensor_ids": len(joints["pools"][leg]["extensor"]), "controls": len(trials),
            "passive_degrees": round(passive, 2), "coactivation_degrees": round(active, 2), "status": "Bestanden"})
    snapshot["queries"]["direct_motor_joint_controls"] = {"rows": joint_rows, "source": {
        "label": "Direkte Motoraktivierung im unkalibrierten Gelenkmodell: 6 Beine × 8 Kontrollen",
        "executedAt": joints["generatedAt"],
        "tables": [{"name": "Reproduzierbarer lokaler Audit", "href": "http://127.0.0.1:4173/data/motor_joint_audit.json"},
                   {"name": "Modellgleichungen und Grenzen", "href": "http://127.0.0.1:4173/MOTOR_METHODS.md"}],
        "evidenceFlow": [{"title": "Quellenbindung", "detail": "motor_joint_audit.json: 113 anatomisch zugeordnete IDs; Quellenhash stimmt mit dem finalen Motorpfadexport überein. 48 Versuche, 72.000 Integrationsschritte, alle Kontrollen bestanden."},
                         {"title": "Gleiche Störung", "detail": "Maximale Winkelabweichung bei identischem Störmoment ohne Aktivierung beziehungsweise bei gleichzeitiger Gegenspieleraktivierung. Winkel in Grad, Kräfte und mechanische Parameter in unkalibrierten Modelleinheiten."},
                         {"title": "Grenze der Tests", "detail": "Die Kontrollen prüfen die implementierte Mechanik und exakte ID-Zuordnung. Keine neuronale Ausbreitung, kein Lernziel und keine biologische Bestätigung. Null- und Ausschaltungskontrollen, Sham, entgegengesetzte Aktion, Winkelgrenzen und feste Segmentlängen werden ebenfalls geprüft."}],
        "metricDefinitions": [{"label": "Winkelabweichung", "definition": "Größter absoluter Abstand vom Ausgangswinkel während des dreisekündigen Einzelgelenkversuchs; direkter Motorantrieb 0,65, Körper fixiert.", "componentIds": ["motor-joint-controls-table"]}]
    }}
