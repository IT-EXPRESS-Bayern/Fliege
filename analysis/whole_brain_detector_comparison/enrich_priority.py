"""Attach original-graph cell-type recurrence to the 50k strongest new-detector pairs.

This is a review aid. A recurring type combination is anatomical context, not
independent verification of any individual automatic synapse call.
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


def main() -> None:
    con = duckdb.connect(database=":memory:")
    con.execute("SET memory_limit='2GB'")
    con.execute("SET threads=4")
    con.execute(f"SET temp_directory={path('duckdb_tmp')}")
    con.execute("SET preserve_insertion_order=false")
    con.execute(f"CREATE VIEW old_pairs AS SELECT * FROM read_parquet({path('original_pair_aggregated.parquet')})")
    con.execute(f"CREATE VIEW ann AS SELECT * FROM read_parquet({path('annotation_lookup.parquet')})")
    support_path = OUT / "old_graph_cell_type_pair_recurrence.parquet"
    if not support_path.exists():
        con.execute(f"""
            COPY (
              SELECT a.cell_type AS pre_cell_type, b.cell_type AS post_cell_type,
                     COUNT(*)::BIGINT AS original_connected_neuron_pairs,
                     SUM(o.syn_count)::BIGINT AS original_synapses_across_type_pair,
                     MAX(o.syn_count)::BIGINT AS maximum_original_pair_count
              FROM old_pairs o
              JOIN ann a ON o.pre_root_id=a.root_id
              JOIN ann b ON o.post_root_id=b.root_id
              WHERE NULLIF(a.cell_type,'') IS NOT NULL AND NULLIF(b.cell_type,'') IS NOT NULL
              GROUP BY 1,2
            ) TO {path(support_path.name)}
            (FORMAT PARQUET, COMPRESSION ZSTD)
        """)
    con.execute(f"CREATE VIEW support AS SELECT * FROM read_parquet({path(support_path.name)})")
    con.execute(f"CREATE VIEW priority AS SELECT * FROM read_csv({path('top_50000_new_princeton_pairs_between_old_connected_roots.csv')}, all_varchar=true)")
    result = con.execute("""
        SELECT p.*,
               COALESCE(s.original_connected_neuron_pairs,0)::BIGINT AS old_edges_between_same_cell_types,
               COALESCE(s.original_synapses_across_type_pair,0)::BIGINT AS old_synapses_between_same_cell_types,
               COALESCE(s.maximum_original_pair_count,0)::BIGINT AS strongest_old_pair_between_same_cell_types,
               CASE WHEN p.pre_cell_type<>'' AND p.post_cell_type<>''
                         AND s.original_connected_neuron_pairs>0 THEN 'known_type_pair'
                    WHEN p.pre_cell_type<>'' AND p.post_cell_type<>'' THEN 'type_pair_not_in_original'
                    ELSE 'cell_type_missing' END AS recurrence_status
        FROM priority p
        LEFT JOIN support s ON p.pre_cell_type=s.pre_cell_type AND p.post_cell_type=s.post_cell_type
        ORDER BY p.princeton_synapse_count::BIGINT DESC,
                 p.pre_root_id::BIGINT, p.post_root_id::BIGINT
    """)
    rows = result.fetchall()
    columns = [item[0] for item in result.description]
    with (OUT / "top_50000_new_pairs_with_type_recurrence.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)
    groups = {"known_type_pair": 0, "type_pair_not_in_original": 0, "cell_type_missing": 0}
    for row in rows:
        groups[row[-1]] += 1
    audit = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "review_rows": len(rows),
        "recurrence_status_in_top_50000": groups,
        "old_graph_type_pair_rows": con.execute("SELECT COUNT(*) FROM support").fetchone()[0],
        "interpretation": "Type-pair recurrence in the older graph supports prioritization only. Each new detector pair remains an unconfirmed automated observation; this is not independent single-synapse evidence.",
    }
    if len(rows) != 50000:
        raise ValueError("Expected 50,000 distinct top priority pairs")
    (OUT / "priority_enrichment_audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
