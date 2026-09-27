"""Compare side annotations without silently rewriting source labels."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
FILES = {
    "v2_1": ("data/flywire_annotations_v2.1.0/Supplemental_file1_neuron_annotations.tsv", "\t", "root_id"),
    "banc_harmonized_fafb": ("data/research_sources/other/banc_2026/supplemental_data_3.txt", ",", "root_783"),
    "stuerner_dn": ("data/research_sources/other/stuerner_neckconnective/Supplemental_file5_FAFB_DNs.tsv", "\t", "root_id"),
}


def normalized(value):
    return {"l": "left", "r": "right", "m": "center", "left": "left", "right": "right", "center": "center"}.get(value.strip().lower())


def main():
    tables, hashes = {}, {}
    for name, (path, delim, key) in FILES.items():
        p = ROOT / path
        with p.open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f, delimiter=delim))
        tables[name] = {r[key]: r for r in rows}
        assert len(tables[name]) == len(rows)
        hashes[path] = hashlib.sha256(p.read_bytes()).hexdigest()
    a, b, s = [tables[k] for k in FILES]
    global_counts = Counter()
    discrepancies = []
    for root in sorted(a.keys() & b.keys()):
        left, right = normalized(a[root]["side"]), normalized(b[root]["side"])
        status = "both_unknown" if left is None and right is None else "one_unknown" if left is None or right is None else "agree" if left == right else "disagree"
        global_counts[status] += 1
        if status == "disagree":
            discrepancies.append({"root_id": root, "v2_1_side": a[root]["side"], "banc_harmonized_fafb_side": b[root]["side"], "v2_1_type": a[root]["cell_type"], "banc_harmonized_fafb_type": b[root]["cell_type"]})
    dn_rows = []
    for root, r in sorted(s.items()):
        x, y, z = normalized(r["side"]), normalized(a.get(root, {}).get("side", "")), normalized(b.get(root, {}).get("side", ""))
        status = "source_opposite_both_current" if x in ("left", "right") and y == z and y in ("left", "right") and x != y else "all_agree" if x == y == z and x is not None else "requires_individual_review"
        dn_rows.append({"root_id": root, "stuerner_type": r["type"], "stuerner_side_raw": r["side"], "v2_1_side_raw": a.get(root, {}).get("side", ""), "banc_harmonized_fafb_side_raw": b.get(root, {}).get("side", ""), "comparison": status})
    for filename, rows in [("global_side_discrepancies.csv", discrepancies), ("stuerner_dn_side_comparison.csv", dn_rows)]:
        with (OUT / filename).open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    selected = [r for r in dn_rows if r["stuerner_type"] in ("DNa02", "DNg13")]
    for name, root in [("aDN1_l", "720575940616185531"), ("aDN2_l", "720575940629806974")]:
        selected.append({"root_id": root, "shiu_source_name": name, "v2_1_side_raw": a[root]["side"], "banc_harmonized_fafb_side_raw": b[root]["side"], "banc_harmonized_type": b[root]["cell_type"], "comparison": "old_name_side_opposes_current_annotations"})
    audit = {"created_utc": datetime.now(timezone.utc).isoformat(), "source_sha256": hashes,
             "common_fafb_ids": len(a.keys() & b.keys()), "side_comparison": dict(global_counts),
             "stuerner_dn_rows": len(dn_rows), "stuerner_comparison": dict(Counter(r["comparison"] for r in dn_rows)),
             "selected_test_cells": selected,
             "official_coordinate_convention_source": "https://codex.flywire.ai/faq",
             "official_explanation": "Codex documents historical left/right inversion during FAFB image acquisition, later corrected annotation labels, and unchanged mirrored imagery/segmentation.",
             "interpretation": "The systematic source reversal is consistent with that documented convention change; the exact correction history of every source row is not independently established. Preserve original side fields. An annotation-side comparison alone does not calibrate a biological turning command.",
             "normalization": "L/R/M -> left/right/center; empty and NA/na -> unknown; root IDs matched exactly."}
    (OUT / "side_convention_audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
