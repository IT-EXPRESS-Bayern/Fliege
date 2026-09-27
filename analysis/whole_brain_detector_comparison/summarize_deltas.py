"""Summarize full FAFB-v783 detector deltas without loading the graph into RAM.

Run after compare_all.py with analysis/.venv/Scripts/python.exe.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb


OUT = Path(__file__).resolve().parent


def path(name: str) -> str:
    return "'" + str((OUT / name).resolve()).replace("\\", "/").replace("'", "''") + "'"


def write_csv(con: duckdb.DuckDBPyConnection, name: str, query: str) -> int:
    result = con.execute(query)
    with (OUT / name).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([column[0] for column in result.description])
        rows = result.fetchall()
        writer.writerows(rows)
    print(f"{name}: {len(rows):,} rows", flush=True)
    return len(rows)


def main() -> None:
    con = duckdb.connect(database=":memory:")
    con.execute("SET memory_limit='2GB'")
    con.execute("SET threads=4")
    con.execute(f"SET temp_directory={path('duckdb_tmp')}")
    con.execute("SET preserve_insertion_order=false")
    con.execute(f"CREATE VIEW pair_delta AS SELECT * FROM read_parquet({path('full_directed_pair_delta.parquet')})")
    con.execute(f"CREATE VIEW region_delta AS SELECT * FROM read_parquet({path('full_pair_region_delta.parquet')})")
    con.execute(f"CREATE VIEW annotations AS SELECT * FROM read_parquet({path('annotation_lookup.parquet')})")
    con.execute(f"CREATE VIEW old_pairs AS SELECT * FROM read_parquet({path('original_pair_aggregated.parquet')})")
    con.execute("""
        CREATE TEMP TABLE old_connected_nodes AS
        SELECT pre_root_id AS root_id FROM old_pairs UNION
        SELECT post_root_id AS root_id FROM old_pairs
    """)
    query = """
        SELECT comparison_class, neuropil,
               COUNT(*)::BIGINT AS directed_pair_region_keys,
               SUM(COALESCE(original_synapse_count,0))::BIGINT AS original_synapses,
               SUM(COALESCE(princeton_synapse_count,0))::BIGINT AS princeton_synapses,
               SUM(delta_princeton_minus_original)::BIGINT AS detector_count_delta
        FROM region_delta GROUP BY 1,2
        ORDER BY comparison_class, directed_pair_region_keys DESC, neuropil
    """
    region_rows = write_csv(con, "region_change_summary.csv", query)

    query = """
        SELECT p.comparison_class AS pair_comparison_class,
               r.comparison_class AS pair_region_comparison_class,
               COUNT(*)::BIGINT AS directed_pair_region_keys,
               SUM(COALESCE(r.original_synapse_count,0))::BIGINT AS original_synapses,
               SUM(COALESCE(r.princeton_synapse_count,0))::BIGINT AS princeton_synapses
        FROM region_delta r JOIN pair_delta p USING(pre_root_id, post_root_id)
        GROUP BY 1,2 ORDER BY 1,2
    """
    crosswalk_rows = write_csv(con, "region_pair_class_crosswalk.csv", query)

    # Every pair belongs to one and only one class; bucket weight comes from
    # the detector where the pair exists. A count is no physiological weight.
    query = """
        WITH base AS (
          SELECT comparison_class,
                 COALESCE(princeton_synapse_count, original_synapse_count) AS count_in_available_detector,
                 COALESCE(original_synapse_count,0) AS old_count,
                 COALESCE(princeton_synapse_count,0) AS new_count
          FROM pair_delta
        ), labeled AS (
          SELECT *, CASE
            WHEN count_in_available_detector=1 THEN '01: 1'
            WHEN count_in_available_detector BETWEEN 2 AND 4 THEN '02: 2-4'
            WHEN count_in_available_detector BETWEEN 5 AND 9 THEN '03: 5-9'
            WHEN count_in_available_detector BETWEEN 10 AND 19 THEN '04: 10-19'
            WHEN count_in_available_detector BETWEEN 20 AND 49 THEN '05: 20-49'
            WHEN count_in_available_detector BETWEEN 50 AND 99 THEN '06: 50-99'
            ELSE '07: 100+'
          END AS count_bucket FROM base
        )
        SELECT comparison_class, count_bucket,
               COUNT(*)::BIGINT AS directed_pairs,
               SUM(old_count)::BIGINT AS original_synapses,
               SUM(new_count)::BIGINT AS princeton_synapses
        FROM labeled GROUP BY 1,2 ORDER BY 1,2
    """
    strength_rows = write_csv(con, "pair_strength_distribution.csv", query)

    query = """
        SELECT CASE WHEN delta_princeton_minus_original>0 THEN 'Princeton_higher'
                    WHEN delta_princeton_minus_original<0 THEN 'Original_higher'
                    ELSE 'Same_count' END AS detector_count_relation,
               COUNT(*)::BIGINT AS shared_directed_pairs,
               SUM(original_synapse_count)::BIGINT AS original_synapses,
               SUM(princeton_synapse_count)::BIGINT AS princeton_synapses,
               SUM(delta_princeton_minus_original)::BIGINT AS detector_count_delta
        FROM pair_delta
        WHERE comparison_class IN ('both_same_count','both_different_count')
        GROUP BY 1 ORDER BY 1
    """
    shared_pair_rows = write_csv(con, "shared_pair_count_direction.csv", query)

    query = """
        SELECT d.pre_root_id::VARCHAR AS pre_root_id,
               d.post_root_id::VARCHAR AS post_root_id,
               d.original_synapse_count, d.original_neuropil_count,
               COALESCE(a.cell_type,'') AS pre_cell_type,
               COALESCE(a.cell_class,'') AS pre_cell_class,
               COALESCE(b.cell_type,'') AS post_cell_type,
               COALESCE(b.cell_class,'') AS post_cell_class
        FROM pair_delta d
        LEFT JOIN annotations a ON d.pre_root_id=a.root_id
        LEFT JOIN annotations b ON d.post_root_id=b.root_id
        WHERE d.comparison_class='original_only' AND d.original_synapse_count>=5
        ORDER BY d.original_synapse_count DESC, d.pre_root_id, d.post_root_id
    """
    strong_old_only_rows = write_csv(con, "original_only_pairs_ge5_review.csv", query)

    con.execute("""
        CREATE TEMP TABLE p_only_old_connected AS
        SELECT d.pre_root_id, d.post_root_id, d.princeton_synapse_count,
               d.princeton_neuropil_count
        FROM pair_delta d
        JOIN old_connected_nodes a ON d.pre_root_id=a.root_id
        JOIN old_connected_nodes b ON d.post_root_id=b.root_id
        WHERE d.comparison_class='princeton_only'
    """)
    query = """
        SELECT CASE WHEN princeton_synapse_count=1 THEN '01: 1'
                    WHEN princeton_synapse_count BETWEEN 2 AND 4 THEN '02: 2-4'
                    WHEN princeton_synapse_count BETWEEN 5 AND 9 THEN '03: 5-9'
                    WHEN princeton_synapse_count BETWEEN 10 AND 19 THEN '04: 10-19'
                    WHEN princeton_synapse_count BETWEEN 20 AND 49 THEN '05: 20-49'
                    WHEN princeton_synapse_count BETWEEN 50 AND 99 THEN '06: 50-99'
                    ELSE '07: 100+' END AS count_bucket,
               COUNT(*)::BIGINT AS directed_pairs,
               SUM(princeton_synapse_count)::BIGINT AS princeton_synapses
        FROM p_only_old_connected GROUP BY 1 ORDER BY 1
    """
    existing_strength_rows = write_csv(con, "new_pairs_existing_roots_strength.csv", query)

    query = """
        SELECT COALESCE(NULLIF(a.super_class,''),'[unannotated]') AS pre_super_class,
               COALESCE(NULLIF(b.super_class,''),'[unannotated]') AS post_super_class,
               COUNT(*)::BIGINT AS directed_pairs,
               SUM(d.princeton_synapse_count)::BIGINT AS princeton_synapses,
               COUNT(*) FILTER (WHERE d.princeton_synapse_count>=5)::BIGINT AS pairs_ge_5,
               COUNT(*) FILTER (WHERE d.princeton_synapse_count>=10)::BIGINT AS pairs_ge_10,
               COUNT(*) FILTER (WHERE d.princeton_synapse_count>=20)::BIGINT AS pairs_ge_20
        FROM p_only_old_connected d
        LEFT JOIN annotations a ON d.pre_root_id=a.root_id
        LEFT JOIN annotations b ON d.post_root_id=b.root_id
        GROUP BY 1,2 ORDER BY directed_pairs DESC, 1,2
    """
    super_class_rows = write_csv(con, "new_pairs_existing_roots_super_class_flow.csv", query)

    query = """
        SELECT COALESCE(NULLIF(a.cell_class,''),'[unannotated]') AS pre_cell_class,
               COALESCE(NULLIF(b.cell_class,''),'[unannotated]') AS post_cell_class,
               COUNT(*)::BIGINT AS directed_pairs,
               SUM(d.princeton_synapse_count)::BIGINT AS princeton_synapses,
               COUNT(*) FILTER (WHERE d.princeton_synapse_count>=5)::BIGINT AS pairs_ge_5,
               COUNT(*) FILTER (WHERE d.princeton_synapse_count>=10)::BIGINT AS pairs_ge_10,
               COUNT(*) FILTER (WHERE d.princeton_synapse_count>=20)::BIGINT AS pairs_ge_20
        FROM p_only_old_connected d
        LEFT JOIN annotations a ON d.pre_root_id=a.root_id
        LEFT JOIN annotations b ON d.post_root_id=b.root_id
        GROUP BY 1,2 ORDER BY directed_pairs DESC, 1,2
    """
    cell_class_rows = write_csv(con, "new_pairs_existing_roots_cell_class_flow.csv", query)

    query = """
        SELECT COALESCE(NULLIF(a.cell_type,''),'[unannotated]') AS pre_cell_type,
               COALESCE(NULLIF(b.cell_type,''),'[unannotated]') AS post_cell_type,
               COUNT(*)::BIGINT AS directed_pairs,
               SUM(d.princeton_synapse_count)::BIGINT AS princeton_synapses,
               COUNT(*) FILTER (WHERE d.princeton_synapse_count>=5)::BIGINT AS pairs_ge_5,
               COUNT(*) FILTER (WHERE d.princeton_synapse_count>=10)::BIGINT AS pairs_ge_10,
               COUNT(*) FILTER (WHERE d.princeton_synapse_count>=20)::BIGINT AS pairs_ge_20
        FROM p_only_old_connected d
        LEFT JOIN annotations a ON d.pre_root_id=a.root_id
        LEFT JOIN annotations b ON d.post_root_id=b.root_id
        GROUP BY 1,2 ORDER BY pairs_ge_10 DESC, princeton_synapses DESC, 1,2
        LIMIT 1000
    """
    type_rows = write_csv(con, "top_1000_new_pair_cell_type_flows.csv", query)

    query = """
        SELECT r.neuropil,
               COUNT(*)::BIGINT AS princeton_only_directed_pair_region_keys,
               SUM(r.princeton_synapse_count)::BIGINT AS princeton_synapses,
               COUNT(*) FILTER (WHERE r.princeton_synapse_count>=5)::BIGINT AS keys_ge_5,
               COUNT(*) FILTER (WHERE p.princeton_synapse_count>=10)::BIGINT AS keys_on_pairs_ge_10
        FROM region_delta r
        JOIN p_only_old_connected p USING(pre_root_id, post_root_id)
        WHERE r.comparison_class='princeton_only'
        GROUP BY 1 ORDER BY princeton_only_directed_pair_region_keys DESC, 1
    """
    priority_region_rows = write_csv(con, "new_pairs_existing_roots_by_region.csv", query)

    query = """
        SELECT COUNT(*)::BIGINT AS pairs,
               COUNT(*) FILTER (WHERE a.root_id IS NOT NULL)::BIGINT AS pre_in_annotation,
               COUNT(*) FILTER (WHERE b.root_id IS NOT NULL)::BIGINT AS post_in_annotation,
               COUNT(*) FILTER (WHERE NULLIF(a.cell_type,'') IS NOT NULL AND NULLIF(b.cell_type,'') IS NOT NULL)::BIGINT AS both_cell_types_known,
               COUNT(*) FILTER (WHERE d.princeton_synapse_count>=5)::BIGINT AS pairs_ge_5,
               COUNT(*) FILTER (WHERE d.princeton_synapse_count>=10)::BIGINT AS pairs_ge_10,
               COUNT(*) FILTER (WHERE d.princeton_synapse_count>=20)::BIGINT AS pairs_ge_20,
               COUNT(*) FILTER (WHERE d.princeton_synapse_count>=50)::BIGINT AS pairs_ge_50,
               MAX(d.princeton_synapse_count)::BIGINT AS max_pair_synapse_count
        FROM p_only_old_connected d
        LEFT JOIN annotations a ON d.pre_root_id=a.root_id
        LEFT JOIN annotations b ON d.post_root_id=b.root_id
    """
    result = con.execute(query)
    metrics = dict(zip([item[0] for item in result.description], result.fetchone()))
    if metrics["pairs"] != 6323027:
        raise ValueError("Princeton-only existing-root partition changed")
    # We export all candidate IDs/counts, so a downstream model can apply its
    # own review threshold without recomputing the 21 million-pair comparison.
    full_candidates = OUT / "all_new_princeton_pairs_between_old_connected_roots.parquet"
    if not full_candidates.exists():
        con.execute(f"""
            COPY (
              SELECT pre_root_id, post_root_id, princeton_synapse_count,
                     princeton_neuropil_count
              FROM p_only_old_connected
            ) TO {path(full_candidates.name)}
            (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 100000)
        """)
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_audit": "audit.json",
        "princeton_only_existing_old_connected_roots": metrics,
        "output_row_counts": {
            "region_change_summary.csv": region_rows,
            "region_pair_class_crosswalk.csv": crosswalk_rows,
            "pair_strength_distribution.csv": strength_rows,
            "shared_pair_count_direction.csv": shared_pair_rows,
            "original_only_pairs_ge5_review.csv": strong_old_only_rows,
            "new_pairs_existing_roots_strength.csv": existing_strength_rows,
            "new_pairs_existing_roots_super_class_flow.csv": super_class_rows,
            "new_pairs_existing_roots_cell_class_flow.csv": cell_class_rows,
            "top_1000_new_pair_cell_type_flows.csv": type_rows,
            "new_pairs_existing_roots_by_region.csv": priority_region_rows,
            full_candidates.name: metrics["pairs"],
        },
        "interpretation": "Detector-difference review candidates in the same FAFB specimen, not experimentally verified new synapses. Synapse counts from the detectors must never be added.",
    }
    (OUT / "breakdown_audit.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
