"""Idempotently register source data, reconstruction layers and functional assays.

The pack is a manifest of usable evidence, not a script that merges connectomes.
Run from the project root with ``analysis/.venv/Scripts/python.exe``.
"""

from __future__ import annotations

import hashlib
import json
import re
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "analysis/model_integration_pack.json"
data = json.loads(PACK.read_text(encoding="utf-8"))


def upsert(items: list[dict], entry: dict) -> None:
    for index, old in enumerate(items):
        if old["id"] == entry["id"]:
            items[index] = entry
            break
    else:
        items.append(entry)


def source(id: str, path: str, manifest: str, url: str, fmt: str,
           release: str, key: str, role: str, license_note: str) -> None:
    assert (ROOT / path).is_file(), path
    assert (ROOT / manifest).is_file(), manifest
    upsert(data["inputs"], {
        "id": id, "path": path, "integrity_manifest": manifest,
        "source_url": url, "format": fmt, "release": release,
        "state": "ready", "key": key, "role": role,
        "license_note": license_note,
    })


def derived(id: str, path: str, audit: str, release: str,
            key: str, role: str) -> None:
    assert (ROOT / path).is_file(), path
    assert (ROOT / audit).is_file(), audit
    upsert(data["inputs"], {
        "id": id, "path": path, "integrity_manifest": audit,
        "format": Path(path).suffix.lstrip(".").upper(), "release": release,
        "state": "ready", "key": key, "role": role,
        "license_note": "Derived comparison; retain the original source provenance and license",
    })


def join(id: str, left: str, right: str, method: str,
         assertion: str, cardinality: str) -> None:
    upsert(data["joins"], {
        "id": id, "left": left, "right": right,
        "method": method, "cardinality": cardinality,
        "assertion": assertion,
    })


data["as_of_date"] = "2026-09-27"
data["specimen_namespaces"] = {
    "FAFB_v783_female_brain": {
        "id_field": "FlyWire root_id as decimal string",
        "original_graph": "flywire_edges",
        "alternative_detector": ["fafb_princeton_unfiltered_edges", "fafb_princeton_filtered_edges", "fafb_princeton_points"],
        "rule": "Princeton is the same FAFB segmentation with a different synapse detector; retain detector identity and never add detector counts together.",
    },
    "BANC_v888_female_brain_and_vnc": {
        "id_field": "BANC v888 banc_888_id as decimal string",
        "graph_variants": ["banc_v888_edges_v2", "banc_v888_edges_v3"],
        "rule": "A separate female specimen. Choose one v888 detector graph; v2 is the paper graph and v3 is updated. Do not sum them or graft their individual edges onto FAFB.",
    },
    "MaleCNS_v1_male_brain_and_vnc": {
        "id_field": "MaleCNS v1.0 bodyId as decimal string",
        "graph": "malecns_v1_traced_edges",
        "rule": "A separate male specimen. Restrict body_pre and body_post to annotated neuron bodyId when reporting neuron-to-neuron counts. Never treat type matches as identical FAFB cells.",
    },
}
data["version_gate"].update({
    "princeton_2025_detector": "FAFB v783 roots, 783.2 Princeton detector; same specimen as original Zenodo/Buhmann v783.0 but a separate synapse-call release; unfiltered, >=5-pair and point tables must not be added together",
    "banc_graph": "BANC CAVE materialization v888; final Nature 2026 paper and Dataverse v3.0. Paper-compatible synapse detector v2 and later v3 are alternatives within one BANC specimen; v626 preprint data are not v888",
    "malecns_graph": "MaleCNS v1.0, minconf 0.5, traced-only; do not mix preliminary v0.9 figures or extrapolate all-body contacts to neuron-to-neuron contacts",
    "cross_specimen_rule": "BANC and MaleCNS are separate animals from FAFB and from each other. Reviewed matches, published type mappings and sides support homolog/type hypotheses only; no imported exact FAFB synapse.",
})
data["current_unknowns"] = [
    item for item in data["current_unknowns"]
    if not item.startswith("Die originalen Synapsen- und Morphologie-Großdateien")
    and not item.startswith("Warum der Princeton-Einzelpunktexport")
]
for refreshed_unknown in [
    "Der vollständige Princeton-Einzelpunktexport ist verfügbar und MD5-geprüft; er ist ein automatischer Detektorbefund, keine funktionelle Synapsenmessung oder ein kalibriertes Modellgewicht.",
    "Warum der spätere Princeton-Punktexport 213 nichtautaptische Kontakte des R7-Roots 720575940623940963 enthält, der frühere ungefilterte Verbindungsexport aber keine, ist aus den vorliegenden Tabellen nicht kausal bestimmbar. Die reproduzierte Filtergleichheit erklärt nur die rechnerische Differenz.",
]:
    prefix = ("Der vollständige Princeton-Einzelpunktexport" if refreshed_unknown.startswith("Der vollständige")
              else "Warum der spätere Princeton-Punktexport")
    for index, old in enumerate(data["current_unknowns"]):
        if old.startswith(prefix):
            data["current_unknowns"][index] = refreshed_unknown
            break
    else:
        data["current_unknowns"].append(refreshed_unknown)
data["audit"].update({
    "princeton_provenance_file": "data/codex_fafb_v783/princeton_provenance.json",
    "princeton_connection_audit_file": "analysis/reconstruction_candidates_v783/princeton_audit.json",
    "banc_provenance_file": "data/research_sources/other/banc_2026/provenance.json",
    "banc_edgelist_audit_file": "data/research_sources/other/banc_2026/edgelist_audit.json",
    "banc_crosswalk_audit_file": "data/research_sources/other/banc_2026/crosswalk_audit.json",
    "banc_partner_pattern_audit_file": "data/research_sources/other/banc_2026/partner_pattern_audit.json",
    "malecns_provenance_file": "data/malecns_v1_reference/provenance.json",
    "malecns_neuron_graph_audit_file": "analysis/malecns_v1_reference_audit.json",
    "malecns_type_projection_audit_file": "analysis/malecns_type_partner_hypotheses_audit.json",
})

pr = "data/codex_fafb_v783/princeton_provenance.json"
pu = "https://storage.googleapis.com/flywire-data/codex/data/fafb/783/"
source("fafb_princeton_unfiltered_edges",
       "data/codex_fafb_v783/connections_princeton_no_threshold.csv.gz", pr,
       pu + "connections_princeton_no_threshold.csv.gz", "gzip CSV",
       "FAFB v783 roots; Princeton 2025 detector, unfiltered",
       "pre_root_id, post_root_id, neuropil; syn_count",
       "Separate same-specimen alternative detector graph; 22,285,323 pair-neuropil rows and 76,944,499 summed calls overall", "Codex/FlyWire data terms")
source("fafb_princeton_filtered_edges",
       "data/codex_fafb_v783/connections_princeton.csv.gz", "analysis/reconstruction_candidates_v783/princeton_audit.json",
       pu + "connections_princeton.csv.gz", "gzip CSV",
       "FAFB v783 roots; Princeton 2025 detector, directed-pair sum >=5",
       "pre_root_id, post_root_id, neuropil; syn_count",
       "Thresholded view of the Princeton detector; never add to the unfiltered table", "Codex/FlyWire data terms")
source("fafb_princeton_points",
       "data/codex_fafb_v783/fafb_v783_princeton_synapse_table.csv.gz", pr,
       pu + "fafb_v783_princeton_synapse_table.csv.gz", "gzip CSV",
       "FAFB v783 roots; Princeton 2025 individual synapse calls",
       "pre_root_id_720575940/post_root_id_720575940 are nine-digit suffixes; reconstruct decimal-string root IDs; point coordinates and neuropil",
       "MD5-verified full alternate detector point set (2,695,106,039 bytes); no EM images, cleft score or physiological weight", "Codex/FlyWire data terms")

bp = "data/research_sources/other/banc_2026/provenance.json"
bu = "https://doi.org/10.7910/DVN/7WTH1N"
for id, name, fmt, key, role in [
    ("banc_v888_meta", "banc_888_meta.feather", "Feather", "banc_888_id", "188,508 BANC v888 IDs and 81 metadata fields; inspect proofread status and v626/v850/v888 crosswalk"),
    ("banc_v888_edges_v2", "banc_888_edgelist_simple_v2.feather", "Feather", "pre, post; count", "Paper-compatible BANC graph; 11,752,828 directed rows; filter self-connections for most circuit analyses"),
    ("banc_v888_edges_v3", "banc_888_edgelist_simple_v3.feather", "Feather", "pre, post; count", "Updated BANC detector graph; 13,620,865 directed rows; alternative to v2"),
    ("banc_v888_cells", "supplemental_data_2.txt", "TSV", "root_id (BANC), fafb_match (cross-animal FAFB)", "155,927 BANC neurons with cell type, body roles and cross-animal FAFB match labels"),
    ("banc_harmonized_fafb", "supplemental_data_3.txt", "TSV", "root_783", "FAFB harmonized metadata; restrict to official 139,255 FAFB-v783 IDs before direct ID joins"),
    ("banc_an_dn_clusters", "supplemental_data_6.txt", "TSV", "id -> BANC root_id", "3,161 ascending/descending neuron cluster rows with behavioral labels"),
    ("banc_effector_clusters", "supplemental_data_7.txt", "TSV", "id -> BANC root_id", "1,004 effector-neuron rows with body output cluster labels"),
    ("banc_function_literature", "supplemental_data_9.txt", "TSV", "cell_type", "161 literature cell-function rows; type-level evidence only"),
    ("banc_reviewed_fafb_matches", "banc_fafb_reviewed_matches.csv.gz", "Plaintext CSV despite .gz suffix", "query_id BANC -> match_id FAFB; valid=t", "Reviewed cross-animal morphology matches; resolve source BANC IDs to v888 before joining graph"),
]:
    source(id, "data/research_sources/other/banc_2026/" + name, bp,
           bu, fmt, "BANC v888; Nature 2026 final/Dataverse v3.0", key,
           role, "CC BY 4.0")

mp = "data/malecns_v1_reference/provenance.json"
mu = "https://male-cns.janelia.org/download/"
source("malecns_v1_annotations",
       "data/malecns_v1_reference/body-annotations-male-cns-v1.0-minconf-0.5.feather",
       mp, mu, "Feather", "MaleCNS v1.0 minconf 0.5", "bodyId",
       "211,577 annotated bodies; restrict to 166,700 neuron-superclass rows for the neuron graph", "CC BY 4.0")
source("malecns_v1_transmitters",
       "data/malecns_v1_reference/body-neurotransmitters-male-cns-v1.0.feather",
       mp, mu, "Feather", "MaleCNS v1.0", "bodyId",
       "Predicted transmitter labels and confidence; biological sign/receptor effects remain uncertain", "CC BY 4.0")
