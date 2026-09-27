"""Build a reviewed, bounded source snapshot for the local research report."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
audit = json.loads((ROOT / "analysis" / "research_data_audit.json").read_text(encoding="utf-8"))
shiu_audit = json.loads((ROOT / "data" / "research_sources" / "shiu" / "derived" / "shiu_supplement_index.json").read_text(encoding="utf-8"))
original_graph = json.loads((ROOT / "brain" / "graph-original-v783" / "manifest.json").read_text(encoding="utf-8"))
edge_audit = json.loads((ROOT / "analysis" / "model_original_edge_comparison.json").read_text(encoding="utf-8"))
vision_audit = json.loads((ROOT / "data" / "research_sources" / "other" / "visual_system" / "provenance.json").read_text(encoding="utf-8"))
odor_audit = json.loads((ROOT / "data" / "research_sources" / "other" / "olfaction" / "crosswalk_audit.json").read_text(encoding="utf-8"))
peptide_audit = json.loads((ROOT / "data" / "research_sources" / "other" / "neuropeptides" / "crosswalk_audit.json").read_text(encoding="utf-8"))
coverage_audit = json.loads((ROOT / "analysis" / "synapse_coverage_audit.json").read_text(encoding="utf-8"))
missing_link_audit = json.loads((ROOT / "analysis" / "missing_neuron_type_link_audit.json").read_text(encoding="utf-8"))
banc_crosswalk_path = ROOT / "data/research_sources/other/banc_2026/crosswalk_audit.json"
banc_crosswalk = json.loads(banc_crosswalk_path.read_text(encoding="utf-8-sig")) if banc_crosswalk_path.is_file() else None
princeton_audit_path = ROOT / "analysis/reconstruction_candidates_v783/princeton_audit.json"
princeton_audit = json.loads(princeton_audit_path.read_text(encoding="utf-8")) if princeton_audit_path.is_file() else None
princeton_strata_path = ROOT / "analysis/reconstruction_candidates_v783/princeton_strata.json"
princeton_strata = json.loads(princeton_strata_path.read_text(encoding="utf-8")) if princeton_strata_path.is_file() else None
princeton_points_path = ROOT / "analysis/reconstruction_candidates_v783/princeton_point_audit.json"
princeton_points = json.loads(princeton_points_path.read_text(encoding="utf-8")) if princeton_points_path.is_file() else None
banc_patterns_path = ROOT / "data/research_sources/other/banc_2026/partner_pattern_audit.json"
banc_patterns = json.loads(banc_patterns_path.read_text(encoding="utf-8")) if banc_patterns_path.is_file() else None
banc_cross_source_path = ROOT / "data/research_sources/other/banc_2026/cross_source_audit.json"
banc_cross_source = json.loads(banc_cross_source_path.read_text(encoding="utf-8")) if banc_cross_source_path.is_file() else None
malecns_types_path = ROOT / "analysis/malecns_type_partner_hypotheses_audit.json"
malecns_types = json.loads(malecns_types_path.read_text(encoding="utf-8")) if malecns_types_path.is_file() else None
integrated_evidence = json.loads((ROOT / "analysis/reconstruction_candidates_v783/integrated_evidence_audit.json").read_text(encoding="utf-8"))
princeton_exclusions = json.loads((ROOT / "analysis/reconstruction_candidates_v783/princeton_point_exclusion_audit.json").read_text(encoding="utf-8"))
morphology_616 = json.loads((ROOT / "analysis/morphology_616/audit.json").read_text(encoding="utf-8"))
whole_brain = json.loads((ROOT / "analysis/whole_brain_detector_comparison/audit.json").read_text(encoding="utf-8"))
whole_brain_breakdown = json.loads((ROOT / "analysis/whole_brain_detector_comparison/breakdown_audit.json").read_text(encoding="utf-8"))
motor_interface = json.loads((ROOT / "analysis/body_neural_interface/audit.json").read_text(encoding="utf-8"))
pipeline_state = json.loads((ROOT / "logs/pipeline_state.json").read_text(encoding="utf-8"))
full_original_audit = json.loads((ROOT / "analysis/report.json").read_text(encoding="utf-8"))
integration_pack = json.loads((ROOT / "analysis" / "model_integration_pack.json").read_text(encoding="utf-8"))
assert edge_audit["same_exact_directed_pair_set"] and edge_audit["synapse_count_mismatches"] == 0
assert len(integration_pack["inputs"]) >= 37
assert len(integration_pack["joins"]) >= 14
assert sum(integrated_evidence["counts"]["review_bands"].values()) == 616
assert integrated_evidence["counts"]["candidate_pair_region_rows"] == 3233
assert princeton_exclusions["checks"]["point_rows_equal_autapses_plus_R7_nonself_plus_connection_rows"]
assert princeton_exclusions["checks"]["retained_point_groups_equal_unfiltered_connection_groups_exactly"]
assert morphology_616["md5_rechecked_this_run"] and morphology_616["ids_with_nodes"] == 616
assert morphology_616["target_rows_found"] == 151369
assert morphology_616["princeton_only_ids_with_nodes"] == 195
assert pipeline_state["stage"] == "complete"
assert not full_original_audit["incomplete"] and not full_original_audit["morphology"]["incomplete"]
assert full_original_audit["morphology"]["numeric_content_full_scan"]
assert all(row["md5_matches_published"] and row["complete_scan"] for row in full_original_audit["files"].values())
assert all(row["md5_matches_published"] for row in full_original_audit["morphology"]["files"].values())
assert all(whole_brain["checks"].values())
assert whole_brain["source_counts"]["original_directed_pairs"] == 15091983
assert whole_brain["source_counts"]["princeton_directed_pairs"] == 19773733
assert whole_brain["priority"]["princeton_only_pairs_between_two_roots_already_connected_in_original_graph"] == 6323027
assert whole_brain["priority"]["princeton_only_pairs_touching_an_originally_isolated_root"] == 3171
assert motor_interface["namespace"] == "BANC_v888"
assert motor_interface["leg_motor_roots"] == 391 and sum(motor_interface["leg_counts"].values()) == 391
assert motor_interface["incoming_pairs_both_versions"] == 101637
assert motor_interface["calibrated_actuator_channels"] == 0
downloaded = {
    entry["local_path"]: entry
    for entry in json.loads((ROOT / "data" / "research_sources" / "provenance.json").read_text(encoding="utf-8"))["files"]
}


def local_status(path: str) -> str:
    return "Geprüft" if path in downloaded and (ROOT / path).is_file() else "Ausstehend"


def official_download(record: int, filename: str, purpose: str) -> dict:
    folder = "flywire_fafb_v783" if record == 10676866 else "flywire_morphology_v783"
    base = ROOT / "data" / folder
    metadata = json.loads((base / "zenodo_record.json").read_text(encoding="utf-8"))
    entry = next(item for item in metadata["files"] if item["key"] == filename)
    total = entry["size"]
    final_path = base / filename
    progress_path = base / (filename + ".progress.json")
    if final_path.is_file() and final_path.stat().st_size == total:
        downloaded_bytes, state = total, "Prüfsumme geprüft"
    elif progress_path.is_file():
        progress = json.loads(progress_path.read_text(encoding="utf-8"))
        assert progress["size"] == total
        chunk_size = progress["chunk_size"]
        downloaded_bytes = sum(min(chunk_size, total - index * chunk_size) for index in progress["completed"])
        state = "Lädt" if downloaded_bytes < total else "Prüfsumme wird geprüft"
    else:
        downloaded_bytes, state = 0, "Ausstehend"
    return {
        "name": filename, "purpose": purpose, "state": state,
        "downloadedGB": round(downloaded_bytes / 1_000_000_000, 3),
        "totalGB": round(total / 1_000_000_000, 3),
        "sharePercent": round(downloaded_bytes / total * 100, 2),
        "url": f"https://zenodo.org/records/{record}",
    }


downloads = [
    official_download(10676866, "flywire_synapses_783.feather", "Einzelkontakte, Partnersegmente und Orte"),
    official_download(10877326, "sk_lod1_783_healed_ds2.parquet", "3D-Neuronenäste"),
    official_download(10877326, "nblast_flywire_all_right_aba_comp.feather", "Morphologischer Zellvergleich"),
    official_download(10877326, "nblast_flywire_hemibrain_min_comp.feather", "Vergleich mit Hemibrain-Zellen"),
    official_download(10877326, "nblast_flywire_mirrored_hemibrain_min_comp.feather", "Gespiegelter Hemibrain-Vergleich"),
]
download_by_name = {row["name"]: row for row in downloads}

point_audit_path = ROOT / "analysis/synapse_point_audit.json"
point_audit = json.loads(point_audit_path.read_text(encoding="utf-8")) if point_audit_path.is_file() else None
segment_audit_path = ROOT / "analysis/observed_segment_links_audit.json"
segment_audit = json.loads(segment_audit_path.read_text(encoding="utf-8")) if segment_audit_path.is_file() else None
exception_audit_path = ROOT / "analysis/observed_raw_proofread_edge_exceptions_audit.json"
exception_audit = json.loads(exception_audit_path.read_text(encoding="utf-8")) if exception_audit_path.is_file() else None
reconciliation_audit_path = ROOT / "analysis/raw_published_edge_reconciliation_audit.json"
reconciliation_audit = json.loads(reconciliation_audit_path.read_text(encoding="utf-8")) if reconciliation_audit_path.is_file() else None
raw_file_verified = download_by_name["flywire_synapses_783.feather"]["state"] == "Prüfsumme geprüft"
point_detail = [{
    "stage": "Vollscan aller offiziellen Einzelpunkte",
    "state": "Analysiert" if point_audit else "Prüfsumme geprüft; Vollscan noch offen" if raw_file_verified else "Wartet auf Prüfsummen-Download",
    "quantity": point_audit["counts"]["rows"] if point_audit else None,
    "output": "analysis/synapse_point_audit.json" if point_audit else "analysis/audit_synapse_points.py",
}, {
    "stage": "Beobachtete Punkte der 616 kantenlosen IDs",
    "state": "Analysiert" if point_audit else "Wartet auf Vollscan",
    "quantity": point_audit["counts"]["selected_points"] if point_audit else None,
    "output": point_audit["point_export"] if point_audit else "analysis/audit_synapse_points.py",
}, {
    "stage": "Beobachtete Kontakte der 616 kantenlosen IDs",
    "state": "Analysiert" if segment_audit else "Wartet auf Einzelpunkt-Analyse",
    "quantity": segment_audit["counts"]["observed_link_rows_by_pair_direction_neuropil"] if segment_audit else None,
    "points": segment_audit["counts"]["observed_segment_contact_points"] if segment_audit else None,
    "segments": segment_audit["counts"]["opposing_unproofread_segment_ids"] if segment_audit else None,
    "output": segment_audit["output_csv"] if segment_audit else "analysis/build_observed_segment_links.py",
}]

raw_aggregate_exception = []
raw_exception_pairs = []
reconciliation_rows = []
if point_audit:
    disconnected_ids_path = ROOT / "data/research_sources/derived/model_missing_fafb_ids.csv"
    with disconnected_ids_path.open(encoding="utf-8", newline="") as source:
        disconnected_ids = {row["root_id"] for row in csv.DictReader(source)}
    with (ROOT / point_audit["point_export"]).open(encoding="utf-8", newline="") as source:
        exception_points = [row for row in csv.DictReader(source)
                            if row["pre_root_proofread"] == "True" and row["post_root_proofread"] == "True"]
    assert len(exception_points) == point_audit["raw_both_proofread_minus_published_pair_table"]
    assert len({row["synapse_id"] for row in exception_points}) == len(exception_points)
    missing_ids_in_exception = {
        root_id for row in exception_points for root_id in (row["pre_root_id"], row["post_root_id"])
        if root_id in disconnected_ids
    }
    assert missing_ids_in_exception == {"720575940623940963"}
    assert {row["neuropil"] for row in exception_points} == {"ME_R"}
    directed_pairs = {(row["pre_root_id"], row["post_root_id"]) for row in exception_points}
    assert len(directed_pairs) == 21
    if exception_audit:
        assert exception_audit["counts"]["raw_proofread_exception_points"] == len(exception_points)
        assert exception_audit["counts"]["raw_proofread_exception_directed_pairs"] == len(directed_pairs)
        assert exception_audit["checks"]["all_raw_exception_pair_region_keys_absent_from_published_table"]
        assert exception_audit["checks"]["published_pair_region_rows_scanned"] == 16_847_997
    raw_aggregate_exception = [{
        "rootId": "720575940623940963", "cellType": "R7", "neuropil": "ME_R",
        "rawPoints": len(exception_points), "directedPairs": len(directed_pairs),
        "aggregatedRows": 0,
        "meaning": "Beobachtete Rohkontakte mit zwei geprüften Partnern; in proofread_connections nicht enthalten",
    }]
    if exception_audit:
        with (ROOT / exception_audit["output_csv"]).open(encoding="utf-8", newline="") as source:
            exception_pair_source = list(csv.DictReader(source))
        relevant_ids = {row[key] for row in exception_pair_source for key in ("pre_root_id", "post_root_id")}
        with (ROOT / "data/flywire_annotations_v2.1.0/Supplemental_file1_neuron_annotations.tsv").open(
            encoding="utf-8", newline=""
        ) as source:
            annotations = {row["root_id"]: row for row in csv.DictReader(source, delimiter="\t")
                           if row["root_id"] in relevant_ids}
        assert len(exception_pair_source) == 21
        assert len(annotations) == len(relevant_ids)
        assert {annotations[root_id]["side"] for root_id in relevant_ids} == {"right"}
        assert sum(int(row["synapse_count"]) for row in exception_pair_source) == 48
        raw_exception_pairs = [{
            "preRootId": row["pre_root_id"],
            "preType": annotations[row["pre_root_id"]]["cell_type"] or annotations[row["pre_root_id"]]["cell_class"] or "nicht typisiert",
            "postRootId": row["post_root_id"],
            "postType": annotations[row["post_root_id"]]["cell_type"] or annotations[row["post_root_id"]]["cell_class"] or "nicht typisiert",
            "region": row["neuropil"], "synapseCount": int(row["synapse_count"]),
            "status": "Im Rohdatensatz; nicht in der publizierten Paar/Region-Tabelle",
        } for row in exception_pair_source]
        raw_exception_pairs.sort(key=lambda row: (-row["synapseCount"], row["preRootId"], row["postRootId"]))

if reconciliation_audit:
    recon = reconciliation_audit["reconciliation"]
    alignment = reconciliation_audit["region_alignment"]
    assert recon["exception_types"] == {"raw_only": 3214, "published_only": 3193, "different_count": 0}
    assert recon["raw_points_in_exception_rows"] == 4233
    assert recon["published_synapses_in_exception_rows"] == 4185
    assert alignment["all_remaining_exceptions_exactly_prior_616_R7_keys"]
    assert alignment["exception_pair_region_keys_after_alignment"] == 21
    assert alignment["raw_points_in_remaining_exceptions"] == 48
    with (ROOT / reconciliation_audit["exception_csv"]).open(encoding="utf-8", newline="") as source:
        exception_rows = list(csv.DictReader(source))
    by_directed_pair = {}
    for row in exception_rows:
        by_directed_pair.setdefault((row["pre_root_id"], row["post_root_id"]), {})[row["neuropil"]] = row
    mapped_pairs = [group for group in by_directed_pair.values() if set(group) == {"None", "UNASGD"}]
    unmatched_pairs = [group for group in by_directed_pair.values() if set(group) != {"None", "UNASGD"}]
    assert len(mapped_pairs) == 3193 and len(unmatched_pairs) == 21
    assert all(int(group["None"]["raw_synapse_points"]) == int(group["UNASGD"]["published_syn_count"])
               for group in mapped_pairs)
    assert all(set(group) == {"ME_R"} and group["ME_R"]["previously_identified_among_616"] == "True"
               for group in unmatched_pairs)
    mapped_points = sum(int(group["None"]["raw_synapse_points"]) for group in mapped_pairs)
    unmatched_points = sum(int(group["ME_R"]["raw_synapse_points"]) for group in unmatched_pairs)
    assert mapped_points == 4185 and unmatched_points == 48
    exact_matching_keys = recon["raw_distinct_pair_region_keys"] - recon["exception_types"]["raw_only"]
    exact_matching_points = reconciliation_audit["raw_counts"]["both_proofread_points"] - recon["raw_points_in_exception_rows"]
    assert exact_matching_keys == 16_844_804 and exact_matching_points == 54_488_737
    reconciliation_rows = [
        {"class": "Roh- und Aggregat-Key exakt gleich", "pairRegionKeys": exact_matching_keys,
         "synapses": exact_matching_points, "meaning": "Gleiche Richtung, Partner, Hirnregion und Synapsenzahl"},
        {"class": "Regionslabel None → UNASGD", "pairRegionKeys": len(mapped_pairs),
         "synapses": mapped_points, "meaning": "Gleiche gerichtete Paare und Zählwerte; nur Regionsbezeichner anders"},
        {"class": "Nur in Rohpunkten: R7 in ME_R", "pairRegionKeys": len(unmatched_pairs),
         "synapses": unmatched_points, "meaning": "Beobachtete Punkte; im Aggregat fehlen diese Paar/Region-Schlüssel"},
    ]

integration_state = {
    "ready": "Lokal geprüft",
    "ready_as_reference": "Lokale Referenz",
    "reference_index_only": "Externer Datenindex",
    "reference_only": "Architekturvorbild",
}
integration_inputs = [
    {"id": row["id"], "path": row.get("path", ""), "role": row.get("role", ""),
     "state": integration_state.get(row["state"], row["state"]),
     "url": row.get("source_url", "")}
    for row in integration_pack["inputs"]
]


sources = [
    {"id": "flywire", "name": "FlyWire FAFB v783", "kind": "Originalmessung", "version": "783.0",
     "artifact": "proofread_connections_783.feather; proofread_root_ids_783.npy",
     "use": "Offizielle aggregierte Proofread-Verbindungen und exakte Neuron-IDs", "state": "Geprüft",
     "url": "https://zenodo.org/records/10676866"},
    {"id": "synapses", "name": "FlyWire Einzel-Synapsen", "kind": "Originalmessung", "version": "783.0",
     "artifact": "flywire_synapses_783.feather", "use": "Kontaktorte und Transmitterprognosen prüfen",
     "state": download_by_name["flywire_synapses_783.feather"]["state"],
     "url": "https://zenodo.org/records/10676866"},
    {"id": "princeton", "name": "Princeton-Synapsen", "kind": "Neuer Detektor am selben FAFB-v783-Tier", "version": "783.2 / 2025",
     "artifact": "connections_princeton_no_threshold.csv.gz; Einzelpunkt-Tabelle",
     "use": "Mit v783-Original vergleichen und zusätzliche Kontakte der 616 IDs prüfen",
     "state": "Verbindungstabelle und Einzelpunkte MD5-geprüft" if (ROOT / "data/codex_fafb_v783/fafb_v783_princeton_synapse_table.csv.gz").is_file() else "Ungefilterte Verbindungstabelle MD5-geprüft; Einzelpunkte laden" if (ROOT / "data/codex_fafb_v783/connections_princeton_no_threshold.csv.gz").is_file() else "Download läuft",
     "url": "https://codex.flywire.ai/api/download?dataset=fafb"},
    {"id": "morphology", "name": "FlyWire 3D-Skelette", "kind": "Originalrekonstruktion", "version": "783",
     "artifact": "sk_lod1_783_healed_ds2.parquet", "use": "Neuronenäste räumlich anzeigen",
     "state": download_by_name["sk_lod1_783_healed_ds2.parquet"]["state"],
     "url": "https://zenodo.org/records/10877326"},
    {"id": "skeleton-viewer", "name": "Unsere 3D-Skelettansicht", "kind": "Lokaler Forschungsprototyp", "version": "FAFB v783",
     "artifact": "app/skeleton.html; analysis/morphology_616/audit.json",
     "use": "Skelettabdeckung aller 616 belegen; R7 und fünf Partner im Browser zeigen",
     "state": "MD5-geprüft; Skelettknoten für 616/616 IDs nachgewiesen; sechs Beispielbäume im Viewer",
     "url": "http://127.0.0.1:4173/skeleton.html"},
    {"id": "nblast", "name": "FlyWire Morphologievergleiche", "kind": "Originaldaten/abgeleitete Ähnlichkeit", "version": "783",
     "artifact": "Drei NBLAST-Feather-Tabellen", "use": "Zellformen vergleichen und unklare Typen eingrenzen",
     "state": "Alle geprüft" if all(row["state"] == "Prüfsumme geprüft" for row in downloads[2:]) else "Download ausstehend/läuft",
     "url": "https://zenodo.org/records/10877326"},
    {"id": "annotations", "name": "FlyWire Zellannotation", "kind": "Kuratierte Annotation", "version": "2.1.0",
     "artifact": "Supplemental_file1_neuron_annotations.tsv", "use": "Zelltypen, Seiten und Positionen an IDs binden",
     "state": "Geprüft", "url": "https://github.com/flyconnectome/flywire_annotations/releases/tag/v2.1.0"},
    {"id": "shiu-inputs", "name": "Shiu v783 Modelleingaben", "kind": "Abgeleitetes Modell", "version": "Git SHA 91bdd1e",
     "artifact": "Completeness_783.csv; Connectivity_783.parquet", "use": "Publizierte LIF-Struktur reproduzieren",
     "state": local_status("data/research_sources/shiu/Connectivity_783.parquet"),
     "url": "https://github.com/philshiu/Drosophila_brain_model"},
    {"id": "shiu-tables", "name": "Shiu Ergänzungstabellen 1–12", "kind": "Experimentelle Evidenz", "version": "Nature 2024",
     "artifact": "supplementary_tables_1-12.xlsx", "use": "Geschmack, Fressen, Putzen und Parametertests als Validierung",
     "state": local_status("data/research_sources/shiu/supplementary_tables_1-12.xlsx"),
     "url": "https://www.nature.com/articles/s41586-024-07763-9"},
    {"id": "local-graph", "name": "Unser vollständiger v783-Graf", "kind": "Reproduzierbarer Export", "version": "FAFB 783",
     "artifact": "brain/graph-original-v783/manifest.json", "use": "Alle Kanten der offiziellen Aggregattabelle im Browser laden und simulieren",
     "state": "Gebaut und Funktionstest bestanden", "url": "https://zenodo.org/records/10676866"},
    {"id": "autonomous-prototype", "name": "Unsere autonome 3D-Arena", "kind": "Lokaler Forschungsprototyp", "version": "2026-09-26",
     "artifact": "app/autonomy.mjs; app/tests/autonomy.test.mjs", "use": "Spontanes Verhalten und Körperfeedback im Browser prüfen",
     "state": "Läuft; App-Tests einschließlich Kinematik bestanden; keine FlyWire-Motorsteuerung", "url": "http://127.0.0.1:4173/"},
    {"id": "vision", "name": "Visuelles Zellinventar", "kind": "Fachartikel + Datentabellen", "version": "FAFB v783",
     "artifact": "neuron_table.csv; Typverbindungen; compact-ID-Karte", "use": "Sehlappen-Typen und Seiten an Root-IDs binden",
     "state": "Geprüft; 139.255/139.255 IDs", "url": "https://doi.org/10.1038/s41586-024-07981-1"},
    {"id": "olfaction", "name": "DoOR + Benton Geruchskarte", "kind": "Experimentelle Antwortmatrix + Zellkarte", "version": "DoOR 2.0.1; Benton 2025",
     "artifact": "Geruchsmatrix; Rezeptor/Glomerulus; Root-ID-Crosswalk",
     "use": "Gerüche über Zelltypen als Sensor-Kandidaten abbilden",
     "state": "2.281 FAFB-Riechsensoren typbasiert geprüft",
     "url": "https://doi.org/10.1038/s44319-025-00476-8"},
    {"id": "peptides", "name": "Kuratierte Neuropeptid-Evidenz", "kind": "Zelltyp-Evidenz", "version": "FlyConnectome 2026 Git-Stand",
     "artifact": "gt_np_data.csv; FAFB-Typkandidaten", "use": "Interne Zustände als prüfbare Modulationshypothesen aufbauen",
     "state": "11.567 v783-IDs mit Typkandidaten", "url": "https://github.com/flyconnectome/drosophila_neuropeptides"},
    {"id": "autonomy", "name": "Gattuso / DNa-Bewegungsmodelle", "kind": "Fachartikel + Modellcode", "version": "PNAS/eLife 2025",
     "artifact": "Dynamik für spontanes Gehen; DNa-Auswertung", "use": "Eigenaktivität ohne gesetzte Verhaltensziele entwerfen",
     "state": "Code und kleine Referenzdaten geprüft", "url": "https://doi.org/10.1073/pnas.2407626122"},
    {"id": "eon-code", "name": "Eon fly-brain", "kind": "Implementierungsreferenz", "version": "Git SHA a3db62f",
     "artifact": "2025_Completeness_783.csv; Benchmark-CSV; Python-Runner",
     "use": "Backends und Spike-/Laufzeitvergleiche prüfen", "state": "Geprüft",
     "url": "https://github.com/eonsystemspbc/fly-brain"},
    {"id": "eon-embodied", "name": "Eon verkörperte Fliege", "kind": "Technischer Bericht", "version": "2026-03-10",
     "artifact": "öffentlicher Methodenbericht", "use": "Kopplungsarchitektur als Beispiel",
     "state": "Mapping-Tabelle nicht veröffentlicht", "url": "https://eon.systems/updates/embodied-brain-emulation"},
    {"id": "neck", "name": "Stürner DN/AN-Tabellen", "kind": "Fachartikel + Supplement", "version": "Nature 2025",
     "artifact": "FAFB-DN-/AN-Tabellen", "use": "Benannte absteigende und aufsteigende Zellen zuordnen",
     "state": "Geprüft; 1 Seed-ID ohne v783-Treffer", "url": "https://www.nature.com/articles/s41586-025-08925-z"},
    {"id": "bmn", "name": "Kopfborsten-Sensorik", "kind": "Fachartikel + Supplement", "version": "eLife 2026",
     "artifact": "BMN-IDs und Edgelists", "use": "Berührung in belegte sensorische IDs übersetzen",
     "state": "Geprüft; alle benannten IDs im Graph", "url": "https://elifesciences.org/articles/108044/figures"},
    {"id": "taste", "name": "Tastekin Geschmacks-Connectom", "kind": "Fachartikel + Supplement", "version": "Cell 2026",
     "artifact": "Table S1 GRN/MN (XLSX)", "use": "Geschmacksrezeptoren und Motorneuronen über FAFB-IDs einordnen",
     "state": "Geprüft; 477/477 FAFB-IDs im Graph", "url": "https://doi.org/10.1016/j.cell.2026.08.016"},
    {"id": "banc", "name": "BANC v888", "kind": "Anderes weibliches Tier", "version": "888",
     "artifact": "geprüfte FAFB-Matches; AN/DN- und Effektorcluster; BANC-Konnektivität", "use": "Zusammenhängende Gehirn–Bauchmark-Pfade und Körperfunktionen im BANC-Tier untersuchen",
     "state": "Offizielle Zusatzdaten und FAFB-Matches lokal geprüft" if (ROOT / "data/research_sources/other/banc_2026/provenance.json").is_file() else "Zwei Referenztabellen geprüft",
     "url": "https://doi.org/10.7910/DVN/7WTH1N"},
    {"id": "malecns", "name": "MaleCNS v1.0", "kind": "Anderes männliches Tier", "version": "v1.0",
     "artifact": "Neuron-Annotationen, Transmitter und traced-only-Neuronenpaare",
     "use": "Zusammenhängendes Gehirn–Bauchmark als zweite Körpersteuerungsreferenz",
     "state": "GCS-MD5-geprüfter traced-only-Graph und Metadaten" if (ROOT / "data/malecns_v1_reference/connectome-weights-male-cns-v1.0-minconf-0.5-traced-only.feather").is_file() else "Download läuft",
     "url": "https://male-cns.janelia.org/download/"},
    {"id": "flygym", "name": "NeuroMechFly v2 / FlyGym", "kind": "Körpermodell", "version": "2024 paper; 2026 API 2.x",
     "artifact": "Code und Modellbeschreibung", "use": "Physik, Sensorik und Motorcontroller als Referenz",
     "state": "Online dokumentiert", "url": "https://github.com/NeLy-EPFL/flygym"},
    {"id": "flybody", "name": "FlyBody Ganzkörpermodell", "kind": "Körperphysik + trainierte Controller", "version": "Nature 2025",
     "artifact": "Körpercode; Gang-/Flugcontroller; Putzposen", "use": "Gang, Flug und Körpergelenke als Vergleichsmodell",
     "state": "Lokale Referenzen geprüft" if (ROOT / "data/research_sources/other/autonomous_behavior/flybody/provenance.json").is_file() else "Quellenprüfung läuft",
     "url": "https://doi.org/10.1038/s41586-025-09029-4"},
    {"id": "webgpu-fly", "name": "webgpu-fly Browserprojekt", "kind": "Drittprojekt / Architekturbeispiel", "version": "Git SHA bb00419",
     "artifact": "FlyWire + MANC + FlyBody + WebGPU/MuJoCo-WASM",
     "use": "Browserarchitektur und offene Integrationsprobleme vergleichen",
     "state": "Gepinnter Code lokal geprüft; Typnamen-Join und Assist-Controller",
     "url": "https://github.com/abgnydn/webgpu-fly/tree/bb00419e874eee9e878542dcc5fce289ede2e1b9"},
]

graphs = [
    {"name": "FlyWire Original", "neurons": audit["official_root_ids"],
     "connectionRows": 16_847_997, "grain": "Neuronenpaar × Region",
     "synapses": 54_492_922, "meaning": "Geprüfte Original-Verbindungstabelle"},
    {"name": "Shiu / Eon v783", "neurons": audit["shiu_model_ids"],
     "connectionRows": audit["connectivity"]["rows"], "grain": "Neuronenpaar",
     "synapses": audit["connectivity"]["synapse_count_sum"],
     "meaning": "Modellgraph; alle Paare und Zählwerte mit Original-Export abgeglichen"},
    {"name": "Unser vollständiger Export", "neurons": original_graph["node_count"],
     "connectionRows": original_graph["edge_count"], "grain": "Neuronenpaar",
     "synapses": original_graph["synapse_count"],
     "meaning": "Aus Original gebaut; exakt gleiche Paare/Zählwerte wie Shiu; keine Stärkefilterung"},
    {"name": "Früherer kompakter Export", "neurons": 139_255,
     "connectionRows": 3_732_460, "grain": "gefiltertes Neuronenpaar",
     "synapses": 50_666_648, "meaning": "Vorgefilterter historischer Export für Vergleiche"},
]

papers = [
    {"year": 2024, "work": "Dorkenwald et al.", "finding": "FAFB-Gehirnverdrahtung", "asset": "Zenodo v783 Graph", "fit": "Originalgraph", "url": "https://doi.org/10.1038/s41586-024-07558-y"},
    {"year": 2024, "work": "Schlegel et al.", "finding": "Zelltypen und Morphologie", "asset": "Annotationen und Skelette", "fit": "Zellidentität und 3D", "url": "https://doi.org/10.1038/s41586-024-07686-5"},
    {"year": 2024, "work": "Shiu et al.", "finding": "Gehirnweites LIF-Modell für sensorische Schaltkreise", "asset": "Code, v783-Input, 12 Tabellen", "fit": "Dynamik und Validierung", "url": "https://doi.org/10.1038/s41586-024-07763-9"},
    {"year": 2025, "work": "Yu et al.", "finding": "Princeton-Detektor verbessert Synapsenerkennung im selben FAFB-Präparat", "asset": "Codex v783.2 Tabellen", "fit": "Fehlende Kontakte und Photorezeptoren prüfen", "url": "https://doi.org/10.1101/2025.07.11.664377"},
    {"year": 2024, "work": "Matsliah et al.", "finding": "Zelltypen und Verdrahtung des Sehsystems", "asset": "v783-ID- und Typ-Tabellen", "fit": "Sehen", "url": "https://doi.org/10.1038/s41586-024-07981-1"},
    {"year": 2024, "work": "Lappalainen et al.", "finding": "Trainiertes Modell dynamischer visueller Antworten", "asset": "flyvis-Code und Modelle", "fit": "Visuelle Funktion, anderes Connectom", "url": "https://doi.org/10.1038/s41586-024-07939-3"},
    {"year": 2024, "work": "Pospisil et al.", "finding": "Anatomie als Prior für effektive Verbindungen", "asset": "conn2eff-Code", "fit": "Gewichte methodisch prüfen", "url": "https://doi.org/10.1038/s41586-024-07982-0"},
    {"year": 2024, "work": "Wang-Chen et al.", "finding": "NeuroMechFly v2 mit Sinnes- und Körperfeedback", "asset": "FlyGym-Code", "fit": "Körperreferenz", "url": "https://doi.org/10.1038/s41592-024-02497-y"},
    {"year": 2016, "work": "Münch & Galizia / DoOR", "finding": "Geruchsantworten vieler Rezeptortypen", "asset": "DoOR-Antwortmatrix", "fit": "Geruch", "url": "https://doi.org/10.1038/srep21841"},
    {"year": 2025, "work": "Benton et al.", "finding": "Antennen- und Palp-Sinneszelltypen", "asset": "Data Set EV1: Rezeptor/Glomerulus", "fit": "Geruchs-ID-Crosswalk", "url": "https://doi.org/10.1038/s44319-025-00476-8"},
    {"year": 2025, "work": "Gattuso et al.", "finding": "Spontanes und geruchsmoduliertes Gehen", "asset": "Fünf-Einheiten-DN-Modellcode", "fit": "Eigenaktivität als Referenz", "url": "https://doi.org/10.1073/pnas.2407626122"},
    {"year": 2025, "work": "Vaxenburg et al.", "finding": "Ganzkörperphysik mit 67 starren Teilen und 102 Freiheitsgraden", "asset": "FlyBody-Code und trainierte Gang-/Flugcontroller", "fit": "Körper, Gang und Flug", "url": "https://doi.org/10.1038/s41586-025-09029-4"},
    {"year": 2025, "work": "Rayshubskiy et al.", "finding": "DNa01/DNa02-Aktivität bei Lenkung", "asset": "Auswertungscode und Daten", "fit": "Lenkung validieren", "url": "https://doi.org/10.7554/eLife.102230"},
    {"year": 2025, "work": "Stürner et al.", "finding": "Vergleich ab- und aufsteigender Zellen", "asset": "FAFB-DN/AN-Supplement", "fit": "Gehirn–VNC-Schnittstelle", "url": "https://doi.org/10.1038/s41586-025-08925-z"},
    {"year": 2026, "work": "Calle-Schuler et al.", "finding": "Kopfborsten und Putzen", "asset": "BMN-IDs und Edgelists", "fit": "Berührungseingang", "url": "https://elifesciences.org/articles/108044"},
    {"year": 2026, "work": "Tastekin et al.", "finding": "Geschmack und Fresskreise", "asset": "Table S1: GRN- und MN-IDs", "fit": "Geschmack und Fressen", "url": "https://doi.org/10.1016/j.cell.2026.08.016"},
    {"year": 2026, "work": "Bates et al.", "finding": "Verteilte Steuerung im Gehirn und Bauchmark", "asset": "BANC v888 Daten", "fit": "VNC-Vergleich", "url": "https://doi.org/10.1038/s41586-026-10735-w"},
    {"year": 2026, "work": "Berg et al.", "finding": "Vollständiges männliches Zentralnervensystem mit Geschlechtsvergleichen", "asset": "MaleCNS v1.0 Daten", "fit": "Gehirn–Bauchmark-Vergleich", "url": "https://doi.org/10.1016/j.cell.2026.08.015"},
]
papers.sort(key=lambda row: (row["year"], row["work"]))

pathways = [
    {"sense_or_output": "Sehen / Sehlappen", "source": "Matsliah 2024", "matched_ids": "139.255/139.255 Tabellen-IDs", "model_use": "Visuelle Zelltypen und Sehlappen-Seiten direkt an FAFB binden", "constraint": "Photorezeptor-Ausgangssynapsen unterdetektiert", "url": "https://doi.org/10.1038/s41586-024-07981-1"},
    {"sense_or_output": "Geruch", "source": "DoOR + Benton 2025", "matched_ids": "2.281 v783-ORN-Kandidaten", "model_use": "Glomerulus/Typ auf publizierte Geruchsantworten abbilden", "constraint": "Antworten tierübergreifend; kein direkter Root-ID-Messwert", "url": "https://doi.org/10.1038/s44319-025-00476-8"},
    {"sense_or_output": "Interne Modulation", "source": "FlyConnectome Neuropeptides", "matched_ids": "11.567 v783-Typkandidaten", "model_use": "Peptid-exprimierende Zelltypen als Hypothesen markieren", "constraint": "Keine gemessene Rezeptorverteilung oder Wirksamkeit je Neuron", "url": "https://github.com/flyconnectome/drosophila_neuropeptides"},
    {"sense_or_output": "Kopfborsten / Berührung", "source": "Calle-Schuler 2026", "matched_ids": "705/705 BMN-IDs", "model_use": "Berührungsreiz auf belegte sensorische Neuronen abbilden", "constraint": "Reizstärke und Zeitverlauf müssen kalibriert werden", "url": "https://elifesciences.org/articles/108044"},
    {"sense_or_output": "Geschmack und Fressen", "source": "Tastekin 2026", "matched_ids": "411 GRN + 66 MN", "model_use": "Rezeptorzellen und Fressmotorik über IDs zuordnen", "constraint": "Table S1 enthält Zellidentität, keine Muskelkräfte", "url": "https://doi.org/10.1016/j.cell.2026.08.016"},
    {"sense_or_output": "Zucker, Wasser, Bitter; Antenne", "source": "Shiu 2024", "matched_ids": f"{len(shiu_audit['candidates']) - shiu_audit['mapping_status_counts']['absent_from_v783_exact_id']}/{len(shiu_audit['candidates'])} ausgewählte IDs", "model_use": "Sensor- und Auslesekandidaten; publizierte v630-Checks", "constraint": "4 IDs fehlen; 2 Seitenannotationen widersprechen Namen", "url": "https://doi.org/10.1038/s41586-024-07763-9"},
    {"sense_or_output": "Gehirn ↔ Bauchmark", "source": "Stürner 2025", "matched_ids": "1.316 DN + 2.345 AN/SA", "model_use": "Schnittstelle für Motorbefehle und Körperfeedback", "constraint": "Benannte Zellklassen ersetzen keine vollständige VNC-Dynamik", "url": "https://doi.org/10.1038/s41586-025-08925-z"},
    {"sense_or_output": "Gehirn ↔ Bauchmark (anderes Tier)", "source": "BANC v888 / MaleCNS v1.0", "matched_ids": "eigene BANC-/MaleCNS-IDs", "model_use": "Durchgehende sensorisch-motorische Pfade, 17 BANC-AN/DN-Module und 15 Effektorcluster als Vergleich untersuchen", "constraint": "Keine Identität mit FAFB-v783-Root-IDs oder gemessene FAFB-Muskelausgänge", "url": "https://doi.org/10.1038/s41586-026-10735-w"},
    {"sense_or_output": "Körper und Physik", "source": "NeuroMechFly v2", "matched_ids": "keine FAFB-ID-Tabelle", "model_use": "Bewegungs- und Sensorikreferenz", "constraint": "Physik und Controller separat integrieren", "url": "https://doi.org/10.1038/s41592-024-02497-y"},
]
assert vision_audit["audit"]["neuron_ids_exactly_match_official_v783_roots"]
assert odor_audit["fafb_olfactory_neurons"] == 2281
assert peptide_audit["unique_fafb_root_ids"] == 11567

total_points = coverage_audit["pre_table"]["all_synapse_counts"]
if point_audit:
    point_counts = point_audit["counts"]
    both = point_counts["both_proofread"]
    pre_only = point_counts["only_pre_proofread"]
    post_only = point_counts["only_post_proofread"]
    neither = point_counts["neither_proofread"]
    assert point_counts["rows"] == total_points
    assert both - coverage_audit["proofread_connection_synapses"] == 48
    assert point_counts["both_proofread_self"] == 0
else:
    both = coverage_audit["proofread_connection_synapses"]
    pre_only = coverage_audit["proofread_pre_neuron_points_outside_aggregated_pair_table"]
    post_only = coverage_audit["proofread_post_neuron_points_outside_aggregated_pair_table"]
    neither = total_points - both - pre_only - post_only
point_groups = [
    {"class": "Beide Partner geprüft", "synapses": both, "sharePercent": round(both / total_points * 100, 2),
     "meaning": "Rohkontakte mit zwei geprüften Partnern; 48 mehr als in der aggregierten Graphentabelle" if point_audit else "Vorläufig aus Summendateien"},
    {"class": "Nur Sender geprüft", "synapses": pre_only, "sharePercent": round(pre_only / total_points * 100, 2),
     "meaning": "Freigegebener Punkt mit ungeprüftem Empfängersegment" if point_audit else "Vorläufig aus Summendateien"},
    {"class": "Nur Empfänger geprüft", "synapses": post_only, "sharePercent": round(post_only / total_points * 100, 2),
     "meaning": "Freigegebener Punkt mit ungeprüftem Sendersegment" if point_audit else "Vorläufig aus Summendateien"},
    {"class": "Kein Partner geprüft", "synapses": neither, "sharePercent": round(neither / total_points * 100, 2),
     "meaning": "Beide Segmente außerhalb des geprüften ID-Satzes" if point_audit else "Vorläufig aus Summendateien"},
]
assert sum(row["synapses"] for row in point_groups) == 130_054_535
missing_status = [
    {"state": "Ohne geprüfte Kante, mit freigegebenen Punkten", "ids": coverage_audit["of_these_with_any_released_point"],
     "nextEvidence": ("Beobachtete Segmentkontakte separat exportiert" if segment_audit else
                      "Einzelpunkte mit Segmentpartnern exportiert; Gruppierung folgt" if point_audit else
                      "9,49-GB-Tabelle: exakte Position und Segmentpartner auslesen")},
    {"state": "Ohne geprüfte Kante und ohne freigegebene Punkte", "ids": coverage_audit["of_these_with_no_released_point"],
     "nextEvidence": "Skelett, neue FlyWire-Version oder EM-basierte Nachprüfung erforderlich"},
    {"state": "Zelltyp-Verbindungshypothese aus homologen Zellen", "ids": missing_link_audit["ids_with_type_hypotheses"],
     "nextEvidence": "Nur Zielzelltyp; kein belegter exakter Partner oder neuer Graph-Eintrag"},
]
if banc_crosswalk:
    missing_status.append({
        "state": "BANC-Homolog in anderem Tier gefunden",
        "ids": banc_crosswalk["reviewed_valid_missing_fafb_ids"],
        "nextEvidence": "Geprüfte tierübergreifende Zellzuordnung; keine neue FAFB-Synapse",
    })
if malecns_types:
    missing_status.append({
        "state": "MaleCNS-Zelltyp in anderem Tier zugeordnet",
        "ids": malecns_types["counts"]["fafb_ids_with_same_side_male_sources"],
        "nextEvidence": "520 davon R1–6; 42 der übrigen 96 zugeordnet. Nur Typ-/Seitenvergleich, keine FAFB-Kante",
    })
if princeton_audit:
    missing_status.append({
        "state": "Princeton-Detektor: Kandidaten im selben FAFB-Tier",
        "ids": princeton_audit["counts"]["unfiltered_roots_with_any_connection"],
        "nextEvidence": "3.171 gerichtete Paare aus neuem Synapsendetektor; " + ("Einzelpunkte erfasst, Autapsen und R7-Ausnahme separat" if princeton_points else "Einzelpunktprüfung läuft"),
    })

model_parameters = [
    {"parameter": "Start-/Ruhe-/Resetpotenzial", "value": "−52 mV", "use": "Initialzustand jedes LIF-Neurons"},
    {"parameter": "Spike-Schwelle", "value": "−45 mV", "use": "Schwelle für ein simuliertes Aktionspotenzial"},
    {"parameter": "Membran-Zeitkonstante", "value": "20 ms", "use": "Abklingen des Membranpotenzials"},
    {"parameter": "Synaptische Zeitkonstante", "value": "5 ms", "use": "Abklingen des synaptischen Beitrags"},
    {"parameter": "Refraktärzeit / Verzögerung", "value": "2,2 ms / 1,8 ms", "use": "Sperrzeit nach Spike / Leitungsverzögerung"},
    {"parameter": "Gewicht pro Synapse", "value": "0,275 mV", "use": "Globaler Modellskalierungsfaktor"},
    {"parameter": "Zeitschritt Eon-PyTorch", "value": "0,1 ms", "use": "Numerische Integrationsauflösung dieses Backends"},
]

checks_by_label = {row["label"]: row for row in shiu_audit["reference_checks"]}
validation = [
    {"circuit": "Antenne → aBN1", "v630_comparison_hz": "JO-CE 50,77 / JO-F 1,23",
     "sheet_row": "Table 8, Zeile 98", "v783_condition": "aBN1-ID vorhanden; Richtungscheck nach Portierung"},
    {"circuit": "Antenne → aDN1", "v630_comparison_hz": "JO-CE 13,40 / JO-F 0,00",
     "sheet_row": "Table 8, Zeile 277", "v783_condition": "ID vorhanden; Seite vor Körpersteuerung prüfen"},
    {"circuit": "Antenne → aDN2", "v630_comparison_hz": "JO-CE 19,03 / JO-F 0,00",
     "sheet_row": "Table 8, Zeile 258", "v783_condition": "ID vorhanden; Seite vor Körpersteuerung prüfen"},
    {"circuit": "Zucker → MN9 rechts", "v630_comparison_hz": "150 Hz Eingang: 83,67",
     "sheet_row": "Table 1A, Zeile 41", "v783_condition": "MN9_r-ID vorhanden"},
]
assert round(checks_by_label["JO_CE_150_to_aBN1"]["mean_firing_rate_hz"], 2) == 50.77
assert round(checks_by_label["JO_F_150_to_aBN1"]["mean_firing_rate_hz"], 2) == 1.23
assert shiu_audit["published_prediction_summary"]["all_predictions"]["correct"] == 150

band_labels = [
    ("R7_cross_detector_point_exception", "R7: Punkt- und Detektorausnahme", "Punkte in beiden Detektoren; keine Kante in den veröffentlichten Paargraphen"),
    ("P_pair_ge5_export", "Princeton: Paar mit mindestens fünf Kontakten", "Alternativer Detektor am selben FAFB-Tier; exakte Punkt- und Paarbelege"),
    ("P_pair_1_to_4_only", "Princeton: nur ein bis vier Kontakte je Paar", "Im ungefilterten Princeton-Export; unter der Fünfer-Schwelle"),
    ("B_old_segment_only", "Alte Rohpunkte nur zu ungeprüften Segmenten", "Segmentpartner anatomisch prüfen; keine identifizierte ganze Zielzelle"),
    ("P_autapse_points_only", "Princeton: nur Autapsen-Punkte", "Selbstkontaktpunkte; aus dem Princeton-Paar-Export ausgeschlossen"),
    ("C_or_no_direct_points", "Nur Zelltyp-Hypothese oder kein direkter Punkt", "Kein neuer individueller Synapsennachweis"),
]
review_bands = [
    {"band": label, "ids": integrated_evidence["counts"]["review_bands"][key],
     "evidence": meaning, "code": key}
    for key, label, meaning in band_labels
]
assert sum(row["ids"] for row in review_bands) == 616
point_exclusion_rows = [
    {"class": "Autapsen-Punkte", "points": princeton_exclusions["counts"]["autapse_rows"],
     "meaning": "Gleiche Prä- und Post-Root-ID; nicht im Princeton-Verbindungsexport"},
    {"class": "R7-Punkte ohne Eigenkontakt", "points": princeton_exclusions["counts"]["R7_rows_nonself"],
     "meaning": "Root 720575940623940963; im Punktexport, aber nicht im Paar-Export; Ursache offen"},
    {"class": "Punkte im ungefilterten Paar-Export", "points": princeton_exclusions["counts"]["retained_rows"],
     "meaning": "Nach Leerregion→UNASGD stimmen alle 3.233 Paar×Region-Zahlen exakt"},
]
assert sum(row["points"] for row in point_exclusion_rows) == princeton_exclusions["counts"]["point_rows_touching_616"]
morphology_rows = [
    {"metric": "FAFB-IDs ohne originale Aggregatkante mit Skelett", "value": morphology_616["ids_with_nodes"],
     "meaning": "Alle 616 IDs haben Knoten im offiziellen v783-Skelett-LOD"},
    {"metric": "Skelettknoten dieser 616 IDs", "value": morphology_616["target_rows_found"],
     "meaning": "Geometrie für 3D-Anzeige und räumliche Kontaktprüfung; keine neue Synapse"},
    {"metric": "Princeton-only-IDs mit Skelett", "value": morphology_616["princeton_only_ids_with_nodes"],
     "meaning": "Alle 195 IDs mit neuen Princeton-Kandidaten und ohne alte Rohpunkte sind darstellbar"},
]

pair_class_labels = [
    ("both_same_count", "In beiden Exporten, gleiche Synapsenzahl"),
    ("both_different_count", "In beiden Exporten, verschiedene Synapsenzahl"),
    ("original_only", "Nur im Originalexport"),
    ("princeton_only", "Nur im Princeton-Export"),
]
whole_brain_pair_rows = [
    {"class": label, "pairs": whole_brain["pair_comparison"][key]["pairs"],
     "originalSynapses": whole_brain["pair_comparison"][key]["original_synapses"],
     "princetonSynapses": whole_brain["pair_comparison"][key]["princeton_synapses"]}
    for key, label in pair_class_labels
]
assert sum(row["originalSynapses"] for row in whole_brain_pair_rows) == whole_brain["source_counts"]["original_synapses"]
assert sum(row["princetonSynapses"] for row in whole_brain_pair_rows) == whole_brain["source_counts"]["princeton_synapses"]
shared_pairs = (whole_brain["pair_comparison"]["both_same_count"]["pairs"]
                + whole_brain["pair_comparison"]["both_different_count"]["pairs"])
assert shared_pairs == 13447535
assert shared_pairs + whole_brain["pair_comparison"]["original_only"]["pairs"] == 15091983
assert shared_pairs + whole_brain["pair_comparison"]["princeton_only"]["pairs"] == 19773733

with (ROOT / "analysis/whole_brain_detector_comparison/new_pairs_existing_roots_strength.csv").open(encoding="utf-8", newline="") as source:
    whole_brain_strength_rows = [
        {"synapsesPerPair": row["count_bucket"],
         "directedPairs": int(row["directed_pairs"]),
         "princetonSynapses": int(row["princeton_synapses"])}
        for row in csv.DictReader(source)
    ]
assert len(whole_brain_strength_rows) == whole_brain_breakdown["output_row_counts"]["new_pairs_existing_roots_strength.csv"]
assert sum(row["directedPairs"] for row in whole_brain_strength_rows) == 6323027
assert sum(row["directedPairs"] for row in whole_brain_strength_rows[2:]) == whole_brain_breakdown["princeton_only_existing_old_connected_roots"]["pairs_ge_5"]
with (ROOT / "analysis/whole_brain_detector_comparison/pair_strength_distribution.csv").open(encoding="utf-8", newline="") as source:
    all_pair_strength_rows = list(csv.DictReader(source))
assert len(all_pair_strength_rows) == whole_brain_breakdown["output_row_counts"]["pair_strength_distribution.csv"]
original_only_ge5 = sum(int(row["directed_pairs"]) for row in all_pair_strength_rows
                        if row["comparison_class"] == "original_only" and row["count_bucket"][:2] >= "03")
assert original_only_ge5 == 437

with (ROOT / "analysis/whole_brain_detector_comparison/new_pairs_existing_roots_by_region.csv").open(encoding="utf-8", newline="") as source:
    whole_brain_region_rows = [
        {"neuropil": row["neuropil"],
         "pairRegionKeys": int(row["princeton_only_directed_pair_region_keys"]),
         "princetonSynapses": int(row["princeton_synapses"]),
         "keysGe5": int(row["keys_ge_5"])}
        for row in csv.DictReader(source)
    ]
assert len(whole_brain_region_rows) == whole_brain_breakdown["output_row_counts"]["new_pairs_existing_roots_by_region.csv"]
with (ROOT / "analysis/whole_brain_detector_comparison/region_pair_class_crosswalk.csv").open(encoding="utf-8", newline="") as source:
    region_crosswalk = list(csv.DictReader(source))
assert len(region_crosswalk) == 10
region_crosswalk_rows = [
    {"case": "Princeton-only-Region bei gemeinsamem Neuronpaar",
     "pairRegionKeys": sum(int(row["directed_pair_region_keys"]) for row in region_crosswalk
                           if row["pair_comparison_class"].startswith("both_") and row["pair_region_comparison_class"] == "princeton_only")},
    {"case": "Original-only-Region bei gemeinsamem Neuronpaar",
     "pairRegionKeys": sum(int(row["directed_pair_region_keys"]) for row in region_crosswalk
                           if row["pair_comparison_class"].startswith("both_") and row["pair_region_comparison_class"] == "original_only")},
]
assert [row["pairRegionKeys"] for row in region_crosswalk_rows] == [755099, 204865]
motor_interface_rows = [
    {"measure": "Geprüfte Beinmotorneuronen", "value": motor_interface["leg_motor_roots"], "scope": "BANC v888 · sechs Beine"},
    {"measure": "Eingangspaare v2", "value": motor_interface["incoming_graphs"]["v2"]["nonself_directed_pairs"], "scope": "Eigener BANC-Detektorstand"},
    {"measure": "Eingangspaare v3", "value": motor_interface["incoming_graphs"]["v3"]["nonself_directed_pairs"], "scope": "Eigener BANC-Detektorstand"},
    {"measure": "In v2 und v3 gemeinsam", "value": motor_interface["incoming_pairs_both_versions"], "scope": "Gleiche gerichtete BANC-IDs"},
    {"measure": "In beiden Versionen mindestens fünf", "value": motor_interface["incoming_pairs_at_least_5_both"], "scope": "Gleiche gerichtete BANC-IDs"},
    {"measure": "Kalibrierte Modell-Aktuatoren", "value": motor_interface["calibrated_actuator_channels"], "scope": "3D-Körper · derzeit keine"},
]

now = datetime.now(timezone.utc).isoformat()
evidence_cutoff_utc = max(
    *(datetime.fromisoformat(item["generated_at_utc"])
      for item in (integrated_evidence, princeton_exclusions, morphology_616, whole_brain, whole_brain_breakdown)),
    datetime.fromisoformat(motor_interface["created_utc"]),
    datetime.fromisoformat(pipeline_state["updated_utc"]),
)
evidence_cutoff_berlin = evidence_cutoff_utc.astimezone(ZoneInfo("Europe/Berlin")).date().isoformat()
snapshot = {
    "title": "Welche Daten die virtuelle Fliege schon tragen können",
    "generatedAt": now,
    "status": "reviewed",
    "report": {"asOf": evidence_cutoff_berlin,
               "integrationInputCount": len(integration_inputs),
               "integrationJoinCount": len(integration_pack["joins"]),
               "originalPipelineStatus": pipeline_state["stage"],
               "originalPipelineCompletedUtc": pipeline_state["updated_utc"],
               "wholeBrainDetector": {
                   "originalDirectedPairs": whole_brain["source_counts"]["original_directed_pairs"],
                   "princetonDirectedPairs": whole_brain["source_counts"]["princeton_directed_pairs"],
                   "sharedDirectedPairs": shared_pairs,
                   "originalOnlyPairs": whole_brain["pair_comparison"]["original_only"]["pairs"],
                   "princetonOnlyPairs": whole_brain["pair_comparison"]["princeton_only"]["pairs"],
                   "princetonOnlyBetweenPreviouslyConnectedRoots": whole_brain["priority"]["princeton_only_pairs_between_two_roots_already_connected_in_original_graph"],
                   "princetonOnlyTouching616": whole_brain["priority"]["princeton_only_pairs_touching_the_prior_616_roots"],
                   "princetonOnlySingletonsBetweenPreviouslyConnectedRoots": whole_brain_strength_rows[0]["directedPairs"],
                   "princetonOnlyGe5BetweenPreviouslyConnectedRoots": whole_brain_breakdown["princeton_only_existing_old_connected_roots"]["pairs_ge_5"],
                   "originalOnlyGe5": original_only_ge5,
                   "princetonOnlyRegionsOnSharedPairs": region_crosswalk_rows[0]["pairRegionKeys"],
                   "originalOnlyRegionsOnSharedPairs": region_crosswalk_rows[1]["pairRegionKeys"],
               },
               "reconstruction": {
                   "princetonSameSpecimenRootCount": princeton_audit["counts"]["unfiltered_roots_with_any_connection"] if princeton_audit else None,
                   "princetonDirectedPairs": princeton_audit["source_files"]["unfiltered"]["directed_pairs_touching_616"] if princeton_audit else None,
                   "princetonOnlyRoots": princeton_strata["root_coverage_intersection"]["old_raw_no__new_detector_yes"] if princeton_strata else None,
                   "oldRawOnlyRoots": princeton_strata["root_coverage_intersection"]["old_raw_yes__new_detector_no"] if princeton_strata else None,
                   "bancReviewedHomologRoots": banc_patterns["fafb_ids_with_valid_reviewed_cross_animal_match"] if banc_patterns else None,
                   "bancPartnerTypeHypotheses": banc_patterns["partner_type_hypothesis_rows"] if banc_patterns else None,
                   "bancMatchedRootsWithPrinceton": banc_cross_source["ids_with_princeton_unfiltered_same_fafb_candidate_pair"] if banc_cross_source else None,
                   "bancMatchedRootsWithOldRaw": banc_cross_source["ids_with_buhmann_released_raw_call_any_partner"] if banc_cross_source else None,
                   "maleTypeMappedRoots": malecns_types["counts"]["fafb_ids_with_same_side_male_sources"] if malecns_types else None,
                   "maleOther96MappedRoots": malecns_types["strata"]["other_96"]["author_cross_mapped_same_side"] if malecns_types else None,
                   "princetonPointAuditComplete": princeton_points is not None,
                   "princetonPointsTouching616": princeton_points["counts"]["point_rows_touching_616"] if princeton_points else None,
                   "princetonRootsWithAnyPoint": princeton_points["counts"]["roots_with_any_point"] if princeton_points else None,
                   "reviewBandsDisjoint": len(review_bands),
                   "reviewBandsRootTotal": sum(row["ids"] for row in review_bands),
                   "princetonRetainedPairRegionKeys": princeton_exclusions["counts"]["retained_pair_region_keys"],
                   "princetonPointPairExactAfterEmpiricalFilter": princeton_exclusions["checks"]["retained_point_groups_equal_unfiltered_connection_groups_exactly"],
                   "morphologyIdsWithSkeleton": morphology_616["ids_with_nodes"],
                   "morphologyNodesFor616": morphology_616["target_rows_found"],
                   "morphologyPrincetonOnlyIdsWithSkeleton": morphology_616["princeton_only_ids_with_nodes"],
               }},
    "filters": [],
    "queries": {
        "source_inventory": {
            "rows": sources,
            "source": {
                "label": "Geprüfter Katalog der öffentlichen Fliegen-Daten, Fachquellen und lokalen Prototypen",
                "executedAt": now,
                "tables": [{"name": row["name"], "href": row["url"]} for row in sources],
                "evidenceFlow": [
                    {"title": "Quellen", "detail": "Offizielle Zenodo-Archive, Autor-Repositories und begutachtete Artikel mit Supplementen; der lokale Arena-Prototyp ist getrennt als Eigenentwicklung markiert."},
                    {"title": "Lokale Integrität", "detail": "Downloads in data/research_sources/provenance.json mit SHA-256; GitHub-Dateien zusätzlich gegen gepinnte Git-Blob-SHA-1 geprüft."},
                    {"title": "Abgrenzung", "detail": "BANC ist ein anderes Tier; Eons embodied Mapping ist öffentlich beschrieben, aber keine vollständige Mapping-Tabelle wurde gefunden."},
                ],
            },
        },
        "download_pipeline": {
            "rows": downloads,
            "source": {
                "label": "Lokaler Prüfsummen-Downloader und offizielle Zenodo-Dateimanifeste",
                "executedAt": pipeline_state["updated_utc"],
                "tables": [
                    {"name": "FlyWire FAFB v783", "href": "https://zenodo.org/records/10676866"},
                    {"name": "FlyWire 3D-Morphologie", "href": "https://zenodo.org/records/10877326"},
                ],
                "evidenceFlow": [
                    {"title": "Fortschritt", "detail": "Bytes nur aus fertig übertragenen HTTP-Abschnitten der lokalen progress.json gezählt; die vorab auf volle Größe angelegte .partial-Datei gilt nicht als fertiger Download."},
                    {"title": "Integrität", "detail": "Der Downloader benennt eine .partial-Datei erst nach erfolgreichem MD5-Abgleich mit Zenodo in den endgültigen Namen um."},
                    {"title": "Abschluss", "detail": "logs/pipeline_state.json meldet complete am 26.09.2026 um 22:23:23 UTC. analysis/report.json hat alle fünf Originaldateien und alle vier Morphologiedateien gegen veröffentlichte MD5-Werte geprüft; Originaltabellen und Morphologie sind numerisch vollständig gescannt. Diese Tabelle ist eine fertige Momentaufnahme, kein Live-Stream."},
                ],
            },
        },
        "point_analysis": {
            "rows": point_detail,
            "source": {
                "label": "Prüfberichte für die offizielle Einzelpunktdatei und ihre separat exportierten Segmentkontakte",
                "executedAt": segment_audit["generated_at_utc"] if segment_audit else point_audit["generated_at_utc"] if point_audit else now,
                "tables": [{"name": "FlyWire Zenodo v783", "href": "https://zenodo.org/records/10676866"}],
                "evidenceFlow": [
                    {"title": "Einzelpunkte", "detail": "analysis/audit_synapse_points.py prüft alle 130.054.535 Punkte und die vier Partnerklassen. 7.385 Punktzeilen der 616 IDs wurden mit Synapsen-ID und Position exportiert." if point_audit else "Der Vollscan mit Export der Kontakte der 616 IDs steht noch aus."},
                    {"title": "Segmentkontakte", "detail": "7.337 beobachtete Punktkontakte zu 3.475 ungeprüften Segment-IDs bilden 4.327 Gruppen nach Partner, Richtung und Neuropil. Ein Segment erhält dadurch keine erfundene Neuronidentität." if segment_audit else "analysis/build_observed_segment_links.py fasst nur beobachtete Punkte nach exaktem Segmentpartner, Richtung und Neuropil zusammen."},
                    {"title": "Rohpunkt-Ausnahmen", "detail": "48 Punkte mit zwei geprüften Partnern wurden separat gesichert; sie ergeben 21 Paar/Region-Schlüssel, von denen keiner in den 16.847.997 Zeilen der Aggregattabelle vorkommt." if exception_audit else "Separate Rohpunkte mit zwei geprüften Partnern werden gegen die ganze Aggregattabelle geprüft."},
                ],
            },
        },
        "raw_aggregate_exception": {
            "rows": raw_aggregate_exception,
            "source": {
                "label": "Exakte veröffentlichte Einzelkontakte im lokalen Punkt-CSV, mit geprüften v783-Root-IDs abgeglichen",
                "executedAt": point_audit["generated_at_utc"] if point_audit else now,
                "tables": [{"name": "FlyWire Zenodo v783", "href": "https://zenodo.org/records/10676866"}],
                "evidenceFlow": [
                    {"title": "Rohpunkte", "detail": "48 eindeutige synapse_id-Werte haben zwei geprüfte Partner und die R7-ID 720575940623940963; alle im Neuropil ME_R."},
                    {"title": "Paarbildung", "detail": "Diese 48 Punkte ergeben 21 gerichtete (pre_root_id, post_root_id, neuropil)-Schlüssel. Ein Scan aller 16.847.997 veröffentlichten Aggregatzeilen fand keinen davon." if exception_audit else "Die 48 Punkte ergeben 21 gerichtete Paar/Region-Schlüssel, die im geprüften Aggregat bisher nicht gefunden wurden."},
                    {"title": "Deutung", "detail": "Die Punkte sind veröffentlicht und beobachtet. Warum sie in der aggregierten Tabelle fehlen, ist daraus nicht bestimmbar; die Ausnahme bleibt getrennt vom geprüften CSR-Graphen."},
                ] if point_audit else [{"title": "Offen", "detail": "Wird nach dem verifizierten Einzelpunkt-Vollscan gefüllt."}],
            },
        },
        "raw_exception_pairs": {
            "rows": raw_exception_pairs,
            "source": {
                "label": "21 gerichtete Rohkontakt-Paare mit exakten FAFB-v783-IDs und offiziellen Zelltypannotationen",
                "executedAt": exception_audit["generated_at_utc"] if exception_audit else now,
                "tables": [
                    {"name": "FlyWire Einzelpunkte", "href": "https://zenodo.org/records/10676866"},
                    {"name": "FlyWire Zellannotation v2.1.0", "href": "https://github.com/flyconnectome/flywire_annotations/releases/tag/v2.1.0"},
                ],
                "evidenceFlow": [
                    {"title": "Rohbelege", "detail": "Alle 48 synapse_id-Werte bleiben im lokal verifizierten Ausnahme-CSV erhalten; diese Tabelle gruppiert nach gerichtetem Prä/Post-Paar und Neuropil."},
                    {"title": "Zelltyp", "detail": "Zellnamen stammen per exakter Root-ID aus Supplemental_file1_neuron_annotations.tsv v2.1.0; alle beteiligten annotierten Seiten sind right."},
                    {"title": "Grenze", "detail": "21 Paar/Region-Schlüssel fehlen im offiziellen Aggregat. Ihre Rohsynapsen sind ein Datenlückenbefund, keine experimentell funktionell validierten Verbindungen."},
                ],
            },
        },
        "raw_published_reconciliation": {
            "rows": reconciliation_rows,
            "source": {
                "label": "Vollständiger Paar×Neuropil-Abgleich zwischen 130 Mio. Rohpunkten und 16,8 Mio. veröffentlichten Aggregatzeilen",
                "executedAt": reconciliation_audit["generated_at_utc"] if reconciliation_audit else now,
                "tables": [{"name": "FlyWire FAFB v783 Originaldateien", "href": "https://zenodo.org/records/10676866"}],
                "evidenceFlow": [
                    {"title": "Vollvergleich", "detail": "Alle Rohpunkte mit zwei offiziellen Proofread-IDs nach gerichtetem Prä/Post-Paar und Neuropil aggregiert und mit allen 16.847.997 veröffentlichten Verbindungszeilen verglichen."},
                    {"title": "Originale Regionslabels", "detail": "Ohne Normalisierung: 3.214 Roh-only-, 3.193 Aggregat-only-Schlüssel und 0 gemeinsame Schlüssel mit unterschiedlicher Synapsenzahl."},
                    {"title": "Empirische Normalisierung", "detail": "Für exakt 3.193 gerichtete Paare mit 4.185 Punkten steht im Rohfile das Regionslabel None, im Aggregat UNASGD; Richtung, IDs und Zählwert stimmen jeweils. None→UNASGD ist eine beobachtete Dateikonvention, keine neue biologische Zuordnung."},
                    {"title": "Verbleibende Ausnahme", "detail": "Nach dieser Regionsnormalisierung bleiben 21 R7-Paar/Region-Schlüssel mit 48 Rohpunkten ohne Aggregatzeile. Die offizielle Graphdatei und unser CSR-Export bleiben unverändert."},
                ] if reconciliation_audit else [{"title": "Offen", "detail": "Der globale Paar×Neuropil-Vollvergleich steht noch aus."}],
            },
        },
        "integration_inventory": {
            "rows": integration_inputs,
            "source": {
                "label": f"Maschinenlesbares lokales Integrationspaket mit {len(integration_inputs)} Eingaben und {len(integration_pack['joins'])} Verknüpfungsregeln",
                "executedAt": now,
                "tables": [
                    {"name": "FlyWire FAFB v783", "href": "https://zenodo.org/records/10676866"},
                    {"name": "Shiu et al.", "href": "https://doi.org/10.1038/s41586-024-07763-9"},
                    {"name": "FlyGym", "href": "https://doi.org/10.1038/s41592-024-02497-y"},
                ],
                "evidenceFlow": [
                    {"title": "Inventar", "detail": f"{len(integration_inputs)} Einträge aus analysis/model_integration_pack.json, jeder mit lokaler Datei, Rolle, Quelladresse und Nutzungsstatus."},
                    {"title": "Join-Regeln", "detail": f"{len(integration_pack['joins'])} maschinenlesbare Regeln trennen exakte v783-Root-ID-Verknüpfungen von typbasierten oder art-/releasefremden Referenzen."},
                    {"title": "Referenzgrenze", "detail": "Lokal vorhandener Modellcode oder eine Körperdatei ist noch kein funktionierender biologischer Sensor-Motor-Anschluss."},
                ],
            },
        },
        "graph_comparison": {
            "rows": graphs,
            "source": {
                "label": "Lokaler Vollscan und Modelltabellen-Audit, FAFB v783",
                "executedAt": audit["generated_at_utc"],
                "tables": [
                    {"name": "FlyWire FAFB v783", "href": "https://zenodo.org/records/10676866"},
                    {"name": "Shiu v783", "href": "https://github.com/philshiu/Drosophila_brain_model"},
                    {"name": "Eon v783", "href": "https://github.com/eonsystemspbc/fly-brain"},
                ],
                "evidenceFlow": [
                    {"title": "IDs und Indizes", "detail": "analysis/audit_research_sources.py prüfte alle 15.091.983 Parquet-Zeilen gegen die Shiu-Completeness-Reihenfolge; 0 ID-Mismatches."},
                    {"title": "Originalvergleich", "detail": "Der Modellsatz entspricht exakt der Vereinigung aller Neuronen mit einer Original-Verbindungszeile. 616 offizielle IDs fehlen dort. Zusätzlich wurden alle 15.091.983 Shiu-Paare gegen den Original-CSR-Export geprüft: exakt gleiche gerichtete Paarmenge und null abweichende Synapsenzahlen (analysis/model_original_edge_comparison.json)."},
                    {"title": "Tabellengranularität", "detail": "FlyWire Original hat Neuronenpaar×Region-Zeilen; Shiu/Eon Parquet und der neue vollständige CSR-Export haben Neuronenpaar-Zeilen. Ein früherer kompakter Export ist zusätzlich vorgefiltert."},
                ],
                "metricDefinitions": [
                    {"label": "Neuronen", "definition": "Eindeutige Root-IDs der jeweiligen dargestellten Graphknoten.", "componentIds": ["graph-table"]},
                    {"label": "Verbindungszeilen", "definition": "Zeilen in der jeweils angegebenen Granularität; nicht zwischen allen drei Produkten als identische Kantendefinition vergleichen.", "componentIds": ["graph-table"]},
                    {"label": "Synapsen", "definition": "Summe der Synapsenzahlen der jeweiligen Verbindungstabelle.", "componentIds": ["graph-table"]},
                ],
            },
        },
        "literature": {
            "rows": papers,
            "source": {
                "label": "Primärarbeiten und Preprints mit konkretem Modellbeitrag",
                "tables": [{"name": row["work"], "href": row["url"]} for row in papers],
                "evidenceFlow": [
                    {"title": "Auswahl", "detail": "Nur Facharbeiten mit prüfbarem Daten-, Methoden- oder Validierungsbeitrag für FAFB v783 bzw. klar markierten Vergleichsdaten."},
                    {"title": "Versionsgrenze", "detail": "Shiu-Publikation wurde auf v630 gerechnet; Repository enthält v783-Eingaben. BANC ist ein anderes weibliches Tier."},
                ],
            },
        },
        "pathway_evidence": {
            "rows": pathways,
            "source": {
                "label": "Verifizierte Ergänzungstabellen und exakte FAFB-Root-ID-Abgleiche",
                "executedAt": now,
                "tables": [{"name": row["source"], "href": row["url"]} for row in pathways],
                "evidenceFlow": [
                    {"title": "Identität", "detail": "Die Zahlen zählen exakte 18-stellige FAFB-Root-ID-Treffer gegen die lokalen 139.255 v783-IDs, nicht funktionell bestätigte Reizantworten."},
                    {"title": "Nachvollziehbarkeit", "detail": "Die Originaltabellen und SHA-256-Werte stehen in data/research_sources/other/*/provenance.json; Shiu-Zellen mit Blatt/Zeile in data/research_sources/shiu/derived/shiu_supplement_index.json."},
                    {"title": "Grenze", "detail": "Ein passender Zellname oder eine Graphmitgliedschaft allein bestimmt weder Reiztransduktion noch Muskelkraft oder spontane Motivation."},
                ],
            },
        },
        "model_parameters": {
            "rows": model_parameters,
            "source": {
                "label": "Eon-Code, auf Shiu et al. gestütztes LIF-Modell",
                "tables": [
                    {"name": "Eon Brian2-Parameter", "href": "https://github.com/eonsystemspbc/fly-brain/blob/a3db62f9436074e485c0278290c2164ed6150808/code/run_brian2_cuda.py"},
                    {"name": "Eon PyTorch-Parameter", "href": "https://github.com/eonsystemspbc/fly-brain/blob/a3db62f9436074e485c0278290c2164ed6150808/code/run_pytorch.py"},
                    {"name": "Shiu-Fachartikel", "href": "https://doi.org/10.1038/s41586-024-07763-9"},
                ],
                "evidenceFlow": [
                    {"title": "Ablesung", "detail": "Werte aus default_params in code/run_brian2_cuda.py und MODEL_PARAMS/DT in code/run_pytorch.py; Eon-Git-Revision a3db62f."},
                    {"title": "Bedeutung", "detail": "Dies sind Modellannahmen für einen einfachen LIF-Simulator, keine gemessenen individuellen Parameter aller 139.255 Neuronen."},
                ],
            },
        },
        "synapse_point_groups": {
            "rows": point_groups,
            "source": {
                "label": "Vollscan der offiziellen FAFB-v783-Einzelpunkttabelle" if point_audit else "Vorläufige Differenzrechnung aus offiziellen Alle-Partner-Zähltabellen",
                "executedAt": point_audit["generated_at_utc"] if point_audit else coverage_audit["generated_at_utc"],
                "tables": [
                    {"name": "FlyWire Zenodo v783", "href": "https://zenodo.org/records/10676866"},
                ],
                "evidenceFlow": [
                    {"title": "Gesamtmenge", "detail": "Beide per_neuron_neuropil_count-Tabellen und der Rohpunkt-Vollscan summieren je 130.054.535 freigegebene Kontakte." if point_audit else "Die beiden per_neuron_neuropil_count-Tabellen summieren je 130.054.535 Kontakte; Punktklassen sind bis zum Rohscan vorläufig."},
                    {"title": "Vier disjunkte Gruppen", "detail": "Jeder Rohpunkt wurde auf Sender- und Empfängerseite gegen 139.255 Proofread-Root-IDs geprüft; alle vier Gruppen summieren exakt auf die offizielle Gesamtzahl." if point_audit else "Vorläufige Zählung aus Summen und Graph; ein direkter Nachweis je Punkt steht aus."},
                    {"title": "48er-Netto-Differenz", "detail": "Der Rohscan findet 54.492.970 Punkte mit zwei geprüften Partnern, die Aggregattabelle 54.492.922. Ein vollständiger Paar×Region-Abgleich zeigt außerdem 3.193 Fälle mit Rohlabel None versus Aggregatlabel UNASGD und identischen gerichteten Paaren/Zahlen. Nach dieser beobachteten Label-Zuordnung bleiben 21 R7-Paare mit 48 Rohpunkten ohne Aggregatzeile." if reconciliation_audit else "Die Netto-Differenz allein ersetzt keinen vollständigen Paar×Region-Abgleich."},
                ],
            },
        },
        "missing_neuron_status": {
            "rows": missing_status,
            "source": {
                "label": "FAFB v783.0-Originalgraph, Princeton-2025-Detektor, Rohpunkte und getrennte Zelltypvergleiche",
                "executedAt": missing_link_audit["generated_at_utc"],
                "tables": [
                    {"name": "FlyWire Original", "href": "https://zenodo.org/records/10676866"},
                    {"name": "Visuelles Typinventar", "href": "https://doi.org/10.1038/s41586-024-07981-1"},
                    {"name": "BANC v888 (anderes Tier)", "href": "https://doi.org/10.1038/s41586-026-10735-w"},
                    {"name": "MaleCNS v1.0 (anderes Tier)", "href": "https://doi.org/10.1016/j.cell.2026.08.015"},
                    {"name": "Princeton-Synapsendetektor 2025 (dasselbe FAFB-Tier)", "href": "https://doi.org/10.1101/2025.07.11.664377"},
                ],
                "evidenceFlow": [
                    {"title": "616 IDs", "detail": "Offizielle Proofread-ID-Liste minus Vereinigungsmenge der Partner in proofread_connections; diese 616 IDs haben keine Kante im gemessenen Proofread-Paargraphen."},
                    {"title": "336/280", "detail": "Bei 336 der 616 IDs zeigen die offiziellen Alle-Partner-Summendateien freigegebene Synapsen; bei 280 keinen."},
                    {"title": "R7-Ausnahme", "detail": "Eine der 616 IDs, R7 720575940623940963, hat 48 Einzelpunkte mit geprüften Partnern, die in der publizierten aggregierten Proofread-Tabelle fehlen. Diese Rohpunkte werden getrennt von den dort geprüften Kanten geführt." if point_audit else "Die Einzelpunktdatei kann zusätzliche Ausnahmen sichtbar machen."},
                    {"title": "552 Hypothesen", "detail": "Gleicher Zelltyp und gleiche Seite, mindestens 10 verbundene Homologe, mindestens 3 mit Zieltyp und mindestens 5% Kohortenanteil; visuelle Typen zusätzlich gegen publizierte Typmatrix. Keine exakten Kanten erfunden."},
                    {"title": "BANC-Vergleich", "detail": "BANC markiert 38 der 616 IDs als Homolog-Kandidaten; 34 davon haben gültige geprüfte Match-Zeilen. Für diese 34 wurden 7.293 Richtung×Partner-Zelltyp-Muster in einem anderen Tier zusammengestellt. 33 der 34 FAFB-IDs haben zusätzlich Princeton-Kandidaten im selben FAFB-Tier; das macht die BANC-Homologen nicht zu exakten FAFB-Kanten." if banc_patterns and banc_cross_source else "BANC-Typvergleich steht noch aus."},
                    {"title": "MaleCNS-Vergleich", "detail": "562 der 616 FAFB-IDs haben eine typ- und seitengleiche MaleCNS-Quelle; 520 davon sind R1–6-Photorezeptoren. Unter den anderen 96 sind es 42. Diese Information betrifft ein anderes, männliches Tier und ist kein exakter FAFB-Synapsennachweis." if malecns_types else "MaleCNS-Zelltypenvergleich steht noch aus."},
                    {"title": "Neuer Detektor am selben Tier", "detail": "Die ungefilterte Princeton-2025-Verbindungstabelle hat 3.171 gerichtete Paare mit 477 der 616 v783.0-kantenlosen IDs. 195 dieser IDs hatten im älteren Rohpunktexport keinen Punkt. Die Princeton-Einzelpunkttabelle hat 26.941 Punkte an 550 der 616 IDs, einschließlich Selbstkontakten und einer R7-Ausnahme, die im Paar-Export fehlt. Die zwei Exportstufen müssen getrennt bleiben." if princeton_audit and princeton_strata and princeton_points else "Der neue Princeton-Detektor wird separat geprüft."},
                ],
            },
        },
        "whole_brain_pair_classes": {
            "rows": whole_brain_pair_rows,
            "source": {
                "label": "Vollständiger gerichteter Paarvergleich zweier FAFB-v783-Synapsendetektoren",
                "executedAt": whole_brain["generated_at_utc"],
                "tables": [
                    {"name": "Originaler FlyWire-v783-Datensatz", "href": "https://zenodo.org/records/10676866"},
                    {"name": "Princeton-Detektor 2025", "href": "https://doi.org/10.1101/2025.07.11.664377"},
                ],
                "evidenceFlow": [
                    {"title": "Quellen", "detail": "analysis/whole_brain_detector_comparison/audit.json vergleicht die lokal prüfsummenfixierten Original- und Princeton-Verbindungstabellen. Alle Prä-/Post-IDs liegen im offiziellen FAFB-v783-Root-Array."},
                    {"title": "Granularität", "detail": "Neuropile werden pro gerichtetem Prä/Post-Paar summiert. Die vier Paarmengen sind disjunkt und rekonstruieren 15.091.983 Originalpaare sowie 19.773.733 Princeton-Paare; 13.447.535 Paare treten in beiden Exporten auf."},
                    {"title": "Grenze", "detail": "Unterschiede zwischen zwei automatischen Detektoren sind keine experimentell bestätigten neuen Synapsen. Counts werden nicht addiert; der veröffentlichte Originalgraph wurde nicht verändert."},
                ],
                "metricDefinitions": [
                    {"label": "Gerichtete Paare", "definition": "Eindeutige (pre_root_id, post_root_id)-Kombinationen nach Summe über Neuropile, auf FAFB-v783-Root-IDs.", "componentIds": ["whole-brain-pair-table"]},
                    {"label": "Synapsenzahl je Detektor", "definition": "Summe der jeweiligen Detektortabellen innerhalb der angezeigten Paarmengen; nicht zusammenzählen.", "componentIds": ["whole-brain-pair-table"]},
                ],
            },
        },
        "whole_brain_new_pair_strength": {
            "rows": whole_brain_strength_rows,
            "source": {
                "label": "Kontaktzahl-Verteilung der Princeton-only-Paare zwischen FAFB-IDs mit jeweils anderen alten Kanten",
                "executedAt": whole_brain_breakdown["generated_at_utc"],
                "tables": [
                    {"name": "Originaler FlyWire-v783-Datensatz", "href": "https://zenodo.org/records/10676866"},
                    {"name": "Offizielle ungefilterte Princeton-Verbindungen", "href": "https://storage.googleapis.com/flywire-data/codex/data/fafb/783/connections_princeton_no_threshold.csv.gz"},
                ],
                "evidenceFlow": [
                    {"title": "Population", "detail": "analysis/whole_brain_detector_comparison/breakdown_audit.json und new_pairs_existing_roots_strength.csv zählen ausschließlich die 6.323.027 Princeton-only-Paare, deren beide Root-IDs jeweils andere Kanten im älteren Originalgraphen haben. Das konkrete Paar kommt nur bei Princeton vor. Die weiteren 3.171 Paare berühren eine der 616 zuvor isolierten IDs und werden separat analysiert."},
                    {"title": "Schwelle", "detail": "5.207.559 Paare haben genau einen Princeton-Count, 63.854 mindestens fünf. Diese Kategorien sind disjunkt; die Counts sind automatische Synapsendetektionen, keine Konfidenzen oder physiologischen Gewichte."},
                ],
                "metricDefinitions": [{"label": "Gerichtete Paare", "definition": "Princeton-only-Paare zwischen zwei zuvor im Originalgraphen beteiligten FAFB-IDs, gebündelt nach Princeton-Synapsenzahl je Paar.", "componentIds": ["whole-brain-strength-table"]}],
            },
        },
        "whole_brain_new_pair_regions": {
            "rows": whole_brain_region_rows,
            "source": {
                "label": "Neuropil-Verteilung der Princeton-only-Kandidaten zwischen FAFB-IDs mit jeweils anderen alten Kanten",
                "executedAt": whole_brain_breakdown["generated_at_utc"],
                "tables": [
                    {"name": "FlyWire-v783-Original", "href": "https://zenodo.org/records/10676866"},
                    {"name": "Princeton-Detektor 2025", "href": "https://doi.org/10.1101/2025.07.11.664377"},
                ],
                "evidenceFlow": [
                    {"title": "Quelle", "detail": "analysis/whole_brain_detector_comparison/new_pairs_existing_roots_by_region.csv zählt 79 Neuropil-Zeilen; im Bericht stehen die acht größten, die vollständige Verteilung bleibt in der Dateninspektion."},
                    {"title": "Granularität", "detail": "Ein gerichtetes Paar kann mehrere Neuropile berühren. Paar×Region-Schlüssel dürfen deshalb nicht zur Zahl eindeutiger gerichteter Paare aufsummiert werden."},
                    {"title": "Grenze", "detail": "Räumliche Häufung unterstützt die Priorisierung einer Sichtung, validiert aber keine neue FAFB-Synapse."},
                ],
                "metricDefinitions": [{"label": "Paar×Region-Schlüssel", "definition": "Eindeutige gerichtete Prä/Post-Paare innerhalb eines Neuropils; dasselbe Paar kann in mehreren Zeilen stehen.", "componentIds": ["whole-brain-region-table"]}],
            },
        },
        "whole_brain_region_crosswalk": {
            "rows": region_crosswalk_rows,
            "source": {
                "label": "Regionsexklusive Schlüssel auf FAFB-Neuronpaaren, die in beiden Detektoren vorkommen",
                "executedAt": whole_brain_breakdown["generated_at_utc"],
                "tables": [
                    {"name": "Originaler FlyWire-v783-Datensatz", "href": "https://zenodo.org/records/10676866"},
                    {"name": "Offizielle Princeton-Verbindungen", "href": "https://storage.googleapis.com/flywire-data/codex/data/fafb/783/connections_princeton_no_threshold.csv.gz"},
                ],
                "evidenceFlow": [
                    {"title": "Quellvergleich", "detail": "analysis/whole_brain_detector_comparison/region_pair_class_crosswalk.csv ist die vollständige zehnzeilige Kreuztabelle zwischen Status des gerichteten Paars und Status des Paar×Region-Schlüssels; die zwei Berichtszeilen summieren nur gemeinsame Paare mit einseitig vorkommender Region."},
                    {"title": "Grenze", "detail": "755.099 Princeton-only- und 204.865 Original-only-Regionsschlüssel auf gemeinsamen Paaren sind keine zusätzlichen gerichteten Neuronpaare. Sie sind Detektor- beziehungsweise Regionszuordnungsdifferenzen im selben FAFB-Präparat."},
                ],
                "metricDefinitions": [{"label": "Paar×Region-Schlüssel", "definition": "Neuropil-spezifische Prä/Post-Schlüssel, deren Prä/Post-Paar in beiden Detektorständen vorkommt, die Regionszuordnung aber nur in einem.", "componentIds": ["whole-brain-region-crosswalk-table"]}],
            },
        },
        "banc_leg_motor_interface": {
            "rows": motor_interface_rows,
            "source": {
                "label": "Geprüfte BANC-v888-Beinmotorneuronen und getrennte v2/v3-Eingangsgraphen",
                "executedAt": motor_interface["created_utc"],
                "tables": [
                    {"name": "BANC-v888-Datensatz", "href": motor_interface["dataset_doi"]},
                    {"name": "BANC-Primärarbeit", "href": motor_interface["paper"]},
                ],
                "evidenceFlow": [
                    {"title": "Lokale Prüfung", "detail": "analysis/body_neural_interface/audit.json wurde aus prüfsummenfixierten BANC-v888-Metadaten und den separat ausgewerteten v2/v3-Kantenlisten erzeugt; alle 391 Motor-IDs sind als proofread markiert."},
                    {"title": "Granularität", "detail": "112.809 und 117.988 sind getrennte gerichtete Eingangspaare zu denselben 391 BANC-Motorneuronen. 101.637 Paare kommen in beiden Detektorständen vor; 35.725 davon haben in beiden mindestens fünf Counts. Die Versionen nicht summieren."},
                    {"title": "Modellgrenze", "detail": "BANC stammt von einem anderen Tier als FAFB. Die Körperbeobachtung fly.body-observation.v1 liefert geometrische Gelenkwerte; null Aktuatorkanäle sind biologisch kalibriert. Es existiert keine direkte FAFB-Root-ID-zu-Muskel-Kopplung."},
                ],
                "metricDefinitions": [{"label": "Motorneuronen und gerichtete Paare", "definition": "Geprüfte BANC-v888-Beinmotor-Root-IDs beziehungsweise getrennte gerichtete Eingangs-Paarmengen der BANC-v2/v3-Exporte; keine FAFB-v783-Kanten.", "componentIds": ["banc-leg-motor-table"]}],
            },
        },
        "integrated_review_bands": {
            "rows": review_bands,
            "source": {
                "label": "Sechs disjunkte Prüfbänder für die 616 FAFB-v783-IDs ohne Originalkante",
                "executedAt": integrated_evidence["generated_at_utc"],
                "tables": [
                    {"name": "FAFB-v783-Originaldaten", "href": "https://zenodo.org/records/10676866"},
                    {"name": "Princeton-Detektor am selben FAFB-Präparat", "href": "https://doi.org/10.1101/2025.07.11.664377"},
                ],
                "evidenceFlow": [
                    {"title": "Berechnung", "detail": "analysis/reconstruction_candidates_v783/integrated_evidence_audit.json und integrated_root_review_queue_616.csv verknüpfen Original-Rohpunkte, Princeton-Punkte/Paar-Exporte und interne Typ-Hypothesen."},
                    {"title": "Disjunktheit", "detail": "Ein FAFB-Root steht genau in einem der sechs Prüfbänder; 1 + 203 + 274 + 53 + 22 + 63 = 616. Das Band beschreibt die nächste Sichtung, keine kalibrierte Konfidenz."},
                    {"title": "Modellgrenze", "detail": "Princeton-Kandidaten sind ein alternativer automatischer Detektor im selben Tier. BANC- und MaleCNS-Typen aus anderen Tieren sind hier keine individuellen FAFB-Kanten."},
                ],
                "metricDefinitions": [{"label": "IDs", "definition": "Eindeutige FAFB-v783-Root-IDs pro disjunktem Prüfband; Summe 616.", "componentIds": ["integrated-review-bands-table"]}],
            },
        },
        "princeton_point_exclusion": {
            "rows": point_exclusion_rows,
            "source": {
                "label": "Exakter Punkt-zu-Paar-Abgleich des Princeton-2025-Detektors für die 616 FAFB-IDs",
                "executedAt": princeton_exclusions["generated_at_utc"],
                "tables": [
                    {"name": "Offizielle FAFB-v783-Princeton-Punktdatei", "href": "https://storage.googleapis.com/flywire-data/codex/data/fafb/783/fafb_v783_princeton_synapse_table.csv.gz"},
                    {"name": "Offizielle ungefilterte Princeton-Verbindungen", "href": "https://storage.googleapis.com/flywire-data/codex/data/fafb/783/connections_princeton_no_threshold.csv.gz"},
                    {"name": "Princeton-Detektorpaper", "href": "https://doi.org/10.1101/2025.07.11.664377"},
                ],
                "evidenceFlow": [
                    {"title": "Quelle", "detail": "Die offiziellen Princeton-Punkt- und Verbindungsexporte sind gegen die GCS-MD5-Werte geprüft; Audit: analysis/reconstruction_candidates_v783/princeton_point_exclusion_audit.json."},
                    {"title": "Zerlegung", "detail": "26.941 Punktzeilen = 5.814 Autapsen + 213 nichtautaptische R7-Punkte + 20.914 im ungefilterten Paar-Export gezählte Punkte."},
                    {"title": "Exakter Vergleich", "detail": "Nach Ausschluss der ersten beiden Klassen und Leerregion→UNASGD stimmen alle 3.233 gerichteten Paar×Region-Zahlen exakt. Die Filterregel ist empirisch rekonstruiert; warum die R7-Punkte im früheren Paar-Export fehlen, ist unbekannt."},
                ],
                "metricDefinitions": [{"label": "Punktzeilen", "definition": "Disjunkte Princeton-Einzelpunktzeilen, die eine der 616 FAFB-IDs berühren; Summe 26.941.", "componentIds": ["princeton-point-exclusion-table"]}],
            },
        },
        "morphology_616": {
            "rows": morphology_rows,
            "source": {
                "label": "Vollscan und MD5-Prüfung der offiziellen FlyWire-v783-Skelettdatei für 616 IDs",
                "executedAt": morphology_616["generated_at_utc"],
                "tables": [{"name": "FlyWire-v783-Morphologie auf Zenodo", "href": "https://zenodo.org/records/10877326"}],
                "evidenceFlow": [
                    {"title": "Quelle", "detail": "data/flywire_morphology_v783/sk_lod1_783_healed_ds2.parquet (5.355.543.468 Byte), MD5 a4c104776f33ec539ef859064c4de3df in analysis/morphology_616/audit.json erneut bestätigt."},
                    {"title": "Vollscan", "detail": "Alle 268.281.651 Parquet-Zeilen gescannt; 151.369 Skelettknoten gehören zu allen 616 FAFB-IDs ohne Originalkante, darunter alle 195 Princeton-only-IDs."},
                    {"title": "Grenze", "detail": "Skelettknoten und räumliche Nähe erlauben 3D-Sichtung; sie belegen keine neue Synapse, kein Vorzeichen und keine motorische Funktion."},
                ],
                "metricDefinitions": [{"label": "Knoten", "definition": "Parquet-Zeilen der heruntergeladenen LOD1-Skelettdatei für die 616 betrachteten IDs; nicht die Zahl von Synapsen.", "componentIds": ["morphology-616-table"]}],
            },
        },
        "validation_examples": {
            "rows": validation,
            "source": {
                "label": "Shiu et al. Ergänzungstabellen: ausgewählte publizierte v630-Vergleiche",
                "tables": [{"name": "Nature Supplement XLSX", "href": shiu_audit["source"]}],
                "evidenceFlow": [
                    {"title": "Zellwerte", "detail": "Mittelraten sind direkt aus den angegebenen Blättern/Zeilen gelesen; alle 13 Checks mit exakten Quellzellen stehen in data/research_sources/shiu/derived/shiu_supplement_index.json."},
                    {"title": "Versionsgrenze", "detail": "Diese veröffentlichten Aktivitätswerte stammen aus v630. Für v783 sind sie Sollrichtungen/Kontrollmuster, keine garantierten Zahlenwerte."},
                    {"title": "Gesamtcheck", "detail": "Table 10, Zeile 12: 150/164 empirische Vorhersagen korrekt; dies ist kein Maß allgemeiner Verhaltensintelligenz."},
                ],
            },
        },
    },
}
from report_neuron_validation import extend_snapshot
extend_snapshot(snapshot)
from report_motor_control import extend_motor_snapshot
extend_motor_snapshot(snapshot)
from report_sensorimotor import extend_sensorimotor_snapshot
extend_sensorimotor_snapshot(snapshot)
from report_cpg import extend_cpg_snapshot
extend_cpg_snapshot(snapshot)
from report_flight import extend_flight_snapshot
extend_flight_snapshot(snapshot)

(ROOT / "analysis" / "research_report_snapshot.json").write_text(
    json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(f"Wrote {len(sources)} sources, {len(graphs)} graphs, {len(papers)} papers, {len(pathways)} pathways, {len(model_parameters)} parameters and {len(validation)} checks")
