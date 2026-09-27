"""Refresh the local report's reviewed evidence without changing its identity."""

import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = root / "analysis/research_report_snapshot.json"
target = root / "analysis/research_report_app/src/data.json"
snapshot = json.loads(source.read_text(encoding="utf-8"))
existing = json.loads(target.read_text(encoding="utf-8"))
for key in ("id", "surface", "buildStatus", "authoredRevision"):
    if key in existing:
        snapshot[key] = existing[key]
target.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Synced {len(snapshot['queries'])} reviewed queries; app ID {snapshot['id']}")