source("malecns_v1_traced_edges",
       "data/malecns_v1_reference/connectome-weights-male-cns-v1.0-minconf-0.5-traced-only.feather",
       mp, mu, "Feather", "MaleCNS v1.0 minconf 0.5 traced-only",
       "body_pre, body_post; weight",
       "25,563,197 all-body rows and 124,025,046 contacts; after both-end neuron filter 25,558,671 rows and 124,009,893 contacts", "CC BY 4.0")
source("malecns_v1_roles", "data/malecns_v1_reference/model_neuron_roles_v1.csv",
       "analysis/malecns_v1_reference_audit.json", mu, "CSV derived from verified official Feather",
       "MaleCNS v1.0", "bodyId", "166,700 neurons with sensor/motor class, type, side and candidate transmitter", "CC BY 4.0")
source("malecns_flywire_author_type_mapping",
       "data/malecns_v1_reference/mcns_fw_edge_comp_mappings.json", mp,
       "https://github.com/flyconnectome/2025malecns", "JSON",
       "MaleCNS author supplement at pinned commit 67767d2233657983993ff6c2be48e836a935863c",
       "published MaleCNS/FlyWire type-label mapping", "Cross-animal cell-type correspondence, never individual root-ID identity", "Supplemental repository terms; inspect per-file license")

derived("princeton_616_connection_candidates",
        "analysis/reconstruction_candidates_v783/princeton_unfiltered_for_616.csv",
        "analysis/reconstruction_candidates_v783/princeton_audit.json",
        "FAFB v783 Princeton 2025", "FAFB pre/post root and neuropil",
        "3,233 candidate pair-neuropil rows touching 477 of 616 IDs missing original aggregate edges")
derived("princeton_616_individual_point_calls",
        "analysis/reconstruction_candidates_v783/princeton_individual_points_for_616.csv",
        "analysis/reconstruction_candidates_v783/princeton_point_audit.json",
        "FAFB v783 Princeton 2025", "reconstructed full FAFB pre/post root IDs; source_row_number",
        "26,941 alternate detector point calls touch 550/616 original gap IDs; never silently equate to the unfiltered connection counts")
derived("princeton_616_point_connection_reconciliation",
        "analysis/reconstruction_candidates_v783/princeton_point_to_connection_reconciliation.csv",
        "analysis/reconstruction_candidates_v783/princeton_point_audit.json",
        "FAFB v783 Princeton 2025", "pre_root_id, post_root_id, neuropil",
        "Raw point counts differ by 6,027 from the unfiltered connection table; the full discrepancy is 5,814 autapse points plus 213 non-autaptic calls of R7 root 720575940623940963; see filter audit")
derived("banc_34_reviewed_v888_matches",
        "data/research_sources/other/banc_2026/banc_reviewed_matches_resolved_to_v888_for_34_fafb_ids.csv",
        "data/research_sources/other/banc_2026/partner_pattern_audit.json",
        "BANC v888 vs FAFB v783", "resolved_banc_v888_root_id, fafb_v783_root_id",
        "97 uniquely resolved v888 homologs for 34 of 616 FAFB IDs; 14 unresolved source rows excluded")
derived("banc_34_partner_type_hypotheses",
        "data/research_sources/other/banc_2026/banc_partner_type_hypotheses_for_34_fafb_ids.csv",
        "data/research_sources/other/banc_2026/partner_pattern_audit.json",
        "BANC v888 vs FAFB v783", "FAFB root ID, BANC homolog and partner type/direction",
        "7,293 cross-animal partner-type patterns; not FAFB individual edges")
derived("malecns_616_type_mapping_coverage",
        "data/research_sources/derived/malecns_type_mapping_coverage_for_616.csv",
        "analysis/malecns_type_partner_hypotheses_audit.json",
        "MaleCNS v1.0 vs FAFB v783", "fafb_root_id; author_cross_type_label",
        "562/616 mapped by published type/side mapping, including 520 R1-6; other 96: 42 mapped")
derived("malecns_616_partner_type_hypotheses",
        "data/research_sources/derived/malecns_type_partner_hypotheses_for_616.csv",
        "analysis/malecns_type_partner_hypotheses_audit.json",
        "MaleCNS v1.0 vs FAFB v783", "FAFB root ID, MaleCNS partner type/direction",
        "Observed partner-type frequencies projected across specimens; no individual FAFB edges")

join("princeton_to_v783_ids",
     "fafb_princeton_unfiltered_edges.pre_root_id/post_root_id and fafb_princeton_points.pre/post root IDs",
     "flywire_ids array value", "exact decimal-string v783 root-ID match; retain detector and neuropil; reconcile point counts with unfiltered connection counts",
     "Same FAFB specimen but a different detector; after excluding 5,814 point autapses and 213 point calls of R7 root 720575940623940963 and mapping blank point region to UNASGD, all 3,233 aggregate pair-region keys match exactly. This is an empirical filter match, not a known causal pipeline explanation or original-graph correction.",
     "many-to-one to official FAFB root universe")
join("banc_internal_graph",
     "banc_v888_edges_v2 or banc_v888_edges_v3 pre/post",
     "banc_v888_meta.banc_888_id",
     "exact v888 ID match at both ends, choose one detector, inspect proofread status; join supplementary 2 root_id, 6/7 id in BANC namespace",
     "All edge endpoints in meta; v2/v3 are alternatives and v2 self-edges need explicit filtering",
     "many graph edges to one BANC metadata row per endpoint")
join("banc_reviewed_cross_animal_homology",
     "banc_reviewed_fafb_matches query_id/match_id with valid=t",
     "banc_v888_meta.banc_888_id and flywire_annotations.root_id",
     "resolve source BANC ID to v888 with supervoxel anchor; join FAFB match_id to official v783 root set; keep one-to-many matches and unresolved rows explicit",
     "97 resolved BANC homologs across 34 of 616 FAFB roots; homologs do not transfer synapses between animals",
     "many-to-many cross-specimen homology")
join("banc_harmonized_fafb_annotation",
     "banc_harmonized_fafb.root_783", "flywire_annotations.root_id",
     "filter supplemental table to official v783 root universe, then exact decimal-string ID lookup",
     "139,249 of 139,255 official FAFB IDs occur; 928 additional table rows are outside official local universe",
     "many-to-one after official-root filtering")
join("malecns_internal_graph",
     "malecns_v1_traced_edges.body_pre/body_post",
     "malecns_v1_roles.bodyId", "exact MaleCNS v1.0 ID at both ends; filter both endpoints to annotated neuron-superclass list; weight is contact count",
     "25,558,671 neuron-to-neuron rows over 164,403 participating neurons and 124,009,893 contacts in local v1.0 audit",
     "many graph edges to one MaleCNS neuron row per endpoint")
join("malecns_author_type_projection_to_fafb",
     "malecns_flywire_author_type_mapping published type labels and malecns_v1_roles.type/rootSide",
     "flywire_annotations.cell_type/side and malecns_616_type_mapping_coverage.fafb_root_id",
     "author type mapping plus side; aggregate observed MaleCNS partner types/directions; keep ambiguous and unmapped cases",
     "Separate specimens: 562/616 mapped, driven by 520 R1-6; only 42/96 other IDs mapped; no exact FAFB edge follows",
     "many-to-many cross-specimen type hypotheses")

additional_steps = [
    "For an alternative same-FAFB detector layer, load Princeton unfiltered connections and individual points with the verified provenance; preserve original Buhmann and Princeton identities, and use the >=5 file only as a filtered view.",
    "For point-to-connection checks, apply the empirically reproduced Princeton filters: omit point autapses and the 213 non-autaptic calls of R7 root 720575940623940963, map blank point neuropil to UNASGD, then compare by exact pair and region. The reason the later point export excludes that R7 root from the earlier aggregate is unknown.",
    "For a continuous female brain-and-VNC graph, choose BANC v888 v2 or v3 edges, join to BANC v888 metadata and its AN/DN/effector tables; do not combine detector variants or transfer edges to FAFB.",
    "For a continuous male brain-and-VNC graph, use MaleCNS v1.0 traced-only weights with neuron-superclass filtering and v1.0 roles; do not mix v0.9 and v1.0 totals.",
    "Project BANC reviewed homologs or MaleCNS author type matches to FAFB only as labeled cross-animal cell-type hypotheses with side and ambiguity retained; never create a FAFB root-to-root synapse from them.",
]
for step in additional_steps:
    if step.startswith("For point-to-connection checks,"):
        for index, old in enumerate(data["usage_order"]):
            if old.startswith("For point-to-connection checks,"):
                data["usage_order"][index] = step
                break
    if step not in data["usage_order"]:
        data["usage_order"].append(step)

data["audit"]["banc_v888_meta_ids"] = 188508
data["audit"]["banc_v888_v2_pair_rows"] = 11752828
data["audit"]["banc_v888_v3_pair_rows"] = 13620865
data["audit"]["malecns_v1_annotated_neurons"] = 166700
data["audit"]["malecns_v1_neuron_to_neuron_pair_rows"] = 25558671
data["audit"]["malecns_v1_neuron_to_neuron_contact_sum"] = 124009893
data["audit"]["princeton_unfiltered_pair_neuropil_rows"] = 22285323
data["audit"]["princeton_616_ids_with_unfiltered_candidates"] = 477
data["audit"]["princeton_point_audit_file"] = "analysis/reconstruction_candidates_v783/princeton_point_audit.json"
data["audit"]["princeton_all_individual_point_rows"] = 80215790
data["audit"]["princeton_616_individual_point_rows"] = 26941
data["audit"]["princeton_616_ids_with_individual_point_calls"] = 550
data["audit"]["princeton_616_pair_neuropil_point_connection_mismatches"] = 745
data["audit"]["princeton_616_point_minus_connection_count"] = 6027
data["audit"]["princeton_point_filter_reconciliation_file"] = "analysis/reconstruction_candidates_v783/princeton_filter_reconciliation.json"
data["audit"]["princeton_616_point_autapse_calls_excluded_for_aggregate_fit"] = 5814
data["audit"]["princeton_616_R7_non_autapse_calls_excluded_for_aggregate_fit"] = 213
data["audit"]["princeton_616_pair_region_count_mismatches_after_empirical_filters"] = 0

