"""Fetch original run YAMLs with ZIP range requests; full-download fallback is explicit.

Only public Zenodo bytes are fetched. Partial downloads never claim full-archive MD5.
Run from any directory with Python's standard library; no installed network package needed.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "data/research_sources/other/pugliese_cpg_2026/run33241778"
STATUS = ROOT / "app/data/cpg_download_status.json"
SOURCE = "https://zenodo.org/records/22260924/files/DNg100_Stim_BANC_vncOnly.zip?download=1"
EXPECTED_MD5 = "61802de138fdbd34c1d4f78eb9dbd2a8"
PREFIX = "simulations/DNg100_Stim_BANC_vncOnly/hyak/run_id=33241778/"
MEMBERS = ["logs/run_config.yaml", ".hydra/config.yaml", ".hydra/overrides.yaml"]
STATE = {"schema": "fly.cpg-download-status.v1", "phase": "starting", "status": "running",
         "mode": "http_range", "bytesDownloaded": 0, "totalBytes": None,
         "archiveTotalBytes": None, "sourceURL": SOURCE,
         "target": str(TARGET), "detail": "Originale Laufkonfiguration wird gezielt aus dem ZIP gelesen.",
         "error": None, "fullArchiveMd5Verified": False, "files": []}


def atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for retry in range(8):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if retry == 7:
                raise
            time.sleep(.05)


def report(**updates) -> None:
    STATE.update(updates)
    STATE["updatedAt"] = datetime.now(timezone.utc).isoformat()
    STATE["lastUpdate"] = STATE["updatedAt"]
    atomic_json(STATUS, STATE)


def request(headers=None):
    req = urllib.request.Request(SOURCE, headers={"User-Agent": "FlyResearch-public-config-retrieval/1.0",
                                                  "Accept-Encoding": "identity", **(headers or {})})
    for retry in range(4):
        try:
            return urllib.request.urlopen(req, timeout=30)
        except (urllib.error.URLError, TimeoutError):
            if retry == 3:
                raise
            time.sleep(min(2 ** retry, 4))


class RangeUnavailable(RuntimeError):
    pass


class RemoteZip(io.RawIOBase):
    """Seekable HTTP file. Every payload read must be a verified Content-Range."""
    def __init__(self):
        self.position = 0
        report(phase="probing", detail="Prüfe HTTP-Range: Das komplette 807-MB-Archiv wird nur bei Bedarf geladen.")
        with request({"Range": "bytes=0-0"}) as response:
            if response.status != 206:
                raise RangeUnavailable(f"Server antwortet {response.status} statt 206 auf Range-Anfrage")
            match = re.fullmatch(r"bytes 0-0/(\d+)", response.headers.get("Content-Range", ""))
            if not match:
                raise RangeUnavailable("Kein prüfbarer Content-Range-Header")
            self.size = int(match.group(1))
            data = response.read(2)
            if len(data) != 1:
                raise RangeUnavailable("Range-Länge stimmt nicht mit dem Header überein")
            STATE["bytesDownloaded"] += len(data)
        report(phase="reading_directory", archiveTotalBytes=self.size,
               detail="Range-Zugriff funktioniert. ZIP-Inhaltsverzeichnis wird gelesen; große Ergebnisdateien bleiben im Archiv.")

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        self.position = offset if whence == 0 else self.position + offset if whence == 1 else self.size + offset
        if self.position < 0:
            raise ValueError("Negative archive position")
        return self.position

    def read(self, amount=-1):
        if amount < 0:
            amount = self.size - self.position
        amount = min(amount, self.size - self.position)
        if amount <= 0:
            return b""
        # The selected YAMLs and directory should stay small. Never accidentally pull a trajectory.
        if amount > 16 * 1024 * 1024:
            raise RuntimeError(f"Unexpected large range read ({amount} bytes); refusing accidental trajectory download")
        start = self.position
        end = start + amount - 1
        with request({"Range": f"bytes={start}-{end}"}) as response:
            expected = f"bytes {start}-{end}/{self.size}"
            if response.status != 206 or response.headers.get("Content-Range") != expected:
                raise RangeUnavailable("Range-Unterstützung war inkonsistent")
            data = response.read(amount + 1)
        if len(data) != amount:
            raise IOError(f"Short or oversized range: requested {amount}, received {len(data)}")
        self.position += amount
        STATE["bytesDownloaded"] += len(data)
        prefix = STATE.get("progressPrefix", "Gezielter Archivzugriff")
        report(detail=f"{prefix}: {STATE['bytesDownloaded']:,} Bytes übertragen; große Trajektorien werden übersprungen.")
        return data


def full_archive() -> Path:
    report(mode="full_download", phase="downloading_archive",
           detail="Server unterstützt keine zuverlässigen Range-Anfragen. Lade das Originalarchiv mit sichtbarem Fortschritt.")
    dest = TARGET / "DNg100_Stim_BANC_vncOnly.zip"
    partial = dest.with_suffix(".zip.part")
    with request() as response:
        size = response.headers.get("Content-Length")
        report(bytesDownloaded=0, totalBytes=int(size) if size else None,
               archiveTotalBytes=int(size) if size else STATE["archiveTotalBytes"])
        checksum = hashlib.md5()
        with partial.open("wb") as output:
            while True:
                chunk = response.read(128 * 1024)
                if not chunk:
                    break
                output.write(chunk)
                checksum.update(chunk)
                STATE["bytesDownloaded"] += len(chunk)
                report(detail="Originalarchiv wird geladen; anschließend werden MD5 und die ausgewählten YAML-Dateien geprüft.")
    if STATE["totalBytes"] is not None and STATE["bytesDownloaded"] != STATE["totalBytes"]:
        raise IOError("Full archive length does not match Content-Length")
    if checksum.hexdigest() != EXPECTED_MD5:
        raise IOError(f"Full archive MD5 mismatch: {checksum.hexdigest()}")
    os.replace(partial, dest)
    report(phase="archive_verified", fullArchiveMd5Verified=True, detail="Vollständiges Originalarchiv: MD5 stimmt. Konfigurationen werden extrahiert.")
    return dest


def extract_configs(archive):
    with zipfile.ZipFile(archive) as z:
        inventory = [{"member": info.filename, "uncompressedBytes": info.file_size,
                      "compressedBytes": info.compress_size, "compressionMethod": info.compress_type,
                      "crc32Expected": f"{info.CRC:08x}"}
                     for info in z.infolist() if info.filename.startswith(PREFIX)]
        atomic_json(TARGET / "archive_members.json", {"sourceURL": SOURCE, "runPrefix": PREFIX,
                                                       "archiveTotalBytes": STATE["archiveTotalBytes"], "members": inventory})
        names = {i["member"] for i in inventory}
        missing = [PREFIX + member for member in MEMBERS if PREFIX + member not in names]
        if missing:
            raise KeyError(f"Original configuration files absent from archive: {missing}")
        for relative in MEMBERS:
            member = PREFIX + relative
            info = z.getinfo(member)
            if info.file_size > 2 * 1024 * 1024:
                raise RuntimeError(f"Unexpectedly large YAML file {member}")
            report(phase="extracting_config", detail=f"Originaldatei: {relative}")
            data = z.read(member)  # zipfile verifies the uncompressed member CRC32.
            import zlib
            crc = zlib.crc32(data) & 0xFFFFFFFF
            if crc != info.CRC:
                raise IOError(f"CRC mismatch: {member}")
            destination = TARGET / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            STATE["files"].append({"member": member, "path": str(destination.relative_to(ROOT)).replace("\\", "/"),
                                  "bytes": len(data), "compressedBytes": info.compress_size,
                                  "crc32": f"{crc:08x}", "crc32Verified": True,
                                  "sha256": hashlib.sha256(data).hexdigest()})
            report(detail=f"CRC-geprüft und gespeichert: {relative}")


def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    report()
    try:
        try:
            remote = RemoteZip()
            extract_configs(remote)
        except RangeUnavailable as reason:
            # Preserve directory inventory but restart member list if a range server changed behavior.
            STATE["files"] = []
            report(rangeFallbackReason=str(reason))
            extract_configs(full_archive())
        provenance = {"schema": "fly.cpg-original-run-download.v1", "sourceURL": SOURCE,
                      "record": "22260924", "runId": "33241778", "mode": STATE["mode"],
                      "archiveExpectedMd5": EXPECTED_MD5,
                      "fullArchiveMd5Verified": STATE["fullArchiveMd5Verified"],
                      "archiveTotalBytes": STATE["archiveTotalBytes"], "bytesDownloaded": STATE["bytesDownloaded"],
                      "members": STATE["files"], "retrievedAt": datetime.now(timezone.utc).isoformat(),
                      "interpretation": "Member CRC32 and SHA256 validated; full archive MD5 only checked if the entire archive was downloaded."}
        atomic_json(TARGET / "download_provenance.json", provenance)
        detail = (f"Fertig: drei originale YAML-Dateien, CRC-geprüft. Nur {STATE['bytesDownloaded']:,} Bytes per Range übertragen; "
                  "große Trajektorien nicht geladen, vollständige Archiv-MD5 nicht geprüft.") if STATE["mode"] == "http_range" else "Fertig: Originalarchiv MD5-geprüft und drei originale YAML-Dateien CRC-geprüft gespeichert."
        report(phase="complete", status="complete", detail=detail, totalBytes=STATE["bytesDownloaded"], error=None)
        print(json.dumps(provenance, ensure_ascii=False, indent=2), flush=True)
    except Exception as exc:
        report(phase="failed", status="failed", detail="Konfigurationsdownload konnte nicht abgeschlossen werden.", error=f"{type(exc).__name__}: {exc}")
        raise


if __name__ == "__main__":
    main()
