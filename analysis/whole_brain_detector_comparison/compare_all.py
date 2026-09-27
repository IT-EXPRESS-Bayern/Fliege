"""Full FAFB v783 Buhmann-vs-Princeton detector comparison.

Requires DuckDB and PyArrow in analysis/.venv. All source files and the original
CSR remain read-only. Intermediate Parquet files and both complete deltas are
kept for auditability. DuckDB is configured with bounded memory and disk spill.

Run::

    analysis/.venv/Scripts/python.exe analysis/whole_brain_detector_comparison/compare_all.py
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.ipc as ipc
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
ORIGINAL = ROOT / "data/flywire_fafb_v783/proofread_connections_783.feather"
PRINCETON = ROOT / "data/codex_fafb_v783/connections_princeton_no_threshold.csv.gz"
ROOT_IDS = ROOT / "data/flywire_fafb_v783/proofread_root_ids_783.npy"
ANNOTATIONS = ROOT / "data/flywire_annotations_v2.1.0/Supplemental_file1_neuron_annotations.tsv"
ORIGINAL_STAGE = OUT / "original_pair_region_source.parquet"
PRINCETON_STAGE = OUT / "princeton_pair_region_source.parquet"
ORIGINAL_PAIRS = OUT / "original_pair_aggregated.parquet"
PRINCETON_PAIRS = OUT / "princeton_pair_aggregated.parquet"
REGION_DELTA = OUT / "full_pair_region_delta.parquet"
PAIR_DELTA = OUT / "full_directed_pair_delta.parquet"
ANNOTATION_STAGE = OUT / "annotation_lookup.parquet"
ROOT_STAGE = OUT / "official_proofread_roots.parquet"
TOP_CSV = OUT / "top_50000_new_princeton_pairs_between_old_connected_roots.csv"
REGION_CSV = OUT / "source_region_labels.csv"
AUDIT = OUT / "audit.json"
PROGRESS = OUT / "progress.json"
EXPECTED_SHA256 = {
    "original": "24f960ae3e7d4f8cd30db3b62e99fb5179cc3d1e76d8c155bfb441e9737d3faf",
    "princeton": "62c2e562a7470bfd32cbb98e36af3daa607ba0822b37223b34f2aa45250a920e",
    "roots": "7c7b7e818e9232e5ab64793d52ba20574dbe9da3a6509fbc74193b0f259a01be",
}


def sql_path(path: Path) -> str:
    return "'" + str(path.resolve()).replace("\\", "/").replace("'", "''") + "'"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stage(name: str, **info) -> None:
    data = {"stage": name, "updated_utc": datetime.now(timezone.utc).isoformat(), **info}
    PROGRESS.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"[{name}] {info}", flush=True)


def scalar(con: duckdb.DuckDBPyConnection, query: str) -> int:
    return int(con.execute(query).fetchone()[0])


def copy_parquet(con: duckdb.DuckDBPyConnection, select: str, path: Path) -> None:
    temporary = path.with_suffix(path.suffix + ".partial")
    if temporary.exists():
        temporary.unlink()
    con.execute(f"COPY ({select}) TO {sql_path(temporary)} (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 100000)")
    temporary.replace(path)


def build_original_stage() -> None:
    if ORIGINAL_STAGE.is_file():
        stage("original_stage_reuse", bytes=ORIGINAL_STAGE.stat().st_size)
        return
    stage("original_stage_write")
    fields = ("pre_pt_root_id", "post_pt_root_id", "neuropil", "syn_count")
    with pa.memory_map(str(ORIGINAL), "r") as source:
        reader = ipc.open_file(source)
        writer = None
        n_rows = 0
        temporary = ORIGINAL_STAGE.with_suffix(ORIGINAL_STAGE.suffix + ".partial")
        if temporary.exists():
            temporary.unlink()
        try:
            for index in range(reader.num_record_batches):
                batch = reader.get_batch(index).select(fields)
                table = pa.Table.from_batches([batch])
                if writer is None:
                    writer = pq.ParquetWriter(temporary, table.schema, compression="zstd")
                writer.write_table(table, row_group_size=100000)
                n_rows += batch.num_rows
                if index % 32 == 0:
                    stage("original_stage_write", batches_done=index + 1,
                          batches_total=reader.num_record_batches, rows=n_rows)
        finally:
            if writer is not None:
                writer.close()
    if n_rows != 16847997:
        raise ValueError(f"Original published pair-region row count changed: {n_rows}")
    temporary.replace(ORIGINAL_STAGE)
    stage("original_stage_complete", rows=n_rows, bytes=ORIGINAL_STAGE.stat().st_size)


def build_auxiliary_parquets() -> None:
    if not ROOT_STAGE.is_file():
        ids = np.load(ROOT_IDS, allow_pickle=False).astype(np.int64, copy=False)
        pq.write_table(pa.table({"root_id": ids}), ROOT_STAGE, compression="zstd")
    if ANNOTATION_STAGE.is_file():
        return
    table = {k: [] for k in ("root_id", "cell_type", "side", "super_class", "cell_class")}
    with ANNOTATIONS.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            table["root_id"].append(int(row["root_id"]))
            for key in ("cell_type", "side", "super_class", "cell_class"):
                table[key].append(row[key])
    if len(table["root_id"]) != 139255 or len(set(table["root_id"])) != 139255:
        raise ValueError("Pinned annotation ID set changed")
    pq.write_table(pa.table(table), ANNOTATION_STAGE, compression="zstd")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    stage("source_hash")
    source_hashes = {name: sha256(path) for name, path in
                     (("original", ORIGINAL), ("princeton", PRINCETON), ("roots", ROOT_IDS))}
    if source_hashes != EXPECTED_SHA256:
        raise ValueError(f"Verified source hash mismatch: {source_hashes}")
    build_original_stage()
    build_auxiliary_parquets()
    con = duckdb.connect(database=":memory:")
    con.execute("SET memory_limit='2GB'")
    con.execute("SET threads=4")
    con.execute(f"SET temp_directory={sql_path(OUT / 'duckdb_tmp')}")
    con.execute("SET preserve_insertion_order=false")
    stage("princeton_stage_write")
    if not PRINCETON_STAGE.is_file():
        p_csv = sql_path(PRINCETON)
        select = f"""
            SELECT pre_root_id::BIGINT AS pre_root_id,
                   post_root_id::BIGINT AS post_root_id,
                   COALESCE(neuropil, '')::VARCHAR AS neuropil_literal,
                   syn_count::BIGINT AS syn_count,
                   COALESCE(nt_type, '')::VARCHAR AS nt_type
            FROM read_csv({p_csv}, auto_detect=false, header=true, compression='gzip',
                columns={{'pre_root_id':'BIGINT','post_root_id':'BIGINT','neuropil':'VARCHAR',
                         'syn_count':'BIGINT','nt_type':'VARCHAR'}})
        """
        copy_parquet(con, select, PRINCETON_STAGE)
    stage("princeton_stage_complete", bytes=PRINCETON_STAGE.stat().st_size)

    # Both source labels remain available in staging. Alignment is confined to
    # derived comparison views and is never described as anatomical equivalence.
    con.execute(f"""
        CREATE VIEW old_source AS
        SELECT pre_pt_root_id::BIGINT AS pre_root_id,
               post_pt_root_id::BIGINT AS post_root_id,
               COALESCE(neuropil, '')::VARCHAR AS neuropil_literal,
               CASE WHEN neuropil IS NULL OR neuropil IN ('', 'None') THEN 'UNASGD'
                    ELSE neuropil END AS neuropil,
               syn_count::BIGINT AS syn_count
        FROM read_parquet({sql_path(ORIGINAL_STAGE)})
    """)
    con.execute(f"""
        CREATE VIEW new_source AS
        SELECT pre_root_id, post_root_id, neuropil_literal,
               CASE WHEN neuropil_literal IN ('', 'None') THEN 'UNASGD'
                    ELSE neuropil_literal END AS neuropil,
               syn_count, nt_type
        FROM read_parquet({sql_path(PRINCETON_STAGE)})
    """)
    con.execute(f"CREATE VIEW proofread_roots AS SELECT root_id FROM read_parquet({sql_path(ROOT_STAGE)})")
    con.execute(f"CREATE VIEW annotations AS SELECT * FROM read_parquet({sql_path(ANNOTATION_STAGE)})")

    stage("source_counts")
    original_rows, original_synapses = map(int, con.execute(
        "SELECT COUNT(*), SUM(syn_count) FROM old_source").fetchone())
    princeton_rows, princeton_synapses = map(int, con.execute(
        "SELECT COUNT(*), SUM(syn_count) FROM new_source").fetchone())
    if (original_rows, original_synapses) != (16847997, 54492922):
        raise ValueError("Original aggregate counts do not match pinned v783")
    if (princeton_rows, princeton_synapses) != (22285323, 76944499):
        raise ValueError("Princeton counts do not match verified source scan")
    literal_regions = con.execute("""
        SELECT 'original' AS source, neuropil_literal,
               COUNT(*)::BIGINT AS pair_region_rows, SUM(syn_count)::BIGINT AS synapses
        FROM old_source GROUP BY 1,2
        UNION ALL
        SELECT 'princeton', neuropil_literal, COUNT(*)::BIGINT, SUM(syn_count)::BIGINT
        FROM new_source GROUP BY 1,2
        ORDER BY source, neuropil_literal
    """).fetchall()
    with REGION_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("source", "literal_neuropil", "pair_region_rows", "synapse_count"))
        writer.writerows(literal_regions)
    normalized_labels = {
        source: [{"literal": label, "rows": int(n), "synapses": int(count)}
                 for src, label, n, count in literal_regions if src == source and label in ("", "None", "UNASGD")]
        for source in ("original", "princeton")
    }
    original_region_labels = {label for source, label, _, _ in literal_regions if source == "original"}
    princeton_region_labels = {label for source, label, _, _ in literal_regions if source == "princeton"}

    stage("source_membership_and_duplicates")
    membership = {
        "original_pre_outside_official": scalar(con, """SELECT COUNT(*) FROM old_source s ANTI JOIN proofread_roots r ON s.pre_root_id=r.root_id"""),
        "original_post_outside_official": scalar(con, """SELECT COUNT(*) FROM old_source s ANTI JOIN proofread_roots r ON s.post_root_id=r.root_id"""),
        "princeton_pre_outside_official": scalar(con, """SELECT COUNT(*) FROM new_source s ANTI JOIN proofread_roots r ON s.pre_root_id=r.root_id"""),
        "princeton_post_outside_official": scalar(con, """SELECT COUNT(*) FROM new_source s ANTI JOIN proofread_roots r ON s.post_root_id=r.root_id"""),
        "annotation_ids_outside_official": scalar(con, """SELECT COUNT(*) FROM annotations a ANTI JOIN proofread_roots r ON a.root_id=r.root_id"""),
        "official_ids_without_annotation": scalar(con, """SELECT COUNT(*) FROM proofread_roots r ANTI JOIN annotations a ON a.root_id=r.root_id"""),
    }
    if any(membership.values()):
        raise ValueError(f"Exact root-ID membership mismatch: {membership}")
    # Grouping both sources protects the full join even if an export contains
    # duplicate keys. Source-row multiplicity is retained for the audit.
    stage("pair_region_grouping")
    if not (OUT / "old_grouped.parquet").is_file():
        copy_parquet(con, """
            SELECT pre_root_id, post_root_id, neuropil,
                   SUM(syn_count)::BIGINT AS syn_count,
                   COUNT(*)::BIGINT AS source_rows
            FROM old_source GROUP BY 1,2,3
        """, OUT / "old_grouped.parquet")
    if not (OUT / "new_grouped.parquet").is_file():
        copy_parquet(con, """
            SELECT pre_root_id, post_root_id, neuropil,
                   SUM(syn_count)::BIGINT AS syn_count,
                   COUNT(*)::BIGINT AS source_rows
            FROM new_source GROUP BY 1,2,3
        """, OUT / "new_grouped.parquet")
    con.execute(f"CREATE VIEW old_edges AS SELECT * FROM read_parquet({sql_path(OUT / 'old_grouped.parquet')})")
    con.execute(f"CREATE VIEW new_edges AS SELECT * FROM read_parquet({sql_path(OUT / 'new_grouped.parquet')})")
    old_key_rows = scalar(con, "SELECT COUNT(*) FROM old_edges")
    new_key_rows = scalar(con, "SELECT COUNT(*) FROM new_edges")
    stage("pair_region_delta", old_keys=old_key_rows, new_keys=new_key_rows)
    if not REGION_DELTA.is_file():
        copy_parquet(con, """
            SELECT COALESCE(o.pre_root_id, p.pre_root_id) AS pre_root_id,
                   COALESCE(o.post_root_id, p.post_root_id) AS post_root_id,
                   COALESCE(o.neuropil, p.neuropil) AS neuropil,
                   o.syn_count AS original_synapse_count,
                   p.syn_count AS princeton_synapse_count,
                   COALESCE(p.syn_count, 0) - COALESCE(o.syn_count, 0) AS delta_princeton_minus_original,
                   CASE WHEN o.pre_root_id IS NULL THEN 'princeton_only'
                        WHEN p.pre_root_id IS NULL THEN 'original_only'
                        WHEN o.syn_count = p.syn_count THEN 'both_same_count'
                        ELSE 'both_different_count' END AS comparison_class
            FROM old_edges o FULL OUTER JOIN new_edges p USING(pre_root_id, post_root_id, neuropil)
        """, REGION_DELTA)
    con.execute(f"CREATE VIEW region_delta AS SELECT * FROM read_parquet({sql_path(REGION_DELTA)})")
    region_summary = con.execute("""
        SELECT comparison_class, COUNT(*)::BIGINT,
               SUM(COALESCE(original_synapse_count,0))::BIGINT,
               SUM(COALESCE(princeton_synapse_count,0))::BIGINT
        FROM region_delta GROUP BY 1 ORDER BY 1
    """).fetchall()

    stage("directed_pair_aggregation")
    if not ORIGINAL_PAIRS.is_file():
        copy_parquet(con, """
            SELECT pre_root_id, post_root_id, SUM(syn_count)::BIGINT AS syn_count,
                   COUNT(*)::BIGINT AS neuropil_count
            FROM old_edges GROUP BY 1,2
        """, ORIGINAL_PAIRS)
    if not PRINCETON_PAIRS.is_file():
        copy_parquet(con, """
            SELECT pre_root_id, post_root_id, SUM(syn_count)::BIGINT AS syn_count,
                   COUNT(*)::BIGINT AS neuropil_count
            FROM new_edges GROUP BY 1,2
        """, PRINCETON_PAIRS)
    con.execute(f"CREATE VIEW old_pairs AS SELECT * FROM read_parquet({sql_path(ORIGINAL_PAIRS)})")
    con.execute(f"CREATE VIEW new_pairs AS SELECT * FROM read_parquet({sql_path(PRINCETON_PAIRS)})")
    stage("directed_pair_delta")
    if not PAIR_DELTA.is_file():
        copy_parquet(con, """
            SELECT COALESCE(o.pre_root_id, p.pre_root_id) AS pre_root_id,
                   COALESCE(o.post_root_id, p.post_root_id) AS post_root_id,
                   o.syn_count AS original_synapse_count,
                   p.syn_count AS princeton_synapse_count,
                   o.neuropil_count AS original_neuropil_count,
                   p.neuropil_count AS princeton_neuropil_count,
                   COALESCE(p.syn_count,0) - COALESCE(o.syn_count,0) AS delta_princeton_minus_original,
                   CASE WHEN o.pre_root_id IS NULL THEN 'princeton_only'
                        WHEN p.pre_root_id IS NULL THEN 'original_only'
                        WHEN o.syn_count = p.syn_count THEN 'both_same_count'
                        ELSE 'both_different_count' END AS comparison_class
            FROM old_pairs o FULL OUTER JOIN new_pairs p USING(pre_root_id, post_root_id)
        """, PAIR_DELTA)
    con.execute(f"CREATE VIEW pair_delta AS SELECT * FROM read_parquet({sql_path(PAIR_DELTA)})")
    pair_summary = con.execute("""
        SELECT comparison_class, COUNT(*)::BIGINT,
               SUM(COALESCE(original_synapse_count,0))::BIGINT,
               SUM(COALESCE(princeton_synapse_count,0))::BIGINT
        FROM pair_delta GROUP BY 1 ORDER BY 1
    """).fetchall()
    con.execute("""
        CREATE TEMP TABLE old_connected_nodes AS
        SELECT pre_root_id AS root_id FROM old_pairs UNION
        SELECT post_root_id AS root_id FROM old_pairs
    """)
    connected_nodes = scalar(con, "SELECT COUNT(*) FROM old_connected_nodes")
    p_only_both_old_connected = scalar(con, """
        SELECT COUNT(*) FROM pair_delta d
        JOIN old_connected_nodes a ON d.pre_root_id=a.root_id
        JOIN old_connected_nodes b ON d.post_root_id=b.root_id
        WHERE d.comparison_class='princeton_only'
    """)
    p_only_touching_old_isolate = scalar(con, """
        SELECT COUNT(*) FROM pair_delta d
        LEFT JOIN old_connected_nodes a ON d.pre_root_id=a.root_id
        LEFT JOIN old_connected_nodes b ON d.post_root_id=b.root_id
        WHERE d.comparison_class='princeton_only'
          AND (a.root_id IS NULL OR b.root_id IS NULL)
    """)
    stage("priority_top_50000", p_only_both_old_connected=p_only_both_old_connected)
    con.execute("""
        CREATE TEMP TABLE top_new_pairs AS
        SELECT d.pre_root_id, d.post_root_id, d.princeton_synapse_count,
               d.princeton_neuropil_count
        FROM pair_delta d
        JOIN old_connected_nodes a ON d.pre_root_id=a.root_id
        JOIN old_connected_nodes b ON d.post_root_id=b.root_id
        WHERE d.comparison_class='princeton_only'
        ORDER BY d.princeton_synapse_count DESC, d.pre_root_id, d.post_root_id
        LIMIT 50000
    """)
    # Restrict expensive region list aggregation to the selected pairs.
    top = con.execute("""
        SELECT t.pre_root_id::VARCHAR AS pre_root_id,
               t.post_root_id::VARCHAR AS post_root_id,
               t.princeton_synapse_count,
               t.princeton_neuropil_count,
               COALESCE(a.cell_type,'') AS pre_cell_type,
               COALESCE(a.cell_class,'') AS pre_cell_class,
               COALESCE(a.side,'') AS pre_side,
               COALESCE(b.cell_type,'') AS post_cell_type,
               COALESCE(b.cell_class,'') AS post_cell_class,
               COALESCE(b.side,'') AS post_side,
               STRING_AGG(DISTINCT e.neuropil, ';' ORDER BY e.neuropil) AS princeton_neuropils
        FROM top_new_pairs t
        LEFT JOIN annotations a ON t.pre_root_id=a.root_id
        LEFT JOIN annotations b ON t.post_root_id=b.root_id
        LEFT JOIN new_edges e ON t.pre_root_id=e.pre_root_id AND t.post_root_id=e.post_root_id
        GROUP BY ALL
        ORDER BY 3 DESC, 1, 2
    """).fetchall()
    with TOP_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("pre_root_id", "post_root_id", "princeton_synapse_count", "princeton_neuropil_count",
                         "pre_cell_type", "pre_cell_class", "pre_side", "post_cell_type", "post_cell_class",
                         "post_side", "princeton_neuropils"))
        writer.writerows(top)

    stage("audit_and_validation")
    old_pair_count = scalar(con, "SELECT COUNT(*) FROM old_pairs")
    new_pair_count = scalar(con, "SELECT COUNT(*) FROM new_pairs")
    region_delta_total = scalar(con, "SELECT COUNT(*) FROM region_delta")
    pair_delta_total = scalar(con, "SELECT COUNT(*) FROM pair_delta")
    self_pairs = scalar(con, "SELECT COUNT(*) FROM pair_delta WHERE pre_root_id=post_root_id")
    with (ROOT / "data/research_sources/derived/model_missing_fafb_ids.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        missing_ids = [int(row["root_id"]) for row in csv.DictReader(handle)]
    if len(missing_ids) != 616 or len(set(missing_ids)) != 616:
        raise ValueError("Expected 616 unique prior gap IDs")
    con.register("prior_616_arrow", pa.table({"root_id": missing_ids}))
    con.execute("CREATE TEMP TABLE prior_616 AS SELECT root_id::BIGINT AS root_id FROM prior_616_arrow")
    p_only_touching_616 = scalar(con, """
        SELECT COUNT(*) FROM pair_delta d
        WHERE d.comparison_class='princeton_only'
          AND (d.pre_root_id IN (SELECT root_id FROM prior_616)
               OR d.post_root_id IN (SELECT root_id FROM prior_616))
    """)
    region_audit = {name: {"rows": int(n), "original_synapses": int(o), "princeton_synapses": int(p)}
                    for name, n, o, p in region_summary}
    pair_audit = {name: {"pairs": int(n), "original_synapses": int(o), "princeton_synapses": int(p)}
                  for name, n, o, p in pair_summary}
    checks = {
        "original_pinned_rows": original_rows == 16847997,
        "original_pinned_synapses": original_synapses == 54492922,
        "princeton_pinned_rows": princeton_rows == 22285323,
        "princeton_pinned_synapses": princeton_synapses == 76944499,
        "all_root_ids_in_official_v783_array": not any(membership.values()),
        "same_79_literal_neuropil_labels": original_region_labels == princeton_region_labels and len(original_region_labels) == 79,
        "source_pair_region_keys_unique": old_key_rows == original_rows and new_key_rows == princeton_rows,
        "neither_aggregate_contains_autapses": self_pairs == 0,
        "original_pair_count_matches_CSR": old_pair_count == 15091983,
        "region_delta_rows_equal_class_sum": region_delta_total == sum(x["rows"] for x in region_audit.values()),
        "pair_delta_rows_equal_class_sum": pair_delta_total == sum(x["pairs"] for x in pair_audit.values()),
        "princeton_only_pairs_partitioned_by_old_connected_nodes":
            pair_audit["princeton_only"]["pairs"] == p_only_both_old_connected + p_only_touching_old_isolate,
        "prior_616_account_for_all_princeton_only_pairs_touching_old_isolates":
            p_only_touching_616 == p_only_touching_old_isolate,
    }
    if not all(checks.values()):
        raise ValueError(f"Comparison validation failed: {checks}")
    paths = (ORIGINAL_STAGE, PRINCETON_STAGE, OUT / "old_grouped.parquet", OUT / "new_grouped.parquet",
             ORIGINAL_PAIRS, PRINCETON_PAIRS, REGION_DELTA, PAIR_DELTA, ANNOTATION_STAGE,
             ROOT_STAGE, TOP_CSV, REGION_CSV)
    audit = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_releases": {
            "original": "FlyWire FAFB v783, Buhmann detector, Zenodo 10676866",
            "princeton": "Official Codex FAFB v783, Princeton 2025 detector; fafbseg calls the 2025 Princeton synapse release 783.2",
        },
        "source_urls": ["https://zenodo.org/records/10676866",
                        "https://natverse.org/fafbseg/reference/flywire_connectome_data.html",
                        "https://codex.flywire.ai/faq"],
        "source_sha256": source_hashes,
        "software": {"duckdb": duckdb.__version__, "pyarrow": pa.__version__,
                     "memory_limit": "2GB", "threads": 4},
        "source_counts": {
            "original_pair_region_rows": original_rows, "original_synapses": original_synapses,
            "princeton_pair_region_rows": princeton_rows, "princeton_synapses": princeton_synapses,
            "original_grouped_pair_region_keys": old_key_rows,
            "princeton_grouped_pair_region_keys": new_key_rows,
            "original_directed_pairs": old_pair_count,
            "princeton_directed_pairs": new_pair_count,
            "old_connected_root_ids": connected_nodes,
            "literal_neuropil_label_count": len(original_region_labels),
            "autaptic_directed_pairs_in_either_aggregate": self_pairs,
        },
        "literal_region_labels_aligned_for_comparison": normalized_labels,
        "region_comparison": region_audit,
        "pair_comparison": pair_audit,
        "priority": {
            "princeton_only_pairs_between_two_roots_already_connected_in_original_graph": p_only_both_old_connected,
            "princeton_only_pairs_touching_an_originally_isolated_root": p_only_touching_old_isolate,
            "princeton_only_pairs_touching_the_prior_616_roots": p_only_touching_616,
            "top_review_rows_exported": len(top),
        },
        "membership": membership,
        "checks": checks,
        "outputs": {str(p.relative_to(ROOT)).replace("\\", "/"):
                    {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in paths},
        "interpretation": "These are differences between two automatic synapse detectors on the same FAFB v783 segmentation, not newly proven biological edges or added synaptic weights. Literal None/empty region labels are aligned to UNASGD only in the comparison. The published original graph is untouched.",
    }
    AUDIT.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    stage("complete", region_delta_rows=region_delta_total, pair_delta_rows=pair_delta_total,
          p_only_old_connected=p_only_both_old_connected)
    print(json.dumps({"source_counts": audit["source_counts"], "region_comparison": region_audit,
                      "pair_comparison": pair_audit, "priority": audit["priority"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
