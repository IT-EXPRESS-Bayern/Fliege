"""Inspect official 2025 Princeton point calls touching 616 original gap roots.

Run only after `fafb_v783_princeton_synapse_table.csv.gz` has its final name and
the downloader has verified the GCS MD5 in `princeton_provenance.json`. The
compressed source deliberately has no synapse ID or detector confidence score;
source row numbers are identifiers only within this exact hashed export.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / "data/codex_fafb_v783/fafb_v783_princeton_synapse_table.csv.gz"
PROVENANCE = ROOT / "data/codex_fafb_v783/princeton_provenance.json"
MISSING = ROOT / "data/research_sources/derived/model_missing_fafb_ids.csv"
PROOFREAD = ROOT / "data/flywire_fafb_v783/proofread_root_ids_783.npy"
UNFILTERED = HERE / "princeton_unfiltered_for_616.csv"
PREFIX = "720575940"
HEADER = (
    "pre_x", "pre_y", "pre_z", "ctr_x", "ctr_y", "ctr_z",
    "post_x", "post_y", "post_z", "size",
    "pre_root_id_720575940", "post_root_id_720575940", "neuropil",
)
POINT_FIELDS = (
    "source_row_number", "pre_root_id", "post_root_id", "selected_root_ids",
    "partner_proofreading_class", *HEADER[:10], "neuropil",
    "interpretation",
)
GROUP_FIELDS = (
    "pre_root_id", "post_root_id", "neuropil", "Princeton_point_calls",
    "Princeton_unfiltered_connection_count", "difference_points_minus_connections",
    "interpretation",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_verified_provenance() -> dict:
    if not SOURCE.is_file():
        raise FileNotFoundError(f"Verified final Princeton point file is pending: {SOURCE}")
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    relevant = [item for item in provenance.get("files", []) if item["path"].endswith(SOURCE.name)]
    if len(relevant) != 1:
        raise ValueError("Provenance has no unique official Princeton point-file record")
    item = relevant[0]
    if SOURCE.stat().st_size != item.get("bytes") or item.get("official_md5_base64") != item.get("md5_base64"):
        raise ValueError("Official file size/MD5 has not been verified")
    return item


def main() -> None:
    provenance = load_verified_provenance()
    missing = {row["root_id"] for row in read_csv(MISSING)}
    if len(missing) != 616 or not all(rid.startswith(PREFIX) and len(rid) == 18 for rid in missing):
        raise ValueError("616 IDs do not fit the source prefix representation")
    missing_suffixes = {rid[len(PREFIX):] for rid in missing}
    proofread = set(map(str, np.load(PROOFREAD, allow_pickle=False).tolist()))
    proofread_suffixes = {rid[len(PREFIX):] for rid in proofread if rid.startswith(PREFIX) and len(rid) == 18}
    if not missing_suffixes <= proofread_suffixes:
        raise ValueError("Missing roots are not all in official proofread array")
    unfiltered = {}
    for row in read_csv(UNFILTERED):
        key = row["pre_root_id"], row["post_root_id"], row["neuropil"]
        count = int(row["synapse_count"])
        if key in unfiltered and count != unfiltered[key]:
            raise ValueError("Duplicated root view differs in count")
        unfiltered[key] = count

    groups = Counter()
    root_points = Counter()
    proofread_groups = Counter()
    neuropils = Counter()
    source_rows = 0
    selected_rows = 0
    bad_size = 0
    selected_classes = Counter()
    with SOURCE.open("rb") as binary, gzip.open(binary, "rt", encoding="utf-8-sig", newline="") as source, \
            (HERE / "princeton_individual_points_for_616.csv").open("w", encoding="utf-8", newline="") as target:
        reader = csv.reader(source)
        header = tuple(next(reader))
        if header != HEADER:
            raise ValueError(f"Unexpected point source schema: {header}")
        writer = csv.DictWriter(target, fieldnames=POINT_FIELDS)
        writer.writeheader()
        for source_rows, values in enumerate(reader, 1):
            if len(values) != len(HEADER):
                raise ValueError(f"Malformed source row {source_rows}")
            pre_suffix, post_suffix = values[10], values[11]
            selected = ({pre_suffix, post_suffix} & missing_suffixes)
            if not selected:
                continue
            selected_rows += 1
            if not pre_suffix.isdigit() or not post_suffix.isdigit():
                raise ValueError(f"Nonnumeric root suffix at source row {source_rows}")
            pre = PREFIX + pre_suffix.zfill(9)
            post = PREFIX + post_suffix.zfill(9)
            full_selected = [PREFIX + suffix.zfill(9) for suffix in sorted(selected)]
            both = pre_suffix in proofread_suffixes and post_suffix in proofread_suffixes
            partner_class = ("both_officially_proofread" if both else
                             "only_pre_officially_proofread" if pre_suffix in proofread_suffixes else
                             "only_post_officially_proofread")
            selected_classes[partner_class] += 1
            if not values[9].isdigit() or int(values[9]) <= 0:
                bad_size += 1
            key = pre, post, values[12]
            groups[key] += 1
            if both:
                proofread_groups[key] += 1
            neuropils[values[12]] += 1
            for root_id in full_selected:
                root_points[root_id] += 1
            writer.writerow({
                "source_row_number": source_rows,
                "pre_root_id": pre,
                "post_root_id": post,
                "selected_root_ids": ";".join(full_selected),
                "partner_proofreading_class": partner_class,
                **dict(zip(HEADER[:10], values[:10])),
                "neuropil": values[12],
                "interpretation": "Alternate automated point call; coordinates and size are not a calibrated probability or biological weight",
            })

    group_output = []
    for key in sorted(set(proofread_groups) | set(unfiltered)):
        point_count = proofread_groups.get(key, 0)
        edge_count = unfiltered.get(key, 0)
        group_output.append({
            "pre_root_id": key[0], "post_root_id": key[1], "neuropil": key[2],
            "Princeton_point_calls": point_count,
            "Princeton_unfiltered_connection_count": edge_count,
            "difference_points_minus_connections": point_count - edge_count,
            "interpretation": "Same Princeton detector only; equality is an empirical dataset-integrity check",
        })
    with (HERE / "princeton_point_to_connection_reconciliation.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=GROUP_FIELDS)
        writer.writeheader()
        writer.writerows(group_output)
    audit = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_file": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "source_bytes": SOURCE.stat().st_size,
        "source_sha256_verified_by_download": provenance.get("sha256"),
        "source_provenance": str(PROVENANCE.relative_to(ROOT)).replace("\\", "/"),
        "source_columns": HEADER,
        "source_root_id_encoding": f"{PREFIX} + nine-digit suffix; preserved as strings",
        "counts": {
            "source_rows": source_rows,
            "point_rows_touching_616": selected_rows,
            "roots_with_any_point": len(root_points),
            "pair_region_keys_touching_616_all_partners": len(groups),
            "pair_region_keys_with_two_proofread_partners": len(proofread_groups),
            "point_rows_by_partner_class": dict(selected_classes),
            "point_rows_by_neuropil": dict(neuropils.most_common()),
            "invalid_or_zero_size_rows": bad_size,
            "point_connection_pair_region_union": len(group_output),
            "point_connection_mismatched_pair_region_rows": sum(int(r["difference_points_minus_connections"]) != 0 for r in group_output),
            "point_connection_net_difference": sum(int(r["difference_points_minus_connections"]) for r in group_output),
        },
        "outputs": {
            "points": {"file": "princeton_individual_points_for_616.csv",
                       "sha256": sha256(HERE / "princeton_individual_points_for_616.csv")},
            "reconciliation": {"file": "princeton_point_to_connection_reconciliation.csv",
                               "sha256": sha256(HERE / "princeton_point_to_connection_reconciliation.csv")},
        },
        "limitation": "The source has no synapse ID, cleft score or connection score. A source row number is reproducible only for this exact verified file. Site size is not an edge confidence or physiological weight. No link is added to original v783.",
    }
    (HERE / "princeton_point_audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(audit["counts"], indent=2))


if __name__ == "__main__":
    main()
