"""Resume the public FlyWire archives, then run the full local analysis.

The process writes a durable log and retries transient download failures. It
does not download the electron microscopy image volume.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "logs"
LOG_FILE = LOG_DIR / "pipeline.log"
STATE_FILE = LOG_DIR / "pipeline_state.json"
DOWNLOAD = [sys.executable, "-u", str(ROOT / "download_flywire.py"),
            "--workers", "8", "--chunk-mib", "1"]
ANALYSIS_PYTHON = ROOT / "analysis" / ".venv" / "Scripts" / "python.exe"
ANALYZE = [str(ANALYSIS_PYTHON), "-u", str(ROOT / "analysis" / "analyze_flywire.py")]


def mark(stage: str, **details: object) -> None:
    LOG_DIR.mkdir(exist_ok=True)
    payload = {"stage": stage, "updated_utc": datetime.now(timezone.utc).isoformat(), **details}
    STATE_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    line = f"[{payload['updated_utc']}] {stage} {details}\n"
    with LOG_FILE.open("a", encoding="utf-8") as log:
        log.write(line)
    print(line, end="", flush=True)


def run_logged(command: list[str]) -> int:
    with LOG_FILE.open("a", encoding="utf-8") as log:
        process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True,
                                   encoding="utf-8", errors="replace", bufsize=1)
        assert process.stdout is not None
        for line in process.stdout:
            log.write(line)
            log.flush()
            print(line, end="", flush=True)
        return process.wait()


def main() -> int:
    if not ANALYSIS_PYTHON.is_file():
        mark("error", detail=f"Analysis interpreter missing: {ANALYSIS_PYTHON}")
        return 2
    for attempt in range(1, 11):
        mark("download", attempt=attempt)
        result = run_logged(DOWNLOAD)
        if result == 0:
            break
        if attempt == 10:
            mark("error", detail="Download failed after ten attempts", exit_code=result)
            return result
        delay = min(900, 30 * 2 ** (attempt - 1))
        mark("retry", attempt=attempt, exit_code=result, wait_seconds=delay)
        time.sleep(delay)

    mark("analysis")
    result = run_logged(ANALYZE)
    if result:
        mark("analysis_error", exit_code=result)
        return result
    mark("complete", report=str(ROOT / "analysis" / "report.md"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