whole = "analysis/whole_brain_detector_comparison/"
for identifier, filename, key, role in [
    ("fafb_whole_brain_pair_delta", "full_directed_pair_delta.parquet", "pre_root_id, post_root_id", "All original/Princeton directed pairs classified by detector presence and count; no graph merge"),
    ("fafb_whole_brain_pair_region_delta", "full_pair_region_delta.parquet", "pre_root_id, post_root_id, neuropil", "Full detector comparison at pair-region grain; keep separate from directed-pair counts"),
    ("fafb_new_pairs_existing_roots", "all_new_princeton_pairs_between_old_connected_roots.parquet", "pre_root_id, post_root_id", "6,323,027 Princeton-only pairs between roots already connected in original; most have a single detector call"),
    ("fafb_top_new_pairs_type_recurrence", "top_50000_new_pairs_with_type_recurrence.csv", "pre_root_id, post_root_id", "Top 50,000 count-ranked review pairs with original cell-type recurrence as context, not validation"),
]:
    derived(identifier, whole + filename, whole + "audit.json", "FAFB v783 detector comparison", key, role)

motor = "analysis/body_neural_interface/"
for identifier, filename, key, role in [
    ("banc_leg_motor_channels", "banc_leg_motor_channels_391.csv", "banc_888_id", "391 proofread leg motors with anatomical source actions and uncalibrated model-channel proposals; control disabled"),
    ("banc_leg_motor_inputs_v2", "banc_motor_incoming_v2.parquet", "pre, post", "112,809 observed nonself BANC v2 pairs into 391 leg motors"),
    ("banc_leg_motor_inputs_v3", "banc_motor_incoming_v3.parquet", "pre, post", "117,988 observed nonself BANC v3 pairs into 391 leg motors; alternative to v2"),
    ("banc_leg_motor_inputs_comparison", "banc_motor_input_detector_comparison.parquet", "pre_banc_id, post_banc_motor_id", "129,160 union pairs with separate nullable counts; 35,725 have >=5 counts in both versions"),
    ("banc_leg_motor_upstream_metadata", "banc_motor_upstream_metadata.parquet", "banc_888_id", "11,308 upstream neurons with source type, class and sensory metadata"),
]:
    derived(identifier, motor + filename, motor + "audit.json", "BANC v888 leg motor evidence", key, role)
join("banc_leg_motor_incoming", "banc_leg_motor_inputs_v2 or banc_leg_motor_inputs_v3.post", "banc_leg_motor_channels.banc_888_id", "exact BANC v888 decimal-string ID; use one detector at a time", "All 391 motor IDs have input in both versions; no FAFB ID projection", "many incoming pairs to one motor row")
join("banc_motor_anatomy_to_geometric_leg", "banc_leg_motor_channels.body_part_effector and side", "fly.body-observation.v1 legs[].id and candidate joint channel", "front/middle/hind leg plus left/right map to LF/LM/LH/RF/RM/RH; source action names give joint hypotheses", "Geometric observation only: 0 calibrated actuator channels; signs, forces, receptors and dynamics unresolved", "many motor neurons to a candidate leg/joint")
data["audit"]["whole_brain_detector_comparison"] = whole + "audit.json"
data["audit"]["banc_leg_motor_interface"] = motor + "audit.json"

# Exact-root naming, source claims and executed model tests. These entries add
# inspectable evidence; they neither alter the graph nor upgrade model responses
# to biological functional annotations.
catalog = "analysis/neuron_catalog/"
assays = "analysis/neuron_assays/"
paths = "analysis/neuron_pathways/"
for identifier, path, audit, key, role in [
    ("fafb_neuron_catalog", catalog + "catalog_139255.parquet", catalog + "validation.json",
     "root_id decimal string, unique",
     "All 139,255 original roots; 138,765 have a sourced display name and 490 remain unnamed. Original, harmonized, anatomical, curated-function and type-transfer fields remain distinct."),
    ("fafb_neuron_source_claims", catalog + "source_claims.parquet", catalog + "audit.json",
     "claim_id unique; root_id; source_id and source_row",
     "72,040 source claims with evidence_kind and row provenance. A label, anatomical role, model candidate and type-level experiment are different evidence; unmatched roots are excluded from the catalog join."),
    ("fafb_neuron_side_conflicts", catalog + "side_conflicts.parquet", catalog + "audit.json",
     "root_id plus source claim and raw side fields",
     "1,325 source-side conflict rows over 1,317 roots; preserve original source conventions and do not infer a turning command."),
    ("fafb_neuron_assay_sets", catalog + "assay_sets.json", catalog + "validation.json",
     "groups[group_name][] exact decimal-string FAFB root IDs",
     "Source-backed candidate input/readout groups. Shiu v630 IDs are retained only when exactly present; the current left MN9 comes independently from Tastekin 2026."),
    ("fafb_function_assay_protocol", assays + "protocol.json", assays + "audit.json",
     "scenario.id; input.ids; readouts[].id; graphChecksums",
     "Frozen dynamics and stimulus plans for 42 full-graph trials. No parameter fitting to expected behavior; original CSR remains unchanged."),
    ("fafb_function_assay_trajectories", "app/data/neuron_assays.json", assays + "audit.json",
     "scenario.id, trial.id, samples.tMs, readout root ID",
     "42 completed 600-ms trials at 1-ms steps with measured-in-model voltages and spikes. 1,002 checks passed; feeding pattern qualitatively compatible but JO-CE/JO-F selectivity fails. No biological validation."),
    ("fafb_function_assay_neuron_counts", assays + "neuron_spike_counts.csv.gz", assays + "audit.json",
     "scenario, trial, root_id; spike_count, forced_input_count",
     "Exact-root active-neuron counts for every main trial. Counts cover all 600 ms; distinguish imposed sensor spikes from propagated spikes, and do not treat missing rows as missing graph neurons."),
    ("fafb_model_response_profiles", assays + "model_response_profiles.csv", assays + "audit.json",
     "root_id; per-condition all600ms_spikes and forced_input_spikes",
     "7,048 roots respond across six reference conditions, including imposed inputs. Each row is a fixed-model measurement, not a new biological function label."),
    ("fafb_named_model_response_profiles", catalog + "named_model_responses.parquet", catalog + "model_response_join_audit.json",
     "root_id exact one-to-one response/catalog join",
     "7,048 named response profiles; 6,845 roots have at least one non-forced spike, 17 remain unnamed and 6,767 lack a curated functional annotation. Biological catalog fields are unchanged."),
    ("fafb_jo_model_diagnostic", assays + "jo_diagnostic.json", assays + "jo_diagnostic.json",
     "condition, scenario, target root ID, presynaptic source root ID",
     "Two exact trajectory replays and a deterministic 60-vs-60 count/phase comparison. Presynaptic signed-current accounting diagnoses the failed JO selectivity within the fixed model; no new synapse or biological causal proof."),
    ("fafb_assay_path_reachability", paths + "reachability.csv", paths + "audit.json",
     "input_group, readout_root_id, min_synapses_per_edge",
     "Directed anatomical reachability within four hops at thresholds 1 and 5 contacts. Population counts and shortest paths are not a functional or signed dynamical test."),
    ("fafb_assay_example_paths", paths + "example_shortest_paths.json", paths + "audit.json",
     "input-group/readout/threshold plus exact path root IDs",
     "Deterministic original-CSR path examples with synapse counts and transmitter scores; no inferred or added graph edges."),
    ("fafb_side_convention_audit", paths + "side_convention_audit.json", paths + "side_convention_audit.json",
     "selected_test_cells[].root_id; source-specific raw side fields",
     "1,301/1,316 Stuerner DN sides oppose both current annotation sources; 14 agree and one requires review. Historical image inversion is documented; preserve exceptions and raw conventions."),
    ("fafb_neural_body_replay_audit", "app/data/neuron_body_replay_audit.json", "app/data/neuron_body_replay_audit.json",
     "results[].scenario, results[].trial; sourceSha256; mappedIds",
     "42 trace-driven articulated-body replays: eight moving trials and 34 zero-mapped-spike trials. Causal 100-ms mean aDN rate / 50 Hz drives a hypothetical grooming channel. Separate direct actuator demo is excluded; no calibrated muscle forces or body-to-brain feedback."),
]:
    derived(identifier, path, audit, "FAFB v783 exact-root evidence and fixed-model assays, 2026-09-27", key, role)

join("neuron_catalog_to_original_roots", "fafb_neuron_catalog.root_id", "flywire_ids array value",
     "exact decimal-string root-ID equality; preserve original annotation columns and distinct harmonized fields",
     "139,255 unique roots, complete official-root coverage. A display name is not proof of a known function.", "one-to-one over the official root universe")
join("neuron_source_claims_to_catalog", "fafb_neuron_source_claims.root_id", "fafb_neuron_catalog.root_id",
     "exact root-ID match after official-universe filtering; retain claim_id, source_id, source_row and evidence_kind",
     "One root may have several claims of different strength or conflicting sides; do not flatten model/type hypotheses into curated biological functions.", "many claims to one catalog root")
join("function_assays_to_neuron_catalog", "fafb_function_assay_trajectories scenarios[].input.ids and readouts[].id", "fafb_neuron_catalog.root_id",
     "exact string IDs; join scenario.id/trial.id/tMs only within the same frozen protocol; retain input/readout distinction",
     "Input spikes are imposed; readout spikes result from graph propagation. A model response, ablation effect or lack of response does not establish or refute biological function.", "many trials and time samples to one catalog root")
join("model_response_profiles_to_catalog", "fafb_model_response_profiles.root_id", "fafb_neuron_catalog.root_id",
     "validated exact one-to-one left join on root_id; subtract forced_input_spikes from all600ms_spikes only for non-forced model counts",
     "7,048 roots join without loss; counts span 600 ms and are not 400-ms stimulus rates. Keep all biological fields unchanged.", "one-to-one on the 7,048-root responsive subset")
join("anatomical_paths_to_assay_groups", "fafb_assay_path_reachability.input_group/readout_root_id", "fafb_function_assay_protocol scenario/input/readout IDs",
     "explicit group mapping JO_CE->jo_ce, JO_F->jo_f, sugar->sugar, water->water, bitter->bitter; readout root IDs exact; retain synapse threshold and four-hop bound",
     "Anatomical reachability ignores dynamic firing, inhibition and timing; it neither validates the assay nor authorizes connecting new neurons.", "many threshold/readout rows to one input group and readout root")
join("side_conventions_to_catalog", "fafb_side_convention_audit selected_test_cells[].root_id", "fafb_neuron_catalog.root_id",
     "exact root ID; compare source_side_raw, original side and harmonized side separately; normalize vocabulary but never bulk-invert exceptions",
     "aDN1/aDN2 and DNa02/DNg13 source labels oppose current annotations. Keep source labels and refrain from biological lateral motor commands.", "many source conventions to one exact root")
join("jo_diagnostic_to_assay_reference", "fafb_jo_model_diagnostic original_replay scenario/target/tMs", "fafb_function_assay_trajectories reference trial/same scenario/root/tMs",
     "exact equality of every replayed target voltage and spike; treat count_phase_matched_60 as a separate deterministic input intervention",
     "The negative JO-CE/JO-F result persists with matched count and phase; signed-current totals are arbitrary model units, not measured conductances or confirmed biology.", "one-to-one replay samples; separate follow-up conditions")
join("neural_assay_to_articulated_body", "fafb_function_assay_trajectories scenario.id/trial.id and readout spikes", "fafb_neural_body_replay_audit results[].scenario/trial",
     "require sourceSha256 to equal the entire assay JSON hash; exact scenario/trial join and aDN1/aDN2 whitelist; same neural/body time; fixed causal 100-ms mean rate scaled by 50 Hz",
     "The adapter is an explicit uncalibrated display model. Zero mapped spikes produce zero body motion. MN9 has no proboscis actuator; DNa02/DNg13 do not drive yaw; the independent actuator demo is excluded.", "one neural trial to one body replay")

data["version_gate"]["functional_assignment"] = "Separate exact-root biological annotations, cross-release/type hypotheses, anatomical reachability, fixed-model responses and hypothetical body-adapter output. No assay adds a synapse or validates a biological function."
data["version_gate"]["side_conventions"] = "Preserve raw source side labels; historical source reversal is systematic with exceptions. Current v2.1 and harmonized FAFB agree for selected assay DNs, but a label comparison does not calibrate turning."
for item in [
    "Die feste Dynamik reproduziert die veröffentlichte JO-C/E-versus-JO-F-Spezifität der Putz-Auslesen nicht. Zusätzliche Diagnose bestätigt die Abweichung auch bei gleicher Eingangsanzahl und gleichem Phasenplan; Ursache ist biologisch nicht validiert.",
    "7.048 Neuronen haben eine Antwort im Modell; daraus folgen keine neuen biologischen Funktionsnamen. 116.943 Katalogneuronen haben weiterhin keine kuratierte Funktionsannotation.",
    "Das 3D-Labor spielt echte Modell-Auslesesignale über einen hypothetischen Putzadapter ab. MN9-Proboscis-Aktuator, kalibrierte Muskelkräfte, vollständige VNC-Kopplung und sensorische Körperrückkopplung fehlen.",
]:
    if item not in data["current_unknowns"]:
        data["current_unknowns"].append(item)
for step in [
    "For source-backed neuron naming, use the full exact-root catalog and source claims; display curated functions, anatomical roles, type hypotheses and unknown functions separately.",
    "For functional model checks, load the frozen protocol and completed assay traces; inspect baselines, dose comparisons, silencing and matched controls, and retain the failed JO-CE/JO-F literature pattern.",
    "For 3D replay, verify the neural-source checksum and join by scenario/trial; keep the hypothetical grooming adapter and independent actuator demonstration explicit. Do not write model response labels back as biological annotations or create new synapses.",
]:
    if step not in data["usage_order"]:
        data["usage_order"].append(step)
data["audit"].update({
    "neuron_catalog_file": catalog + "audit.json", "neuron_catalog_validation_file": catalog + "validation.json",
    "neuron_model_response_join_file": catalog + "model_response_join_audit.json",
    "neuron_function_assays_file": assays + "audit.json", "neuron_jo_diagnostic_file": assays + "jo_diagnostic.json",
    "neuron_pathways_file": paths + "audit.json", "neuron_side_convention_file": paths + "side_convention_audit.json",
    "neuron_body_replay_file": "app/data/neuron_body_replay_audit.json",
    "neuron_catalog_named_roots": 138765, "neuron_catalog_unknown_function_roots": 116943,
    "neuron_function_main_trials": 42, "neuron_function_diagnostic_trials": 4,
    "neuron_function_checks_passed": 1002, "neuron_model_responsive_roots": 7048,
    "neuron_model_non_forced_responsive_roots": 6845,
})

# BANC motor anatomy, structural pathways and separate direct-actuator trials.
# These entries do not import BANC edges into FAFB or turn contact counts into spikes.
motor_atlas = "analysis/motor_output_atlas/"
motor_paths = "analysis/motor_pathways/"
for identifier, path, audit, key, role in [
    ("banc_motor_output_atlas", motor_atlas + "banc_motor_neurons_805.parquet", motor_atlas + "audit.json",
     "banc_888_id decimal string, unique",
     "805 proofread motor neurons with literal body targets, anatomical actions and separate predicted/verified transmitter fields. Includes 391 leg motors; no automatic actuator sign or cross-specimen edge transfer."),
    ("banc_motor_body_part_summary", motor_atlas + "body_part_summary.csv", motor_atlas + "audit.json",
     "body_part_effector literal complete source label",
     "Disjoint counts of all 805 motor IDs by body target. Composite labels remain intact; action presence is not functional calibration."),
    ("banc_motor_transmitter_conflicts", motor_atlas + "predicted_verified_transmitter_conflicts.csv", motor_atlas + "audit.json",
     "banc_888_id; predicted and source-verified transmitter fields",
     "28 prediction/verified discrepancies among 30 annotated neck/haltere motors. This restricted subset is not a graph-wide error estimate; none of the 391 leg motors has a verified transmitter field."),
    ("banc_motor_direct_paths", motor_paths + "all_direct_paths.parquet", motor_paths + "validation.json",
     "dn, motor; a2/a3 detector counts; mid is unused for direct paths",
     "All 1,618 observed direct DN-to-leg-motor pairs across the two alternative BANC detectors. Preserve nullable detector counts and never sum variants."),
    ("banc_motor_two_edge_paths", motor_paths + "all_two_edge_paths.parquet", motor_paths + "validation.json",
     "dn, mid, motor; a2/a3 and b2/b3 detector-specific counts",
     "All 448,942 complete two-edge paths present in at least one detector. Mixed paths with one edge only in v2 and the next only in v3 are excluded. Structural paths are not firing responses."),
    ("banc_motor_three_edge_examples", motor_paths + "top_three_edge_paths.parquet", motor_paths + "validation.json",
     "dn, mid, mid2, motor; three separate edge counts per detector",
     "6,113 ranked three-edge examples for four prioritized DNa02/DNg13 cells. The complete union contains 5,628,994 paths; this file is not the full three-edge path set and does not cover every DN."),
    ("banc_motor_reachability", motor_paths + "reachability.csv", motor_paths + "audit.json",
     "DN, detector, contact threshold and path-length bound as source columns",
     "Direct and within-two-edge motor reachability for 92 DNs from 36 source-role types. Multiple paths to one motor do not create multiple motors."),
    ("banc_motor_three_edge_reachability", motor_paths + "three_edge_reachability.csv", motor_paths + "audit.json",
     "prioritized DN, detector and threshold",
     "Complete exactly-three-edge counts for four DNa02/DNg13 cells only. Keep separate from within-two-edge endpoint counts."),
    ("banc_motor_structural_ablations", motor_paths + "structural_ablations.json", motor_paths + "validation.json",
     "DN, removed intermediate and matched-control IDs",
     "Node-removal tests on full common >=5 two-edge paths, retaining direct paths. Deliberate outside-path controls have expected null effects; no neural silencing or biological necessity is inferred."),
    ("banc_motor_reviewed_dn_homologies", motor_paths + "reviewed_dn_homologies.csv", motor_paths + "validation.json",
     "source BANC IDs, resolved BANC v888 ID and candidate FAFB ID",
     "93 reviewed cross-animal match rows. Preserve source IDs and resolution method; metadata fafb_match differs from reviewed lists for 46 DN cells. Do not overwrite alternatives or transplant edges."),
    ("banc_motor_browser_pathways", "app/data/motor_pathways.json", motor_paths + "validation.json",
     "motors[].banc_888_id; dns[].id; paths[].id/dnId/motorId/nodes[].id",
     "391 motor references, 92 DNs and 1,739 complete path examples with >=5 contacts on every edge in both detectors. enabled_for_control is false; actuator_sign and force_gain remain null. Structural-only export."),
    ("banc_direct_joint_motor_audit", "app/data/motor_joint_audit.json", "app/data/motor_joint_audit.json",
     "results[].leg and test; directlyDrivenIds/ablatedIds; source.sha256 and modelSourceSha256",
     "48 direct-actuator control trials (six legs x eight conditions, 72,000 integration steps) using 113 anatomy-selected IDs. No BANC spike propagation; equal pool gain, antagonistic dynamics and joint limits are explicit uncalibrated assumptions."),
]:
    derived(identifier, path, audit, "BANC v888 motor evidence and separate direct-actuator model, 2026-09-27", key, role)

join("banc_motor_atlas_to_metadata", "banc_motor_output_atlas.banc_888_id", "banc_v888_meta.banc_888_id",
     "exact decimal-string BANC v888 ID, filtered to source super_class=motor; preserve predicted and verified transmitter separately",
     "805 unique motor IDs; literal body-part groups sum to 805. Proofread identity does not calibrate receptor effects, muscle force or dynamics.", "one-to-one on the motor subset")
join("banc_leg_motor_subset_to_atlas", "banc_leg_motor_channels.banc_888_id", "banc_motor_output_atlas.banc_888_id",
     "exact BANC ID plus unchanged body target, side and published action fields",
     "391 leg motors form a subset of 805. Only 101 explicitly annotated Femur-Tibia flexors and 12 extensors enter the new direct joint demonstration.", "one-to-one on the 391-motor subset")
join("banc_motor_paths_to_separate_graphs", "banc_motor_direct_paths and banc_motor_two_edge_paths and banc_motor_three_edge_examples nodes/edges",
     "banc_v888_edges_v2.pre/post/count or banc_v888_edges_v3.pre/post/count",
     "exact directed BANC pair lookup; all edges of a path must coexist in one chosen detector; common paths require the identical entire sequence in both",
     "Do not fabricate mixed-detector paths or sum v2/v3 counts. Path presence and bottleneck counts are structural evidence only, not signed currents or spikes.", "many paths to reused original detector edges")
join("banc_motor_browser_examples_to_path_audit", "banc_motor_browser_pathways paths[].nodes/edges", "banc_motor_direct_paths/banc_motor_two_edge_paths/banc_motor_three_edge_examples",
     "exact ordered BANC node sequence and detector counts, retaining hop length, ranking and source validation checksum",
     "1,739 display examples are a rank-selected subset; never infer absence of connectivity from absence in the browser sample.", "many displayed paths to the corresponding full or prioritized path records")
join("banc_motor_homologies_remain_cross_animal", "banc_motor_reviewed_dn_homologies resolved BANC ID and candidate FAFB ID",
     "banc_motor_browser_pathways dns[].id and fafb_neuron_catalog.root_id",
     "retain exact identifiers within their own namespaces and preserve conflicting metadata/reviewed homologies as separate claims",
     "This is cross-animal correspondence, never neuron identity or a join that imports a BANC synapse into FAFB. Side and morphology review remain necessary.", "many-to-many cross-specimen hypothesis only")
join("banc_motor_action_to_direct_joint_model", "banc_motor_browser_pathways motors[].banc_888_id/candidate_model_leg/cell_function_detailed",
     "banc_direct_joint_motor_audit pools, results[].directlyDrivenIds and ablatedIds",
     "exact BANC ID whitelist; flex_femur_tibia_joint and extend_femur_tibia_joint only; unique IDs; fixed original pool denominator after ablation; require complete source JSON and model-code hashes",
     "Positive imposed activity follows annotated action, not central neurotransmitter sign. Coactivation preserves both activity channels and increases assumed stiffness/damping. These are direct motor tests, no DN-to-muscle spike simulation, calibrated force or validated body feedback.", "113 motor IDs to 12 experimental antagonist pools, six joints and 48 controlled trials")

data["version_gate"]["motor_evidence_and_control"] = "Keep BANC anatomy, detector-specific structural paths, source-reviewed cross-animal homologies and direct uncalibrated joint trials distinct. Never infer muscle sign from central transmitter predictions or count structural paths as neural activation."
data["audit"].update({
    "motor_output_atlas_file": motor_atlas + "audit.json",
    "motor_pathways_file": motor_paths + "audit.json",
    "motor_pathways_validation_file": motor_paths + "validation.json",
    "motor_joint_control_file": "app/data/motor_joint_audit.json",
    "banc_all_motor_ids": 805, "banc_leg_motor_ids": 391,
    "banc_motor_path_dn_ids": 92, "banc_motor_path_dn_types": 36,
    "banc_motor_direct_paths": 1618, "banc_motor_two_edge_paths": 448942,
    "banc_motor_three_edge_paths_four_priority_dns": 5628994,
    "banc_motor_display_path_examples": 1739, "banc_motor_path_checks_passed": 594,
    "direct_joint_motor_ids": 113, "direct_joint_motor_trials": 48,
})
for item in [
    "Das Motorlabor prüft 113 anatomisch zugeordnete BANC-IDs über direkte Aktivierung und unkalibrierte Gegenspielerdynamik; eine BANC-Spike-Simulation, individuelle Muskelkräfte und sensorische Rückkopplung fehlen.",
    "Die 391 Beinmotoren haben im BANC-Export keine verifizierte Transmitterangabe. Die 28 Konflikte unter 30 annotierten Hals-/Halterenmotoren dürfen nicht als allgemeine Fehlerquote oder Muskelvorzeichen interpretiert werden.",
    "Strukturelle DN-Pfade und Knotenentfernung liefern Erreichbarkeit, keine gemessene neuronale Aktivierung; mehrfach unterstützte Pfade bestimmen weder Kraft noch biologische Kausalität.",
]:
    if item not in data["current_unknowns"]:
        data["current_unknowns"].append(item)
for step in [
    "For motor anatomy, join the 805-motor BANC atlas to v888 metadata by exact BANC ID, keep the 391-leg subset and predicted/verified transmitter evidence distinct.",
    "For DN-to-motor structure, inspect complete direct/two-edge paths and the explicitly limited three-edge analysis. Choose one detector or require the same complete path in both; never merge BANC edges into FAFB.",
    "For direct 3D joint tests, verify motor-path JSON and model-code hashes, use only the 113 documented flexor/extensor IDs, and keep imposed activity, antagonist state, net torque and assumed stiffness distinct from biological neural propagation.",
]:
    if step not in data["usage_order"]:
        data["usage_order"].append(step)

# Source-backed FeCO anatomy and the separate, local LF sensorimotor rate loop.
sm = "analysis/sensorimotor_mapping/"
sm_audit = json.loads((ROOT / sm / "audit.json").read_text(encoding="utf-8"))
sm_validation = json.loads((ROOT / sm / "validation.json").read_text(encoding="utf-8"))
loop_audit_path = "app/data/sensorimotor_audit.json"
loop = json.loads((ROOT / loop_audit_path).read_text(encoding="utf-8"))
assert loop["schema"] == "fly.sensorimotor-audit.v1" and loop["checksPass"] is True
assert all(sm_validation["checks"].values())
assert all(x["all_counts_exact"] and x["within_same_detector"] for x in sm_validation["detectors"].values())


def sha256_file(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


assert sha256_file(loop["source"]["file"]) == loop["source"]["sha256"] == sm_validation["browser_sha256"]
assert sha256_file("app/sensorimotor_model.mjs") == loop["modelSourceSha256"]
assert sha256_file("app/joint_motor_model.mjs") == loop["bodyModelSourceSha256"]
assert sha256_file("app/tests/sensorimotor_model.test.mjs") == loop["testSourceSha256"]

new_ids = []
for identifier, path, integrity, key, role in [
    ("banc_feco_sensor_inventory", sm + "sensor_inventory.csv", sm + "audit.json", "id decimal string, unique BANC v888 ID",
     "625 FeCO claw/hook/club sensor annotations across six legs; source tuning polarity and per-root response curves remain unknown. Proofread and predicted/verified transmitter fields remain separate."),
    ("banc_lf_femur_tibia_motors", sm + "lf_motor_inventory.csv", sm + "audit.json", "id decimal string, unique BANC v888 ID",
     "19 LF femur-tibia motor IDs: 17 source-annotated flexors and two extensors. Anatomical action is not muscle gain or central synapse sign."),
    ("banc_sensorimotor_browser_mapping", "app/data/sensorimotor_mapping.json", sm + "validation.json", "sensors[].id, motors[].id, nodes[id], detectors.v2/v3.edges[].pre/post",
     "625 sensor records, 477 relevant nodes, LF paths and exact detector counts. Per-node full-graph input sums support explicitly normalized model weights. Browser path examples are truncated; edge exports and parquet path sets are complete within the stated LF scope."),
    ("banc_sensorimotor_autonomy_gaps", sm + "autonomy_gaps.json", sm + "audit.json", "gaps[].domain",
     "Known evidence, unknown parameters and required validation across nine selected sensor/motor/body/drive domains; not an exhaustive reconstruction claim."),
    ("banc_sensorimotor_rate_kernel", "app/sensorimotor_model.mjs", loop_audit_path, "BANC v888 decimal-string IDs; chosen detector and declared rate parameters",
     "Local suspended LF joint feedback through selected proofread claw/hook-to-interneuron-to-motor paths. Continuous 0-1 model states, not spikes or measured firing rates; four uniform population-polarity hypotheses remain alternatives."),
    ("banc_sensorimotor_rate_audit", loop_audit_path, loop_audit_path, "results[] and pairedChecks[]; detector, polarity, gain and intervention",
     "194 four-second controlled trials, 388000 integration steps and 24 separate transfer probes. Includes sensory-open, freeze, sensor-edge ablation, matched replay, unseen perturbation, gain-zero, delay and sign-policy controls. Mechanical return is not evidence of neural stabilization."),
    ("banc_sensorimotor_methods", "app/SENSORIMOTOR_METHODS.md", loop_audit_path, "method sections and reproducible commands",
     "Documents physiology versus assumptions, exact selected circuit, control interpretation and numerical validation. No biological validation, locomotion or full-brain autonomy."),
]:
    derived(identifier, path, integrity, "BANC v888 FeCO anatomy; separate uncalibrated local rate model, 2026-09-27", key, role)
    new_ids.append(identifier)
for detector in ["v2", "v3"]:
    for kind, key, role in [
        ("paths", "sensor, intermediate, motor; one complete ordered BANC path", "Complete direct/two-edge LF sensory-to-femur-tibia motor paths within this detector only; anatomical reachability, not response or reflex polarity."),
        ("edges", "pre, post; exact original detector contact count", "Unique original edges used by the selected LF paths; do not add or mix alternative detector versions."),
        ("reachability", "sensor subtype, motor action and stated contact threshold", "Detector-specific LF endpoint reachability and path counts; alternative sensory tuning remains unassigned."),
    ]:
        identifier = f"banc_lf_sensorimotor_{kind}_{detector}"
        extension = "csv" if kind == "reachability" else "parquet"
        derived(identifier, sm + f"lf_{kind}_{detector}.{extension}", sm + "validation.json", f"BANC v888 detector {detector}", key, role)
        new_ids.append(identifier)

join("banc_feco_ids_to_metadata", "banc_feco_sensor_inventory.id", "banc_v888_meta.banc_888_id",
     "exact decimal-string BANC v888 ID; preserve literal subtype, side, leg, proofread status and both transmitter fields",
     "625 unique sensor annotations, including 110 LF cells. Cell-class literature does not assign flexion/extension polarity to individual roots.", "one-to-one on the selected sensor subset")
join("banc_feco_paths_same_detector", "banc_lf_sensorimotor_paths_v2/v3 and banc_lf_sensorimotor_edges_v2/v3",
     "banc_v888_edges_v2 or banc_v888_edges_v3",
     "lookup every ordered edge using the same detector as its path; verify full-graph input sums separately for each version",
     "7292 paths/2720 unique edges in v2 and 8968 paths/3232 unique edges in v3. No mixed-detector path; no added synapse.", "many paths to reused original graph edges")
join("banc_feco_rate_loop_selected_ids", "banc_sensorimotor_browser_mapping sensors/motors/nodes/edges", "banc_sensorimotor_rate_audit circuits[].nodes and source.sha256",
     "exact IDs, proofread=true, claw/hook LF only and >=5 contacts on every selected edge; verify source and kernel hashes",
     "Default v2 has 54 sensors/45 interneurons/19 motors/321 edges; v3 has 54/55/19/461. Normalization, time constants, central receptor effects and uniform subtype polarities are model assumptions. Muscle action follows annotation, not transmitter prediction.", "selected anatomical graph to one local model circuit per detector")
join("banc_feco_joint_feedback", "banc_sensorimotor_rate_kernel actual LF angle/angular velocity", "banc_sensorimotor_rate_audit results and pairedChecks",
     "actual joint state drives declared claw/hook rate hypotheses, graph states drive separate fixed-denominator flexor/extensor pools, and the same joint updates",
     "Technical causal closure is tested with open, frozen, ablated and replay controls. Neither negative nor positive reduction selects a biological polarity; passive mechanical return occurs without sensory feedback.", "one suspended joint, 194 controlled trials, 24 separate transfer probes")

# Original CPG files are local; their published run parameters/results are separate.
cpg_dir = "data/research_sources/other/pugliese_cpg_2026/"
cpg_provenance_path = cpg_dir + "provenance.json"
cpg = json.loads((ROOT / cpg_provenance_path).read_text(encoding="utf-8"))
cpg_roles = {
    "W_20260217.npz": ("pugliese_cpg_original_weights", "Sparse source signed matrix; pre in rows and post in columns; use its own accompanying row order, not global BANC order."),
    "wTable_20260217_fullData_consistentColumns.csv": ("pugliese_cpg_original_cell_table", "Source BANC subset cell identities, row indices, sizes, modules and transmitter fields. This newer curated table is independent of the pinned compiled BANC metadata; retain differing motor classifications."),
    "wTable_20260217_fullData.csv": ("pugliese_cpg_original_run_cell_table", "Exact cell-table filename referenced by original run33241778. Validate row order and compare against consistentColumns table separately; do not assume byte identity."),
    "src/utils/sim_utils.py": ("pugliese_cpg_original_sim_utils", "Unmodified source model equations, parameter sampler and rhythm score; source code availability is not completion of an original published run."),
    "src/simulation/vnc_sim.py": ("pugliese_cpg_original_runner", "Unmodified original simulation runner; source availability alone does not reproduce a published run or its random parameter draw."),
    "configs/neuron_params/default.yaml": ("pugliese_cpg_original_neuron_defaults", "Original default parameter distributions; not a particular published BANC run's random draw."),
    "configs/sim/default.yaml": ("pugliese_cpg_original_sim_defaults", "Original example simulation defaults; not sufficient to reproduce a specific published BANC run configuration."),
}
for item in cpg["files"]:
    path = cpg_dir + item["file"]
    assert (ROOT / path).stat().st_size == item["bytes"]
    assert sha256_file(path) == item["sha256"], path
    identifier, role = cpg_roles[item["file"]]
    source(identifier, path, cpg_provenance_path, item["url"], Path(path).suffix.lstrip(".").upper(),
           "Pugliese_2026 commit " + cpg["commit"], "Source-defined matrix/table index or config key; exact IDs as text", role,
           "Retain original repository terms and attribution; this manifest grants no additional rights.")
    new_ids.append(identifier)
join("pugliese_cpg_weights_to_own_cell_order", "pugliese_cpg_original_weights matrix axes", "pugliese_cpg_original_cell_table source index and root_id",
     "verify source shape, row order and exact IDs before using the pre-by-post matrix; dynamic matrix multiplication uses the corresponding transpose",
     "Keep the published signed matrix and updated cell metadata as their own release. Do not substitute BANC v2/v3 counts, infer NMJ sign, or claim the original run is reproduced from defaults alone.", "4963 matrix rows/columns to 4963 source table cells; independently audited by the CPG runner")

run_provenance_path = cpg_dir + "run33241778/download_provenance.json"
run_provenance = json.loads((ROOT / run_provenance_path).read_text(encoding="utf-8"))
for index, item in enumerate(run_provenance["members"]):
    payload = (ROOT / item["path"]).read_bytes()
    assert len(payload) == item["bytes"] and hashlib.sha256(payload).hexdigest() == item["sha256"]
    assert format(zlib.crc32(payload) & 0xffffffff, "08x") == item["crc32"]
    identifier = ["pugliese_cpg_original_run_config", "pugliese_cpg_original_hydra_config", "pugliese_cpg_original_hydra_overrides"][index]
    source(identifier, item["path"], run_provenance_path, run_provenance["sourceURL"], "YAML",
           "Zenodo 22260924; DNg100_Stim_BANC_vncOnly run33241778", "original run configuration keys",
           "Original archived configuration: stimulation 400, seed 129, 1024 replicates. Member CRC32 matches ZIP directory; local SHA256 recorded. Only selected ZIP members fetched; full archive MD5 is not verified. Configuration availability is not a completed reproduction.",
           "Retain archive attribution and source license; no additional rights granted by this manifest.")
    entry = next(x for x in data["inputs"] if x["id"] == identifier)
    entry["archive_member"] = item["member"]
    entry["archive_crc32"] = item["crc32"]
    entry["full_archive_md5_verified"] = run_provenance["fullArchiveMd5Verified"]
    new_ids.append(identifier)

# Original archived replicate-0 arrays plus independently verified CPU port trials.
cpg_run = "analysis/cpg_reproduction/run33241778_replicate0/"
parameter_provenance_path = cpg_dir + "run33241778/original_parameter_extract_provenance.json"
parameter_provenance = json.loads((ROOT / parameter_provenance_path).read_text(encoding="utf-8"))
parameter_file = parameter_provenance["output"]["path"]
assert sha256_file(parameter_file) == parameter_provenance["output"]["sha256"]
assert not parameter_provenance["parametersResampled"] and not parameter_provenance["valuesTransformed"]
derived("pugliese_cpg_archived_replicate0_parameters", parameter_file, parameter_provenance_path,
        "Zenodo 22260924 run33241778, exact original replicate 0 array selections",
        "tau/a/threshold/fr_cap source row order (1,4963); input_currents and source seeds",
        "Unchanged archived parameter arrays extracted by bounded HDF5/ZIP range reads. The local NPZ is a derived container. Selected bytes/arrays are hashed; whole HDF5 CRC32 and full ZIP MD5 were not verified.")
new_ids.append("pugliese_cpg_archived_replicate0_parameters")
cpg_audit = json.loads((ROOT / cpg_run / "audit.json").read_text(encoding="utf-8"))
cpg_summary = json.loads((ROOT / cpg_run / "summary.json").read_text(encoding="utf-8"))
cpg_verified = json.loads((ROOT / "analysis/cpg_reproduction/result_verification.json").read_text(encoding="utf-8"))
assert cpg_verified["checks_failed"] == 0 and len(cpg_audit["completed_conditions"]) == 8
for filename, expected in cpg_audit["outputs"].items():
    assert sha256_file(cpg_run + filename) == expected, filename
    identifier = "pugliese_cpg_rep0_" + filename.replace(".", "_")
    derived(identifier, cpg_run + filename, cpg_run + "audit.json",
            "CPU model-equation controls using original run33241778 replicate0 parameters, 2026-09-27",
            "exact BANC subset row order; condition/root/time or frozen protocol fields",
            "Controlled CPU-port result for the original signed 4963-cell subgraph. Original parameter values are retained; no comparison against original saved trajectories, no full-brain sensory/body loop and no flight-frequency interpretation.")
    new_ids.append(identifier)
for identifier, path in [("pugliese_cpg_rep0_audit", cpg_run + "audit.json"),
                         ("pugliese_cpg_result_verification", "analysis/cpg_reproduction/result_verification.json"),
                         ("pugliese_cpg_solver_verification", "analysis/cpg_reproduction/solver_unit_audit.json")]:
    derived(identifier, path, path, "CPG CPU-port audit, 2026-09-27", "named checks and source/result hashes",
            "Technical verification of exact input identity, matrix orientation, original RHS comparison, preserved archived parameters and controlled outputs; not experimental biological validation.")
    new_ids.append(identifier)
join("pugliese_archived_parameters_to_cpu_trials", "pugliese_cpg_archived_replicate0_parameters and pugliese_cpg_original_run_config",
     "pugliese_cpg_rep0_protocol_json and pugliese_cpg_rep0_audit",
     "preserve archived replicate0 parameter arrays exactly; source stimulation400 at index1605; source metadata row order and signed matrix",
     "Eight CPU-port controls, not 1024 original replicates. DNg100 yields six rhythmic conservative motor readouts (~15.15Hz); E1/E2 removal eliminates their rhythm in this model. No original trajectory comparison and no inferred biological necessity.", "one original parameter draw to eight intervention/control conditions")

# Flight metadata, checked motor/sensory candidate conflicts and same-detector paths.
flight = "analysis/flight_control_mapping/"
flight_audit = json.loads((ROOT / flight / "audit.json").read_text(encoding="utf-8"))
assert sha256_file("app/data/flight_control_mapping.json") == flight_audit["browserSha256"]
for identifier, path, key, role in [
    ("banc_flight_motor_inventory", flight + "motor_inventory.csv", "id exact BANC v888 decimal string",
     "91 wing/haltere target rows, six annotation conflicts excluded from 85 anatomical pool candidates. DLM5 target side comes from nerve, preserving sourceSide; no kinematic sign, force gain or spike-to-wingbeat conversion."),
    ("banc_flight_sensory_inventory", flight + "sensory_inventory.csv", "id exact BANC v888 decimal string",
     "1032 sensory rows include touch and taste; 245 proprioception candidates, 244 proofread path inputs. Per-root strain/phase tuning remains unknown."),
    ("banc_flight_dn_candidates", flight + "dn_candidates.csv", "id, literatureType and source family",
     "92 exact DN candidates; 59 prioritized proofread inputs, including 38 DNg02 subtype roots. Cell-type experiments do not assign individual root-specific flight-axis tuning."),
    ("banc_flight_visual_candidates", flight + "visual_candidates.csv", "id exact BANC v888 decimal string",
     "38 HS/VS-family LPTC candidates; visual input calibration and root-level directional tuning remain unknown."),
    ("banc_flight_browser_mapping", "app/data/flight_control_mapping.json", "motors/sensors/dns/nodes and separate detectors.v2/v3",
     "Complete selected >=5 pathway-edge subgraphs, ranked motor path examples and observed LPTC-to-DN routes; anatomy only. Never sum detector versions or copy FANC/FAFB edges into BANC."),
    ("banc_flight_gaps", flight + "gaps.json", "gaps[].domain",
     "Unresolved power mechanics, steering phase, sensor tuning, visual transforms, aerodynamics, behavioral state and electrical connectivity."),
    ("banc_flight_primary_sources", flight + "sources.json", "sources[].id and URL",
     "Eleven primary/reference sources with experiment scope and explicit limits; papers were inspected online, not downloaded as original datasets."),
    ("flybody_flight_mechanics_reference", flight + "flybody_mechanics.json", "original local file paths/hashes and raw XML options",
     "Three wing DOFs per side and raw fluid/joint values. Preserve model units; original flight task uses baseline wing patterns and learnt residual actions, not a reconstructed biological brain."),
]:
    derived(identifier, path, flight + "audit.json", "BANC v888 anatomy and separate flight mechanics references, 2026-09-27", key, role)
    new_ids.append(identifier)
for v in ("v2", "v3"):
    for base in ("paths", "edges", "visual_two_edge_paths"):
        file = (f"edges_{v}_at5.parquet" if base == "edges" else f"{base}_{v}.parquet")
        identifier = f"banc_flight_{base}_{v}"
        derived(identifier, flight + file, flight + "audit.json", f"BANC v888 detector {v}", "ordered exact BANC IDs and detector contact counts",
                "All paths/edges within the documented selected input/motor or LPTC/DN scope. An anatomical route is not a measured neural response or a flight control coefficient.")
        new_ids.append(identifier)
join("banc_flight_motor_side_and_conflicts", "banc_flight_motor_inventory.id/sourceSide/nerve", "banc_v888_meta.banc_888_id",
     "exact IDs; retain raw source side, derive effector side only from an unambiguous peripheral nerve prefix, exclude flagged class/action conflicts",
     "91 records, six conflicts, 85 anatomical candidates. DLM5 is crossed; soma side is not automatically muscle side. Muscle names and tonic/phasic labels do not determine 3D moment signs.", "one-to-one source identity; no physiological calibration")
join("banc_flight_paths_to_chosen_graph", "banc_flight_paths_v2/v3 and visual_two_edge_paths_v2/v3", "banc_v888_edges_v2 or banc_v888_edges_v3",
     "all ordered edges of a route checked in the same detector; all browser counts rechecked independently",
     "Motor paths >=5:10625/15347 and edges5529/7304 in v2/v3. LPTC two-edge DN routes >=5:18/32. Zero direct selected LPTC-to-DN edges does not imply absent visual control.", "many complete source paths to reused original graph edges")

cpg_view = json.loads((ROOT / "app/data/cpg_viewer_audit.json").read_text(encoding="utf-8"))
assert sha256_file(cpg_view["browserReplayPath"]) == cpg_view["browserReplaySha256"]
assert sha256_file(cpg_view["sourceReplayPath"]) == cpg_view["sourceReplaySha256"]
assert cpg_view["originalNumbersPreserved"] and not cpg_view["syntheticRatesAdded"]
flight_roll = json.loads((ROOT / "app/data/flight_audit.json").read_text(encoding="utf-8"))
assert flight_roll["checksPass"] and flight_roll["source"]["sha256"] == flight_audit["browserSha256"]
assert sha256_file("app/flight_model.mjs") == flight_roll["modelSourceSha256"]
assert sha256_file("app/tests/flight_model.test.mjs") == flight_roll["testSourceSha256"]
for identifier, path, audit, role in [
    ("pugliese_cpg_browser_replay", "app/data/cpg_replay.json", "app/data/cpg_viewer_audit.json",
     "Eight CPU-model conditions x135 series x1001 samples. All 1081080 values exactly match original local trial replay; no synthetic rates, no joint actuation. Browser visual QA is a separate gate."),
    ("pugliese_cpg_browser_replay_audit", "app/data/cpg_viewer_audit.json", "app/data/cpg_viewer_audit.json",
     "Exact replay/source hash and value comparison, static DOM and HTTP checks. Inspect browserVisualAndInteractionQA rather than inferring visual QA from numeric equality."),
    ("flight_roll_engineering_kernel", "app/flight_model.mjs", "app/data/flight_audit.json",
     "Reduced mechanical wing self-oscillation driven by tonic power pools with 24 exact MN IDs and two b1 steering references. Body-roll feedback is an explicit engineering channel; BANC sensory paths and spikes are not simulated."),
    ("flight_roll_engineering_audit", "app/data/flight_audit.json", "app/data/flight_audit.json",
     "26 controlled trials, 432000 integration steps. Uncalibrated roll rig with mechanical wing oscillation, passive haltere motion and open/inverted/delayed feedback controls; no free translation, biological calibration or autonomous flight."),
    ("flight_roll_engineering_methods", "app/FLIGHT_METHODS.md", "app/data/flight_audit.json",
     "Documents exact root pools, nerve-side correction, mechanical assumptions, engineering feedback, limits and reproducible flight-roll checks."),
]:
    derived(identifier, path, audit, "Separate model/visualization checkpoint, 2026-09-27", "source hashes; exact IDs or condition/sample keys", role)
    new_ids.append(identifier)
join("pugliese_cpg_browser_exact_replay", "pugliese_cpg_rep0_replay_json", "pugliese_cpg_browser_replay",
     "verify full-file source/browser checksums and all condition/series/sample values", "1081080 unchanged rates; no added synthetic dynamics or body control", "eight conditions x135 series x1001 samples")
join("flight_anatomy_to_engineering_roll_rig", "banc_flight_browser_mapping.motors", "flight_roll_engineering_audit.pools",
     "exact 24 wing-power IDs plus two b1 roots; use nerve-derived effectorSide; preserve fixed denominators and test ablations",
     "Mechanical parameters, b1 effect sign and roll-velocity feedback are declared engineering choices. Source kinematicSign/forceGain stay null. No neural propagation or autonomous free flight is claimed.", "26 exact motor references to two power/steering sides in a constrained roll rig")

for entry in data["inputs"]:
    if entry["id"] in new_ids:
        entry["sha256"] = sha256_file(entry["path"])
        entry["bytes"] = (ROOT / entry["path"]).stat().st_size

data["version_gate"]["sensorimotor_scope"] = "A separate continuous 0-1 rate loop propagates along selected exact BANC LF paths, one detector at a time. Source tuning remains unknown; four uniform subtype-polarity hypotheses and uncalibrated receptor effects/forces are tested without selecting a biological winner. No spikes, gait, whole-brain autonomy or original graph modification."
data["version_gate"]["pugliese_cpg_sources"] = f"{len(cpg['files'])} pinned original files are present and SHA256 checked. Original published-run configurations, random draws and results are tracked separately; CPU-port model-equation controls are a different evidence layer and are not biological validation."
data["audit"].update({
    "sensorimotor_mapping_file": sm + "audit.json", "sensorimotor_validation_file": sm + "validation.json",
    "sensorimotor_rate_file": loop_audit_path, "sensorimotor_source_sha256": loop["source"]["sha256"],
    "sensorimotor_model_sha256": loop["modelSourceSha256"],
    "sensorimotor_sensor_inventory_ids": sm_audit["sensor_inventory_roots"],
    "sensorimotor_lf_sensor_ids": sm_audit["lf_sensor_roots"], "sensorimotor_lf_motor_ids": sm_audit["lf_motor_roots"],
    "sensorimotor_trials": loop["trialCount"], "sensorimotor_transfer_probes": loop["transferProbeCount"],
    "sensorimotor_integration_steps": loop["integratedTrialSteps"], "sensorimotor_checks_pass": loop["checksPass"],
    "sensorimotor_partial_neural_propagation": loop["neuralPropagationSimulated"],
    "sensorimotor_biological_validation": loop["biologicalReconstructionValidated"], "full_brain_closed_autonomy": False,
    "pugliese_cpg_source_files": len(cpg["files"]), "pugliese_cpg_source_commit": cpg["commit"],
    "pugliese_cpg_source_provenance": cpg_provenance_path, "pugliese_cpg_original_published_run_reproduced": False,
    "pugliese_cpg_original_run_config_provenance": run_provenance_path,
    "pugliese_cpg_original_run_config_available": True,
    "pugliese_cpg_original_parameter_replicate0_available": True,
    "pugliese_cpg_cpu_conditions": len(cpg_audit["completed_conditions"]),
    "pugliese_cpg_result_checks_passed": cpg_verified["checks_passed"],
    "pugliese_cpg_cpu_audit": cpg_run + "audit.json",
    "flight_mapping_audit": flight + "audit.json", "flight_mapping_source_sha256": flight_audit["browserSha256"],
    "flight_anatomical_motor_pool_ids": flight_audit["eligibleMotorPoolRows"],
    "flight_proofread_proprioceptor_ids": flight_audit["proofreadProprioceptorInputs"],
    "flight_roll_audit": "app/data/flight_audit.json", "flight_roll_trials": flight_roll["trialCount"],
    "flight_roll_integration_steps": flight_roll["integratedSteps"], "flight_roll_checks_pass": flight_roll["checksPass"],
    "cpg_browser_replay_audit": "app/data/cpg_viewer_audit.json", "cpg_browser_replay_values_checked": cpg_view["totalRateValuesCompared"],
})
data["current_unknowns"] = [x for x in data["current_unknowns"] if not x.startswith(("Das Motorlabor prüft 113 anatomisch", "Fünf gepinnte Original-CPG-Dateien", "Gepinnte Original-CPG-Dateien"))]
for item in [
    "Der separate LF-Sensor-Motor-Kreis propagiert kontinuierliche Modellzustände über ausgewählte BANC-Kanten. Exakte Sensorpolaritäten, Rezeptorwirkungen, Zeitkonstanten und Muskelkräfte sind nicht biologisch kalibriert; die mechanische Rückfederung dominiert den getesteten Versuch.",
    "Vollständige autonome Gehirn-Körper-Regelung, Gang, Balance, Bodenkräfte, Motivation und Energie-/Fütterungsrückkopplung sind weiterhin nicht rekonstruiert. Das Haupt-FlyWire-Spiking-Modell bleibt davon getrennt.",
    "Gepinnte Original-CPG-Dateien sind lokal geprüft. Die Verfügbarkeit publizierter Einzel-Laufkonfigurationen, Zufallsparameter und Resultate wird getrennt erfasst; eine kontrollierte CPU-Portierung ersetzt die Original-Laufreplikation nicht.",
]:
    if item not in data["current_unknowns"]:
        data["current_unknowns"].append(item)
for step in [
    "For FeCO feedback, validate the exact BANC LF mapping and one detector, then run the frozen local rate-loop controls. Retain all four polarity hypotheses and both positive and negative outcomes; do not rename individual roots from model behavior.",
    "For CPG work, use the pinned original source files with their own matrix order and signed weights. Keep model-equation port checks separate from original published-run replication, sensory closure and biological validation.",
]:
    if step not in data["usage_order"]:
        data["usage_order"].append(step)

# Refresh only these owned status fields; other completed research remains intact.
status_path = ROOT / "analysis/research_session_status.json"
status = json.loads(status_path.read_text(encoding="utf-8"))
status.update({
    "updated_utc": max(status["updated_utc"], loop["generatedAt"], flight_roll["generatedAt"]),
    "integration_inputs": len(data["inputs"]), "integration_joins": len(data["joins"]),
    "banc_neural_propagation_simulated": True,
    "banc_neural_propagation_scope": "Selected proofread LF claw/hook-interneuron-motor paths; continuous uncalibrated 0-1 model rates, not spikes or full brain",
    "sensory_partial_neural_propagation": True, "full_brain_closed_autonomy": False,
    "biological_motor_coupling": False, "original_graph_modified": False,
    "sensorimotor_mapping": sm + "audit.json", "sensorimotor_mapping_validation": sm + "validation.json",
    "sensorimotor_audit": loop_audit_path, "sensorimotor_methods": "app/SENSORIMOTOR_METHODS.md",
    "sensorimotor_autonomy_gaps": sm + "autonomy_gaps.json",
    "sensorimotor_trials": loop["trialCount"], "sensorimotor_transfer_probes": loop["transferProbeCount"],
    "sensorimotor_integration_steps": loop["integratedTrialSteps"], "sensorimotor_checks_pass": loop["checksPass"],
    "sensorimotor_source_sha256": loop["source"]["sha256"], "sensorimotor_model_source_sha256": loop["modelSourceSha256"],
    "sensorimotor_biologically_validated": False, "sensorimotor_locomotion_simulated": False,
    "sensorimotor_findings": loop["findings"],
    "additional_cpg_downloads": f"{len(cpg['files'])} pinned original files local; SHA256/size verified against download provenance",
    "cpg_download_provenance": cpg_provenance_path, "cpg_source_commit": cpg["commit"],
    "cpg_original_published_run_reproduced": False,
    "cpg_original_run_config_available": True, "cpg_original_run_config_provenance": run_provenance_path,
    "cpg_original_run_status": "Original run33241778 configuration and archived replicate0 parameters available; eight CPU-port controls complete; comparison with original saved trajectories remains pending",
    "cpg_archived_replicate0_available": True, "cpg_original_parameter_provenance": parameter_provenance_path,
    "cpg_cpu_model_audit": cpg_run + "audit.json", "cpg_cpu_summary": cpg_run + "summary.json",
    "cpg_cpu_conditions": len(cpg_audit["completed_conditions"]), "cpg_result_checks_passed": cpg_verified["checks_passed"],
    "cpg_original_trajectory_comparison_complete": False,
    "flight_mapping": flight + "audit.json", "flight_mapping_source_sha256": flight_audit["browserSha256"],
    "flight_anatomical_pool_candidates": flight_audit["eligibleMotorPoolRows"], "flight_proofread_proprioceptors": flight_audit["proofreadProprioceptorInputs"],
    "flight_biologically_validated": False,
    "flight_roll_audit": "app/data/flight_audit.json", "flight_roll_methods": "app/FLIGHT_METHODS.md",
    "flight_roll_trials": flight_roll["trialCount"], "flight_roll_integration_steps": flight_roll["integratedSteps"],
    "flight_roll_checks_pass": flight_roll["checksPass"], "flight_neural_propagation_simulated": False,
    "flight_sensor_to_motor_edges_simulated": False, "autonomous_flight": False, "flight_free_translation": False,
    "cpg_browser_replay_audit": "app/data/cpg_viewer_audit.json", "cpg_browser_values_checked": cpg_view["totalRateValuesCompared"],
})
status["open_scientific_questions"] = [x for x in status["open_scientific_questions"] if not x.startswith(("Original published CPG run configuration,", "Original CPG run33241778 configuration is available;"))]
status["local_urls"]["sensorimotor_lab"] = "http://127.0.0.1:4173/sensorimotor.html"
status["local_urls"]["cpg_viewer"] = "http://127.0.0.1:4173/cpg.html"
for question in [
    "Exact-root claw/hook tuning and central receptor effects remain unknown; all four uniform-polarity model hypotheses are retained",
    "Local LF feedback uses rate states and uncalibrated forces; passive mechanical return is not biological neural stabilization",
    "Full-brain closed autonomy, body contacts, balance, locomotion, energy and feeding feedback remain unvalidated",
    "Original CPG config and replicate0 parameters support eight completed CPU-port controls; original saved trajectory comparison and full 1024-replicate reproduction remain pending",
]:
    if question not in status["open_scientific_questions"]:
        status["open_scientific_questions"].append(question)
status_path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

md_path = ROOT / "analysis/model_integration_pack.md"
md = md_path.read_text(encoding="utf-8")
md = re.sub(r"\*\*\d+ Inputs und \d+ Joins\*\*", f"**{len(data['inputs'])} Inputs und {len(data['joins'])} Joins**", md)
section = f"""<!-- SENSORIMOTOR-INTEGRATION:START -->
## Lokaler Sensor-Motor-Kreis und Original-CPG-Dateien

Der [FeCO-Datensatz](sensorimotor_mapping/README.md) enthält **{sm_audit['sensor_inventory_roots']} exakte BANC-Sensor-IDs** aller sechs Beine. Der linke Vorderbein-Ausschnitt enthält 110 Sensoren und 19 Femur–Tibia-Motorneuronen. Die vollständigen Wege und verwendeten Kanten bleiben getrennt: v2 mit 7.292 Wegen/2.720 Kanten, v3 mit 8.968 Wegen/3.232 Kanten. Der [Join-Audit](sensorimotor_mapping/validation.json) prüft jede Kante gegen denselben Detektor und die Eingangs-Normierung gegen den Gesamtgraphen. Exakte Sensorpolaritäten bleiben unbekannt.

Das [Sensor-Motor-Labor](http://127.0.0.1:4173/sensorimotor.html) schließt einen lokalen Kreis: tatsächlicher LF-Gelenkwinkel → deklarierte claw/hook-Eingänge → Zustände ausgewählter BANC-Neuronen → getrennte Beuger-/Strecker-Pools → dasselbe Gelenk. Standard v2: 54 Sensoren, 45 Zwischenzellen, 19 Motoren und 321 Kanten; v3: 54/55/19/461. Die kontinuierlichen Zustände sind Modellaktivitäten von 0 bis 1, keine gemessenen Raten oder Spikes. Originalgraphen bleiben unverändert.

Der [Audit](../app/data/sensorimotor_audit.json) umfasst **{loop['trialCount']} Viersekundenversuche**, {loop['integratedTrialSteps']:,} Integrationsschritte und {loop['transferProbeCount']} zusätzliche Übertragungsproben. Eingänge abschalten, einfrieren, Kanten entfernen und passende sowie unpassende Sensor-Replays prüfen den technischen Kausalweg. Alle vier Polaritätshypothesen und negative Resultate bleiben erhalten. Bei Standardverstärkung liegt die relative Spitzenauslenkungsreduktion ungefähr zwischen −0,60 % und +0,33 %; die mechanische Rückfederung dominiert. Das belegt keine biologische Stabilisierung. Quell- und Codeprüfsummen sind im Audit hinterlegt; [Methoden](../app/SENSORIMOTOR_METHODS.md) und [offene Rekonstruktionslücken](sensorimotor_mapping/autonomy_gaps.md) benennen Parameter und Grenzen.

**{len(cpg['files'])} originale CPG-Dateien** liegen nun lokal unter `data/research_sources/other/pugliese_cpg_2026/`: signierte Matrix, zugehörige Zelltabellen, `sim_utils.py`, Original-Runner `vnc_sim.py` sowie zwei Standard-Konfigurationen. Commit `{cpg['commit']}` und die tatsächlichen SHA256-Werte stehen in der [Download-Provenienz](../data/research_sources/other/pugliese_cpg_2026/provenance.json) und werden beim Manifest-Update erneut geprüft. Die neuere CPG-Zelltabelle bleibt eine eigene Annotationsversion; abweichende Motor-/Transmitterfelder überschreiben den älteren BANC-Export nicht.

Die **Originalkonfiguration von Lauf 33241778** liegt zusätzlich in drei archivierten YAML-Dateien vor: Reiz 400, Seed 129, 1.024 Replikate. Diese per HTTP-Range beschafften ZIP-Mitglieder sind gegen ihre CRC32 geprüft und mit eigenen SHA256-Werten dokumentiert; die MD5 des unvollständig geladenen Gesamtarchivs ist ausdrücklich nicht verifiziert ([Provenienz](../data/research_sources/other/pugliese_cpg_2026/run33241778/download_provenance.json)). Auch die unveränderten Originalparameter von Replikat 0 sind gezielt aus dem HDF5 extrahiert und gehasht; die CRC des gesamten HDF5 wurde nicht geprüft.

Die [CPU-Nachrechnung](cpg_reproduction/results.md) ist mit **acht Bedingungen und 57 bestandenen Ergebnisprüfungen** fertig. Bei konstantem DNg100-Eingang entstehen sechs rhythmische Motorantworten um 15,15 Hz; E1-/E2-Entfernung beseitigt diese Rhythmik im Modell, I2-Entfernung erhält sie bei etwa 13,33 Hz. Das ist ein Ergebnis des Bein-Teilnetzmodells, keine Flügelschlagfrequenz. Originalparameter, eigener Solver und fehlender Vergleich gegen ursprüngliche Trajektorien bleiben getrennt. Der lokale LF-Regelkreis bildet weder das vollständige Gehirn noch Gang, Balance, Motivation oder eine autonome Fliege ab.

Das [Flug-Anschlusspaket](flight_control_mapping/README.md) ergänzt 91 Wing-/Halteren-Motorquellzeilen, 85 konfliktfreie anatomische Poolkandidaten, 244 proofread Propriozeptor-Eingänge und echte separate v2/v3-Wege. Peripherer Nervenverlauf bestimmt die Effektor-Seite; DLM5-Somaseite ist gekreuzt. Muskelkräfte, Flügelphase, Aero-/Sensorparameter und eine biologische Flugvalidierung bleiben offen.

Der getrennte [Flügel-Rollprüfstand](../app/FLIGHT_METHODS.md) ist mit **26 Versuchen und 432.000 Integrationsschritten** technisch geprüft. Er verwendet 24 Power-Motor-IDs und zwei b1-Referenzen, mechanische Selbstschwingung und einen ausdrücklich technischen Rollrückmeldekanal. Die erfassten BANC-Sensor-Motor-Kanten werden dort noch nicht dynamisch simuliert; freie Translation und autonomer Flug sind nicht implementiert. Der [CPG-Viewer](http://127.0.0.1:4173/cpg.html) bewahrt sämtliche 1.081.080 geprüften Modellwerte ohne zusätzliche Raten oder Körperaktionen.
<!-- SENSORIMOTOR-INTEGRATION:END -->"""
marker = r"<!-- SENSORIMOTOR-INTEGRATION:START -->.*?<!-- SENSORIMOTOR-INTEGRATION:END -->"
md = re.sub(marker, lambda _: section, md, flags=re.S) if re.search(marker, md, flags=re.S) else md.rstrip() + "\n\n" + section + "\n"
md_path.write_text(md, encoding="utf-8")

PACK.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Updated {PACK}: {len(data['inputs'])} inputs, {len(data['joins'])} joins")
